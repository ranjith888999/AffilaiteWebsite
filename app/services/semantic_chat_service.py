import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
import google.generativeai as genai
import json
import os
import re


# Delayed import approach - only import when actually needed
EMBEDDINGS_AVAILABLE = False
SentenceTransformer = None
GEMINI_API_KEY = "AIzaSyC35Sdh0lxRv8WdGPJzb6nwNF7h1f3i5wI"
genai.configure(api_key=GEMINI_API_KEY)

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

    def get_general_response(self, user_first_name: str = None) -> dict:
        """Return a friendly response redirecting general knowledge questions to deals/offers"""
        if user_first_name:
            # Personalized response for logged-in users
            response_messages = [
                f"Hi {user_first_name}! 👋 I appreciate your question, but I'm specifically designed to help you find amazing deals, coupons, and offers!",
                f"Hey {user_first_name}! 😊 While that's an interesting question, my expertise is in finding you the best discounts and deals!",
                f"Hello {user_first_name}! 🎉 I'm your shopping assistant, so I specialize in deals and offers rather than general knowledge!",
                f"Hi there, {user_first_name}! 💫 That's outside my area, but I'm excellent at finding you incredible savings and deals!"
            ]
            # Rotate through messages based on name length for variety
            message_index = len(user_first_name) % len(response_messages)
            response_message = response_messages[message_index]
        else:
            # Generic but friendly response for non-logged-in users
            response_message = "Hey there! 👋 I appreciate your curiosity, but I'm your AI shopping assistant specialized in finding deals, coupons, and offers!"
        
        return {
            "type": "greeting",
            "message": response_message + "\n\n💡 **I can help you with:**\n\n• Finding the best deals on electronics, fashion, travel & more\n• Discovering exclusive coupons and discount codes\n• Comparing offers across different brands\n• Getting cashback opportunities\n\n**Try asking me:**\n\n• 'Show me laptop deals'\n• 'Find Nike discount codes'\n• 'Best offers on smartphones'\n• 'Travel deals and coupons'\n\nWhat deals are you looking for today? 🛍️",
            "suggestions": [
                "Electronics deals",
                "Fashion discounts", 
                "Food & Restaurant coupons",
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

    async def _generate_llm_response(self, query: str, context_offers: list, user_first_name: str = None) -> str:
        """
        Generate a personalized response using an LLM with the retrieved offers as context.
        """
        # Personalized opening based on user login status
        if user_first_name:
            personalized_intro = f"Hi {user_first_name}! "
        else:
            personalized_intro = ""
        
        if not OPENAI_AVAILABLE:
            if context_offers:
                return f"{personalized_intro}I found {len(context_offers)} great deals for '{query}'! Let me show you what I've got:"
            else:
                return f"{personalized_intro}I couldn't find any deals for '{query}'. Try a different search term!"

        # Create a detailed context string from the offers
        context_str = "\n".join([
            f"- **{offer['title']}** from {offer['campaign']} (Category: {', '.join(offer['categories'])}). Description: {offer['description']}. Coupon: `{offer['coupon_code'] if offer['coupon_code'] else 'N/A'}`."
            for offer in context_offers
        ])

        # System prompt to guide the LLM with personalization instructions
        system_prompt = f"""
        You are DealsHub AI, a friendly and helpful shopping assistant. Your goal is to help users find the best deals based on the context provided.
        {"The user's name is " + user_first_name + ". Use their name naturally in your responses to create a warm, personal conversation." if user_first_name else "The user is not logged in. Be friendly but use generic greetings."}
        - Analyze the user's query and the provided list of deals.
        - Synthesize a friendly, conversational, and informative response.
        - Mention the most relevant deals and highlight key details like coupon codes or discounts.
        - If no deals are found, say so politely and suggest trying other search terms.
        - Do not invent deals or information not present in the context.
        - Keep the response concise, warm, and engaging.
        - Use emojis sparingly to add personality (1-2 per response).
        """

        # User prompt with the context
        user_prompt = f"""
        User Query: "{query}"

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
                max_tokens=250
            )
            return response.choices[0].message['content'].strip()
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            # Fallback to the personalized simple message if the LLM call fails
            if context_offers:
                return f"{personalized_intro}I found {len(context_offers)} great deals for '{query}'! Let me show you what I've got:"
            else:
                return f"{personalized_intro}I couldn't find any deals for '{query}'. Try a different search term!"

    async def semantic_search(self, query: str, db: Session, top_k: int = 10, user_first_name: str = None, fromloc: str = None) -> dict:
        """
        Perform semantic search for offers and generate a personalized response using an LLM.
        """
        if fromloc is not None:
            queryType = await self.classify_query(query)
            logger.info(f"Query classified as: {queryType}")
            
            if queryType == "General":
                return self.get_general_response(user_first_name)
            elif queryType == "Greetings":
                return self.get_greeting_response(user_first_name)
            # If queryType == "Offers", continue with semantic search below

        # Try to load the embedding model
        embedding_model = self._load_embedding_model()
        if not embedding_model:
            logger.warning("No embedding model available. Falling back to text search.")
            offers = await self.fallback_search(query, db, top_k)
            message = await self._generate_llm_response(query, offers, user_first_name)
            return {
                "type": "offers",
                "message": message,
                "offers": offers,
                "total": len(offers)
            }
            
        try:
            # 1. Generate embedding for the user query
            query_embedding = embedding_model.encode(query).tolist()
            
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
            
            # 4. Generate a conversational response using the LLM with personalization
            llm_message = await self._generate_llm_response(query, formatted_results, user_first_name)

            return {
                "type": "offers",
                "message": llm_message,
                "offers": formatted_results,
                "total": len(formatted_results)
            }
            
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            # Fallback to a simple text search if vector search fails
            offers = await self.fallback_search(query, db, top_k)
            message = await self._generate_llm_response(query, offers, user_first_name)
            return {
                "type": "offers",
                "message": message,
                "offers": offers,
                "total": len(offers)
            }

    async def classify_query(self, user_query):
        """
        Classify user query into one of three categories: Greetings, General, or Offers.
        Includes fallback mechanism if Gemini API fails.
        """
        # Create the classification prompt
        prompt = f"""You are a query classifier for an affiliate deals and coupons website. Your job is to classify the given user query into exactly one of these three categories:

        1. "Greetings" - If the query is a greeting such as:
        - Hi, Hello, Hey, Howdy
        - Good morning, Good afternoon, Good evening
        - How are you, How do you do, What's up
        - Hi Good Morning, Hello Good Evening
        - Any combination of greetings or casual conversation starters

        2. "General" - If the query is a general knowledge question NOT related to shopping, deals, or offers:
        - What is the capital of India?
        - Where is Hyderabad?
        - Who invented the telephone?
        - Questions about facts, places, people, science, history, etc.
        - Any informational question unrelated to shopping or deals

        3. "Offers" - If the query is related to deals, coupons, offers, discounts, or shopping:
        - Show me laptop deals
        - Find Nike discount codes
        - Best offers on smartphones
        - Cheap shoes under $50
        - Electronics deals
        - Fashion coupons
        - Travel offers
        - Restaurant discounts
        - Any query about products, brands, categories, prices, deals, coupons, or shopping

        User Query: "{user_query}"

        Respond with ONLY one word: either "Greetings", "General", or "Offers". No explanation needed."""

        try:
            # Initialize the model (using gemini-2.5-flash-lite for lower cost)
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            
            # Generate response with timeout
            response = model.generate_content(prompt)
            
            # Extract and clean the response
            classification = response.text.strip()
            
            # Ensure the response is one of the expected values
            if "Greetings" in classification:
                return "Greetings"
            elif "General" in classification:
                return "General"
            elif "Offers" in classification:
                return "Offers"
            else:
                # If unexpected response, use fallback
                logger.warning(f"Unexpected classification response: {classification}. Using fallback.")
                return self._fallback_classification(user_query)
                
        except Exception as e:
            logger.error(f"Error during Gemini API classification: {e}. Using fallback mechanism.")
            return self._fallback_classification(user_query)
    
    def _fallback_classification(self, user_query: str) -> str:
        """
        Fallback classification using simple keyword matching when Gemini API fails.
        """
        query_lower = user_query.lower().strip()
        
        # Check for greetings first (most specific)
        greeting_keywords = [
            'hello', 'hi', 'hey', 'howdy', 'greetings',
            'good morning', 'good afternoon', 'good evening', 'good night',
            'how are you', "what's up", 'whats up', 'sup', 'yo'
        ]
        if any(keyword in query_lower for keyword in greeting_keywords):
            return "Greetings"
        
        # Check for shopping/deals related keywords (highest priority for business logic)
        offers_keywords = [
            'deal', 'deals', 'offer', 'offers', 'coupon', 'coupons', 'discount', 'discounts',
            'sale', 'sales', 'promo', 'promotion', 'code', 'cashback', 'voucher',
            'buy', 'shop', 'shopping', 'purchase', 'price', 'cheap', 'affordable',
            'show me', 'find', 'search', 'looking for', 'want', 'need',
            'best', 'top', 'cheapest', 'lowest', 'under', 'below',
            # Categories
            'electronics', 'fashion', 'clothing', 'shoes', 'laptop', 'phone', 'mobile',
            'smartphone', 'tablet', 'computer', 'tv', 'camera', 'headphone',
            'travel', 'hotel', 'flight', 'food', 'restaurant', 'grocery',
            'home', 'furniture', 'appliance', 'beauty', 'makeup', 'skincare',
            'sports', 'fitness', 'book', 'toy', 'game', 'jewelry',
            # Brands (common ones)
            'amazon', 'flipkart', 'nike', 'adidas', 'samsung', 'apple', 'sony'
        ]
        if any(keyword in query_lower for keyword in offers_keywords):
            return "Offers"
        
        # Check for general knowledge question patterns
        general_patterns = [
            'what is', 'what are', 'who is', 'who are', 'where is', 'where are',
            'when is', 'when was', 'when were', 'how does', 'how do', 'why is', 'why does',
            'capital of', 'president of', 'population of', 'meaning of',
            'explain', 'define', 'tell me about', 'information about'
        ]
        if any(pattern in query_lower for pattern in general_patterns):
            # Double check it's not about deals/offers
            if not any(keyword in query_lower for keyword in offers_keywords):
                return "General"
        
        # Default to Offers for this shopping-focused website
        # This ensures most queries are handled as potential deal searches
        return "Offers"

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
