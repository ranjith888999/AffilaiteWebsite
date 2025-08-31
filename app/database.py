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
DATABASE_USER = os.getenv('DATABASE_USER', 'default_user')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'default_password')
DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
DATABASE_PORT = os.getenv('DATABASE_PORT', '5432')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'default_db')

DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}?sslmode=require"
ASYNC_DATABASE_URL = f"postgresql+asyncpg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

# Global variables for engines
engine = None
async_engine = None
SessionLocal = None
AsyncSessionLocal = None
db_available = False

def initialize_database():
    global engine, async_engine, SessionLocal, AsyncSessionLocal, db_available
    if db_available:  # Already initialized
        return
        
    try:
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
                "options": "-c timezone=utc",
                "connect_timeout": 10  # Add connection timeout
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
                },
                "connect_timeout": 10  # Add connection timeout
            }
        )
        AsyncSessionLocal = sessionmaker(
            async_engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        db_available = True
        logger.info("Database connection established successfully.")
    except Exception as e:
        logger.warning(f"Database connection failed: {e}. Running in offline mode.")
        db_available = False

# Remove automatic initialization on import
# initialize_database()

def create_tables():
    """Create tables if they don't exist"""
    if not db_available or engine is None:
        logger.warning("Database not available, skipping table creation.")
        return
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
    if not db_available:
        initialize_database()  # Try to initialize if not already done
    if not db_available or SessionLocal is None:
        logger.warning("Database not available, yielding None.")
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_sync():
    """Synchronous database session for non-async contexts"""
    if not db_available:
        initialize_database()  # Try to initialize if not already done
    if not db_available or SessionLocal is None:
        logger.warning("Database not available, yielding None.")
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    """Async database session for embedding-based search"""
    if not db_available:
        initialize_database()  # Try to initialize if not already done
    if not db_available or AsyncSessionLocal is None:
        logger.warning("Database not available, yielding None.")
        yield None
        return
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        # Don't explicitly close the session here - it will be closed by the context manager
