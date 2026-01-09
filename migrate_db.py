import sqlite3
import os

def migrate():
    db_path = 'voters.db'
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Add the missing column
        cursor.execute('ALTER TABLE voters ADD COLUMN voter_status VARCHAR DEFAULT "AVAILABLE"')
        conn.commit()
        print("Migration successful: Added voter_status column.")
    except Exception as e:
        print(f"Migration failed or column already exists: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
