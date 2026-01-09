from database import engine, Base
from main import SurveyorRequest

def migrate_phase3():
    print("Creating new tables for Phase 3 (SurveyorRequest)...")
    Base.metadata.create_all(bind=engine)
    print("Migration Complete. 'surveyor_requests' table created.")

if __name__ == "__main__":
    migrate_phase3()
