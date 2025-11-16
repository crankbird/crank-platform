"""
Sonnet Zettel Manager Worker

A service for managing zettel notes created by chat agents, with extensible
architecture for future AI-powered categorization, title generation, and
semantic search capabilities.

Features:
- Store zettels with metadata and content
- Retrieve zettels by ID or search criteria
- List zettels with filtering options
- Extensible design for future AI enhancements

Extension Points (for future implementation):
- Auto-generate zettel titles using language models
- Categorize zettels and organize into directories
- Similarity-based categorization using existing zettel corpus
- Semantic search and retrieval
- Publish filtered zettel lists with various criteria
"""

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from crank.capabilities.schema import CapabilityDefinition, CapabilityVersion, IOContract
from crank.worker_runtime.base import WorkerApplication

logger = logging.getLogger(__name__)


# Phase A: Schema Definition (Type-Safe Foundation)
# ================================================

class ZettelMetadata(BaseModel):
    """Metadata for a zettel note."""

    id: str = Field(description="Unique identifier for the zettel")
    title: str | None = Field(default=None, description="Optional title for the zettel")
    created_at: datetime = Field(description="When the zettel was created")
    updated_at: datetime = Field(description="When the zettel was last updated")
    source_agent: str | None = Field(default=None, description="Agent that created this zettel (e.g., 'chatgpt', 'claude')")
    category: str | None = Field(default=None, description="Category classification")
    tags: list[str] = Field(default_factory=list, description="Associated tags")

    # Extension points for future AI features
    auto_generated_title: bool = Field(default=False, description="Whether title was AI-generated")
    similarity_cluster: str | None = Field(default=None, description="Cluster ID for similar zettels")
    semantic_embeddings: list[float] = Field(default_factory=list, description="Vector embeddings for semantic search")


class ZettelContent(BaseModel):
    """Complete zettel with metadata and content."""

    metadata: ZettelMetadata = Field(description="Zettel metadata")
    content: str = Field(description="The actual zettel content in markdown format")
    word_count: int = Field(description="Number of words in the content")


class StoreZettelRequest(BaseModel):
    """Request to store a new zettel."""

    content: str = Field(description="Zettel content in markdown format")
    title: str | None = Field(default=None, description="Optional title (can be auto-generated later)")
    source_agent: str | None = Field(default=None, description="Agent that created this zettel")
    category: str | None = Field(default=None, description="Optional category classification")
    tags: list[str] = Field(default_factory=list, description="Optional tags")


class RetrieveZettelRequest(BaseModel):
    """Request to retrieve a specific zettel."""

    zettel_id: str = Field(description="Unique identifier of the zettel to retrieve")


class ListZettelsRequest(BaseModel):
    """Request to list zettels with optional filtering."""

    category: str | None = Field(default=None, description="Filter by category")
    source_agent: str | None = Field(default=None, description="Filter by source agent")
    tags: list[str] = Field(default_factory=list, description="Filter by tags (AND operation)")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum number of zettels to return")
    offset: int = Field(default=0, ge=0, description="Number of zettels to skip")


class ZettelOperationResponse(BaseModel):
    """Response from zettel operations."""

    success: bool = Field(description="Whether the operation succeeded")
    zettel_id: str | None = Field(default=None, description="ID of the affected zettel")
    message: str = Field(description="Operation result message")
    data: ZettelContent | list[ZettelContent] | None = Field(default=None, description="Operation result data")


# Capability definition for the zettel management service
SONNET_ZETTEL_MANAGEMENT = CapabilityDefinition(
    id="knowledge.sonnet_zettel_management",
    version=CapabilityVersion(major=1, minor=0, patch=0),
    name="Sonnet Zettel Management",
    description="Store, retrieve, and manage zettel notes with extensible AI enhancement capabilities",
    contract=IOContract(
        input_schema={
            "type": "object",
            "oneOf": [
                {
                    "properties": {
                        "operation": {"type": "string", "enum": ["store"]},
                        "content": {"type": "string"},
                        "title": {"type": "string"},
                        "source_agent": {"type": "string"},
                        "category": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["operation", "content"]
                },
                {
                    "properties": {
                        "operation": {"type": "string", "enum": ["retrieve"]},
                        "zettel_id": {"type": "string"}
                    },
                    "required": ["operation", "zettel_id"]
                },
                {
                    "properties": {
                        "operation": {"type": "string", "enum": ["list"]},
                        "category": {"type": "string"},
                        "source_agent": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "limit": {"type": "integer"},
                        "offset": {"type": "integer"}
                    },
                    "required": ["operation"]
                }
            ]
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "zettel_id": {"type": "string"},
                "message": {"type": "string"},
                "data": {"type": "object"}
            },
            "required": ["success", "message"]
        }
    ),
    tags=["knowledge", "zettel", "notes", "storage", "ai-extensible"],
    estimated_duration_ms=100
)


# Phase B: Business Logic (Isolated Testing)
# ===========================================

