import urllib.parse
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Body, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Column, Integer, String, asc, desc, ForeignKey, DateTime, func
from sqlalchemy.orm import Session, relationship
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

# --- CONFIGURATION ---
MAIN_VERSION = "v19.20 (Fix)" # Rebuild Trigger: AppName Error
EXPECTED_FRONTEND_VERSION = "v19.20"

# Import robust database setup
from database import engine, SessionLocal, Base, get_db

# --- 0. GEO MASTER TABLES (Hierarchy) ---
class DistrictMaster(Base):
    __tablename__ = "district_master"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, index=True)

class MandalMaster(Base):
    __tablename__ = "mandal_master"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)
    district_id = Column(Integer, ForeignKey("district_master.id"))

class VillageMaster(Base):
    __tablename__ = "village_master"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)
    mandal_id = Column(Integer, ForeignKey("mandal_master.id"))

class WardMaster(Base):
    __tablename__ = "ward_master"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    village_id = Column(Integer, ForeignKey("village_master.id"))

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
    
    # Geo-Scope (Full Hierarchy)
    district = Column(String)
    mandal = Column(String)
    village = Column(String)
    ward = Column(String)

    scope_type = Column(String) # e.g., "DISTRICT", "MANDAL", "VILLAGE" (High level intent)
    scope_value = Column(String) # Legacy support (e.g. Ward ID)
    scope_config = Column(String, nullable=True) # JSON: {district: 1, mandals: "ALL", villages: [1,2]}
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
    
    # Requested Location (Full Hierarchy)
    district_name = Column(String)
    mandal_name = Column(String)
    village_name = Column(String)
    ward_no = Column(String)

    status = Column(String, default="PENDING") # PENDING, APPROVED, REJECTED
    role = Column(String, default="SURVEYOR") # SURVEYOR, COORDINATOR
    assigned_village_id = Column(Integer, nullable=True) # Scope for Coordinator
    
    created_at = Column(DateTime, default=datetime.utcnow)

# --- 5. SURVEY ASSIGNMENTS (Access Control) ---
class SurveyAssignment(Base):
    __tablename__ = "survey_assignments"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), index=True)
    surveyor_id = Column(Integer, ForeignKey("surveyor_requests.id"), index=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="ACTIVE") # ACTIVE, REVOKED

# Backward compatibility alias - Delete this once migration is complete
Voter = VoterMaster

# Create the table in Google Cloud if it doesn't exist


# Create the table in Google Cloud if it doesn't exist
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Helper for mobile sanitization
def clean_mobile(mobile: str) -> str:
    if not mobile:
        return ""
    return mobile.replace("+91", "").replace(" ", "").replace("-", "").strip()

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

# STARTUP: Auto-Seed Database if Empty
@app.on_event("startup")
def startup_event():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Check if we need to seed
    db = SessionLocal()
    try:
        count = db.query(VoterMaster).count()
        if count == 0:
            print("[STARTUP] Database appears empty. Running seeder...")
            from seed_db import seed_data
            seed_data()
            print("[STARTUP] Seeding complete.")
        else:
            print(f"[STARTUP] Database has {count} voters. Skipping seed.")
        
        # --- PHASE 1: GEO SEEDING (Always Check/Run) ---
        print("[STARTUP] Checking Master Location Data...")
        if db.query(DistrictMaster).count() == 0:
             print("[STARTUP] District Table is Empty. Seeding Full Geo Data...")
             from seed_geo import seed_geo_data
             seed_geo_data()
             print("[STARTUP] Geo Seeding Complete.")

        # --- PHASE 4.2: AUTO-MIGRATE (Schema Updates) ---
        print("[STARTUP] Checking Phase 4.2 Schema...")
        try:
             from migrate_phase4_2 import migrate
             migrate()
        except Exception as e:
             print(f"[STARTUP] Migration Check: {e}")

        # --- PHASE 5: ASSIGNMENTS (Schema) ---
        print("[STARTUP] Checking Phase 5 Schema (Assignments)...")
        try:
             from migrate_phase5 import migrate_phase5
             migrate_phase5()
        except Exception as e:
             print(f"[STARTUP] Phase 5 Migration Error: {e}")

        # --- PHASE 4.2: SEED DEMO COORDINATOR (Auto-Fix) ---
        # Ensure the test user 9999999999 exists for the User to log in
        demo_coord = db.query(SurveyorRequest).filter(SurveyorRequest.mobile_no == '9999999999').first()
        if not demo_coord:
            print("[STARTUP] Creating Demo Coordinator (9999999999)...")
            new_coord = SurveyorRequest(
                name="Demo Coordinator",
                mobile_no="9999999999",
                district_name="Yadadri Bhuvanagiri",
                mandal_name="Choutuppal",
                village_name="Aregudem",
                ward_no="0",
                role="COORDINATOR",
                assigned_village_id=1,
                status="APPROVED", # Pre-approved
                device_id="auto-seed"
            )
            db.add(new_coord)
            db.commit()
            print("[STARTUP] Demo Coordinator Created!")
        else:
            print("[STARTUP] Demo Coordinator already exists.")

        print("[STARTUP] v19.14 Startup Checks Complete.")
    except Exception as e:
        print(f"[STARTUP] Error checking/seeding DB: {e}")
    finally:
        db.close()

