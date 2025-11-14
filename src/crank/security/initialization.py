"""
Certificate Initialization

Handles certificate bootstrapping for workers and controllers:
- CSR generation (private keys never leave worker)
- CA service communication
- Certificate storage and validation

Workers use this to obtain certificates from the CA service.
Controllers use this for initial CA setup.
"""

import asyncio
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import aiohttp

from .config import get_security_config
from .constants import (
    CA_CERT_FILENAME,
    CLIENT_CERT_FILENAME,
    CLIENT_KEY_FILENAME,
    DEFAULT_CA_SERVICE_TIMEOUT,
    DEFAULT_CA_SERVICE_URL,
    RSA_KEY_SIZE,
)
from .events import CertificateEvent, emit_certificate_event, record_ca_unavailable

logger = logging.getLogger(__name__)


# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 16.0  # seconds


class CertificateInitializationError(Exception):
    """Raised when certificate initialization fails."""


async def wait_for_ca_service(
    ca_service_url: str,
    timeout: int = DEFAULT_CA_SERVICE_TIMEOUT,
    correlation_id: Optional[str] = None,
) -> bool:
    """
    Wait for Certificate Authority Service to become available.

    Args:
        ca_service_url: CA service endpoint URL
        timeout: Maximum wait time in seconds
        correlation_id: Optional correlation ID for distributed tracing

    Returns:
        True if CA service is available, False if timeout

    Example:
        >>> if await wait_for_ca_service("https://cert-authority:9090"):
        ...     print("CA service ready")
    """
    logger.info("⏳ Waiting for Certificate Authority Service at %s", ca_service_url)

    for attempt in range(timeout):
        try:
            # Use insecure connection for health check (CA cert not yet obtained)
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False),
                timeout=aiohttp.ClientTimeout(total=2),
            ) as session:
                async with session.get(f"{ca_service_url}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        logger.info(
                            "✅ Certificate Authority Service ready: %s",
                            health_data.get("provider", "unknown"),
                        )
                        return True
        except Exception as e:
            logger.debug("CA service not ready (attempt %d/%d): %s", attempt + 1, timeout, e)

        await asyncio.sleep(1)

    # Emit CA unavailable event
    emit_certificate_event(
        CertificateEvent.CA_UNAVAILABLE,
        worker_id="system",
        correlation_id=correlation_id,
        metadata={"ca_service_url": ca_service_url, "timeout": timeout},
        log_level=logging.ERROR,
    )
    record_ca_unavailable("system")

    logger.error("❌ Certificate Authority Service not available after %d seconds", timeout)
    return False


async def get_ca_certificate(
    ca_service_url: str,
    correlation_id: Optional[str] = None,
) -> str:
    """
    Retrieve CA root certificate for verification.

    Args:
        ca_service_url: CA service endpoint URL
        correlation_id: Optional correlation ID for distributed tracing

    Returns:
        CA certificate PEM string

    Raises:
        CertificateInitializationError: If CA cert retrieval fails after retries
    """
    logger.info("📥 Retrieving CA certificate from %s", ca_service_url)

    for attempt in range(MAX_RETRIES):
        try:
            # Use insecure connection (we don't have CA cert yet)
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False),
                timeout=aiohttp.ClientTimeout(total=5),
            ) as session:
                async with session.get(f"{ca_service_url}/ca/certificate") as response:
                    if response.status == 200:
                        ca_data = await response.json()
                        ca_cert: str = ca_data["ca_certificate"]
                        logger.info("✅ CA certificate obtained for verification")
                        return ca_cert

                    error_text = await response.text()
                    raise CertificateInitializationError(
                        f"Failed to get CA certificate: {response.status} - {error_text}"
                    )
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                backoff = min(INITIAL_BACKOFF * (2 ** attempt), MAX_BACKOFF)
                logger.warning(
                    "⚠️ Failed to get CA certificate (attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1, MAX_RETRIES, backoff, e
                )
                emit_certificate_event(
                    CertificateEvent.CA_UNAVAILABLE,
                    worker_id="system",
                    correlation_id=correlation_id,
                    metadata={
                        "ca_service_url": ca_service_url,
                        "attempt": attempt + 1,
                        "max_retries": MAX_RETRIES,
                        "error": str(e),
                    },
                    log_level=logging.WARNING,
                )
                record_ca_unavailable("system")
                await asyncio.sleep(backoff)
            else:
                logger.error("❌ Failed to retrieve CA certificate after %d attempts", MAX_RETRIES)
                emit_certificate_event(
                    CertificateEvent.CA_UNAVAILABLE,
                    worker_id="system",
                    correlation_id=correlation_id,
                    metadata={
                        "ca_service_url": ca_service_url,
                        "attempts": MAX_RETRIES,
                        "error": str(e),
                    },
                    log_level=logging.ERROR,
                )
                record_ca_unavailable("system")
                if isinstance(e, CertificateInitializationError):
                    raise
                raise CertificateInitializationError(f"CA certificate retrieval failed: {e}") from e

    # Should never reach here
    raise CertificateInitializationError("Unexpected retry loop exit")


