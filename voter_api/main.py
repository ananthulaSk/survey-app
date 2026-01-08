import urllib.parse
from fastapi import FastAPI, Depends, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, Integer, String, asc
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

# Import robust database setup
from database import engine, SessionLocal, Base, get_db

# --- VOTER MODEL (Matches AREGUDEM_MASTER_FINAL_PROD.csv) ---
class Voter(Base):
    __tablename__ = "voters"
    # We use a dedicated voter_id as the primary key for the database
    voter_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    serial_no = Column(Integer)
    house_no = Column(String)
    voter_name = Column(String)
    gender = Column(String)
    age = Column(Integer)
    relation_name = Column(String)
    surname = Column(String)
    ward_no = Column(Integer)
    family_id = Column(String)
    # Survey fields
    expected_party = Column(String, nullable=True)
    occupation = Column(String, nullable=True)
    religion = Column(String, nullable=True)
    caste = Column(String, nullable=True)
    sub_caste = Column(String, nullable=True)
    mobile_no = Column(String, nullable=True)

# Create the table in Google Cloud if it doesn't exist
Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS for Chrome/Web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models for Request Body ---
class VoterUpdate(BaseModel):
    voter_id: int
    party: Optional[str] = None
    occupation: Optional[str] = None
    religion: Optional[str] = None
    caste: Optional[str] = None
    sub_caste: Optional[str] = None
    mobile_no: Optional[str] = None

# --- API ENDPOINTS ---

@app.get("/")
def read_root():
    return {"status": "online", "message": "Voter API is running", "docs_url": "/docs"}

@app.get("/voters/search", response_model=List[dict])
def search_voters(query: str, db: Session = Depends(get_db)):
    # Search across Name and Surname
    voters = db.query(Voter).filter(
        (Voter.voter_name.ilike(f"%{query}%")) | 
        (Voter.surname.ilike(f"%{query}%"))
    ).limit(50).all()
    
    return [
        {
            "voter_id": v.voter_id,
            "name": v.voter_name,
            "surname": v.surname,
            "ward": v.ward_no,
            "house_no": v.house_no,
            "age": v.age,
            "gender": v.gender,
            "relation": v.relation_name,
            "expected_party": v.expected_party,
            "occupation": v.occupation,
            "religion": v.religion,
            "caste": v.caste,
            "sub_caste": v.sub_caste,
            "mobile_no": v.mobile_no
        } for v in voters
    ]

@app.get("/voters/next")
def get_next_voter(current_id: int = 0, db: Session = Depends(get_db)):
    # Fetch the next voter with ID greater than current_id
    voter = db.query(Voter).filter(Voter.voter_id > current_id).order_by(asc(Voter.voter_id)).first()
    
    if not voter:
        return {"status": "finished", "data": None}
        
    return {
        "status": "success",
        "data": {
            "voter_id": voter.voter_id,
            "name": voter.voter_name,
            "surname": voter.surname,
            "ward": voter.ward_no,
            "house_no": voter.house_no,
            "age": voter.age,
            "gender": voter.gender,
            "relation": voter.relation_name,
            "expected_party": voter.expected_party,
            "occupation": voter.occupation,
            "religion": voter.religion,
            "caste": voter.caste,
            "sub_caste": voter.sub_caste,
            "mobile_no": voter.mobile_no
        }
    }

@app.put("/voters/update")
def update_voter_data(data: VoterUpdate, db: Session = Depends(get_db)):
    voter = db.query(Voter).filter(Voter.voter_id == data.voter_id).first()
    if not voter:
        raise HTTPException(status_code=404, detail="Voter not found")
        
    # Update fields if provided
    if data.party is not None: voter.expected_party = data.party
    if data.occupation is not None: voter.occupation = data.occupation
    if data.religion is not None: voter.religion = data.religion
    if data.caste is not None: voter.caste = data.caste
    if data.sub_caste is not None: voter.sub_caste = data.sub_caste
    if data.mobile_no is not None: voter.mobile_no = data.mobile_no
    
    db.commit()
    return {"status": "success"}

@app.get("/voters/stats")
def get_voter_stats(ward: Optional[int] = None, current_voter_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Voter)
    if ward is not None:
        query = query.filter(Voter.ward_no == ward)
        
    total = query.count()
    completed = query.filter(Voter.expected_party != None).count()
    
    stats = {
        "total": total,
        "completed": completed,
        "ward": ward
    }

    if current_voter_id is not None and ward is not None:
        # Calculate rank of current voter in this ward
        current_index = db.query(Voter).filter(
            Voter.ward_no == ward, 
            Voter.voter_id <= current_voter_id
        ).count()
        stats["current_index"] = current_index

    return stats

# Legacy endpoint support (optional, can keep for backward compatibility if needed)
@app.put("/voters/update_legacy")
def update_voter_legacy(voter_id: int, party: str, db: Session = Depends(get_db)):
    voter = db.query(Voter).filter(Voter.voter_id == voter_id).first()
    if not voter:
        raise HTTPException(status_code=404, detail="Voter not found")
    voter.expected_party = party
    db.commit()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
