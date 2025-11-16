# ADR-0023: Capability Publishing and Discovery Protocol

**Status**: Proposed
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Platform Services / Extensions](../planning/adr-backlog-2025-11-16.md#platform-services--extensions)

## Context and Problem Statement

Workers provide capabilities (e.g., "convert_document_to_pdf", "classify_email"). The controller needs to discover which workers provide which capabilities to route requests. How should workers advertise capabilities and how should the controller discover them?

## Decision Drivers

- Dynamic discovery: Workers can start/stop
- Type safety: Capability schemas validated
- Routing efficiency: Fast capability lookup
- Decentralization: No single point of failure
- Versioning: Capability evolution
- Multi-mesh: Controllers share discovery

## Considered Options

- **Option 1**: Registry-based with heartbeat publishing - Proposed
- **Option 2**: Service mesh with sidecar discovery
- **Option 3**: Static configuration files

## Decision Outcome

**Chosen option**: "Registry-based with heartbeat publishing", because it provides dynamic discovery with type-safe schemas while remaining simple enough for initial implementation and extensible to distributed mesh scenarios.

### Positive Consequences

- Workers advertise capabilities on startup
- Controller maintains capability→worker mapping
- Type-safe capability schemas
- Heartbeat keeps registry fresh
- Stale workers auto-removed
- Foundation for multi-controller mesh

### Negative Consequences

- Controller is central registry (single point)
- Heartbeat overhead
- Schema validation adds latency
- Manual failover if controller dies

## Pros and Cons of the Options

### Option 1: Registry-Based with Heartbeat Publishing

Workers POST capabilities to controller on startup + heartbeat.

**Pros:**
- Simple implementation
- Type-safe schemas
- Dynamic discovery
- Fresh registry via heartbeat
- Controller-local routing

**Cons:**
- Central registry (SPOF)
- Heartbeat network overhead
- Manual failover
- Not fully distributed

### Option 2: Service Mesh with Sidecar Discovery

Dedicated service mesh (Consul, Istio) for discovery.

**Pros:**
- Distributed discovery
- Built-in health checks
- Load balancing
- Multi-datacenter

**Cons:**
- Complex infrastructure
- Sidecar overhead
- Learning curve
- Overkill for single-node

### Option 3: Static Configuration Files

Pre-configured capability→worker mappings.

**Pros:**
- No discovery overhead
- Predictable
- Simple deployment

**Cons:**
- No dynamic workers
- Manual updates
- Doesn't scale
- No failover

## Links

- [Related to] ADR-0001 (Controller/worker model)
- [Related to] ADR-0006 (Verb/capability registry)
- [Depends on] Capability schema (`src/crank/capabilities/`)
- [Related to] Worker runtime (`src/crank/worker_runtime/`)

## Implementation Notes

**Capability Schema** (Already Implemented - Phase 0):

```python
# src/crank/capabilities/capability_schema.py
from pydantic import BaseModel

class CapabilitySchema(BaseModel):
    """Describes a capability provided by a worker."""
    name: str                    # e.g., "convert_document_to_pdf"
    verb: str                    # e.g., "convert"
    input_schema: dict           # JSON Schema for inputs
    output_schema: dict          # JSON Schema for outputs
    version: str                 # Semantic version
    requires_gpu: bool = False
    max_concurrency: int = 10
```

**Worker Registration** (Startup):

```python
# Worker advertises capabilities on startup
from crank.worker_runtime import WorkerApplication
from crank.capabilities import CapabilitySchema

class DocumentWorker(WorkerApplication):
    def __init__(self):
        super().__init__(https_port=8501)

        # Define capabilities
        self.capabilities = [
            CapabilitySchema(
                name="convert_document_to_pdf",
                verb="convert",
                input_schema={
                    "type": "object",
                    "properties": {
                        "source_format": {"type": "string"},
                        "document_bytes": {"type": "string"}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "pdf_bytes": {"type": "string"}
                    }
                },
                version="1.0.0",
                requires_gpu=False
            )
        ]

    async def on_startup(self):
        """Register capabilities with controller."""
        await self.register_capabilities(
            controller_url=self.controller_url,
            capabilities=self.capabilities
        )
```

**Controller Registry** (Proposed):

```python
# Controller maintains capability registry
class CapabilityRegistry:
    def __init__(self):
        self.capabilities: dict[str, list[WorkerEndpoint]] = {}
        self.last_heartbeat: dict[str, datetime] = {}

    def register(
        self,
        worker_id: str,
        worker_url: str,
        capabilities: list[CapabilitySchema]
    ):
        """Register worker capabilities."""
        for cap in capabilities:
            # Validate schema
            cap_validated = CapabilitySchema.model_validate(cap)

            # Add to registry
            key = f"{cap_validated.verb}:{cap_validated.name}"
            if key not in self.capabilities:
                self.capabilities[key] = []

            self.capabilities[key].append(
                WorkerEndpoint(
                    worker_id=worker_id,
                    url=worker_url,
                    capability=cap_validated
                )
            )

        # Track heartbeat
        self.last_heartbeat[worker_id] = datetime.now()

    def route(self, verb: str, capability: str) -> WorkerEndpoint | None:
        """Route request to capable worker."""
        key = f"{verb}:{capability}"
        workers = self.capabilities.get(key, [])

        # Filter healthy workers (heartbeat < 60s ago)
        now = datetime.now()
        healthy = [
            w for w in workers
            if (now - self.last_heartbeat[w.worker_id]).seconds < 60
        ]

        # Load balancing (round-robin for now)
        return healthy[0] if healthy else None

    def heartbeat(self, worker_id: str):
        """Update worker heartbeat."""
        self.last_heartbeat[worker_id] = datetime.now()

    def cleanup_stale(self):
        """Remove workers without recent heartbeat."""
        now = datetime.now()
        stale_threshold = 120  # 2 minutes

        stale_workers = [
            worker_id
            for worker_id, last_beat in self.last_heartbeat.items()
            if (now - last_beat).seconds > stale_threshold
        ]

        for worker_id in stale_workers:
            # Remove from registry
            for cap_list in self.capabilities.values():
                cap_list[:] = [w for w in cap_list if w.worker_id != worker_id]
            del self.last_heartbeat[worker_id]
```

**Heartbeat Protocol**:

```python
# Worker sends heartbeat every 30s
async def heartbeat_loop(self):
    while True:
        await asyncio.sleep(30)
        await self.send_heartbeat()

async def send_heartbeat(self):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{self.controller_url}/heartbeat",
            data={
                "worker_id": self.worker_id,
                "load_score": self.get_load_score()
            },
            cert=(self.cert_path, self.key_path),
            verify=self.ca_path
        )
```

**Controller Routing API** (Proposed):

```http
POST /route
Content-Type: application/json

{
  "verb": "convert",
  "capability": "convert_document_to_pdf",
  "input": {
    "source_format": "docx",
    "document_bytes": "..."
  }
}

Response:
{
  "worker_url": "https://worker-doc-1.local:8501",
  "worker_id": "worker-doc-1"
}
```

**Future: Multi-Controller Mesh**:

```python
# Controllers share capability registries
class MeshRegistry(CapabilityRegistry):
    def __init__(self, peer_controllers: list[str]):
        super().__init__()
        self.peers = peer_controllers

    async def sync_to_peers(self):
        """Broadcast local registry to peer controllers."""
        for peer in self.peers:
            await self.send_registry_update(peer)

    async def query_peers(self, verb: str, capability: str):
        """Ask peer controllers for capability."""
        for peer in self.peers:
            result = await self.query_peer_registry(peer, verb, capability)
            if result:
                return result
        return None
```

## Review History

- 2025-11-16 - Initial proposal (Phase 3+ implementation)
