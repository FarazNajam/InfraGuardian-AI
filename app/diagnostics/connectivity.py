
from azure.mgmt.network import NetworkManagementClient

from app.providers.azure_provider import (
    get_azure_credential,
    load_settings
)


def discover_nsgs():

    settings = load_settings()

    subscription_id = settings["azure"]["subscription_id"]
    resource_group = settings["azure"]["resource_group"]

    client = NetworkManagementClient(
        get_azure_credential(),
        subscription_id
    )

    nsgs = client.network_security_groups.list(resource_group)

    inventory = []

    for nsg in nsgs:

        rules = []

        all_rules = (
            list(nsg.security_rules or [])
            + list(nsg.default_security_rules or [])
        )

        for rule in all_rules:

            rules.append({
                "name": rule.name,
                "priority": rule.priority,
                "direction": (
                    str(rule.direction) if rule.direction else None
                ),
                "access": (
                    str(rule.access) if rule.access else None
                ),
                "protocol": (
                    str(rule.protocol) if rule.protocol else None
                ),
                "source_address_prefix": rule.source_address_prefix,
                "source_address_prefixes": rule.source_address_prefixes,
                "source_port_range": rule.source_port_range,
                "source_port_ranges": rule.source_port_ranges,
                "destination_address_prefix": (
                    rule.destination_address_prefix
                ),
                "destination_address_prefixes": (
                    rule.destination_address_prefixes
                ),
                "destination_port_range": (
                    rule.destination_port_range
                ),
                "destination_port_ranges": (
                    rule.destination_port_ranges
                )
            })

        inventory.append({
            "name": nsg.name,
            "location": nsg.location,
            "security_rules": rules
        })

    return {
        "resource_group": resource_group,
        "nsg_count": len(inventory),
        "network_security_groups": inventory
    }
