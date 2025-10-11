"""
Admin Image Upload Controller
Allows admins to upload images and get URLs for use in the website
"""

import os
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.database import UploadedImage
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Configuration
UPLOAD_DIR = Path("static/images/uploads")
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Create upload directory if it doesn't exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return Path(filename).suffix.lower()

def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename to prevent collisions"""
    ext = get_file_extension(original_filename)
    unique_id = uuid.uuid4().hex[:12]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{unique_id}{ext}"

def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return get_file_extension(filename) in ALLOWED_EXTENSIONS

@router.get("/admin/images", response_class=HTMLResponse)
async def admin_images_page(request: Request):
    """Admin page for image uploads"""
    return templates.TemplateResponse("admin_images.html", {"request": request})

@router.post("/admin/api/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    description: str = None,
    db: Session = Depends(get_db)
):
    """
    Upload an image and return its URL
    """
    try:
        # Validate file extension
        if not is_allowed_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Check file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Generate unique filename
        unique_filename = generate_unique_filename(file.filename)
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Generate URL
        # Get the base URL from request or use a default
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        image_url = f"{base_url}/static/images/uploads/{unique_filename}"
        
        # Save to database
        db_image = UploadedImage(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=str(file_path),
            url=image_url,
            file_size=file_size,
            mime_type=file.content_type,
            description=description
        )
        
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        
        logger.info(f"Image uploaded successfully: {unique_filename}")
        
        return JSONResponse(content={
            "success": True,
            "message": "Image uploaded successfully",
            "data": {
                "id": db_image.id,
                "filename": db_image.filename,
                "original_filename": db_image.original_filename,
                "url": db_image.url,
                "file_size": db_image.file_size,
                "mime_type": db_image.mime_type,
                "uploaded_at": db_image.uploaded_at.isoformat(),
                "description": db_image.description
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")

@router.get("/admin/api/images")
async def get_uploaded_images(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get list of all uploaded images
    """
    try:
        images = db.query(UploadedImage).order_by(
            UploadedImage.uploaded_at.desc()
        ).offset(skip).limit(limit).all()
        
        total_count = db.query(UploadedImage).count()
        
        return JSONResponse(content={
            "success": True,
            "total": total_count,
            "images": [
                {
                    "id": img.id,
                    "filename": img.filename,
                    "original_filename": img.original_filename,
                    "url": img.url,
                    "file_size": img.file_size,
                    "mime_type": img.mime_type,
                    "uploaded_at": img.uploaded_at.isoformat(),
                    "description": img.description
                }
                for img in images
            ]
        })
        
    except Exception as e:
        logger.error(f"Error fetching images: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching images: {str(e)}")

@router.delete("/admin/api/images/{image_id}")
async def delete_image(image_id: int, db: Session = Depends(get_db)):
    """
    Delete an uploaded image
    """
    try:
        # Find image in database
        image = db.query(UploadedImage).filter(UploadedImage.id == image_id).first()
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Delete physical file
        file_path = Path(image.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # Delete from database
        db.delete(image)
        db.commit()
        
        logger.info(f"Image deleted successfully: {image.filename}")
        
        return JSONResponse(content={
            "success": True,
            "message": "Image deleted successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting image: {str(e)}")

@router.put("/admin/api/images/{image_id}")
async def update_image_description(
    image_id: int,
    description: str,
    db: Session = Depends(get_db)
):
    """
    Update image description
    """
    try:
        image = db.query(UploadedImage).filter(UploadedImage.id == image_id).first()
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        image.description = description
        db.commit()
        db.refresh(image)
        
        return JSONResponse(content={
            "success": True,
            "message": "Description updated successfully",
            "data": {
                "id": image.id,
                "description": image.description
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating image: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating image: {str(e)}")

@router.get("/admin/api/images/stats")
async def get_upload_stats(db: Session = Depends(get_db)):
    """
    Get statistics about uploaded images
    """
    try:
        from sqlalchemy import func
        
        total_images = db.query(func.count(UploadedImage.id)).scalar()
        total_size = db.query(func.sum(UploadedImage.file_size)).scalar() or 0
        
        # Get recent uploads (last 7 days)
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_uploads = db.query(func.count(UploadedImage.id)).filter(
            UploadedImage.uploaded_at >= week_ago
        ).scalar()
        
        return JSONResponse(content={
            "success": True,
            "stats": {
                "total_images": total_images,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "recent_uploads": recent_uploads,
                "upload_directory": str(UPLOAD_DIR)
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")
