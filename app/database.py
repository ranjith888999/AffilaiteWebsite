from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.models.database import Base
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

# Database configuration for Supabase
DATABASE_URL = f"postgresql://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}?sslmode=require"
ASYNC_DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"

# Create engine with optimized settings for Supabase
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,  # Disable SQL logging for better performance
    connect_args={
        "sslmode": "require",
        "options": "-c timezone=utc"
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create async engine for embedding-based search with Supabase settings
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "ssl": "require",
        "server_settings": {
            "timezone": "utc"
        }
    }
)
AsyncSessionLocal = sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

def create_tables():
    """Create tables if they don't exist"""
    Base.metadata.create_all(bind=engine)

def reset_database():
    """Drop all tables and recreate them (WARNING: all data will be lost)"""
    try:
        logger.warning("Dropping all database tables!")
        Base.metadata.drop_all(bind=engine)
        logger.info("Recreating database tables")
        Base.metadata.create_all(bind=engine)
        logger.info("Database reset complete")
        return True
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return False

def get_db():
    """Async database session for FastAPI endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_sync():
    """Synchronous database session for non-async contexts"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    """Async database session for embedding-based search"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        # Don't explicitly close the session here - it will be closed by the context manager
