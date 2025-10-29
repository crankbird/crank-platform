#!/usr/bin/env python3
"""
Test script for Crank Platform mesh services.

This script tests both individual services and the gateway.
"""

import asyncio
import json
from pathlib import Path
import httpx
import tempfile


async def test_service_health(base_url: str, service_name: str):
    """Test service health endpoints."""
    print(f"\n🏥 Testing {service_name} health...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test liveness
            response = await client.get(f"{base_url}/health/live")
            if response.status_code == 200:
                print(f"✅ {service_name} is alive")
            else:
                print(f"❌ {service_name} liveness check failed: {response.status_code}")
            
            # Test readiness
            response = await client.get(f"{base_url}/health/ready")
            if response.status_code == 200:
                print(f"✅ {service_name} is ready")
            else:
                print(f"⚠️ {service_name} readiness check failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Failed to connect to {service_name}: {e}")


async def test_service_capabilities(base_url: str, service_name: str):
    """Test service capabilities endpoint."""
    print(f"\n🔍 Testing {service_name} capabilities...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{base_url}/v1/capabilities")
            if response.status_code == 200:
                capabilities = response.json()
                print(f"✅ {service_name} capabilities:")
                print(f"   Service type: {capabilities.get('service_type')}")
                print(f"   Operations: {capabilities.get('operations')}")
                print(f"   Formats: {capabilities.get('supported_formats')}")
            else:
                print(f"❌ {service_name} capabilities failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Failed to get {service_name} capabilities: {e}")


async def test_document_service():
    """Test CrankDoc mesh service."""
    print("\n📄 Testing CrankDoc service...")
    base_url = "http://localhost:8000"
    
    await test_service_health(base_url, "CrankDoc")
    await test_service_capabilities(base_url, "CrankDoc")
    
    # Test document validation
    print("\n📝 Testing document validation...")
    async with httpx.AsyncClient() as client:
        try:
            # Create test document
            test_content = b"# Test Document\n\nThis is a test markdown document."
            
            files = {"file": ("test.md", test_content, "text/markdown")}
            data = {
                "service_type": "document",
                "operation": "validate",
                "parameters": json.dumps({})
            }
            
            response = await client.post(f"{base_url}/v1/process", data=data, files=files)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Document validation successful:")
                print(f"   Job ID: {result.get('job_id')}")
                print(f"   Status: {result.get('status')}")
                if result.get('result'):
                    validation = result['result']
                    print(f"   Valid: {validation.get('is_valid')}")
                    print(f"   Format: {validation.get('format_detected')}")
            else:
                print(f"❌ Document validation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Document validation error: {e}")


async def test_email_service():
    """Test CrankEmail mesh service."""
    print("\n📧 Testing CrankEmail service...")
    base_url = "http://localhost:8001"
    
    await test_service_health(base_url, "CrankEmail")
    await test_service_capabilities(base_url, "CrankEmail")
    
    # Test email classification
    print("\n🔍 Testing email classification...")
    async with httpx.AsyncClient() as client:
        try:
            # Create test email
            test_email = """Subject: Your Amazon order receipt
From: auto-confirm@amazon.com
Date: Mon, 1 Jan 2024 12:00:00 +0000

Thank you for your order! 

Order Details:
- Product: Test Item
- Total: $29.99
- Order #: 123-4567890-1234567

Your item will be shipped soon.
"""
            
            files = {"file": ("test_email.eml", test_email.encode(), "message/rfc822")}
            data = {
                "service_type": "email",
                "operation": "classify",
                "parameters": json.dumps({})
            }
            
            response = await client.post(f"{base_url}/v1/process", data=data, files=files)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Email classification successful:")
                print(f"   Job ID: {result.get('job_id')}")
                print(f"   Status: {result.get('status')}")
                if result.get('result'):
                    classification = result['result']['classification']
                    print(f"   Is receipt: {classification.get('is_receipt')}")
                    print(f"   Confidence: {classification.get('confidence')}")
                    print(f"   Method: {classification.get('method')}")
            else:
                print(f"❌ Email classification failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Email classification error: {e}")


async def test_gateway():
    """Test the platform gateway."""
    print("\n🌐 Testing Platform Gateway...")
    base_url = "http://localhost:8080"
    
    await test_service_health(base_url, "Gateway")
    
    # Test gateway capabilities
    print("\n🔍 Testing gateway capabilities...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{base_url}/v1/capabilities")
            if response.status_code == 200:
                capabilities = response.json()
                print(f"✅ Gateway capabilities:")
                print(f"   Available services: {capabilities.get('available_services')}")
                for service, caps in capabilities.get('service_capabilities', {}).items():
                    if 'error' not in caps:
                        print(f"   {service}: {caps.get('operations', [])}")
                    else:
                        print(f"   {service}: {caps['error']}")
            else:
                print(f"❌ Gateway capabilities failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Gateway capabilities error: {e}")
    
    # Test routing through gateway
    print("\n📄 Testing document processing through gateway...")
    async with httpx.AsyncClient() as client:
        try:
            test_content = b"# Gateway Test\n\nTesting document processing through gateway."
            
            files = {"file": ("gateway_test.md", test_content, "text/markdown")}
            data = {
                "service_type": "document",
                "operation": "analyze",
                "parameters": json.dumps({})
            }
            
            response = await client.post(f"{base_url}/v1/process", data=data, files=files)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Gateway routing successful:")
                print(f"   Job ID: {result.get('job_id')}")
                print(f"   Service: {result.get('service_type')}")
                print(f"   Status: {result.get('status')}")
            else:
                print(f"❌ Gateway routing failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Gateway routing error: {e}")


async def main():
    """Run all tests."""
    print("🚀 Crank Platform Mesh Services Test")
    print("=" * 50)
    
    # Test individual services
    await test_document_service()
    await test_email_service()
    
    # Test gateway
    await test_gateway()
    
    print("\n✅ Testing complete!")
    print("\n📋 Next steps:")
    print("   1. Check service logs for any errors")
    print("   2. Test with real documents and emails")
    print("   3. Set up monitoring and alerts")
    print("   4. Deploy to Azure for production testing")


if __name__ == "__main__":
    asyncio.run(main())