from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging
import json

from app.database import get_sync_db_session
from app.services.semantic_chat_service import semantic_chat_service
from app.models.database import ChatFeedback

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/chat", tags=["Chat V2"])

class UserInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None

class ChatQuery(BaseModel):
    message: str
    session_id: str
    user_info: Optional[UserInfo] = None

class FeedbackPayload(BaseModel):
    session_id: str
    user_message: str
    bot_response: str  # The full JSON response
    feedback_type: str  # 'like' or 'dislike'
    offer_id: int

@router.post("/")
async def handle_chat(query: ChatQuery, request: Request, db: Session = Depends(get_sync_db_session)):
    """
    Handle user chat query using semantic search with personalization
    """
    if not query.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        # Extract user info from session cookie if not provided
        user_name = None
        user_first_name = None
        
        if query.user_info and query.user_info.name:
            user_name = query.user_info.name
            # Extract first name from full name
            user_first_name = user_name.split()[0] if user_name else None
        else:
            # Try to get from session cookie
            try:
                user_session = request.cookies.get("user_session")
                if user_session:
                    session_data = json.loads(user_session)
                    user_name = session_data.get('name')
                    user_first_name = user_name.split()[0] if user_name else None
            except:
                pass
        
        results = await semantic_chat_service.semantic_search(
            query=query.message,
            db=db,
            user_first_name=user_first_name,
            fromloc="chat_endpoint",
            session_id=query.session_id
        )
        
        return {
            "success": True,
            "session_id": query.session_id,
            "user_message": query.message,
            "response": results,
            "user_name": user_first_name  # Send back for frontend confirmation
        }
        
    except Exception as e:
        logger.error(f"Error in chat handler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat message: {str(e)}")

@router.post("/feedback")
async def handle_feedback(payload: FeedbackPayload, db: Session = Depends(get_sync_db_session)):
    """
    Handle user feedback for a specific offer
    """
    try:
        feedback = ChatFeedback(
            session_id=payload.session_id,
            user_message=payload.user_message,
            bot_response=payload.bot_response,
            feedback_type=payload.feedback_type,
            offer_id=payload.offer_id,
            feedback_text=f"Feedback on offer {payload.offer_id}"
        )
        db.add(feedback)
        db.commit()
        
        return {"success": True, "message": "Feedback received"}
        
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {str(e)}")

@router.get("/history")
async def get_chat_history(session_id: str, db: Session = Depends(get_sync_db_session)):
    """
    Get chat history for a session (Not fully implemented, placeholder)
    """
    return {"message": "Chat history endpoint is a placeholder."}
