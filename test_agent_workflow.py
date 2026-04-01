"""
Test script for agent workflow endpoints
"""
import requests
import json
from datetime import datetime
import uuid

BASE_URL = "http://127.0.0.1:8003"

# Test data for precall agent
precall_data = {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_name": "John Doe",
    "user_phone": "+1-555-1234",
    "user_mail": "john@example.com",
    "account_status": "Active",
    "preferred_language": "English",
    "preferred_contact_time": "Morning",
    "agent_contact_allowed": True,
    "collector_name": "Jane Smith",
    "collector_id": "COL001",
    "billing_address": "123 Main St, Anytown, USA",
    "credit_limit": "$10,000.00",
    "invoice_amount": "$5,000.00",
    "short_payment": 0,
    "over_payment": 0,
    "call_type": 1,
    "dispute": "$0.00",
    "payment_terms": "Net 30",
    "status": "Pending",
    "date": datetime.now().isoformat(),
    "notes": ["Customer called about payment arrangement", "Interested in partial payment"],
    "audio_recording_enable": True,
    "agent_call": True,
    "transcript": True
}

# Test data for caller agent (uses precall output structure)
caller_data = {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_name": "John Doe",
    "user_phone": "+1-555-1234",
    "user_mail": "john@example.com",
    "account_status": "Active",
    "preferred_language": "English",
    "preferred_contact_time": "Morning",
    "agent_contact_allowed": True,
    "collector_name": "Jane Smith",
    "collector_id": "COL001",
    "billing_address": "123 Main St, Anytown, USA",
    "credit_limit": "$10,000.00",
    "invoice_amount": "$5,000.00",
    "short_payment": 0,
    "over_payment": 0,
    "call_type": 1,
    "dispute": "$0.00",
    "payment_terms": "Net 30",
    "status": "Pending",
    "date": datetime.now().isoformat(),
    "notes": ["Customer called about payment arrangement", "Interested in partial payment"],
    "last_notes": "Interested in partial payment",
    "audio_recording_enable": True,
    "agent_call": True,
    "transcript": True,
    "call_prompt": "call_1",
    "message": "New record created for customer ID 550e8400-e29b-41d4-a716-446655440000"
}

# Test postcall agent input
postcall_data = {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_name": "John Doe",
    "user_phone": "+1-555-1234",
    "user_mail": "john@example.com",
    "account_status": "Active",
    "preferred_language": "English",
    "preferred_contact_time": "Morning",
    "agent_contact_allowed": True,
    "collector_name": "Jane Smith",
    "collector_id": "COL001",
    "billing_address": "123 Main St, Anytown, USA",
    "credit_limit": "$10,000.00",
    "invoice_amount": "$5,000.00",
    "short_payment": 0,
    "over_payment": 0,
    "call_type": 1,
    "dispute": "$0.00",
    "payment_terms": "Net 30",
    "status": "Pending",
    "date": datetime.now().isoformat(),
    "notes": ["Customer called about payment arrangement", "Interested in partial payment"],
    "last_notes": "Interested in partial payment",
    "audio_recording_enable": True,
    "agent_call": True,
    "transcript": True,
    "call_prompt": "call_1",
    "transcript_address": "https://blob.storage/transcript/550e8400.txt",
    "audio_address": "https://blob.storage/audio/550e8400.wav",
    "message": "New record created for customer ID 550e8400-e29b-41d4-a716-446655440000"
}

def test_endpoints():
    """Test all agent workflow endpoints"""
    
    print("=" * 80)
    print("TESTING AGENT WORKFLOW ENDPOINTS")
    print("=" * 80)
    
    # Test 1: Precall Agent
    print("\n1. Testing /precall-agent/ endpoint")
    print("-" * 80)
    try:
        response = requests.post(
            f"{BASE_URL}/precall-agent/",
            json=precall_data,
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code in [200, 201]:
            result = response.json()
            print("✓ SUCCESS - Precall Agent Response:")
            print(json.dumps(result, indent=2))
        else:
            print(f"✗ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
    
    # Test 2: Caller Agent
    print("\n2. Testing /caller-agent/ endpoint")
    print("-" * 80)
    try:
        response = requests.post(
            f"{BASE_URL}/caller-agent/",
            json=caller_data,
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code in [200, 201]:
            result = response.json()
            print("✓ SUCCESS - Caller Agent Response:")
            print(json.dumps(result, indent=2))
        else:
            print(f"✗ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
    
    # Test 3: Postcall Agent
    print("\n3. Testing /postcall-agent/ endpoint")
    print("-" * 80)
    try:
        response = requests.post(
            f"{BASE_URL}/postcall-agent/",
            json=postcall_data,
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code in [200, 201]:
            result = response.json()
            print("✓ SUCCESS - Postcall Agent Response:")
            print(json.dumps(result, indent=2))
        else:
            print(f"✗ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
    
    # Test 4: Get OpenAPI docs
    print("\n4. Testing API Documentation")
    print("-" * 80)
    try:
        response = requests.get(f"{BASE_URL}/api/docs", timeout=5)
        print(f"API Docs Status: {response.status_code}")
        if response.status_code == 200:
            print("✓ SUCCESS - API documentation is accessible at /api/docs")
        else:
            print(f"✗ ERROR: {response.status_code}")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    test_endpoints()
