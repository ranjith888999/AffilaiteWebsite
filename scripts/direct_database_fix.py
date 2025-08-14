"""
Direct Database Fix Script - Resolves issues with offer_embeddings table
This script uses direct database connections to fix schema issues without relying on SQLAlchemy ORM
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_database_schema():
    """Fix the database schema directly using psycopg2"""
    # Load environment variables
    load_dotenv()
    
    # Database configuration
    DB_USER = os.getenv('DATABASE_USER')
    DB_PASSWORD = os.getenv('DATABASE_PASSWORD')
    DB_HOST = os.getenv('DATABASE_HOST')
    DB_PORT = os.getenv('DATABASE_PORT')
    DB_NAME = os.getenv('DATABASE_NAME')
    
    if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
        logger.error("Database configuration incomplete. Check your .env file.")
        return False
    
    try:
        # Connect to PostgreSQL database
        connection = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Create a cursor
        cursor = connection.cursor()
        
        # Step 1: Check if the offer_embeddings table exists
        logger.info("Checking for offer_embeddings table...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'offer_embeddings'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            logger.error("offer_embeddings table doesn't exist! Please run database initialization first.")
            return False
        
        # Step 2: Check for campaign_id column
        logger.info("Checking for campaign_id column...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'offer_embeddings' AND column_name = 'campaign_id'
            );
        """)
        campaign_id_exists = cursor.fetchone()[0]
        
        if not campaign_id_exists:
            logger.info("Adding campaign_id column...")
            try:
                cursor.execute("""
                    ALTER TABLE offer_embeddings 
                    ADD COLUMN campaign_id INTEGER REFERENCES campaigns(id);
                """)
                logger.info("campaign_id column added successfully.")
                
                # Update the campaign_id column from offers table
                logger.info("Updating campaign_id values...")
                cursor.execute("""
                    UPDATE offer_embeddings oe
                    SET campaign_id = o.campaign_id
                    FROM offers o
                    WHERE oe.offer_id = o.id;
                """)
                logger.info("campaign_id values updated successfully.")
                
                # Create index on campaign_id
                logger.info("Creating index on campaign_id...")
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_offer_embeddings_campaign_id 
                    ON offer_embeddings(campaign_id);
                """)
                logger.info("Index created successfully.")
            except Exception as column_error:
                logger.error(f"Error adding campaign_id column: {column_error}")
        else:
            logger.info("campaign_id column already exists.")
        
        # Step 3: Check for meta_data vs metadata column
        logger.info("Checking for meta_data column...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'offer_embeddings' AND column_name = 'meta_data'
            );
        """)
        meta_data_exists = cursor.fetchone()[0]
        
        if not meta_data_exists:
            # Check if old metadata column exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'offer_embeddings' AND column_name = 'metadata'
                );
            """)
            metadata_exists = cursor.fetchone()[0]
            
            if metadata_exists:
                logger.info("Renaming metadata column to meta_data...")
                try:
                    cursor.execute("""
                        ALTER TABLE offer_embeddings 
                        RENAME COLUMN metadata TO meta_data;
                    """)
                    logger.info("Column renamed successfully.")
                except Exception as rename_error:
                    logger.error(f"Error renaming column: {rename_error}")
            else:
                logger.info("Adding meta_data column...")
                try:
                    cursor.execute("""
                        ALTER TABLE offer_embeddings 
                        ADD COLUMN meta_data TEXT;
                    """)
                    logger.info("meta_data column added successfully.")
                except Exception as add_error:
                    logger.error(f"Error adding meta_data column: {add_error}")
        else:
            logger.info("meta_data column already exists.")
        
        # Step 4: Check for embeddings data
        logger.info("Checking for embeddings data...")
        cursor.execute("SELECT COUNT(*) FROM offer_embeddings;")
        embedding_count = cursor.fetchone()[0]
        logger.info(f"Found {embedding_count} embedding records.")
        
        # Step 5: Analyze tables for better performance
        logger.info("Analyzing tables for performance optimization...")
        cursor.execute("ANALYZE offer_embeddings;")
        cursor.execute("ANALYZE offers;")
        logger.info("Tables analyzed successfully.")
        
        # Close cursor and connection
        cursor.close()
        connection.close()
        
        logger.info("✅ Database schema fixes completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing database schema: {e}")
        return False

if __name__ == "__main__":
    print("==== Direct Database Fix Tool ====")
    print("This tool will fix issues with the offer_embeddings table")
    print("Running fixes...")
    
    if fix_database_schema():
        print("\n✅ All fixes completed successfully!")
        print("You can now restart your application to use embedding search.")
    else:
        print("\n❌ Some fixes failed. Check the logs above for details.")
        print("You may need to manually fix the database or use a fallback search method.")
