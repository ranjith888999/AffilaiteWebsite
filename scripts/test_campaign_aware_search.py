"""
Test script for improved RAG search with campaign awareness

This script tests the RAG service's ability to handle queries related to specific campaigns
"""

import os
import sys
import asyncio
import json

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.services.rag_service import rag_service
from app.database import get_db

# Database URL from environment
DB_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/affiliate_website")

# Create async engine and session
async_engine = create_async_engine(DB_URL)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

async def test_campaign_search():
    """Test the RAG search with campaign-related queries"""
    print("Testing campaign-aware RAG search...")
    
    # Sample queries to test
    test_queries = [
        "Show me Amazon offers",
        "What are the best Flipkart coupons?",
        "Latest Myntra discounts",
        "Nike shoes offers",
        "Travel discount offers",
        "Food delivery coupons",
        "Electronics deals"
    ]
    
    async with AsyncSessionLocal() as session:
        for query in test_queries:
            print(f"\n\n>>> Testing query: '{query}'")
            
            # Perform search
            results = await rag_service.get_offer_recommendations(query, session, top_k=3)
            
            # Display results
            print(f"Found {len(results['offers'])} relevant offers with confidence {results['confidence']:.2f}")
            print(f"Answer: {results['answer']}")
            
            print("\nTop offers:")
            for i, offer in enumerate(results['offers'], 1):
                print(f"{i}. {offer.title}")
                print(f"   Campaign: {getattr(offer, 'campaign_name', 'N/A')}")
                if hasattr(offer, 'description') and offer.description:
                    desc = offer.description[:100] + "..." if len(offer.description) > 100 else offer.description
                    print(f"   {desc}")
                if hasattr(offer, 'coupon_code') and offer.coupon_code:
                    print(f"   Coupon: {offer.coupon_code}")
                print()

async def main():
    try:
        await test_campaign_search()
        print("Test completed successfully!")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
