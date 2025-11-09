#!/usr/bin/env python3
"""
Certificate Fix Confidence Test
Tests document conversion after mTLS certificate initialization fix
"""

import pytest
import requests


def test_document_conversion() -> bool:
    """Test document conversion with confidence tests"""

    platform_url = "https://crank-platform.greenforest-24b43401.australiaeast.azurecontainerapps.io"

    print("🧪 Testing document conversion after certificate fix...")

    # Test health first
    try:
        health_response = requests.get(f"{platform_url}/health/live", timeout=10)
        print(f"✅ Platform health: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Platform health failed: {e}")
        pytest.fail(f"Platform health failed: {e}")

    # Test worker status
    try:
        workers_response = requests.get(
            f"{platform_url}/v1/workers",
            headers={"Authorization": "Bearer azure-mesh-key-secure"},
            timeout=10,
        )
        if workers_response.status_code == 200:
            workers = workers_response.json()
            print(f"✅ Active workers: {len(workers)}")
            for worker in workers:
                print(
                    f"   - {worker['service_type']}: {worker['status']} (load: {worker['load_score']})",
                )
        else:
            print(f"⚠️  Worker status: {workers_response.status_code}")
    except Exception as e:
        print(f"❌ Worker status failed: {e}")

    # Test document conversion
    test_content = "This is a test document for conversion testing."

    try:
        print("\n📄 Testing document conversion...")
        conversion_response = requests.post(
            f"{platform_url}/v1/documents/convert",
            headers={"Authorization": "Bearer azure-mesh-key-secure"},
            data={"target_format": "pdf"},
            files={"file": ("test.txt", test_content, "text/plain")},
            timeout=30,
        )

        print(f"📊 Conversion response: {conversion_response.status_code}")

        if conversion_response.status_code == 200:
            result = conversion_response.json()
            print("✅ Document conversion successful!")
            print(f"   - Status: {result.get('status', 'unknown')}")
            print(f"   - Worker: {result.get('worker_id', 'unknown')}")
            print(f"   - Format: {result.get('target_format', 'unknown')}")
        else:
            print(f"❌ Document conversion failed: {conversion_response.status_code}")
            try:
                error_detail = conversion_response.json()
                print(f"   Error details: {error_detail}")
            except ValueError:
                print(f"   Error text: {conversion_response.text}")
            pytest.fail(f"Document conversion failed: {conversion_response.status_code}")

    except Exception as e:
        print(f"❌ Document conversion error: {e}")
        pytest.fail(f"Document conversion error: {e}")

    return True


def test_email_classification() -> bool:
    """Test email classification with confidence tests"""

    platform_url = "https://crank-platform.greenforest-24b43401.australiaeast.azurecontainerapps.io"

    print("\n📧 Testing email classification...")

    test_email = """From: test@example.com
To: support@company.com
Subject: Need help with account

I'm having trouble logging into my account. Can you please help me reset my password?

Thanks,
John"""

    try:
        classification_response = requests.post(
            f"{platform_url}/v1/route",
            headers={"Authorization": "Bearer azure-mesh-key-secure"},
            json={
                "service_type": "email-classifier",
                "payload": {"email_content": test_email},
            },
            timeout=30,
        )

        print(f"📊 Classification response: {classification_response.status_code}")

        if classification_response.status_code == 200:
            result = classification_response.json()
            print("✅ Email classification successful!")
            print(f"   - Status: {result.get('status', 'unknown')}")
            print(f"   - Worker: {result.get('worker_id', 'unknown')}")
            print(f"   - Classification: {result.get('classification', 'unknown')}")
        else:
            print(f"❌ Email classification failed: {classification_response.status_code}")
            try:
                error_detail = classification_response.json()
                print(f"   Error details: {error_detail}")
            except ValueError:
                print(f"   Error text: {classification_response.text}")
            pytest.fail(f"Email classification failed: {classification_response.status_code}")

    except Exception as e:
        print(f"❌ Email classification error: {e}")
        pytest.fail(f"Email classification error: {e}")

    return True


if __name__ == "__main__":
    print("🔐 Testing mTLS Certificate Fix - Document and Email Processing")
    print("=" * 60)

    doc_success = test_document_conversion()
    email_success = test_email_classification()

    print("\n" + "=" * 60)
    print("🎯 CONFIDENCE TEST RESULTS:")
    print(f"   Document Conversion: {'✅ PASS' if doc_success else '❌ FAIL'}")
    print(f"   Email Classification: {'✅ PASS' if email_success else '❌ FAIL'}")

    if doc_success and email_success:
        print("\n🎉 ALL TESTS PASSED - mTLS certificates working properly!")
    else:
        print("\n⚠️  Some tests failed - investigating...")
