#!/usr/bin/env python
"""
This script fixes empty campaign names in the database and updates
the corresponding offer_embeddings content.
"""

import os
import sys
import logging
import asyncio
from sqlalchemy import select, update
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

async def fix_empty_campaign_names():
    """
    Fix empty campaign names in the database and update offer_embeddings
    """
    async with async_session() as session:
        # First, find campaigns with empty names
        query = select(Campaign).where(Campaign.name == "")
        result = await session.execute(query)
        empty_campaigns = result.scalars().all()
        
        logger.info(f"Found {len(empty_campaigns)} campaigns with empty names")
        
        if not empty_campaigns:
            logger.info("No empty campaign names found. Nothing to fix.")
            return
        
        # Update campaign names to a default value like "Unknown Campaign {id}"
        updated_campaigns = []
        for campaign in empty_campaigns:
            new_name = f"Unknown Campaign {campaign.id}"
            stmt = update(Campaign).where(Campaign.id == campaign.id).values(name=new_name)
            await session.execute(stmt)
            updated_campaigns.append({"id": campaign.id, "new_name": new_name})
            logger.info(f"Updated campaign ID {campaign.id} name to '{new_name}'")
        
        await session.commit()
        logger.info(f"Updated {len(updated_campaigns)} campaigns with default names")
        
        # Now update offer_embeddings content for offers with those campaigns
        updated_embeddings = 0
        
        for campaign_info in updated_campaigns:
            campaign_id = campaign_info["id"]
            new_campaign_name = campaign_info["new_name"]
            
            # Find offers with this campaign_id
            query = select(Offer).where(Offer.campaign_id == campaign_id)
            result = await session.execute(query)
            offers = result.scalars().all()
            
            logger.info(f"Found {len(offers)} offers for campaign ID {campaign_id}")
            
            # For each offer, update its embedding content
            for offer in offers:
                # Find the embedding for this offer
                query = select(OfferEmbedding).where(OfferEmbedding.offer_id == offer.id)
                result = await session.execute(query)
                embedding = result.scalar_one_or_none()
                
                if embedding:
                    # Replace "Campaign: " with "Campaign: {new_name}"
                    if "Campaign: \n" in embedding.content:
                        new_content = embedding.content.replace("Campaign: \n", f"Campaign: {new_campaign_name}\n")
                    else:
                        new_content = embedding.content.replace("Campaign: ", f"Campaign: {new_campaign_name}")
                    
                    stmt = update(OfferEmbedding).where(OfferEmbedding.id == embedding.id).values(content=new_content)
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
    logger.info("Starting fix for empty campaign names")
    await fix_empty_campaign_names()
    logger.info("Completed fix for empty campaign names")

if __name__ == "__main__":
    asyncio.run(main())
