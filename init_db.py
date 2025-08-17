#!/usr/bin/env python
"""
Database Initialization Script for Docker

This script:
1. Creates necessary database tables
2. Initializes pgvector extension if needed
3. Can be run safely multiple times
"""

import sys
import os
import logging
from sqlalchemy import create_engine, text

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from app.models.database import Base
from app.database import engine

def init_database():
    """Initialize the database with required tables"""
    try:
        # Create tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Initialize pgvector extension
        with engine.connect() as conn:
            logger.info("Checking pgvector extension...")
            result = conn.execute(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"))
            has_vector = result.scalar()
            
            if not has_vector:
                logger.info("Creating pgvector extension...")
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                logger.info("pgvector extension created successfully")
            else:
                logger.info("pgvector extension already exists")
        
        logger.info("Database initialization completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting database initialization...")
    success = init_database()
    sys.exit(0 if success else 1)
