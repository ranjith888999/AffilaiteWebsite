from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.semantic_search_service import semantic_search_service
from typing import Dict, Any, Optional
from pydantic import BaseModel
import uuid
import time
from datetime import datetime
import logging
import asyncio

from app.models.database import ChatMessage, ChatFeedback
from app.database import get_db, get_async_db

router = APIRouter()
logger = logging.getLogger(__name__)

# Request models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatOffersRequest(BaseModel):
    query: str
    campaign_id: Optional[int] = None

class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    feedback_type: str
    feedback_text: Optional[str] = None


# Lazy import and initialization of semantic service
_semantic_search_service = None

def get_semantic_search_service():
    """Lazy load the semantic search service only when needed"""
    global _semantic_search_service
    if _semantic_search_service is None:
        logger.info("🔄 Initializing Semantic Search service...")
        try:
            _semantic_search_service = semantic_search_service
            logger.info("✅ Semantic Search service ready")
        except Exception as e:
            logger.error(f"❌ Error initializing Semantic Search service: {str(e)}")
            return None
    return _semantic_search_service

@router.post("/chat")
async def chat_with_offers(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat endpoint using semantic search for fast and accurate results.
    """
    try:
        start_time = time.time()
        
        user_message = request.message.strip()
        session_id = request.session_id or str(uuid.uuid4())
        
        if not user_message:
            return {
                "response": "Please provide a message to get offer recommendations.",
                "session_id": session_id,
                "offers": []
            }
        
        logger.info(f"🧠 Processing chat query with Semantic Search: '{user_message}'")
        
        search_service = get_semantic_search_service()
        
        if search_service is None:
            raise HTTPException(status_code=503, detail="Search service is currently unavailable.")

        offers, bot_response = search_service.search(user_message, top_k=10)
        
        processing_time = time.time() - start_time
        logger.info(f"✅ Semantic search completed in {processing_time:.3f} seconds.")

        # Save chat message to the database
        try:
            chat_message = ChatMessage(
                session_id=session_id,
                message=user_message,
                response=bot_response,
                offers_retrieved=len(offers),
                processing_time=processing_time,
                source="semantic_search"
            )
            db.add(chat_message)
            db.commit()
        except Exception as db_error:
            logger.error(f"Failed to save chat message: {db_error}")
            db.rollback()

        return {
            "response": bot_response,
            "session_id": session_id,
            "offers": offers,
            "processing_time": round(processing_time, 3)
        }
        
    except Exception as e:
        logger.error(f"Error in /chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred.")


@router.post("/chat/with-offers", deprecated=True)
async def chat_with_offers_legacy(request: ChatOffersRequest, db: Session = Depends(get_db)):
    """
    This is a deprecated endpoint. Use /chat instead.
    """
    return {"message": "This endpoint is deprecated. Please use the /chat endpoint."}

    #         description = offer.get('description', '')
    #         if description and len(description) > 120:
    #             description = description[:120] + "..."
            
    #         formatted_offers.append({
    #             "id": offer.get('id'),
    #             "title": offer.get('title', 'Special Offer'),
    #             "description": description,
    #             "image_url": offer.get('image_url', '/static/images/placeholder_small.jpg'),
    #             "categories": offer.get('categories', ''),
    #             "coupon_code": offer.get('coupon_code', ''),
    #             "affiliate_url": offer.get('affiliate_url', ''),
    #             "website_url": offer.get('url', ''),
    #             "similarity": round(offer.get('similarity', 0.0), 3),
    #             "campaign_name": offer.get('campaign_name', '')  # Include campaign name
    #         })
        
    #     # Save the chat interaction to the database
    #     try:
    #         chat_message = ChatMessage(
    #             session_id=session_id,
    #             user_message=user_message,
    #             bot_response=bot_response,
    #             offer_count=len(offers),
    #             timestamp=datetime.utcnow()
    #         )
    #         db.add(chat_message)
    #         db.commit()
    #     except Exception as db_error:
    #         logger.error(f"Error saving chat message: {db_error}")
    #         db.rollback()
            
    #     processing_time = time.time() - start_time
    #     logger.info(f"⚡ Total chat processing time: {processing_time:.3f}s")
        
    #     return {
    #         "response": bot_response,
    #         "session_id": session_id,
    #         "offers": formatted_offers,
    #         "total_found": len(offers),
    #         "processing_time": round(processing_time, 3)
    #     }
        
    # except Exception as e:
    #     logger.error(f"❌ Chat error: {str(e)}")
    #     return {
    #         "response": f"🔍 I'm searching for '{user_message}' offers with advanced embedding technology. Please try again in a moment!",
    #         "session_id": session_id,
    #         "offers": [],
    #         "error": "search_timeout"
    #     }

@router.post("/chat/with-offers")
async def chat_with_offers_api(request: ChatOffersRequest, db: Session = Depends(get_db)):
    """
    Simplified API endpoint for chat with offers (no session management)
    """
    start_time = time.time()
    user_query = request.query.strip()
    
    if not user_query:
        return {
            "response": "Please provide a query to search for offers.",
            "offers": []
        }
    
    logger.info(f"⚡ Processing offers query: '{user_query}'")
    
    try:
        # Use ultra-fast service directly for speed
        from app.services.ultra_fast_service import search_offers_ultra_fast, generate_response_ultra_fast
        
        # Get relevant offers using ultra-fast search - limit to exactly 5 results
        offers = search_offers_ultra_fast(user_query, limit=5)
        bot_response = generate_response_ultra_fast(user_query, offers)
        
        # Log performance information
        logger.info(f"Found {len(offers)} offers in {time.time() - start_time:.3f} seconds")
        
        # Format offers for response
        formatted_offers = []
        for offer in offers:
            # Truncate description for better display
            description = offer.get('description', '')
            if description and len(description) > 120:
                description = description[:120] + "..."
            
            formatted_offers.append({
                "id": offer.get('id'),
                "title": offer.get('title', 'Special Offer'),
                "description": description,
                "image_url": offer.get('image_url', '/static/images/placeholder_small.jpg'),
                "categories": offer.get('categories', ''),
                "coupon_code": offer.get('coupon_code', ''),
                "affiliate_url": offer.get('affiliate_url', ''),
                "website_url": offer.get('url', ''),
                "similarity": round(offer.get('similarity', 0.0), 3),
                "campaign_name": offer.get('campaign_name', '')
            })
        
        processing_time = time.time() - start_time
        logger.info(f"⚡ Offers API processing time: {processing_time:.3f}s")
        
        return {
            "response": bot_response,
            "offers": formatted_offers,
            "processing_time": round(processing_time, 3)
        }
        
    except Exception as e:
        logger.error(f"❌ Offers API error: {str(e)}")
        return {
            "response": "I'm sorry, I couldn't find offers matching your query. Please try with different keywords.",
            "offers": [],
            "error": "search_error"
        }

@router.get("/chat/history/{session_id}")
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get chat history for a session"""
    try:
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp.desc()).limit(50).all()
        
        return {
            "session_id": session_id,
            "messages": [
                {
                    "user_message": msg.user_message,
                    "bot_response": msg.bot_response,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in reversed(messages)
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/feedback")
async def submit_chat_feedback(
    feedback_data: dict,
    db: Session = Depends(get_db)
):
    """Submit feedback for a chat conversation"""
    try:
        session_id = feedback_data.get("session_id")
        user_message = feedback_data.get("user_message", "")
        bot_response = feedback_data.get("bot_response", "")
        feedback_type = feedback_data.get("feedback_type")  # 'like', 'dislike', 'feedback'
        feedback_text = feedback_data.get("feedback_text", "")
        offer_id = feedback_data.get("offer_id")  # Track specific offer feedback
        
        if not session_id or not feedback_type:
            raise HTTPException(status_code=400, detail="session_id and feedback_type are required")
        
        if feedback_type not in ['like', 'dislike', 'feedback']:
            raise HTTPException(status_code=400, detail="feedback_type must be 'like', 'dislike', or 'feedback'")
        
        # Create feedback record
        feedback = ChatFeedback(
            session_id=session_id,
            user_message=user_message,
            bot_response=bot_response,
            feedback_type=feedback_type,
            feedback_text=feedback_text if feedback_text else None,
            offer_id=offer_id if offer_id else None,
            timestamp=datetime.utcnow()
        )
        
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        
        logger.info(f"Feedback submitted: {feedback_type} for session {session_id}")
        
        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "feedback_id": feedback.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/feedback/stats")
async def get_feedback_stats(db: Session = Depends(get_db)):
    """Get overall feedback statistics"""
    try:
        from sqlalchemy import func
        
        # Get feedback counts by type
        feedback_stats = db.query(
            ChatFeedback.feedback_type,
            func.count(ChatFeedback.id).label('count')
        ).group_by(ChatFeedback.feedback_type).all()
        
        # Get total conversations with feedback
        total_sessions_with_feedback = db.query(
            func.count(func.distinct(ChatFeedback.session_id))
        ).scalar()
        
        # Get recent feedback
        recent_feedback = db.query(ChatFeedback).filter(
            ChatFeedback.feedback_text.isnot(None)
        ).order_by(ChatFeedback.timestamp.desc()).limit(10).all()
        
        stats = {
            "feedback_counts": {stat.feedback_type: stat.count for stat in feedback_stats},
            "total_sessions_with_feedback": total_sessions_with_feedback,
            "recent_feedback": [
                {
                    "feedback_type": fb.feedback_type,
                    "feedback_text": fb.feedback_text,
                    "timestamp": fb.timestamp.isoformat(),
                    "user_message": fb.user_message[:100] + "..." if len(fb.user_message) > 100 else fb.user_message
                }
                for fb in recent_feedback
            ]
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting feedback stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/feedback/offers")
async def get_offer_feedback_stats(db: Session = Depends(get_db)):
    """Get feedback statistics by offer"""
    try:
        from sqlalchemy import func
        
        # Get feedback counts by offer
        offer_feedback = db.query(
            ChatFeedback.offer_id,
            ChatFeedback.feedback_type,
            func.count(ChatFeedback.id).label('count')
        ).filter(
            ChatFeedback.offer_id.isnot(None)
        ).group_by(
            ChatFeedback.offer_id, 
            ChatFeedback.feedback_type
        ).all()
        
        # Get offer titles for context
        from app.models.database import Offer
        offer_details = db.query(Offer.id, Offer.title).filter(
            Offer.id.in_([fb.offer_id for fb in offer_feedback])
        ).all()
        
        offer_titles = {offer.id: offer.title for offer in offer_details}
        
        # Organize data by offer
        offer_stats = {}
        for feedback in offer_feedback:
            offer_id = feedback.offer_id
            if offer_id not in offer_stats:
                offer_stats[offer_id] = {
                    'offer_id': offer_id,
                    'offer_title': offer_titles.get(offer_id, 'Unknown Offer'),
                    'feedback_counts': {'like': 0, 'dislike': 0, 'feedback': 0},
                    'total_feedback': 0
                }
            
            offer_stats[offer_id]['feedback_counts'][feedback.feedback_type] = feedback.count
            offer_stats[offer_id]['total_feedback'] += feedback.count
        
        # Sort by total feedback (most feedback first)
        sorted_offers = sorted(
            offer_stats.values(), 
            key=lambda x: x['total_feedback'], 
            reverse=True
        )
        
        return {
            "offer_feedback_stats": sorted_offers,
            "total_offers_with_feedback": len(offer_stats)
        }
        
    except Exception as e:
        logger.error(f"Error getting offer feedback stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
