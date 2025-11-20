"""
Ultra Fast Chat Service - Maximum simplicity for reliability
"""

import logging
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from app.database import get_db_sync
from app.models.database import Offer

logger = logging.getLogger(__name__)

class UltraFastChatService:
    """Ultra simplified service for maximum reliability"""
    
    def search_offers_simple(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Ultra simple search - but with proper query filtering"""
        start_time = time.time()
        db = None
        try:
            db = next(get_db_sync())
            query_lower = query.lower()
            result = []
            
            # Extract keywords (potential brand/merchant names)
            keywords = [word for word in query_lower.replace(',', ' ').replace('.', ' ').split() 
                       if len(word) > 2 and word not in {'the', 'and', 'for', 'with', 'are', 'you', 'get', 'all', 'offer', 'offers', 'deal', 'deals'}]
            
            # Known popular brands for better logging and potential special handling
            popular_brands = {'myntra', 'ajio', 'amazon', 'flipkart', 'nykaa', 'zomato', 'swiggy', 'tata', 'reliance', 'snapdeal'}
            detected_brands = [brand for brand in popular_brands if brand in query_lower]
            
            if detected_brands:
                brand_str = ', '.join(detected_brands)
                logger.info(f"Searching for offers from popular brands: {brand_str}")
            
            # Build search conditions for the SQL query
            search_conditions = []
            params = {"limit": limit}  # Exact limit to reduce processing time
            
            # Add conditions for all keywords that might be brand names
            for i, keyword in enumerate(keywords):
                if len(keyword) > 3:  # Only use keywords with more than 3 chars
                    param_name = f"keyword_{i}"
                    # Search in campaign names (primary focus for brand searches)
                    search_conditions.append(f"c.name ILIKE :{param_name}")
                    # Also search in title and description for comprehensive results
                    search_conditions.append(f"o.title ILIKE :{param_name}")
                    search_conditions.append(f"o.description ILIKE :{param_name}")
                    params[param_name] = f"%{keyword}%"
            
            # Add category conditions if relevant
            if 'fashion' in query_lower or 'clothing' in query_lower or 'clothes' in query_lower:
                search_conditions.append("o.categories ILIKE '%fashion%' OR o.categories ILIKE '%clothing%'")
            
            if 'electronic' in query_lower or 'gadget' in query_lower or 'phone' in query_lower:
                search_conditions.append("o.categories ILIKE '%electronic%' OR o.categories ILIKE '%gadget%'")
            
                # Execute the search query if we have conditions
                if search_conditions:
                    condition_str = " OR ".join(search_conditions)
                    logger.info(f"Searching with conditions: {condition_str}")
                    
                    sql_query = text(f"""
                    SELECT o.*, c.name as campaign_name 
                    FROM offers o
                    JOIN campaigns c ON o.campaign_id = c.id
                    WHERE (o.status = 'active' OR o.status = 'live')
                    AND ({condition_str})
                    LIMIT :limit
                    """)
                    offers = db.execute(sql_query, params).all()
                else:
                    # Fallback to category search if no keywords found
                    offers = self._search_by_category(db, query_lower, limit)
                
                # If no results, get recent offers - but limit the number to save time
                if not offers:
                    logger.info("No results found, fetching recent offers")
                    sql_query = text("""
                    SELECT o.*, c.name as campaign_name 
                    FROM offers o
                    JOIN campaigns c ON o.campaign_id = c.id
                    WHERE (o.status = 'active' OR o.status = 'live')
                    ORDER BY o.created_at DESC
                    LIMIT :limit
                    """)
                    offers = db.execute(sql_query, {"limit": limit}).all()            # Convert to dict format
            for offer in offers[:limit]:
                # Handle both Row objects from SQL queries and ORM objects
                try:
                    # For direct SQL results (Row objects)
                    if hasattr(offer, '_mapping'):
                        offer_dict = dict(offer._mapping)
                    # For ORM objects
                    else:
                        offer_dict = {
                            'id': offer.id,
                            'title': offer.title,
                            'description': offer.description,
                            'image_url': offer.image_url,
                            'categories': offer.categories,
                            'coupon_code': offer.coupon_code,
                            'affiliate_url': offer.affiliate_url,
                            'url': offer.url,
                            'status': offer.status,
                            'offer_type': getattr(offer, 'offer_type', ''),
                            'campaign_name': getattr(offer, 'campaign_name', '')
                        }
                    
                    # Set defaults and format
                    affiliate_url = offer_dict.get('affiliate_url', '') or offer_dict.get('url', '')
                    if not affiliate_url or affiliate_url == '#':
                        affiliate_url = offer_dict.get('url', '#')
                    if not affiliate_url:
                        affiliate_url = '#'
                    
                    # Include campaign name in the result
                    campaign_name = offer_dict.get('campaign_name', '')
                    
                    result.append({
                        'id': offer_dict.get('id'),
                        'title': offer_dict.get('title') or 'Special Offer',
                        'description': (offer_dict.get('description') or 'Great deal available!')[:150],
                        'image_url': offer_dict.get('image_url') or '/static/images/placeholder.jpg',
                        'categories': offer_dict.get('categories') or '',
                        'coupon_code': offer_dict.get('coupon_code') or '',
                        'affiliate_url': affiliate_url,
                        'url': affiliate_url,
                        'website_url': affiliate_url,
                        'similarity': 0.85,
                        'offer_type': offer_dict.get('offer_type') or '',
                        'status': offer_dict.get('status') or 'active',
                        'campaign_name': campaign_name  # Add campaign name to results
                    })
                except Exception as e:
                    logger.error(f"Error converting offer to dict: {e}")
                    continue
            
            logger.info(f"Ultra fast search found {len(result)} offers for query: '{query}'")
            return result
            
        except Exception as e:
            logger.error(f"Ultra fast search error: {e}")
            return []
        finally:
            if db:
                db.close()
            
    def _search_by_category(self, db, query_lower, limit):
        """Helper method to search by category and other fallback methods"""
        
        # Build a unified query approach
        search_conditions = []
        params = {"limit": limit * 2}
        
        # Add category-specific conditions
        if 'fashion' in query_lower or 'clothing' in query_lower or 'clothes' in query_lower:
            logger.info("Adding fashion category conditions")
            search_conditions.append("""
                o.categories ILIKE '%fashion%' OR
                o.categories ILIKE '%clothing%' OR
                o.title ILIKE '%fashion%' OR
                o.title ILIKE '%cloth%'
            """)
        
        if 'electronic' in query_lower or 'gadget' in query_lower or 'phone' in query_lower or 'laptop' in query_lower:
            logger.info("Adding electronics category conditions")
            search_conditions.append("""
                o.categories ILIKE '%electronic%' OR
                o.categories ILIKE '%gadget%' OR
                o.title ILIKE '%phone%' OR
                o.title ILIKE '%laptop%' OR
                o.title ILIKE '%electronic%'
            """)
            
        if 'travel' in query_lower or 'flight' in query_lower or 'hotel' in query_lower:
            logger.info("Adding travel category conditions")
            search_conditions.append("""
                o.categories ILIKE '%travel%' OR
                o.categories ILIKE '%flight%' OR
                o.categories ILIKE '%hotel%'
            """)
            
        if 'food' in query_lower or 'restaurant' in query_lower or 'dining' in query_lower:
            logger.info("Adding food category conditions")
            search_conditions.append("""
                o.categories ILIKE '%food%' OR
                o.categories ILIKE '%restaurant%' OR
                o.categories ILIKE '%dining%'
            """)
        
        # Extract keywords for generic search
        keywords = [word for word in query_lower.replace(',', ' ').replace('.', ' ').split() 
                  if len(word) > 3 and word not in {'the', 'and', 'for', 'with', 'are', 'you', 'get', 'all', 'offer', 'offers', 'deal', 'deals'}]
        
        # Add keyword-based conditions
        for i, keyword in enumerate(keywords):
            param_name = f"cat_keyword_{i}"
            search_conditions.append(f"o.title ILIKE :{param_name} OR o.description ILIKE :{param_name} OR c.name ILIKE :{param_name}")
            params[param_name] = f"%{keyword}%"
        
        # Execute search with all conditions if any exist
        if search_conditions:
            condition_str = " OR ".join(search_conditions)
            logger.info(f"Category search with conditions: {condition_str}")
            
            sql_query = text(f"""
            SELECT o.*, c.name as campaign_name 
            FROM offers o
            JOIN campaigns c ON o.campaign_id = c.id
            WHERE (o.status = 'active' OR o.status = 'live')
            AND ({condition_str})
            LIMIT :limit
            """)
            return db.execute(sql_query, params).all()
        
        # If no conditions were found, return recent offers
        logger.info("No specific conditions, getting recent offers")
        sql_query = text("""
        SELECT o.*, c.name as campaign_name 
        FROM offers o
        JOIN campaigns c ON o.campaign_id = c.id
        WHERE (o.status = 'active' OR o.status = 'live')
        ORDER BY o.created_at DESC
        LIMIT :limit
        """)
        return db.execute(sql_query, {"limit": limit}).all()
    
    def generate_response_simple(self, query: str, offers: List[Dict]) -> str:
        """Generate more specific responses based on the query and offers"""
        if not offers:
            return "I'm searching for the best deals matching your request. Please try a different search term or browse our categories for amazing deals!"
        
        query_lower = query.lower()
        offer_count = len(offers)
        
        # Greeting responses
        if 'hello' in query_lower or 'hi' in query_lower or 'hey' in query_lower:
            return f"Hello! I found {offer_count} great deals for you. Check them out below and click 'Get Deal' to save money! 🛍️"
        
        # Brand-specific responses
        if 'myntra' in query_lower:
            return f"🛍️ Found {offer_count} Myntra fashion deals just for you! Browse these offers and click 'Get Deal' to shop with discounts."
        
        if 'ajio' in query_lower:
            return f"👕 Here are {offer_count} amazing Ajio fashion deals! Shop these offers now and save big on your favorite styles."
        
        if 'amazon' in query_lower:
            return f"� Discovered {offer_count} fantastic Amazon deals! Check out these offers to find great savings on a wide range of products."
        
        # Category-specific responses
        if 'fashion' in query_lower or 'clothing' in query_lower or 'clothes' in query_lower:
            return f"👗 Perfect! Here are {offer_count} stylish fashion deals curated just for you. Find your perfect look at a perfect price!"
        
        if 'electronic' in query_lower or 'gadget' in query_lower or 'phone' in query_lower:
            return f"🔌 Found {offer_count} awesome electronics deals! Upgrade your tech with these special offers and save money."
        
        if 'book' in query_lower or 'reading' in query_lower:
            return f"� Here are {offer_count} great book deals for your reading pleasure! Expand your library while saving with these offers."
        
        if 'travel' in query_lower or 'flight' in query_lower or 'hotel' in query_lower:
            return f"✈️ Discovered {offer_count} travel deals for your next adventure! Book now to secure these special rates."
        
        if 'food' in query_lower or 'restaurant' in query_lower or 'dining' in query_lower:
            return f"�️ Found {offer_count} delicious food and dining deals! Treat yourself to these tasty savings."
        
        # Default response for other queries
        return f"🎯 Found {offer_count} excellent deals matching '{query}'! Browse these offers and click 'Get Deal' to start saving! 💰"

# Global ultra fast service
ultra_fast_service = UltraFastChatService()

# Export functions for chat controller
def search_offers_ultra_fast(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Ultra fast search - optimized for performance under 10 seconds"""
    start_time = time.time()
    db = None
    try:
        db = next(get_db_sync())
        query_lower = query.lower()
        result = []
        
        # Extract keywords for direct search
        keywords = [word for word in query_lower.replace(',', ' ').replace('.', ' ').split() 
                  if len(word) > 2 and word not in {'the', 'and', 'for', 'with', 'are', 'you', 'get', 'all', 'offer', 'offers', 'deal', 'deals'}]
        
        # Quick lookup for popular categories
        category_matches = {
            'fashion': 'fashion OR clothing OR clothes OR apparel',
            'electronics': 'electronics OR gadget OR phone OR laptop OR computer',
            'travel': 'travel OR flight OR hotel OR vacation',
            'food': 'food OR restaurant OR dining OR delivery',
            'beauty': 'beauty OR makeup OR cosmetics OR skincare',
            'home': 'home OR furniture OR decor OR kitchen'
        }
        
        # First try direct search with limit 5
        search_conditions = []
        params = {"limit": limit}  # Strict limit
        
        # Add quick category conditions
        for category in category_matches:
            if category in query_lower:
                search_conditions.append(f"o.categories ILIKE '%{category}%'")
        
        # Add keyword conditions (max 3 for performance)
        for i, keyword in enumerate(keywords[:3]):
            if len(keyword) > 3:
                param_name = f"kw_{i}"
                search_conditions.append(f"o.title ILIKE :{param_name}")
                params[param_name] = f"%{keyword}%"
        
        # Build and execute query
        if search_conditions:
            condition_str = " OR ".join(search_conditions)
            sql_query = text(f"""
            SELECT o.*, c.name as campaign_name 
            FROM offers o
            JOIN campaigns c ON o.campaign_id = c.id
            WHERE (o.status = 'active' OR o.status = 'live')
            AND ({condition_str})
            LIMIT :limit
            """)
            offers = db.execute(sql_query, params).all()
        else:
            # Fallback to recent offers
            sql_query = text("""
            SELECT o.*, c.name as campaign_name 
            FROM offers o
            JOIN campaigns c ON o.campaign_id = c.id
            WHERE (o.status = 'active' OR o.status = 'live')
            ORDER BY o.created_at DESC
            LIMIT :limit
            """)
            offers = db.execute(sql_query, {"limit": limit}).all()
        
        # Process results (max 5)
        for offer in offers[:limit]:
            try:
                # Extract offer details
                if hasattr(offer, '_mapping'):
                    offer_dict = dict(offer._mapping)
                else:
                    offer_dict = {
                        'id': offer.id,
                        'title': offer.title,
                        'description': offer.description,
                        'image_url': offer.image_url,
                        'categories': offer.categories,
                        'coupon_code': offer.coupon_code,
                        'affiliate_url': offer.affiliate_url,
                        'url': offer.url,
                        'status': offer.status,
                        'campaign_name': getattr(offer, 'campaign_name', '')
                    }
                
                # Get URL with fallbacks
                affiliate_url = offer_dict.get('affiliate_url', '') or offer_dict.get('url', '')
                if not affiliate_url or affiliate_url == '#':
                    affiliate_url = offer_dict.get('url', '#')
                
                # Add formatted result
                result.append({
                    'id': offer_dict.get('id'),
                    'title': offer_dict.get('title') or 'Special Offer',
                    'description': (offer_dict.get('description') or 'Great deal available!')[:100],
                    'image_url': offer_dict.get('image_url') or '/static/images/placeholder_small.jpg',
                    'categories': offer_dict.get('categories') or '',
                    'coupon_code': offer_dict.get('coupon_code') or '',
                    'affiliate_url': affiliate_url,
                    'url': affiliate_url,
                    'website_url': affiliate_url,
                    'similarity': 0.85,
                    'campaign_name': offer_dict.get('campaign_name', '')
                })
            except Exception as e:
                logger.error(f"Error processing offer: {e}")
                continue
        
        # Log performance
        elapsed = time.time() - start_time
        logger.info(f"⚡ Ultra-fast search completed in {elapsed:.3f}s with {len(result)} results")
        return result
        
    except Exception as e:
        logger.error(f"Error in optimized search: {e}")
        elapsed = time.time() - start_time
        logger.error(f"Search failed after {elapsed:.3f}s")
        return []
    finally:
        if db:
            db.close()

def generate_response_ultra_fast(query: str, offers: List[Dict]) -> str:
    """Ultra fast response"""
    return ultra_fast_service.generate_response_simple(query, offers)
