# ADR-0014: Standardise Secrets Management Across Environments

**Status**: Proposed
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Security & Governance](../planning/adr-backlog-2025-11-16.md#security--governance)

## Context and Problem Statement

Workers and agents need secrets (API keys, database credentials, encryption keys). Secrets must be stored securely, rotated regularly, and never committed to version control. How should we manage secrets across development, staging, and production environments?

## Decision Drivers

- Security: Secrets never in code or logs
- Rotation: Support key rotation without downtime
- Auditability: Track secret access
- Environment separation: Dev/staging/prod isolation
- Developer experience: Easy local development
- Zero-trust: Secrets only accessible to authorized components

## Considered Options

- **Option 1**: Environment variables + secret management service - Proposed
- **Option 2**: Encrypted files in repository
- **Option 3**: Configuration management system

## Decision Outcome

**Chosen option**: "Environment variables + secret management service", because it provides secure storage, supports rotation, and works across all deployment environments.

### Positive Consequences

- Secrets never in version control
- Support for rotation
- Audit trail of access
- Environment isolation
- Works locally and in production
- Industry standard pattern

### Negative Consequences

- Requires secret management infrastructure
- Initial setup complexity
- Need rotation procedures
- Local development requires setup
- Multiple tools (dotenv local, vault/secrets prod)

## Pros and Cons of the Options

### Option 1: Environment Variables + Secret Management

`.env` files locally, HashiCorp Vault/AWS Secrets Manager in production.

**Pros:**
- Secure storage
- Rotation support
- Audit trail
- Environment separation
- Industry standard
- Works everywhere

**Cons:**
- Infrastructure needed
- Setup complexity
- Multiple tools
- Learning curve

### Option 2: Encrypted Files in Repository

SOPS/git-crypt encrypted files in git.

**Pros:**
- Version controlled
- Easy distribution
- No external service

**Cons:**
- Encryption keys distribution problem
- Hard to rotate
- All or nothing access
- Risky if encryption compromised

### Option 3: Configuration Management System

Ansible Vault, Chef encrypted data bags.

**Pros:**
- Integrated with deployment
- Version controlled
- Encryption built-in

**Cons:**
- Tied to config management tool
- Complex setup
- Hard to use locally
- Not designed for dynamic secrets

## Links

- [Related to] ADR-0002 (mTLS certificates are managed separately)
- [Related to] ADR-0012 (Secrets needed for authorized external API calls)

## Implementation Notes

**Local Development** (`.env` files):

```bash
# .env (gitignored)
DATABASE_URL=postgresql://localhost/crank_dev
API_KEY_OPENAI=sk-...
API_KEY_ANTHROPIC=sk-ant-...
ENCRYPTION_KEY=base64:...

# Load in worker
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("API_KEY_OPENAI")
```

**Production** (AWS Secrets Manager example):

```python
import boto3

def get_secret(secret_name: str) -> str:
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

# Usage
api_key = get_secret("crank/production/openai-api-key")
```

**Docker Compose** (local):

```yaml
services:
  email-classifier:
    image: crank-email-classifier
    env_file:
      - .env
    # Or explicit environment vars
    environment:
      - API_KEY=${API_KEY_SPAM_DATABASE}
```

**Kubernetes** (production):

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: email-classifier
    env:
    - name: API_KEY
      valueFrom:
        secretKeyRef:
          name: spam-api-credentials
          key: api-key
```

**Secret Rotation Strategy**:
1. Generate new secret in secret manager
2. Update workers to accept both old and new
3. Switch traffic to new secret
4. Remove old secret after grace period

**Naming Convention**:
- `{project}/{environment}/{service}/{key-name}`
- Example: `crank/production/email-classifier/spam-api-key`

## Review History

- 2025-11-16 - Initial proposal
