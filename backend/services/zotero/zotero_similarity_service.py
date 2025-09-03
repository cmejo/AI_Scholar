"""
Zotero Similarity and Recommendation Service
Implements vector embeddings, similarity detection, and recommendation engine
"""
import json
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import requests
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import pickle
import hashlib

from core.config import settings
from core.database import get_db
from models.zotero_models import ZoteroItem, ZoteroLibrary, ZoteroConnection

logger = logging.getLogger(__name__)


class ZoteroSimilarityService:
    """Service for similarity detection and recommendations between Zotero references"""
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.embedding_model = settings.EMBEDDING_MODEL
        self.tfidf_vectorizer = None
        self.embedding_cache = {}
        self.similarity_threshold = 0.3
        self.max_recommendations = 10
        
    async def generate_embeddings(
        self,
        item_id: str,
        user_id: str,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate vector embeddings for a reference
        
        Args:
            item_id: Zotero item ID
            user_id: User ID for access control
            force_regenerate: Whether to regenerate existing embeddings
            
        Returns:
            Dictionary containing embedding vectors and metadata
        """
        try:
            db = next(get_db())
            
            # Get the reference item with access control
            item = await self._get_user_item(db, item_id, user_id)
            if not item:
                raise ValueError(f"Item {item_id} not found or access denied")
            
            # Check if embeddings already exist and are current
            existing_embeddings = await self._get_stored_embeddings(db, item_id)
            if existing_embeddings and not force_regenerate:
                return existing_embeddings
            
            # Extract content for embedding generation
            content = self._extract_embedding_content(item)
            if not content.strip():
                return {
                    "item_id": item_id,
                    "error": "No content available for embedding generation"
                }
            
            # Generate different types of embeddings
            embeddings = {
                "item_id": item_id,
                "generation_timestamp": datetime.utcnow().isoformat(),
                "content_hash": hashlib.md5(content.encode()).hexdigest(),
                "embeddings": {}
            }
            
            # Generate semantic embeddings using LLM
            semantic_embedding = await self._generate_semantic_embedding(content)
            embeddings["embeddings"]["semantic"] = semantic_embedding
            
            # Generate TF-IDF embeddings for keyword-based similarity
            tfidf_embedding = await self._generate_tfidf_embedding(content, item)
            embeddings["embeddings"]["tfidf"] = tfidf_embedding
            
            # Generate metadata-based embeddings
            metadata_embedding = await self._generate_metadata_embedding(item)
            embeddings["embeddings"]["metadata"] = metadata_embedding
            
            # Store embeddings in item metadata
            await self._store_embeddings(db, item_id, embeddings)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings for item {item_id}: {e}")
            raise
    
    async def find_similar_references(
        self,
        item_id: str,
        user_id: str,
        similarity_types: List[str] = None,
        max_results: int = 10,
        min_similarity: float = 0.3
    ) -> Dict[str, Any]:
        """
        Find similar references to a given item
        
        Args:
            item_id: Reference item ID to find similarities for
            user_id: User ID for access control
            similarity_types: Types of similarity to compute (semantic, tfidf, metadata)
            max_results: Maximum number of similar items to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            Dictionary containing similar references with similarity scores
        """
        if similarity_types is None:
            similarity_types = ["semantic", "tfidf", "metadata"]
            
        try:
            db = next(get_db())
            
            # Get target item embeddings
            target_embeddings = await self.generate_embeddings(item_id, user_id)
            if "error" in target_embeddings:
                return target_embeddings
            
            # Get all user's items for comparison
            user_items = await self._get_user_items_with_embeddings(db, user_id, exclude_item_id=item_id)
            
            similarities = []
            
            for candidate_item in user_items:
                candidate_embeddings = candidate_item.get("embeddings", {})
                if not candidate_embeddings:
                    continue
                
                # Calculate similarity scores for each type
                similarity_scores = {}
                overall_score = 0.0
                
                for sim_type in similarity_types:
                    if sim_type in target_embeddings["embeddings"] and sim_type in candidate_embeddings:
                        score = await self._calculate_similarity(
                            target_embeddings["embeddings"][sim_type],
                            candidate_embeddings[sim_type],
                            sim_type
                        )
                        similarity_scores[sim_type] = score
                        overall_score += score
                
                if similarity_scores:
                    overall_score /= len(similarity_scores)
                    
                    if overall_score >= min_similarity:
                        similarities.append({
                            "item_id": candidate_item["item_id"],
                            "item_title": candidate_item.get("title", ""),
                            "item_type": candidate_item.get("item_type", ""),
                            "publication_year": candidate_item.get("publication_year"),
                            "creators": candidate_item.get("creators", []),
                            "overall_similarity": round(overall_score, 4),
                            "similarity_scores": similarity_scores,
                            "similarity_reasons": await self._generate_similarity_reasons(
                                target_embeddings, candidate_embeddings, similarity_scores
                            )
                        })
            
            # Sort by overall similarity and limit results
            similarities.sort(key=lambda x: x["overall_similarity"], reverse=True)
            similarities = similarities[:max_results]
            
            return {
                "target_item_id": item_id,
                "similarity_types": similarity_types,
                "min_similarity": min_similarity,
                "total_candidates": len(user_items),
                "similar_items_found": len(similarities),
                "similar_items": similarities,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error finding similar references for item {item_id}: {e}")
            raise
    
    async def generate_recommendations(
        self,
        user_id: str,
        library_id: Optional[str] = None,
        recommendation_types: List[str] = None,
        max_recommendations: int = 10
    ) -> Dict[str, Any]:
        """
        Generate personalized recommendations for a user
        
        Args:
            user_id: User ID
            library_id: Optional specific library to generate recommendations for
            recommendation_types: Types of recommendations (similar, trending, gap_filling)
            max_recommendations: Maximum number of recommendations
            
        Returns:
            Dictionary containing personalized recommendations
        """
        if recommendation_types is None:
            recommendation_types = ["similar", "trending", "gap_filling"]
            
        try:
            db = next(get_db())
            
            recommendations = {
                "user_id": user_id,
                "library_id": library_id,
                "recommendation_types": recommendation_types,
                "recommendations": {},
                "generation_timestamp": datetime.utcnow().isoformat()
            }
            
            # Get user's reading patterns and preferences
            user_profile = await self._build_user_profile(db, user_id, library_id)
            
            if "similar" in recommendation_types:
                recommendations["recommendations"]["similar"] = await self._generate_similar_recommendations(
                    db, user_id, user_profile, max_recommendations // len(recommendation_types)
                )
            
            if "trending" in recommendation_types:
                recommendations["recommendations"]["trending"] = await self._generate_trending_recommendations(
                    db, user_id, user_profile, max_recommendations // len(recommendation_types)
                )
            
            if "gap_filling" in recommendation_types:
                recommendations["recommendations"]["gap_filling"] = await self._generate_gap_filling_recommendations(
                    db, user_id, user_profile, max_recommendations // len(recommendation_types)
                )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations for user {user_id}: {e}")
            raise
    
    async def cluster_references(
        self,
        user_id: str,
        library_id: Optional[str] = None,
        num_clusters: Optional[int] = None,
        clustering_method: str = "kmeans"
    ) -> Dict[str, Any]:
        """
        Cluster references based on similarity
        
        Args:
            user_id: User ID
            library_id: Optional specific library to cluster
            num_clusters: Number of clusters (auto-determined if None)
            clustering_method: Clustering algorithm to use
            
        Returns:
            Dictionary containing clustering results
        """
        try:
            db = next(get_db())
            
            # Get user's items with embeddings
            user_items = await self._get_user_items_with_embeddings(db, user_id, library_id)
            
            if len(user_items) < 3:
                return {
                    "error": "Insufficient items for clustering (minimum 3 required)",
                    "item_count": len(user_items)
                }
            
            # Prepare embedding matrix
            embedding_matrix = []
            item_ids = []
            
            for item in user_items:
                embeddings = item.get("embeddings", {})
                if "semantic" in embeddings:
                    embedding_matrix.append(embeddings["semantic"])
                    item_ids.append(item["item_id"])
            
            if len(embedding_matrix) < 3:
                return {
                    "error": "Insufficient items with embeddings for clustering",
                    "items_with_embeddings": len(embedding_matrix)
                }
            
            # Determine optimal number of clusters if not specified
            if num_clusters is None:
                num_clusters = min(max(2, len(embedding_matrix) // 5), 10)
            
            # Perform clustering
            embedding_array = np.array(embedding_matrix)
            
            if clustering_method == "kmeans":
                clusterer = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
                cluster_labels = clusterer.fit_predict(embedding_array)
                cluster_centers = clusterer.cluster_centers_
            else:
                raise ValueError(f"Unsupported clustering method: {clustering_method}")
            
            # Organize results by cluster
            clusters = {}
            for i, (item_id, label) in enumerate(zip(item_ids, cluster_labels)):
                cluster_id = f"cluster_{label}"
                if cluster_id not in clusters:
                    clusters[cluster_id] = {
                        "cluster_id": cluster_id,
                        "cluster_label": label,
                        "items": [],
                        "cluster_topics": [],
                        "cluster_summary": ""
                    }
                
                # Find the original item data
                item_data = next((item for item in user_items if item["item_id"] == item_id), None)
                if item_data:
                    clusters[cluster_id]["items"].append({
                        "item_id": item_id,
                        "title": item_data.get("title", ""),
                        "item_type": item_data.get("item_type", ""),
                        "publication_year": item_data.get("publication_year"),
                        "creators": item_data.get("creators", [])
                    })
            
            # Generate cluster summaries and topics
            for cluster_id, cluster_data in clusters.items():
                cluster_data["cluster_topics"] = await self._extract_cluster_topics(cluster_data["items"])
                cluster_data["cluster_summary"] = await self._generate_cluster_summary(cluster_data["items"])
            
            return {
                "user_id": user_id,
                "library_id": library_id,
                "clustering_method": clustering_method,
                "num_clusters": num_clusters,
                "total_items": len(item_ids),
                "clusters": list(clusters.values()),
                "clustering_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error clustering references for user {user_id}: {e}")
            raise
    
    async def _generate_semantic_embedding(self, content: str) -> List[float]:
        """Generate semantic embedding using LLM"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": content[:2000]  # Limit content length
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("embedding", [])
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to generate semantic embedding: {e}")
            # Fallback to simple text-based embedding
            return self._generate_simple_embedding(content)
    
    def _generate_simple_embedding(self, content: str) -> List[float]:
        """Generate simple embedding as fallback"""
        # Simple hash-based embedding for fallback
        words = content.lower().split()
        embedding = [0.0] * 384  # Standard embedding size
        
        for i, word in enumerate(words[:100]):  # Limit to first 100 words
            hash_val = hash(word) % 384
            embedding[hash_val] += 1.0
        
        # Normalize
        norm = sum(x * x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    async def _generate_tfidf_embedding(self, content: str, item: ZoteroItem) -> Dict[str, Any]:
        """Generate TF-IDF based embedding"""
        try:
            # Combine title, abstract, and tags for TF-IDF
            tfidf_content = []
            if item.title:
                tfidf_content.append(item.title)
            if item.abstract_note:
                tfidf_content.append(item.abstract_note)
            if item.tags:
                tfidf_content.extend(item.tags)
            
            combined_content = " ".join(tfidf_content)
            
            # For now, return a simple keyword-based representation
            # In a full implementation, this would use a fitted TF-IDF vectorizer
            words = combined_content.lower().split()
            word_freq = {}
            for word in words:
                if len(word) > 3:  # Filter short words
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top keywords
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
            
            return {
                "keywords": [kw[0] for kw in top_keywords],
                "frequencies": [kw[1] for kw in top_keywords],
                "total_words": len(words)
            }
            
        except Exception as e:
            logger.warning(f"Failed to generate TF-IDF embedding: {e}")
            return {"keywords": [], "frequencies": [], "total_words": 0}
    
    async def _generate_metadata_embedding(self, item: ZoteroItem) -> Dict[str, Any]:
        """Generate metadata-based embedding"""
        metadata_features = {
            "item_type": item.item_type or "",
            "publication_year": item.publication_year or 0,
            "creator_count": len(item.creators) if item.creators else 0,
            "tag_count": len(item.tags) if item.tags else 0,
            "has_abstract": bool(item.abstract_note),
            "has_doi": bool(item.doi),
            "publication_title": item.publication_title or "",
            "publisher": item.publisher or ""
        }
        
        # Extract creator types and names
        creator_types = []
        creator_names = []
        if item.creators:
            for creator in item.creators:
                if isinstance(creator, dict):
                    creator_types.append(creator.get("creatorType", ""))
                    if creator.get("lastName"):
                        creator_names.append(creator["lastName"])
        
        metadata_features["creator_types"] = creator_types
        metadata_features["creator_names"] = creator_names
        
        return metadata_features
    
    async def _calculate_similarity(
        self,
        embedding1: Any,
        embedding2: Any,
        similarity_type: str
    ) -> float:
        """Calculate similarity between two embeddings"""
        try:
            if similarity_type == "semantic":
                if isinstance(embedding1, list) and isinstance(embedding2, list):
                    if len(embedding1) == len(embedding2):
                        # Cosine similarity
                        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
                        norm1 = sum(a * a for a in embedding1) ** 0.5
                        norm2 = sum(b * b for b in embedding2) ** 0.5
                        
                        if norm1 > 0 and norm2 > 0:
                            return dot_product / (norm1 * norm2)
                
            elif similarity_type == "tfidf":
                if isinstance(embedding1, dict) and isinstance(embedding2, dict):
                    keywords1 = set(embedding1.get("keywords", []))
                    keywords2 = set(embedding2.get("keywords", []))
                    
                    if keywords1 and keywords2:
                        intersection = len(keywords1.intersection(keywords2))
                        union = len(keywords1.union(keywords2))
                        return intersection / union if union > 0 else 0.0
                
            elif similarity_type == "metadata":
                if isinstance(embedding1, dict) and isinstance(embedding2, dict):
                    score = 0.0
                    comparisons = 0
                    
                    # Compare item types
                    if embedding1.get("item_type") == embedding2.get("item_type"):
                        score += 0.3
                    comparisons += 1
                    
                    # Compare publication years (closer years = higher similarity)
                    year1 = embedding1.get("publication_year", 0)
                    year2 = embedding2.get("publication_year", 0)
                    if year1 > 0 and year2 > 0:
                        year_diff = abs(year1 - year2)
                        year_similarity = max(0, 1 - year_diff / 20)  # 20-year window
                        score += year_similarity * 0.2
                    comparisons += 1
                    
                    # Compare creator overlap
                    creators1 = set(embedding1.get("creator_names", []))
                    creators2 = set(embedding2.get("creator_names", []))
                    if creators1 and creators2:
                        creator_overlap = len(creators1.intersection(creators2)) / len(creators1.union(creators2))
                        score += creator_overlap * 0.3
                    comparisons += 1
                    
                    # Compare publication titles
                    pub1 = embedding1.get("publication_title", "").lower()
                    pub2 = embedding2.get("publication_title", "").lower()
                    if pub1 and pub2 and pub1 == pub2:
                        score += 0.2
                    comparisons += 1
                    
                    return score / comparisons if comparisons > 0 else 0.0
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Error calculating {similarity_type} similarity: {e}")
            return 0.0
    
    def _extract_embedding_content(self, item: ZoteroItem) -> str:
        """Extract content for embedding generation"""
        content_parts = []
        
        if item.title:
            content_parts.append(item.title)
        
        if item.abstract_note:
            content_parts.append(item.abstract_note)
        
        if item.creators:
            authors = []
            for creator in item.creators:
                if isinstance(creator, dict):
                    name_parts = []
                    if creator.get("firstName"):
                        name_parts.append(creator["firstName"])
                    if creator.get("lastName"):
                        name_parts.append(creator["lastName"])
                    if name_parts:
                        authors.append(" ".join(name_parts))
            if authors:
                content_parts.append(" ".join(authors))
        
        if item.tags:
            if isinstance(item.tags, list):
                content_parts.append(" ".join(item.tags))
        
        return " ".join(content_parts)
    
    async def _get_user_item(self, db: Session, item_id: str, user_id: str) -> Optional[ZoteroItem]:
        """Get Zotero item with user access control"""
        return db.query(ZoteroItem).join(
            ZoteroLibrary, ZoteroItem.library_id == ZoteroLibrary.id
        ).join(
            ZoteroConnection, ZoteroLibrary.connection_id == ZoteroConnection.id
        ).filter(
            and_(
                ZoteroItem.id == item_id,
                ZoteroConnection.user_id == user_id,
                ZoteroItem.is_deleted == False
            )
        ).first()
    
    async def _get_user_items_with_embeddings(
        self,
        db: Session,
        user_id: str,
        library_id: Optional[str] = None,
        exclude_item_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get user's items that have embeddings"""
        query = db.query(ZoteroItem).join(
            ZoteroLibrary, ZoteroItem.library_id == ZoteroLibrary.id
        ).join(
            ZoteroConnection, ZoteroLibrary.connection_id == ZoteroConnection.id
        ).filter(
            and_(
                ZoteroConnection.user_id == user_id,
                ZoteroItem.is_deleted == False
            )
        )
        
        if library_id:
            query = query.filter(ZoteroLibrary.id == library_id)
        
        if exclude_item_id:
            query = query.filter(ZoteroItem.id != exclude_item_id)
        
        items = query.all()
        
        # Filter items that have embeddings and convert to dict format
        items_with_embeddings = []
        for item in items:
            if item.item_metadata and "embeddings" in item.item_metadata:
                items_with_embeddings.append({
                    "item_id": item.id,
                    "title": item.title,
                    "item_type": item.item_type,
                    "publication_year": item.publication_year,
                    "creators": item.creators,
                    "embeddings": item.item_metadata["embeddings"]["embeddings"]
                })
        
        return items_with_embeddings
    
    async def _get_stored_embeddings(self, db: Session, item_id: str) -> Optional[Dict[str, Any]]:
        """Get stored embeddings for an item"""
        item = db.query(ZoteroItem).filter(ZoteroItem.id == item_id).first()
        if item and item.item_metadata:
            return item.item_metadata.get("embeddings")
        return None
    
    async def _store_embeddings(
        self,
        db: Session,
        item_id: str,
        embeddings: Dict[str, Any]
    ) -> None:
        """Store embeddings in item metadata"""
        try:
            item = db.query(ZoteroItem).filter(ZoteroItem.id == item_id).first()
            if item:
                metadata = item.item_metadata or {}
                metadata["embeddings"] = embeddings
                item.item_metadata = metadata
                db.commit()
        except Exception as e:
            logger.error(f"Error storing embeddings for item {item_id}: {e}")
            db.rollback()
            raise
    
    async def _generate_similarity_reasons(
        self,
        target_embeddings: Dict[str, Any],
        candidate_embeddings: Dict[str, Any],
        similarity_scores: Dict[str, float]
    ) -> List[str]:
        """Generate human-readable reasons for similarity"""
        reasons = []
        
        for sim_type, score in similarity_scores.items():
            if score > 0.5:
                if sim_type == "semantic":
                    reasons.append(f"Similar content and themes (score: {score:.2f})")
                elif sim_type == "tfidf":
                    reasons.append(f"Shared keywords and terminology (score: {score:.2f})")
                elif sim_type == "metadata":
                    reasons.append(f"Similar publication characteristics (score: {score:.2f})")
        
        return reasons
    
    async def _build_user_profile(
        self,
        db: Session,
        user_id: str,
        library_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build user profile for recommendations"""
        # This is a simplified version - in practice, this would analyze
        # user's reading patterns, frequently accessed items, etc.
        return {
            "user_id": user_id,
            "library_id": library_id,
            "preferences": {
                "item_types": [],
                "topics": [],
                "time_periods": [],
                "authors": []
            }
        }
    
    async def _generate_similar_recommendations(
        self,
        db: Session,
        user_id: str,
        user_profile: Dict[str, Any],
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on similarity to user's items"""
        # Simplified implementation
        return []
    
    async def _generate_trending_recommendations(
        self,
        db: Session,
        user_id: str,
        user_profile: Dict[str, Any],
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on trending topics"""
        # Simplified implementation
        return []
    
    async def _generate_gap_filling_recommendations(
        self,
        db: Session,
        user_id: str,
        user_profile: Dict[str, Any],
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Generate recommendations to fill gaps in user's research"""
        # Simplified implementation
        return []
    
    async def _extract_cluster_topics(self, items: List[Dict[str, Any]]) -> List[str]:
        """Extract common topics from clustered items"""
        # Simplified implementation
        return ["Topic 1", "Topic 2"]
    
    async def _generate_cluster_summary(self, items: List[Dict[str, Any]]) -> str:
        """Generate summary for a cluster of items"""
        # Simplified implementation
        return f"Cluster of {len(items)} related research papers"