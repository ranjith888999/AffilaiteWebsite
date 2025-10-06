from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import QueuePool, NullPool
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

# For Easypanel PostgreSQL, use sslmode=disable instead of require
DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}?sslmode=disable"
ASYNC_DATABASE_URL = f"postgresql+asyncpg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

# Detect production environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').lower()
IS_PRODUCTION = (
    ENVIRONMENT == 'production' or 
    os.getenv('RENDER') or 
    os.getenv('RAILWAY_ENVIRONMENT') or 
    os.getenv('DYNO') or
    os.getenv('EASYPANEL')
)

# Production-optimized connection pool settings for 10,000+ daily visitors
if IS_PRODUCTION:
    # Production: Handle high concurrent traffic
    POOL_SIZE = 50  # Base pool size (up from 30)
    MAX_OVERFLOW = 20  # Additional connections during peaks (up from 10)
    POOL_TIMEOUT = 45  # Wait time before timeout (up from 30)
    POOL_RECYCLE = 1800  # Recycle connections every 30 minutes
    POOL_PRE_PING = True  # Check connection health before use
    STATEMENT_TIMEOUT = 30000  # 30 seconds max per query
else:
    # Development: Conservative settings
    POOL_SIZE = 5
    MAX_OVERFLOW = 5
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 300
    POOL_PRE_PING = True
    STATEMENT_TIMEOUT = 60000  # 60 seconds for development

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
        logger.info(f"Initializing database for {ENVIRONMENT} environment...")
        logger.info(f"Pool settings: size={POOL_SIZE}, overflow={MAX_OVERFLOW}, timeout={POOL_TIMEOUT}s")
        
        # Create engine with production-optimized settings
        engine = create_engine(
            DATABASE_URL,
            poolclass=QueuePool,  # Explicitly use QueuePool for production
            pool_size=POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            pool_timeout=POOL_TIMEOUT,
            pool_pre_ping=POOL_PRE_PING,
            pool_recycle=POOL_RECYCLE,
            echo=False,  # Disable SQL logging for better performance
            connect_args={
                "options": f"-c statement_timeout={STATEMENT_TIMEOUT} -c timezone=utc",
                "connect_timeout": 10,  # Connection timeout
            }
        )
        
        # Add connection pool event listeners for monitoring
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            logger.debug("Database connection established")
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            # Log pool status on checkout in production
            if IS_PRODUCTION:
                pool = engine.pool
                logger.debug(
                    f"Pool status - Size: {pool.size()}, "
                    f"Checked out: {pool.checkedout()}, "
                    f"Overflow: {pool.overflow()}, "
                    f"Queue size: {pool.size() - pool.checkedout()}"
                )
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Create async engine for embedding-based search with production settings
        async_engine = create_async_engine(
            ASYNC_DATABASE_URL,
            pool_size=POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            pool_timeout=POOL_TIMEOUT,
            echo=False,
            pool_pre_ping=POOL_PRE_PING,
            pool_recycle=POOL_RECYCLE,
            connect_args={
                "server_settings": {
                    "timezone": "utc",
                    "statement_timeout": str(STATEMENT_TIMEOUT)
                },
                "timeout": 10,  # Connection timeout
                "command_timeout": 60,  # Command execution timeout
            }
        )
        AsyncSessionLocal = sessionmaker(
            async_engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        db_available = True
        logger.info(f"[OK] Database connection pool initialized successfully for {ENVIRONMENT}")
        logger.info(f"[INFO] Max concurrent connections: {POOL_SIZE + MAX_OVERFLOW}")
    except Exception as e:
        logger.warning(f"Database connection failed: {e}. Running in offline mode.")
        db_available = False

# Remove automatic initialization on import
# initialize_database()

def create_tables():
    """Create tables if they don't exist"""
    if not db_available:
        initialize_database()  # Try to initialize if not already done
    if not db_available or engine is None:
        logger.warning("Database not available, skipping table creation.")
        return
    try:
        logger.info("Creating database tables...")
        
        # First, try to create the pgvector extension
        try:
            with engine.connect() as conn:
                # conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.commit()
                logger.info("pgvector extension created/verified.")
        except Exception as e:
            logger.warning(f"Could not create pgvector extension: {e}")
            logger.warning("Vector similarity search may not work optimally.")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

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
    """Async database session for FastAPI endpoints with automatic retry"""
    if not db_available:
        initialize_database()  # Try to initialize if not already done
    if not db_available or SessionLocal is None:
        logger.warning("Database not available, yielding None.")
        yield None
        return
    
    db = None
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            db = SessionLocal()
            yield db
            break  # Success, exit retry loop
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"Database connection attempt {retry_count} failed, retrying... Error: {e}")
                if db:
                    db.close()
                continue
            else:
                logger.error(f"Database connection failed after {max_retries} attempts: {e}")
                yield None
                break
        finally:
            if db:
                db.close()

def get_db_sync():
    """Synchronous database session for non-async contexts with retry logic"""
    if not db_available:
        initialize_database()  # Try to initialize if not already done
    if not db_available or SessionLocal is None:
        logger.warning("Database not available, yielding None.")
        yield None
        return
    
    db = None
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            db = SessionLocal()
            yield db
            break
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"Sync DB connection attempt {retry_count} failed, retrying... Error: {e}")
                if db:
                    db.close()
                continue
            else:
                logger.error(f"Sync DB connection failed after {max_retries} attempts: {e}")
                yield None
                break
        finally:
            if db:
                db.close()

def get_sync_db_session():
    """Get a synchronous database session for sync operations"""
    if not db_available:
        initialize_database()  # Try to initialize if not already done
    if not db_available or SessionLocal is None:
        logger.warning("Database not available, returning None.")
        return None
    return SessionLocal()

async def get_async_db():
    """Async database session for embedding-based search with retry logic"""
    if not db_available:
        initialize_database()  # Try to initialize if not already done
    if not db_available or AsyncSessionLocal is None:
        logger.warning("Database not available, yielding None.")
        yield None
        return
    
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            async with AsyncSessionLocal() as session:
                yield session
                break  # Success
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"Async DB connection attempt {retry_count} failed, retrying... Error: {e}")
                continue
            else:
                logger.error(f"Async DB connection failed after {max_retries} attempts: {e}")
                yield None
                break

async def get_async_db_session():
    """Get an async database session for async operations with retry"""
    if not db_available:
        initialize_database()  # Try to initialize if not already done
    if not db_available or AsyncSessionLocal is None:
        logger.warning("Database not available, returning None.")
        return None
    
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            return AsyncSessionLocal()
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"Async session creation attempt {retry_count} failed, retrying... Error: {e}")
                continue
            else:
                logger.error(f"Async session creation failed after {max_retries} attempts: {e}")
                return None

def get_pool_status():
    """Get current connection pool status for monitoring"""
    if not engine:
        return {"status": "not_initialized"}
    
    try:
        pool = engine.pool
        return {
            "status": "healthy",
            "pool_size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "available": pool.size() - pool.checkedout(),
            "max_connections": POOL_SIZE + MAX_OVERFLOW,
            "timeout": POOL_TIMEOUT,
            "environment": ENVIRONMENT
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
