from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- DATABASE CONFIG ---
# FALLBACK: Use SQLite for local development to ensure it runs immediately
# without network/firewall issues.
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
