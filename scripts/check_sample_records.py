#!/usr/bin/env python
"""
This script checks sample records from the offers and offer_embeddings tables
to understand the current structure of the data.
"""

import os
import sys
import logging
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import OfferEmbedding, Offer, Campaign
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

async def check_sample_records():
    """
    Check sample records from offers and offer_embeddings tables
    """
    async with async_session() as session:
        # Get sample records from offer_embeddings
        query = select(
            OfferEmbedding,
            Offer,
            Campaign
        ).join(
            Offer, OfferEmbedding.offer_id == Offer.id
        ).join(
            Campaign, Offer.campaign_id == Campaign.id, isouter=True
        ).order_by(OfferEmbedding.id)
        
        result = await session.execute(query)
        records = result.fetchall()
        
        total_count = len(records)
        logger.info(f"Found {total_count} total records")
        
        # Check first few and some around row 120
        sample_indices = [0, 1, 2, 119, 120, 121, 122, 200, 500, 800]
        
        # Count records with missing campaign names
        missing_campaign_count = 0
        empty_campaign_content_count = 0
        
        for i, (embedding, offer, campaign) in enumerate(records):
            # Check if campaign name is missing in the content
            if embedding.content and "Campaign: " in embedding.content:
                first_line = embedding.content.split('\n')[0].strip()
                campaign_name_in_content = first_line.replace("Campaign: ", "")
                
                if not campaign_name_in_content:
                    empty_campaign_content_count += 1
                
                if campaign and campaign.name and campaign_name_in_content != campaign.name:
                    missing_campaign_count += 1
            
            # Log sample records
            if i in sample_indices:
                logger.info(f"\nSample record {i+1}:")
                logger.info(f"Embedding ID: {embedding.id}")
                logger.info(f"Offer ID: {offer.id}")
                logger.info(f"Offer Title: {offer.title}")
                
                if campaign:
                    logger.info(f"Campaign ID: {campaign.id}")
                    logger.info(f"Campaign Name: {campaign.name}")
                else:
                    logger.info("Campaign: None")
                
                # Show first 3 lines of content
                content_lines = embedding.content.split('\n')
                logger.info(f"Content (first 3 lines):")
                for j in range(min(3, len(content_lines))):
                    logger.info(f"  {content_lines[j]}")
                
                logger.info("---")
        
        logger.info(f"\nSummary:")
        logger.info(f"Total records: {total_count}")
        logger.info(f"Records with empty campaign name in content: {empty_campaign_content_count}")
        logger.info(f"Records with mismatched campaign name: {missing_campaign_count}")

async def main():
    logger.info("Starting database record check")
    await check_sample_records()
    logger.info("Completed database record check")

if __name__ == "__main__":
    asyncio.run(main())
