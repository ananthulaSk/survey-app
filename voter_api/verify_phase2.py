from database import SessionLocal
from main import Survey, SurveyVoter, VoterMaster, create_survey, SurveyCreate

def verify_phase2():
    db = SessionLocal()
    
    print("--- 1. Checking Master Data ---")
    master_count = db.query(VoterMaster).count()
    print(f"Total Master Voters: {master_count}")
    
    if master_count == 0:
        print("ERROR: No master data found. Please seed DB first.")
        # return
        
    print("\n--- 2. Creating Test Survey (Ward 1) ---")
    # Simulate API call logic
    survey_input = SurveyCreate(name="Verification Survey", scope_type="WARD", scope_value="1")
    
    try:
        # Check if survey already exists to avoid dupes in this run
        existing = db.query(Survey).filter(Survey.name == "Verification Survey").first()
        if existing:
            print("Survey already exists, using ID:", existing.id)
            survey_id = existing.id
        else:
            result = create_survey(survey_input, db)
            print("Survey Created:", result)
            survey_id = result["survey_id"]

        print("\n--- 3. Verifying Snapshot ---")
        snapshot_count = db.query(SurveyVoter).filter(SurveyVoter.survey_id == survey_id).count()
        print(f"Snapshot Voters for Survey {survey_id}: {snapshot_count}")
        
        if snapshot_count == 0:
            print("WARN: Snapshot is empty. Does Ward 1 have voters?")
        else:
            print("SUCCESS: Snapshot created.")
            
            # Check data integrity
            sample = db.query(SurveyVoter).filter(SurveyVoter.survey_id == survey_id).first()
            print(f"Sample Snapshot Voter: {sample.voter_name} (Master ID: {sample.master_voter_id})")
            
            print("\n--- 4. Verify Read Isolation ---")
            # Update Snapshot
            sample.expected_party = "TEST_PARTY"
            db.commit()
            print("Updated Snapshot Voter with Party: TEST_PARTY")
            
            # Check Master
            master = db.query(VoterMaster).filter(VoterMaster.voter_id == sample.master_voter_id).first()
            print(f"Master Voter Party: {master.expected_party}")
            
            if master.expected_party != "TEST_PARTY":
                print("SUCCESS: Master data is UNTOUCHED.")
            else:
                print("FAIL: Master data was modified!")
                
    except Exception as e:
        print(f"Verification Failed: {e}")
        
    db.close()

if __name__ == "__main__":
    verify_phase2()
