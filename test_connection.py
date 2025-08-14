"""
Simple HTTP connectivity test
"""
import sys
import time
import traceback

def test_http_connection():
    try:
        print("Importing requests...")
        import requests
        
        # Test different ports
        ports = [8000, 8003, 8080]
        
        for port in ports:
            url = f"http://localhost:{port}/"
            print(f"\nTesting connection to {url}")
            
            try:
                print("Sending request...")
                response = requests.get(url, timeout=5)
                print(f"Response received: Status {response.status_code}")
                if response.status_code == 200:
                    print("Connection successful!")
                    print(f"Response size: {len(response.text)} bytes")
                    return True
                else:
                    print(f"Server responded with status {response.status_code}")
            except requests.exceptions.ConnectionError:
                print(f"Connection refused on port {port}")
            except requests.exceptions.Timeout:
                print(f"Connection timed out on port {port}")
            except Exception as e:
                print(f"Error: {str(e)}")
        
        print("\nAll connection attempts failed.")
        return False
    
    except Exception as e:
        print(f"Test failed: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_http_connection()
