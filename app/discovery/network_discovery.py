
from azure.mgmt.network import NetworkManagementClient

from app.providers.azure_provider import (
    get_azure_credential,
    load_settings
)


def discover_network():
    """
    Discover VNet and subnet configuration.
    """

    settings = load_settings()

    subscription_id = settings["azure"]["subscription_id"]
    resource_group = settings["azure"]["resource_group"]

    credential = get_azure_credential()

    client = NetworkManagementClient(
        credential,
        subscription_id
    )

    virtual_networks = client.virtual_networks.list(resource_group)

    inventory = []

    for vnet in virtual_networks:

        vnet_details = client.virtual_networks.get(
            resource_group,
            vnet.name
        )

        subnets = []

        for subnet in vnet_details.subnets or []:

            nsg_id = None

            if subnet.network_security_group:
                nsg_id = subnet.network_security_group.id

            subnets.append({
                "name": subnet.name,
                "id": subnet.id,
                "address_prefix": subnet.address_prefix,
                "address_prefixes": subnet.address_prefixes,
                "network_security_group_id": nsg_id,
                "private_endpoint_network_policies": (
                    str(subnet.private_endpoint_network_policies)
                    if subnet.private_endpoint_network_policies
                    else None
                ),
                "delegations": [
                    delegation.service_name
                    for delegation in subnet.delegations or []
                ]
            })

        inventory.append({
            "name": vnet_details.name,
            "id": vnet_details.id,
            "location": vnet_details.location,
            "address_space": vnet_details.address_space.address_prefixes,
            "subnets": subnets
        })

    return {
        "resource_group": resource_group,
        "vnet_count": len(inventory),
        "virtual_networks": inventory
    }
