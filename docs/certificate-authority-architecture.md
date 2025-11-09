# Certificate Authority Service Architecture

## Overview

The Certificate Authority Service provides centralized, enterprise-grade certificate management for the Crank Platform. This architecture solves several critical security issues:

1. **Security Consistency**: All services run as non-root users (worker:1000)

2. **Enterprise Integration**: Pluggable certificate providers support multiple backends

3. **Zero-Trust Security**: Complete HTTPS-only operation with mTLS

4. **Operational Simplicity**: Centralized certificate lifecycle management

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Certificate Authority Service                  │
│                     (cert-authority:9090)                       │
├─────────────────────────────────────────────────────────────────┤
│  🔐 Pluggable Certificate Providers:                           │
│    • Development (self-signed)                                  │
│    • Azure Key Vault (cloud-managed)                           │
│    • HashiCorp Vault (enterprise PKI)                          │
│    • Active Directory Certificate Services (ADCS)              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTPS API
                                ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    Crank Platform                          │
    │               (platform:8443)                              │
    │               User: worker:1000                             │
    └─────────────────────────────────────────────────────────────┘
                                │
                                │ mTLS
                                ▼
    ┌───────────────┬───────────────┬───────────────┬─────────────┐
    │  CrankDoc     │  Email        │  Email        │ Streaming   │
    │  Converter    │  Classifier   │  Parser       │ Worker      │
    │  :8101        │  :8201        │  :8301        │ :8501       │
    │  worker:1000  │  worker:1000  │  worker:1000  │ worker:1000 │
    └───────────────┴───────────────┴───────────────┴─────────────┘

```

## Security Model

### Development Environment

- **Mode**: `development-https`

- **Certificate Provider**: Self-signed certificates

- **Certificate Permissions**: World-readable (0644) for Docker compatibility

- **Validation**: Relaxed certificate verification

- **Purpose**: Local development with HTTPS enforcement

### Production Environment

- **Mode**: `production`

- **Certificate Provider**: Enterprise (Vault/ADCS/Azure)

- **Certificate Permissions**: Restricted (0600) private keys

- **Validation**: Strict certificate chain validation

- **Purpose**: Production deployment with enterprise PKI

## Certificate Providers

### Development Provider

```python
# Self-signed certificates for development

CERT_PROVIDER=development

```

- Generates self-signed certificates

- CA hierarchy: Root CA → Server/Client certificates

- Suitable for development and testing

### Azure Key Vault Provider

```python
# Azure-managed certificates

CERT_PROVIDER=azure-keyvault
AZURE_KEYVAULT_URL=https://your-keyvault.vault.azure.net/
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id

```

- Cloud-managed PKI infrastructure

- Automatic certificate rotation

- Azure AD integration

### HashiCorp Vault Provider

```python
# Enterprise PKI with Vault

CERT_PROVIDER=vault
VAULT_URL=https://vault.company.com:8200
VAULT_TOKEN=your-vault-token
VAULT_PKI_PATH=pki/issue/crank-platform

```

- Enterprise-grade PKI

- Policy-driven certificate issuance

- Integration with corporate identity systems

### Active Directory Certificate Services

```python
# Windows enterprise PKI

CERT_PROVIDER=adcs
ADCS_CA_SERVER=ca.company.com
ADCS_TEMPLATE=WebServerTemplate
ADCS_USERNAME=cert-user
ADCS_PASSWORD=cert-password

```

- Windows Active Directory integration

- Group Policy certificate deployment

- Enterprise certificate templates

## API Endpoints

### Certificate Authority Service (port 9090)

#### Health Check

```bash
GET /health

```

#### Get CA Certificate

```bash
GET /ca/certificate

```

#### Provision Platform Certificates

```bash
POST /certificates/platform

```

Returns complete certificate bundle for platform service.

#### Provision Server Certificate

```bash
POST /certificates/server
Content-Type: application/json

{
  "common_name": "worker.crank.local",
  "subject_alt_names": ["worker", "localhost"],
  "key_usage": ["digital_signature", "key_encipherment"],
  "extended_key_usage": ["server_auth"]
}

```

#### Provision Client Certificate

```bash
POST /certificates/client
Content-Type: application/json

{
  "common_name": "platform-client",
  "extended_key_usage": ["client_auth"]
}

```

#### Revoke Certificate

```bash
DELETE /certificates/{serial_number}

```

## Deployment

### Development Deployment

```bash
# Use development certificate provider

docker-compose -f docker-compose.enterprise.yml up

# Services start with

# 1. Certificate Authority Service initializes

# 2. Platform requests certificates from CA service

# 3. Workers request certificates and start

```

### Production Deployment

```bash
# Configure enterprise certificate provider

export CRANK_ENVIRONMENT=production
export CERT_PROVIDER=vault
export VAULT_URL=https://vault.company.com:8200
export VAULT_TOKEN=your-production-token

# Deploy with production security

docker-compose -f docker-compose.production.yml up

```

## Service Integration

All platform services follow this pattern:

1. **Container Startup**: Run as non-root user (worker:1000)

2. **Certificate Initialization**: Request certificates from CA service

3. **Application Startup**: Start with HTTPS-only configuration

### Certificate Directory Structure

```
/etc/certs/
├── ca.crt              # Certificate Authority root certificate
├── platform.crt       # Platform server certificate
├── platform.key       # Platform private key
├── client.crt          # Platform client certificate
├── client.key          # Platform client private key
└── metadata.json       # Certificate metadata and provider info

```

## Migration from Legacy Architecture

### Before (Legacy)

- Platform container runs as root

- Direct certificate generation in containers

- HTTP fallbacks enabled

- No centralized certificate management

### After (Certificate Authority Service)

- All containers run as non-root users

- Centralized certificate provisioning

- HTTPS-only operation

- Enterprise certificate provider integration

## Security Benefits

1. **Principle of Least Privilege**: No containers require root access

2. **Certificate Lifecycle Management**: Centralized renewal and revocation

3. **Enterprise Integration**: Seamless integration with corporate PKI

4. **Zero-Trust Architecture**: mTLS for all inter-service communication

5. **Audit Trail**: Complete certificate provisioning audit log

## Troubleshooting

### Certificate Authority Service Not Starting

```bash
# Check service health

curl -f http://cert-authority:9090/health

# Check certificate provider status

curl -f http://cert-authority:9090/provider/status

```

### Certificate Initialization Failures

```bash
# Check platform logs

docker logs crank-platform

# Verify CA service availability

docker exec crank-platform curl -f http://cert-authority:9090/health

```

### Enterprise Provider Issues

```bash
# Check provider configuration

curl -f http://cert-authority:9090/provider/config

# Validate provider credentials

docker exec cert-authority python -c "
from certificate_authority_service import create_certificate_provider
provider = create_certificate_provider()
print(provider.get_provider_info())
"

```

## Future Enhancements

1. **Certificate Rotation**: Automatic certificate renewal before expiration

2. **Certificate Templates**: Predefined certificate profiles for different service types

3. **Certificate Monitoring**: Prometheus metrics for certificate expiration monitoring

4. **ACME Protocol**: Let's Encrypt integration for internet-facing deployments

5. **Certificate Backup**: Automated certificate backup and recovery procedures
