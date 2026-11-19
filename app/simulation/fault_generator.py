
import argparse
import json
import subprocess
import sys

from pathlib import Path

from app.simulation.fault_validator import validate_fault


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENVIRONMENT_MODEL = PROJECT_ROOT / "output" / "environment_model.json"
GENERATED_FAULT = PROJECT_ROOT / "output" / "generated_fault.json"
STATE_FILE = PROJECT_ROOT / "output" / "fault_injection_state.json"

APP_SETTING_NAMES = [
    "IGAI_FAULT_OPERATION",
    "IGAI_FAULT_PARAMETERS",
    "IGAI_FAULT_ID",
]

APPLICATION_OPERATIONS = {
    "simulate_app_unavailable",
    "simulate_startup_failure",
    "simulate_dependency_timeout",
    "simulate_database_unavailable",
    "simulate_database_authentication_failure",
    "simulate_database_connection_exhaustion",
}


def run_az(arguments):
    """Execute Azure CLI and return parsed JSON when available."""

    result = subprocess.run(
        ["az"] + arguments,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or result.stdout.strip()
        )

    output = result.stdout.strip()

    if not output:
        return None

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return output


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def find_app_services(data):
    """Find App Services in the environment model."""

    found = []
    seen = set()

    def walk(node):
        if isinstance(node, dict):

            resource_type = str(node.get("type", "")).lower()

            resource_id = (
                node.get("id")
                or node.get("resource_id")
                or node.get("resourceId")
            )

            if (
                resource_type == "microsoft.web/sites"
                and resource_id
                and str(resource_id).lower() not in seen
            ):
                seen.add(str(resource_id).lower())
                found.append(node)

            for value in node.values():
                if isinstance(value, (dict, list)):
                    walk(value)

        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return found


def get_app_service(environment, requested_name=None):
    apps = find_app_services(environment)

    if requested_name:
        matches = [
            app for app in apps
            if app.get("name", "").lower() == requested_name.lower()
        ]

        if len(matches) != 1:
            raise ValueError(
                f"Could not uniquely find App Service '{requested_name}'."
            )

        return matches[0]

    if not apps:
        raise ValueError(
            "No App Service was found in the environment model."
        )

    preferred = [
        app for app in apps
        if "customerapp-api" in app.get("name", "").lower()
    ]

    if len(preferred) == 1:
        return preferred[0]

    if len(apps) == 1:
        return apps[0]

    raise ValueError(
        "Multiple App Services were found. Specify --app-name."
    )


def parse_resource_id(resource_id):
    parts = resource_id.strip("/").split("/")

    try:
        resource_group = parts[
            parts.index("resourceGroups") + 1
        ]

        name = parts[
            parts.index("sites") + 1
        ]

    except (ValueError, IndexError):
        raise ValueError(
            f"Invalid App Service resource ID: {resource_id}"
        )

    return resource_group, name


def validate_generated_fault(fault, environment):
    result = validate_fault(fault, environment)

    if not result.get("valid"):
        raise ValueError(
            "Fault validation failed: "
            + json.dumps(result.get("errors", []))
        )

    return result


def inject_application_fault(app_name=None):
    if STATE_FILE.exists():
        raise RuntimeError(
            "An IGAI fault is already recorded. "
            "Rollback it before injecting another fault."
        )

    environment = load_json(ENVIRONMENT_MODEL)
    fault = load_json(GENERATED_FAULT)

    validate_generated_fault(fault, environment)

    operation = fault["operation"]

    if operation not in APPLICATION_OPERATIONS:
        raise ValueError(
            f"Operation '{operation}' cannot be injected "
            "through the Flask application handler. "
            "Choose an application-compatible fault."
        )

    app = get_app_service(environment, app_name)

    resource_group, actual_app_name = parse_resource_id(
        app.get("id") or app.get("resource_id")
    )

    current_settings = run_az([
        "webapp", "config", "appsettings", "list",
        "--resource-group", resource_group,
        "--name", actual_app_name,
        "--output", "json",
    ])

    previous_settings = {
        setting["name"]: setting["value"]
        for setting in current_settings
        if setting["name"] in APP_SETTING_NAMES
    }

    state = {
        "fault_id": fault["fault_id"],
        "operation": operation,
        "app_name": actual_app_name,
        "resource_group": resource_group,
        "resource_id": app.get("id") or app.get("resource_id"),
        "previous_settings": previous_settings,
    }

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with STATE_FILE.open("w", encoding="utf-8") as file:
        json.dump(state, file, indent=4)

    parameters = json.dumps(fault.get("parameters", {}))

    try:
        run_az([
            "webapp", "config", "appsettings", "set",
            "--resource-group", resource_group,
            "--name", actual_app_name,
            "--settings",
            f"IGAI_FAULT_OPERATION={operation}",
            f"IGAI_FAULT_PARAMETERS={parameters}",
            f"IGAI_FAULT_ID={fault['fault_id']}",
            "--output", "none",
        ])

    except Exception:
        STATE_FILE.unlink(missing_ok=True)
        raise

    print("Fault injected successfully.")
    print(f"Fault ID: {fault['fault_id']}")
    print(f"Operation: {operation}")
    print(f"App Service: {actual_app_name}")
    print()
    print("The App Service may restart after its settings change.")
    print("Original settings have been saved for rollback.")


def rollback_application_fault():
    if not STATE_FILE.exists():
        raise FileNotFoundError(
            "No recorded IGAI fault injection was found."
        )

    state = load_json(STATE_FILE)

    resource_group = state["resource_group"]
    app_name = state["app_name"]

    # Remove the IGAI settings first.
    run_az([
        "webapp", "config", "appsettings", "delete",
        "--resource-group", resource_group,
        "--name", app_name,
        "--setting-names",
        *APP_SETTING_NAMES,
        "--output", "none",
    ])

    # Restore any settings that existed before injection.
    previous = state.get("previous_settings", {})

    if previous:
        settings = [
            f"{key}={value}"
            for key, value in previous.items()
        ]

        run_az([
            "webapp", "config", "appsettings", "set",
            "--resource-group", resource_group,
            "--name", app_name,
            "--settings",
            *settings,
            "--output", "none",
        ])

    STATE_FILE.unlink()

    print("Fault rollback completed.")
    print(f"Fault ID: {state['fault_id']}")
    print(f"App Service: {app_name}")
    print("Original application settings restored.")


def main():
    parser = argparse.ArgumentParser(
        description="InfraGuardian AI fault injector"
    )

    parser.add_argument(
        "action",
        choices=["inject", "rollback"],
    )

    parser.add_argument(
        "--app-name",
        help="App Service name when the environment has multiple apps.",
    )

    args = parser.parse_args()

    try:
        if args.action == "inject":
            inject_application_fault(args.app_name)

        elif args.action == "rollback":
            rollback_application_fault()

    except Exception as error:
        print(f"ERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
