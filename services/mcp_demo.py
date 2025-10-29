#!/usr/bin/env python3
"""
MCP Agent Demo - Testing Crank Mesh Services via MCP

This script demonstrates how an AI agent would discover and use
Crank services through the Model Context Protocol interface.
"""

import asyncio
import json
from typing import Dict, Any


class MockMCPAgent:
    """
    Mock AI agent that demonstrates MCP protocol interactions
    with Crank mesh services.
    """
    
    def __init__(self, agent_name: str = "demo-agent"):
        self.agent_name = agent_name
        self.server_connection = None
        self.available_tools = []
    
    async def connect_to_server(self):
        """Simulate connecting to Crank MCP server."""
        print(f"🤖 {self.agent_name}: Connecting to Crank MCP server...")
        
        # Simulate MCP initialize handshake
        init_request = {
            "jsonrpc": "2.0",
            "id": "init-1",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {
                    "name": self.agent_name,
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": {"listChanged": True}
                }
            }
        }
        
        print(f"   Sending: {init_request['method']}")
        
        # Simulate server response
        init_response = {
            "jsonrpc": "2.0",
            "id": "init-1",
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True}
                },
                "serverInfo": {
                    "name": "crank-mesh",
                    "version": "1.0.0",
                    "description": "Crank Mesh Services exposed via Model Context Protocol"
                }
            }
        }
        
        print(f"   ✅ Connected to {init_response['result']['serverInfo']['name']}")
        self.server_connection = True
    
    async def discover_tools(self):
        """Discover available tools from Crank services."""
        print(f"\n🔍 {self.agent_name}: Discovering available tools...")
        
        # Simulate tools/list request
        list_request = {
            "jsonrpc": "2.0",
            "id": "list-1", 
            "method": "tools/list"
        }
        
        # Simulate server response with Crank tools
        self.available_tools = [
            {
                "name": "document_convert",
                "description": "Convert documents between formats with security validation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to document"},
                        "target_format": {"type": "string", "description": "Target format (pdf, docx, etc.)"},
                        "auth_token": {"type": "string", "description": "Authentication token"}
                    },
                    "required": ["file_path", "target_format", "auth_token"]
                }
            },
            {
                "name": "email_parse",
                "description": "Parse email archives with security validation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mbox_path": {"type": "string", "description": "Path to MBOX file"},
                        "privacy_mode": {"type": "string", "description": "Privacy level (strict, normal, minimal)"},
                        "auth_token": {"type": "string", "description": "Authentication token"}
                    },
                    "required": ["mbox_path", "auth_token"]
                }
            },
            {
                "name": "email_classify",
                "description": "Classify emails using AI with privacy protection",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "emails": {"type": "array", "description": "List of email content to classify"},
                        "categories": {"type": "array", "description": "Target categories"},
                        "auth_token": {"type": "string", "description": "Authentication token"}
                    },
                    "required": ["emails", "auth_token"]
                }
            },
            {
                "name": "parsing_extract_receipts",
                "description": "Extract receipts and expense data from email archives",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mbox_path": {"type": "string", "description": "Path to MBOX file"},
                        "date_range": {"type": "object", "description": "Date range filter"},
                        "auth_token": {"type": "string", "description": "Authentication token"}
                    },
                    "required": ["mbox_path", "auth_token"]
                }
            }
        ]
        
        print(f"   📋 Discovered {len(self.available_tools)} tools:")
        for tool in self.available_tools:
            print(f"      • {tool['name']}: {tool['description']}")
        
        return self.available_tools
    
    async def use_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Demonstrate using a Crank tool via MCP."""
        print(f"\n🛠️  {self.agent_name}: Using tool '{tool_name}'")
        
        # Find the tool
        tool = next((t for t in self.available_tools if t['name'] == tool_name), None)
        if not tool:
            print(f"   ❌ Tool '{tool_name}' not found")
            return
        
        # Simulate tool call
        call_request = {
            "jsonrpc": "2.0",
            "id": f"call-{tool_name}",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        print(f"   📤 Calling: {tool_name}")
        print(f"   📋 Arguments: {json.dumps(arguments, indent=2)}")
        
        # Simulate successful response
        call_response = {
            "jsonrpc": "2.0",
            "id": f"call-{tool_name}",
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "success": True,
                            "result": f"Tool {tool_name} executed successfully",
                            "receipt_id": f"receipt-{hash(str(arguments)) % 10000}",
                            "processing_time_ms": 1234,
                            "mesh_node_id": "crank-mesh-01",
                            "security_validation": "passed"
                        }, indent=2)
                    }
                ]
            }
        }
        
        result = json.loads(call_response["result"]["content"][0]["text"])
        print(f"   ✅ Success: {result['success']}")
        print(f"   🧾 Receipt: {result['receipt_id']}")
        print(f"   ⏱️  Time: {result['processing_time_ms']}ms")
        print(f"   🔒 Security: {result['security_validation']}")
        
        return result
    
    async def demonstrate_workflow(self):
        """Demonstrate a complete workflow using multiple tools."""
        print(f"\n🔄 {self.agent_name}: Demonstrating multi-tool workflow")
        
        # Step 1: Parse email archive
        print("\n   Step 1: Parse email archive")
        await self.use_tool("email_parse", {
            "mbox_path": "/data/archives/2023.mbox",
            "privacy_mode": "strict",
            "auth_token": "demo-token-123"
        })
        
        # Step 2: Classify parsed emails
        print("\n   Step 2: Classify emails")
        await self.use_tool("email_classify", {
            "emails": ["sample email content"],
            "categories": ["business", "personal", "receipts", "newsletters"],
            "auth_token": "demo-token-123"
        })
        
        # Step 3: Extract receipts
        print("\n   Step 3: Extract receipts and expenses")
        await self.use_tool("parsing_extract_receipts", {
            "mbox_path": "/data/archives/2023.mbox", 
            "date_range": {"start": "2023-01-01", "end": "2023-12-31"},
            "auth_token": "demo-token-123"
        })
        
        print(f"\n   ✅ Workflow complete! Agent successfully used 3 Crank tools")


async def main():
    """Main demo execution."""
    print("=" * 70)
    print("🤖 MCP AGENT DEMO - Crank Mesh Services Integration")
    print("=" * 70)
    print()
    print("This demonstrates how AI agents discover and use Crank services")
    print("through the Model Context Protocol (MCP) interface.")
    print()
    
    # Create and run demo agent
    agent = MockMCPAgent("CrankDemo-Agent")
    
    try:
        # Connect to server
        await agent.connect_to_server()
        
        # Discover available tools
        await agent.discover_tools()
        
        # Demonstrate tool usage
        await agent.demonstrate_workflow()
        
        print("\n" + "=" * 70)
        print("🎉 DEMO COMPLETE")
        print("=" * 70)
        print()
        print("Key Benefits Demonstrated:")
        print("• Agents can discover Crank services automatically")
        print("• All tools require authentication (security-first)")
        print("• Operations provide audit receipts and timing")
        print("• Privacy and security policies are enforced")
        print("• Standardized interface across all services")
        print()
        print("Ready for real agent integration! 🚀")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")


if __name__ == "__main__":
    asyncio.run(main())