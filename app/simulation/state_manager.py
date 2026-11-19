
import json

from datetime import datetime, timezone
from pathlib import Path


def serialize_rule(rule):
    """
    Convert an Azure NSG security rule into JSON-compatible data.
    """

    fields = [
        "id",
        "name",
        "protocol",
        "source_port_range",
        "source_port_ranges",
        "destination_port_range",
        "destination_port_ranges",
        "source_address_prefix",
        "source_address_prefixes",
        "destination_address_prefix",
        "destination_address_prefixes",
        "access",
        "priority",
        "direction",
        "description",
    ]

    result = {}

    for field in fields:
        value = getattr(rule, field, None)

        if hasattr(value, "value"):
            value = value.value

        result[field] = value

    return result


def capture_nsg_state(nsg, fault):
    """
    Capture the original NSG state before fault execution.

    This function is read-only with respect to Azure.
    """

    project_root = Path(__file__).resolve().parents[2]

    output_dir = project_root / "output" / "fault_states"
    output_dir.mkdir(parents=True, exist_ok=True)

    existing_rules = nsg.security_rules or []

    state = {
        "fault_id": fault.fault_id,
        "captured_at": datetime.now(timezone.utc).isoformat(),

        "resource": {
            "id": nsg.id,
            "name": nsg.name,
            "location": nsg.location,
            "etag": nsg.etag,
            "type": "Microsoft.Network/networkSecurityGroups",
        },

        "original_custom_rules": [
            serialize_rule(rule)
            for rule in existing_rules
        ],

        "planned_operation": {
            "operation": "add_security_rule",
            "rule_name": fault.rule_name,
            "priority": fault.priority,
            "direction": fault.direction,
            "access": fault.access,
            "protocol": fault.protocol,
            "destination_address_prefix":
                fault.destination_address_prefix,
            "destination_port_range":
                fault.destination_port_range,
        },

        "execution_status": "state_captured",
    }

    output_file = output_dir / f"{fault.fault_id}.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(state, file, indent=4, default=str)

    print("\nOriginal resource state captured.")
    print(f"Existing custom rules: {len(existing_rules)}")
    print(f"State file: {output_file}")

    return state


if __name__ == "__main__":
    print(
        "State manager loaded. "
        "Run through the fault executor to capture Azure state."
    )
