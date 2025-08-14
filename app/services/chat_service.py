from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.database import Offer, Campaign, ChatMessage
import json
import re

class ChatService:
    def __init__(self, db: Session):
        self.db = db
    
    def process_user_query(self, user_message: str, session_id: str) -> str:
        """Process user query and return relevant response"""
        user_message_lower = user_message.lower()
        
        # Check for greeting
        if any(greeting in user_message_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            response = "Hello! Welcome to our affiliate website. I can help you find amazing offers and deals. What are you looking for today?"
        
        # Check for category-specific queries
        elif any(keyword in user_message_lower for keyword in ['fashion', 'clothes', 'dress', 'shirt', 'shoes']):
            response = self._get_category_offers("Fashion", user_message)
        
        elif any(keyword in user_message_lower for keyword in ['electronics', 'mobile', 'laptop', 'phone', 'computer', 'gadget']):
            response = self._get_category_offers("Electronics", user_message)
        
        elif any(keyword in user_message_lower for keyword in ['food', 'grocery', 'restaurant', 'delivery']):
            response = self._get_category_offers("Food & Grocery", user_message)
        
        elif any(keyword in user_message_lower for keyword in ['travel', 'flight', 'hotel', 'booking']):
            response = self._get_category_offers("Travel", user_message)
        
        elif any(keyword in user_message_lower for keyword in ['beauty', 'cosmetics', 'skincare', 'makeup']):
            response = self._get_category_offers("Health & Beauty", user_message)
        
        # Check for discount/offer queries
        elif any(keyword in user_message_lower for keyword in ['discount', 'offer', 'deal', 'sale', 'coupon']):
            response = self._get_discount_offers(user_message)
        
        # Check for specific brand queries
        elif any(keyword in user_message_lower for keyword in ['flipkart', 'amazon', 'myntra', 'paytm']):
            response = self._get_brand_offers(user_message)
        
        # General help
        elif any(keyword in user_message_lower for keyword in ['help', 'what can you do', 'assistance']):
            response = """I can help you with:
            
🛍️ Finding offers by category (Fashion, Electronics, Travel, etc.)
💰 Searching for discounts and deals
🏪 Getting brand-specific offers
🔗 Generating affiliate links
📊 Checking latest campaigns

Just ask me about any product or category you're interested in!"""
        
        else:
            response = self._search_general_offers(user_message)
        
        # Save chat message to database
        chat_message = ChatMessage(
            user_message=user_message,
            bot_response=response,
            session_id=session_id
        )
        self.db.add(chat_message)
        self.db.commit()
        
        return response
    
    def _get_category_offers(self, category: str, user_message: str) -> str:
        """Get offers for a specific category"""
        # Query offers by category
        offers = self.db.query(Offer).filter(
            Offer.categories.contains(category),
            Offer.status == "live"
        ).limit(5).all()
        
        if offers:
            response = f"Here are some great {category} offers I found:\n\n"
            for offer in offers:
                response += f"🎯 **{offer.title}**\n"
                if offer.description:
                    # Clean HTML tags from description
                    clean_desc = re.sub('<.*?>', '', offer.description)
                    response += f"   {clean_desc[:100]}...\n"
                if offer.coupon_code:
                    response += f"   💳 Coupon: {offer.coupon_code}\n"
                response += f"   🔗 [Get Deal]({offer.affiliate_url})\n\n"
        else:
            response = f"I don't have any live {category} offers right now, but I'm constantly updating our deals. Please check back soon!"
        
        return response
    
    def _get_discount_offers(self, user_message: str) -> str:
        """Get discount offers"""
        offers = self.db.query(Offer).filter(
            Offer.offer_type == "discount",
            Offer.status == "live"
        ).limit(5).all()
        
        if offers:
            response = "Here are some amazing discount offers:\n\n"
            for offer in offers:
                response += f"💸 **{offer.title}**\n"
                if offer.description:
                    clean_desc = re.sub('<.*?>', '', offer.description)
                    response += f"   {clean_desc[:100]}...\n"
                if offer.coupon_code:
                    response += f"   💳 Coupon: {offer.coupon_code}\n"
                response += f"   🔗 [Get Deal]({offer.affiliate_url})\n\n"
        else:
            response = "No discount offers available right now, but I'm constantly updating our deals!"
        
        return response
    
    def _get_brand_offers(self, user_message: str) -> str:
        """Get offers for specific brands"""
        user_message_lower = user_message.lower()
        
        # Extract brand name
        brand_keywords = {
            'flipkart': 'Flipkart',
            'amazon': 'Amazon',
            'myntra': 'Myntra',
            'paytm': 'Paytm',
            'croma': 'Croma',
            'pepperfry': 'Pepperfry'
        }
        
        brand_name = None
        for keyword, brand in brand_keywords.items():
            if keyword in user_message_lower:
                brand_name = brand
                break
        
        if brand_name:
            # Get campaign by brand name
            campaign = self.db.query(Campaign).filter(
                Campaign.name.ilike(f"%{brand_name}%")
            ).first()
            
            if campaign:
                offers = self.db.query(Offer).filter(
                    Offer.campaign_id == campaign.campaign_id,
                    Offer.status == "live"
                ).limit(5).all()
                
                if offers:
                    response = f"Here are the latest {brand_name} offers:\n\n"
                    for offer in offers:
                        response += f"🛒 **{offer.title}**\n"
                        if offer.description:
                            clean_desc = re.sub('<.*?>', '', offer.description)
                            response += f"   {clean_desc[:100]}...\n"
                        if offer.coupon_code:
                            response += f"   💳 Coupon: {offer.coupon_code}\n"
                        response += f"   🔗 [Shop Now]({offer.affiliate_url})\n\n"
                else:
                    response = f"No live offers available for {brand_name} right now."
            else:
                response = f"I couldn't find any offers for {brand_name} at the moment."
        else:
            response = "I couldn't identify the brand you're looking for. Could you please specify the brand name?"
        
        return response
    
    def _search_general_offers(self, user_message: str) -> str:
        """Search for offers based on general keywords"""
        # Extract keywords from user message
        keywords = user_message.lower().split()
        
        # Search in offer titles and descriptions
        offers = []
        for keyword in keywords:
            if len(keyword) > 3:  # Only search for meaningful keywords
                found_offers = self.db.query(Offer).filter(
                    (Offer.title.ilike(f"%{keyword}%")) |
                    (Offer.description.ilike(f"%{keyword}%")),
                    Offer.status == "live"
                ).limit(3).all()
                offers.extend(found_offers)
        
        # Remove duplicates
        unique_offers = list({offer.id: offer for offer in offers}.values())[:5]
        
        if unique_offers:
            response = "I found these offers that might interest you:\n\n"
            for offer in unique_offers:
                response += f"✨ **{offer.title}**\n"
                if offer.description:
                    clean_desc = re.sub('<.*?>', '', offer.description)
                    response += f"   {clean_desc[:100]}...\n"
                if offer.coupon_code:
                    response += f"   💳 Coupon: {offer.coupon_code}\n"
                response += f"   🔗 [Check it out]({offer.affiliate_url})\n\n"
        else:
            response = """I couldn't find specific offers for your query, but here are some ways I can help:

🔍 Try searching for:
• Category names (Fashion, Electronics, Travel, etc.)
• Brand names (Amazon, Flipkart, Myntra, etc.)
• Product types (mobile, laptop, shoes, etc.)
• Deal types (discount, cashback, offers)

Would you like me to show you our latest offers instead?"""
        
        return response
