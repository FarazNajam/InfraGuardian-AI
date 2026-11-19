
import json
from pathlib import Path

from app.discovery.azure_discovery import discover_resource_group


def main():

    print("=" * 55)
    print("InfraGuardian AI - Environment Discovery")
    print("=" * 55)

    inventory = discover_resource_group()

    print(f"\nResources discovered: {inventory['resource_count']}")

    for resource in inventory["resources"]:
        print(
            f"{resource['name']} "
            f"| {resource['type']} "
            f"| {resource['location']}"
        )

    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "output"

    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "azure_inventory.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(inventory, file, indent=4)

    print(f"\nInventory saved to: {output_file}")


if __name__ == "__main__":
    main()
