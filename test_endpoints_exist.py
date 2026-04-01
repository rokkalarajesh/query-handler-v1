"""Quick test to verify agent endpoints are registered"""
import requests
import json

BASE_URL = "http://127.0.0.1:8003"

print("Testing API Endpoints Registration...")
print("=" * 80)

# Check OpenAPI schema to see if our endpoints are registered
try:
    response = requests.get(f"{BASE_URL}/api/openapi.json", timeout=2)
    if response.status_code == 200:
        schema = response.json()
        paths = schema.get("paths", {})
        
        print("\n✓ API Schema Retrieved Successfully\n")
        print("Available Endpoints:")
        print("-" * 80)
        
        agent_endpoints = {
            "/precall-agent/": False,
            "/caller-agent/": False, 
            "/postcall-agent/": False
        }
        
        for path in paths.keys():
            print(f"  • {path}")
            for agent_path in agent_endpoints:
                if agent_path in path:
                    agent_endpoints[agent_path] = True
        
        print("\n" + "=" * 80)
        print("Agent Workflow Endpoints Status:")
        print("-" * 80)
        
        for endpoint, found in agent_endpoints.items():
            status = "✓ FOUND" if found else "✗ NOT FOUND"
            print(f"{status}: {endpoint}")
            if found:
                methods = list(paths.get(endpoint, {}).keys())
                print(f"   Methods: {', '.join(m.upper() for m in methods)}")
        
        print("\n" + "=" * 80)
        all_found = all(agent_endpoints.values())
        if all_found:
            print("✓ ALL AGENT ENDPOINTS REGISTERED SUCCESSFULLY!")
        else:
            print("✗ Some endpoints are missing")
        
    else:
        print(f"Failed to get API schema. Status: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")

print("=" * 80)
