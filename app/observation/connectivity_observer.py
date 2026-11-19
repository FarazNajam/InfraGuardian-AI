
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class FaultDefinition:
    fault_id: str
    name: str
    description: str

    target_resource: str
    target_resource_type: str

    rule_name: str
    priority: int
    direction: str
    access: str
    protocol: str

    source_address_prefix: str
    destination_address_prefix: str
    destination_port_range: str

    expected_impact: str
    rollback_action: str
    requires_approval: bool = True

    def validate(self):
        if not self.fault_id:
            raise ValueError("Fault ID is required")

        if not self.target_resource:
            raise ValueError("Target resource is required")

        if not 100 <= self.priority <= 4096:
            raise ValueError("NSG priority must be between 100 and 4096")

        if self.direction not in ("Inbound", "Outbound"):
            raise ValueError("Invalid NSG direction")

        if self.access not in ("Allow", "Deny"):
            raise ValueError("Invalid NSG access")

        if self.protocol not in ("Tcp", "Udp", "*"):
            raise ValueError("Invalid protocol")

        if not self.requires_approval:
            raise ValueError("Approval is mandatory for this initial engine")

        return True

    def to_dict(self):
        return asdict(self)


SQL_CONNECTIVITY_FAULT = FaultDefinition(
    fault_id="FAULT-001",
    name="Block API to SQL connectivity",
    description="Block outbound SQL traffic from the App Service integration subnet.",

    target_resource="p-auea-customerapp-nsg-appsvc",
    target_resource_type="Microsoft.Network/networkSecurityGroups",

    rule_name="ig-fault-001-block-sql",
    priority=100,
    direction="Outbound",
    access="Deny",
    protocol="Tcp",

    source_address_prefix="*",
    destination_address_prefix="10.0.1.4",
    destination_port_range="1433",

    expected_impact="API cannot establish TCP connectivity to Azure SQL.",
    rollback_action="Remove the temporary NSG security rule.",
    requires_approval=True
)


if __name__ == "__main__":
    fault = SQL_CONNECTIVITY_FAULT

    print("Fault definition")
    print("================")

    fault.validate()

    for key, value in fault.to_dict().items():
        print(f"{key}: {value}")
