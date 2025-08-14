#!/usr/bin/env python
"""
Update embeddings to include coupon code information
"""

import os
import sys
import asyncio
import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import numpy as np
from sentence_transformers import SentenceTransformer

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import Offer, OfferEmbedding
from app.database import ASYNC_DATABASE_URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Create async engine and session
engine = create_async_engine(ASYNC_DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Initialize embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

async def update_embeddings_with_coupon():
    """
    Update all existing embeddings to include coupon code information
    """
    total_updated = 0
    batch_size = 50
    
    async with async_session() as session:
        # Count total embeddings to update
        count_result = await session.execute(select(OfferEmbedding))
        total_embeddings = len(count_result.scalars().all())
        logger.info(f"Found {total_embeddings} embeddings to update with coupon codes")
        
        # Get all offer_ids with embeddings
        result = await session.execute(select(OfferEmbedding.offer_id).distinct())
        offer_ids = [row[0] for row in result.all()]
        logger.info(f"Found {len(offer_ids)} unique offers with embeddings")
        
        # Process in batches
        batch_count = (len(offer_ids) + batch_size - 1) // batch_size
        logger.info(f"Processing in {batch_count} batches of size {batch_size}")
        
        for batch_idx in range(batch_count):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(offer_ids))
            batch_offer_ids = offer_ids[start_idx:end_idx]
            
            logger.info(f"Processing batch {batch_idx + 1}/{batch_count} ({len(batch_offer_ids)} offers)")
            
            # Get offers with embeddings in this batch
            offers_result = await session.execute(
                select(Offer).where(Offer.id.in_(batch_offer_ids))
            )
            offers = {offer.id: offer for offer in offers_result.scalars().all()}
            
            # Get embeddings for these offers
            embeddings_result = await session.execute(
                select(OfferEmbedding).where(OfferEmbedding.offer_id.in_(batch_offer_ids))
            )
            embeddings = embeddings_result.scalars().all()
            
            for embedding in embeddings:
                offer = offers.get(embedding.offer_id)
                if not offer:
                    logger.warning(f"Offer {embedding.offer_id} not found for embedding {embedding.id}")
                    continue
                
                # Get current content
                content = embedding.content
                
                # Check if content already contains coupon code
                if "Coupon:" in content or "CouponCode:" in content:
                    logger.debug(f"Embedding {embedding.id} already has coupon code information")
                    continue
                
                # Add coupon code if available
                if offer.coupon_code:
                    # Split content into lines
                    lines = content.split('\n')
                    
                    # Find where to insert the coupon code (after Description or Category)
                    insert_index = -1
                    for i, line in enumerate(lines):
                        if line.startswith("Category:") or line.startswith("Type:"):
                            insert_index = i + 1
                            break
                    
                    if insert_index != -1:
                        # Insert coupon code after Category or Type
                        lines.insert(insert_index, f"CouponCode: {offer.coupon_code}")
                    else:
                        # Append to the end if Category/Type not found
                        lines.append(f"CouponCode: {offer.coupon_code}")
                    
                    # Rebuild content
                    new_content = '\n'.join(lines)
                    
                    # Generate new embedding
                    new_embedding_vector = embedding_model.encode(new_content).tolist()
                    
                    # Update database
                    embedding.content = new_content
                    embedding.embedding = new_embedding_vector
                    session.add(embedding)
                    
                    total_updated += 1
                    
            # Commit batch
            await session.commit()
            logger.info(f"Batch {batch_idx + 1} complete, {total_updated} embeddings updated so far")
    
    logger.info(f"Finished updating embeddings. Total embeddings updated: {total_updated}")

async def check_updated_embeddings():
    """
    Check a few embeddings to verify coupon codes were added
    """
    async with async_session() as session:
        # Get 10 random embeddings with offers that have coupon codes
        result = await session.execute(
            select(OfferEmbedding, Offer)
            .join(Offer, OfferEmbedding.offer_id == Offer.id)
            .where(Offer.coupon_code != None)
            .order_by(Offer.id)
            .limit(10)
        )
        
        samples = result.all()
        logger.info(f"Checking {len(samples)} sample embeddings with coupon codes:")
        
        for embedding, offer in samples:
            logger.info(f"Offer {offer.id}: {offer.title}")
            logger.info(f"Coupon Code: {offer.coupon_code}")
            
            # Check if coupon code is in the content
            has_coupon = f"CouponCode: {offer.coupon_code}" in embedding.content
            logger.info(f"Embedding has coupon code: {has_coupon}")
            
            # Print content preview
            content_preview = '\n'.join(embedding.content.split('\n')[:10])
            logger.info(f"Content preview:\n{content_preview}\n")

async def main():
    # First update the embeddings
    await update_embeddings_with_coupon()
    
    # Then check some updated embeddings
    await check_updated_embeddings()

if __name__ == "__main__":
    asyncio.run(main())
