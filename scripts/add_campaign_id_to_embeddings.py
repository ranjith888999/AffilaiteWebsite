"""
Migration script to add campaign_id column to offer_embeddings table
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_campaign_id_column():
    """Add campaign_id column to offer_embeddings table"""
    # Load environment variables
    load_dotenv()
    
    # Database configuration
    DB_USER = os.getenv('DATABASE_USER')
    DB_PASSWORD = os.getenv('DATABASE_PASSWORD')
    DB_HOST = os.getenv('DATABASE_HOST')
    DB_PORT = os.getenv('DATABASE_PORT')
    DB_NAME = os.getenv('DATABASE_NAME')
    
    # Connect to database
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        # Use direct SQL to add the column
        engine = create_engine(DATABASE_URL)
        
        # Check if column exists
        with engine.connect() as conn:
            # Check if the column already exists
            check_column = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'offer_embeddings' AND column_name = 'campaign_id'
            """)
            result = conn.execute(check_column)
            column_exists = result.fetchone() is not None
            
            if column_exists:
                logger.info("campaign_id column already exists in offer_embeddings table")
                return
            
            # Add the column
            logger.info("Adding campaign_id column to offer_embeddings table")
            add_column = text("""
                ALTER TABLE offer_embeddings 
                ADD COLUMN campaign_id INTEGER REFERENCES campaigns(id)
            """)
            conn.execute(add_column)
            
            # Create index
            create_index = text("""
                CREATE INDEX IF NOT EXISTS idx_offer_embeddings_campaign_id ON offer_embeddings(campaign_id)
            """)
            conn.execute(create_index)
            
            # Update the campaign_id column based on offers table
            update_campaign_id = text("""
                UPDATE offer_embeddings oe
                SET campaign_id = o.campaign_id
                FROM offers o
                WHERE oe.offer_id = o.id
            """)
            result = conn.execute(update_campaign_id)
            
            # Also check for the meta_data column (renamed from metadata)
            check_meta_data = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'offer_embeddings' AND column_name = 'meta_data'
            """)
            result = conn.execute(check_meta_data)
            meta_data_exists = result.fetchone() is not None
            
            if not meta_data_exists:
                # Check if old metadata column exists
                check_old_metadata = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'offer_embeddings' AND column_name = 'metadata'
                """)
                result = conn.execute(check_old_metadata)
                old_metadata_exists = result.fetchone() is not None
                
                if old_metadata_exists:
                    # Rename metadata to meta_data
                    logger.info("Renaming 'metadata' column to 'meta_data'")
                    rename_column = text("""
                        ALTER TABLE offer_embeddings 
                        RENAME COLUMN metadata TO meta_data
                    """)
                    conn.execute(rename_column)
                else:
                    # Add meta_data column
                    logger.info("Adding 'meta_data' column")
                    add_meta_data = text("""
                        ALTER TABLE offer_embeddings 
                        ADD COLUMN meta_data TEXT
                    """)
                    conn.execute(add_meta_data)
            
            # Commit all changes
            conn.commit()
            logger.info(f"Successfully added/updated columns in offer_embeddings table")
            
    except Exception as e:
        logger.error(f"Error updating offer_embeddings table: {e}")
        raise

if __name__ == "__main__":
    add_campaign_id_column()
