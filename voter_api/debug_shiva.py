from database import SessionLocal
from main import SurveyorRequest, SurveyVoter, Survey

db = SessionLocal()

# 1. Check Shiva's Assignment
shiva = db.query(SurveyorRequest).filter(SurveyorRequest.name.ilike("%shiva%")).first()
if shiva:
    print(f"User: {shiva.name} | Mobile: {shiva.mobile_no} | Ward: '{shiva.ward_no}' (Type: {type(shiva.ward_no)})")
else:
    print("User Shiva not found.")

# 2. Check Survey Data
# Get latest survey
survey = db.query(Survey).order_by(Survey.id.desc()).first()
if survey:
    print(f"Survey: {survey.name} (ID: {survey.id})")
    
    # Check Voters in Ward 4
    count_w4 = db.query(SurveyVoter).filter(
        SurveyVoter.survey_id == survey.id,
        SurveyVoter.ward_no == 4
    ).count()
    print(f"Voters in Ward 4 (Int): {count_w4}")
    
    # Check Voters in "Ward 4" (String? - though DB column is int, sqlalchemy might cast)
    # Actually checking raw
    
    # Check what wards ARE there
    wards = db.query(SurveyVoter.ward_no).filter(SurveyVoter.survey_id == survey.id).distinct().all()
    print(f"Distinct Wards in Survey: {wards}")
else:
    print("No surveys found.")

db.close()
