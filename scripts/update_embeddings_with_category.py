#!/usr/bin/env python
"""
Update offer embeddings to include category information and regenerate embeddings
"""

import os
import sys
import asyncio
import json
import logging
from sentence_transformers import SentenceTransformer
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import Campaign, Offer, OfferEmbedding
from app.database import ASYNC_DATABASE_URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

engine = create_async_engine(ASYNC_DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Initialize the embedding model
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')

def create_embedding(text):
    """
    Create an embedding for the given text
    """
    try:
        embedding = EMBEDDING_MODEL.encode(text)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Error creating embedding: {e}")
        return None

async def update_embeddings_with_category():
    """
    Update all offer embeddings to include category information
    """
    async with async_session() as session:
        # Get all offers with their related data
        stmt = select(Offer, Campaign).join(Campaign, Offer.campaign_id == Campaign.id)
        result = await session.execute(stmt)
        offer_data = result.all()
        
        logger.info(f"Found {len(offer_data)} offers to update")
        
        # Prepare a dictionary mapping offer_id to categories
        offer_categories = {}
        for offer, campaign in offer_data:
            try:
                # Parse categories from JSON string
                categories = json.loads(offer.categories) if offer.categories else {}
                
                # Extract category names
                if isinstance(categories, dict):
                    category_names = list(categories.values())
                else:
                    category_names = []
                
                offer_categories[offer.id] = {
                    'campaign_name': campaign.name,
                    'categories': category_names
                }
            except Exception as e:
                logger.warning(f"Error parsing categories for offer {offer.id}: {e}")
                offer_categories[offer.id] = {
                    'campaign_name': campaign.name,
                    'categories': []
                }
        
        # Get all embeddings
        stmt = select(OfferEmbedding)
        result = await session.execute(stmt)
        embeddings = result.scalars().all()
        
        logger.info(f"Found {len(embeddings)} embeddings to update")
        
        # Update each embedding
        updated_count = 0
        batch_size = 50
        for i in range(0, len(embeddings), batch_size):
            batch = embeddings[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(embeddings) + batch_size - 1)//batch_size}")
            
            for embedding in tqdm(batch, desc="Updating embeddings"):
                offer_id = embedding.offer_id
                if offer_id not in offer_categories:
                    logger.warning(f"No categories found for offer {offer_id}, skipping")
                    continue
                
                # Get the current content
                content = embedding.content
                
                # Get category information
                info = offer_categories[offer_id]
                campaign_name = info['campaign_name']
                categories = info['categories']
                
                # Create category text
                category_text = ", ".join(categories) if categories else "Unknown"
                
                # Check if the content already has a Category line
                if "Category:" not in content:
                    # Split the content by lines
                    lines = content.split("\n")
                    
                    # Find the right position to insert category (after title and before description)
                    new_lines = []
                    for j, line in enumerate(lines):
                        new_lines.append(line)
                        if line.startswith("Title:") and j+1 < len(lines) and lines[j+1].startswith("Description:"):
                            new_lines.append(f"Category: {category_text}")
                    
                    # If we couldn't find the right spot, just append at the end
                    if len(new_lines) == len(lines):
                        new_lines.append(f"Category: {category_text}")
                    
                    new_content = "\n".join(new_lines)
                else:
                    # Replace the existing category line
                    lines = content.split("\n")
                    new_lines = []
                    for line in lines:
                        if line.startswith("Category:"):
                            new_lines.append(f"Category: {category_text}")
                        else:
                            new_lines.append(line)
                    new_content = "\n".join(new_lines)
                
                # Create new embedding
                new_embedding_vector = create_embedding(new_content)
                
                if new_embedding_vector:
                    # Update the embedding in the database
                    embedding.content = new_content
                    embedding.embedding = new_embedding_vector
                    updated_count += 1
                else:
                    logger.error(f"Failed to create embedding for offer {offer_id}")
            
            # Commit the batch
            await session.commit()
            logger.info(f"Committed batch {i//batch_size + 1}, updated {updated_count} embeddings so far")
        
        logger.info(f"Successfully updated {updated_count} embeddings with category information")

async def main():
    logger.info("Starting embedding update with category information")
    await update_embeddings_with_category()
    logger.info("Embedding update complete")

if __name__ == "__main__":
    asyncio.run(main())
