from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from voter_api.main import Voter, Base

DATABASE_URL = "sqlite:///./voter_api/voters.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def test_stats(ward, current_id):
    print(f"Testing stats for Ward: {ward}, Current ID: {current_id}")
    
    query = db.query(Voter)
    if ward is not None:
        query = query.filter(Voter.ward_no == ward)
        
    total = query.count()
    completed = query.filter(Voter.expected_party != None).count()
    
    print(f"Total: {total}, Completed: {completed}")

    if current_id is not None and ward is not None:
        current_index = db.query(Voter).filter(
            Voter.ward_no == ward, 
            Voter.voter_id <= current_id
        ).count()
        print(f"Current Index: {current_index}")
    
    # Check data sample
    sample = db.query(Voter).first()
    if sample:
        print(f"Sample Voter Ward: {sample.ward_no} (Type: {type(sample.ward_no)})")

test_stats(1, 1) # Assuming Ward 1 exists
if __name__ == "__main__":
    pass
