from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import csv
import os

CSV_PATH = "voter_data.csv"

async def async_seed_data(db: AsyncSession):
    from main import Voter
    
    # 1. Clear existing data
    res_del = await db.execute(delete(Voter))
    await db.commit()
    print(f"[SEED] Cleared existing records.")

    if not os.path.exists(CSV_PATH):
        print(f"[SEED] Error: CSV file not found at {CSV_PATH}")
        return

    voters = []
    try:
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
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
        
        if voters:
            db.add_all(voters)
            await db.commit()
            print(f"[SEED] Successfully seeded {len(voters)} voters from CSV.")
        
    except Exception as e:
        print(f"[SEED] Error seeding database: {e}")
        await db.rollback()

if __name__ == "__main__":
    seed_data()
