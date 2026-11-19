
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def load_environment_snapshot():
    """
    Load the unified Azure environment discovery snapshot.
    """

    project_root = Path(__file__).resolve().parents[2]

    snapshot_path = (
        project_root
        / "output"
        / "environment_snapshot.json"
    )

    if not snapshot_path.exists():
        raise FileNotFoundError(
            f"Environment snapshot not found: {snapshot_path}"
        )

    with snapshot_path.open("r", encoding="utf-8") as file:
        snapshot = json.load(file)

    if snapshot.get("discovery_status") not in (
        "completed",
        "partial",
    ):
        raise ValueError(
            "Environment snapshot is not usable. "
            f"Status: {snapshot.get('discovery_status')}"
        )

    return snapshot


def add_node(nodes, node_id, node_type, name, properties=None):
    """
    Add a unique component to the environment model.
    """

    if not node_id:
        return

    if node_id in nodes:
        return

    nodes[node_id] = {
        "id": node_id,
        "type": node_type,
        "name": name,
        "properties": properties or {},
    }


def add_relationship(
    relationships,
    source_id,
    target_id,
    relationship_type,
    evidence,
    evidence_type="confirmed_configuration",
):
    """
    Add a relationship between two environment components.

    evidence_type:
    - confirmed_configuration
    - inferred
    - runtime_verified
    """

    if not source_id or not target_id:
        return

    # Avoid duplicate relationships.
    for existing in relationships:
        if (
            existing["source"] == source_id
            and existing["target"] == target_id
            and existing["relationship"] == relationship_type
        ):
            return

    relationships.append({
        "source": source_id,
        "target": target_id,
        "relationship": relationship_type,
        "evidence_type": evidence_type,
        "evidence": evidence,
    })


def discover_resource_nodes(snapshot, nodes):
    """
    Add Azure resources discovered through Resource Manager.
    """

    results = snapshot["discovery_results"]
    resource_inventory = results["azure_resources"]

    for resource in resource_inventory.get("resources", []):

        add_node(
            nodes=nodes,
            node_id=resource.get("id"),
            node_type=resource.get("type"),
            name=resource.get("name"),
            properties={
                "location": resource.get("location"),
                "kind": resource.get("kind"),
                "tags": resource.get("tags"),
            },
        )


def discover_application_relationships(snapshot, nodes, relationships):
    """
    Model App Services and their configured VNet integration.
    """

    results = snapshot["discovery_results"]

    app_services = results.get(
        "app_services", {}
    ).get("app_services", [])

    for app in app_services:

        app_name = app.get("name")
        app_id = None

        # Find the corresponding Azure resource by exact name.
        for node_id, node in nodes.items():

            if (
                node["name"] == app_name
                and node["type"] == "Microsoft.Web/sites"
            ):
                app_id = node_id
                break

        if not app_id:
            continue

        identity = app.get("identity") or {}

        nodes[app_id]["properties"].update({
            "state": app.get("state"),
            "default_host_name": app.get("default_host_name"),
            "https_only": app.get("https_only"),
            "identity_type": identity.get("type"),
            "principal_id": identity.get("principal_id"),
            "application_setting_names": app.get(
                "application_setting_names", []
            ),
        })

        subnet_id = app.get("virtual_network_subnet_id")

        if subnet_id:

            add_relationship(
                relationships,
                source_id=app_id,
                target_id=subnet_id,
                relationship_type="integrates_with_subnet",
                evidence=(
                    "App Service virtual_network_subnet_id "
                    "matches the subnet resource ID."
                ),
            )


def normalize_hostname(value):
    """
    Extract and normalize a hostname from a URL or hostname value.
    """

    if not value:
        return None

    value = value.strip()

    if not value:
        return None

    # urlparse needs a scheme to reliably identify the hostname.
    if "://" not in value:
        value = f"//{value}"

    try:
        hostname = urlparse(value).hostname

        if hostname:
            return hostname.rstrip(".").lower()

    except ValueError:
        pass

    return None


