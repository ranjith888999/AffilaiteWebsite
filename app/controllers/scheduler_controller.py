from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from datetime import datetime
import logging

from app.services.offers_sync_scheduler import offers_sync_scheduler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scheduler", tags=["Offers Sync Scheduler"])

@router.get("/status")
async def get_scheduler_status() -> Dict[str, Any]:
    """
    Get scheduler status information
    
    Returns:
        Dict containing scheduler status and next sync time
    """
    try:
        status = offers_sync_scheduler.get_scheduler_status()
        
        return {
            "success": True,
            "data": {
                "is_running": status["is_running"],
                "sync_time": status["sync_time"],
                "next_sync": status["next_sync"].isoformat() if status["next_sync"] else None,
                "thread_alive": status["thread_alive"],
                "status_checked_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")

@router.post("/start")
async def start_scheduler() -> Dict[str, Any]:
    """
    Start the offers sync scheduler
    
    Returns:
        Dict containing operation status
    """
    try:
        if offers_sync_scheduler.is_scheduler_running():
            return {
                "success": True,
                "message": "Scheduler is already running",
                "already_running": True
            }
        
        offers_sync_scheduler.start_scheduler()
        
        return {
            "success": True,
            "message": f"Scheduler started successfully - daily sync at {offers_sync_scheduler.sync_time}",
            "started_at": datetime.utcnow().isoformat(),
            "sync_time": offers_sync_scheduler.sync_time
        }
        
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")

@router.post("/stop")
async def stop_scheduler() -> Dict[str, Any]:
    """
    Stop the offers sync scheduler
    
    Returns:
        Dict containing operation status
    """
    try:
        if not offers_sync_scheduler.is_scheduler_running():
            return {
                "success": True,
                "message": "Scheduler is already stopped",
                "already_stopped": True
            }
        
        offers_sync_scheduler.stop_scheduler()
        
        return {
            "success": True,
            "message": "Scheduler stopped successfully",
            "stopped_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")

@router.post("/restart")
async def restart_scheduler() -> Dict[str, Any]:
    """
    Restart the offers sync scheduler
    
    Returns:
        Dict containing operation status
    """
    try:
        offers_sync_scheduler.stop_scheduler()
        offers_sync_scheduler.start_scheduler()
        
        return {
            "success": True,
            "message": f"Scheduler restarted successfully - daily sync at {offers_sync_scheduler.sync_time}",
            "restarted_at": datetime.utcnow().isoformat(),
            "sync_time": offers_sync_scheduler.sync_time
        }
        
    except Exception as e:
        logger.error(f"Error restarting scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart scheduler: {str(e)}")

@router.put("/sync-time")
async def update_sync_time(sync_time: str = Body(..., embed=True)) -> Dict[str, Any]:
    """
    Update the daily sync time
    
    Args:
        sync_time: New sync time in HH:MM format (e.g., "02:00")
        
    Request Body:
        {
            "sync_time": "02:00"
        }
        
    Returns:
        Dict containing operation status
    """
    try:
        offers_sync_scheduler.update_sync_time(sync_time)
        
        next_sync = offers_sync_scheduler.get_next_sync_time()
        
        return {
            "success": True,
            "message": f"Sync time updated to {sync_time}",
            "new_sync_time": sync_time,
            "next_sync": next_sync.isoformat() if next_sync else None,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating sync time: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update sync time: {str(e)}")

@router.get("/next-sync")
async def get_next_sync_time() -> Dict[str, Any]:
    """
    Get the next scheduled sync time
    
    Returns:
        Dict containing next sync time information
    """
    try:
        next_sync = offers_sync_scheduler.get_next_sync_time()
        
        return {
            "success": True,
            "data": {
                "next_sync": next_sync.isoformat() if next_sync else None,
                "sync_time": offers_sync_scheduler.sync_time,
                "is_running": offers_sync_scheduler.is_scheduler_running(),
                "checked_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting next sync time: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get next sync time: {str(e)}")

@router.post("/trigger-now")
async def trigger_sync_now() -> Dict[str, Any]:
    """
    Manually trigger a sync immediately (similar to scheduled sync)
    
    Returns:
        Dict containing operation status
    """
    try:
        from app.services.cuelinks_offers_service import cuelinks_offers_service
        
        # Run sync
        result = await cuelinks_offers_service.sync_offers_from_api(
            sync_type="manual_immediate",
            clear_data=True
        )
        
        return {
            "success": result["success"],
            "message": "Immediate sync completed",
            "sync_result": result,
            "triggered_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error triggering immediate sync: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger sync: {str(e)}")
