"""
Comprehensive test for the chat controller functionality
Tests both the direct API endpoint and underlying services
"""

import asyncio
import sys
import os
from dotenv import load_dotenv
import logging
import json
import httpx
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

# Prepare test configuration
BASE_URL = "http://localhost:8000"  # Change if your server runs on a different port

async def test_chat_api():
    """Test the chat API endpoint directly"""
    logger.info("Testing chat API endpoint")
    
    # List of campaign names to test
    test_queries = [
        "Nykaa offers",
        "Amazon deals",
        "Myntra fashion",
        "Ajio coupons",
        "I want some good electronics deals"
    ]
    
    session_id = str(uuid.uuid4())
    
    async with httpx.AsyncClient() as client:
        for query in test_queries:
            logger.info(f"Testing API with query: '{query}'")
            
            # Prepare request payload
            payload = {
                "message": query,
                "session_id": session_id
            }
            
            # Make API request
            try:
                response = await client.post(f"{BASE_URL}/api/chat", json=payload)
                
                # Check response
                if response.status_code == 200:
                    result = response.json()
                    
                    logger.info(f"API Response: {result['response']}")
                    logger.info(f"Found {len(result['offers'])} offers")
                    
                    # Print offer details
                    for i, offer in enumerate(result['offers']):
                        logger.info(f"Offer {i+1}: {offer['title']}")
                        if 'campaign_name' in offer:
                            logger.info(f"  Campaign: {offer['campaign_name']}")
                        
                else:
                    logger.error(f"API request failed with status code: {response.status_code}")
                    logger.error(f"Response: {response.text}")
            
            except Exception as e:
                logger.error(f"Error calling API: {str(e)}")
            
            logger.info("-" * 50)
    
    logger.info("Chat API test completed")

async def test_search_services():
    """Test the underlying search services directly"""
    logger.info("Testing search services directly")
    
    # Import services
    from app.services.ultra_fast_service import search_offers_ultra_fast
    
    # List of campaign names to test
    test_queries = [
        "Nykaa offers",
        "Amazon deals",
        "Myntra fashion",
        "Ajio coupons",
        "Electronics"
    ]
    
    for query in test_queries:
        logger.info(f"Testing service with query: '{query}'")
        
        # Get results from service
        results = search_offers_ultra_fast(query, limit=5)
        
        logger.info(f"Found {len(results)} results")
        
        # Print result details
        for i, result in enumerate(results):
            logger.info(f"Result {i+1}: {result['title']}")
            if 'campaign_name' in result:
                logger.info(f"  Campaign: {result['campaign_name']}")
        
        logger.info("-" * 50)
    
    logger.info("Search services test completed")

async def main():
    """Run all tests"""
    # First test the services directly
    await test_search_services()
    
    # Then test the API if the server is running
    try:
        await test_chat_api()
    except Exception as e:
        logger.error(f"API test failed: {str(e)}")
        logger.info("Make sure the server is running before testing the API")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
