"""
REST API and Swagger Documentation for Crank Mesh Services

This module enhances the mesh interface with comprehensive REST endpoints
and OpenAPI/Swagger documentation. Shows how the same mesh services can
be exposed through multiple protocols simultaneously.

Your mesh architecture supports:
- MCP (Model Context Protocol) for AI agents
- REST API for web applications and traditional integrations
- OpenAPI/Swagger for documentation and testing
- GraphQL (could be added)
- gRPC (could be added)
"""

import time

from fastapi import Depends, FastAPI, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from mesh_interface import MeshInterface, MeshRequest


def enhance_mesh_with_rest_api(service: MeshInterface) -> FastAPI:
    """
    Enhance a mesh service with comprehensive REST API and Swagger docs.

    This shows how the same mesh service can expose multiple interfaces:
    - Core mesh interface (universal)
    - MCP interface (for AI agents)
    - REST API (for web apps)
    - Swagger UI (for documentation)
    """

    app = service.create_app()  # Start with base mesh app

    # Add comprehensive REST endpoints
    _add_rest_endpoints(app, service)

    # Enhance OpenAPI documentation
    _enhance_openapi_docs(app, service)

    # Add Swagger UI customization
    _add_custom_swagger_ui(app, service)

    return app


def _add_rest_endpoints(app: FastAPI, service: MeshInterface):
    """Add comprehensive REST endpoints for each capability."""

    # Get capabilities to create specific endpoints
    capabilities = service.get_capabilities()

    for capability in capabilities:
        # Create REST endpoint for each capability
        endpoint_path = f"/api/v1/{service.service_type}/{capability.operation}"

        # Create the endpoint function dynamically
        async def create_capability_endpoint(cap=capability):
            async def capability_handler(
                request_data: dict,
                auth_context: dict = Depends(service._get_auth_context),
            ):
                """Handle REST request for specific capability."""
                try:
                    # Convert REST request to mesh request
                    mesh_request = MeshRequest(
                        service_type=service.service_type,
                        operation=cap.operation,
                        input_data=request_data,
                        policies=cap.policies_required,
                        metadata={"access_method": "rest_api"},
                    )

                    # Process through mesh interface
                    response = await service.process_request(mesh_request, auth_context)

                    # Return REST-friendly response
                    if response.success:
                        return {
                            "success": True,
                            "data": response.result,
                            "metadata": {
                                "receipt_id": response.receipt_id,
                                "processing_time_ms": response.processing_time_ms,
                                "service": service.service_type,
                                "operation": cap.operation,
                            },
                        }
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "success": False,
                            "errors": response.errors,
                            "operation": cap.operation,
                        },
                    )

                except Exception as e:
                    raise HTTPException(
                        status_code=500,
                        detail={
                            "success": False,
                            "error": str(e),
                            "operation": cap.operation,
                        },
                    )

            return capability_handler

        # Add the endpoint to FastAPI
        handler = create_capability_endpoint()
        app.post(
            endpoint_path,
            summary=capability.description,
            description=f"REST endpoint for {capability.operation} operation",
            tags=[f"{service.service_type}-operations"],
            response_model=dict,
        )(handler)

    # Add service-level endpoints
    @app.get(f"/api/v1/{service.service_type}/info", tags=[f"{service.service_type}-info"])
    async def get_service_info(auth_context: dict = Depends(service._get_auth_context)):
        """Get detailed service information."""
        return {
            "service_type": service.service_type,
            "capabilities": [
                {
                    "operation": cap.operation,
                    "description": cap.description,
                    "endpoint": f"/api/v1/{service.service_type}/{cap.operation}",
                    "policies_required": cap.policies_required,
                    "limits": cap.limits,
                }
                for cap in service.get_capabilities()
            ],
            "protocols_supported": ["mesh", "rest", "mcp"],
            "security": "API key authentication required",
        }

    @app.get(f"/api/v1/{service.service_type}/health", tags=[f"{service.service_type}-health"])
    async def health_check():
        """Health check endpoint (no auth required)."""
        return {
            "status": "healthy",
            "service": service.service_type,
            "timestamp": time.time(),
            "protocols": ["mesh", "rest", "mcp"],
        }


