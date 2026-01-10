import requests
import json
import sys

# Windows safe print
def safe_print(msg):
    try:
        print(msg.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
    except:
        print(msg)

BASE_URL = "http://127.0.0.1:8000"

def test_registration():
    safe_print(f"Testing Registration against {BASE_URL}...")
    
    payload = {
        "name": "TEST_USER_API_2",
        "mobile": "6666666666",
        "device_id": "test_script_002"
    }
    
    try:
        # 1. Register
        safe_print("\n1. Sending Registration Request...")
        resp = requests.post(f"{BASE_URL}/register/surveyor", json=payload)
        
        if resp.status_code == 200:
            safe_print(f"   [SUCCESS] Response: {resp.json()}")
        else:
            safe_print(f"   [FAILED] Status: {resp.status_code}, Body: {resp.text}")
            return

        # 2. Check Dashboard List
        safe_print("\n2. Checking Dashboard Approvals List...")
        resp = requests.get(f"{BASE_URL}/dashboard/approvals")
        data = resp.json()
        
        found = False
        for req in data:
            if req['mobile'] == "6666666666":
                safe_print(f"   [FOUND] in Dashboard! ID: {req['id']}, Name: {req['name']}")
                found = True
                break
        
        if not found:
            safe_print("   [NOT FOUND] in Dashboard list")
            
    except Exception as e:
        safe_print(f"[ERROR] Connection Error: {e}")

if __name__ == "__main__":
    test_registration()
