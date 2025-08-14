"""
Optimize the embeddings in the database by using only combined embeddings
This script reduces database size and improves query performance
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
import numpy as np
from sqlalchemy import text
from sentence_transformers import SentenceTransformer
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import app modules
from app.models.database import Offer, Campaign, OfferEmbedding
from app.database import AsyncSessionLocal

# Load environment variables
load_dotenv()

async def clear_existing_embeddings(session):
    """Clear existing embeddings to start fresh"""
    try:
        await session.execute(text("DELETE FROM offer_embeddings"))
        await session.commit()
        logger.info("Cleared existing embeddings")
    except Exception as e:
        await session.rollback()
        logger.error(f"Error clearing embeddings: {e}")
        raise

async def get_offers_with_campaigns(session, batch_size=10, offset=0):
    """Get offers with their associated campaign names"""
    query = text("""
        SELECT o.*, c.name as campaign_name
        FROM offers o
        LEFT JOIN campaigns c ON o.campaign_id = c.id
        ORDER BY o.id
        LIMIT :limit OFFSET :offset
    """)
    
    result = await session.execute(query, {"limit": batch_size, "offset": offset})
    return result.fetchall()

async def generate_optimized_embeddings(session):
    """Generate optimized embeddings using only the combined approach"""
    # Initialize the embedding model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    try:
        # Get total count of offers
        count_result = await session.execute(text("SELECT COUNT(*) FROM offers"))
        total_offers = count_result.scalar()
        logger.info(f"Found {total_offers} offers to process")
        
        # Process offers in batches
        offset = 0
        offers_processed = 0
        batch_counter = 0
        BATCH_SIZE = 10
        
        while offset < total_offers:
            offers = await get_offers_with_campaigns(session, BATCH_SIZE, offset)
            if not offers:
                break
            
            batch_counter += 1
            logger.info(f"Processing batch {batch_counter} ({len(offers)} offers)")
            
            for offer in offers:
                # Create combined text with all relevant information
                combined_text = f"Campaign: {getattr(offer, 'campaign_name', '') or ''}\n"
                combined_text += f"Title: {offer.title or ''}\n"
                combined_text += f"Description: {offer.description or ''}\n"
                combined_text += f"Category: {offer.categories or ''}\n"
                combined_text += f"Type: {offer.offer_type or ''}\n"
                if offer.coupon_code:
                    combined_text += f"Coupon: {offer.coupon_code}\n"
                
                # Generate embedding
                embedding = model.encode(combined_text).tolist()
                
                # Create metadata
                metadata = {
                    'offer_id': offer.id,
                    'title': offer.title,
                    'categories': offer.categories,
                    'status': offer.status,
                    'offer_type': offer.offer_type,
                    'campaign_id': offer.campaign_id,
                    'campaign_name': getattr(offer, 'campaign_name', None)
                }
                
                # Create embedding record
                embedding_record = OfferEmbedding(
                    offer_id=offer.id,
                    campaign_id=offer.campaign_id,
                    chunk_id=f"{offer.id}_combined",
                    content=combined_text,
                    content_type='combined',
                    embedding=embedding,
                    meta_data=json.dumps(metadata)
                )
                
                session.add(embedding_record)
                offers_processed += 1
                
                # Log progress for each offer
                logger.info(f"Processing offer {offer.id}: {offer.title}")
            
            # Commit batch
            await session.commit()
            logger.info(f"Committed embeddings for {offers_processed} offers")
            
            # Update offset for next batch
            offset += BATCH_SIZE
        
        logger.info(f"Successfully processed {offers_processed} offers with optimized embeddings")
        
        # Verify the results
        verification_query = text("""
            SELECT COUNT(*) as count, content_type 
            FROM offer_embeddings 
            GROUP BY content_type
        """)
        verification_result = await session.execute(verification_query)
        verification_data = verification_result.fetchall()
        
        logger.info("Verification of embeddings:")
        for row in verification_data:
            logger.info(f"  - {row.content_type}: {row.count} embeddings")
        
        logger.info("Embedding optimization completed successfully!")
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Error generating optimized embeddings: {e}")
        raise

async def main():
    """Main function to run the embedding optimization"""
    try:
        async with AsyncSessionLocal() as session:
            # Clear existing embeddings
            await clear_existing_embeddings(session)
            
            # Generate optimized embeddings
            await generate_optimized_embeddings(session)
            
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
