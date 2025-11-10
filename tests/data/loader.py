"""
Test data corpus loader utilities.

Provides convenient functions for loading test fixtures from tests/data/:
- Certificate bundles (valid/invalid PEM files)
- Controller exchanges (registration, heartbeat, shutdown)
- Shutdown scenarios (graceful, error, timeout)
- Capability definitions (valid, invalid, adversarial)
"""

import json
from pathlib import Path
from typing import Any

# Base directory for test data (this file is in tests/data/loader.py)
TEST_DATA_DIR = Path(__file__).parent


def load_cert_bundle(bundle_name: str) -> dict[str, Path]:
    """
    Load a certificate bundle by name.

    Args:
        bundle_name: Name of the bundle (e.g., "valid/platform", "invalid/truncated-cert")

    Returns:
        Dictionary with 'cert_path' and 'key_path' keys

    Example:
        >>> bundle = load_cert_bundle("valid/platform")
        >>> assert bundle["cert_path"].exists()
    """
    certs_dir = TEST_DATA_DIR / "certs"

    # If bundle_name includes extension, use it directly
    if bundle_name.endswith((".pem", ".crt")):
        cert_path = certs_dir / bundle_name
        # Try to find matching key
        key_path = cert_path.with_suffix(".key")
        if not key_path.exists():
            key_path = cert_path.parent / cert_path.name.replace(".crt", ".key").replace(
                ".pem", ".key"
            )
    else:
        # Assume standard naming (platform.crt, platform.key)
        cert_path = certs_dir / f"{bundle_name}.crt"
        key_path = certs_dir / f"{bundle_name}.key"

    return {"cert_path": cert_path, "key_path": key_path}


def load_controller_exchange(exchange_path: str) -> dict[str, Any]:
    """
    Load a controller exchange fixture (registration, heartbeat, etc.).

    Args:
        exchange_path: Relative path from tests/data/controller/ (e.g., "registration/successful.json")

    Returns:
        Dictionary with request, response, and expected state

    Example:
        >>> exchange = load_controller_exchange("registration/successful.json")
        >>> assert exchange["response"]["status_code"] == 200
    """
    controller_dir = TEST_DATA_DIR / "controller"
    fixture_path = controller_dir / exchange_path

    if not fixture_path.exists():
        raise FileNotFoundError(f"Exchange fixture not found: {fixture_path}")

    with open(fixture_path) as f:
        return json.load(f)


def load_shutdown_scenario(scenario_path: str) -> dict[str, Any]:
    """
    Load a shutdown scenario fixture.

    Args:
        scenario_path: Relative path from tests/data/controller/shutdown/ (e.g., "valid/graceful.json")

    Returns:
        Dictionary with scenario metadata and task list

    Example:
        >>> scenario = load_shutdown_scenario("valid/graceful.json")
        >>> assert scenario["expected_outcome"] == "success"
    """
    shutdown_dir = TEST_DATA_DIR / "controller" / "shutdown"
    fixture_path = shutdown_dir / scenario_path

    if not fixture_path.exists():
        raise FileNotFoundError(f"Shutdown scenario not found: {fixture_path}")

    with open(fixture_path) as f:
        return json.load(f)


def list_fixtures(category: str, extension: str = "*") -> list[Path]:
    """
    List all fixtures in a category.

    Args:
        category: Category path (e.g., "certs/invalid", "controller/registration")
        extension: File extension filter (default: "*")

    Returns:
        List of fixture file paths

    Example:
        >>> invalid_certs = list_fixtures("certs/invalid", "*.pem")
        >>> assert len(invalid_certs) > 0
    """
    category_dir = TEST_DATA_DIR / category

    if not category_dir.exists():
        raise FileNotFoundError(f"Fixture category not found: {category_dir}")

    return sorted(category_dir.glob(f"*.{extension}" if extension != "*" else "*"))


def load_json_fixture(fixture_path: str) -> dict[str, Any]:
    """
    Load any JSON fixture by relative path from tests/data/.

    Args:
        fixture_path: Relative path from tests/data/ (e.g., "capabilities/valid/streaming.json")

    Returns:
        Parsed JSON content

    Example:
        >>> fixture = load_json_fixture("capabilities/valid/streaming.json")
    """
    full_path = TEST_DATA_DIR / fixture_path

    if not full_path.exists():
        raise FileNotFoundError(f"JSON fixture not found: {full_path}")

    with open(full_path) as f:
        return json.load(f)
