
import socket
from datetime import datetime, timezone


def check_tcp(target, port, timeout=5, target_name=None):
    """
    Test TCP connectivity to a hostname or IP address.

    Args:
        target: Hostname or IP address.
        port: Destination TCP port.
        timeout: Connection timeout in seconds.
        target_name: Friendly name for the target service.

    Returns:
        Structured observation result.
    """

    started_at = datetime.now(timezone.utc)

    try:
        with socket.create_connection(
            (target, port),
            timeout=timeout,
        ):
            status = "healthy"
            message = (
                f"Connectivity to {target_name or target} "
                "is operational."
            )

    except (socket.timeout, TimeoutError):
        status = "failed"
        message = (
            f"{target_name or target} is not responding "
            "to connectivity checks."
        )

    except OSError:
        status = "failed"
        message = (
            f"Connectivity to {target_name or target} "
            "could not be established."
        )

    completed_at = datetime.now(timezone.utc)

    return {
        "check_type": "tcp",
        "target": target,
        "target_name": target_name or target,
        "port": port,
        "status": status,
        "message": message,
        "observed_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
    }


if __name__ == "__main__":

    result = check_tcp(
        target="p-auea-customerapp-sqlserver.database.windows.net",
        port=1433,
        target_name="Customer Database",
    )

    print("\nConnectivity Observation")
    print("========================")
    print(f"Target: {result['target_name']}")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
