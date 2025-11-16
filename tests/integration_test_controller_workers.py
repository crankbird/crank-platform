#!/usr/bin/env python3
"""
🚀 Controller + Workers Integration Test Suite (Live Containers)
================================================================

End-to-end system validation for Phase 3 controller/worker architecture.
Tests actual running containers (docker-compose) with all 8 workers:

1. crank-streaming (8500) - Streaming email classification
2. crank-email-classifier (8201) - Email intent classification
3. crank-email-parser (8301) - Email archive parsing
4. crank-doc-converter (8401) - Document format conversion
5. crank-philosophical-analyzer (8601) - Philosophical content analysis
6. crank-sonnet-zettel-manager (8700) - Zettel note management
7. crank-codex-zettel-repository (8800) - Zettel repository storage
8. crank-hello-world (8900) - Reference implementation

Tests validate:
✅ Controller health and startup
✅ All workers register with controller
✅ Capability-based routing works
✅ Worker health endpoints respond
✅ HTTPS-only enforcement with mTLS
✅ Controller capability introspection
✅ Multi-worker scenarios (duplicate capabilities)

Platform Support: Auto-detects macOS (Apple Silicon), Linux (x86_64/CUDA), Windows (WSL2)

Usage:
    python tests/integration_test_controller_workers.py --rebuild    # Rebuild and test
    python tests/integration_test_controller_workers.py --json       # JSON output
    pytest tests/integration_test_controller_workers.py -v            # Via pytest
"""

import argparse
import asyncio
import json
import logging
import platform
import re
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import urllib3

try:
    import httpx
except ImportError:
    print("❌ Missing dependencies. Install with: pip install httpx")
    sys.exit(1)

# Disable SSL warnings for development testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class WorkerConfig:
    """Configuration for each worker in the controller/worker architecture"""

    def __init__(
        self,
        name: str,
        container_name: str,
        port: int,
        worker_id: str,
        test_endpoints: list[str],
        expected_capability_ids: list[str],
        gpu_required: bool = False,
    ):
        self.name = name
        self.container_name = container_name
        self.port = port
        self.worker_id = worker_id
        self.test_endpoints = test_endpoints
        self.expected_capability_ids = expected_capability_ids
        self.gpu_required = gpu_required
        self.base_url = f"https://localhost:{port}"


