#!/usr/bin/env python
"""
Test the RAG system with searches related to coupon codes
"""

import os
import sys
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag_service import PostgreSQLVectorStore, RAGService
from app.database import AsyncSessionLocal
from app.models.database import Offer, OfferEmbedding

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

async def test_coupon_code_searches():
    """
    Test searches related to coupon codes
    """
    # Initialize the RAG service
    rag_service = RAGService()
    
    # Define test queries related to coupon codes
    test_queries = [
        "offers with coupon codes",
        "discount coupons",
        "travel offers with coupon code",
        "electronics with promo code",
        "fashion discounts with coupons",
        "TRAVELDEALS coupon",
        "LASH500 coupon code",
        "offers with free shipping coupon"
    ]
    
    # Test each query
    for query in test_queries:
        print(f"\n\n====== Testing Query: '{query}' ======")
        async with AsyncSessionLocal() as session:
            # Use similarity_search
            results = await PostgreSQLVectorStore(session, rag_service.embedding_model).similarity_search(query, k=5)
            
            # Display results
            print(f"Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                offer = result["offer"]
                similarity = result["similarity"]
                
                # Extract coupon code from content
                coupon_code = "None"
                for line in offer.embedding.content.split('\n'):
                    if line.startswith("CouponCode:"):
                        coupon_code = line.replace("CouponCode:", "").strip()
                        break
                
                print(f"\nResult {i} (Similarity: {similarity:.4f}):")
                print(f"Campaign: {offer.campaign.name}")
                print(f"Title: {offer.title}")
                print(f"Coupon Code: {coupon_code}")
                print(f"Actual Offer Coupon: {offer.coupon_code or 'None'}")
                print(f"Description: {offer.description[:100]}...")

async def check_coupon_code_coverage():
    """
    Check how many offers have coupon codes
    """
    async with AsyncSessionLocal() as session:
        # Count offers with coupon codes
        offers_with_coupon_result = await session.execute(
            select(Offer).where(Offer.coupon_code != None)
        )
        offers_with_coupon = offers_with_coupon_result.scalars().all()
        
        # Count total offers
        total_offers_result = await session.execute(select(Offer))
        total_offers = len(total_offers_result.scalars().all())
        
        print(f"\n\nCoupon Code Coverage:")
        print(f"Total Offers: {total_offers}")
        print(f"Offers with Coupon Codes: {len(offers_with_coupon)} ({len(offers_with_coupon)/total_offers*100:.2f}%)")
        
        # Show some examples
        print("\nSample Offers with Coupon Codes:")
        for i, offer in enumerate(offers_with_coupon[:5], 1):
            print(f"{i}. {offer.title} - Coupon: {offer.coupon_code}")

async def main():
    # First check coupon code coverage
    await check_coupon_code_coverage()
    
    # Then test coupon code searches
    await test_coupon_code_searches()

if __name__ == "__main__":
    asyncio.run(main())
