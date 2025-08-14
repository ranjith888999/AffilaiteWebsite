"""
Database Migration Verification Script
This script verifies that the data has been properly migrated to the new schema.
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from app.models.database import Base, Campaign, Offer, OfferEmbedding

def verify_database_migration():
    """Verify that the database migration was successful"""
    # Load environment variables
    load_dotenv()
    
    # Database configuration
    DATABASE_URL = f"postgresql://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"
    
    # Create engine and session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        logger.info("Verifying database migration...")
        
        # 1. Check if campaigns exist
        campaign_count = session.query(Campaign).count()
        logger.info(f"Found {campaign_count} campaigns")
        
        if campaign_count == 0:
            logger.error("No campaigns found! Migration may have failed.")
            return False
        
        # 2. Check if offers exist and have valid campaign_id references
        offer_count = session.query(Offer).count()
        logger.info(f"Found {offer_count} offers")
        
        if offer_count == 0:
            logger.error("No offers found! Migration may have failed.")
            return False
        
        # 3. Check for offers with null campaign_id
        null_campaign_offers = session.query(Offer).filter(Offer.campaign_id.is_(None)).count()
        logger.info(f"Found {null_campaign_offers} offers with NULL campaign_id")
        
        if null_campaign_offers > 0:
            logger.warning(f"There are {null_campaign_offers} offers with NULL campaign_id!")
        
        # 4. Check for valid relationships
        valid_relationships = session.query(Offer).join(Campaign).count()
        logger.info(f"Found {valid_relationships} offers with valid campaign relationships")
        
        if valid_relationships != offer_count - null_campaign_offers:
            logger.error("Some offers have invalid campaign relationships!")
            return False
        
        # 5. Check for embeddings (if any)
        embedding_count = session.query(OfferEmbedding).count()
        logger.info(f"Found {embedding_count} offer embeddings")
        
        if embedding_count > 0:
            # Check for embeddings with valid campaign_id
            valid_embedding_campaign = session.query(OfferEmbedding).filter(OfferEmbedding.campaign_id.isnot(None)).count()
            logger.info(f"Found {valid_embedding_campaign} embeddings with valid campaign_id")
            
            if valid_embedding_campaign < embedding_count:
                logger.warning(f"There are {embedding_count - valid_embedding_campaign} embeddings missing campaign_id!")
        
        # 6. Run a sample query to test campaign name search
        if campaign_count > 0 and offer_count > 0:
            # Get a sample campaign name
            sample_campaign = session.query(Campaign).first()
            if sample_campaign:
                sample_name = sample_campaign.name
                logger.info(f"Testing search with sample campaign name: '{sample_name}'")
                
                # Search for offers with this campaign name
                results = session.query(Offer).join(Campaign).filter(Campaign.name.ilike(f"%{sample_name}%")).count()
                logger.info(f"Found {results} offers with campaign name '{sample_name}'")
        
        logger.info("Database migration verification completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying database migration: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    verify_database_migration()
