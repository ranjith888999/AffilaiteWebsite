"""
Fast Chat Service - Optimized for speed and reduced latency
"""

import logging
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, text, or_
from app.database import get_db_sync
from app.models.database import Offer

logger = logging.getLogger(__name__)

class FastChatService:
    """
    Speed-optimized chat service that prioritizes response time over complex AI features
    """
    
    def __init__(self):
        self.categories = {
            'fashion': ['fashion', 'clothes', 'clothing', 'dress', 'shirt', 'shoes', 'bag', 'myntra', 'ajio', 'style'],
            'electronics': ['electronics', 'phone', 'mobile', 'laptop', 'computer', 'tech', 'iphone', 'samsung'],
            'travel': ['travel', 'flight', 'hotel', 'trip', 'vacation', 'booking', 'holiday'],
            'food': ['food', 'restaurant', 'dining', 'delivery', 'zomato', 'swiggy', 'meal'],
            'beauty': ['beauty', 'cosmetics', 'skincare', 'makeup', 'nykaa', 'hair', 'fragrance'],
            'home': ['home', 'furniture', 'decor', 'kitchen', 'appliance'],
            'books': ['book', 'reading', 'education', 'study'],
            'sports': ['sports', 'fitness', 'gym', 'exercise', 'outdoor']
        }
    
    def _detect_category_fast(self, query: str) -> Optional[str]:
        """Fast category detection using simple keyword matching"""
        query_lower = query.lower()
        for category, keywords in self.categories.items():
            if any(keyword in query_lower for keyword in keywords):
                return category
        return None
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """Extract key terms for database search"""
        # Remove common words and get meaningful terms
        stop_words = {'for', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'with', 'from', 'by', 'of', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'what', 'where', 'when', 'how', 'why', 'who', 'which'}
        
        words = query.lower().replace(',', ' ').replace('.', ' ').split()
        meaningful_words = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return meaningful_words[:3]  # Return top 3 terms for speed
    
    def search_offers_fast(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fast offer search with minimal database queries"""
        start_time = time.time()
        
        try:
            db = next(get_db_sync())
            
            # Start with active offers only (most offers are 'active', not 'live')
            base_query = db.query(Offer).filter(
                or_(
                    Offer.status == 'active',
                    Offer.status == 'live'
                )
            )
            
            # Fast category detection
            category = self._detect_category_fast(query)
            if category:
                logger.info(f"Category detected: {category}")
                # Use simple LIKE query for speed
                if category == 'fashion':
                    base_query = base_query.filter(
                        or_(
                            Offer.categories.ilike('%Fashion%'),
                            Offer.categories.ilike('%Clothing%'),
                            Offer.title.ilike('%fashion%'),
                            Offer.title.ilike('%clothes%')
                        )
                    )
                elif category == 'electronics':
                    base_query = base_query.filter(
                        or_(
                            Offer.categories.ilike('%Electronics%'),
                            Offer.categories.ilike('%Mobile%'),
                            Offer.title.ilike('%electronics%'),
                            Offer.title.ilike('%phone%')
                        )
                    )
                elif category == 'travel':
                    base_query = base_query.filter(
                        or_(
                            Offer.categories.ilike('%Travel%'),
                            Offer.title.ilike('%travel%'),
                            Offer.title.ilike('%flight%'),
                            Offer.title.ilike('%hotel%')
                        )
                    )
            
            # Add search term filtering
            search_terms = self._extract_search_terms(query)
            if search_terms:
                # Use the first 2 terms for speed
                for term in search_terms[:2]:
                    base_query = base_query.filter(
                        or_(
                            Offer.title.ilike(f'%{term}%'),
                            Offer.description.ilike(f'%{term}%')
                        )
                    )
            
            # Get results with limit
            offers = base_query.order_by(Offer.created_at.desc()).limit(limit * 2).all()
            
            # If no results, try fallback search
            if not offers:
                logger.info("No offers found, trying fallback search...")
                offers = db.query(Offer).filter(
                    or_(
                        Offer.status == 'active',
                        Offer.status == 'live'
                    )
                ).order_by(Offer.created_at.desc()).limit(limit).all()
            
            # Convert to dict format quickly
            result = []
            for offer in offers[:limit]:
                # Simple URL handling
                affiliate_url = offer.affiliate_url if offer.affiliate_url and offer.affiliate_url != '#' else offer.url
                if not affiliate_url or affiliate_url == '#':
                    affiliate_url = '#'
                
                result.append({
                    'id': offer.id,
                    'title': offer.title or 'Special Offer',
                    'description': (offer.description or 'Great deal available!')[:150],  # Truncate for speed
                    'image_url': offer.image_url or '/static/images/placeholder.jpg',
                    'categories': offer.categories or '',
                    'coupon_code': offer.coupon_code or '',
                    'affiliate_url': affiliate_url,
                    'url': affiliate_url,
                    'website_url': affiliate_url,
                    'similarity': 0.85,  # Fixed similarity for speed
                    'offer_type': offer.offer_type or '',
                    'status': offer.status or 'active'
                })
            
            search_time = time.time() - start_time
            logger.info(f"⚡ Fast search completed in {search_time:.3f}s, found {len(result)} offers")
            
            return result
            
        except Exception as e:
            logger.error(f"Fast search error: {e}")
            return []
        finally:
            if 'db' in locals():
                db.close()
    
    def generate_response_fast(self, query: str, offers: List[Dict]) -> str:
        """Generate quick response without complex processing"""
        if not offers:
            return "I'm currently searching for the best deals for you! Our offers database is being updated. Please try again in a moment or browse our categories for amazing deals!"
        
        query_lower = query.lower()
        
        # Quick greeting check
        if any(word in query_lower for word in ['hello', 'hi', 'hey']):
            return f"Hello! I found {len(offers)} great deals for you. Check them out below and click 'Get Deal' to start saving! 🛍️"
        
        # Category-based responses
        category = self._detect_category_fast(query)
        if category:
            category_responses = {
                'fashion': f"👗 Perfect! I found {len(offers)} amazing fashion deals just for you!",
                'electronics': f"📱 Great choice! Here are {len(offers)} fantastic tech deals!",
                'travel': f"✈️ Wonderful! I discovered {len(offers)} excellent travel offers!",
                'food': f"🍽️ Yummy! Found {len(offers)} delicious food deals!",
                'beauty': f"💄 Beautiful! Here are {len(offers)} stunning beauty offers!",
            }
            response = category_responses.get(category, f"🎯 Perfect match! Found {len(offers)} great deals for you!")
        else:
            response = f"🔍 Found {len(offers)} excellent deals matching your search!"
        
        response += "\n\nClick 'Get Deal' on any offer to visit the store and save money! 💰"
        
        return response

# Global fast service instance
fast_chat_service = FastChatService()

# Export functions
def search_offers_fast(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Fast offer search"""
    return fast_chat_service.search_offers_fast(query, limit)

def generate_response_fast(query: str, offers: List[Dict]) -> str:
    """Fast response generation"""
    return fast_chat_service.generate_response_fast(query, offers)
