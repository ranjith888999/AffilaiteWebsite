"""
Script to directly test similarity search in RAG service
"""
import sys
import os
import asyncio
import logging
import json
import numpy as np
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
from app.database import AsyncSessionLocal
from sentence_transformers import SentenceTransformer
from sqlalchemy import text

async def test_similarity_search():
    """Directly test the similarity search functionality"""
    logger.info("Starting direct similarity search test")
    
    # Load embedding model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("Loaded embedding model")
    
    # Test query
    query = "beauty products from Nykaa"
    query_embedding = model.encode(query).tolist()
    logger.info(f"Created query embedding for: '{query}'")
    
    async with AsyncSessionLocal() as session:
        # Directly execute SQL query to get embeddings
        query_sql = text("""
        SELECT 
            oe.id, oe.offer_id, oe.chunk_id, oe.content, oe.content_type, 
            oe.embedding, oe.created_at,
            oe.campaign_id, oe.meta_data,
            o.id AS o_id, o.title AS o_title, o.description AS o_description, 
            o.coupon_code AS o_coupon_code, o.image_url AS o_image_url, 
            o.offer_type AS o_offer_type, o.status AS o_status, 
            o.url AS o_url, o.affiliate_url AS o_affiliate_url, 
            o.categories AS o_categories, o.campaign_name AS o_campaign_name
        FROM offer_embeddings oe
        JOIN offers o ON oe.offer_id = o.id
        WHERE o.status = :status
        """)
        
        result = await session.execute(query_sql, {"status": "live"})
        embeddings_with_offers = result.fetchall()
        logger.info(f"Found {len(embeddings_with_offers)} embeddings matching status='live'")
        
        if not embeddings_with_offers:
            logger.warning("No embeddings found matching the query")
            return
        
        # Calculate cosine similarity
        similarities = []
        for row in embeddings_with_offers:
            try:
                # Get embedding data
                embedding_data = row.embedding
                
                if embedding_data is None:
                    logger.warning("No embedding data found in row")
                    continue
                    
                # Convert to numpy array
                stored_embedding = np.array(embedding_data)
                query_embedding_np = np.array(query_embedding)
                
                # Calculate cosine similarity
                norm_stored = np.linalg.norm(stored_embedding)
                norm_query = np.linalg.norm(query_embedding_np)
                
                if norm_stored > 0 and norm_query > 0:
                    cosine_sim = np.dot(stored_embedding, query_embedding_np) / (norm_stored * norm_query)
                else:
                    cosine_sim = 0.0
                
                # Skip if similarity is too low (this might be the issue!)
                if cosine_sim < 0.05:  # Try with a very low threshold
                    continue
                
                # Extract offer information
                offer_info = {
                    "id": row.o_id,
                    "offer_id": row.offer_id,
                    "title": row.o_title,
                    "description": row.o_description[:100] + "..." if row.o_description else None,
                    "campaign_name": row.o_campaign_name,
                    "content": row.content[:100] + "..." if row.content else None,
                    "similarity": float(cosine_sim)
                }
                
                similarities.append(offer_info)
                
            except Exception as e:
                logger.error(f"Error processing row: {str(e)}")
                continue
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        top_results = similarities[:5]
        
        logger.info(f"Found {len(top_results)} results with similarity matching")
        
        # Display results
        for i, result in enumerate(top_results, 1):
            logger.info(f"Result {i}:")
            logger.info(f"  Title: {result['title']}")
            logger.info(f"  Campaign: {result['campaign_name']}")
            logger.info(f"  Similarity: {result['similarity']}")
            logger.info(f"  Content: {result['content']}")
            logger.info("-" * 50)
    
    logger.info("Similarity search test completed")

if __name__ == "__main__":
    asyncio.run(test_similarity_search())
