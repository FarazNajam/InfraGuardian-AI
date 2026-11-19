
from azure.mgmt.web import WebSiteManagementClient

from app.providers.azure_provider import (
    get_azure_credential,
    load_settings,
)


# Only retain these explicitly approved, non-secret settings.
ALLOWED_SETTING_NAMES = {
    "API_URL",
    "DB_SERVER",
    "DB_NAME",
}


def discover_application_config():
    """
    Discover selected non-secret application settings
    from App Services in the configured resource group.

    Only allowlisted settings are retained in the results.
    """

    settings = load_settings()
    resource_group = settings["azure"]["resource_group"]
    subscription_id = settings["azure"]["subscription_id"]

    credential = get_azure_credential()

    client = WebSiteManagementClient(
        credential=credential,
        subscription_id=subscription_id,
    )

    results = {
        "status": "completed",
        "applications": [],
        "errors": [],
    }

    try:
        web_apps = client.web_apps.list_by_resource_group(
            resource_group
        )

        for app in web_apps:

            app_result = {
                "name": app.name,
                "resource_id": app.id,
                "settings": {},
            }

            try:
                response = client.web_apps.list_application_settings(
                    resource_group,
                    app.name,
                )

                # Azure returns the complete settings collection.
                # Retain only the explicitly allowlisted keys.
                properties = response.properties or {}

                app_result["settings"] = {
                    key: properties[key]
                    for key in ALLOWED_SETTING_NAMES
                    if key in properties and properties[key] is not None
                }

                results["applications"].append(app_result)

                print(
                    f"Discovered application configuration: {app.name}"
                )

            except Exception as error:
                results["errors"].append({
                    "application": app.name,
                    "error_type": type(error).__name__,
                    "message": str(error),
                })

        if results["errors"]:
            results["status"] = (
                "partial" if results["applications"] else "failed"
            )

    except Exception as error:
        results["status"] = "failed"
        results["errors"].append({
            "error_type": type(error).__name__,
            "message": str(error),
        })

    return results
