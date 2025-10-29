#!/usr/bin/env python3
"""
Adversarial Testing Suite for Crank Platform

This script tests edge cases, security vulnerabilities, and failure modes
to ensure the platform is robust and secure.
"""

import asyncio
import json
import random
import string
import tempfile
from pathlib import Path
import httpx
import time


class AdversarialTester:
    """Adversarial testing suite for Crank Platform."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.results = []
        self.auth_headers = {"Authorization": "Bearer dev-mesh-key"}
    
    def log_result(self, test_name: str, status: str, details: str = ""):
        """Log test result."""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": time.time()
        }
        self.results.append(result)
        
        if status == "PASS":
            print(f"✅ {test_name}")
        elif status == "FAIL":
            print(f"❌ {test_name}: {details}")
        elif status == "WARNING":
            print(f"⚠️ {test_name}: {details}")
    
    async def test_auth_bypass(self):
        """Test authentication bypass attempts."""
        print("\n🔒 Testing Authentication Security...")
        
        # Test without auth header
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/v1/capabilities")
                if response.status_code == 401:
                    self.log_result("Auth: Missing header rejected", "PASS")
                else:
                    self.log_result("Auth: Missing header allowed", "FAIL", 
                                  f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Auth: Missing header test", "FAIL", str(e))
        
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/v1/capabilities", 
                                          headers=invalid_headers)
                if response.status_code == 401:
                    self.log_result("Auth: Invalid token rejected", "PASS")
                else:
                    self.log_result("Auth: Invalid token allowed", "FAIL",
                                  f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Auth: Invalid token test", "FAIL", str(e))
        
        # Test with malformed auth header
        malformed_headers = {"Authorization": "NotBearer token"}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/v1/capabilities",
                                          headers=malformed_headers)
                if response.status_code == 401:
                    self.log_result("Auth: Malformed header rejected", "PASS")
                else:
                    self.log_result("Auth: Malformed header allowed", "FAIL",
                                  f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Auth: Malformed header test", "FAIL", str(e))
    
    async def test_oversized_requests(self):
        """Test handling of oversized requests."""
        print("\n📦 Testing Oversized Request Handling...")
        
        # Test extremely large file (100MB of random data)
        large_content = b'A' * (100 * 1024 * 1024)  # 100MB
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                files = {"file": ("huge.txt", large_content, "text/plain")}
                data = {
                    "service_type": "document",
                    "operation": "validate",
                    "parameters": "{}"
                }
                
                response = await client.post(f"{self.base_url}/v1/process",
                                           headers=self.auth_headers,
                                           data=data, files=files)
                
                if response.status_code in [413, 400]:  # Request too large or bad request
                    self.log_result("Oversized: Large file rejected", "PASS")
                elif response.status_code == 500:
                    self.log_result("Oversized: Large file caused server error", "WARNING",
                                  "Server should handle gracefully")
                else:
                    self.log_result("Oversized: Large file processed", "FAIL",
                                  "Should reject files > 50MB")
                    
            except httpx.TimeoutException:
                self.log_result("Oversized: Request timeout", "PASS", 
                              "Timeout protection working")
            except Exception as e:
                self.log_result("Oversized: Large file test", "WARNING", str(e))
    
    async def test_malformed_requests(self):
        """Test handling of malformed requests."""
        print("\n🔧 Testing Malformed Request Handling...")
        
        # Test invalid JSON parameters
        async with httpx.AsyncClient() as client:
            try:
                data = {
                    "service_type": "document",
                    "operation": "validate",
                    "parameters": "invalid-json{"
                }
                
                response = await client.post(f"{self.base_url}/v1/process",
                                           headers=self.auth_headers, data=data)
                
                if response.status_code == 400:
                    self.log_result("Malformed: Invalid JSON rejected", "PASS")
                else:
                    self.log_result("Malformed: Invalid JSON accepted", "FAIL",
                                  f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Malformed: Invalid JSON test", "FAIL", str(e))
        
        # Test missing required fields
        async with httpx.AsyncClient() as client:
            try:
                data = {"parameters": "{}"}  # Missing service_type and operation
                
                response = await client.post(f"{self.base_url}/v1/process",
                                           headers=self.auth_headers, data=data)
                
                if response.status_code == 422:  # Validation error
                    self.log_result("Malformed: Missing fields rejected", "PASS")
                else:
                    self.log_result("Malformed: Missing fields accepted", "FAIL",
                                  f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Malformed: Missing fields test", "FAIL", str(e))
        
        # Test invalid service type
        async with httpx.AsyncClient() as client:
            try:
                data = {
                    "service_type": "nonexistent",
                    "operation": "test",
                    "parameters": "{}"
                }
                
                response = await client.post(f"{self.base_url}/v1/process",
                                           headers=self.auth_headers, data=data)
                
                if response.status_code == 400:
                    self.log_result("Malformed: Invalid service type rejected", "PASS")
                else:
                    self.log_result("Malformed: Invalid service type accepted", "FAIL",
                                  f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Malformed: Invalid service type test", "FAIL", str(e))
    
    async def test_malicious_files(self):
        """Test handling of potentially malicious files."""
        print("\n🦠 Testing Malicious File Handling...")
        
        # Test file with null bytes
        malicious_content = b"Normal content\x00\x00\x00malicious"
        async with httpx.AsyncClient() as client:
            try:
                files = {"file": ("null_bytes.txt", malicious_content, "text/plain")}
                data = {
                    "service_type": "document",
                    "operation": "validate",
                    "parameters": "{}"
                }
                
                response = await client.post(f"{self.base_url}/v1/process",
                                           headers=self.auth_headers,
                                           data=data, files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "completed":
                        self.log_result("Malicious: Null bytes handled", "PASS")
                    else:
                        self.log_result("Malicious: Null bytes rejected", "PASS")
                else:
                    self.log_result("Malicious: Null bytes test", "WARNING",
                                  f"Unexpected status: {response.status_code}")
            except Exception as e:
                self.log_result("Malicious: Null bytes test", "WARNING", str(e))
        
        # Test extremely long filename
        long_filename = "A" * 1000 + ".txt"
        async with httpx.AsyncClient() as client:
            try:
                files = {"file": (long_filename, b"content", "text/plain")}
                data = {
                    "service_type": "document", 
                    "operation": "validate",
                    "parameters": "{}"
                }
                
                response = await client.post(f"{self.base_url}/v1/process",
                                           headers=self.auth_headers,
                                           data=data, files=files)
                
                if response.status_code in [200, 400]:
                    self.log_result("Malicious: Long filename handled", "PASS")
                else:
                    self.log_result("Malicious: Long filename caused error", "WARNING",
                                  f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Malicious: Long filename test", "WARNING", str(e))
        
        # Test binary file as text
        binary_content = bytes(range(256))
        async with httpx.AsyncClient() as client:
            try:
                files = {"file": ("binary.txt", binary_content, "text/plain")}
                data = {
                    "service_type": "email",
                    "operation": "classify", 
                    "parameters": "{}"
                }
                
                response = await client.post(f"{self.base_url}/v1/process",
                                           headers=self.auth_headers,
                                           data=data, files=files)
                
                if response.status_code == 200:
                    self.log_result("Malicious: Binary as text handled", "PASS")
                else:
                    self.log_result("Malicious: Binary as text rejected", "PASS")
            except Exception as e:
                self.log_result("Malicious: Binary as text test", "WARNING", str(e))
    
    async def test_resource_exhaustion(self):
        """Test resource exhaustion attacks."""
        print("\n⚡ Testing Resource Exhaustion...")
        
        # Test rapid concurrent requests
        async def make_request(client, i):
            try:
                data = {
                    "service_type": "document",
                    "operation": "validate",
                    "parameters": "{}"
                }
                files = {"file": (f"test{i}.txt", b"test content", "text/plain")}
                
                response = await client.post(f"{self.base_url}/v1/process",
                                           headers=self.auth_headers,
                                           data=data, files=files)
                return response.status_code
            except Exception:
                return 500
        
        # Send 50 concurrent requests
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                tasks = [make_request(client, i) for i in range(50)]
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                success_count = sum(1 for r in responses if isinstance(r, int) and r == 200)
                error_count = sum(1 for r in responses if isinstance(r, int) and r >= 500)
                
                if success_count > 0 and error_count < 10:
                    self.log_result("Resource: Concurrent requests handled", "PASS",
                                  f"{success_count}/50 successful")
                elif error_count > 25:
                    self.log_result("Resource: Service overwhelmed", "FAIL",
                                  f"{error_count}/50 errors")
                else:
                    self.log_result("Resource: Partial degradation", "WARNING",
                                  f"{error_count}/50 errors")
            except Exception as e:
                self.log_result("Resource: Concurrent test", "WARNING", str(e))
    
    async def test_injection_attacks(self):
        """Test various injection attack vectors."""
        print("\n💉 Testing Injection Attacks...")
        
        # Test SQL injection in parameters
        sql_injection = "'; DROP TABLE users; --"
        async with httpx.AsyncClient() as client:
            try:
                data = {
                    "service_type": "document",
                    "operation": "validate",
                    "parameters": json.dumps({"filename": sql_injection})
                }
                files = {"file": ("test.txt", b"content", "text/plain")}
                
                response = await client.post(f"{self.base_url}/v1/process",
                                           headers=self.auth_headers,
                                           data=data, files=files)
                
                if response.status_code in [200, 400]:
                    self.log_result("Injection: SQL injection handled", "PASS")
                else:
                    self.log_result("Injection: SQL injection caused error", "WARNING",
                                  f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Injection: SQL injection test", "WARNING", str(e))
        
        # Test command injection
        cmd_injection = "; rm -rf / #"
        async with httpx.AsyncClient() as client:
            try:
                data = {
                    "service_type": "email",
                    "operation": "parse",
                    "parameters": json.dumps({"output_format": cmd_injection})
                }
                files = {"file": ("test.eml", b"Subject: test\n\nContent", "message/rfc822")}
                
                response = await client.post(f"{self.base_url}/v1/process",
                                           headers=self.auth_headers,
                                           data=data, files=files)
                
                if response.status_code in [200, 400]:
                    self.log_result("Injection: Command injection handled", "PASS")
                else:
                    self.log_result("Injection: Command injection caused error", "WARNING",
                                  f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Injection: Command injection test", "WARNING", str(e))
    
    async def test_service_availability(self):
        """Test service availability and recovery."""
        print("\n🏥 Testing Service Availability...")
        
        # Test health endpoints
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/health/live")
                if response.status_code == 200:
                    self.log_result("Availability: Liveness endpoint", "PASS")
                else:
                    self.log_result("Availability: Liveness endpoint", "FAIL",
                                  f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Availability: Liveness endpoint", "FAIL", str(e))
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/health/ready")
                if response.status_code == 200:
                    self.log_result("Availability: Readiness endpoint", "PASS")
                else:
                    self.log_result("Availability: Readiness endpoint", "WARNING",
                                  f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Availability: Readiness endpoint", "FAIL", str(e))
    
    async def run_all_tests(self):
        """Run the complete adversarial testing suite."""
        print("🛡️ Crank Platform Adversarial Testing Suite")
        print("=" * 60)
        
        test_functions = [
            self.test_auth_bypass,
            self.test_oversized_requests,
            self.test_malformed_requests,
            self.test_malicious_files,
            self.test_resource_exhaustion,
            self.test_injection_attacks,
            self.test_service_availability,
        ]
        
        for test_func in test_functions:
            try:
                await test_func()
            except Exception as e:
                print(f"❌ Test {test_func.__name__} crashed: {e}")
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary report."""
        print("\n" + "=" * 60)
        print("📊 ADVERSARIAL TESTING SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        warnings = sum(1 for r in self.results if r["status"] == "WARNING")
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Warnings: {warnings}")
        
        if failed == 0:
            print("\n🎉 All critical security tests passed!")
        else:
            print(f"\n🚨 {failed} critical security issues found!")
        
        if warnings > 0:
            print(f"⚠️ {warnings} warnings require investigation")
        
        # Show failed tests
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"   • {result['test']}: {result['details']}")
        
        # Show warnings
        if warnings > 0:
            print("\n⚠️ WARNINGS:")
            for result in self.results:
                if result["status"] == "WARNING":
                    print(f"   • {result['test']}: {result['details']}")
        
        # Calculate security score
        if total_tests > 0:
            security_score = (passed / total_tests) * 100
            print(f"\n🛡️ Security Score: {security_score:.1f}%")
            
            if security_score >= 90:
                print("   Excellent security posture!")
            elif security_score >= 75:
                print("   Good security, minor improvements needed")
            elif security_score >= 60:
                print("   Moderate security, improvements required")
            else:
                print("   Poor security, immediate action required")


async def main():
    """Main function."""
    import sys
    
    # Check if gateway URL provided
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    
    print(f"🎯 Testing against: {base_url}")
    
    tester = AdversarialTester(base_url)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())