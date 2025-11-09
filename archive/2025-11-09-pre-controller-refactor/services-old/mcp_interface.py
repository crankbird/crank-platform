"""
MCP (Model Context Protocol) Interface for Crank Mesh Services

This module provides MCP server functionality to expose mesh services
as tools that AI agents can discover and use programmatically.

MCP enables agents to:
- Discover available mesh services and capabilities
- Invoke mesh operations with proper authentication
- Receive structured responses for further processing
- Handle errors and security constraints gracefully
"""

import json
from datetime import datetime
from typing import Any, Callable, Optional

from mesh_interface import MeshCapability, MeshInterface, MeshRequest


class MCPTool:
    """Represents a mesh operation as an MCP tool."""

    def __init__(self, service_type: str, capability: MeshCapability, handler: Callable):
        self.name = f"{service_type}_{capability.operation}"
        self.description = capability.description
        self.input_schema = capability.input_schema
        self.handler = handler
        self.policies_required = capability.policies_required
        self.limits = capability.limits or {}

    def to_mcp_tool(self) -> dict[str, Any]:
        """Convert to MCP tool definition."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    **self.input_schema.get("properties", {}),
                    "auth_token": {
                        "type": "string",
                        "description": "Authentication token for mesh service access",
                    },
                },
                "required": self.input_schema.get("required", []),
            },
        }


class MCPMeshServer:
    """
    MCP Server that exposes mesh services as tools for AI agents.

    This bridges the security-first mesh interface with MCP protocol,
    enabling agents to programmatically use Crank services.
    """

    def __init__(self, server_name: str = "crank-mesh"):
        self.server_name = server_name
        self.version = "1.0.0"
        self.tools: dict[str, MCPTool] = {}
        self.mesh_services: dict[str, MeshInterface] = {}

    def register_mesh_service(self, service: MeshInterface):
        """Register a mesh service and expose its capabilities as MCP tools."""
        service_type = service.service_type
        self.mesh_services[service_type] = service

        # Convert each capability to an MCP tool
        for capability in service.get_capabilities():
            handler = self._create_capability_handler(service, capability)
            tool = MCPTool(service_type, capability, handler)
            self.tools[tool.name] = tool

    def _create_capability_handler(
        self,
        service: MeshInterface,
        capability: MeshCapability,
    ) -> Callable:
        """Create a handler function for a specific capability."""

        async def handle_request(arguments: dict[str, Any]) -> dict[str, Any]:
            try:
                # Extract authentication
                auth_token = arguments.pop("auth_token", None)
                if not auth_token:
                    return {
                        "error": "Authentication token required",
                        "error_type": "authentication_error",
                    }

                # Create auth context (simplified - would integrate with real auth)
                auth_context = {
                    "user_id": f"mcp_user_{hash(auth_token) % 10000}",
                    "authenticated": True,
                    "api_key": auth_token,
                    "access_method": "mcp",
                }

                # Create mesh request
                mesh_request = MeshRequest(
                    service_type=service.service_type,
                    operation=capability.operation,
                    input_data=arguments,
                    policies=capability.policies_required,
                    metadata={"mcp_request": True, "timestamp": datetime.now().isoformat()},
                )

                # Process through mesh interface
                response = await service.process_request(mesh_request, auth_context)

                if response.success:
                    return {
                        "success": True,
                        "result": response.result,
                        "receipt_id": response.receipt_id,
                        "processing_time_ms": response.processing_time_ms,
                        "mesh_node_id": response.mesh_node_id,
                    }
                return {
                    "success": False,
                    "errors": response.errors,
                    "error_type": "processing_error",
                }

            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": "system_error",
                }

        return handle_request

    def get_mcp_server_info(self) -> dict[str, Any]:
        """Get MCP server information."""
        return {
            "name": self.server_name,
            "version": self.version,
            "description": "Crank Mesh Services exposed via Model Context Protocol",
            "capabilities": {
                "tools": True,
                "resources": False,  # Could add later for file/data access
                "prompts": False,  # Could add later for prompt templates
            },
        }

    def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools for MCP clients."""
        return [tool.to_mcp_tool() for tool in self.tools.values()]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool call from an MCP client."""
        if name not in self.tools:
            return {
                "error": f"Tool '{name}' not found",
                "error_type": "tool_not_found",
                "available_tools": list(self.tools.keys()),
            }

        tool = self.tools[name]

        # Validate tool limits and policies
        if tool.limits:
            # Check basic limits (could be more sophisticated)
            if "max_file_size" in tool.limits:
                # Would validate file sizes here
                pass

        try:
            result = await tool.handler(arguments)

            # Add MCP metadata
            result["tool_name"] = name
            result["server"] = self.server_name
            result["timestamp"] = datetime.now().isoformat()

            return result

        except Exception as e:
            return {
                "error": f"Tool execution failed: {e!s}",
                "error_type": "execution_error",
                "tool_name": name,
            }

    def get_tool_schema(self, tool_name: str) -> Optional[dict[str, Any]]:
        """Get detailed schema for a specific tool."""
        if tool_name not in self.tools:
            return None

        tool = self.tools[tool_name]
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema,
            "policies_required": tool.policies_required,
            "limits": tool.limits,
            "security_note": "This tool requires authentication and follows security policies",
        }


class MCPMeshAdapter:
    """
    Adapter that converts between MCP protocol messages and mesh service calls.

    This handles the MCP protocol specifics while leveraging the security-first
    mesh interface underneath.
    """

    def __init__(self):
        self.server = MCPMeshServer()

    async def handle_mcp_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """Handle incoming MCP protocol messages."""
        method = message.get("method")
        params = message.get("params", {})
        request_id = message.get("id")

        try:
            if method == "initialize":
                return await self._handle_initialize(request_id, params)
            if method == "tools/list":
                return await self._handle_list_tools(request_id)
            if method == "tools/call":
                return await self._handle_call_tool(request_id, params)
            if method == "tools/schema":
                return await self._handle_tool_schema(request_id, params)
            return self._error_response(request_id, f"Unknown method: {method}")

        except Exception as e:
            return self._error_response(request_id, f"Error handling {method}: {e!s}")

    async def _handle_initialize(self, request_id: str, params: dict[str, Any]) -> dict[str, Any]:
        """Handle MCP initialize request."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True},
                },
                "serverInfo": self.server.get_mcp_server_info(),
            },
        }

    async def _handle_list_tools(self, request_id: str) -> dict[str, Any]:
        """Handle tools/list request."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": self.server.list_tools(),
            },
        }

    async def _handle_call_tool(self, request_id: str, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        result = await self.server.call_tool(tool_name, arguments)

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2),
                    },
                ],
            },
        }

    async def _handle_tool_schema(self, request_id: str, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tools/schema request."""
        tool_name = params.get("name")
        schema = self.server.get_tool_schema(tool_name)

        if schema:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": schema,
            }
        return self._error_response(request_id, f"Tool '{tool_name}' not found")

    def _error_response(self, request_id: str, error_message: str) -> dict[str, Any]:
        """Create an MCP error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -1,
                "message": error_message,
            },
        }


# Factory functions for easy setup
def create_mcp_mesh_server(mesh_services: list[MeshInterface]) -> MCPMeshServer:
    """Create an MCP server with multiple mesh services."""
    server = MCPMeshServer()

    for service in mesh_services:
        server.register_mesh_service(service)

    return server


def create_mcp_adapter_with_services(mesh_services: list[MeshInterface]) -> MCPMeshAdapter:
    """Create a complete MCP adapter with mesh services."""
    adapter = MCPMeshAdapter()

    for service in mesh_services:
        adapter.server.register_mesh_service(service)

    return adapter


# Example usage
if __name__ == "__main__":
    # This would be used in conjunction with mesh services
    print("MCP Mesh Interface - Ready for agent integration")
    print("Agents can now discover and use Crank services programmatically!")

    # Example of what an agent would see:
    example_tools = [
        {
            "name": "document_convert",
            "description": "Convert documents between formats with security validation",
            "requires_auth": True,
            "policies": ["file_validation", "format_allowlist", "size_limits"],
        },
        {
            "name": "email_parse",
            "description": "Parse email archives with security validation",
            "requires_auth": True,
            "policies": ["file_validation", "email_content_scan", "size_limits"],
        },
        {
            "name": "email_classify",
            "description": "Classify emails using AI with privacy protection",
            "requires_auth": True,
            "policies": ["ai_model_validation", "privacy_protection"],
        },
    ]

    print(f"Example tools available: {len(example_tools)}")
    for tool in example_tools:
        print(f"  - {tool['name']}: {tool['description']}")
