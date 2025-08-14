"""
Simple direct test for the ultra_fast_service to verify performance
"""

import time
import traceback

# Test the direct function
def test_ultra_fast_service():
    try:
        print("Importing modules...")
        from app.services.ultra_fast_service import search_offers_ultra_fast, generate_response_ultra_fast
        
        # Test queries
        queries = [
            "best laptop deals",
            "fashion discounts",
            "travel offers"
        ]
        
        total_time = 0
        for query in queries:
            print(f"\nTesting query: '{query}'")
            start_time = time.time()
            
            # Search for offers
            try:
                offers = search_offers_ultra_fast(query, 5)
                search_time = time.time() - start_time
                print(f"Search completed in {search_time:.3f} seconds")
                print(f"Found {len(offers)} offers")
                
                # Generate response
                if offers:
                    response = generate_response_ultra_fast(query, offers)
                    print(f"Response: {response}")
                    
                    # Print first offer details
                    print("\nFirst offer details:")
                    offer = offers[0]
                    for key, value in offer.items():
                        if isinstance(value, str) and len(value) > 50:
                            value = value[:50] + "..."
                        print(f"  {key}: {value}")
                
                query_time = time.time() - start_time
                total_time += query_time
                print(f"Total query time: {query_time:.3f} seconds")
                
                # Check if meeting the target
                if query_time < 10:
                    print("✅ Performance target met (under 10 seconds)")
                else:
                    print("❌ Performance target not met (over 10 seconds)")
                    
            except Exception as e:
                print(f"Error processing query '{query}': {str(e)}")
                traceback.print_exc()
        
        # Print summary
        if queries:
            print(f"\nAverage query time: {total_time / len(queries):.3f} seconds")
    
    except Exception as e:
        print(f"Test failed: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    test_ultra_fast_service()
