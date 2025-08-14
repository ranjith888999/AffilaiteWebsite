"""
API Test Script - Direct testing of the chat API endpoints
"""
import requests
import time
import json
import sys

# Base URL for API
BASE_URL = "http://localhost:8003/api"

def test_chat_with_offers_endpoint(query):
    """Test the /chat/with-offers endpoint with timing"""
    url = f"{BASE_URL}/chat/with-offers"
    payload = {"query": query}
    
    print(f"\n\n-----------------------------------")
    print(f"Testing chat API with query: '{query}'")
    print(f"-----------------------------------")
    
    # Send request with timing
    start_time = time.time()
    try:
        response = requests.post(url, json=payload, timeout=30)
        request_time = time.time() - start_time
        
        print(f"Request completed in {request_time:.3f} seconds")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Print response details
            print(f"\nResponse content:")
            print(f"  Bot response: {data.get('response', 'No response')[:100]}...")
            print(f"  Number of offers: {len(data.get('offers', []))}")
            print(f"  Processing time (reported by API): {data.get('processing_time', 'N/A')} seconds")
            
            # Print offers
            offers = data.get('offers', [])
            if offers:
                print("\nOffer details:")
                for i, offer in enumerate(offers, 1):
                    title = offer.get('title', 'No title')
                    if len(title) > 40:
                        title = title[:40] + "..."
                    print(f"  Offer {i}: {title}")
            
            return {
                "success": True,
                "request_time": request_time,
                "num_offers": len(data.get('offers', [])),
                "api_time": data.get('processing_time')
            }
        else:
            print(f"Error: {response.text}")
            return {
                "success": False,
                "request_time": request_time,
                "error": response.text
            }
    
    except requests.RequestException as e:
        print(f"Request failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def run_tests():
    """Run a series of tests on the API"""
    # Test queries
    queries = [
        "best laptop deals",
        "fashion discounts",
        "travel offers",
        "smartphone deals",
        "food delivery coupons"
    ]
    
    results = []
    
    for query in queries:
        result = test_chat_with_offers_endpoint(query)
        results.append({"query": query, **result})
    
    # Print summary
    print("\n\n===============================")
    print("API TEST SUMMARY")
    print("===============================")
    
    successful_tests = [r for r in results if r.get("success")]
    
    if successful_tests:
        avg_time = sum(r.get("request_time", 0) for r in successful_tests) / len(successful_tests)
        print(f"Successful tests: {len(successful_tests)}/{len(queries)}")
        print(f"Average API response time: {avg_time:.3f} seconds")
        
        # Check if meeting performance target
        if avg_time < 10:
            print("✅ Performance target met (under 10 seconds)")
        else:
            print("❌ Performance target not met (over 10 seconds)")
    else:
        print("No successful tests")

if __name__ == "__main__":
    run_tests()
