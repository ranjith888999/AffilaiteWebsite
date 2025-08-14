"""
Database Schema Migration and Data Refresh Script

This script:
1. Checks and alters the offers table to add the campaign_name column
2. Truncates existing data from offers and offer_embeddings tables
3. Fetches new offers from Cuelinks API with correct campaign information
4. Regenerates embeddings with campaign information included
"""

import os
import sys
import json
import asyncio
import httpx
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, create_engine, MetaData, Table, Column, String
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.services.cuelinks_service import cuelinks_service
from app.services.rag_service import rag_service
from app.models.database import Base, Campaign, Offer, OfferEmbedding
from app.database import get_db

# Database URL from environment or .env file
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration from environment variables
DB_HOST = os.getenv("DATABASE_HOST", "localhost")
DB_PORT = os.getenv("DATABASE_PORT", "5432")
DB_NAME = os.getenv("DATABASE_NAME", "postgres")
DB_USER = os.getenv("DATABASE_USER", "postgres")
DB_PASS = os.getenv("DATABASE_PASSWORD", "postgres")

# Build connection strings
DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
SYNC_DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Synchronous engine for altering tables
sync_engine = create_engine(SYNC_DB_URL)
# Async engine for data operations
async_engine = create_async_engine(DB_URL)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

async def check_and_alter_schema():
    """Check and alter database schema to add campaign_name column"""
    print("Checking database schema...")
    
    # Check if campaign_name column exists in offers table
    with sync_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'offers' AND column_name = 'campaign_name'
        """))
        column_exists = result.fetchone() is not None
        
        if not column_exists:
            print("Adding campaign_name column to offers table...")
            conn.execute(text("""
                ALTER TABLE offers 
                ADD COLUMN campaign_name VARCHAR(500)
            """))
            
            # Create index on campaign_name
            conn.execute(text("""
                CREATE INDEX idx_offers_campaign_name ON offers (campaign_name)
            """))
            
            print("Schema updated successfully.")
        else:
            print("Campaign_name column already exists.")

async def truncate_existing_data():
    """Truncate existing data from offers and offer_embeddings tables"""
    print("Truncating existing data...")
    
    async with AsyncSessionLocal() as session:
        # Delete all embeddings first (foreign key constraint)
        await session.execute(text("DELETE FROM offer_embeddings"))
        # Delete all offers
        await session.execute(text("DELETE FROM offers"))
        # Commit changes
        await session.commit()
    
    print("Data truncated successfully.")

async def fetch_and_store_offers():
    """Fetch offers from Cuelinks API and store in database"""
    print("Fetching offers from Cuelinks API...")
    
    # Ensure cuelinks_service has the correct base_url
    if not cuelinks_service.base_url or not cuelinks_service.base_url.startswith(('http://', 'https://')):
        cuelinks_service.base_url = "https://www.cuelinks.com/api/v2"
        print(f"Updated Cuelinks base URL to: {cuelinks_service.base_url}")
    
    async with AsyncSessionLocal() as session:
        # Fetch offers directly - we'll get campaign info from each offer
        page = 1
        total_offers = 0
        
        while True:
            offers_data = await cuelinks_service.get_offers(page=page, per_page=50)
            
            if "offers" not in offers_data or not offers_data["offers"]:
                break
                
            print(f"Processing page {page} with {len(offers_data['offers'])} offers...")
            
            for offer_data in offers_data["offers"]:
                # Parse dates
                start_date_parsed = None
                end_date_parsed = None
                
                try:
                    if offer_data.get("start_date"):
                        start_date_parsed = datetime.strptime(offer_data["start_date"], "%Y-%m-%d")
                except:
                    pass
                
                try:
                    if offer_data.get("end_date"):
                        end_date_parsed = datetime.strptime(offer_data["end_date"], "%Y-%m-%d")
                except:
                    pass
                
                # Find campaign ID (API has typo "camapign_id")
                campaign_id = offer_data.get("camapign_id")
                campaign_name = offer_data.get("campaign", f"Campaign {campaign_id}")
                
                # Check if campaign exists
                campaign_result = await session.execute(
                    text(f"SELECT id FROM campaigns WHERE campaign_id = {campaign_id}")
                )
                campaign_row = campaign_result.fetchone()
                
                if not campaign_row:
                    # Create a new campaign
                    campaign = Campaign(
                        campaign_id=campaign_id,
                        name=campaign_name,
                        status="active",
                        category=json.dumps({}),  # Empty category for now
                    )
                    session.add(campaign)
                    await session.flush()  # Get the ID without committing
                    db_campaign_id = campaign.id
                else:
                    db_campaign_id = campaign_row[0]
                
                # Create offer with campaign_name
                offer = Offer(
                    offer_id=offer_data["id"],
                    campaign_id=db_campaign_id,
                    campaign_name=campaign_name,  # Store campaign name directly
                    title=offer_data.get("title", ""),
                    description=offer_data.get("description", ""),
                    terms_and_conditions=offer_data.get("terms_and_condition", ""),
                    coupon_code=offer_data.get("coupon_code", ""),
                    image_url=offer_data.get("image_url", ""),
                    offer_type=offer_data.get("type", ""),
                    shipping_charge=offer_data.get("shipping_charge", ""),
                    status=offer_data.get("status", ""),
                    url=offer_data.get("url", ""),
                    affiliate_url=offer_data.get("affiliate_url", ""),
                    start_date=start_date_parsed,
                    end_date=end_date_parsed,
                    categories=json.dumps(offer_data.get("categories", {}))
                )
                session.add(offer)
                total_offers += 1
            
            await session.commit()
            page += 1
            
            # Limit to 5 pages for testing
            if page > 5:
                break
        
        print(f"Successfully stored {total_offers} offers.")

async def generate_embeddings():
    """Generate embeddings for all offers with campaign information"""
    print("Generating embeddings with campaign information...")
    
    async with AsyncSessionLocal() as session:
        # Process all offers for embeddings
        await rag_service.process_offers_for_embeddings(session)
    
    print("Embeddings generated successfully.")

async def main():
    """Main function to run the migration"""
    print("Starting database migration and data refresh...")
    
    try:
        # Check and alter schema
        await check_and_alter_schema()
        
        # Truncate existing data
        await truncate_existing_data()
        
        # Fetch and store offers
        await fetch_and_store_offers()
        
        # Generate embeddings
        await generate_embeddings()
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
