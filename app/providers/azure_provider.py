
import json
from pathlib import Path

from azure.identity import AzureCliCredential
from azure.mgmt.resource.resources import ResourceManagementClient


def load_settings():
    """Load InfraGuardian configuration."""

    project_root = Path(__file__).resolve().parents[2]
    settings_path = project_root / "config" / "settings.json"

    with settings_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_azure_credential():
    """Authenticate using the existing Azure CLI session."""

    return AzureCliCredential()


def get_resource_client():
    """Create an Azure Resource Management client."""

    settings = load_settings()
    subscription_id = settings["azure"]["subscription_id"]

    credential = get_azure_credential()

    return ResourceManagementClient(
        credential=credential,
        subscription_id=subscription_id
    )
