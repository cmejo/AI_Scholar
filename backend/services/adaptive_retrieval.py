"""
Adaptive Retrieval System

This service implements personalized retrieval that adapts based on user history,
preferences, and interaction patterns to provide increasingly relevant results.
"""
import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
from sqlalchemy.orm import Session

from core.database import get_db, UserProfile, DocumentTag, AnalyticsEvent, Message, Document, Conversation
from services.vector_store import VectorStoreService
from services.user_profile_service import UserProfileManager
from models.schemas import PersonalizationSettings

logger = logging.getLogger(__name__)

class AdaptiveRetriever:
    """
    Adaptive retrieval system that personalizes search results based on user history,
    preferences, and interaction patterns.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.vector_store = VectorStoreService()
        self.profile_manager = UserProfileManager(db)
        self.default_settings = PersonalizationSettings()
        
    async def personalized_search(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        personalization_level: float = 1.0,
        settings: Optional[PersonalizationSettings] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform personalized semantic search with adaptive ranking.
        
        Args:
            query: Search query
            user_id: User identifier
            limit: Maximum number of results
            personalization_level: How much to apply personalization (0.0-1.0)
            settings: Personalization settings
            
        Returns:
            List of personalized search results
        """
        try:
            if settings is None:
                settings = self.default_settings
            
            # Get user profile and preferences
            user_profile = await self.profile_manager.get_user_profile(user_id)
            if not user_profile:
                logger.info(f"No user profile found for {user_id}, using default search")
                return await self.vector_store.semantic_search(query, user_id, limit)
            
            # Get base search results (more than needed for reranking)
            base_results = await self.vector_store.semantic_search(
                query, user_id, limit * 2
            )
            
            if not base_results:
                return []
            
            # Apply personalization if enabled
            if personalization_level > 0 and settings.enable_adaptive_retrieval:
                # Get personalization weights
                weights = await self._get_personalization_weights(user_id, query, user_profile)
                
                # Apply personalized ranking
                personalized_results = await self._apply_personalized_ranking(
                    base_results, query, user_id, weights, personalization_level
                )
                
                # Apply domain adaptation if enabled
                if settings.domain_adaptation:
                    personalized_results = await self._apply_domain_adaptation(
                        personalized_results, user_id, user_profile
                    )
                
                # Learn from this search for future improvements
                await self._learn_from_search(user_id, query, personalized_results[:limit])
                
                return personalized_results[:limit]
            else:
                return base_results[:limit]
                
        except Exception as e:
            logger.error(f"Error in personalized search: {str(e)}")
            # Fallback to basic search
            return await self.vector_store.semantic_search(query, user_id, limit)
    
    async def _get_personalization_weights(
        self,
        user_id: str,
        query: str,
        user_profile: Any
    ) -> Dict[str, float]:
        """Get personalization weights based on user profile and query context."""
        try:
            # Base weights from user profile service
            base_weights = await self.profile_manager.get_personalization_weights(user_id)
            
            # Query-specific adjustments
            query_weights = await self._analyze_query_context(query, user_id)
            
            # Historical performance weights
            historical_weights = await self._get_historical_performance_weights(user_id, query)
            
            # Combine weights with appropriate scaling
            combined_weights = {
                "domain_preference": self._combine_weight_values(
                    base_weights.get("domain_weights", {}),
                    query_weights.get("domain_signals", {}),
                    historical_weights.get("domain_performance", {})
                ),
                "content_type_preference": query_weights.get("content_type_signals", {}),
                "recency_preference": base_weights.get("recency_weight", 0.5),
                "complexity_preference": base_weights.get("complexity_preference", 0.6),
                "source_quality_weight": base_weights.get("satisfaction_weight", 0.7),
                "interaction_boost": historical_weights.get("interaction_boost", {}),
                "feedback_adjustment": historical_weights.get("feedback_adjustment", 1.0)
            }
            
            return combined_weights
            
        except Exception as e:
            logger.error(f"Error getting personalization weights: {str(e)}")
            return self._get_default_weights()
    
    async def _analyze_query_context(self, query: str, user_id: str) -> Dict[str, Any]:
        """Analyze query to extract contextual signals for personalization."""
        try:
            query_lower = query.lower()
            
            # Domain signals from query keywords
            domain_keywords = {
                "technology": ["software", "programming", "computer", "tech", "algorithm", "data", "ai", "machine learning"],
                "science": ["research", "study", "experiment", "hypothesis", "theory", "analysis", "scientific"],
                "business": ["market", "strategy", "finance", "management", "revenue", "profit", "business"],
                "medicine": ["health", "medical", "patient", "treatment", "diagnosis", "clinical", "healthcare"],
                "education": ["learning", "teaching", "student", "curriculum", "academic", "school", "education"],
                "law": ["legal", "court", "law", "regulation", "compliance", "contract", "judicial"]
            }
            
            domain_signals = {}
            for domain, keywords in domain_keywords.items():
                score = sum(1 for keyword in keywords if keyword in query_lower)
                if score > 0:
                    domain_signals[domain] = min(score / len(keywords), 1.0)
            
            # Content type signals
            content_type_signals = {}
            if any(word in query_lower for word in ["example", "case study", "tutorial"]):
                content_type_signals["practical"] = 0.8
            if any(word in query_lower for word in ["theory", "concept", "definition"]):
                content_type_signals["theoretical"] = 0.8
            if any(word in query_lower for word in ["how to", "step by step", "guide"]):
                content_type_signals["instructional"] = 0.9
            
            # Complexity signals
            complexity_score = 0.5  # Default
            if len(query.split()) > 10:
                complexity_score += 0.2
            if any(word in query_lower for word in ["advanced", "complex", "detailed", "comprehensive"]):
                complexity_score += 0.3
            if any(word in query_lower for word in ["simple", "basic", "introduction", "overview"]):
                complexity_score -= 0.2
            
            complexity_score = max(0.1, min(1.0, complexity_score))
            
            return {
                "domain_signals": domain_signals,
                "content_type_signals": content_type_signals,
                "complexity_signal": complexity_score,
                "query_length": len(query),
                "question_type": self._classify_question_type(query)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing query context: {str(e)}")
            return {}
    
    def _classify_question_type(self, query: str) -> str:
        """Classify the type of question being asked."""
        query_lower = query.lower()
        
        if query_lower.startswith(("what", "define", "explain")):
            return "definitional"
        elif query_lower.startswith(("how", "steps", "process")):
            return "procedural"
        elif query_lower.startswith(("why", "reason", "cause")):
            return "causal"
        elif query_lower.startswith(("compare", "difference", "versus")):
            return "comparative"
        elif "?" in query:
            return "interrogative"
        else:
            return "informational"
    
    async def _get_historical_performance_weights(
        self,
        user_id: str,
        query: str
    ) -> Dict[str, Any]:
        """Get weights based on historical search performance."""
        try:
            # Get recent user interactions by joining with conversations
            recent_messages = self.db.query(Message).join(
                Conversation, Message.conversation_id == Conversation.id
            ).filter(
                Conversation.user_id == user_id,
                Message.created_at >= datetime.utcnow() - timedelta(days=30)
            ).order_by(Message.created_at.desc()).limit(100).all()
            
            if not recent_messages:
                return {}
            
            # Analyze document interaction patterns
            document_interactions = defaultdict(int)
            domain_performance = defaultdict(list)
            
            for message in recent_messages:
                if message.sources:
                    try:
                        sources = json.loads(message.sources) if isinstance(message.sources, str) else message.sources
                        for source in sources:
                            doc_id = source.get("document_id")
                            if doc_id:
                                document_interactions[doc_id] += 1
                                
                                # Get document tags for domain analysis
                                doc_tags = self.db.query(DocumentTag).filter(
                                    DocumentTag.document_id == doc_id,
                                    DocumentTag.tag_type == "domain"
                                ).all()
                                
                                for tag in doc_tags:
                                    # Use relevance as performance indicator
                                    relevance = source.get("relevance", 0.5)
                                    domain_performance[tag.tag_name].append(relevance)
                    except (json.JSONDecodeError, TypeError):
                        continue
            
            # Calculate interaction boost for frequently accessed documents
            interaction_boost = {}
            if document_interactions:
                max_interactions = max(document_interactions.values())
                for doc_id, count in document_interactions.items():
                    boost = min(count / max_interactions, 1.0) * 0.2  # Max 20% boost
                    interaction_boost[doc_id] = boost
            
            # Calculate domain performance scores
            domain_perf_scores = {}
            for domain, scores in domain_performance.items():
                if scores:
                    avg_score = sum(scores) / len(scores)
                    domain_perf_scores[domain] = avg_score
            
            return {
                "interaction_boost": interaction_boost,
                "domain_performance": domain_perf_scores,
                "feedback_adjustment": 1.0  # Placeholder for future feedback integration
            }
            
        except Exception as e:
            logger.error(f"Error getting historical performance weights: {str(e)}")
            return {}
    
    async def _apply_personalized_ranking(
        self,
        results: List[Dict[str, Any]],
        query: str,
        user_id: str,
        weights: Dict[str, Any],
        personalization_level: float
    ) -> List[Dict[str, Any]]:
        """Apply personalized ranking to search results."""
        try:
            personalized_results = []
            
            for result in results:
                # Start with base relevance score
                base_score = result.get("relevance", 0.0)
                personalized_score = base_score
                
                metadata = result.get("metadata", {})
                document_id = metadata.get("document_id")
                
                # Apply domain preference weighting
                domain_boost = await self._calculate_domain_boost(
                    document_id, weights.get("domain_preference", {}), metadata
                )
                personalized_score += domain_boost * personalization_level * 0.3
                
                # Apply interaction history boost
                interaction_boost = weights.get("interaction_boost", {}).get(document_id, 0)
                personalized_score += interaction_boost * personalization_level
                
                # Apply content type preference
                content_type_boost = self._calculate_content_type_boost(
                    result, weights.get("content_type_preference", {})
                )
                personalized_score += content_type_boost * personalization_level * 0.2
                
                # Apply recency preference
                recency_boost = self._calculate_recency_boost(
                    metadata, weights.get("recency_preference", 0.5)
                )
                personalized_score += recency_boost * personalization_level * 0.1
                
                # Apply complexity preference
                complexity_boost = self._calculate_complexity_boost(
                    result, weights.get("complexity_preference", 0.6)
                )
                personalized_score += complexity_boost * personalization_level * 0.15
                
                # Apply source quality weighting
                quality_boost = self._calculate_quality_boost(
                    metadata, weights.get("source_quality_weight", 0.7)
                )
                personalized_score += quality_boost * personalization_level * 0.1
                
                # Apply feedback adjustment
                feedback_adjustment = weights.get("feedback_adjustment", 1.0)
                personalized_score *= feedback_adjustment
                
                # Ensure score stays within reasonable bounds
                personalized_score = max(0.0, min(1.0, personalized_score))
                
                # Create enhanced result
                enhanced_result = result.copy()
                enhanced_result["personalized_score"] = personalized_score
                enhanced_result["personalization_factors"] = {
                    "domain_boost": domain_boost,
                    "interaction_boost": interaction_boost,
                    "content_type_boost": content_type_boost,
                    "recency_boost": recency_boost,
                    "complexity_boost": complexity_boost,
                    "quality_boost": quality_boost,
                    "feedback_adjustment": feedback_adjustment
                }
                
                personalized_results.append(enhanced_result)
            
            # Sort by personalized score
            personalized_results.sort(key=lambda x: x["personalized_score"], reverse=True)
            
            return personalized_results
            
        except Exception as e:
            logger.error(f"Error applying personalized ranking: {str(e)}")
            return results
    
    async def _calculate_domain_boost(
        self,
        document_id: str,
        domain_preferences: Dict[str, float],
        metadata: Dict[str, Any]
    ) -> float:
        """Calculate domain-based boost for a result."""
        try:
            if not domain_preferences or not document_id:
                return 0.0
            
            # Get document tags
            doc_tags = self.db.query(DocumentTag).filter(
                DocumentTag.document_id == document_id,
                DocumentTag.tag_type.in_(["domain", "topic"])
            ).all()
            
            total_boost = 0.0
            tag_count = 0
            
            for tag in doc_tags:
                if tag.tag_name in domain_preferences:
                    # Weight by tag confidence and user preference
                    boost = (
                        domain_preferences[tag.tag_name] * 
                        tag.confidence_score * 
                        (1.0 if tag.tag_type == "domain" else 0.5)  # Domain tags weighted higher
                    )
                    total_boost += boost
                    tag_count += 1
            
            # Average the boost if multiple relevant tags
            return total_boost / max(tag_count, 1) if tag_count > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating domain boost: {str(e)}")
            return 0.0
    
    def _calculate_content_type_boost(
        self,
        result: Dict[str, Any],
        content_type_preferences: Dict[str, float]
    ) -> float:
        """Calculate content type boost based on user preferences."""
        try:
            if not content_type_preferences:
                return 0.0
            
            content = result.get("content", "").lower()
            total_boost = 0.0
            
            # Check for practical content indicators
            if "practical" in content_type_preferences:
                practical_indicators = ["example", "case study", "implementation", "tutorial", "demo"]
                if any(indicator in content for indicator in practical_indicators):
                    total_boost += content_type_preferences["practical"] * 0.1
            
            # Check for theoretical content indicators
            if "theoretical" in content_type_preferences:
                theoretical_indicators = ["theory", "concept", "definition", "principle", "framework"]
                if any(indicator in content for indicator in theoretical_indicators):
                    total_boost += content_type_preferences["theoretical"] * 0.1
            
            # Check for instructional content indicators
            if "instructional" in content_type_preferences:
                instructional_indicators = ["how to", "step", "guide", "instruction", "method"]
                if any(indicator in content for indicator in instructional_indicators):
                    total_boost += content_type_preferences["instructional"] * 0.1
            
            return min(total_boost, 0.2)  # Cap at 20% boost
            
        except Exception as e:
            logger.error(f"Error calculating content type boost: {str(e)}")
            return 0.0
    
    def _calculate_recency_boost(
        self,
        metadata: Dict[str, Any],
        recency_preference: float
    ) -> float:
        """Calculate recency boost based on user preference."""
        try:
            # This would require document creation/modification dates
            # For now, return a small boost based on preference
            return (recency_preference - 0.5) * 0.05  # Small adjustment
            
        except Exception as e:
            logger.error(f"Error calculating recency boost: {str(e)}")
            return 0.0
    
    def _calculate_complexity_boost(
        self,
        result: Dict[str, Any],
        complexity_preference: float
    ) -> float:
        """Calculate complexity boost based on content and user preference."""
        try:
            content = result.get("content", "")
            content_length = len(content)
            
            # Estimate complexity based on content characteristics
            complexity_score = 0.5  # Base complexity
            
            # Length-based complexity
            if content_length > 1000:
                complexity_score += 0.2
            elif content_length < 300:
                complexity_score -= 0.2
            
            # Technical term density (rough estimate)
            technical_indicators = ["algorithm", "implementation", "architecture", "framework", "methodology"]
            technical_count = sum(1 for term in technical_indicators if term in content.lower())
            complexity_score += min(technical_count * 0.1, 0.3)
            
            # Calculate boost based on alignment with user preference
            complexity_alignment = 1.0 - abs(complexity_score - complexity_preference)
            return complexity_alignment * 0.1  # Max 10% boost
            
        except Exception as e:
            logger.error(f"Error calculating complexity boost: {str(e)}")
            return 0.0
    
    def _calculate_quality_boost(
        self,
        metadata: Dict[str, Any],
        quality_weight: float
    ) -> float:
        """Calculate quality boost based on source characteristics."""
        try:
            # Quality indicators from metadata
            quality_score = 0.5  # Base quality
            
            # Document name quality indicators
            doc_name = metadata.get("document_name", "").lower()
            if any(indicator in doc_name for indicator in ["official", "guide", "manual", "documentation"]):
                quality_score += 0.2
            
            # Content length as quality indicator (moderate length preferred)
            content_length = metadata.get("content_length", 0)
            if 200 <= content_length <= 1500:
                quality_score += 0.1
            
            # Apply user's quality weight preference
            return (quality_score - 0.5) * quality_weight * 0.1
            
        except Exception as e:
            logger.error(f"Error calculating quality boost: {str(e)}")
            return 0.0
    
    async def _apply_domain_adaptation(
        self,
        results: List[Dict[str, Any]],
        user_id: str,
        user_profile: Any
    ) -> List[Dict[str, Any]]:
        """Apply domain-specific adaptations to results."""
        try:
            domain_expertise = user_profile.domain_expertise or {}
            
            if not domain_expertise:
                return results
            
            # Find user's strongest domain
            primary_domain = max(domain_expertise.items(), key=lambda x: x[1])[0] if domain_expertise else None
            
            if not primary_domain:
                return results
            
            # Apply domain-specific ranking adjustments
            adapted_results = []
            for result in results:
                adapted_result = result.copy()
                
                # Check if result is from user's primary domain
                document_id = result.get("metadata", {}).get("document_id")
                if document_id:
                    doc_tags = self.db.query(DocumentTag).filter(
                        DocumentTag.document_id == document_id,
                        DocumentTag.tag_type == "domain",
                        DocumentTag.tag_name == primary_domain
                    ).first()
                    
                    if doc_tags:
                        # Boost results from user's expertise domain
                        current_score = adapted_result.get("personalized_score", adapted_result.get("relevance", 0))
                        domain_boost = domain_expertise[primary_domain] * 0.1
                        adapted_result["personalized_score"] = min(1.0, current_score + domain_boost)
                        adapted_result["domain_adapted"] = True
                
                adapted_results.append(adapted_result)
            
            # Re-sort by updated scores
            adapted_results.sort(key=lambda x: x.get("personalized_score", x.get("relevance", 0)), reverse=True)
            
            return adapted_results
            
        except Exception as e:
            logger.error(f"Error applying domain adaptation: {str(e)}")
            return results
    
    async def _learn_from_search(
        self,
        user_id: str,
        query: str,
        results: List[Dict[str, Any]]
    ) -> None:
        """Learn from search interaction for future improvements."""
        try:
            # Track search analytics
            search_event = {
                "query": query,
                "results_count": len(results),
                "top_domains": self._extract_top_domains(results),
                "personalization_applied": any(r.get("personalized_score") for r in results),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store analytics event
            analytics_event = AnalyticsEvent(
                user_id=user_id,
                event_type="adaptive_search",
                event_data=search_event
            )
            
            self.db.add(analytics_event)
            self.db.commit()
            
            logger.debug(f"Logged adaptive search for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error learning from search: {str(e)}")
            self.db.rollback()
    
    def _extract_top_domains(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract top domains from search results."""
        try:
            domain_counts = Counter()
            
            for result in results[:5]:  # Top 5 results
                document_id = result.get("metadata", {}).get("document_id")
                if document_id:
                    doc_tags = self.db.query(DocumentTag).filter(
                        DocumentTag.document_id == document_id,
                        DocumentTag.tag_type == "domain"
                    ).all()
                    
                    for tag in doc_tags:
                        domain_counts[tag.tag_name] += 1
            
            return [domain for domain, _ in domain_counts.most_common(3)]
            
        except Exception as e:
            logger.error(f"Error extracting top domains: {str(e)}")
            return []
    
    def _combine_weight_values(self, *weight_dicts: Dict[str, float]) -> Dict[str, float]:
        """Combine multiple weight dictionaries with averaging."""
        combined = defaultdict(list)
        
        for weight_dict in weight_dicts:
            if weight_dict:
                for key, value in weight_dict.items():
                    combined[key].append(value)
        
        # Average the values
        result = {}
        for key, values in combined.items():
            result[key] = sum(values) / len(values)
        
        return result
    
    def _get_default_weights(self) -> Dict[str, Any]:
        """Get default personalization weights."""
        return {
            "domain_preference": {},
            "content_type_preference": {},
            "recency_preference": 0.5,
            "complexity_preference": 0.6,
            "source_quality_weight": 0.7,
            "interaction_boost": {},
            "feedback_adjustment": 1.0
        }
    
    async def get_personalization_stats(self, user_id: str) -> Dict[str, Any]:
        """Get personalization statistics for a user."""
        try:
            # Get recent search events
            recent_searches = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.event_type == "adaptive_search",
                AnalyticsEvent.timestamp >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            if not recent_searches:
                return {"message": "No recent search data available"}
            
            # Analyze personalization effectiveness
            total_searches = len(recent_searches)
            personalized_searches = sum(
                1 for search in recent_searches 
                if search.event_data.get("personalization_applied", False)
            )
            
            # Extract domain patterns
            all_domains = []
            for search in recent_searches:
                domains = search.event_data.get("top_domains", [])
                all_domains.extend(domains)
            
            domain_distribution = Counter(all_domains)
            
            return {
                "total_searches": total_searches,
                "personalized_searches": personalized_searches,
                "personalization_rate": personalized_searches / total_searches if total_searches > 0 else 0,
                "top_domains": dict(domain_distribution.most_common(5)),
                "avg_results_per_search": sum(
                    search.event_data.get("results_count", 0) for search in recent_searches
                ) / total_searches if total_searches > 0 else 0,
                "period_days": 30
            }
            
        except Exception as e:
            logger.error(f"Error getting personalization stats: {str(e)}")
            return {"error": str(e)}

class RetrievalOptimizer:
    """
    Optimizer for retrieval strategies based on user feedback and performance metrics.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.adaptive_retriever = AdaptiveRetriever(db)
    
    async def optimize_for_user(
        self,
        user_id: str,
        feedback_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Optimize retrieval strategy for a specific user based on feedback.
        
        Args:
            user_id: User identifier
            feedback_data: List of feedback items with ratings and context
            
        Returns:
            Optimization results and updated settings
        """
        try:
            # Analyze feedback patterns
            feedback_analysis = self._analyze_feedback_patterns(feedback_data)
            
            # Get current user profile
            profile_manager = UserProfileManager(self.db)
            user_profile = await profile_manager.get_user_profile(user_id)
            
            if not user_profile:
                return {"error": "User profile not found"}
            
            # Generate optimization recommendations
            recommendations = await self._generate_optimization_recommendations(
                feedback_analysis, user_profile
            )
            
            # Apply optimizations if confidence is high enough
            if recommendations.get("confidence", 0) > 0.7:
                await self._apply_optimizations(user_id, recommendations)
                
                return {
                    "optimizations_applied": True,
                    "recommendations": recommendations,
                    "confidence": recommendations["confidence"]
                }
            else:
                return {
                    "optimizations_applied": False,
                    "recommendations": recommendations,
                    "confidence": recommendations["confidence"],
                    "message": "Confidence too low to apply automatic optimizations"
                }
                
        except Exception as e:
            logger.error(f"Error optimizing retrieval for user {user_id}: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_feedback_patterns(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in user feedback."""
        if not feedback_data:
            return {}
        
        # Analyze rating patterns
        ratings = [item.get("rating", 0) for item in feedback_data if item.get("rating")]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Analyze domain preferences from highly rated items
        high_rated_domains = []
        low_rated_domains = []
        
        for item in feedback_data:
            rating = item.get("rating", 0)
            domains = item.get("domains", [])
            
            if rating >= 4:  # High rating
                high_rated_domains.extend(domains)
            elif rating <= 2:  # Low rating
                low_rated_domains.extend(domains)
        
        return {
            "avg_rating": avg_rating,
            "total_feedback": len(feedback_data),
            "preferred_domains": Counter(high_rated_domains).most_common(3),
            "avoided_domains": Counter(low_rated_domains).most_common(3),
            "satisfaction_trend": "improving" if avg_rating > 3.5 else "declining" if avg_rating < 2.5 else "stable"
        }
    
    async def _generate_optimization_recommendations(
        self,
        feedback_analysis: Dict[str, Any],
        user_profile: Any
    ) -> Dict[str, Any]:
        """Generate optimization recommendations based on analysis."""
        recommendations = {
            "domain_weight_adjustments": {},
            "complexity_adjustment": 0,
            "personalization_level_adjustment": 0,
            "confidence": 0.5
        }
        
        # Domain preference adjustments
        preferred_domains = feedback_analysis.get("preferred_domains", [])
        avoided_domains = feedback_analysis.get("avoided_domains", [])
        
        for domain, count in preferred_domains:
            if count >= 2:  # At least 2 positive feedbacks
                recommendations["domain_weight_adjustments"][domain] = 0.1
                recommendations["confidence"] += 0.1
        
        for domain, count in avoided_domains:
            if count >= 2:  # At least 2 negative feedbacks
                recommendations["domain_weight_adjustments"][domain] = -0.1
                recommendations["confidence"] += 0.1
        
        # Satisfaction-based adjustments
        avg_rating = feedback_analysis.get("avg_rating", 3)
        if avg_rating < 2.5:
            recommendations["personalization_level_adjustment"] = 0.2  # Increase personalization
            recommendations["confidence"] += 0.2
        elif avg_rating > 4.5:
            recommendations["personalization_level_adjustment"] = -0.1  # Slight decrease
            recommendations["confidence"] += 0.1
        
        return recommendations
    
    async def _apply_optimizations(
        self,
        user_id: str,
        recommendations: Dict[str, Any]
    ) -> None:
        """Apply optimization recommendations to user profile."""
        try:
            profile_manager = UserProfileManager(self.db)
            user_profile = await profile_manager.get_user_profile(user_id)
            
            if not user_profile:
                return
            
            # Update domain expertise based on recommendations
            domain_adjustments = recommendations.get("domain_weight_adjustments", {})
            current_expertise = user_profile.domain_expertise or {}
            
            for domain, adjustment in domain_adjustments.items():
                current_score = current_expertise.get(domain, 0.5)
                new_score = max(0.0, min(1.0, current_score + adjustment))
                current_expertise[domain] = new_score
            
            # Update user profile
            await profile_manager.track_user_interaction(
                user_id=user_id,
                interaction_type="optimization",
                interaction_data={
                    "recommendations_applied": recommendations,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Applied retrieval optimizations for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error applying optimizations: {str(e)}")
            raise