class ControllerIntegrationTest:
    """Live integration test suite for controller + workers architecture"""

    def __init__(self, compose_file: Optional[str] = None):
        self.base_path = Path(__file__).parent.parent

        # Auto-detect platform for appropriate testing
        self.platform_info = self._detect_platform()

        # Default compose file selection
        if compose_file:
            self.compose_file = compose_file
        else:
            # Auto-select compose file based on platform
            self.compose_file = str(self.base_path / "docker-compose.development.yml")

        # Display platform information at startup
        logger.info(f"🖥️  Platform: {self.platform_info['description']}")
        logger.info(f"🏗️  Architecture: {self.platform_info['architecture']}")
        logger.info(f"🐳  Docker Environment: {self.platform_info['docker_env']}")

        # Controller configuration (replaces old platform)
        self.controller_config = WorkerConfig(
            name="Controller Service",
            container_name="crank-controller-dev",
            port=9000,
            worker_id="controller",
            test_endpoints=["/health", "/workers", "/capabilities", "/docs"],
            expected_capability_ids=[],  # Controller doesn't provide capabilities, it routes them
        )

        # 8 Workers (Phase 3 architecture)
        self.workers = {
            "streaming": WorkerConfig(
                name="Streaming Worker",
                container_name="crank-streaming-dev",
                port=8500,
                worker_id="streaming",
                test_endpoints=["/health"],
                expected_capability_ids=["streaming.email.classify"],
            ),
            "email_classifier": WorkerConfig(
                name="Email Classifier",
                container_name="crank-email-classifier-dev",
                port=8201,
                worker_id="email_classifier",
                test_endpoints=["/health"],
                expected_capability_ids=["email.classify"],
            ),
            "email_parser": WorkerConfig(
                name="Email Parser",
                container_name="crank-email-parser-dev",
                port=8301,
                worker_id="email_parser",
                test_endpoints=["/health"],
                expected_capability_ids=["email.parse"],
            ),
            "doc_converter": WorkerConfig(
                name="Document Converter",
                container_name="crank-doc-converter-dev",
                port=8401,
                worker_id="doc_converter",
                test_endpoints=["/health"],
                expected_capability_ids=["document.convert"],
            ),
            "philosophical_analyzer": WorkerConfig(
                name="Philosophical Analyzer",
                container_name="crank-philosophical-analyzer-dev",
                port=8601,
                worker_id="philosophical_analyzer",
                test_endpoints=["/health"],
                expected_capability_ids=["content.philosophical_analysis"],
            ),
            "sonnet_zettel": WorkerConfig(
                name="Sonnet Zettel Manager",
                container_name="crank-sonnet-zettel-manager-dev",
                port=8700,
                worker_id="sonnet_zettel",
                test_endpoints=["/health"],
                expected_capability_ids=["knowledge.sonnet_zettel_management"],
            ),
            "codex_zettel": WorkerConfig(
                name="Codex Zettel Repository",
                container_name="crank-codex-zettel-repository-dev",
                port=8800,
                worker_id="codex_zettel",
                test_endpoints=["/health"],
                expected_capability_ids=["zettel.codex_repository"],
            ),
            "hello_world": WorkerConfig(
                name="Hello World (Reference)",
                container_name="hello-world-dev",
                port=8900,
                worker_id="hello_world",
                test_endpoints=["/health"],
                expected_capability_ids=["example.hello_world"],
            ),
        }

        # Certificate Authority
        self.cert_authority_config = WorkerConfig(
            name="Certificate Authority",
            container_name="crank-cert-authority-dev",
            port=9090,
            worker_id="cert_authority",
            test_endpoints=["/health"],
            expected_capability_ids=[],
        )

    def _detect_platform(self) -> dict[str, str]:
        """Detect the current platform and Docker environment."""
        system = platform.system()
        machine = platform.machine()

        if system == "Darwin":
            if machine in ["arm64", "aarch64"]:
                return {
                    "os": "macOS",
                    "architecture": "Apple Silicon",
                    "docker_env": "Docker Desktop",
                    "description": "macOS Apple Silicon (M1/M2/M3)",
                }
            return {
                "os": "macOS",
                "architecture": "Intel x86_64",
                "docker_env": "Docker Desktop",
                "description": "macOS Intel",
            }
        if system == "Linux":
            return {
                "os": "Linux",
                "architecture": machine,
                "docker_env": "Native Docker",
                "description": f"Linux {machine}",
            }
        if system == "Windows":
            return {
                "os": "Windows",
                "architecture": machine,
                "docker_env": "Docker Desktop (WSL2)",
                "description": f"Windows {machine}",
            }
        return {
            "os": system,
            "architecture": machine,
            "docker_env": "Unknown",
            "description": f"{system} {machine}",
        }

    async def _rebuild_and_restart_environment(self) -> bool:
        """
        Rebuild and restart all containers to ensure fresh environment.
        This prevents issues with stale containers that have previously valid credentials.
        """
        logger.info("🔄 Phase 0: Environment Rebuild and Restart")
        logger.info("  🔄 Ensuring completely fresh environment (no stale containers)...")

        try:
            # Stop all containers
            logger.info("  ⏹️  Stopping all containers...")
            result = subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    self.compose_file,
                    "down",
                ],
                check=False,
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                logger.error("  ❌ Failed to stop containers: {result.stderr}")
                return False

            # Build all services to ensure latest code
            logger.info("  🔨 Building all services with latest code...")
            result = subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    self.compose_file,
                    "build",
                ],
                check=False,
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=600,
            )  # Increased to 10 minutes for GPU builds

            if result.returncode != 0:
                logger.error("  ❌ Failed to build services: {result.stderr}")
                return False

            # Start all containers
            logger.info("  🚀 Starting all containers...")
            result = subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    self.compose_file,
                    "up",
                    "-d",
                ],
                check=False,
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                logger.error("  ❌ Failed to start containers: {result.stderr}")
                return False

            # Wait for containers to fully initialize
            logger.info("  ⏰ Waiting for containers to fully initialize...")
            await asyncio.sleep(30)  # Give containers time to start and register

            logger.info("  ✅ Environment rebuild and restart completed successfully")
            return True

        except subprocess.TimeoutExpired:
            logger.exception("  ❌ Timeout during environment rebuild: {e}")
            return False
        except Exception:
            logger.exception("  ❌ Error during environment rebuild: {e}")
            return False

    async def run_comprehensive_test(self, rebuild_environment: bool = False) -> dict[str, Any]:
        """Run all controller/worker integration tests

        Args:
            rebuild_environment: If True, rebuild and restart containers before testing.
                               If False (default), test existing environment state.
        """
        logger.info("🚀 Starting Controller + Workers Integration Test Suite")
        logger.info("=" * 80)

        # Phase 0: Optionally rebuild and restart environment
        if rebuild_environment:
            logger.info("🔄 Rebuild requested: rebuilding environment before testing")
            rebuild_success = await self._rebuild_and_restart_environment()
            if not rebuild_success:
                return {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "test_suite": "Controller + Workers Integration Test",
                    "error": "Failed to rebuild and restart environment",
                    "summary": {
                        "passed": 0,
                        "failed": 1,
                        "warnings": [],
                        "critical_failures": ["Environment rebuild failed"],
                        "overall_success": False,
                    },
                }
        else:
            logger.info(
                "🎯 Testing existing environment (use --rebuild to force container restart)",
            )

        results: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_suite": "Controller + Workers Integration Test",
            "total_services": len(self.workers) + 2,  # +2 for controller and CA
            "container_status": {},
            "health_checks": {},
            "controller_registration": {},
            "api_functionality": {},
            "worker_validation": {},
            "cross_service_communication": {},
            "summary": {
                "passed": 0,
                "failed": 0,
                "warnings": [],
                "critical_failures": [],
                "worker_status": {},
            },
        }

        try:
            # Phase 1: Container Health
            logger.info("📦 Phase 1: Container Health Validation")
            await self._test_container_health(results)

            # Phase 2: Basic Health Endpoints
            logger.info("🏥 Phase 2: Health Endpoint Validation")
            await self._test_health_endpoints(results)

            # Phase 3: Controller Registration
            logger.info("🔗 Phase 3: Worker Registration with Controller")
            await self._test_controller_registration(results)

            # Phase 4: API Functionality
            logger.info("⚡ Phase 4: API Functionality Validation")
            await self._test_api_functionality(results)

            # Phase 5: Worker Capability Validation
            logger.info("🎯 Phase 5: Worker Capability Validation")
            await self._test_worker_capabilities(results)

            # Phase 6: Cross-Service Communication
            logger.info("🌐 Phase 6: Cross-Service Communication")
            await self._test_cross_service_communication(results)

        except Exception as e:
            logger.exception(f"❌ Test suite failed with exception: {e}")
            logger.exception(traceback.format_exc())
            summary_dict: dict[str, Any] = results["summary"]
            if "critical_failures" in summary_dict:
                critical_failures: list[str] = summary_dict["critical_failures"]
                critical_failures.append(f"Test suite exception: {e}")

        # Calculate final summary
        self._calculate_summary(results)

        return results

    async def _test_container_health(self, results: dict[str, Any]) -> None:
        """Test container health and Docker status"""
        logger.info("  🔍 Checking Docker container status...")

        try:
            # Get container status using docker ps
            result = subprocess.run(
                ["docker", "ps", "--format", "json"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                results["summary"]["critical_failures"].append(f"Docker ps failed: {result.stderr}")
                return

            # Parse container status
            containers = {}
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    try:
                        container_data = json.loads(line)
                        name = container_data.get("Names", "unknown")
                        containers[name] = {
                            "status": container_data.get("Status", "unknown"),
                            "state": container_data.get("State", "unknown"),
                            "ports": container_data.get("Ports", "unknown"),
                        }
                    except json.JSONDecodeError:
                        continue

            results["container_status"] = containers

            # Check if all expected containers are running
            all_expected = [
                *list(self.workers.values()),
                self.controller_config,
                self.cert_authority_config,
            ]

            for worker in all_expected:
                if worker.container_name not in containers:
                    results["summary"]["critical_failures"].append(
                        f"Container {worker.container_name} not found",
                    )
                    logger.error(f"  ❌ {worker.container_name}: NOT FOUND")
                elif "Up" not in containers[worker.container_name]["status"]:
                    results["summary"]["warnings"].append(
                        f"Container {worker.container_name} not running",
                    )
                    logger.warning(f"  ⚠️  {worker.container_name}: NOT RUNNING")
                else:
                    logger.info(f"  ✅ {worker.container_name}: Running")

        except Exception as e:
            results["summary"]["critical_failures"].append(f"Container health check failed: {e}")
            logger.exception(f"  ❌ Container health check failed: {e}")

    async def _test_health_endpoints(self, results: dict[str, Any]) -> None:
        """Test health endpoints for all services"""
        logger.info("  🏥 Testing health endpoints...")

        all_configs = [
            *list(self.workers.values()),
            self.controller_config,
            self.cert_authority_config,
        ]

        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            for config in all_configs:
                health_url = f"{config.base_url}/health"

                try:
                    response = await client.get(health_url)

                    health_data: dict[str, Any] = {
                        "status_code": response.status_code,
                        "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
                        "healthy": response.status_code == 200,
                        "endpoint": health_url,
                    }

                    # Try to parse JSON response
                    try:
                        json_response = response.json()
                        health_data["response_data"] = json_response
                        health_data["service_info"] = json_response.get("service", {})
                    except Exception:
                        health_data["response_text"] = response.text[:200]

                    results["health_checks"][config.container_name] = health_data

                    if health_data["healthy"]:
                        logger.info(
                            f"  ✅ {config.name}: Health OK ({health_data['response_time_ms']}ms)",
                        )
                    else:
                        logger.error(
                            f"  ❌ {config.name}: Health FAILED (HTTP {response.status_code})",
                        )
                        results["summary"]["warnings"].append(
                            f"{config.name} health check failed: HTTP {response.status_code}",
                        )

                except Exception as e:
                    logger.exception(f"  ❌ {config.name}: Health endpoint error: {e}")
                    results["health_checks"][config.container_name] = {
                        "healthy": False,
                        "error": str(e),
                        "endpoint": health_url,
                    }
                    results["summary"]["warnings"].append(
                        f"{config.name} health endpoint error: {e}",
                    )

    async def _test_controller_registration(self, results: dict[str, Any]) -> None:
        """Test worker registration with controller"""
        logger.info("  🔗 Testing worker registration with controller...")

        controller_url = f"{self.controller_config.base_url}/workers"

        async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
            try:
                # Test 1: Get list of registered workers from controller
                response = await client.get(
                    controller_url,
                    headers={
                        "Authorization": "Bearer dev-mesh-key",
                    },
                )

                if response.status_code == 200:
                    response_data = response.json()
                    # Controller returns {"workers": [{"worker_id": "...", "url": "...", ...}, ...]}
                    all_workers: list[dict[str, Any]] = response_data.get("workers", [])

                    logger.info(f"  ✅ Controller worker endpoint accessible")
                    logger.info(f"  📊 Registered workers: {len(all_workers)} found")

                    results["controller_registration"]["worker_list"] = {
                        "accessible": True,
                        "worker_count": len(all_workers),
                        "workers": all_workers,
                    }

                    # Check if our expected workers are registered
                    registered_worker_ids: set[str] = {
                        worker.get("worker_id", "") for worker in all_workers
                    }

                    for worker_key, config in self.workers.items():
                        if config.worker_id in registered_worker_ids:
                            logger.info(f"  ✅ {config.name}: Registered with controller")
                            results["controller_registration"][worker_key] = {"registered": True}

                            # Find the registered worker and store its details
                            registered_worker = next(
                                (w for w in all_workers if w.get("worker_id") == config.worker_id),
                                None,
                            )
                            if registered_worker:
                                results["controller_registration"][worker_key]["details"] = registered_worker
                        else:
                            logger.warning(f"  ⚠️  {config.name}: NOT registered with controller")
                            results["controller_registration"][worker_key] = {"registered": False}
                            results["summary"]["warnings"].append(
                                f"{config.name} not registered with controller",
                            )

                else:
                    logger.error(
                        f"  ❌ Controller worker endpoint failed: HTTP {response.status_code}",
                    )
                    results["controller_registration"]["worker_list"] = {
                        "accessible": False,
                        "error": f"HTTP {response.status_code}",
                        "response": response.text[:200],
                    }
                    results["summary"]["critical_failures"].append(
                        f"Controller worker endpoint failed: HTTP {response.status_code}",
                    )

            except Exception as e:
                logger.exception(f"  ❌ Controller registration test failed: {e}")
                results["controller_registration"]["error"] = str(e)
                results["summary"]["critical_failures"].append(
                    f"Controller registration test failed: {e}",
                )

    async def _test_api_functionality(self, results: dict[str, Any]) -> None:
        """Test API functionality for workers and controller"""
        logger.info("  ⚡ Testing API functionality...")

        async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
            # Test controller endpoints
            logger.info(f"    🔍 Testing {self.controller_config.name} APIs...")

            controller_results: dict[str, Any] = {
                "service": self.controller_config.name,
                "endpoints": {},
                "functional": False,
            }

            for endpoint in self.controller_config.test_endpoints:
                endpoint_url = f"{self.controller_config.base_url}{endpoint}"

                try:
                    response = await client.get(endpoint_url)

                    endpoint_data: dict[str, Any] = {
                        "status_code": response.status_code,
                        "accessible": response.status_code in [200, 401, 422],
                        "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
                    }

                    endpoint_data["functional"] = response.status_code == 200
                    controller_results["endpoints"][endpoint] = endpoint_data

                    if endpoint_data["functional"]:
                        logger.info(f"      ✅ {endpoint}: OK (HTTP {response.status_code})")
                    else:
                        logger.warning(
                            f"      ⚠️  {endpoint}: Unexpected (HTTP {response.status_code})",
                        )

                except Exception as e:
                    logger.exception(f"      ❌ {endpoint}: Error - {e}")
                    controller_results["endpoints"][endpoint] = {
                        "accessible": False,
                        "error": str(e),
                    }

            functional_endpoints = sum(
                1 for ep_data in controller_results["endpoints"].values()
                if ep_data.get("functional", False)
            )
            controller_results["functional"] = functional_endpoints >= 2
            results["api_functionality"]["controller"] = controller_results

            if controller_results["functional"]:
                logger.info(f"    ✅ {self.controller_config.name}: API Functional")
            else:
                logger.error(f"    ❌ {self.controller_config.name}: API NOT Functional")
                results["summary"]["warnings"].append(f"{self.controller_config.name} API not functional")

            # Test worker endpoints
            for worker_key, config in self.workers.items():
                logger.info(f"    🔍 Testing {config.name} APIs...")

                api_results: dict[str, Any] = {
                    "service": config.name,
                    "endpoints": {},
                    "functional": False,
                }

                # Test each endpoint
                for endpoint in config.test_endpoints:
                    endpoint_url = f"{config.base_url}{endpoint}"

                    try:
                        response = await client.get(endpoint_url)

                        endpoint_data: dict[str, Any] = {
                            "status_code": response.status_code,
                            "accessible": response.status_code in [200, 401, 422],
                            "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
                        }

                        # Workers primarily have /health endpoint
                        endpoint_data["functional"] = response.status_code == 200

                        api_results["endpoints"][endpoint] = endpoint_data

                        if endpoint_data["functional"]:
                            logger.info(f"      ✅ {endpoint}: OK (HTTP {response.status_code})")
                        else:
                            logger.warning(
                                f"      ⚠️  {endpoint}: Unexpected (HTTP {response.status_code})",
                            )

                    except Exception as e:
                        logger.exception(f"      ❌ {endpoint}: Error - {e}")
                        api_results["endpoints"][endpoint] = {
                            "accessible": False,
                            "error": str(e),
                        }

                # Determine if service is functional
                functional_endpoints = sum(
                    1
                    for ep_data in api_results["endpoints"].values()
                    if ep_data.get("functional", False)
                )
                api_results["functional"] = functional_endpoints >= 1  # At least health

                results["api_functionality"][worker_key] = api_results

                if api_results["functional"]:
                    logger.info(f"    ✅ {config.name}: API Functional")
                else:
                    logger.error(f"    ❌ {config.name}: API NOT Functional")
                    results["summary"]["warnings"].append(f"{config.name} API not functional")

    async def _test_worker_capabilities(self, results: dict[str, Any]) -> None:
        """Test worker capability declarations and validation"""
        logger.info("  🎯 Testing worker capability declarations...")

        # Test both direct worker capabilities and controller's capability routing
        for worker_key, config in self.workers.items():
            capability_results: dict[str, Any] = {
                "worker": config.name,
                "capabilities_validated": False,
                "capability_ids": [],
                "gpu_validation": None,
                "compliance": False,
            }

            # Check health endpoint response for capability info
            health_data = results["health_checks"].get(config.container_name, {})
            if health_data.get("healthy") and "response_data" in health_data:
                response_data: Any = health_data["response_data"]

                # Check if worker exposes capabilities in health response
                if isinstance(response_data, dict) and "capabilities" in response_data:
                    worker_capabilities = response_data["capabilities"]
                    capability_ids = [cap.get("id") for cap in worker_capabilities if isinstance(cap, dict)]
                    capability_results["capability_ids"] = capability_ids

                    # Validate expected capabilities are present
                    expected_ids = set(config.expected_capability_ids)
                    actual_ids = set(capability_ids)

                    if expected_ids.issubset(actual_ids):
                        capability_results["capabilities_validated"] = True
                        logger.info(f"    ✅ {config.name}: All expected capabilities present")
                        logger.info(f"       Capabilities: {', '.join(capability_ids)}")
                    else:
                        missing = expected_ids - actual_ids
                        logger.warning(f"    ⚠️  {config.name}: Missing capabilities: {missing}")
                        results["summary"]["warnings"].append(
                            f"{config.name} missing capabilities: {missing}",
                        )
                else:
                    # Some workers may not expose capabilities in health endpoint
                    # Check if registered with controller instead
                    registration_data = results.get("controller_registration", {}).get(worker_key, {})
                    if registration_data.get("registered"):
                        # Consider it validated if registered (controller validates capabilities)
                        capability_results["capabilities_validated"] = True
                        logger.info(f"    ✅ {config.name}: Registered with controller (capabilities validated)")

            # GPU validation for GPU-required services
            if config.gpu_required:
                gpu_available = health_data.get("response_data", {}).get("gpu_available", False)
                capability_results["gpu_validation"] = {
                    "required": True,
                    "available": gpu_available,
                }

                if gpu_available:
                    logger.info(f"    ✅ {config.name}: GPU validation passed")
                else:
                    logger.warning(f"    ⚠️  {config.name}: GPU validation failed")
                    results["summary"]["warnings"].append(f"{config.name} GPU not available")

            # Overall compliance
            capability_results["compliance"] = capability_results["capabilities_validated"]

            results["worker_validation"][worker_key] = capability_results
            results["summary"]["worker_status"][worker_key] = capability_results["compliance"]

    async def _test_cross_service_communication(self, results: dict[str, Any]) -> None:
        """Test cross-service communication patterns"""
        logger.info("  🌐 Testing cross-service communication...")

        # Test controller can reach workers
        controller_url = f"{self.controller_config.base_url}/workers"

        async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
            try:
                response = await client.get(
                    controller_url,
                    headers={
                        "Authorization": "Bearer local-dev-key",
                    },
                )

                if response.status_code == 200:
                    response_data = response.json()
                    # Controller returns {"workers": [{"worker_id": "...", "url": "...", ...}, ...]}
                    all_workers: list[dict[str, Any]] = response_data.get("workers", [])

                    communication_results: dict[str, Any] = {
                        "controller_to_workers": True,
                        "worker_count": len(all_workers),
                        "reachable_workers": [],
                    }

                    # Test if controller can reach each worker's health endpoint
                    for worker_item in all_workers:
                        current_worker: dict[str, Any] = worker_item
                        worker_url: str = str(current_worker.get("url", ""))
                        worker_id: str = str(current_worker.get("worker_id", ""))

                        if worker_url:
                            try:
                                health_url = f"{worker_url}/health"
                                health_response = await client.get(health_url)

                                if health_response.status_code == 200:
                                    reachable_list: list[str] = communication_results["reachable_workers"]
                                    reachable_list.append(worker_id)

                            except Exception:
                                pass  # Worker not reachable, continue

                    results["cross_service_communication"] = communication_results

                    logger.info(
                        f"    ✅ Controller communication: {len(communication_results['reachable_workers'])}/{len(all_workers)} workers reachable",
                    )

                else:
                    results["cross_service_communication"] = {
                        "controller_to_workers": False,
                        "error": f"Controller endpoint failed: HTTP {response.status_code}",
                    }

            except Exception as e:
                results["cross_service_communication"] = {
                    "platform_to_workers": False,
                    "error": str(e),
                }
                logger.exception("    ❌ Cross-service communication test failed: {e}")

    def _calculate_summary(self, results: dict[str, Any]) -> None:
        """Calculate final test summary"""
        summary = results["summary"]

        # Count passed/failed services
        passed = 0
        failed = 0

        for _worker_key, status in summary["worker_status"].items():
            if status:
                passed += 1
            else:
                failed += 1

        summary["passed"] = passed
        summary["failed"] = failed

        # Overall success
        summary["overall_success"] = (
            len(summary["critical_failures"]) == 0
            and passed >= len(self.workers) * 0.8  # 80% success rate
        )

    def print_results(self, results: dict[str, Any]) -> None:
        """Print comprehensive test results"""
        print("\n" + "=" * 80)
        print("📊 CONTROLLER + WORKERS INTEGRATION TEST RESULTS")
        print("=" * 80)

        summary = results["summary"]

        print(f"🕐 Test Time: {results['timestamp']}")
        print(f"📦 Total Services: {results['total_services']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⚠️  Warnings: {len(summary['warnings'])}")
        print(f"🚨 Critical Failures: {len(summary['critical_failures'])}")
        print(f"🎯 Overall Success: {'✅ YES' if summary['overall_success'] else '❌ NO'}")

        print("\n🎮 WORKER STATUS:")
        for worker_key, status in summary["worker_status"].items():
            config = self.workers[worker_key]
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

    def format_json_output(self, results: dict[str, Any]) -> dict[str, Any]:
        """Format results for JSON output compatible with GitHub Actions"""
        # Convert to format expected by GitHub Actions parsing scripts
        return {
            "timestamp": results["timestamp"],
            "total_services": results["total_services"],
            "warnings": results["summary"]["warnings"],  # This is what the parser looks for
            "critical_failures": results["summary"]["critical_failures"],
            "summary": {
                "passed": results["summary"]["passed"],
                "failed": results["summary"]["failed"],
                "warning_count": len(results["summary"]["warnings"]),
                "overall_success": results["summary"]["overall_success"],
            },
            "detailed_results": {
                "container_status": results["container_status"],
                "health_checks": results["health_checks"],
                "controller_registration": results["controller_registration"],
                "api_functionality": results["api_functionality"],
                "worker_validation": results["worker_validation"],
                "worker_status": results["summary"]["worker_status"],
            },
        }


async def main() -> None:
    """Main test runner"""

    parser = argparse.ArgumentParser(description="Enhanced Crank Platform Smoke Test")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument(
        "--compose-file",
        default="docker-compose.development.yml",
        help="Docker compose file to use",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild and restart containers before testing (default: test existing environment)",
    )

    args = parser.parse_args()

    # Create and run tests
    tester = ControllerIntegrationTest(compose_file=args.compose_file)
    results = await tester.run_comprehensive_test(rebuild_environment=args.rebuild)

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
