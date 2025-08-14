"""
Script to test semantic search with explicit status parameter
"""
import sys
import os
import asyncio
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from app.database import get_async_db
from app.services.rag_service import rag_service

async def test_semantic_search_with_status():
    """Test semantic search with explicit status parameter"""
    logger.info("Starting semantic search test with explicit status")
    
    # Test query
    query = "beauty products from Nykaa"
    
    # Get async database session
    async for async_session in get_async_db():
        logger.info(f"Testing semantic search for: '{query}' with status 'live'")
        
        # Get recommendations using RAG with embeddings
        try:
            # Get recommendations using RAG with embeddings
            start_time = datetime.now()
            recommendations = await rag_service.get_offer_recommendations(
                query=query,
                session=async_session,
                top_k=5
            )
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Extract offers and answer
            offers_data = recommendations.get('offers', [])
            bot_response = recommendations.get('answer', '')
            
            logger.info(f"Response: {bot_response}")
            logger.info(f"Found {len(offers_data)} results in {processing_time:.3f} seconds")
            
            # Display each offer
            for i, offer in enumerate(offers_data, 1):
                logger.info(f"Result {i}: {offer.title} - Campaign: {offer.campaign_name}")
                
                # Get similarity score if available
                similarity = "N/A"
                for meta in recommendations.get('metadata', []):
                    if meta.get('offer_id') == offer.id:
                        similarity = meta.get('similarity', 'N/A')
                        break
                
                logger.info(f"  Similarity: {similarity}")
            
            logger.info("-" * 50)
            
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            logger.info("-" * 50)
        
        # Only need one session
        break
    
    logger.info("Semantic search test completed")

if __name__ == "__main__":
    asyncio.run(test_semantic_search_with_status())
