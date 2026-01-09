import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_registration():
    print(f"Testing Registration against {BASE_URL}...")
    
    payload = {
        "name": "TEST_USER_API",
        "mobile": "9998887777",
        "device_id": "test_script_001"
    }
    
    try:
        # 1. Register
        print("\n1. Sending Registration Request...")
        resp = requests.post(f"{BASE_URL}/register/surveyor", json=payload)
        
        if resp.status_code == 200:
            print("   ✅ Success! Response:", resp.json())
        else:
            print(f"   ❌ Failed. Status: {resp.status_code}, Body: {resp.text}")
            return

        # 2. Check Dashboard List
        print("\n2. Checking Dashboard Approvals List...")
        resp = requests.get(f"{BASE_URL}/dashboard/approvals")
        data = resp.json()
        
        found = False
        for req in data:
            if req['mobile'] == "9998887777":
                print(f"   ✅ FOUND in Dashboard! ID: {req['id']}, Name: {req['name']}")
                found = True
                break
        
        if not found:
            print("   ❌ NOT FOUND in Dashboard list (Backend saved it, but List didn't return it?)")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_registration()
