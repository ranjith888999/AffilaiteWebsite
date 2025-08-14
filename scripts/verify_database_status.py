"""
Script to verify the database status after loading offers and creating embeddings
"""
import sys
import os
import logging
import asyncio
import json

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import necessary modules
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.database import DATABASE_URL, ASYNC_DATABASE_URL
from sqlalchemy.orm import sessionmaker

# Create database engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create async engine for embeddings
async_engine = create_async_engine(ASYNC_DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

def check_database_status():
    """Check the status of the database tables"""
    with SessionLocal() as session:
        # Check campaign table
        campaign_count = session.execute(text("SELECT COUNT(*) FROM campaigns")).scalar()
        logger.info(f"Total campaigns in database: {campaign_count}")
        
        # Check offer table
        offer_count = session.execute(text("SELECT COUNT(*) FROM offers")).scalar()
        logger.info(f"Total offers in database: {offer_count}")
        
        # Get offer status distribution
        status_query = text("SELECT status, COUNT(*) FROM offers GROUP BY status")
        status_results = session.execute(status_query).fetchall()
        logger.info("Offer status distribution:")
        for status, count in status_results:
            logger.info(f"  {status}: {count}")
        
        # Check a sample offer
        sample_offer = session.execute(text("SELECT id, title, campaign_id FROM offers LIMIT 1")).fetchone()
        if sample_offer:
            logger.info(f"Sample offer: ID={sample_offer.id}, Title={sample_offer.title}")

async def check_embeddings():
    """Check the status of the embeddings"""
    async with AsyncSessionLocal() as session:
        # Check embedding table
        embedding_count = (await session.execute(text("SELECT COUNT(*) FROM offer_embeddings"))).scalar()
        logger.info(f"Total embeddings in database: {embedding_count}")
        
        # Check content type distribution
        content_type_query = text("SELECT content_type, COUNT(*) FROM offer_embeddings GROUP BY content_type")
        content_type_results = (await session.execute(content_type_query)).fetchall()
        logger.info("Embedding content type distribution:")
        for content_type, count in content_type_results:
            logger.info(f"  {content_type}: {count}")
        
        # Check embedding coverage
        coverage_query = text("""
        SELECT 
            COUNT(DISTINCT o.id) as total_offers,
            COUNT(DISTINCT e.offer_id) as offers_with_embeddings
        FROM offers o
        LEFT JOIN offer_embeddings e ON o.id = e.offer_id
        """)
        coverage_result = (await session.execute(coverage_query)).fetchone()
        if coverage_result:
            total_offers = coverage_result[0]
            offers_with_embeddings = coverage_result[1]
            coverage_pct = (offers_with_embeddings / total_offers * 100) if total_offers > 0 else 0
            logger.info(f"Embedding coverage: {offers_with_embeddings}/{total_offers} offers ({coverage_pct:.2f}%)")
        
        # Sample an embedding
        sample_query = text("""
        SELECT e.id, e.offer_id, e.content_type, e.content, o.title, c.name as campaign_name,
               length(e.embedding::text) as embedding_size
        FROM offer_embeddings e
        JOIN offers o ON e.offer_id = o.id
        JOIN campaigns c ON o.campaign_id = c.id
        LIMIT 1
        """)
        sample = (await session.execute(sample_query)).fetchone()
        if sample:
            logger.info(f"Sample embedding:")
            logger.info(f"  ID: {sample.id}")
            logger.info(f"  Offer ID: {sample.offer_id}")
            logger.info(f"  Offer Title: {sample.title}")
            logger.info(f"  Campaign: {sample.campaign_name}")
            logger.info(f"  Content Type: {sample.content_type}")
            logger.info(f"  Content Snippet: {sample.content[:100]}...")
            logger.info(f"  Embedding Size: {sample.embedding_size} chars")

async def main():
    """Main function to run the script"""
    try:
        logger.info("Checking database status")
        check_database_status()
        
        logger.info("\nChecking embeddings")
        await check_embeddings()
        
        logger.info("\nVerification completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