async def generate_csr(
    worker_id: str,
    additional_san_names: Optional[list[str]] = None,
) -> tuple[str, str]:
    """
    Generate RSA key pair and Certificate Signing Request locally (async).

    SECURITY: Private key is generated locally and NEVER transmitted.
    Only the CSR (containing public key) is sent to the CA service.

    NOTE: Runs CPU-intensive OpenSSL operations in thread pool to avoid
    blocking the event loop. RSA-4096 key generation can take seconds.

    Args:
        worker_id: Worker/service identifier (becomes CN in certificate)
        additional_san_names: Additional Subject Alternative Names

    Returns:
        Tuple of (private_key_pem, csr_pem)

    Raises:
        CertificateInitializationError: If CSR generation fails

    Example:
        >>> private_key, csr = await generate_csr("streaming-worker-1")
        >>> # private_key stays local, only csr is sent to CA
    """
    logger.info("🔑 Generating local RSA key pair and CSR for %s...", worker_id)

    def _generate_csr_sync() -> tuple[str, str]:
        """Synchronous CSR generation (runs in thread pool)."""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                private_key_path = temp_path / "service.key"
                csr_path = temp_path / "service.csr"
                config_path = temp_path / "csr.conf"

                # Generate RSA private key locally (NEVER leaves this machine)
                subprocess.run(
                    [
                        "openssl",
                        "genrsa",
                        "-out",
                        str(private_key_path),
                        str(RSA_KEY_SIZE),
                    ],
                    check=True,
                    capture_output=True,
                )
                logger.info("✅ Private key generated locally (%d-bit RSA)", RSA_KEY_SIZE)

                # Build Subject Alternative Names list
                san_names = [worker_id, "localhost"]
                if additional_san_names:
                    san_names.extend(additional_san_names)

                san_list = ",".join([f"DNS:{name}" for name in san_names])

                # Create OpenSSL config for CSR with SAN extensions
                config_content = f"""[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
CN = {worker_id}
O = Crank Platform
OU = Worker Services

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = {san_list}
"""

                config_path.write_text(config_content)

                # Generate CSR with SAN extensions
                subprocess.run(
                    [
                        "openssl",
                        "req",
                        "-new",
                        "-key",
                        str(private_key_path),
                        "-out",
                        str(csr_path),
                        "-config",
                        str(config_path),
                    ],
                    check=True,
                    capture_output=True,
                )
                logger.info("✅ CSR generated with SAN: %s", san_list)

                # Read generated key and CSR
                private_key_pem = private_key_path.read_text()
                csr_pem = csr_path.read_text()

                return private_key_pem, csr_pem

        except subprocess.CalledProcessError as e:
            raise CertificateInitializationError(
                f"OpenSSL CSR generation failed: {e.stderr.decode() if e.stderr else str(e)}"
            ) from e
        except Exception as e:
            raise CertificateInitializationError(f"CSR generation failed: {e}") from e

    try:
        # Run blocking OpenSSL operations in thread pool to avoid blocking event loop
        private_key_pem, csr_pem = await asyncio.to_thread(_generate_csr_sync)

        # Build SAN list for event metadata (matches what was generated in sync function)
        san_names = [worker_id, "localhost"]
        if additional_san_names:
            san_names.extend(additional_san_names)

        # Emit observability event (now that we're back in async context)
        emit_certificate_event(
            CertificateEvent.CSR_GENERATED,
            worker_id=worker_id,
            metadata={"key_size": RSA_KEY_SIZE, "san_names": san_names},
        )

        return private_key_pem, csr_pem

    except CertificateInitializationError:
        raise
    except Exception as e:
        raise CertificateInitializationError(f"Async CSR generation failed: {e}") from e


