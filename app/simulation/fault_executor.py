
import json

from datetime import datetime, timezone
from pathlib import Path

from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.network.models import SecurityRule

from app.providers.azure_provider import (
    load_settings,
    get_azure_credential,
)

from app.simulation.fault_definition import SQL_CONNECTIVITY_FAULT


def get_state_file(fault_id):
    """Return the saved state file for a fault."""

    project_root = Path(__file__).resolve().parents[2]

    return (
        project_root
        / "output"
        / "fault_states"
        / f"{fault_id}.json"
    )


def load_fault_state(fault_id):
    """Load the original resource state."""

    state_file = get_state_file(fault_id)

    if not state_file.exists():
        raise FileNotFoundError(
            f"No state snapshot found for {fault_id}. "
            "Run the dry-run and state capture first."
        )

    with state_file.open("r", encoding="utf-8") as file:
        state = json.load(file)

    return state, state_file


def save_fault_state(state, state_file):
    """Persist the updated fault execution record."""

    with state_file.open("w", encoding="utf-8") as file:
        json.dump(state, file, indent=4, default=str)


def normalize(value):
    """Normalize Azure SDK values for comparison."""

    if value is None:
        return None

    if hasattr(value, "value"):
        value = value.value

    return str(value).lower()


def validate_saved_operation(state, fault):
    """Ensure the saved plan matches the requested fault."""

    operation = state["planned_operation"]

    expected_values = {
        "rule_name": fault.rule_name,
        "priority": fault.priority,
        "direction": fault.direction,
        "access": fault.access,
        "protocol": fault.protocol,
        "destination_address_prefix":
            fault.destination_address_prefix,
        "destination_port_range":
            fault.destination_port_range,
    }

    for key, expected in expected_values.items():
        if operation.get(key) != expected:
            raise ValueError(
                f"Saved fault plan does not match current "
                f"definition for '{key}'."
            )


def get_azure_network_client():
    """Create the Azure Network Management client."""

    settings = load_settings()

    credential = get_azure_credential()

    client = NetworkManagementClient(
        credential=credential,
        subscription_id=settings["azure"]["subscription_id"],
    )

    return client, settings["azure"]["resource_group"]


def verify_rule(rule, fault):
    """Verify that the created rule matches the fault definition."""

    checks = {
        "name": rule.name == fault.rule_name,
        "priority": rule.priority == fault.priority,
        "direction": (
            normalize(rule.direction)
            == normalize(fault.direction)
        ),
        "access": (
            normalize(rule.access)
            == normalize(fault.access)
        ),
        "protocol": (
            normalize(rule.protocol)
            == normalize(fault.protocol)
        ),
        "destination_address": (
            normalize(rule.destination_address_prefix)
            == normalize(fault.destination_address_prefix)
        ),
        "destination_port": (
            normalize(rule.destination_port_range)
            == normalize(fault.destination_port_range)
        ),
    }

    failed = [
        name for name, passed in checks.items()
        if not passed
    ]

    if failed:
        raise RuntimeError(
            f"Azure rule verification failed: {failed}"
        )


