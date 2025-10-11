"""
Top Deals Controller
Provides semantic search for highest discount offers
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import json
import re

from app.database import get_sync_db_session
from app.services.semantic_chat_service import semantic_chat_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/top-deals", tags=["Top Deals"])

def extract_discount_percentage(text: str) -> float:
    """
    Extract discount percentage from text (title, description, coupon code)
    Returns the highest percentage found, or 0 if none found
    """
    if not text:
        return 0.0
    
    # Look for patterns like: 50%, 50 %, 50% OFF, FLAT 50%, UPTO 50%
    patterns = [
        r'(\d+)\s*%\s*(?:off|discount)',  # "50% off" or "50% discount"
        r'(?:upto|up to|flat)\s+(\d+)\s*%',  # "upto 50%" or "flat 50%"
        r'(\d+)\s*%',  # Just "50%"
        r'save\s+(\d+)\s*%',  # "save 50%"
        r'(\d+)\s*percent',  # "50 percent"
    ]
    
    percentages = []
    text_lower = text.lower()
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            try:
                percentage = float(match)
                if 0 < percentage <= 100:  # Valid percentage range
                    percentages.append(percentage)
            except ValueError:
                continue
    
    return max(percentages) if percentages else 0.0

def calculate_offer_discount_score(offer_data: dict) -> float:
    """
    Calculate a discount score based on various fields
    Higher score = better discount
    """
    title = offer_data.get('title', '')
    description = offer_data.get('description', '')
    coupon_code = offer_data.get('coupon_code', '')
    
    # Extract percentages from all fields
    title_discount = extract_discount_percentage(title)
    desc_discount = extract_discount_percentage(description)
    coupon_discount = extract_discount_percentage(coupon_code)
    
    # Return the highest discount found
    max_discount = max(title_discount, desc_discount, coupon_discount)
    
    # Boost score if offer has a coupon code
    if coupon_code and max_discount > 0:
        max_discount += 5  # Add 5 points for having a coupon
    
    return max_discount

@router.get("/highest-discounts")
async def get_highest_discount_offers(
    limit: int = 10,
    category: str = None,
    db: Session = Depends(get_sync_db_session)
):
    """
    Get offers with highest discount percentages using optimized semantic search
    Reduced from 4 queries to 2 for better performance
    """
    try:
        # Optimized: Use only 2 targeted queries instead of 4 to reduce DB load
        search_queries = [
            "highest discount percentage off best deals",
            "maximum savings flat discount upto"
        ]
        
        all_offers = []
        seen_offer_ids = set()
        
        # Search with optimized queries - increased top_k to get more results per query
        for query in search_queries:
            result = await semantic_chat_service.semantic_search(
                query=query,
                db=db,
                top_k=75  # Increased from 50 to get more results with fewer queries
            )
            
            if result.get('offers'):
                for offer in result['offers']:
                    offer_id = offer.get('offer_id')
                    if offer_id and offer_id not in seen_offer_ids:
                        seen_offer_ids.add(offer_id)
                        all_offers.append(offer)
        
        # Calculate discount scores for all offers
        offers_with_scores = []
        for offer in all_offers:
            discount_score = calculate_offer_discount_score(offer)
            if discount_score > 0:  # Only include offers with detected discounts
                offer['discount_percentage'] = discount_score
                offers_with_scores.append(offer)
        
        # Sort by discount score (highest first)
        offers_with_scores.sort(key=lambda x: x['discount_percentage'], reverse=True)
        
        # Filter by category if specified
        if category:
            offers_with_scores = [
                offer for offer in offers_with_scores
                if category.lower() in [cat.lower() for cat in offer.get('categories', [])]
            ]
        
        # Return top N offers
        top_offers = offers_with_scores[:limit]
        
        return {
            "success": True,
            "total": len(top_offers),
            "offers": top_offers,
            "message": f"Found {len(top_offers)} highest discount offers"
        }
        
    except Exception as e:
        logger.error(f"Error fetching highest discount offers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trending-deals")
async def get_trending_deals(
    limit: int = 12,
    db: Session = Depends(get_sync_db_session)
):
    """
    Get trending deals - combination of high discounts and popular categories
    Optimized to use fewer queries for better performance
    """
    try:
        # Optimized: Reduced from 4 queries to 2
        trending_queries = [
            "trending hot deals discount today",
            "limited time flash sale special offer"
        ]
        
        all_offers = []
        seen_offer_ids = set()
        
        for query in trending_queries:
            result = await semantic_chat_service.semantic_search(
                query=query,
                db=db,
                top_k=50  # Increased from 30 to compensate for fewer queries
            )
            
            if result.get('offers'):
                for offer in result['offers']:
                    offer_id = offer.get('offer_id')
                    if offer_id and offer_id not in seen_offer_ids:
                        seen_offer_ids.add(offer_id)
                        
                        # Calculate discount score
                        discount_score = calculate_offer_discount_score(offer)
                        offer['discount_percentage'] = discount_score
                        
                        # Calculate trending score (combination of similarity and discount)
                        similarity = offer.get('similarity_score', 0)
                        trending_score = (similarity * 50) + (discount_score * 50)
                        offer['trending_score'] = trending_score
                        
                        all_offers.append(offer)
        
        # Sort by trending score
        all_offers.sort(key=lambda x: x.get('trending_score', 0), reverse=True)
        
        # Return top N
        top_deals = all_offers[:limit]
        
        return {
            "success": True,
            "total": len(top_deals),
            "offers": top_deals,
            "message": f"Found {len(top_deals)} trending deals"
        }
        
    except Exception as e:
        logger.error(f"Error fetching trending deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/category-best-deals/{category}")
async def get_category_best_deals(
    category: str,
    limit: int = 10,
    db: Session = Depends(get_sync_db_session)
):
    """
    Get best deals for a specific category
    """
    try:
        # Search for best deals in category
        query = f"best discount deals in {category} category highest percentage off"
        
        result = await semantic_chat_service.semantic_search(
            query=query,
            db=db,
            top_k=50
        )
        
        offers_with_scores = []
        
        if result.get('offers'):
            for offer in result['offers']:
                # Calculate discount score
                discount_score = calculate_offer_discount_score(offer)
                offer['discount_percentage'] = discount_score
                
                # Filter by category
                offer_categories = [cat.lower() for cat in offer.get('categories', [])]
                if category.lower() in offer_categories or discount_score > 0:
                    offers_with_scores.append(offer)
        
        # Sort by discount percentage
        offers_with_scores.sort(key=lambda x: x.get('discount_percentage', 0), reverse=True)
        
        # Return top N
        top_deals = offers_with_scores[:limit]
        
        return {
            "success": True,
            "category": category,
            "total": len(top_deals),
            "offers": top_deals,
            "message": f"Found {len(top_deals)} best deals in {category}"
        }
        
    except Exception as e:
        logger.error(f"Error fetching category best deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))
