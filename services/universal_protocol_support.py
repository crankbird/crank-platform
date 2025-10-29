"""
Protocol Adapter Framework - Supporting Legacy and Future Protocols

This demonstrates how the mesh architecture can support ANY protocol
without breaking existing functionality. From gRPC to ONC RPC to 
protocols that don't exist yet.

The secret: Your MeshInterface is a perfect abstraction layer!
"""

from typing import Dict, List, Any, Optional, Union
import asyncio
import json
import struct
from abc import ABC, abstractmethod

# Your existing mesh interface
from mesh_interface import MeshInterface, MeshRequest, MeshResponse


class ProtocolAdapter(ABC):
    """Abstract base for any protocol adapter."""
    
    def __init__(self, mesh_service: MeshInterface):
        self.mesh_service = mesh_service
        self.protocol_name = "unknown"
    
    @abstractmethod
    async def handle_request(self, raw_request: bytes) -> bytes:
        """Convert protocol request -> mesh -> protocol response."""
        pass
    
    @abstractmethod
    def serialize_response(self, mesh_response: MeshResponse) -> bytes:
        """Convert mesh response to protocol format."""
        pass
    
    @abstractmethod
    def deserialize_request(self, raw_request: bytes) -> MeshRequest:
        """Convert protocol request to mesh format."""
        pass


class GRPCAdapter(ProtocolAdapter):
    """gRPC protocol adapter - modern, efficient."""
    
    def __init__(self, mesh_service: MeshInterface):
        super().__init__(mesh_service)
        self.protocol_name = "gRPC"
    
    async def handle_request(self, raw_request: bytes) -> bytes:
        """Handle gRPC request."""
        # In real implementation, would use protobuf
        grpc_request = self._parse_grpc_request(raw_request)
        
        # Convert to mesh request
        mesh_request = MeshRequest(
            service_type=self.mesh_service.service_type,
            operation=grpc_request["method"],
            input_data=grpc_request["params"],
            policies=grpc_request.get("policies", []),
            metadata={"protocol": "grpc", "version": grpc_request.get("version", "1.0")}
        )
        
        # Process through mesh (same security, validation, audit)
        auth_context = self._extract_grpc_auth(grpc_request)
        mesh_response = await self.mesh_service.process_request(mesh_request, auth_context)
        
        # Convert back to gRPC format
        return self._serialize_grpc_response(mesh_response)
    
    def _parse_grpc_request(self, raw_request: bytes) -> dict:
        """Parse gRPC protobuf request (simplified)."""
        # In real implementation: protobuf.parse(raw_request)
        return {
            "method": "convert",
            "params": {"file_path": "/data/test.docx", "format": "pdf"},
            "metadata": {"auth_token": "grpc-token-123"}
        }
    
    def _extract_grpc_auth(self, grpc_request: dict) -> dict:
        """Extract auth from gRPC metadata."""
        token = grpc_request.get("metadata", {}).get("auth_token", "")
        return {
            "authenticated": bool(token),
            "api_key": token,
            "user_id": f"grpc_user_{hash(token) % 10000}",
            "access_method": "grpc"
        }
    
    def _serialize_grpc_response(self, mesh_response: MeshResponse) -> bytes:
        """Convert mesh response to gRPC protobuf."""
        # In real implementation: protobuf.serialize(response_proto)
        grpc_response = {
            "success": mesh_response.success,
            "result": mesh_response.result,
            "metadata": {
                "receipt_id": mesh_response.receipt_id,
                "processing_time": mesh_response.processing_time_ms,
                "node_id": mesh_response.mesh_node_id
            },
            "errors": mesh_response.errors
        }
        return json.dumps(grpc_response).encode('utf-8')
    
    def deserialize_request(self, raw_request: bytes) -> MeshRequest:
        """Required by abstract base."""
        grpc_req = self._parse_grpc_request(raw_request)
        return MeshRequest(
            service_type=self.mesh_service.service_type,
            operation=grpc_req["method"],
            input_data=grpc_req["params"]
        )
    
    def serialize_response(self, mesh_response: MeshResponse) -> bytes:
        """Required by abstract base."""
        return self._serialize_grpc_response(mesh_response)


