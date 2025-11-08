"""
Test Framework Quick Validation

A minimal test to ensure our testing framework is working.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the conftest module directly
import importlib.util

spec = importlib.util.spec_from_file_location("conftest", project_root / "tests" / "conftest.py")
conftest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(conftest)

def test_basic_functionality():
    """Test basic functionality without fixtures."""

    # Test performance benchmark exists and has methods
    assert hasattr(conftest.PerformanceBenchmark, 'measure_sync_operation')
    assert hasattr(conftest.PerformanceBenchmark, 'measure_async_operation')

    # Test ServiceTestBase exists and has methods
    assert hasattr(conftest.ServiceTestBase, 'create_test_request')
    assert hasattr(conftest.ServiceTestBase, 'validate_response_structure')
    assert hasattr(conftest.ServiceTestBase, 'assert_response_time')

    # Test TestConfig has expected values
    assert hasattr(conftest.TestConfig, 'COVERAGE_MINIMUM')
    assert conftest.TestConfig.COVERAGE_MINIMUM == 80

    print("✅ All framework components imported successfully")


def test_response_validation():
    """Test response structure validation."""

    # Test valid response
    valid_response = {
        "status": "success",
        "data": {"result": "test"},
        "timestamp": "2024-01-01T00:00:00Z"
    }

    required_fields = ["status", "data", "timestamp"]
    assert conftest.ServiceTestBase.validate_response_structure(valid_response, required_fields)

    # Test invalid response (missing field)
    invalid_response = {"status": "success", "data": {"result": "test"}}
    assert not conftest.ServiceTestBase.validate_response_structure(invalid_response, required_fields)

    print("✅ Response validation working correctly")


def test_performance_measurement():
    """Test performance measurement utilities."""
    import time

    def slow_function(n: int) -> int:
        time.sleep(0.01)  # 10ms
        return n * 2

    result, duration = conftest.PerformanceBenchmark.measure_sync_operation(slow_function, 5)

    assert result == 10
    assert 0.005 < duration < 0.1  # Should be around 10ms

    print(f"✅ Performance measurement: {duration:.3f}s")


if __name__ == "__main__":
    test_basic_functionality()
    test_response_validation()
    test_performance_measurement()
    print("🎉 All framework validation tests passed!")
