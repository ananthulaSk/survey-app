import urllib.parse
import os
import threading
print("--- [DEBUG] STARTING MAIN.PY LOADING ---")
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Body, Query, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, Response, StreamingResponse # Added for Export & Root Redirect
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func, and_, or_
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict # Pydantic V2
from fastapi import Security
from fastapi.security import APIKeyHeader

# --- CONFIGURATION (Dynamic Versioning) ---
# --- CONFIGURATION (Static Versioning for Debug) ---
MAIN_VERSION = os.getenv("APP_VERSION", "v20.100")
EXPECTED_FRONTEND_VERSION = os.getenv("FRONTEND_VERSION", "v20.100")

# Import robust database setup
from database import engine, Base, get_db

# --- MODELS (Consolidated and Mapped) ---
# Note: Models are kept here for single-file visibility as per legacy structure,
# but we ensure they are imported correctly in all tasks.

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

class VoterMaster(Base):
    __tablename__ = "voters"
    voter_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    serial_no = Column(Integer)
    house_no = Column(String)
    voter_name = Column(String)
    gender = Column(String)
    age = Column(Integer)
    voter_id_no = Column(String, index=True, nullable=True) # Added for EPIC No
    relation_name = Column(String)
    surname = Column(String)
    ward_no = Column(Integer)
    family_id = Column(String)
    expected_party = Column(String, nullable=True)
    occupation = Column(String, nullable=True)
    religion = Column(String, nullable=True)
    caste = Column(String, nullable=True)
    sub_caste = Column(String, nullable=True)
    mobile_no = Column(String, nullable=True)
    ward_id = Column(Integer, ForeignKey("ward_master.id"), nullable=True)
    voter_status = Column(String, default="AVAILABLE")

class Survey(Base):
    __tablename__ = "surveys"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    district = Column(String)
    mandal = Column(String)
    village = Column(String)
    ward = Column(String)
    scope_type = Column(String)
    scope_value = Column(String)
    scope_config = Column(String, nullable=True)
    status = Column(String, default="CREATED")
    survey_code = Column(String, unique=True)
    survey_type = Column(String, default="TEST")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    @property
    def is_locked(self):
        return self.status in ["COMPLETED", "ARCHIVED"]

class SurveyVoter(Base):
    __tablename__ = "survey_voters"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), index=True)
    master_voter_id = Column(Integer, ForeignKey("voters.voter_id"), index=True)
    snapshot_created_at = Column(DateTime, default=datetime.utcnow)
    voter_name = Column(String)
    surname = Column(String)
    ward_no = Column(Integer)
    house_no = Column(String)
    age = Column(Integer)
    gender = Column(String)
    relation_name = Column(String)
    expected_party = Column(String, nullable=True)
    occupation = Column(String, nullable=True)
    religion = Column(String, nullable=True)
    caste = Column(String, nullable=True)
    sub_caste = Column(String, nullable=True)
    mobile_no = Column(String, nullable=True)
    voter_status = Column(String, default="AVAILABLE")

# --- SEEDING LOGIC (Inline) ---
async def seed_master_data(db: AsyncSession):
    try:
        from sqlalchemy import select
        # 1. District
        res = await db.execute(select(DistrictMaster).filter(DistrictMaster.name == "Yadadri Bhuvanagiri"))
        dist = res.scalar()
        if not dist:
            dist = DistrictMaster(id=1, name="Yadadri Bhuvanagiri")
            db.add(dist)
            print("Seeded District: Yadadri Bhuvanagiri")
        
        # 2. Mandal
        res = await db.execute(select(MandalMaster).filter(MandalMaster.name == "Choutuppal"))
        mandal = res.scalar()
        if not mandal:
            mandal = MandalMaster(id=1, name="Choutuppal", district_id=1)
            db.add(mandal)
            print("Seeded Mandal: Choutuppal")
            
        # 3. Village (Example)
        res = await db.execute(select(VillageMaster).filter(VillageMaster.name == "Choutuppal Village"))
        vill = res.scalar()
        if not vill:
            vill = VillageMaster(id=1, name="Choutuppal Village", mandal_id=1)
            db.add(vill)
            print("Seeded Village: Choutuppal Village")
            
        # 4. Ward (Fix for Empty Dropdown)
        res = await db.execute(select(WardMaster).filter(WardMaster.village_id == 1))
        ward = res.scalar()
        if not ward:
            ward = WardMaster(id=1, name="Ward 1", village_id=1)
            db.add(ward)
            print("Seeded Ward: Ward 1")

        await db.commit()
    except Exception as e:
        print(f"Seeding Warning: {e}")

class SurveyorRequest(Base):
    __tablename__ = "surveyor_requests"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    mobile_no = Column(String)
    device_id = Column(String, nullable=True)
    district_name = Column(String)
    mandal_name = Column(String)
    village_name = Column(String)
    ward_no = Column(String)
    status = Column(String, default="PENDING")
    role = Column(String, default="SURVEYOR")
    assigned_village_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SurveyAssignment(Base):
    __tablename__ = "survey_assignments"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), index=True)
    surveyor_id = Column(Integer, ForeignKey("surveyor_requests.id"), index=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="ACTIVE")

# Backward compatibility alias
Voter = VoterMaster

# --- SECURITY & CONTEXT ---
api_key_header = APIKeyHeader(name="X-Auth-Token", auto_error=False)

class UserContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int
    role: str
    ward_no: int | None

