#!/usr/bin/env python3
"""
🔍 Container Smoke Test Suite
Comprehensive testing for crank-platform container states, API connectivity, and resource allocation.
"""

import json
import subprocess
import sys
import time
import requests
from typing import Dict, List, Optional, Tuple
import urllib3

# Disable SSL warnings for development testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ContainerSmokeTest:
    def __init__(self, compose_file: str = "docker-compose.development.yml"):
        self.compose_file = compose_file
        self.base_path = "/home/johnr/projects/crank-platform"
        self.expected_services = {
            "crank-cert-authority-dev": {"port": 9090, "path": "/health"},
            "crank-platform-dev": {"port": 8443, "path": "/health/live"},
            "crank-email-parser-dev": {"port": 8300, "path": "/health"},
            "crank-email-classifier-dev": {"port": 8200, "path": "/health"},
            "crank-doc-converter-dev": {"port": 8100, "path": "/health"},
            "crank-image-classifier-gpu-dev": {"port": 8400, "path": "/health"},
            "crank-image-classifier-cpu-dev": {"port": 8401, "path": "/health"},
            "crank-streaming-dev": {"port": 8500, "path": "/health"},
        }

        # Expected dual classifier setup
        self.classifier_services = {
            "cpu": "crank-image-classifier-cpu-dev",
            "gpu": "crank-image-classifier-gpu-dev"
        }

        # Only check GPU allocation for services that should have GPU
        self.gpu_expected_services = [
            "crank-image-classifier-gpu-dev"
        ]

    def run_command(self, cmd: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
        """Run a shell command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.base_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)

    def get_container_status(self) -> Dict:
        """Get detailed status of all containers."""
        print("🔍 Checking container status...")

        exit_code, stdout, stderr = self.run_command([
            "docker-compose", "-f", self.compose_file, "ps", "--format", "json"
        ])

        if exit_code != 0:
            print(f"❌ Failed to get container status: {stderr}")
            return {}

        try:
            # Parse each line as JSON (docker-compose ps --format json outputs one JSON per line)
            containers = []
            for line in stdout.strip().split('\n'):
                if line.strip():
                    containers.append(json.loads(line))

            status = {}
            for container in containers:
                name = container.get('Name', 'unknown')
                status[name] = {
                    'state': container.get('State', 'unknown'),
                    'health': container.get('Health', 'unknown'),
                    'ports': container.get('Publishers', []),
                    'service': container.get('Service', 'unknown')
                }

            return status
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse container status JSON: {e}")
            return {}

    def check_gpu_allocation(self, container_name: str) -> Dict:
        """Check if container has GPU resources allocated."""
        print(f"🎮 Checking GPU allocation for {container_name}...")

        exit_code, stdout, stderr = self.run_command([
            "docker", "inspect", container_name
        ])

        if exit_code != 0:
            return {"error": f"Failed to inspect container: {stderr}"}

        try:
            inspection = json.loads(stdout)
            if not inspection:
                return {"error": "No container data returned"}

            container_data = inspection[0]
            host_config = container_data.get('HostConfig', {})
            device_requests = host_config.get('DeviceRequests', []) or []

            gpu_info = {
                "has_gpu_allocation": len(device_requests) > 0,
                "device_requests": device_requests,
                "runtime": container_data.get('HostConfig', {}).get('Runtime'),
            }

            return gpu_info

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            return {"error": f"Failed to parse inspection data: {e}"}

    def test_service_health(self, service_name: str, port: int, path: str) -> Dict:
        """Test if a service responds to health checks."""
        url = f"https://localhost:{port}{path}"
        print(f"🏥 Testing health endpoint: {url}")

        try:
            response = requests.get(
                url,
                verify=False,
                timeout=10,
                headers={'User-Agent': 'CrankPlatform-SmokeTest/1.0'}
            )

            health_data = {
                "status_code": response.status_code,
                "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
                "healthy": response.status_code == 200
            }

            # Try to parse JSON response
            try:
                json_response = response.json()
                health_data["response_data"] = json_response
                health_data["gpu_available"] = json_response.get("gpu_available", "unknown")
            except:
                health_data["response_text"] = response.text[:200]

            return health_data

        except requests.RequestException as e:
            return {
                "healthy": False,
                "error": str(e),
                "status_code": None
            }

    def test_platform_worker_endpoints(self) -> Dict:
        """Test platform worker registration endpoints."""
        print("🔗 Testing platform worker endpoints...")

        base_url = "https://localhost:8443"
        # Critical endpoints that MUST work
        critical_endpoints = [
            {"path": "/v1/workers", "expected_codes": [401], "description": "Worker registration (auth required)"},
            {"path": "/health/live", "expected_codes": [200], "description": "Platform health check"},
        ]

        # Standard endpoints that should exist (principle of least surprise)
        expected_endpoints = [
            {"path": "/api/docs", "expected_codes": [200, 401], "description": "API documentation"},
            {"path": "/health", "expected_codes": [200], "description": "Basic health check"},
            {"path": "/metrics", "expected_codes": [200, 401], "description": "Prometheus/metrics endpoint"},
            {"path": "/version", "expected_codes": [200], "description": "Service version info"},
            {"path": "/status", "expected_codes": [200], "description": "Detailed status info"},
            {"path": "/api/v1", "expected_codes": [200, 401], "description": "API root/discovery"},
        ]

        results = {"critical": {}, "expected": {}}

        # Test critical endpoints
        for endpoint_info in critical_endpoints:
            endpoint = endpoint_info["path"]
            url = f"{base_url}{endpoint}"
            try:
                response = requests.get(url, verify=False, timeout=5)
                is_expected = response.status_code in endpoint_info["expected_codes"]
                results["critical"][endpoint] = {
                    "status_code": response.status_code,
                    "accessible": is_expected,
                    "description": endpoint_info["description"],
                    "critical": True
                }
            except Exception as e:
                results["critical"][endpoint] = {
                    "status_code": None,
                    "accessible": False,
                    "description": endpoint_info["description"],
                    "error": str(e),
                    "critical": True
                }

        # Test expected endpoints (for warnings)
        for endpoint_info in expected_endpoints:
            endpoint = endpoint_info["path"]
            url = f"{base_url}{endpoint}"
            try:
                response = requests.get(url, verify=False, timeout=5)
                is_expected = response.status_code in endpoint_info["expected_codes"]
                results["expected"][endpoint] = {
                    "status_code": response.status_code,
                    "accessible": is_expected,
                    "description": endpoint_info["description"],
                    "critical": False
                }
            except Exception as e:
                results["expected"][endpoint] = {
                    "status_code": None,
                    "accessible": False,
                    "description": endpoint_info["description"],
                    "error": str(e),
                    "critical": False
                }

        return results

    def run_comprehensive_test(self) -> Dict:
        """Run all smoke tests and return comprehensive results."""
        print("🚀 Starting comprehensive container smoke test...")
        print("=" * 60)

        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "container_status": {},
            "health_checks": {},
            "gpu_allocations": {},
            "platform_endpoints": {},
            "warnings": [],
            "summary": {
                "total_services": len(self.expected_services),
                "healthy_services": 0,
                "gpu_enabled_services": 0,
                "failed_services": [],
                "warning_count": 0
            }
        }

        # 1. Check container status
        container_status = self.get_container_status()
        results["container_status"] = container_status

        # 2. Test health endpoints
        for service_name, config in self.expected_services.items():
            if service_name in container_status:
                health_result = self.test_service_health(
                    service_name, config["port"], config["path"]
                )
                results["health_checks"][service_name] = health_result

                if health_result.get("healthy", False):
                    results["summary"]["healthy_services"] += 1
                else:
                    results["summary"]["failed_services"].append(service_name)
            else:
                results["health_checks"][service_name] = {
                    "healthy": False,
                    "error": "Container not found"
                }
                results["summary"]["failed_services"].append(service_name)

        # 3. Check GPU allocations only for GPU-expected services
        for service_name in self.gpu_expected_services:
            if service_name in container_status:
                gpu_info = self.check_gpu_allocation(service_name)
                results["gpu_allocations"][service_name] = gpu_info

                if gpu_info.get("has_gpu_allocation", False):
                    results["summary"]["gpu_enabled_services"] += 1

        # 4. Test platform endpoints
        results["platform_endpoints"] = self.test_platform_worker_endpoints()

        # 5. Collect warnings
        self._collect_warnings(results)

        return results

    def _collect_warnings(self, results: Dict):
        """Collect all warnings for the summary."""
        warnings = []

        # GPU warnings
        for service, gpu_info in results["gpu_allocations"].items():
            if gpu_info.get("has_gpu_allocation", False):
                # Check if GPU is allocated but not detected in health
                health_data = results["health_checks"].get(service, {}).get("response_data", {})
                if not health_data.get("gpu_available", False):
                    warnings.append(f"GPU allocated to {service} but not detected at runtime - missing GPU libraries?")

        # Missing expected endpoints
        expected_endpoints = results["platform_endpoints"].get("expected", {})
        for endpoint, info in expected_endpoints.items():
            if not info.get("accessible", False):
                code = info.get("status_code", "N/A")
                warnings.append(f"Expected endpoint {endpoint} not available (HTTP {code}) - {info.get('description', '')}")

        # Service-specific warnings
        for service, health in results["health_checks"].items():
            response_time = health.get("response_time_ms", 0)
            if response_time > 5000:  # > 5 seconds
                warnings.append(f"{service} slow response time: {response_time}ms")

        results["warnings"] = warnings
        results["summary"]["warning_count"] = len(warnings)

    def print_results(self, results: Dict):
        """Pretty print test results."""
        print("\n" + "=" * 60)
        print("📊 SMOKE TEST RESULTS SUMMARY")
        print("=" * 60)

        summary = results["summary"]
        print(f"🕐 Test Time: {results['timestamp']}")
        print(f"📦 Total Services: {summary['total_services']}")
        print(f"✅ Healthy Services: {summary['healthy_services']}")
        print(f"🎮 GPU Enabled Services: {summary['gpu_enabled_services']}")
        print(f"⚠️  Warnings: {summary['warning_count']}")

        if summary["failed_services"]:
            print(f"❌ Failed Services: {', '.join(summary['failed_services'])}")

        print("\n🏥 HEALTH CHECK DETAILS:")
        for service, health in results["health_checks"].items():
            status = "✅" if health.get("healthy") else "❌"

            # Handle GPU status more intelligently
            gpu_status = ""
            if "image-classifier" in service:
                gpu_available = health.get("response_data", {}).get("gpu_available", "unknown")
                gpu_allocated = results["gpu_allocations"].get(service, {}).get("has_gpu_allocation", False)

                if "gpu" in service:
                    # This is the GPU classifier - should have GPU
                    if gpu_available:
                        gpu_status = " (GPU: ✅ Active)"
                    elif gpu_allocated:
                        gpu_status = " (GPU: ⚠️ Allocated but not detected)"
                    else:
                        gpu_status = " (GPU: ❌ Not allocated)"
                elif "cpu" in service:
                    # This is the CPU classifier - should NOT have GPU
                    if not gpu_available and not gpu_allocated:
                        gpu_status = " (CPU-only: ✅)"
                    else:
                        gpu_status = " (CPU-only: ⚠️ Unexpected GPU)"

            print(f"{status} {service}{gpu_status}")
            if health.get("error"):
                print(f"   Error: {health['error']}")

        print("\n🎮 GPU ALLOCATION DETAILS:")
        if results["gpu_allocations"]:
            for service, gpu_info in results["gpu_allocations"].items():
                if gpu_info.get("error"):
                    print(f"❌ {service}: {gpu_info['error']}")
                else:
                    has_gpu = gpu_info.get("has_gpu_allocation", False)
                    status = "✅" if has_gpu else "❌"
                    print(f"{status} {service}: GPU allocation = {has_gpu}")
        else:
            print("No GPU-expected services configured")

        print("\n🔗 PLATFORM ENDPOINT STATUS:")

        # Show critical endpoints
        critical_endpoints = results["platform_endpoints"].get("critical", {})
        for endpoint, info in critical_endpoints.items():
            if info.get("accessible", False):
                status = "✅"
                description = info.get("description", "")
                code = info.get("status_code", "N/A")
                print(f"{status} {endpoint}: HTTP {code} - {description}")
            else:
                status = "❌"
                code = info.get("status_code", "N/A")
                error = info.get("error", "Failed")
                print(f"{status} {endpoint}: HTTP {code} - {error}")

        # Show warnings section
        if results["warnings"]:
            print(f"\n⚠️  WARNINGS ({len(results['warnings'])} items for worklist):")
            for i, warning in enumerate(results["warnings"], 1):
                print(f"  {i}. {warning}")
        else:
            print(f"\n✅ NO WARNINGS - All systems optimal!")

def main():
    """Main smoke test execution."""
    if len(sys.argv) > 1:
        compose_file = sys.argv[1]
    else:
        compose_file = "docker-compose.development.yml"

    print(f"🔥 Running smoke tests with {compose_file}")

    smoke_test = ContainerSmokeTest(compose_file)
    results = smoke_test.run_comprehensive_test()
    smoke_test.print_results(results)

    # Exit with error code if any services failed
    if results["summary"]["failed_services"]:
        print(f"\n❌ {len(results['summary']['failed_services'])} services failed!")
        sys.exit(1)
    else:
        print("\n✅ All services are healthy!")
        sys.exit(0)

if __name__ == "__main__":
    main()