# --- MANUAL SURVEY CREATION ENDPOINT (For Dashboard) ---
# [DELETED] Duplicate create_survey and SurveyCreate model removed to fix logic conflict.
# The correct implementation is further down with security checks and rollback logic.

# --- VERSION HANDSHAKE ---
@app.get("/version")
def get_version():
    return {
        "version": "v19.14",
        "env": "PROD",
        "last_updated": datetime.utcnow().isoformat()
    }

@app.post("/admin/reset_db")
def reset_database(x_admin_token: Optional[str] = Header(None)):
    if x_admin_token != "admin-secret-123":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    from seed_db import seed_data
    seed_data()
    return {"status": "success", "message": "Database Reset and Seeded from CSV."}

@app.post("/admin/seed_geo")
def seed_geo_endpoint(x_admin_token: Optional[str] = Header(None)):
    if x_admin_token != "admin-secret-123":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    try:
        from seed_geo import seed_geo_data
        seed_geo_data()
        
        # Verify
        db = SessionLocal()
        d_count = db.query(DistrictMaster).count()
        m_count = db.query(MandalMaster).count()
        v_count = db.query(VillageMaster).count()
        db.close()
        
        return {
            "status": "success", 
            "message": f"Seeding Run Complete. DB Now Has: {d_count} Districts, {m_count} Mandals, {v_count} Villages.",
            "counts": {"districts": d_count}
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/debug/geo")
def debug_geo_data(db: Session = Depends(get_db)):
    d_count = db.query(DistrictMaster).count()
    districts = db.query(DistrictMaster).limit(5).all()
    d_names = [d.name for d in districts]
    
    return {
        "status": "online",
        "district_count": d_count,
        "sample_districts": d_names,
        "db_info": str(engine.url)
    }

@app.get("/debug/dump")
def debug_dump_data(db: Session = Depends(get_db)):
    surveys = db.query(Survey).all()
    s_data = [{
        "id": s.id, "name": s.name, 
        "scope": s.scope_type, "val": s.scope_value,
        "d": s.district, "m": s.mandal, "v": s.village 
    } for s in surveys]
    
    coordinators = db.query(SurveyorRequest).filter(SurveyorRequest.role == "COORDINATOR").all()
    c_data = [{
        "mobile": c.mobile_no, "name": c.name,
        "d": c.district_name, "m": c.mandal_name, "v": c.village_name
    } for c in coordinators]
    
    return {"surveys": s_data, "coordinators": c_data}

# Serve Flutter Mobile App (Web Version)
from fastapi.responses import FileResponse

# Explicitly serve index.html with NO-CACHE headers to break stale service workers

@app.get("/app/")
@app.get("/app/index.html")
async def serve_app_index():
    return FileResponse(
        "static/flutter_app/index.html", 
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate", 
            "Pragma": "no-cache", 
            "Expires": "0"
        }
    )

app.mount("/app", StaticFiles(directory="static/flutter_app", html=True), name="flutter_app")

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

import json

