from database import SessionLocal, engine
from main import Survey, SurveyVoter, SurveyAssignment, SurveyorRequest
from sqlalchemy import text

db = SessionLocal()

try:
    print("--- Clearing All Surveys and Requests ---")
    
    # 1. Delete all Assignments
    print("Deleting Assignments...")
    db.query(SurveyAssignment).delete()
    
    # 2. Delete all Survey Voters (Snapshots)
    print("Deleting Survey Snapshots...")
    db.query(SurveyVoter).delete()
    
    # 3. Delete all Surveys
    print("Deleting Surveys...")
    db.query(Survey).delete()
    
    # 4. Delete all Surveyor Requests (to clear the approval list too, so they can re-register)
    print("Deleting Surveyor Requests...")
    db.query(SurveyorRequest).delete()
    
    db.commit()
    print("✅ All data cleared successfully.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
finally:
    db.close()
