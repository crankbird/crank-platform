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
from typing import Any

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
    
    def __init__(self, worker_id: str | None = None) -> None:
        """
        Initialize hello world worker.
        
        Args:
            worker_id: Optional unique identifier for this worker instance
        """
        super().__init__(worker_id=worker_id)
        self.engine = HelloWorldEngine()
        logger.info("HelloWorld worker initialized with ID: %s", self.worker_id)
    
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

async def main() -> None:
    """Main entry point for running the hello world worker."""
    import uvicorn
    
    # Create worker instance
    worker = HelloWorldWorker()
    
    logger.info("Starting HelloWorld worker server")
    logger.info("Worker capabilities: %s", [cap.name for cap in worker.get_capabilities()])
    
    # Configure and start server
    config = uvicorn.Config(
        app=worker.app,
        host="0.0.0.0",
        port=8500,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")


if __name__ == "__main__":
    import asyncio
    import sys
    
    # Test mode for development validation
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("=== HelloWorld Worker Test Mode ===")
        
        # Test worker instantiation
        worker = HelloWorldWorker(worker_id="test-hello-world")
        print(f"✅ Worker created with ID: {worker.worker_id}")
        
        # Test capabilities
        capabilities = worker.get_capabilities()
        print(f"✅ Capabilities: {[cap.name for cap in capabilities]}")
        
        # Test routes setup
        worker.setup_routes()
        total_routes = len(worker.app.routes)
        print(f"✅ Routes configured: {total_routes} total routes")
        
        # Test core engine functionality
        engine = HelloWorldEngine()
        result = engine.create_greeting("World", {"uppercase": True, "exclamations": 2})
        print(f"✅ Engine test: {result.greeting}")
        print(f"   Processing time: {result.processing_time_ms:.2f}ms")
        
        print("\n🎉 All tests passed! Hello World worker is ready.")
    else:
        # Production mode
        asyncio.run(main())