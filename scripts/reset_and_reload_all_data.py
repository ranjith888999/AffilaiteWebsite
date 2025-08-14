#!/usr/bin/env python
"""
This script deletes all existing offer data and re-uploads everything from scratch,
ensuring that campaign names are properly included in the embeddings.
"""

import os
import sys
import logging
import asyncio
import json
import time
import requests
import numpy as np
from datetime import datetime
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import Campaign, Offer, OfferEmbedding
from app.database import ASYNC_DATABASE_URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

engine = create_async_engine(ASYNC_DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

CUELINKS_API_KEY = "MUmQPF2MLjDzMOHi0PSCdOwI082JAfj6vRLLT1QcY00"
EMBEDDING_MODEL = None  # Will be initialized later

def fetch_all_offers(page=1, per_page=100):
    """
    Fetch all offers from the Cuelinks API, paging through results
    """
    all_offers = []
    total_count = None
    current_page = page
    
    while True:
        url = f"https://www.cuelinks.com/api/v2/offers.json?page={current_page}&per_page={per_page}"
        
        headers = {
            'Authorization': f'Token token={CUELINKS_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Fetching offers page {current_page}, per_page {per_page}")
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch offers: {response.status_code} - {response.text}")
            break
        
        data = response.json()
        offers = data['offers']
        
        if total_count is None:
            total_count = data['total_count']
            logger.info(f"Total offers to fetch: {total_count}")
        
        logger.info(f"Fetched {len(offers)} offers on page {current_page}")
        all_offers.extend(offers)
        
        # If we've fetched all offers or this page has fewer than per_page, we're done
        if len(all_offers) >= total_count or len(offers) < per_page:
            break
        
        current_page += 1
        # Be nice to the API and don't hammer it
        time.sleep(1)
    
    logger.info(f"Total offers fetched: {len(all_offers)}")
    return all_offers

def fetch_all_campaigns():
    """
    Fetch all campaigns from the Cuelinks API
    """
    all_campaigns = []
    current_page = 1
    per_page = 100
    
    while True:
        url = f"https://www.cuelinks.com/api/v2/campaigns.json?page={current_page}&per_page={per_page}"
        
        headers = {
            'Authorization': f'Token token={CUELINKS_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Fetching campaigns page {current_page}, per_page {per_page}")
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch campaigns: {response.status_code} - {response.text}")
            break
        
        data = response.json()
        campaigns = data['campaigns']
        
        if not campaigns:
            break
        
        logger.info(f"Fetched {len(campaigns)} campaigns on page {current_page}")
        all_campaigns.extend(campaigns)
        
        # If this page has fewer than per_page, we're done
        if len(campaigns) < per_page:
            break
        
        current_page += 1
        # Be nice to the API and don't hammer it
        time.sleep(1)
    
    logger.info(f"Total campaigns fetched: {len(all_campaigns)}")
    return all_campaigns

def create_embedding(text):
    """
    Create an embedding for the given text
    """
    global EMBEDDING_MODEL
    
    if EMBEDDING_MODEL is None:
        logger.info("Initializing embedding model")
        EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    
    try:
        embedding = EMBEDDING_MODEL.encode(text)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Error creating embedding: {e}")
        return None

def preprocess_offer_for_embedding(offer, campaigns_dict):
    """
    Preprocess offer data for embedding, combining campaign, title, and description
    """
    # Get campaign name from the campaigns dictionary or use the campaign string from the offer
    campaign_id = offer.get('camapign_id')  # Note the typo in the API response
    campaign_name = campaigns_dict.get(campaign_id, {}).get('name') if campaign_id in campaigns_dict else offer.get('campaign', 'Unknown')
    
    # Combine campaign, title, and description for the combined embedding
    combined_text = f"Campaign: {campaign_name}\nTitle: {offer['title']}\nDescription: {offer['description']}"
    
    return combined_text

async def delete_all_existing_data():
    """
    Delete all existing campaigns, offers, and offer embeddings from the database
    """
    async with async_session() as session:
        # Delete offer embeddings first due to foreign key constraints
        stmt = delete(OfferEmbedding)
        result = await session.execute(stmt)
        logger.info(f"Deleted {result.rowcount} offer embeddings")
        
        # Delete offers
        stmt = delete(Offer)
        result = await session.execute(stmt)
        logger.info(f"Deleted {result.rowcount} offers")
        
        # Delete campaigns
        stmt = delete(Campaign)
        result = await session.execute(stmt)
        logger.info(f"Deleted {result.rowcount} campaigns")
        
        # Reset sequences (depends on your database)
        try:
            await session.execute(text("ALTER SEQUENCE campaigns_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE offers_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE offer_embeddings_id_seq RESTART WITH 1"))
        except Exception as e:
            logger.warning(f"Error resetting sequences: {e}")
            # Try alternate approach for resetting sequences
            try:
                await session.execute(text("SELECT setval('campaigns_id_seq', 1, false)"))
                await session.execute(text("SELECT setval('offers_id_seq', 1, false)"))
                await session.execute(text("SELECT setval('offer_embeddings_id_seq', 1, false)"))
            except Exception as e2:
                logger.error(f"Failed to reset sequences with alternate method: {e2}")
        
        await session.commit()
        logger.info("Database reset complete")

async def upload_offers_and_create_embeddings(offers, campaigns, batch_size=50):
    """
    Upload offers and create embeddings in batches
    """
    # Create a dictionary of campaigns by ID for easy lookup
    campaigns_dict = {campaign['id']: campaign for campaign in campaigns}
    
    # First, organize offers by campaign
    campaigns_map = {}
    for offer in offers:
        campaign_id = offer.get('camapign_id')  # Note the typo in the API response
        
        if not campaign_id:
            logger.warning(f"Offer {offer.get('id')} has no campaign ID, skipping")
            continue
            
        if campaign_id not in campaigns_map:
            # Get the campaign data from our campaigns dictionary
            campaign_data = campaigns_dict.get(campaign_id)
            
            if not campaign_data:
                logger.warning(f"Campaign ID {campaign_id} not found in campaigns data, using basic info")
                # Create minimal campaign data
                campaign_data = {
                    'id': campaign_id,
                    'name': offer.get('campaign', f"Unknown Campaign {campaign_id}"),
                    'description': ''
                }
            
            campaigns_map[campaign_id] = {
                'data': campaign_data,
                'offers': []
            }
        
        campaigns_map[campaign_id]['offers'].append(offer)
    
    logger.info(f"Found {len(campaigns_map)} unique campaigns")
    
    # Campaign ID to database ID mapping
    campaign_id_map = {}
    
    # Now process campaigns and their offers
    async with async_session() as session:
        # Insert campaigns first
        for api_campaign_id, campaign_info in campaigns_map.items():
            campaign_data = campaign_info['data']
            
            # Create campaign object
            campaign = Campaign(
                campaign_id=api_campaign_id,  # Set the original campaign_id
                name=campaign_data['name'],
                description=campaign_data.get('description', ''),
                status='active',
                category=json.dumps(campaign_data.get('categories', {}))
            )
            
            session.add(campaign)
            await session.flush()  # Get the ID
            
            # Map API campaign ID to database ID
            campaign_id_map[api_campaign_id] = campaign.id
        
        await session.commit()
        logger.info(f"Inserted {len(campaign_id_map)} campaigns")
        
        # Now insert offers and create embeddings in batches
        total_offers = len(offers)
        total_batches = (total_offers + batch_size - 1) // batch_size
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, total_offers)
            batch_offers = offers[start_idx:end_idx]
            
            logger.info(f"Processing batch {batch_idx + 1}/{total_batches} ({len(batch_offers)} offers)")
            
            for offer_data in tqdm(batch_offers, desc="Batches"):
                # Get database campaign ID
                api_campaign_id = offer_data.get('camapign_id')  # Note the typo in the API response
                
                if not api_campaign_id:
                    logger.warning(f"Offer {offer_data.get('id')} has no campaign ID, skipping")
                    continue
                
                db_campaign_id = campaign_id_map.get(api_campaign_id)
                
                if not db_campaign_id:
                    logger.warning(f"Campaign ID {api_campaign_id} not found in mapping, skipping offer")
                    continue
                
                # Get campaign name
                campaign_name = campaigns_dict.get(api_campaign_id, {}).get('name', offer_data.get('campaign', f"Unknown Campaign {api_campaign_id}"))
                
                # Create offer object
                offer = Offer(
                    offer_id=offer_data['id'],
                    title=offer_data['title'],
                    description=offer_data['description'],
                    campaign_id=db_campaign_id,
                    campaign_name=campaign_name,  # Store campaign name directly
                    url=offer_data.get('url', ''),
                    image_url=offer_data.get('image_url', ''),
                    status=offer_data.get('status', 'live'),
                    categories=json.dumps(offer_data.get('categories', {})),
                    terms_and_conditions=offer_data.get('terms_and_condition', ''),
                    coupon_code=offer_data.get('coupon_code', ''),
                    offer_type=offer_data.get('type', ''),
                    shipping_charge=offer_data.get('shipping_charge', ''),
                    affiliate_url=offer_data.get('affiliate_url', ''),
                    start_date=datetime.strptime(offer_data['start_date'], '%Y-%m-%d') if offer_data.get('start_date') else None,
                    end_date=datetime.strptime(offer_data['end_date'], '%Y-%m-%d') if offer_data.get('end_date') else None
                )
                
                session.add(offer)
                await session.flush()  # Get the ID
                
                # Create combined embedding
                combined_text = preprocess_offer_for_embedding(offer_data, campaigns_dict)
                embedding_vector = create_embedding(combined_text)
                
                if embedding_vector:
                    # Create embedding object
                    offer_embedding = OfferEmbedding(
                        offer_id=offer.id,
                        campaign_id=db_campaign_id,  # Add campaign ID
                        content=combined_text,
                        content_type='combined',
                        embedding=embedding_vector,
                        chunk_id=f"offer_{offer.id}_combined"  # Add chunk ID
                    )
                    
                    session.add(offer_embedding)
            
            # Commit batch
            await session.commit()
            logger.info(f"Committed batch {batch_idx + 1}/{total_batches}")
    
    logger.info("Upload complete")

async def main():
    logger.info("Starting complete data refresh")
    
    # Step 1: Fetch all campaigns from the API
    logger.info("Fetching all campaigns from API")
    all_campaigns = fetch_all_campaigns()
    
    if not all_campaigns:
        logger.error("Failed to fetch campaigns, aborting")
        return
    
    # Step 2: Fetch all offers from the API
    logger.info("Fetching all offers from API")
    all_offers = fetch_all_offers()
    
    if not all_offers:
        logger.error("Failed to fetch offers, aborting")
        return
    
    # Step 3: Delete all existing data
    logger.info("Deleting all existing data")
    await delete_all_existing_data()
    
    # Step 4: Upload offers and create embeddings
    logger.info("Uploading offers and creating embeddings")
    await upload_offers_and_create_embeddings(all_offers, all_campaigns)
    
    logger.info("Data refresh complete")

if __name__ == "__main__":
    asyncio.run(main())
