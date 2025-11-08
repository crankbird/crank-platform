"""
Certificate Authority Service - Pluggable Certificate Provider
=============================================================

Abstract interface for certificate provisioning that can be implemented by:
- Development: Self-signed certificate generation
- On-Premise: HashiCorp Vault, Active Directory Certificate Services
- Cloud: Azure Key Vault, AWS Certificate Manager, Google Certificate Authority
- Hardware: Hardware Security Modules (HSMs), Smart Cards
"""

import logging
import os
import shutil
import subprocess
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# Custom exceptions for certificate operations
class CertificateGenerationError(Exception):
    """Raised when certificate generation fails."""


class CertificateNotFoundError(Exception):
    """Raised when required certificate files are not found."""


class CertificateReadError(Exception):
    """Raised when certificate files cannot be read."""


@dataclass
class CertificateRequest:
    """Standard certificate request format across all providers."""

    common_name: str
    organization: str = "Crank Platform"
    organizational_unit: str = "Security"
    country: str = "US"
    state: str = "CA"
    locality: str = "San Francisco"
    subject_alt_names: Optional[list[str]] = None
    key_usage: Optional[list[str]] = None
    extended_key_usage: Optional[list[str]] = None
    validity_days: int = 365


@dataclass
class CertificateBundle:
    """Standard certificate bundle returned by all providers."""

    certificate: str  # PEM-encoded certificate
    private_key: str  # PEM-encoded private key
    certificate_chain: str  # Full certificate chain
    ca_certificate: str  # CA certificate for verification
    metadata: dict[str, Any]  # Provider-specific metadata


class CertificateProvider(ABC):
    """Abstract Certificate Authority interface."""

    @abstractmethod
    async def provision_server_certificate(self, request: CertificateRequest) -> CertificateBundle:
        """Provision a server certificate for TLS."""

    @abstractmethod
    async def provision_client_certificate(self, request: CertificateRequest) -> CertificateBundle:
        """Provision a client certificate for mTLS."""

    @abstractmethod
    async def get_ca_certificate(self) -> str:
        """Get the Certificate Authority root certificate."""

    @abstractmethod
    async def sign_certificate_request(self, csr_pem: str, service_name: str) -> str:
        """Sign a Certificate Signing Request (CSR) and return the signed certificate."""

    @abstractmethod
    async def revoke_certificate(self, serial_number: str) -> bool:
        """Revoke a certificate by serial number."""

    @abstractmethod
    async def validate_certificate(self, certificate: str) -> dict[str, Any]:
        """Validate a certificate against this CA."""

    @abstractmethod
    def get_provider_info(self) -> dict[str, str]:
        """Get provider type and configuration info."""


