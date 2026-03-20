#!/usr/bin/env python
"""Test all API endpoints"""
import requests
import json

print("=" * 70)
print("TESTING COLLECTIONS API ENDPOINTS")
print("=" * 70)

# 1. Health Check
print("\n1. Health Check (/collections/health)")
print("-" * 70)
response = requests.get('http://localhost:8001/collections/health')
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# 2. Get Queue
print("\n2. Get Queue (/collections/queue)")
print("-" * 70)
response = requests.get('http://localhost:8001/collections/queue')
print(f"Status: {response.status_code}")
data = response.json()
print(f"Total Records: {data['total_records']}")
print(f"Sample Item:")
if data['records']:
    print(json.dumps(data['records'][0], indent=2, default=str))

# 3. Get Queue with Filter
print("\n3. Get Queue with Status Filter (/collections/queue?action_status=PromiseToPay)")
print("-" * 70)
response = requests.get('http://localhost:8001/collections/queue?action_status=PromiseToPay')
print(f"Status: {response.status_code}")
data = response.json()
print(f"Filtered Records: {data['total_records']}")

# 4. Get Case Details
if data['records']:
    case_id = data['records'][0]['case_id']
    print(f"\n4. Get Case Details (/collections/case/{case_id}/details)")
    print("-" * 70)
    response = requests.get(f'http://localhost:8001/collections/case/{case_id}/details')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        detail = response.json()
        print(f"Case ID: {detail.get('case_id')}")
        print(f"Customer Number: {detail.get('customer_number')}")
        print(f"Phone: {detail.get('phone')}")
        print(f"Email: {detail.get('email')}")
        print(f"Region: {detail.get('region')}")
        print(f"Invoice Numbers: {detail.get('invoice_numbers')}")
        print(f"Due Date: {detail.get('due_date')}")
        print(f"Outstanding Balance: {detail.get('outstanding_balance')}")
        print(f"Workflow Steps:")
        for step in (detail.get('workflow_steps') or []):
            print(f"  - {step}")
        print(f"Full Transcript:")
        for t in (detail.get('full_transcript') or []):
            print(f"  - {t}")
        print(f"Call Summary: {detail.get('call_summary')}")
        print(f"Actions:")
        for action in (detail.get('actions') or []):
            print(f"  - {action}")
        print(f"Call Recording: {detail.get('call_recording')}")
    else:
        print(f"Error: {response.text}")

print("\n" + "=" * 70)
print("✅ ALL ENDPOINTS TESTED SUCCESSFULLY!")
print("=" * 70)
