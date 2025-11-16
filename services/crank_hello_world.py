"""
Hello World Worker - Reference Implementation

This worker provides a complete, minimal example of the Crank Platform
worker development patterns. It demonstrates:

1. Schema-first development with Pydantic models
2. Contract-driven WorkerApplication implementation
3. Type-safe error handling and logging
4. Proper FastAPI route registration

Use this as a template for new worker development.
"""

import logging
import os
from typing import Any, Optional

import httpx
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from crank.capabilities.schema import CapabilityDefinition, CapabilityVersion, IOContract
from crank.worker_runtime.base import WorkerApplication

logger = logging.getLogger(__name__)


# Phase A: Schema Definition (Type-Safe Foundation)
# ================================================

class HelloWorldRequest(BaseModel):
    """Request model for hello world processing."""

    message: str = Field(description="Input message to process")
    options: dict[str, Any] = Field(
        default_factory=dict,
        description="Processing options (uppercase, reverse, etc.)"
    )


class HelloWorldResponse(BaseModel):
    """Response model for hello world processing."""

    greeting: str = Field(description="Processed greeting message")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Processing metadata and statistics"
    )
    processing_time_ms: float = Field(
        ge=0.0,
        description="Time taken to process request in milliseconds"
    )


# Capability definition matching the request/response schema
HELLO_WORLD_CAPABILITY = CapabilityDefinition(
    id="example.hello_world",
    version=CapabilityVersion(major=1, minor=0, patch=0),
    name="Hello World",
    description="Simple greeting service that demonstrates worker patterns",
    contract=IOContract(
        input_schema={
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "options": {"type": "object"}
            },
            "required": ["message"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "greeting": {"type": "string"},
                "metadata": {"type": "object"},
                "processing_time_ms": {"type": "number"}
            },
            "required": ["greeting", "processing_time_ms"]
        }
    ),
    tags=["example", "demo", "hello-world"],
    estimated_duration_ms=10
)


# Phase B: Business Logic (Isolated Testing)
# ===========================================

class HelloWorldEngine:
    """Core hello world processing logic - no FastAPI dependencies."""

    def __init__(self) -> None:
        """Initialize the greeting engine."""
        self._greeting_count = 0
        logger.info("HelloWorld engine initialized")

    def create_greeting(
        self,
        message: str,
        options: dict[str, Any] | None = None
    ) -> HelloWorldResponse:
        """
        Create a personalized greeting message.

        Args:
            message: Input message to process
            options: Optional processing flags:
                - uppercase: Convert to uppercase
                - reverse: Reverse the message
                - exclamations: Number of exclamation marks to add

        Returns:
            HelloWorldResponse with greeting and metadata

        Raises:
            ValueError: If message is empty or invalid options provided
        """
        import time

        start_time = time.perf_counter()

        # Input validation
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        # Process options with defaults
        opts = options or {}
        use_uppercase = opts.get("uppercase", False)
        use_reverse = opts.get("reverse", False)
        exclamations = opts.get("exclamations", 1)

        # Validate exclamations count
        if not isinstance(exclamations, int) or exclamations < 0 or exclamations > 10:
            raise ValueError("exclamations must be an integer between 0 and 10")

        # Create greeting
        processed_message = message.strip()

        if use_reverse:
            processed_message = processed_message[::-1]

        if use_uppercase:
            processed_message = processed_message.upper()

        greeting = f"Hello, {processed_message}{'!' * exclamations}"

        # Update statistics
        self._greeting_count += 1
        end_time = time.perf_counter()
        processing_time = (end_time - start_time) * 1000  # Convert to milliseconds

        return HelloWorldResponse(
            greeting=greeting,
            metadata={
                "total_greetings": self._greeting_count,
                "options_applied": opts,
                "character_count": len(greeting)
            },
            processing_time_ms=processing_time
        )

    @property
    def greeting_count(self) -> int:
        """Get the total number of greetings processed."""
        return self._greeting_count
# Phase C: Worker Runtime Integration
# ===================================

class HelloWorldWorker(WorkerApplication):
    """Worker providing hello world greeting capabilities."""

    def __init__(self) -> None:
        """Initialize hello world worker."""
        super().__init__(
            service_name="hello-world",
            https_port=int(os.getenv("HELLO_WORLD_HTTPS_PORT", "8900")),
        )
        self.engine = HelloWorldEngine()

        # Controller registration
        self.controller_url = os.getenv("CONTROLLER_URL")
        self.registered_with_controller = False

        logger.info("HelloWorld worker initialized with ID: %s", self.worker_id)
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
            # Convert capability to dict for registration
            capabilities = [
                {
                    "name": cap.id,
                    "verb": "invoke",
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

            # HTTPS with mTLS using worker certificates
            # Use worker's existing certificates for controller communication
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
            # Worker continues running even if registration fails

    def get_capabilities(self) -> list[CapabilityDefinition]:
        """Return capabilities this worker provides."""
        return [HELLO_WORLD_CAPABILITY]

    def setup_routes(self) -> None:
        """Register FastAPI routes for business logic."""

        # Main greeting endpoint
        async def greet_endpoint(request: HelloWorldRequest) -> JSONResponse:
            """Create greeting message matching the capability contract."""
            try:
                result = self.engine.create_greeting(
                    message=request.message,
                    options=request.options
                )
                return JSONResponse(content=result.model_dump())

            except ValueError as e:
                # Client errors - invalid input
                logger.warning("Invalid greeting request: %s", e)
                raise HTTPException(status_code=400, detail=str(e)) from e
            except Exception as e:
                # Server errors - unexpected failures
                logger.exception("Greeting processing failed")
                raise HTTPException(status_code=500, detail="GREETING_FAILED") from e

        # Statistics endpoint (bonus functionality)
        async def stats_endpoint() -> JSONResponse:
            """Return worker statistics."""
            return JSONResponse(content={
                "total_greetings": self.engine.greeting_count,
                "worker_id": self.worker_id,
                "capabilities": len(self.get_capabilities())
            })

        # Register routes with explicit binding (avoids Pylance warnings)
        self.app.post("/greet")(greet_endpoint)
        self.app.get("/stats")(stats_endpoint)


# Phase D: End-to-End Integration & Main Entry
# =============================================

def main() -> None:
    """Main entry point - creates and runs hello world worker."""
    worker = HelloWorldWorker()
    worker.run()


if __name__ == "__main__":
    main()
