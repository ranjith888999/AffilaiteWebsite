"""
Conversation Context Service
Manages conversation history and context for context-aware chatbot responses
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.database import ChatMessage, User

logger = logging.getLogger(__name__)


class ConversationContextService:
    """
    Service to manage conversation context and history
    """
    
    def __init__(self):
        # Entity extraction patterns
        self.category_keywords = {
            'electronics': ['laptop', 'phone', 'mobile', 'computer', 'tablet', 'gadget', 'electronics', 'tech'],
            'fashion': ['clothes', 'shirt', 'dress', 'shoes', 'fashion', 'clothing', 'wear', 'apparel'],
            'food': ['food', 'restaurant', 'dining', 'grocery', 'meal', 'cuisine'],
            'travel': ['travel', 'flight', 'hotel', 'vacation', 'trip', 'booking'],
            'home': ['furniture', 'decor', 'home', 'appliance', 'kitchen'],
            'beauty': ['beauty', 'makeup', 'cosmetics', 'skincare', 'fragrance'],
            'sports': ['sports', 'fitness', 'gym', 'exercise', 'athletic'],
            'books': ['book', 'reading', 'novel', 'textbook', 'ebook'],
            'toys': ['toy', 'game', 'kids', 'children', 'play'],
            'automotive': ['car', 'auto', 'vehicle', 'automotive', 'bike', 'motorcycle']
        }
        
        self.brand_pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b')
        self.price_pattern = re.compile(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars?|bucks?|rupees?|rs\.?)?|under\s+(\d+)|below\s+(\d+)|less\s+than\s+(\d+)')
        
    def extract_entities(self, message: str) -> Dict[str, Any]:
        """
        Extract entities from user message (categories, brands, price range, etc.)
        """
        message_lower = message.lower()
        entities = {
            'categories': [],
            'brands': [],
            'price_range': None,
            'keywords': []
        }
        
        # Extract categories
        for category, keywords in self.category_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                entities['categories'].append(category)
        
        # Extract potential brand names (capitalized words)
        brands = self.brand_pattern.findall(message)
        # Filter out common words
        common_words = {'The', 'This', 'That', 'What', 'Where', 'When', 'How', 'Why', 'Show', 'Find', 'Get'}
        entities['brands'] = [b for b in brands if b not in common_words and len(b) > 2]
        
        # Extract price range
        price_match = self.price_pattern.search(message_lower)
        if price_match:
            # Get the first non-None group
            price_str = next((g for g in price_match.groups() if g), None)
            if price_str:
                try:
                    price = float(price_str.replace(',', ''))
                    entities['price_range'] = {'max': price}
                except ValueError:
                    pass
        
        # Extract keywords (words longer than 3 characters, excluding common words)
        words = re.findall(r'\b\w{4,}\b', message_lower)
        stop_words = {'show', 'find', 'need', 'want', 'looking', 'search', 'help', 'please', 'thanks', 'thank'}
        entities['keywords'] = [w for w in words if w not in stop_words][:5]
        
        return entities
    
    def get_conversation_history(
        self, 
        session_id: str, 
        db: Session, 
        limit: int = 5,
        time_window_minutes: int = 30
    ) -> List[ChatMessage]:
        """
        Get recent conversation history for a session
        """
        try:
            # Get messages from the last time window
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id,
                ChatMessage.timestamp >= cutoff_time
            ).order_by(desc(ChatMessage.timestamp)).limit(limit).all()
            
            return list(reversed(messages))  # Chronological order
        except Exception as e:
            logger.error(f"Error fetching conversation history: {e}")
            return []
    
    def build_context_summary(
        self, 
        history: List[ChatMessage], 
        current_message: str
    ) -> Dict[str, Any]:
        """
        Build a comprehensive context summary from conversation history
        """
        context = {
            'message_count': len(history),
            'categories_mentioned': set(),
            'brands_mentioned': set(),
            'price_constraints': [],
            'recent_queries': [],
            'current_entities': {}
        }
        
        # Extract entities from history
        for msg in history:
            if msg.extracted_entities:
                try:
                    entities = json.loads(msg.extracted_entities)
                    context['categories_mentioned'].update(entities.get('categories', []))
                    context['brands_mentioned'].update(entities.get('brands', []))
                    if entities.get('price_range'):
                        context['price_constraints'].append(entities['price_range'])
                    
                    # Keep track of recent queries
                    if msg.message:
                        context['recent_queries'].append({
                            'query': msg.message[:100],  # Limit length
                            'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
                        })
                except json.JSONDecodeError:
                    pass
        
        # Extract entities from current message
        context['current_entities'] = self.extract_entities(current_message)
        
        # Merge current entities with historical context
        context['categories_mentioned'].update(context['current_entities'].get('categories', []))
        context['brands_mentioned'].update(context['current_entities'].get('brands', []))
        
        # Convert sets to lists for JSON serialization
        context['categories_mentioned'] = list(context['categories_mentioned'])
        context['brands_mentioned'] = list(context['brands_mentioned'])
        
        return context
    
    def generate_context_aware_prompt(
        self, 
        current_message: str, 
        context: Dict[str, Any],
        user_first_name: Optional[str] = None
    ) -> str:
        """
        Generate a context-aware prompt for the LLM
        """
        prompt_parts = []
        
        # Add personalization
        if user_first_name:
            prompt_parts.append(f"User's name is {user_first_name}.")
        
        # Add conversation context
        if context['message_count'] > 0:
            prompt_parts.append(f"This is a continuing conversation (message #{context['message_count'] + 1}).")
            
            # Add category context
            if context['categories_mentioned']:
                categories = ', '.join(context['categories_mentioned'])
                prompt_parts.append(f"User has been interested in: {categories}.")
            
            # Add brand context
            if context['brands_mentioned']:
                brands = ', '.join(context['brands_mentioned'])
                prompt_parts.append(f"User mentioned brands: {brands}.")
            
            # Add price context
            if context['price_constraints']:
                latest_price = context['price_constraints'][-1]
                if 'max' in latest_price:
                    prompt_parts.append(f"User's budget is under ${latest_price['max']}.")
            
            # Add recent queries context
            if len(context['recent_queries']) > 0:
                recent = context['recent_queries'][-1]['query']
                prompt_parts.append(f"Previous query: '{recent}'")
        
        # Current query context
        current_entities = context.get('current_entities', {})
        if current_entities.get('categories'):
            cats = ', '.join(current_entities['categories'])
            prompt_parts.append(f"Current interest: {cats}.")
        
        context_prompt = ' '.join(prompt_parts)
        return context_prompt if context_prompt else "This is the start of a new conversation."
    
    def is_followup_query(self, message: str, context: Dict[str, Any]) -> bool:
        """
        Determine if the current message is a follow-up query
        """
        # Short messages are likely follow-ups
        if len(message.split()) <= 3:
            return True
        
        # Contains reference words
        reference_words = ['that', 'those', 'these', 'them', 'it', 'more', 'other', 'different', 'similar', 'cheaper', 'better']
        message_lower = message.lower()
        if any(word in message_lower for word in reference_words):
            return True
        
        # Has conversation history
        if context['message_count'] > 0:
            # Check if message builds on previous context
            current_entities = context.get('current_entities', {})
            if not current_entities.get('categories') and context['categories_mentioned']:
                return True  # No new categories, likely refining previous search
        
        return False
    
    def enhance_query_with_context(
        self, 
        message: str, 
        context: Dict[str, Any]
    ) -> str:
        """
        Enhance the query with context for better search results
        """
        if not self.is_followup_query(message, context):
            return message  # Independent query, no enhancement needed
        
        # Build enhanced query
        enhancements = []
        
        # Add categories from context if not in current message
        current_entities = context.get('current_entities', {})
        if not current_entities.get('categories') and context['categories_mentioned']:
            enhancements.extend(context['categories_mentioned'])
        
        # Add brands from context if relevant
        if not current_entities.get('brands') and context['brands_mentioned']:
            enhancements.extend(list(context['brands_mentioned'])[:2])  # Limit to 2 brands
        
        if enhancements:
            enhanced = f"{message} {' '.join(enhancements)}"
            logger.info(f"Enhanced query: '{message}' → '{enhanced}'")
            return enhanced
        
        return message
    
    def save_message_with_context(
        self,
        db: Session,
        session_id: str,
        user_id: Optional[int],
        message: str,
        response: str,
        offers_count: int,
        processing_time: float,
        context: Dict[str, Any],
        previous_message_id: Optional[int] = None
    ) -> ChatMessage:
        """
        Save chat message with context information
        """
        try:
            chat_message = ChatMessage(
                session_id=session_id,
                user_id=user_id,
                message=message,
                response=response,
                offers_retrieved=offers_count,
                processing_time=processing_time,
                source='semantic_search',
                previous_message_id=previous_message_id,
                context_summary=json.dumps({
                    'categories': context.get('categories_mentioned', []),
                    'brands': context.get('brands_mentioned', []),
                    'message_count': context.get('message_count', 0)
                }),
                extracted_entities=json.dumps(context.get('current_entities', {}))
            )
            
            db.add(chat_message)
            db.commit()
            db.refresh(chat_message)
            
            logger.info(f"Saved message with context for session {session_id}")
            return chat_message
            
        except Exception as e:
            logger.error(f"Error saving message with context: {e}")
            db.rollback()
            raise
    
    def get_last_user_search(self, user_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """
        Get the user's last search query and context (for persistent context across sessions)
        Returns None if no previous search exists or if it's too old (>7 days)
        """
        try:
            # Get the last message from this user (within last 7 days)
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            
            last_message = db.query(ChatMessage).filter(
                ChatMessage.user_id == user_id,
                ChatMessage.timestamp >= cutoff_time,
                ChatMessage.is_offer_query == True  # Only queries that searched for offers
            ).order_by(desc(ChatMessage.timestamp)).first()
            
            if not last_message:
                return None
            
            # Parse context summary and extracted entities
            context_summary = {}
            extracted_entities = {}
            
            if last_message.context_summary:
                try:
                    context_summary = json.loads(last_message.context_summary)
                except:
                    pass
            
            if last_message.extracted_entities:
                try:
                    extracted_entities = json.loads(last_message.extracted_entities)
                except:
                    pass
            
            return {
                'query': last_message.user_message,
                'timestamp': last_message.timestamp,
                'categories': context_summary.get('categories', []) or extracted_entities.get('categories', []),
                'brands': context_summary.get('brands', []) or extracted_entities.get('brands', []),
                'keywords': extracted_entities.get('keywords', []),
                'found_offers': last_message.found_offers or 0,
                'session_id': last_message.session_id
            }
        
        except Exception as e:
            logger.error(f"Error getting last user search: {e}")
            return None
    
    def has_returning_user_context(self, user_id: int, current_session_id: str, db: Session) -> bool:
        """
        Check if user has previous search context from a different session
        (Used to determine if we should show "welcome back" message)
        """
        try:
            last_search = self.get_last_user_search(user_id, db)
            
            if not last_search:
                return False
            
            # Check if last search was from a different session
            return last_search['session_id'] != current_session_id
        
        except Exception as e:
            logger.error(f"Error checking returning user context: {e}")
            return False
    
    def get_welcome_back_message(
        self, 
        user_first_name: str, 
        last_search: Dict[str, Any]
    ) -> str:
        """
        Generate a personalized welcome back message with context reminder
        """
        categories = last_search.get('categories', [])
        brands = last_search.get('brands', [])
        query = last_search.get('query', '')
        
        # Build a friendly description of what they were searching for
        search_description = ""
        
        if categories and brands:
            # e.g., "Nike shoes" or "Apple electronics"
            search_description = f"{brands[0]} {categories[0]}"
        elif brands:
            # e.g., "Nike products"
            search_description = f"{brands[0]} products"
        elif categories:
            # e.g., "mobile deals" or "electronics"
            category = categories[0]
            if category == 'electronics' and 'mobile' in query.lower():
                search_description = "mobile deals 📱"
            elif category == 'fashion' and 'shoe' in query.lower():
                search_description = "shoe deals 👟"
            elif category == 'electronics' and 'laptop' in query.lower():
                search_description = "laptop deals 💻"
            else:
                search_description = f"{category} deals"
        else:
            # Fallback to first few words of query
            words = query.split()[:3]
            search_description = " ".join(words)
        
        # Add emoji based on category
        emoji = self._get_category_emoji(categories[0] if categories else None)
        if emoji and emoji not in search_description:
            search_description = f"{search_description} {emoji}"
        
        # Generate personalized message
        welcome_message = (
            f"Hey {user_first_name} 👋, welcome back! "
            f"Last time, you were checking out {search_description}. "
            f"Would you like to see updated offers for that?"
        )
        
        return welcome_message
    
    def _get_category_emoji(self, category: Optional[str]) -> str:
        """Get emoji for category"""
        emoji_map = {
            'electronics': '💻',
            'fashion': '👗',
            'food': '🍕',
            'travel': '✈️',
            'home': '🏠',
            'beauty': '💄',
            'sports': '⚽',
            'books': '📚',
            'toys': '🎮',
            'automotive': '🚗'
        }
        return emoji_map.get(category, '🎁')


# Singleton instance
_conversation_context_service = None

def get_conversation_context_service() -> ConversationContextService:
    """Get or create the conversation context service instance"""
    global _conversation_context_service
    if _conversation_context_service is None:
        _conversation_context_service = ConversationContextService()
    return _conversation_context_service
