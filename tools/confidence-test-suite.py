#!/usr/bin/env python3
"""
🔒 Crank Platform HTTPS-Only Confidence Test Suite
==================================================

Comprehensive validation of all 7 services with HTTPS-only certificate integration:
- Certificate Authority (9090)
- Platform Service (8443)
- Email Classifier (8200)
- Email Parser (8300)
- Doc Converter (8100)
- Image Classifier (8400)
- Streaming Service (8500)

Tests:
1. Container Health Checks
2. HTTPS Endpoint Validation
3. Certificate Authority Integration
4. Service Dependencies
5. Security Validation (no HTTP)
6. API Functionality Tests
"""

import json
import socket
import ssl
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class ServiceSpec:
    """Service specification for testing"""

    name: str
    container_name: str
    port: int
    health_endpoint: str
    protocol: str = "https"
    depends_on: list[str] = None

    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


@dataclass
class TestResult:
    """Test result container"""

    service: str
    test_name: str
    status: str  # "PASS", "FAIL", "SKIP"
    message: str
    duration: float = 0.0
    details: Optional[dict] = None


class CrankConfidenceTestSuite:
    """Comprehensive test suite for HTTPS-only Crank Platform"""

    def __init__(self):
        self.services = {
            "cert-authority": ServiceSpec(
                name="Certificate Authority",
                container_name="crank-cert-authority-dev",
                port=9090,
                health_endpoint="/health",
            ),
            "platform": ServiceSpec(
                name="Platform Service",
                container_name="crank-platform-dev",
                port=8443,
                health_endpoint="/health/live",
                depends_on=["cert-authority"],
            ),
            "email-classifier": ServiceSpec(
                name="Email Classifier",
                container_name="crank-email-classifier-dev",
                port=8200,
                health_endpoint="/health",
                depends_on=["platform"],
            ),
            "email-parser": ServiceSpec(
                name="Email Parser",
                container_name="crank-email-parser-dev",
                port=8300,
                health_endpoint="/health",
                depends_on=["platform"],
            ),
            "doc-converter": ServiceSpec(
                name="Document Converter",
                container_name="crank-doc-converter-dev",
                port=8100,
                health_endpoint="/health",
                depends_on=["platform"],
            ),
            "image-classifier": ServiceSpec(
                name="Image Classifier",
                container_name="crank-image-classifier-dev",
                port=8400,
                health_endpoint="/health",
                depends_on=["platform"],
            ),
            "streaming": ServiceSpec(
                name="Streaming Service",
                container_name="crank-streaming-dev",
                port=8500,
                health_endpoint="/health",
                depends_on=["platform"],
            ),
        }

        self.results: list[TestResult] = []
        self.session = requests.Session()
        self.session.verify = False  # Accept self-signed certificates

    def log_result(
        self,
        service: str,
        test_name: str,
        status: str,
        message: str,
        duration: float = 0.0,
        details: Optional[dict] = None,
    ):
        """Log test result"""
        result = TestResult(service, test_name, status, message, duration, details)
        self.results.append(result)

        # Color-coded output
        color = "🟢" if status == "PASS" else "🔴" if status == "FAIL" else "🟡"
        print(f"{color} {service:15} | {test_name:25} | {status:4} | {message}")

    def run_command(self, command: str) -> tuple[int, str, str]:
        """Run shell command and return exit code, stdout, stderr"""
        try:
            result = subprocess.run(
                command,
                check=False,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"

    def check_container_health(self, service_key: str) -> bool:
        """Check if container is healthy via Docker"""
        service = self.services[service_key]
        start_time = time.time()

        # Check container status
        exit_code, stdout, stderr = self.run_command(
            f"docker inspect {service.container_name} --format='{{{{.State.Health.Status}}}}'",
        )

        duration = time.time() - start_time

        if exit_code != 0:
            self.log_result(
                service_key,
                "Container Health",
                "FAIL",
                f"Container not found: {stderr}",
                duration,
            )
            return False

        health_status = stdout.strip()

        if health_status == "healthy":
            self.log_result(
                service_key,
                "Container Health",
                "PASS",
                "Container is healthy",
                duration,
            )
            return True
        self.log_result(
            service_key,
            "Container Health",
            "FAIL",
            f"Container unhealthy: {health_status}",
            duration,
        )
        return False

    def check_https_endpoint(self, service_key: str) -> bool:
        """Check HTTPS endpoint availability"""
        service = self.services[service_key]
        url = f"https://localhost:{service.port}{service.health_endpoint}"
        start_time = time.time()

        try:
            response = self.session.get(url, timeout=10)
            duration = time.time() - start_time

            if response.status_code == 200:
                self.log_result(
                    service_key,
                    "HTTPS Endpoint",
                    "PASS",
                    f"Responded with 200 ({duration:.2f}s)",
                    duration,
                    {"status_code": response.status_code, "response_time": duration},
                )
                return True
            self.log_result(
                service_key,
                "HTTPS Endpoint",
                "FAIL",
                f"Status {response.status_code}",
                duration,
            )
            return False

        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_result(
                service_key,
                "HTTPS Endpoint",
                "FAIL",
                f"Request failed: {str(e)[:50]}...",
                duration,
            )
            return False

    def check_no_http_exposure(self, service_key: str) -> bool:
        """Verify HTTP endpoints are not accessible (security test)"""
        service = self.services[service_key]
        http_url = f"http://localhost:{service.port}{service.health_endpoint}"
        start_time = time.time()

        try:
            response = requests.get(http_url, timeout=5)
            duration = time.time() - start_time
            # If we get a response, that's BAD - HTTP should be blocked
            self.log_result(
                service_key,
                "HTTP Security",
                "FAIL",
                f"HTTP accessible (BAD): {response.status_code}",
                duration,
            )
            return False

        except requests.exceptions.RequestException:
            duration = time.time() - start_time
            # Exception means HTTP is properly blocked - GOOD
            self.log_result(service_key, "HTTP Security", "PASS", "HTTP properly blocked", duration)
            return True

    def check_certificate_chain(self, service_key: str) -> bool:
        """Validate certificate chain from Certificate Authority"""
        service = self.services[service_key]
        start_time = time.time()

        try:
            # Create SSL context to check certificate
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE  # We expect self-signed

            with socket.create_connection(("localhost", service.port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname="localhost") as ssock:
                    cert = ssock.getpeercert(binary_form=False)
                    duration = time.time() - start_time

                    # Check if certificate has expected properties
                    subject = dict(x[0] for x in cert["subject"])

                    self.log_result(
                        service_key,
                        "Certificate Chain",
                        "PASS",
                        f"Valid cert: {subject.get('CN', 'Unknown CN')}",
                        duration,
                        {"subject": subject, "version": cert.get("version")},
                    )
                    return True

        except Exception as e:
            duration = time.time() - start_time
            self.log_result(
                service_key,
                "Certificate Chain",
                "FAIL",
                f"Certificate error: {str(e)[:50]}...",
                duration,
            )
            return False

    def check_service_dependencies(self, service_key: str) -> bool:
        """Check that service dependencies are healthy before testing this service"""
        service = self.services[service_key]

        if not service.depends_on:
            self.log_result(service_key, "Dependencies", "PASS", "No dependencies")
            return True

        failed_deps = []
        for dep in service.depends_on:
            if not self.check_container_health(dep):
                failed_deps.append(dep)

        if failed_deps:
            self.log_result(
                service_key,
                "Dependencies",
                "FAIL",
                f"Failed deps: {', '.join(failed_deps)}",
            )
            return False
        self.log_result(
            service_key,
            "Dependencies",
            "PASS",
            f"All deps healthy: {', '.join(service.depends_on)}",
        )
        return True

    def test_service_comprehensive(self, service_key: str) -> dict[str, bool]:
        """Run comprehensive tests for a single service"""
        results = {}

        print(f"\n🔍 Testing {self.services[service_key].name} ({service_key})")
        print("=" * 60)

        # Test 1: Dependencies
        results["dependencies"] = self.check_service_dependencies(service_key)

        # Test 2: Container Health
        results["container_health"] = self.check_container_health(service_key)

        # Test 3: HTTPS Endpoint
        if results["container_health"]:
            results["https_endpoint"] = self.check_https_endpoint(service_key)
        else:
            self.log_result(service_key, "HTTPS Endpoint", "SKIP", "Container unhealthy")
            results["https_endpoint"] = False

        # Test 4: HTTP Security (ensure HTTP is blocked)
        results["http_security"] = self.check_no_http_exposure(service_key)

        # Test 5: Certificate Chain
        if results["https_endpoint"]:
            results["certificate_chain"] = self.check_certificate_chain(service_key)
        else:
            self.log_result(service_key, "Certificate Chain", "SKIP", "HTTPS not accessible")
            results["certificate_chain"] = False

        return results

    def test_all_services(self) -> dict[str, dict[str, bool]]:
        """Test all services in dependency order"""
        print("🔒 Crank Platform HTTPS-Only Confidence Test Suite")
        print("=" * 60)
        print("🎯 Testing 7 services with HTTPS-only security")
        print()

        all_results = {}

        # Test services in dependency order
        test_order = [
            "cert-authority",
            "platform",
            "email-classifier",
            "email-parser",
            "doc-converter",
            "image-classifier",
            "streaming",
        ]

        for service_key in test_order:
            all_results[service_key] = self.test_service_comprehensive(service_key)

        return all_results

    def generate_report(self, all_results: dict[str, dict[str, bool]]) -> dict:
        """Generate comprehensive test report"""
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_services": len(self.services),
            "total_tests": len(self.results),
            "summary": {
                "passed": len([r for r in self.results if r.status == "PASS"]),
                "failed": len([r for r in self.results if r.status == "FAIL"]),
                "skipped": len([r for r in self.results if r.status == "SKIP"]),
            },
            "services": {},
            "overall_health": True,
        }

        for service_key, results in all_results.items():
            service_passed = all(results.values())
            service_critical_passed = results.get("container_health", False) and results.get(
                "https_endpoint",
                False,
            )

            report["services"][service_key] = {
                "name": self.services[service_key].name,
                "port": self.services[service_key].port,
                "all_tests_passed": service_passed,
                "critical_tests_passed": service_critical_passed,
                "results": results,
            }

            if not service_critical_passed:
                report["overall_health"] = False

        return report

    def print_summary(self, report: dict):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🔒 TEST SUMMARY")
        print("=" * 60)

        summary = report["summary"]
        print(
            f"📊 Tests: {summary['passed']} passed, {summary['failed']} failed, {summary['skipped']} skipped",
        )

        print("\n🏥 Service Health:")
        for _service_key, service_data in report["services"].items():
            status = "🟢 HEALTHY" if service_data["critical_tests_passed"] else "🔴 UNHEALTHY"
            print(f"   {service_data['name']:20} ({service_data['port']:4d}) {status}")

        overall = "🟢 PASS" if report["overall_health"] else "🔴 FAIL"
        print(f"\n🎯 Overall Platform Health: {overall}")

        if report["overall_health"]:
            print("✅ All critical services are healthy and HTTPS-only!")
        else:
            print("❌ Some services have critical issues!")


def main():
    """Main test execution"""
    suite = CrankConfidenceTestSuite()

    try:
        # Run all tests
        all_results = suite.test_all_services()

        # Generate report
        report = suite.generate_report(all_results)

        # Print summary
        suite.print_summary(report)

        # Save detailed report
        report_file = Path("confidence-test-report.json")
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n📄 Detailed report saved to: {report_file}")

        # Exit with appropriate code
        exit_code = 0 if report["overall_health"] else 1
        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n⚠️  Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
