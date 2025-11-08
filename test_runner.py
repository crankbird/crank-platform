#!/usr/bin/env python3
"""
🧪 Unified Test Runner for Crank Platform
=========================================

CI/CD-friendly test runner supporting multiple test categories with proper exit codes,
coverage reporting, and flexible test selection for different pipeline stages.

Usage:
    # Development workflow
    python test_runner.py --unit                    # Fast unit tests only
    python test_runner.py --smoke                   # Critical smoke tests
    python test_runner.py --integration            # Full integration suite
    
    # CI/CD workflow  
    python test_runner.py --ci                     # CI-optimized test suite
    python test_runner.py --pr                     # Pull request validation
    python test_runner.py --release                # Release validation
    
    # Coverage and reporting
    python test_runner.py --unit --coverage        # Unit tests with coverage
    python test_runner.py --all --coverage --html  # Full suite with HTML report
    
    # Docker-based testing
    python test_runner.py --docker                 # Tests requiring containers
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestSuite:
    """Test suite configuration for different testing scenarios."""
    name: str
    markers: list[str]
    description: str
    timeout: int = 300  # 5 minutes default
    requires_docker: bool = False
    requires_network: bool = False


# Define test suites for different scenarios
TEST_SUITES = {
    "unit": TestSuite(
        name="Unit Tests",
        markers=["unit"],
        description="Fast, isolated tests with no external dependencies",
        timeout=60
    ),
    "smoke": TestSuite(
        name="Smoke Tests", 
        markers=["smoke"],
        description="Critical path validation and service health checks",
        timeout=120,
        requires_docker=True
    ),
    "integration": TestSuite(
        name="Integration Tests",
        markers=["integration"],
        description="Multi-service tests requiring full platform",
        timeout=600,
        requires_docker=True,
        requires_network=True
    ),
    "performance": TestSuite(
        name="Performance Tests",
        markers=["performance"],
        description="Performance benchmarks and load tests",
        timeout=900
    ),
    "security": TestSuite(
        name="Security Tests",
        markers=["security"],
        description="Security validation and certificate tests",
        timeout=300,
        requires_docker=True
    ),
    "ci": TestSuite(
        name="CI Pipeline Tests",
        markers=["unit", "smoke"],
        description="Fast tests for continuous integration",
        timeout=180,
        requires_docker=True
    ),
    "pr": TestSuite(
        name="Pull Request Tests",
        markers=["unit", "smoke", "not slow"],
        description="Tests for pull request validation",
        timeout=300,
        requires_docker=True
    ),
    "release": TestSuite(
        name="Release Tests",
        markers=["unit", "smoke", "integration", "security"],
        description="Comprehensive tests for release validation",
        timeout=1200,
        requires_docker=True,
        requires_network=True
    )
}


class UnifiedTestRunner:
    """Unified test runner for all test categories."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.test_dir = workspace_root / "tests"
        
    def check_prerequisites(self, suite: TestSuite) -> bool:
        """Check if prerequisites for test suite are met."""
        logger.info(f"🔍 Checking prerequisites for {suite.name}...")
        
        # Check Docker if required
        if suite.requires_docker:
            try:
                result = subprocess.run(
                    ["docker", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    logger.error("❌ Docker is required but not available")
                    return False
                logger.info("✅ Docker available")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.error("❌ Docker is required but not available")
                return False
        
        # Check network connectivity if required
        if suite.requires_network:
            try:
                result = subprocess.run(
                    ["ping", "-c", "1", "8.8.8.8"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    logger.warning("⚠️ Network connectivity test failed")
                    # Don't fail - network tests may still work locally
                logger.info("✅ Network connectivity available")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.warning("⚠️ Network connectivity check failed")
        
        return True
    
    def build_pytest_command(
        self,
        suite: TestSuite,
        coverage: bool = False,
        coverage_html: bool = False,
        verbose: bool = False,
        parallel: bool = False,
        xml_output: Optional[Path] = None
    ) -> list[str]:
        """Build pytest command with appropriate options."""
        
        cmd = ["uv", "run", "pytest"]
        
        # Add test directory
        cmd.append(str(self.test_dir))
        
        # Add markers
        if suite.markers:
            marker_expr = " or ".join(suite.markers)
            cmd.extend(["-m", marker_expr])
        
        # Add verbosity
        if verbose:
            cmd.append("-v")
        
        # Add coverage options
        if coverage:
            cmd.extend([
                "--cov=services",
                "--cov=tests",
                "--cov-report=term-missing"
            ])
            
            if coverage_html:
                cmd.extend(["--cov-report=html:htmlcov"])
        
        # Add XML output for CI/CD
        if xml_output:
            cmd.extend(["--junit-xml", str(xml_output)])
        
        # Add parallel execution for faster tests
        if parallel and suite.name in ["Unit Tests", "Smoke Tests"]:
            try:
                # Check if pytest-xdist is available
                subprocess.run(["uv", "run", "python", "-c", "import pytest_xdist"], 
                             check=True, capture_output=True)
                cmd.extend(["-n", "auto"])
            except subprocess.CalledProcessError:
                logger.info("pytest-xdist not available, running sequentially")
        
        # Add timeout (only if pytest-timeout is available)
        try:
            subprocess.run(["uv", "run", "python", "-c", "import pytest_timeout"], 
                         check=True, capture_output=True)
            cmd.extend(["--timeout", str(suite.timeout)])
        except subprocess.CalledProcessError:
            logger.info("pytest-timeout not available, running without timeout")
        
        return cmd
    
    async def run_pytest_suite(
        self,
        suite: TestSuite,
        coverage: bool = False,
        coverage_html: bool = False,
        verbose: bool = False,
        parallel: bool = False,
        xml_output: Optional[Path] = None
    ) -> tuple[bool, float, dict[str, Any]]:
        """Run a pytest test suite and return results."""
        
        logger.info(f"🚀 Running {suite.name}")
        logger.info(f"📋 Description: {suite.description}")
        
        # Check prerequisites
        if not self.check_prerequisites(suite):
            logger.error(f"❌ Prerequisites not met for {suite.name}")
            return False, 0.0, {"error": "Prerequisites not met"}
        
        # Build command
        cmd = self.build_pytest_command(
            suite, coverage, coverage_html, verbose, parallel, xml_output
        )
        
        logger.info(f"🔧 Command: {' '.join(cmd)}")
        
        # Run tests
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=suite.timeout
            )
            
            duration = time.time() - start_time
            
            # Parse output for results
            test_results = {
                "suite": suite.name,
                "duration": duration,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd)
            }
            
            success = result.returncode == 0
            
            if success:
                logger.info(f"✅ {suite.name} completed successfully in {duration:.1f}s")
            else:
                logger.error(f"❌ {suite.name} failed after {duration:.1f}s")
                logger.error(f"Exit code: {result.returncode}")
                if result.stderr:
                    logger.error(f"Stderr: {result.stderr[:500]}")
            
            return success, duration, test_results
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error(f"⏱️ {suite.name} timed out after {duration:.1f}s")
            return False, duration, {
                "suite": suite.name,
                "error": "timeout",
                "duration": duration,
                "timeout": suite.timeout
            }
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"💥 {suite.name} failed with exception: {e}")
            return False, duration, {
                "suite": suite.name,
                "error": str(e),
                "duration": duration
            }
    
    async def run_smoke_tests_integration(self) -> tuple[bool, dict[str, Any]]:
        """Run existing smoke tests in pytest framework."""
        logger.info("🌪️ Running legacy smoke tests integration...")
        
        # Run existing enhanced smoke test
        smoke_tests = [
            "tests/enhanced_smoke_test.py",
            "tests/test_streaming_basic.py", 
            "tests/quick_validation_test.py"
        ]
        
        results: dict[str, Any] = {}
        all_passed = True
        
        for test_file in smoke_tests:
            test_path = self.workspace_root / test_file
            if test_path.exists():
                logger.info(f"🔥 Running {test_file}...")
                
                try:
                    result = subprocess.run(
                        ["uv", "run", "python", str(test_path)],
                        cwd=self.workspace_root,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    success = result.returncode == 0
                    results[test_file] = {
                        "success": success,
                        "returncode": result.returncode,
                        "stdout": result.stdout[:500] if result.stdout else "",
                        "stderr": result.stderr[:500] if result.stderr else ""
                    }
                    
                    if success:
                        logger.info(f"✅ {test_file} passed")
                    else:
                        logger.error(f"❌ {test_file} failed")
                        all_passed = False
                        
                except subprocess.TimeoutExpired:
                    logger.error(f"⏱️ {test_file} timed out")
                    results[test_file] = {"success": False, "error": "timeout"}
                    all_passed = False
                    
            else:
                logger.warning(f"⚠️ {test_file} not found")
                results[test_file] = {"success": False, "error": "not_found"}
                
        return all_passed, results
    
    def generate_ci_report(
        self,
        results: list[tuple[bool, float, dict[str, Any]]],
        output_file: Optional[Path] = None
    ) -> dict[str, Any]:
        """Generate CI/CD compatible test report."""
        
        total_duration = sum(r[1] for r in results)
        passed_suites = sum(1 for r in results if r[0])
        total_suites = len(results)
        
        report = {
            "timestamp": time.time(),
            "summary": {
                "total_suites": total_suites,
                "passed_suites": passed_suites,
                "failed_suites": total_suites - passed_suites,
                "total_duration": total_duration,
                "success": passed_suites == total_suites
            },
            "suites": [r[2] for r in results],
            "environment": {
                "python_version": sys.version,
                "platform": os.name,
                "cwd": str(self.workspace_root)
            }
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"📊 Test report written to {output_file}")
        
        return report


async def main() -> int:
    """Main entry point for unified test runner."""
    parser = argparse.ArgumentParser(
        description="Unified Test Runner for Crank Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Test suite selection (mutually exclusive)
    suite_group = parser.add_mutually_exclusive_group(required=True)
    for suite_name in TEST_SUITES.keys():
        suite_group.add_argument(
            f"--{suite_name}",
            action="store_true",
            help=f"Run {TEST_SUITES[suite_name].name}: {TEST_SUITES[suite_name].description}"
        )
    
    suite_group.add_argument("--all", action="store_true", help="Run all test suites")
    
    # Test options
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--coverage-html", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", "-j", action="store_true", help="Run tests in parallel when possible")
    parser.add_argument("--xml-output", type=Path, help="Generate XML output for CI/CD")
    parser.add_argument("--json-report", type=Path, help="Generate JSON test report")
    parser.add_argument("--include-legacy", action="store_true", help="Include legacy smoke tests")
    
    args = parser.parse_args()
    
    # Initialize test runner
    workspace_root = Path(__file__).parent.resolve()
    runner = UnifiedTestRunner(workspace_root)
    
    # Determine which suites to run
    suites_to_run = []
    if args.all:
        suites_to_run = list(TEST_SUITES.values())
    else:
        for suite_name, suite in TEST_SUITES.items():
            if getattr(args, suite_name, False):
                suites_to_run = [suite]
                break
    
    if not suites_to_run:
        logger.error("❌ No test suite specified")
        return 1
    
    # Run test suites
    results = []
    overall_success = True
    
    logger.info("🧪 Starting Unified Test Runner")
    logger.info(f"📂 Workspace: {workspace_root}")
    logger.info(f"🎯 Running {len(suites_to_run)} test suite(s)")
    
    for suite in suites_to_run:
        success, duration, result_data = await runner.run_pytest_suite(
            suite,
            coverage=args.coverage,
            coverage_html=args.coverage_html,
            verbose=args.verbose,
            parallel=args.parallel,
            xml_output=args.xml_output
        )
        
        results.append((success, duration, result_data))
        if not success:
            overall_success = False
    
    # Run legacy smoke tests if requested
    if args.include_legacy:
        legacy_success, _ = await runner.run_smoke_tests_integration()
        if not legacy_success:
            overall_success = False
            logger.error("❌ Legacy smoke tests failed")
    
    # Generate CI/CD report
    if args.json_report or not overall_success:
        report_path = args.json_report or Path("test_results.json")
        runner.generate_ci_report(results, report_path)
    
    # Final summary
    total_duration = sum(r[1] for r in results)
    passed_count = sum(1 for r in results if r[0])
    
    logger.info("=" * 50)
    logger.info("🏁 Test Summary")
    logger.info(f"📊 Suites: {passed_count}/{len(results)} passed")
    logger.info(f"⏱️ Total Duration: {total_duration:.1f}s")
    
    if overall_success:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)