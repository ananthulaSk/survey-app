from database import engine
from sqlalchemy import text

def migrate_phase6():
    print("Running Phase 6 Migration: Voter Location Context...")
    
    with engine.connect() as conn:
        print("Phase 6.1: Checking 'ward_id' in 'voters'...")
        try:
            conn.execute(text("SELECT ward_id FROM voters LIMIT 1"))
            print("- 'ward_id' exists.")
        except Exception:
            print("- Adding 'ward_id' to 'voters'...")
            try:
                conn.execute(text("ALTER TABLE voters ADD COLUMN ward_id INTEGER REFERENCES ward_master(id)"))
                conn.commit()
                print("- Added 'ward_id'.")
            except Exception as e:
                print(f"- Error: {e}")

        # FIX: Also add ward_no to surveyor_requests if missing
        print("Phase 6.2: Checking 'ward_no' in 'surveyor_requests'...")
        try:
            conn.execute(text("SELECT ward_no FROM surveyor_requests LIMIT 1"))
            print("- 'ward_no' exists.")
        except Exception:
            print("- Adding 'ward_no' to 'surveyor_requests'...")
            try:
                conn.execute(text("ALTER TABLE surveyor_requests ADD COLUMN ward_no VARCHAR"))
                conn.commit()
                print("- Added 'ward_no'.")
            except Exception as e:
                print(f"- Error: {e}")

        print("Phase 6 Database Migration Complete.")

if __name__ == "__main__":
    migrate_phase6()
