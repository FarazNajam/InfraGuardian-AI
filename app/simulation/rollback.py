
import json

from datetime import datetime, timezone
from pathlib import Path

from azure.mgmt.network import NetworkManagementClient

from app.providers.azure_provider import (
    load_settings,
    get_azure_credential,
)


def load_fault_state(fault_id):
    """
    Load the saved original state for a fault.
    """

    project_root = Path(__file__).resolve().parents[2]

    state_file = (
        project_root
        / "output"
        / "fault_states"
        / f"{fault_id}.json"
    )

    if not state_file.exists():
        raise FileNotFoundError(
            f"No state file found for {fault_id}"
        )

    with state_file.open("r", encoding="utf-8") as file:
        return json.load(file), state_file


def normalize(value):
    """
    Normalize Azure SDK values for comparison.
    """

    if value is None:
        return None

    if hasattr(value, "value"):
        return str(value.value).lower()

    return str(value).lower()


def verify_fault_rule(rule, planned_operation):
    """
    Confirm that the existing rule matches the
    fault operation recorded by InfraGuardian.
    """

    checks = {
        "name": rule.name == planned_operation["rule_name"],
        "priority": rule.priority == planned_operation["priority"],
        "direction": (
            normalize(rule.direction)
            == normalize(planned_operation["direction"])
        ),
        "access": (
            normalize(rule.access)
            == normalize(planned_operation["access"])
        ),
        "protocol": (
            normalize(rule.protocol)
            == normalize(planned_operation["protocol"])
        ),
        "destination_address": (
            normalize(rule.destination_address_prefix)
            == normalize(
                planned_operation["destination_address_prefix"]
            )
        ),
        "destination_port": (
            normalize(rule.destination_port_range)
            == normalize(
                planned_operation["destination_port_range"]
            )
        ),
    }

    failed_checks = [
        name for name, passed in checks.items() if not passed
    ]

    if failed_checks:
        raise ValueError(
            "The current NSG rule does not match the recorded "
            f"fault definition. Failed checks: {failed_checks}"
        )

    return True


def update_fault_state(state, state_file, status):
    """
    Update the local execution record.
    """

    state["execution_status"] = status
    state["last_updated"] = datetime.now(
        timezone.utc
    ).isoformat()

    with state_file.open("w", encoding="utf-8") as file:
        json.dump(state, file, indent=4, default=str)


def rollback_fault(fault_id, execute=False):
    """
    Inspect or roll back a previously applied fault.

    execute=False:
        Read-only rollback dry run.

    execute=True:
        Delete only the verified temporary NSG rule.
    """

    print("\nInfraGuardian - Fault Rollback")
    print("==============================")

    # Step 1: Load original state
    state, state_file = load_fault_state(fault_id)

    if state.get("execution_status") == "rolled_back":
        print("This fault has already been rolled back.")

        return {
            "status": "already_rolled_back",
            "azure_modified": False,
        }

    if state.get("execution_status") != "fault_applied":
        raise ValueError(
            "Rollback requires a fault record with "
            "execution_status='fault_applied'. "
            f"Current status: {state.get('execution_status')}"
        )

    resource = state["resource"]
    operation = state["planned_operation"]

    nsg_name = resource["name"]
    resource_id = resource["id"]
    rule_name = operation["rule_name"]

    # Step 2: Connect to Azure
    settings = load_settings()

    subscription_id = settings["azure"]["subscription_id"]
    resource_group = settings["azure"]["resource_group"]

    credential = get_azure_credential()

    client = NetworkManagementClient(
        credential=credential,
        subscription_id=subscription_id,
    )

    # Step 3: Retrieve current NSG
    print(f"\nInspecting NSG: {nsg_name}")

    nsg = client.network_security_groups.get(
        resource_group_name=resource_group,
        network_security_group_name=nsg_name,
    )

    # Confirm this is the original resource
    if nsg.id.lower() != resource_id.lower():
        raise ValueError(
            "NSG resource ID does not match the saved state."
        )

    # Step 4: Find the exact temporary rule
    existing_rules = nsg.security_rules or []

    matching_rules = [
        rule for rule in existing_rules
        if rule.name.lower() == rule_name.lower()
    ]

    if not matching_rules:
        raise ValueError(
            f"Temporary rule {rule_name} was not found. "
            "No changes have been made."
        )

    if len(matching_rules) != 1:
        raise ValueError(
            "Unexpected duplicate matching rules. "
            "Manual inspection is required."
        )

    fault_rule = matching_rules[0]

    # Step 5: Verify the rule matches our fault record
    verify_fault_rule(fault_rule, operation)

    print("\nFault rule verified.")
    print(f"Rule: {fault_rule.name}")
    print(f"Priority: {fault_rule.priority}")

    # Step 6: Dry-run mode
    if not execute:
        print("\nROLLBACK DRY RUN")
        print("==============================")
        print(f"Target NSG: {nsg_name}")
        print(f"Rule to remove: {rule_name}")
        print("Validation successful.")
        print("No Azure configuration was modified.")

        return {
            "status": "rollback_dry_run_successful",
            "fault_id": fault_id,
            "rule": rule_name,
            "azure_modified": False,
        }

    # Step 7: Delete only the verified child rule
    print("\nExecuting rollback...")

    poller = client.security_rules.begin_delete(
        resource_group_name=resource_group,
        network_security_group_name=nsg_name,
        security_rule_name=rule_name,
    )

    poller.result()

    # Step 8: Verify the rule was removed
    updated_nsg = client.network_security_groups.get(
        resource_group_name=resource_group,
        network_security_group_name=nsg_name,
    )

    remaining_rules = updated_nsg.security_rules or []

    still_exists = any(
        rule.name.lower() == rule_name.lower()
        for rule in remaining_rules
    )

    if still_exists:
        raise RuntimeError(
            "Rollback operation completed, but the rule "
            "is still present in the NSG."
        )

    # Step 9: Update the local execution record
    update_fault_state(
        state,
        state_file,
        "rolled_back",
    )

    print("\nRollback successful.")
    print("Temporary rule removed.")
    print("Original custom rules were not replaced.")

    return {
        "status": "rolled_back",
        "fault_id": fault_id,
        "rule": rule_name,
        "azure_modified": True,
    }


if __name__ == "__main__":

    result = rollback_fault(
        fault_id="FAULT-001",
        execute=False,
    )

    print("\nResult:")
    print(result)
