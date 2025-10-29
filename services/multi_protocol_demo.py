#!/usr/bin/env python3
"""
Multi-Protocol Demo - Same Service, Multiple Interfaces

This demonstrates how your mesh architecture supports multiple protocols
simultaneously - REST, MCP, and native mesh interface.
"""

import asyncio
import json
from typing import Dict, Any


class MultiProtocolDemo:
    """Demonstrate the same service through different protocols."""
    
    def __init__(self):
        self.service_name = "document"  # Using document service as example
        self.base_url = "http://localhost:8000"
    
    async def demonstrate_protocols(self):
        """Show the same operation through different protocols."""
        
        print("🔌 MULTI-PROTOCOL DEMONSTRATION")
        print("=" * 50)
        print()
        print("Same mesh service, accessed through different protocols:")
        print()
        
        # Document conversion operation through each protocol
        operation_data = {
            "file_path": "/data/sample.docx",
            "target_format": "pdf",
            "options": {"quality": "high"}
        }
        
        await self._demo_rest_api(operation_data)
        await self._demo_mcp_protocol(operation_data)
        await self._demo_mesh_interface(operation_data)
        await self._demo_swagger_ui()
        
        print("\n" + "=" * 50)
        print("🎉 SAME SERVICE, MULTIPLE WAYS TO ACCESS!")
        print("=" * 50)
        print()
        print("Benefits:")
        print("• Web apps use REST API")
        print("• AI agents use MCP protocol") 
        print("• Services use mesh interface")
        print("• Swagger UI for testing/docs")
        print("• Security consistent across all protocols")
    
    async def _demo_rest_api(self, data: Dict[str, Any]):
        """Demonstrate REST API access."""
        print("🌐 REST API Access")
        print("-" * 20)
        
        # REST endpoint for document conversion
        rest_endpoint = f"{self.base_url}/api/v1/document/convert"
        
        print(f"Endpoint: POST {rest_endpoint}")
        print("Headers:")
        print("  Authorization: Bearer <your-api-key>")
        print("  Content-Type: application/json")
        print()
        print("Request Body:")
        print(json.dumps(data, indent=2))
        print()
        
        # Simulated response
        rest_response = {
            "success": True,
            "data": {
                "converted_file": "/output/sample.pdf",
                "format": "pdf",
                "size_bytes": 245760
            },
            "metadata": {
                "receipt_id": "rest-receipt-12345",
                "processing_time_ms": 2340,
                "service": "document",
                "operation": "convert"
            }
        }
        
        print("Response:")
        print(json.dumps(rest_response, indent=2))
        print()
    
    async def _demo_mcp_protocol(self, data: Dict[str, Any]):
        """Demonstrate MCP protocol access."""
        print("🤖 MCP Protocol Access (AI Agents)")
        print("-" * 35)
        
        # MCP tool call
        mcp_request = {
            "jsonrpc": "2.0",
            "id": "convert-123",
            "method": "tools/call",
            "params": {
                "name": "document_convert",
                "arguments": {
                    **data,
                    "auth_token": "agent-api-key"
                }
            }
        }
        
        print("MCP Request:")
        print(json.dumps(mcp_request, indent=2))
        print()
        
        # Simulated MCP response
        mcp_response = {
            "jsonrpc": "2.0",
            "id": "convert-123",
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "success": True,
                            "result": {
                                "converted_file": "/output/sample.pdf",
                                "format": "pdf",
                                "size_bytes": 245760
                            },
                            "receipt_id": "mcp-receipt-67890",
                            "processing_time_ms": 2340,
                            "mesh_node_id": "crank-doc-01"
                        }, indent=2)
                    }
                ]
            }
        }
        
        print("MCP Response:")
        print(json.dumps(mcp_response, indent=2))
        print()
    
    async def _demo_mesh_interface(self, data: Dict[str, Any]):
        """Demonstrate native mesh interface access."""
        print("⚡ Native Mesh Interface Access")
        print("-" * 30)
        
        # Mesh request
        mesh_request = {
            "service_type": "document",
            "operation": "convert",
            "input_data": data,
            "policies": ["file_validation", "format_allowlist"],
            "metadata": {"access_method": "mesh_direct"}
        }
        
        print(f"Endpoint: POST {self.base_url}/v1/process")
        print("Headers:")
        print("  Authorization: Bearer <service-api-key>")
        print("  Content-Type: application/json")
        print()
        print("Mesh Request:")
        print(json.dumps(mesh_request, indent=2))
        print()
        
        # Simulated mesh response
        mesh_response = {
            "success": True,
            "result": {
                "converted_file": "/output/sample.pdf",
                "format": "pdf", 
                "size_bytes": 245760
            },
            "receipt_id": "mesh-receipt-abcde",
            "processing_time_ms": 2340,
            "mesh_node_id": "crank-doc-01",
            "errors": [],
            "audit_trail": {
                "policies_checked": ["file_validation", "format_allowlist"],
                "validation_passed": True,
                "timestamp": "2025-10-29T10:30:00Z"
            }
        }
        
        print("Mesh Response:")
        print(json.dumps(mesh_response, indent=2))
        print()
    
    async def _demo_swagger_ui(self):
        """Demonstrate Swagger UI access."""
        print("📖 Swagger UI Documentation")
        print("-" * 27)
        
        swagger_endpoints = [
            f"{self.base_url}/docs - Interactive API documentation",
            f"{self.base_url}/api-guide - API usage guide",
            f"{self.base_url}/api/v1/document/info - Service capabilities",
            f"{self.base_url}/openapi.json - OpenAPI specification"
        ]
        
        print("Available Documentation:")
        for endpoint in swagger_endpoints:
            print(f"  • {endpoint}")
        print()
        
        print("Swagger UI Features:")
        print("  • Try-it-out functionality")
        print("  • Request/response examples")
        print("  • Authentication testing")
        print("  • Schema validation")
        print("  • Download OpenAPI spec")
        print()


async def main():
    """Run the multi-protocol demonstration."""
    demo = MultiProtocolDemo()
    await demo.demonstrate_protocols()


if __name__ == "__main__":
    asyncio.run(main())