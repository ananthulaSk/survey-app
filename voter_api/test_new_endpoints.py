import requests
import json

BASE_URL = "http://localhost:8000"

def test_assignments():
    print("Testing Assignments API...")
    # 1. Create a test survey
    res = requests.post(f"{BASE_URL}/surveys/create", json={
        "name": "Verification Test Survey",
        "scope_type": "DISTRICT",
        "scope_value": "ALL",
        "district_id": 1,
        "mandal_ids": "ALL",
        "village_ids": "ALL"
    })
    survey_id = res.json().get("survey_id")
    print(f"Created Survey ID: {survey_id}")

    # 2. Assign a surveyor (Assumes surveyor ID 1 exists)
    res = requests.post(f"{BASE_URL}/surveys/assign", json={
        "survey_id": survey_id,
        "surveyor_id": 1
    })
    print(f"Assign Status: {res.status_code}, Response: {res.json()}")

    # 3. List assignments
    res = requests.get(f"{BASE_URL}/assignments/list?survey_id={survey_id}")
    print(f"Assignments List: {res.json()}")

    # 4. Unassign
    res = requests.post(f"{BASE_URL}/surveys/unassign", json={
        "survey_id": survey_id,
        "surveyor_id": 1
    })
    print(f"Unassign Status: {res.status_code}, Response: {res.json()}")

    # 5. Delete Survey
    res = requests.delete(f"{BASE_URL}/surveys/{survey_id}", headers={"x-admin-token": "admin-secret-123"})
    print(f"Delete Status: {res.status_code}, Response: {res.json()}")

if __name__ == "__main__":
    try:
        test_assignments()
    except Exception as e:
        print(f"Server is likely not running: {e}")
