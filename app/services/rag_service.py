"""
RAG (Retrieval Augmented Generation) Service using LangChain
This service provides accurate offer recommendations and answers using vector embeddings
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio

# LangChain imports
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.vectorstores.base import VectorStore
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from langchain_openai import OpenAI, ChatOpenAI

# Database imports
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, text
from sqlalchemy.orm import selectinload
import numpy as np

from app.models.database import Offer, OfferEmbedding
from app.database import get_db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostgreSQLVectorStore:
    """
    Custom PostgreSQL Vector Store for embeddings
    Implements similarity search using cosine similarity
    """
    
    def __init__(self, session: AsyncSession, embedding_model):
        self.session = session
        self.embedding_model = embedding_model
        
    async def add_documents(self, documents: List[Document], offer_id: int, campaign_id: Optional[int] = None):
        """Add documents with embeddings to PostgreSQL"""
        try:
            for i, doc in enumerate(documents):
                # Generate embedding
                embedding = self.embedding_model.encode(doc.page_content).tolist()
                
                try:
                    # Create embedding record with campaign_id if the column exists
                    embedding_record = OfferEmbedding(
                        offer_id=offer_id,
                        campaign_id=campaign_id,  # Add campaign_id to embedding
                        chunk_id=f"{offer_id}_{i}",
                        content=doc.page_content,
                        content_type=doc.metadata.get('type', 'combined'),
                        embedding=embedding,
                        meta_data=json.dumps(doc.metadata)  # Use meta_data instead of metadata
                    )
                except Exception as column_error:
                    # If campaign_id column doesn't exist, create without it
                    logger.warning(f"Error with campaign_id, creating embedding without it: {column_error}")
                    embedding_record = OfferEmbedding(
                        offer_id=offer_id,
                        chunk_id=f"{offer_id}_{i}",
                        content=doc.page_content,
                        content_type=doc.metadata.get('type', 'combined'),
                        embedding=embedding,
                        meta_data=json.dumps(doc.metadata)
                    )
                
                self.session.add(embedding_record)
            
            await self.session.commit()
            logger.info(f"Added {len(documents)} embeddings for offer {offer_id}")
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error adding documents: {str(e)}")
            raise
    
    async def similarity_search(self, query: str, k: int = 5, filter_metadata: Dict = None) -> List[Dict]:
        """
        Perform similarity search using cosine similarity
        Returns top k most similar documents
        """
        start_time = datetime.now()
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            logger.info(f"Generated query embedding for: '{query}'")
            
            # First, check if the campaign_id column exists in the offer_embeddings table
            try:
                check_column_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'offer_embeddings' AND column_name = 'campaign_id'
                """)
                result = await self.session.execute(check_column_query)
                campaign_id_exists = result.fetchone() is not None
                logger.info(f"Campaign ID column exists: {campaign_id_exists}")
            except Exception as e:
                logger.warning(f"Error checking for campaign_id column: {e}")
                campaign_id_exists = False
            
            # Use raw SQL for more control over the query
            if campaign_id_exists:
                # Use full query with campaign_id
                query_sql = text("""
                SELECT 
                    oe.id, oe.offer_id, oe.chunk_id, oe.content, oe.content_type, 
                    oe.embedding, oe.created_at,
                    oe.campaign_id, oe.meta_data,
                    o.id AS o_id, o.title AS o_title, o.description AS o_description, 
                    o.terms_and_conditions AS o_terms_and_conditions,
                    o.coupon_code AS o_coupon_code, o.image_url AS o_image_url, 
                    o.offer_type AS o_offer_type, o.status AS o_status, 
                    o.url AS o_url, o.affiliate_url AS o_affiliate_url, 
                    o.categories AS o_categories, o.campaign_name AS o_campaign_name
                FROM offer_embeddings oe
                JOIN offers o ON oe.offer_id = o.id
                WHERE o.status = :status
                """)
            else:
                # Use simplified query without campaign_id
                query_sql = text("""
                SELECT 
                    oe.id, oe.offer_id, oe.chunk_id, oe.content, oe.content_type, 
                    oe.embedding, oe.created_at,
                    o.id AS o_id, o.title AS o_title, o.description AS o_description, 
                    o.terms_and_conditions AS o_terms_and_conditions,
                    o.coupon_code AS o_coupon_code, o.image_url AS o_image_url, 
                    o.offer_type AS o_offer_type, o.status AS o_status, 
                    o.url AS o_url, o.affiliate_url AS o_affiliate_url, 
                    o.categories AS o_categories, o.campaign_name AS o_campaign_name
                FROM offer_embeddings oe
                JOIN offers o ON oe.offer_id = o.id
                WHERE o.status = :status
                """)
            
            # Add category filter if provided
            params = {"status": filter_metadata.get('status', 'live') if filter_metadata else 'live'}
            if filter_metadata and 'category' in filter_metadata:
                query_sql = text(query_sql.text + " AND o.categories LIKE :category")
                params["category"] = f"%{filter_metadata['category']}%"
            
            logger.info(f"Executing query with params: {params}")
            
            # Execute query
            try:
                result = await self.session.execute(query_sql, params)
                embeddings_with_offers = result.fetchall()
                logger.info(f"Found {len(embeddings_with_offers)} embeddings matching query")
            except Exception as query_error:
                logger.error(f"Error executing similarity search query: {query_error}")
                # Ultimate fallback - get any embeddings and offers
                fallback_query = text("""
                SELECT 
                    oe.id, oe.offer_id, oe.chunk_id, oe.content, oe.content_type, 
                    oe.embedding, oe.created_at,
                    o.id AS o_id, o.title AS o_title, o.description AS o_description,
                    o.coupon_code AS o_coupon_code, o.image_url AS o_image_url, 
                    o.status AS o_status, 
                    o.url AS o_url, o.affiliate_url AS o_affiliate_url
                FROM offer_embeddings oe
                JOIN offers o ON oe.offer_id = o.id
                LIMIT 50
                """)
                
                result = await self.session.execute(fallback_query)
                embeddings_with_offers = result.fetchall()
                logger.warning(f"Using fallback query. Found {len(embeddings_with_offers)} embeddings")
                
            if not embeddings_with_offers:
                logger.warning("No embeddings found matching the query")
                return []
            
            # Calculate cosine similarity
            similarities = []
            for row in embeddings_with_offers:
                try:
                    # Access embedding data safely
                    embedding_data = None
                    for column_name in ['embedding', 'oe_embedding', 'embedding_1']:
                        if hasattr(row, column_name) and getattr(row, column_name) is not None:
                            embedding_data = getattr(row, column_name)
                            break
                    
                    if embedding_data is None:
                        logger.warning("No embedding data found in row")
                        continue
                        
                    # Convert to numpy array safely
                    stored_embedding = np.array(embedding_data)
                    query_embedding_np = np.array(query_embedding)
                    
                    # Calculate cosine similarity with error handling
                    try:
                        norm_stored = np.linalg.norm(stored_embedding)
                        norm_query = np.linalg.norm(query_embedding_np)
                        
                        if norm_stored > 0 and norm_query > 0:
                            cosine_sim = np.dot(stored_embedding, query_embedding_np) / (norm_stored * norm_query)
                        else:
                            cosine_sim = 0.0
                    except Exception as calc_error:
                        logger.warning(f"Error calculating similarity: {calc_error}")
                        cosine_sim = 0.5  # Default fallback similarity
                    
                    # Filter out results with low similarity
                    if cosine_sim < 0.2:  # Minimum threshold for similarity
                        continue
                    
                    # Create offer object with data from row
                    offer = type('Offer', (), {})()
                    for attr in ['id', 'offer_id', 'title', 'description', 'terms_and_conditions', 
                                'coupon_code', 'image_url', 'offer_type', 'status', 
                                'url', 'affiliate_url', 'categories', 'campaign_name']:
                        # Try different column naming patterns
                        for col_name in [attr, f'o_{attr}', f'{attr}_1']:
                            if hasattr(row, col_name):
                                setattr(offer, attr, getattr(row, col_name))
                                break
                        else:
                            # Set default if attribute not found
                            setattr(offer, attr, None)
                    
                    # Get content from row
                    content = None
                    for content_col in ['content', 'oe_content', 'content_1']:
                        if hasattr(row, content_col):
                            content = getattr(row, content_col)
                            break
                    
                    # Extract metadata safely
                    metadata = {}
                    for meta_col in ['meta_data', 'metadata', 'oe_meta_data']:
                        if hasattr(row, meta_col) and getattr(row, meta_col):
                            try:
                                metadata = json.loads(getattr(row, meta_col))
                                break
                            except (json.JSONDecodeError, TypeError):
                                pass
                    
                    logger.info(f"Found match: {offer.title} with similarity {cosine_sim:.3f}")
                    
                    similarities.append({
                        'similarity': float(cosine_sim),
                        'content': content or '',
                        'metadata': metadata,
                        'offer': offer,
                        'embedding_record': row
                    })
                    
                except Exception as row_error:
                    logger.warning(f"Error processing row for similarity: {row_error}")
                    continue
            
            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            top_results = similarities[:k]
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            logger.info(f"Similarity search completed in {processing_time:.2f} seconds, found {len(top_results)} results")
            
            return top_results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            # Return empty list in case of error
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            logger.error(f"Similarity search failed after {processing_time:.2f} seconds")
            return []

