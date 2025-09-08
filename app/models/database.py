from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from datetime import datetime
import uuid

# Try to import pgvector, fallback to ARRAY if not available
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = None

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String(100), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    name = Column(String(255))
    picture = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Add indexes for efficient querying
    __table_args__ = (
        Index('idx_users_google_id', 'google_id'),
        Index('idx_users_email', 'email'),
        Index('idx_users_active', 'is_active'),
    )

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, unique=True, index=True)
    name = Column(String(500), index=True)
    description = Column(Text)
    status = Column(String(100))
    category = Column(Text)  # Store as JSON string, can be long
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Create relationship with Offer
    offers = relationship("Offer", back_populates="campaign")
    
    # Add indexes for efficient querying
    __table_args__ = (
        Index('idx_campaigns_name', 'name'),
        Index('idx_campaigns_status', 'status'),
    )

class Offer(Base):
    __tablename__ = "offers"
    
    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, unique=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), index=True)  # Add proper foreign key relationship
    campaign_name = Column(String(500), index=True)  # Store campaign name directly for quick access
    title = Column(String(1000))  # Increase length
    description = Column(Text)
    terms_and_conditions = Column(Text)
    coupon_code = Column(String(200))
    image_url = Column(String(1000))
    offer_type = Column(String(100))
    shipping_charge = Column(String(200))
    status = Column(String(100))
    url = Column(String(1000))
    affiliate_url = Column(String(1000))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    categories = Column(Text)  # Store as JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Create relationship with Campaign
    campaign = relationship("Campaign", back_populates="offers")
    
    # Add index for efficient querying
    __table_args__ = (
        Index('idx_offers_campaign_id', 'campaign_id'),
        Index('idx_offers_status', 'status'),
    )

class OfferEmbedding(Base):
    """
    Dedicated table for storing embeddings for RAG approach
    This enables efficient vector similarity search for chat functionality
    """
    __tablename__ = "offer_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id"), index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), index=True)  # Add campaign relationship
    chunk_id = Column(String(100), index=True)  # For document chunking
    content = Column(Text)  # The actual text content
    content_type = Column(String(50))  # 'title', 'description', 'combined', 'terms', 'campaign'
    # Use pgvector if available, otherwise fallback to ARRAY
    embedding = Column(Vector(384) if PGVECTOR_AVAILABLE else ARRAY(Float))  # Vector embedding (384 dimensions for sentence-transformers)
    meta_data = Column(Text)  # JSON metadata for filtering (renamed from metadata)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Create relationships
    offer = relationship("Offer", foreign_keys=[offer_id])
    campaign = relationship("Campaign", foreign_keys=[campaign_id])
    
    # Create index for efficient similarity search
    __table_args__ = (
        Index('idx_offer_embeddings_content_type', 'content_type'),
        Index('idx_offer_embeddings_offer_id', 'offer_id'),
        Index('idx_offer_embeddings_campaign_id', 'campaign_id'),
    )

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(100), unique=True, index=True)
    campaign_id = Column(Integer)
    sub_id = Column(String(100))
    amount = Column(Float)
    commission = Column(Float)
    status = Column(String(50))
    date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_message = Column(Text)
    bot_response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String(100))

class ChatFeedback(Base):
    __tablename__ = "chat_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)
    user_message = Column(Text)
    bot_response = Column(Text)
    feedback_type = Column(String(20))  # 'like', 'dislike', 'feedback'
    feedback_text = Column(Text, nullable=True)  # For written feedback
    offer_id = Column(Integer, nullable=True)  # Track specific offer feedback
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Add index for efficient querying
    __table_args__ = (
        Index('idx_chat_feedback_session', 'session_id'),
        Index('idx_chat_feedback_type', 'feedback_type'),
        Index('idx_chat_feedback_offer', 'offer_id'),
        Index('idx_chat_feedback_timestamp', 'timestamp'),
    )

class OfferSyncLog(Base):
    __tablename__ = "offer_sync_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    last_run_date = Column(DateTime, default=datetime.utcnow)
    total_offers_retrieved = Column(Integer, default=0)
    status = Column(String(50), default='running')  # running, completed, failed
    error_message = Column(Text, nullable=True)
    sync_type = Column(String(50), default='auto')  # auto, manual
    execution_time_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Add index for efficient querying
    __table_args__ = (
        Index('idx_sync_logs_date', 'last_run_date'),
        Index('idx_sync_logs_status', 'status'),
        Index('idx_sync_logs_type', 'sync_type'),
    )

class Link(Base):
    __tablename__ = "links"
    
    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String(500))
    affiliate_url = Column(String(500))
    shortened_url = Column(String(500))
    sub_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
