#!/usr/bin/env python
"""
Create a simple script to verify offers with coupon codes
"""

import os
import sys
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.database import Offer, OfferEmbedding, Campaign

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

async def check_offers_with_coupon_codes():
    """
    Check offers that have coupon codes and verify their embeddings contain the coupon info
    """
    async with AsyncSessionLocal() as session:
        # Get offers with coupon codes
        offers_query = (
            select(Offer)
            .options(selectinload(Offer.campaign))
            .where(Offer.coupon_code != None)
            .limit(10)
        )
        
        offers = (await session.execute(offers_query)).scalars().all()
        
        print(f"Found {len(offers)} offers with coupon codes")
        
        for offer in offers:
            print(f"\nOffer ID: {offer.id}")
            print(f"Title: {offer.title}")
            print(f"Campaign: {offer.campaign.name}")
            print(f"Coupon Code: {offer.coupon_code}")
            
            # Get the embedding for this offer
            embedding_query = (
                select(OfferEmbedding)
                .where(OfferEmbedding.offer_id == offer.id)
            )
            
            embedding = (await session.execute(embedding_query)).scalar_one_or_none()
            
            if embedding:
                # Check if the coupon code is in the content
                has_coupon_in_content = "CouponCode:" in embedding.content
                
                print(f"Has Coupon in Embedding: {has_coupon_in_content}")
                
                # Print the content with line breaks for better readability
                lines = embedding.content.split("\n")
                coupon_line = None
                
                for line in lines:
                    if line.startswith("CouponCode:"):
                        coupon_line = line
                        break
                
                # Print the coupon line if found
                if coupon_line:
                    print(f"Coupon Line in Embedding: {coupon_line}")
                else:
                    print("Coupon code not found in embedding content")
                
                # Print a portion of the content
                print("Content Preview:")
                print("\n".join(lines[:5]) + "...")
            else:
                print("No embedding found for this offer")

async def search_offers_with_coupon_keywords():
    """
    Search for offers with coupon-related keywords in their embeddings
    """
    coupon_keywords = ["coupon", "discount", "promo", "code", "offer"]
    
    async with AsyncSessionLocal() as session:
        # Get some embeddings that might contain coupon-related content
        for keyword in coupon_keywords:
            print(f"\n\nSearching for embeddings with keyword: '{keyword}'")
            
            # Simple text search in embedding content
            query = (
                select(OfferEmbedding)
                .where(OfferEmbedding.content.ilike(f"%{keyword}%"))
                .limit(3)
            )
            
            embeddings = (await session.execute(query)).scalars().all()
            
            print(f"Found {len(embeddings)} embeddings with keyword '{keyword}'")
            
            for embedding in embeddings:
                # Get the offer
                offer_query = (
                    select(Offer)
                    .options(selectinload(Offer.campaign))
                    .where(Offer.id == embedding.offer_id)
                )
                
                offer = (await session.execute(offer_query)).scalar_one_or_none()
                
                if offer:
                    print(f"\nOffer ID: {offer.id}")
                    print(f"Title: {offer.title}")
                    print(f"Campaign: {offer.campaign.name}")
                    print(f"Coupon Code: {offer.coupon_code or 'None'}")
                    
                    # Print a portion of the embedding content
                    print("Content Preview:")
                    print("\n".join(embedding.content.split("\n")[:5]) + "...")
                else:
                    print(f"No offer found for embedding {embedding.id}")

async def main():
    # Check offers with coupon codes
    await check_offers_with_coupon_codes()
    
    # Search for offers with coupon-related keywords
    await search_offers_with_coupon_keywords()

if __name__ == "__main__":
    asyncio.run(main())
