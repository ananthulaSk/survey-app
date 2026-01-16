from sqlalchemy.orm import Session
from database import SessionLocal, engine
from main import DistrictMaster, MandalMaster, VillageMaster, WardMaster

# Full 33 Districts of Telangana
TELANGANA_DISTRICTS = [
    "Adilabad", "Bhadradri Kothagudem", "Hanumakonda", "Hyderabad", "Jagtial", 
    "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar", 
    "Khammam", "Komaram Bheem Asifabad", "Mahabubabad", "Mahabubnagar", "Mancherial", 
    "Medak", "Medchal-Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda", 
    "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla", 
    "Ranga Reddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", 
    "Wanaparthy", "Warangal", "Yadadri Bhuvanagiri"
]

def seed_geo_data():
    db = SessionLocal()
    try:
        print("[GEO-SEED] Starting District Seeding...")
        
        # 1. Seed Districts
        for d_name in TELANGANA_DISTRICTS:
            existing = db.query(DistrictMaster).filter(DistrictMaster.name == d_name).first()
            if not existing:
                print(f" -> Adding District: {d_name}")
                new_dist = DistrictMaster(name=d_name)
                db.add(new_dist)
            else:
                pass # Already exists
        db.commit()

        # 2. Seed Sample Mandals (For Testing)
        # Yadadri (Focus Area)
        yadadri = db.query(DistrictMaster).filter(DistrictMaster.name == "Yadadri Bhuvanagiri").first()
        if yadadri:
            sample_mandals = ["Choutuppal", "Bhuvanagiri", "Alair", "Mothkur", "Turkapally"]
            for m_name in sample_mandals:
                mandal = db.query(MandalMaster).filter(MandalMaster.name == m_name, MandalMaster.district_id == yadadri.id).first()
                if not mandal:
                    print(f" -> Adding Mandal: {m_name}")
                    mandal = MandalMaster(name=m_name, district_id=yadadri.id)
                    db.add(mandal)
                    db.flush() # Need ID for village
                
                # 3. Seed Village (Generic "Main Village" for each Mandal for now)
                v_name = f"{m_name} Village"
                village = db.query(VillageMaster).filter(VillageMaster.name == v_name, VillageMaster.mandal_id == mandal.id).first()
                if not village:
                    print(f"   -> Adding Village: {v_name}")
                    village = VillageMaster(name=v_name, mandal_id=mandal.id)
                    db.add(village)
                    db.flush()
                    
                    # 4. Seed Wards (1 to 10)
                    for i in range(1, 11):
                        db.add(WardMaster(name=f"Ward {i}", village_id=village.id))
            
            db.commit()

        # Ranga Reddy (Sample)
        rr = db.query(DistrictMaster).filter(DistrictMaster.name == "Ranga Reddy").first()
        if rr:
             exists = db.query(MandalMaster).filter(MandalMaster.name == "Serilingampally", MandalMaster.district_id == rr.id).first()
             if not exists:
                 db.add(MandalMaster(name="Serilingampally", district_id=rr.id))
                 db.commit()

        print("[GEO-SEED] Seeding Complete!")

    except Exception as e:
        print(f"[GEO-SEED] Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_geo_data()
