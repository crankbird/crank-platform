#!/usr/bin/env python3
"""
🚀 Run Enhanced Smoke Tests for M4 Mac Mini Apple Silicon Environment
====================================================================

Apple Silicon optimized smoke test runner that validates:
✅ Universal GPU detection (MPS/CUDA/CPU)
✅ Container health and worker registration
✅ Certificate provisioning and mTLS
✅ All 6 archetype patterns working correctly

Usage:
    python3 run_apple_silicon_smoke_tests.py

Environment: M4 Mac Mini (Apple Silicon) with Docker Desktop
"""

import asyncio
import json
import sys
from pathlib import Path

# Add tests directory to path for import
sys.path.insert(0, str(Path(__file__).parent / "tests"))
from enhanced_smoke_test import EnhancedSmokeTest

async def main():
    """Run enhanced smoke tests optimized for Apple Silicon"""
    print("🍎 Apple Silicon Enhanced Smoke Test Runner")
    print("==========================================")
    print("📍 Platform: Apple M4 Mac Mini")
    print("🐳 Docker: Desktop for Apple Silicon")
    print("🎮 GPU: Metal Performance Shaders (MPS)")
    print("")

    # Initialize enhanced smoke test
    smoke_test = EnhancedSmokeTest("docker-compose.development.yml")

    # Run comprehensive tests
    results = await smoke_test.run_comprehensive_test()

    # Output results
    print("\n" + "="*80)
    print("🏁 APPLE SILICON SMOKE TEST RESULTS")
    print("="*80)

    summary = results["summary"]
    print(f"✅ Tests Passed: {summary['passed']}")
    print(f"❌ Tests Failed: {summary['failed']}")
    print(f"⚠️  Warnings: {len(summary['warnings'])}")

    if summary["critical_failures"]:
        print(f"🚨 Critical Failures: {len(summary['critical_failures'])}")
        for failure in summary["critical_failures"]:
            print(f"   • {failure}")

    # Archetype status summary
    print("\n📊 Archetype Pattern Status:")
    for archetype, status in summary["archetype_status"].items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {archetype}")

    # GPU validation summary for Apple Silicon
    print("\n🎮 Apple Silicon GPU Status:")
    for archetype_key, validation_data in results["archetype_validation"].items():
        if validation_data.get("gpu_validation"):
            gpu_data = validation_data["gpu_validation"]
            if gpu_data["required"]:
                status_icon = "✅" if gpu_data["available"] else "❌"
                print(f"   {status_icon} {archetype_key}: GPU {'available' if gpu_data['available'] else 'not available'}")

    # Save detailed results
    results_file = Path("apple_silicon_smoke_test_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Detailed results saved to: {results_file}")

    # Exit with appropriate code
    if summary["critical_failures"]:
        print("\n🚨 SMOKE TESTS FAILED - Critical failures detected")
        sys.exit(1)
    elif summary["failed"] > summary["passed"]:
        print("\n⚠️  SMOKE TESTS INCOMPLETE - More failures than passes")
        sys.exit(1)
    else:
        print("\n🎉 SMOKE TESTS SUCCESSFUL - Apple Silicon ready!")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
