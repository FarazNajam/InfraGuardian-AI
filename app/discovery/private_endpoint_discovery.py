
from azure.mgmt.network import NetworkManagementClient

from app.providers.azure_provider import (
    get_azure_credential,
    load_settings
)


def discover_private_endpoints():
    """
    Discover Azure Private Endpoints and their configuration.

    Retrieves:
    - Private endpoint name and location
    - Subnet association
    - Network interface IDs
    - Assigned private IP addresses
    - Private Link connection details
    - Connection approval status
    - Custom DNS configurations

    This function is read-only.
    """

    settings = load_settings()

    subscription_id = settings["azure"]["subscription_id"]
    resource_group = settings["azure"]["resource_group"]

    credential = get_azure_credential()

    client = NetworkManagementClient(
        credential,
        subscription_id
    )

    endpoints = client.private_endpoints.list(resource_group)

    inventory = []

    for endpoint in endpoints:

        # Discover Private Link connections
        connections = []

        for connection in (
            endpoint.private_link_service_connections or []
        ):

            state = connection.private_link_service_connection_state

            connections.append({
                "name": connection.name,
                "target_resource_id": connection.private_link_service_id,
                "group_ids": connection.group_ids,
                "connection_status": (
                    state.status if state else None
                ),
                "connection_description": (
                    state.description if state else None
                )
            })

        # Discover custom DNS configurations
        dns_configs = []

        for dns_config in endpoint.custom_dns_configs or []:

            dns_configs.append({
                "fqdn": dns_config.fqdn,
                "ip_addresses": dns_config.ip_addresses
            })

        # Discover network interfaces and private IP addresses
        network_interfaces = []
        private_ips = []

        for nic_reference in endpoint.network_interfaces or []:

            nic_id = nic_reference.id

            network_interfaces.append(nic_id)

            # Extract NIC name from its Azure resource ID
            nic_name = nic_id.rsplit("/", 1)[-1]

            # Retrieve NIC using resource group and NIC name
            nic = client.network_interfaces.get(
                resource_group,
                nic_name
            )

            # Extract private IP configurations
            for ip_config in nic.ip_configurations or []:

                private_ips.append({
                    "name": ip_config.name,
                    "private_ip_address": ip_config.private_ip_address,
                    "subnet_id": (
                        ip_config.subnet.id
                        if ip_config.subnet else None
                    )
                })

        # Build private endpoint inventory
        inventory.append({
            "name": endpoint.name,
            "location": endpoint.location,

            "subnet_id": (
                endpoint.subnet.id
                if endpoint.subnet else None
            ),

            "network_interfaces": network_interfaces,

            "private_ip_addresses": private_ips,

            "connections": connections,

            "custom_dns_configs": dns_configs
        })

    return {
        "resource_group": resource_group,
        "private_endpoint_count": len(inventory),
        "private_endpoints": inventory
    }
