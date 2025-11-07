#!/usr/bin/env python3
"""
Mesh Diagnostic Testing - Infrastructure vs Business Logic Isolation

This script demonstrates how built-in diagnostics help isolate issues:
- Is it the mesh wrapper? (ping test)
- Is it file handling? (echo_file test)
- Is it performance? (load_test)
- Is it error handling? (error_test)
- Or is it the actual business logic?

Like ICMP ping for mesh services!
"""

import asyncio
from typing import Any


class DiagnosticTestSuite:
    """Test suite that uses diagnostic operations to isolate issues."""

    def __init__(self, service_url: str = "http://localhost:8000"):
        self.service_url = service_url
        self.test_results = {}

    async def run_full_diagnostic(self):
        """Run complete diagnostic suite to isolate any issues."""
        print("🔍 MESH DIAGNOSTIC TEST SUITE")
        print("=" * 40)
        print()
        print("Testing infrastructure vs business logic...")
        print()

        # Test 1: Basic mesh functionality
        await self._test_ping()

        # Test 2: File handling pipeline
        await self._test_file_echo()

        # Test 3: Performance characteristics
        await self._test_load_handling()

        # Test 4: Error propagation
        await self._test_error_handling()

        # Test 5: Business logic (if diagnostics pass)
        await self._test_business_logic()

        # Analyze results
        await self._analyze_results()

    async def _test_ping(self):
        """Test basic mesh wrapper functionality."""
        print("📡 Testing Basic Mesh Wrapper (ping)...")

        # Simulate ping test
        test_data = {
            "message": "hello from test suite",
            "delay_ms": 50,
        }

        # Would make actual HTTP request in real implementation
        result = await self._simulate_request("ping", test_data)

        self.test_results["ping"] = result

        if result["success"]:
            print(f"   ✅ Mesh wrapper working - {result['processing_time_ms']:.1f}ms")
            print(f"   📤 Echo: {result['result']['echo']}")
        else:
            print(f"   ❌ Mesh wrapper issue: {result['error']}")
        print()

    async def _test_file_echo(self):
        """Test file upload/download pipeline."""
        print("📄 Testing File Handling Pipeline (echo_file)...")

        # Simulate file echo test
        test_data = {
            "return_hash": True,
            "return_size": True,
        }

        # Would include actual file in real implementation
        result = await self._simulate_file_request(
            "echo_file", test_data, "test.txt", b"Hello, file test!",
        )

        self.test_results["echo_file"] = result

        if result["success"]:
            print(f"   ✅ File pipeline working - {result['processing_time_ms']:.1f}ms")
            print(
                f"   📁 File: {result['result']['filename']} ({result['result']['size_bytes']} bytes)",
            )
            print(f"   🔐 Hash: {result['result']['sha256_hash'][:16]}...")
        else:
            print(f"   ❌ File pipeline issue: {result['error']}")
        print()

    async def _test_load_handling(self):
        """Test performance and resource handling."""
        print("⚡ Testing Load Handling (load_test)...")

        test_data = {
            "cpu_work_ms": 100,
            "memory_mb": 2,
            "response_size_kb": 5,
        }

        result = await self._simulate_request("load_test", test_data)

        self.test_results["load_test"] = result

        if result["success"]:
            print(f"   ✅ Load handling working - {result['processing_time_ms']:.1f}ms")
            print(f"   🔥 CPU work: {result['result']['requested_cpu_ms']}ms")
            print(f"   🧠 Memory: {result['result']['requested_memory_mb']}MB allocated")
        else:
            print(f"   ❌ Load handling issue: {result['error']}")
        print()

    async def _test_error_handling(self):
        """Test error handling and propagation."""
        print("💥 Testing Error Handling (error_test)...")

        test_data = {
            "error_type": "validation",
            "error_message": "Test validation error",
        }

        result = await self._simulate_request("error_test", test_data)

        self.test_results["error_test"] = result

        # For error tests, we expect failure
        if not result["success"]:
            print("   ✅ Error handling working - error properly propagated")
            print(f"   💥 Error: {result['error']}")
        else:
            print("   ❌ Error handling issue - should have failed but didn't")
        print()

    async def _test_business_logic(self):
        """Test actual business logic (if infrastructure is working)."""
        print("🏢 Testing Business Logic (convert)...")

        # Only test business logic if infrastructure tests passed
        infrastructure_ok = self.test_results.get("ping", {}).get(
            "success", False,
        ) and self.test_results.get("echo_file", {}).get("success", False)

        if not infrastructure_ok:
            print("   ⏭️  Skipping business logic test - infrastructure issues detected")
            print("   📋 Fix infrastructure issues first, then test business logic")
            print()
            return

        test_data = {
            "target_format": "pdf",
            "quality": "high",
        }

        # Would include actual document in real implementation
        result = await self._simulate_file_request(
            "convert", test_data, "test.docx", b"Fake document content",
        )

        self.test_results["convert"] = result

        if result["success"]:
            print(f"   ✅ Business logic working - {result['processing_time_ms']:.1f}ms")
            print(f"   📄 Converted to: {result['result'].get('target_format', 'unknown')}")
        else:
            print(f"   ❌ Business logic issue: {result['error']}")
            print("   💡 Infrastructure OK, problem is in conversion logic")
        print()

    async def _simulate_request(self, operation: str, data: dict[str, Any]) -> dict[str, Any]:
        """Simulate a mesh request (would be actual HTTP in real implementation)."""
        import time

        start_time = time.time()

        try:
            if operation == "ping":
                # Simulate successful ping
                await asyncio.sleep(data.get("delay_ms", 0) / 1000)
                result = {
                    "echo": data.get("message", "hello"),
                    "timestamp": "2025-10-29T10:30:00Z",
                    "test_passed": True,
                }

            elif operation == "load_test":
                # Simulate load test
                cpu_ms = data.get("cpu_work_ms", 100)
                await asyncio.sleep(cpu_ms / 1000)  # Simulate CPU work
                result = {
                    "requested_cpu_ms": cpu_ms,
                    "requested_memory_mb": data.get("memory_mb", 1),
                    "test_passed": True,
                }

            elif operation == "error_test":
                # Simulate error (should fail)
                raise ValueError(f"Test error: {data.get('error_message', 'test error')}")

            else:
                result = {"message": f"Simulated {operation} operation"}

            processing_time = (time.time() - start_time) * 1000

            return {
                "success": True,
                "result": result,
                "processing_time_ms": processing_time,
                "receipt_id": f"test-{hash(str(data)) % 10000}",
            }

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000

            return {
                "success": False,
                "error": str(e),
                "processing_time_ms": processing_time,
                "receipt_id": f"test-error-{hash(str(e)) % 10000}",
            }

    async def _simulate_file_request(
        self, operation: str, data: dict[str, Any], filename: str, content: bytes,
    ) -> dict[str, Any]:
        """Simulate a file-based mesh request."""
        import hashlib
        import time

        start_time = time.time()

        try:
            if operation == "echo_file":
                # Simulate file echo
                file_hash = hashlib.sha256(content).hexdigest()
                result = {
                    "filename": filename,
                    "size_bytes": len(content),
                    "sha256_hash": file_hash,
                    "test_passed": True,
                }

            elif operation == "convert":
                # Simulate document conversion
                result = {
                    "converted": True,
                    "target_format": data.get("target_format", "pdf"),
                    "original_size": len(content),
                    "converted_size": len(content) * 1.2,  # Simulate size change
                    "message": "Simulated conversion (replace with real logic)",
                }

            else:
                result = {"message": f"Simulated {operation} with file {filename}"}

            processing_time = (time.time() - start_time) * 1000

            return {
                "success": True,
                "result": result,
                "processing_time_ms": processing_time,
                "receipt_id": f"test-{hash(filename) % 10000}",
            }

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000

            return {
                "success": False,
                "error": str(e),
                "processing_time_ms": processing_time,
                "receipt_id": f"test-error-{hash(str(e)) % 10000}",
            }

    async def _analyze_results(self):
        """Analyze test results and provide diagnostic guidance."""
        print("📊 DIAGNOSTIC ANALYSIS")
        print("=" * 25)
        print()

        # Check infrastructure layer
        infrastructure_tests = ["ping", "echo_file", "load_test"]
        infrastructure_passed = sum(
            1
            for test in infrastructure_tests
            if self.test_results.get(test, {}).get("success", False)
        )

        print(f"Infrastructure Tests: {infrastructure_passed}/{len(infrastructure_tests)} passed")

        if infrastructure_passed == len(infrastructure_tests):
            print("✅ Infrastructure layer: HEALTHY")
            print("   Mesh wrapper, file handling, and load management working")
            print()

            # Check business logic
            business_result = self.test_results.get("convert", {})
            if business_result.get("success", False):
                print("✅ Business Logic: HEALTHY")
                print("   Document conversion working correctly")
            else:
                print("❌ Business Logic: ISSUE DETECTED")
                print("   Problem is in the actual conversion logic")
                print("   Infrastructure is fine - focus on business logic")
        else:
            print("❌ Infrastructure layer: ISSUES DETECTED")
            print("   Fix infrastructure before testing business logic")
            print()

            # Specific guidance
            if not self.test_results.get("ping", {}).get("success", False):
                print("   🔧 PING FAILED: Basic mesh wrapper not working")
                print("      Check: Authentication, routing, basic request handling")

            if not self.test_results.get("echo_file", {}).get("success", False):
                print("   🔧 FILE ECHO FAILED: File handling pipeline broken")
                print("      Check: File upload, storage, permissions")

            if not self.test_results.get("load_test", {}).get("success", False):
                print("   🔧 LOAD TEST FAILED: Resource/performance issues")
                print("      Check: Memory limits, CPU constraints, timeouts")

        print()
        print("💡 Diagnostic Strategy:")
        print("   1. Always test diagnostics first (ping, echo_file, load_test)")
        print("   2. Only test business logic if diagnostics pass")
        print("   3. Use error_test to verify error handling works")
        print("   4. This isolates infrastructure vs application issues")
        print()
        print("🏥 Just like medical diagnostics - test the basics first!")


async def main():
    """Run the diagnostic test suite."""
    print("🏥 MESH DIAGNOSTIC TESTING FRAMEWORK")
    print("=" * 45)
    print()
    print("Isolating infrastructure vs business logic issues...")
    print("Like ICMP ping, but for mesh services!")
    print()

    suite = DiagnosticTestSuite()
    await suite.run_full_diagnostic()


if __name__ == "__main__":
    asyncio.run(main())
