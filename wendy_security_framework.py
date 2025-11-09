"""Compatibility shim for importing Wendy's security framework in tests."""

from scripts.wendy_security_framework import SecurityViolation, WendyInputSanitizer

__all__ = ["SecurityViolation", "WendyInputSanitizer"]
