"""
Semantic Search Service
This service provides fast and accurate semantic search over offer embeddings.
"""

import logging
from typing import List, Dict, Any
import numpy as np
from sqlalchemy.orm import Session
from app.models.database import Offer, OfferEmbedding
from app.database import get_db_sync

logger = logging.getLogger(__name__)

class SemanticSearchService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        # Lazy import to avoid startup delays
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.offer_embeddings = {}
        self.offers_cache = {}
        self._load_data()

    def _load_data(self):
        """Load all offer embeddings and offer data from the database into memory."""
        logger.info("Loading offer embeddings and data into memory...")
        db = next(get_db_sync())
        try:
            embeddings = db.query(OfferEmbedding).all()
            # Assuming one embedding per offer for simplicity
            self.offer_embeddings = {emb.offer_id: np.array(emb.embedding) for emb in embeddings}

            all_offers = db.query(Offer).all()
            self.offers_cache = {offer.id: offer for offer in all_offers}
            logger.info(f"Loaded {len(self.offer_embeddings)} embeddings and {len(self.offers_cache)} offers.")
        finally:
            db.close()


    def search(self, query: str, top_k: int = 5):
        """Perform semantic search."""
        if not self.offer_embeddings:
            logger.warning("No offer embeddings loaded.")
            return [], "Sorry, no offers are available at the moment."

        query_embedding = self.model.encode(query, convert_to_tensor=False)
        
        offer_ids = list(self.offer_embeddings.keys())
        embeddings = np.array(list(self.offer_embeddings.values()))

        # Cosine similarity
        similarities = self._cosine_similarity(query_embedding, embeddings)[0]
        
        # Get top k results
        # argsort sorts in ascending order, so we take the last 'limit' elements and reverse them
        top_k_indices = np.argsort(similarities)[-top_k:][::-1]
        
        top_offer_ids = [offer_ids[i] for i in top_k_indices]
        top_similarities = [float(similarities[i]) for i in top_k_indices]

        results = self._get_offers_by_ids(top_offer_ids, top_similarities)

        # Separate offers with and without coupon codes
        offers_with_coupons = [offer for offer in results if offer.get("coupon_code")]
        offers_without_coupons = [offer for offer in results if not offer.get("coupon_code")]

        # Combine the lists with coupon offers first
        sorted_results = offers_with_coupons + offers_without_coupons

        if not sorted_results:
            response_message = f"I couldn't find any specific offers for '{query}'. Feel free to try another search!"
        else:
            response_message = f"I found {len(sorted_results)} great offers for you based on your search for '{query}'."
        
        return sorted_results, response_message

    def _get_offers_by_ids(self, ids: List[int], similarities: List[float]) -> List[Dict[str, Any]]:
        """Retrieve offer details from the in-memory cache."""
        results = []
        for offer_id, sim in zip(ids, similarities):
            offer = self.offers_cache.get(offer_id)
            if offer:
                results.append({
                    "id": offer.id,
                    "title": offer.title,
                    "description": offer.description,
                    "url": offer.url,
                    "affiliate_url": offer.affiliate_url,
                    "image_url": offer.image_url,
                    "coupon_code": offer.coupon_code,
                    "similarity": sim
                })
        return results

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> np.ndarray:
        """Calculate cosine similarity."""
        vec1 = vec1.reshape(1, -1) # Reshape for broadcasting
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2, axis=1)
        # handle potential division by zero
        norm2[norm2 == 0] = 1e-12
        return (vec1 @ vec2.T) / (norm1 * norm2)


# Singleton instance
# semantic_search_service = SemanticSearchService()

_semantic_search_service_instance = None

def get_semantic_search_service():
    global _semantic_search_service_instance
    if _semantic_search_service_instance is None:
        _semantic_search_service_instance = SemanticSearchService()
    return _semantic_search_service_instance
