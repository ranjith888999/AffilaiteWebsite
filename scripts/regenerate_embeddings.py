"""
Regenerate Embeddings Script

This script uses the updated RAG service to regenerate embeddings
with campaign information included.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, delete

from app.models.database import OfferEmbedding
from app.services.rag_service import rag_service

# Load environment variables
load_dotenv()

# Database configuration from environment variables
DB_HOST = os.getenv("DATABASE_HOST", "localhost")
DB_PORT = os.getenv("DATABASE_PORT", "5432")
DB_NAME = os.getenv("DATABASE_NAME", "postgres")
DB_USER = os.getenv("DATABASE_USER", "postgres")
DB_PASS = os.getenv("DATABASE_PASSWORD", "postgres")

# Build connection string
DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create async engine
async_engine = create_async_engine(DB_URL)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

async def regenerate_embeddings():
    """Regenerate embeddings with campaign information"""
    print("Regenerating embeddings with campaign information...")
    
    async with AsyncSessionLocal() as session:
        # Delete existing embeddings
        print("Deleting existing embeddings...")
        await session.execute(text("DELETE FROM offer_embeddings"))
        await session.commit()
        
        # Check offers count
        result = await session.execute(text("SELECT COUNT(*) FROM offers"))
        offers_count = result.scalar()
        print(f"Found {offers_count} offers in database")
        
        # Process all offers for embeddings
        print("Processing offers for embeddings...")
        await rag_service.process_offers_for_embeddings(session)
        
        # Check if embeddings were created
        result = await session.execute(text("SELECT COUNT(*) FROM offer_embeddings"))
        embeddings_count = result.scalar()
        print(f"Generated {embeddings_count} embeddings")
        
        print("Embeddings regenerated successfully!")

if __name__ == "__main__":
    asyncio.run(regenerate_embeddings())
