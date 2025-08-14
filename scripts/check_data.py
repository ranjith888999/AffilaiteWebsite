#!/usr/bin/env python
"""
Check the database to verify campaigns and embeddings were correctly loaded
"""

import os
import sys
import asyncio
import logging
from sqlalchemy import select
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

async def check_data():
    """
    Check database data after the reset and reload
    """
    async with async_session() as session:
        # Count campaigns
        stmt = select(Campaign)
        result = await session.execute(stmt)
        campaigns = result.scalars().all()
        print(f"Total campaigns: {len(campaigns)}")
        
        print("\nSample campaigns:")
        for campaign in campaigns[:5]:
            print(f"  ID: {campaign.id}, Campaign ID: {campaign.campaign_id}, Name: {campaign.name}")
        
        # Count offers
        stmt = select(Offer)
        result = await session.execute(stmt)
        offers = result.scalars().all()
        print(f"\nTotal offers: {len(offers)}")
        
        # Count embeddings
        stmt = select(OfferEmbedding)
        result = await session.execute(stmt)
        embeddings = result.scalars().all()
        print(f"\nTotal embeddings: {len(embeddings)}")
        
        print("\nSample embedding contents:")
        for embedding in embeddings[:3]:
            print(f"Embedding {embedding.id} for Offer {embedding.offer_id}:")
            print(f"{embedding.content[:200]}...")
        
        # Check for 'Unknown Campaign' in embeddings
        unknown_count = 0
        for embedding in embeddings:
            if "Unknown Campaign" in embedding.content:
                unknown_count += 1
        
        print(f"\nEmbeddings with 'Unknown Campaign': {unknown_count}")

async def main():
    await check_data()

if __name__ == "__main__":
    asyncio.run(main())
