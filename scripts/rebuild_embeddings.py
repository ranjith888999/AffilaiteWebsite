"""
Rebuild Embeddings Script
This script rebuilds all embeddings to include campaign information.
"""

import os
import sys
import asyncio
import json
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from langchain.schema import Document
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

# Add the parent directory to the path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from app.models.database import Offer, Campaign, OfferEmbedding, Base
from app.services.rag_service import PostgreSQLVectorStore

async def rebuild_embeddings():
    """Rebuild all embeddings with campaign information"""
    # Load environment variables
    load_dotenv()
    
    # Database configuration
    DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"
    
    # Create async engine and session
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    
    # Load embedding model
    model_name = "sentence-transformers/all-MiniLM-L6-v2"  # Fast and efficient model
    embedding_model = SentenceTransformer(model_name)
    
    async with engine.begin() as conn:
        print("Creating tables if they don't exist...")
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        # Create vector store
        vector_store = PostgreSQLVectorStore(session, embedding_model)
        
        # Delete existing embeddings
        print("Deleting existing embeddings...")
        await session.execute(select(OfferEmbedding).delete())
        await session.commit()
        
        # Get all offers with their campaigns
        print("Fetching offers and campaigns...")
        result = await session.execute(
            select(Offer, Campaign)
            .join(Campaign, Offer.campaign_id == Campaign.id)
            .where(Offer.status.in_(["active", "live"]))
        )
        offer_campaigns = result.all()
        print(f"Found {len(offer_campaigns)} active offers to process")
        
        # Process each offer
        processed = 0
        for offer, campaign in offer_campaigns:
            # Create documents for various offer components
            documents = []
            
            # Combined document with campaign name
            combined_text = f"Campaign: {campaign.name}\nTitle: {offer.title}\nDescription: {offer.description}"
            if offer.coupon_code:
                combined_text += f"\nCoupon Code: {offer.coupon_code}"
                
            # Add categories if available
            try:
                categories = json.loads(offer.categories)
                if categories:
                    categories_text = ", ".join([cat.get("name", "") for cat in categories if cat.get("name")])
                    combined_text += f"\nCategories: {categories_text}"
            except:
                pass
                
            # Create document
            combined_doc = Document(
                page_content=combined_text,
                metadata={
                    "type": "combined",
                    "offer_id": offer.id,
                    "campaign_id": campaign.id,
                    "campaign_name": campaign.name,
                    "status": offer.status
                }
            )
            documents.append(combined_doc)
            
            # Create separate document for campaign name for better matching
            campaign_doc = Document(
                page_content=f"Campaign: {campaign.name}",
                metadata={
                    "type": "campaign",
                    "offer_id": offer.id,
                    "campaign_id": campaign.id,
                    "campaign_name": campaign.name,
                    "status": offer.status
                }
            )
            documents.append(campaign_doc)
            
            # Add documents to vector store
            await vector_store.add_documents(documents, offer.id, campaign.id)
            
            processed += 1
            if processed % 10 == 0:
                print(f"Processed {processed}/{len(offer_campaigns)} offers")
        
        print(f"Successfully rebuilt embeddings for {processed} offers")

if __name__ == "__main__":
    asyncio.run(rebuild_embeddings())
