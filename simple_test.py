"""
Simple API test script
"""
import requests

# Try to connect to the server
try:
    response = requests.get("http://localhost:8003/")
    print(f"Server status: {response.status_code}")
    print("Server is working!")
except Exception as e:
    print(f"Error connecting to server: {e}")

# Try to use the chat API
try:
    response = requests.post(
        "http://localhost:8003/chat/with-offers",
        json={"query": "test query"}
    )
    print(f"API status: {response.status_code}")
    data = response.json()
    print(f"API response contains {len(data.get('offers', []))} offers")
except Exception as e:
    print(f"Error calling API: {e}")
