#!/usr/bin/env python3
"""
Test refactored email classifier without requiring CA service
"""
import os
import sys
from fastapi import FastAPI

# Mock the certificate environment for testing
os.environ["HTTPS_ONLY"] = "false"  # Disable HTTPS requirement for testing
os.environ["SERVICE_NAME"] = "crank-email-classifier"

# Import our refactored version
sys.path.append('/app')
from crank_email_classifier_refactored import setup_email_classifier_routes

def main():
    """Test the refactored email classifier without certificates."""
    print("🧪 Testing refactored email classifier (HTTP mode)...")
    
    # Create a simple FastAPI app for testing
    app = FastAPI(title="Test Email Classifier")
    
    # Mock worker config for HTTP mode
    mock_worker_config = {
        "app": app,
        "cert_store": None,  # No certificates in test mode
        "platform_url": "http://localhost:8080",
        "worker_url": "http://localhost:8201", 
        "service_name": "crank-email-classifier"
    }
    
    # Setup routes using the refactored function
    setup_email_classifier_routes(app, mock_worker_config)
    
    print("✅ Successfully set up email classifier routes using refactored pattern")
    print("✅ Routes configured:")
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"   - {route.methods} {route.path}")
    
    # Test health endpoint
    print("\n🔍 Testing health endpoint...")
    import asyncio
    from fastapi.testclient import TestClient
    
    with TestClient(app) as client:
        response = client.get("/health")
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Service: {data.get('service')}")
            print(f"Capabilities: {data.get('capabilities')}")
            print(f"Security status: {data.get('security')}")
            print("✅ Health endpoint working correctly")
        else:
            print(f"❌ Health endpoint failed: {response.text}")

if __name__ == "__main__":
    main()