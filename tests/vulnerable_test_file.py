#!/usr/bin/env python3
"""
🚨 VULNERABLE TEST FILE - Demonstrates Security Issues
This file contains intentional security vulnerabilities for testing Oliver & Wendy's detection.
DO NOT USE IN PRODUCTION!
"""

import subprocess
import os
import pickle
import yaml
from pathlib import Path

# 🚨 COMMAND INJECTION VULNERABILITIES
def vulnerable_command_execution(user_input):
    """Bobby Tables style command injection"""
    # Dangerous: String concatenation in subprocess
    cmd = "pandoc " + user_input + " -o output.pdf"
    result = subprocess.run(cmd, shell=True)  # Very dangerous!
    
    # Another dangerous pattern
    os.system("convert " + user_input)  # Direct shell execution
    
    return result

# 🚨 PATH TRAVERSAL VULNERABILITIES  
def vulnerable_file_operations(filename):
    """Path traversal vulnerability"""
    # Dangerous: No path validation
    file_path = Path("/uploads") / filename  # Could be ../../etc/passwd
    
    # Direct string concatenation in file operations
    with open("/data/" + filename, 'r') as f:  # Path traversal risk
        content = f.read()
    
    return content

# 🚨 UNSAFE DESERIALIZATION
def vulnerable_deserialization(data):
    """Unsafe deserialization - remote code execution"""
    # Extremely dangerous: pickle can execute arbitrary code
    obj = pickle.loads(data)
    
    # Also dangerous: yaml.load instead of yaml.safe_load
    config = yaml.load(data)
    
    # Code execution risks
    result = eval(data)  # Never do this!
    exec(data)  # Or this!
    
    return obj

# 🚨 HARDCODED SECRETS
API_KEY = "sk-1234567890abcdef"  # Plaintext secret
DATABASE_PASSWORD = "super_secret_password"  # Another secret
SECRET_TOKEN = "jwt_token_12345"  # More secrets

def connect_to_api():
    """Function with hardcoded credentials"""
    return {
        "api_key": API_KEY,
        "password": DATABASE_PASSWORD,
        "token": SECRET_TOKEN
    }

# 🚨 GOD OBJECT EXAMPLE
class MassiveGodClass:
    """A class that does everything - violates Single Responsibility"""
    
    def method1(self): pass
    def method2(self): pass  
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
    def method11(self): pass
    def method12(self): pass
    def method13(self): pass
    def method14(self): pass
    def method15(self): pass
    def method16(self): pass  # This should trigger Oliver's God Object detection
    def method17(self): pass
    def method18(self): pass
    def method19(self): pass
    def method20(self): pass

if __name__ == "__main__":
    print("🚨 This file contains intentional vulnerabilities for testing!")
    print("🐰 Wendy would be very concerned about this code!")
    print("🦅 Oliver should detect multiple anti-patterns!")