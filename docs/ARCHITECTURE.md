# Platform Architecture

**Status**: Active
**Type**: Architecture (AS-IS — Current System Design)
**Last Updated**: 2025-11-10
**Owner**: Platform Team
**Purpose**: Document current system architecture, JEMM principles, and energy efficiency strategy

---

## Architecture Philosophy

### The Hybrid Approach: Best of All Worlds

```text
┌─────────────────────────────────────────────────────────────┐
│                     Big Models as Teachers                  │
│              (GPT-4, Claude - Training Phase)               │
└─────────────────────┬───────────────────────────────────────┘
                      │ One-time training cost
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Efficient Inference                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Procedural  │  │ Specialized │  │ Battle-tested       │  │
│  │ Python      │  │ AI Models   │  │ Unix Utilities      │  │
│  │ <1W         │  │ <50W        │  │ <5W                 │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

```

### Energy Efficiency Hierarchy

| Layer | Power Usage | Examples | Use Case |
|-------|-------------|----------|----------|
| **Procedural** | <1W | Email parsing, file operations | Deterministic processing |
| **Unix Utilities** | <5W | Pandoc, ImageMagick, FFmpeg | Proven algorithms |
| **Specialized AI** | <50W | Document classifiers, CNNs | Domain-specific intelligence |
| **Small Transformers** | <200W | Sentence-BERT, distilled models | Language understanding |
| **Large LLMs** | >1000W | GPT-4, Claude | Training teachers only |

### JEMM: Just Enough Microservices and Monoliths

**The JEMM Principle**: *Use the simplest architecture that solves your actual constraints, not your imagined future constraints.*

```text
JEMM Decision Framework:
├─ Team Size < 8 engineers? → Modular Monolith
├─ Deployment conflicts? → Extract ONE service, measure impact
├─ Technology constraints? → Selective extraction only
└─ Performance/scaling needs? → Worker containers (not platform services)

```

**Crank Platform Implementation:**

- **Platform Monolith**: Auth, billing, routing in single container (clean internal boundaries)

- **Worker Containers**: CrankDoc, CrankEmail as separate scalable units

- **Extract-Ready Design**: Interface-based modules that can become services if needed

**JEMM vs. Alternatives:**

- ❌ **Microservices First**: Premature complexity, distributed debugging nightmares

- ❌ **Monolith Forever**: Ignores real team/scaling constraints

- ✅ **JEMM**: Right-sized architecture that evolves with actual needs

*Architecture serves business value, not resume building.*

## AI Strategy: Gaming Laptop Constraints as Design Driver

### The "Just Enough GPU" Philosophy

**Constraint**: 8GB VRAM gaming laptop
**Benefit**: Forces efficient model design
**Result**: Models that scale from laptop to cloud

### Model Distillation Pipeline

```python
class SustainableAI:
    """Use big models to train efficient specialized models."""

    def training_phase(self):
        # Expensive but one-time: Use GPT-4 to create training data

        training_data = self.generate_labels_with_gpt4(raw_data)

        # Train small, specialized model

        efficient_model = self.train_cnn(training_data, target_size="1MB")

        return efficient_model

    def inference_phase(self, efficient_model):
        # Fast, cheap, local inference

        result = efficient_model.predict(input_data)  # <10ms
        return result

```

### Container-First GPU Strategy

**Design Principle**: GPU detection happens at runtime, not build time.

```python
class UniversalGPUManager:
    """Detect and use available GPU resources at runtime."""

    def detect_gpu_capability(self):
        """Runtime detection avoids build-time assumptions."""
        if self._cuda_available():
            return "cuda"
        elif self._mps_available():  # Apple Silicon
            return "mps"
        else:
            return "cpu"

    def optimize_for_device(self, model, device_type):
        """Optimize model for detected hardware."""
        if device_type == "cuda":
            return model.cuda()
        elif device_type == "mps":
            return model.to("mps")
        else:
            return model.cpu()

```

**Benefits**:

- Same container works on laptops, desktops, cloud

- No separate GPU/CPU builds

- Graceful degradation when GPU unavailable

## Service Mesh Architecture

### Universal MeshInterface Pattern

Every service implements the same interface:

```python
@crank_service
class DocumentConverter(MeshInterface):
    """Convert documents between formats."""

    def process_request(self, input_data: Dict) -> Dict:
        # Your business logic here

        return {"converted_document": result}

    # Automatically provides:

    # - FastAPI endpoints with auth

    # - Health checks and metrics

    # - Audit logging

    # - Policy enforcement

    # - Container deployment

```

### Security Architecture

**Zero-Trust Mesh**: Every service-to-service call is authenticated and encrypted.

```text
┌─────────────┐   mTLS   ┌─────────────┐   mTLS   ┌─────────────┐
│   Service   │ ◄─────► │   Gateway   │ ◄─────► │   Service   │
│     A       │         │             │         │     B       │
└─────────────┘         └─────────────┘         └─────────────┘
      │                        │                        │
      ▼                        ▼                        ▼
  [Audit Log]            [Policy Engine]           [Audit Log]

```

**Wendy's Security Framework**:

- mTLS certificates for all inter-service communication

- Bearer token authentication for client requests

- Policy-based access control (OPA/Rego ready)

- Comprehensive audit logging

- Service isolation via containers

### Deployment Flexibility

**From Laptop to Cloud**: Same containers, different orchestration.

```yaml
# Local Development

docker compose up

# Production Cloud

kubectl apply -f k8s/

# Edge Device

docker run -p 8080:8080 crank-platform

```

## Platform Integration

### Three-Tier Clean Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    SaaS Layer                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │  CrankDoc   │ │ EmailParser │ │   Business Logic       │ │
│  │             │ │             │ │   Services             │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    PaaS Layer                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   Gateway   │ │ Mesh        │ │   Security & Audit     │ │
│  │             │ │ Interface   │ │   Platform             │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    IaaS Layer                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   Docker    │ │   VM        │ │   Cloud Resources      │ │
│  │ Containers  │ │ Instances   │ │   & Networking         │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

```

**Clean Separation**:

- **IaaS**: Infrastructure provisioning and container orchestration

- **PaaS**: Service mesh, security, governance, and platform services

- **SaaS**: Business logic and domain-specific functionality

This separation enables independent scaling, testing, and deployment of each layer.
