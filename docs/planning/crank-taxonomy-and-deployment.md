# Crank Platform — Core Taxonomy & Deployment Model

_Last updated: (fill date)_

This document defines the shared terminology and architecture primitives used across the Crank ecosystem.
It ensures consistent language for workers, controller, nodes, jobs, and capabilities, independent of deployment method.

---

## 1. Core Concepts & Naming

| Term | Meaning | Notes |
|---|---|---|
| **Crank-Node** | A host environment capable of running workers and a controller. | A node is _software-defined_, not tied to physical hardware. Laptops, servers, phones, and Raspberry Pi devices can all be nodes. |
| **Crank-Controller** | The supervisory process on each node that manages workers, trust, routing, workload coordination, and participation in the mesh. | One per node. Privileged. Previously named `crank-platform`. |
| **Crank-Worker** | A runtime component that performs work. Provides one or more **capabilities**. | Workers may run in a container, venv, mobile runtime, etc. |
| **Crank-Capability** | A declared function a worker provides, including input/output format. | Example: `convert_document(pdf → text)`, `classify_image`, `sign_csr`. Capabilities are how the system routes work. |
| **Crank-Job** | A request for work, routed to a suitable worker based on capability + context (latency, load, locality). | Jobs are evaluated and scheduled by the controller. |
| **Mesh** | The distributed network of controllers sharing capability + health + load information. | Mesh is controller-to-controller; workers do not speak mesh. |

### Structural Relationship

```text
Crank-Node
   ├── Crank-Controller   (manages routing, governance, trust)
   └── Crank-Workers      (provide capabilities to fulfill jobs)
         └── advertise → Crank-Capabilities
```

---

## 2. Design Principles

1. **Workers are not containers.**
   Workers are _logical service providers_. Containers, venvs, NPUs, pods, mobile apps are just execution strategies.

2. **Capabilities are the source of truth.**
   Capability definitions determine worker interchangeability and routing correctness.

3. **The Controller is the only privileged component on a node.**
   Workers run as restricted processes, often without shell.

4. **The Mesh coordinates state, not execution.**
   Actual work remains local to a node unless intentionally routed across nodes.

---

## 3. Deployment Model (by Platform)

| Platform | Worker Execution Mode | Why | Notes |
|---|---|---|---|
| **Windows 11 + WSL2 + Docker Desktop** | Workers + controller run in **containers** | GPU pass-through + reproducible environment | Baseline development configuration. |
| **macOS** | **Hybrid**: CPU workers in containers; GPU workers run **native venv** | Metal GPU is not container-accessible | Controller sees both uniformly. |
| **Azure / GCP / AWS** | **Containers** for workers + controllers | Scales horizontally | Mesh auto-discovers nodes. |
| **iOS / Android** | Workers run **embedded** inside app sandbox | Enables local-first inference | Exposes capabilities to controller-lite instance. |
| **Raspberry Pi (current)** | Workers run **natively** (CPU only) | Resource-limited edge nodes | Still fully mesh-participating. |
| **Raspberry Pi / IoT (3–5 yrs)** | Workers run on **ARM+NPU** accelerator path | Edge inference becomes cheap & common | Design is already forward-compatible. |

---

## 4. Strategic Insight

This architecture **decouples**:

- Capability descriptions
- Execution environment
- Deployment packaging

This ensures:

- Workers remain replaceable
- Different hardware stays interoperable
- System scales from embedded devices to cloud clusters

---

## 5. Next Architecture Work (Choose One to Proceed)

| Option | Focus | Outcome |
|---|---|---|
| **A. Capability Schema** | Define representation + versioning | Enables routing & worker substitutability |
| **B. Worker Registration + Heartbeat** | Define lifecycle + health reporting | Enables scaling + fault tolerance |
| **C. Job Routing Policy** | Define load / locality / latency strategies | Enables optimized work placement |
| **D. Trust & Certificate Onboarding** | Define secure join of new nodes | Enables secure mesh expansion |

**Reply with A, B, C, or D to continue design.**

---
