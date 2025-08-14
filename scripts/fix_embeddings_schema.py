"""
Fix Database Schema for Embeddings

This script:
1. Adds the campaign_id column to the offer_embeddings table
2. Creates appropriate indexes for campaign_id
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database imports
from sqlalchemy import text, create_engine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.getenv("DATABASE_HOST", "localhost")
DB_PORT = os.getenv("DATABASE_PORT", "5432")
DB_NAME = os.getenv("DATABASE_NAME", "postgres")
DB_USER = os.getenv("DATABASE_USER", "postgres")
DB_PASS = os.getenv("DATABASE_PASSWORD", "postgres")

# Build connection string (synchronous for schema modifications)
DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def fix_schema():
    """Add campaign_id column to offer_embeddings table"""
    engine = create_engine(DB_URL)
    
    with engine.connect() as connection:
        try:
            # Check if column exists
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'offer_embeddings' AND column_name = 'campaign_id'
            """)
            result = connection.execute(check_query)
            column_exists = result.fetchone() is not None
            
            if not column_exists:
                logger.info("Adding campaign_id column to offer_embeddings table...")
                
                # Add campaign_id column with a foreign key to campaigns table
                alter_query = text("""
                    ALTER TABLE offer_embeddings 
                    ADD COLUMN campaign_id INTEGER REFERENCES campaigns(id)
                """)
                connection.execute(alter_query)
                
                # Create index on campaign_id
                index_query = text("""
                    CREATE INDEX idx_offer_embeddings_campaign_id ON offer_embeddings(campaign_id)
                """)
                connection.execute(index_query)
                
                connection.commit()
                logger.info("Schema updated successfully!")
            else:
                logger.info("campaign_id column already exists in offer_embeddings table.")
                
        except Exception as e:
            connection.rollback()
            logger.error(f"Error fixing schema: {str(e)}")
            raise

def main():
    """Main function to run the schema fix"""
    logger.info("Starting database schema fix")
    
    try:
        fix_schema()
        logger.info("Database schema fix completed successfully!")
    except Exception as e:
        logger.error(f"Error in database schema fix: {str(e)}")

if __name__ == "__main__":
    main()
