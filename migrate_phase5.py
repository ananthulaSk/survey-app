from database import engine, Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, text
import datetime

def migrate_phase5():
    print("Running Phase 5 Migration: Survey Assignments...")
    
    with engine.connect() as conn:
        print("Checking if 'survey_assignments' table exists...")
        try:
            conn.execute(text("SELECT 1 FROM survey_assignments LIMIT 1"))
            print("- 'survey_assignments' table already exists. Skipping.")
        except:
            print("- Creating 'survey_assignments' table...")
            # We use raw SQL for SQLite to be safe, or we can use SQLAlchemy create_all if we isolate the model.
            # Since main.py has all models, let's try raw SQL for this specific table to avoid import issues 
            # or just rely on the model definition if we import it.
            # Let's use the explicit CREATE TABLE for control.
            
            sql = """
            CREATE TABLE survey_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                survey_id INTEGER,
                surveyor_id INTEGER,
                assigned_at DATETIME,
                status VARCHAR DEFAULT 'ACTIVE',
                FOREIGN KEY(survey_id) REFERENCES surveys(id),
                FOREIGN KEY(surveyor_id) REFERENCES surveyor_requests(id)
            );
            """
            conn.execute(text(sql))
            
            # Add index
            conn.execute(text("CREATE INDEX ix_survey_assignments_survey_id ON survey_assignments (survey_id)"))
            conn.execute(text("CREATE INDEX ix_survey_assignments_surveyor_id ON survey_assignments (surveyor_id)"))

        
        print("Phase 5 Database Migration Complete.")

if __name__ == "__main__":
    migrate_phase5()
