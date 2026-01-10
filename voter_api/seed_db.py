import csv
import os
from database import engine, SessionLocal, Base
from main import Voter

CSV_PATH = "voter_data.csv"

def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Clear existing data to ensure we have a clean slate (removes dummy data)
    num_deleted = db.query(Voter).delete()
    db.commit()
    print(f"Cleared {num_deleted} existing records.")

    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV file not found at {CSV_PATH}")
        return

    voters = []
    try:
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Map CSV columns to Database Model
                # CSV: serial_no,house_no,voter_name,gender,age,relation_name,surname,ward_no,family_id
                voter = Voter(
                    serial_no=int(row['serial_no']) if row['serial_no'] else 0,
                    house_no=row['house_no'],
                    voter_name=row['voter_name'],
                    gender=row['gender'],
                    age=int(row['age']) if row['age'] and row['age'].isdigit() else 0,
                    relation_name=row['relation_name'],
                    surname=row['surname'],
                    ward_no=int(row['ward_no']) if row['ward_no'] else 0,
                    family_id=row['family_id']
                )
                voters.append(voter)
        
        db.add_all(voters)
        db.commit()
        print(f"Successfully seeded {len(voters)} voters from CSV.")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