class SonnetZettelEngine:
    """Core zettel management logic - no FastAPI dependencies."""

    def __init__(self, storage_path: Path | None = None) -> None:
        """
        Initialize the zettel management engine.

        Args:
            storage_path: Directory for storing zettels (defaults to docs/knowledge/zettels)
        """
        self.storage_path = storage_path or Path("docs/knowledge/zettels")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Simple in-memory index for fast retrieval (would be replaced by proper DB)
        self._zettel_index: dict[str, ZettelContent] = {}
        self._load_existing_zettels()

        logger.info("Sonnet Zettel Engine initialized with storage at %s", self.storage_path)

    def store_zettel(self, request: StoreZettelRequest) -> ZettelOperationResponse:
        """
        Store a new zettel with generated metadata.

        Args:
            request: Zettel storage request

        Returns:
            Operation response with zettel ID

        Raises:
            ValueError: If content is empty or invalid
        """
        if not request.content.strip():
            raise ValueError("Zettel content cannot be empty")

        # Generate unique ID and metadata
        zettel_id = self._generate_zettel_id()
        now = datetime.now()
        word_count = len(request.content.split())

        metadata = ZettelMetadata(
            id=zettel_id,
            title=request.title,
            created_at=now,
            updated_at=now,
            source_agent=request.source_agent,
            category=request.category,
            tags=request.tags.copy()
        )

        zettel = ZettelContent(
            metadata=metadata,
            content=request.content,
            word_count=word_count
        )

        # Store to filesystem and index
        self._persist_zettel(zettel)
        self._zettel_index[zettel_id] = zettel

        return ZettelOperationResponse(
            success=True,
            zettel_id=zettel_id,
            message=f"Zettel stored successfully with {word_count} words",
            data=zettel
        )

    def retrieve_zettel(self, request: RetrieveZettelRequest) -> ZettelOperationResponse:
        """
        Retrieve a specific zettel by ID.

        Args:
            request: Zettel retrieval request

        Returns:
            Operation response with zettel data

        Raises:
            ValueError: If zettel ID not found
        """
        zettel = self._zettel_index.get(request.zettel_id)
        if not zettel:
            raise ValueError(f"Zettel not found: {request.zettel_id}")

        return ZettelOperationResponse(
            success=True,
            zettel_id=request.zettel_id,
            message="Zettel retrieved successfully",
            data=zettel
        )

    def list_zettels(self, request: ListZettelsRequest) -> ZettelOperationResponse:
        """
        List zettels with optional filtering.

        Args:
            request: List request with filtering options

        Returns:
            Operation response with list of matching zettels
        """
        # Apply filters
        filtered_zettels = []
        for zettel in self._zettel_index.values():
            if self._matches_filters(zettel, request):
                filtered_zettels.append(zettel)

        # Sort by creation date (newest first)
        filtered_zettels.sort(key=lambda z: z.metadata.created_at, reverse=True)

        # Apply pagination
        start_idx = request.offset
        end_idx = start_idx + request.limit
        paginated_zettels = filtered_zettels[start_idx:end_idx]

        return ZettelOperationResponse(
            success=True,
            zettel_id=None,
            message=f"Found {len(filtered_zettels)} zettels, returning {len(paginated_zettels)}",
            data=paginated_zettels
        )

    def _generate_zettel_id(self) -> str:
        """Generate a unique zettel identifier."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        unique_suffix = str(uuid.uuid4())[:8]
        return f"sonnet-{timestamp}-{unique_suffix}"

    def _persist_zettel(self, zettel: ZettelContent) -> None:
        """Save zettel to filesystem."""
        # Extension point: Could save to different directories based on category
        filename = f"{zettel.metadata.id}.md"
        filepath = self.storage_path / filename

        # Create markdown file with metadata frontmatter
        content_lines = [
            "---",
            f"id: {zettel.metadata.id}",
            f"title: {zettel.metadata.title or 'Untitled'}",
            f"created_at: {zettel.metadata.created_at.isoformat()}",
            f"updated_at: {zettel.metadata.updated_at.isoformat()}",
        ]

        if zettel.metadata.source_agent:
            content_lines.append(f"source_agent: {zettel.metadata.source_agent}")
        if zettel.metadata.category:
            content_lines.append(f"category: {zettel.metadata.category}")
        if zettel.metadata.tags:
            content_lines.append(f"tags: [{', '.join(zettel.metadata.tags)}]")

        content_lines.extend([
            f"word_count: {zettel.word_count}",
            "---",
            "",
            zettel.content
        ])

        filepath.write_text("\n".join(content_lines), encoding="utf-8")

    def _load_existing_zettels(self) -> None:
        """Load existing zettels from storage into index."""
        # Extension point: Would implement proper markdown parsing
        # For now, just initialize empty index
        logger.info("Zettel index initialized (existing zettel loading not yet implemented)")

    def _matches_filters(self, zettel: ZettelContent, request: ListZettelsRequest) -> bool:
        """Check if zettel matches the given filters."""
        # Category filter
        if request.category and zettel.metadata.category != request.category:
            return False

        # Source agent filter
        if request.source_agent and zettel.metadata.source_agent != request.source_agent:
            return False

        # Tags filter (AND operation - zettel must have all requested tags)
        if request.tags and not all(tag in zettel.metadata.tags for tag in request.tags):
            return False

        return True


# Phase C: Worker Runtime Integration
# ===================================

class SonnetZettelManagerWorker(WorkerApplication):
    """Worker providing zettel management capabilities."""

    def __init__(self) -> None:
        """Initialize zettel manager worker."""
        super().__init__(
            service_name="sonnet-zettel-manager",
            https_port=int(os.getenv("SONNET_ZETTEL_MANAGER_HTTPS_PORT", "8700")),
        )
        self.engine = SonnetZettelEngine()

        # Controller registration
        self.controller_url = os.getenv("CONTROLLER_URL")
        self.registered_with_controller = False

        logger.info("Sonnet Zettel Manager worker initialized with ID: %s", self.worker_id)
        if self.controller_url:
            logger.info("Controller URL configured: %s", self.controller_url)
        else:
            logger.info("No controller URL - running standalone")

    async def on_startup(self) -> None:
        """Register with controller on startup (if configured)."""
        await super().on_startup()

        if self.controller_url:
            await self._register_with_controller()

    async def _register_with_controller(self) -> None:
        """Send registration request to controller."""
        try:
            capabilities = [
                {
                    "name": cap.id,
                    "verb": "manage",
                    "version": f"{cap.version.major}.{cap.version.minor}.{cap.version.patch}",
                    "input_schema": cap.contract.input_schema,
                    "output_schema": cap.contract.output_schema,
                }
                for cap in self.get_capabilities()
            ]

            registration_payload = {
                "worker_id": self.worker_id,
                "worker_url": self.worker_url,
                "capabilities": capabilities,
            }

            logger.info("Registering with controller at %s", self.controller_url)
            ssl_config = self.cert_manager.get_ssl_context()

            async with httpx.AsyncClient(
                cert=(ssl_config["ssl_certfile"], ssl_config["ssl_keyfile"]),
                verify=ssl_config["ssl_ca_certs"],
            ) as client:
                response = await client.post(
                    f"{self.controller_url}/register",
                    json=registration_payload,
                    timeout=10.0,
                )
                response.raise_for_status()
                result = response.json()
                self.registered_with_controller = True
                logger.info(
                    "✅ Registered with controller: %s capabilities",
                    result.get("capabilities_registered", 0)
                )
        except Exception as e:
            logger.error(
                "❌ Failed to register with controller: %s (continuing anyway)",
                str(e)
            )

    def get_capabilities(self) -> list[CapabilityDefinition]:
        """Return capabilities this worker provides."""
        return [SONNET_ZETTEL_MANAGEMENT]

    def setup_routes(self) -> None:
        """Register FastAPI routes for zettel management."""

        # Store zettel endpoint
        async def store_zettel_endpoint(request: StoreZettelRequest) -> JSONResponse:  # pyright: ignore[reportUnusedFunction]
            """Store a new zettel note."""
            try:
                result = self.engine.store_zettel(request)
                return JSONResponse(content=result.model_dump())

            except ValueError as e:
                logger.warning("Invalid zettel storage request: %s", e)
                raise HTTPException(status_code=400, detail=str(e)) from e
            except Exception as e:
                logger.exception("Zettel storage failed")
                raise HTTPException(status_code=500, detail="STORAGE_FAILED") from e

        # Retrieve zettel endpoint
        async def retrieve_zettel_endpoint(request: RetrieveZettelRequest) -> JSONResponse:  # pyright: ignore[reportUnusedFunction]
            """Retrieve a specific zettel by ID."""
            try:
                result = self.engine.retrieve_zettel(request)
                return JSONResponse(content=result.model_dump())

            except ValueError as e:
                logger.warning("Zettel not found: %s", e)
                raise HTTPException(status_code=404, detail=str(e)) from e
            except Exception as e:
                logger.exception("Zettel retrieval failed")
                raise HTTPException(status_code=500, detail="RETRIEVAL_FAILED") from e

        # List zettels endpoint
        async def list_zettels_endpoint(request: ListZettelsRequest) -> JSONResponse:  # pyright: ignore[reportUnusedFunction]
            """List zettels with optional filtering."""
            try:
                result = self.engine.list_zettels(request)
                return JSONResponse(content=result.model_dump())

            except Exception as e:
                logger.exception("Zettel listing failed")
                raise HTTPException(status_code=500, detail="LISTING_FAILED") from e

        # Register routes with explicit binding (avoids Pylance warnings)
        self.app.post("/store")(store_zettel_endpoint)
        self.app.post("/retrieve")(retrieve_zettel_endpoint)
        self.app.post("/list")(list_zettels_endpoint)


# Phase D: End-to-End Integration & Main Entry
# =============================================

def main() -> None:
    """Main entry point - creates and runs sonnet zettel manager worker."""
    worker = SonnetZettelManagerWorker()
    worker.run()


if __name__ == "__main__":
    main()
