"""
Script to check the database embeddings
"""
import sys
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from sqlalchemy import create_engine, text
from app.database import DATABASE_URL

def check_db():
    """Check the database embeddings"""
    logger.info(f"Connecting to database: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check offer_embeddings table
            result = conn.execute(text('SELECT COUNT(*) FROM offer_embeddings'))
            count = result.scalar()
            logger.info(f"Number of embeddings in database: {count}")
            
            # Check if there are any offers
            result = conn.execute(text('SELECT COUNT(*) FROM offers'))
            offers_count = result.scalar()
            logger.info(f"Number of offers in database: {offers_count}")
            
            # Sample some embeddings
            if count > 0:
                logger.info("Sampling some embeddings:")
                result = conn.execute(text('SELECT id, offer_id, campaign_id, content_type, length(embedding::text) FROM offer_embeddings LIMIT 5'))
                for row in result:
                    logger.info(f"ID: {row[0]}, Offer ID: {row[1]}, Campaign ID: {row[2]}, Type: {row[3]}, Embedding Size: {row[4]}")
            
            # Check column structure
            logger.info("Checking offer_embeddings table structure:")
            result = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'offer_embeddings'
                ORDER BY ordinal_position
            """))
            for row in result:
                logger.info(f"Column: {row[0]}, Type: {row[1]}")
    
    except Exception as e:
        logger.error(f"Error checking database: {str(e)}")

if __name__ == "__main__":
    check_db()