def discover_configured_application_relationships(
    snapshot,
    nodes,
    relationships,
):
    """
    Discover application dependencies using allowlisted
    non-secret App Service configuration values.

    API_URL:
        Frontend App Service -> API App Service

    DB_SERVER:
        API App Service -> SQL Server

    DB_NAME:
        API App Service -> SQL Database

    These relationships establish configured dependencies,
    not successful runtime connectivity.
    """

    results = snapshot["discovery_results"]

    config_results = results.get(
        "application_config", {}
    )

    applications = config_results.get("applications", [])

    # Build an index of App Service default hostnames.
    app_hostname_lookup = {}

    for node_id, node in nodes.items():

        if node["type"] != "Microsoft.Web/sites":
            continue

        hostname = normalize_hostname(
            node["properties"].get("default_host_name")
        )

        if hostname:
            app_hostname_lookup[hostname] = node_id

    # Build SQL Server and database lookup indexes.
    sql_server_lookup = {}
    sql_database_lookup = {}

    for node_id, node in nodes.items():

        node_type = node["type"]
        node_name = (node["name"] or "").lower()

        if node_type == "Microsoft.Sql/servers":

            sql_server_lookup[
                f"{node_name}.database.windows.net"
            ] = node_id

            sql_server_lookup[node_name] = node_id

        elif node_type == "Microsoft.Sql/servers/databases":

            # Azure resource names for SQL databases contain
            # server/database, so extract the database name
            # from the actual Azure resource ID.
            database_id = node["id"]

            marker = "/databases/"

            if marker in database_id:

                database_name = database_id.split(
                    marker, 1
                )[1].split("/", 1)[0]

                sql_database_lookup[
                    database_name.lower()
                ] = node_id

    # Process each application's allowlisted configuration.
    for app_config in applications:

        app_name = app_config.get("name")
        settings = app_config.get("settings", {})

        # Use the exact Azure resource ID from configuration discovery.
        app_id = app_config.get("resource_id")

        if app_id not in nodes:

            # Fall back to exact resource name matching.
            app_id = None

            for node_id, node in nodes.items():

                if (
                    node["type"] == "Microsoft.Web/sites"
                    and node["name"] == app_name
                ):
                    app_id = node_id
                    break

        if not app_id:
            continue

        # -----------------------------------------------------
        # Frontend -> API
        # -----------------------------------------------------

        api_url = settings.get("API_URL")

        if api_url:

            api_hostname = normalize_hostname(api_url)

            target_api_id = app_hostname_lookup.get(api_hostname)

            if target_api_id:

                add_relationship(
                    relationships,
                    source_id=app_id,
                    target_id=target_api_id,
                    relationship_type="calls_api",
                    evidence={
                        "setting_name": "API_URL",
                        "configured_value": api_url,
                        "matched_hostname": api_hostname,
                    },
                    evidence_type="confirmed_configuration",
                )

        # -----------------------------------------------------
        # API -> SQL Server
        # -----------------------------------------------------

        db_server = settings.get("DB_SERVER")

        if db_server:

            sql_hostname = normalize_hostname(db_server)

            target_sql_id = sql_server_lookup.get(sql_hostname)

            if target_sql_id:

                add_relationship(
                    relationships,
                    source_id=app_id,
                    target_id=target_sql_id,
                    relationship_type="connects_to_sql_server",
                    evidence={
                        "setting_name": "DB_SERVER",
                        "configured_value": db_server,
                        "matched_hostname": sql_hostname,
                    },
                    evidence_type="confirmed_configuration",
                )

        # -----------------------------------------------------
        # API -> SQL Database
        # -----------------------------------------------------

        db_name = settings.get("DB_NAME")

        if db_name:

            target_database_id = sql_database_lookup.get(
                db_name.strip().lower()
            )

            if target_database_id:

                add_relationship(
                    relationships,
                    source_id=app_id,
                    target_id=target_database_id,
                    relationship_type="uses_database",
                    evidence={
                        "setting_name": "DB_NAME",
                        "configured_value": db_name,
                    },
                    evidence_type="confirmed_configuration",
                )


def discover_network_relationships(snapshot, nodes, relationships):
    """
    Model VNets, subnets and their NSG associations.
    """

    results = snapshot["discovery_results"]

    networks = results.get(
        "network", {}
    ).get("virtual_networks", [])

    for vnet in networks:

        vnet_id = vnet.get("id")

        if not vnet_id:
            continue

        add_node(
            nodes,
            vnet_id,
            "Microsoft.Network/virtualNetworks",
            vnet.get("name"),
            {
                "address_space": vnet.get("address_space", []),
                "location": vnet.get("location"),
            },
        )

        for subnet in vnet.get("subnets", []):

            subnet_id = subnet.get("id")

            if not subnet_id:
                continue

            add_node(
                nodes,
                subnet_id,
                "Microsoft.Network/virtualNetworks/subnets",
                subnet.get("name"),
                {
                    "address_prefix": subnet.get("address_prefix"),
                    "delegations": subnet.get("delegations", []),
                    "private_endpoint_network_policies": subnet.get(
                        "private_endpoint_network_policies"
                    ),
                },
            )

            add_relationship(
                relationships,
                source_id=subnet_id,
                target_id=vnet_id,
                relationship_type="belongs_to_vnet",
                evidence="Subnet is listed under this VNet.",
            )

            nsg_id = subnet.get("network_security_group_id")

            if nsg_id:

                add_relationship(
                    relationships,
                    source_id=subnet_id,
                    target_id=nsg_id,
                    relationship_type="associated_with_nsg",
                    evidence=(
                        "Subnet network_security_group_id "
                        "references this NSG."
                    ),
                )


