"""Testing utilities for Crank Platform workers.

Provides standardized dependency checking and environment-specific skip handling
for consistent testing behavior across development, CI, and production environments.
"""

from .dependency_checker import DependencyCheckResult, ensure_dependency

__all__ = ["DependencyCheckResult", "ensure_dependency"]
