"""
Generate Embeddings for Offers

This script:
1. Connects directly to the database
2. Retrieves all offers
3. Generates embeddings for campaign names, titles, and descriptions
4. Stores embeddings in the offer_embeddings table
"""

import os
import sys
import json
import asyncio
from dotenv import load_dotenv
import logging
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database imports
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

# Sentence transformer for embeddings
from sentence_transformers import SentenceTransformer

# Import models
from app.models.database import Offer, OfferEmbedding, Campaign

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.getenv("DATABASE_HOST", "localhost")
DB_PORT = os.getenv("DATABASE_PORT", "5432")
DB_NAME = os.getenv("DATABASE_NAME", "postgres")
DB_USER = os.getenv("DATABASE_USER", "postgres")
DB_PASS = os.getenv("DATABASE_PASSWORD", "postgres")

# Build connection string
DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create async engine and session
async_engine = create_async_engine(DB_URL)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# Initialize the embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions

async def clear_existing_embeddings():
    """Clear all existing embeddings to start fresh"""
    async with AsyncSessionLocal() as session:
        try:
            # Delete all existing embeddings
            await session.execute(text("DELETE FROM offer_embeddings"))
            await session.commit()
            logger.info("All existing embeddings have been deleted")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error clearing embeddings: {str(e)}")
            raise

async def generate_embeddings():
    """Generate embeddings for all offers"""
    async with AsyncSessionLocal() as session:
        try:
            # Get all offers with campaign information
            query = text("""
                SELECT o.id, o.offer_id, o.campaign_id, o.campaign_name, o.title, o.description, 
                       o.terms_and_conditions, o.coupon_code, o.offer_type, o.status, o.categories
                FROM offers o
                ORDER BY o.id
            """)
            
            result = await session.execute(query)
            offers = result.fetchall()
            
            logger.info(f"Found {len(offers)} offers for embedding generation")
            
            if not offers:
                logger.warning("No offers found to generate embeddings for")
                return
            
            # Process each offer
            for offer in offers:
                offer_id = offer[0]  # First column is id
                campaign_id = offer[2]
                campaign_name = offer[3] or ""
                title = offer[4] or ""
                description = offer[5] or ""
                terms = offer[6] or ""
                coupon = offer[7] or ""
                offer_type = offer[8] or ""
                status = offer[9] or ""
                categories = offer[10] or "{}"
                
                logger.info(f"Processing offer {offer_id}: {title}")
                
                # Generate documents for embedding
                documents = []
                
                # Document types and their content
                doc_types = [
                    {"type": "campaign", "content": f"Campaign: {campaign_name}"},
                    {"type": "title", "content": title},
                    {"type": "description", "content": description},
                    {"type": "terms", "content": terms},
                    {"type": "combined", "content": f"Campaign: {campaign_name}\nTitle: {title}\nDescription: {description}\nType: {offer_type}\nCategories: {categories}"}
                ]
                
                # Generate metadata
                metadata = {
                    'offer_id': offer_id,
                    'campaign_id': campaign_id,
                    'campaign_name': campaign_name,
                    'title': title,
                    'categories': categories,
                    'status': status,
                    'offer_type': offer_type
                }
                
                # Generate and store embeddings for each document type
                for i, doc in enumerate(doc_types):
                    if not doc["content"].strip():
                        continue  # Skip empty content
                    
                    # Generate embedding
                    embedding = embedding_model.encode(doc["content"]).tolist()
                    
                    # Create document metadata
                    doc_metadata = {**metadata, 'type': doc["type"]}
                    
                    # Create embedding record
                    embedding_record = OfferEmbedding(
                        offer_id=offer_id,
                        campaign_id=campaign_id,
                        chunk_id=f"{offer_id}_{doc['type']}_{i}",
                        content=doc["content"],
                        content_type=doc["type"],
                        embedding=embedding,
                        meta_data=json.dumps(doc_metadata)
                    )
                    
                    session.add(embedding_record)
                
                # Commit every 10 offers to avoid large transactions
                if offer_id % 10 == 0:
                    await session.commit()
                    logger.info(f"Committed embeddings for {offer_id} offers")
            
            # Final commit for any remaining offers
            await session.commit()
            logger.info("All embeddings generated successfully")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

async def verify_embeddings():
    """Verify that embeddings were created successfully"""
    async with AsyncSessionLocal() as session:
        try:
            # Count embeddings
            count_query = text("SELECT COUNT(*) FROM offer_embeddings")
            result = await session.execute(count_query)
            count = result.scalar()
            
            # Count offers
            offers_query = text("SELECT COUNT(*) FROM offers")
            offers_result = await session.execute(offers_query)
            offers_count = offers_result.scalar()
            
            logger.info(f"Verification: Found {count} embeddings for {offers_count} offers")
            
            # Check embedding types
            types_query = text("SELECT content_type, COUNT(*) FROM offer_embeddings GROUP BY content_type")
            types_result = await session.execute(types_query)
            types = types_result.fetchall()
            
            logger.info("Embedding types distribution:")
            for type_info in types:
                logger.info(f"  - {type_info[0]}: {type_info[1]} embeddings")
            
            return count > 0
            
        except Exception as e:
            logger.error(f"Error verifying embeddings: {str(e)}")
            return False

async def main():
    """Main function to run the embedding generation"""
    logger.info("Starting embedding generation process")
    
    try:
        # Clear existing embeddings
        await clear_existing_embeddings()
        
        # Generate new embeddings
        await generate_embeddings()
        
        # Verify embeddings
        success = await verify_embeddings()
        
        if success:
            logger.info("Embedding generation completed successfully!")
        else:
            logger.error("Embedding generation failed or no embeddings were created")
            
    except Exception as e:
        logger.error(f"Error in embedding generation process: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
