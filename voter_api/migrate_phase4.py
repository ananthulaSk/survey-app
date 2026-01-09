from database import engine, Base
from sqlalchemy import Column, String, DateTime, text
import datetime

def migrate_phase4():
    print("Running Phase 4 Migration: Assessment & Hardening...")
    
    with engine.connect() as conn:
        print("Checking 'surveys' table columns...")
        # Check if survey_code exists, if not add it
        try:
            conn.execute(text("SELECT survey_code FROM surveys LIMIT 1"))
            print("- survey_code already exists.")
        except:
            print("- Adding column: survey_code")
            # SQLite doesn't support adding constraints (UNIQUE) easily in ALTER TABLE, 
            # so we add the column first. Pydantic/Logic will enforce uniqueness.
            conn.execute(text("ALTER TABLE surveys ADD COLUMN survey_code TEXT"))
            conn.execute(text("UPDATE surveys SET survey_code = 'LEGACY-' || id WHERE survey_code IS NULL"))

        # Check if survey_type exists
        try:
            conn.execute(text("SELECT survey_type FROM surveys LIMIT 1"))
            print("- survey_type already exists.")
        except:
            print("- Adding column: survey_type")
            conn.execute(text("ALTER TABLE surveys ADD COLUMN survey_type TEXT DEFAULT 'TEST'"))

        print("Checking 'survey_voters' table columns...")
        # Check if snapshot_created_at exists
        try:
            conn.execute(text("SELECT snapshot_created_at FROM survey_voters LIMIT 1"))
            print("- snapshot_created_at already exists.")
        except:
            print("- Adding column: snapshot_created_at")
            conn.execute(text("ALTER TABLE survey_voters ADD COLUMN snapshot_created_at DATETIME"))
            # Backfill with current time for existing
            now_str = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            conn.execute(text(f"UPDATE survey_voters SET snapshot_created_at = '{now_str}' WHERE snapshot_created_at IS NULL"))
        
        conn.commit()
    
    print("Phase 4 Database Migration Complete.")

if __name__ == "__main__":
    migrate_phase4()
