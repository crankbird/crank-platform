# The Crank Platform: Sustainable AI for the Agent Economy

> *"AI doesn't have to be evil. It doesn't have to be wasteful. It just has to be inevitable."*
>
> **Platform as a Service (PaaS) layer for the Crank ecosystem**

## Meet Our Architectural Menagerie

Our platform is guided by architectural mascots who ensure quality and consistency:

| Mascot | Role | Code References | Mission |
|--------|------|-----------------|---------|
| 🐰 **Wendy** | Zero-Trust Security Bunny | `*security*`, `*mTLS*`, `*auth*`, `*certs*` | Ensures encrypted communication and service isolation |
| 🦙 **Kevin** | Portability Llama | `*runtime*`, `*kevin*`, `container_runtime.py` | Provides container runtime abstraction across Docker/Podman |
| 🐩 **Bella** | Modularity Poodle | `*separation*`, `*modular*`, `*plugin*` | Maintains clean service boundaries and separation readiness |
| 🦅 **Oliver** | Anti-Pattern Eagle | `*pattern*`, `*review*`, code reviews | Prevents architectural anti-patterns and technical debt |
| 🐌 **Gary** | Methodical Snail | `*context*`, `*documentation*`, `*maintainability*` | Preserves context and ensures "back of the cabinet craftsmanship" |

*When you see mascot names in our code, they represent architectural principles in action! Gary's gentle "meow" reminds us to slow down and think methodically.*

---

## Architecture Role

The Crank Platform serves as the **PaaS layer** in a clean three-tier architecture:

- **🏗️ IaaS**: [crank-infrastructure](https://github.com/crankbird/crank-infrastructure) - Environment provisioning, containers, VMs
- **🕸️ PaaS**: **crank-platform** (this repo) - Service mesh, security, governance patterns
- **📱 SaaS**: [crankdoc](https://github.com/crankbird/crankdoc), [parse-email-archive](https://github.com/crankbird/parse-email-archive) - Business logic services

## Quick Start

### Prerequisites

```bash
# Check your environment is ready
./scripts/validate-host-environment.sh

# Quick dependency check for services
make deps-check

# Validate test organization
make test-org
```

### Development

```bash
# Start development environment
./dev-universal.sh

# Quick testing (unified test runner)
uv run python test_runner.py --unit

# Run comprehensive tests
uv run python test_runner.py --integration

# CI/CD pipeline validation
uv run python test_runner.py --ci
```

## Documentation

- **[🏗️ Architecture](docs/ARCHITECTURE.md)** - Platform architecture, JEMM principles, GPU strategy
- **[🚀 Platform Services](docs/PLATFORM_SERVICES.md)** - Service catalog, universal patterns, deployment
- **[🌟 Vision & Strategy](docs/VISION.md)** - Economic model, market strategy, long-term vision
- **[🧪 Testing Strategy](docs/development/testing-strategy.md)** - CI/CD testing approach, unified test runner
- **[Quick Start Guide](QUICK_START.md)** - Get running in 5 minutes
- **[Azure Setup Guide](AZURE_SETUP_GUIDE.md)** - Cloud deployment walkthrough
- **[Universal GPU Dependencies](scripts/QUICK_START.md)** - Automated dependency installation for GPU services
- **[WSL2 GPU Compatibility](docs/WSL2-GPU-CUDA-COMPATIBILITY.md)** - Critical gaming laptop GPU setup for WSL2
- **[Enhancement Roadmap](ENHANCEMENT_ROADMAP.md)** - Platform development plan
- **[Legacy Integration Guide](LEGACY_INTEGRATION.md)** - Industrial & enterprise system integration
- **[Mesh Interface Design](mesh-interface-design.md)** - Universal service architecture

## The Universal Pattern

Every service follows the same architecture:

```python
@crank_service
def process_transaction(input_data, policies, context):
    # Your original Python logic here
    result = do_something(input_data)
    return result

# Automatically gets:
# - FastAPI endpoint with authentication
# - Security isolation in containers
# - Audit logging and receipts
# - Policy enforcement via OPA/Rego
# - Chargeback tracking
# - Multi-deployment options (laptop to cloud)
```

## Core Philosophy

### Vision Statement

The Crank Platform transforms every useful Python script into an enterprise-ready service with built-in security, auditability, and compliance - deployable anywhere from a gaming laptop to a multi-cloud federation. We're building the economic infrastructure for a sustainable AI agent economy.

### The Core Insight

Every time ChatGPT says "I can't do X, but here's some Python code to run in your environment," that represents a **market opportunity**. We wrap that code in enterprise governance and make it available as a service that machines can discover, negotiate for, and pay for automatically.

## Contributing

1. **Read the docs**: Start with [Architecture](docs/ARCHITECTURE.md) to understand the platform
2. **Use unified testing**: Run `uv run python test_runner.py --unit` for development validation
3. **Follow testing strategy**: See [Testing Strategy](docs/development/testing-strategy.md) for comprehensive CI/CD approach
4. **Check implementation**: Review [Testing Implementation](docs/development/testing-implementation-summary.md) for current status
5. **Follow mascot guidance**: Our architectural mascots guide code quality and consistency

## Support

- **Issues**: [GitHub Issues](https://github.com/crankbird/crank-platform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/crankbird/crank-platform/discussions)
- **Documentation**: [docs/](docs/) directory for detailed guides

---

**Next**: Read [Architecture](docs/ARCHITECTURE.md) to understand the platform design, or [Quick Start](QUICK_START.md) to get running immediately.
