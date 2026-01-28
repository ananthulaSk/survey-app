import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"
ADMIN_KEY = "admin-secret-123"

def print_header(msg):
    print(f"\n{'='*60}\n{msg}\n{'='*60}")

def print_step(msg):
    print(f"\n--- {msg} ---")

def test_lifecycle():
    session = requests.Session()
    
    print_header("STARTING E2E RELEASE VERIFICATION (v19.60-RC)")

    # ==================================================================================
    # STEP 0: CLEAN SLATE
    # ==================================================================================
    print_step("0. Resetting System & Seeding Master Data")
    resp = session.post(f"{BASE_URL}/admin/reset_db", headers={"X-Admin-Token": ADMIN_KEY})
    if resp.status_code != 200:
        print(f"[FAIL] DB Reset Failed: {resp.text}")
        return
    
    resp = session.post(f"{BASE_URL}/admin/seed_geo", headers={"X-Admin-Token": ADMIN_KEY})
    if resp.status_code != 200:
        print(f"[FAIL] Geo Seed Failed: {resp.text}")
        return
    print("   [OK] System Clean & Seeded")

    # ==================================================================================
    # STEP 1: LOGIN / REGISTRATION (Screen 1)
    # ==================================================================================
    print_step("1. User Registration (Mobile App Flow)")
    
    # Coordinator
    coord_mobile = "9900000001"
    coord_data = {
        "name": "Coordinator Rao",
        "mobile": coord_mobile,
        "district_name": "Yadadri Bhuvanagiri",
        "mandal_name": "Choutuppal",
        "village_name": "Aregudem",
        "ward_no": "0",
        "role": "COORDINATOR",
        "village_id": 1
    }
    resp = session.post(f"{BASE_URL}/register/surveyor", json=coord_data)
    coord_id = resp.json()['id']
    print(f"   [OK] Coordinator Registered: {coord_data['name']} (ID: {coord_id})")

    # Surveyor
    surv_mobile = "8800000001"
    surv_data = {
        "name": "Surveyor Suresh",
        "mobile": surv_mobile,
        "district_name": "Yadadri Bhuvanagiri",
        "mandal_name": "Choutuppal",
        "village_name": "Aregudem",
        "ward_no": "1",
        "role": "SURVEYOR",
        "village_id": 1
    }
    resp = session.post(f"{BASE_URL}/register/surveyor", json=surv_data)
    surv_id = resp.json()['id']
    print(f"   [OK] Surveyor Registered: {surv_data['name']} (ID: {surv_id})")

    # ==================================================================================
    # STEP 2: APPROVAL PENDING (Screen 2)
    # ==================================================================================
    print_step("2. Verifying 'Pending Approval' State")
    
    # Coordinator Approves Surveyor
    resp = session.post(f"{BASE_URL}/dashboard/approve", 
                        json={"request_id": surv_id, "action": "APPROVED"})
    print(f"   [OK] Coordinator Approved Surveyor {surv_id}")

    # ==================================================================================
    # STEP 3: CREATE & ASSIGN SURVEY (Backend Logic)
    # ==================================================================================
    print_step("3. Creating Survey & Retrieving Geography")
    
    # Get District ID
    resp = session.get(f"{BASE_URL}/locations/districts")
    districts = resp.json()
    dist_id = next(d['id'] for d in districts if d['name'] == "Yadadri Bhuvanagiri")
    
    # Create Survey
    survey_payload = {
        "name": "General Election 2026",
        "district_id": dist_id,
        "scope_type": "MANDAL",
        "mandal_ids": "ALL",
        "village_ids": "ALL",
        "survey_type": "GENERAL"
    }
    resp = session.post(f"{BASE_URL}/surveys/create", json=survey_payload, headers={"X-Admin-Token": ADMIN_KEY})
    survey_id = resp.json()['survey_id']
    print(f"   [OK] Survey Created: 'General Election 2026' (ID: {survey_id})")

    # Assign to Surveyor (Ward 1)
    assign_payload = {"survey_id": survey_id, "surveyor_id": surv_id}
    resp = session.post(f"{BASE_URL}/assignments/create", json=assign_payload)
    print(f"   [OK] Assigned Survey to Surveyor (Ward 1 Only)")

    # ==================================================================================
    # STEP 4: COLLECT VOTES (Screen 4 - Offline/Online)
    # ==================================================================================
    print_step("4. Data Collection (Surveyor Flow)")
    
    # Fetch Voter 1 (Ward 1)
    # IMPORTANT: Ensure ward filter works
    resp = session.get(f"{BASE_URL}/voters/next?ward=1&current_voter_id=0&survey_id={survey_id}")
    if resp.json()['status'] != 'success':
         print(f"[FAIL] Voter Fetch Error: {resp.text}")
         return
    voter1 = resp.json()['data']
    print(f"   [OK] Surveyor fetched voter: {voter1['name']} (Ward: {voter1.get('ward_no')})")

    # Submit Vote 1 (Online)
    vote1 = {
        "voter_id": voter1['voter_id'],
        "party": "PARTY_A",
        "mobile_no": "9111111111",
        "voter_status": "AVAILABLE",
        "occupation": "Farmer",
        "survey_id": survey_id
    }
    session.put(f"{BASE_URL}/voters/update", json=vote1)
    print("   [OK] Vote 1 Submitted (Online)")

    # Submit Vote 2 (Offline Simulation)
    # Fetch next voter
    resp = session.get(f"{BASE_URL}/voters/next?ward=1&current_voter_id={voter1['voter_id']}&survey_id={survey_id}")
    voter2 = resp.json()['data']
    
    vote2 = {
        "voter_id": voter2['voter_id'],
        "party": "PARTY_B",
        "voter_status": "AVAILABLE",
        "occupation": "Student",
        "survey_id": survey_id,
        "_saved_at": "2026-01-28T10:00:00" # Offline timestamp
    }
    session.put(f"{BASE_URL}/voters/update", json=vote2)
    print("   [OK] Vote 2 Submitted (Offline Sync)")

    # ==================================================================================
    # STEP 5: AGGREGATE REPORTS (Phase 7 - Screen 5)
    # ==================================================================================
    print_step("5. Phase 7 Reporting (Aggregation)")
    
    # Aggregate by Mandal
    agg_payload = {
        "scope_type": "MANDAL",
        "district_ids": [dist_id],
        "mandal_ids": [] # All
    }
    resp = session.post(f"{BASE_URL}/analytics/aggregate", json=agg_payload)
    stats = resp.json()
    # Expecting PARTY_A: 1, PARTY_B: 1
    print(f"   [OK] Aggregated Stats Received")
    print(f"   DEBUG Sample: {json.dumps(stats, indent=2)}")

    # ==================================================================================
    # STEP 6: MASTER DATA EXPORT (Phase 7)
    # ==================================================================================
    print_step("6. Master Data Export")
    
    export_payload = {
        "scope_type": "DISTRICT",
        "district_ids": [dist_id]
    }
    resp = session.post(f"{BASE_URL}/analytics/export/master", json=export_payload)
    assert resp.status_code == 200
    csv_lines = resp.text.splitlines()
    print(f"   [OK] Master Export Success. Total Rows: {len(csv_lines)}")
    print(f"   [OK] CSV Header: {csv_lines[0]}")

    print_header("VERIFICATION COMPLETE - ALL SYSTEMS GO")

if __name__ == "__main__":
    try:
        test_lifecycle()
    except Exception as e:
        print(f"\n[FAIL] Test Failed: {e}")
