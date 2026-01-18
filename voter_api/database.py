from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os

# --- DATABASE CONFIG ---
# PRIORITY 1: Environment Variable (Cloud SQL / Production)
# PRIORITY 2: Local SQLite Fallback

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Production (PostgreSQL / Cloud SQL)
    # Ensure sqlalchemy compatible postgresql:// scheme
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(DATABASE_URL)
else:
    # Local Development / Cloud Run Ephemeral Fallback
    # Check OS to decide path
    if os.name == 'nt': # Windows
        DISPLAY_DB_PATH = "voters.db" # Local file in project root
        SQLALCHEMY_DATABASE_URL = "sqlite:///./voters.db"
    else: # Linux / Cloud Run
        # CLOUD RUN FIX: Use /tmp because system dirs might be read-only
        # WARNING: This is Ephemeral! Data is lost on restart.
        DISPLAY_DB_PATH = "/tmp/voters.db"
        SQLALCHEMY_DATABASE_URL = "sqlite:////tmp/voters.db"
    
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
