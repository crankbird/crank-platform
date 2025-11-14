#!/usr/bin/env python3
"""
Test script to validate the unified knowledge base infrastructure.
Checks directory structure, file accessibility, and integration readiness.
"""

import os
import sys
from pathlib import Path
import json

def check_directory_structure():
    """Verify expected directory structure exists."""
    base_dir = Path(".")
    required_dirs = [
        "zettels",
        "gherkins", 
        "personas",
        "themes",
        "content-pipeline",
        "scripts",
        ".obsidian"
    ]
    
    print("🏗️  Checking directory structure...")
    missing_dirs = []
    
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ (missing)")
            missing_dirs.append(dir_name)
    
    return len(missing_dirs) == 0

def check_obsidian_config():
    """Verify Obsidian configuration files."""
    print("\n🧭 Checking Obsidian configuration...")
    
    obsidian_dir = Path(".obsidian")
    if not obsidian_dir.exists():
        print("  ❌ .obsidian/ directory missing")
        return False
    
    config_files = ["workspace.json", "app.json"]
    for config_file in config_files:
        config_path = obsidian_dir / config_file
        if config_path.exists():
            try:
                with open(config_path) as f:
                    json.load(f)
                print(f"  ✅ {config_file} (valid JSON)")
            except json.JSONDecodeError:
                print(f"  ❌ {config_file} (invalid JSON)")
                return False
        else:
            print(f"  ❌ {config_file} (missing)")
            return False
    
    return True

def check_integration_scripts():
    """Verify integration scripts are present and executable."""
    print("\n🔧 Checking integration scripts...")
    
    scripts_dir = Path("scripts")
    expected_scripts = [
        "integrate-zettels.py",
        "extract-gherkins.py"
    ]
    
    all_present = True
    for script_name in expected_scripts:
        script_path = scripts_dir / script_name
        if script_path.exists():
            # Check if it's a Python file
            with open(script_path) as f:
                first_line = f.readline().strip()
                if first_line.startswith('#!') and 'python' in first_line:
                    print(f"  ✅ {script_name} (executable Python)")
                else:
                    print(f"  ⚠️  {script_name} (missing shebang)")
        else:
            print(f"  ❌ {script_name} (missing)")
            all_present = False
    
    return all_present

def check_documentation():
    """Verify README and documentation files."""
    print("\n📝 Checking documentation...")
    
    readme_path = Path("README.md")
    if readme_path.exists():
        with open(readme_path) as f:
            content = f.read()
            if "# Unified Knowledge Base" in content:
                print("  ✅ README.md (proper title)")
            else:
                print("  ⚠️  README.md (missing expected title)")
                return False
    else:
        print("  ❌ README.md (missing)")
        return False
    
    return True

def main():
    """Run all infrastructure checks."""
    print("🚀 Testing Unified Knowledge Base Infrastructure\n")
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir.parent)
    
    checks = [
        ("Directory Structure", check_directory_structure),
        ("Obsidian Configuration", check_obsidian_config),
        ("Integration Scripts", check_integration_scripts), 
        ("Documentation", check_documentation)
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        try:
            if check_func():
                passed += 1
            else:
                print(f"\n❌ {check_name} check failed")
        except Exception as e:
            print(f"\n💥 {check_name} check error: {e}")
    
    print(f"\n{'='*50}")
    print(f"Infrastructure Check Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All checks passed! Infrastructure ready for integration.")
        print("\nNext steps:")
        print("1. Run integrate-zettels.py to merge content collections")
        print("2. Run extract-gherkins.py to generate feature files")
        print("3. Open directory in Obsidian as vault")
        print("4. Import gherkins into development repo")
        return 0
    else:
        print("⚠️  Infrastructure needs attention before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())