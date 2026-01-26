import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"
ADMIN_KEY = "admin-secret-123"

def print_step(msg):
    print(f"\n--- {msg} ---")

def test_reporting_flow():
    session = requests.Session()
    
    # 1. SETUP: Reset & Seed Geo
    print_step("1. Resetting & Seeding Geo")
    session.post(f"{BASE_URL}/admin/reset_db", headers={"X-Admin-Token": ADMIN_KEY})
    session.post(f"{BASE_URL}/admin/seed_geo", headers={"X-Admin-Token": ADMIN_KEY})
    time.sleep(1) # Wait for geo commit
    
    # 2. FETCH MASTER DATA (Context for Upload)
    print_step("2. Fetching Master Data")
    # Get District
    resp = session.get(f"{BASE_URL}/locations/districts")
    districts = resp.json()
    district = next((d for d in districts if "Yadadri" in d['name']), None)
    if not district: raise Exception("District not found")
    print(f"   District: {district['name']} ({district['id']})")
    
    # Get Mandal
    resp = session.get(f"{BASE_URL}/locations/mandals/{district['id']}")
    mandal = resp.json()[0]
    print(f"   Mandal: {mandal['name']} ({mandal['id']})")
    
    # Get Village
    resp = session.get(f"{BASE_URL}/locations/villages/{mandal['id']}")
    village = resp.json()[0]
    print(f"   Village: {village['name']} ({village['id']})")
    
    # Get Ward
    resp = session.get(f"{BASE_URL}/locations/wards/{village['id']}")
    ward = resp.json()[0]
    print(f"   Ward: {ward['name']} ({ward['id']})")

    # 3. UPLOAD VOTERS (Linking to Ward ID)
    print_step("3. Uploading Voters to Ward")
    csv_content = """serial_no,house_no,voter_name,gender,age,relation_name,surname,ward_no,family_id
1,1-1,Ramesh Gupta,M,45,Suresh,Gupta,1,FAM001
2,1-2,Sita Gupta,F,40,Ramesh,Gupta,1,FAM001
3,1-3,Rajesh Kumar,M,22,Mahesh,Kumar,1,FAM002"""
    
    files = {'file': ('test.csv', csv_content, 'text/csv')}
    data = {
        'secret_key': ADMIN_KEY,
        'district_id': district['id'],
        'mandal_id': mandal['id'],
        'village_id': village['id'],
        'ward_id': ward['id'] # CRITICAL: This enables the Report Join
    }
    
    resp = session.post(f"{BASE_URL}/admin/upload-voters", files=files, data=data) 
    print(f"   Upload Status: {resp.json().get('status')}")

    # 4. REGISTER & APPROVE SURVEYOR
    print_step("4. Setup Surveyor")
    # Register
    surv_payload = {
        "name": "Report Tester", "mobile": "5555555555", 
        "district_name": district['name'], "mandal_name": mandal['name'],
        "village_name": village['name'], "ward_no": "1", "role": "SURVEYOR"
    }
    resp = session.post(f"{BASE_URL}/register/surveyor", json=surv_payload)
    sid = resp.json()['id']
    # Approve
    session.post(f"{BASE_URL}/dashboard/approve", json={"request_id": sid, "action": "APPROVED"})
    print(f"   Surveyor {sid} Ready")

    # 5. CREATE SURVEY & VOTE
    print_step("5. Create Activity")
    # Create Survey
    s_payload = {
        "name": "Reporting Demo", "scope_type": "MANDAL",
        "district_id": district['id'], "mandal_ids": json.dumps([mandal['id']]), 
        "village_ids": "ALL", "survey_type": "TEST"
    }
    resp = session.post(f"{BASE_URL}/surveys/create", json=s_payload, headers={"X-Admin-Token": ADMIN_KEY})
    survey_id = resp.json()['survey_id']
    print(f"   Survey Created: {survey_id}")
    
    # Assign
    session.post(f"{BASE_URL}/assignments/create", json={"survey_id": survey_id, "surveyor_id": sid})
    
    # Vote (Online)
    # Fetch
    resp = session.get(f"{BASE_URL}/voters/next?survey_id={survey_id}&ward=1&current_voter_id=0")
    voter_data = resp.json()['data']
    vid = voter_data['voter_id']
    
    # Vote
    vote_load = {
        "voter_id": vid, "survey_id": survey_id, "party": "TRS", 
        "voter_status": "AVAILABLE", "caste": "BC"
    }
    session.put(f"{BASE_URL}/voters/update", json=vote_load)
    print("   Vote Cast: TRS / BC")

    # 6. TEST ANALYTICS (AGGREGATION)
    print_step("6. Verify Aggregated Reports")
    
    # A. Mandal Report
    agg_payload = {
        "scope_type": "MANDAL",
        "mandal_ids": [mandal['id']]
    }
    resp = session.post(f"{BASE_URL}/analytics/aggregate", json=agg_payload)
    print(f"DEBUG: Aggregate Response: {resp.text}") # Debug
    report = resp.json()['data']
    print(f"   Mandal Report: {json.dumps(report, indent=2)}")
    
    # Validation
    metrics = report['metrics']
    if metrics['total_scope_voters'] >= 3 and metrics['completed_surveys'] >= 1:
        print("[OK] Aggregation Logic Verified")
    else:
        print(f"[FAIL] Aggregation Mismatch: {metrics}")

    # 7. TEST EXPORT
    print_step("7. Verify Master Export")
    resp = session.post(f"{BASE_URL}/analytics/export/master", json=agg_payload)
    if resp.status_code == 200:
        rows = resp.text.splitlines()
        print(f"   Export Rows: {len(rows)}")
        print(f"   Header: {rows[0]}")
        if len(rows) >= 4: # Header + 3 Voters
             print("[OK] Export Logic Verified")
        else:
             print("[FAIL] Export Content Missing")
    else:
        print(f"[FAIL] Export Failed: {resp.status_code}")

if __name__ == "__main__":
    try:
        test_reporting_flow()
    except Exception as e:
        print(f"\n[FAIL] FATAL: {e}")
