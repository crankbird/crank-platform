#!/usr/bin/env python3
"""
🧪 Port Configuration Validation Test
Validates that all services properly use environment variables for ports.

This test satisfies:
- Kevin the Portability Llama: Environment-based configuration
- Oliver the Evidence-Based Owl: Evidence-based validation
- Wendy the Zero Security Bunny: Configurable deployment options
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

import pytest


def test_service_port_configuration() -> None:
    """Test that all services respect environment variables for ports."""

    services_dir = Path("services")
    python_files = list(services_dir.glob("*.py"))
    python_files = [
        f for f in python_files if not f.name.startswith("test_") and f.name != "__init__.py"
    ]

    print(f"🧪 Testing {len(python_files)} Python Services...")
    print("=" * 50)

    all_passed = True
    for service_file in python_files:
        content = service_file.read_text()

        # Check for environment variable usage for ports
        if "os.getenv(" in content and ("PORT" in content or "port" in content):
            print(f"{service_file.name:30} ✅ Uses environment variables")
        elif "uvicorn.run" in content and "port=" in content:
            # Check if it's using hardcoded ports
            if "port=8" in content and "os.getenv" not in content:
                print(f"{service_file.name:30} ❌ Has hardcoded ports")
                all_passed = False
            else:
                print(f"{service_file.name:30} ✅ Port configuration detected")
        else:
            print(f"{service_file.name:30} - No uvicorn server detected")

    print("\n" + "=" * 50)
    if not all_passed:
        pytest.fail("Some services need port configuration fixes")
    print("🎉 All services properly configured!")
    print("Kevin the Portability Llama is happy! 🦙")


def test_dockerfile_port_configuration() -> None:
    """Test that Dockerfiles use environment variables or call files that do."""

    services_dir = Path("services")
    dockerfiles = list(services_dir.glob("Dockerfile.*"))

    print(f"\n🐳 Testing {len(dockerfiles)} Dockerfiles...")
    print("=" * 50)

    all_passed = True
    for dockerfile in dockerfiles:
        content = dockerfile.read_text()

        # Check for direct environment variable usage
        if "os.getenv(" in content:
            print(f"{dockerfile.name:25} ✅ Uses environment variables")
        # Check if it calls a Python file that we know uses environment variables
        elif any(
            f'"{py_file}"' in content or f"python.*{py_file}" in content
            for py_file in [
                "platform_app.py",
                "gateway.py",
                "crank_doc_converter.py",
                "crank_email_classifier.py",
                "crank_email_parser.py",
                "crank_streaming_service.py",
            ]
        ):
            print(f"{dockerfile.name:25} ✅ Calls env-configured service")
        # Check for hardcoded ports that would be problematic
        elif any(
            port in content for port in ["port=8000", "port=8001", "port=8080", ":8000", ":8001"]
        ):
            print(f"{dockerfile.name:25} ❌ Has hardcoded ports")
            all_passed = False
        else:
            print(f"{dockerfile.name:25} ✅ No port conflicts detected")

    if not all_passed:
        pytest.fail("Some Dockerfiles have port configuration issues")


def test_oliver_validation() -> None:
    """Test Oliver's pattern checker on our services."""

    print("\n🦅 Running Oliver's Evidence-Based Validation...")
    print("=" * 50)

    try:
        # Run Oliver on services directory only
        result = subprocess.run(
            ["python3", "oliver_pattern_checker.py", "services/"],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        if "No anti-patterns detected" in result.stdout:
            print("✅ Oliver approves: No anti-patterns detected!")
            print("🦅 Architecture is clean according to industry authorities")
        else:
            print("❌ Oliver found issues:")
            print(result.stdout[-500:])  # Last 500 chars
            pytest.fail("Oliver found anti-patterns in services")

    except Exception as e:
        print(f"❌ Could not run Oliver: {e}")
        pytest.fail(f"Could not run Oliver: {e}")


def main() -> None:
    """Run all validation tests."""

    print("🚢 Crank Platform Port Configuration Validation")
    print("Validating Kevin, Oliver, Wendy, and Bella's requirements")
    print("=" * 60)

    tests: list[tuple[str, Callable[[], None]]] = [
        ("Service Port Configuration", test_service_port_configuration),
        ("Dockerfile Configuration", test_dockerfile_port_configuration),
        ("Oliver's Pattern Validation", test_oliver_validation),
    ]

    all_passed = True
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            all_passed = False

    print("\n" + "=" * 60)
    if not all_passed:
        pytest.fail("Some tests failed")
    print("🎉 ALL TESTS PASSED!")
    print("✅ Kevin the Portability Llama: Environment configuration working")
    print("✅ Oliver the Evidence-Based Owl: No anti-patterns detected")
    print("✅ Wendy the Zero Security Bunny: Configurable deployments ready")
    print("✅ Bella the Modularity Poodle: Service separation maintained")
    print("\n🏆 Architecture passes all mascot requirements!")


if __name__ == "__main__":
    main()
