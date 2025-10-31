"""
🦙 Kevin's Runtime Abstraction Package

This package provides seamless container runtime abstraction for the Crank Platform.
Kevin believes in portability without pain.

Usage:
    from runtime import RuntimeManager
    
    # Kevin chooses the best available runtime
    runtime = RuntimeManager()
    
    # Deploy a service
    container_id = runtime.run_service(
        "crank/email-classifier:latest",
        ports=["8200:8200"],
        environment=["LOG_LEVEL=INFO"]
    )
    
    # Build a service
    runtime.build_service("Dockerfile", "crank/my-service:latest")
"""

from .container_runtime import (
    ContainerRuntime,
    DockerRuntime, 
    PodmanRuntime,
    RuntimeManager,
    create_runtime_manager
)

__version__ = "1.0.0"
__author__ = "Kevin the Portability Llama 🦙"

# Convenience imports for easy usage
__all__ = [
    "ContainerRuntime",
    "DockerRuntime",
    "PodmanRuntime", 
    "RuntimeManager",
    "create_runtime_manager"
]