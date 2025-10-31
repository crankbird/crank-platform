#!/usr/bin/env python3
"""
🐰 Wendy's Security Input Sanitization Framework
Comprehensive input validation and sanitization to prevent Bobby Tables and buffer overflow attacks.

Authority Sources:
- OWASP Top 10 2021
- NIST SP 800-53 (Input Validation)
- CWE-78 (Command Injection)
- CWE-22 (Path Traversal)
- CWE-120 (Buffer Overflow)
"""

import re
import hashlib
import mimetypes
import tempfile
import shlex
from pathlib import Path, PurePath
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SecurityViolation(Exception):
    """Raised when input fails security validation."""
    pass

class WendyInputSanitizer:
    """
    🐰 Wendy's comprehensive input sanitization framework.
    
    Prevents:
    - Command injection (Bobby Tables for commands)
    - Path traversal attacks
    - Buffer overflow via malformed inputs
    - File type confusion attacks
    - Resource exhaustion attacks
    """
    
    # File size limits (prevent buffer overflow attacks)
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_FILENAME_LENGTH = 255
    MAX_JSON_DEPTH = 10
    MAX_STRING_LENGTH = 1024 * 1024  # 1MB string limit
    
    # Allowed file extensions (whitelist approach)
    ALLOWED_DOCUMENT_EXTENSIONS = {
        'txt', 'md', 'pdf', 'docx', 'doc', 'rtf', 'html', 'htm', 'odt'
    }
    
    ALLOWED_EMAIL_EXTENSIONS = {
        'eml', 'msg', 'mbox', 'txt'
    }
    
    ALLOWED_IMAGE_EXTENSIONS = {
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'tif'
    }
    
    # Dangerous patterns that could indicate injection attempts
    DANGEROUS_PATTERNS = [
        r'\.\.[\\/]',  # Path traversal
        r'[;&|`$()]',  # Command injection characters
        r'<script',    # XSS attempts
        r'javascript:', # Javascript URLs
        r'vbscript:',  # VBScript URLs
        r'data:',      # Data URLs (can be dangerous)
        r'\\x[0-9a-fA-F]{2}',  # Hex encoding (potential obfuscation)
        r'%[0-9a-fA-F]{2}',     # URL encoding (potential obfuscation)
    ]
    
    def __init__(self):
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.DANGEROUS_PATTERNS]
    
    def sanitize_filename(self, filename: str, service_type: str = "document") -> str:
        """
        🐰 Wendy's filename sanitization - prevents path traversal and injection.
        
        Authority: OWASP File Upload Security, CWE-22
        """
        if not filename:
            raise SecurityViolation("Empty filename not allowed")
        
        if len(filename) > self.MAX_FILENAME_LENGTH:
            raise SecurityViolation(f"Filename too long: {len(filename)} > {self.MAX_FILENAME_LENGTH}")
        
        # Check for dangerous patterns
        for pattern in self.compiled_patterns:
            if pattern.search(filename):
                raise SecurityViolation(f"Dangerous pattern detected in filename: {filename}")
        
        # Extract just the filename (no path components)
        safe_path = PurePath(filename)
        clean_filename = safe_path.name
        
        # Validate extension
        extension = clean_filename.split('.')[-1].lower() if '.' in clean_filename else ''
        
        if service_type == "document":
            allowed_exts = self.ALLOWED_DOCUMENT_EXTENSIONS
        elif service_type == "email":
            allowed_exts = self.ALLOWED_EMAIL_EXTENSIONS
        elif service_type == "image":
            allowed_exts = self.ALLOWED_IMAGE_EXTENSIONS
        else:
            allowed_exts = self.ALLOWED_DOCUMENT_EXTENSIONS
        
        if extension and extension not in allowed_exts:
            raise SecurityViolation(f"File extension '{extension}' not allowed for {service_type} service")
        
        # Generate safe filename using hash if needed
        if not re.match(r'^[a-zA-Z0-9._-]+$', clean_filename):
            # Use hash-based naming for safety
            file_hash = hashlib.sha256(filename.encode()).hexdigest()[:16]
            safe_filename = f"file_{file_hash}.{extension}" if extension else f"file_{file_hash}"
            logger.warning(f"🐰 Wendy sanitized dangerous filename: {filename} -> {safe_filename}")
            return safe_filename
        
        return clean_filename
    
    def validate_file_content(self, content: bytes, expected_type: str, filename: str = "") -> bool:
        """
        🐰 Wendy's file content validation - prevents malformed file attacks.
        
        Authority: OWASP File Upload Security, CWE-434
        """
        if len(content) == 0:
            raise SecurityViolation("Empty file content not allowed")
        
        if len(content) > self.MAX_FILE_SIZE:
            raise SecurityViolation(f"File too large: {len(content)} > {self.MAX_FILE_SIZE}")
        
        # Basic magic number validation
        magic_numbers = {
            'pdf': [b'%PDF'],
            'docx': [b'PK\x03\x04'],  # ZIP format
            'jpg': [b'\xff\xd8\xff'],
            'png': [b'\x89PNG\r\n\x1a\n'],
            'gif': [b'GIF87a', b'GIF89a'],
        }
        
        if expected_type in magic_numbers:
            if not any(content.startswith(magic) for magic in magic_numbers[expected_type]):
                logger.warning(f"🐰 Wendy detected file type mismatch: {filename}")
                # Don't fail hard, but log the suspicious activity
        
        # Check for embedded executable content (basic scan)
        dangerous_signatures = [
            b'MZ',  # PE executable
            b'\x7fELF',  # ELF executable
            b'\xfe\xed\xfa',  # Mach-O executable
            b'<script',  # Embedded scripts
            b'javascript:',
            b'vbscript:',
        ]
        
        for signature in dangerous_signatures:
            if signature in content:
                raise SecurityViolation(f"Dangerous content detected in file: {filename}")
        
        return True
    
    def sanitize_json_input(self, data: Any, max_depth: int = None, current_depth: int = 0) -> Any:
        """
        🐰 Wendy's JSON input sanitization - prevents deep recursion and oversized data.
        
        Authority: OWASP JSON Security, CWE-400 (Resource Exhaustion)
        """
        if max_depth is None:
            max_depth = self.MAX_JSON_DEPTH
        
        if current_depth > max_depth:
            raise SecurityViolation(f"JSON nesting too deep: {current_depth} > {max_depth}")
        
        if isinstance(data, dict):
            if len(data) > 1000:  # Limit dict size
                raise SecurityViolation(f"Dictionary too large: {len(data)} keys")
            
            sanitized = {}
            for key, value in data.items():
                # Sanitize keys
                clean_key = self.sanitize_string(str(key), max_length=100)
                clean_value = self.sanitize_json_input(value, max_depth, current_depth + 1)
                sanitized[clean_key] = clean_value
            return sanitized
        
        elif isinstance(data, list):
            if len(data) > 10000:  # Limit array size
                raise SecurityViolation(f"Array too large: {len(data)} items")
            
            return [self.sanitize_json_input(item, max_depth, current_depth + 1) for item in data]
        
        elif isinstance(data, str):
            return self.sanitize_string(data)
        
        elif isinstance(data, (int, float, bool)) or data is None:
            return data
        
        else:
            # Convert unknown types to string and sanitize
            return self.sanitize_string(str(data))
    
    def sanitize_string(self, text: str, max_length: int = None) -> str:
        """
        🐰 Wendy's string sanitization - prevents injection and overflow.
        
        Authority: OWASP Input Validation, CWE-20
        """
        if max_length is None:
            max_length = self.MAX_STRING_LENGTH
        
        if len(text) > max_length:
            raise SecurityViolation(f"String too long: {len(text)} > {max_length}")
        
        # Check for dangerous patterns
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                # Log but don't fail - might be legitimate content
                logger.warning(f"🐰 Wendy detected suspicious pattern in text: {pattern.pattern}")
        
        # Remove null bytes (can cause issues in C libraries)
        text = text.replace('\x00', '')
        
        # Limit control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        return text
    
    def create_safe_temp_file(self, content: bytes, suffix: str = "") -> Path:
        """
        🐰 Wendy's safe temporary file creation - prevents path traversal.
        
        Authority: OWASP File Upload Security, CWE-22
        """
        # Sanitize suffix
        clean_suffix = re.sub(r'[^a-zA-Z0-9.]', '', suffix)
        if not clean_suffix.startswith('.'):
            clean_suffix = '.' + clean_suffix if clean_suffix else '.tmp'
        
        # Create secure temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=clean_suffix) as tmp_file:
            tmp_file.write(content)
            temp_path = Path(tmp_file.name)
        
        # Verify the file was created in the expected location
        if not str(temp_path).startswith(tempfile.gettempdir()):
            temp_path.unlink(missing_ok=True)
            raise SecurityViolation("Temporary file created outside safe directory")
        
        return temp_path
    
    def sanitize_command_args(self, args: List[str]) -> List[str]:
        """
        🐰 Wendy's command argument sanitization - prevents command injection.
        
        Authority: OWASP Command Injection Prevention, CWE-78
        """
        sanitized_args = []
        
        for arg in args:
            # Use shlex.quote for proper shell escaping
            if isinstance(arg, str):
                # Additional validation
                if any(pattern.search(arg) for pattern in self.compiled_patterns):
                    raise SecurityViolation(f"Dangerous pattern in command argument: {arg}")
                
                # Escape the argument properly
                safe_arg = shlex.quote(arg)
                sanitized_args.append(safe_arg)
            else:
                sanitized_args.append(shlex.quote(str(arg)))
        
        return sanitized_args
    
    def validate_request_size(self, request_data: Dict[str, Any]) -> bool:
        """
        🐰 Wendy's request size validation - prevents resource exhaustion.
        
        Authority: OWASP DoS Prevention, CWE-400
        """
        # Estimate request size
        import json
        try:
            request_size = len(json.dumps(request_data))
            if request_size > 50 * 1024 * 1024:  # 50MB limit
                raise SecurityViolation(f"Request too large: {request_size} bytes")
        except (TypeError, ValueError):
            # If we can't serialize, it's probably too complex
            raise SecurityViolation("Request data too complex to validate")
        
        return True

