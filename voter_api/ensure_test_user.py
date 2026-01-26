from database import SessionLocal
from main import SurveyorRequest

db = SessionLocal()

# 1. Check for 'Demo Coordinator' (9999999999)
demo = db.query(SurveyorRequest).filter(SurveyorRequest.mobile_no == '9999999999').first()
if demo:
    print(f"[FOUND] Demo User: {demo.name} ({demo.mobile_no}) - Status: {demo.status}")
else:
    print("[CREATING] Demo Coordinator 9999999999...")
    new_coord = SurveyorRequest(
        name="Demo Coordinator",
        mobile_no="9999999999",
        district_name="Yadadri Bhuvanagiri",
        mandal_name="Choutuppal",
        village_name="Aregudem",
        ward_no="0",
        role="COORDINATOR",
        assigned_village_id=1,
        status="APPROVED",
        device_id="manual-seed-coord"
    )
    db.add(new_coord)
    db.commit()
    print("[SUCCESS] Created Demo Coordinator 9999999999")

# 2. Check/Create 'Test User' (6666666666)
test_user = db.query(SurveyorRequest).filter(SurveyorRequest.mobile_no == '6666666666').first()
if test_user:
    print(f"[FOUND] Test User: {test_user.name} ({test_user.mobile_no}) - Status: {test_user.status}")
else:
    print("[CREATING] Test User 6666666666...")
    new_user = SurveyorRequest(
        name="TEST_USER_API_2",
        mobile_no="6666666666",
        district_name="Yadadri Bhuvanagiri",
        mandal_name="Choutuppal",
        village_name="Aregudem",
        ward_no="1",
        role="SURVEYOR",
        assigned_village_id=1,
        status="APPROVED",
        device_id="manual-seed-script"
    )
    db.add(new_user)
    db.commit()
    print("[SUCCESS] Created Test User 6666666666")

db.close()
