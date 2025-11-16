"""Capability Registry - tracks worker capabilities and enables routing.

Implementation of ADR-0023: Capability Publishing Protocol.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# --- Extended CapabilitySchema (Phase 3 Future-Proof) ---


class CapabilitySchema(BaseModel):
    """Extended capability metadata with future-proof fields.

    Core fields (Phase 0):
        - name, verb, version: Basic identification
        - input_schema, output_schema: API contracts
        - requires_gpu, max_concurrency: Resource requirements

    Extended fields (Phase 3+, all optional):
        - FaaS metadata: runtime, env_profile, constraints
        - SLO constraints: slo
        - Identity/CAP: spiffe_id, required_capabilities
        - Economic routing: cost_tokens_per_invocation, slo_bid
        - Multi-controller: controller_affinity
    """

    # Core fields (Phase 0)
    name: str
    verb: str
    version: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    requires_gpu: bool = False
    max_concurrency: int = 10

    # FaaS metadata (faas-worker-specification.md)
    runtime: Optional[str] = None  # "python3.11", "node20", "dotnet8"
    env_profile: Optional[str] = None  # "cpu-optimized", "gpu-required", "memory-intensive"
    constraints: Optional[dict[str, Any]] = None  # {"min_memory_mb": 2048, "gpu_count": 1}

    # SLO constraints (enhancement-roadmap.md: SLO Files)
    slo: Optional[dict[str, Any]] = None  # {"latency_p95_ms": 100, "availability_pct": 99.9}

    # Identity + CAP (crank-mesh-access-model-evolution.md: SPIFFE)
    spiffe_id: Optional[str] = None  # "spiffe://crank.local/worker/streaming"
    required_capabilities: Optional[list[str]] = None  # Capabilities this worker calls

    # Economic routing (from-job-scheduling-to-capability-markets.md)
    cost_tokens_per_invocation: Optional[float] = None
    slo_bid: Optional[float] = None

    # Multi-controller (enhancement-roadmap.md: multi-node quorum)
    controller_affinity: Optional[list[str]] = None  # Preferred controller IDs


# --- Worker Endpoint ---


@dataclass
class WorkerEndpoint:
    """Registered worker with capabilities and health tracking."""

    worker_id: str
    worker_url: str
    capabilities: list[CapabilitySchema]
    last_heartbeat: datetime = field(default_factory=datetime.now)
    registered_at: datetime = field(default_factory=datetime.now)

    def is_healthy(self, timeout_seconds: int = 120) -> bool:
        """Check if worker is healthy (received heartbeat recently)."""
        age = datetime.now() - self.last_heartbeat
        return age.total_seconds() < timeout_seconds

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSONL storage."""
        return {
            "worker_id": self.worker_id,
            "worker_url": self.worker_url,
            "capabilities": [c.model_dump() for c in self.capabilities],
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "registered_at": self.registered_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkerEndpoint":
        """Deserialize from JSONL storage."""
        return cls(
            worker_id=data["worker_id"],
            worker_url=data["worker_url"],
            capabilities=[
                CapabilitySchema(**cap) for cap in data["capabilities"]
            ],
            last_heartbeat=datetime.fromisoformat(data["last_heartbeat"]),
            registered_at=datetime.fromisoformat(data["registered_at"]),
        )


# --- Capability Registry ---


class CapabilityRegistry:
    """Tracks worker capabilities and enables routing.

    Core responsibilities:
    - Register workers with their capabilities
    - Track worker heartbeats (staleness detection)
    - Route capability requests to workers
    - Persist state to disk (JSONL format per ADR-0005)
    - Support multi-controller sync (export/import state)
    """

    def __init__(
        self,
        state_file: Optional[Path] = None,
        heartbeat_timeout: int = 120,
    ):
        """Initialize registry.

        Args:
            state_file: Path to JSONL persistence file (default: state/controller/registry.jsonl)
            heartbeat_timeout: Worker staleness timeout in seconds (default: 120)
        """
        self.state_file = (
            state_file
            if state_file
            else Path("state/controller/registry.jsonl")
        )
        self.heartbeat_timeout = heartbeat_timeout
        self._workers: dict[str, WorkerEndpoint] = {}
        self._capability_index: dict[str, list[str]] = {}  # capability -> [worker_ids]

        # Load persisted state on startup
        self._load_state()

    # --- Registration ---

    def register(
        self,
        worker_id: str,
        worker_url: str,
        capabilities: list[CapabilitySchema],
    ) -> None:
        """Register worker with capabilities.

        Args:
            worker_id: Unique worker identifier
            worker_url: Worker HTTPS endpoint
            capabilities: List of capabilities worker provides
        """
        worker = WorkerEndpoint(
            worker_id=worker_id,
            worker_url=worker_url,
            capabilities=capabilities,
        )

        self._workers[worker_id] = worker
        self._rebuild_capability_index()
        self._save_state()

        logger.info(
            "Worker registered: %s with capabilities: %s",
            worker_id,
            [f"{c.verb}:{c.name}" for c in capabilities],
        )

    # --- Heartbeat ---

    def heartbeat(self, worker_id: str) -> bool:
        """Update worker heartbeat timestamp.

        Args:
            worker_id: Worker identifier

        Returns:
            True if worker is registered, False otherwise
        """
        if worker_id not in self._workers:
            logger.warning("Heartbeat from unknown worker: %s", worker_id)
            return False

        self._workers[worker_id].last_heartbeat = datetime.now()
        self._save_state()

        logger.debug("Worker heartbeat: %s", worker_id)
        return True

    # --- Deregistration ---

    def deregister(self, worker_id: str) -> None:
        """Deregister worker (graceful shutdown)."""
        if worker_id in self._workers:
            del self._workers[worker_id]
            self._rebuild_capability_index()
            self._save_state()
            logger.info("Worker deregistered: %s", worker_id)

    # --- Routing ---

    def route(
        self,
        verb: str,
        capability: str,
        slo_constraints: Optional[dict[str, Any]] = None,
        requester_identity: Optional[str] = None,
        budget_tokens: Optional[float] = None,
    ) -> Optional[WorkerEndpoint]:
        """Find worker for capability.

        Args:
            verb: Capability verb (e.g., "convert", "classify")
            capability: Capability name (e.g., "document_to_pdf")
            slo_constraints: SLO requirements (future: SLO-aware routing)
            requester_identity: SPIFFE ID (future: CAP policy)
            budget_tokens: Budget (future: economic routing)

        Returns:
            WorkerEndpoint if found, None otherwise
        """
        capability_key = f"{verb}:{capability}"
        worker_ids = self._capability_index.get(capability_key, [])

        # Filter healthy workers
        healthy = [
            self._workers[wid]
            for wid in worker_ids
            if wid in self._workers and self._workers[wid].is_healthy(self.heartbeat_timeout)
        ]

        # FUTURE HOOK: SLO filtering
        # if slo_constraints:
        #     healthy = [w for w in healthy if w.meets_slo(slo_constraints)]

        # FUTURE HOOK: Economic routing
        # if budget_tokens:
        #     healthy = [w for w in healthy if w.cost_tokens <= budget_tokens]
        #     healthy.sort(key=lambda w: w.cost_tokens)

        if not healthy:
            logger.warning(
                "No worker available for capability: %s (total registered: %d)",
                capability_key,
                len(worker_ids),
            )
            return None

        # Simple routing: return first healthy worker
        return healthy[0]

    def get_workers_for_capability(
        self, capability: str
    ) -> list[WorkerEndpoint]:
        """Get all workers providing a capability.

        Args:
            capability: Full capability key (verb:name)

        Returns:
            List of worker endpoints
        """
        worker_ids = self._capability_index.get(capability, [])
        return [self._workers[wid] for wid in worker_ids if wid in self._workers]

    # --- Cleanup ---

    def cleanup_stale(self) -> int:
        """Remove stale workers (no heartbeat within timeout).

        Returns:
            Number of workers removed
        """
        stale = [
            wid
            for wid, worker in self._workers.items()
            if not worker.is_healthy(self.heartbeat_timeout)
        ]

        for wid in stale:
            logger.warning("Worker stale, removing: %s", wid)
            del self._workers[wid]

        if stale:
            self._rebuild_capability_index()
            self._save_state()

        return len(stale)

    # --- Introspection ---

    def get_all_capabilities(self) -> dict[str, dict[str, int]]:
        """Get all registered capabilities with worker counts."""
        return {
            cap: {
                "workers": len(worker_ids),
                "healthy_workers": sum(
                    1
                    for wid in worker_ids
                    if wid in self._workers and self._workers[wid].is_healthy(self.heartbeat_timeout)
                ),
            }
            for cap, worker_ids in self._capability_index.items()
        }

    def get_all_workers(self) -> list[dict[str, Any]]:
        """Get all registered workers with health status."""
        return [
            {
                "worker_id": worker.worker_id,
                "worker_url": worker.worker_url,
                "is_healthy": worker.is_healthy(self.heartbeat_timeout),
                "last_heartbeat": worker.last_heartbeat.isoformat(),
                "capabilities": [
                    f"{c.verb}:{c.name}" for c in worker.capabilities
                ],
            }
            for worker in self._workers.values()
        ]

    # --- Persistence (ADR-0005: File-Backed State) ---

    def _save_state(self) -> None:
        """Persist registry to JSONL file."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.state_file, "w") as f:
            for worker in self._workers.values():
                f.write(json.dumps(worker.to_dict()) + "\n")

        logger.debug("Registry state saved: %d workers", len(self._workers))

    def _load_state(self) -> None:
        """Load registry from JSONL file (warm cache on startup)."""
        if not self.state_file.exists():
            logger.info("Registry state file not found, creating new registry")
            return

        try:
            with open(self.state_file) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        worker = WorkerEndpoint.from_dict(data)
                        self._workers[worker.worker_id] = worker

            self._rebuild_capability_index()
            logger.info(
                "Registry state loaded: %d workers (will reregister on next heartbeat)",
                len(self._workers),
            )
        except Exception as e:
            logger.error("Registry state load failed: %s", str(e))

    # --- Multi-Controller Support (Future) ---

    def export_state(self) -> dict[str, Any]:
        """Export registry state for controller-to-controller sync.

        Returns:
            Serializable state dictionary
        """
        return {
            "workers": [w.to_dict() for w in self._workers.values()],
            "exported_at": datetime.now().isoformat(),
        }

    def import_remote_state(self, controller_id: str, state: dict[str, Any]) -> None:
        """Import state from remote controller (merge, not replace).

        Args:
            controller_id: Source controller identifier
            state: State dictionary from export_state()
        """
        # FUTURE: Implement conflict resolution, quorum logic
        logger.info(
            "Import remote state stub called from controller: %s with %d workers",
            controller_id,
            len(state.get("workers", [])),
        )

    # --- Internal Helpers ---

    def _rebuild_capability_index(self) -> None:
        """Rebuild capability -> workers index."""
        self._capability_index.clear()

        for worker_id, worker in self._workers.items():
            for cap in worker.capabilities:
                cap_key = f"{cap.verb}:{cap.name}"
                if cap_key not in self._capability_index:
                    self._capability_index[cap_key] = []
                self._capability_index[cap_key].append(worker_id)
