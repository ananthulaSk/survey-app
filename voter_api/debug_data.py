from main import SessionLocal, Survey, SurveyorRequest

db = SessionLocal()

print("--- ACTIVE SURVEYS ---")
surveys = db.query(Survey).filter(Survey.status == "ACTIVE").all()
if not surveys:
    print("No Active Surveys Found.")
else:
    for s in surveys:
        print(f"ID: {s.id} | Name: {s.name}")
        print(f"  Scope: {s.scope_type} | Val: {s.scope_value}")
        print(f"  Loc: Dist='{s.district}', Mandal='{s.mandal}', Vill='{s.village}'")
        print("-" * 30)

print("\n--- DEMO COORDINATOR ---")
coord = db.query(SurveyorRequest).filter(SurveyorRequest.mobile_no == "9999999999").first()
if coord:
    print(f"Name: {coord.name} | Role: {coord.role}")
    print(f"Loc: Dist='{coord.district_name}', Mandal='{coord.mandal_name}', Vill='{coord.village_name}'")
    print(f"Assigned Village ID: {coord.assigned_village_id}")
else:
    print("Demo Coordinator NOT FOUND")

db.close()
