import asyncio
from voter_api.database import AsyncSessionLocal
from voter_api.main import SurveyorRequest
from sqlalchemy import select

async def check_surveyors():
    async with AsyncSessionLocal() as db:
        print("--- CHECKING SURVEYOR REQUESTS ---")
        res = await db.execute(select(SurveyorRequest))
        reqs = res.scalars().all()
        for r in reqs:
            print(f"ID: {r.id} | Name: {r.name} | Mobile: {r.mobile_no} | Status: {r.status} | Role: {r.role}")
            
        if not reqs:
            print("No surveyor requests found.")

if __name__ == "__main__":
    asyncio.run(check_surveyors())
