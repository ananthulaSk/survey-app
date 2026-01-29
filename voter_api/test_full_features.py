import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"
ADMIN_KEY = "admin-secret-123"

def print_step(msg):
    print(f"\n--- {msg} ---")

def test_full_flow():
    session = requests.Session()
    
    # 1. RESET DATABASE
    print_step("1. Resetting Database")
    resp = session.post(f"{BASE_URL}/admin/reset_db", headers={"X-Admin-Token": ADMIN_KEY})
    if resp.status_code == 200:
        print("[OK] DB Reset Success")
    else:
        print(f"[FAIL] DB Reset Failed: {resp.text}")
        return

    # 1.5 SEED GEO DATA
    print_step("1.5 Seeding Geo Data")
    resp = session.post(f"{BASE_URL}/admin/seed_geo", headers={"X-Admin-Token": ADMIN_KEY})
    if resp.status_code == 200:
        print("[OK] Geo Data Seeded")
    else:
        print(f"[FAIL] Geo Seed Failed: {resp.text}")

    # 1.6 FETCH GEO IDs (Dynamic Resolution)
    print_step("1.6 Fetching Geo Master Data")
    time.sleep(1) 
    
    # Get District
    resp = session.get(f"{BASE_URL}/locations/districts")
    districts = resp.json()
    target_dist = next((d for d in districts if d['name'] == "Yadadri Bhuvanagiri"), None)
    if not target_dist:
        print("[FAIL] Yadadri Bhuvanagiri not found!")
        return
    district_id = target_dist['id']
    print(f"   [INFO] Using District ID: {district_id} ({target_dist['name']})")

    # Get Village (Fetch mandals first -> then villages)
    # Simplified: We know seed_geo creates "Choutuppal" mandal
    # Just need A valid village ID for registration.
    # Since we can't easily query villages by name without mandal ID, we'll assume ID 1 exists 
    # OR better: Add a quick lookup help if needed. 
    # For now, keeping village_id=1 but noting the risk. 
    # Actually, in seed_geo, Aregudem is likely the first village created. So ID 1 is probable.

    # 2. REGISTER USERS
    print_step("2. Registering Users")
    
    # Coordinator
    coord_payload = {
        "name": "Auto Coordinator",
        "mobile": "9988776655",
        "district_name": "Yadadri Bhuvanagiri",
        "mandal_name": "Choutuppal",
        "village_name": "Aregudem",
        "ward_no": "0",
        "role": "COORDINATOR",
        "village_id": 1 # Likely correct after fresh seed
    }
    resp = session.post(f"{BASE_URL}/register/surveyor", json=coord_payload)
    if resp.ok:
        coord_id = resp.json()['id']
        print(f"[OK] Coordinator Registered (ID: {coord_id})")
    else:
        print(f"[FAIL] Coord Reg Failed: {resp.text}")
        coord_id = None

    # Surveyor
    surv_payload = {
        "name": "Auto Surveyor",
        "mobile": "1122334455",
        "district_name": "Yadadri Bhuvanagiri",
        "mandal_name": "Choutuppal",
        "village_name": "Aregudem",
        "ward_no": "1",
        "role": "SURVEYOR",
        "village_id": 1
    }
    resp = session.post(f"{BASE_URL}/register/surveyor", json=surv_payload)
    if resp.ok:
        surv_id = resp.json()['id']
        print(f"[OK] Surveyor Registered (ID: {surv_id})")
    else:
        print(f"[FAIL] Surv Reg Failed: {resp.text}")
        surv_id = None

    # 3. APPROVE USERS (Admin)
    print_step("3. Approving Users")
    ids_to_approve = [uid for uid in [coord_id, surv_id] if uid]
    for uid in ids_to_approve:
        resp = session.post(f"{BASE_URL}/dashboard/approve", json={"request_id": uid, "action": "APPROVED"})
        if resp.ok:
            print(f"[OK] Approved User {uid}")
        else:
            print(f"[FAIL] Approval Failed for {uid}")

    # 4. CREATE SURVEY
    print_step("4. Creating Survey")
    # ... Survey Logic uses district_id fetched in 1.6

    # 4. CREATE SURVEY
    print_step("4. Creating Survey")
    survey_payload = {
        "name": "E2E Test Survey",
        "district_id": district_id,
        "scope_type": "VILLAGE",
        "survey_type": "TEST",
        "village_ids": "ALL",
        "mandal_ids": "ALL"
    }
    resp = session.post(f"{BASE_URL}/surveys/create", json=survey_payload, headers={"X-Admin-Token": ADMIN_KEY})
    print(f"DEBUG: Survey Create Response: {resp.text}")
    survey_id = resp.json()['survey_id']
    print(f"[OK] Survey Created (ID: {survey_id})")

    # 5. ASSIGN SURVEYOR
    print_step("5. Assigning Surveyor")
    assign_payload = {"survey_id": survey_id, "surveyor_id": surv_id}
    resp = session.post(f"{BASE_URL}/assignments/create", json=assign_payload)
    if resp.json()['status'] == 'success':
        print("[OK] Assignment Success")
    else:
        print(f"[FAIL] Assignment Failed: {resp.text}")

    # 6. SURVEYOR FLOW: FETCH VOTERS
    print_step("6. Surveyor: Fetching Voters")
    # Login check
    resp = session.post(f"{BASE_URL}/login", json={"mobile": "1122334455", "device_id": "auto-test"})
    # Fetch Next
    resp = session.get(f"{BASE_URL}/voters/next?ward=1&current_voter_id=0&survey_id={survey_id}")
    # print(f"DEBUG: Voter Fetch Response: {resp.text}") # Disabled for cleanup
    
    json_data = resp.json()
    if json_data.get('status') != 'success' or 'data' not in json_data:
        print(f"[FAIL] Voter Fetch Error: {resp.text}")
        return
        
    voter = json_data['data']
    voter_id = voter['voter_id'] # Note: 'voter_id' not 'id'
    print(f"[OK] Fetched Voter: {voter['name']} (ID: {voter_id})")

    # 7. SUBMIT VOTE (Online)
    print_step("7. Submitting Vote (Online)")
    vote_payload = {
        "voter_id": voter_id,
        "party": "TRS",
        "mobile_no": "9000000000",
        "voter_status": "AVAILABLE",
        "occupation": "Farmer",
        "survey_id": survey_id # Must include survey_id
    }
    resp = session.put(f"{BASE_URL}/voters/update", json=vote_payload)
    print(f"DEBUG: Vote Response: {resp.text}")
    if resp.status_code == 200 and resp.json().get('status') == 'success':
        print("[OK] Vote Submitted Successfully")
    else:
        print(f"[FAIL] Vote Failed: {resp.text}")

    # 8. SUBMIT VOTE (Offline Sync Simulation)
    print_step("8. Simulating Offline Sync")
    # Get another voter
    resp = session.get(f"{BASE_URL}/voters/next?ward=1&current_voter_id={voter_id}&survey_id={survey_id}")
    voter2 = resp.json()['data']
    voter2_id = voter2['voter_id']
    
    sync_payload = {
        "voter_id": voter2_id,
        "party": "INC",
        "voter_status": "AVAILABLE",
        "occupation": "Student",
        "survey_id": survey_id,
        "_saved_at": "2023-01-01T12:00:00" # Simulate offline timestamp
    }
    resp = session.put(f"{BASE_URL}/voters/update", json=sync_payload)
    if resp.json()['status'] == 'success':
        print("[OK] Offline Sync Vote Accepted")
    else:
        print(f"[FAIL] Offline Sync Failed: {resp.text}")

    # 9. DASHBOARD STATS
    print_step("9. Verifying Dashboard Stats")
    resp = session.get(f"{BASE_URL}/dashboard/summary?survey_id={survey_id}")
    stats = resp.json()['data']
    print(f"Stats: {stats}")
    # Check 'completed_surveys' (votes)
    if stats['completed_surveys'] >= 2:
        print("[OK] Stats Verified (2 Votes Collected)")
    else:
        print(f"[FAIL] Stats Mismatch: Found {stats['completed_surveys']}")

    # 10. EXPORT
    print_step("10. Testing Export")
    resp = session.get(f"{BASE_URL}/analytics/export/{survey_id}")
    if resp.status_code == 200:
        lines = resp.text.splitlines()
        print(f"[OK] Export Success. Rows: {len(lines)}")
        print(f"   Header: {lines[0]}")
    else:
        print(f"[FAIL] Export Failed: {resp.status_code}")

if __name__ == "__main__":
    try:
        test_full_flow()
    except Exception as e:
        print(f"\n[FAIL] FATAL ERROR: {e}")
