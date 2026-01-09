import urllib.parse
from fastapi import FastAPI, Depends, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Column, Integer, String, asc, desc, ForeignKey, DateTime, func
from sqlalchemy.orm import Session, relationship
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

# Import robust database setup
from database import engine, SessionLocal, Base, get_db

# --- 1. VOTER MASTER (Production Data - Read Only) ---
class VoterMaster(Base):
    __tablename__ = "voters"  # Existing table
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
    # Master data should typically NOT maintain dynamic survey fields, 
    # but we keep them here as they exist in legacy schema.
    # In the new architecture, these will be ignored/read-only in this table.
    expected_party = Column(String, nullable=True)
    occupation = Column(String, nullable=True)
    religion = Column(String, nullable=True)
    caste = Column(String, nullable=True)
    sub_caste = Column(String, nullable=True)
    mobile_no = Column(String, nullable=True)
    voter_status = Column(String, default="AVAILABLE") 

# --- 2. SURVEY META DATA ---
class Survey(Base):
    __tablename__ = "surveys"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    scope_type = Column(String) # e.g., "WARD", "VILLAGE"
    scope_value = Column(String) 
    status = Column(String, default="CREATED") # CREATED, ACTIVE, COMPLETED, ARCHIVED
    survey_code = Column(String, unique=True) # WARD-01-TEST-2026...
    survey_type = Column(String, default="TEST") # TEST, FINAL, EXIT_POLL
    created_at = Column(DateTime, default=datetime.utcnow)
    
    @property
    def is_locked(self):
        return self.status in ["COMPLETED", "ARCHIVED"]

# --- 3. SURVEY SNAPSHOT (Writable Survey Data) ---
class SurveyVoter(Base):
    __tablename__ = "survey_voters"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    survey_id = Column(Integer, ForeignKey("surveys.id"), index=True)
    master_voter_id = Column(Integer, ForeignKey("voters.voter_id"), index=True)
    snapshot_created_at = Column(DateTime, default=datetime.utcnow) # Audit timestamp
    
    # Copied Identity Fields (for search/display performance)
    voter_name = Column(String)
    surname = Column(String)
    ward_no = Column(Integer)
    house_no = Column(String)
    age = Column(Integer)
    gender = Column(String)
    relation_name = Column(String)
    
    # Writable Survey Fields
    expected_party = Column(String, nullable=True)
    occupation = Column(String, nullable=True)
    religion = Column(String, nullable=True)
    caste = Column(String, nullable=True)
    sub_caste = Column(String, nullable=True)
    mobile_no = Column(String, nullable=True)
    voter_status = Column(String, default="AVAILABLE")

# --- 4. SURVEYOR REQUESTS (For Approval Workflow) ---
class SurveyorRequest(Base):
    __tablename__ = "surveyor_requests"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    mobile_no = Column(String)
    device_id = Column(String, nullable=True) # To uniquely identify app installation
    status = Column(String, default="PENDING") # PENDING, APPROVED, REJECTED
    created_at = Column(DateTime, default=datetime.utcnow)

# Backward compatibility alias - Delete this once migration is complete
Voter = VoterMaster

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

# Serve Static Files (Web Dashboard)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# --- Pydantic Models for Request Body ---
class VoterUpdate(BaseModel):
    voter_id: int
    survey_id: int # REQUIRED NOW
    party: Optional[str] = None
    occupation: Optional[str] = None
    religion: Optional[str] = None
    caste: Optional[str] = None
    sub_caste: Optional[str] = None
    mobile_no: Optional[str] = None
    voter_status: Optional[str] = None

class SurveyCreate(BaseModel):
    name: str
    scope_type: str 
    scope_value: str
    survey_type: str = "TEST" # Default to TEST

@app.get("/")
def read_root():
    return {"status": "online", "message": "Voter API is running", "docs_url": "/docs"}