def execute_fault(fault, approval_token=None):
    """
    Apply a fault to Azure.

    Requires an explicit approval token.
    Uses the saved state snapshot and ETag protection.
    """

    print("\nInfraGuardian - Fault Execution")
    print("================================")

    # 1. Validate the fault definition
    fault.validate()

    # 2. Load the original state
    state, state_file = load_fault_state(fault.fault_id)

    if state.get("execution_status") != "state_captured":
        raise ValueError(
            "Fault cannot be executed. Expected state_captured, "
            f"found: {state.get('execution_status')}"
        )

    validate_saved_operation(state, fault)

    resource = state["resource"]

    nsg_name = resource["name"]
    original_resource_id = resource["id"]
    original_etag = resource["etag"]

    # 3. Require explicit approval
    required_approval = f"APPLY {fault.fault_id}"

    if approval_token != required_approval:
        raise PermissionError(
            f"Explicit approval required. "
            f"Enter: {required_approval}"
        )

    # 4. Connect to Azure
    client, resource_group = get_azure_network_client()

    print(f"\nTarget NSG: {nsg_name}")

    # 5. Retrieve the current NSG
    nsg = client.network_security_groups.get(
        resource_group_name=resource_group,
        network_security_group_name=nsg_name,
    )

    # 6. Verify resource identity
    if nsg.id.lower() != original_resource_id.lower():
        raise ValueError(
            "The current NSG resource ID does not match "
            "the saved state."
        )

    # 7. Detect changes since state capture
    if not original_etag:
        raise ValueError(
            "Original ETag is missing. Cannot safely execute."
        )

    if nsg.etag != original_etag:
        raise RuntimeError(
            "NSG configuration has changed since state capture. "
            "Execution cancelled. Capture and review a fresh state."
        )

    print("ETag validation successful.")

    # 8. Check rule name and priority again
    existing_rules = nsg.security_rules or []

    if any(
        rule.name.lower() == fault.rule_name.lower()
        for rule in existing_rules
    ):
        raise ValueError(
            "The proposed rule name already exists."
        )

    if any(
        rule.priority == fault.priority
        for rule in existing_rules
    ):
        raise ValueError(
            "The proposed rule priority is already in use."
        )

    # 9. Construct the Azure NSG rule
    rule_parameters = SecurityRule(
        protocol=fault.protocol,
        source_port_range="*",
        destination_port_range=fault.destination_port_range,
        source_address_prefix=fault.source_address_prefix,
        destination_address_prefix=(
            fault.destination_address_prefix
        ),
        access=fault.access,
        priority=fault.priority,
        direction=fault.direction,
        description=(
            f"Managed by InfraGuardian. "
            f"Fault ID: {fault.fault_id}"
        ),
    )

    print("\nProposed Azure operation:")
    print(f"NSG: {nsg_name}")
    print(f"Rule: {fault.rule_name}")
    print(f"Direction: {fault.direction}")
    print(f"Destination: {fault.destination_address_prefix}")
    print(f"Port: {fault.destination_port_range}")
    print(f"Action: {fault.access}")
    print(f"Priority: {fault.priority}")

    # 10. Apply the fault
    print("\nApplying fault to Azure...")

    poller = client.security_rules.begin_create_or_update(
        resource_group_name=resource_group,
        network_security_group_name=nsg_name,
        security_rule_name=fault.rule_name,
        security_rule_parameters=rule_parameters,
    )

    poller.result()

    # 11. Retrieve and verify the created rule
    created_rule = client.security_rules.get(
        resource_group_name=resource_group,
        network_security_group_name=nsg_name,
        security_rule_name=fault.rule_name,
    )

    verify_rule(created_rule, fault)

    # 12. Update the execution record
    state["execution_status"] = "fault_applied"
    state["applied_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    state["applied_rule"] = {
        "name": created_rule.name,
        "priority": created_rule.priority,
        "direction": str(created_rule.direction),
        "access": str(created_rule.access),
        "protocol": str(created_rule.protocol),
        "destination_address_prefix":
            created_rule.destination_address_prefix,
        "destination_port_range":
            created_rule.destination_port_range,
    }

    save_fault_state(state, state_file)

    print("\nFault successfully applied.")
    print("Azure rule verification successful.")
    print("Execution state updated to fault_applied.")

    return {
        "status": "fault_applied",
        "fault_id": fault.fault_id,
        "target": nsg_name,
        "rule": created_rule.name,
        "azure_modified": True,
    }


if __name__ == "__main__":

    print("WARNING: This operation modifies Azure networking.")
    print(
        "The rule affects outbound SQL traffic from "
        "the shared App Service integration subnet."
    )

    approval = input(
        f"\nTo proceed, type APPLY "
        f"{SQL_CONNECTIVITY_FAULT.fault_id}: "
    ).strip()

    result = execute_fault(
        fault=SQL_CONNECTIVITY_FAULT,
        approval_token=approval,
    )

    print("\nExecution result:")
    print(result)
