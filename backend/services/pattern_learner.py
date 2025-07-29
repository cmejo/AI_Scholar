"""
Pattern Learning Service for analyzing user interaction patterns and optimizing system behavior.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from core.database import get_db
from core.redis_client import get_redis_client

logger = logging.getLogger(__name__)

@dataclass
class QueryPattern:
    """Represents a discovered query pattern."""
    pattern_id: str
    pattern_type: str  # 'frequent_terms', 'temporal', 'semantic', 'behavioral'
    description: str
    frequency: int
    confidence: float
    examples: List[str]
    metadata: Dict[str, Any]

@dataclass
class DocumentUsagePattern:
    """Represents document usage patterns."""
    document_id: str
    access_frequency: int
    peak_usage_times: List[str]
    common_query_contexts: List[str]
    user_segments: List[str]
    effectiveness_score: float

@dataclass
class UserBehaviorPattern:
    """Represents user behavior patterns."""
    user_id: str
    session_duration_avg: float
    query_complexity_preference: str  # 'simple', 'moderate', 'complex'
    preferred_response_length: str  # 'brief', 'detailed', 'comprehensive'
    domain_preferences: List[str]
    interaction_style: str  # 'exploratory', 'targeted', 'research'
    feedback_tendency: str  # 'positive', 'critical', 'neutral'

@dataclass
class SystemOptimization:
    """Represents system optimization recommendations."""
    optimization_type: str
    target_component: str
    recommendation: str
    expected_improvement: float
    confidence: float
    implementation_priority: str  # 'high', 'medium', 'low'

class PatternLearner:
    """Service for learning from user interaction patterns and optimizing system behavior."""
    
    def __init__(self):
        self.redis_client = None
        self.db_session = None
        self.pattern_cache_ttl = 3600  # 1 hour
        self.min_pattern_frequency = 5
        self.confidence_threshold = 0.7
        
    async def initialize(self):
        """Initialize the pattern learner service."""
        try:
            self.redis_client = await get_redis_client()
            # For now, we'll handle db_session in each method to avoid session management issues
            logger.info("PatternLearner initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PatternLearner: {e}")
            raise
    
    async def analyze_query_patterns(self, user_id: Optional[str] = None, 
                                   time_window_days: int = 30) -> List[QueryPattern]:
        """Analyze query patterns from user interactions."""
        try:
            # Get query data from analytics events
            query_data = await self._get_query_data(user_id, time_window_days)
            
            patterns = []
            
            # Analyze frequent terms
            frequent_term_patterns = await self._analyze_frequent_terms(query_data)
            patterns.extend(frequent_term_patterns)
            
            # Analyze temporal patterns
            temporal_patterns = await self._analyze_temporal_patterns(query_data)
            patterns.extend(temporal_patterns)
            
            # Analyze semantic patterns
            semantic_patterns = await self._analyze_semantic_patterns(query_data)
            patterns.extend(semantic_patterns)
            
            # Cache results
            cache_key = f"query_patterns:{user_id or 'global'}:{time_window_days}"
            await self.redis_client.setex(
                cache_key, 
                self.pattern_cache_ttl,
                json.dumps([asdict(p) for p in patterns])
            )
            
            logger.info(f"Analyzed {len(patterns)} query patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing query patterns: {e}")
            return []
    
    async def analyze_document_usage_patterns(self, time_window_days: int = 30) -> List[DocumentUsagePattern]:
        """Analyze document usage patterns."""
        try:
            # Get document access data
            usage_data = await self._get_document_usage_data(time_window_days)
            
            patterns = []
            for doc_id, data in usage_data.items():
                pattern = DocumentUsagePattern(
                    document_id=doc_id,
                    access_frequency=data['access_count'],
                    peak_usage_times=await self._identify_peak_times(data['access_times']),
                    common_query_contexts=await self._extract_query_contexts(data['queries']),
                    user_segments=await self._identify_user_segments(data['users']),
                    effectiveness_score=await self._calculate_effectiveness_score(doc_id, data)
                )
                patterns.append(pattern)
            
            # Cache results
            cache_key = f"document_patterns:{time_window_days}"
            await self.redis_client.setex(
                cache_key,
                self.pattern_cache_ttl,
                json.dumps([asdict(p) for p in patterns])
            )
            
            logger.info(f"Analyzed {len(patterns)} document usage patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing document usage patterns: {e}")
            return []
    
    async def analyze_user_behavior_patterns(self, user_id: str, 
                                           time_window_days: int = 90) -> UserBehaviorPattern:
        """Analyze individual user behavior patterns."""
        try:
            # Get user interaction data
            user_data = await self._get_user_interaction_data(user_id, time_window_days)
            
            pattern = UserBehaviorPattern(
                user_id=user_id,
                session_duration_avg=await self._calculate_avg_session_duration(user_data),
                query_complexity_preference=await self._analyze_query_complexity(user_data),
                preferred_response_length=await self._analyze_response_preferences(user_data),
                domain_preferences=await self._identify_domain_preferences(user_data),
                interaction_style=await self._classify_interaction_style(user_data),
                feedback_tendency=await self._analyze_feedback_tendency(user_data)
            )
            
            # Cache results
            cache_key = f"user_behavior:{user_id}:{time_window_days}"
            await self.redis_client.setex(
                cache_key,
                self.pattern_cache_ttl,
                json.dumps(asdict(pattern))
            )
            
            logger.info(f"Analyzed behavior pattern for user {user_id}")
            return pattern
            
        except Exception as e:
            logger.error(f"Error analyzing user behavior patterns: {e}")
            return UserBehaviorPattern(
                user_id=user_id,
                session_duration_avg=0.0,
                query_complexity_preference="moderate",
                preferred_response_length="detailed",
                domain_preferences=[],
                interaction_style="targeted",
                feedback_tendency="neutral"
            )
    
    async def generate_system_optimizations(self, patterns: Dict[str, Any]) -> List[SystemOptimization]:
        """Generate system optimization recommendations based on learned patterns."""
        try:
            optimizations = []
            
            # Analyze query patterns for retrieval optimization
            if 'query_patterns' in patterns:
                retrieval_opts = await self._generate_retrieval_optimizations(patterns['query_patterns'])
                optimizations.extend(retrieval_opts)
            
            # Analyze document patterns for caching optimization
            if 'document_patterns' in patterns:
                caching_opts = await self._generate_caching_optimizations(patterns['document_patterns'])
                optimizations.extend(caching_opts)
            
            # Analyze user patterns for personalization optimization
            if 'user_patterns' in patterns:
                personalization_opts = await self._generate_personalization_optimizations(patterns['user_patterns'])
                optimizations.extend(personalization_opts)
            
            # Sort by expected improvement and confidence
            optimizations.sort(key=lambda x: x.expected_improvement * x.confidence, reverse=True)
            
            logger.info(f"Generated {len(optimizations)} system optimizations")
            return optimizations
            
        except Exception as e:
            logger.error(f"Error generating system optimizations: {e}")
            return []
    
    async def apply_pattern_based_optimization(self, optimization: SystemOptimization) -> bool:
        """Apply a pattern-based optimization to the system."""
        try:
            success = False
            
            if optimization.target_component == "retrieval":
                success = await self._apply_retrieval_optimization(optimization)
            elif optimization.target_component == "caching":
                success = await self._apply_caching_optimization(optimization)
            elif optimization.target_component == "personalization":
                success = await self._apply_personalization_optimization(optimization)
            
            if success:
                # Log the optimization application
                await self._log_optimization_application(optimization)
                logger.info(f"Applied optimization: {optimization.recommendation}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error applying optimization: {e}")
            return False
    
    async def _get_query_data(self, user_id: Optional[str], time_window_days: int) -> List[Dict]:
        """Get query data from analytics events."""
        try:
            from core.database import AnalyticsEvent
            
            # Get a fresh database session
            db_session = next(get_db())
            
            try:
                # Build query
                query = db_session.query(AnalyticsEvent).filter(
                    AnalyticsEvent.event_type == 'query_submitted',
                    AnalyticsEvent.timestamp >= datetime.now() - timedelta(days=time_window_days)
                )
                
                if user_id:
                    query = query.filter(AnalyticsEvent.user_id == user_id)
                
                results = query.order_by(AnalyticsEvent.timestamp.desc()).all()
                
                return [
                    {
                        'query': result.event_data.get('query', '') if result.event_data else '',
                        'timestamp': result.timestamp,
                        'user_id': result.user_id,
                        'metadata': result.event_data or {}
                    }
                    for result in results
                ]
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error getting query data: {e}")
            return []
    
    async def _analyze_frequent_terms(self, query_data: List[Dict]) -> List[QueryPattern]:
        """Analyze frequent terms in queries."""
        try:
            # Extract and count terms
            term_counts = Counter()
            query_examples = defaultdict(list)
            
            for item in query_data:
                query = item['query'].lower()
                terms = query.split()
                for term in terms:
                    if len(term) > 2:  # Filter short terms
                        term_counts[term] += 1
                        if len(query_examples[term]) < 3:
                            query_examples[term].append(query)
            
            patterns = []
            for term, count in term_counts.most_common(20):
                if count >= self.min_pattern_frequency:
                    pattern = QueryPattern(
                        pattern_id=f"frequent_term_{term}",
                        pattern_type="frequent_terms",
                        description=f"Frequent term: '{term}' appears in {count} queries",
                        frequency=count,
                        confidence=min(count / len(query_data), 1.0),
                        examples=query_examples[term],
                        metadata={"term": term, "total_queries": len(query_data)}
                    )
                    patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing frequent terms: {e}")
            return []
    
    async def _analyze_temporal_patterns(self, query_data: List[Dict]) -> List[QueryPattern]:
        """Analyze temporal patterns in queries."""
        try:
            # Group queries by hour of day
            hourly_counts = defaultdict(int)
            for item in query_data:
                hour = item['timestamp'].hour
                hourly_counts[hour] += 1
            
            patterns = []
            
            # Find peak hours
            if hourly_counts:
                max_count = max(hourly_counts.values())
                avg_count = sum(hourly_counts.values()) / len(hourly_counts)
                
                for hour, count in hourly_counts.items():
                    if count > avg_count * 1.5:  # 50% above average
                        pattern = QueryPattern(
                            pattern_id=f"peak_hour_{hour}",
                            pattern_type="temporal",
                            description=f"Peak query activity at hour {hour} with {count} queries",
                            frequency=count,
                            confidence=count / max_count,
                            examples=[],
                            metadata={"hour": hour, "avg_count": avg_count}
                        )
                        patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing temporal patterns: {e}")
            return []
    
    async def _analyze_semantic_patterns(self, query_data: List[Dict]) -> List[QueryPattern]:
        """Analyze semantic patterns in queries using clustering."""
        try:
            if len(query_data) < 10:  # Need minimum data for clustering
                return []
            
            # Simple semantic clustering based on query length and word overlap
            features = []
            queries = []
            
            for item in query_data:
                query = item['query']
                queries.append(query)
                
                # Simple features: length, word count, question indicators
                features.append([
                    len(query),
                    len(query.split()),
                    1 if any(q in query.lower() for q in ['what', 'how', 'why', 'when', 'where']) else 0,
                    1 if '?' in query else 0
                ])
            
            # Perform clustering
            if len(features) >= 3:
                scaler = StandardScaler()
                features_scaled = scaler.fit_transform(features)
                
                n_clusters = min(5, len(features) // 3)  # Reasonable number of clusters
                kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                clusters = kmeans.fit_predict(features_scaled)
                
                # Create patterns for each cluster
                patterns = []
                for cluster_id in range(n_clusters):
                    cluster_queries = [queries[i] for i, c in enumerate(clusters) if c == cluster_id]
                    if len(cluster_queries) >= self.min_pattern_frequency:
                        pattern = QueryPattern(
                            pattern_id=f"semantic_cluster_{cluster_id}",
                            pattern_type="semantic",
                            description=f"Semantic cluster {cluster_id} with {len(cluster_queries)} similar queries",
                            frequency=len(cluster_queries),
                            confidence=len(cluster_queries) / len(queries),
                            examples=cluster_queries[:3],
                            metadata={"cluster_id": cluster_id, "cluster_size": len(cluster_queries)}
                        )
                        patterns.append(pattern)
                
                return patterns
            
            return []
            
        except Exception as e:
            logger.error(f"Error analyzing semantic patterns: {e}")
            return []
    
    async def _get_document_usage_data(self, time_window_days: int) -> Dict[str, Dict]:
        """Get document usage data."""
        try:
            from core.database import AnalyticsEvent
            
            # Get a fresh database session
            db_session = next(get_db())
            
            try:
                results = db_session.query(AnalyticsEvent).filter(
                    AnalyticsEvent.event_type.in_(['document_accessed', 'search_performed']),
                    AnalyticsEvent.timestamp >= datetime.now() - timedelta(days=time_window_days)
                ).order_by(AnalyticsEvent.timestamp.desc()).all()
                
                usage_data = defaultdict(lambda: {
                    'access_count': 0,
                    'access_times': [],
                    'queries': [],
                    'users': set()
                })
                
                for result in results:
                    event_data = result.event_data or {}
                    timestamp = result.timestamp
                    user_id = result.user_id
                    
                    if 'document_id' in event_data:
                        doc_id = event_data['document_id']
                        usage_data[doc_id]['access_count'] += 1
                        usage_data[doc_id]['access_times'].append(timestamp)
                        usage_data[doc_id]['users'].add(user_id)
                        
                        if 'query' in event_data:
                            usage_data[doc_id]['queries'].append(event_data['query'])
                
                # Convert sets to lists for JSON serialization
                for doc_id in usage_data:
                    usage_data[doc_id]['users'] = list(usage_data[doc_id]['users'])
                
                return dict(usage_data)
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error getting document usage data: {e}")
            return {}
    
    async def _identify_peak_times(self, access_times: List[datetime]) -> List[str]:
        """Identify peak usage times."""
        try:
            if not access_times:
                return []
            
            # Group by hour
            hourly_counts = defaultdict(int)
            for timestamp in access_times:
                hour = timestamp.hour
                hourly_counts[hour] += 1
            
            # Find hours with above-average activity
            if hourly_counts:
                avg_count = sum(hourly_counts.values()) / len(hourly_counts)
                peak_hours = [
                    f"{hour:02d}:00" 
                    for hour, count in hourly_counts.items() 
                    if count > avg_count * 1.2
                ]
                return sorted(peak_hours)
            
            return []
            
        except Exception as e:
            logger.error(f"Error identifying peak times: {e}")
            return []
    
    async def _extract_query_contexts(self, queries: List[str]) -> List[str]:
        """Extract common query contexts."""
        try:
            if not queries:
                return []
            
            # Simple context extraction based on common terms
            contexts = []
            term_counts = Counter()
            
            for query in queries:
                terms = query.lower().split()
                for term in terms:
                    if len(term) > 3:
                        term_counts[term] += 1
            
            # Get most common terms as contexts
            for term, count in term_counts.most_common(5):
                if count > 1:
                    contexts.append(term)
            
            return contexts
            
        except Exception as e:
            logger.error(f"Error extracting query contexts: {e}")
            return []
    
    async def _identify_user_segments(self, users: List[str]) -> List[str]:
        """Identify user segments accessing the document."""
        try:
            # Simple segmentation based on user count
            segments = []
            user_count = len(users)
            
            if user_count == 1:
                segments.append("single_user")
            elif user_count <= 5:
                segments.append("small_group")
            elif user_count <= 20:
                segments.append("medium_group")
            else:
                segments.append("large_group")
            
            return segments
            
        except Exception as e:
            logger.error(f"Error identifying user segments: {e}")
            return []
    
    async def _calculate_effectiveness_score(self, doc_id: str, data: Dict) -> float:
        """Calculate document effectiveness score."""
        try:
            # Simple effectiveness based on access frequency and user diversity
            access_count = data['access_count']
            user_count = len(data['users'])
            
            # Normalize scores
            access_score = min(access_count / 100, 1.0)  # Cap at 100 accesses
            diversity_score = min(user_count / 20, 1.0)  # Cap at 20 users
            
            # Weighted combination
            effectiveness = (access_score * 0.6) + (diversity_score * 0.4)
            
            return round(effectiveness, 3)
            
        except Exception as e:
            logger.error(f"Error calculating effectiveness score: {e}")
            return 0.0
    
    async def _get_user_interaction_data(self, user_id: str, time_window_days: int) -> Dict:
        """Get user interaction data."""
        try:
            from core.database import AnalyticsEvent
            
            # Get a fresh database session
            db_session = next(get_db())
            
            try:
                results = db_session.query(AnalyticsEvent).filter(
                    AnalyticsEvent.user_id == user_id,
                    AnalyticsEvent.timestamp >= datetime.now() - timedelta(days=time_window_days)
                ).order_by(AnalyticsEvent.timestamp.desc()).all()
                
                return {
                    'events': [
                        {
                            'type': result.event_type,
                            'data': result.event_data or {},
                            'timestamp': result.timestamp
                        }
                        for result in results
                    ]
                }
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error getting user interaction data: {e}")
            return {'events': []}
    
    async def _calculate_avg_session_duration(self, user_data: Dict) -> float:
        """Calculate average session duration."""
        try:
            events = user_data.get('events', [])
            if not events:
                return 0.0
            
            # Group events by session (simple time-based grouping)
            sessions = []
            current_session = []
            session_gap_minutes = 30
            
            for event in sorted(events, key=lambda x: x['timestamp']):
                if (current_session and 
                    (event['timestamp'] - current_session[-1]['timestamp']).total_seconds() > session_gap_minutes * 60):
                    # New session
                    if current_session:
                        sessions.append(current_session)
                    current_session = [event]
                else:
                    current_session.append(event)
            
            if current_session:
                sessions.append(current_session)
            
            # Calculate session durations
            durations = []
            for session in sessions:
                if len(session) > 1:
                    duration = (session[-1]['timestamp'] - session[0]['timestamp']).total_seconds() / 60
                    durations.append(duration)
            
            return sum(durations) / len(durations) if durations else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating session duration: {e}")
            return 0.0
    
    async def _analyze_query_complexity(self, user_data: Dict) -> str:
        """Analyze user's query complexity preference."""
        try:
            events = user_data.get('events', [])
            query_events = [e for e in events if e['type'] == 'query_submitted']
            
            if not query_events:
                return "moderate"
            
            complexities = []
            for event in query_events:
                query = event['data'].get('query', '')
                # Simple complexity scoring
                word_count = len(query.split())
                has_operators = any(op in query.lower() for op in ['and', 'or', 'not', '"'])
                has_questions = '?' in query
                
                if word_count > 10 or has_operators:
                    complexities.append("complex")
                elif word_count < 3 and not has_questions:
                    complexities.append("simple")
                else:
                    complexities.append("moderate")
            
            # Return most common complexity
            complexity_counts = Counter(complexities)
            return complexity_counts.most_common(1)[0][0]
            
        except Exception as e:
            logger.error(f"Error analyzing query complexity: {e}")
            return "moderate"
    
    async def _analyze_response_preferences(self, user_data: Dict) -> str:
        """Analyze user's response length preference."""
        try:
            # This would typically analyze user feedback on response lengths
            # For now, return a default based on query patterns
            events = user_data.get('events', [])
            feedback_events = [e for e in events if e['type'] == 'feedback_provided']
            
            if feedback_events:
                # Analyze feedback for length preferences
                length_feedback = []
                for event in feedback_events:
                    feedback_data = event['data']
                    if 'response_length_rating' in feedback_data:
                        length_feedback.append(feedback_data['response_length_rating'])
                
                if length_feedback:
                    avg_rating = sum(length_feedback) / len(length_feedback)
                    if avg_rating > 4:
                        return "detailed"
                    elif avg_rating < 3:
                        return "brief"
            
            return "detailed"  # Default
            
        except Exception as e:
            logger.error(f"Error analyzing response preferences: {e}")
            return "detailed"
    
    async def _identify_domain_preferences(self, user_data: Dict) -> List[str]:
        """Identify user's domain preferences."""
        try:
            events = user_data.get('events', [])
            document_events = [e for e in events if e['type'] == 'document_accessed']
            
            # Extract domains from document metadata
            domains = []
            for event in document_events:
                doc_data = event['data']
                if 'document_domain' in doc_data:
                    domains.append(doc_data['document_domain'])
                elif 'document_tags' in doc_data:
                    # Extract domain-like tags
                    tags = doc_data['document_tags']
                    domain_tags = [tag for tag in tags if tag in ['technology', 'science', 'business', 'health', 'education']]
                    domains.extend(domain_tags)
            
            # Return most common domains
            if domains:
                domain_counts = Counter(domains)
                return [domain for domain, count in domain_counts.most_common(3)]
            
            return []
            
        except Exception as e:
            logger.error(f"Error identifying domain preferences: {e}")
            return []
    
    async def _classify_interaction_style(self, user_data: Dict) -> str:
        """Classify user's interaction style."""
        try:
            events = user_data.get('events', [])
            
            # Analyze interaction patterns
            query_count = len([e for e in events if e['type'] == 'query_submitted'])
            document_count = len([e for e in events if e['type'] == 'document_accessed'])
            session_count = max(1, len(events) // 10)  # Rough session estimate
            
            queries_per_session = query_count / session_count
            docs_per_query = document_count / max(1, query_count)
            
            if queries_per_session > 5 and docs_per_query > 2:
                return "exploratory"
            elif queries_per_session < 2 and docs_per_query < 1.5:
                return "targeted"
            else:
                return "research"
                
        except Exception as e:
            logger.error(f"Error classifying interaction style: {e}")
            return "targeted"
    
    async def _analyze_feedback_tendency(self, user_data: Dict) -> str:
        """Analyze user's feedback tendency."""
        try:
            events = user_data.get('events', [])
            feedback_events = [e for e in events if e['type'] == 'feedback_provided']
            
            if not feedback_events:
                return "neutral"
            
            ratings = []
            for event in feedback_events:
                feedback_data = event['data']
                if 'rating' in feedback_data:
                    ratings.append(feedback_data['rating'])
            
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                if avg_rating >= 4:
                    return "positive"
                elif avg_rating <= 2:
                    return "critical"
            
            return "neutral"
            
        except Exception as e:
            logger.error(f"Error analyzing feedback tendency: {e}")
            return "neutral"
    
    async def _generate_retrieval_optimizations(self, query_patterns: List[QueryPattern]) -> List[SystemOptimization]:
        """Generate retrieval optimization recommendations."""
        optimizations = []
        
        try:
            for pattern in query_patterns:
                if pattern.pattern_type == "frequent_terms" and pattern.confidence > self.confidence_threshold:
                    opt = SystemOptimization(
                        optimization_type="term_boosting",
                        target_component="retrieval",
                        recommendation=f"Boost relevance for term '{pattern.metadata['term']}' in search results",
                        expected_improvement=0.15 * pattern.confidence,
                        confidence=pattern.confidence,
                        implementation_priority="medium"
                    )
                    optimizations.append(opt)
                
                elif pattern.pattern_type == "semantic" and pattern.frequency > 10:
                    opt = SystemOptimization(
                        optimization_type="semantic_clustering",
                        target_component="retrieval",
                        recommendation=f"Create semantic cluster for query type: {pattern.description}",
                        expected_improvement=0.20 * pattern.confidence,
                        confidence=pattern.confidence,
                        implementation_priority="high"
                    )
                    optimizations.append(opt)
            
            return optimizations
            
        except Exception as e:
            logger.error(f"Error generating retrieval optimizations: {e}")
            return []
    
    async def _generate_caching_optimizations(self, document_patterns: List[DocumentUsagePattern]) -> List[SystemOptimization]:
        """Generate caching optimization recommendations."""
        optimizations = []
        
        try:
            # Sort by access frequency
            high_usage_docs = sorted(document_patterns, key=lambda x: x.access_frequency, reverse=True)[:10]
            
            for pattern in high_usage_docs:
                if pattern.access_frequency > 50:  # High usage threshold
                    opt = SystemOptimization(
                        optimization_type="document_caching",
                        target_component="caching",
                        recommendation=f"Cache document {pattern.document_id} with high access frequency ({pattern.access_frequency})",
                        expected_improvement=0.25,
                        confidence=0.8,
                        implementation_priority="high"
                    )
                    optimizations.append(opt)
                
                # Peak time caching
                if pattern.peak_usage_times:
                    opt = SystemOptimization(
                        optimization_type="temporal_caching",
                        target_component="caching",
                        recommendation=f"Pre-cache document {pattern.document_id} during peak times: {', '.join(pattern.peak_usage_times)}",
                        expected_improvement=0.20,
                        confidence=0.7,
                        implementation_priority="medium"
                    )
                    optimizations.append(opt)
            
            return optimizations
            
        except Exception as e:
            logger.error(f"Error generating caching optimizations: {e}")
            return []
    
    async def _generate_personalization_optimizations(self, user_patterns: List[UserBehaviorPattern]) -> List[SystemOptimization]:
        """Generate personalization optimization recommendations."""
        optimizations = []
        
        try:
            # Analyze common patterns across users
            complexity_preferences = Counter([p.query_complexity_preference for p in user_patterns])
            response_preferences = Counter([p.preferred_response_length for p in user_patterns])
            
            # Generate optimizations based on common preferences
            most_common_complexity = complexity_preferences.most_common(1)[0][0]
            most_common_response = response_preferences.most_common(1)[0][0]
            
            opt1 = SystemOptimization(
                optimization_type="default_complexity",
                target_component="personalization",
                recommendation=f"Set default query complexity handling to '{most_common_complexity}'",
                expected_improvement=0.15,
                confidence=0.7,
                implementation_priority="medium"
            )
            optimizations.append(opt1)
            
            opt2 = SystemOptimization(
                optimization_type="default_response_length",
                target_component="personalization",
                recommendation=f"Set default response length to '{most_common_response}'",
                expected_improvement=0.12,
                confidence=0.6,
                implementation_priority="low"
            )
            optimizations.append(opt2)
            
            return optimizations
            
        except Exception as e:
            logger.error(f"Error generating personalization optimizations: {e}")
            return []
    
    async def _apply_retrieval_optimization(self, optimization: SystemOptimization) -> bool:
        """Apply retrieval optimization."""
        try:
            # Store optimization in Redis for retrieval service to pick up
            opt_key = f"retrieval_optimization:{optimization.optimization_type}"
            opt_data = {
                "type": optimization.optimization_type,
                "recommendation": optimization.recommendation,
                "applied_at": datetime.now().isoformat(),
                "metadata": optimization.__dict__
            }
            
            await self.redis_client.setex(opt_key, 86400, json.dumps(opt_data))  # 24 hours
            return True
            
        except Exception as e:
            logger.error(f"Error applying retrieval optimization: {e}")
            return False
    
    async def _apply_caching_optimization(self, optimization: SystemOptimization) -> bool:
        """Apply caching optimization."""
        try:
            # Store optimization in Redis for caching service
            opt_key = f"caching_optimization:{optimization.optimization_type}"
            opt_data = {
                "type": optimization.optimization_type,
                "recommendation": optimization.recommendation,
                "applied_at": datetime.now().isoformat(),
                "metadata": optimization.__dict__
            }
            
            await self.redis_client.setex(opt_key, 86400, json.dumps(opt_data))
            return True
            
        except Exception as e:
            logger.error(f"Error applying caching optimization: {e}")
            return False
    
    async def _apply_personalization_optimization(self, optimization: SystemOptimization) -> bool:
        """Apply personalization optimization."""
        try:
            # Store optimization in Redis for personalization service
            opt_key = f"personalization_optimization:{optimization.optimization_type}"
            opt_data = {
                "type": optimization.optimization_type,
                "recommendation": optimization.recommendation,
                "applied_at": datetime.now().isoformat(),
                "metadata": optimization.__dict__
            }
            
            await self.redis_client.setex(opt_key, 86400, json.dumps(opt_data))
            return True
            
        except Exception as e:
            logger.error(f"Error applying personalization optimization: {e}")
            return False
    
    async def _log_optimization_application(self, optimization: SystemOptimization):
        """Log optimization application for tracking."""
        try:
            from core.database import AnalyticsEvent
            
            # Get a fresh database session
            db_session = next(get_db())
            
            try:
                event_data = {
                    "optimization_type": optimization.optimization_type,
                    "target_component": optimization.target_component,
                    "expected_improvement": optimization.expected_improvement,
                    "confidence": optimization.confidence
                }
                
                analytics_event = AnalyticsEvent(
                    event_type="optimization_applied",
                    event_data=event_data,
                    timestamp=datetime.now()
                )
                
                db_session.add(analytics_event)
                db_session.commit()
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error logging optimization application: {e}")

# Global instance
pattern_learner = PatternLearner()