class ONCRPCAdapter(ProtocolAdapter):
    """ONC RPC adapter - because sometimes legacy systems happen! 😅"""
    
    def __init__(self, mesh_service: MeshInterface):
        super().__init__(mesh_service)
        self.protocol_name = "ONC-RPC"
        # ONC RPC program/version numbers
        self.program_number = 100001
        self.version_number = 1
    
    async def handle_request(self, raw_request: bytes) -> bytes:
        """Handle ONC RPC request (XDR encoded)."""
        rpc_request = self._parse_onc_rpc(raw_request)
        
        # Convert to mesh request  
        mesh_request = MeshRequest(
            service_type=self.mesh_service.service_type,
            operation=self._map_rpc_procedure(rpc_request["procedure"]),
            input_data=rpc_request["params"],
            policies=["legacy_system_validation"],  # Special policies for legacy
            metadata={
                "protocol": "onc-rpc",
                "program": rpc_request["program"],
                "version": rpc_request["version"],
                "procedure": rpc_request["procedure"],
                "xid": rpc_request["xid"]  # Transaction ID
            }
        )
        
        # Process through mesh (same security!)
        auth_context = self._extract_rpc_auth(rpc_request)
        mesh_response = await self.mesh_service.process_request(mesh_request, auth_context)
        
        # Convert back to ONC RPC XDR format
        return self._serialize_onc_rpc_response(mesh_response, rpc_request["xid"])
    
    def _parse_onc_rpc(self, raw_request: bytes) -> dict:
        """Parse ONC RPC XDR request (simplified)."""
        # Real implementation would use XDR parsing
        # For demo, simulate parsing XDR-encoded request
        
        if len(raw_request) < 16:
            raise ValueError("Invalid ONC RPC request")
        
        # Simulate XDR parsing (big-endian format)
        xid = struct.unpack('>I', raw_request[0:4])[0]
        msg_type = struct.unpack('>I', raw_request[4:8])[0]  # 0 = CALL
        rpc_version = struct.unpack('>I', raw_request[8:12])[0]  # Should be 2
        program = struct.unpack('>I', raw_request[12:16])[0]
        
        return {
            "xid": xid,
            "msg_type": msg_type,
            "rpc_version": rpc_version,
            "program": program,
            "version": 1,
            "procedure": 1,  # CONVERT_DOCUMENT procedure
            "params": {
                "file_path": "/legacy/systems/document.txt",
                "target_format": "pdf"
            },
            "credentials": {"auth_type": "AUTH_SYS", "uid": 1000}
        }
    
    def _map_rpc_procedure(self, procedure_num: int) -> str:
        """Map ONC RPC procedure numbers to mesh operations."""
        procedure_map = {
            0: "ping",          # NULL procedure (always exists)
            1: "convert",       # CONVERT_DOCUMENT
            2: "validate",      # VALIDATE_DOCUMENT  
            3: "analyze",       # ANALYZE_DOCUMENT
            # Could map legacy procedure numbers to modern operations
        }
        return procedure_map.get(procedure_num, "unknown")
    
    def _extract_rpc_auth(self, rpc_request: dict) -> dict:
        """Extract auth from ONC RPC credentials."""
        creds = rpc_request.get("credentials", {})
        uid = creds.get("uid", 0)
        
        return {
            "authenticated": uid > 0,
            "api_key": f"legacy_uid_{uid}",
            "user_id": f"rpc_user_{uid}",
            "access_method": "onc-rpc",
            "legacy_uid": uid,
            "auth_type": creds.get("auth_type", "AUTH_NONE")
        }
    
    def _serialize_onc_rpc_response(self, mesh_response: MeshResponse, xid: int) -> bytes:
        """Convert mesh response to ONC RPC XDR format."""
        # Real implementation would use XDR encoding
        
        # ONC RPC response header (simplified)
        response_header = struct.pack('>I', xid)  # Transaction ID
        response_header += struct.pack('>I', 1)   # REPLY message type
        response_header += struct.pack('>I', 0 if mesh_response.success else 1)  # Accept status
        
        # Encode result data (simplified - real XDR would be more complex)
        if mesh_response.success:
            result_data = json.dumps({
                "success": True,
                "result": mesh_response.result,
                "receipt_id": mesh_response.receipt_id,
                "processing_time": mesh_response.processing_time_ms
            }).encode('utf-8')
        else:
            result_data = json.dumps({
                "success": False,
                "errors": mesh_response.errors
            }).encode('utf-8')
        
        # Length prefix for data
        length_prefix = struct.pack('>I', len(result_data))
        
        return response_header + length_prefix + result_data
    
    def deserialize_request(self, raw_request: bytes) -> MeshRequest:
        """Required by abstract base."""
        rpc_req = self._parse_onc_rpc(raw_request)
        return MeshRequest(
            service_type=self.mesh_service.service_type,
            operation=self._map_rpc_procedure(rpc_req["procedure"]),
            input_data=rpc_req["params"]
        )
    
    def serialize_response(self, mesh_response: MeshResponse) -> bytes:
        """Required by abstract base."""
        return self._serialize_onc_rpc_response(mesh_response, 12345)