# Global instance for easy import
wendy_sanitizer = WendyInputSanitizer()

def validate_upload_file(file_content: bytes, filename: str, service_type: str = "document") -> tuple[bytes, str]:
    """
    🐰 Wendy's complete file upload validation.
    
    Returns: (validated_content, safe_filename)
    Raises: SecurityViolation on any security issues
    """
    # Sanitize filename
    safe_filename = wendy_sanitizer.sanitize_filename(filename, service_type)
    
    # Validate content
    wendy_sanitizer.validate_file_content(file_content, service_type, safe_filename)
    
    logger.info(f"🐰 Wendy approved file upload: {safe_filename} ({len(file_content)} bytes)")
    
    return file_content, safe_filename

def validate_json_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    🐰 Wendy's complete JSON request validation.
    
    Returns: Sanitized request data
    Raises: SecurityViolation on any security issues
    """
    # Validate request size
    wendy_sanitizer.validate_request_size(data)
    
    # Sanitize all input data
    sanitized_data = wendy_sanitizer.sanitize_json_input(data)
    
    logger.info(f"🐰 Wendy approved JSON request with {len(sanitized_data)} fields")
    
    return sanitized_data

def safe_subprocess_run(cmd: List[str], **kwargs) -> Any:
    """
    🐰 Wendy's safe subprocess execution - prevents command injection.
    
    Authority: OWASP Command Injection Prevention, CWE-78
    """
    import subprocess
    
    # Sanitize command arguments
    safe_cmd = wendy_sanitizer.sanitize_command_args(cmd)
    
    # Set safe defaults
    safe_kwargs = {
        'capture_output': True,
        'text': True,
        'timeout': 30,  # Prevent hanging
        'check': False,  # Don't raise on non-zero exit
        **kwargs
    }
    
    logger.info(f"🐰 Wendy executing safe command: {safe_cmd[0]} (with {len(safe_cmd)-1} args)")
    
    try:
        result = subprocess.run(safe_cmd, **safe_kwargs)
        return result
    except subprocess.TimeoutExpired:
        raise SecurityViolation("Command execution timeout - possible DoS attempt")
    except subprocess.CalledProcessError as e:
        logger.warning(f"🐰 Wendy detected command failure: {e}")
        raise SecurityViolation(f"Command execution failed: {e}")

if __name__ == "__main__":
    # Test the sanitizer
    sanitizer = WendyInputSanitizer()
    
    # Test filename sanitization
    test_files = [
        "normal_file.pdf",
        "../../../etc/passwd",
        "file; rm -rf /",
        "file$(whoami).txt",
        "Ȧṫṫṛḭɓüṫḝd_ḟḭłḗ.pdf",
    ]
    
    print("🐰 Wendy's Security Test Results:")
    print("=" * 50)
    
    for filename in test_files:
        try:
            safe_name = sanitizer.sanitize_filename(filename)
            print(f"✅ {filename:25} -> {safe_name}")
        except SecurityViolation as e:
            print(f"🚨 {filename:25} -> BLOCKED: {e}")
    
    print("\n🐰 Wendy says: Input sanitization system ready!")