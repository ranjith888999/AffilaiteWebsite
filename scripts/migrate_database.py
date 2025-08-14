"""
Database Migration Script - Link existing campaigns and offers
This script should be run once after updating the database models.
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Column, Integer, ForeignKey
from sqlalchemy.orm import sessionmaker
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from app.models.database import Base, Campaign, Offer, OfferEmbedding

def migrate_database():
    # Load environment variables
    load_dotenv()
    
    # Database configuration
    DATABASE_URL = f"postgresql://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"
    
    # Create engine and session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        logger.info("Starting database migration...")
        
        # 1. Ensure all tables exist with the new schema
        logger.info("Creating/updating tables if needed...")
        Base.metadata.create_all(bind=engine)
        
        # 2. Check if we need to handle campaigns
        campaign_count = session.query(Campaign).count()
        logger.info(f"Found {campaign_count} existing campaigns")
        
        # 3. Get all offers with their original Cuelinks campaign_id values
        # We need to use raw SQL here because the model has already been updated
        logger.info("Fetching offer data...")
        
        # Create temporary mapping from offer to original Cuelinks campaign_id
        offers_with_cuelinks_id = []
        for row in session.execute(text("SELECT id, campaign_id FROM offers")):
            offers_with_cuelinks_id.append((row[0], row[1]))
        
        logger.info(f"Found {len(offers_with_cuelinks_id)} offers to process")
        
        # 4. First create any missing campaigns
        campaigns_created = 0
        campaign_mapping = {}  # Maps Cuelinks campaign_id to our database campaign.id
        
        # Build mapping of existing campaigns
        for campaign in session.query(Campaign).all():
            campaign_mapping[campaign.campaign_id] = campaign.id
        
        # Find unique Cuelinks campaign IDs that need to be created
        unique_cuelinks_campaign_ids = set()
        for _, cuelinks_campaign_id in offers_with_cuelinks_id:
            if cuelinks_campaign_id and cuelinks_campaign_id not in campaign_mapping:
                unique_cuelinks_campaign_ids.add(cuelinks_campaign_id)
        
        # Create missing campaigns
        for cuelinks_campaign_id in unique_cuelinks_campaign_ids:
            campaign = Campaign(
                campaign_id=cuelinks_campaign_id,
                name=f"Campaign {cuelinks_campaign_id}",
                status="active"
            )
            session.add(campaign)
            campaigns_created += 1
        
        # Flush to get IDs for the new campaigns
        session.flush()
        
        # Rebuild mapping with newly created campaigns
        campaign_mapping = {}
        for campaign in session.query(Campaign).all():
            campaign_mapping[campaign.campaign_id] = campaign.id
            
        # 5. Now update all offers with the correct campaign_id reference
        offers_updated = 0
        for offer_id, cuelinks_campaign_id in offers_with_cuelinks_id:
            if cuelinks_campaign_id in campaign_mapping:
                # Update the offer with the correct campaign_id (which is now a foreign key)
                session.execute(
                    text("UPDATE offers SET campaign_id = :campaign_id WHERE id = :offer_id"),
                    {"campaign_id": campaign_mapping[cuelinks_campaign_id], "offer_id": offer_id}
                )
                offers_updated += 1
        
        # 6. Update the OfferEmbedding table to include campaign_id
        # First we need to add any missing campaign_id values
        embeddings_updated = 0
        for row in session.execute(text("""
            UPDATE offer_embeddings oe
            SET campaign_id = (
                SELECT o.campaign_id 
                FROM offers o 
                WHERE o.id = oe.offer_id
            )
            WHERE oe.campaign_id IS NULL
            RETURNING oe.id
        """)):
            embeddings_updated += 1
        
        # Commit all changes
        session.commit()
        logger.info(f"Migration completed successfully!")
        logger.info(f"Created {campaigns_created} new campaigns")
        logger.info(f"Updated {offers_updated} offers")
        logger.info(f"Updated {embeddings_updated} embeddings")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error during migration: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    migrate_database()
