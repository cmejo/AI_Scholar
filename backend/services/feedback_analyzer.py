"""
Feedback Analyzer Service for processing user feedback and driving system improvements.
"""

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
from enum import Enum
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score

from core.database import get_db
from core.redis_client import get_redis_client

logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    """Types of feedback."""
    RATING = "rating"
    CORRECTION = "correction"
    PREFERENCE = "preference"
    RELEVANCE = "relevance"
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"

class ImprovementType(Enum):
    """Types of system improvements."""
    RETRIEVAL_TUNING = "retrieval_tuning"
    RESPONSE_GENERATION = "response_generation"
    RANKING_ADJUSTMENT = "ranking_adjustment"
    PERSONALIZATION = "personalization"
    KNOWLEDGE_UPDATE = "knowledge_update"

@dataclass
class FeedbackItem:
    """Represents a feedback item."""
    feedback_id: str
    user_id: str
    message_id: str
    feedback_type: FeedbackType
    feedback_value: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: datetime
    processed: bool = False
    impact_score: float = 0.0

@dataclass
class ImprovementAction:
    """Represents a system improvement action."""
    action_id: str
    improvement_type: ImprovementType
    description: str
    target_component: str
    parameters: Dict[str, Any]
    expected_impact: float
    confidence: float
    priority: str  # 'high', 'medium', 'low'
    created_at: datetime
    applied: bool = False

@dataclass
class ABTestVariant:
    """Represents an A/B test variant."""
    variant_id: str
    name: str
    description: str
    parameters: Dict[str, Any]
    traffic_percentage: float
    active: bool = True
    created_at: datetime = None

@dataclass
class ABTestResult:
    """Represents A/B test results."""
    test_id: str
    variant_id: str
    metric_name: str
    metric_value: float
    sample_size: int
    confidence_interval: Tuple[float, float]
    statistical_significance: bool

