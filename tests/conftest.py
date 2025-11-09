"""
Crank Platform Test Framework Configuration

This module provides the foundation for comprehensive test coverage including:
- Unit tests with pytest
- Integration tests with service mocking
- Code coverage reporting with coverage.py
- Performance benchmarking
- Security validation
"""

import asyncio
import logging
import os
import sys
from collections.abc import Awaitable, Callable, Generator
from pathlib import Path
from typing import Any, ClassVar
from unittest.mock import MagicMock

import pytest

try:
    from coverage import Coverage
except ImportError:
    Coverage = None  # type: ignore[assignment]

# Add platform modules to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "services"))

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestConfig:
    """Central configuration for test framework."""

    # Coverage settings
    COVERAGE_MINIMUM = 80  # Target 80% code coverage
    COVERAGE_EXCLUDE_PATTERNS: ClassVar[list[str]] = [
        "*/tests/*",
        "*/venv/*",
        "*/.venv/*",
        "*/site-packages/*",
        "*/archive/*",
        "*/scripts/deprecated/*",
    ]

    # Test environment settings
    TEST_ENVIRONMENT = "test"
    MOCK_EXTERNAL_SERVICES = True
    TIMEOUT_SECONDS = 30

    # Service endpoints for integration tests
    TEST_SERVICES: ClassVar[dict[str, str]] = {
        "image_classifier_gpu": "http://localhost:8506",
        "email_parser": "http://localhost:8501",
        "doc_converter": "http://localhost:8502",
        "streaming": "http://localhost:8503",
    }


@pytest.fixture(scope="session")
def coverage_instance() -> Generator[Any, None, None]:
    """Set up code coverage tracking for the test session."""
    if Coverage is None:
        print("⚠️ Coverage module not available, skipping coverage tracking")
        yield None
        return

    cov = Coverage(
        source=["services", "src"], omit=TestConfig.COVERAGE_EXCLUDE_PATTERNS, config_file=False
    )
    cov.start()

    yield cov

    cov.stop()
    cov.save()

    # Generate coverage report
    print("\n" + "=" * 60)
    print("📊 CODE COVERAGE REPORT")
    print("=" * 60)
    cov.report(show_missing=True)

    # Check if we meet minimum coverage
    total_coverage = cov.report(show_missing=False)
    if total_coverage < TestConfig.COVERAGE_MINIMUM:
        print(
            f"\n⚠️ WARNING: Coverage {total_coverage}% below target {TestConfig.COVERAGE_MINIMUM}%"
        )
    else:
        print(f"\n✅ Coverage target achieved: {total_coverage}% >= {TestConfig.COVERAGE_MINIMUM}%")


@pytest.fixture
def mock_gpu_manager() -> MagicMock:
    """Mock UniversalGPUManager for testing without GPU dependencies."""
    mock = MagicMock()
    mock.get_device.return_value = MagicMock()
    mock.get_device_str.return_value = "mps"  # Simulate Apple Silicon
    mock.get_info.return_value = {
        "device": "mps",
        "type": "Apple Silicon GPU",
        "memory_gb": 36.0,
        "platform": "darwin",
        "architecture": "arm64",
    }
    return mock


@pytest.fixture
def mock_ml_models() -> MagicMock:
    """Mock ML models (YOLO, CLIP, etc.) for testing without model dependencies."""
    mock_models = MagicMock()
    mock_models.yolo = MagicMock()
    mock_models.clip = MagicMock()
    mock_models.sentence_transformer = MagicMock()
    return mock_models


@pytest.fixture
def mock_http_session() -> MagicMock:
    """Mock HTTP session for testing HTTP interactions."""
    session_mock = MagicMock()

    # Mock successful responses by default
    response_mock = MagicMock()
    response_mock.status_code = 200
    response_mock.json.return_value = {"status": "healthy"}
    response_mock.text = "OK"

    session_mock.get.return_value = response_mock
    session_mock.post.return_value = response_mock

    return session_mock


@pytest.fixture(scope="session")
def test_certificates() -> dict[str, str]:
    """Provide test certificates for mTLS testing."""
    return {
        "ca_cert": """-----BEGIN CERTIFICATE-----
MIIBkTCB+wIJAK8xyz123TestCA...
-----END CERTIFICATE-----""",
        "client_cert": """-----BEGIN CERTIFICATE-----
MIIBkTCB+wIJAK8xyz123TestClient...
-----END CERTIFICATE-----""",
        "client_key": """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0Test...
-----END PRIVATE KEY-----""",
    }


class ServiceTestBase:
    """Base class for service testing with common utilities."""

    def setup_method(self) -> None:
        """Set up test environment."""
        os.environ["CRANK_ENVIRONMENT"] = "test"
        os.environ["LOG_LEVEL"] = "INFO"

    def teardown_method(self) -> None:
        """Clean up test environment."""
        # Remove test-specific environment variables
        test_vars = [k for k in os.environ.keys() if k.startswith("TEST_")]
        for var in test_vars:
            del os.environ[var]

    async def wait_for_service(self, url: str, timeout: int = 30) -> bool:
        """Wait for a service to become available."""
        import aiohttp
        from aiohttp import ClientTimeout

        timeout_config = ClientTimeout(total=2)

        for _ in range(timeout):
            try:
                async with aiohttp.ClientSession(timeout=timeout_config) as session:
                    async with session.get(f"{url}/health") as response:
                        if response.status == 200:
                            return True
            except Exception:
                await asyncio.sleep(1)

        return False

    @staticmethod
    def create_test_request(method: str, path: str, data: Any = None) -> Any:
        """Create a test request object."""
        from unittest.mock import MagicMock

        request = MagicMock()
        request.method = method
        request.url = MagicMock()
        request.url.path = path
        request.json = data
        return request

    @staticmethod
    def validate_response_structure(response: dict[str, Any], required_fields: list[str]) -> bool:
        """Validate that a response contains all required fields."""
        return all(field in response for field in required_fields)

    @staticmethod
    def assert_response_time(duration: float, max_seconds: float = 1.0) -> None:
        """Assert that response time is within acceptable limits."""
        if duration > max_seconds:
            raise AssertionError(f"Response too slow: {duration:.3f}s > {max_seconds:.3f}s")


class PerformanceBenchmark:
    """Performance testing utilities."""

    @staticmethod
    async def measure_async_operation(
        operation: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any
    ) -> tuple[Any, float]:
        """Measure execution time of async operation."""
        import time

        start_time = time.perf_counter()
        result = await operation(*args, **kwargs)
        end_time = time.perf_counter()
        return result, end_time - start_time

    @staticmethod
    def measure_sync_operation(
        operation: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> tuple[Any, float]:
        """Measure execution time of sync operation."""
        import time

        start_time = time.perf_counter()
        result = operation(*args, **kwargs)
        end_time = time.perf_counter()
        return result, end_time - start_time


# Test discovery and execution utilities
def run_coverage_tests() -> None:
    """Run all tests with coverage reporting."""
    pytest.main(
        [
            "--cov=services",
            "--cov=src",
            "--cov-report=html:tests/coverage_html",
            "--cov-report=term-missing",
            f"--cov-fail-under={TestConfig.COVERAGE_MINIMUM}",
            "tests/",
            "-v",
        ]
    )


def run_performance_tests() -> None:
    """Run performance benchmark tests."""
    pytest.main(["tests/", "-m", "performance", "-v", "--tb=short"])


def run_integration_tests() -> None:
    """Run integration tests only."""
    pytest.main(["tests/", "-m", "integration", "-v", "--tb=short"])


if __name__ == "__main__":
    # Default: run all tests with coverage
    run_coverage_tests()
