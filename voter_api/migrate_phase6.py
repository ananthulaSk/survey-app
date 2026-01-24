from database import engine
from sqlalchemy import text

def migrate_phase6():
    print("Running Phase 6 Migration: Voter Location Context...")
    
    with engine.connect() as conn:
        print("Checking if 'ward_id' column exists in 'voters' table...")
        try:
            # Check for column existence (SQLite/Postgres approach varies, simplified check)
            # We try to select the column. If it fails, we add it.
            conn.execute(text("SELECT ward_id FROM voters LIMIT 1"))
            print("- 'ward_id' column already exists. Skipping.")
        except Exception:
            print("- Adding 'ward_id' column to 'voters' table...")
            try:
                # Add ward_id column
                conn.execute(text("ALTER TABLE voters ADD COLUMN ward_id INTEGER REFERENCES ward_master(id)"))
                print("- Added 'ward_id' column.")
            except Exception as e:
                print(f"- Error adding column: {e}")
                
        print("Phase 6 Database Migration Complete.")

if __name__ == "__main__":
    migrate_phase6()
