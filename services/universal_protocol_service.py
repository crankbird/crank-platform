"""
Universal Protocol Adapter Service - Critical Innovation

This service provides the universal protocol support that enables any protocol
to communicate with the mesh through a common interface. This is a CORE
architectural innovation that must be preserved.

Protocol Flow: External Protocol → Adapter → MeshInterface → Business Logic
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
import asyncio
import json
import struct
from datetime import datetime, timezone

from mesh_interface_v2 import MeshRequest, MeshResponse, MeshCapability
from platform_service import User


class ProtocolAdapter(ABC):
    """Abstract base for any protocol adapter - the core innovation."""
    
    def __init__(self, platform_service):
        self.platform = platform_service
        self.protocol_name = "unknown"
    
    @abstractmethod
    async def handle_request(self, raw_request: Any, user: User) -> Any:
        """Convert protocol request → mesh → protocol response."""
        pass
    
    @abstractmethod
    def serialize_response(self, mesh_response: Dict[str, Any]) -> Any:
        """Convert platform response to protocol format."""
        pass
    
    @abstractmethod
    def deserialize_request(self, raw_request: Any) -> Dict[str, Any]:
        """Convert protocol request to platform format."""
        pass


class RESTAdapter(ProtocolAdapter):
    """REST/HTTP adapter - already implemented in main platform."""
    
    def __init__(self, platform_service):
        super().__init__(platform_service)
        self.protocol_name = "REST"
    
    async def handle_request(self, request_data: Dict[str, Any], user: User) -> Dict[str, Any]:
        """Handle REST request through platform."""
        return await self.platform.route_request(
            request_data["service_type"],
            request_data["operation"], 
            request_data.get("data", {}),
            user
        )
    
    def serialize_response(self, platform_response: Dict[str, Any]) -> Dict[str, Any]:
        """REST responses are already JSON."""
        return platform_response
    
    def deserialize_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """REST requests are already in correct format."""
        return request_data


class MCPAdapter(ProtocolAdapter):
    """MCP (Model Context Protocol) adapter for AI agents."""
    
    def __init__(self, platform_service):
        super().__init__(platform_service)
        self.protocol_name = "MCP"
    
    async def handle_request(self, mcp_request: Dict[str, Any], user: User) -> Dict[str, Any]:
        """Handle MCP request from AI agent."""
        method = mcp_request.get("method")
        params = mcp_request.get("params", {})
        
        if method == "tools/list":
            return await self._list_tools(user)
        elif method == "tools/call":
            return await self._call_tool(params, user)
        else:
            raise ValueError(f"Unknown MCP method: {method}")
    
    async def _list_tools(self, user: User) -> Dict[str, Any]:
        """List available tools (platform capabilities)."""
        # Get capabilities from diagnostic service
        from mesh_diagnostics_v2 import DiagnosticMeshService
        diagnostic = DiagnosticMeshService()
        capabilities = diagnostic.get_capabilities()
        
        tools = []
        for cap in capabilities:
            tools.append({
                "name": f"crank_{cap.operation}",
                "description": cap.description,
                "inputSchema": cap.input_schema
            })
        
        # Add platform tools
        platform_tools = [
            {
                "name": "crank_route_request",
                "description": "Route request to worker services",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "service_type": {"type": "string"},
                        "operation": {"type": "string"},
                        "data": {"type": "object"}
                    },
                    "required": ["service_type", "operation"]
                }
            },
            {
                "name": "crank_list_workers",
                "description": "List available worker services",
                "inputSchema": {"type": "object", "properties": {}}
            }
        ]
        
        return {
            "tools": tools + platform_tools
        }
    
    async def _call_tool(self, params: Dict[str, Any], user: User) -> Dict[str, Any]:
        """Execute a tool call."""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        if tool_name.startswith("crank_"):
            operation = tool_name[6:]  # Remove "crank_" prefix
            
            if operation in ["ping", "echo_file", "load_test", "error_test"]:
                # Diagnostic operations
                mesh_request = MeshRequest(
                    service_type="diagnostic",
                    operation=operation,
                    input_data=arguments
                )
                
                # Create auth context
                auth_context = {
                    "user_id": user.user_id,
                    "username": user.username,
                    "roles": user.roles,
                    "authenticated": True
                }
                
                # Call diagnostic service
                from mesh_diagnostics_v2 import DiagnosticMeshService
                diagnostic = DiagnosticMeshService()
                response = await diagnostic.process_request(mesh_request, auth_context)
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(response.dict(), indent=2)
                        }
                    ]
                }
            
            elif operation == "route_request":
                # Platform routing
                result = await self.platform.route_request(
                    arguments["service_type"],
                    arguments["operation"],
                    arguments.get("data", {}),
                    user
                )
                
                return {
                    "content": [
                        {
                            "type": "text", 
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            
            elif operation == "list_workers":
                # List workers
                workers = await self.platform.discovery.get_workers()
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(workers, indent=2)
                        }
                    ]
                }
        
        raise ValueError(f"Unknown tool: {tool_name}")
    
    def serialize_response(self, platform_response: Dict[str, Any]) -> Dict[str, Any]:
        """Format response for MCP."""
        return platform_response
    
    def deserialize_request(self, mcp_request: Dict[str, Any]) -> Dict[str, Any]:
        """Parse MCP request."""
        return mcp_request


class gRPCAdapter(ProtocolAdapter):
    """gRPC adapter - high performance binary protocol."""
    
    def __init__(self, platform_service):
        super().__init__(platform_service)
        self.protocol_name = "gRPC"
    
    async def handle_request(self, grpc_request: Any, user: User) -> Any:
        """Handle gRPC request (stub for now)."""
        # TODO: Implement protobuf message parsing
        # For now, assume request has been converted to dict
        request_dict = {
            "service_type": getattr(grpc_request, "service_type", "diagnostic"),
            "operation": getattr(grpc_request, "operation", "ping"),
            "data": getattr(grpc_request, "data", {})
        }
        
        result = await self.platform.route_request(
            request_dict["service_type"],
            request_dict["operation"],
            request_dict["data"],
            user
        )
        
        return result
    
    def serialize_response(self, platform_response: Dict[str, Any]) -> Any:
        """Convert to gRPC response (stub)."""
        # TODO: Convert to protobuf message
        return platform_response
    
    def deserialize_request(self, grpc_request: Any) -> Dict[str, Any]:
        """Convert from gRPC request (stub)."""
        # TODO: Parse protobuf message
        return {}


class LegacyProtocolAdapter(ProtocolAdapter):
    """Framework for legacy/industrial protocols (RS422, Modbus, etc.)."""
    
    def __init__(self, platform_service, protocol_spec: Dict[str, Any]):
        super().__init__(platform_service)
        self.protocol_spec = protocol_spec
        self.protocol_name = protocol_spec.get("name", "Legacy")
    
    async def handle_request(self, raw_bytes: bytes, user: User) -> bytes:
        """Handle binary protocol request."""
        # Parse according to protocol specification
        request_dict = self._parse_binary_request(raw_bytes)
        
        # Route through platform
        result = await self.platform.route_request(
            request_dict["service_type"],
            request_dict["operation"], 
            request_dict["data"],
            user
        )
        
        # Convert back to binary format
        return self._encode_binary_response(result)
    
    def _parse_binary_request(self, raw_bytes: bytes) -> Dict[str, Any]:
        """Parse binary request according to protocol spec."""
        # Placeholder implementation - would be protocol-specific
        return {
            "service_type": "diagnostic",
            "operation": "ping",
            "data": {"message": "Legacy protocol request"}
        }
    
    def _encode_binary_response(self, response: Dict[str, Any]) -> bytes:
        """Encode response in binary format."""
        # Placeholder implementation - would be protocol-specific
        response_json = json.dumps(response)
        return response_json.encode('utf-8')
    
    def serialize_response(self, platform_response: Dict[str, Any]) -> bytes:
        """Convert to binary protocol format."""
        return self._encode_binary_response(platform_response)
    
    def deserialize_request(self, raw_bytes: bytes) -> Dict[str, Any]:
        """Parse binary protocol format."""
        return self._parse_binary_request(raw_bytes)


class UniversalProtocolService:
    """Universal protocol support service - the core innovation."""
    
    def __init__(self, platform_service):
        self.platform = platform_service
        self.adapters: Dict[str, ProtocolAdapter] = {}
        
        # Register default adapters
        self.register_adapter("REST", RESTAdapter(platform_service))
        self.register_adapter("MCP", MCPAdapter(platform_service))
        self.register_adapter("gRPC", gRPCAdapter(platform_service))
    
    def register_adapter(self, protocol_name: str, adapter: ProtocolAdapter):
        """Register a new protocol adapter."""
        self.adapters[protocol_name] = adapter
    
    def get_supported_protocols(self) -> List[str]:
        """Get list of supported protocols."""
        return list(self.adapters.keys())
    
    async def handle_protocol_request(self, protocol: str, request: Any, user: User) -> Any:
        """Route request through appropriate protocol adapter."""
        if protocol not in self.adapters:
            raise ValueError(f"Unsupported protocol: {protocol}")
        
        adapter = self.adapters[protocol]
        return await adapter.handle_request(request, user)
    
    def add_legacy_protocol(self, name: str, spec: Dict[str, Any]):
        """Add support for a legacy/industrial protocol."""
        adapter = LegacyProtocolAdapter(self.platform, spec)
        self.register_adapter(name, adapter)