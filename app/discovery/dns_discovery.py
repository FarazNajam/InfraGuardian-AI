
from azure.mgmt.privatedns import PrivateDnsManagementClient

from app.providers.azure_provider import (
    get_azure_credential,
    load_settings
)


def get_record_type(record):
    """
    Determine DNS record type from populated record properties.
    """

    record_types = {
        "A": "a_records",
        "AAAA": "aaaa_records",
        "CNAME": "cname_record",
        "MX": "mx_records",
        "NS": "ns_records",
        "PTR": "ptr_records",
        "SOA": "soa_record",
        "SRV": "srv_records",
        "TXT": "txt_records"
    }

    for record_type, property_name in record_types.items():

        if getattr(record, property_name, None):
            return record_type

    return "UNKNOWN"


def discover_private_dns():
    """
    Discover Azure Private DNS zones, records and VNet links.

    Retrieves:
    - Private DNS zone names and resource IDs
    - DNS record names, types and TTLs
    - A record IPv4 addresses
    - Virtual network links and their states

    This function is read-only.
    """

    settings = load_settings()

    subscription_id = settings["azure"]["subscription_id"]
    resource_group = settings["azure"]["resource_group"]

    credential = get_azure_credential()

    client = PrivateDnsManagementClient(
        credential,
        subscription_id
    )

    zones = client.private_zones.list_by_resource_group(
        resource_group
    )

    inventory = []

    for zone in zones:

        # Discover DNS record sets in this zone
        record_sets = client.record_sets.list(
            resource_group,
            zone.name
        )

        records = []

        for record in record_sets:

            # Determine record type from populated properties
            record_type = get_record_type(record)

            # Extract IPv4 addresses from A records
            a_records = []

            for a_record in record.a_records or []:

                a_records.append({
                    "ipv4_address": a_record.ipv4_address
                })

            records.append({
                "name": record.name,
                "fqdn": record.fqdn,
                "ttl": record.ttl,
                "record_type": record_type,
                "a_records": a_records
            })

        # Discover virtual network links
        links = client.virtual_network_links.list(
            resource_group,
            zone.name
        )

        virtual_network_links = []

        for link in links:

            virtual_network_links.append({
                "name": link.name,
                "virtual_network_id": (
                    link.virtual_network.id
                    if link.virtual_network else None
                ),
                "registration_enabled": link.registration_enabled,
                "link_state": link.virtual_network_link_state
            })

        # Build DNS zone inventory
        inventory.append({
            "name": zone.name,
            "id": zone.id,
            "location": zone.location,
            "number_of_record_sets": len(records),
            "records": records,
            "virtual_network_links": virtual_network_links
        })

    return {
        "resource_group": resource_group,
        "private_dns_zone_count": len(inventory),
        "private_dns_zones": inventory
    }
