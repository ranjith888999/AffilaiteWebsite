import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CUELINKS_API_KEY")

async def test_cuelinks_api():
    """Test the Cuelinks API directly"""
    print(f"Using API key: {API_KEY}")
    
    headers = {
        "Authorization": f"Token token={API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Test offers endpoint
    async with httpx.AsyncClient() as client:
        try:
            offers_url = "https://www.cuelinks.com/api/v2/offers.json"
            print(f"Testing offers endpoint: {offers_url}")
            response = await client.get(offers_url, headers=headers)
            
            print(f"Status code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Found {len(data.get('offers', []))} offers")
                
                # Print first offer as example
                if data.get('offers'):
                    first_offer = data['offers'][0]
                    print("\nExample offer:")
                    print(f"ID: {first_offer.get('id')}")
                    print(f"Campaign ID: {first_offer.get('camapign_id')}")
                    print(f"Campaign: {first_offer.get('campaign')}")
                    print(f"Title: {first_offer.get('title')}")
            else:
                print(f"Error response: {response.text}")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_cuelinks_api())
