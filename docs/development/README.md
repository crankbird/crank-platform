# Development Documentation

**Last Updated**: 2025-11-10  
**Purpose**: Guides for developing on the Crank Platform

---

## 🚀 Quick Start

**New to the platform?** Start here:

1. **[ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md)** ⭐ — Set up your development environment (all platforms)
2. **[../ARCHITECTURE.md](../ARCHITECTURE.md)** — Understand the system design
3. **[../.vscode/AGENT_CONTEXT.md](../../.vscode/AGENT_CONTEXT.md)** — Critical context for AI coding assistants

## 🧭 Directory Purpose & Boundaries

- **Use this directory for**: local environment setup, coding standards, workflows, and agent instructions that affect developer experience.
- **Do NOT store** production runbooks (→ `docs/operations/`), speculative ideas (→ `docs/proposals/`), or historical reports (→ `docs/reports/`).
- **Naming**: Uppercase files (`ENVIRONMENT_SETUP.md`, `DOCKER_CONFIGS.md`) are canonical references; lowercase files are working memos that should either graduate to uppercase or be archived after they stabilize.
- **Lifecycle**: When a memo becomes an accepted practice, promote it (rename to ALL_CAPS and refresh metadata). If it is tied to a resolved issue, summarize the learning here and move the deep dive to `docs/issues/`.

This keeps development docs actionable for humans and AI agents who need a concise view of how to work on the platform today.

## 📖 Core Development Guides

### Environment Setup

**[ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md)** ⭐ **START HERE**

- Quick start for macOS, Linux, Windows
- GPU setup (CUDA, MPS, CPU fallback)
- Docker configuration
- Troubleshooting

### Platform-Specific Guides

**[mac-mini-development-strategy.md](mac-mini-development-strategy.md)**

- Mac Mini M2/M4 development
- Apple Silicon MPS GPU support
- macOS-specific setup

**[windows-agent-instructions.md](windows-agent-instructions.md)**

- Windows development setup
- WSL2 integration
- Windows-specific considerations

**[WSL2-GPU-CUDA-COMPATIBILITY.md](WSL2-GPU-CUDA-COMPATIBILITY.md)**

- WSL2 CUDA GPU passthrough
- NVIDIA GPU on Windows
- WSL2 Docker integration

### Advanced Environment Topics

**[universal-gpu-environment.md](universal-gpu-environment.md)**

- Cross-platform GPU detection
- PyTorch CUDA/MPS setup
- GPU environment troubleshooting

**[uv-conda-hybrid-strategy.md](uv-conda-hybrid-strategy.md)**

- Hybrid package management
- When to use uv vs conda
- ML-specific dependencies

## 🛠️ Development Practices

### Code Quality

**[code-quality-strategy.md](code-quality-strategy.md)** ⭐ **CRITICAL**

- Three-ring type safety architecture
- Boundary shim patterns for ML libraries
- Type safety for untyped dependencies

**[LINTING_AND_TYPE_CHECKING.md](LINTING_AND_TYPE_CHECKING.md)**

- Ruff linter configuration
- Pylance type checker setup
- Auto-formatting on save

**[pylance-ml-configuration.md](pylance-ml-configuration.md)**

- ML-specific type checking
- Handling untyped ML libraries
- Type stubs and overrides

**[error-suppression-strategy.md](error-suppression-strategy.md)**

- When to suppress errors
- Proper suppression patterns
- Error handling best practices

### Testing

**[testing-strategy.md](testing-strategy.md)**

- Testing architecture
- Unit, integration, E2E tests
- Mascot-driven testing framework

### Docker & Containers

**[DOCKER_CONFIGS.md](DOCKER_CONFIGS.md)**

- Docker Compose configurations
- Service definitions
- Container networking

### Machine Learning

**[ml-development-guide.md](ml-development-guide.md)**

- ML service development
- Model integration patterns
- GPU utilization

## 📁 File Organization

```text
development/
├── ENVIRONMENT_SETUP.md          # ⭐ Start here - unified setup guide
├── code-quality-strategy.md      # ⭐ Critical - type safety architecture
├── testing-strategy.md           # Testing framework
├── DOCKER_CONFIGS.md             # Container configuration
├── LINTING_AND_TYPE_CHECKING.md  # Code quality tools
│
├── mac-mini-development-strategy.md     # macOS/Apple Silicon
├── windows-agent-instructions.md        # Windows development
├── WSL2-GPU-CUDA-COMPATIBILITY.md       # WSL2 GPU setup
│
├── universal-gpu-environment.md  # GPU detection & setup
├── uv-conda-hybrid-strategy.md   # Hybrid package management
├── ml-development-guide.md       # ML development
├── pylance-ml-configuration.md   # ML type checking
└── error-suppression-strategy.md # Error handling
```

## 🔗 Related Documentation

- **Architecture**: [../ARCHITECTURE.md](../ARCHITECTURE.md) — Current system design
- **Security**: [../security/README.md](../security/README.md) — Security architecture
- **Operations**: [../operations/](../operations/) — Deployment and monitoring
- **Planning**: [../planning/ENHANCEMENT_ROADMAP.md](../planning/ENHANCEMENT_ROADMAP.md) — Future roadmap

## 🎭 Development Workflow

1. **Setup environment** → [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md)
2. **Understand architecture** → [../ARCHITECTURE.md](../ARCHITECTURE.md)
3. **Learn mascots** → [../ARCHITECTURAL_MENAGERIE_GUIDE.md](../ARCHITECTURAL_MENAGERIE_GUIDE.md)
4. **Follow code quality** → [code-quality-strategy.md](code-quality-strategy.md)
5. **Write tests** → [testing-strategy.md](testing-strategy.md)
6. **Deploy** → [../operations/DEPLOYMENT_STRATEGY.md](../operations/DEPLOYMENT_STRATEGY.md)

## 💡 Development Tips

- **Use container-first approach**: Develop inside containers when possible
- **Follow three-ring type safety**: See code-quality-strategy.md
- **Run tests frequently**: `pytest` before committing
- **Check security**: Run `.github/workflows/security-scan.yml` locally
- **Ask mascots**: Review changes through Wendy (security), Kevin (portability), Gary (consistency)

---

**Questions?** Check `.vscode/AGENT_CONTEXT.md` for full platform context.
