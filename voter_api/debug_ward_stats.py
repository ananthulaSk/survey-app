from database import SessionLocal
from main import Voter

def check_stats():
    db = SessionLocal()
    
    print("--- CHECKING WARD 1 STATS ---")
    query = db.query(Voter).filter(Voter.ward_no == 1)
    total = query.count()
    print(f"Total voters in Ward 1: {total}")
    
    if total == 0:
        print("WARN: No voters found for Ward 1 (Integer). Checking string '1'...")
        # Since SQLAlchemy models force type, we might need raw SQL or just list all unique wards
        all_wards = db.query(Voter.ward_no).distinct().all()
        print(f"Distinct Wards in DB: {all_wards}")
        
    completed = query.filter(Voter.expected_party != None).count()
    print(f"Completed surveys in Ward 1: {completed}")
    
    # Check sample voter
    voter = db.query(Voter).filter(Voter.ward_no == 1).first()
    if voter:
        print(f"Sample Voter: ID={voter.voter_id}, Ward={voter.ward_no} (Type: {type(voter.ward_no)}), Status={voter.voter_status}")

    db.close()

if __name__ == "__main__":
    check_stats()
