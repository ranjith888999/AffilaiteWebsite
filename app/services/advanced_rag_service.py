"""
Advanced RAG-based Chat Service with Semantic Search and Hybrid Approach
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re

# For embeddings and semantic search
EMBEDDINGS_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

# Database imports
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.database import get_db_sync
from app.models.database import Offer, Campaign

logger = logging.getLogger(__name__)

class AdvancedRAGChatService:
    """
    Advanced RAG service combining:
    1. Semantic search using sentence transformers
    2. Keyword-based search for immediate relevance
    3. Category mapping for better organization
    4. Real database integration
    """
    
    def __init__(self):
        self.embeddings_model = None
        self.offer_embeddings = {}
        self.categories = {
            'fashion': {
                'keywords': ['fashion', 'clothes', 'clothing', 'dress', 'shirt', 'shoes', 'bag', 'accessories', 'style', 'wear', 'apparel', 'garment', 'myntra', 'zara', 'h&m'],
                'categories': ['Fashion', 'Clothing', 'Accessories', 'Footwear']
            },
            'electronics': {
                'keywords': ['electronics', 'phone', 'mobile', 'smartphone', 'laptop', 'computer', 'gadget', 'tech', 'technology', 'device', 'tablet', 'headphones', 'electronic', 'iphone', 'samsung'],
                'categories': ['Electronics', 'Mobile', 'Technology', 'Gadgets', 'Computers']
            },
            'beauty': {
                'keywords': ['nykaa', 'beauty', 'makeup', 'cosmetics', 'skincare', 'lipstick', 'foundation', 'perfume', 'fragrance'],
                'categories': ['Beauty', 'Health & Beauty', 'Cosmetics']
            },
            'travel': {
                'keywords': ['travel', 'trip', 'vacation', 'hotel', 'flight', 'booking', 'tourism', 'holiday', 'journey', 'destination', 'makemytrip'],
                'categories': ['Travel', 'Hotels', 'Tourism', 'Flight']
            },
            'food': {
                'keywords': ['food', 'grocery', 'restaurant', 'delivery', 'cooking', 'recipe', 'meal', 'eat', 'dining', 'cuisine'],
                'categories': ['Food', 'Grocery', 'Restaurant', 'Food & Grocery']
            },
            'health': {
                'keywords': ['health', 'wellness', 'fitness', 'vitamin', 'medical', 'care'],
                'categories': ['Health', 'Wellness', 'Fitness']
            },
            'home': {
                'keywords': ['home', 'furniture', 'kitchen', 'garden', 'decoration', 'appliance', 'house', 'living'],
                'categories': ['Home', 'Kitchen', 'Home & Kitchen', 'Furniture', 'Garden']
            },
            'books': {
                'keywords': ['book', 'books', 'reading', 'novel', 'education', 'study', 'literature'],
                'categories': ['Books', 'Education', 'Literature']
            },
            'gaming': {
                'keywords': ['game', 'gaming', 'console', 'playstation', 'xbox', 'nintendo', 'pc gaming', 'video game'],
                'categories': ['Gaming', 'Games', 'Video Games']
            }
        }
        
        # Initialize embeddings model if available
        global EMBEDDINGS_AVAILABLE
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ Sentence transformer model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load sentence transformer: {e}")
                EMBEDDINGS_AVAILABLE = False
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Remove special characters and convert to lowercase
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = clean_text.split()
        
        # Filter out common words (basic stop words)
        stop_words = {'the', 'is', 'at', 'which', 'on', 'and', 'a', 'to', 'are', 'as', 'for', 'with', 'by', 'from', 'of', 'in', 'or'}
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _detect_category(self, query: str) -> Optional[str]:
        """Detect the most relevant category from the query"""
        query_lower = query.lower()
        
        for category, data in self.categories.items():
            for keyword in data['keywords']:
                if keyword in query_lower:
                    return category
        
        return None
    
    def _get_database_offers(self, limit: int = 20, category: Optional[str] = None, 
                           search_term: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get offers from database with filtering"""
        try:
            db = next(get_db_sync())
            query = db.query(Offer).filter(Offer.status != 'inactive')
            
            # Category filtering
            if category and category in self.categories:
                category_filters = self.categories[category]['categories']
                conditions = []
                for cat in category_filters:
                    conditions.append(Offer.categories.like(f'%{cat}%'))
                if conditions:
                    query = query.filter(func.or_(*conditions))
            
            # Search term filtering
            if search_term:
                keywords = self._extract_keywords(search_term)
                for keyword in keywords[:3]:  # Use top 3 keywords
                    query = query.filter(
                        func.or_(
                            Offer.title.ilike(f'%{keyword}%'),
                            Offer.description.ilike(f'%{keyword}%')
                        )
                    )
            
            # Get results
            offers = query.limit(limit).all()
            
            # Convert to dict format
            result = []
            for offer in offers:
                # Fix URLs - ensure they're proper external URLs
                affiliate_url = offer.affiliate_url or ''
                if not affiliate_url or affiliate_url == '#' or 'localhost' in affiliate_url:
                    # Generate a proper affiliate URL using the original URL
                    if offer.url and offer.url.startswith('http'):
                        affiliate_url = offer.url
                    else:
                        affiliate_url = f"https://www.cuelinks.com/redirect?url={offer.url}" if offer.url else "#"
                
                result.append({
                    'id': offer.id,
                    'title': offer.title or 'Special Offer',
                    'description': offer.description or 'Amazing deal available',
                    'image_url': offer.image_url or '/static/images/placeholder.jpg',
                    'categories': offer.categories or '',
                    'coupon_code': offer.coupon_code or '',
                    'affiliate_url': affiliate_url,
                    'url': offer.url or affiliate_url,
                    'website_url': affiliate_url,  # Use affiliate_url for website_url
                    'similarity': 0.8,  # Default similarity score
                    'offer_type': offer.offer_type or '',
                    'status': offer.status or 'active'
                })
            
            logger.info(f"Retrieved {len(result)} offers from database")
            return result
            
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return []
        finally:
            if 'db' in locals():
                db.close()
    
    def _semantic_search(self, query: str, offers: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings"""
        global EMBEDDINGS_AVAILABLE
        if not EMBEDDINGS_AVAILABLE or not self.embeddings_model or not offers:
            return offers[:top_k]
        
        try:
            # Create embeddings for query
            query_embedding = self.embeddings_model.encode([query])
            
            # Create embeddings for offers
            offer_texts = []
            for offer in offers:
                # Combine title and description for better semantic matching
                text = f"{offer['title']} {offer['description']}"
                offer_texts.append(text)
            
            if not offer_texts:
                return offers[:top_k]
                
            offer_embeddings = self.embeddings_model.encode(offer_texts)
            
            # Calculate cosine similarity
            similarities = cosine_similarity(query_embedding, offer_embeddings)[0]
            
            # Add similarity scores and sort
            for i, offer in enumerate(offers):
                offer['similarity'] = float(similarities[i])
            
            # Sort by similarity and return top results
            sorted_offers = sorted(offers, key=lambda x: x['similarity'], reverse=True)
            
            logger.info(f"Semantic search completed. Top similarity: {sorted_offers[0]['similarity']:.3f}")
            return sorted_offers[:top_k]
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return offers[:top_k]
    
    def _hybrid_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Hybrid search combining:
        1. Category detection
        2. Keyword-based database search
        3. Semantic search for ranking
        """
        
        # Step 1: Detect category
        detected_category = self._detect_category(query)
        logger.info(f"Detected category: {detected_category}")
        
        # Step 2: Extract search terms
        keywords = self._extract_keywords(query)
        search_term = ' '.join(keywords[:3]) if keywords else query
        
        # Step 3: Get offers from database
        offers = self._get_database_offers(
            limit=limit * 3,  # Get more for better semantic filtering
            category=detected_category,
            search_term=search_term
        )
        
        if not offers:
            # Fallback: get general offers
            offers = self._get_database_offers(limit=limit * 2)
        
        # Step 4: Apply semantic search for ranking
        ranked_offers = self._semantic_search(query, offers, limit)
        
        return ranked_offers
    
    def search_offers(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Main search function using hybrid approach"""
        try:
            return self._hybrid_search(query, limit)
        except Exception as e:
            logger.error(f"Search error: {e}")
            # Ultimate fallback
            return self._get_database_offers(limit=limit)
    
    def generate_response(self, query: str, offers: List[Dict]) -> str:
        """Generate an intelligent response based on query and offers"""
        if not offers:
            return f"I'm currently updating our offers database. Please try again in a moment, or browse our available categories for the latest deals!"
        
        # Analyze query intent
        query_lower = query.lower()
        
        # Greeting responses
        if any(word in query_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return "Hello! I'm your personal deal finder assistant. I can help you discover amazing offers across fashion, electronics, travel, and more. What kind of deals are you looking for today?"
        
        # Generate contextual response
        detected_category = self._detect_category(query)
        
        if detected_category:
            category_name = detected_category.title()
            response = f"Great choice! I found {len(offers)} excellent {category_name.lower()} deals for you:\n\n"
        else:
            response = f"Perfect! I discovered {len(offers)} amazing deals matching your search:\n\n"
        
        # Add offer details
        for i, offer in enumerate(offers[:3], 1):
            title = offer['title'][:60] + "..." if len(offer['title']) > 60 else offer['title']
            response += f"{i}. **{title}**\n"
            
            description = offer['description'][:100] + "..." if len(offer['description']) > 100 else offer['description']
            response += f"   {description}\n"
            
            if offer.get('coupon_code'):
                response += f"   💰 Coupon: {offer['coupon_code']}\n"
            
            if offer.get('similarity', 0) > 0.7:
                response += f"   ⭐ Highly recommended\n"
            
            response += "\n"
        
        if len(offers) > 3:
            response += f"Plus {len(offers) - 3} more fantastic deals available!\n\n"
        
        response += "Click 'Get Deal' on any offer to visit the store and save money! 💰"
        
        return response

# Global service instance
advanced_rag_service = AdvancedRAGChatService()

# Convenience functions for backward compatibility
def search_offers_advanced(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search offers using advanced RAG approach"""
    return advanced_rag_service.search_offers(query, limit)

def generate_advanced_response(query: str, offers: List[Dict]) -> str:
    """Generate response using advanced RAG approach"""
    return advanced_rag_service.generate_response(query, offers)
