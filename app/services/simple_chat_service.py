"""
Simple fallback chat service when RAG is not available
"""
from typing import List, Dict, Any
from app.services.chat_service import ChatService

class SimpleChatService:
    """Simple chat service with basic keyword matching"""
    
    def __init__(self):
        self.categories = {
            'fashion': ['fashion', 'clothes', 'dress', 'shirt', 'shoes', 'bag', 'clothing'],
            'electronics': ['electronics', 'phone', 'laptop', 'computer', 'gadget', 'tech'],
            'travel': ['travel', 'hotel', 'flight', 'vacation', 'trip', 'booking'],
            'food': ['food', 'restaurant', 'grocery', 'delivery', 'cooking', 'recipe'],
            'health': ['health', 'beauty', 'skincare', 'wellness', 'fitness', 'vitamin'],
            'home': ['home', 'furniture', 'kitchen', 'garden', 'decoration', 'appliance']
        }
    
    def search_offers_simple(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Simple keyword-based offer search"""
        query_lower = query.lower()
        
        # Determine category
        detected_category = None
        for category, keywords in self.categories.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_category = category
                break
        
        # Return mock offers for the detected category
        if detected_category == 'fashion':
            return [
                {
                    'id': 1,
                    'title': 'Fashion Sale - Up to 50% Off',
                    'description': 'Discover the latest fashion trends with amazing discounts on clothing, shoes, and accessories.',
                    'image_url': '/static/images/fashion_1.jpg',
                    'categories': 'Fashion',
                    'coupon_code': 'FASHION50',
                    'affiliate_url': '#',
                    'similarity': 0.85
                },
                {
                    'id': 2,
                    'title': 'Summer Collection - Extra 30% Off',
                    'description': 'Beat the heat with our summer collection. Lightweight fabrics and trendy designs.',
                    'image_url': '/static/images/fashion_2.jpg',
                    'categories': 'Fashion',
                    'coupon_code': 'SUMMER30',
                    'affiliate_url': '#',
                    'similarity': 0.75
                }
            ]
        elif detected_category == 'electronics':
            return [
                {
                    'id': 3,
                    'title': 'Electronics Mega Sale',
                    'description': 'Latest smartphones, laptops, and gadgets at unbeatable prices.',
                    'image_url': '/static/images/electronics_1.jpg',
                    'categories': 'Electronics',
                    'coupon_code': 'TECH25',
                    'affiliate_url': '#',
                    'similarity': 0.80
                }
            ]
        else:
            # General offers
            return [
                {
                    'id': 4,
                    'title': 'Special Deals Just for You',
                    'description': 'Explore our handpicked deals across all categories.',
                    'image_url': '/static/images/general_1.jpg',
                    'categories': 'Others',
                    'coupon_code': 'SAVE20',
                    'affiliate_url': '#',
                    'similarity': 0.60
                }
            ]
    
    def generate_simple_response(self, query: str, offers: List[Dict]) -> str:
        """Generate a simple response based on offers"""
        if not offers:
            return f"I'm currently searching for deals related to '{query}'. Please check back soon for updated offers!"
        
        response = f"Great news! I found {len(offers)} amazing deal{'s' if len(offers) > 1 else ''} for you:\n\n"
        
        for i, offer in enumerate(offers[:3], 1):
            response += f"{i}. **{offer['title']}**\n"
            response += f"   {offer['description'][:100]}...\n"
            if offer.get('coupon_code'):
                response += f"   💰 Use code: {offer['coupon_code']}\n"
            response += "\n"
        
        if len(offers) > 3:
            response += f"And {len(offers) - 3} more great deals available!"
        
        return response

# Global simple service instance
simple_chat_service = SimpleChatService()
