#!/usr/bin/env python3
"""
🦙 Kevin's Runtime Abstraction Demo

This script demonstrates Kevin's container runtime abstraction in action.
It will automatically detect available runtimes and deploy a test service.
"""

import logging
import os
import sys
import time

# Add the services directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "services"))

from runtime import RuntimeManager

# Configure logging to see Kevin in action
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def main():
    print("🦙 Kevin's Runtime Abstraction Demo")
    print("=" * 50)

    try:
        # Initialize Kevin's runtime manager
        print("\n1. 🔍 Detecting available container runtimes...")
        runtime_manager = RuntimeManager()

        # Show what Kevin selected
        info = runtime_manager.get_runtime_info()
        print(f"   Selected runtime: {info['current_runtime']}")
        print(f"   Kevin's mood: {info['kevin_happiness']}")

        # Test service deployment
        print("\n2. 🚀 Testing service deployment...")

        # Use a simple test image that should be available
        test_image = "hello-world"
        test_config = {
            "name": "kevin-test-container",
            "detach": True,
            "environment": ["TEST_VAR=kevin_says_hello"],
        }

        print(f"   Deploying {test_image} with {runtime_manager.current_runtime}...")
        container_id = runtime_manager.run_service(test_image, **test_config)
        print(f"   ✅ Container started: {container_id[:12]}...")

        # Wait a moment for the container to run
        print("   ⏳ Waiting for container to complete...")
        time.sleep(3)

        # Get logs
        print("\n3. 📋 Getting container logs...")
        logs = runtime_manager.get_service_logs(container_id)
        if logs:
            print(f"   Logs preview: {logs[:200]}...")
        else:
            print("   No logs available (container may have exited)")

        # Inspect the container
        print("\n4. 🔍 Inspecting container...")
        inspection = runtime_manager.inspect_service(container_id)
        if inspection:
            state = inspection.get("State", {})
            print(f"   Container status: {state.get('Status', 'unknown')}")
            print(f"   Exit code: {state.get('ExitCode', 'unknown')}")

        # Clean up
        print("\n5. 🧹 Cleaning up...")
        runtime_manager.remove_service(container_id, force=True)
        print("   ✅ Container removed")

        print(
            f"\n🎉 Kevin's demo complete! Runtime abstraction works with {runtime_manager.current_runtime}!",
        )

    except Exception as e:
        print(f"\n❌ Kevin encountered an error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
