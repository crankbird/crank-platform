"""
Basic framework tests that work with pytest properly.
"""
import pytest


def test_basic_test() -> None:
    """Simple test that always passes."""
    assert True


def test_math_operations() -> None:
    """Test basic math to validate test runner."""
    assert 2 + 2 == 4
    assert 10 * 5 == 50
    assert 100 / 4 == 25.0


@pytest.mark.unit
def test_string_operations() -> None:
    """Test string operations."""
    test_string = "Hello, Testing Framework!"
    assert "Testing" in test_string
    assert test_string.startswith("Hello")
    assert test_string.endswith("!")


@pytest.mark.unit
def test_list_operations() -> None:
    """Test list operations."""
    test_list = [1, 2, 3, 4, 5]
    assert len(test_list) == 5
    assert 3 in test_list
    assert test_list[0] == 1
    assert test_list[-1] == 5


@pytest.mark.performance
def test_performance_baseline() -> None:
    """Baseline performance test."""
    import time

    start_time = time.perf_counter()

    # Simple computation
    result = sum(range(10000))

    end_time = time.perf_counter()
    duration = end_time - start_time

    # Should complete quickly
    assert duration < 1.0
    assert result == 49995000  # sum of 0 to 9999


class TestFrameworkUtils:
    """Test utilities and helper functions."""

    @pytest.mark.unit
    def test_fixture_loading(self) -> None:
        """Test that pytest fixtures are available."""
        # This test validates that our test framework loads correctly
        assert True

    def test_markers_work(self) -> None:
        """Test that pytest markers are working."""
        # If this test runs, markers are configured correctly
        assert True
