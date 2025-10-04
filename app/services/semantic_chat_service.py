import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import os
import re

# Delayed import approach - only import when actually needed
EMBEDDINGS_AVAILABLE = False
SentenceTransformer = None

def _import_sentence_transformers():
    """Import sentence transformers only when needed"""
    global EMBEDDINGS_AVAILABLE, SentenceTransformer
    if SentenceTransformer is None:
        try:
            from sentence_transformers import SentenceTransformer as ST
            SentenceTransformer = ST
            EMBEDDINGS_AVAILABLE = True
            print("✅ sentence-transformers loaded successfully")
        except ImportError as e:
            EMBEDDINGS_AVAILABLE = False
            SentenceTransformer = None
            print(f"⚠️ Warning: sentence-transformers not available: {e}")
        except Exception as e:
            EMBEDDINGS_AVAILABLE = False
            SentenceTransformer = None
            print(f"⚠️ Warning: Error loading sentence-transformers: {e}")
    return EMBEDDINGS_AVAILABLE

# Import OpenAI for LLM-based response generation
try:
    import openai
    OPENAI_AVAILABLE = True
    
    # Configure client for local Llama model (Ollama)
    # Assumes an OpenAI-compatible API is running at this address
    openai.api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434/v1")
    openai.api_key = "ollama"  # Local models often don't require a key, but the client might
    
    print(f"✅ LLM generation enabled, using endpoint: {openai.api_base}")

except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ Warning: openai library not installed. LLM generation is disabled.")


from app.models.database import Offer, OfferEmbedding
from app.services.conversation_context_service import get_conversation_context_service

logger = logging.getLogger(__name__)

