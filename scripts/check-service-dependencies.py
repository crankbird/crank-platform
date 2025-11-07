#!/usr/bin/env python3
"""
Service Dependency Checker

Validates that all required dependencies are available before service startup.
Prevents silent failures from missing GPU libraries.
"""

import sys
import importlib
from typing import List, Optional

def check_dependency(package: str, import_name: Optional[str] = None) -> bool:
    """Check if a package can be imported"""
    try:
        module_name = import_name or package
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def get_service_dependencies(service_name: str) -> List[str]:
    """Get required dependencies for a service"""

    dependencies = {
        "crank_image_classifier": [
            "torch",
            "torchvision",
            "ultralytics",
            "cv2:opencv-python",
            "GPUtil",
            "psutil",
            "PIL:Pillow"
        ],
        "universal_gpu_base": [
            "torch",
            "psutil"
        ]
    }

    return dependencies.get(service_name, [])

def validate_service_dependencies(service_name: str) -> bool:
    """Validate all dependencies for a service"""

    print(f"🔍 Checking dependencies for {service_name}")
    print("=" * 50)

    dependencies = get_service_dependencies(service_name)
    if not dependencies:
        print(f"⚠️  No dependency requirements defined for {service_name}")
        return True

    missing = []
    available = []

    for dep in dependencies:
        if ":" in dep:
            import_name, package_name = dep.split(":")
        else:
            import_name, package_name = dep, dep

        if check_dependency(package_name, import_name):
            available.append(f"✅ {package_name}")
        else:
            missing.append(f"❌ {package_name} (import: {import_name})")

    # Report results
    if available:
        print("Available dependencies:")
        for dep in available:
            print(f"  {dep}")

    if missing:
        print("\nMissing dependencies:")
        for dep in missing:
            print(f"  {dep}")

        print("\n🔧 Install missing dependencies:")
        print("   cd /path/to/crank-platform")
        print("   source .venv/bin/activate")
        print("   ./scripts/install-gpu-dependencies.sh")

        return False

    print(f"\n🎯 All dependencies satisfied for {service_name}!")
    return True

def main():
    """Main dependency checker"""

    if len(sys.argv) < 2:
        print("Usage: python check-service-dependencies.py <service_name>")
        print("Examples:")
        print("  python check-service-dependencies.py crank_image_classifier")
        print("  python check-service-dependencies.py universal_gpu_base")
        sys.exit(1)

    service_name = sys.argv[1]

    if validate_service_dependencies(service_name):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
