#!/usr/bin/env python
"""
This script fixes the campaign name in offer_embeddings content column
where it's missing or null.
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

async def fix_embeddings():
    """
    Fix offer_embeddings where campaign name is missing in content
    """
    async with async_session() as session:
        # Get all offer embeddings with their related offer and campaign
        query = select(
            OfferEmbedding,
            Offer,
            Campaign
        ).join(
            Offer, OfferEmbedding.offer_id == Offer.id
        ).join(
            Campaign, Offer.campaign_id == Campaign.id, isouter=True
        )
        
        result = await session.execute(query)
        embeddings_to_fix = []
        
        total_count = 0
        fixed_count = 0
        
        for embedding, offer, campaign in result:
            total_count += 1
            
            # Check if campaign name is missing in the content
            if embedding.content and "Campaign: " in embedding.content:
                first_line = embedding.content.split('\n')[0].strip()
                if first_line == "Campaign: " or "Campaign: \n" in embedding.content:
                    # Missing campaign name
                    if campaign and campaign.name:
                        # Replace the empty campaign line with the proper campaign name
                        new_content = embedding.content.replace(
                            "Campaign: ", 
                            f"Campaign: {campaign.name}"
                        )
                        
                        embeddings_to_fix.append({
                            "id": embedding.id,
                            "old_content": embedding.content[:100] + "...",
                            "new_content": new_content[:100] + "...",
                            "campaign_name": campaign.name
                        })
                        
                        # Update the embedding
                        stmt = update(OfferEmbedding).where(
                            OfferEmbedding.id == embedding.id
                        ).values(content=new_content)
                        
                        await session.execute(stmt)
                        fixed_count += 1
                        
                        if fixed_count % 20 == 0:
                            logger.info(f"Fixed {fixed_count} embeddings so far")
                            await session.commit()
        
        # Final commit for any remaining updates
        if fixed_count % 20 != 0:
            await session.commit()
        
        logger.info(f"Examined {total_count} embeddings, fixed {fixed_count} embeddings")
        
        # Log some examples of the fixes
        if embeddings_to_fix:
            logger.info("Examples of fixes made:")
            for i, fix in enumerate(embeddings_to_fix[:5]):
                logger.info(f"Example {i+1}:")
                logger.info(f"  ID: {fix['id']}")
                logger.info(f"  Campaign: {fix['campaign_name']}")
                logger.info(f"  Old content: {fix['old_content']}")
                logger.info(f"  New content: {fix['new_content']}")

async def main():
    logger.info("Starting campaign name fix in offer_embeddings")
    await fix_embeddings()
    logger.info("Completed campaign name fix in offer_embeddings")

if __name__ == "__main__":
    asyncio.run(main())
