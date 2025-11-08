# Crank Platform Documentation

## Architecture & Development

### Code Quality
- **[Code Quality Strategy](development/code-quality-strategy.md)** - Three-ring type safety architecture for ML applications
- **[Type Safety Implementation](development/code-quality-strategy.md#boundary-shim-pattern)** - Boundary shim patterns for ML library integration

### Security
- **[Docker Security Guide](security/docker-security-guide.md)** - Base image management and container security
- **[mTLS Configuration](security/)** - Certificate management and zero-trust networking

### Operations
- **[Deployment Strategies](operations/)** - Multi-environment deployment patterns
- **[Monitoring & Observability](operations/)** - Logging, metrics, and tracing

## Development Guidelines

### Quick Start
1. Review the [Code Quality Strategy](development/code-quality-strategy.md) for type safety patterns
2. Follow [Docker Security Guide](security/docker-security-guide.md) for container best practices
3. Implement boundary shims for any new ML library integrations

### Key Principles
- **Type Safety First**: Use three-ring architecture for ML complexity
- **Security by Design**: Minimal attack surface with proper isolation
- **Production Ready**: Enterprise-grade patterns throughout

## Documentation Standards

All documentation follows:
- **Practical Examples**: Every pattern includes working code samples
- **Clear Reasoning**: Why decisions were made, not just what was implemented
- **Future Maintenance**: Guidelines for extending and maintaining patterns
- **Measurable Results**: Before/after metrics where applicable

This documentation represents battle-tested patterns that successfully reduced type errors by 97% while maintaining full ML functionality.
