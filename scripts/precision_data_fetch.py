"""
PRECISION DATA FETCH - Get all 1,184 offers using proper pagination
"""

import asyncio
import os
import sys
import json
from datetime import datetime
import time
import math

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def precision_data_fetch():
    """Fetch ALL 1,184 offers using proper pagination"""
    from app.database import SessionLocal
    from app.services.cuelinks_service import cuelinks_service
    from app.models.database import Offer, OfferEmbedding
    from sentence_transformers import SentenceTransformer
    
    print("🎯 PRECISION DATA FETCH - Getting all 1,184 offers...")
    
    # Load embedding model
    print("🤖 Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    db = SessionLocal()
    
    try:
        # Clear existing data first
        print("🗑️  Clearing existing data...")
        deleted_embeddings = db.query(OfferEmbedding).delete()
        deleted_offers = db.query(Offer).delete()
        db.commit()
        print(f"   ✅ Deleted {deleted_embeddings} embeddings, {deleted_offers} offers")
        
        all_offers = []
        api_calls_used = 0
        
        # First, get the total count to calculate pages needed
        print("📊 Getting total count...")
        first_response = await cuelinks_service.get_offers(
            page=1, 
            per_page=100,
            start_date="2020-01-01",  # Wide date range
            end_date="2030-12-31"
        )
        api_calls_used += 1
        
        if not first_response:
            print("❌ No response from API")
            return
        
        total_count = first_response.get('total_count', 0)
        offers_per_page = 100
        total_pages = math.ceil(total_count / offers_per_page)
        
        print(f"📊 FOUND: {total_count} total offers across {total_pages} pages")
        
        # Add offers from first response
        if 'offers' in first_response:
            all_offers.extend(first_response['offers'])
            print(f"   📦 Page 1: Got {len(first_response['offers'])} offers")
        
        # Fetch remaining pages
        for page in range(2, total_pages + 1):
            print(f"   📄 Fetching page {page}/{total_pages}...")
            
            try:
                offers_response = await cuelinks_service.get_offers(
                    page=page, 
                    per_page=100,
                    start_date="2020-01-01",
                    end_date="2030-12-31"
                )
                api_calls_used += 1
                
                if offers_response and 'offers' in offers_response:
                    offers = offers_response['offers']
                    all_offers.extend(offers)
                    print(f"   📦 Page {page}: Got {len(offers)} offers (Total: {len(all_offers)})")
                else:
                    print(f"   ❌ No offers on page {page}")
                
                # Small delay to be respectful
                await asyncio.sleep(0.3)
                
            except Exception as e:
                print(f"   ❌ Error fetching page {page}: {e}")
                continue
        
        print(f"🎉 FETCHED {len(all_offers)} TOTAL OFFERS using {api_calls_used} API calls")
        
        if not all_offers:
            print("❌ No offers to process")
            return
        
        # Remove duplicates based on offer ID
        unique_offers = {}
        for offer in all_offers:
            offer_id = offer.get('id')
            if offer_id:
                unique_offers[offer_id] = offer
        
        unique_offers_list = list(unique_offers.values())
        print(f"🔄 After deduplication: {len(unique_offers_list)} unique offers")
        
        # Insert all offers
        print("💾 Inserting all offers into database...")
        offers_created = 0
        
        for offer_data in unique_offers_list:
            offer_id = offer_data.get('id')
            if not offer_id:
                continue
            
            try:
                new_offer = Offer(
                    offer_id=offer_id,
                    title=offer_data.get('title', '')[:500],
                    description=offer_data.get('description', '')[:1000],
                    coupon_code=offer_data.get('coupon_code', ''),
                    affiliate_url=offer_data.get('affiliate_url', ''),
                    status=offer_data.get('status', 'active'),
                    campaign_name=offer_data.get('campaign', '')[:200],
                    categories=json.dumps(offer_data.get('categories', {})),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(new_offer)
                offers_created += 1
                
                # Commit in batches for better performance
                if offers_created % 100 == 0:
                    db.commit()
                    print(f"   ⚡ Inserted {offers_created}/{len(unique_offers_list)} offers...")
                    
            except Exception as e:
                print(f"   ⚠️  Error inserting offer {offer_id}: {e}")
                continue
        
        # Final commit for remaining offers
        db.commit()
        print(f"✅ INSERTED {offers_created} OFFERS")
        
        # Generate embeddings for all offers
        print("🤖 Generating embeddings for all offers...")
        
        # Get all offers with their database IDs
        all_db_offers = db.query(Offer).all()
        embeddings_created = 0
        
        for i, offer in enumerate(all_db_offers):
            try:
                # Create text for embedding
                text_content = f"{offer.title} {offer.description} {offer.coupon_code or ''}"
                
                # Generate embedding
                embedding = model.encode(text_content)
                
                # Save to database
                offer_embedding = OfferEmbedding(
                    offer_id=offer.id,
                    embedding=embedding.tolist(),
                    created_at=datetime.now()
                )
                db.add(offer_embedding)
                embeddings_created += 1
                
                # Commit in batches for better performance
                if embeddings_created % 50 == 0:
                    db.commit()
                    print(f"   🧠 Generated {embeddings_created}/{len(all_db_offers)} embeddings...")
                    
            except Exception as e:
                print(f"   ⚠️  Error generating embedding for offer {offer.id}: {e}")
                continue
        
        # Final commit for remaining embeddings
        db.commit()
        print(f"✅ GENERATED {embeddings_created} EMBEDDINGS")
        
        # Final summary
        print("\n" + "="*60)
        print("🎯 PRECISION DATA FETCH COMPLETE!")
        print("="*60)
        print(f"📊 API Calls Used: {api_calls_used}")
        print(f"📦 Total Offers Fetched: {len(all_offers)}")
        print(f"🔄 Unique Offers: {len(unique_offers_list)}")
        print(f"💾 Offers Inserted: {offers_created}")
        print(f"🧠 Embeddings Generated: {embeddings_created}")
        print(f"🎯 Target was 1,184 offers - We got {offers_created}!")
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        db.rollback()
        
    finally:
        db.close()

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    
    print("🎯 PRECISION DATA FETCH")
    print("📊 Target: All 1,184 offers from Cuelinks API")
    print("📞 Estimated API calls: ~12 calls")
    print("⏱️  Estimated time: 5-7 minutes")
    print("\nStarting in 3 seconds...")
    time.sleep(3)
    
    asyncio.run(precision_data_fetch())
