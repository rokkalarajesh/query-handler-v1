#!/usr/bin/env python
"""Test API after fixes"""
import requests
import json
import time

# Wait for reload
time.sleep(2)

try:
    print("Testing /collections/queue endpoint...")
    response = requests.get('http://localhost:8000/collections/queue')
    
    print(f'Status: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        print(f'✅ Queue endpoint working!')
        print(f'Total records: {data.get("total_records")}')
        
        if data.get('records'):
            print(f'\nFirst queue item:')
            print(json.dumps(data['records'][0], indent=2, default=str))
    else:
        print(f'❌ Error response: {response.text}')
        
except Exception as e:
    print(f'❌ Exception: {e}')
    import traceback
    traceback.print_exc()
