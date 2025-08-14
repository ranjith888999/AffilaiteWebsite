"""
Script to debug the RAG service
"""
import sys
import os
import asyncio
import logging
from datetime import datetime
import json

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
from app.database import get_async_db, AsyncSessionLocal

async def debug_rag_service():
    """Debug the RAG service and the embedding search"""
    logger.info("Starting RAG service debug")
    
    # Get async database session
    async with AsyncSessionLocal() as session:
        # Check the SQL query directly
        logger.info("Executing similarity search query manually")
        
        try:
            # Query with a simple WHERE clause (just status = 'active')
            query_sql = text("""
            SELECT 
                oe.id, oe.offer_id, oe.chunk_id, oe.content, oe.content_type, 
                oe.embedding, oe.created_at,
                oe.campaign_id, oe.meta_data,
                o.id AS offer_id, o.title, o.description, o.terms_and_conditions,
                o.coupon_code, o.image_url, o.offer_type, o.status, 
                o.url, o.affiliate_url, o.categories
            FROM offer_embeddings oe
            JOIN offers o ON oe.offer_id = o.id
            WHERE o.status = :status
            LIMIT 5
            """)
            
            result = await session.execute(query_sql, {"status": "active"})
            rows = result.fetchall()
            logger.info(f"Found {len(rows)} embeddings with status 'active'")
            
            if len(rows) > 0:
                logger.info("Query is working correctly")
                # Show sample data
                for i, row in enumerate(rows):
                    logger.info(f"Row {i+1}:")
                    logger.info(f"  Offer ID: {row.offer_id}")
                    logger.info(f"  Title: {row.title}")
                    logger.info(f"  Content Type: {row.content_type}")
                    logger.info(f"  Embedding Length: {len(row.embedding) if row.embedding else 'None'}")
            else:
                logger.error("No embeddings found with status 'active'")
                
                # Check if there are any active offers
                check_offers = text("SELECT COUNT(*) FROM offers WHERE status = :status")
                result = await session.execute(check_offers, {"status": "active"})
                active_offers = result.scalar()
                logger.info(f"Number of active offers: {active_offers}")
                
                # Check if there are any embeddings at all
                check_embeddings = text("SELECT COUNT(*) FROM offer_embeddings")
                result = await session.execute(check_embeddings)
                total_embeddings = result.scalar()
                logger.info(f"Total number of embeddings: {total_embeddings}")
                
                # Check if the join is the issue
                check_join = text("""
                SELECT COUNT(*) 
                FROM offer_embeddings oe
                JOIN offers o ON oe.offer_id = o.id
                """)
                result = await session.execute(check_join)
                join_count = result.scalar()
                logger.info(f"Number of rows after join: {join_count}")
                
                # Check status values
                check_statuses = text("SELECT DISTINCT status FROM offers")
                result = await session.execute(check_statuses)
                statuses = [row[0] for row in result.fetchall()]
                logger.info(f"Status values in offers table: {statuses}")
        
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
    
    logger.info("RAG service debug completed")

if __name__ == "__main__":
    asyncio.run(debug_rag_service())
