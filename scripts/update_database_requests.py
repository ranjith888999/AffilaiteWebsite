"""
Database Update Script for Affiliate Website

This script:
1. Adds a campaign_name column to the offers table
2. Truncates existing data
3. Fetches new offers from Cuelinks API with correct campaign information
4. Regenerates embeddings with campaign information

Uses the requests library for API calls that was confirmed to work
"""

import os
import sys
import json
import asyncio
import requests
from datetime import datetime
from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import Base, Campaign, Offer
from app.services.rag_service import rag_service

# Load environment variables
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

# Synchronous engine for schema updates
sync_engine = create_engine(SYNC_DB_URL)

# Async engine for data operations
async_engine = create_async_engine(DB_URL)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# API constants
CUELINKS_API_KEY = os.getenv("CUELINKS_API_KEY", "MUmQPF2MLjDzMOHi0PSCdOwI082JAfj6vRLLT1QcY00")
CUELINKS_API_URL = "https://www.cuelinks.com/api/v2/offers.json"

def check_and_alter_schema():
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

def fetch_offers_from_api(page=1, per_page=50):
    """Fetch offers from Cuelinks API using requests"""
    print(f"Fetching offers from API (page {page})...")
    
    headers = {
        'Authorization': f'Token token={CUELINKS_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    params = {
        'page': page,
        'per_page': per_page
    }
    
    response = requests.get(CUELINKS_API_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: API returned status {response.status_code}")
        print(f"Response: {response.text}")
        return {"offers": []}

async def store_offers_in_db():
    """Fetch and store offers in database"""
    print("Starting to fetch and store offers...")
    
    async with AsyncSessionLocal() as session:
        page = 1
        total_offers = 0
        max_pages = 5  # Limit to 5 pages for testing
        
        while page <= max_pages:
            # Fetch offers using the requests library
            offers_data = fetch_offers_from_api(page=page)
            
            if "offers" not in offers_data or not offers_data["offers"]:
                print("No more offers found or reached end of data")
                break
            
            offers_count = len(offers_data["offers"])
            print(f"Processing page {page} with {offers_count} offers...")
            
            for offer_data in offers_data["offers"]:
                # Parse dates
                start_date_parsed = None
                end_date_parsed = None
                
                try:
                    if offer_data.get("start_date"):
                        start_date_parsed = datetime.strptime(offer_data["start_date"], "%Y-%m-%d")
                except Exception as e:
                    print(f"Error parsing start date: {e}")
                
                try:
                    if offer_data.get("end_date"):
                        end_date_parsed = datetime.strptime(offer_data["end_date"], "%Y-%m-%d")
                except Exception as e:
                    print(f"Error parsing end date: {e}")
                
                # Get campaign details
                campaign_id = offer_data.get("camapign_id")  # API has typo in field name
                campaign_name = offer_data.get("campaign", f"Campaign {campaign_id}")
                
                # Find or create campaign
                campaign_result = await session.execute(
                    text(f"SELECT id FROM campaigns WHERE campaign_id = {campaign_id}")
                )
                campaign_row = campaign_result.fetchone()
                
                if not campaign_row:
                    # Create new campaign
                    campaign = Campaign(
                        campaign_id=campaign_id,
                        name=campaign_name,
                        status="active"
                    )
                    session.add(campaign)
                    await session.flush()  # Get ID without committing
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
            
            # Commit after each page
            await session.commit()
            print(f"Committed page {page} with {offers_count} offers")
            
            # Move to next page
            page += 1
        
        print(f"Successfully stored {total_offers} offers from {page-1} pages")

async def generate_embeddings():
    """Generate embeddings for all offers with campaign information"""
    print("Generating embeddings with campaign information...")
    
    async with AsyncSessionLocal() as session:
        # Process all offers for embeddings
        await rag_service.process_offers_for_embeddings(session)
    
    print("Embeddings generated successfully.")

async def main():
    """Main function to run the entire process"""
    print("Starting database update process...")
    
    try:
        # Step 1: Update schema
        check_and_alter_schema()
        
        # Step 2: Truncate existing data
        await truncate_existing_data()
        
        # Step 3: Fetch and store offers
        await store_offers_in_db()
        
        # Step 4: Generate embeddings
        await generate_embeddings()
        
        print("Database update completed successfully!")
        
    except Exception as e:
        print(f"Error during database update: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
