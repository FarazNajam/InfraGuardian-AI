import json
from pathlib import Path

from app.simulation.operation_registry import get_operation


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENVIRONMENT_MODEL = (
    PROJECT_ROOT / "output" / "environment_model.json"
)

GENERATED_FAULT = (
    PROJECT_ROOT / "output" / "generated_fault.json"
)


REQUIRED_FIELDS = [
    "fault_id",
    "generated_at",
    "category",
    "operation",
    "name",
    "description",
    "target",
    "parameters",
    "expected_impact",
    "preconditions",
    "rollback",
    "requires_approval",
    "execution_mode",
    "status",
]


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def classify_resource(resource):
    resource_type = str(resource.get("type", "")).lower()

    if resource_type.startswith("microsoft.web/sites"):
        return "app_service"

    if resource_type.startswith(
        (
            "microsoft.sql/servers",
            "microsoft.sql/managedinstances",
            "microsoft.dbforpostgresql/",
        )
    ):
        return "sql"

    if resource_type.startswith("microsoft.storage/storageaccounts"):
        return "storage"

    if resource_type.startswith("microsoft.keyvault/vaults"):
        return "key_vault"

    if resource_type.startswith("microsoft.servicebus/namespaces"):
        return "service_bus"

    if resource_type in (
        "microsoft.network/networksecuritygroups",
        "microsoft.network/virtualnetworks",
        "microsoft.network/virtualnetworks/subnets",
        "microsoft.network/privatednszones",
        "microsoft.network/privatednszones/virtualnetworklinks",
    ):
        return "network"

    if resource_type in (
        "dns/a",
        "dns/aaaa",
        "dns/cname",
        "microsoft.network/privatednszones/a",
        "microsoft.network/privatednszones/aaaa",
        "microsoft.network/privatednszones/cname",
    ):
        return "dns"

    if resource_type.startswith("microsoft.appconfiguration/configurationstores"):
        return "app_configuration"

    return None


def get_resource_id(resource):
    return (
        resource.get("id")
        or resource.get("resource_id")
        or resource.get("resourceId")
    )


def find_resources(data):
    """
    Recursively discover resources in the environment model.
    """

    resources = []

    def walk(node):
        if isinstance(node, dict):

            resource_type = node.get("type")
            resource_name = node.get("name")
            resource_id = get_resource_id(node)

            if (
                isinstance(resource_type, str)
                and isinstance(resource_name, str)
                and resource_id
            ):
                resources.append(node)

            for value in node.values():
                if isinstance(value, (dict, list)):
                    walk(value)

        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)

    return resources


def validate_required_fields(fault):
    errors = []

    for field in REQUIRED_FIELDS:
        if field not in fault:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors

    string_fields = [
        "fault_id",
        "generated_at",
        "category",
        "operation",
        "name",
        "description",
        "expected_impact",
        "execution_mode",
        "status",
    ]

    for field in string_fields:
        if not isinstance(fault[field], str) or not fault[field].strip():
            errors.append(f"Field '{field}' must be a non-empty string.")

    return errors


def validate_target(fault, environment, definition):
    errors = []

    target = fault.get("target")

    if not isinstance(target, dict):
        return ["Target must be a JSON object."]

    required_target_fields = [
        "resource_name",
        "resource_type",
        "resource_id",
    ]

    for field in required_target_fields:
        value = target.get(field)

        if not isinstance(value, str) or not value.strip():
            errors.append(
                f"Target field '{field}' must be a non-empty string."
            )

    if errors:
        return errors

    target_id = target["resource_id"].lower()

    resources = find_resources(environment)

    matches = [
        resource
        for resource in resources
        if str(get_resource_id(resource)).lower() == target_id
    ]

    if len(matches) == 0:
        return ["Target resource was not found in the environment model."]

    if len(matches) > 1:
        return ["Target resource ID is not unique in the environment model."]

    resource = matches[0]

    if resource.get("name") != target["resource_name"]:
        errors.append("Target resource name does not match the environment model.")

    if str(resource.get("type", "")).lower() != target["resource_type"].lower():
        errors.append("Target resource type does not match the environment model.")

    actual_category = classify_resource(resource)

    if actual_category != definition["resource_category"]:
        errors.append(
            "Target resource category is incompatible with this operation. "
            f"Expected '{definition['resource_category']}', "
            f"found '{actual_category}'."
        )

    return errors


