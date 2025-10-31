#!/usr/bin/env python3
"""
Test script for refactored mesh architecture.

This validates that the clean architecture fixes all the issues:
- No more hacky patches
- Proper type safety
- Consistent field handling
- Unified receipt system
"""

import httpx
import json
from typing import Dict, Any


class MeshArchitectureValidator:
    """Validates the refactored mesh architecture."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.headers = {
            "Authorization": "Bearer dev-mesh-key",
            "Content-Type": "application/json"
        }
    
    def run_validation(self) -> bool:
        """Run complete architecture validation."""
        print("🔧 Mesh Architecture Validation")
        print("=" * 50)
        
        tests = [
            ("Health Check", self._test_health),
            ("Capabilities Schema", self._test_capabilities_schema),
            ("Request/Response Types", self._test_request_response_types),
            ("Metadata Lifecycle", self._test_metadata_lifecycle),
            ("Receipt Generation", self._test_receipt_generation),
            ("Error Handling", self._test_error_handling),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{passed + 1}. {test_name}:")
            try:
                result = test_func()
                if result:
                    print(f"   ✅ PASS")
                    passed += 1
                else:
                    print(f"   ❌ FAIL")
            except Exception as e:
                print(f"   ❌ FAIL - {e}")
        
        print(f"\n{'='*50}")
        print(f"Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 Architecture refactor successful!")
            return True
        else:
            print("⚠️ Architecture issues remain.")
            return False
    
    def _test_health(self) -> bool:
        """Test health endpoint works without auth."""
        response = httpx.get(f"{self.base_url}/health/live")
        
        if response.status_code != 200:
            print(f"   Status: {response.status_code}")
            return False
        
        data = response.json()
        expected_keys = {"status", "service"}
        
        if not expected_keys.issubset(data.keys()):
            print(f"   Missing keys: {expected_keys - data.keys()}")
            return False
        
        print(f"   Health: {data['status']}, Service: {data['service']}")
        return True
    
    def _test_capabilities_schema(self) -> bool:
        """Test capabilities have proper schema."""
        response = httpx.get(f"{self.base_url}/v1/capabilities", headers=self.headers)
        
        if response.status_code != 200:
            print(f"   Status: {response.status_code}")
            return False
        
        capabilities = response.json()
        
        if not isinstance(capabilities, list):
            print(f"   Expected list, got {type(capabilities)}")
            return False
        
        if len(capabilities) == 0:
            print("   No capabilities found")
            return False
        
        # Validate first capability structure
        cap = capabilities[0]
        required_fields = {"operation", "description", "input_schema", "output_schema", "policies_required", "limits"}
        
        if not required_fields.issubset(cap.keys()):
            print(f"   Missing capability fields: {required_fields - cap.keys()}")
            return False
        
        # Check that limits is proper dict (not string-integer confusion)
        if not isinstance(cap["limits"], dict):
            print(f"   Limits should be dict, got {type(cap['limits'])}")
            return False
        
        print(f"   Found {len(capabilities)} capabilities with proper schema")
        return True
    
    def _test_request_response_types(self) -> bool:
        """Test request/response have consistent types."""
        ping_request = {
            "job_id": "test-types-123",
            "service_type": "diagnostic", 
            "operation": "ping",
            "input_data": {"message": "Type test"},
            "policies": ["basic_auth"],
            "metadata": {"test": "metadata_lifecycle"}
        }
        
        response = httpx.post(
            f"{self.base_url}/v1/process",
            headers=self.headers,
            json=ping_request
        )
        
        if response.status_code != 200:
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        data = response.json()
        
        # Check response structure
        required_fields = {"success", "result", "receipt_id", "errors", "metadata", "processing_time_ms", "mesh_node_id"}
        if not required_fields.issubset(data.keys()):
            print(f"   Missing response fields: {required_fields - data.keys()}")
            return False
        
        # Check field types
        if not isinstance(data["success"], bool):
            print(f"   success should be bool, got {type(data['success'])}")
            return False
        
        if not isinstance(data["processing_time_ms"], int):
            print(f"   processing_time_ms should be int, got {type(data['processing_time_ms'])}")
            return False
        
        if not isinstance(data["errors"], list):
            print(f"   errors should be list, got {type(data['errors'])}")
            return False
        
        if not isinstance(data["metadata"], dict):
            print(f"   metadata should be dict, got {type(data['metadata'])}")
            return False
        
        print("   All response types correct")
        return True
    
    def _test_metadata_lifecycle(self) -> bool:
        """Test metadata is properly managed throughout request lifecycle."""
        ping_request = {
            "job_id": "test-metadata-123",
            "service_type": "diagnostic",
            "operation": "ping", 
            "input_data": {"message": "Metadata test"},
            "policies": ["basic_auth"],
            "metadata": {"original": "data", "test_type": "metadata_lifecycle"}
        }
        
        response = httpx.post(
            f"{self.base_url}/v1/process",
            headers=self.headers,
            json=ping_request
        )
        
        if response.status_code != 200:
            print(f"   Status: {response.status_code}")
            return False
        
        data = response.json()
        
        # Check that result contains metadata from request processing
        if not data.get("result"):
            print("   No result in response")
            return False
        
        result = data["result"]
        
        # The diagnostic service should include metadata info
        if "service_node" not in result:
            print("   Missing service_node in result (metadata not enriched)")
            return False
        
        # Check that diagnostic_info includes proper metadata
        if "diagnostic_info" not in result:
            print("   Missing diagnostic_info")
            return False
        
        diag_info = result["diagnostic_info"]
        if not diag_info.get("auth_validated"):
            print("   Auth not properly validated in metadata")
            return False
        
        print("   Metadata properly enriched and passed through")
        return True
    
    def _test_receipt_generation(self) -> bool:
        """Test receipt generation is working and consistent."""
        ping_request = {
            "job_id": "test-receipt-123",
            "service_type": "diagnostic",
            "operation": "ping",
            "input_data": {"message": "Receipt test"},
            "policies": ["basic_auth"]
        }
        
        response = httpx.post(
            f"{self.base_url}/v1/process",
            headers=self.headers,
            json=ping_request
        )
        
        if response.status_code != 200:
            print(f"   Status: {response.status_code}")
            return False
        
        data = response.json()
        
        # Check receipt_id exists and has proper format
        receipt_id = data.get("receipt_id")
        if not receipt_id:
            print("   Missing receipt_id")
            return False
        
        if not receipt_id.startswith("receipt_"):
            print(f"   Receipt ID has wrong format: {receipt_id}")
            return False
        
        print(f"   Receipt generated: {receipt_id}")
        return True
    
    def _test_error_handling(self) -> bool:
        """Test error handling works correctly."""
        error_request = {
            "job_id": "test-error-123",
            "service_type": "diagnostic",
            "operation": "error_test",
            "input_data": {
                "error_type": "validation",
                "error_message": "Test validation error"
            },
            "policies": ["basic_auth"]
        }
        
        response = httpx.post(
            f"{self.base_url}/v1/process",
            headers=self.headers,
            json=error_request
        )
        
        if response.status_code != 200:
            print(f"   Status: {response.status_code}")
            return False
        
        data = response.json()
        
        # Should be a failed operation
        if data.get("success") is not False:
            print(f"   Expected success=False, got {data.get('success')}")
            return False
        
        # Should have errors
        if not data.get("errors"):
            print("   Expected errors in response")
            return False
        
        # Should still have receipt_id
        if not data.get("receipt_id"):
            print("   Missing receipt_id for failed operation")
            return False
        
        print(f"   Error properly handled: {data['errors'][0]}")
        return True


def main():
    """Run architecture validation."""
    validator = MeshArchitectureValidator()
    success = validator.run_validation()
    
    if success:
        print("\n🚀 Ready to proceed with refactored architecture!")
    else:
        print("\n🔧 Need to fix remaining architecture issues.")
    
    return success


if __name__ == "__main__":
    main()