from database import engine, Base
from main import Survey, SurveyVoter

def migrate():
    print("Creating new tables for Survey Infrastructure...")
    # This will create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    print("Migration Complete. 'surveys' and 'survey_voters' tables created.")

if __name__ == "__main__":
    migrate()
