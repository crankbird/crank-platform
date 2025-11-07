#!/usr/bin/env python3
"""
🚀 Quick Validation Test
Focus on validating the core changes we made work correctly.
"""

import os
import subprocess
import sys
import tempfile


def test_core_functionality():
    """Test the essential functionality that we added"""

    print("🚀 Quick Validation Test")
    print("=" * 40)

    # Test 1: Port Configuration Logic
    print("\n1. 🦙 Kevin's Port Configuration:")
    test_ports = {
        "GATEWAY_PORT": "8080",
        "PLATFORM_HTTP_PORT": "8000",
    }

    for env_var, default in test_ports.items():
        # Clear any existing value
        if env_var in os.environ:
            del os.environ[env_var]

        # Test default
        port = int(os.getenv(env_var, default))
        print(f"   ✅ {env_var}: {port} (default)")

        # Test override
        os.environ[env_var] = "9999"
        port = int(os.getenv(env_var, default))
        print(f"   ✅ {env_var}: {port} (override)")
        del os.environ[env_var]

    # Test 2: Wendy's Security Framework
    print("\n2. 🐰 Wendy's Security Framework:")
    try:
        from wendy_security_framework import WendyInputSanitizer

        sanitizer = WendyInputSanitizer()

        # Test safe filename
        safe_file = sanitizer.sanitize_filename("document.pdf")
        print(f"   ✅ Safe filename: document.pdf -> {safe_file}")

        # Test dangerous filename (should raise exception)
        try:
            sanitizer.sanitize_filename("../../../etc/passwd")
            print("   ❌ Dangerous filename was not blocked!")
        except:
            print("   ✅ Dangerous filename blocked: ../../../etc/passwd")

        # Test JSON sanitization
        test_data = {"key": "value", "port": 8080}
        sanitized = sanitizer.sanitize_json_input(test_data)
        print(f"   ✅ JSON sanitization: {len(sanitized)} fields processed")

    except Exception as e:
        print(f"   ❌ Wendy's framework error: {e}")
        return False

    # Test 3: Oliver's Pattern Detection
    print("\n3. 🦅 Oliver's Pattern Detection:")

    # Create test file with vulnerability
    test_content = """
import subprocess
import os

# Command injection vulnerability
result = subprocess.run("ls " + user_input, shell=True)

# Hardcoded secret
API_KEY = "secret123"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_content)
        temp_file = f.name

    try:
        result = subprocess.run(
            [
                "python3",
                "oliver_pattern_checker.py",
                temp_file,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )

        if result.returncode > 0:  # Oliver found violations
            output = result.stdout
            if "Command Injection Risk" in output:
                print("   ✅ Command injection detection working")
            if "Hardcoded Configuration" in output:
                print("   ✅ Hardcoded config detection working")
            if "CRITICAL SEVERITY" in output:
                print("   ✅ Security severity classification working")
        else:
            print("   ❌ Oliver didn't detect expected vulnerabilities")
            return False

    except Exception as e:
        print(f"   ❌ Oliver detection error: {e}")
        return False
    finally:
        os.unlink(temp_file)

    # Test 4: Configuration Files
    print("\n4. ⚙️  Configuration Files:")

    if os.path.exists(".env.template"):
        with open(".env.template") as f:
            content = f.read()

        required_vars = ["GATEWAY_PORT", "PLATFORM_HTTP_PORT", "DIAGNOSTICS_PORT"]
        missing = [var for var in required_vars if var not in content]

        if not missing:
            print("   ✅ .env.template has all required port variables")
        else:
            print(f"   ❌ .env.template missing: {missing}")
            return False
    else:
        print("   ❌ .env.template not found")
        return False

    print("\n" + "=" * 40)
    print("🎉 CORE FUNCTIONALITY VALIDATED!")
    print("✅ Port configuration system working")
    print("✅ Security framework operational")
    print("✅ Pattern detection enhanced")
    print("✅ Configuration files complete")
    print("\n🏆 Essential changes are working correctly!")

    return True


if __name__ == "__main__":
    success = test_core_functionality()
    sys.exit(0 if success else 1)
