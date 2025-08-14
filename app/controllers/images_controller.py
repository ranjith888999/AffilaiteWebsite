import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pathlib import Path

router = APIRouter()

@router.get("/local-images")
async def get_local_images():
    """Get list of locally downloaded images"""
    try:
        images_dir = Path("static/images/downloaded")
        
        if not images_dir.exists():
            return JSONResponse(content=[])
        
        # Get all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        local_images = []
        
        for file_path in images_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                local_images.append(file_path.name)
        
        return JSONResponse(content=local_images)
        
    except Exception as e:
        print(f"Error getting local images: {e}")
        return JSONResponse(content=[])

@router.get("/image-stats")
async def get_image_stats():
    """Get statistics about downloaded images"""
    try:
        images_dir = Path("static/images/downloaded")
        
        if not images_dir.exists():
            return JSONResponse(content={
                "total_images": 0,
                "total_size_mb": 0,
                "status": "No downloaded images directory"
            })
        
        # Count files and calculate total size
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        total_files = 0
        total_size = 0
        
        for file_path in images_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                total_files += 1
                total_size += file_path.stat().st_size
        
        return JSONResponse(content={
            "total_images": total_files,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "status": "success"
        })
        
    except Exception as e:
        print(f"Error getting image stats: {e}")
        return JSONResponse(content={
            "total_images": 0,
            "total_size_mb": 0,
            "status": f"Error: {str(e)}"
        })
