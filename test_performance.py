"""
Test script for the ultra-fast service to verify response time
"""

import time
import sys
sys.path.append('.')  # Add current directory to path

from app.services.ultra_fast_service import search_offers_ultra_fast, generate_response_ultra_fast

def test_search_performance(query, limit=5):
    """Test the performance of the ultra-fast search function"""
    print(f"\nTesting search for: '{query}' with limit {limit}")
    
    # Test search performance
    start_time = time.time()
    offers = search_offers_ultra_fast(query, limit)
    search_time = time.time() - start_time
    
    # Test response generation
    start_time = time.time()
    response = generate_response_ultra_fast(query, offers)
    response_time = time.time() - start_time
    
    # Print results
    print(f"Search completed in {search_time:.3f} seconds")
    print(f"Response generated in {response_time:.3f} seconds")
    print(f"Total time: {search_time + response_time:.3f} seconds")
    print(f"Found {len(offers)} offers")
    
    # Print first offer if available
    if offers:
        print("\nSample offer:")
        offer = offers[0]
        print(f"Title: {offer.get('title')}")
        print(f"Description: {offer.get('description')[:50]}...")
        print(f"Campaign: {offer.get('campaign_name')}")
    
    print("\nResponse:")
    print(response)
    
    return search_time + response_time

if __name__ == "__main__":
    # Test with different queries
    queries = [
        "best laptop deals",
        "fashion discounts",
        "travel offers",
        "smartphone offers",
        "food delivery coupons"
    ]
    
    total_time = 0
    for query in queries:
        query_time = test_search_performance(query)
        total_time += query_time
        print("-" * 50)
    
    # Print summary
    print("\nPerformance Summary:")
    print(f"Average time per query: {total_time / len(queries):.3f} seconds")
    print(f"All {len(queries)} queries completed in {total_time:.3f} seconds")