class GraphQLAdapter(ProtocolAdapter):
    """GraphQL adapter - for when you need flexible queries."""
    
    def __init__(self, mesh_service: MeshInterface):
        super().__init__(mesh_service)
        self.protocol_name = "GraphQL"
    
    async def handle_request(self, raw_request: bytes) -> bytes:
        """Handle GraphQL query/mutation."""
        graphql_request = json.loads(raw_request.decode('utf-8'))
        
        # Parse GraphQL query to determine operation
        query = graphql_request.get("query", "")
        variables = graphql_request.get("variables", {})
        
        operation = self._parse_graphql_operation(query)
        
        # Convert to mesh request
        mesh_request = MeshRequest(
            service_type=self.mesh_service.service_type,
            operation=operation["name"],
            input_data={**operation["args"], **variables},
            policies=operation.get("policies", []),
            metadata={"protocol": "graphql", "query": query}
        )
        
        # Process through mesh
        auth_context = self._extract_graphql_auth(graphql_request)
        mesh_response = await self.mesh_service.process_request(mesh_request, auth_context)
        
        # Convert to GraphQL response
        return self._serialize_graphql_response(mesh_response)
    
    def _parse_graphql_operation(self, query: str) -> dict:
        """Parse GraphQL query (simplified)."""
        # Real implementation would use graphql-core parser
        if "mutation" in query.lower() and "convert" in query.lower():
            return {
                "name": "convert",
                "args": {"file_path": "/data/test.docx", "format": "pdf"},
                "type": "mutation"
            }
        elif "query" in query.lower():
            return {
                "name": "capabilities",
                "args": {},
                "type": "query"
            }
        else:
            return {"name": "unknown", "args": {}, "type": "query"}
    
    def _extract_graphql_auth(self, graphql_request: dict) -> dict:
        """Extract auth from GraphQL context."""
        # Would typically come from HTTP headers
        return {
            "authenticated": True,
            "api_key": "graphql-token-456",
            "user_id": "graphql_user_789",
            "access_method": "graphql"
        }
    
    def _serialize_graphql_response(self, mesh_response: MeshResponse) -> bytes:
        """Convert mesh response to GraphQL format."""
        if mesh_response.success:
            graphql_response = {
                "data": {
                    "result": mesh_response.result,
                    "metadata": {
                        "receiptId": mesh_response.receipt_id,
                        "processingTimeMs": mesh_response.processing_time_ms,
                        "meshNodeId": mesh_response.mesh_node_id
                    }
                }
            }
        else:
            graphql_response = {
                "errors": [
                    {
                        "message": error,
                        "extensions": {"code": "MESH_ERROR"}
                    }
                    for error in mesh_response.errors
                ]
            }
        
        return json.dumps(graphql_response).encode('utf-8')
    
    def deserialize_request(self, raw_request: bytes) -> MeshRequest:
        """Required by abstract base."""
        gql_req = json.loads(raw_request.decode('utf-8'))
        operation = self._parse_graphql_operation(gql_req.get("query", ""))
        return MeshRequest(
            service_type=self.mesh_service.service_type,
            operation=operation["name"],
            input_data=operation["args"]
        )
    
    def serialize_response(self, mesh_response: MeshResponse) -> bytes:
        """Required by abstract base."""
        return self._serialize_graphql_response(mesh_response)


