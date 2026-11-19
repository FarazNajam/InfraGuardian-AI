
import json
from datetime import datetime, timezone
from pathlib import Path

from app.discovery.azure_discovery import discover_resource_group
from app.discovery.app_service_discovery import discover_app_services
from app.discovery.network_discovery import discover_network
from app.discovery.nsg_discovery import discover_nsgs
from app.discovery.private_endpoint_discovery import (
    discover_private_endpoints,
)
from app.discovery.dns_discovery import discover_private_dns
from app.discovery.application_config_discovery import (
    discover_application_config,
)


def discover_environment():
    """
    Run all Azure discovery modules and combine their results.

    Each module executes independently so that a failure
    does not prevent the remaining modules from running.
    """

    discovery_tasks = {
        "azure_resources": discover_resource_group,
        "app_services": discover_app_services,
        "network": discover_network,
        "network_security_groups": discover_nsgs,
        "private_endpoints": discover_private_endpoints,
        "private_dns": discover_private_dns,
        "application_config": discover_application_config,
    }

    environment = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "discovery_status": "completed",
        "discovery_results": {},
        "discovery_errors": [],
    }

    print("=" * 60)
    print("InfraGuardian AI - Unified Environment Discovery")
    print("=" * 60)

    for discovery_name, discovery_function in discovery_tasks.items():

        print(f"\nRunning discovery: {discovery_name}")

        try:
            result = discovery_function()

            environment["discovery_results"][discovery_name] = result

            module_status = (
                result.get("status", "completed")
                if isinstance(result, dict)
                else "completed"
            )

            if module_status == "failed":
                environment["discovery_errors"].append({
                    "module": discovery_name,
                    "error_type": "DiscoveryFailure",
                    "message": "Discovery module returned failed status.",
                })

            print(f"Status: {module_status} - {discovery_name}")

        except Exception as error:

            error_details = {
                "module": discovery_name,
                "error_type": type(error).__name__,
                "message": str(error),
            }

            environment["discovery_errors"].append(error_details)

            print(f"Failed: {discovery_name}")
            print(f"Error: {type(error).__name__}: {error}")

    if environment["discovery_errors"]:
        if environment["discovery_results"]:
            environment["discovery_status"] = "partial"
        else:
            environment["discovery_status"] = "failed"

    return environment


def save_environment_snapshot(environment):
    """
    Save unified discovery results as JSON.
    """

    project_root = Path(__file__).resolve().parents[2]

    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "environment_snapshot.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(
            environment,
            file,
            indent=4,
            default=str,
        )

    print("\n" + "=" * 60)
    print("Environment Discovery Summary")
    print("=" * 60)

    print(f"Status: {environment['discovery_status']}")
    print(
        f"Successful results: "
        f"{len(environment['discovery_results'])}"
    )
    print(
        f"Errors: {len(environment['discovery_errors'])}"
    )
    print(f"Snapshot saved to: {output_file}")

    return output_file


def run_environment_discovery():
    """
    Main entry point.
    """

    environment = discover_environment()

    save_environment_snapshot(environment)

    return environment


if __name__ == "__main__":
    run_environment_discovery()
