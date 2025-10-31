#!/usr/bin/env python3
"""
Trivial Hello World Test for Crank Platform Mesh

This script tests the basic mesh functionality using the built-in diagnostic capabilities.
Perfect for validating the cross-platform Docker deployment works.
"""

import asyncio
import httpx
import json
from datetime import datetime


async def test_mesh_hello_world():
    """Test the simplest possible mesh interaction - a ping/echo."""
    
    print("🚀 Crank Platform Mesh - Hello World Test")
    print("=" * 50)
    print(f"🕐 {datetime.now().isoformat()}")
    print()
    
    # Test services (should be running via docker-compose)
    services = {
        "Document Service": "http://localhost:8000",
        "Email Service": "http://localhost:8001", 
        "Gateway": "http://localhost:8080"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for service_name, base_url in services.items():
            print(f"🔍 Testing {service_name}...")
            
            # Test 1: Health Check (no auth required)
            try:
                response = await client.get(f"{base_url}/health/live")
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"   ✅ Health: {health_data.get('status', 'unknown')}")
                else:
                    print(f"   ❌ Health check failed: {response.status_code}")
                    continue
            except Exception as e:
                print(f"   ❌ Cannot connect to {service_name}: {e}")
                continue
            
            # Test 2: Capabilities (requires auth)
            try:
                headers = {"Authorization": "Bearer dev-mesh-key"}
                response = await client.get(f"{base_url}/v1/capabilities", headers=headers)
                if response.status_code == 200:
                    caps = response.json()
                    if isinstance(caps, list):
                        diagnostic_ops = [cap.get('operation') for cap in caps if cap.get('operation') in ['ping', 'echo_file', 'load_test']]
                        print(f"   ✅ Capabilities: {len(caps)} total, diagnostics: {diagnostic_ops}")
                    else:
                        print(f"   ✅ Capabilities available")
                else:
                    print(f"   ⚠️ Capabilities failed: {response.status_code}")
                    continue
            except Exception as e:
                print(f"   ⚠️ Capabilities error: {e}")
                continue
            
            # Test 3: Simple Ping (hello world!)
            try:
                ping_request = {
                    "job_id": f"hello-{int(datetime.now().timestamp())}",
                    "service_type": service_name.split()[0].lower(),
                    "operation": "ping",
                    "input_data": {
                        "message": "Hello World from Docker!"
                    },
                    "policies": ["basic_auth"]
                }
                
                headers = {"Authorization": "Bearer dev-mesh-key", "Content-Type": "application/json"}
                response = await client.post(f"{base_url}/v1/process", 
                                           headers=headers, 
                                           json=ping_request)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        echo_msg = result.get('result', {}).get('echo', 'no echo')
                        processing_time = result.get('result', {}).get('processing_time_ms', 'unknown')
                        print(f"   ✅ Ping successful: '{echo_msg}' ({processing_time}ms)")
                    else:
                        print(f"   ⚠️ Ping failed: {result.get('errors', 'unknown error')}")
                else:
                    print(f"   ⚠️ Ping request failed: {response.status_code}")
                    if response.status_code == 404:
                        print(f"      (Service may not have diagnostic capabilities)")
            except Exception as e:
                print(f"   ⚠️ Ping error: {e}")
            
            print()
    
    print("🎯 Hello World Test Results:")
    print("   - If you see ✅ Health checks, containers are running correctly")
    print("   - If you see ✅ Capabilities, mesh interface is working")  
    print("   - If you see ✅ Ping successful, full mesh communication works")
    print("   - This validates your Docker deployment is functional!")
    print()
    print("🌐 Next steps:")
    print("   - Visit http://localhost:8080 for gateway info")
    print("   - Try http://localhost:8888 for Jupyter (if running)")
    print("   - Run real document/email processing tests")


if __name__ == "__main__":
    asyncio.run(test_mesh_hello_world())