async def submit_csr(
    ca_service_url: str,
    csr_pem: str,
    worker_id: str,
    correlation_id: Optional[str] = None,
) -> str:
    """
    Submit Certificate Signing Request to CA service.

    Args:
        ca_service_url: CA service endpoint URL
        csr_pem: Certificate Signing Request in PEM format
        worker_id: Worker/service identifier
        correlation_id: Optional correlation ID for distributed tracing

    Returns:
        Signed certificate in PEM format

    Raises:
        CertificateInitializationError: If CSR submission/signing fails after retries
    """
    logger.info("📝 Submitting CSR to CA service for %s", worker_id)

    # Emit observability event
    emit_certificate_event(
        CertificateEvent.CSR_SUBMITTED,
        worker_id=worker_id,
        correlation_id=correlation_id,
    )

    for attempt in range(MAX_RETRIES):
        try:
            # Use insecure connection (we're getting our first cert)
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as session:
                async with session.post(
                    f"{ca_service_url}/certificates/csr",
                    json={
                        "csr": csr_pem,
                        "service_name": worker_id,
                    },
                ) as response:
                    if response.status == 200:
                        cert_response = await response.json()
                        signed_cert: str = cert_response["certificate"]
                        logger.info("✅ Certificate signed by CA service")

                        # Note: CERT_ISSUED event emitted after files persisted in initialize_worker_certificates
                        # to avoid double-counting in metrics/alerting

                        return signed_cert

                    error_text = await response.text()
                    raise CertificateInitializationError(
                        f"CA service rejected CSR: {response.status} - {error_text}"
                    )

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                backoff = min(INITIAL_BACKOFF * (2 ** attempt), MAX_BACKOFF)
                logger.warning(
                    "⚠️ Failed to submit CSR (attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1, MAX_RETRIES, backoff, e
                )
                emit_certificate_event(
                    CertificateEvent.CA_UNAVAILABLE,
                    worker_id=worker_id,
                    correlation_id=correlation_id,
                    metadata={
                        "ca_service_url": ca_service_url,
                        "attempt": attempt + 1,
                        "max_retries": MAX_RETRIES,
                        "error": str(e),
                    },
                    log_level=logging.WARNING,
                )
                record_ca_unavailable(worker_id)
                await asyncio.sleep(backoff)
            else:
                logger.error("❌ Failed to submit CSR after %d attempts", MAX_RETRIES)
                # Emit CA-specific failure event with full context for observability
                emit_certificate_event(
                    CertificateEvent.CSR_FAILED,
                    worker_id=worker_id,
                    correlation_id=correlation_id,
                    metadata={
                        "phase": "csr_submission",
                        "attempts": MAX_RETRIES,
                        "error": str(e),
                        "ca_service_url": ca_service_url,
                    },
                    log_level=logging.ERROR,
                )
                if isinstance(e, CertificateInitializationError):
                    raise
                raise CertificateInitializationError(f"CSR submission failed: {e}") from e

    # Should never reach here
    raise CertificateInitializationError("Unexpected retry loop exit")


