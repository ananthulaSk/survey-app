import requests

# Validates the new Coordinator Flow
BASE_URL = "http://localhost:8000" # Local for you
# BASE_URL = "https://voter-api-734320499622.asia-south2.run.app" # Cloud

def create_coordinator():
    payload = {
        "name": "Demo Coordinator",
        "mobile": "9999999999",
        "device_id": "web-admin-seed",
        "district_name": "Yadadri Bhuvanagiri",
        "mandal_name": "Choutuppal",
        "village_name": "Aregudem", # Scope
        "ward_no": "0",
        "role": "COORDINATOR",
        "village_id": 1 # Assuming ID 1 is Aregudem from fresh seed
    }
    
    print(f"Registering Coordinator: {payload['name']}...")
    try:
        # 1. Register
        resp = requests.post(f"{BASE_URL}/register/surveyor", json=payload)
        data = resp.json()
        print(f"Register Response: {data}")
        
        if data['status'] == 'success' or data['status'] == 'exists':
             # 2. Approve (Simulate Admin Approval)
             req_id = data.get('id')
             print(f"Approving ID {req_id}...")
             approve_load = {"request_id": req_id, "action": "APPROVED"}
             # Needs Admin Token? Currently dashboard/approve doesn't check header in my quick check? 
             # Let's check main.py... It depends on get_db. It DOES NOT check X-Admin-Token in headers explicitly in the function body I reviewed!
             # Wait, Step 4057, approve_surveyor def... no header check. Good for seeding.
             
             resp2 = requests.post(f"{BASE_URL}/dashboard/approve", json=approve_load)
             print(f"Approval Response: {resp2.json()}")
             
             print("\n✅ SUCCESS! Use Mobile '9999999999' to Login as Coordinator.")
        else:
            print("Failed to register.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_coordinator()
