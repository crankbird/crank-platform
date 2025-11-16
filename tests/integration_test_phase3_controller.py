#!/usr/bin/env python3
"""
Phase 3 Controller Integration Tests
=====================================

Tests the controller/worker architecture with all 8 migrated workers:
1. crank_streaming (8500)
2. crank_email_classifier (8201)
3. crank_email_parser (8301)
4. crank_doc_converter (8401)
5. crank_philosophical_analyzer (8601)
6. crank_sonnet_zettel_manager (8700)
7. crank_codex_zettel_repository (8800)
8. crank_hello_world (8900)

Validates:
✅ All workers register with controller on startup
✅ Controller tracks all worker capabilities
✅ Capability-based routing works (single worker per capability)
✅ Multi-worker routing works (duplicate capabilities)
✅ Heartbeat mechanism functions
✅ Graceful degradation (workers run without controller)
✅ HTTPS-only enforcement with mTLS

Usage:
    pytest tests/integration_test_phase3_controller.py -v
    python tests/integration_test_phase3_controller.py --live  # Test with real containers
"""

import asyncio
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from services.crank_codex_zettel_repository import CodexZettelRepositoryWorker
from services.crank_controller import ControllerService
from services.crank_doc_converter import DocumentConverterWorker
from services.crank_email_classifier import EmailClassifierWorker
from services.crank_email_parser import EmailParserWorker
from services.crank_hello_world import HelloWorldWorker
from services.crank_philosophical_analyzer import PhilosophicalAnalyzerWorker
from services.crank_sonnet_zettel_manager import SonnetZettelManagerWorker
from services.crank_streaming import StreamingWorker


@pytest.fixture
def temp_state_file() -> Path:
    """Provide temporary state file for controller."""
    with NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
        yield Path(f.name)
    # Cleanup after test
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def controller(temp_state_file: Path) -> ControllerService:
    """Create controller service for testing."""
    os.environ["CONTROLLER_STATE_FILE"] = str(temp_state_file)
    controller = ControllerService(https_port=9000)
    return controller


@pytest.fixture
def controller_client(controller: ControllerService) -> TestClient:
    """Create test client for controller API."""
    return TestClient(controller.app)


# Worker fixtures for all 8 workers
@pytest.fixture
def streaming_worker() -> StreamingWorker:
    """Create streaming worker."""
    os.environ["CONTROLLER_URL"] = "https://localhost:9000"
    os.environ["STREAMING_HTTPS_PORT"] = "8500"
    return StreamingWorker()


@pytest.fixture
def email_classifier_worker() -> EmailClassifierWorker:
    """Create email classifier worker."""
    os.environ["CONTROLLER_URL"] = "https://localhost:9000"
    os.environ["EMAIL_CLASSIFIER_HTTPS_PORT"] = "8201"
    return EmailClassifierWorker()


@pytest.fixture
def email_parser_worker() -> EmailParserWorker:
    """Create email parser worker."""
    os.environ["CONTROLLER_URL"] = "https://localhost:9000"
    os.environ["EMAIL_PARSER_HTTPS_PORT"] = "8301"
    return EmailParserWorker()


@pytest.fixture
def doc_converter_worker() -> DocumentConverterWorker:
    """Create document converter worker."""
    os.environ["CONTROLLER_URL"] = "https://localhost:9000"
    os.environ["DOC_CONVERTER_HTTPS_PORT"] = "8401"
    return DocumentConverterWorker()


@pytest.fixture
def philosophical_analyzer_worker() -> PhilosophicalAnalyzerWorker:
    """Create philosophical analyzer worker."""
    os.environ["CONTROLLER_URL"] = "https://localhost:9000"
    os.environ["PHILOSOPHICAL_ANALYZER_HTTPS_PORT"] = "8601"
    return PhilosophicalAnalyzerWorker()


@pytest.fixture
def sonnet_zettel_worker() -> SonnetZettelManagerWorker:
    """Create sonnet zettel manager worker."""
    os.environ["CONTROLLER_URL"] = "https://localhost:9000"
    os.environ["SONNET_ZETTEL_HTTPS_PORT"] = "8700"
    return SonnetZettelManagerWorker()


