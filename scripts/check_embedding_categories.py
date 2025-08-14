#!/usr/bin/env python
"""
Check embeddings to verify category information was added correctly
"""

import os
import sys
import asyncio
import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

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

engine = create_async_engine(ASYNC_DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def check_embedding_categories():
    """
    Check random embeddings to verify that category information was added
    """
    async with async_session() as session:
        # Get 10 random embeddings to check
        stmt = select(OfferEmbedding).order_by(func.random()).limit(10)
        result = await session.execute(stmt)
        embeddings = result.scalars().all()
        
        print(f"Checking {len(embeddings)} random embeddings for category information:")
        
        for i, embedding in enumerate(embeddings, 1):
            # Check if Category is in the content
            has_category = "Category:" in embedding.content
            
            print(f"\nEmbedding {i} (Offer ID: {embedding.offer_id}):")
            print(f"Has Category: {has_category}")
            
            # Print the content with line breaks for better readability
            lines = embedding.content.split("\n")
            category_line = None
            
            for line in lines:
                if line.startswith("Category:"):
                    category_line = line
                    break
            
            # Print the category line if found
            if category_line:
                print(f"Category Line: {category_line}")
            
            # Print a portion of the content
            print("Content Preview:")
            print("\n".join(lines[:5]) + "...")

async def main():
    await check_embedding_categories()

if __name__ == "__main__":
    asyncio.run(main())