async def get_current_user(
    token: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> UserContext:
    if not token:
        # For now, we allow unauthenticated access for certain things OR legacy
        # But per constitution, we should return anonymous context or fail.
        # For full compliance, we fail if endpoint requires it.
        # But to avoid breaking login, we make it optional below or handle it.
        # Actually, let's allow None token implies Anonymous, but endpoints enforce.
        # However, the user provided code: if not token: raise 401.
        # We will assume endpoints using this REQUIRE auth.
        raise HTTPException(status_code=401, detail="Missing auth token")

    mobile = token.replace("+91", "").replace(" ", "").replace("-", "").strip()
    
    # SPECIAL: Admin Bypass
    if token == "admin-secret-123":
        return UserContext(user_id=0, role="ADMIN", ward_no=None)

    from sqlalchemy import select
    res = await db.execute(
        select(SurveyorRequest)
        .filter(
            SurveyorRequest.mobile_no == mobile,
            SurveyorRequest.status == "APPROVED"
        )
    )
    user = res.scalar()

    if not user:
        raise HTTPException(status_code=403, detail="Invalid credentials")

    # Ward extraction
    ward_no = None
    if user.ward_no and user.ward_no.isdigit():
        ward_no = int(user.ward_no)

    return UserContext(
        user_id=user.id,
        role=user.role,
        ward_no=ward_no
    )

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

# CACHE BUSTER MIDDLEWARE: Force no-cache for index.html to fix "Zombie Frontend"
@app.middleware("http")
async def add_no_cache_header(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    # Apply to root HTML and Flutter HTML
    if path.endswith("index.html") or path == "/static/" or path == "/app/" or path == "/flutter_app/":
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Static files will be mounted at the end as root fallback to solve 404 issues with base href="/"

@app.on_event("startup")
async def startup_event():
    print("--- APP STARTUP SEQUENCE INITIATED ---")
    try:
        # 1. Create tables asynchronously
        print("--- ATTEMPTING DB CONNECTION ---")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("--- DB TABLES CREATED/VERIFIED ---")
    
        # 2. Run seeding in background
        print("--- STARTING BACKGROUND SEEDER ---")
        thread = threading.Thread(target=run_background_seeding)
        thread.start()
        print("--- APP STARTUP SUCCESSFUL ---")
        
    except Exception as e:
        # CRITICAL: Do not crash the app if DB fails. Log it and allow startup so logs are visible.
        print(f"!!! CRITICAL STARTUP ERROR: {e} !!!")
        print("!!! CONTINUING STARTUP TO ALLOW LOGGING !!!")

def run_background_seeding():
    print("--- BACKGROUND THREAD STARTED ---")
    try:
        import asyncio
        asyncio.run(async_seeding())
    except Exception as e:
        print(f"!!! BACKGROUND THREAD CRASH: {e} !!!")

async def async_seeding():
    from database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import select
            # 1. Voter Seeding
            v_count_res = await db.execute(select(func.count()).select_from(VoterMaster))
            if v_count_res.scalar() == 0:
                print("[BACKGROUND] Seeding voters...")
                from seed_db import async_seed_data
                await async_seed_data(db)
            
            # 2. Geo Seeding
            d_count_res = await db.execute(select(func.count()).select_from(DistrictMaster))
            if d_count_res.scalar() == 0:
                print("[BACKGROUND] Seeding geo data...")
                from seed_geo import async_seed_geo_data
                await async_seed_geo_data(db)

            # 3. Demo Coordinator
            demo_res = await db.execute(select(SurveyorRequest).filter(SurveyorRequest.mobile_no == '9999999999'))
            if not demo_res.scalar():
                print("[BACKGROUND] Creating Demo Coordinator...")
                new_coord = SurveyorRequest(
                    name="Demo Coordinator",
                    mobile_no="9999999999",
                    district_name="Yadadri Bhuvanagiri",
                    mandal_name="Choutuppal",
                    village_name="Aregudem",
                    ward_no="0",
                    role="COORDINATOR",
                    assigned_village_id=1,
                    status="APPROVED",
                    device_id="auto-seed"
                )
                db.add(new_coord)
                await db.commit()
            
            # 4. Migrations (Wrap in try/except)
            print("[BACKGROUND] Checking migrations...")
            # Ideally migrations are handled outside main app but for now:
            pass
            
            print("[BACKGROUND] Startup processing finished.")
        except Exception as e:
            print(f"[BACKGROUND] Error in seeding: {e}")

# --- VERSION HANDSHAKE ---
@app.get("/version")
async def get_version():
    return {
        "version": EXPECTED_FRONTEND_VERSION,
        "real_version": MAIN_VERSION,
        "env": "PROD",
        "last_updated": datetime.utcnow().isoformat()
    }

@app.post("/voters/upload_bulk")
async def upload_voters_bulk(
    file: UploadFile = File(...),
    district_id: int = Form(...),
    mandal_id: int = Form(...),
    village_id: int = Form(...),
    x_admin_token: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Bulk upload voters from CSV file"""
    if x_admin_token != "admin-secret-123":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        from sqlalchemy import select
        contents = await file.read()
        csv_data = contents.decode('utf-8').splitlines()
        
        import csv
        import io
        reader = csv.DictReader(io.StringIO('\n'.join(csv_data)))
        
        added = 0
        updated = 0
        total_processed = 0
        
        # Get ward_id from village_id if possible
        ward_res = await db.execute(select(WardMaster).filter(WardMaster.village_id == village_id))
        ward = ward_res.scalar()
        ward_id = ward.id if ward else None
        
        errors_log = []
        for row in reader:
            total_processed += 1
            try:
                # Flexible Column Mapping
                def get_val(keys, default=''):
                    for k in keys:
                        if k in row and row[k]: return row[k]
                    return default

                # serial_no, s_no, sl_no
                s_no_val = get_val(['serial_no', 's_no', 'sl_no', 'no'], '0')
                s_no = int(s_no_val) if s_no_val.isdigit() else 0

                v_name = get_val(['voter_name', 'name', 'votername'])
                
                # voter_id, epic_no, card_no
                v_id_no = get_val(['voter_id_no', 'voter_id', 'epic_no', 'card_no', 'id_card_no'])
                
                # house_no, h_no
                h_no = get_val(['house_no', 'h_no', 'house', 'door_no'])

                # mobile, phone
                mob = get_val(['mobile_no', 'mobile', 'phone', 'contact'])
                
                # gender
                gen = get_val(['gender', 'sex'])

                # age
                age_val = get_val(['age'])
                age = int(age_val) if age_val and age_val.isdigit() else None

                # Relation
                rel_name = get_val(['relation_name', 'father_name', 'husband_name', 'guardian_name'])

                existing_res = await db.execute(select(VoterMaster).filter(
                    VoterMaster.serial_no == s_no,
                    VoterMaster.voter_name == v_name,
                    VoterMaster.ward_id == ward_id
                ))
                existing_voter = existing_res.scalar()
                
                if existing_voter:
                    existing_voter.house_no = h_no or existing_voter.house_no
                    existing_voter.serial_no = s_no if s_no > 0 else existing_voter.serial_no
                    existing_voter.gender = gen or existing_voter.gender
                    existing_voter.age = age or existing_voter.age
                    existing_voter.relation_name = rel_name or existing_voter.relation_name
                    updated += 1
                else:
                    new_voter = VoterMaster(
                        serial_no=s_no if s_no > 0 else None,
                        house_no=h_no,
                        voter_name=v_name,
                        gender=gen,
                        age=age,
                        voter_id_no=v_id_no,
                        mobile_no=mob,
                        ward_id=ward_id
                    )
                    db.add(new_voter)
                    added += 1
            except Exception as e:
                err_msg = f"Row {total_processed}: {str(e)}"
                print(err_msg)
                if len(errors_log) < 3:
                     errors_log.append(err_msg)
                continue
        
        try:
            await db.commit()
        except Exception as commit_err:
             await db.rollback()
             raise HTTPException(status_code=500, detail=f"Database Commit Failed: {str(commit_err)}")
        
        return {
            "status": "success",
            "total_processed": total_processed,
            "added": added,
            "updated": updated,
            "errors": errors_log
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/admin/reset_db")
async def reset_database(x_admin_token: Optional[str] = Header(None)):
    if x_admin_token != "admin-secret-123":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    from seed_db import seed_data
    # Seed data needs to be wraped or updated to async for full compliance,
    # but for now running sync in thread or wrapper.
    seed_data()
    return {"status": "success", "message": "Database Reset and Seeded from CSV."}

@app.post("/admin/seed_geo")
async def seed_geo_endpoint(x_admin_token: Optional[str] = Header(None)):
    if x_admin_token != "admin-secret-123":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    try:
        from seed_geo import seed_geo_data
        seed_geo_data()
        
        # Verify
        from sqlalchemy import select
        async with AsyncSessionLocal() as db:
            d_count = (await db.execute(select(func.count()).select_from(DistrictMaster))).scalar()
            m_count = (await db.execute(select(func.count()).select_from(MandalMaster))).scalar()
            v_count = (await db.execute(select(func.count()).select_from(VillageMaster))).scalar()
        
        return {
            "status": "success", 
            "message": f"Seeding Run Complete. DB Now Has: {d_count} Districts, {m_count} Mandals, {v_count} Villages.",
            "counts": {"districts": d_count}
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/debug/geo")
async def debug_geo_data(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    d_count = (await db.execute(select(func.count()).select_from(DistrictMaster))).scalar()
    districts_res = await db.execute(select(DistrictMaster).limit(5))
    districts = districts_res.scalars().all()
    d_names = [d.name for d in districts]
    
    return {
        "status": "online",
        "district_count": d_count,
        "sample_districts": d_names,
        "db_info": str(engine.url)
    }

@app.get("/debug/dump")
async def debug_dump_data(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    surveys_res = await db.execute(select(Survey))
    surveys = surveys_res.scalars().all()
    s_data = [{
        "id": s.id, "name": s.name, 
        "scope": s.scope_type, "val": s.scope_value,
        "d": s.district, "m": s.mandal, "v": s.village 
    } for s in surveys]
    
    coordinators_res = await db.execute(select(SurveyorRequest).filter(SurveyorRequest.role == "COORDINATOR"))
    coordinators = coordinators_res.scalars().all()
    c_data = [{
        "mobile": c.mobile_no, "name": c.name,
        "d": c.district_name, "m": c.mandal_name, "v": c.village_name
    } for c in coordinators]
    
    return {"surveys": s_data, "coordinators": c_data}

# Serve Flutter Mobile App (Web Version)
from fastapi.responses import FileResponse

# Explicitly serve index.html with NO-CACHE headers to break stale service workers

@app.get("/")
async def serve_spa(request: Request):
    # FORCE NO CACHE for index.html
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    return FileResponse("static/index.html", headers=headers)

@app.get("/app/")
@app.get("/app/index.html")
async def serve_app_index():
    return FileResponse(
        "static/index.html", 
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate", 
            "Pragma": "no-cache", 
            "Expires": "0"
        }
    )

# --- Pydantic Models for Request Body ---
# --- STRICT API CONTRACTS (Response Models) ---
class DistrictOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    name: str

class VoterOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    voter_id: int
    name: str | None = None
    surname: str | None = None
    ward: int | None = None
    house_no: str | None = None
    age: int | None = None
    gender: str | None = None
    relation: str | None = None
    expected_party: str | None = None
    occupation: str | None = None
    religion: str | None = None
    caste: str | None = None
    sub_caste: str | None = None
    mobile_no: str | None = None
    voter_status: str | None = None
    snapshot_id: Optional[int] = None # Added for search compatibility

class VoterUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    voter_id: int
    survey_id: int 
    party: Optional[str] = None
    occupation: Optional[str] = None
    religion: Optional[str] = None
    caste: Optional[str] = None
    sub_caste: Optional[str] = None
    mobile_no: Optional[str] = None
    voter_status: Optional[str] = None

class SurveyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    scope_type: str 
    scope_value: str
    survey_type: str = "TEST" 

class AnalyticsFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scope_type: str 
    district_ids: List[int] = []
    mandal_ids: List[int] = []
    village_ids: List[int] = []
    ward_ids: List[int] = []

class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mobile_no: str

@app.get("/api/status")
async def read_root():
    return {"status": "online", "message": "Voter API is running", "docs_url": "/docs", "version": MAIN_VERSION}

import json

@app.post("/surveys/create")
async def create_survey(
    name: str = Body(...), 
    scope_type: str = Body(...), 
    district_id: Optional[int] = Body(None),
    mandal_ids: Optional[str] = Body("ALL"), 
    village_ids: Optional[str] = Body("ALL"), 
    survey_type: str = Body("TEST"),
    x_admin_token: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    try:
        if x_admin_token != "admin-secret-123":
            raise HTTPException(status_code=403, detail="Forbidden: Admin Access Required")

        from sqlalchemy import select, or_
        
        # --- AUTO-HEALING LOGIC ---
        target_dist_id = district_id
        if not target_dist_id or target_dist_id <= 0:
            res = await db.execute(select(DistrictMaster).filter(DistrictMaster.name == "Yadadri Bhuvanagiri"))
            target_dist = res.scalar()
            
            if not target_dist:
                 # Use the inline seeder we defined
                 await seed_master_data(db)
                 res = await db.execute(select(DistrictMaster).filter(DistrictMaster.name == "Yadadri Bhuvanagiri"))
                 target_dist = res.scalar()
            
            if target_dist:
                target_dist_id = target_dist.id
            else:
                first_res = await db.execute(select(DistrictMaster).limit(1))
                first = first_res.scalar()
                if first: target_dist_id = first.id
                else: raise HTTPException(status_code=500, detail="Auto-Seeder failed completely.")

        target_village_ids = []
        try:
            req_mandals = mandal_ids if mandal_ids == "ALL" else json.loads(mandal_ids)
            req_villages = village_ids if village_ids == "ALL" else json.loads(village_ids)
        except:
            raise HTTPException(status_code=400, detail="Invalid Mandal/Village ID format")

        final_mandal_ids = []
        if req_mandals == "ALL":
            res = await db.execute(select(MandalMaster).filter(MandalMaster.district_id == target_dist_id))
            mandals = res.scalars().all()
            final_mandal_ids = [m.id for m in mandals]
        else:
            final_mandal_ids = [int(m) for m in req_mandals]

        if req_villages == "ALL":
            res = await db.execute(select(VillageMaster).filter(VillageMaster.mandal_id.in_(final_mandal_ids)))
            villages = res.scalars().all()
            target_village_ids = [v.id for v in villages]
        else:
            target_village_ids = [int(v) for v in req_villages]

        if not target_village_ids:
             raise HTTPException(status_code=400, detail="Scope resolution failed: No villages found.")

        res = await db.execute(select(WardMaster).filter(WardMaster.village_id.in_(target_village_ids)))
        wards = res.scalars().all()
        target_ward_nums = []
        for w in wards:
            try:
                num_str = ''.join(filter(str.isdigit, w.name))
                if num_str: target_ward_nums.append(int(num_str))
            except: pass
        target_ward_nums = list(set(target_ward_nums))
        
        date_str = datetime.utcnow().strftime("%Y%m%d")
        code = f"{scope_type}-{target_dist_id}-{survey_type}-{date_str}"
        
        existing_res = await db.execute(select(Survey).filter(Survey.survey_code == code))
        if existing_res.scalar():
            code = f"{code}-{datetime.utcnow().strftime('%H%M%S')}"

        config_json = json.dumps({
            "district_id": target_dist_id,
            "mandal_ids": req_mandals,
            "village_ids": req_villages,
            "derived_wards_count": len(target_ward_nums),
            "derived_villages_count": len(target_village_ids)
        })

        # Verify and Fetch Location Names
        dist_name = "Unknown District"
        mandal_name = "ALL"
        village_name = "ALL"
        
        # Needs to be re-fetched because target_dist logic above might have manipulated ID
        d_res = await db.execute(select(DistrictMaster).filter(DistrictMaster.id == target_dist_id))
        d_obj = d_res.scalar()
        if d_obj: dist_name = d_obj.name

        # Fetch Mandal Name
        if req_mandals != "ALL" and final_mandal_ids:
            try:
                m_res = await db.execute(select(MandalMaster).filter(MandalMaster.id == final_mandal_ids[0]))
                m_obj = m_res.scalar()
                if m_obj: mandal_name = m_obj.name
            except Exception as e:
                print(f"Error fetching mandal name: {e}")
                
        # Fetch Village Name
        if req_villages != "ALL" and target_village_ids:
            try:
                 v_res = await db.execute(select(VillageMaster).filter(VillageMaster.id == target_village_ids[0]))
                 v_obj = v_res.scalar()
                 if v_obj: village_name = v_obj.name
            except Exception as e:
                print(f"Error fetching village name: {e}")

        new_survey = Survey(
            name=name,
            scope_type=scope_type,
            scope_value=str(target_dist_id),
            scope_config=config_json,
            status="ACTIVE", 
            survey_code=code,
            survey_type=survey_type,
            district=dist_name, 
            mandal=mandal_name, 
            village=village_name 
        )
        
        db.add(new_survey)
        await db.flush() # Get ID

        # 4. Snapshot Logic
        copied_count = 0
        if target_ward_nums or wards:
            target_ward_ids = [w.id for w in wards]
            ward_id_map = {}
            import re
            for w in wards:
                match = re.search(r'\d+', w.name)
                if match: ward_id_map[w.id] = int(match.group())

        masters_res = await db.execute(select(VoterMaster).filter(
            or_(
                VoterMaster.ward_id.in_(target_ward_ids),
                VoterMaster.ward_no.in_(target_ward_nums)
            )
        ))
        masters = masters_res.scalars().all()
        
        now = datetime.utcnow()
        for v in masters:
            final_ward_no = v.ward_no
            if v.ward_id in ward_id_map:
                final_ward_no = ward_id_map[v.ward_id]

            sv = SurveyVoter(
                survey_id=new_survey.id,
                master_voter_id=v.voter_id,
                voter_name=v.voter_name,
                surname=v.surname,
                ward_no=final_ward_no,
                house_no=v.house_no,
                age=v.age,
                gender=v.gender,
                relation_name=v.relation_name,
                expected_party=None,
                occupation=None,
                voter_status="AVAILABLE",
                snapshot_created_at=now
            )
            db.add(sv)
        
        
        # Note: In async, we can't easily count before commit in the same way without flush/refresh
        # We assume they are added.
        copied_count = len(masters)
    
        await db.commit()

        return {
            "status": "success",
            "survey_id": new_survey.id,
            "survey_code": new_survey.survey_code,
            "message": f"Survey created. Snapshot size: {copied_count}"
        }
    except Exception as e:
        await db.rollback()
        print(f"Error creating survey: {e}")
        raise HTTPException(status_code=500, detail=f"Survey Creation Failed: {str(e)}")

@app.get("/surveys/active")
async def get_active_surveys(
    mobile_no: Optional[str] = Query(None), 
    village_filter: Optional[str] = Query(None), 
    mandal_filter: Optional[str] = Query(None),
    district_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select, or_, and_, desc
    
    # 1. Base Query
    query = select(Survey).filter(
        or_(Survey.status == "ACTIVE", Survey.status == "CREATED")
    )
    
    # 2. Surveyor View (Filtered by Assignment)
    if mobile_no:
        mobile_no = clean_mobile(mobile_no)
        res = await db.execute(select(SurveyorRequest).filter(SurveyorRequest.mobile_no == mobile_no, SurveyorRequest.status == "APPROVED"))
        surveyor = res.scalar()
        
        if surveyor:
            # Join assignments
            query = query.join(SurveyAssignment, Survey.id == SurveyAssignment.survey_id)\
                         .filter(SurveyAssignment.surveyor_id == surveyor.id, SurveyAssignment.status == "ACTIVE")
        else:
            # Unknown surveyor sees nothing
            return []

    # 3. Location Filters (Optional)
    conditions = []
    if district_filter:
        conditions.append(and_(Survey.scope_type=="DISTRICT", func.lower(Survey.district) == district_filter.lower().strip()))
    if mandal_filter:
        conditions.append(and_(Survey.scope_type=="MANDAL", func.lower(Survey.mandal) == mandal_filter.lower().strip()))
    if village_filter:
        conditions.append(func.lower(Survey.village) == village_filter.lower().strip())

    if conditions:
        query = query.filter(or_(*conditions))
    
    # 4. Execute
    res = await db.execute(query.order_by(desc(Survey.created_at)))
    return res.scalars().all()
    
    
@app.post("/assignments/create")
async def create_assignment(survey_id: int = Body(...), surveyor_id: int = Body(...), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    # Check if exists
    res = await db.execute(select(SurveyAssignment).filter(
        SurveyAssignment.survey_id == survey_id,
        SurveyAssignment.surveyor_id == surveyor_id,
        SurveyAssignment.status == "ACTIVE"
    ))
    existing = res.scalar()
    
    if existing:
        return {"status": "exists", "message": "Already assigned"}
        
    new_assign = SurveyAssignment(survey_id=survey_id, surveyor_id=surveyor_id)
    db.add(new_assign)
    await db.commit()
    return {"status": "success"}

@app.get("/assignments/list")
async def list_assignments(survey_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    query = select(SurveyAssignment).filter(SurveyAssignment.status == "ACTIVE")
    if survey_id:
        query = query.filter(SurveyAssignment.survey_id == survey_id)
        
    res = await db.execute(query)
    assignments = res.scalars().all()
    results = []
    for a in assignments:
        s_res = await db.execute(select(SurveyorRequest).filter(SurveyorRequest.id == a.surveyor_id))
        s_req = s_res.scalar()
        sv_res = await db.execute(select(Survey).filter(Survey.id == a.survey_id))
        survey = sv_res.scalar()
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
async def search_voters(query: str, survey_id: int, ward: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, or_
    q = select(SurveyVoter).filter(
        SurveyVoter.survey_id == survey_id,
        or_(
            SurveyVoter.voter_name.ilike(f"%{query}%"),
            SurveyVoter.surname.ilike(f"%{query}%")
        )
    )
    if ward is not None:
        q = q.filter(SurveyVoter.ward_no == ward)
        
    res = await db.execute(q.limit(50))
    voters = res.scalars().all()
    
    return [
        {
            "voter_id": v.master_voter_id,
            "snapshot_id": v.id,
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
async def get_next_voter(survey_id: int, current_id: int = 0, skip_completed: bool = True, ward: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, asc
    query = select(SurveyVoter).filter(
        SurveyVoter.survey_id == survey_id,
        SurveyVoter.master_voter_id > current_id
    )

    if ward is not None:
        query = query.filter(SurveyVoter.ward_no == ward)

    if skip_completed:
        query = query.filter(SurveyVoter.expected_party == None)

    res = await db.execute(query.order_by(asc(SurveyVoter.master_voter_id)).limit(1))
    voter = res.scalar()
    
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
async def get_previous_voter(survey_id: int, current_id: int, skip_completed: bool = True, ward: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, desc
    query = select(SurveyVoter).filter(
        SurveyVoter.survey_id == survey_id,
        SurveyVoter.master_voter_id < current_id
    )

    if ward is not None:
        query = query.filter(SurveyVoter.ward_no == ward)

    if skip_completed:
        query = query.filter(SurveyVoter.expected_party == None)

    res = await db.execute(query.order_by(desc(SurveyVoter.master_voter_id)).limit(1))
    voter = res.scalar()
    
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
async def update_voter_data(data: VoterUpdate, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    res_s = await db.execute(select(Survey).filter(Survey.id == data.survey_id))
    survey = res_s.scalar()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    if survey.is_locked:
        raise HTTPException(status_code=403, detail="Survey is LOCKED (Completed or Archived). No updates allowed.")
    
    res_v = await db.execute(select(SurveyVoter).filter(
        SurveyVoter.survey_id == data.survey_id,
        SurveyVoter.master_voter_id == data.voter_id
    ))
    voter = res_v.scalar()
    
    if not voter:
        raise HTTPException(status_code=404, detail="Voter not found in this survey")
        
    if data.voter_status is not None: 
        voter.voter_status = data.voter_status
    
    if data.party is not None: voter.expected_party = data.party
    if data.occupation is not None: voter.occupation = data.occupation
    if data.religion is not None: voter.religion = data.religion
    if data.caste is not None: voter.caste = data.caste
    if data.sub_caste is not None: voter.sub_caste = data.sub_caste
    if data.mobile_no is not None: voter.mobile_no = data.mobile_no
    
    await db.commit()
    return {"status": "success"}

@app.get("/voters/stats")
async def get_voter_stats(survey_id: int, ward: Optional[int] = None, current_voter_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, func
    base_q = select(SurveyVoter).filter(SurveyVoter.survey_id == survey_id)
    if ward is not None:
        base_q = base_q.filter(SurveyVoter.ward_no == ward)
        
    res_total = await db.execute(select(func.count()).select_from(base_q.subquery()))
    total = res_total.scalar()
    
    res_completed = await db.execute(select(func.count()).select_from(base_q.filter(SurveyVoter.expected_party != None).subquery()))
    completed = res_completed.scalar()
    
    stats = {
        "total": total,
        "completed": completed,
        "ward": ward
    }

    if current_voter_id is not None and ward is not None:
        res_index = await db.execute(select(func.count()).select_from(
            select(SurveyVoter).filter(
                SurveyVoter.survey_id == survey_id,
                SurveyVoter.ward_no == ward, 
                SurveyVoter.master_voter_id <= current_voter_id
            ).subquery()
        ))
        stats["current_index"] = res_index.scalar()

    return stats

@app.get("/voters/{voter_id}")
async def get_voter_by_id(voter_id: int, survey_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    res = await db.execute(select(SurveyVoter).filter(
        SurveyVoter.survey_id == survey_id,
        SurveyVoter.master_voter_id == voter_id
    ))
    voter = res.scalar()
    
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

@app.get("/master/districts", response_model=List[DistrictOut])
async def get_all_districts(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    res = await db.execute(select(DistrictMaster))
    districts = res.scalars().all()
    
    if not districts:
        await seed_master_data(db)
        res = await db.execute(select(DistrictMaster))
        districts = res.scalars().all()
        
    return [DistrictOut(id=d.id, name=d.name) for d in districts]

@app.get("/master/mandals/{district_id}")
async def get_mandals(district_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    res = await db.execute(select(MandalMaster).filter(MandalMaster.district_id == district_id))
    return res.scalars().all()

@app.get("/master/villages/{mandal_id}")
async def get_villages(mandal_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    res = await db.execute(select(VillageMaster).filter(VillageMaster.mandal_id == mandal_id))
    return res.scalars().all()

# --- VOTER SEARCH (Auth Enforced) ---
@app.get("/voters/search", response_model=List[VoterOut])
async def search_voters(
    query: str,
    survey_id: int,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select, or_

    # Strict Auth: Enforce Ward
    ward_filter = None
    if user.role == "SURVEYOR":
        if user.ward_no is None:
             raise HTTPException(status_code=403, detail="Ward not assigned to surveyor.")
        ward_filter = user.ward_no
    
    stmt = select(SurveyVoter).filter(
        SurveyVoter.survey_id == survey_id,
        or_(
            SurveyVoter.voter_name.ilike(f"%{query}%"),
            SurveyVoter.surname.ilike(f"%{query}%"),
            SurveyVoter.house_no.ilike(f"%{query}%")
        )
    )

    if ward_filter is not None:
        stmt = stmt.filter(SurveyVoter.ward_no == ward_filter)
    
    # Debug: Print query if needed
    # print(stmt)

    res = await db.execute(stmt)
    voters = res.scalars().all()
    
    return [
        VoterOut(
            voter_id=v.master_voter_id, # Return master ID for updates
            name=v.voter_name,
            surname=v.surname,
            ward=v.ward_no,
            house_no=v.house_no,
            age=v.age,
            gender=v.gender,
            relation=v.relation_name,
            expected_party=v.expected_party,
            occupation=v.occupation,
            religion=v.religion,
            caste=v.caste,
            sub_caste=v.sub_caste,
            mobile_no=v.mobile_no,
            voter_status=v.voter_status,
            snapshot_id=v.id
        ) for v in voters
    ]

# --- BULK UPLOAD VALIDATION ENDPOINTS ---

# --- DASHBOARD ENDPOINTS ---

@app.get("/dashboard/summary")
async def get_dashboard_summary(survey_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, func, distinct
    
    # 1. Total
    total_voters = (await db.execute(select(func.count()).filter(SurveyVoter.survey_id == survey_id))).scalar()
    
    # 2. Completed
    completed_surveys = (await db.execute(select(func.count()).filter(
        SurveyVoter.survey_id == survey_id,
        SurveyVoter.expected_party != None
    ))).scalar()
    
    # 3. Effective
    effective_voters = (await db.execute(select(func.count()).filter(
        SurveyVoter.survey_id == survey_id,
        SurveyVoter.voter_status == "AVAILABLE"
    ))).scalar()
    
    # 4. Ward Count
    ward_count = (await db.execute(select(func.count(distinct(SurveyVoter.ward_no))).filter(SurveyVoter.survey_id == survey_id))).scalar()
    
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
async def get_dashboard_progress(survey_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, func, distinct
    
    wards_res = await db.execute(select(distinct(SurveyVoter.ward_no)).filter(SurveyVoter.survey_id == survey_id).order_by(SurveyVoter.ward_no))
    wards = [w[0] for w in wards_res.all()]
    
    progress_data = []
    for ward in wards:
        w_total = (await db.execute(select(func.count()).filter(SurveyVoter.survey_id == survey_id, SurveyVoter.ward_no == ward))).scalar()
        w_completed = (await db.execute(select(func.count()).filter(SurveyVoter.survey_id == survey_id, SurveyVoter.ward_no == ward, SurveyVoter.expected_party != None))).scalar()
        w_effective = (await db.execute(select(func.count()).filter(SurveyVoter.survey_id == survey_id, SurveyVoter.ward_no == ward, SurveyVoter.voter_status == "AVAILABLE"))).scalar()
        
        status = "IN_PROGRESS"
        if w_effective > 0 and w_completed >= w_effective: status = "COMPLETED"
        elif w_completed == 0: status = "PENDING"
            
        progress_data.append({
            "ward_no": ward,
            "total_voters": w_total,
            "effective_voters": w_effective,
            "completed": w_completed,
            "status": status,
            "surveyor": "Unassigned"
        })
        
    return {"status": "success", "data": progress_data}

@app.get("/analytics/export/{survey_id}")
async def export_survey_csv(survey_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    res = await db.execute(select(SurveyVoter).filter(SurveyVoter.survey_id == survey_id))
    voters = res.scalars().all()
    
    if not voters:
        raise HTTPException(status_code=404, detail="No data found for this survey")

    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Voter ID", "Name", "Surname", "Father/Husband", "Age", "Gender", 
        "Ward", "House No", "Mobile", 
        "Status", "Expected Party", "Caste", "Religion", "Occupation"
    ])
    
    for v in voters:
        writer.writerow([
            v.master_voter_id, v.voter_name, v.surname, v.relation_name,
            v.age, v.gender, v.ward_no, v.house_no, v.mobile_no,
            v.voter_status or "PENDING", v.expected_party or "", 
            v.caste or "", v.religion or "", v.occupation or ""
        ])
        
    output.seek(0)
    filename = f"survey_{survey_id}_export.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# Duplicate get_active_surveys removed

@app.get("/dashboard/analytics")
async def get_dashboard_analytics(survey_id: int, db: AsyncSession = Depends(get_db)):
    try:
        from sqlalchemy import select, func
        # Validate Survey ID exists first
        s_res = await db.execute(select(Survey).filter(Survey.id == survey_id))
        if not s_res.scalar():
             # Return empty to prevent crash
             return {"status": "success", "total_polled": 0, "data": []}

        res = await db.execute(select(
            SurveyVoter.expected_party, 
            func.count(SurveyVoter.expected_party)
        ).filter(
            SurveyVoter.survey_id == survey_id,
            SurveyVoter.voter_status == "AVAILABLE",
            SurveyVoter.expected_party != None
        ).group_by(SurveyVoter.expected_party))
        results = res.all()
        
        analytics_data = []
        total_polled = 0
        for party, count in results:
            analytics_data.append({"party": party, "count": count})
            total_polled += count
            
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
    except Exception as e:
        print(f"[ANALYTICS ERROR] {e}")
        # Return graceful empty stats instead of 500
        return {"status": "success", "total_polled": 0, "data": []}

@app.get("/dashboard/approvals")
async def get_surveyor_requests(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, desc
    res = await db.execute(select(SurveyorRequest).order_by(desc(SurveyorRequest.created_at)))
    requests = res.scalars().all()
    response_data = []
    for r in requests:
        assigned_survey_name = "-"
        if r.status == "APPROVED":
            res_a = await db.execute(select(SurveyAssignment).filter(SurveyAssignment.surveyor_id == r.id))
            assignment = res_a.scalar()
            if assignment:
                 res_s = await db.execute(select(Survey).filter(Survey.id == assignment.survey_id))
                 survey = res_s.scalar()
                 if survey: assigned_survey_name = survey.name

        response_data.append({
            "id": r.id, 
            "name": r.name, 
            "mobile": r.mobile_no, 
            "role": r.role,
            "date": r.created_at,
            "status": r.status,
            "district": r.district_name,
            "mandal": r.mandal_name,
            "village": r.village_name,
            "ward": r.ward_no,
            "assigned_survey": assigned_survey_name
        })
    return response_data

@app.delete("/dashboard/surveyor/{surveyor_id}")
async def delete_surveyor(surveyor_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, delete
    res = await db.execute(select(SurveyorRequest).filter(SurveyorRequest.id == surveyor_id))
    surveyor = res.scalar()
    if not surveyor:
         return JSONResponse(status_code=404, content={"status": "fail", "message": "Surveyor not found"})
    
    await db.execute(delete(SurveyAssignment).filter(SurveyAssignment.surveyor_id == surveyor_id))
    db.delete(surveyor)
    await db.commit()
    return {"status": "success", "message": "Surveyor deleted successfully"}

@app.post("/dashboard/approve")
async def approve_surveyor(request_id: int = Body(...), action: str = Body(...), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    res = await db.execute(select(SurveyorRequest).filter(SurveyorRequest.id == request_id))
    req = res.scalar()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if action not in ["APPROVED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    req.status = action
    await db.commit()
    return {"status": "success"}

# --- PUBLIC ENDPOINT FOR APP REGISTRATION (To feed into approvals) ---
@app.post("/register/surveyor")
async def register_surveyor(
    name: str = Body(...), 
    mobile: str = Body(...), 
    device_id: str = Body(None),
    district_name: str = Body(None),
    mandal_name: str = Body(None),
    village_name: str = Body(None),
    ward_no: str = Body(None),
    role: str = Body("SURVEYOR"), 
    village_id: int = Body(None),
    db: AsyncSession = Depends(get_db)
):
    mobile = clean_mobile(mobile)
    from sqlalchemy import select
    res = await db.execute(select(SurveyorRequest).filter(SurveyorRequest.mobile_no == mobile))
    existing = res.scalar()
    if existing:
        return {"status": "exists", "id": existing.id, "current_status": existing.status}
        
    new_req = SurveyorRequest(
        name=name, mobile_no=mobile, device_id=device_id,
        district_name=district_name, mandal_name=mandal_name, village_name=village_name, ward_no=ward_no,
        role=role.strip().upper(), assigned_village_id=village_id
    )
    db.add(new_req)
    await db.commit()
    return {"status": "success", "id": new_req.id, "current_status": "PENDING"}

@app.post("/auth/login")
async def coordinator_login(login: LoginRequest, db: AsyncSession = Depends(get_db)):
    cleaned_mobile = clean_mobile(login.mobile_no)
    from sqlalchemy import select
    res = await db.execute(select(SurveyorRequest).filter(
        SurveyorRequest.mobile_no == cleaned_mobile,
        SurveyorRequest.role == "COORDINATOR",
        SurveyorRequest.status == "APPROVED"
    ))
    user = res.scalar()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid Mobile Number or Not Authorized")
    
    village_name = user.village_name
    if not village_name and user.assigned_village_id:
         res_v = await db.execute(select(VillageMaster).filter(VillageMaster.id == user.assigned_village_id))
         v = res_v.scalar()
         if v: village_name = v.name

    return {
        "status": "success", "role": user.role, "name": user.name,
        "village_id": user.assigned_village_id, "village_name": village_name,
        "mandal_name": user.mandal_name, "district_name": user.district_name
    }

@app.get("/locations/districts")
async def get_districts(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    res = await db.execute(select(DistrictMaster))
    return res.scalars().all()

@app.get("/locations/mandals/{district_id}")
async def get_mandals(district_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    res = await db.execute(select(MandalMaster).filter(MandalMaster.district_id == district_id))
    return res.scalars().all()

@app.get("/locations/villages/{mandal_id}")
async def get_villages(mandal_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    res = await db.execute(select(VillageMaster).filter(VillageMaster.mandal_id == mandal_id))
    return res.scalars().all()

@app.get("/locations/wards/{village_id}")
async def get_wards(village_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    res = await db.execute(select(WardMaster).filter(WardMaster.village_id == village_id))
    return res.scalars().all()



@app.get("/register/status/mobile")
async def check_registration_status_by_mobile(mobile_no: str, db: AsyncSession = Depends(get_db)):
    mobile_no = clean_mobile(mobile_no)
    from sqlalchemy import select
    res = await db.execute(select(SurveyorRequest).filter(SurveyorRequest.mobile_no == mobile_no))
    req = res.scalar()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return {
        "status": "success", 
        "approval_status": req.status, 
        "surveyor_id": req.id,
        "ward_no": req.ward_no,
        "role": req.role
    }

@app.get("/register/status/{request_id}")
async def check_registration_status(request_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    res = await db.execute(select(SurveyorRequest).filter(SurveyorRequest.id == request_id))
    req = res.scalar()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"status": "success", "approval_status": req.status}


# --- 6. BULK UPLOAD API (Part 1 - Data Onboarding) ---
@app.post("/admin/upload-voters")
async def upload_voters(
    file: UploadFile = File(...),
    secret_key: str = Form(...),
    district_id: int = Form(None),
    mandal_id: int = Form(None),
    village_id: int = Form(None),
    ward_id: int = Form(None),
    db: AsyncSession = Depends(get_db)
):
    if secret_key != "admin-secret-123":
         raise HTTPException(status_code=401, detail="Invalid Admin Secret")

    import csv
    import codecs
    
    def safe_int(val, default=0):
        if val is None or val == "" or val == "None" or val == "null":
            return default
        try:
            return int(float(val)) 
        except (ValueError, TypeError):
            import re
            match = re.search(r'\d+', str(val))
            if match:
                return int(match.group())
            return default

    try:
        csv_reader = csv.DictReader(codecs.iterdecode(file.file, 'utf-8'))
        voters_to_add = []
        count = 0
        forced_ward_no = None
        
        from sqlalchemy import select, delete
        if ward_id:
            await db.execute(delete(VoterMaster).filter(VoterMaster.ward_id == ward_id))
            res_w = await db.execute(select(WardMaster).filter(WardMaster.id == ward_id))
            ward_obj = res_w.scalar()
            if ward_obj:
                import re
                match = re.search(r'\d+', ward_obj.name)
                if match:
                    forced_ward_no = int(match.group())

        for row in csv_reader:
            voter_name = row.get("voter_name")
            if not voter_name:
                continue
            
            final_ward_no = forced_ward_no if forced_ward_no is not None else safe_int(row.get("ward_no"))

            voter = VoterMaster(
                serial_no=safe_int(row.get("serial_no")),
                house_no=row.get("house_no", ""),
                voter_name=row.get("voter_name"),
                gender=row.get("gender", ""),
                age=safe_int(row.get("age")),
                relation_name=row.get("relation_name", ""),
                surname=row.get("surname", ""),
                ward_no=final_ward_no,
                ward_id=ward_id,
                family_id=row.get("family_id", ""),
                mobile_no=row.get("mobile_no", None)
            )
            voters_to_add.append(voter)
            count += 1
            
            if len(voters_to_add) >= 1000:
                db.add_all(voters_to_add)
                await db.commit()
                voters_to_add = []

        if voters_to_add:
            db.add_all(voters_to_add)
            await db.commit()
            
        return {
            "status": "success", 
            "message": f"Successfully uploaded {count} voters (Ward ID: {ward_id})",
            "context": {"ward_id": ward_id, "district_id": district_id}
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Upload Failed: {str(e)}")

# --- PHASE 7: ADVANCED REPORTING API ---
print("--- LOADING PHASE 7 ANALYTICS APIs ---")

@app.get("/analytics/health")
def analytics_health():
    return {"status": "active"}

def apply_analytics_filter(query, filter: AnalyticsFilter):
    # Base Join: SurveyVoter -> VoterMaster -> Ward -> Village -> Mandal -> District
    
    # Debug
    print(f"DEBUG JOIN: {VoterMaster}")
    
    query = query.join(VoterMaster) \
                 .join(WardMaster) \
                 .join(VillageMaster) \
                 .join(MandalMaster) \
                 .join(DistrictMaster)

    conditions = []
    
    if filter.scope_type == "DISTRICT":
        if filter.district_ids:
            conditions.append(DistrictMaster.id.in_(filter.district_ids))
            
    elif filter.scope_type == "MANDAL":
        if filter.mandal_ids:
             conditions.append(MandalMaster.id.in_(filter.mandal_ids))
             
    elif filter.scope_type == "VILLAGE":
        if filter.village_ids:
            conditions.append(VillageMaster.id.in_(filter.village_ids))
            
    elif filter.scope_type == "CUSTOM":
        if filter.ward_ids: conditions.append(WardMaster.id.in_(filter.ward_ids))
        if filter.village_ids: conditions.append(VillageMaster.id.in_(filter.village_ids))
        if filter.mandal_ids: conditions.append(MandalMaster.id.in_(filter.mandal_ids))
        if conditions:
            return query.filter(or_(*conditions))
    
    if conditions:
        query = query.filter(and_(*conditions))
        
    return query

@app.post("/analytics/aggregate")
async def get_aggregated_stats(filter: AnalyticsFilter, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, func
    base_query = select(SurveyVoter)
    filtered_query = apply_analytics_filter(base_query, filter)
    
    # Aggregations
    party_stats_res = await db.execute(filtered_query.with_entities(
        SurveyVoter.expected_party, 
        func.count(SurveyVoter.expected_party)
    ).filter(
        SurveyVoter.expected_party != None,
        SurveyVoter.voter_status == "AVAILABLE"
    ).group_by(SurveyVoter.expected_party))
    party_stats = party_stats_res.all()
    party_data = [{"party": p, "count": c} for p, c in party_stats]
    
    caste_stats_res = await db.execute(filtered_query.with_entities(
        SurveyVoter.caste, 
        func.count(SurveyVoter.caste)
    ).filter(SurveyVoter.caste != None).group_by(SurveyVoter.caste))
    caste_stats = caste_stats_res.all()
    caste_data = [{"caste": c, "count": count} for c, count in caste_stats]
    
    total_res = await db.execute(select(func.count()).select_from(filtered_query.subquery()))
    total_polled_voters = total_res.scalar()
    
    completed_res = await db.execute(select(func.count()).select_from(filtered_query.filter(SurveyVoter.expected_party != None).subquery()))
    completed_count = completed_res.scalar()
    
    return {
        "status": "success",
        "data": {
            "party_distribution": party_data,
            "caste_distribution": caste_data,
            "metrics": {
                "total_scope_voters": total_polled_voters,
                "completed_surveys": completed_count,
                "polling_percentage": round((completed_count / total_polled_voters * 100), 1) if total_polled_voters > 0 else 0
            }
        }
    }

@app.post("/analytics/export/master")
async def export_master_data(filter: AnalyticsFilter, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    base_query = select(
        DistrictMaster.name.label("District"),
        MandalMaster.name.label("Mandal"),
        VillageMaster.name.label("Village"),
        WardMaster.name.label("Ward"),
        SurveyVoter.voter_name,
        SurveyVoter.surname,
        SurveyVoter.relation_name,
        SurveyVoter.age,
        SurveyVoter.gender,
        SurveyVoter.mobile_no,
        SurveyVoter.house_no,
        SurveyVoter.voter_status,
        SurveyVoter.expected_party,
        SurveyVoter.caste,
        SurveyVoter.religion,
        SurveyVoter.occupation,
        SurveyVoter.snapshot_created_at
    )
    
    # apply_analytics_filter needs adjustment to work with this select
    query = base_query.join(SurveyVoter, DistrictMaster.id == DistrictMaster.id) # Placeholder for joins
    # Actually, apply_analytics_filter already does joins. 
    # Let's rewrite the logic here to be safer.
    
    # Manual query for export master to ensure correct joins
    q = select(
        DistrictMaster.name, MandalMaster.name, VillageMaster.name, WardMaster.name,
        SurveyVoter.voter_name, SurveyVoter.surname, SurveyVoter.relation_name,
        SurveyVoter.age, SurveyVoter.gender, SurveyVoter.mobile_no, SurveyVoter.house_no,
        SurveyVoter.voter_status, SurveyVoter.expected_party, SurveyVoter.caste,
        SurveyVoter.religion, SurveyVoter.occupation, SurveyVoter.snapshot_created_at
    ).join(VoterMaster, SurveyVoter.master_voter_id == VoterMaster.voter_id) \
     .join(WardMaster, VoterMaster.ward_id == WardMaster.id) \
     .join(VillageMaster, WardMaster.village_id == VillageMaster.id) \
     .join(MandalMaster, VillageMaster.mandal_id == MandalMaster.id) \
     .join(DistrictMaster, MandalMaster.district_id == DistrictMaster.id)
    
    # Basic filtering logic (simplified from apply_analytics_filter for this specific route)
    if filter.scope_type == "DISTRICT" and filter.district_ids:
        q = q.filter(DistrictMaster.id.in_(filter.district_ids))
    elif filter.scope_type == "MANDAL" and filter.mandal_ids:
        q = q.filter(MandalMaster.id.in_(filter.mandal_ids))
    elif filter.scope_type == "VILLAGE" and filter.village_ids:
        q = q.filter(VillageMaster.id.in_(filter.village_ids))
        
    res = await db.execute(q)
    rows = res.all()
    
    import io
    import csv
    output = io.StringIO()
    writer = csv.writer(output)
    headers = ["District", "Mandal", "Village", "Ward", "Name", "Surname", "Father/Husband", 
               "Age", "Gender", "Mobile", "House No", "Status", "Party", "Caste", "Religion", "Occupation", "Timestamp"]
    writer.writerow(headers)
    for row in rows: writer.writerow(row)
        
    output.seek(0)
    filename = f"master_export_{filter.scope_type}_{datetime.utcnow().strftime('%Y%m%d%H%M')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
# --- ANALYTICS EXPORT (EXCEL/CSV) ---
@app.get('/analytics/export/{survey_id}')
async def export_survey_analytics(survey_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    res_s = await db.execute(select(Survey).filter(Survey.id == survey_id))
    survey = res_s.scalar()
    if not survey:
        raise HTTPException(status_code=404, detail='Survey not found')
    
    res_v = await db.execute(select(SurveyVoter).filter(SurveyVoter.survey_id == survey_id))
    results = res_v.scalars().all()
    
    import csv
    import io
    
    headers = ['Voter ID', 'Name', 'Surname', 'Father/Husband', 'Age', 'Gender', 'Ward', 'House No', 'Mobile', 'Status', 'Expected Party', 'Caste', 'Religion', 'Occupation']
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    
    for row in results:
        writer.writerow([
            row.master_voter_id, row.voter_name, row.surname, 
            getattr(row, "relation_name", ""), row.age, row.gender, 
            row.ward_no, getattr(row, "house_no", ""), row.mobile_no, 
            row.voter_status, row.expected_party, row.caste, 
            row.religion, row.occupation
        ])
    
    output.seek(0)
    filename = f'survey_{survey_id}_export.csv'
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

# --- 14. SURVEY ASSIGNMENT APIS (Phase 5) ---
class AssignmentRequest(BaseModel):
    survey_id: int
    surveyor_id: int

@app.post("/surveys/assign")
async def assign_surveyor(req: AssignmentRequest, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    res = await db.execute(select(SurveyAssignment).filter(
        SurveyAssignment.survey_id == req.survey_id,
        SurveyAssignment.surveyor_id == req.surveyor_id
    ))
    existing = res.scalar()

    if existing:
        if existing.status == "REVOKED":
            existing.status = "ACTIVE"
            await db.commit()
            return {"status": "success", "message": "Re-activated assignment"}
        return {"status": "success", "message": "Already assigned"}
    
    new_assign = SurveyAssignment(
        survey_id=req.survey_id,
        surveyor_id=req.surveyor_id,
        status="ACTIVE"
    )
    db.add(new_assign)
    await db.commit()
    return {"status": "success", "message": "Assigned successfully"}

@app.post("/surveys/unassign")
async def unassign_surveyor(req: AssignmentRequest, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    res = await db.execute(select(SurveyAssignment).filter(
        SurveyAssignment.survey_id == req.survey_id,
        SurveyAssignment.surveyor_id == req.surveyor_id
    ))
    existing = res.scalar()

    if existing:
        existing.status = "REVOKED"
        await db.commit()
    
    return {"status": "success", "message": "Unassigned successfully"}

@app.delete("/surveys/{survey_id}")
async def delete_survey(survey_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, delete
    # 1. Check if survey exists
    res = await db.execute(select(Survey).filter(Survey.id == survey_id))
    survey = res.scalar()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    # Validation Rules
    if survey.status in ["COMPLETED", "ARCHIVED"]:
        raise HTTPException(status_code=400, detail="Cannot delete COMPLETED or ARCHIVED surveys. Please Archive only.")
    
    # 2. Delete related data first (cascade)
    await db.execute(delete(SurveyVoter).filter(SurveyVoter.survey_id == survey_id))
    await db.execute(delete(SurveyAssignment).filter(SurveyAssignment.survey_id == survey_id))
    
    # 3. Delete survey
    db.delete(survey)
    await db.commit()
    
    return {"status": "success", "message": "Survey and all related records deleted"}

# --- 15. STATIC & DASHBOARD ROUTING (Root Fallback) ---
# Simple root fallback using mount only (StaticFiles with html=True handles / automatically)

# Explicit routes for Dashboard and Mobile App as requested
@app.get("/dashboard", response_class=FileResponse)
async def serve_dashboard_link():
    """Serves the dashboard entry point"""
    return FileResponse("static/index.html")

@app.get("/app", response_class=FileResponse)
async def serve_app_link():
    """Serves the mobile app entry point"""
    return FileResponse("static/index.html")

# --- STARTUP EVENT ---
# Duplicate Startup Event Removed

# Duplicate mounts to ensure backward compatibility and asset resolution
app.mount("/static", StaticFiles(directory="static", html=True), name="static_path")
app.mount("/app_static", StaticFiles(directory="static", html=True), name="app_path_static")

# Root fallback mount - MUST BE LAST. This serves as both / and all asset requests
app.mount("/", StaticFiles(directory="static", html=True), name="root_static")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)