@app.post("/surveys/create")
def create_survey(survey_data: SurveyCreate, db: Session = Depends(get_db)):
    # 0. Generate Survey Code
    # Format: SCOPE-VALUE-TYPE-DATE (e.g., WARD-01-TEST-20260109)
    date_str = datetime.utcnow().strftime("%Y%m%d")
    code = f"{survey_data.scope_type}-{survey_data.scope_value}-{survey_data.survey_type}-{date_str}"
    
    # Check uniqueness (simple append if exists)
    existing = db.query(Survey).filter(Survey.survey_code == code).first()
    if existing:
        code = f"{code}-{datetime.utcnow().strftime('%H%M%S')}"

    # 1. Create Survey Record
    new_survey = Survey(
        name=survey_data.name,
        scope_type=survey_data.scope_type,
        scope_value=survey_data.scope_value,
        status="ACTIVE", # Auto-activate for now, user can change logic if CREATED state needed
        survey_code=code,
        survey_type=survey_data.survey_type
    )
    db.add(new_survey)
    db.commit()
    db.refresh(new_survey)

    # 2. Bulk Copy Logic (Snapshot)
    copied_count = 0
    if survey_data.scope_type == "WARD":
        try:
            ward_num = int(survey_data.scope_value)
            masters = db.query(VoterMaster).filter(VoterMaster.ward_no == ward_num).all()

            survey_voters = []
            now = datetime.utcnow()
            for v in masters:
                sv = SurveyVoter(
                    survey_id=new_survey.id,
                    master_voter_id=v.voter_id,
                    voter_name=v.voter_name,
                    surname=v.surname,
                    ward_no=v.ward_no,
                    house_no=v.house_no,
                    age=v.age,
                    gender=v.gender,
                    relation_name=v.relation_name,
                    # Initialize blank survey data
                    expected_party=None,
                    occupation=None,
                    voter_status="AVAILABLE",
                    snapshot_created_at=now
                )
                survey_voters.append(sv)

            if survey_voters:
                db.add_all(survey_voters)
                db.commit()
                copied_count = len(survey_voters)

        except ValueError:
            raise HTTPException(status_code=400, detail="Scope value must be an integer for WARD type")

    return {
        "status": "success",
        "survey_id": new_survey.id,
        "survey_code": new_survey.survey_code,
        "message": f"Survey created with {copied_count} voters in snapshot."
    }

@app.get("/surveys/active")
def get_active_surveys(db: Session = Depends(get_db)):
    surveys = db.query(Survey).filter(Survey.status == "ACTIVE").order_by(desc(Survey.created_at)).all()
    return surveys