@app.post("/surveys/create")
def create_survey(
    name: str = Body(...), 
    scope_type: str = Body(...), # "DISTRICT", "MANDAL", "VILLAGE" (Primary Intent)
    district_id: int = Body(...),
    mandal_ids: str = Body(...), # "ALL" or JSON list "[1, 2]"
    village_ids: str = Body(...), # "ALL" or JSON list "[10, 11]"
    survey_type: str = Body("TEST"),
    x_admin_token: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    # --- SECURITY GUARD ---
    if x_admin_token != "admin-secret-123":
        raise HTTPException(status_code=403, detail="Forbidden: Admin Access Required")
    # ----------------------

    # 1. Resolve Geographic Scope (Villages)
    target_village_ids = []
    
    # Parse inputs (Frontend sends stringified JSON or "ALL")
    try:
        req_mandals = mandal_ids if mandal_ids == "ALL" else json.loads(mandal_ids)
        req_villages = village_ids if village_ids == "ALL" else json.loads(village_ids)
    except:
        raise HTTPException(status_code=400, detail="Invalid Mandal/Village ID format")

    # A. Get Mandals
    final_mandal_ids = []
    if req_mandals == "ALL":
        # Get all mandals in district
        mandals = db.query(MandalMaster).filter(MandalMaster.district_id == district_id).all()
        final_mandal_ids = [m.id for m in mandals]
    else:
        final_mandal_ids = [int(m) for m in req_mandals]

    # B. Get Villages
    if req_villages == "ALL":
        # Get all villages in selected mandals
        villages = db.query(VillageMaster).filter(VillageMaster.mandal_id.in_(final_mandal_ids)).all()
        target_village_ids = [v.id for v in villages]
    else:
        target_village_ids = [int(v) for v in req_villages]

    if not target_village_ids:
         raise HTTPException(status_code=400, detail="Scope resolution failed: No villages found for selection.")

    # 2. Derive Wards (Auto-Included)
    # Get all wards in these villages
    wards = db.query(WardMaster).filter(WardMaster.village_id.in_(target_village_ids)).all()
    # Logic to normalize names? "Ward 1" vs "1". 
    # For now, we assume we need to match VoterMaster.ward_no using simple parsing or direct mapping if possible.
    # Since VoterMaster has INT ward_no, we extract integers.
    target_ward_nums = []
    for w in wards:
        try:
            # Extract number from "Ward 5", "5", "Ward-5"
            num_str = ''.join(filter(str.isdigit, w.name))
            if num_str:
                target_ward_nums.append(int(num_str))
        except: pass
    
    target_ward_nums = list(set(target_ward_nums)) # Deduplicate
    
    # 3. Create Survey Record
    # Generate Code: TYPE-DIST-DATE
    date_str = datetime.utcnow().strftime("%Y%m%d")
    code = f"{scope_type}-{district_id}-{survey_type}-{date_str}"
    
    # Uniqueness check
    existing = db.query(Survey).filter(Survey.survey_code == code).first()
    if existing:
        code = f"{code}-{datetime.utcnow().strftime('%H%M%S')}"

    # Store Scope Config
    config_json = json.dumps({
        "district_id": district_id,
        "mandal_ids": req_mandals,
        "village_ids": req_villages,
        "derived_wards_count": len(target_ward_nums),
        "derived_villages_count": len(target_village_ids)
    })

    new_survey = Survey(
        name=name,
        scope_type=scope_type,
        scope_value=str(district_id), # High level reference
        scope_config=config_json,
        status="ACTIVE", 
        survey_code=code,
        survey_type=survey_type
    )
    db.add(new_survey)
    db.commit()
    db.refresh(new_survey)

    # 4. Snapshot Logic (Bulk Copy)
    copied_count = 0
    if target_ward_nums:
        # We need to be careful: VoterMaster.ward_no is unique ONLY within a Village usually, 
        # but in our simplistic schema, we might risk cross-village collision if we only filter by ward_no.
        # ideally we need Village ID in VoterMaster. 
        # CAUTION: If VoterMaster doesn't have Village ID, relying on Ward No 1 is dangerous if multiple villages have Ward 1.
        # User confirmed "Aregudem village has 10 wards".
        # IF VoterMaster relies only on `ward_no`, we assume the User's csv data was global?
        # Actually, without VillageId in VoterMaster, we cannot distinguish Ward 1 of Village A from Ward 1 of Village B.
        # FOR THIS PILOT/PHASE: We proceed with pure Ward Number matching as per current schema, 
        # BUT this is a known risk unless VoterMaster has Unique Ward IDs or Village association.
        # Let's assume for now we filter broadly.
        
        # Performance: Chunking might be needed for huge datasets, but focusing on correctness first.
        masters = db.query(VoterMaster).filter(VoterMaster.ward_no.in_(target_ward_nums)).all()
        
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
    
    return {
        "status": "success",
        "survey_id": new_survey.id,
        "survey_code": new_survey.survey_code,
        "message": f"Survey created covering {len(target_village_ids)} villages and {len(target_ward_nums)} wards. Snapshot size: {copied_count}"
    }

@app.get("/surveys/active")
def get_active_surveys(
    mobile_no: Optional[str] = None, 
    village_filter: Optional[str] = None, 
    mandal_filter: Optional[str] = None,
    district_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    from sqlalchemy import or_, and_
    query = db.query(Survey).filter(Survey.status == "ACTIVE")
    
    # FILTER 1: Coordinator Scope (Hierarchical Match)
    # detailed logic: Show surveys if they match District OR Mandal OR Village
    if village_filter or mandal_filter or district_filter:
        print(f"[DEBUG] Filtering surveys for Loc: {district_filter} -> {mandal_filter} -> {village_filter}")
        
        conditions = []
        if district_filter:
            # Matches District Level Survey
            conditions.append(and_(Survey.scope_type=="DISTRICT", func.lower(Survey.district) == district_filter.lower().strip()))
        if mandal_filter:
            # Matches Mandal Level Survey
            conditions.append(and_(Survey.scope_type=="MANDAL", func.lower(Survey.mandal) == mandal_filter.lower().strip()))
        if village_filter:
            # Matches Village Level Survey (Target specific village)
            conditions.append(func.lower(Survey.village) == village_filter.lower().strip())

        if conditions:
            query = query.filter(or_(*conditions))

    # FILTER 2: Mobile App Surveyor (Show only assigned surveys)
    elif mobile_no:
        mobile_no = clean_mobile(mobile_no)
        print(f"[DEBUG] Filtering surveys for mobile: {mobile_no}")
        # Find surveyor by mobile
        surveyor = db.query(SurveyorRequest).filter(SurveyorRequest.mobile_no == mobile_no, SurveyorRequest.status == "APPROVED").first()
        if not surveyor:
            print(f"[DEBUG] No approved surveyor found for {mobile_no}")
            return [] # No approved surveyor found, return empty list (Authentication failed conceptually)
            
        # Join with assignments
        query = query.join(SurveyAssignment, Survey.id == SurveyAssignment.survey_id)\
                     .filter(SurveyAssignment.surveyor_id == surveyor.id, SurveyAssignment.status == "ACTIVE")
    else:
        print(f"[DEBUG] No filters provided. Returning ALL active surveys (Admin view).")
    
    surveys = query.order_by(desc(Survey.created_at)).all()
    # print(f"[DEBUG] Found {len(surveys)} surveys.")
    return surveys
    
@app.delete("/surveys/{survey_id}")
def delete_survey(survey_id: int, x_admin_token: Optional[str] = Header(None), db: Session = Depends(get_db)):
    # --- SECURITY GUARD ---
    if x_admin_token != "admin-secret-123":
        raise HTTPException(status_code=403, detail="Forbidden: Admin Access Required")
    # ----------------------
    
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
        
    # Validation Rules
    if survey.status in ["COMPLETED", "ARCHIVED"]:
        raise HTTPException(status_code=400, detail="Cannot delete COMPLETED or ARCHIVED surveys. Please Archive only.")
        
    try:
        # Cascade Delete (Manually to be safe with SQLite fk support)
        # 1. Delete Assignments
        db.query(SurveyAssignment).filter(SurveyAssignment.survey_id == survey_id).delete()
        
        # 2. Delete Voters (Snapshot)
        db.query(SurveyVoter).filter(SurveyVoter.survey_id == survey_id).delete()
        
        # 3. Delete Survey
        db.delete(survey)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
        
    return {"status": "success", "message": f"Survey '{survey.name}' deleted."}
    
@app.post("/assignments/create")
def create_assignment(survey_id: int = Body(...), surveyor_id: int = Body(...), db: Session = Depends(get_db)):
    # Check if exists
    existing = db.query(SurveyAssignment).filter(
        SurveyAssignment.survey_id == survey_id,
        SurveyAssignment.surveyor_id == surveyor_id,
        SurveyAssignment.status == "ACTIVE"
    ).first()
    
    if existing:
        return {"status": "exists", "message": "Already assigned"}
        
    new_assign = SurveyAssignment(survey_id=survey_id, surveyor_id=surveyor_id)
    db.add(new_assign)
    db.commit()
    return {"status": "success"}

@app.get("/assignments/list")
def list_assignments(survey_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(SurveyAssignment).filter(SurveyAssignment.status == "ACTIVE")
    if survey_id:
        query = query.filter(SurveyAssignment.survey_id == survey_id)
        
    assignments = query.all()
    # Enrich with names
    results = []
    for a in assignments:
        s_req = db.query(SurveyorRequest).filter(SurveyorRequest.id == a.surveyor_id).first()
        survey = db.query(Survey).filter(Survey.id == a.survey_id).first()
        if s_req and survey:
            results.append({
                "id": a.id,
                "survey_name": survey.name,
                "surveyor_name": s_req.name,
                "surveyor_mobile": s_req.mobile_no,
                "assigned_at": a.assigned_at
            })
    return results

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
def get_next_voter(survey_id: int, current_id: int = 0, skip_completed: bool = True, db: Session = Depends(get_db)):
    # Use Master ID for sequential navigation, but fetch from Snapshot
    # If skip_completed is True, we only fetch voters where expected_party IS NULL
    
    query = db.query(SurveyVoter).filter(
        SurveyVoter.survey_id == survey_id,
        SurveyVoter.master_voter_id > current_id
    )

    if skip_completed:
        # Also skip statuses that are decidedly handled (like Death, Out of Station etc if desired, 
        # but typically "Completed" means data entered).
        # Assuming "expected_party" presence implies data was collected.
        query = query.filter(SurveyVoter.expected_party == None)

    voter = query.order_by(asc(SurveyVoter.master_voter_id)).first()
    
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
def get_previous_voter(survey_id: int, current_id: int, skip_completed: bool = True, db: Session = Depends(get_db)):
    query = db.query(SurveyVoter).filter(
        SurveyVoter.survey_id == survey_id,
        SurveyVoter.master_voter_id < current_id
    )

    if skip_completed:
        query = query.filter(SurveyVoter.expected_party == None)

    voter = query.order_by(desc(SurveyVoter.master_voter_id)).first()
    
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
        
    # FIX: Update fields regardless of previous availability
    # We NO LONGER wipe data if status is not available.
    if data.voter_status is not None: 
        voter.voter_status = data.voter_status
    
    # Always update data fields if provided, to ensure we capture
    # info even if user is marked Out of Station / Death
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

@app.get("/dashboard/approvals")
def get_surveyor_requests(db: Session = Depends(get_db)):
    # Return ALL requests (Pending + History)
    requests = db.query(SurveyorRequest).order_by(desc(SurveyorRequest.created_at)).all()
    print(f"[DEBUG] Total Requests Found: {len(requests)}")
    # Fetch all surveys to map assignments (Optimization: Fetch all assignments)
    # For now, simplest approach:
    response_data = []
    for r in requests:
        assigned_survey_name = "-"
        if r.status == "APPROVED":
            # Check for existing assignment using SurveyorRequest.id
            assignment = db.query(SurveyAssignment).filter(SurveyAssignment.surveyor_id == r.id).first()
            if assignment:
                 survey = db.query(Survey).filter(Survey.id == assignment.survey_id).first()
                 if survey:
                     assigned_survey_name = survey.name

        response_data.append({
            "id": r.id, 
            "name": r.name, 
            "mobile": r.mobile_no, 
            "date": r.created_at,
            "status": r.status,
            "district": r.district_name,
            "mandal": r.mandal_name,
            "village": r.village_name,
            "ward": r.ward_no,
            "assigned_survey": assigned_survey_name
        })
    return response_data

# --- DELETE SURVEYOR FEATURE ---
@app.delete("/dashboard/surveyor/{surveyor_id}")
def delete_surveyor(surveyor_id: int, db: Session = Depends(get_db)):
    # 1. Find the surveyor
    surveyor = db.query(SurveyorRequest).filter(SurveyorRequest.id == surveyor_id).first()
    if not surveyor:
         return JSONResponse(status_code=404, content={"status": "fail", "message": "Surveyor not found"})
    
    # 2. Delete assignments first (Foreign Key Logic)
    db.query(SurveyAssignment).filter(SurveyAssignment.surveyor_id == surveyor_id).delete()
    
    # 3. Delete the surveyor
    db.delete(surveyor)
    db.commit()
    
    print(f"[DEBUG] Deleted surveyor ID {surveyor_id} and their assignments.")
    return {"status": "success", "message": "Surveyor deleted successfully"}

@app.post("/dashboard/approve")
def approve_surveyor(request_id: int = Body(...), action: str = Body(...), db: Session = Depends(get_db)):
    # Action: APPROVED / REJECTED
    req = db.query(SurveyorRequest).filter(SurveyorRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if action not in ["APPROVED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    # 1. Update Request Status
    req.status = action
    db.commit() # Commit status change first

    # 2. [CHANGED v19.1] REMOVED AUTO-ASSIGN LOGIC
    # User Explicitly Requested: "I dont want the automatic dummany survey creation part"
    # We now rely 100% on the Admin Dashboard to "Create Survey" and "Assign Surveyor".
    
    if action == "APPROVED":
        print(f"[APPROVE] Surveyor {req.name} Approved. Waiting for Manual Assignment.")

    return {"status": "success"}

# --- PUBLIC ENDPOINT FOR APP REGISTRATION (To feed into approvals) ---
@app.post("/register/surveyor")
def register_surveyor(
    name: str = Body(...), 
    mobile: str = Body(...), 
    device_id: str = Body(None),
    # Phase 1: Location Payload
    district_name: str = Body(None),
    mandal_name: str = Body(None),
    village_name: str = Body(None),
    ward_no: str = Body(None),
    # Phase 4.2: Coordinator Role
    role: str = Body("SURVEYOR"), 
    village_id: int = Body(None),
    db: Session = Depends(get_db)
):
    mobile = clean_mobile(mobile)
    print(f"[DEBUG] Registering {role}: Name={name}, Mobile={mobile}, Loc={district_name}/{mandal_name}/{village_name}/{ward_no}")
    
    # Check if already exists
    existing = db.query(SurveyorRequest).filter(SurveyorRequest.mobile_no == mobile).first()
    if existing:
        return {"status": "exists", "id": existing.id, "current_status": existing.status}
        
    new_req = SurveyorRequest(
        name=name, 
        mobile_no=mobile, 
        device_id=device_id,
        # Save Location
        district_name=district_name,
        mandal_name=mandal_name,
        village_name=village_name,
        ward_no=ward_no,
        # Role & Scope
        role=role.upper(),
        assigned_village_id=village_id
    )
    db.add(new_req)
    db.commit()
    return {"status": "success", "id": new_req.id, "current_status": "PENDING"}

class LoginRequest(BaseModel):
    mobile_no: str

@app.post("/auth/login")
def coordinator_login(login: LoginRequest, db: Session = Depends(get_db)):
    cleaned_mobile = clean_mobile(login.mobile_no)
    
    # Coordinator Login Check
    user = db.query(SurveyorRequest).filter(
        SurveyorRequest.mobile_no == cleaned_mobile,
        SurveyorRequest.role == "COORDINATOR",
        SurveyorRequest.status == "APPROVED"
    ).first()
    
    if not user:
        # Check if Admin (Hardcoded/Env for now for Mobile Login?)
        # Actually Admin login usually happens via token in header.
        # This endpoint is specific for Coordinators as per plan.
        raise HTTPException(status_code=401, detail="Invalid Mobile Number or Not Authorized as Coordinator")
    
    # Fetch Village Name for convenience
    village_name = user.village_name
    if not village_name and user.assigned_village_id:
         v = db.query(VillageMaster).filter(VillageMaster.id == user.assigned_village_id).first()
         if v: village_name = v.name

    return {
        "status": "success",
        "role": user.role,
        "name": user.name,
        "village_id": user.assigned_village_id,
        "village_name": user.village_name,
        "mandal_name": user.mandal_name,
        "district_name": user.district_name
    }

# --- LOCATION APIS (For Dropdowns) ---
@app.get("/locations/districts")
def get_districts(db: Session = Depends(get_db)):
    return db.query(DistrictMaster).all()

@app.get("/locations/mandals/{district_id}")
def get_mandals(district_id: int, db: Session = Depends(get_db)):
    return db.query(MandalMaster).filter(MandalMaster.district_id == district_id).all()

@app.get("/locations/villages/{mandal_id}")
def get_villages(mandal_id: int, db: Session = Depends(get_db)):
    return db.query(VillageMaster).filter(VillageMaster.mandal_id == mandal_id).all()

@app.get("/locations/wards/{village_id}")
def get_wards(village_id: int, db: Session = Depends(get_db)):
    return db.query(WardMaster).filter(WardMaster.village_id == village_id).all()



@app.get("/register/status/mobile")
def check_registration_status_by_mobile(mobile_no: str, db: Session = Depends(get_db)):
    mobile_no = clean_mobile(mobile_no)
    print(f"[DEBUG] CHECKING STATUS FOR MOBILE: {mobile_no}")
    req = db.query(SurveyorRequest).filter(SurveyorRequest.mobile_no == mobile_no).first()
    if not req:
        print(f"[DEBUG] STATUS CHECK: {mobile_no} -> NOT FOUND")
        raise HTTPException(status_code=404, detail="Request not found")
    
    print(f"[DEBUG] STATUS CHECK: {mobile_no} -> {req.status}")
    return {"status": "success", "approval_status": req.status, "surveyor_id": req.id}

@app.get("/register/status/{request_id}")
def check_registration_status(request_id: int, db: Session = Depends(get_db)):
    req = db.query(SurveyorRequest).filter(SurveyorRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"status": "success", "approval_status": req.status}

# --- FINAL FALLBACK: Serve Flutter App at Root ---
# This ensures that /flutter_bootstrap.js, /main.dart.js, etc. are found.
# API routes defined above take precedence.
app.mount("/flutter_app", StaticFiles(directory="static/flutter_app", html=True), name="flutter_app")

# --- 6. BULK UPLOAD API (Part 1 - Data Onboarding) ---
@app.post("/admin/upload-voters")
async def upload_voters(
    file: UploadFile = File(...),
    secret_key: str = Form(...),
    db: Session = Depends(get_db)
):
    # 1. Simple Auth Check (Phase 4 legacy style)
    if secret_key != "admin-secret-123":
         raise HTTPException(status_code=401, detail="Invalid Admin Secret")

    # 2. Parse CSV
    import csv
    import codecs
    
    try:
        # iterdecode allows reading the file stream as string directly
        csv_reader = csv.DictReader(codecs.iterdecode(file.file, 'utf-8'))
        
        voters_to_add = []
        count = 0
        
        # 3. Process Rows
        for row in csv_reader:
            # Basic validation
            if not row.get("voter_name") or not row.get("ward_no"):
                continue

            voter = VoterMaster(
                serial_no=int(row.get("serial_no", 0)),
                house_no=row.get("house_no", ""),
                voter_name=row.get("voter_name"),
                gender=row.get("gender", ""),
                age=int(row.get("age", 0)),
                relation_name=row.get("relation_name", ""),
                surname=row.get("surname", ""),
                ward_no=int(row.get("ward_no", 0)),
                family_id=row.get("family_id", ""),
                mobile_no=row.get("mobile_no", None)
            )
            voters_to_add.append(voter)
            count += 1
            
            # Batch Insert every 1000 records
            if len(voters_to_add) >= 1000:
                db.add_all(voters_to_add)
                db.commit()
                voters_to_add = []

        # Insert remaining
        if voters_to_add:
            db.add_all(voters_to_add)
            db.commit()
            
        return {"status": "success", "message": f"Successfully uploaded {count} voters"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Upload Failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
