from copy import deepcopy


# One source of truth for all supported fault operations.
#
# resource_category determines which discovered Azure resources can
# receive the operation. Parameters are fixed templates at this stage.

SUPPORTED_OPERATIONS = {
    "simulate_app_unavailable": {
        "name": "Simulate App Unavailable",
        "category": "availability",
        "resource_category": "app_service",
        "description": "Simulate an App Service becoming unavailable.",
        "parameters": {
            "failure_mode": "application_unavailable",
            "http_status": 503,
        },
        "expected_impact": "Application requests fail with HTTP 503.",
        "rollback_operation": "restore_app_availability",
        "rollback_description": (
            "Restore the original application availability and verify "
            "normal service operation."
        ),
    },
    "simulate_startup_failure": {
        "name": "Simulate Startup Failure",
        "category": "application",
        "resource_category": "app_service",
        "description": "Simulate an App Service application failing to start.",
        "parameters": {
            "failure_mode": "startup_failure",
        },
        "expected_impact": "The application fails to start or remains unavailable.",
        "rollback_operation": "restore_application_configuration",
        "rollback_description": (
            "Restore the original application configuration and verify startup."
        ),
    },
    "simulate_dependency_timeout": {
        "name": "Simulate Dependency Timeout",
        "category": "connectivity",
        "resource_category": "app_service",
        "description": "Simulate an application dependency timing out.",
        "parameters": {
            "failure_mode": "dependency_timeout",
            "timeout_seconds": 30,
        },
        "expected_impact": "Application requests experience dependency timeouts.",
        "rollback_operation": "restore_dependency_connectivity",
        "rollback_description": (
            "Restore dependency connectivity and verify successful requests."
        ),
    },
    "simulate_database_unavailable": {
        "name": "Simulate Database Unavailable",
        "category": "availability",
        "resource_category": "sql",
        "description": "Simulate a database becoming unavailable.",
        "parameters": {
            "failure_mode": "database_unavailable",
        },
        "expected_impact": "Applications cannot establish database connections.",
        "rollback_operation": "restore_database_availability",
        "rollback_description": (
            "Restore database availability and verify database connectivity."
        ),
    },
    "simulate_database_authentication_failure": {
        "name": "Simulate Database Authentication Failure",
        "category": "identity",
        "resource_category": "sql",
        "description": "Simulate database authentication failures.",
        "parameters": {
            "failure_mode": "authentication_failure",
            "sql_error": 18456,
        },
        "expected_impact": "Database authentication attempts fail.",
        "rollback_operation": "restore_database_authentication",
        "rollback_description": (
            "Restore valid database authentication and verify access."
        ),
    },
    "simulate_database_connection_exhaustion": {
        "name": "Simulate Database Connection Exhaustion",
        "category": "performance",
        "resource_category": "sql",
        "description": "Simulate database connection pool exhaustion.",
        "parameters": {
            "failure_mode": "connection_exhaustion",
        },
        "expected_impact": "New database connections fail or are delayed.",
        "rollback_operation": "restore_database_connections",
        "rollback_description": (
            "Restore database connection capacity and verify connectivity."
        ),
    },
    "simulate_storage_authorization_failure": {
        "name": "Simulate Storage Authorization Failure",
        "category": "identity",
        "resource_category": "storage",
        "description": "Simulate an authorization failure against Storage.",
        "parameters": {
            "failure_mode": "authorization_failure",
            "http_status": 403,
        },
        "expected_impact": "Storage requests fail with HTTP 403.",
        "rollback_operation": "restore_storage_authorization",
        "rollback_description": (
            "Restore the original storage permissions and verify access."
        ),
    },
    "simulate_storage_unavailable": {
        "name": "Simulate Storage Unavailable",
        "category": "availability",
        "resource_category": "storage",
        "description": "Simulate a Storage service becoming unavailable.",
        "parameters": {
            "failure_mode": "service_unavailable",
            "http_status": 503,
        },
        "expected_impact": "Storage operations fail with service unavailable errors.",
        "rollback_operation": "restore_storage_availability",
        "rollback_description": (
            "Restore storage availability and verify normal operations."
        ),
    },
    "simulate_secret_access_denied": {
        "name": "Simulate Key Vault Secret Access Denied",
        "category": "identity",
        "resource_category": "key_vault",
        "description": "Simulate an application being denied access to a Key Vault secret.",
        "parameters": {
            "failure_mode": "access_denied",
            "http_status": 403,
        },
        "expected_impact": "Secret retrieval attempts fail with HTTP 403.",
        "rollback_operation": "restore_secret_access",
        "rollback_description": (
            "Restore the original secret permissions and verify secret retrieval."
        ),
    },
    "simulate_secret_reference_failure": {
        "name": "Simulate Key Vault Secret Reference Failure",
        "category": "configuration",
        "resource_category": "key_vault",
        "description": "Simulate an invalid Key Vault secret reference.",
        "parameters": {
            "failure_mode": "invalid_secret_reference",
        },
        "expected_impact": "Applications fail to retrieve the expected secret.",
        "rollback_operation": "restore_secret_reference",
        "rollback_description": (
            "Restore the valid secret reference and verify retrieval."
        ),
    },
    "simulate_message_delivery_failure": {
        "name": "Simulate Service Bus Message Delivery Failure",
        "category": "application",
        "resource_category": "service_bus",
        "description": "Simulate messages failing to reach their consumers.",
        "parameters": {
            "failure_mode": "message_delivery_failure",
        },
        "expected_impact": "Messages are not successfully delivered to consumers.",
        "rollback_operation": "restore_message_delivery",
        "rollback_description": (
            "Restore message delivery and verify consumer processing."
        ),
    },
    "simulate_service_bus_unavailable": {
        "name": "Simulate Service Bus Unavailable",
        "category": "availability",
        "resource_category": "service_bus",
        "description": "Simulate Azure Service Bus becoming unavailable.",
        "parameters": {
            "failure_mode": "service_unavailable",
        },
        "expected_impact": "Applications cannot communicate with Service Bus.",
        "rollback_operation": "restore_service_bus_availability",
        "rollback_description": (
            "Restore Service Bus availability and verify connectivity."
        ),
    },
    "simulate_network_connectivity_failure": {
        "name": "Simulate Network Connectivity Failure",
        "category": "networking",
        "resource_category": "network",
        "description": "Simulate a network connectivity failure.",
        "parameters": {
            "failure_mode": "connectivity_failure",
        },
        "expected_impact": "The affected service cannot reach its network dependency.",
        "rollback_operation": "restore_network_connectivity",
        "rollback_description": (
            "Restore the original network connectivity and verify traffic flow."
        ),
    },
    "simulate_nsg_rule_conflict": {
        "name": "Simulate NSG Rule Conflict",
        "category": "networking",
        "resource_category": "network",
        "description": "Simulate a conflicting network security rule.",
        "parameters": {
            "failure_mode": "security_rule_conflict",
        },
        "expected_impact": "Network traffic is blocked or unexpectedly permitted.",
        "rollback_operation": "restore_nsg_rules",
        "rollback_description": (
            "Restore the original NSG rules and verify expected traffic flow."
        ),
    },
    "simulate_dns_resolution_failure": {
        "name": "Simulate DNS Resolution Failure",
        "category": "networking",
        "resource_category": "dns",
        "description": "Simulate DNS resolution failure for a DNS record.",
        "parameters": {
            "failure_mode": "dns_failure",
        },
        "expected_impact": "Clients cannot resolve the affected DNS name.",
        "rollback_operation": "restore_dns_resolution",
        "rollback_description": (
            "Restore the original DNS record and verify name resolution."
        ),
    },
    "simulate_missing_configuration": {
        "name": "Simulate Missing Configuration",
        "category": "configuration",
        "resource_category": "app_configuration",
        "description": "Simulate an application configuration value being unavailable.",
        "parameters": {
            "failure_mode": "missing_configuration",
        },
        "expected_impact": "Applications cannot retrieve the required configuration value.",
        "rollback_operation": "restore_configuration",
        "rollback_description": (
            "Restore the original configuration value and verify retrieval."
        ),
    },
    "simulate_configuration_unavailable": {
        "name": "Simulate Configuration Service Unavailable",
        "category": "availability",
        "resource_category": "app_configuration",
        "description": "Simulate Azure App Configuration becoming unavailable.",
        "parameters": {
            "failure_mode": "service_unavailable",
        },
        "expected_impact": "Applications cannot retrieve configuration settings.",
        "rollback_operation": "restore_configuration_availability",
        "rollback_description": (
            "Restore configuration service availability and verify retrieval."
        ),
    },
}


def get_operation(operation_name):
    """Return a copy of an operation definition."""
    operation = SUPPORTED_OPERATIONS.get(operation_name)

    if operation is None:
        return None

    return deepcopy(operation)


def get_operations_for_resource(resource_category):
    """Return operations compatible with a resource category."""
    return {
        name: deepcopy(definition)
        for name, definition in SUPPORTED_OPERATIONS.items()
        if definition["resource_category"] == resource_category
    }