"""
Health and monitoring controller for system status
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db, get_pool_status, db_available
import logging
import psutil
import os
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/health", tags=["Health & Monitoring"])


@router.get("/status")
async def health_check(db: Session = Depends(get_db)):
    """
    Overall health check endpoint
    """
    try:
        # Check database connectivity
        db_status = "healthy" if db_available and db is not None else "unhealthy"
        
        # Get pool status
        pool_info = get_pool_status()
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        return {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "status": db_status,
                "pool": pool_info
            },
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024)
            },
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/pool")
async def get_connection_pool_status():
    """
    Get detailed connection pool status
    """
    try:
        pool_info = get_pool_status()
        
        # Add recommendations
        if pool_info.get("status") == "healthy":
            checked_out = pool_info.get("checked_out", 0)
            max_conn = pool_info.get("max_connections", 0)
            
            if max_conn > 0:
                utilization = (checked_out / max_conn) * 100
                pool_info["utilization_percent"] = round(utilization, 2)
                
                if utilization > 90:
                    pool_info["warning"] = "Pool utilization above 90% - consider increasing pool size"
                elif utilization > 75:
                    pool_info["info"] = "Pool utilization above 75% - monitor closely"
        
        return pool_info
    except Exception as e:
        logger.error(f"Pool status error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/db-test")
async def test_database_connection(db: Session = Depends(get_db)):
    """
    Test database connection with a simple query
    """
    if not db:
        return {
            "status": "error",
            "message": "Database connection not available"
        }
    
    try:
        # Execute a simple query
        result = db.execute("SELECT 1 as test").fetchone()
        return {
            "status": "success",
            "message": "Database connection successful",
            "test_result": result[0] if result else None
        }
    except Exception as e:
        logger.error(f"Database test error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
