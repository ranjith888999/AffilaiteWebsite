from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.cuelinks_service import cuelinks_service
from app.models.database import Link
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/links", tags=["links"])

class LinkRequest(BaseModel):
    url: str
    shorten: bool = False
    subid: Optional[str] = None

class LinkResponse(BaseModel):
    original_url: str
    affiliate_url: str
    shortened_url: Optional[str] = None

@router.post("/", response_model=LinkResponse)
async def create_affiliate_link(
    link_request: LinkRequest,
    db: Session = Depends(get_db)
):
    """Create affiliate link for a given URL"""
    try:
        # Get affiliate link from Cuelinks API
        link_data = await cuelinks_service.get_link(
            url=link_request.url,
            shorten=link_request.shorten,
            subid=link_request.subid
        )
        
        if "url" in link_data and "affiliate_url" in link_data:
            # Store in database
            link = Link(
                original_url=link_request.url,
                affiliate_url=link_data["affiliate_url"],
                shortened_url=link_data.get("shortened_url"),
                sub_id=link_request.subid
            )
            db.add(link)
            db.commit()
            
            return LinkResponse(
                original_url=link_request.url,
                affiliate_url=link_data["affiliate_url"],
                shortened_url=link_data.get("shortened_url")
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to generate affiliate link")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_link_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get link generation history"""
    try:
        total_count = db.query(Link).count()
        links = db.query(Link).offset((page - 1) * per_page).limit(per_page).all()
        
        links_list = []
        for link in links:
            links_list.append({
                "id": link.id,
                "original_url": link.original_url,
                "affiliate_url": link.affiliate_url,
                "shortened_url": link.shortened_url,
                "sub_id": link.sub_id,
                "created_at": link.created_at.isoformat()
            })
        
        return {
            "total_count": total_count,
            "links": links_list,
            "page": page,
            "per_page": per_page
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
