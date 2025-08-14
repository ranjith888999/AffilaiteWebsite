#!/usr/bin/env python
"""
Test the improved RAG system with category information in embeddings
"""

import os
import sys
import asyncio
import logging
from pprint import pprint

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag_service import RAGService, PostgreSQLVectorStore
from app.database import get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

async def test_category_searches():
    """
    Test searches that should benefit from category information
    """
    # Initialize the RAG service
    rag_service = RAGService()
    
    # Define test queries that should benefit from category information
    test_queries = [
        "electronics deals",
        "fashion offers",
        "food and grocery discounts",
        "health and beauty products",
        "travel offers",
        "sports equipment",
        "gaming discounts",
        "entertainment deals",
        "financial services"
    ]
    
    # Test each query
    for query in test_queries:
        print(f"\n\n====== Testing Query: '{query}' ======")
        # Get a database session
        async for session in get_db():
            # Use similarity_search directly since that's available
            results = await PostgreSQLVectorStore(session, rag_service.embedding_model).similarity_search(query, k=5)
            
            # Display results
            print(f"Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                offer = result["offer"]
                similarity = result["similarity"]
                
                # Extract category from the content
                category = "Unknown"
                for line in offer.embedding.content.split('\n'):
                    if line.startswith("Category:"):
                        category = line.replace("Category:", "").strip()
                        break
                
                print(f"\nResult {i} (Similarity: {similarity:.4f}):")
                print(f"Campaign: {offer.campaign.name}")
                print(f"Title: {offer.title}")
                print(f"Category: {category}")
                print(f"Description: {offer.description[:100]}...")
            
            # Only need one session iteration
            break
        
        # Display results
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            offer = result["offer"]
            similarity = result["similarity"]
            
            # Extract category from the content
            category = "Unknown"
            for line in offer.embedding.content.split('\n'):
                if line.startswith("Category:"):
                    category = line.replace("Category:", "").strip()
                    break
            
            print(f"\nResult {i} (Similarity: {similarity:.4f}):")
            print(f"Campaign: {offer.campaign.name}")
            print(f"Title: {offer.title}")
            print(f"Category: {category}")
            print(f"Description: {offer.description[:100]}...")

async def test_specific_category_match(category_name):
    """
    Test if searching for a specific category returns relevant results
    """
    # Initialize the RAG service
    rag_service = RAGService()
    
    query = f"{category_name} offers"
    print(f"\n\n====== Testing Specific Category: '{query}' ======")
    
    async for session in get_db():
        results = await PostgreSQLVectorStore(session, rag_service.embedding_model).similarity_search(query, k=5)
        
        # Display results
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            offer = result["offer"]
            similarity = result["similarity"]
            
            # Extract category from the content
            category = "Unknown"
            for line in offer.embedding.content.split('\n'):
                if line.startswith("Category:"):
                    category = line.replace("Category:", "").strip()
                    break
            
            # Check if the category matches
            matches_query = category_name.lower() in category.lower()
            
            print(f"\nResult {i} (Similarity: {similarity:.4f}):")
            print(f"Campaign: {offer.campaign.name}")
            print(f"Title: {offer.title}")
            print(f"Category: {category}")
            print(f"Matches Query Category: {matches_query}")
            print(f"Description: {offer.description[:100]}...")
        
        # Only need one session iteration
        break

async def main():
    # First test general category searches
    await test_category_searches()
    
    # Then test specific category matches
    await test_specific_category_match("Electronics")
    await test_specific_category_match("Health & Beauty")
    await test_specific_category_match("Travel")

if __name__ == "__main__":
    asyncio.run(main())
