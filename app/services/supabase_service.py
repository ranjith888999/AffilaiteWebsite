"""
Supabase service for additional Supabase-specific features
This complements the existing SQLAlchemy database setup
"""
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase client not installed. Install with: pip install supabase")

class SupabaseService:
    """Service for Supabase-specific operations"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        if SUPABASE_AVAILABLE:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client"""
        try:
            url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
            key = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
            
            if url and key:
                self.client = create_client(url, key)
                logger.info("Supabase client initialized successfully")
            else:
                logger.error("Supabase URL or ANON_KEY not found in environment variables")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
    
    def is_available(self) -> bool:
        """Check if Supabase client is available and initialized"""
        return SUPABASE_AVAILABLE and self.client is not None
    
    def test_connection(self) -> bool:
        """Test Supabase connection"""
        if not self.is_available():
            return False
        
        try:
            # Try to read from a system table to test connection
            response = self.client.table('information_schema.tables').select('table_name').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase connection test failed: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information using Supabase client"""
        if not self.is_available():
            return {"error": "Supabase client not available"}
        
        try:
            # Get basic database info
            response = self.client.rpc('version').execute()
            return {
                "status": "connected",
                "version": response.data if response.data else "Unknown",
                "client_available": True
            }
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {
                "status": "error",
                "error": str(e),
                "client_available": True
            }

# Global instance
supabase_service = SupabaseService()