def _enhance_openapi_docs(app: FastAPI, service: MeshInterface):
    """Enhance OpenAPI documentation with rich descriptions."""

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=f"Crank {service.service_type.title()} Mesh Service API",
            version="1.0.0",
            description=f"""
# Crank {service.service_type.title()} Mesh Service

This service provides secure, enterprise-grade {service.service_type} processing capabilities through multiple interfaces:

## 🔌 **Multiple Protocol Support**
- **REST API** - Traditional HTTP endpoints for web applications
- **MCP (Model Context Protocol)** - For AI agent integration
- **Mesh Interface** - Universal service mesh communication

## 🔒 **Security First**
- API key authentication required for all operations
- Input validation and sanitization
- Audit trails and receipt generation
- Policy-based access control

## 📋 **Available Operations**
{chr(10).join([f"- **{cap.operation}**: {cap.description}" for cap in service.get_capabilities()])}

## 🚀 **Getting Started**
1. Obtain an API key
2. Include `Authorization: Bearer <your-api-key>` header
3. Make requests to operation endpoints
4. Check audit receipts in responses

## 📖 **Documentation**
- REST endpoints: `/api/v1/{service.service_type}/{{operation}}`
- Service info: `/api/v1/{service.service_type}/info`
- Health check: `/api/v1/{service.service_type}/health`
- MCP interface: `/mcp` (for AI agents)

Built on proven security foundation with adversarial testing.
            """,
            routes=app.routes,
            servers=[
                {"url": "http://localhost:8000", "description": "Development server"},
                {"url": "https://api.crank.example.com", "description": "Production server"},
            ],
        )

        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "API key authentication. Include 'Bearer ' prefix.",
            },
        }

        # Apply security to all endpoints
        for path_data in openapi_schema["paths"].values():
            for operation in path_data.values():
                if isinstance(operation, dict) and "tags" in operation:
                    if not any("health" in tag for tag in operation["tags"]):
                        operation["security"] = [{"ApiKeyAuth": []}]

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi


def _add_custom_swagger_ui(app: FastAPI, service: MeshInterface):
    """Add custom Swagger UI with enhanced documentation."""

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"Crank {service.service_type.title()} API Documentation",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
            swagger_ui_parameters={
                "deepLinking": True,
                "displayRequestDuration": True,
                "docExpansion": "list",
                "filter": True,
                "showExtensions": True,
                "showCommonExtensions": True,
                "tryItOutEnabled": True,
            },
        )

    @app.get("/api-guide", include_in_schema=False)
    async def api_guide():
        """Interactive API guide."""
        return JSONResponse(
            {
                "title": f"Crank {service.service_type.title()} API Guide",
                "getting_started": {
                    "1": "Get API key from administrator",
                    "2": "Include 'Authorization: Bearer <key>' header",
                    "3": "Make requests to operation endpoints",
                    "4": "Check responses for receipt IDs and audit info",
                },
                "endpoints": {
                    f"/api/v1/{service.service_type}/{cap.operation}": {
                        "method": "POST",
                        "description": cap.description,
                        "requires_auth": True,
                        "policies": cap.policies_required,
                    }
                    for cap in service.get_capabilities()
                },
                "protocols": {
                    "rest": f"/api/v1/{service.service_type}/{{operation}}",
                    "mcp": "/mcp (for AI agents)",
                    "mesh": "/v1/process (universal)",
                },
                "examples": {
                    "curl": f"""curl -X POST http://localhost:8000/api/v1/{service.service_type}/{{operation}} \\
  -H "Authorization: Bearer your-api-key" \\
  -H "Content-Type: application/json" \\
  -d '{{"key": "value"}}'""",
                    "python": f"""import requests

response = requests.post(
    'http://localhost:8000/api/v1/{service.service_type}/{{operation}}',
    headers={{'Authorization': 'Bearer your-api-key'}},
    json={{'key': 'value'}}
)""",
                },
            },
        )


# Example of creating a full REST API service
def create_rest_api_service(service: MeshInterface) -> FastAPI:
    """Create a complete REST API service with all enhancements."""

    # Start with enhanced mesh service
    app = enhance_mesh_with_rest_api(service)

    # Add additional REST-specific features
    @app.get("/", include_in_schema=False)
    async def root():
        """API root with navigation."""
        return {
            "message": f"Crank {service.service_type.title()} Mesh Service API",
            "version": "1.0.0",
            "documentation": "/docs",
            "api_guide": "/api-guide",
            "service_info": f"/api/v1/{service.service_type}/info",
            "health": f"/api/v1/{service.service_type}/health",
            "protocols": {
                "rest": "This interface - traditional HTTP endpoints",
                "mcp": "/mcp - for AI agent integration",
                "mesh": "/v1/process - universal service mesh",
            },
            "security": "API key required (Authorization: Bearer <key>)",
        }

    return app


if __name__ == "__main__":
    print("REST API Enhancement for Crank Mesh Services")
    print("=" * 50)
    print()
    print("Features provided:")
    print("✓ REST endpoints for each mesh capability")
    print("✓ Comprehensive OpenAPI/Swagger documentation")
    print("✓ Interactive API guide and examples")
    print("✓ Multiple protocol support (REST + MCP + Mesh)")
    print("✓ Security-first design with API key auth")
    print("✓ Audit trails and receipt generation")
    print()
    print("Same mesh service, multiple interfaces! 🚀")