class UniversalProtocolServer:
    """Server that can handle ANY protocol through adapters."""
    
    def __init__(self, mesh_service: MeshInterface):
        self.mesh_service = mesh_service
        self.adapters: Dict[str, ProtocolAdapter] = {}
        
        # Register protocol adapters
        self.register_adapter("grpc", GRPCAdapter(mesh_service))
        self.register_adapter("onc-rpc", ONCRPCAdapter(mesh_service))
        self.register_adapter("graphql", GraphQLAdapter(mesh_service))
    
    def register_adapter(self, protocol_name: str, adapter: ProtocolAdapter):
        """Register a new protocol adapter."""
        self.adapters[protocol_name] = adapter
        print(f"✓ Registered {protocol_name} adapter")
    
    async def handle_request(self, protocol: str, raw_request: bytes) -> bytes:
        """Route request to appropriate protocol adapter."""
        if protocol not in self.adapters:
            raise ValueError(f"Unsupported protocol: {protocol}")
        
        adapter = self.adapters[protocol]
        return await adapter.handle_request(raw_request)
    
    def list_supported_protocols(self) -> List[str]:
        """List all supported protocols."""
        return list(self.adapters.keys())


async def demonstrate_universal_protocols():
    """Demonstrate supporting any protocol."""
    print("🌐 UNIVERSAL PROTOCOL SUPPORT DEMONSTRATION")
    print("=" * 55)
    print()
    
    # Mock mesh service (would be your actual service)
    class MockMeshService(MeshInterface):
        def __init__(self):
            self.service_type = "document"
        
        async def process_request(self, request: MeshRequest, auth_context: dict) -> MeshResponse:
            return MeshResponse(
                success=True,
                result={"converted_file": "/output/test.pdf", "format": "pdf"},
                receipt_id=f"{auth_context.get('access_method', 'unknown')}-receipt-123",
                processing_time_ms=1500,
                mesh_node_id="universal-node-01"
            )
        
        def get_capabilities(self):
            return []
    
    mesh_service = MockMeshService()
    server = UniversalProtocolServer(mesh_service)
    
    print("🔧 Supported Protocols:")
    for protocol in server.list_supported_protocols():
        print(f"   • {protocol}")
    print()
    
    # Test each protocol
    protocols_to_test = [
        ("grpc", b"mock_grpc_request_data"),
        ("onc-rpc", struct.pack('>IIII', 12345, 0, 2, 100001) + b"padding_data"),
        ("graphql", b'{"query": "mutation { convert(file: \\"test.docx\\", format: \\"pdf\\") }"}')
    ]
    
    for protocol, test_data in protocols_to_test:
        print(f"🔄 Testing {protocol.upper()} Protocol:")
        try:
            response = await server.handle_request(protocol, test_data)
            print(f"   ✅ Success! Response length: {len(response)} bytes")
            
            # Show snippet of response
            if protocol == "graphql":
                response_data = json.loads(response.decode('utf-8'))
                print(f"   📄 Response: {json.dumps(response_data, indent=2)[:200]}...")
            else:
                print(f"   📄 Response starts with: {response[:50]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        print()
    
    print("🎉 KEY INSIGHT:")
    print("=" * 15)
    print("Your mesh architecture can support ANY protocol:")
    print("• Same security validation for all protocols")
    print("• Same audit trails and receipts") 
    print("• Same business logic and capabilities")
    print("• Protocol adapters are thin translation layers")
    print("• Legacy systems? No problem!")
    print("• Future protocols? Just add an adapter!")
    print()
    print("The mesh interface is the perfect abstraction! 🚀")


if __name__ == "__main__":
    asyncio.run(demonstrate_universal_protocols())