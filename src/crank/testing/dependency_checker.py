"""Dependency checking utilities for consistent testing behavior.

Provides standardized dependency validation with environment-specific skip handling.
Used across all Crank Platform workers to ensure consistent test behavior
regardless of deployment environment (dev/CI/production).
"""

import importlib.util
import os
import shutil
from dataclasses import dataclass

import pytest


@dataclass
class DependencyCheckResult:
    """Result of dependency availability check."""
    
    available: bool
    name: str
    skip_message: str
    install_hint: str = ""
    check_method: str = ""


def ensure_dependency(
    dependency: str,
    skip_message: str,
    install_hint: str = "",
    raise_on_missing: bool = False
) -> DependencyCheckResult:
    """
    Standard dependency checker with consistent output formatting.
    
    Args:
        dependency: Name of dependency to check (module name, executable, etc.)
        skip_message: Message to display when dependency is missing
        install_hint: Optional hint for installing the dependency
        raise_on_missing: If True, raise pytest.skip; if False, return result
        
    Returns:
        DependencyCheckResult with availability status and metadata
        
    Examples:
        # Check for Python module
        ensure_dependency("torch.cuda", "CUDA not available, skipping GPU tests")
        
        # Check for system executable
        ensure_dependency("pandoc", "Pandoc not available, skipping conversions",
                         install_hint="brew install pandoc")
    """
    result = _check_dependency_available(dependency)
    
    if not result.available:
        print(f"⚠️  SKIP: {skip_message}")
        if install_hint:
            print(f"💡 Install: {install_hint}")
            
        if raise_on_missing:
            pytest.skip(skip_message)
    
    return DependencyCheckResult(
        available=result.available,
        name=dependency,
        skip_message=skip_message,
        install_hint=install_hint,
        check_method=result.check_method
    )


def _check_dependency_available(dependency: str) -> DependencyCheckResult:
    """
    Check if a dependency is available using appropriate detection method.
    
    Supports:
    - Python modules (e.g., "torch", "torch.cuda") 
    - System executables (e.g., "pandoc", "libreoffice")
    - Special cases (e.g., "nvidia-ml-py")
    """
    # Special handling for CUDA availability
    if dependency == "torch.cuda":
        return _check_torch_cuda()
    
    # Special handling for NVIDIA ML
    if dependency == "nvidia-ml-py":
        return _check_nvidia_ml()
        
    # Check if it's a Python module
    if _is_python_module_name(dependency):
        return _check_python_module(dependency)
        
    # Check if it's a system executable
    if _is_system_executable(dependency):
        return _check_system_executable(dependency)
        
    # Default to module check
    return _check_python_module(dependency)


def _check_torch_cuda() -> DependencyCheckResult:
    """Check PyTorch CUDA availability."""
    try:
        import torch
        available = torch.cuda.is_available()
        return DependencyCheckResult(
            available=available,
            name="torch.cuda", 
            skip_message="",
            check_method="torch.cuda.is_available()"
        )
    except ImportError:
        return DependencyCheckResult(
            available=False,
            name="torch.cuda",
            skip_message="",
            check_method="import torch (failed)"
        )


def _check_nvidia_ml() -> DependencyCheckResult:
    """Check NVIDIA ML Python library."""
    try:
        import pynvml  # type: ignore[import-not-found]
        pynvml.nvmlInit()  # This will fail if no NVIDIA driver
        return DependencyCheckResult(
            available=True,
            name="nvidia-ml-py",
            skip_message="",
            check_method="pynvml.nvmlInit()"
        )
    except (ImportError, Exception):
        return DependencyCheckResult(
            available=False,
            name="nvidia-ml-py", 
            skip_message="",
            check_method="pynvml import/init (failed)"
        )


def _check_python_module(module_name: str) -> DependencyCheckResult:
    """Check if Python module can be imported."""
    try:
        spec = importlib.util.find_spec(module_name)
        available = spec is not None
        return DependencyCheckResult(
            available=available,
            name=module_name,
            skip_message="",
            check_method=f"importlib.util.find_spec({module_name})"
        )
    except (ImportError, ValueError, ModuleNotFoundError):
        return DependencyCheckResult(
            available=False,
            name=module_name,
            skip_message="",
            check_method=f"importlib.util.find_spec({module_name}) failed"
        )


def _check_system_executable(executable_name: str) -> DependencyCheckResult:
    """Check if system executable is available in PATH."""
    available = shutil.which(executable_name) is not None
    return DependencyCheckResult(
        available=available,
        name=executable_name,
        skip_message="",
        check_method=f"shutil.which({executable_name})"
    )


def _is_python_module_name(name: str) -> bool:
    """Heuristic to determine if name refers to a Python module."""
    # Contains dots (package.module) or common Python package patterns
    return ("." in name or 
            name in ["torch", "transformers", "pandas", "numpy", "fastapi", "pydantic"] or
            name.startswith(("py", "sk")))  # Common prefixes


def _is_system_executable(name: str) -> bool:
    """Heuristic to determine if name refers to a system executable."""
    # Common system tools or doesn't look like Python module
    system_tools = ["pandoc", "libreoffice", "ffmpeg", "git", "docker", "kubectl"]
    return name in system_tools or not _is_python_module_name(name)


# Convenience functions for common patterns
def skip_if_no_gpu() -> None:
    """Skip test if no GPU available."""
    ensure_dependency("torch.cuda", 
                     "CUDA not available, skipping GPU tests",
                     install_hint="Install PyTorch with CUDA support",
                     raise_on_missing=True)


def skip_if_no_pandoc() -> None:
    """Skip test if Pandoc not available.""" 
    ensure_dependency("pandoc",
                     "Pandoc not available, skipping document conversion tests",
                     install_hint="brew install pandoc",
                     raise_on_missing=True)


def skip_if_no_libreoffice() -> None:
    """Skip test if LibreOffice not available."""
    ensure_dependency("libreoffice", 
                     "LibreOffice not available, skipping office document tests",
                     install_hint="Download from https://libreoffice.org",
                     raise_on_missing=True)