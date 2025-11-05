#!/usr/bin/env python3
"""
🚀 Enhanced Crank Platform Smoke Test Suite
===========================================

Comprehensive functional testing for all 6 worker archetype patterns:
1. File conversion (in-memory) - doc-converter
2. File processing (large files) - email-parser
3. Message text classification - email-classifier
4. Still image classification (CPU) - image-classifier-cpu
5. Still image classification (GPU) - image-classifier-gpu
6. Streaming data processing - streaming

Tests validate:
✅ Container health and startup
✅ Worker registration with platform
✅ API endpoint functionality and responses
✅ Service capabilities and configuration
✅ Cross-service communication patterns
✅ Archetype-specific functionality
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import urllib3

try:
    import httpx
    import requests
except ImportError:
    print("❌ Missing dependencies. Install with: pip install httpx requests")
    sys.exit(1)

# Disable SSL warnings for development testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ArchetypeConfig:
    """Configuration for each worker archetype"""
    def __init__(self, name: str, container_name: str, port: int, service_type: str,
                 test_endpoints: List[str], capabilities: List[str], gpu_required: bool = False):
        self.name = name
        self.container_name = container_name
        self.port = port
        self.service_type = service_type
        self.test_endpoints = test_endpoints
        self.capabilities = capabilities
        self.gpu_required = gpu_required
        self.base_url = f"https://localhost:{port}"


class EnhancedSmokeTest:
    """Enhanced smoke test suite for all archetype patterns"""

    def __init__(self, compose_file: str = "docker-compose.development.yml"):
        self.compose_file = compose_file
        self.base_path = Path.cwd()

        # 6 Core Worker Archetypes
        self.archetypes = {
            "doc_converter": ArchetypeConfig(
                name="Document Conversion (In-Memory)",
                container_name="crank-doc-converter-dev",
                port=8100,
                service_type="document_conversion",
                test_endpoints=["/health", "/convert", "/docs"],
                capabilities=["pdf_to_text", "docx_to_text", "format_conversion"]
            ),
            "email_parser": ArchetypeConfig(
                name="File Processing (Large Files)",
                container_name="crank-email-parser-dev",
                port=8300,
                service_type="email_parsing",
                test_endpoints=["/health", "/parse", "/docs"],
                capabilities=["mbox_parsing", "eml_parsing", "attachment_extraction"]
            ),
            "email_classifier": ArchetypeConfig(
                name="Message Text Classification",
                container_name="crank-email-classifier-dev",
                port=8200,
                service_type="email_classification",
                test_endpoints=["/health", "/classify", "/docs"],
                capabilities=["text_classification", "sentiment_analysis", "spam_detection"]
            ),
            "image_classifier_cpu": ArchetypeConfig(
                name="Still Image Classification (CPU)",
                container_name="crank-image-classifier-cpu-dev",
                port=8401,
                service_type="image_classification",
                test_endpoints=["/health", "/classify", "/docs"],
                capabilities=["basic_classification", "cpu_inference"],
                gpu_required=False
            ),
            "image_classifier_gpu": ArchetypeConfig(
                name="Still Image Classification (GPU)",
                container_name="crank-image-classifier-gpu-dev",
                port=8400,
                service_type="image_classification",
                test_endpoints=["/health", "/classify", "/docs"],
                capabilities=["advanced_classification", "gpu_inference", "real_time_processing"],
                gpu_required=True
            ),
            "streaming": ArchetypeConfig(
                name="Streaming Data Processing",
                container_name="crank-streaming-dev",
                port=8500,
                service_type="streaming_analytics",
                test_endpoints=["/health", "/stream", "/docs"],
                capabilities=["real_time_processing", "websocket_streaming", "event_processing"]
            )
        }

        # Platform configuration
        self.platform_config = ArchetypeConfig(
            name="Crank Platform",
            container_name="crank-platform-dev",
            port=8443,
            service_type="platform",
            test_endpoints=["/health/live", "/v1/workers", "/api/docs"],
            capabilities=["worker_registration", "service_discovery", "health_monitoring"]
        )

        self.cert_authority_config = ArchetypeConfig(
            name="Certificate Authority",
            container_name="crank-cert-authority-dev",
            port=9090,
            service_type="certificate_authority",
            test_endpoints=["/health", "/ca/cert", "/api/docs"],
            capabilities=["certificate_generation", "ca_services", "mtls_support"]
        )

    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all enhanced smoke tests"""
        logger.info("🚀 Starting Enhanced Crank Platform Smoke Tests")
        logger.info("=" * 80)

        results = {
            "timestamp": datetime.now().isoformat(),
            "test_suite": "Enhanced Smoke Test",
            "total_services": len(self.archetypes) + 2,  # +2 for platform and CA
            "container_status": {},
            "health_checks": {},
            "platform_registration": {},
            "api_functionality": {},
            "archetype_validation": {},
            "cross_service_communication": {},
            "summary": {
                "passed": 0,
                "failed": 0,
                "warnings": [],
                "critical_failures": [],
                "archetype_status": {}
            }
        }

        try:
            # Phase 1: Container Health
            logger.info("📦 Phase 1: Container Health Validation")
            await self._test_container_health(results)

            # Phase 2: Basic Health Endpoints
            logger.info("🏥 Phase 2: Health Endpoint Validation")
            await self._test_health_endpoints(results)

            # Phase 3: Platform Registration
            logger.info("🔗 Phase 3: Worker Registration Validation")
            await self._test_platform_registration(results)

            # Phase 4: API Functionality
            logger.info("⚡ Phase 4: API Functionality Validation")
            await self._test_api_functionality(results)

            # Phase 5: Archetype-Specific Tests
            logger.info("🎯 Phase 5: Archetype Pattern Validation")
            await self._test_archetype_patterns(results)

            # Phase 6: Cross-Service Communication
            logger.info("🌐 Phase 6: Cross-Service Communication")
            await self._test_cross_service_communication(results)

        except Exception as e:
            logger.error(f"❌ Test suite failed with exception: {e}")
            logger.error(traceback.format_exc())
            results["summary"]["critical_failures"].append(f"Test suite exception: {e}")

        # Calculate final summary
        self._calculate_summary(results)

        return results

    async def _test_container_health(self, results: Dict[str, Any]):
        """Test container health and Docker status"""
        logger.info("  🔍 Checking Docker container status...")

        try:
            # Get container status using docker ps
            result = subprocess.run(
                ["docker", "ps", "--format", "json"],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode != 0:
                results["summary"]["critical_failures"].append(f"Docker ps failed: {result.stderr}")
                return

            # Parse container status
            containers = {}
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        container_data = json.loads(line)
                        name = container_data.get('Names', 'unknown')
                        containers[name] = {
                            'status': container_data.get('Status', 'unknown'),
                            'state': container_data.get('State', 'unknown'),
                            'ports': container_data.get('Ports', 'unknown')
                        }
                    except json.JSONDecodeError:
                        continue

            results["container_status"] = containers

            # Check if all expected containers are running
            all_expected = list(self.archetypes.values()) + [self.platform_config, self.cert_authority_config]

            for archetype in all_expected:
                if archetype.container_name not in containers:
                    results["summary"]["critical_failures"].append(
                        f"Container {archetype.container_name} not found"
                    )
                    logger.error(f"  ❌ {archetype.container_name}: NOT FOUND")
                elif 'Up' not in containers[archetype.container_name]['status']:
                    results["summary"]["warnings"].append(
                        f"Container {archetype.container_name} not running"
                    )
                    logger.warning(f"  ⚠️  {archetype.container_name}: NOT RUNNING")
                else:
                    logger.info(f"  ✅ {archetype.container_name}: Running")

        except Exception as e:
            results["summary"]["critical_failures"].append(f"Container health check failed: {e}")
            logger.error(f"  ❌ Container health check failed: {e}")

    async def _test_health_endpoints(self, results: Dict[str, Any]):
        """Test health endpoints for all services"""
        logger.info("  🏥 Testing health endpoints...")

        all_configs = list(self.archetypes.values()) + [self.platform_config, self.cert_authority_config]

        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            for config in all_configs:
                health_url = f"{config.base_url}/health"
                # Platform uses /health/live
                if config.service_type == "platform":
                    health_url = f"{config.base_url}/health/live"

                try:
                    response = await client.get(health_url)

                    health_data = {
                        "status_code": response.status_code,
                        "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
                        "healthy": response.status_code == 200,
                        "endpoint": health_url
                    }

                    # Try to parse JSON response
                    try:
                        json_response = response.json()
                        health_data["response_data"] = json_response
                        health_data["service_info"] = json_response.get("service", {})
                    except:
                        health_data["response_text"] = response.text[:200]

                    results["health_checks"][config.container_name] = health_data

                    if health_data["healthy"]:
                        logger.info(f"  ✅ {config.name}: Health OK ({health_data['response_time_ms']}ms)")
                    else:
                        logger.error(f"  ❌ {config.name}: Health FAILED (HTTP {response.status_code})")
                        results["summary"]["warnings"].append(
                            f"{config.name} health check failed: HTTP {response.status_code}"
                        )

                except Exception as e:
                    logger.error(f"  ❌ {config.name}: Health endpoint error: {e}")
                    results["health_checks"][config.container_name] = {
                        "healthy": False,
                        "error": str(e),
                        "endpoint": health_url
                    }
                    results["summary"]["warnings"].append(f"{config.name} health endpoint error: {e}")

    async def _test_platform_registration(self, results: Dict[str, Any]):
        """Test worker registration with platform"""
        logger.info("  🔗 Testing worker registration...")

        platform_url = f"{self.platform_config.base_url}/v1/workers"

        async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
            try:
                # Test 1: Get list of registered workers
                response = await client.get(platform_url, headers={
                    "Authorization": "Bearer dev-mesh-key"
                })

                if response.status_code == 200:
                    response_data = response.json()
                    # Platform returns {"workers": {"service_type": [worker_list]}}
                    workers_by_type = response_data.get("workers", {})

                    # Flatten the workers dict into a list
                    all_workers = []
                    for service_type, worker_list in workers_by_type.items():
                        for worker in worker_list:
                            worker["service_type"] = service_type  # Add service_type to worker
                            all_workers.append(worker)

                    logger.info(f"  ✅ Platform worker endpoint accessible")
                    logger.info(f"  📊 Registered workers: {len(all_workers)} found")

                    results["platform_registration"]["worker_list"] = {
                        "accessible": True,
                        "worker_count": len(all_workers),
                        "workers": all_workers,
                        "workers_by_type": workers_by_type
                    }

                    # Check if our expected workers are registered
                    registered_services = {worker.get("service_type") for worker in all_workers}
                    expected_services = {config.service_type for config in self.archetypes.values()}

                    for archetype_key, config in self.archetypes.items():
                        if config.service_type in registered_services:
                            logger.info(f"  ✅ {config.name}: Registered with platform")
                            results["platform_registration"][archetype_key] = {"registered": True}
                        else:
                            logger.warning(f"  ⚠️  {config.name}: NOT registered with platform")
                            results["platform_registration"][archetype_key] = {"registered": False}
                            results["summary"]["warnings"].append(
                                f"{config.name} not registered with platform"
                            )

                else:
                    logger.error(f"  ❌ Platform worker endpoint failed: HTTP {response.status_code}")
                    results["platform_registration"]["worker_list"] = {
                        "accessible": False,
                        "error": f"HTTP {response.status_code}",
                        "response": response.text[:200]
                    }
                    results["summary"]["critical_failures"].append(
                        f"Platform worker endpoint failed: HTTP {response.status_code}"
                    )

            except Exception as e:
                logger.error(f"  ❌ Platform registration test failed: {e}")
                results["platform_registration"]["error"] = str(e)
                results["summary"]["critical_failures"].append(f"Platform registration test failed: {e}")

    async def _test_api_functionality(self, results: Dict[str, Any]):
        """Test API functionality for each service"""
        logger.info("  ⚡ Testing API functionality...")

        async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
            for archetype_key, config in self.archetypes.items():
                logger.info(f"    🔍 Testing {config.name} APIs...")

                api_results = {
                    "service": config.name,
                    "endpoints": {},
                    "functional": False
                }

                # Test each endpoint
                for endpoint in config.test_endpoints:
                    endpoint_url = f"{config.base_url}{endpoint}"

                    try:
                        response = await client.get(endpoint_url)

                        endpoint_data = {
                            "status_code": response.status_code,
                            "accessible": response.status_code in [200, 401, 422],  # These are OK responses
                            "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2)
                        }

                        # Special handling for different endpoint types
                        if endpoint == "/health":
                            endpoint_data["functional"] = response.status_code == 200
                        elif endpoint in ["/convert", "/parse", "/classify", "/stream"]:
                            # These might return 405 (method not allowed) or 422 (validation error) which is OK for GET requests
                            endpoint_data["functional"] = response.status_code in [200, 405, 422]
                        elif endpoint in ["/docs"]:
                            # API docs should be accessible
                            endpoint_data["functional"] = response.status_code == 200
                        else:
                            endpoint_data["functional"] = response.status_code == 200

                        api_results["endpoints"][endpoint] = endpoint_data

                        if endpoint_data["functional"]:
                            logger.info(f"      ✅ {endpoint}: OK (HTTP {response.status_code})")
                        else:
                            logger.warning(f"      ⚠️  {endpoint}: Unexpected (HTTP {response.status_code})")

                    except Exception as e:
                        logger.error(f"      ❌ {endpoint}: Error - {e}")
                        api_results["endpoints"][endpoint] = {
                            "accessible": False,
                            "error": str(e)
                        }

                # Determine if service is functional
                functional_endpoints = sum(1 for ep_data in api_results["endpoints"].values()
                                         if ep_data.get("functional", False))
                api_results["functional"] = functional_endpoints >= 2  # At least health + one other

                results["api_functionality"][archetype_key] = api_results

                if api_results["functional"]:
                    logger.info(f"    ✅ {config.name}: API Functional")
                else:
                    logger.error(f"    ❌ {config.name}: API NOT Functional")
                    results["summary"]["warnings"].append(f"{config.name} API not functional")

    async def _test_archetype_patterns(self, results: Dict[str, Any]):
        """Test archetype-specific patterns"""
        logger.info("  🎯 Testing archetype-specific patterns...")

        # This is where we'd test specific functionality for each archetype
        # For now, we'll validate the expected capabilities are exposed

        for archetype_key, config in self.archetypes.items():
            pattern_results = {
                "archetype": config.name,
                "capabilities_validated": False,
                "gpu_validation": None,
                "pattern_compliance": False
            }

            # Check health endpoint response for capabilities
            health_data = results["health_checks"].get(config.container_name, {})
            if health_data.get("healthy") and "response_data" in health_data:
                response_data = health_data["response_data"]

                # Handle both dict and string responses
                if isinstance(response_data, dict):
                    service_info = response_data.get("service", {})
                    if isinstance(service_info, dict):
                        reported_capabilities = service_info.get("capabilities", [])
                    else:
                        # service_info is a string, check if it contains capability keywords
                        reported_capabilities = str(service_info).lower()
                else:
                    # response_data is a string
                    reported_capabilities = str(response_data).lower()

                # Check if expected capabilities are present
                if isinstance(reported_capabilities, list):
                    capability_match = any(cap.lower() in [rc.lower() for rc in reported_capabilities] for cap in config.capabilities)
                else:
                    # String matching for capabilities
                    capability_match = any(cap.lower() in reported_capabilities for cap in config.capabilities)

                if capability_match:
                    pattern_results["capabilities_validated"] = True
                    logger.info(f"    ✅ {config.name}: Capabilities validated")
                else:
                    logger.warning(f"    ⚠️  {config.name}: Capabilities not fully validated")
                    results["summary"]["warnings"].append(
                        f"{config.name} capabilities not fully validated"
                    )

            # GPU validation for GPU-required services
            if config.gpu_required:
                gpu_available = health_data.get("response_data", {}).get("gpu_available", False)
                pattern_results["gpu_validation"] = {
                    "required": True,
                    "available": gpu_available
                }

                if gpu_available:
                    logger.info(f"    ✅ {config.name}: GPU validation passed")
                else:
                    logger.warning(f"    ⚠️  {config.name}: GPU validation failed")
                    results["summary"]["warnings"].append(f"{config.name} GPU not available")

            # Overall pattern compliance
            pattern_results["pattern_compliance"] = (
                pattern_results["capabilities_validated"] and
                (not config.gpu_required or pattern_results.get("gpu_validation", {}).get("available", True))
            )

            results["archetype_validation"][archetype_key] = pattern_results
            results["summary"]["archetype_status"][archetype_key] = pattern_results["pattern_compliance"]

    async def _test_cross_service_communication(self, results: Dict[str, Any]):
        """Test cross-service communication patterns"""
        logger.info("  🌐 Testing cross-service communication...")

        # Test platform can reach workers
        platform_url = f"{self.platform_config.base_url}/v1/workers"

        async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
            try:
                response = await client.get(platform_url, headers={
                    "Authorization": "Bearer dev-mesh-key"
                })

                if response.status_code == 200:
                    workers = response.json()

                    communication_results = {
                        "platform_to_workers": True,
                        "worker_count": len(workers),
                        "reachable_workers": []
                    }

                    # Test if platform can reach each worker's health endpoint
                    for worker in workers:
                        endpoint = worker.get("endpoint", "")
                        if endpoint:
                            try:
                                # Extract the port from the endpoint URL
                                import re
                                port_match = re.search(r':(\d+)', endpoint)
                                if port_match:
                                    port = port_match.group(1)
                                    health_url = f"https://localhost:{port}/health"

                                    health_response = await client.get(health_url)
                                    if health_response.status_code == 200:
                                        communication_results["reachable_workers"].append(worker.get("service_type"))

                            except Exception:
                                pass  # Worker not reachable, continue

                    results["cross_service_communication"] = communication_results

                    logger.info(f"    ✅ Platform communication: {len(communication_results['reachable_workers'])}/{len(workers)} workers reachable")

                else:
                    results["cross_service_communication"] = {
                        "platform_to_workers": False,
                        "error": f"Platform endpoint failed: HTTP {response.status_code}"
                    }

            except Exception as e:
                results["cross_service_communication"] = {
                    "platform_to_workers": False,
                    "error": str(e)
                }
                logger.error(f"    ❌ Cross-service communication test failed: {e}")

    def _calculate_summary(self, results: Dict[str, Any]):
        """Calculate final test summary"""
        summary = results["summary"]

        # Count passed/failed services
        passed = 0
        failed = 0

        for archetype_key, status in summary["archetype_status"].items():
            if status:
                passed += 1
            else:
                failed += 1

        summary["passed"] = passed
        summary["failed"] = failed

        # Overall success
        summary["overall_success"] = (
            len(summary["critical_failures"]) == 0 and
            passed >= len(self.archetypes) * 0.8  # 80% success rate
        )

    def print_results(self, results: Dict[str, Any]):
        """Print comprehensive test results"""
        print("\n" + "=" * 80)
        print("📊 ENHANCED SMOKE TEST RESULTS")
        print("=" * 80)

        summary = results["summary"]

        print(f"🕐 Test Time: {results['timestamp']}")
        print(f"📦 Total Services: {results['total_services']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⚠️  Warnings: {len(summary['warnings'])}")
        print(f"🚨 Critical Failures: {len(summary['critical_failures'])}")
        print(f"🎯 Overall Success: {'✅ YES' if summary['overall_success'] else '❌ NO'}")

        print("\n🎮 ARCHETYPE STATUS:")
        for archetype_key, status in summary["archetype_status"].items():
            config = self.archetypes[archetype_key]
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {config.name}")

        if summary["critical_failures"]:
            print("\n🚨 CRITICAL FAILURES:")
            for failure in summary["critical_failures"]:
                print(f"  ❌ {failure}")

        if summary["warnings"]:
            print("\n⚠️  WARNINGS:")
            for warning in summary["warnings"]:
                print(f"  ⚠️  {warning}")

        print("\n" + "=" * 80)

    def format_json_output(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Format results for JSON output compatible with GitHub Actions"""
        # Convert to format expected by GitHub Actions parsing scripts
        json_output = {
            "timestamp": results["timestamp"],
            "total_services": results["total_services"],
            "warnings": results["summary"]["warnings"],  # This is what the parser looks for
            "critical_failures": results["summary"]["critical_failures"],
            "summary": {
                "passed": results["summary"]["passed"],
                "failed": results["summary"]["failed"],
                "warning_count": len(results["summary"]["warnings"]),
                "overall_success": results["summary"]["overall_success"]
            },
            "detailed_results": {
                "container_status": results["container_status"],
                "health_checks": results["health_checks"],
                "platform_registration": results["platform_registration"],
                "api_functionality": results["api_functionality"],
                "archetype_validation": results["archetype_validation"],
                "archetype_status": results["summary"]["archetype_status"]
            }
        }
        return json_output


async def main():
    """Main test runner"""
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced Crank Platform Smoke Test")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--compose-file", default="docker-compose.development.yml",
                       help="Docker compose file to use")

    args = parser.parse_args()

    # Create and run tests
    tester = EnhancedSmokeTest(compose_file=args.compose_file)
    results = await tester.run_comprehensive_test()

    if args.json:
        json_output = tester.format_json_output(results)
        print(json.dumps(json_output, indent=2))
    else:
        tester.print_results(results)

    # Exit with error if tests failed
    if not results["summary"]["overall_success"]:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
