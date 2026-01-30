from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def async_seed_geo_data(db: AsyncSession):
    # Import locally to avoid circular dependency with main.py
    from main import DistrictMaster, MandalMaster, VillageMaster, WardMaster
    
    TELANGANA_DISTRICTS = [
        "Adilabad", "Bhadradri Kothagudem", "Hanumakonda", "Hyderabad", "Jagtial", 
        "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar", 
        "Khammam", "Komaram Bheem Asifabad", "Mahabubabad", "Mahabubnagar", "Mancherial", 
        "Medak", "Medchal-Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda", 
        "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla", 
        "Ranga Reddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", 
        "Wanaparthy", "Warangal", "Yadadri Bhuvanagiri"
    ]

    try:
        print("[GEO-SEED] Starting District Seeding...")
        
        # 1. Seed Districts
        for d_name in TELANGANA_DISTRICTS:
            res = await db.execute(select(DistrictMaster).filter(DistrictMaster.name == d_name))
            existing = res.scalar()
            if not existing:
                print(f" -> Adding District: {d_name}")
                new_dist = DistrictMaster(name=d_name)
                db.add(new_dist)
        await db.commit()

        # 2. Seed Sample Mandals
        res_yadadri = await db.execute(select(DistrictMaster).filter(DistrictMaster.name == "Yadadri Bhuvanagiri"))
        yadadri = res_yadadri.scalar()
        if yadadri:
            sample_mandals = ["Choutuppal", "Bhuvanagiri", "Alair", "Mothkur", "Turkapally"]
            for m_name in sample_mandals:
                res_m = await db.execute(select(MandalMaster).filter(MandalMaster.name == m_name, MandalMaster.district_id == yadadri.id))
                mandal = res_m.scalar()
                if not mandal:
                    print(f" -> Adding Mandal: {m_name}")
                    mandal = MandalMaster(name=m_name, district_id=yadadri.id)
                    db.add(mandal)
                    await db.flush()
                
                # 3. Seed Villages
                villages_to_seed = [f"{m_name} Village"]
                if m_name == "Choutuppal":
                    villages_to_seed.append("Aregudem")
                
                for v_name in villages_to_seed:
                    res_v = await db.execute(select(VillageMaster).filter(VillageMaster.name == v_name, VillageMaster.mandal_id == mandal.id))
                    village = res_v.scalar()
                    if not village:
                        print(f"   -> Adding Village: {v_name}")
                        village = VillageMaster(name=v_name, mandal_id=mandal.id)
                        db.add(village)
                        await db.flush()
                        
                        # 4. Seed Wards (1 to 10)
                        for i in range(1, 11):
                            db.add(WardMaster(name=f"Ward {i}", village_id=village.id))
            
            await db.commit()
    except Exception as e:
        print(f"[GEO-SEED] Error: {e}")
        await db.rollback()
        # Non-critical, just log
    finally:
        # In async, we usually don't close here if dependency handles it, 
        # but for a script it's fine.
        pass

if __name__ == "__main__":
    seed_geo_data()
