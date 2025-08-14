"""
Direct Database Update Script for Affiliate Website

This script uses direct SQL execution with psycopg2 for more reliable database operations
1. Adds a campaign_name column to the offers table
2. Truncates existing data
3. Fetches new offers from Cuelinks API with correct campaign information
4. Regenerates embeddings with campaign information
"""

import os
import sys
import json
import asyncio
import requests
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Database configuration from environment variables
DB_HOST = os.getenv("DATABASE_HOST", "localhost")
DB_PORT = os.getenv("DATABASE_PORT", "5432")
DB_NAME = os.getenv("DATABASE_NAME", "postgres")
DB_USER = os.getenv("DATABASE_USER", "postgres")
DB_PASS = os.getenv("DATABASE_PASSWORD", "postgres")

# API constants
CUELINKS_API_KEY = os.getenv("CUELINKS_API_KEY", "MUmQPF2MLjDzMOHi0PSCdOwI082JAfj6vRLLT1QcY00")
CUELINKS_API_URL = "https://www.cuelinks.com/api/v2/offers.json"

def get_db_connection():
    """Create a database connection"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def update_schema():
    """Update database schema to add campaign_name column"""
    print("Updating database schema...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'offers' AND column_name = 'campaign_name'
        """)
        column_exists = cursor.fetchone() is not None
        
        if not column_exists:
            print("Adding campaign_name column to offers table...")
            cursor.execute("""
                ALTER TABLE offers 
                ADD COLUMN campaign_name VARCHAR(500)
            """)
            
            # Create index on campaign_name
            cursor.execute("""
                CREATE INDEX idx_offers_campaign_name ON offers (campaign_name)
            """)
            
            conn.commit()
            print("Schema updated successfully.")
        else:
            print("Campaign_name column already exists.")
    
    except Exception as e:
        conn.rollback()
        print(f"Error updating schema: {e}")
    finally:
        cursor.close()
        conn.close()

def truncate_data():
    """Truncate existing data"""
    print("Truncating existing data...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Delete all embeddings first (foreign key constraint)
        cursor.execute("DELETE FROM offer_embeddings")
        # Delete all offers
        cursor.execute("DELETE FROM offers")
        
        conn.commit()
        print("Data truncated successfully.")
    
    except Exception as e:
        conn.rollback()
        print(f"Error truncating data: {e}")
    finally:
        cursor.close()
        conn.close()

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

def store_offers():
    """Fetch and store offers in database"""
    print("Starting to fetch and store offers...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
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
                start_date = None
                end_date = None
                
                try:
                    if offer_data.get("start_date"):
                        start_date = offer_data.get("start_date")
                except Exception as e:
                    print(f"Error parsing start date: {e}")
                
                try:
                    if offer_data.get("end_date"):
                        end_date = offer_data.get("end_date")
                except Exception as e:
                    print(f"Error parsing end date: {e}")
                
                # Get campaign details
                campaign_id = offer_data.get("camapign_id")  # API has typo in field name
                campaign_name = offer_data.get("campaign", f"Campaign {campaign_id}")
                
                # Find or create campaign
                cursor.execute(
                    "SELECT id FROM campaigns WHERE campaign_id = %s",
                    (campaign_id,)
                )
                campaign_row = cursor.fetchone()
                
                if not campaign_row:
                    # Create new campaign
                    cursor.execute(
                        """
                        INSERT INTO campaigns 
                        (campaign_id, name, status, created_at, updated_at)
                        VALUES (%s, %s, %s, NOW(), NOW())
                        RETURNING id
                        """,
                        (campaign_id, campaign_name, 'active')
                    )
                    db_campaign_id = cursor.fetchone()[0]
                else:
                    db_campaign_id = campaign_row[0]
                
                # Create offer with campaign_name
                cursor.execute(
                    """
                    INSERT INTO offers 
                    (offer_id, campaign_id, campaign_name, title, description, 
                    terms_and_conditions, coupon_code, image_url, offer_type, 
                    shipping_charge, status, url, affiliate_url, 
                    start_date, end_date, categories, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """,
                    (
                        offer_data["id"], 
                        db_campaign_id,
                        campaign_name,
                        offer_data.get("title", ""),
                        offer_data.get("description", ""),
                        offer_data.get("terms_and_condition", ""),
                        offer_data.get("coupon_code", ""),
                        offer_data.get("image_url", ""),
                        offer_data.get("type", ""),
                        offer_data.get("shipping_charge", ""),
                        offer_data.get("status", ""),
                        offer_data.get("url", ""),
                        offer_data.get("affiliate_url", ""),
                        start_date,
                        end_date,
                        json.dumps(offer_data.get("categories", {}))
                    )
                )
                total_offers += 1
            
            # Commit after each page
            conn.commit()
            print(f"Committed page {page} with {offers_count} offers")
            
            # Move to next page
            page += 1
        
        print(f"Successfully stored {total_offers} offers from {page-1} pages")
    
    except Exception as e:
        conn.rollback()
        print(f"Error storing offers: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

def regenerate_embeddings():
    """Run the rebuild_embeddings.py script to regenerate embeddings"""
    print("Regenerating embeddings with campaign information...")
    
    try:
        # Use the existing script for rebuilding embeddings
        # This uses the RAG service which we've already updated
        import subprocess
        result = subprocess.run(["python", "scripts/rebuild_embeddings.py"], 
                               capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print(f"Errors during embedding generation: {result.stderr}")
        
        print("Embeddings regeneration completed.")
    
    except Exception as e:
        print(f"Error regenerating embeddings: {e}")

def main():
    """Main function to run the entire process"""
    print("Starting database update process...")
    
    try:
        # Step 1: Update schema
        update_schema()
        
        # Step 2: Truncate existing data
        truncate_data()
        
        # Step 3: Fetch and store offers
        store_offers()
        
        # Step 4: Regenerate embeddings
        regenerate_embeddings()
        
        print("Database update completed successfully!")
        
    except Exception as e:
        print(f"Error during database update: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
