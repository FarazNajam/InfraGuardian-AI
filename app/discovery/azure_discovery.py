
from app.providers.azure_provider import (
    get_resource_client,
    load_settings
)


def discover_resource_group():
    """
    Discover Azure resources within the configured resource group.

    Returns resource metadata without retrieving secret values.
    """

    settings = load_settings()
    resource_group = settings["azure"]["resource_group"]

    client = get_resource_client()

    print(f"Discovering resources in: {resource_group}")

    resources = client.resources.list_by_resource_group(
        resource_group
    )

    inventory = []

    for resource in resources:
        inventory.append({
            "id": resource.id,
            "name": resource.name,
            "type": resource.type,
            "location": resource.location,
            "kind": resource.kind,
            "tags": resource.tags
        })

    return {
        "subscription_id": settings["azure"]["subscription_id"],
        "resource_group": resource_group,
        "resource_count": len(inventory),
        "resources": inventory
    }
