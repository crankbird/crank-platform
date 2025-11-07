#!/usr/bin/env python3

import json

import httpx


def test_mesh_diagnostic():
    """Test basic diagnostic mesh functionality."""
    base_url = "http://localhost:8000"

    print("Testing Mesh Diagnostic Service...")
    print("=" * 50)

    # Test health
    print("\n1. Health Check:")
    try:
        response = httpx.get(f"{base_url}/health/live")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        health_ok = response.status_code == 200
        print(f"   ✅ Health: {'PASS' if health_ok else 'FAIL'}")
    except Exception as e:
        print(f"   ❌ Health: FAIL - {e}")
        health_ok = False

    # Test capabilities
    print("\n2. Capabilities Check:")
    try:
        response = httpx.get(
            f"{base_url}/v1/capabilities",
            headers={"Authorization": "Bearer dev-mesh-key"},
        )
        print(f"   Status: {response.status_code}")
        caps = response.json()
        print(f"   Response type: {type(caps)}")

        # Handle both dict and list responses
        if isinstance(caps, dict):
            diag_count = len(caps.get("diagnostics", []))
            diagnostics = caps.get("diagnostics", [])
        else:
            diag_count = len(caps) if isinstance(caps, list) else 0
            diagnostics = caps if isinstance(caps, list) else []

        print(f"   Capabilities: {diag_count} total")
        for diag in diagnostics:
            if isinstance(diag, dict):
                print(
                    f"     - {diag.get('name', 'unknown')}: {diag.get('description', 'no description')}",
                )
            else:
                print(f"     - {diag}")
        caps_ok = response.status_code == 200 and diag_count > 0
        print(f"   ✅ Capabilities: {'PASS' if caps_ok else 'FAIL'}")
    except Exception as e:
        print(f"   ❌ Capabilities: FAIL - {e}")
        caps_ok = False

    # Test ping operation
    print("\n3. Ping Operation:")
    try:
        ping_request = {
            "job_id": "test-123",
            "service_type": "diagnostic",
            "operation": "ping",
            "input_data": {"message": "Hello World"},
            "policies": ["basic_auth"],
        }

        response = httpx.post(
            f"{base_url}/v1/process",
            headers={
                "Authorization": "Bearer dev-mesh-key",
                "Content-Type": "application/json",
            },
            json=ping_request,
        )

        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Response: {json.dumps(result, indent=2)}")

        ping_ok = (
            response.status_code == 200
            and result.get("success")
            and "echo" in result.get("result", {})
        )
        print(f"   ✅ Ping: {'PASS' if ping_ok else 'FAIL'}")

        if ping_ok:
            echo_msg = result["result"]["echo"]
            print(f"   Echo message: '{echo_msg}'")

    except Exception as e:
        print(f"   ❌ Ping: FAIL - {e}")
        ping_ok = False

    # Summary
    print("\n" + "=" * 50)
    total_tests = 3
    passed_tests = sum([health_ok, caps_ok, ping_ok])
    print(f"Summary: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 All diagnostic tests PASSED! Mesh is ready.")
        return True
    print("⚠️  Some tests failed. Check the output above.")
    return False


if __name__ == "__main__":
    test_mesh_diagnostic()
