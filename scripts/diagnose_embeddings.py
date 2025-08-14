"""
Script to diagnose embeddings and query execution
"""
import sys
import os
import asyncio
import logging
from datetime import datetime
import numpy as np

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from sqlalchemy import text
from app.database import AsyncSessionLocal
from sentence_transformers import SentenceTransformer

async def diagnose_embeddings():
    """Diagnose embeddings and SQL query execution"""
    logger.info("Starting embeddings diagnostics")
    
    # Load embedding model directly
    model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("Loaded embedding model")
    
    # Create a test query embedding
    query = "I need beauty products from Nykaa"
    query_embedding = model.encode(query).tolist()
    logger.info(f"Created query embedding for: '{query}'")
    
    async with AsyncSessionLocal() as session:
        # 1. Check total embeddings
        result = await session.execute(text("SELECT COUNT(*) FROM offer_embeddings"))
        total_count = result.scalar()
        logger.info(f"Total embeddings in database: {total_count}")
        
        # 2. Check content types
        result = await session.execute(text("SELECT content_type, COUNT(*) FROM offer_embeddings GROUP BY content_type"))
        content_types = result.fetchall()
        for ct in content_types:
            logger.info(f"Content type: {ct[0]}, Count: {ct[1]}")
            
        # 3. Check statuses in offers table
        result = await session.execute(text("SELECT status, COUNT(*) FROM offers GROUP BY status"))
        statuses = result.fetchall()
        for status in statuses:
            logger.info(f"Status: {status[0]}, Count: {status[1]}")
            
        # 4. Sample some offer_embeddings directly
        result = await session.execute(text("SELECT id, offer_id, content, content_type, embedding FROM offer_embeddings LIMIT 2"))
        samples = result.fetchall()
        for i, sample in enumerate(samples):
            logger.info(f"Sample {i+1}:")
            logger.info(f"  ID: {sample.id}")
            logger.info(f"  Offer ID: {sample.offer_id}")
            logger.info(f"  Content: {sample.content[:100]}...")
            logger.info(f"  Content Type: {sample.content_type}")
            logger.info(f"  Embedding Length: {len(sample.embedding) if sample.embedding else 'None'}")
            
            # Try to compute similarity
            if sample.embedding:
                embedding_np = np.array(sample.embedding)
                query_np = np.array(query_embedding)
                
                # Calculate cosine similarity with error handling
                try:
                    norm_stored = np.linalg.norm(embedding_np)
                    norm_query = np.linalg.norm(query_np)
                    
                    if norm_stored > 0 and norm_query > 0:
                        cosine_sim = np.dot(embedding_np, query_np) / (norm_stored * norm_query)
                        logger.info(f"  Cosine Similarity: {cosine_sim}")
                    else:
                        logger.warning("  Zero norm detected in embeddings")
                except Exception as e:
                    logger.error(f"  Error calculating similarity: {str(e)}")
            
        # 5. Try the basic join query with LIMIT
        query_sql = text("""
        SELECT 
            oe.id, oe.offer_id, oe.content_type, o.status, o.title
        FROM offer_embeddings oe
        JOIN offers o ON oe.offer_id = o.id
        WHERE o.status = :status
        LIMIT 5
        """)
        
        result = await session.execute(query_sql, {"status": "live"})
        join_results = result.fetchall()
        logger.info(f"Basic join query returned {len(join_results)} results")
        for row in join_results:
            logger.info(f"  ID: {row.id}, Offer ID: {row.offer_id}, Content Type: {row.content_type}, Status: {row.status}, Title: {row.title}")
    
    logger.info("Embeddings diagnostics completed")

if __name__ == "__main__":
    asyncio.run(diagnose_embeddings())
