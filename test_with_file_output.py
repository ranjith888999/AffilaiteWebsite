"""
Test ultra_fast_service and write results to a file
"""
import time
import traceback
import sys
from pathlib import Path

# Redirect output to a file
log_file = Path("performance_test_results.txt")
with log_file.open("w") as f:
    try:
        f.write("Starting performance test...\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Import the service
        f.write("Importing ultra_fast_service...\n")
        from app.services.ultra_fast_service import search_offers_ultra_fast, generate_response_ultra_fast
        
        # Test queries
        queries = [
            "best laptop deals",
            "fashion discounts",
            "travel offers"
        ]
        
        total_time = 0
        successful_queries = 0
        
        for query in queries:
            f.write(f"\n\nTesting query: '{query}'\n")
            f.write("-" * 40 + "\n")
            
            start_time = time.time()
            try:
                # Search for offers
                f.write(f"Searching for offers with query: '{query}'...\n")
                offers = search_offers_ultra_fast(query, 5)
                search_time = time.time() - start_time
                
                f.write(f"Search completed in {search_time:.3f} seconds\n")
                f.write(f"Found {len(offers)} offers\n")
                
                # Generate response
                if offers:
                    response_start = time.time()
                    response = generate_response_ultra_fast(query, offers)
                    response_time = time.time() - response_start
                    
                    f.write(f"Response generated in {response_time:.3f} seconds\n")
                    f.write(f"Response: {response}\n")
                    
                    # Print first offer details
                    if offers:
                        f.write("\nFirst offer details:\n")
                        offer = offers[0]
                        for key, value in offer.items():
                            if isinstance(value, str) and len(value) > 50:
                                value = value[:50] + "..."
                            f.write(f"  {key}: {value}\n")
                
                query_time = time.time() - start_time
                total_time += query_time
                successful_queries += 1
                
                f.write(f"\nTotal query time: {query_time:.3f} seconds\n")
                
                # Check if meeting the target
                if query_time < 10:
                    f.write("✅ Performance target met (under 10 seconds)\n")
                else:
                    f.write("❌ Performance target not met (over 10 seconds)\n")
                    
            except Exception as e:
                f.write(f"Error processing query '{query}': {str(e)}\n")
                f.write(traceback.format_exc() + "\n")
        
        # Print summary
        f.write("\n\n" + "=" * 50 + "\n")
        f.write("PERFORMANCE TEST SUMMARY\n")
        f.write("=" * 50 + "\n")
        
        if successful_queries > 0:
            f.write(f"Successful queries: {successful_queries}/{len(queries)}\n")
            f.write(f"Average query time: {total_time / successful_queries:.3f} seconds\n")
        else:
            f.write("No queries completed successfully\n")
            
        f.write(f"\nTest completed at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    except Exception as e:
        f.write(f"Test failed with error: {str(e)}\n")
        f.write(traceback.format_exc() + "\n")

print(f"Test completed. Results written to {log_file}")
