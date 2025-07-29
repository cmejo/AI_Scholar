"""
Domain Adaptation Service

This service implements domain-specific customization for document processing,
retrieval strategies, and response generation based on user interaction patterns
and document characteristics.
"""
import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict, Counter
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from core.database import (
    UserProfile, DocumentTag, AnalyticsEvent, Message, Document, Conversation,
    DocumentChunkEnhanced, KnowledgeGraphEntity, KnowledgeGraphRelationship
)
from models.schemas import PersonalizationSettings, UserPreferences
from services.user_profile_service import UserProfileManager

logger = logging.getLogger(__name__)

class DomainAdapter:
    """
    Domain adaptation system that customizes retrieval and response strategies
    based on document types and user domain expertise.
    """
    
    # Domain-specific configuration
    DOMAIN_CONFIGS = {
        "technology": {
            "keywords": ["software", "programming", "computer", "tech", "algorithm", "data", "ai", "machine learning", "api", "framework"],
            "chunk_size": 800,  # Larger chunks for technical content
            "overlap_ratio": 0.15,
            "complexity_weight": 0.8,
            "recency_weight": 0.9,  # Tech content becomes outdated quickly
            "citation_style": "technical",
            "reasoning_emphasis": ["causal", "procedural"],
            "content_types": ["documentation", "tutorial", "specification", "code_example"]
        },
        "science": {
            "keywords": ["research", "study", "experiment", "hypothesis", "theory", "analysis", "scientific", "methodology"],
            "chunk_size": 1000,  # Larger chunks for detailed scientific content
            "overlap_ratio": 0.2,
            "complexity_weight": 0.9,
            "recency_weight": 0.6,  # Scientific knowledge is more stable
            "citation_style": "academic",
            "reasoning_emphasis": ["causal", "analogical", "evidence-based"],
            "content_types": ["paper", "journal", "research", "methodology"]
        },
        "business": {
            "keywords": ["market", "strategy", "finance", "management", "revenue", "profit", "business", "corporate"],
            "chunk_size": 600,  # Moderate chunks for business content
            "overlap_ratio": 0.1,
            "complexity_weight": 0.6,
            "recency_weight": 0.8,  # Business info can change frequently
            "citation_style": "business",
            "reasoning_emphasis": ["strategic", "analytical"],
            "content_types": ["report", "analysis", "case_study", "presentation"]
        },
        "medicine": {
            "keywords": ["health", "medical", "patient", "treatment", "diagnosis", "clinical", "healthcare", "therapeutic"],
            "chunk_size": 900,  # Detailed chunks for medical content
            "overlap_ratio": 0.25,  # High overlap for medical context
            "complexity_weight": 0.9,
            "recency_weight": 0.7,
            "citation_style": "medical",
            "reasoning_emphasis": ["causal", "evidence-based", "diagnostic"],
            "content_types": ["clinical_guide", "research", "case_study", "protocol"]
        },
        "education": {
            "keywords": ["learning", "teaching", "student", "curriculum", "academic", "school", "education", "pedagogy"],
            "chunk_size": 700,  # Moderate chunks for educational content
            "overlap_ratio": 0.15,
            "complexity_weight": 0.5,  # More accessible content
            "recency_weight": 0.5,
            "citation_style": "educational",
            "reasoning_emphasis": ["explanatory", "analogical"],
            "content_types": ["textbook", "lesson", "tutorial", "guide"]
        },
        "law": {
            "keywords": ["legal", "court", "law", "regulation", "compliance", "contract", "judicial", "statute"],
            "chunk_size": 1200,  # Large chunks for legal context
            "overlap_ratio": 0.3,  # High overlap for legal precision
            "complexity_weight": 0.9,
            "recency_weight": 0.8,  # Laws change frequently
            "citation_style": "legal",
            "reasoning_emphasis": ["precedent-based", "analytical"],
            "content_types": ["statute", "case_law", "regulation", "contract"]
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.profile_manager = UserProfileManager(db)
        
    async def detect_user_domains(self, user_id: str) -> Dict[str, float]:
        """
        Detect user's domain preferences from interaction patterns.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary of domain names to confidence scores
        """
        try:
            # Get user profile for existing domain expertise
            user_profile = await self.profile_manager.get_user_profile(user_id)
            existing_domains = user_profile.domain_expertise if user_profile else {}
            
            # Analyze recent interactions
            interaction_domains = await self._analyze_interaction_domains(user_id)
            
            # Analyze query patterns
            query_domains = await self._analyze_query_domains(user_id)
            
            # Analyze document access patterns
            document_domains = await self._analyze_document_domains(user_id)
            
            # Combine all domain signals
            combined_domains = self._combine_domain_signals(
                existing_domains, interaction_domains, query_domains, document_domains
            )
            
            # Normalize scores
            normalized_domains = self._normalize_domain_scores(combined_domains)
            
            logger.info(f"Detected domains for user {user_id}: {normalized_domains}")
            return normalized_domains
            
        except Exception as e:
            logger.error(f"Error detecting user domains: {str(e)}")
            return {}
    
    async def _analyze_interaction_domains(self, user_id: str) -> Dict[str, float]:
        """Analyze user interactions to detect domain preferences."""
        try:
            # Get recent analytics events
            recent_events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.timestamp >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            domain_scores = defaultdict(float)
            
            for event in recent_events:
                event_data = event.event_data or {}
                
                # Analyze search events
                if event.event_type == "adaptive_search":
                    top_domains = event_data.get("top_domains", [])
                    for domain in top_domains:
                        domain_scores[domain] += 0.2
                
                # Analyze chat events
                elif event.event_type == "chat_interaction":
                    query = event_data.get("query", "").lower()
                    for domain, config in self.DOMAIN_CONFIGS.items():
                        keyword_matches = sum(1 for keyword in config["keywords"] if keyword in query)
                        if keyword_matches > 0:
                            domain_scores[domain] += keyword_matches * 0.1
            
            return dict(domain_scores)
            
        except Exception as e:
            logger.error(f"Error analyzing interaction domains: {str(e)}")
            return {}
    
    async def _analyze_query_domains(self, user_id: str) -> Dict[str, float]:
        """Analyze user queries to detect domain preferences."""
        try:
            # Get recent messages by joining with conversations
            recent_messages = self.db.query(Message).join(
                Conversation, Message.conversation_id == Conversation.id
            ).filter(
                Conversation.user_id == user_id,
                Message.role == "user",
                Message.created_at >= datetime.utcnow() - timedelta(days=30)
            ).limit(100).all()
            
            domain_scores = defaultdict(float)
            
            for message in recent_messages:
                content = message.content.lower()
                
                # Check for domain-specific keywords
                for domain, config in self.DOMAIN_CONFIGS.items():
                    keyword_matches = sum(1 for keyword in config["keywords"] if keyword in content)
                    if keyword_matches > 0:
                        # Weight by keyword density
                        density = keyword_matches / len(content.split())
                        domain_scores[domain] += min(density * 10, 1.0)  # Cap at 1.0
            
            return dict(domain_scores)
            
        except Exception as e:
            logger.error(f"Error analyzing query domains: {str(e)}")
            return {}
    
    async def _analyze_document_domains(self, user_id: str) -> Dict[str, float]:
        """Analyze user's document access patterns to detect domain preferences."""
        try:
            # Get user's document interactions from profile
            user_profile = await self.profile_manager.get_user_profile(user_id)
            if not user_profile or not user_profile.interaction_history:
                return {}
            
            doc_interactions = user_profile.interaction_history.get("document_interactions", {})
            domain_scores = defaultdict(float)
            
            for doc_id, interaction in doc_interactions.items():
                # Get document tags
                doc_tags = self.db.query(DocumentTag).filter(
                    DocumentTag.document_id == doc_id,
                    DocumentTag.tag_type == "domain"
                ).all()
                
                # Weight by interaction frequency
                interaction_weight = min(interaction["access_count"] / 10.0, 1.0)
                
                for tag in doc_tags:
                    domain_scores[tag.tag_name] += interaction_weight * tag.confidence_score
            
            return dict(domain_scores)
            
        except Exception as e:
            logger.error(f"Error analyzing document domains: {str(e)}")
            return {}
    
    def _combine_domain_signals(self, *domain_dicts: Dict[str, float]) -> Dict[str, float]:
        """Combine multiple domain signal dictionaries."""
        combined = defaultdict(list)
        
        for domain_dict in domain_dicts:
            if domain_dict:
                for domain, score in domain_dict.items():
                    combined[domain].append(score)
        
        # Calculate weighted average
        result = {}
        for domain, scores in combined.items():
            if scores:
                # Give more weight to recent signals
                weights = [1.0, 0.8, 0.6, 0.4][:len(scores)]
                weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
                weight_sum = sum(weights[:len(scores)])
                result[domain] = weighted_sum / weight_sum
        
        return result
    
    def _normalize_domain_scores(self, domain_scores: Dict[str, float]) -> Dict[str, float]:
        """Normalize domain scores to 0-1 range."""
        if not domain_scores:
            return {}
        
        max_score = max(domain_scores.values())
        if max_score == 0:
            return {}
        
        return {domain: score / max_score for domain, score in domain_scores.items()}
    
    async def get_domain_specific_strategy(
        self, 
        user_id: str, 
        query: str,
        detected_domains: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Get domain-specific retrieval and response strategy.
        
        Args:
            user_id: User identifier
            query: Search query
            detected_domains: Pre-detected domains (optional)
            
        Returns:
            Domain-specific strategy configuration
        """
        try:
            if detected_domains is None:
                detected_domains = await self.detect_user_domains(user_id)
            
            # Detect query-specific domain signals
            query_domains = self._detect_query_domains(query)
            
            # Combine user domains with query domains
            combined_domains = self._combine_domain_signals(detected_domains, query_domains)
            
            if not combined_domains:
                return self._get_default_strategy()
            
            # Get primary domain
            primary_domain = max(combined_domains.items(), key=lambda x: x[1])[0]
            primary_confidence = combined_domains[primary_domain]
            
            # Get domain configuration
            domain_config = self.DOMAIN_CONFIGS.get(primary_domain, {})
            
            # Build strategy
            strategy = {
                "primary_domain": primary_domain,
                "domain_confidence": primary_confidence,
                "chunking_strategy": {
                    "chunk_size": domain_config.get("chunk_size", 600),
                    "overlap_ratio": domain_config.get("overlap_ratio", 0.15),
                    "preserve_context": primary_domain in ["law", "medicine", "science"]
                },
                "retrieval_strategy": {
                    "complexity_weight": domain_config.get("complexity_weight", 0.6),
                    "recency_weight": domain_config.get("recency_weight", 0.5),
                    "domain_boost": primary_confidence * 0.3,
                    "content_type_preference": domain_config.get("content_types", [])
                },
                "response_strategy": {
                    "citation_style": domain_config.get("citation_style", "standard"),
                    "reasoning_emphasis": domain_config.get("reasoning_emphasis", ["analytical"]),
                    "detail_level": "high" if domain_config.get("complexity_weight", 0.6) > 0.7 else "medium",
                    "uncertainty_handling": "conservative" if primary_domain in ["medicine", "law"] else "standard"
                },
                "all_domains": combined_domains
            }
            
            logger.debug(f"Generated domain strategy for user {user_id}: {strategy}")
            return strategy
            
        except Exception as e:
            logger.error(f"Error getting domain-specific strategy: {str(e)}")
            return self._get_default_strategy()
    
    def _detect_query_domains(self, query: str) -> Dict[str, float]:
        """Detect domain signals from a specific query."""
        query_lower = query.lower()
        domain_scores = {}
        
        for domain, config in self.DOMAIN_CONFIGS.items():
            keyword_matches = sum(1 for keyword in config["keywords"] if keyword in query_lower)
            if keyword_matches > 0:
                # Calculate keyword density
                density = keyword_matches / len(query.split())
                domain_scores[domain] = min(density * 5, 1.0)  # Scale and cap
        
        return domain_scores
    
    def _get_default_strategy(self) -> Dict[str, Any]:
        """Get default strategy when no domain is detected."""
        return {
            "primary_domain": "general",
            "domain_confidence": 0.0,
            "chunking_strategy": {
                "chunk_size": 600,
                "overlap_ratio": 0.15,
                "preserve_context": False
            },
            "retrieval_strategy": {
                "complexity_weight": 0.6,
                "recency_weight": 0.5,
                "domain_boost": 0.0,
                "content_type_preference": []
            },
            "response_strategy": {
                "citation_style": "standard",
                "reasoning_emphasis": ["analytical"],
                "detail_level": "medium",
                "uncertainty_handling": "standard"
            },
            "all_domains": {}
        }
    
    async def adapt_retrieval_results(
        self,
        results: List[Dict[str, Any]],
        strategy: Dict[str, Any],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Adapt retrieval results based on domain-specific strategy.
        
        Args:
            results: Original retrieval results
            strategy: Domain-specific strategy
            user_id: User identifier
            
        Returns:
            Adapted retrieval results
        """
        try:
            if not results or strategy["primary_domain"] == "general":
                return results
            
            adapted_results = []
            retrieval_strategy = strategy.get("retrieval_strategy", {})
            
            for result in results:
                adapted_result = result.copy()
                
                # Apply domain-specific scoring
                domain_score = await self._calculate_domain_relevance(
                    result, strategy["primary_domain"], strategy["all_domains"]
                )
                
                # Apply content type preference
                content_type_score = self._calculate_content_type_relevance(
                    result, retrieval_strategy.get("content_type_preference", [])
                )
                
                # Apply complexity weighting
                complexity_score = self._calculate_complexity_alignment(
                    result, retrieval_strategy.get("complexity_weight", 0.6)
                )
                
                # Apply recency weighting
                recency_score = self._calculate_recency_relevance(
                    result, retrieval_strategy.get("recency_weight", 0.5)
                )
                
                # Combine scores
                base_score = result.get("relevance", 0.0)
                domain_boost = retrieval_strategy.get("domain_boost", 0.0)
                
                adapted_score = (
                    base_score * 0.6 +
                    domain_score * domain_boost +
                    content_type_score * 0.15 +
                    complexity_score * 0.15 +
                    recency_score * 0.1
                )
                
                adapted_result["domain_adapted_score"] = min(1.0, adapted_score)
                adapted_result["domain_factors"] = {
                    "domain_score": domain_score,
                    "content_type_score": content_type_score,
                    "complexity_score": complexity_score,
                    "recency_score": recency_score,
                    "primary_domain": strategy["primary_domain"]
                }
                
                adapted_results.append(adapted_result)
            
            # Sort by adapted score
            adapted_results.sort(key=lambda x: x["domain_adapted_score"], reverse=True)
            
            logger.debug(f"Adapted {len(results)} results for domain {strategy['primary_domain']}")
            return adapted_results
            
        except Exception as e:
            logger.error(f"Error adapting retrieval results: {str(e)}")
            return results
    
    async def _calculate_domain_relevance(
        self,
        result: Dict[str, Any],
        primary_domain: str,
        all_domains: Dict[str, float]
    ) -> float:
        """Calculate domain relevance score for a result."""
        try:
            document_id = result.get("metadata", {}).get("document_id")
            if not document_id:
                return 0.0
            
            # Get document domain tags
            doc_tags = self.db.query(DocumentTag).filter(
                DocumentTag.document_id == document_id,
                DocumentTag.tag_type == "domain"
            ).all()
            
            if not doc_tags:
                return 0.0
            
            max_relevance = 0.0
            for tag in doc_tags:
                if tag.tag_name in all_domains:
                    relevance = all_domains[tag.tag_name] * tag.confidence_score
                    max_relevance = max(max_relevance, relevance)
            
            return max_relevance
            
        except Exception as e:
            logger.error(f"Error calculating domain relevance: {str(e)}")
            return 0.0
    
    def _calculate_content_type_relevance(
        self,
        result: Dict[str, Any],
        preferred_types: List[str]
    ) -> float:
        """Calculate content type relevance score."""
        if not preferred_types:
            return 0.5  # Neutral score
        
        content = result.get("content", "").lower()
        metadata = result.get("metadata", {})
        doc_name = metadata.get("document_name", "").lower()
        
        relevance_score = 0.0
        
        for content_type in preferred_types:
            type_indicators = {
                "documentation": ["doc", "guide", "manual", "reference"],
                "tutorial": ["tutorial", "how-to", "step", "example"],
                "specification": ["spec", "standard", "protocol", "requirement"],
                "code_example": ["code", "example", "sample", "demo"],
                "paper": ["paper", "journal", "article", "study"],
                "research": ["research", "analysis", "investigation"],
                "methodology": ["method", "approach", "procedure"],
                "report": ["report", "summary", "findings"],
                "case_study": ["case", "study", "example", "scenario"],
                "presentation": ["presentation", "slide", "overview"],
                "clinical_guide": ["clinical", "guideline", "protocol"],
                "protocol": ["protocol", "procedure", "standard"],
                "textbook": ["textbook", "book", "chapter"],
                "lesson": ["lesson", "lecture", "class"],
                "statute": ["statute", "law", "code", "regulation"],
                "case_law": ["case", "court", "decision", "ruling"],
                "contract": ["contract", "agreement", "terms"]
            }
            
            indicators = type_indicators.get(content_type, [content_type])
            matches = sum(1 for indicator in indicators if indicator in content or indicator in doc_name)
            
            if matches > 0:
                relevance_score = max(relevance_score, min(matches / len(indicators), 1.0))
        
        return relevance_score
    
    def _calculate_complexity_alignment(
        self,
        result: Dict[str, Any],
        preferred_complexity: float
    ) -> float:
        """Calculate how well content complexity aligns with domain preference."""
        content = result.get("content", "")
        
        # Estimate content complexity
        complexity_indicators = {
            "high": ["advanced", "complex", "sophisticated", "comprehensive", "detailed"],
            "medium": ["moderate", "standard", "typical", "general"],
            "low": ["basic", "simple", "introduction", "overview", "elementary"]
        }
        
        complexity_score = 0.5  # Default medium complexity
        
        # Check for complexity indicators
        content_lower = content.lower()
        high_count = sum(1 for word in complexity_indicators["high"] if word in content_lower)
        low_count = sum(1 for word in complexity_indicators["low"] if word in content_lower)
        
        if high_count > low_count:
            complexity_score = 0.8
        elif low_count > high_count:
            complexity_score = 0.2
        
        # Also consider content length as complexity indicator
        content_length = len(content)
        if content_length > 1000:
            complexity_score += 0.1
        elif content_length < 300:
            complexity_score -= 0.1
        
        complexity_score = max(0.1, min(0.9, complexity_score))
        
        # Calculate alignment with user preference
        alignment = 1.0 - abs(complexity_score - preferred_complexity)
        return alignment
    
    def _calculate_recency_relevance(
        self,
        result: Dict[str, Any],
        recency_weight: float
    ) -> float:
        """Calculate recency relevance score."""
        # This would require document timestamps
        # For now, return a score based on recency preference
        return recency_weight * 0.5  # Placeholder implementation
    
    async def update_domain_adaptation(
        self,
        user_id: str,
        query: str,
        results: List[Dict[str, Any]],
        user_feedback: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update domain adaptation based on user interaction and feedback.
        
        Args:
            user_id: User identifier
            query: Original query
            results: Retrieved results
            user_feedback: Optional user feedback
        """
        try:
            # Detect domains from this interaction
            query_domains = self._detect_query_domains(query)
            
            # Analyze result domains
            result_domains = await self._analyze_result_domains(results)
            
            # Create learning event
            learning_event = {
                "query": query,
                "query_domains": query_domains,
                "result_domains": result_domains,
                "user_feedback": user_feedback,
                "timestamp": datetime.utcnow().isoformat(),
                "adaptation_type": "domain_learning"
            }
            
            # Store analytics event for learning
            analytics_event = AnalyticsEvent(
                user_id=user_id,
                event_type="domain_adaptation_learning",
                event_data=learning_event
            )
            
            self.db.add(analytics_event)
            self.db.commit()
            
            # Update user domain expertise if feedback is positive
            if user_feedback and user_feedback.get("rating", 0) >= 4:
                await self._reinforce_domain_learning(user_id, query_domains, result_domains)
            
            logger.debug(f"Updated domain adaptation for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating domain adaptation: {str(e)}")
            self.db.rollback()
    
    async def _analyze_result_domains(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze domains present in search results."""
        domain_counts = defaultdict(int)
        total_results = len(results)
        
        if total_results == 0:
            return {}
        
        for result in results:
            document_id = result.get("metadata", {}).get("document_id")
            if document_id:
                doc_tags = self.db.query(DocumentTag).filter(
                    DocumentTag.document_id == document_id,
                    DocumentTag.tag_type == "domain"
                ).all()
                
                for tag in doc_tags:
                    domain_counts[tag.tag_name] += tag.confidence_score
        
        # Normalize by total results
        return {domain: count / total_results for domain, count in domain_counts.items()}
    
    async def _reinforce_domain_learning(
        self,
        user_id: str,
        query_domains: Dict[str, float],
        result_domains: Dict[str, float]
    ) -> None:
        """Reinforce domain learning based on positive feedback."""
        try:
            # Get current user profile
            user_profile = await self.profile_manager.get_user_profile(user_id)
            if not user_profile:
                return
            
            # Update domain expertise with small increments
            current_expertise = user_profile.domain_expertise or {}
            
            # Reinforce query domains
            for domain, score in query_domains.items():
                current_score = current_expertise.get(domain, 0.0)
                # Small learning rate to prevent overfitting
                new_score = current_score + (score * 0.1)
                current_expertise[domain] = min(1.0, new_score)
            
            # Reinforce result domains (smaller weight)
            for domain, score in result_domains.items():
                current_score = current_expertise.get(domain, 0.0)
                new_score = current_score + (score * 0.05)
                current_expertise[domain] = min(1.0, new_score)
            
            # Update profile
            profile_record = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if profile_record:
                profile_record.domain_expertise = current_expertise
                profile_record.updated_at = datetime.utcnow()
                self.db.commit()
            
            logger.debug(f"Reinforced domain learning for user {user_id}: {current_expertise}")
            
        except Exception as e:
            logger.error(f"Error reinforcing domain learning: {str(e)}")
            self.db.rollback()
    
    async def get_domain_adaptation_stats(self, user_id: str) -> Dict[str, Any]:
        """Get domain adaptation statistics for a user."""
        try:
            # Get user domains
            user_domains = await self.detect_user_domains(user_id)
            
            # Get recent domain adaptation events
            recent_events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.event_type == "domain_adaptation_learning",
                AnalyticsEvent.timestamp >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            # Analyze adaptation effectiveness
            adaptation_stats = {
                "detected_domains": user_domains,
                "primary_domain": max(user_domains.items(), key=lambda x: x[1])[0] if user_domains else None,
                "domain_confidence": max(user_domains.values()) if user_domains else 0.0,
                "adaptation_events": len(recent_events),
                "learning_trend": self._calculate_learning_trend(recent_events),
                "domain_distribution": self._calculate_domain_distribution(recent_events)
            }
            
            return adaptation_stats
            
        except Exception as e:
            logger.error(f"Error getting domain adaptation stats: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_learning_trend(self, events: List[AnalyticsEvent]) -> str:
        """Calculate learning trend from adaptation events."""
        if len(events) < 5:
            return "insufficient_data"
        
        # Sort by timestamp
        events.sort(key=lambda x: x.timestamp)
        
        # Compare first half with second half
        mid_point = len(events) // 2
        first_half = events[:mid_point]
        second_half = events[mid_point:]
        
        # Count positive feedback in each half
        first_positive = sum(
            1 for event in first_half 
            if event.event_data.get("user_feedback", {}).get("rating", 0) >= 4
        )
        second_positive = sum(
            1 for event in second_half 
            if event.event_data.get("user_feedback", {}).get("rating", 0) >= 4
        )
        
        first_rate = first_positive / len(first_half) if first_half else 0
        second_rate = second_positive / len(second_half) if second_half else 0
        
        if second_rate > first_rate + 0.1:
            return "improving"
        elif first_rate > second_rate + 0.1:
            return "declining"
        else:
            return "stable"
    
    def _calculate_domain_distribution(self, events: List[AnalyticsEvent]) -> Dict[str, int]:
        """Calculate domain distribution from adaptation events."""
        domain_counts = Counter()
        
        for event in events:
            query_domains = event.event_data.get("query_domains", {})
            for domain in query_domains.keys():
                domain_counts[domain] += 1
        
        return dict(domain_counts.most_common(5))

class DomainDetector:
    """
    Helper class for detecting document and query domains.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.domain_adapter = DomainAdapter(db)
    
    async def detect_document_domain(
        self,
        document_id: str,
        content: str
    ) -> List[Tuple[str, float]]:
        """
        Detect domains for a document based on its content.
        
        Args:
            document_id: Document identifier
            content: Document content
            
        Returns:
            List of (domain, confidence) tuples
        """
        try:
            content_lower = content.lower()
            domain_scores = {}
            
            # Check against domain configurations
            for domain, config in DomainAdapter.DOMAIN_CONFIGS.items():
                keyword_matches = sum(1 for keyword in config["keywords"] if keyword in content_lower)
                if keyword_matches > 0:
                    # Calculate keyword density
                    density = keyword_matches / len(content.split())
                    # Normalize by number of keywords in domain
                    normalized_score = min(density * len(config["keywords"]), 1.0)
                    domain_scores[domain] = normalized_score
            
            # Sort by confidence
            sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Return top domains with confidence > 0.1
            return [(domain, score) for domain, score in sorted_domains if score > 0.1]
            
        except Exception as e:
            logger.error(f"Error detecting document domain: {str(e)}")
            return []
    
    async def auto_tag_document_domains(
        self,
        document_id: str,
        content: str
    ) -> None:
        """
        Automatically tag a document with detected domains.
        
        Args:
            document_id: Document identifier
            content: Document content
        """
        try:
            detected_domains = await self.detect_document_domain(document_id, content)
            
            for domain, confidence in detected_domains:
                # Create domain tag
                domain_tag = DocumentTag(
                    document_id=document_id,
                    tag_name=domain,
                    tag_type="domain",
                    confidence_score=confidence,
                    generated_by="domain_detector"
                )
                
                self.db.add(domain_tag)
            
            self.db.commit()
            logger.info(f"Auto-tagged document {document_id} with domains: {detected_domains}")
            
        except Exception as e:
            logger.error(f"Error auto-tagging document domains: {str(e)}")
            self.db.rollback()