def validate_parameters(fault, definition):
    errors = []

    parameters = fault.get("parameters")

    if not isinstance(parameters, dict):
        return ["Parameters must be a JSON object."]

    expected_parameters = definition["parameters"]

    if set(parameters.keys()) != set(expected_parameters.keys()):
        errors.append(
            "Parameter names do not match the operation registry. "
            f"Expected: {sorted(expected_parameters.keys())}; "
            f"received: {sorted(parameters.keys())}."
        )
        return errors

    for key, expected_value in expected_parameters.items():

        actual_value = parameters[key]

        # Compare both value and type. This prevents values such as
        # True being accepted where the expected value is integer 1.
        if type(actual_value) is not type(expected_value):
            errors.append(
                f"Parameter '{key}' has an invalid type. "
                f"Expected {type(expected_value).__name__}."
            )
            continue

        if actual_value != expected_value:
            errors.append(
                f"Parameter '{key}' does not match the operation registry."
            )

    return errors


def validate_rollback(fault, definition):
    errors = []

    rollback = fault.get("rollback")

    if not isinstance(rollback, dict):
        return ["Rollback must be a JSON object."]

    expected_operation = definition["rollback_operation"]

    if rollback.get("operation") != expected_operation:
        errors.append(
            "Rollback operation does not match the operation registry. "
            f"Expected '{expected_operation}'."
        )

    description = rollback.get("description")

    if not isinstance(description, str) or not description.strip():
        errors.append("Rollback description must be a non-empty string.")

    return errors


def validate_fault(fault, environment):
    errors = []

    if not isinstance(fault, dict):
        return {
            "valid": False,
            "message": "Generated fault must be a JSON object.",
            "errors": ["Invalid fault structure."],
        }

    errors.extend(validate_required_fields(fault))

    if errors:
        return {
            "valid": False,
            "message": "Fault validation failed.",
            "errors": errors,
        }

    operation_name = fault["operation"]

    definition = get_operation(operation_name)

    if definition is None:
        errors.append(
            f"Unsupported fault operation: {operation_name}"
        )

        return {
            "valid": False,
            "fault_id": fault["fault_id"],
            "message": "Fault validation failed.",
            "errors": errors,
        }

    if fault["category"] != definition["category"]:
        errors.append(
            "Fault category does not match the operation registry."
        )

    if fault["name"] != definition["name"]:
        errors.append(
            "Fault name does not match the operation registry."
        )

    if fault["description"] != definition["description"]:
        errors.append(
            "Fault description does not match the operation registry."
        )

    if fault["expected_impact"] != definition["expected_impact"]:
        errors.append(
            "Expected impact does not match the operation registry."
        )

    if fault["requires_approval"] is not True:
        errors.append("Fault must require explicit human approval.")

    if fault["execution_mode"] != "simulation_only":
        errors.append(
            "Fault execution mode must be 'simulation_only'."
        )

    if fault["status"] != "generated":
        errors.append(
            "Fault status must be 'generated' before validation."
        )

    preconditions = fault["preconditions"]

    if (
        not isinstance(preconditions, list)
        or not preconditions
        or any(
            not isinstance(item, str) or not item.strip()
            for item in preconditions
        )
    ):
        errors.append(
            "Preconditions must be a non-empty list of non-empty strings."
        )

    errors.extend(
        validate_target(fault, environment, definition)
    )

    errors.extend(
        validate_parameters(fault, definition)
    )

    errors.extend(
        validate_rollback(fault, definition)
    )

    if errors:
        return {
            "valid": False,
            "fault_id": fault["fault_id"],
            "operation": operation_name,
            "category": fault["category"],
            "message": "Fault validation failed.",
            "errors": errors,
            "execution_mode": fault["execution_mode"],
            "approval_required": True,
            "execution_authorised": False,
        }

    return {
        "valid": True,
        "fault_id": fault["fault_id"],
        "operation": operation_name,
        "category": fault["category"],
        "target": fault["target"]["resource_name"],
        "target_id": fault["target"]["resource_id"],
        "message": "Fault validation successful.",
        "execution_mode": "simulation_only",
        "approval_required": True,
        "execution_authorised": False,
    }


def main():
    print("InfraGuardian AI - Fault Validator")
    print("==================================")
    print()

    try:
        environment = load_json(ENVIRONMENT_MODEL)
        fault = load_json(GENERATED_FAULT)

        result = validate_fault(fault, environment)

        print("Validation result:")
        print(json.dumps(result, indent=4))

        if not result["valid"]:
            raise SystemExit(1)

    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()