from database import engine, SessionLocal
from sqlalchemy import text
import sys

def migrate():
    print("Migrating Database for Phase 4.2 (Village Coordinator)...")
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Add 'role' column
            try:
                conn.execute(text("ALTER TABLE surveyor_requests ADD COLUMN role VARCHAR DEFAULT 'SURVEYOR'"))
                print("✅ Added column 'role'")
            except Exception as e:
                print(f"ℹ️ Column 'role' likely exists or error: {e}")

            # 2. Add 'assigned_village_id' column
            try:
                conn.execute(text("ALTER TABLE surveyor_requests ADD COLUMN assigned_village_id INTEGER"))
                print("✅ Added column 'assigned_village_id'")
            except Exception as e:
                print(f"ℹ️ Column 'assigned_village_id' likely exists or error: {e}")

            trans.commit()
            print("Migration Phase 4.2 Complete!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Migration Failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    migrate()
