#!/usr/bin/env python
"""
This script fetches campaign data from the Cuelinks API and checks if we can find
the actual campaign name for Campaign ID 89.
"""

import os
import sys
import logging
import json
import asyncio
import requests
from sqlalchemy import select, update
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

def fetch_all_campaigns():
    """
    Fetch all campaigns from the Cuelinks API
    """
    url = "https://www.cuelinks.com/api/v2/campaigns.json"
    
    headers = {
        'Authorization': f'Token token={CUELINKS_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    logger.info("Fetching campaigns from Cuelinks API")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch campaigns: {response.status_code} - {response.text}")
        return None
    
    data = response.json()
    logger.info(f"Fetched {len(data['campaigns'])} campaigns")
    return data['campaigns']

def fetch_campaign_offers(campaign_id):
    """
    Fetch offers for a specific campaign from the Cuelinks API
    """
    url = f"https://www.cuelinks.com/api/v2/campaigns/{campaign_id}/offers.json"
    
    headers = {
        'Authorization': f'Token token={CUELINKS_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    logger.info(f"Fetching offers for campaign ID {campaign_id}")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch offers for campaign {campaign_id}: {response.status_code} - {response.text}")
        return None
    
    data = response.json()
    logger.info(f"Fetched {len(data['offers'])} offers for campaign {campaign_id}")
    return data['offers']

def fetch_offers_with_campaign_info(page=1, per_page=100):
    """
    Fetch offers with campaign info from the Cuelinks API
    """
    url = f"https://www.cuelinks.com/api/v2/offers.json?page={page}&per_page={per_page}"
    
    headers = {
        'Authorization': f'Token token={CUELINKS_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    logger.info(f"Fetching offers (page {page}, per_page {per_page})")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch offers: {response.status_code} - {response.text}")
        return None
    
    data = response.json()
    logger.info(f"Fetched {len(data['offers'])} offers (total: {data['meta']['total_count']})")
    return data

async def check_database_campaign_info():
    """
    Check campaign information in the database
    """
    async with async_session() as session:
        # Get Campaign ID 89
        query = select(Campaign).where(Campaign.id == 89)
        result = await session.execute(query)
        campaign = result.scalar_one_or_none()
        
        if campaign:
            logger.info(f"Campaign ID 89 in database: {campaign.name}")
            
            # Get offers for this campaign
            query = select(Offer).where(Offer.campaign_id == 89).limit(5)
            result = await session.execute(query)
            offers = result.scalars().all()
            
            logger.info(f"Sample offers for Campaign ID 89:")
            for offer in offers:
                logger.info(f"  Offer ID: {offer.id}, Title: {offer.title}")
        else:
            logger.info("Campaign ID 89 not found in database")

async def update_campaign_and_embeddings(campaign_id, actual_campaign_name):
    """
    Update campaign name and related offer embeddings
    """
    async with async_session() as session:
        # Update campaign name
        stmt = update(Campaign).where(
            Campaign.id == campaign_id
        ).values(name=actual_campaign_name)
        
        await session.execute(stmt)
        logger.info(f"Updated campaign ID {campaign_id} name to '{actual_campaign_name}'")
        
        # Find offers with this campaign_id
        query = select(Offer).where(Offer.campaign_id == campaign_id)
        result = await session.execute(query)
        offers = result.scalars().all()
        
        logger.info(f"Found {len(offers)} offers for campaign ID {campaign_id}")
        
        # For each offer, update its embedding content
        updated_embeddings = 0
        for offer in offers:
            # Find the embedding for this offer
            query = select(OfferEmbedding).where(OfferEmbedding.offer_id == offer.id)
            result = await session.execute(query)
            embedding = result.scalar_one_or_none()
            
            if embedding:
                # Replace "Campaign: Unknown Campaign {id}" with "Campaign: {actual_name}"
                new_content = embedding.content.replace(
                    f"Campaign: Unknown Campaign {campaign_id}", 
                    f"Campaign: {actual_campaign_name}"
                )
                
                stmt = update(OfferEmbedding).where(
                    OfferEmbedding.id == embedding.id
                ).values(content=new_content)
                
                await session.execute(stmt)
                updated_embeddings += 1
                
                if updated_embeddings % 20 == 0:
                    logger.info(f"Updated {updated_embeddings} embeddings so far")
                    await session.commit()
        
        # Final commit for any remaining updates
        if updated_embeddings % 20 != 0:
            await session.commit()
        
        logger.info(f"Updated content for {updated_embeddings} embeddings")

async def main():
    logger.info("Starting campaign data check")
    
    # Check campaign info in database
    await check_database_campaign_info()
    
    # Fetch all campaigns from API
    campaigns = fetch_all_campaigns()
    
    if campaigns:
        # Look for a campaign that might correspond to ID 89
        logger.info("Checking API data for campaign that might match ID 89")
        campaign_89 = None
        
        # Print all campaign info
        logger.info("Campaigns from API:")
        for campaign in campaigns:
            logger.info(f"Campaign: {campaign['name']} (ID: {campaign['id']})")
            
            # If campaign has a lot of offers, it might be the one we're looking for
            if campaign.get('offers_count', 0) > 800:
                logger.info(f"Potential match for Campaign 89: {campaign['name']} (offers: {campaign['offers_count']})")
                campaign_89 = campaign
    
    # Fetch a sample of offers with campaign info
    offers_data = fetch_offers_with_campaign_info(page=1, per_page=5)
    
    if offers_data:
        logger.info("Sample offers with campaign info:")
        for offer in offers_data['offers']:
            logger.info(f"Offer: {offer['title']}")
            logger.info(f"  Campaign: {offer['campaign']['name']} (ID: {offer['campaign']['id']})")
    
    # If we found a match for Campaign 89, update the database
    if campaign_89:
        actual_name = campaign_89['name']
        logger.info(f"Updating Campaign 89 to '{actual_name}'")
        await update_campaign_and_embeddings(89, actual_name)
    
    logger.info("Completed campaign data check")

if __name__ == "__main__":
    asyncio.run(main())
