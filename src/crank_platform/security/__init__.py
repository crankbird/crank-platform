"""
Security module for Crank Platform

Provides certificate management, initialization, and worker patterns
for secure service communication.
"""

# Import the main certificate components for easy access
from .cert_initialize import SecureCertificateStore, cert_store
from .cert_initialize import main as init_certificates
from .cert_worker_pattern import WorkerCertificatePattern, create_worker_fastapi_with_certs

__all__ = [
    "SecureCertificateStore",
    "WorkerCertificatePattern",
    "cert_store",
    "create_worker_fastapi_with_certs",
    "init_certificates",
]
