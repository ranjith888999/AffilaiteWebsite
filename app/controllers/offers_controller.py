from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.cuelinks_service import cuelinks_service
from app.models.database import Offer, Campaign
from typing import Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/offers", tags=["offers"])

@router.get("/")
async def get_offers(
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    categories: Optional[str] = None,
    campaigns: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get offers from Cuelinks API and store in database"""
    try:
        # Fetch from Cuelinks API
        offers_data = await cuelinks_service.get_offers(
            page=page,
            per_page=per_page,
            start_date=start_date,
            end_date=end_date,
            categories=categories,
            campaigns=campaigns
        )
        
        # Store offers in database
        if "offers" in offers_data:
            for offer_data in offers_data["offers"]:
                existing_offer = db.query(Offer).filter(
                    Offer.offer_id == offer_data["id"]
                ).first()
                
                if not existing_offer:
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
                    
                    # Find the campaign in our database using the campaign_id from API
                    campaign_id = offer_data.get("camapign_id")  # Note: API has typo "camapign_id"
                    
                    # Get or create the campaign
                    campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
                    
                    if not campaign:
                        # Try to fetch the campaign details from Cuelinks API
                        campaign_data = await cuelinks_service.get_campaign_by_id(campaign_id)
                        
                        if campaign_data:
                            campaign = Campaign(
                                campaign_id=campaign_id,
                                name=campaign_data.get("name", f"Campaign {campaign_id}"),
                                description=campaign_data.get("description", ""),
                                status=campaign_data.get("status", "active"),
                                category=json.dumps(campaign_data.get("categories", {}))
                            )
                            db.add(campaign)
                            db.flush()  # Get the ID without committing
                        else:
                            # Create a placeholder campaign if not found
                            campaign = Campaign(
                                campaign_id=campaign_id,
                                name=f"Campaign {campaign_id}",
                                status="active"
                            )
                            db.add(campaign)
                            db.flush()  # Get the ID without committing
                    
                    offer = Offer(
                        offer_id=offer_data["id"],
                        campaign_id=campaign.id,  # Use the campaign ID from our database
                        campaign_name=offer_data.get("campaign", ""),  # Store campaign name directly
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
        
        return offers_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database")
async def get_offers_from_db(
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    search_term: Optional[str] = None,
    category: Optional[str] = None,
    campaign: Optional[str] = None,
    coupon_only: Optional[bool] = False,
    status: str = Query("all"),  # Changed default to "all" to bypass status filtering
    db: Session = Depends(get_db)
):
    """Get offers from local database"""
    try:
        print(f"🔍 DEBUG: Starting query - page={page}, per_page={per_page}, status={status}, category={category}, campaign={campaign}, coupon_only={coupon_only}")
        
        # Start with basic query - using only Offer table initially for debugging
        query = db.query(Offer)
        
        # Apply filters
        if status and status.lower() != "all":
            query = query.filter(Offer.status == status)
        
        if search_term:
            search_term = f"%{search_term}%"
            query = query.filter(
                (Offer.title.ilike(search_term)) |
                (Offer.description.ilike(search_term)) |
                (Offer.campaign_name.ilike(search_term))  # Search in campaign name directly
            )
        
        if category and category.lower() != "all":
            query = query.filter(Offer.categories.ilike(f"%{category}%"))
            
        if campaign and campaign.lower() != "all":
            query = query.filter(Offer.campaign_name.ilike(f"%{campaign}%"))
            
        if coupon_only:
            query = query.filter(Offer.coupon_code != None).filter(Offer.coupon_code != "")
        
        # Count total
        total_count = query.count()
        print(f"🔍 DEBUG: Total matching offers before pagination: {total_count}")
        
        # Paginate
        query = query.order_by(Offer.created_at.desc())
        offers = query.offset((page - 1) * per_page).limit(per_page).all()
        print(f"🔍 DEBUG: Retrieved {len(offers)} offers after pagination")
        
        # Convert to JSON response
        result = []
        for offer in offers:
            # For debugging, let's print a sample offer
            if len(result) == 0:
                print(f"🔍 DEBUG: Sample offer ID: {offer.id}, Status: {offer.status}")
                
            result.append({
                "id": offer.id,
                "offer_id": offer.offer_id,
                "title": offer.title,
                "description": offer.description,
                "terms_and_conditions": offer.terms_and_conditions,
                "coupon_code": offer.coupon_code,
                "image_url": offer.image_url,
                "offer_type": offer.offer_type,
                "shipping_charge": offer.shipping_charge,
                "status": offer.status,
                "url": offer.url,
                "affiliate_url": offer.affiliate_url,
                "start_date": offer.start_date.isoformat() if offer.start_date else None,
                "end_date": offer.end_date.isoformat() if offer.end_date else None,
                "categories": offer.categories,
                "created_at": offer.created_at.isoformat(),
                "updated_at": offer.updated_at.isoformat(),
                "campaign": {
                    "id": offer.campaign_id,
                    "name": offer.campaign_name,
                    "status": "active"  # Default value since we're not joining with Campaign
                }
            })
        
        return {
            "offers": result,
            "page": page,
            "per_page": per_page,
            "total": total_count,
            "total_pages": (total_count + per_page - 1) // per_page
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        offset = (page - 1) * per_page
        offers = query.offset(offset).limit(per_page).all()
        print(f"🔍 DEBUG: Retrieved {len(offers)} offers for page {page}")
        
        # Format offers for response
        offers_list = []
        for offer in offers:
            # Handle image URL with better validation
            image_url = offer.image_url
            if image_url:
                image_url = image_url.strip()
                # Fix common URL issues
                if image_url and not image_url.startswith(('http://', 'https://')):
                    # If it starts with //, add https:
                    if image_url.startswith('//'):
                        image_url = f"https:{image_url}"
                    # If it's a relative path starting with /, treat as placeholder
                    elif image_url.startswith('/'):
                        image_url = "/static/images/placeholder.jpg"
                    # Otherwise, assume it needs https://
                    else:
                        image_url = f"https://{image_url}"
                # Validate that the URL looks reasonable
                elif image_url and ('cuelinks.com' in image_url or 'cdn' in image_url or image_url.startswith(('http://', 'https://'))):
                    # Keep the original URL if it looks like a valid CDN URL
                    pass
                else:
                    image_url = "/static/images/placeholder.jpg"
            else:
                # Use local placeholder for empty URLs
                image_url = "/static/images/placeholder.jpg"
                
            offers_list.append({
                "id": offer.id,
                "offer_id": offer.offer_id,
                "campaign_id": offer.campaign_id,
                "title": offer.title or "No Title",
                "description": offer.description or "No Description",
                "terms_and_conditions": offer.terms_and_conditions or "",
                "coupon_code": offer.coupon_code or "",
                "image_url": image_url,
                "offer_type": offer.offer_type or "",
                "shipping_charge": offer.shipping_charge or "",
                "status": offer.status or "active",
                "url": offer.url or "",
                "affiliate_url": offer.affiliate_url or "",
                "categories": offer.categories or "{}",
                "start_date": offer.start_date.isoformat() if offer.start_date else None,
                "end_date": offer.end_date.isoformat() if offer.end_date else None
            })
        
        response = {
            "total_count": total_count,
            "offers": offers_list,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_count + per_page - 1) // per_page
        }
        
        print(f"🔍 DEBUG: Returning {len(offers_list)} offers")
        return response
        
    except Exception as e:
        print(f"❌ DEBUG: Error in database endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories_old")
async def get_categories_old():
    """Get available categories (old version, kept for backward compatibility)"""
    categories = {
        "1": "Fashion",
        "2": "Baby & Kids",
        "3": "Books",
        "4": "Electronics",
        "5": "Finance",
        "6": "Flowers & Gifts",
        "7": "Food & Grocery",
        "8": "Health & Beauty",
        "9": "Home & Kitchen",
        "10": "Recharge",
        "11": "Travel",
        "12": "Others",
        "13": "Gaming",
        "14": "Services",
        "18": "Entertainment"
    }
    return {"categories": categories}

@router.get("/featured")
async def get_featured_offers(db: Session = Depends(get_db)):
    """Get featured offers for homepage"""
    try:
        offers = db.query(Offer).filter(
            Offer.status == "live"
        ).order_by(Offer.created_at.desc()).limit(6).all()
        
        # If no offers in database, fetch from API
        if len(offers) == 0:
            try:
                api_data = await cuelinks_service.get_offers(per_page=6)
                if "offers" in api_data:
                    featured_offers = []
                    for offer_data in api_data["offers"]:
                        featured_offers.append({
                            "id": offer_data["id"],
                            "title": offer_data.get("title", ""),
                            "description": offer_data.get("description", ""),
                            "image_url": offer_data.get("image_url", ""),
                            "affiliate_url": offer_data.get("affiliate_url", ""),
                            "coupon_code": offer_data.get("coupon_code", ""),
                            "type": offer_data.get("type", ""),
                            "categories": json.dumps(offer_data.get("categories", {}))
                        })
                    return {"offers": featured_offers}
            except Exception as api_error:
                print(f"API fallback failed: {api_error}")
                return {"offers": []}
        
        featured_offers = []
        for offer in offers:
            # Apply same image URL handling as in database endpoint
            image_url = offer.image_url
            if image_url:
                image_url = image_url.strip()
                # If starts with //, add https:
                if image_url.startswith('//'):
                    image_url = f"https:{image_url}"
                # If starts with http(s), use as is
                elif image_url.startswith(('http://', 'https://')):
                    pass
                # If it's a relative path, use placeholder
                elif image_url.startswith('/'):
                    image_url = "/static/images/placeholder.jpg"
                # Otherwise, assume it's a domain and add https
                else:
                    image_url = f"https://{image_url}"
            else:
                image_url = "/static/images/placeholder.jpg"
                
            featured_offers.append({
                "id": offer.offer_id,
                "title": offer.title,
                "description": offer.description,
                "image_url": image_url,
                "affiliate_url": offer.affiliate_url,
                "coupon_code": offer.coupon_code,
                "type": offer.offer_type,
                "categories": offer.categories
            })
        
        return {"offers": featured_offers}
    
    except Exception as e:
        # Fallback to API if database fails
        try:
            api_data = await cuelinks_service.get_offers(per_page=6)
            if "offers" in api_data:
                featured_offers = []
                for offer_data in api_data["offers"]:
                    featured_offers.append({
                        "id": offer_data["id"],
                        "title": offer_data.get("title", ""),
                        "description": offer_data.get("description", ""),
                        "image_url": offer_data.get("image_url", ""),
                        "affiliate_url": offer_data.get("affiliate_url", ""),
                        "coupon_code": offer_data.get("coupon_code", ""),
                        "type": offer_data.get("type", ""),
                        "categories": json.dumps(offer_data.get("categories", {}))
                    })
                return {"offers": featured_offers}
        except:
            pass
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns")
async def get_campaigns(db: Session = Depends(get_db)):
    """Get all unique campaign names for filtering"""
    try:
        # Query unique campaign names from Offer table
        campaigns = db.query(Offer.campaign_name).distinct().order_by(Offer.campaign_name).all()
        result = [campaign[0] for campaign in campaigns if campaign[0]]
        print(f"🔍 DEBUG: Found {len(result)} unique campaign names")
        
        # If no campaigns found, add some defaults to avoid empty dropdown
        if not result:
            print("⚠️ WARNING: No campaigns found in database, adding defaults")
            result = ["Amazon", "Flipkart", "Myntra", "Ajio", "Nykaa"]
            
        return {"campaigns": result}
    except Exception as e:
        print(f"❌ ERROR in get_campaigns: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """Get all unique categories for filtering"""
    try:
        print("🔍 DEBUG: Fetching categories")
        
        # Return fixed categories as an array including all categories from the old version
        result = [
            "Fashion", 
            "Baby & Kids",
            "Books",
            "Electronics", 
            "Finance",
            "Flowers & Gifts",
            "Food & Grocery", 
            "Health & Beauty", 
            "Home & Kitchen",
            "Recharge",
            "Travel", 
            "Gaming",
            "Services",
            "Entertainment",
            "Sports & Fitness", 
            "Toys & Games",
            "Others"
        ]
        print(f"🔍 DEBUG: Returning {len(result)} fixed categories")
        
        return {"categories": result}
    except Exception as e:
        print(f"❌ ERROR in get_categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns-by-category")
async def get_campaigns_by_category(category: str = Query(None), db: Session = Depends(get_db)):
    """Get campaigns filtered by category"""
    try:
        print(f"🔍 DEBUG: Fetching campaigns for category: {category}")
        
        # Base query for campaigns
        query = db.query(Offer.campaign_name).distinct()
        
        # Apply category filter if provided
        if category and category.lower() != "all":
            print(f"🔍 DEBUG: Filtering campaigns by category: {category}")
            query = query.filter(Offer.categories.ilike(f"%{category}%"))
        
        # Get results and sort
        campaigns = query.order_by(Offer.campaign_name).all()
        result = [campaign[0] for campaign in campaigns if campaign[0]]
        print(f"🔍 DEBUG: Found {len(result)} campaigns for category: {category}")
        
        # If no campaigns found, add some defaults
        if not result:
            print(f"⚠️ WARNING: No campaigns found for category {category}, adding defaults")
            result = ["Amazon", "Flipkart", "Myntra", "Ajio", "Nykaa"]
        
        return {"campaigns": result}
    except Exception as e:
        print(f"❌ ERROR in get_campaigns_by_category: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/initialize-data")
async def initialize_data(db: Session = Depends(get_db)):
    """Initialize database with offers data from Cuelinks API"""
    try:
        # Check current data count
        offer_count = db.query(Offer).count()
        
        if offer_count > 0:
            return {
                "status": "info",
                "message": f"Database already contains {offer_count} offers. Use force=true to reinitialize.",
                "current_count": offer_count
            }
        
        # Fetch from Cuelinks API
        logger.info("🔄 Fetching offers from Cuelinks API...")
        offers_data = await cuelinks_service.get_offers(page=1, per_page=100)
        
        if not offers_data or 'offers' not in offers_data:
            raise HTTPException(status_code=500, detail="Failed to fetch data from Cuelinks API")
        
        # Store offers in database
        new_offers = []
        for offer_data in offers_data['offers']:
            try:
                # Create offer object
                offer = Offer(
                    offer_id=offer_data.get('id'),
                    title=offer_data.get('title', ''),
                    description=offer_data.get('description', ''),
                    terms=offer_data.get('terms', ''),
                    start_date=datetime.fromisoformat(offer_data['start_date']) if offer_data.get('start_date') else None,
                    end_date=datetime.fromisoformat(offer_data['end_date']) if offer_data.get('end_date') else None,
                    categories=json.dumps(offer_data.get('categories', [])),
                    campaign_id=offer_data.get('campaign', {}).get('id'),
                    campaign_name=offer_data.get('campaign', {}).get('name', ''),
                    link=offer_data.get('link', ''),
                    image_url=offer_data.get('image_url', ''),
                    status=offer_data.get('status', 'active'),
                    discount_percentage=offer_data.get('discount_percentage'),
                    coupon_code=offer_data.get('coupon_code', ''),
                    tracking_url=offer_data.get('tracking_url', ''),
                    commission_percentage=offer_data.get('commission_percentage'),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                # Check if offer already exists
                existing = db.query(Offer).filter(Offer.offer_id == offer.offer_id).first()
                if not existing:
                    new_offers.append(offer)
                    
            except Exception as e:
                logger.warning(f"⚠️ Error processing offer {offer_data.get('id', 'unknown')}: {str(e)}")
                continue
        
        # Bulk insert new offers
        if new_offers:
            db.add_all(new_offers)
            db.commit()
            logger.info(f"✅ Added {len(new_offers)} new offers to database")
        
        final_count = db.query(Offer).count()
        
        return {
            "status": "success",
            "message": f"Database initialized successfully",
            "offers_added": len(new_offers),
            "total_offers": final_count
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error initializing data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize data: {str(e)}")
