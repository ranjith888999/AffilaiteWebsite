from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime
import logging

from app.database import get_sync_db_session
from app.services.cuelinks_offers_service import cuelinks_offers_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/offers-sync", tags=["Offers Sync"])

@router.post("/manual-sync")
async def manual_sync_offers(
    background_tasks: BackgroundTasks,
    clear_data: bool = True,
    db: Session = Depends(get_sync_db_session)
) -> Dict[str, Any]:
    """
    Manually trigger offers sync from Cuelinks API
    
    Args:
        clear_data: Whether to clear existing data before sync (default: True)
        
    Returns:
        Dict containing sync status and details
    """
    try:
        # Add background task for the sync
        background_tasks.add_task(
            cuelinks_offers_service.sync_offers_from_api,
            sync_type="manual",
            clear_data=clear_data
        )
        
        return {
            "success": True,
            "message": "Manual sync started in background",
            "started_at": datetime.utcnow(),
            "clear_data": clear_data
        }
        
    except Exception as e:
        logger.error(f"Error starting manual sync: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start manual sync: {str(e)}")

@router.post("/sync-now")
async def sync_offers_now(
    clear_data: bool = True,
    db: Session = Depends(get_sync_db_session)
) -> Dict[str, Any]:
    """
    Synchronously sync offers from Cuelinks API (blocks until complete)
    
    Args:
        clear_data: Whether to clear existing data before sync (default: True)
        
    Returns:
        Dict containing sync results
    """
    try:
        result = await cuelinks_offers_service.sync_offers_from_api(
            sync_type="manual",
            clear_data=clear_data
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in sync now: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.get("/last-sync")
async def get_last_sync_info(db: Session = Depends(get_sync_db_session)) -> Dict[str, Any]:
    """
    Get information about the last sync operation
    
    Returns:
        Dict containing last sync details or null if no sync has been performed
    """
    try:
        last_sync = cuelinks_offers_service.get_last_sync_info(db)
        
        if last_sync:
            return {
                "success": True,
                "data": last_sync
            }
        else:
            return {
                "success": True,
                "data": None,
                "message": "No sync operations found"
            }
            
    except Exception as e:
        logger.error(f"Error getting last sync info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get last sync info: {str(e)}")

@router.get("/sync-history")
async def get_sync_history(
    limit: int = 10,
    db: Session = Depends(get_sync_db_session)
) -> Dict[str, Any]:
    """
    Get sync history
    
    Args:
        limit: Number of sync records to return (default: 10)
        
    Returns:
        Dict containing list of sync operations
    """
    try:
        if limit > 50:
            limit = 50  # Cap at 50 for performance
            
        history = cuelinks_offers_service.get_sync_history(db, limit)
        
        return {
            "success": True,
            "data": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting sync history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sync history: {str(e)}")

@router.get("/status")
async def get_sync_status(db: Session = Depends(get_sync_db_session)) -> Dict[str, Any]:
    """
    Get overall sync status and statistics
    
    Returns:
        Dict containing sync status and database statistics
    """
    try:
        from app.models.database import Campaign, Offer, OfferEmbedding
        
        # Get counts
        campaigns_count = db.query(Campaign).count()
        offers_count = db.query(Offer).count()
        embeddings_count = db.query(OfferEmbedding).count()
        
        # Get last sync info
        last_sync = cuelinks_offers_service.get_last_sync_info(db)
        
        return {
            "success": True,
            "data": {
                "database_counts": {
                    "campaigns": campaigns_count,
                    "offers": offers_count,
                    "embeddings": embeddings_count
                },
                "last_sync": last_sync,
                "embedding_model_loaded": cuelinks_offers_service.embedding_model is not None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")

@router.delete("/clear-data")
async def clear_offers_data(db: Session = Depends(get_sync_db_session)) -> Dict[str, Any]:
    """
    Clear all offers, campaigns, and embeddings data
    
    Returns:
        Dict containing operation status
    """
    try:
        cuelinks_offers_service.clear_existing_data(db)
        
        return {
            "success": True,
            "message": "All offers data cleared successfully",
            "cleared_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")

@router.get("/test-api")
async def test_cuelinks_api() -> Dict[str, Any]:
    """
    Test connectivity to Cuelinks API
    
    Returns:
        Dict containing API test results
    """
    try:
        # Test by fetching first page of offers
        result = await cuelinks_offers_service.fetch_offers_from_api(page=1, per_page=5)
        
        return {
            "success": True,
            "message": "Cuelinks API is accessible",
            "sample_data": {
                "total_count": result.get("total_count", 0),
                "offers_in_sample": len(result.get("offers", [])),
                "first_offer_title": result.get("offers", [{}])[0].get("title", "N/A") if result.get("offers") else "No offers"
            }
        }
        
    except Exception as e:
        logger.error(f"Error testing Cuelinks API: {e}")
        raise HTTPException(status_code=500, detail=f"API test failed: {str(e)}")
