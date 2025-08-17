"""
Database Initialization Script for Render Deployment

This script:
1. Creates all necessary database tables
2. Ensures the pgvector extension is installed
3. Can be run safely multiple times

Run this script after deployment:
python init_render_database.py
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path
parent_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(parent_dir)

# Import app modules
from app.models.database import Base
from app.database import engine

def init_database():
    """Initialize the database with required tables and extensions"""
    try:
        # Create tables from SQLAlchemy models
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
        
        # Check and create pgvector extension
        with engine.connect() as conn:
            logger.info("Checking for pgvector extension...")
            result = conn.execute(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"))
            has_vector = result.scalar()
            
            if not has_vector:
                logger.info("Creating pgvector extension...")
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                logger.info("pgvector extension created successfully.")
            else:
                logger.info("pgvector extension already exists.")
        
        logger.info("Database initialization completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    logger.info("Starting database initialization...")
    success = init_database()
    
    if success:
        logger.info("Database initialization completed successfully.")
        
        # Check if we need to populate the database with initial data
        try:
            from app.models.database import Offer
            from app.database import get_db_sync
            
            db = next(get_db_sync())
            offer_count = db.query(Offer).count()
            logger.info(f"Current offers in database: {offer_count}")
            
            if offer_count == 0:
                logger.info("Database is empty. Fetching initial data from Cuelinks API...")
                
                # Import and run the data fetching script
                import subprocess
                import sys
                
                # Run the fetch script
                result = subprocess.run([
                    sys.executable, 
                    "/app/scripts/fetch_and_embed_all_offers.py"
                ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
                
                if result.returncode == 0:
                    logger.info("✅ Data fetching completed successfully!")
                    logger.info(f"Output: {result.stdout}")
                else:
                    logger.warning(f"⚠️ Data fetching failed: {result.stderr}")
                    logger.info("Application will start anyway. Data can be fetched later via API.")
            else:
                logger.info(f"✅ Database already contains {offer_count} offers. Skipping data fetch.")
                
        except Exception as e:
            logger.warning(f"⚠️ Error checking/fetching data: {str(e)}")
            logger.info("Application will start anyway. Data can be fetched later via API.")
        
        sys.exit(0)
    else:
        logger.error("Database initialization failed.")
        sys.exit(1)
