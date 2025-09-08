import asyncio
import schedule
import time
from datetime import datetime, timedelta
from threading import Thread
import logging

from app.services.cuelinks_offers_service import cuelinks_offers_service

logger = logging.getLogger(__name__)

class OffersSyncScheduler:
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        self.sync_time = "02:00"  # 2 AM daily sync
        
    def start_scheduler(self):
        """Start the scheduler in a separate thread"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
            
        self.is_running = True
        
        # Schedule daily sync at 2 AM
        schedule.clear()
        schedule.every().day.at(self.sync_time).do(self._run_scheduled_sync)
        
        # Start scheduler thread
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info(f"Offers sync scheduler started - daily sync at {self.sync_time}")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
            
        logger.info("Offers sync scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)
    
    def _run_scheduled_sync(self):
        """Run the scheduled sync"""
        try:
            logger.info("Starting scheduled offers sync...")
            
            # Run async sync in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    cuelinks_offers_service.sync_offers_from_api(
                        sync_type="auto",
                        clear_data=True
                    )
                )
                
                if result["success"]:
                    logger.info(f"Scheduled sync completed successfully: {result['message']}")
                else:
                    logger.error(f"Scheduled sync failed: {result.get('error', 'Unknown error')}")
                    
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error in scheduled sync: {e}")
    
    def get_next_sync_time(self) -> datetime:
        """Get the next scheduled sync time"""
        if not self.is_running:
            return None
            
        next_job = schedule.next_run()
        return next_job
    
    def update_sync_time(self, new_time: str):
        """Update the sync time (format: HH:MM)"""
        try:
            # Validate time format
            datetime.strptime(new_time, "%H:%M")
            
            self.sync_time = new_time
            
            # Reschedule if running
            if self.is_running:
                schedule.clear()
                schedule.every().day.at(self.sync_time).do(self._run_scheduled_sync)
                logger.info(f"Sync time updated to {self.sync_time}")
                
        except ValueError:
            raise ValueError("Invalid time format. Use HH:MM format (e.g., '02:00')")
    
    def is_scheduler_running(self) -> bool:
        """Check if scheduler is running"""
        return self.is_running
    
    def get_scheduler_status(self) -> dict:
        """Get scheduler status information"""
        return {
            "is_running": self.is_running,
            "sync_time": self.sync_time,
            "next_sync": self.get_next_sync_time(),
            "thread_alive": self.scheduler_thread.is_alive() if self.scheduler_thread else False
        }

# Global scheduler instance
offers_sync_scheduler = OffersSyncScheduler()

# Auto-start scheduler when module is imported
def start_scheduler_on_startup():
    """Start scheduler on application startup"""
    try:
        offers_sync_scheduler.start_scheduler()
        logger.info("Offers sync scheduler auto-started")
    except Exception as e:
        logger.error(f"Failed to auto-start scheduler: {e}")

# Call on import
start_scheduler_on_startup()