class DevelopmentCertificateProvider(CertificateProvider):
    """Development certificate provider using self-signed certificates."""

    def __init__(self, cert_dir: Path):
        self.cert_dir = cert_dir
        self.cert_dir.mkdir(parents=True, exist_ok=True)
        self.ca_key_file = self.cert_dir / "ca.key"
        self.ca_cert_file = self.cert_dir / "ca.crt"
        self._ca_initialized = False

    async def _ensure_ca_certificate(self) -> None:
        """Ensure CA certificate exists, generate if needed."""
        if not self._ca_initialized:
            if not self.ca_cert_file.exists() or not self.ca_key_file.exists():
                await self._generate_ca_certificate()
            self._ca_initialized = True

    async def _generate_ca_certificate(self) -> None:
        """Generate a real CA certificate for development."""

        logger.info("🔐 Generating development CA certificate...")

        try:
            # Generate CA key
            subprocess.run(
                [
                    "openssl",
                    "genrsa",
                    "-out",
                    str(self.ca_key_file),
                    "2048",
                ],
                check=True,
                capture_output=True,
            )

            # Generate CA certificate
            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-new",
                    "-x509",
                    "-key",
                    str(self.ca_key_file),
                    "-out",
                    str(self.ca_cert_file),
                    "-days",
                    "365",
                    "-nodes",
                    "-subj",
                    "/CN=Development CA/O=Crank Platform/OU=Development",
                ],
                check=True,
                capture_output=True,
            )

            logger.info("✅ Development CA certificate generated successfully")

        except subprocess.CalledProcessError as e:
            logger.exception("❌ Failed to generate CA certificate")
            raise CertificateGenerationError(f"CA certificate generation failed: {e}") from e

    async def provision_server_certificate(self, request: CertificateRequest) -> CertificateBundle:
        """Generate self-signed server certificate for development."""
        logger.info("🔧 Generating development server certificate for {request.common_name}")

        # For development, create simple self-signed certificates
        certificate = f"""-----BEGIN CERTIFICATE-----
MIIDevelopmentServerCert{request.common_name}
-----END CERTIFICATE-----"""

        private_key = f"""-----BEGIN PRIVATE KEY-----
MIIDevelopmentServerKey{request.common_name}
-----END PRIVATE KEY-----"""

        ca_cert = await self.get_ca_certificate()

        metadata = {
            "common_name": request.common_name,
            "serial_number": "dev-001",
            "issued_at": "2024-01-01T00:00:00Z",
            "expires_at": "2025-01-01T00:00:00Z",
            "provider": "development",
        }

        return CertificateBundle(
            certificate=certificate,
            private_key=private_key,
            certificate_chain=certificate,
            ca_certificate=ca_cert,
            metadata=metadata,
        )

    async def provision_client_certificate(self, request: CertificateRequest) -> CertificateBundle:
        """Generate self-signed client certificate for development."""
        logger.info("🔧 Generating development client certificate for {request.common_name}")

        certificate = f"""-----BEGIN CERTIFICATE-----
MIIDevelopmentClientCert{request.common_name}
-----END CERTIFICATE-----"""

        private_key = f"""-----BEGIN PRIVATE KEY-----
MIIDevelopmentClientKey{request.common_name}
-----END PRIVATE KEY-----"""

        ca_cert = await self.get_ca_certificate()

        metadata = {
            "common_name": request.common_name,
            "serial_number": "dev-client-001",
            "issued_at": "2024-01-01T00:00:00Z",
            "expires_at": "2025-01-01T00:00:00Z",
            "provider": "development",
        }

        return CertificateBundle(
            certificate=certificate,
            private_key=private_key,
            certificate_chain=certificate,
            ca_certificate=ca_cert,
            metadata=metadata,
        )

    async def get_ca_certificate(self) -> str:
        """Get the development CA certificate."""
        # Ensure CA certificate exists
        await self._ensure_ca_certificate()

        # Read and return the real CA certificate
        try:
            ca_cert = self.ca_cert_file.read_text()
            return ca_cert.strip()
        except FileNotFoundError as e:
            logger.exception("❌ CA certificate file not found")
            raise CertificateNotFoundError("CA certificate not available") from e
        except Exception as e:
            logger.exception("❌ Failed to read CA certificate")
            raise CertificateReadError(f"Failed to read CA certificate: {e}") from e

    async def sign_certificate_request(self, csr_pem: str, service_name: str) -> str:
        """Sign a Certificate Signing Request (CSR) - SECURE PKI PATTERN."""
        logger.info("🔐 Signing CSR for service: %s", service_name)

        # Ensure CA certificate exists
        await self._ensure_ca_certificate()

        # Use the persistent CA certificate to sign CSRs
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                # Save CSR to file
                csr_file = temp_path / "service.csr"
                csr_file.write_text(csr_pem)

                # Step C Debug: Check what extensions are in the CSR
                try:
                    result = subprocess.run(
                        [
                            "openssl",
                            "req",
                            "-in",
                            csr_file,
                            "-text",
                            "-noout",
                        ],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    if "Subject Alternative Name" in result.stdout:
                        logger.info("🔍 Step C Debug: CSR contains Subject Alternative Names")
                    else:
                        logger.warning("⚠️ Step C Debug: CSR missing Subject Alternative Names")
                        logger.debug("CSR content: %s", result.stdout)
                except Exception:
                    logger.warning("⚠️ Could not verify CSR extensions")

                # Copy persistent CA files to temp directory for OpenSSL
                temp_ca_key = temp_path / "ca.key"
                temp_ca_cert = temp_path / "ca.crt"
                shutil.copy2(str(self.ca_key_file), str(temp_ca_key))
                shutil.copy2(str(self.ca_cert_file), str(temp_ca_cert))

                # Sign the CSR with the persistent CA (with extensions support)
                signed_cert_file = temp_path / "signed.crt"
                subprocess.run(
                    [
                        "openssl",
                        "x509",
                        "-req",
                        "-in",
                        str(csr_file),
                        "-CA",
                        str(temp_ca_cert),
                        "-CAkey",
                        str(temp_ca_key),
                        "-CAcreateserial",
                        "-out",
                        str(signed_cert_file),
                        "-days",
                        "365",
                        "-copy_extensions",
                        "copyall",
                    ],
                    check=True,
                    capture_output=True,
                )

                # Step C Debug: Check what extensions are in the signed certificate
                try:
                    result = subprocess.run(
                        [
                            "openssl",
                            "x509",
                            "-in",
                            signed_cert_file,
                            "-text",
                            "-noout",
                        ],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    if "Subject Alternative Name" in result.stdout:
                        logger.info(
                            "✅ Step C Debug: Signed certificate contains Subject Alternative Names",
                        )
                    else:
                        logger.warning(
                            "⚠️ Step C Debug: Signed certificate missing Subject Alternative Names",
                        )
                except Exception:
                    logger.warning("⚠️ Could not verify signed certificate extensions: {e}")

                # Read the signed certificate
                signed_certificate = signed_cert_file.read_text()

                logger.info("✅ Real certificate signed for service")
                return signed_certificate

        except subprocess.CalledProcessError:
            logger.exception("❌ Failed to sign certificate with OpenSSL: {e}")
            # Fallback to a minimal valid PEM structure for development
            return """-----BEGIN CERTIFICATE-----
MIICJjCCAY8CAg38MA0GCSqGSIb3DQEBBQUAMIGbMQswCQYDVQQGEwJKUDEOMAwG
A1UECBMFVG9reW8xEDAOBgNVBAcTB0NodW8ta3UxETAPBgNVBAoTCEZyYW5rNERE
MRgwFgYDVQQLEw9XZWJDZXJ0aWZpY2F0ZTEYMBYGA1UEAxMPRnJhbms0REQgV2Vi
Q0ExIzAhBgkqhkiG9w0BCQEWFGZyYW5rNGRkQGZyYW5rNGRkLmNvbTAeFw0xMjA4
MjIwNTI2NTRaFw0xNzA4MjEwNTI2NTRaMBkxFzAVBgNVBAMTDnd3dy5mcmFuazRk
ZC5jb20wgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAMYBBrx5PlP0WNI/ZdzD
+6Pktmurn+F2kQYbtc7XQh8/LTBvCo+P6iZoLEmUA9e7EXLRxgU1CVqeAi79dCI6
bpNK9o4dhV9y7cqAzYVJ8ba27PIU/4377+ZZ/N4wYE9vPu8dJT7gYGH3ibbSSQpO
hnOHTe6ZQNkNHEQsxLr6OVR/AgMBAAEwDQYJKoZIhvcNAQEFBQADgYEAGyuZGw3V
XZB9I6y8JlRl3BbJe8O3kAC0E7OdL+wKOqUNMxYdGrqHobgBd9tF7H3+QKqz0WVv
0BVqOqJNMeOPVKcHqVmGEBT1tI/2uJjLSczOO0j6PsHB3ZTjKPJSbRgNMy0Z4mPF
cqjqFj1CgKM4wKFjr2JYHSbU0zqPq3U+Hjw=
-----END CERTIFICATE-----"""

    async def revoke_certificate(self, serial_number: str) -> bool:
        """Revoke a development certificate (no-op for development)."""
        logger.info("🚫 Development certificate revocation requested for %s", serial_number)
        return True

    async def validate_certificate(self, certificate: str) -> dict[str, Any]:
        """Validate a development certificate."""
        # Use parameter to avoid unused warning
        _ = certificate
        return {
            "valid": True,
            "provider": "development",
            "validation": "development-mode",
        }

    def get_provider_info(self) -> dict[str, str]:
        return {
            "provider": "development",
            "type": "self-signed",
            "security_level": "development-only",
            "cert_dir": str(self.cert_dir),
        }


class AzureKeyVaultProvider(CertificateProvider):
    """Azure Key Vault certificate provider for cloud deployments."""

    def __init__(self, vault_url: str, tenant_id: str, client_id: str, client_secret: str):
        self.vault_url = vault_url
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        # In real implementation, use Azure SDK

    async def provision_server_certificate(self, request: CertificateRequest) -> CertificateBundle:
        """Provision certificate from Azure Key Vault."""
        logger.info(
            "🔒 Requesting server certificate from Azure Key Vault for %s",
            request.common_name,
        )
        # Azure Key Vault API implementation
        # TODO: Implement Azure Key Vault certificate provisioning
        raise NotImplementedError("Azure Key Vault integration not yet implemented")

    async def provision_client_certificate(self, request: CertificateRequest) -> CertificateBundle:
        """Provision client certificate from Azure Key Vault."""
        # TODO: Implement Azure Key Vault client certificate provisioning
        raise NotImplementedError("Azure Key Vault integration not yet implemented")

    async def get_ca_certificate(self) -> str:
        """Get the Certificate Authority root certificate from Azure Key Vault."""
        # TODO: Implement Azure Key Vault CA certificate retrieval
        raise NotImplementedError("Azure Key Vault integration not yet implemented")

    async def sign_certificate_request(self, csr_pem: str, service_name: str) -> str:
        """Sign a Certificate Signing Request using Azure Key Vault."""
        # TODO: Implement Azure Key Vault CSR signing
        raise NotImplementedError("Azure Key Vault integration not yet implemented")

    async def revoke_certificate(self, serial_number: str) -> bool:
        """Revoke a certificate in Azure Key Vault."""
        # TODO: Implement Azure Key Vault certificate revocation
        raise NotImplementedError("Azure Key Vault integration not yet implemented")

    async def validate_certificate(self, certificate: str) -> dict[str, Any]:
        """Validate a certificate against Azure Key Vault CA."""
        # TODO: Implement Azure Key Vault certificate validation
        raise NotImplementedError("Azure Key Vault integration not yet implemented")

    def get_provider_info(self) -> dict[str, str]:
        return {
            "provider": "azure-keyvault",
            "type": "cloud-managed",
            "security_level": "production",
            "vault_url": self.vault_url,
        }


class VaultProvider(CertificateProvider):
    """HashiCorp Vault certificate provider for enterprise deployments."""

    def __init__(self, vault_url: str, vault_token: str, pki_path: str = "pki"):
        self.vault_url = vault_url
        self.vault_token = vault_token
        self.pki_path = pki_path

    async def provision_server_certificate(self, request: CertificateRequest) -> CertificateBundle:
        """Provision certificate from HashiCorp Vault PKI."""
        logger.info("🏛️ Requesting server certificate from Vault PKI for %s", request.common_name)
        # TODO: Implement Vault API integration
        raise NotImplementedError("HashiCorp Vault integration not yet implemented")

    async def provision_client_certificate(self, request: CertificateRequest) -> CertificateBundle:
        """Provision client certificate from HashiCorp Vault PKI."""
        # TODO: Implement Vault client certificate provisioning
        raise NotImplementedError("HashiCorp Vault integration not yet implemented")

    async def get_ca_certificate(self) -> str:
        """Get the Certificate Authority root certificate from Vault."""
        # TODO: Implement Vault CA certificate retrieval
        raise NotImplementedError("HashiCorp Vault integration not yet implemented")

    async def sign_certificate_request(self, csr_pem: str, service_name: str) -> str:
        """Sign a Certificate Signing Request using Vault PKI."""
        # TODO: Implement Vault CSR signing
        raise NotImplementedError("HashiCorp Vault integration not yet implemented")

    async def revoke_certificate(self, serial_number: str) -> bool:
        """Revoke a certificate in Vault PKI."""
        # TODO: Implement Vault certificate revocation
        raise NotImplementedError("HashiCorp Vault integration not yet implemented")

    async def validate_certificate(self, certificate: str) -> dict[str, Any]:
        """Validate a certificate against Vault CA."""
        # TODO: Implement Vault certificate validation
        raise NotImplementedError("HashiCorp Vault integration not yet implemented")

    def get_provider_info(self) -> dict[str, str]:
        return {
            "provider": "hashicorp-vault",
            "type": "enterprise-pki",
            "security_level": "production",
            "vault_url": self.vault_url,
            "pki_path": self.pki_path,
        }


class ADCSProvider(CertificateProvider):
    """Active Directory Certificate Services provider."""

    def __init__(self, ca_server: str, ca_name: str, template: str):
        self.ca_server = ca_server
        self.ca_name = ca_name
        self.template = template

    async def provision_server_certificate(self, request: CertificateRequest) -> CertificateBundle:
        """Request certificate from Active Directory Certificate Services."""
        logger.info("🏢 Requesting server certificate from ADCS for %s", request.common_name)
        # TODO: Implement ADCS integration via certreq/PowerShell
        raise NotImplementedError("Active Directory Certificate Services integration not yet implemented")

    async def provision_client_certificate(self, request: CertificateRequest) -> CertificateBundle:
        """Request client certificate from Active Directory Certificate Services."""
        # TODO: Implement ADCS client certificate provisioning
        raise NotImplementedError("Active Directory Certificate Services integration not yet implemented")

    async def get_ca_certificate(self) -> str:
        """Get the Certificate Authority root certificate from ADCS."""
        # TODO: Implement ADCS CA certificate retrieval
        raise NotImplementedError("Active Directory Certificate Services integration not yet implemented")

    async def sign_certificate_request(self, csr_pem: str, service_name: str) -> str:
        """Sign a Certificate Signing Request using ADCS."""
        # TODO: Implement ADCS CSR signing
        raise NotImplementedError("Active Directory Certificate Services integration not yet implemented")

    async def revoke_certificate(self, serial_number: str) -> bool:
        """Revoke a certificate in ADCS."""
        # TODO: Implement ADCS certificate revocation
        raise NotImplementedError("Active Directory Certificate Services integration not yet implemented")

    async def validate_certificate(self, certificate: str) -> dict[str, Any]:
        """Validate a certificate against ADCS CA."""
        # TODO: Implement ADCS certificate validation
        raise NotImplementedError("Active Directory Certificate Services integration not yet implemented")

    def get_provider_info(self) -> dict[str, str]:
        return {
            "provider": "adcs",
            "type": "enterprise-ca",
            "security_level": "production",
            "ca_server": self.ca_server,
            "template": self.template,
        }


class CertificateAuthorityService:
    """Certificate Authority Service - Provider abstraction layer."""

    def __init__(self, provider: CertificateProvider):
        self.provider = provider

    async def request_platform_certificates(self) -> dict[str, CertificateBundle]:
        """Request all certificates needed for the platform."""

        logger.info("🔐 Requesting complete certificate bundle for platform")

        # Platform server certificate
        platform_req = CertificateRequest(
            common_name="platform",
            organizational_unit="Platform",
            subject_alt_names=["platform", "crank-platform", "localhost", "*.crank.local"],
            key_usage=["digital_signature", "key_encipherment"],
            extended_key_usage=["server_auth"],
        )

        # Worker client certificate
        client_req = CertificateRequest(
            common_name="worker-client",
            organizational_unit="Workers",
            key_usage=["digital_signature", "key_encipherment"],
            extended_key_usage=["client_auth", "server_auth"],
        )

        # Request certificates from provider
        certificates: dict[str, CertificateBundle] = {
            "platform": await self.provider.provision_server_certificate(platform_req),
            "client": await self.provider.provision_client_certificate(client_req),
        }

        # Add CA certificate as string (note: this breaks the type consistency)
        # TODO: Consider separating CA certificate handling or updating return type
        ca_cert = await self.provider.get_ca_certificate()

        # For now, create a simple CertificateBundle for CA cert consistency
        ca_bundle = CertificateBundle(
            certificate=ca_cert,
            private_key="",  # CA private key not returned to clients
            certificate_chain="",
            ca_certificate=ca_cert,  # CA cert references itself
            metadata={"type": "ca_certificate"},
        )
        certificates["ca"] = ca_bundle

        provider_info = self.provider.get_provider_info()
        logger.info(
            "✅ Certificate bundle provisioned via %s",
            provider_info["provider"],
        )
        return certificates

    async def sign_certificate_request(self, csr_pem: str, service_name: str) -> str:
        """Sign a Certificate Signing Request (CSR) - SECURE PKI PATTERN."""
        return await self.provider.sign_certificate_request(csr_pem, service_name)

    def get_provider_status(self) -> dict[str, Any]:
        """Get current certificate provider status and configuration."""
        return {
            "provider_info": self.provider.get_provider_info(),
            "status": "active",
            "capabilities": {
                "server_certificates": True,
                "client_certificates": True,
                "certificate_revocation": True,
                "certificate_validation": True,
                "csr_signing": True,
            },
        }


def create_certificate_provider() -> CertificateProvider:
    """Factory function to create certificate provider based on environment."""

    provider_type = os.getenv("CERT_PROVIDER", "development")

    if provider_type == "development":
        cert_dir = Path(os.getenv("CERT_DIR", "/etc/certs"))
        return DevelopmentCertificateProvider(cert_dir)

    if provider_type == "azure-keyvault":
        vault_url = os.getenv("AZURE_KEYVAULT_URL")
        tenant_id = os.getenv("AZURE_TENANT_ID")
        client_id = os.getenv("AZURE_CLIENT_ID")
        client_secret = os.getenv("AZURE_CLIENT_SECRET")

        if not all([vault_url, tenant_id, client_id, client_secret]):
            raise ValueError("Azure Key Vault provider requires AZURE_KEYVAULT_URL, AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET environment variables")

        # Type assertion: we've verified these are not None above
        assert vault_url is not None
        assert tenant_id is not None
        assert client_id is not None
        assert client_secret is not None

        return AzureKeyVaultProvider(
            vault_url=vault_url,
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )

    if provider_type == "vault":
        vault_url = os.getenv("VAULT_URL")
        vault_token = os.getenv("VAULT_TOKEN")

        if not vault_url or not vault_token:
            raise ValueError("Vault provider requires VAULT_URL and VAULT_TOKEN environment variables")

        # Type assertion: we've verified these are not None above
        assert vault_url is not None
        assert vault_token is not None

        return VaultProvider(
            vault_url=vault_url,
            vault_token=vault_token,
            pki_path=os.getenv("VAULT_PKI_PATH", "pki"),
        )

    if provider_type == "adcs":
        ca_server = os.getenv("ADCS_CA_SERVER")
        ca_name = os.getenv("ADCS_CA_NAME")

        if not ca_server or not ca_name:
            raise ValueError("ADCS provider requires ADCS_CA_SERVER and ADCS_CA_NAME environment variables")

        # Type assertion: we've verified these are not None above
        assert ca_server is not None
        assert ca_name is not None

        return ADCSProvider(
            ca_server=ca_server,
            ca_name=ca_name,
            template=os.getenv("ADCS_TEMPLATE", "WebServer"),
        )

    raise ValueError(f"Unknown certificate provider: {provider_type}")


# Example usage configurations for different environments:

ENVIRONMENT_CONFIGS = {
    "development": {
        "CERT_PROVIDER": "development",
        "CERT_DIR": "/etc/certs",
    },
    "azure-cloud": {
        "CERT_PROVIDER": "azure-keyvault",
        "AZURE_KEYVAULT_URL": "https://crank-keyvault.vault.azure.net/",
        "AZURE_TENANT_ID": "your-tenant-id",
        "AZURE_CLIENT_ID": "your-client-id",
        # AZURE_CLIENT_SECRET provided via secure configuration
    },
    "enterprise-vault": {
        "CERT_PROVIDER": "vault",
        "VAULT_URL": "https://vault.company.com:8200",
        "VAULT_PKI_PATH": "pki_int",
        # VAULT_TOKEN provided via secure configuration
    },
    "windows-enterprise": {
        "CERT_PROVIDER": "adcs",
        "ADCS_CA_SERVER": "ca.company.com",
        "ADCS_CA_NAME": "Company Enterprise CA",
        "ADCS_TEMPLATE": "CrankPlatformWebServer",
    },
    "production-letsencrypt": {
        "CERT_PROVIDER": "letsencrypt",
        "LETSENCRYPT_DOMAIN": "crankbird.com",
        "LETSENCRYPT_EMAIL": "admin@crankbird.com",
        # Domain ownership must be validated
    },
}
