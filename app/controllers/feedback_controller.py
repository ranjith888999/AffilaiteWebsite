from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.database import get_db
from app.models.database import UserFeedback, User
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import logging

router = APIRouter(prefix="/api/feedback", tags=["feedback"])
logger = logging.getLogger(__name__)

# Pydantic models for request validation
class FeedbackCreate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    feedback_type: str
    page_url: str
    rating: Optional[int] = None
    message: str
    browser_info: Optional[str] = None

class FeedbackUpdate(BaseModel):
    status: Optional[str] = None
    admin_notes: Optional[str] = None

@router.post("/submit")
async def submit_feedback(
    feedback: FeedbackCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Submit user feedback"""
    try:
        # Validate rating if provided
        if feedback.rating is not None and (feedback.rating < 1 or feedback.rating > 5):
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        # Validate feedback type
        valid_types = ['bug', 'feature', 'general', 'complaint', 'appreciation']
        if feedback.feedback_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid feedback type. Must be one of: {', '.join(valid_types)}")
        
        # Get user_id from session if logged in
        user_id = None
        session_data = request.session.get("user")
        if session_data:
            user_id = session_data.get("id")
        
        # Create feedback entry
        db_feedback = UserFeedback(
            name=feedback.name,
            email=feedback.email,
            feedback_type=feedback.feedback_type,
            page_url=feedback.page_url,
            rating=feedback.rating,
            message=feedback.message,
            browser_info=feedback.browser_info,
            user_id=user_id,
            status='new'
        )
        
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        
        # Send email notification
        try:
            from app.services.email_service import send_feedback_notification
            send_feedback_notification(db_feedback)
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            # Don't fail the request if email sending fails
        
        return {
            "success": True,
            "message": "Thank you for your feedback! We appreciate your input.",
            "feedback_id": db_feedback.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@router.get("/list")
async def get_feedback_list(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    feedback_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get list of all feedback (admin endpoint)"""
    try:
        query = db.query(UserFeedback)
        
        # Apply filters
        if status:
            query = query.filter(UserFeedback.status == status)
        if feedback_type:
            query = query.filter(UserFeedback.feedback_type == feedback_type)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        feedbacks = query.order_by(desc(UserFeedback.created_at)).offset(skip).limit(limit).all()
        
        # Convert to dict
        feedback_list = []
        for fb in feedbacks:
            feedback_list.append({
                "id": fb.id,
                "name": fb.name,
                "email": fb.email,
                "feedback_type": fb.feedback_type,
                "page_url": fb.page_url,
                "rating": fb.rating,
                "message": fb.message,
                "status": fb.status,
                "admin_notes": fb.admin_notes,
                "created_at": fb.created_at.isoformat() if fb.created_at else None,
                "browser_info": fb.browser_info
            })
        
        return {
            "success": True,
            "total": total,
            "feedbacks": feedback_list
        }
        
    except Exception as e:
        logger.error(f"Error fetching feedback list: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch feedback")

@router.get("/stats")
async def get_feedback_stats(db: Session = Depends(get_db)):
    """Get feedback statistics (admin endpoint)"""
    try:
        total_feedback = db.query(func.count(UserFeedback.id)).scalar()
        
        # Count by status
        status_counts = db.query(
            UserFeedback.status,
            func.count(UserFeedback.id)
        ).group_by(UserFeedback.status).all()
        
        # Count by type
        type_counts = db.query(
            UserFeedback.feedback_type,
            func.count(UserFeedback.id)
        ).group_by(UserFeedback.feedback_type).all()
        
        # Average rating
        avg_rating = db.query(func.avg(UserFeedback.rating)).filter(
            UserFeedback.rating.isnot(None)
        ).scalar()
        
        return {
            "success": True,
            "total_feedback": total_feedback,
            "status_breakdown": {status: count for status, count in status_counts},
            "type_breakdown": {type_: count for type_, count in type_counts},
            "average_rating": round(float(avg_rating), 2) if avg_rating else None
        }
        
    except Exception as e:
        logger.error(f"Error fetching feedback stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stats")

@router.patch("/{feedback_id}")
async def update_feedback(
    feedback_id: int,
    update: FeedbackUpdate,
    db: Session = Depends(get_db)
):
    """Update feedback status or admin notes (admin endpoint)"""
    try:
        feedback = db.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()
        
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        # Update fields
        if update.status is not None:
            valid_statuses = ['new', 'reviewed', 'resolved', 'closed']
            if update.status not in valid_statuses:
                raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
            feedback.status = update.status
        
        if update.admin_notes is not None:
            feedback.admin_notes = update.admin_notes
        
        feedback.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": "Feedback updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to update feedback")

@router.delete("/{feedback_id}")
async def delete_feedback(
    feedback_id: int,
    db: Session = Depends(get_db)
):
    """Delete feedback (admin endpoint)"""
    try:
        feedback = db.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()
        
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        db.delete(feedback)
        db.commit()
        
        return {
            "success": True,
            "message": "Feedback deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete feedback")