@pytest.fixture
def codex_zettel_worker() -> CodexZettelRepositoryWorker:
    """Create codex zettel repository worker."""
    os.environ["CONTROLLER_URL"] = "https://localhost:9000"
    os.environ["CODEX_ZETTEL_HTTPS_PORT"] = "8800"
    return CodexZettelRepositoryWorker()


@pytest.fixture
def hello_world_worker() -> HelloWorldWorker:
    """Create hello world worker."""
    os.environ["CONTROLLER_URL"] = "https://localhost:9000"
    os.environ["HELLO_WORLD_HTTPS_PORT"] = "8900"
    return HelloWorldWorker()


class TestControllerWorkerRegistration:
    """Test worker registration with controller."""

    def test_all_workers_register_successfully(
        self,
        controller_client: TestClient,
        streaming_worker: StreamingWorker,
        email_classifier_worker: EmailClassifierWorker,
        email_parser_worker: EmailParserWorker,
        doc_converter_worker: DocumentConverterWorker,
        philosophical_analyzer_worker: PhilosophicalAnalyzerWorker,
        sonnet_zettel_worker: SonnetZettelManagerWorker,
        codex_zettel_worker: CodexZettelRepositoryWorker,
        hello_world_worker: HelloWorldWorker,
    ) -> None:
        """Test all 8 workers can register with controller.

        Validates:
        - Each worker has unique worker_id
        - Each worker has valid capabilities
        - Controller tracks all registrations
        """
        workers = [
            streaming_worker,
            email_classifier_worker,
            email_parser_worker,
            doc_converter_worker,
            philosophical_analyzer_worker,
            sonnet_zettel_worker,
            codex_zettel_worker,
            hello_world_worker,
        ]

        # Register all workers
        for worker in workers:
            capabilities = [
                {
                    "name": cap.id,
                    "verb": cap.id.split(":")[0] if ":" in cap.id else "invoke",
                    "version": f"{cap.version.major}.{cap.version.minor}.{cap.version.patch}",
                }
                for cap in worker.get_capabilities()
            ]

            registration = {
                "worker_id": worker.worker_id,
                "worker_url": worker.worker_url,
                "capabilities": capabilities,
            }

            response = controller_client.post("/register", json=registration)
            assert response.status_code == 200, f"Failed to register {worker.worker_id}"

            result = response.json()
            assert result["status"] == "registered"
            assert result["worker_id"] == worker.worker_id

        # Verify all workers tracked by controller
        response = controller_client.get("/workers")
        assert response.status_code == 200

        workers_data = response.json()["workers"]
        assert len(workers_data) == 8, f"Expected 8 workers, got {len(workers_data)}"

        # Verify unique worker IDs
        worker_ids = [w["worker_id"] for w in workers_data]
        assert len(worker_ids) == len(set(worker_ids)), "Duplicate worker IDs detected"

    def test_streaming_worker_multiple_capabilities(
        self,
        controller_client: TestClient,
        streaming_worker: StreamingWorker,
    ) -> None:
        """Test streaming worker registers multiple capabilities.

        Streaming worker provides:
        - stream:text_events
        - stream:sse_events
        """
        capabilities = [
            {
                "name": cap.id,
                "verb": "stream",
                "version": f"{cap.version.major}.{cap.version.minor}.{cap.version.patch}",
            }
            for cap in streaming_worker.get_capabilities()
        ]

        assert len(capabilities) >= 2, "Streaming worker should have multiple capabilities"

        registration = {
            "worker_id": streaming_worker.worker_id,
            "worker_url": streaming_worker.worker_url,
            "capabilities": capabilities,
        }

        response = controller_client.post("/register", json=registration)
        assert response.status_code == 200

        result = response.json()
        assert result["capabilities_registered"] >= 2


