from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json

from app.database import get_sync_db_session
from app.models.database import Campaign, Offer, OfferEmbedding
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/offers", tags=["Admin Offers Management"])

# Pydantic models for request validation
class OfferCreateRequest(BaseModel):
    campaign_id: int
    campaign: str
    title: str
    description: str
    terms_and_condition: Optional[str] = ""
    coupon_code: Optional[str] = ""
    image_url: Optional[str] = ""
    type: str = "discount"
    shipping_charge: Optional[str] = ""
    status: str = "live"
    url: str
    affiliate_url: str
    start_date: Optional[str] = ""
    end_date: Optional[str] = ""
    categories: Dict[str, str] = {}

class OfferUpdateRequest(BaseModel):
    campaign_id: Optional[int] = None
    campaign: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    terms_and_condition: Optional[str] = None
    coupon_code: Optional[str] = None
    image_url: Optional[str] = None
    type: Optional[str] = None
    shipping_charge: Optional[str] = None
    status: Optional[str] = None
    url: Optional[str] = None
    affiliate_url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    categories: Optional[Dict[str, str]] = None

@router.get("/list")
async def list_all_offers(
    page: int = 1,
    per_page: int = 50,
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_sync_db_session)
) -> Dict[str, Any]:
    """
    Get paginated list of all offers with filtering options
    
    Args:
        page: Page number (default: 1)
        per_page: Items per page (default: 50, max: 100)
        search: Search term for title or campaign name
        status: Filter by status (live, expired, etc.)
    
    Returns:
        Dict containing offers list and pagination info
    """
    try:
        # Build query
        query = db.query(Offer)
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Offer.title.ilike(search_term)) | 
                (Offer.campaign_name.ilike(search_term))
            )
        
        if status:
            query = query.filter(Offer.status == status)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        per_page = min(per_page, 100)  # Cap at 100
        offset = (page - 1) * per_page
        offers = query.order_by(Offer.id.desc()).offset(offset).limit(per_page).all()
        
        # Format response
        offers_list = []
        for offer in offers:
            offers_list.append({
                "id": offer.id,
                "offer_id": offer.offer_id,
                "campaign_id": offer.campaign_id,
                "campaign_name": offer.campaign_name,
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
                "categories": json.loads(offer.categories) if offer.categories else {},
                "created_at": offer.created_at.isoformat() if offer.created_at else None,
                "updated_at": offer.updated_at.isoformat() if offer.updated_at else None
            })
        
        return {
            "success": True,
            "data": offers_list,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": (total_count + per_page - 1) // per_page
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing offers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list offers: {str(e)}")

@router.get("/{offer_id}")
async def get_offer(
    offer_id: int,
    db: Session = Depends(get_sync_db_session)
) -> Dict[str, Any]:
    """
    Get a single offer by ID
    
    Args:
        offer_id: Database ID of the offer
    
    Returns:
        Dict containing offer details
    """
    try:
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        
        return {
            "success": True,
            "data": {
                "id": offer.id,
                "offer_id": offer.offer_id,
                "campaign_id": offer.campaign_id,
                "campaign_name": offer.campaign_name,
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
                "categories": json.loads(offer.categories) if offer.categories else {},
                "created_at": offer.created_at.isoformat() if offer.created_at else None,
                "updated_at": offer.updated_at.isoformat() if offer.updated_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting offer: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get offer: {str(e)}")

@router.post("/create")
async def create_offer(
    offer_data: OfferCreateRequest,
    db: Session = Depends(get_sync_db_session)
) -> Dict[str, Any]:
    """
    Create a new custom offer
    
    Args:
        offer_data: Offer details
    
    Returns:
        Dict containing created offer details
    """
    try:
        from app.services.cuelinks_offers_service import cuelinks_offers_service
        import os
        
        # Get the next available offer_id
        max_offer = db.query(Offer).order_by(Offer.offer_id.desc()).first()
        next_offer_id = (max_offer.offer_id + 1) if max_offer else 1000
        
        # Check if campaign exists, create if not
        campaign = db.query(Campaign).filter(Campaign.campaign_id == offer_data.campaign_id).first()
        
        if not campaign:
            # Create new campaign
            campaign = Campaign(
                campaign_id=offer_data.campaign_id,
                name=offer_data.campaign,
                description=f"Campaign for {offer_data.campaign}",
                status="active",
                category=json.dumps(offer_data.categories)
            )
            db.add(campaign)
            db.flush()  # Get campaign.id
        
        # Parse dates
        start_date = None
        end_date = None
        
        if offer_data.start_date:
            try:
                start_date = datetime.strptime(offer_data.start_date, "%Y-%m-%d")
            except:
                pass
        
        if offer_data.end_date:
            try:
                end_date = datetime.strptime(offer_data.end_date, "%Y-%m-%d")
            except:
                pass
        
        # Create offer
        new_offer = Offer(
            offer_id=next_offer_id,
            campaign_id=campaign.id,
            campaign_name=offer_data.campaign,
            title=offer_data.title,
            description=offer_data.description,
            terms_and_conditions=offer_data.terms_and_condition,
            coupon_code=offer_data.coupon_code,
            image_url=offer_data.image_url,
            offer_type=offer_data.type,
            shipping_charge=offer_data.shipping_charge,
            status=offer_data.status,
            url=offer_data.url,
            affiliate_url=offer_data.affiliate_url,
            start_date=start_date,
            end_date=end_date,
            categories=json.dumps(offer_data.categories)
        )
        
        db.add(new_offer)
        db.commit()
        db.refresh(new_offer)
        
        # Generate embeddings for the new offer
        try:
            await cuelinks_offers_service.create_offer_embeddings(db, new_offer)
        except Exception as e:
            logger.warning(f"Failed to create embeddings: {e}")
        
        # Add to offers_extended.json
        try:
            extended_file_path = os.path.join("data", "offers_extended.json")
            
            # Read existing data
            if os.path.exists(extended_file_path):
                with open(extended_file_path, 'r', encoding='utf-8') as f:
                    extended_offers = json.load(f)
            else:
                extended_offers = []
            
            # Add new offer to extended list
            extended_offers.append({
                "id": next_offer_id,
                "campaign_id": offer_data.campaign_id,
                "campaign": offer_data.campaign,
                "title": offer_data.title,
                "description": offer_data.description,
                "terms_and_condition": offer_data.terms_and_condition,
                "coupon_code": offer_data.coupon_code,
                "image_url": offer_data.image_url,
                "type": offer_data.type,
                "shipping_charge": offer_data.shipping_charge,
                "status": offer_data.status,
                "url": offer_data.url,
                "affiliate_url": offer_data.affiliate_url,
                "start_date": offer_data.start_date,
                "end_date": offer_data.end_date,
                "categories": offer_data.categories
            })
            
            # Write back to file
            with open(extended_file_path, 'w', encoding='utf-8') as f:
                json.dump(extended_offers, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.warning(f"Failed to update offers_extended.json: {e}")
        
        return {
            "success": True,
            "message": "Offer created successfully",
            "data": {
                "id": new_offer.id,
                "offer_id": new_offer.offer_id
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating offer: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create offer: {str(e)}")

@router.put("/{offer_id}")
async def update_offer(
    offer_id: int,
    offer_data: OfferUpdateRequest,
    db: Session = Depends(get_sync_db_session)
) -> Dict[str, Any]:
    """
    Update an existing offer
    
    Args:
        offer_id: Database ID of the offer
        offer_data: Updated offer details
    
    Returns:
        Dict containing success message
    """
    try:
        from app.services.cuelinks_offers_service import cuelinks_offers_service
        import os
        
        # Get existing offer
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        
        # Update fields
        if offer_data.campaign_id is not None:
            offer.campaign_id = offer_data.campaign_id
        if offer_data.campaign is not None:
            offer.campaign_name = offer_data.campaign
        if offer_data.title is not None:
            offer.title = offer_data.title
        if offer_data.description is not None:
            offer.description = offer_data.description
        if offer_data.terms_and_condition is not None:
            offer.terms_and_conditions = offer_data.terms_and_condition
        if offer_data.coupon_code is not None:
            offer.coupon_code = offer_data.coupon_code
        if offer_data.image_url is not None:
            offer.image_url = offer_data.image_url
        if offer_data.type is not None:
            offer.offer_type = offer_data.type
        if offer_data.shipping_charge is not None:
            offer.shipping_charge = offer_data.shipping_charge
        if offer_data.status is not None:
            offer.status = offer_data.status
        if offer_data.url is not None:
            offer.url = offer_data.url
        if offer_data.affiliate_url is not None:
            offer.affiliate_url = offer_data.affiliate_url
        if offer_data.categories is not None:
            offer.categories = json.dumps(offer_data.categories)
        
        # Update dates
        if offer_data.start_date is not None:
            try:
                offer.start_date = datetime.strptime(offer_data.start_date, "%Y-%m-%d")
            except:
                pass
        
        if offer_data.end_date is not None:
            try:
                offer.end_date = datetime.strptime(offer_data.end_date, "%Y-%m-%d")
            except:
                pass
        
        offer.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Delete old embeddings and regenerate
        try:
            db.query(OfferEmbedding).filter(OfferEmbedding.offer_id == offer.id).delete()
            db.commit()
            await cuelinks_offers_service.create_offer_embeddings(db, offer)
        except Exception as e:
            logger.warning(f"Failed to regenerate embeddings: {e}")
        
        # Update offers_extended.json
        try:
            extended_file_path = os.path.join("data", "offers_extended.json")
            
            if os.path.exists(extended_file_path):
                with open(extended_file_path, 'r', encoding='utf-8') as f:
                    extended_offers = json.load(f)
                
                # Find and update the offer
                for i, ext_offer in enumerate(extended_offers):
                    if ext_offer.get("id") == offer.offer_id:
                        # Update the offer in the JSON
                        extended_offers[i] = {
                            "id": offer.offer_id,
                            "campaign_id": offer_data.campaign_id if offer_data.campaign_id else ext_offer.get("campaign_id"),
                            "campaign": offer_data.campaign if offer_data.campaign else ext_offer.get("campaign"),
                            "title": offer_data.title if offer_data.title else ext_offer.get("title"),
                            "description": offer_data.description if offer_data.description else ext_offer.get("description"),
                            "terms_and_condition": offer_data.terms_and_condition if offer_data.terms_and_condition is not None else ext_offer.get("terms_and_condition", ""),
                            "coupon_code": offer_data.coupon_code if offer_data.coupon_code is not None else ext_offer.get("coupon_code", ""),
                            "image_url": offer_data.image_url if offer_data.image_url is not None else ext_offer.get("image_url", ""),
                            "type": offer_data.type if offer_data.type else ext_offer.get("type"),
                            "shipping_charge": offer_data.shipping_charge if offer_data.shipping_charge is not None else ext_offer.get("shipping_charge", ""),
                            "status": offer_data.status if offer_data.status else ext_offer.get("status"),
                            "url": offer_data.url if offer_data.url else ext_offer.get("url"),
                            "affiliate_url": offer_data.affiliate_url if offer_data.affiliate_url else ext_offer.get("affiliate_url"),
                            "start_date": offer_data.start_date if offer_data.start_date is not None else ext_offer.get("start_date", ""),
                            "end_date": offer_data.end_date if offer_data.end_date is not None else ext_offer.get("end_date", ""),
                            "categories": offer_data.categories if offer_data.categories else ext_offer.get("categories", {})
                        }
                        break
                
                # Write back to file
                with open(extended_file_path, 'w', encoding='utf-8') as f:
                    json.dump(extended_offers, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            logger.warning(f"Failed to update offers_extended.json: {e}")
        
        return {
            "success": True,
            "message": "Offer updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating offer: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update offer: {str(e)}")

@router.delete("/{offer_id}")
async def delete_offer(
    offer_id: int,
    db: Session = Depends(get_sync_db_session)
) -> Dict[str, Any]:
    """
    Delete an offer
    
    Args:
        offer_id: Database ID of the offer
    
    Returns:
        Dict containing success message
    """
    try:
        import os
        
        # Get offer
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        
        offer_external_id = offer.offer_id
        
        # Delete embeddings first
        db.query(OfferEmbedding).filter(OfferEmbedding.offer_id == offer.id).delete()
        
        # Delete offer
        db.delete(offer)
        db.commit()
        
        # Remove from offers_extended.json
        try:
            extended_file_path = os.path.join("data", "offers_extended.json")
            
            if os.path.exists(extended_file_path):
                with open(extended_file_path, 'r', encoding='utf-8') as f:
                    extended_offers = json.load(f)
                
                # Filter out the deleted offer
                extended_offers = [o for o in extended_offers if o.get("id") != offer_external_id]
                
                # Write back to file
                with open(extended_file_path, 'w', encoding='utf-8') as f:
                    json.dump(extended_offers, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            logger.warning(f"Failed to update offers_extended.json: {e}")
        
        return {
            "success": True,
            "message": "Offer deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting offer: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete offer: {str(e)}")

@router.get("/stats/summary")
async def get_offers_stats(
    db: Session = Depends(get_sync_db_session)
) -> Dict[str, Any]:
    """
    Get summary statistics about offers
    
    Returns:
        Dict containing offer statistics
    """
    try:
        total_offers = db.query(Offer).count()
        live_offers = db.query(Offer).filter(Offer.status == "live").count()
        total_campaigns = db.query(Campaign).count()
        total_embeddings = db.query(OfferEmbedding).count()
        
        return {
            "success": True,
            "data": {
                "total_offers": total_offers,
                "live_offers": live_offers,
                "total_campaigns": total_campaigns,
                "total_embeddings": total_embeddings
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
