#!/usr/bin/env python3
"""
CI Regression Test: Prevent CUDA-only GPU Detection

This test ensures all GPU services use UniversalGPUManager instead of hard-coded CUDA detection.
Prevents regression of Issue #20 work.
"""

import re
import sys
from pathlib import Path


def find_cuda_only_patterns(file_path: Path) -> list[tuple[int, str]]:
    """Find lines with CUDA-only detection patterns"""
    patterns = [
        r"torch\.cuda\.is_available\(\)",
        r"torch\.device\s*\(\s*['\"]cuda['\"]",
        r"torch\.device\s*\(\s*['\"]cuda:\d+['\"]",
    ]

    violations = []
    try:
        with open(file_path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line_stripped = line.strip()
                # Skip comments and documentation
                if line_stripped.startswith("#") or '"""' in line_stripped:
                    continue

                for pattern in patterns:
                    if re.search(pattern, line):
                        violations.append((line_num, line.strip()))
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")

    return violations


def scan_gpu_services() -> list[tuple[Path, list[tuple[int, str]]]]:
    """Scan all GPU services for CUDA-only patterns"""

    # Define paths to scan for GPU services
    service_paths = [
        Path("services"),
        Path("archive/legacy-services"),
        Path("src"),  # Check src too for any GPU utilities
    ]

    # File patterns that might contain GPU code
    gpu_file_patterns = [
        "*gpu*.py",
        "*image*classifier*.py",
        "*cuda*.py",
        "*gpu_manager*.py",  # Allow gpu_manager.py since it needs CUDA detection internally
    ]

    violations = []

    for service_path in service_paths:
        if not service_path.exists():
            continue

        for pattern in gpu_file_patterns:
            for file_path in service_path.rglob(pattern):
                if file_path.is_file() and file_path.suffix == ".py":
                    # Skip the UniversalGPUManager itself and test files
                    if file_path.name == "gpu_manager.py" or "test_" in file_path.name:
                        continue

                    file_violations = find_cuda_only_patterns(file_path)
                    if file_violations:
                        violations.append((file_path, file_violations))

    return violations


def main():
    """Main regression test"""
    print("🔍 Issue #20 Regression Test: Checking for CUDA-only GPU detection")
    print("=" * 70)

    violations = scan_gpu_services()

    if not violations:
        print("✅ SUCCESS: All GPU services use UniversalGPUManager")
        print("✅ No CUDA-only detection patterns found")
        return 0

    print("❌ FAILURE: Found CUDA-only GPU detection patterns")
    print("")

    for file_path, file_violations in violations:
        print(f"📁 File: {file_path}")
        for line_num, line in file_violations:
            print(f"   Line {line_num}: {line}")
        print("")

    print("🔧 FIX REQUIRED:")
    print("   Replace torch.cuda.is_available() with UniversalGPUManager:")
    print("")
    print("   # Before (CUDA-only)")
    print("   if torch.cuda.is_available():")
    print("       device = torch.device('cuda:0')")
    print("")
    print("   # After (Universal)")
    print("   from gpu_manager import UniversalGPUManager")
    print("   gpu_manager = UniversalGPUManager()")
    print("   device = gpu_manager.get_device()")
    print("")
    print("📚 See: docs/development/universal-gpu-dependencies.md")

    return 1


if __name__ == "__main__":
    sys.exit(main())
