from database import SessionLocal
from main import Voter

def check_data():
    db = SessionLocal()
    voters = db.query(Voter).limit(5).all()
    print(f"Total voters found: {db.query(Voter).count()}")
    print("-" * 30)
    for v in voters:
        print(f"ID: {v.voter_id}, Name: {v.voter_name}, House: {v.house_no}")
    db.close()

if __name__ == "__main__":
    check_data()
