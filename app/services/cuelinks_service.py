import httpx
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

class CuelinksService:
    def __init__(self):
        self.api_key = os.getenv("CUELINKS_API_KEY")
        self.base_url = os.getenv("CUELINKS_BASE_URL")
        self.headers = {
            "Authorization": f"Token token={self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_campaigns(self, page: int = 1, per_page: int = 30, 
                           search_term: Optional[str] = None,
                           categories: Optional[str] = None) -> Dict[str, Any]:
        """Fetch campaigns from Cuelinks API"""
        url = f"{self.base_url}/campaigns.json"
        params = {
            "page": page,
            "per_page": per_page,
            "sort_column": "name",
            "sort_direction": "asc"
        }
        
        if search_term:
            params["search_term"] = search_term
        if categories:
            params["categories"] = categories
            
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            return response.json()
    
    async def get_all_campaigns(self, page: int = 1, per_page: int = 30,
                               search_term: Optional[str] = None,
                               categories: Optional[str] = None) -> Dict[str, Any]:
        """Fetch all campaigns including paused ones"""
        url = f"{self.base_url}/all_campaigns.json"
        params = {
            "page": page,
            "per_page": per_page,
            "sort_column": "name",
            "sort_direction": "asc"
        }
        
        if search_term:
            params["search_term"] = search_term
        if categories:
            params["categories"] = categories
            
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            return response.json()
    
    async def get_offers(self, page: int = 1, per_page: int = 30,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None,
                        categories: Optional[str] = None,
                        campaigns: Optional[str] = None) -> Dict[str, Any]:
        """Fetch offers from Cuelinks API"""
        url = f"{self.base_url}/offers.json"
        
        # Default date range - today to one month from today
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if not end_date:
            end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        params = {
            "page": page,
            "per_page": per_page,
            "start_date": start_date,
            "end_date": end_date
        }
        
        if categories:
            params["categories"] = categories
        if campaigns:
            params["campaigns"] = campaigns
            
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            return response.json()
    
    async def get_transactions(self, page: int = 1, per_page: int = 30,
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None,
                              sub_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch transactions from Cuelinks API"""
        url = f"{self.base_url}/transactions.json"
        
        # Default date range - yesterday to today
        if not start_date:
            start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        params = {
            "page": page,
            "per_page": per_page,
            "start_date": start_date,
            "end_date": end_date
        }
        
        if sub_id:
            params["sub_id"] = sub_id
            
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            return response.json()
            
    async def get_campaign_by_id(self, campaign_id: int) -> Dict[str, Any]:
        """Fetch a specific campaign by ID"""
        url = f"{self.base_url}/campaigns/{campaign_id}.json"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers)
                if response.status_code == 200:
                    return response.json().get("campaign", {})
                return {}
            except Exception:
                return {}
    
    async def get_link(self, url: str, shorten: bool = False,
                      subid: Optional[str] = None) -> Dict[str, Any]:
        """Get affiliate URL for a plain URL"""
        api_url = f"{self.base_url}/links.json"
        params = {
            "url": url,
            "shorten": str(shorten).lower()
        }
        
        if subid:
            params["subid"] = subid
            
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, headers=self.headers, params=params)
            return response.json()
    
    async def apply_for_campaign(self, campaign_id: int, traffic_source: str,
                                promotion_details: str) -> Dict[str, Any]:
        """Apply for a campaign that requires approval"""
        url = f"{self.base_url}/apply_for_campaign.json"
        data = {
            "campaign_id": campaign_id,
            "traffic_source": traffic_source,
            "promotion_details": promotion_details
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=data)
            return response.json()

# Global instance
cuelinks_service = CuelinksService()