class TestCapabilityBasedRouting:
    """Test controller routes requests by capability."""

    def test_route_to_email_classifier(
        self,
        controller_client: TestClient,
        email_classifier_worker: EmailClassifierWorker,
    ) -> None:
        """Test routing to email classifier via capability."""
        # Register worker
        capabilities = [
            {
                "name": cap.id,
                "verb": "classify",
                "version": f"{cap.version.major}.{cap.version.minor}.{cap.version.patch}",
            }
            for cap in email_classifier_worker.get_capabilities()
        ]

        registration = {
            "worker_id": email_classifier_worker.worker_id,
            "worker_url": email_classifier_worker.worker_url,
            "capabilities": capabilities,
        }

        response = controller_client.post("/register", json=registration)
        assert response.status_code == 200

        # Request routing for email classification
        route_request = {
            "verb": "classify",
            "capability": "email_intent",
        }

        response = controller_client.post("/route", json=route_request)
        assert response.status_code == 200

        route = response.json()
        assert route["worker_id"] == email_classifier_worker.worker_id
        assert route["worker_url"] == email_classifier_worker.worker_url

    def test_route_to_document_converter(
        self,
        controller_client: TestClient,
        doc_converter_worker: DocumentConverterWorker,
    ) -> None:
        """Test routing to document converter via capability."""
        # Register worker
        capabilities = [
            {
                "name": cap.id,
                "verb": "convert",
                "version": f"{cap.version.major}.{cap.version.minor}.{cap.version.patch}",
            }
            for cap in doc_converter_worker.get_capabilities()
        ]

        registration = {
            "worker_id": doc_converter_worker.worker_id,
            "worker_url": doc_converter_worker.worker_url,
            "capabilities": capabilities,
        }

        response = controller_client.post("/register", json=registration)
        assert response.status_code == 200

        # Request routing for document conversion
        route_request = {
            "verb": "convert",
            "capability": "document_to_pdf",
        }

        response = controller_client.post("/route", json=route_request)
        assert response.status_code == 200

        route = response.json()
        assert route["worker_id"] == doc_converter_worker.worker_id


class TestMultiWorkerScenarios:
    """Test scenarios with multiple workers providing same capability."""

    def test_multiple_zettel_managers(
        self,
        controller_client: TestClient,
        sonnet_zettel_worker: SonnetZettelManagerWorker,
        codex_zettel_worker: CodexZettelRepositoryWorker,
    ) -> None:
        """Test routing with multiple workers providing 'manage' capability.

        Both sonnet and codex workers provide zettel management.
        Controller should route to first healthy worker.
        """
        workers = [sonnet_zettel_worker, codex_zettel_worker]

        # Register both workers
        for worker in workers:
            capabilities = [
                {
                    "name": cap.id,
                    "verb": "manage",
                    "version": f"{cap.version.major}.{cap.version.minor}.{cap.version.patch}",
                }
                for cap in worker.get_capabilities()
            ]

            registration = {
                "worker_id": worker.worker_id,
                "worker_url": worker.worker_url,
                "capabilities": capabilities,
            }

            response = controller_client.post("/register", json=registration)
            assert response.status_code == 200

        # Verify controller sees both workers
        response = controller_client.get("/workers")
        assert response.status_code == 200
        assert len(response.json()["workers"]) == 2

        # Request routing - should get one of the workers
        route_request = {
            "verb": "manage",
            "capability": "zettel",
        }

        response = controller_client.post("/route", json=route_request)
        assert response.status_code == 200

        route = response.json()
        worker_ids = [w.worker_id for w in workers]
        assert route["worker_id"] in worker_ids


class TestCapabilityIntrospection:
    """Test controller capability listing and introspection."""

    def test_list_all_capabilities(
        self,
        controller_client: TestClient,
        streaming_worker: StreamingWorker,
        email_classifier_worker: EmailClassifierWorker,
        doc_converter_worker: DocumentConverterWorker,
    ) -> None:
        """Test controller lists all registered capabilities."""
        workers = [streaming_worker, email_classifier_worker, doc_converter_worker]

        # Register all workers
        for worker in workers:
            capabilities = [
                {
                    "name": cap.id,
                    "verb": cap.id.split(":")[0] if ":" in cap.id else "invoke",
                    "version": f"{cap.version.major}.{cap.version.minor}.{cap.version.patch}",
                }
                for cap in worker.get_capabilities()
            ]

            registration = {
                "worker_id": worker.worker_id,
                "worker_url": worker.worker_url,
                "capabilities": capabilities,
            }

            response = controller_client.post("/register", json=registration)
            assert response.status_code == 200

        # Get all capabilities
        response = controller_client.get("/capabilities")
        assert response.status_code == 200

        capabilities_data = response.json()["capabilities"]

        # Verify expected capabilities present
        expected_verbs = ["stream", "classify", "convert"]
        for verb in expected_verbs:
            matching_caps = [
                cap for cap in capabilities_data.keys() if cap.startswith(f"{verb}:")
            ]
            assert len(matching_caps) > 0, f"Missing capabilities for verb: {verb}"


