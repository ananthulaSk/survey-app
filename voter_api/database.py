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
    # CLOUD RUN FIX: Use /tmp/voters.db because the /app directory might be read-only.
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
