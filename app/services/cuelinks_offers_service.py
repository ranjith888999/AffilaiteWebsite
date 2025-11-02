import asyncio
import httpx
import os
import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

# Delayed import approach - only import when actually needed
EMBEDDINGS_AVAILABLE = False
SentenceTransformer = None

def _import_sentence_transformers():
    """Import sentence transformers only when needed"""
    global EMBEDDINGS_AVAILABLE, SentenceTransformer
    if SentenceTransformer is None:
        try:
            from sentence_transformers import SentenceTransformer as ST
            SentenceTransformer = ST
            EMBEDDINGS_AVAILABLE = True
            print("✅ sentence-transformers loaded successfully")
        except ImportError as e:
            EMBEDDINGS_AVAILABLE = False
            SentenceTransformer = None
            print(f"⚠️ Warning: sentence-transformers not available: {e}")
        except Exception as e:
            EMBEDDINGS_AVAILABLE = False
            SentenceTransformer = None
            print(f"⚠️ Warning: Error loading sentence-transformers: {e}")
    return EMBEDDINGS_AVAILABLE

from app.database import get_sync_db_session, get_async_db_session
from app.models.database import Campaign, Offer, OfferEmbedding, OfferSyncLog

logger = logging.getLogger(__name__)

class CuelinksOffersService:
    def __init__(self):
        self.api_key = os.getenv("CUELINKS_API_KEY")
        self.base_url = os.getenv("CUELINKS_BASE_URL", "https://www.cuelinks.com/api/v2")
        self.headers = {
            "Authorization": f"Token token={self.api_key}",
            "Content-Type": "application/json"
        }
        self.embedding_model = None
        
    def get_embedding_model(self):
        """Lazy load the embedding model"""
        if not _import_sentence_transformers():
            return None
            
        if self.embedding_model is None:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Embedding model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                self.embedding_model = None
        return self.embedding_model
    
    def generate_simple_embedding(self, text: str) -> List[float]:
        """Generate a simple hash-based embedding as fallback"""
        import hashlib
        
        # Create a simple 384-dimension vector based on text hash
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to float vector
        embedding = []
        for i in range(0, min(len(hash_bytes), 48), 1):  # Use 48 bytes for 384 dimensions (8 dims per byte)
            byte_val = hash_bytes[i]
            for bit in range(8):
                embedding.append(float((byte_val >> bit) & 1) - 0.5)  # Normalize to [-0.5, 0.5]
        
        # Pad to 384 dimensions if needed
        while len(embedding) < 384:
            embedding.append(0.0)
            
        return embedding[:384]
    
    async def fetch_offers_from_api(self, page: int = 1, per_page: int = 100) -> Dict[str, Any]:
        """Fetch offers from Cuelinks API with pagination"""
        url = f"{self.base_url}/offers.json"
        
        # Set date range - get offers that are currently live or starting soon
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        
        params = {
            "page": page,
            "per_page": per_page,
            "start_date": start_date,
            "end_date": end_date
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching offers from API: {e}")
            raise
    
    async def fetch_all_offers_from_api(self) -> List[Dict[str, Any]]:
        """Fetch all offers from API with pagination"""
        all_offers = []
        page = 1
        per_page = 100
        
        logger.info("Starting to fetch all offers from Cuelinks API...")
        
        while True:
            try:
                result = await self.fetch_offers_from_api(page=page, per_page=per_page)
                offers = result.get('offers', [])
                
                if not offers:
                    break
                    
                all_offers.extend(offers)
                logger.info(f"Fetched page {page}: {len(offers)} offers (Total so far: {len(all_offers)})")
                
                # Check if we have more pages
                total_count = result.get('total_count', 0)
                if len(all_offers) >= total_count:
                    break
                    
                page += 1
                
                # Small delay to be respectful to the API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error fetching offers page {page}: {e}")
                break
        
        logger.info(f"Completed fetching offers. Total retrieved: {len(all_offers)}")
        return all_offers
    
    def clear_existing_data(self, db: Session):
        """Clear existing data from campaigns, offers, and offer_embeddings tables"""
        logger.info("Clearing existing data from database...")
        
        try:
            # Delete in correct order to respect foreign key constraints
            db.execute(text("DELETE FROM offer_embeddings"))
            db.execute(text("DELETE FROM offers"))
            db.execute(text("DELETE FROM campaigns"))
            db.commit()
            logger.info("Successfully cleared existing data")
        except Exception as e:
            db.rollback()
            logger.error(f"Error clearing existing data: {e}")
            raise
    
    def process_and_store_offers(self, offers_data: List[Dict[str, Any]], db: Session) -> int:
        """Process and store offers in the database"""
        logger.info(f"Processing and storing {len(offers_data)} offers...")
        
        campaigns_dict = {}
        offers_processed = 0
        
        try:
            for offer_data in offers_data:
                try:
                    # Process campaign
                    campaign_id = offer_data.get('camapign_id')  # Note: API has typo in field name
                    campaign_name = offer_data.get('campaign', '')
                    
                    if campaign_id and campaign_id not in campaigns_dict:
                        # Create campaign if not exists
                        campaign = Campaign(
                            campaign_id=campaign_id,
                            name=campaign_name,
                            description=f"Campaign for {campaign_name}",
                            status="active",
                            category=json.dumps(offer_data.get('categories', {}))
                        )
                        db.add(campaign)
                        db.flush()  # Get the ID
                        campaigns_dict[campaign_id] = campaign.id
                    
                    campaign_db_id = campaigns_dict.get(campaign_id)
                    
                    # Process dates
                    start_date = self.parse_date(offer_data.get('start_date'))
                    end_date = self.parse_date(offer_data.get('end_date'))
                    
                    # Create offer
                    offer = Offer(
                        offer_id=offer_data.get('id'),
                        campaign_id=campaign_db_id,
                        campaign_name=campaign_name,
                        title=offer_data.get('title', ''),
                        description=offer_data.get('description', ''),
                        terms_and_conditions=offer_data.get('terms_and_condition', ''),
                        coupon_code=offer_data.get('coupon_code', ''),
                        image_url=offer_data.get('image_url', ''),
                        offer_type=offer_data.get('type', ''),
                        shipping_charge=offer_data.get('shipping_charge', ''),
                        status=offer_data.get('status', ''),
                        url=offer_data.get('url', ''),
                        affiliate_url=offer_data.get('affiliate_url', ''),
                        start_date=start_date,
                        end_date=end_date,
                        categories=json.dumps(offer_data.get('categories', {}))
                    )
                    db.add(offer)
                    db.flush()  # Get the ID
                    
                    # Create embedding
                    self.create_offer_embedding(offer, campaign_name, offer_data, db)
                    
                    offers_processed += 1
                    
                    if offers_processed % 100 == 0:
                        logger.info(f"Processed {offers_processed} offers...")
                        
                except Exception as e:
                    logger.error(f"Error processing offer {offer_data.get('id', 'unknown')}: {e}")
                    continue
            
            db.commit()
            logger.info(f"Successfully processed and stored {offers_processed} offers")
            return offers_processed
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error processing offers: {e}")
            raise
    
    def create_offer_embedding(self, offer: Offer, campaign_name: str, offer_data: Dict[str, Any], db: Session):
        """Create embedding for the offer"""
        try:
            # Combine all relevant text for embedding
            categories_text = ", ".join(offer_data.get('categories', {}).values())
            
            content_parts = [
                f"Campaign: {campaign_name}",
                f"Title: {offer.title}",
                f"Description: {self.clean_html(offer.description)}",
                f"Coupon Code: {offer.coupon_code}" if offer.coupon_code else "",
                f"Type: {offer.offer_type}",
                f"Categories: {categories_text}",
                f"Terms: {self.clean_html(offer.terms_and_conditions)}" if offer.terms_and_conditions else ""
            ]
            
            content = " | ".join([part for part in content_parts if part])
            
            # Generate embedding
            embedding = None
            model = self.get_embedding_model()
            if model:
                try:
                    embedding_vector = model.encode(content)
                    embedding = embedding_vector.tolist()
                except Exception as e:
                    logger.error(f"Error generating embedding for offer {offer.offer_id}: {e}")
                    # Fallback to simple embedding
                    embedding = self.generate_simple_embedding(content)
            else:
                # Use simple embedding as fallback
                embedding = self.generate_simple_embedding(content)
            
            # Create embedding record
            offer_embedding = OfferEmbedding(
                offer_id=offer.id,
                campaign_id=offer.campaign_id,
                chunk_id=f"offer_{offer.offer_id}",
                content=content,
                content_type="combined",
                embedding=embedding,
                meta_data=json.dumps({
                    "campaign_name": campaign_name,
                    "offer_type": offer.offer_type,
                    "categories": offer_data.get('categories', {}),
                    "status": offer.status
                })
            )
            db.add(offer_embedding)
            
        except Exception as e:
            logger.error(f"Error creating embedding for offer {offer.offer_id}: {e}")
    
    async def create_offer_embeddings(self, db: Session, offer: Offer):
        """Create embeddings for a single offer (used by admin controller)"""
        try:
            # Get offer categories from JSON
            categories = {}
            if offer.categories:
                try:
                    categories = json.loads(offer.categories)
                except:
                    pass
            
            # Create offer data dict
            offer_data = {
                'categories': categories
            }
            
            # Create embedding
            self.create_offer_embedding(offer, offer.campaign_name, offer_data, db)
            db.commit()
            
            logger.info(f"Created embedding for offer {offer.offer_id}")
            
        except Exception as e:
            logger.error(f"Error creating embeddings for offer {offer.offer_id}: {e}")
            raise
    
    def clean_html(self, text: str) -> str:
        """Clean HTML tags from text"""
        if not text:
            return ""
        
        import re
        # Remove HTML tags
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            logger.warning(f"Could not parse date: {date_str}")
            return None
    
    def log_sync_start(self, db: Session, sync_type: str = "auto") -> OfferSyncLog:
        """Log the start of a sync operation"""
        sync_log = OfferSyncLog(
            last_run_date=datetime.utcnow(),
            status="running",
            sync_type=sync_type
        )
        db.add(sync_log)
        db.commit()
        db.refresh(sync_log)
        return sync_log
    
    def log_sync_completion(self, db: Session, sync_log: OfferSyncLog, 
                           total_offers: int, execution_time: float, 
                           success: bool = True, error_message: str = None):
        """Log the completion of a sync operation"""
        sync_log.total_offers_retrieved = total_offers
        sync_log.execution_time_seconds = execution_time
        sync_log.status = "completed" if success else "failed"
        if error_message:
            sync_log.error_message = error_message
        
        db.commit()
    
    def load_extended_offers(self) -> List[Dict[str, Any]]:
        """Load offers from offers_extended.json file"""
        try:
            extended_file_path = os.path.join("data", "offers_extended.json")
            
            if os.path.exists(extended_file_path):
                with open(extended_file_path, 'r', encoding='utf-8') as f:
                    extended_offers = json.load(f)
                    logger.info(f"Loaded {len(extended_offers)} extended offers from JSON file")
                    return extended_offers
            else:
                logger.warning("offers_extended.json not found")
                return []
                
        except Exception as e:
            logger.error(f"Error loading extended offers: {e}")
            return []
    
    async def sync_offers_from_api(self, sync_type: str = "auto", clear_data: bool = True) -> Dict[str, Any]:
        """Main method to sync offers from API"""
        start_time = time.time()
        
        # Get database session
        db = get_sync_db_session()
        sync_log = None
        
        try:
            # Log sync start
            sync_log = self.log_sync_start(db, sync_type)
            logger.info(f"Starting {sync_type} sync of offers (ID: {sync_log.id})")
            
            # Clear existing data if requested
            if clear_data:
                self.clear_existing_data(db)
            
            # Fetch all offers from API
            offers_data = await self.fetch_all_offers_from_api()
            
            if not offers_data:
                logger.warning("No offers retrieved from API, will only use extended offers")
                offers_data = []
            
            # Load and append extended offers
            extended_offers = self.load_extended_offers()
            if extended_offers:
                offers_data.extend(extended_offers)
                logger.info(f"Total offers including extended: {len(offers_data)}")
            
            # Process and store offers
            total_processed = self.process_and_store_offers(offers_data, db)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log completion
            self.log_sync_completion(db, sync_log, total_processed, execution_time)
            
            result = {
                "success": True,
                "sync_id": sync_log.id,
                "total_offers_retrieved": total_processed,
                "execution_time_seconds": execution_time,
                "message": f"Successfully synced {total_processed} offers in {execution_time:.2f} seconds"
            }
            
            logger.info(result["message"])
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)
            
            if sync_log:
                self.log_sync_completion(db, sync_log, 0, execution_time, False, error_message)
            
            logger.error(f"Sync failed: {error_message}")
            
            return {
                "success": False,
                "sync_id": sync_log.id if sync_log else None,
                "total_offers_retrieved": 0,
                "execution_time_seconds": execution_time,
                "error": error_message,
                "message": f"Sync failed: {error_message}"
            }
            
        finally:
            db.close()
    
    def get_last_sync_info(self, db: Session) -> Optional[Dict[str, Any]]:
        """Get information about the last sync"""
        try:
            last_sync = db.query(OfferSyncLog).order_by(OfferSyncLog.last_run_date.desc()).first()
            
            if last_sync:
                return {
                    "id": last_sync.id,
                    "last_run_date": last_sync.last_run_date,
                    "total_offers_retrieved": last_sync.total_offers_retrieved,
                    "status": last_sync.status,
                    "sync_type": last_sync.sync_type,
                    "execution_time_seconds": last_sync.execution_time_seconds,
                    "error_message": last_sync.error_message
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting last sync info: {e}")
            return None
    
    def get_sync_history(self, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sync history"""
        try:
            syncs = db.query(OfferSyncLog).order_by(OfferSyncLog.last_run_date.desc()).limit(limit).all()
            
            return [
                {
                    "id": sync.id,
                    "last_run_date": sync.last_run_date,
                    "total_offers_retrieved": sync.total_offers_retrieved,
                    "status": sync.status,
                    "sync_type": sync.sync_type,
                    "execution_time_seconds": sync.execution_time_seconds,
                    "error_message": sync.error_message
                }
                for sync in syncs
            ]
            
        except Exception as e:
            logger.error(f"Error getting sync history: {e}")
            return []

# Global instance
cuelinks_offers_service = CuelinksOffersService()
