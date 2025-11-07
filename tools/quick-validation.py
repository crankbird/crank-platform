#!/usr/bin/env python3
"""
🚀 Quick Container Validation Script
===================================

Quick validation of container status before running full confidence test suite.
"""

import subprocess
import sys


def run_command(command):
    """Run command and return output"""
    try:
        result = subprocess.run(command, check=False, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def check_docker_running():
    """Check if Docker is running"""
    exit_code, _stdout, _stderr = run_command("docker info")
    if exit_code == 0:
        print("✅ Docker is running")
        return True
    print("❌ Docker is not running or not accessible")
    return False


def check_containers():
    """Check container status"""
    expected_containers = [
        "crank-cert-authority-dev",
        "crank-platform-dev",
        "crank-email-classifier-dev",
        "crank-email-parser-dev",
    ]

    print("\n📋 Container Status Check:")

    exit_code, stdout, _stderr = run_command(
        "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'",
    )

    if exit_code != 0:
        print("❌ Failed to get container status")
        return False

    print(stdout)

    # Check if critical containers are running
    running_containers = []
    for line in stdout.split("\n")[1:]:  # Skip header
        if line.strip():
            container_name = line.split()[0]
            if any(expected in container_name for expected in expected_containers):
                running_containers.append(container_name)

    print(f"\n🔍 Running containers: {len(running_containers)} found")
    for container in running_containers:
        print(f"   ✅ {container}")

    return len(running_containers) >= 4  # At least the 4 working services


def main():
    """Main validation"""
    print("🚀 Quick Container Validation")
    print("=" * 40)

    if not check_docker_running():
        sys.exit(1)

    if not check_containers():
        print("\n❌ Not enough containers running for testing")
        print(
            "💡 Tip: Start containers with: docker-compose -f docker-compose.development.yml up -d",
        )
        sys.exit(1)

    print("\n✅ Ready for confidence testing!")
    print("🎯 Run: python3 tools/confidence-test-suite.py")


if __name__ == "__main__":
    main()
