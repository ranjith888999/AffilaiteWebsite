"""
Script to fetch offers from Cuelinks API and add them to the database with optimized embeddings.
This script:
1. Fetches all offers from Cuelinks API using pagination
2. Adds them to the database
3. Creates combined embeddings for each offer (including campaign, title, and description)
"""
import sys
import os
import requests
import json
import logging
import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import necessary modules
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.database import DATABASE_URL, ASYNC_DATABASE_URL
from app.models.database import Campaign, Offer, OfferEmbedding, Base
from sentence_transformers import SentenceTransformer

# Cuelinks API details
API_URL = "https://www.cuelinks.com/api/v2/offers.json"
API_KEY = "MUmQPF2MLjDzMOHi0PSCdOwI082JAfj6vRLLT1QcY00"  # Consider loading this from environment variable
HEADERS = {
    'Authorization': f'Token token={API_KEY}',
    'Content-Type': 'application/json'
}

# Create database engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create async engine for embeddings
async_engine = create_async_engine(ASYNC_DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Create tables if they don't exist
def create_tables():
    """Create database tables if they don't exist"""
    Base.metadata.create_all(bind=engine)

def fetch_all_offers():
    """Fetch all offers from Cuelinks API using pagination"""
    all_offers = []
    page = 1
    per_page = 100
    total_pages = 1  # Will be updated from the first API response
    
    logger.info(f"Starting to fetch offers from Cuelinks API")
    
    while page <= total_pages:
        try:
            logger.info(f"Fetching page {page} of offers (per_page={per_page})")
            url = f"{API_URL}?page={page}&per_page={per_page}"
            response = requests.get(url, headers=HEADERS)
            
            if response.status_code != 200:
                logger.error(f"Error fetching offers: {response.status_code} - {response.text}")
                break
                
            data = response.json()
            
            # Update total pages on first fetch
            if page == 1:
                total_count = data.get('total_count', 0)
                total_pages = (total_count + per_page - 1) // per_page
                logger.info(f"Total offers: {total_count}, Total pages: {total_pages}")
            
            # Add offers from this page to the list
            offers = data.get('offers', [])
            all_offers.extend(offers)
            logger.info(f"Fetched {len(offers)} offers from page {page}")
            
            # Go to next page
            page += 1
            
            # Sleep to avoid hitting rate limits
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error fetching offers: {str(e)}")
            break
    
    logger.info(f"Completed fetching offers. Total fetched: {len(all_offers)}")
    return all_offers

def save_campaigns_and_offers(offers_data: List[Dict]):
    """Save campaigns and offers to the database"""
    logger.info(f"Saving {len(offers_data)} offers to database")
    
    with SessionLocal() as session:
        # Process each offer
        processed_count = 0
        campaigns_created = 0
        offers_created = 0
        
        for offer_data in offers_data:
            try:
                # First, process the campaign
                campaign_data = offer_data.get('advertiser', {})
                campaign_id = campaign_data.get('id')
                
                # Check if campaign already exists
                campaign = session.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
                
                if not campaign:
                    # Create new campaign
                    campaign = Campaign(
                        campaign_id=campaign_id,
                        name=campaign_data.get('name', ''),
                        description=campaign_data.get('description', ''),
                        status=campaign_data.get('status', 'active'),
                        category=json.dumps(campaign_data.get('categories', []))
                    )
                    session.add(campaign)
                    session.flush()  # Flush to get the ID
                    campaigns_created += 1
                
                # Now process the offer
                offer_id = offer_data.get('id')
                
                # Check if offer already exists
                existing_offer = session.query(Offer).filter(Offer.offer_id == offer_id).first()
                
                if not existing_offer:
                    # Create new offer
                    new_offer = Offer(
                        offer_id=offer_id,
                        campaign_id=campaign.id,
                        campaign_name=campaign.name,
                        title=offer_data.get('title', ''),
                        description=offer_data.get('description', ''),
                        terms_and_conditions=offer_data.get('terms_and_conditions', ''),
                        coupon_code=offer_data.get('coupon_code', ''),
                        image_url=offer_data.get('image_url', ''),
                        offer_type=offer_data.get('offer_type', ''),
                        shipping_charge=offer_data.get('shipping_charge', ''),
                        status='live',  # Set status to 'live' to match our RAG service
                        url=offer_data.get('url', ''),
                        affiliate_url=offer_data.get('affiliate_url', ''),
                        start_date=datetime.strptime(offer_data.get('start_date', '2023-01-01'), '%Y-%m-%d') if offer_data.get('start_date') else None,
                        end_date=datetime.strptime(offer_data.get('end_date', '2025-12-31'), '%Y-%m-%d') if offer_data.get('end_date') else None,
                        categories=json.dumps(offer_data.get('categories', []))
                    )
                    session.add(new_offer)
                    offers_created += 1
                
                processed_count += 1
                if processed_count % 100 == 0:
                    logger.info(f"Processed {processed_count}/{len(offers_data)} offers")
                    session.commit()  # Commit in batches
            
            except Exception as e:
                logger.error(f"Error processing offer {offer_data.get('id')}: {str(e)}")
        
        # Final commit
        session.commit()
        logger.info(f"Saved {campaigns_created} new campaigns and {offers_created} new offers to database")
        return offers_created

async def create_embeddings():
    """Create embeddings for offers in the database"""
    logger.info("Creating embeddings for offers")
    
    # Load embedding model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("Loaded embedding model")
    
    # Check if we have existing embeddings
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM offer_embeddings"))
        existing_count = result.scalar()
        logger.info(f"Found {existing_count} existing embeddings")
        
        # Get offers that don't have embeddings yet
        query = text("""
        SELECT o.id, o.title, o.description, c.name as campaign_name, o.campaign_id
        FROM offers o
        JOIN campaigns c ON o.campaign_id = c.id
        WHERE o.id NOT IN (SELECT DISTINCT offer_id FROM offer_embeddings)
        AND o.status = 'live'
        """)
        
        result = await session.execute(query)
        offers_to_process = result.fetchall()
        logger.info(f"Found {len(offers_to_process)} offers without embeddings")
        
        # Process offers in batches
        batch_size = 50
        total_processed = 0
        
        for i in range(0, len(offers_to_process), batch_size):
            batch = offers_to_process[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(offers_to_process) + batch_size - 1)//batch_size}")
            
            for offer in batch:
                try:
                    # Create combined text that includes campaign, title and description
                    combined_text = f"Campaign: {offer.campaign_name}\nTitle: {offer.title}\nDescription: {offer.description}"
                    
                    # Generate embedding
                    embedding = model.encode(combined_text).tolist()
                    
                    # Create embedding record
                    embedding_record = OfferEmbedding(
                        offer_id=offer.id,
                        campaign_id=offer.campaign_id,
                        chunk_id=f"{offer.id}_combined",
                        content=combined_text,
                        content_type="combined",
                        embedding=embedding,
                        meta_data=json.dumps({
                            "type": "combined",
                            "offer_id": offer.id,
                            "campaign_id": offer.campaign_id
                        })
                    )
                    
                    session.add(embedding_record)
                    total_processed += 1
                    
                    if total_processed % 10 == 0:
                        logger.info(f"Created {total_processed}/{len(offers_to_process)} embeddings")
                    
                except Exception as e:
                    logger.error(f"Error creating embedding for offer {offer.id}: {str(e)}")
            
            # Commit after each batch
            await session.commit()
            logger.info(f"Committed batch {i//batch_size + 1}")
            
        logger.info(f"Created embeddings for {total_processed} offers")
        
        # Final count
        result = await session.execute(text("SELECT COUNT(*) FROM offer_embeddings"))
        final_count = result.scalar()
        logger.info(f"Total embeddings in database: {final_count}")

async def main():
    """Main function to run the script"""
    try:
        # Create tables if they don't exist
        create_tables()
        
        # Fetch offers from API
        offers = fetch_all_offers()
        logger.info(f"Fetched {len(offers)} offers from API")
        
        # Save offers to database
        new_offers = save_campaigns_and_offers(offers)
        
        # Create embeddings
        if new_offers > 0:
            logger.info("Creating embeddings for new offers")
            await create_embeddings()
        else:
            logger.info("No new offers to create embeddings for")
        
        logger.info("Script completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
