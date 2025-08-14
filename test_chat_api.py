"""
API Test Script - Direct testing of the chat API endpoints
"""
import requests
import time
import json
import statistics

# Configuration
BASE_URL = "http://localhost:8003"  # Update this if your server uses a different port
TEST_QUERIES = [
    "best laptop deals",
    "fashion discounts",
    "travel offers"
]
EXPECTED_RESULTS = 5  # We expect exactly 5 results for each query

def test_server_connectivity():
    """Test if the server is accessible"""
    print("🔍 Testing server connectivity...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print(f"✅ Server is running and accessible at {BASE_URL}")
            return True
        else:
            print(f"⚠️ Server returned status code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to server: {str(e)}")
        return False

def test_chat_api_performance():
    """Test the performance of the chat API"""
    print("🔍 Testing API performance...")
    
    if not test_server_connectivity():
        print("❌ Cannot test API performance because server is not accessible")
        return
    
    response_times = []
    all_successful = True
    
    for query in TEST_QUERIES:
        print(f"📝 Running query: {query}")
        
        # Measure response time
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/chat/with-offers",
            json={"query": query}
        )
        end_time = time.time()
        
        # Calculate response time
        response_time = end_time - start_time
        response_times.append(response_time)
        
        print(f"🕒 Response time: {response_time:.2f} seconds")
        
        # Check if response is valid
        if response.status_code != 200:
            print(f"❌ Error: Received status code {response.status_code}")
            all_successful = False
            continue
        
        # Parse response
        try:
            data = response.json()
            offers = data.get("offers", [])
            
            # Check number of results
            if len(offers) == EXPECTED_RESULTS:
                print(f"✅ Query returned {len(offers)} results as expected")
            else:
                print(f"⚠️ Query returned {len(offers)} results, expected {EXPECTED_RESULTS}")
                all_successful = False
                
        except Exception as e:
            print(f"❌ Error parsing response: {str(e)}")
            all_successful = False
    
    # Print summary
    if response_times:
        avg_time = statistics.mean(response_times)
        print("\n📊 Performance Summary:")
        print(f"   - Average response time: {avg_time:.2f} seconds")
        print(f"   - All queries completed in less than 10 seconds {'✅' if all(t < 10 for t in response_times) else '❌'}")
        print(f"   - All queries returned exactly {EXPECTED_RESULTS} results {'✅' if all_successful else '❌'}")

if __name__ == "__main__":
    test_chat_api_performance()
