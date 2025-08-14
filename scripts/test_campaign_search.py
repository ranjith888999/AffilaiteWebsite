"""
Test script to verify the chat search functionality
with campaign name searches (e.g., "Nykaa offers")
"""

import asyncio
import sys
import os
from dotenv import load_dotenv
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

# Import the ultra_fast_service for testing
from app.services.ultra_fast_service import search_offers_ultra_fast, generate_response_ultra_fast

async def test_search_by_campaign_name():
    """Test searching by campaign name"""
    logger.info("Starting test for campaign name search")
    
    # List of campaign names to test
    test_queries = [
        "Nykaa offers",
        "Amazon deals",
        "Myntra fashion",
        "Ajio coupons"
    ]
    
    for query in test_queries:
        logger.info(f"Testing search for: '{query}'")
        
        # Perform search
        search_results = search_offers_ultra_fast(query, limit=5)
        
        # Generate response
        response = generate_response_ultra_fast(query, search_results)
        
        # Log results
        logger.info(f"Found {len(search_results)} results for '{query}'")
        logger.info(f"Response: {response}")
        
        # Print campaign names from results
        for i, result in enumerate(search_results):
            campaign_name = result.get('campaign_name', 'Unknown')
            logger.info(f"Result {i+1}: {result['title']} - Campaign: {campaign_name}")
        
        logger.info("-" * 50)
    
    logger.info("Campaign name search test completed")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(test_search_by_campaign_name())