async def initialize_worker_certificates(
    worker_id: str,
    ca_service_url: Optional[str] = None,
    cert_dir: Optional[Path] = None,
    additional_san_names: Optional[list[str]] = None,
    correlation_id: Optional[str] = None,
) -> tuple[Path, Path, Path]:
    """
    Initialize certificates for a worker using secure CSR pattern.

    Complete flow:
    1. Wait for CA service availability
    2. Generate local key pair + CSR (private key never leaves)
    3. Submit CSR to CA service
    4. Receive signed certificate
    5. Store certificates to disk

    Args:
        worker_id: Worker/service identifier
        ca_service_url: CA service URL (default: from config)
        cert_dir: Certificate directory (default: from config)
        additional_san_names: Additional Subject Alternative Names
        correlation_id: Optional correlation ID for distributed tracing

    Returns:
        Tuple of (cert_file, key_file, ca_cert_file) paths

    Raises:
        CertificateInitializationError: If initialization fails

    Example:
        >>> cert, key, ca = await initialize_worker_certificates("streaming-1")
        >>> print(f"Certificates ready: {cert}")
    """
    config = get_security_config()
    ca_service_url = ca_service_url or os.getenv("CA_SERVICE_URL", DEFAULT_CA_SERVICE_URL)
    cert_dir = cert_dir or config.cert_dir

    # Ensure ca_service_url is not None
    if not ca_service_url:
        raise CertificateInitializationError("CA_SERVICE_URL not configured")

    logger.info("🔐 Initializing certificates for worker: %s", worker_id)
    logger.info("📁 Certificate directory: %s", cert_dir)
    logger.info("🌐 CA Service URL: %s", ca_service_url)

    try:
        # Step 1: Wait for CA service
        if not await wait_for_ca_service(ca_service_url, correlation_id=correlation_id):
            raise CertificateInitializationError("CA service unavailable")

        # Step 2: Get CA certificate for verification
        ca_cert_pem = await get_ca_certificate(ca_service_url, correlation_id=correlation_id)

        # Step 3: Generate local key pair and CSR (async to avoid blocking event loop)
        private_key_pem, csr_pem = await generate_csr(worker_id, additional_san_names)

        # Step 4: Submit CSR and get signed certificate
        signed_cert_pem = await submit_csr(
            ca_service_url, csr_pem, worker_id, correlation_id=correlation_id
        )

        # Step 5: Store certificates to disk
        # Check if cert_dir is writable, provide helpful error if not
        try:
            cert_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Helpful error message for common development scenario
            dev_cert_dir = Path("./certs").resolve()
            raise CertificateInitializationError(
                f"Cannot create certificate directory {cert_dir} (permission denied).\n"
                f"\n"
                f"Production: Run as root or ensure directory exists with proper permissions.\n"
                f"Development: Set CERT_DIR environment variable:\n"
                f"  export CERT_DIR={dev_cert_dir}\n"
                f"  # or use helper: source scripts/dev-setup-certs.sh\n"
                f"\n"
                f"Then re-run initialization."
            ) from None

        # CRITICAL: Write to client.{crt,key} for mTLS client compatibility
        # This ensures create_mtls_client() can find certificates without
        # manual file copying/symlinking
        cert_file = cert_dir / CLIENT_CERT_FILENAME
        key_file = cert_dir / CLIENT_KEY_FILENAME
        ca_cert_file = cert_dir / CA_CERT_FILENAME

        cert_file.write_text(signed_cert_pem)
        key_file.write_text(private_key_pem)
        ca_cert_file.write_text(ca_cert_pem)

        # Set proper permissions
        key_file.chmod(0o600)  # Private key: owner read/write only
        cert_file.chmod(0o644)  # Certificate: owner read/write, others read
        ca_cert_file.chmod(0o644)  # CA cert: owner read/write, others read

        logger.info("✅ Certificates initialized and stored")
        logger.info("   Cert: %s", cert_file)
        logger.info("   Key:  %s", key_file)
        logger.info("   CA:   %s", ca_cert_file)

        # Emit bootstrap success event
        emit_certificate_event(
            CertificateEvent.CERT_ISSUED,
            worker_id=worker_id,
            correlation_id=correlation_id,
            metadata={
                "cert_file": str(cert_file),
                "key_file": str(key_file),
                "ca_cert_file": str(ca_cert_file),
            },
        )

        return cert_file, key_file, ca_cert_file

    except CertificateInitializationError:
        # CSR-specific failures already emitted their events, just propagate
        raise
    except Exception as e:
        logger.error("❌ Certificate initialization failed for %s: %s", worker_id, e)
        # Emit failure event for non-CSR failures (file I/O, unexpected errors)
        # CSR submission failures are handled in submit_csr with CA-specific context
        emit_certificate_event(
            CertificateEvent.CSR_FAILED,
            worker_id=worker_id,
            correlation_id=correlation_id,
            metadata={"error": str(e), "phase": "bootstrap_other"},
            log_level=logging.ERROR,
        )
        raise


# Convenience function for backward compatibility with old patterns
async def initialize_certificates_from_env() -> tuple[Path, Path, Path]:
    """
    Initialize certificates using environment variables.

    Reads: SERVICE_NAME, CA_SERVICE_URL, CERT_DIR from environment.
    This is a convenience wrapper for containerized workers.

    Returns:
        Tuple of (cert_file, key_file, ca_cert_file) paths

    Raises:
        CertificateInitializationError: If initialization fails
    """
    worker_id = os.getenv("SERVICE_NAME", "worker")
    return await initialize_worker_certificates(worker_id=worker_id)
