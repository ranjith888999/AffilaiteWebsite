"""
Database Reset and Rebuild Script
This script resets the database, recreates tables, and loads fresh data.
"""

import os
import sys
import asyncio
import httpx
from datetime import datetime
import json
from dotenv import load_dotenv

# Add the parent directory to the path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from app.database import reset_database, get_db_sync
from app.models.database import Campaign, Offer
from app.services.cuelinks_service import CuelinksService

async def fetch_and_load_data():
    """Fetch data from Cuelinks API and load into the database"""
    # Initialize Cuelinks service
    cuelinks_service = CuelinksService()
    db = next(get_db_sync())
    
    try:
        print("Fetching campaigns from Cuelinks API...")
        campaigns_data = await cuelinks_service.get_all_campaigns(per_page=100)
        
        if "campaigns" in campaigns_data and len(campaigns_data["campaigns"]) > 0:
            print(f"Found {len(campaigns_data['campaigns'])} campaigns")
            
            # Store campaigns in database
            for campaign_data in campaigns_data["campaigns"]:
                campaign = Campaign(
                    campaign_id=campaign_data["id"],
                    name=campaign_data.get("name", ""),
                    description=campaign_data.get("description", ""),
                    status=campaign_data.get("status", ""),
                    category=json.dumps(campaign_data.get("categories", {}))
                )
                db.add(campaign)
            
            db.commit()
            print("Campaigns saved to database")
        else:
            print("No campaigns found or API error")
        
        print("Fetching offers from Cuelinks API...")
        offers_data = await cuelinks_service.get_offers(per_page=100)
        
        if "offers" in offers_data and len(offers_data["offers"]) > 0:
            print(f"Found {len(offers_data['offers'])} offers")
            
            # Store offers in database
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
                
                # Find campaign by Cuelinks campaign_id
                campaign_id = offer_data.get("camapign_id")  # Note: API has typo "camapign_id"
                campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
                
                if not campaign:
                    # Create a placeholder campaign if not found
                    campaign = Campaign(
                        campaign_id=campaign_id,
                        name=f"Campaign {campaign_id}",
                        status="active"
                    )
                    db.add(campaign)
                    db.flush()
                
                # Create offer with proper campaign relationship
                offer = Offer(
                    offer_id=offer_data["id"],
                    campaign_id=campaign.id,
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
                db.add(offer)
            
            db.commit()
            print("Offers saved to database")
        else:
            print("No offers found or API error")
            
    except Exception as e:
        print(f"Error fetching and loading data: {e}")
        db.rollback()
    finally:
        db.close()

async def main():
    # Reset database
    print("Resetting database...")
    reset_database()
    
    # Fetch and load fresh data
    print("Loading fresh data...")
    await fetch_and_load_data()
    
    print("Database reset and rebuild completed successfully!")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
