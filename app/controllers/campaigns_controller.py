from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.cuelinks_service import cuelinks_service
from app.models.database import Campaign
from typing import Optional
import json

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

@router.get("/")
async def get_campaigns(
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    search_term: Optional[str] = None,
    categories: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get campaigns from Cuelinks API and store in database"""
    try:
        # Fetch from Cuelinks API
        campaigns_data = await cuelinks_service.get_campaigns(
            page=page,
            per_page=per_page,
            search_term=search_term,
            categories=categories
        )
        
        # Store campaigns in database
        if "campaigns" in campaigns_data:
            for campaign_data in campaigns_data["campaigns"]:
                existing_campaign = db.query(Campaign).filter(
                    Campaign.campaign_id == campaign_data["id"]
                ).first()
                
                if not existing_campaign:
                    campaign = Campaign(
                        campaign_id=campaign_data["id"],
                        name=campaign_data["name"],
                        description=campaign_data.get("description", ""),
                        status=campaign_data.get("status", ""),
                        category=json.dumps(campaign_data.get("categories", {}))
                    )
                    db.add(campaign)
            
            db.commit()
        
        return campaigns_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/all")
async def get_all_campaigns(
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    search_term: Optional[str] = None,
    categories: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all campaigns including paused ones"""
    try:
        campaigns_data = await cuelinks_service.get_all_campaigns(
            page=page,
            per_page=per_page,
            search_term=search_term,
            categories=categories
        )
        
        # Store campaigns in database
        if "campaigns" in campaigns_data:
            for campaign_data in campaigns_data["campaigns"]:
                existing_campaign = db.query(Campaign).filter(
                    Campaign.campaign_id == campaign_data["id"]
                ).first()
                
                if not existing_campaign:
                    campaign = Campaign(
                        campaign_id=campaign_data["id"],
                        name=campaign_data["name"],
                        description=campaign_data.get("description", ""),
                        status=campaign_data.get("status", ""),
                        category=json.dumps(campaign_data.get("categories", {}))
                    )
                    db.add(campaign)
            
            db.commit()
        
        return campaigns_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database")
async def get_campaigns_from_db(
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    search_term: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get campaigns from local database"""
    try:
        query = db.query(Campaign)
        
        if search_term:
            query = query.filter(Campaign.name.ilike(f"%{search_term}%"))
        
        total_count = query.count()
        campaigns = query.offset((page - 1) * per_page).limit(per_page).all()
        
        campaigns_list = []
        for campaign in campaigns:
            campaigns_list.append({
                "id": campaign.campaign_id,
                "name": campaign.name,
                "description": campaign.description,
                "status": campaign.status,
                "category": campaign.category,
                "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
                "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None
            })
        
        return {
            "total_count": total_count,
            "campaigns": campaigns_list,
            "page": page,
            "per_page": per_page
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