class FeedbackAnalyzer:
    """Service for analyzing feedback and driving system improvements."""
    
    def __init__(self):
        self.redis_client = None
        self.feedback_cache_ttl = 3600  # 1 hour
        self.min_feedback_threshold = 10
        self.improvement_confidence_threshold = 0.7
        self.ab_test_duration_days = 14
        
    async def initialize(self):
        """Initialize the feedback analyzer service."""
        try:
            self.redis_client = await get_redis_client()
            logger.info("FeedbackAnalyzer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize FeedbackAnalyzer: {e}")
            raise
    
    async def process_feedback(self, feedback_item: FeedbackItem) -> bool:
        """Process a single feedback item."""
        try:
            # Store feedback in database
            await self._store_feedback(feedback_item)
            
            # Calculate impact score
            impact_score = await self._calculate_feedback_impact(feedback_item)
            feedback_item.impact_score = impact_score
            
            # Update feedback processing status
            await self._update_feedback_status(feedback_item.feedback_id, True)
            
            # Trigger improvement analysis if threshold reached
            await self._check_improvement_trigger(feedback_item)
            
            logger.info(f"Processed feedback {feedback_item.feedback_id} with impact {impact_score:.3f}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
            return False
    
    async def analyze_feedback_patterns(self, time_window_days: int = 30) -> Dict[str, Any]:
        """Analyze feedback patterns to identify improvement opportunities."""
        try:
            # Get feedback data
            feedback_data = await self._get_feedback_data(time_window_days)
            
            analysis = {
                'total_feedback': len(feedback_data),
                'feedback_by_type': self._analyze_feedback_by_type(feedback_data),
                'rating_trends': await self._analyze_rating_trends(feedback_data),
                'common_issues': await self._identify_common_issues(feedback_data),
                'user_satisfaction': await self._calculate_user_satisfaction(feedback_data),
                'improvement_opportunities': await self._identify_improvement_opportunities(feedback_data)
            }
            
            # Cache results
            cache_key = f"feedback_analysis:{time_window_days}"
            await self.redis_client.setex(
                cache_key,
                self.feedback_cache_ttl,
                json.dumps(analysis, default=str)
            )
            
            logger.info(f"Analyzed {len(feedback_data)} feedback items")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing feedback patterns: {e}")
            return {}
    
    async def generate_improvement_actions(self, feedback_analysis: Dict[str, Any]) -> List[ImprovementAction]:
        """Generate improvement actions based on feedback analysis."""
        try:
            actions = []
            
            # Generate actions based on rating trends
            if 'rating_trends' in feedback_analysis:
                rating_actions = await self._generate_rating_based_actions(feedback_analysis['rating_trends'])
                actions.extend(rating_actions)
            
            # Generate actions based on common issues
            if 'common_issues' in feedback_analysis:
                issue_actions = await self._generate_issue_based_actions(feedback_analysis['common_issues'])
                actions.extend(issue_actions)
            
            # Generate actions based on improvement opportunities
            if 'improvement_opportunities' in feedback_analysis:
                opportunity_actions = await self._generate_opportunity_based_actions(
                    feedback_analysis['improvement_opportunities']
                )
                actions.extend(opportunity_actions)
            
            # Sort by expected impact and confidence
            actions.sort(key=lambda x: x.expected_impact * x.confidence, reverse=True)
            
            logger.info(f"Generated {len(actions)} improvement actions")
            return actions
            
        except Exception as e:
            logger.error(f"Error generating improvement actions: {e}")
            return []
    
    async def apply_improvement_action(self, action: ImprovementAction) -> bool:
        """Apply an improvement action to the system."""
        try:
            success = False
            
            if action.improvement_type == ImprovementType.RETRIEVAL_TUNING:
                success = await self._apply_retrieval_tuning(action)
            elif action.improvement_type == ImprovementType.RESPONSE_GENERATION:
                success = await self._apply_response_generation_improvement(action)
            elif action.improvement_type == ImprovementType.RANKING_ADJUSTMENT:
                success = await self._apply_ranking_adjustment(action)
            elif action.improvement_type == ImprovementType.PERSONALIZATION:
                success = await self._apply_personalization_improvement(action)
            elif action.improvement_type == ImprovementType.KNOWLEDGE_UPDATE:
                success = await self._apply_knowledge_update(action)
            
            if success:
                # Mark action as applied
                await self._update_action_status(action.action_id, True)
                
                # Log the application
                await self._log_improvement_application(action)
                
                logger.info(f"Applied improvement action: {action.description}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error applying improvement action: {e}")
            return False
    
    async def create_ab_test(self, test_name: str, variants: List[ABTestVariant], 
                           metric_name: str) -> str:
        """Create an A/B test for system improvements."""
        try:
            test_id = f"ab_test_{test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Validate traffic allocation
            total_traffic = sum(v.traffic_percentage for v in variants)
            if abs(total_traffic - 100.0) > 0.01:
                raise ValueError(f"Traffic allocation must sum to 100%, got {total_traffic}%")
            
            # Store test configuration
            test_config = {
                'test_id': test_id,
                'test_name': test_name,
                'variants': [asdict(v) for v in variants],
                'metric_name': metric_name,
                'start_date': datetime.now().isoformat(),
                'end_date': (datetime.now() + timedelta(days=self.ab_test_duration_days)).isoformat(),
                'active': True
            }
            
            await self.redis_client.setex(
                f"ab_test:{test_id}",
                86400 * self.ab_test_duration_days,  # Test duration
                json.dumps(test_config, default=str)
            )
            
            # Initialize metrics tracking
            for variant in variants:
                await self.redis_client.setex(
                    f"ab_test_metrics:{test_id}:{variant.variant_id}",
                    86400 * self.ab_test_duration_days,
                    json.dumps({'samples': [], 'count': 0})
                )
            
            logger.info(f"Created A/B test {test_id} with {len(variants)} variants")
            return test_id
            
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            return ""
    
    async def assign_ab_test_variant(self, test_id: str, user_id: str) -> Optional[str]:
        """Assign a user to an A/B test variant."""
        try:
            # Get test configuration
            test_config_data = await self.redis_client.get(f"ab_test:{test_id}")
            if not test_config_data:
                return None
            
            test_config = json.loads(test_config_data)
            if not test_config.get('active', False):
                return None
            
            # Check if user already assigned
            existing_assignment = await self.redis_client.get(f"ab_test_assignment:{test_id}:{user_id}")
            if existing_assignment:
                return existing_assignment
            
            # Assign variant based on traffic allocation
            variants = test_config['variants']
            random_value = random.random() * 100
            
            cumulative_percentage = 0
            for variant in variants:
                cumulative_percentage += variant['traffic_percentage']
                if random_value <= cumulative_percentage:
                    variant_id = variant['variant_id']
                    
                    # Store assignment
                    await self.redis_client.setex(
                        f"ab_test_assignment:{test_id}:{user_id}",
                        86400 * self.ab_test_duration_days,
                        variant_id
                    )
                    
                    return variant_id
            
            # Fallback to first variant
            return variants[0]['variant_id'] if variants else None
            
        except Exception as e:
            logger.error(f"Error assigning A/B test variant: {e}")
            return None
    
    async def record_ab_test_metric(self, test_id: str, variant_id: str, 
                                  metric_value: float) -> bool:
        """Record a metric value for an A/B test variant."""
        try:
            metrics_key = f"ab_test_metrics:{test_id}:{variant_id}"
            metrics_data = await self.redis_client.get(metrics_key)
            
            if not metrics_data:
                return False
            
            metrics = json.loads(metrics_data)
            metrics['samples'].append({
                'value': metric_value,
                'timestamp': datetime.now().isoformat()
            })
            metrics['count'] += 1
            
            # Keep only recent samples to manage memory
            if len(metrics['samples']) > 10000:
                metrics['samples'] = metrics['samples'][-5000:]
            
            await self.redis_client.setex(
                metrics_key,
                86400 * self.ab_test_duration_days,
                json.dumps(metrics)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording A/B test metric: {e}")
            return False
    
    async def analyze_ab_test_results(self, test_id: str) -> List[ABTestResult]:
        """Analyze A/B test results and determine statistical significance."""
        try:
            # Get test configuration
            test_config_data = await self.redis_client.get(f"ab_test:{test_id}")
            if not test_config_data:
                return []
            
            test_config = json.loads(test_config_data)
            variants = test_config['variants']
            metric_name = test_config['metric_name']
            
            results = []
            
            for variant in variants:
                variant_id = variant['variant_id']
                
                # Get metrics data
                metrics_data = await self.redis_client.get(f"ab_test_metrics:{test_id}:{variant_id}")
                if not metrics_data:
                    continue
                
                metrics = json.loads(metrics_data)
                samples = [s['value'] for s in metrics['samples']]
                
                if len(samples) < 10:  # Minimum sample size
                    continue
                
                # Calculate statistics
                mean_value = np.mean(samples)
                std_value = np.std(samples)
                sample_size = len(samples)
                
                # Calculate confidence interval (95%)
                confidence_interval = (
                    mean_value - 1.96 * std_value / np.sqrt(sample_size),
                    mean_value + 1.96 * std_value / np.sqrt(sample_size)
                )
                
                # Simple statistical significance test (would need proper implementation)
                statistical_significance = sample_size >= 100 and std_value > 0
                
                result = ABTestResult(
                    test_id=test_id,
                    variant_id=variant_id,
                    metric_name=metric_name,
                    metric_value=mean_value,
                    sample_size=sample_size,
                    confidence_interval=confidence_interval,
                    statistical_significance=statistical_significance
                )
                
                results.append(result)
            
            logger.info(f"Analyzed A/B test {test_id} with {len(results)} variant results")
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing A/B test results: {e}")
            return []
    
    async def measure_improvement_effectiveness(self, action: ImprovementAction, 
                                             measurement_period_days: int = 7) -> Dict[str, float]:
        """Measure the effectiveness of an applied improvement action."""
        try:
            # Get baseline metrics (before improvement)
            baseline_start = action.created_at - timedelta(days=measurement_period_days)
            baseline_end = action.created_at
            baseline_metrics = await self._get_performance_metrics(baseline_start, baseline_end)
            
            # Get post-improvement metrics
            post_start = action.created_at
            post_end = action.created_at + timedelta(days=measurement_period_days)
            post_metrics = await self._get_performance_metrics(post_start, post_end)
            
            # Calculate improvements
            effectiveness = {}
            
            for metric_name in baseline_metrics:
                if metric_name in post_metrics:
                    baseline_value = baseline_metrics[metric_name]
                    post_value = post_metrics[metric_name]
                    
                    if baseline_value > 0:
                        improvement = (post_value - baseline_value) / baseline_value
                        effectiveness[metric_name] = improvement
            
            # Store effectiveness results
            await self._store_improvement_effectiveness(action.action_id, effectiveness)
            
            logger.info(f"Measured effectiveness for action {action.action_id}: {effectiveness}")
            return effectiveness
            
        except Exception as e:
            logger.error(f"Error measuring improvement effectiveness: {e}")
            return {}
    
    async def _store_feedback(self, feedback_item: FeedbackItem):
        """Store feedback in database."""
        try:
            from core.database import UserFeedback
            
            db_session = next(get_db())
            try:
                user_feedback = UserFeedback(
                    user_id=feedback_item.user_id,
                    message_id=feedback_item.message_id,
                    feedback_type=feedback_item.feedback_type.value,
                    feedback_value=feedback_item.feedback_value,
                    processed=feedback_item.processed
                )
                
                db_session.add(user_feedback)
                db_session.commit()
                
                # Update feedback_item with database ID
                feedback_item.feedback_id = user_feedback.id
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error storing feedback: {e}")
            raise
    
    async def _calculate_feedback_impact(self, feedback_item: FeedbackItem) -> float:
        """Calculate the impact score of a feedback item."""
        try:
            impact_score = 0.0
            
            # Base impact based on feedback type
            type_weights = {
                FeedbackType.RATING: 0.3,
                FeedbackType.CORRECTION: 0.8,
                FeedbackType.PREFERENCE: 0.4,
                FeedbackType.RELEVANCE: 0.6,
                FeedbackType.ACCURACY: 0.9,
                FeedbackType.COMPLETENESS: 0.5
            }
            
            impact_score += type_weights.get(feedback_item.feedback_type, 0.3)
            
            # Adjust based on feedback value
            if feedback_item.feedback_type == FeedbackType.RATING:
                rating = feedback_item.feedback_value.get('rating', 3)
                # Higher impact for extreme ratings
                if rating <= 2 or rating >= 4:
                    impact_score *= 1.5
            
            # Adjust based on user history (simplified)
            user_feedback_count = await self._get_user_feedback_count(feedback_item.user_id)
            if user_feedback_count > 10:  # Frequent feedback provider
                impact_score *= 1.2
            
            return min(impact_score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating feedback impact: {e}")
            return 0.0
    
    async def _get_user_feedback_count(self, user_id: str) -> int:
        """Get the count of feedback items from a user."""
        try:
            from core.database import UserFeedback
            
            db_session = next(get_db())
            try:
                count = db_session.query(UserFeedback).filter(
                    UserFeedback.user_id == user_id
                ).count()
                return count
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error getting user feedback count: {e}")
            return 0
    
    async def _update_feedback_status(self, feedback_id: str, processed: bool):
        """Update feedback processing status."""
        try:
            from core.database import UserFeedback
            
            db_session = next(get_db())
            try:
                feedback = db_session.query(UserFeedback).filter(
                    UserFeedback.id == feedback_id
                ).first()
                
                if feedback:
                    feedback.processed = processed
                    db_session.commit()
                    
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error updating feedback status: {e}")
    
    async def _check_improvement_trigger(self, feedback_item: FeedbackItem):
        """Check if feedback should trigger improvement analysis."""
        try:
            # Get recent feedback count
            recent_feedback = await self._get_recent_feedback_count(hours=24)
            
            # Trigger improvement analysis if threshold reached
            if recent_feedback >= self.min_feedback_threshold:
                await self._trigger_improvement_analysis()
                
        except Exception as e:
            logger.error(f"Error checking improvement trigger: {e}")
    
    async def _get_recent_feedback_count(self, hours: int = 24) -> int:
        """Get count of recent feedback items."""
        try:
            from core.database import UserFeedback
            
            db_session = next(get_db())
            try:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                count = db_session.query(UserFeedback).filter(
                    UserFeedback.created_at >= cutoff_time
                ).count()
                return count
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error getting recent feedback count: {e}")
            return 0
    
    async def _trigger_improvement_analysis(self):
        """Trigger improvement analysis."""
        try:
            # Store trigger event in Redis for background processing
            trigger_data = {
                'triggered_at': datetime.now().isoformat(),
                'trigger_type': 'feedback_threshold'
            }
            
            await self.redis_client.lpush(
                'improvement_analysis_queue',
                json.dumps(trigger_data)
            )
            
            logger.info("Triggered improvement analysis")
            
        except Exception as e:
            logger.error(f"Error triggering improvement analysis: {e}")
    
    async def _get_feedback_data(self, time_window_days: int) -> List[Dict]:
        """Get feedback data from database."""
        try:
            from core.database import UserFeedback
            
            db_session = next(get_db())
            try:
                cutoff_time = datetime.now() - timedelta(days=time_window_days)
                results = db_session.query(UserFeedback).filter(
                    UserFeedback.created_at >= cutoff_time
                ).all()
                
                return [
                    {
                        'feedback_id': result.id,
                        'user_id': result.user_id,
                        'message_id': result.message_id,
                        'feedback_type': result.feedback_type,
                        'feedback_value': result.feedback_value or {},
                        'created_at': result.created_at,
                        'processed': result.processed
                    }
                    for result in results
                ]
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error getting feedback data: {e}")
            return []
    
    def _analyze_feedback_by_type(self, feedback_data: List[Dict]) -> Dict[str, int]:
        """Analyze feedback distribution by type."""
        type_counts = Counter()
        for feedback in feedback_data:
            type_counts[feedback['feedback_type']] += 1
        return dict(type_counts)
    
    async def _analyze_rating_trends(self, feedback_data: List[Dict]) -> Dict[str, Any]:
        """Analyze rating trends."""
        try:
            rating_feedback = [
                f for f in feedback_data 
                if f['feedback_type'] == 'rating' and 'rating' in f['feedback_value']
            ]
            
            if not rating_feedback:
                return {}
            
            ratings = [f['feedback_value']['rating'] for f in rating_feedback]
            
            return {
                'average_rating': np.mean(ratings),
                'rating_distribution': dict(Counter(ratings)),
                'total_ratings': len(ratings),
                'trend': 'improving' if np.mean(ratings) > 3.5 else 'declining'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing rating trends: {e}")
            return {}
    
    async def _identify_common_issues(self, feedback_data: List[Dict]) -> List[Dict[str, Any]]:
        """Identify common issues from feedback."""
        try:
            issues = []
            
            # Analyze correction feedback
            corrections = [
                f for f in feedback_data 
                if f['feedback_type'] == 'correction'
            ]
            
            if corrections:
                issues.append({
                    'issue_type': 'accuracy',
                    'frequency': len(corrections),
                    'severity': 'high',
                    'description': f'{len(corrections)} accuracy corrections reported'
                })
            
            # Analyze low ratings
            low_ratings = [
                f for f in feedback_data 
                if (f['feedback_type'] == 'rating' and 
                    f['feedback_value'].get('rating', 5) <= 2)
            ]
            
            if len(low_ratings) > 5:
                issues.append({
                    'issue_type': 'satisfaction',
                    'frequency': len(low_ratings),
                    'severity': 'medium',
                    'description': f'{len(low_ratings)} low satisfaction ratings'
                })
            
            return issues
            
        except Exception as e:
            logger.error(f"Error identifying common issues: {e}")
            return []
    
    async def _calculate_user_satisfaction(self, feedback_data: List[Dict]) -> Dict[str, float]:
        """Calculate user satisfaction metrics."""
        try:
            rating_feedback = [
                f for f in feedback_data 
                if f['feedback_type'] == 'rating' and 'rating' in f['feedback_value']
            ]
            
            if not rating_feedback:
                return {'satisfaction_score': 0.0, 'nps_score': 0.0}
            
            ratings = [f['feedback_value']['rating'] for f in rating_feedback]
            
            # Calculate satisfaction score (percentage of ratings >= 4)
            satisfied_count = sum(1 for r in ratings if r >= 4)
            satisfaction_score = satisfied_count / len(ratings)
            
            # Calculate NPS-like score
            promoters = sum(1 for r in ratings if r >= 4)
            detractors = sum(1 for r in ratings if r <= 2)
            nps_score = (promoters - detractors) / len(ratings)
            
            return {
                'satisfaction_score': satisfaction_score,
                'nps_score': nps_score
            }
            
        except Exception as e:
            logger.error(f"Error calculating user satisfaction: {e}")
            return {'satisfaction_score': 0.0, 'nps_score': 0.0}
    
    async def _identify_improvement_opportunities(self, feedback_data: List[Dict]) -> List[Dict[str, Any]]:
        """Identify improvement opportunities from feedback."""
        try:
            opportunities = []
            
            # Analyze preference feedback
            preferences = [
                f for f in feedback_data 
                if f['feedback_type'] == 'preference'
            ]
            
            if preferences:
                opportunities.append({
                    'opportunity_type': 'personalization',
                    'priority': 'medium',
                    'description': f'Personalization improvements based on {len(preferences)} preference feedback items',
                    'expected_impact': 0.3
                })
            
            # Analyze relevance feedback
            relevance_issues = [
                f for f in feedback_data 
                if (f['feedback_type'] == 'relevance' and 
                    f['feedback_value'].get('relevant', True) == False)
            ]
            
            if len(relevance_issues) > 3:
                opportunities.append({
                    'opportunity_type': 'retrieval_improvement',
                    'priority': 'high',
                    'description': f'Retrieval improvements needed based on {len(relevance_issues)} relevance issues',
                    'expected_impact': 0.5
                })
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error identifying improvement opportunities: {e}")
            return []
    
    async def _generate_rating_based_actions(self, rating_trends: Dict[str, Any]) -> List[ImprovementAction]:
        """Generate improvement actions based on rating trends."""
        actions = []
        
        try:
            if rating_trends.get('average_rating', 5) < 3.5:
                action = ImprovementAction(
                    action_id=f"rating_improvement_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    improvement_type=ImprovementType.RESPONSE_GENERATION,
                    description="Improve response quality based on low average ratings",
                    target_component="response_generator",
                    parameters={
                        'quality_threshold': 0.8,
                        'review_responses': True
                    },
                    expected_impact=0.4,
                    confidence=0.7,
                    priority="high",
                    created_at=datetime.now()
                )
                actions.append(action)
            
            return actions
            
        except Exception as e:
            logger.error(f"Error generating rating-based actions: {e}")
            return []
    
    async def _generate_issue_based_actions(self, common_issues: List[Dict[str, Any]]) -> List[ImprovementAction]:
        """Generate improvement actions based on common issues."""
        actions = []
        
        try:
            for issue in common_issues:
                if issue['issue_type'] == 'accuracy':
                    action = ImprovementAction(
                        action_id=f"accuracy_improvement_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        improvement_type=ImprovementType.KNOWLEDGE_UPDATE,
                        description=f"Address accuracy issues: {issue['description']}",
                        target_component="knowledge_base",
                        parameters={
                            'accuracy_check': True,
                            'source_verification': True
                        },
                        expected_impact=0.6,
                        confidence=0.8,
                        priority="high",
                        created_at=datetime.now()
                    )
                    actions.append(action)
                
                elif issue['issue_type'] == 'satisfaction':
                    action = ImprovementAction(
                        action_id=f"satisfaction_improvement_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        improvement_type=ImprovementType.PERSONALIZATION,
                        description=f"Improve user satisfaction: {issue['description']}",
                        target_component="personalization_engine",
                        parameters={
                            'satisfaction_target': 0.8,
                            'personalization_boost': True
                        },
                        expected_impact=0.3,
                        confidence=0.6,
                        priority="medium",
                        created_at=datetime.now()
                    )
                    actions.append(action)
            
            return actions
            
        except Exception as e:
            logger.error(f"Error generating issue-based actions: {e}")
            return []
    
    async def _generate_opportunity_based_actions(self, opportunities: List[Dict[str, Any]]) -> List[ImprovementAction]:
        """Generate improvement actions based on opportunities."""
        actions = []
        
        try:
            for opportunity in opportunities:
                if opportunity['opportunity_type'] == 'personalization':
                    action = ImprovementAction(
                        action_id=f"personalization_opportunity_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        improvement_type=ImprovementType.PERSONALIZATION,
                        description=opportunity['description'],
                        target_component="personalization_engine",
                        parameters={
                            'personalization_level': 'enhanced',
                            'preference_weight': 1.5
                        },
                        expected_impact=opportunity.get('expected_impact', 0.3),
                        confidence=0.7,
                        priority=opportunity.get('priority', 'medium'),
                        created_at=datetime.now()
                    )
                    actions.append(action)
                
                elif opportunity['opportunity_type'] == 'retrieval_improvement':
                    action = ImprovementAction(
                        action_id=f"retrieval_opportunity_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        improvement_type=ImprovementType.RETRIEVAL_TUNING,
                        description=opportunity['description'],
                        target_component="retrieval_engine",
                        parameters={
                            'relevance_threshold': 0.8,
                            'ranking_boost': True
                        },
                        expected_impact=opportunity.get('expected_impact', 0.5),
                        confidence=0.8,
                        priority=opportunity.get('priority', 'high'),
                        created_at=datetime.now()
                    )
                    actions.append(action)
            
            return actions
            
        except Exception as e:
            logger.error(f"Error generating opportunity-based actions: {e}")
            return []
    
    async def _apply_retrieval_tuning(self, action: ImprovementAction) -> bool:
        """Apply retrieval tuning improvement."""
        try:
            # Store tuning parameters in Redis for retrieval service
            tuning_key = f"retrieval_tuning:{action.action_id}"
            tuning_data = {
                "action_id": action.action_id,
                "parameters": action.parameters,
                "applied_at": datetime.now().isoformat()
            }
            
            await self.redis_client.setex(tuning_key, 86400, json.dumps(tuning_data))
            return True
            
        except Exception as e:
            logger.error(f"Error applying retrieval tuning: {e}")
            return False
    
    async def _apply_response_generation_improvement(self, action: ImprovementAction) -> bool:
        """Apply response generation improvement."""
        try:
            # Store improvement parameters in Redis
            improvement_key = f"response_improvement:{action.action_id}"
            improvement_data = {
                "action_id": action.action_id,
                "parameters": action.parameters,
                "applied_at": datetime.now().isoformat()
            }
            
            await self.redis_client.setex(improvement_key, 86400, json.dumps(improvement_data))
            return True
            
        except Exception as e:
            logger.error(f"Error applying response generation improvement: {e}")
            return False
    
    async def _apply_ranking_adjustment(self, action: ImprovementAction) -> bool:
        """Apply ranking adjustment improvement."""
        try:
            # Store ranking parameters in Redis
            ranking_key = f"ranking_adjustment:{action.action_id}"
            ranking_data = {
                "action_id": action.action_id,
                "parameters": action.parameters,
                "applied_at": datetime.now().isoformat()
            }
            
            await self.redis_client.setex(ranking_key, 86400, json.dumps(ranking_data))
            return True
            
        except Exception as e:
            logger.error(f"Error applying ranking adjustment: {e}")
            return False
    
    async def _apply_personalization_improvement(self, action: ImprovementAction) -> bool:
        """Apply personalization improvement."""
        try:
            # Store personalization parameters in Redis
            personalization_key = f"personalization_improvement:{action.action_id}"
            personalization_data = {
                "action_id": action.action_id,
                "parameters": action.parameters,
                "applied_at": datetime.now().isoformat()
            }
            
            await self.redis_client.setex(personalization_key, 86400, json.dumps(personalization_data))
            return True
            
        except Exception as e:
            logger.error(f"Error applying personalization improvement: {e}")
            return False
    
    async def _apply_knowledge_update(self, action: ImprovementAction) -> bool:
        """Apply knowledge update improvement."""
        try:
            # Store knowledge update parameters in Redis
            knowledge_key = f"knowledge_update:{action.action_id}"
            knowledge_data = {
                "action_id": action.action_id,
                "parameters": action.parameters,
                "applied_at": datetime.now().isoformat()
            }
            
            await self.redis_client.setex(knowledge_key, 86400, json.dumps(knowledge_data))
            return True
            
        except Exception as e:
            logger.error(f"Error applying knowledge update: {e}")
            return False
    
    async def _update_action_status(self, action_id: str, applied: bool):
        """Update improvement action status."""
        try:
            status_key = f"action_status:{action_id}"
            status_data = {
                "applied": applied,
                "updated_at": datetime.now().isoformat()
            }
            
            await self.redis_client.setex(status_key, 86400 * 7, json.dumps(status_data))
            
        except Exception as e:
            logger.error(f"Error updating action status: {e}")
    
    async def _log_improvement_application(self, action: ImprovementAction):
        """Log improvement action application."""
        try:
            from core.database import AnalyticsEvent
            
            db_session = next(get_db())
            try:
                event_data = {
                    "action_id": action.action_id,
                    "improvement_type": action.improvement_type.value,
                    "target_component": action.target_component,
                    "expected_impact": action.expected_impact,
                    "confidence": action.confidence
                }
                
                analytics_event = AnalyticsEvent(
                    event_type="improvement_applied",
                    event_data=event_data,
                    timestamp=datetime.now()
                )
                
                db_session.add(analytics_event)
                db_session.commit()
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error logging improvement application: {e}")
    
    async def _get_performance_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Get performance metrics for a time period."""
        try:
            from core.database import AnalyticsEvent
            
            db_session = next(get_db())
            try:
                # Get relevant analytics events
                events = db_session.query(AnalyticsEvent).filter(
                    AnalyticsEvent.timestamp >= start_date,
                    AnalyticsEvent.timestamp <= end_date,
                    AnalyticsEvent.event_type.in_(['query_submitted', 'feedback_provided'])
                ).all()
                
                metrics = {}
                
                # Calculate response time metrics
                response_times = []
                satisfaction_ratings = []
                
                for event in events:
                    event_data = event.event_data or {}
                    
                    if event.event_type == 'query_submitted' and 'response_time' in event_data:
                        response_times.append(event_data['response_time'])
                    
                    elif event.event_type == 'feedback_provided' and 'rating' in event_data:
                        satisfaction_ratings.append(event_data['rating'])
                
                if response_times:
                    metrics['avg_response_time'] = np.mean(response_times)
                
                if satisfaction_ratings:
                    metrics['avg_satisfaction'] = np.mean(satisfaction_ratings)
                    metrics['satisfaction_rate'] = sum(1 for r in satisfaction_ratings if r >= 4) / len(satisfaction_ratings)
                
                return metrics
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}
    
    async def _store_improvement_effectiveness(self, action_id: str, effectiveness: Dict[str, float]):
        """Store improvement effectiveness results."""
        try:
            effectiveness_key = f"improvement_effectiveness:{action_id}"
            effectiveness_data = {
                "action_id": action_id,
                "effectiveness": effectiveness,
                "measured_at": datetime.now().isoformat()
            }
            
            await self.redis_client.setex(effectiveness_key, 86400 * 30, json.dumps(effectiveness_data))
            
        except Exception as e:
            logger.error(f"Error storing improvement effectiveness: {e}")

# Global instance
feedback_analyzer = FeedbackAnalyzer()