def discover_private_endpoint_relationships(
    snapshot,
    nodes,
    relationships,
):
    """
    Model private endpoints, their target resources,
    subnets and private IP addresses.
    """

    results = snapshot["discovery_results"]

    endpoints = results.get(
        "private_endpoints", {}
    ).get("private_endpoints", [])

    for endpoint in endpoints:

        endpoint_name = endpoint.get("name")
        endpoint_id = None

        # Match the endpoint to its Azure resource ID.
        for node_id, node in nodes.items():

            if (
                node["name"] == endpoint_name
                and node["type"] == "Microsoft.Network/privateEndpoints"
            ):
                endpoint_id = node_id
                break

        if not endpoint_id:
            continue

        nodes[endpoint_id]["properties"].update({
            "location": endpoint.get("location"),
            "private_ip_addresses": endpoint.get(
                "private_ip_addresses", []
            ),
        })

        subnet_id = endpoint.get("subnet_id")

        if subnet_id:

            add_relationship(
                relationships,
                source_id=endpoint_id,
                target_id=subnet_id,
                relationship_type="deployed_in_subnet",
                evidence="Private endpoint subnet_id.",
            )

        # Connect the endpoint to its target Azure resource.
        for connection in endpoint.get("connections", []):

            target_id = connection.get("target_resource_id")
            status = connection.get("connection_status")

            add_relationship(
                relationships,
                source_id=endpoint_id,
                target_id=target_id,
                relationship_type="private_endpoint_targets_resource",
                evidence={
                    "connection_name": connection.get("name"),
                    "group_ids": connection.get("group_ids", []),
                    "connection_status": status,
                },
            )

            nodes[endpoint_id]["properties"].setdefault(
                "connections", []
            ).append({
                "target_resource_id": target_id,
                "connection_status": status,
            })

        # Associate private endpoint NICs with discovered NIC resources.
        for nic_id in endpoint.get("network_interfaces", []):

            add_relationship(
                relationships,
                source_id=endpoint_id,
                target_id=nic_id,
                relationship_type="uses_network_interface",
                evidence="NIC ID listed by private endpoint discovery.",
            )


def discover_dns_relationships(snapshot, nodes, relationships):
    """
    Model private DNS zones, A records and VNet links.

    An A record is associated with a private endpoint only
    when its IPv4 address matches a discovered endpoint IP.

    This is an inferred association, not runtime DNS verification.
    """

    results = snapshot["discovery_results"]

    zones = results.get(
        "private_dns", {}
    ).get("private_dns_zones", [])

    # Build an IP-to-private-endpoint lookup.
    endpoint_ip_lookup = {}

    endpoints = results.get(
        "private_endpoints", {}
    ).get("private_endpoints", [])

    for endpoint in endpoints:

        endpoint_id = None

        for node_id, node in nodes.items():

            if (
                node["name"] == endpoint.get("name")
                and node["type"] == "Microsoft.Network/privateEndpoints"
            ):
                endpoint_id = node_id
                break

        if not endpoint_id:
            continue

        for ip_config in endpoint.get("private_ip_addresses", []):

            ip_address = ip_config.get("private_ip_address")

            if ip_address:
                endpoint_ip_lookup.setdefault(
                    ip_address, []
                ).append(endpoint_id)

    for zone in zones:

        zone_id = zone.get("id")

        if not zone_id:
            continue

        add_node(
            nodes,
            zone_id,
            "Microsoft.Network/privateDnsZones",
            zone.get("name"),
            {
                "location": zone.get("location"),
                "number_of_record_sets": zone.get(
                    "number_of_record_sets"
                ),
            },
        )

        # Discover VNet links.
        for link in zone.get("virtual_network_links", []):

            vnet_id = link.get("virtual_network_id")

            add_relationship(
                relationships,
                source_id=zone_id,
                target_id=vnet_id,
                relationship_type="linked_to_vnet",
                evidence={
                    "link_name": link.get("name"),
                    "link_state": link.get("link_state"),
                    "registration_enabled": link.get(
                        "registration_enabled"
                    ),
                },
            )

        # Discover DNS records.
        for record in zone.get("records", []):

            record_name = record.get("name")
            record_type = record.get("record_type")

            record_id = f"{zone_id}/recordsets/{record_name}"

            add_node(
                nodes,
                record_id,
                f"DNS/{record_type}",
                record.get("fqdn") or record_name,
                {
                    "zone": zone.get("name"),
                    "ttl": record.get("ttl"),
                    "record_type": record_type,
                    "a_records": record.get("a_records", []),
                },
            )

            add_relationship(
                relationships,
                source_id=record_id,
                target_id=zone_id,
                relationship_type="belongs_to_dns_zone",
                evidence="Record was discovered inside this DNS zone.",
            )

            # Match A record IP addresses against endpoint IPs.
            for a_record in record.get("a_records", []):

                ip_address = a_record.get("ipv4_address")

                matching_endpoints = endpoint_ip_lookup.get(
                    ip_address, []
                )

                for endpoint_id in matching_endpoints:

                    add_relationship(
                        relationships,
                        source_id=record_id,
                        target_id=endpoint_id,
                        relationship_type="resolves_to_private_endpoint_ip",
                        evidence={
                            "dns_ipv4_address": ip_address,
                            "private_endpoint_ip_match": True,
                        },
                        evidence_type="inferred",
                    )


