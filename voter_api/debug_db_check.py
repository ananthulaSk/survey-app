from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base

# Setup
Base = declarative_base()
engine = create_engine('sqlite:///voters.db')
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Models
class SurveyorRequest(Base):
    __tablename__ = "surveyor_requests"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    mobile_no = Column(String)
    ward_no = Column(String)
    status = Column(String)

class SurveyVoter(Base):
    __tablename__ = "survey_voters"
    id = Column(Integer, primary_key=True)
    survey_id = Column(Integer)
    ward_no = Column(Integer)
    voter_name = Column(String)

class Survey(Base):
    __tablename__ = "surveys"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    status = Column(String)

# Checks
print("-" * 30)
print("DEBUG: Checking Data for User 'Shiva'")

# 1. Check User
shiva = db.query(SurveyorRequest).filter(SurveyorRequest.name.ilike('%shiva%')).first()
if shiva:
    print(f"User Found: {shiva.name}")
    print(f"  > Mobile: {shiva.mobile_no}")
    print(f"  > Ward: '{shiva.ward_no}' (Type: {type(shiva.ward_no)})")
    print(f"  > Status: {shiva.status}")
else:
    print("User 'Shiva' not found in DB.")

# 2. Check Surveys
print("\nDEBUG: Checking Active Surveys")
surveys = db.query(Survey).filter(Survey.status == "ACTIVE").all()
if surveys:
    for s in surveys:
        print(f"Survey ID {s.id}: {s.name} (Status: {s.status})")
        
        # Check Voters
        if shiva:
             # Try parsing Shiva's ward
             try:
                 ward_int = int(''.join(filter(str.isdigit, shiva.ward_no)))
                 print(f"  > Parsing Ward '{shiva.ward_no}' -> {ward_int}")
                 
                 count = db.query(SurveyVoter).filter(
                     SurveyVoter.survey_id == s.id,
                     SurveyVoter.ward_no == ward_int
                 ).count()
                 print(f"  > Voters in Ward {ward_int}: {count}")
                 
                 if count == 0:
                     print("    !! WARNING: Zero voters found. Checking distinct wards...")
                     distinct_wards = db.query(SurveyVoter.ward_no).filter(SurveyVoter.survey_id == s.id).distinct().all()
                     print(f"    Available Wards in Survey: {[w[0] for w in distinct_wards]}")

             except Exception as e:
                 print(f"  > Error parsing ward: {e}")

else:
    print("No ACTIVE surveys found.")

db.close()
print("-" * 30)
