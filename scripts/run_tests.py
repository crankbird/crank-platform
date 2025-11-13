#!/usr/bin/env python3
"""
Crank Platform Test Runner

Comprehensive test execution with coverage reporting, performance benchmarks,
and different test categories.
"""

import argparse
import sys


def run_unit_tests(coverage: bool = True, verbose: bool = True) -> int:
    """Run unit tests with optional coverage."""
    import subprocess

    cmd = ["uv", "run", "pytest", "tests/", "-v"]

    if coverage:
        cmd.extend(
            [
                "--cov=services",
                "--cov=src",
                "--cov=tests",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-fail-under=60",  # Require 60% coverage minimum
            ]
        )

    if verbose:
        cmd.append("-v")

    print("🧪 Running unit tests...")
    print(f"Command: {' '.join(cmd)}")

    return subprocess.run(cmd).returncode


def run_integration_tests(verbose: bool = True) -> int:
    """Run integration tests."""
    import subprocess

    cmd = [
        "uv",
        "run",
        "pytest",
        "tests/",
        "-m",
        "integration",  # Run only tests marked as integration
        "-v" if verbose else "",
    ]

    print("🔗 Running integration tests...")
    return subprocess.run([c for c in cmd if c]).returncode


def run_performance_tests(verbose: bool = True) -> int:
    """Run performance benchmark tests."""
    import subprocess

    cmd = [
        "uv",
        "run",
        "pytest",
        "tests/",
        "-m",
        "performance",  # Run only tests marked as performance
        "-v" if verbose else "",
    ]

    print("⚡ Running performance tests...")
    return subprocess.run([c for c in cmd if c]).returncode


def run_security_tests(verbose: bool = True) -> int:
    """Run security validation tests."""
    import subprocess

    cmd = [
        "uv",
        "run",
        "pytest",
        "tests/",
        "-m",
        "security",  # Run only tests marked as security
        "-v" if verbose else "",
    ]

    print("🔒 Running security tests...")
    return subprocess.run([c for c in cmd if c]).returncode


def main() -> int:
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Crank Platform Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--security", action="store_true", help="Run security tests")
    parser.add_argument("--all", action="store_true", help="Run all test categories")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage reporting")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")

    args = parser.parse_args()

    if not any([args.unit, args.integration, args.performance, args.security, args.all]):
        args.unit = True  # Default to unit tests

    verbose = not args.quiet
    coverage = not args.no_coverage
    exit_code = 0

    print("🚀 Crank Platform Test Suite")
    print("=" * 50)

    if args.all or args.unit:
        print("\n📋 Unit Tests")
        print("-" * 30)
        result = run_unit_tests(coverage=coverage, verbose=verbose)
        if result != 0:
            exit_code = result
            print(f"❌ Unit tests failed with exit code {result}")
        else:
            print("✅ Unit tests passed")

    if args.all or args.integration:
        print("\n🔗 Integration Tests")
        print("-" * 30)
        result = run_integration_tests(verbose=verbose)
        if result != 0:
            exit_code = result
            print(f"❌ Integration tests failed with exit code {result}")
        else:
            print("✅ Integration tests passed")

    if args.all or args.performance:
        print("\n⚡ Performance Tests")
        print("-" * 30)
        result = run_performance_tests(verbose=verbose)
        if result != 0:
            exit_code = result
            print(f"❌ Performance tests failed with exit code {result}")
        else:
            print("✅ Performance tests passed")

    if args.all or args.security:
        print("\n🔒 Security Tests")
        print("-" * 30)
        result = run_security_tests(verbose=verbose)
        if result != 0:
            exit_code = result
            print(f"❌ Security tests failed with exit code {result}")
        else:
            print("✅ Security tests passed")

    print("\n" + "=" * 50)
    if exit_code == 0:
        print("🎉 All tests passed!")
    else:
        print(f"💥 Tests failed with exit code {exit_code}")

    if coverage and (args.all or args.unit):
        print("\n📊 Coverage report saved to htmlcov/index.html")
        print("   Open in browser: open htmlcov/index.html")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
