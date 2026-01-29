from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

import os

# --- DATABASE CONFIG ---
# PRIORITY 1: Environment Variable (Cloud SQL / Production)
# PRIORITY 2: Local SQLite Fallback

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Production (PostgreSQL / Cloud SQL)
    # Ensure sqlalchemy compatible postgresql+asyncpg:// scheme
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(DATABASE_URL)
else:
    # Local Development / Cloud Run Ephemeral Fallback
    if os.name == 'nt': # Windows
        SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./voters.db"
    else: # Linux / Cloud Run
        # CLOUD RUN FIX: Use /tmp because system dirs might be read-only
        SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:////tmp/voters.db"
    
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

# Async Dependency to get a DB session
async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()

# Keep names compatible where possible, but use Async equivalents
SessionLocal = AsyncSessionLocal