class SemanticChatService:
    def __init__(self):
        self.embedding_model = None
        self.greeting_patterns = [
            'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
            'how are you', 'whats up', "what's up", 'greetings', 'howdy'
        ]
        # Defer loading of sentence transformers until actually needed
        self.embedding_model = None
        # Get conversation context service
        self.context_service = get_conversation_context_service()
    
    def _load_embedding_model(self):
        """Lazy load the embedding model"""
        if self.embedding_model is None and _import_sentence_transformers():
            try:
                # Using a smaller, efficient model suitable for semantic search
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Semantic search embedding model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load embedding model for semantic search: {e}")
                self.embedding_model = None
        return self.embedding_model
    
    def is_greeting(self, query: str) -> bool:
        """Check if the query is a greeting"""
        query_lower = query.lower().strip()
        return any(pattern in query_lower for pattern in self.greeting_patterns)
    
    def get_greeting_response(self, user_first_name: str = None) -> dict:
        """Return a friendly greeting response with personalization"""
        if user_first_name:
            # Personalized greeting for logged-in users
            greeting_messages = [
                f"Hi {user_first_name}! 👋 How's your day going? I'm here to help you find amazing deals!",
                f"Hey {user_first_name}! 😊 Great to see you again! What kind of deals are you looking for today?",
                f"Hello {user_first_name}! 🎉 Ready to save big? Let me help you discover the best offers!",
                f"Hi there, {user_first_name}! � I'm excited to help you find incredible deals today!"
            ]
            # Rotate through messages based on name length for variety
            message_index = len(user_first_name) % len(greeting_messages)
            greeting_message = greeting_messages[message_index]
        else:
            # Generic but friendly greeting for non-logged-in users
            greeting_message = "Hey there 👋, how can I help you today? I'm your AI shopping assistant ready to find you the best deals!"
        
        return {
            "type": "greeting",
            "message": greeting_message + "\n\nTry asking me something like:\n\n• 'Show me electronics deals'\n• 'Find Nike coupons'\n• 'Best laptop offers'\n• 'Cheap shoes under $50'\n\nWhat are you looking for today?",
            "suggestions": [
                "Electronics deals",
                "Fashion discounts", 
                "Food coupons",
                "Travel offers"
            ]
        }
    
    def _clean_html(self, text: str) -> str:
        """Clean HTML tags from text"""
        if not text:
            return ""
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', text)
        return ' '.join(text.split())

    async def _generate_llm_response(
        self, 
        query: str, 
        context_offers: list, 
        user_first_name: str = None,
        conversation_context: dict = None,
        is_followup: bool = False
    ) -> str:
        """
        Generate a context-aware personalized response using an LLM with the retrieved offers as context.
        """
        # Personalized opening based on user login status
        if user_first_name:
            personalized_intro = f"Hi {user_first_name}! "
        else:
            personalized_intro = ""
        
        # Context-aware response adjustments
        context_intro = ""
        if is_followup and conversation_context:
            if conversation_context.get('categories_mentioned'):
                cats = conversation_context['categories_mentioned']
                if len(cats) == 1:
                    context_intro = f"Looking for more {cats[0]} deals? "
                elif len(cats) > 1:
                    context_intro = f"I see you're interested in {' and '.join(cats[:2])}. "
        
        if not OPENAI_AVAILABLE:
            if context_offers:
                return f"{personalized_intro}{context_intro}I found {len(context_offers)} great deals for you! Let me show you what I've got:"
            else:
                suggestions = ""
                if conversation_context and conversation_context.get('categories_mentioned'):
                    cats = conversation_context['categories_mentioned']
                    suggestions = f" Try searching for '{cats[0]}' or similar terms."
                return f"{personalized_intro}I couldn't find any deals for that.{suggestions} Try a different search term!"

        # Create a detailed context string from the offers
        context_str = "\n".join([
            f"- **{offer['title']}** from {offer['campaign']} (Category: {', '.join(offer['categories'])}). Description: {offer['description']}. Coupon: `{offer['coupon_code'] if offer['coupon_code'] else 'N/A'}`."
            for offer in context_offers
        ])

        # Build conversation context for LLM
        conv_context_str = ""
        if conversation_context and conversation_context.get('message_count', 0) > 0:
            conv_context_str = f"\nConversation context: "
            if conversation_context.get('categories_mentioned'):
                conv_context_str += f"User previously searched for {', '.join(conversation_context['categories_mentioned'])}. "
            if conversation_context.get('brands_mentioned'):
                conv_context_str += f"Interested in brands: {', '.join(conversation_context['brands_mentioned'])}. "
            if is_followup:
                conv_context_str += "This is a follow-up query to refine the previous search. "

        # System prompt to guide the LLM with personalization and context awareness
        system_prompt = f"""
        You are DealsHub AI, a friendly and helpful shopping assistant. Your goal is to help users find the best deals based on the context provided.
        {"The user's name is " + user_first_name + ". Use their name naturally in your responses to create a warm, personal conversation." if user_first_name else "The user is not logged in. Be friendly but use generic greetings."}
        
        CONTEXT AWARENESS:
        {conv_context_str if conv_context_str else "This is the start of a new conversation."}
        {"The user is refining their previous search. Acknowledge this and help them narrow down options." if is_followup else "This is a new search query."}
        
        RESPONSE GUIDELINES:
        - Analyze the user's query and the provided list of deals
        - If this is a follow-up, reference the conversation history naturally
        - Synthesize a friendly, conversational, and informative response
        - Mention the most relevant deals and highlight key details like coupon codes or discounts
        - If no deals are found, suggest alternatives based on conversation history
        - Do not invent deals or information not present in the context
        - Keep the response concise, warm, and engaging
        - Use emojis sparingly to add personality (1-2 per response)
        - Help users refine their search if they seem to be exploring options
        """

        # User prompt with the context
        user_prompt = f"""
        User Query: "{query}"
        
        {conv_context_str}

        Here are the deals I found in the database:
        {context_str if context_offers else "No deals found."}

        Based on this, what is the best response to the user?
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # Slightly higher for more personality
                max_tokens=300  # Slightly more for context-aware responses
            )
            return response.choices[0].message['content'].strip()
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            # Fallback to the personalized context-aware simple message
            if context_offers:
                return f"{personalized_intro}{context_intro}I found {len(context_offers)} great deals for you! Let me show you what I've got:"
            else:
                suggestions = ""
                if conversation_context and conversation_context.get('categories_mentioned'):
                    cats = conversation_context['categories_mentioned']
                    suggestions = f" Maybe try '{cats[0]}' or something similar?"
                return f"{personalized_intro}I couldn't find any deals for that.{suggestions}"

    async def semantic_search(
        self, 
        query: str, 
        db: Session, 
        session_id: str = None,
        user_id: int = None,
        top_k: int = 10, 
        user_first_name: str = None
    ) -> dict:
        """
        Perform semantic search for offers with conversation context awareness
        """
        import time
        start_time = time.time()
        
        # Handle greetings
        if self.is_greeting(query):
            return self.get_greeting_response(user_first_name)
        
        # Get conversation history and build context
        conversation_history = []
        context = {'message_count': 0, 'categories_mentioned': [], 'brands_mentioned': []}
        previous_message_id = None
        
        if session_id:
            conversation_history = self.context_service.get_conversation_history(
                session_id=session_id,
                db=db,
                limit=5,
                time_window_minutes=30
            )
            context = self.context_service.build_context_summary(conversation_history, query)
            
            # Get the last message ID for linking
            if conversation_history:
                previous_message_id = conversation_history[-1].id
        
        # Enhance query with context for better results
        enhanced_query = self.context_service.enhance_query_with_context(query, context)
        is_followup = self.context_service.is_followup_query(query, context)
        
        logger.info(f"Query: '{query}' | Enhanced: '{enhanced_query}' | Follow-up: {is_followup} | Context: {len(conversation_history)} msgs")
        
        # Try to load the embedding model
        embedding_model = self._load_embedding_model()
        if not embedding_model:
            logger.warning("No embedding model available. Falling back to text search.")
            offers = await self.fallback_search(enhanced_query, db, top_k)
            message = await self._generate_llm_response(
                query, offers, user_first_name, context, is_followup
            )
            
            # Save message with context
            if session_id:
                try:
                    self.context_service.save_message_with_context(
                        db=db,
                        session_id=session_id,
                        user_id=user_id,
                        message=query,
                        response=message,
                        offers_count=len(offers),
                        processing_time=time.time() - start_time,
                        context=context,
                        previous_message_id=previous_message_id
                    )
                except Exception as e:
                    logger.error(f"Error saving context: {e}")
            
            return {
                "type": "offers",
                "message": message,
                "offers": offers,
                "total": len(offers),
                "context": {
                    "is_followup": is_followup,
                    "categories": context.get('categories_mentioned', []),
                    "conversation_length": len(conversation_history)
                }
            }
            
        try:
            # 1. Generate embedding for the enhanced query (with context)
            query_embedding = embedding_model.encode(enhanced_query).tolist()
            
            # 2. Perform vector similarity search in the public.offer_embeddings table
            # The query uses the <=> operator for cosine distance (1 - cosine_similarity)
            # We calculate similarity as (1 - distance) and order by similarity desc for highest scores first
            sql_query = text("""
                SELECT
                    o.id AS offer_id,
                    o.title,
                    o.description,
                    o.coupon_code,
                    o.image_url,
                    o.affiliate_url,
                    o.offer_type AS type,
                    o.categories,
                    c.name AS campaign,
                    oe.embedding <=> CAST(:query_embedding AS vector) AS distance,
                    (1 - (oe.embedding <=> CAST(:query_embedding AS vector))) AS similarity_score
                FROM
                    public.offer_embeddings oe
                JOIN
                    public.offers o ON oe.offer_id = o.id
                JOIN
                    public.campaigns c ON o.campaign_id = c.id
                ORDER BY
                    similarity_score DESC
                LIMIT :top_k
            """)
            
            results = db.execute(
                sql_query,
                {"query_embedding": str(query_embedding), "top_k": top_k}
            ).fetchall()
            
            # 3. Format the results for the LLM and the UI
            formatted_results = []
            for row in results:
                try:
                    categories = json.loads(row.categories) if row.categories and row.categories.startswith('{') else {}
                    category_names = list(categories.values())
                except (json.JSONDecodeError, TypeError):
                    category_names = []

                formatted_results.append({
                    "offer_id": row.offer_id,
                    "campaign": row.campaign,
                    "title": row.title,
                    "description": self._clean_html(row.description),
                    "image_url": row.image_url or "/static/images/placeholder.jpg",
                    "coupon_code": row.coupon_code,
                    "categories": category_names,
                    "type": row.type,
                    "affiliate_url": row.affiliate_url,
                    "distance": row.distance,
                    "similarity_score": row.similarity_score  # Add the calculated similarity score
                })
            
            # 4. Generate a context-aware conversational response using the LLM
            llm_message = await self._generate_llm_response(
                query, formatted_results, user_first_name, context, is_followup
            )
            
            # 5. Save message with context
            if session_id:
                try:
                    self.context_service.save_message_with_context(
                        db=db,
                        session_id=session_id,
                        user_id=user_id,
                        message=query,
                        response=llm_message,
                        offers_count=len(formatted_results),
                        processing_time=time.time() - start_time,
                        context=context,
                        previous_message_id=previous_message_id
                    )
                except Exception as e:
                    logger.error(f"Error saving context: {e}")

            return {
                "type": "offers",
                "message": llm_message,
                "offers": formatted_results,
                "total": len(formatted_results),
                "context": {
                    "is_followup": is_followup,
                    "categories": context.get('categories_mentioned', []),
                    "conversation_length": len(conversation_history),
                    "enhanced_query": enhanced_query if enhanced_query != query else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            # Fallback to a simple text search if vector search fails
            offers = await self.fallback_search(enhanced_query, db, top_k)
            message = await self._generate_llm_response(
                query, offers, user_first_name, context, is_followup
            )
            
            # Save message with context even in fallback
            if session_id:
                try:
                    self.context_service.save_message_with_context(
                        db=db,
                        session_id=session_id,
                        user_id=user_id,
                        message=query,
                        response=message,
                        offers_count=len(offers),
                        processing_time=time.time() - start_time,
                        context=context,
                        previous_message_id=previous_message_id
                    )
                except Exception as save_err:
                    logger.error(f"Error saving context in fallback: {save_err}")
            
            return {
                "type": "offers",
                "message": message,
                "offers": offers,
                "total": len(offers),
                "context": {
                    "is_followup": is_followup,
                    "categories": context.get('categories_mentioned', []),
                    "conversation_length": len(conversation_history)
                }
            }

    async def fallback_search(self, query: str, db: Session, top_k: int = 10) -> list:
        """
        Fallback to simple text search if vector search fails.
        """
        logger.warning(f"Falling back to simple text search for query: {query}")
        try:
            search_term = f"%{query}%"
            
            results = db.query(Offer).filter(
                (Offer.title.ilike(search_term)) |
                (Offer.description.ilike(search_term))
            ).limit(top_k).all()
            
            formatted_results = []
            for offer in results:
                try:
                    categories = json.loads(offer.categories) if offer.categories and offer.categories.startswith('{') else {}
                    category_names = list(categories.values())
                except (json.JSONDecodeError, TypeError):
                    category_names = []

                formatted_results.append({
                    "offer_id": offer.id,
                    "campaign": offer.campaign_name,
                    "title": offer.title,
                    "description": self._clean_html(offer.description),
                    "image_url": offer.image_url or "/static/images/placeholder.jpg",
                    "coupon_code": offer.coupon_code,
                    "categories": category_names,
                    "type": offer.offer_type,
                    "affiliate_url": offer.affiliate_url,
                    "distance": 1.0  # Indicate it's not a vector search result
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error during fallback search: {e}")
            return []

# Global instance
semantic_chat_service = SemanticChatService()