def discover_database_relationships(nodes, relationships):
    """
    Associate SQL database resources with their parent SQL server.

    The relationship is derived from the Azure resource ID structure.
    """

    database_nodes = [
        node for node in nodes.values()
        if node["type"] == "Microsoft.Sql/servers/databases"
    ]

    for database in database_nodes:

        database_id = database["id"]
        marker = "/databases/"

        if marker not in database_id:
            continue

        server_id = database_id.split(marker, 1)[0]

        if server_id not in nodes:
            continue

        add_relationship(
            relationships,
            source_id=database_id,
            target_id=server_id,
            relationship_type="hosted_on_sql_server",
            evidence=(
                "Parent SQL server ID derived from the database "
                "Azure resource ID."
            ),
        )


def build_environment_model(snapshot):
    """
    Construct the unified environment intelligence model.
    """

    nodes = {}
    relationships = []

    # Create resource nodes first so other modules can reference them.
    discover_resource_nodes(snapshot, nodes)

    # Enrich the resource inventory with discovered relationships.
    discover_application_relationships(
        snapshot, nodes, relationships
    )

    # Add application dependencies from actual configuration values.
    discover_configured_application_relationships(
        snapshot, nodes, relationships
    )

    discover_network_relationships(
        snapshot, nodes, relationships
    )

    discover_private_endpoint_relationships(
        snapshot, nodes, relationships
    )

    discover_dns_relationships(
        snapshot, nodes, relationships
    )

    discover_database_relationships(
        nodes, relationships
    )

    model = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_snapshot_generated_at": snapshot.get(
            "generated_at"
        ),
        "source_discovery_status": snapshot.get(
            "discovery_status"
        ),
        "model_status": "completed",
        "summary": {
            "node_count": len(nodes),
            "relationship_count": len(relationships),
        },
        "nodes": list(nodes.values()),
        "relationships": relationships,
        "limitations": [
            (
                "Application dependencies are derived from "
                "allowlisted App Service configuration values. "
                "They establish configured dependencies, not "
                "successful runtime communication."
            ),
            (
                "Runtime connectivity tests are not yet stored "
                "in the environment snapshot."
            ),
            (
                "A DNS-to-private-endpoint relationship based on "
                "matching IP addresses establishes an IP match, "
                "not proof of runtime DNS resolution."
            ),
        ],
    }

    return model


def save_environment_model(model):
    """
    Save the environment intelligence model as JSON.
    """

    project_root = Path(__file__).resolve().parents[2]

    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "environment_model.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(
            model,
            file,
            indent=4,
            default=str,
        )

    return output_file


def run_environment_model():
    """
    Load the discovery snapshot, build the model and save it.
    """

    print("=" * 60)
    print("InfraGuardian AI - Environment Intelligence")
    print("=" * 60)

    snapshot = load_environment_snapshot()

    print("\nBuilding environment model...")

    model = build_environment_model(snapshot)

    output_file = save_environment_model(model)

    print("\nEnvironment model completed.")
    print(f"Nodes: {model['summary']['node_count']}")
    print(
        "Relationships: "
        f"{model['summary']['relationship_count']}"
    )
    print(f"Saved to: {output_file}")

    return model


if __name__ == "__main__":
    run_environment_model()
