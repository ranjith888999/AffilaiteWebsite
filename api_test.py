"""
API Test Script - Testing with requests
"""
import requests
import time
import json

BASE_URL = "http://localhost:8003"
TEST_QUERY = "best laptop deals"

def make_api_request():
    print(f"Sending request to {BASE_URL}/chat/with-offers...")
    
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/chat/with-offers",
        json={"query": TEST_QUERY}
    )
    end_time = time.time()
    
    print(f"Request took {end_time - start_time:.2f} seconds")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Received {len(data.get('offers', []))} offers")
            print(f"Bot response: {data.get('response', 'No response')}")
            return True
        except Exception as e:
            print(f"Error parsing response: {e}")
            return False
    else:
        print(f"Request failed with status code {response.status_code}")
        return False

if __name__ == "__main__":
    print("Testing API...")
    make_api_request()