class RAGService:
    """
    Main RAG Service for accurate offer recommendations
    Uses LangChain for retrieval and generation
    """
    
    def __init__(self):
        # Initialize embedding model with lazy import
        from sentence_transformers import SentenceTransformer
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions
        
        # Initialize text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", "? ", "! ", ", "]
        )
        
        # Initialize LLM (you can switch between OpenAI, Ollama, or other models)
        self.llm = self._initialize_llm()
        
        # Custom prompt template for offer recommendations
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are an expert affiliate marketing assistant. Use the following offer information to provide accurate and helpful recommendations.

Context Information:
{context}

User Question: {question}

Instructions:
1. Analyze the user's question carefully
2. Use ONLY the provided offer information to answer
3. Recommend the most relevant offers based on the context
4. Include specific details like offer titles, descriptions, and any special terms
5. If no relevant offers are found, politely explain this
6. Always be helpful and accurate
7. Format your response in a user-friendly way

Answer:"""
        )
    
    def _initialize_llm(self):
        """Initialize the Language Model"""
        try:
            # Try OpenAI first (if API key is available)
            if os.getenv("OPENAI_API_KEY"):
                return ChatOpenAI(
                    model="gpt-3.5-turbo",
                    temperature=0.1,  # Low temperature for more accurate responses
                    max_tokens=500
                )
            else:
                # Fallback to a simple rule-based approach if no LLM is available
                return None
        except Exception as e:
            logger.warning(f"Could not initialize LLM: {str(e)}")
            return None
    
    async def process_offers_for_embeddings(self, session: AsyncSession, limit: int = None):
        """
        Process all offers and create embeddings for RAG
        This should be run after populating the database with offers
        """
        try:
            # Get all offers - use a more permissive query to include all offers
            # Don't filter by status to ensure we process all offers
            query = select(Offer)
            if limit:
                query = query.limit(limit)
            
            result = await session.execute(query)
            offers = result.scalars().all()
            
            logger.info(f"Processing {len(offers)} offers for embeddings")
            
            vector_store = PostgreSQLVectorStore(session, self.embedding_model)
            
            for offer in offers:
                # Check if embeddings already exist
                existing_check = await session.execute(
                    select(OfferEmbedding).where(OfferEmbedding.offer_id == offer.id)
                )
                if existing_check.scalars().first():
                    # Delete existing embeddings to regenerate with campaign info
                    await session.execute(
                        text(f"DELETE FROM offer_embeddings WHERE offer_id = {offer.id}")
                    )
                    await session.commit()
                
                # Create documents for different parts of the offer
                documents = self._create_offer_documents(offer)
                
                # Add to vector store with campaign_id
                await vector_store.add_documents(documents, offer.id, offer.campaign_id)
                
                logger.info(f"Processed offer {offer.id}: {offer.title}")
            
            logger.info("Completed processing offers for embeddings")
            
        except Exception as e:
            logger.error(f"Error processing offers for embeddings: {str(e)}")
            raise
    
    def _create_offer_documents(self, offer: Offer) -> List[Document]:
        """Create document chunks for an offer"""
        documents = []
        
        # Create metadata
        metadata = {
            'offer_id': offer.id,
            'title': offer.title,
            'categories': offer.categories,
            'status': offer.status,
            'offer_type': offer.offer_type,
            'campaign_id': offer.campaign_id,
            'campaign_name': getattr(offer, 'campaign_name', None)
        }
        
        # Create single combined document for better efficiency and context
        combined_text = f"Campaign: {getattr(offer, 'campaign_name', '') or ''}\n"
        combined_text += f"Title: {offer.title or ''}\n"
        combined_text += f"Description: {offer.description or ''}\n"
        combined_text += f"Category: {offer.categories or ''}\n"
        combined_text += f"Type: {offer.offer_type or ''}\n"
        if offer.coupon_code:
            combined_text += f"CouponCode: {offer.coupon_code}\n"
        
        documents.append(Document(
            page_content=combined_text,
            metadata={**metadata, 'type': 'combined'}
        ))
        
        return documents
    
    async def get_offer_recommendations(self, 
                                     query: str, 
                                     session: AsyncSession,
                                     top_k: int = 5,
                                     category_filter: str = None) -> Dict[str, Any]:
        """
        Get offer recommendations based on user query using RAG
        """
        try:
            # Create vector store
            vector_store = PostgreSQLVectorStore(session, self.embedding_model)
            
            # Prepare filters
            filter_metadata = {}
            if category_filter:
                filter_metadata['category'] = category_filter
            filter_metadata['status'] = 'live'  # Use 'live' instead of 'active'
            
            # Measure time for search operation
            import time
            start_time = time.time()
            
            # Perform similarity search
            similar_docs = await vector_store.similarity_search(
                query, k=top_k * 2, filter_metadata=filter_metadata
            )
            
            search_time = time.time() - start_time
            logger.info(f"Similarity search completed in {search_time:.2f} seconds, found {len(similar_docs)} results")
            
            if not similar_docs:
                return {
                    'answer': "I couldn't find any relevant offers for your query. Please try with different keywords.",
                    'offers': [],
                    'confidence': 0.0
                }
            
            # Extract unique offers
            unique_offers = {}
            context_parts = []
            
            for doc in similar_docs:
                offer = doc['offer']
                if offer.id not in unique_offers:
                    unique_offers[offer.id] = offer
                
                context_parts.append(f"Offer: {offer.title}")
                context_parts.append(f"Description: {offer.description}")
                if offer.coupon_code:
                    context_parts.append(f"Coupon: {offer.coupon_code}")
                context_parts.append(f"Category: {offer.categories}")
                context_parts.append("---")
            
            # Prepare context for LLM
            context = "\n".join(context_parts)
            
            # Generate response using LLM or rule-based approach
            if self.llm:
                # Use LangChain with LLM
                answer = await self._generate_llm_response(context, query)
            else:
                # Use rule-based response
                answer = self._generate_rule_based_response(query, list(unique_offers.values()))
            
            # Calculate confidence based on similarity scores
            avg_confidence = np.mean([doc['similarity'] for doc in similar_docs[:top_k]])
            
            return {
                'answer': answer,
                'offers': list(unique_offers.values())[:top_k],
                'confidence': float(avg_confidence),
                'total_found': len(similar_docs)
            }
            
        except Exception as e:
            logger.error(f"Error getting offer recommendations: {str(e)}")
            return {
                'answer': "I apologize, but I encountered an error while searching for offers. Please try again.",
                'offers': [],
                'confidence': 0.0
            }
    
    async def _generate_llm_response(self, context: str, query: str) -> str:
        """Generate response using LLM"""
        try:
            prompt = self.prompt_template.format(context=context, question=query)
            response = await self.llm.agenerate([prompt])
            return response.generations[0][0].text.strip()
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return self._generate_rule_based_response(query, [])
    
    def _generate_rule_based_response(self, query: str, offers: List[Offer]) -> str:
        """Generate response using rule-based approach"""
        if not offers:
            return "I couldn't find any relevant offers for your query. Please try with different keywords like 'electronics', 'fashion', 'travel', etc."
        
        response = f"I found {len(offers)} relevant offers for your query:\n\n"
        
        for i, offer in enumerate(offers[:3], 1):  # Show top 3
            response += f"{i}. **{offer.title}**\n"
            if offer.description:
                # Truncate long descriptions
                desc = offer.description[:200] + "..." if len(offer.description) > 200 else offer.description
                response += f"   {desc}\n"
            if offer.coupon_code:
                response += f"   💰 Coupon Code: {offer.coupon_code}\n"
            response += "\n"
        
        if len(offers) > 3:
            response += f"And {len(offers) - 3} more offers available!"
        
        return response

# Initialize global RAG service
rag_service = RAGService()