@app.get("/voters/search", response_model=List[dict])
def search_voters(query: str, survey_id: int, db: Session = Depends(get_db)):
    # Search in the active Survey Snapshot
    voters = db.query(SurveyVoter).filter(
        SurveyVoter.survey_id == survey_id,
        (SurveyVoter.voter_name.ilike(f"%{query}%")) | 
        (SurveyVoter.surname.ilike(f"%{query}%"))
    ).limit(50).all()
    
    # Return formatted data (same structure as before but from Snapshot)
    return [
        {
            "voter_id": v.master_voter_id, # Return MASTER ID for reference
            "snapshot_id": v.id, # Keep track of snapshot ID if needed internaly
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
def get_next_voter(survey_id: int, current_id: int = 0, db: Session = Depends(get_db)):
    # Use Master ID for sequential navigation, but fetch from Snapshot
    # We assume snapshots are ordered by master_voter_id as they were inserted that way
    
    voter = db.query(SurveyVoter).filter(
        SurveyVoter.survey_id == survey_id,
        SurveyVoter.master_voter_id > current_id
    ).order_by(asc(SurveyVoter.master_voter_id)).first()
    
    if not voter:
        return {"status": "finished", "data": None}
        
    return {
        "status": "success",
        "data": {
            "voter_id": voter.master_voter_id,
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
            "mobile_no": voter.mobile_no,
            "voter_status": voter.voter_status
        }
    }

@app.get("/voters/previous")
def get_previous_voter(survey_id: int, current_id: int, db: Session = Depends(get_db)):
    voter = db.query(SurveyVoter).filter(
        SurveyVoter.survey_id == survey_id,
        SurveyVoter.master_voter_id < current_id
    ).order_by(desc(SurveyVoter.master_voter_id)).first()
    
    if not voter:
        return {"status": "finished", "data": None}
        
    return {
        "status": "success",
        "data": {
            "voter_id": voter.master_voter_id,
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
            "mobile_no": voter.mobile_no,
            "voter_status": voter.voter_status
        }
    }



@app.put("/voters/update")
def update_voter_data(data: VoterUpdate, db: Session = Depends(get_db)):
    # GUARD: Context Lock
    survey = db.query(Survey).filter(Survey.id == data.survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    if survey.is_locked:
        raise HTTPException(status_code=403, detail="Survey is LOCKED (Completed or Archived). No updates allowed.")
    
    # Update Survey Snapshot
    voter = db.query(SurveyVoter).filter(
        SurveyVoter.survey_id == data.survey_id,
        SurveyVoter.master_voter_id == data.voter_id
    ).first()
    
    if not voter:
        raise HTTPException(status_code=404, detail="Voter not found in this survey")
        
    # Update fields if provided
    if data.voter_status is not None: 
        voter.voter_status = data.voter_status
        # STRICT RULE: If status is not AVAILABLE, wipe all survey data
        if data.voter_status != "AVAILABLE":
            voter.expected_party = None
            voter.occupation = None
            voter.religion = None
            voter.caste = None
            voter.sub_caste = None
            voter.mobile_no = None
    
    is_available = (data.voter_status == "AVAILABLE") if data.voter_status is not None else (voter.voter_status == "AVAILABLE")
    
    if is_available:
        if data.party is not None: voter.expected_party = data.party
        if data.occupation is not None: voter.occupation = data.occupation
        if data.religion is not None: voter.religion = data.religion
        if data.caste is not None: voter.caste = data.caste
        if data.sub_caste is not None: voter.sub_caste = data.sub_caste
        if data.mobile_no is not None: voter.mobile_no = data.mobile_no
    
    db.commit()
    return {"status": "success"}

@app.get("/voters/stats")
def get_voter_stats(survey_id: int, ward: Optional[int] = None, current_voter_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(SurveyVoter).filter(SurveyVoter.survey_id == survey_id)
    if ward is not None:
        query = query.filter(SurveyVoter.ward_no == ward)
        
    total = query.count()
    completed = query.filter(SurveyVoter.expected_party != None).count()
    
    stats = {
        "total": total,
        "completed": completed,
        "ward": ward
    }

    if current_voter_id is not None and ward is not None:
        # Calculate rank of current voter in this ward
        current_index = db.query(SurveyVoter).filter(
            SurveyVoter.survey_id == survey_id,
            SurveyVoter.ward_no == ward, 
            SurveyVoter.master_voter_id <= current_voter_id
        ).count()
        stats["current_index"] = current_index

    return stats

@app.get("/voters/{voter_id}")
def get_voter_by_id(voter_id: int, survey_id: int, db: Session = Depends(get_db)):
    voter = db.query(SurveyVoter).filter(
        SurveyVoter.survey_id == survey_id,
        SurveyVoter.master_voter_id == voter_id
    ).first()
    
    if not voter:
        raise HTTPException(status_code=404, detail="Voter not found in this survey")
        
    return {
        "status": "success",
        "data": {
            "voter_id": voter.master_voter_id,
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
            "mobile_no": voter.mobile_no,
            "voter_status": voter.voter_status
        }
    }

# Legacy endpoint support (optional, can keep for backward compatibility if needed)
@app.put("/voters/update_legacy")
def update_voter_legacy(voter_id: int, party: str, db: Session = Depends(get_db)):
    voter = db.query(Voter).filter(Voter.voter_id == voter_id).first()
    if not voter:
        raise HTTPException(status_code=404, detail="Voter not found")
    voter.expected_party = party
    db.commit()
    return {"status": "success"}

# --- DASHBOARD ENDPOINTS ---

@app.get("/dashboard/summary")
def get_dashboard_summary(survey_id: int, db: Session = Depends(get_db)):
    # 1. Total Voters in Survey
    total_voters = db.query(SurveyVoter).filter(SurveyVoter.survey_id == survey_id).count()
    
    # 2. Completed Surveys (Any Status + Survey Data)
    # Actually, completion is usually defined by having collected data (e.g. expected_party)
    completed_surveys = db.query(SurveyVoter).filter(
        SurveyVoter.survey_id == survey_id,
        SurveyVoter.expected_party != None
    ).count()
    
    # 3. Effective Voters (Available only)
    effective_voters = db.query(SurveyVoter).filter(
        SurveyVoter.survey_id == survey_id,
        SurveyVoter.voter_status == "AVAILABLE"
    ).count()
    
    # 4. Ward Count (Distinct Wards)
    # SQLite distinct count syntax might need specific func usage or python len
    # using simple python distinct for compatibility/ease
    wards = db.query(SurveyVoter.ward_no).filter(SurveyVoter.survey_id == survey_id).distinct().all()
    ward_count = len(wards)
    
    completion_percentage = 0
    if effective_voters > 0:
        completion_percentage = round((completed_surveys / effective_voters) * 100, 1)

    return {
        "status": "success",
        "data": {
            "total_voters": total_voters,
            "effective_voters": effective_voters,
            "completed_surveys": completed_surveys,
            "completion_percentage": completion_percentage,
            "ward_count": ward_count
        }
    }

@app.get("/dashboard/progress")
def get_dashboard_progress(survey_id: int, db: Session = Depends(get_db)):
    # Return list of stats per ward
    # We can use raw SQL for aggregation or python loop if dataset is small (<100k)
    # Given requirements, simple python loop over wards is robust enough for now
    
    # Get all distinct wards
    wards_res = db.query(SurveyVoter.ward_no).filter(SurveyVoter.survey_id == survey_id).distinct().order_by(SurveyVoter.ward_no).all()
    wards = [w[0] for w in wards_res]
    
    progress_data = []
    
    for ward in wards:
        w_total = db.query(SurveyVoter).filter(SurveyVoter.survey_id == survey_id, SurveyVoter.ward_no == ward).count()
        w_completed = db.query(SurveyVoter).filter(SurveyVoter.survey_id == survey_id, SurveyVoter.ward_no == ward, SurveyVoter.expected_party != None).count()
        w_effective = db.query(SurveyVoter).filter(SurveyVoter.survey_id == survey_id, SurveyVoter.ward_no == ward, SurveyVoter.voter_status == "AVAILABLE").count()
        
        status = "IN_PROGRESS"
        if w_effective > 0 and w_completed >= w_effective:
            status = "COMPLETED"
        elif w_completed == 0:
            status = "PENDING"
            
        progress_data.append({
            "ward_no": ward,
            "total_voters": w_total,
            "effective_voters": w_effective,
            "completed": w_completed,
            "status": status,
            "surveyor": "Unassigned" # Placeholder for Phase 4 (Assignment)
        })
        
    return {
        "status": "success",
        "data": progress_data
    }

@app.get("/dashboard/analytics")
def get_dashboard_analytics(survey_id: int, db: Session = Depends(get_db)):
    # Access Analytics: Party Vote Share based on EFFECTIVE VOTERS only
    
    # 1. Total Effective Voters who have voted (Expected Party is not None AND Status is AVAILABLE)
    # Note: If status != AVAILABLE, we wiped party data anyway, so checking party != None serves same purpose mostly,
    # but explicitly checking status is safer.
    
    results = db.query(
        SurveyVoter.expected_party, 
        func.count(SurveyVoter.expected_party)
    ).filter(
        SurveyVoter.survey_id == survey_id,
        SurveyVoter.voter_status == "AVAILABLE",
        SurveyVoter.expected_party != None
    ).group_by(SurveyVoter.expected_party).all()
    
    analytics_data = []
    total_polled = 0
    for party, count in results:
        analytics_data.append({"party": party, "count": count})
        total_polled += count
        
    # Calculate percentages
    final_data = []
    for item in analytics_data:
        percent = 0
        if total_polled > 0:
            percent = round((item["count"] / total_polled) * 100, 1)
        
        final_data.append({
            "party": item["party"],
            "count": item["count"],
            "percentage": percent
        })
        
    return {
        "status": "success",
        "total_polled": total_polled,
        "data": final_data
    }

    return {
        "status": "success",
        "total_polled": total_polled,
        "data": final_data
    }

@app.get("/dashboard/approvals")
def get_pending_approvals(db: Session = Depends(get_db)):
    requests = db.query(SurveyorRequest).filter(SurveyorRequest.status == "PENDING").all()
    return [{"id": r.id, "name": r.name, "mobile": r.mobile_no, "date": r.created_at} for r in requests]

@app.post("/dashboard/approve")
def approve_surveyor(request_id: int = Body(...), action: str = Body(...), db: Session = Depends(get_db)):
    # Action: APPROVED / REJECTED
    req = db.query(SurveyorRequest).filter(SurveyorRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if action not in ["APPROVED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    req.status = action
    db.commit()
    return {"status": "success"}

# --- PUBLIC ENDPOINT FOR APP REGISTRATION (To feed into approvals) ---
@app.post("/register/surveyor")
def register_surveyor(name: str = Body(...), mobile: str = Body(...), device_id: str = Body(None), db: Session = Depends(get_db)):
    # Check if already exists
    existing = db.query(SurveyorRequest).filter(SurveyorRequest.mobile_no == mobile).first()
    if existing:
        return {"status": "exists", "id": existing.id, "current_status": existing.status}
        
    new_req = SurveyorRequest(name=name, mobile_no=mobile, device_id=device_id)
    db.add(new_req)
    db.commit()
    return {"status": "success", "id": new_req.id, "current_status": "PENDING"}

@app.get("/register/status/{request_id}")
def check_registration_status(request_id: int, db: Session = Depends(get_db)):
    req = db.query(SurveyorRequest).filter(SurveyorRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"status": "success", "approval_status": req.status}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
