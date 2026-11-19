
from azure.mgmt.web import WebSiteManagementClient

from app.providers.azure_provider import (
    get_azure_credential,
    load_settings
)


def discover_app_services():
    """
    Discover App Service configuration without exposing secrets.
    """

    settings = load_settings()

    subscription_id = settings["azure"]["subscription_id"]
    resource_group = settings["azure"]["resource_group"]

    credential = get_azure_credential()

    client = WebSiteManagementClient(
        credential,
        subscription_id
    )

    apps = client.web_apps.list_by_resource_group(resource_group)

    inventory = []

    for app in apps:

        # Only inspect App Services, not other Microsoft.Web resources.
        if app.type.lower() != "microsoft.web/sites":
            continue

        details = client.web_apps.get(
            resource_group,
            app.name
        )

        app_settings = client.web_apps.list_application_settings(
            resource_group,
            app.name
        )

        identity = details.identity
        site_config = details.site_config

        inventory.append({
            "name": details.name,
            "state": details.state,
            "location": details.location,
            "default_host_name": details.default_host_name,
            "virtual_network_subnet_id": (details.virtual_network_subnet_id),
            "https_only": details.https_only,
            "identity": {
                "type": identity.type if identity else None,
                "principal_id": (
                    identity.principal_id if identity else None
                )
            },
            "site_config": {
                "always_on": (
                    site_config.always_on if site_config else None
                ),
                "linux_fx_version": (
                    site_config.linux_fx_version if site_config else None
                )
            },
            "application_setting_names": sorted(
                (app_settings.properties or {}).keys()
            )
        })

    return {
        "resource_group": resource_group,
        "app_service_count": len(inventory),
        "app_services": inventory
    }