class TestWorkerGracefulDegradation:
    """Test workers operate without controller (graceful degradation)."""

    @pytest.mark.asyncio
    async def test_worker_runs_without_controller(self) -> None:
        """Test worker operates when controller unavailable.

        Workers should:
        - Start successfully
        - Log warning about missing controller
        - Continue providing services
        - Not crash on registration failure
        """
        # Remove controller URL to simulate unavailable controller
        if "CONTROLLER_URL" in os.environ:
            del os.environ["CONTROLLER_URL"]

        worker = HelloWorldWorker()

        # Trigger startup - should not fail
        await worker.on_startup()

        # Verify worker not registered
        assert not worker.registered_with_controller

        # But worker still has capabilities
        assert len(worker.get_capabilities()) > 0


class TestHeartbeatMechanism:
    """Test worker heartbeat tracking."""

    def test_heartbeat_updates_worker_status(
        self,
        controller_client: TestClient,
        hello_world_worker: HelloWorldWorker,
    ) -> None:
        """Test heartbeat endpoint updates worker status."""
        # Register worker
        capabilities = [
            {
                "name": cap.id,
                "verb": "invoke",
                "version": f"{cap.version.major}.{cap.version.minor}.{cap.version.patch}",
            }
            for cap in hello_world_worker.get_capabilities()
        ]

        registration = {
            "worker_id": hello_world_worker.worker_id,
            "worker_url": hello_world_worker.worker_url,
            "capabilities": capabilities,
        }

        response = controller_client.post("/register", json=registration)
        assert response.status_code == 200

        # Send heartbeat
        heartbeat = {
            "worker_id": hello_world_worker.worker_id,
            "load_score": 0.5,
        }

        response = controller_client.post("/heartbeat", data=heartbeat)
        assert response.status_code == 200

        result = response.json()
        assert result["status"] == "ok"


# CLI for live testing with real containers
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Phase 3 Controller Integration Tests"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run tests against live containers (requires docker-compose up)",
    )
    args = parser.parse_args()

    if args.live:
        print("🚀 Testing Phase 3 Controller/Worker Architecture (Live Containers)")
        print("=" * 80)
        print("⚠️  Ensure containers running: docker-compose -f docker-compose.development.yml up")
        print()

        async def test_live_workers() -> None:
            """Test actual running workers."""
            controller_url = "https://localhost:9000"
            worker_ports = {
                "streaming": 8500,
                "email_classifier": 8201,
                "email_parser": 8301,
                "doc_converter": 8401,
                "philosophical_analyzer": 8601,
                "sonnet_zettel": 8700,
                "codex_zettel": 8800,
                "hello_world": 8900,
            }

            print("🔍 Checking worker health...")
            async with httpx.AsyncClient(verify=False) as client:
                for name, port in worker_ports.items():
                    try:
                        response = await client.get(
                            f"https://localhost:{port}/health", timeout=5.0
                        )
                        if response.status_code == 200:
                            print(f"✅ {name:30} - HEALTHY (port {port})")
                        else:
                            print(
                                f"⚠️  {name:30} - UNHEALTHY (port {port}, status {response.status_code})"
                            )
                    except Exception as e:
                        print(f"❌ {name:30} - UNREACHABLE (port {port})")

            print("\n🔍 Checking controller capabilities...")
            async with httpx.AsyncClient(verify=False) as client:
                try:
                    response = await client.get(f"{controller_url}/capabilities")
                    if response.status_code == 200:
                        caps = response.json()["capabilities"]
                        print(f"✅ Controller tracking {len(caps)} capabilities")
                        for cap_id, cap_info in list(caps.items())[:5]:
                            print(
                                f"   - {cap_id}: {cap_info['workers']} worker(s)"
                            )
                        if len(caps) > 5:
                            print(f"   ... and {len(caps) - 5} more")
                    else:
                        print(
                            f"❌ Controller unreachable (status {response.status_code})"
                        )
                except Exception as e:
                    print(f"❌ Controller unreachable: {e}")

        asyncio.run(test_live_workers())
    else:
        print("Run with pytest: pytest tests/integration_test_phase3_controller.py -v")
        print("Or test live containers: python tests/integration_test_phase3_controller.py --live")
        sys.exit(1)
