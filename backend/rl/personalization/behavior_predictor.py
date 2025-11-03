"""
User behavior prediction system for advanced personalization.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

from .personalization_models import (
    BehaviorPattern,
    BehaviorPatternType,
    PredictedAction,
    SatisfactionTrajectory,
    ContextCondition,
    SuccessIndicator
)

logger = logging.getLogger(__name__)


class PredictionConfidence(Enum):
    """Confidence levels for predictions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class BehaviorCategory(Enum):
    """Categories of user behavior."""
    ENGAGEMENT = "engagement"
    TASK_COMPLETION = "task_completion"
    SATISFACTION = "satisfaction"
    LEARNING = "learning"
    EXPLORATION = "exploration"
    EFFICIENCY = "efficiency"


@dataclass
class UserHistory:
    """User interaction history for behavior analysis."""
    user_id: str
    interactions: List[Dict[str, Any]]
    sessions: List[Dict[str, Any]]
    preferences: Dict[str, float]
    performance_metrics: Dict[str, List[float]]
    temporal_patterns: Dict[str, Any] = field(default_factory=dict)
    
    def get_recent_interactions(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get interactions from the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent = []
        for interaction in self.interactions:
            timestamp = interaction.get('timestamp')
            if timestamp and isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif not isinstance(timestamp, datetime):
                continue
            
            if timestamp >= cutoff_time:
                recent.append(interaction)
        
        return recent
    
    def get_session_statistics(self) -> Dict[str, float]:
        """Get statistics about user sessions."""
        if not self.sessions:
            return {}
        
        durations = [session.get('duration', 0) for session in self.sessions]
        satisfactions = [session.get('satisfaction', 0.5) for session in self.sessions]
        completions = [session.get('completion_rate', 0.5) for session in self.sessions]
        
        return {
            'avg_session_duration': np.mean(durations),
            'avg_satisfaction': np.mean(satisfactions),
            'avg_completion_rate': np.mean(completions),
            'total_sessions': len(self.sessions),
            'session_frequency': len(self.sessions) / max(1, (datetime.now() - 
                datetime.fromisoformat(self.sessions[0].get('timestamp', datetime.now().isoformat()))).days)
        }


class PatternDetector:
    """Detects behavioral patterns in user interactions."""
    
    def __init__(self, min_pattern_occurrences: int = 3):
        self.min_pattern_occurrences = min_pattern_occurrences
        self.detected_patterns: Dict[str, List[BehaviorPattern]] = {}
    
    async def detect_patterns(self, user_history: UserHistory) -> List[BehaviorPattern]:
        """Detect behavioral patterns from user history."""
        patterns = []
        
        # Detect different types of patterns
        patterns.extend(await self._detect_sequential_patterns(user_history))
        patterns.extend(await self._detect_cyclical_patterns(user_history))
        patterns.extend(await self._detect_contextual_patterns(user_history))
        patterns.extend(await self._detect_preference_patterns(user_history))
        patterns.extend(await self._detect_temporal_patterns(user_history))
        
        # Store detected patterns
        self.detected_patterns[user_history.user_id] = patterns
        
        return patterns
    
    async def _detect_sequential_patterns(self, user_history: UserHistory) -> List[BehaviorPattern]:
        """Detect sequential behavior patterns."""
        patterns = []
        interactions = user_history.interactions
        
        if len(interactions) < self.min_pattern_occurrences:
            return patterns
        
        # Look for action sequences
        action_sequences = []
        for i in range(len(interactions) - 2):
            sequence = [
                interactions[i].get('action_type', 'unknown'),
                interactions[i+1].get('action_type', 'unknown'),
                interactions[i+2].get('action_type', 'unknown')
            ]
            action_sequences.append(sequence)
        
        # Find common sequences
        sequence_counts = {}
        for seq in action_sequences:
            seq_key = tuple(seq)
            sequence_counts[seq_key] = sequence_counts.get(seq_key, 0) + 1
        
        # Create patterns for frequent sequences
        total_sequences = len(action_sequences)
        for sequence, count in sequence_counts.items():
            if count >= self.min_pattern_occurrences:
                frequency = count / total_sequences
                
                pattern = BehaviorPattern(
                    pattern_id=f"seq_{hash(sequence)}",
                    pattern_type=BehaviorPatternType.SEQUENTIAL,
                    frequency=frequency,
                    context_conditions=[],
                    predictive_features=[f"action_sequence_{i}" for i in range(3)],
                    success_indicators=[
                        SuccessIndicator(
                            metric_name="sequence_completion",
                            target_value=1.0,
                            current_value=frequency
                        )
                    ],
                    confidence=min(1.0, count / 10.0)
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _detect_cyclical_patterns(self, user_history: UserHistory) -> List[BehaviorPattern]:
        """Detect cyclical behavior patterns."""
        patterns = []
        interactions = user_history.interactions
        
        if len(interactions) < 7:  # Need at least a week of data
            return patterns
        
        # Group interactions by day of week and hour
        daily_patterns = {}
        hourly_patterns = {}
        
        for interaction in interactions:
            timestamp = interaction.get('timestamp')
            if not timestamp:
                continue
            
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            day_of_week = timestamp.weekday()
            hour = timestamp.hour
            
            # Track daily patterns
            if day_of_week not in daily_patterns:
                daily_patterns[day_of_week] = []
            daily_patterns[day_of_week].append(interaction)
            
            # Track hourly patterns
            if hour not in hourly_patterns:
                hourly_patterns[hour] = []
            hourly_patterns[hour].append(interaction)
        
        # Analyze daily patterns
        for day, day_interactions in daily_patterns.items():
            if len(day_interactions) >= self.min_pattern_occurrences:
                avg_satisfaction = np.mean([
                    interaction.get('satisfaction', 0.5) 
                    for interaction in day_interactions
                ])
                
                pattern = BehaviorPattern(
                    pattern_id=f"daily_{day}",
                    pattern_type=BehaviorPatternType.CYCLICAL,
                    frequency=len(day_interactions) / len(interactions),
                    context_conditions=[
                        ContextCondition(
                            condition_type="day_of_week",
                            condition_value=day,
                            operator="equals"
                        )
                    ],
                    predictive_features=["day_of_week", "satisfaction_trend"],
                    success_indicators=[
                        SuccessIndicator(
                            metric_name="daily_satisfaction",
                            target_value=0.7,
                            current_value=avg_satisfaction
                        )
                    ],
                    confidence=min(1.0, len(day_interactions) / 20.0)
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _detect_contextual_patterns(self, user_history: UserHistory) -> List[BehaviorPattern]:
        """Detect context-dependent behavior patterns."""
        patterns = []
        interactions = user_history.interactions
        
        # Group interactions by context features
        context_groups = {}
        
        for interaction in interactions:
            context = interaction.get('context', {})
            
            # Group by task complexity
            complexity = context.get('task_complexity', 0.5)
            complexity_bucket = "low" if complexity < 0.3 else "medium" if complexity < 0.7 else "high"
            
            if complexity_bucket not in context_groups:
                context_groups[complexity_bucket] = []
            context_groups[complexity_bucket].append(interaction)
        
        # Analyze patterns for each context group
        for context_key, group_interactions in context_groups.items():
            if len(group_interactions) >= self.min_pattern_occurrences:
                avg_completion = np.mean([
                    interaction.get('task_completion', 0.5)
                    for interaction in group_interactions
                ])
                
                avg_duration = np.mean([
                    interaction.get('duration', 60)
                    for interaction in group_interactions
                ])
                
                pattern = BehaviorPattern(
                    pattern_id=f"context_{context_key}",
                    pattern_type=BehaviorPatternType.CONTEXTUAL,
                    frequency=len(group_interactions) / len(interactions),
                    context_conditions=[
                        ContextCondition(
                            condition_type="task_complexity_bucket",
                            condition_value=context_key,
                            operator="equals"
                        )
                    ],
                    predictive_features=["task_complexity", "completion_rate", "duration"],
                    success_indicators=[
                        SuccessIndicator(
                            metric_name="completion_rate",
                            target_value=0.8,
                            current_value=avg_completion
                        )
                    ],
                    confidence=min(1.0, len(group_interactions) / 15.0)
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _detect_preference_patterns(self, user_history: UserHistory) -> List[BehaviorPattern]:
        """Detect preference-based behavior patterns."""
        patterns = []
        
        # Analyze preference stability over time
        preferences = user_history.preferences
        interactions = user_history.interactions
        
        if not preferences or len(interactions) < 5:
            return patterns
        
        # Track preference consistency
        preference_consistency = {}
        
        for interaction in interactions:
            interaction_prefs = interaction.get('preferences', {})
            
            for pref_key, pref_value in interaction_prefs.items():
                if pref_key in preferences:
                    if pref_key not in preference_consistency:
                        preference_consistency[pref_key] = []
                    
                    # Calculate consistency (how close to stored preference)
                    consistency = 1.0 - abs(pref_value - preferences[pref_key])
                    preference_consistency[pref_key].append(consistency)
        
        # Create patterns for stable preferences
        for pref_key, consistency_scores in preference_consistency.items():
            if len(consistency_scores) >= self.min_pattern_occurrences:
                avg_consistency = np.mean(consistency_scores)
                
                if avg_consistency > 0.7:  # High consistency threshold
                    pattern = BehaviorPattern(
                        pattern_id=f"pref_{pref_key}",
                        pattern_type=BehaviorPatternType.PREFERENCE_BASED,
                        frequency=avg_consistency,
                        context_conditions=[],
                        predictive_features=[pref_key, "preference_stability"],
                        success_indicators=[
                            SuccessIndicator(
                                metric_name="preference_consistency",
                                target_value=0.8,
                                current_value=avg_consistency
                            )
                        ],
                        confidence=min(1.0, len(consistency_scores) / 10.0)
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _detect_temporal_patterns(self, user_history: UserHistory) -> List[BehaviorPattern]:
        """Detect temporal behavior patterns."""
        patterns = []
        interactions = user_history.interactions
        
        if len(interactions) < 10:
            return patterns
        
        # Analyze satisfaction trends over time
        satisfaction_over_time = []
        
        for interaction in interactions:
            timestamp = interaction.get('timestamp')
            satisfaction = interaction.get('satisfaction', 0.5)
            
            if timestamp:
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                satisfaction_over_time.append((timestamp, satisfaction))
        
        if len(satisfaction_over_time) >= 5:
            # Sort by time
            satisfaction_over_time.sort(key=lambda x: x[0])
            
            # Calculate trend
            satisfactions = [s for _, s in satisfaction_over_time]
            time_indices = list(range(len(satisfactions)))
            
            # Simple linear trend
            if len(satisfactions) > 1:
                correlation = np.corrcoef(time_indices, satisfactions)[0, 1]
                
                if not np.isnan(correlation) and abs(correlation) > 0.3:
                    trend_direction = "improving" if correlation > 0 else "declining"
                    
                    pattern = BehaviorPattern(
                        pattern_id=f"temporal_satisfaction_{trend_direction}",
                        pattern_type=BehaviorPatternType.TEMPORAL,
                        frequency=abs(correlation),
                        context_conditions=[],
                        predictive_features=["time_trend", "satisfaction_history"],
                        success_indicators=[
                            SuccessIndicator(
                                metric_name="satisfaction_trend",
                                target_value=0.1 if trend_direction == "improving" else -0.1,
                                current_value=correlation
                            )
                        ],
                        confidence=min(1.0, abs(correlation))
                    )
                    patterns.append(pattern)
        
        return patterns


class ActionPredictor:
    """Predicts user actions based on current context and patterns."""
    
    def __init__(self):
        self.action_probabilities: Dict[str, Dict[str, float]] = {}
        self.context_action_mapping: Dict[str, List[str]] = {}
    
    async def predict_next_action(
        self, 
        current_context: Dict[str, Any],
        user_patterns: List[BehaviorPattern],
        user_history: UserHistory
    ) -> PredictedAction:
        """Predict the most likely next user action."""
        
        # Get applicable patterns
        applicable_patterns = [
            pattern for pattern in user_patterns
            if pattern.matches_context(current_context)
        ]
        
        if not applicable_patterns:
            return await self._predict_default_action(current_context)
        
        # Calculate action probabilities based on patterns
        action_scores = {}
        
        for pattern in applicable_patterns:
            pattern_strength = pattern.get_prediction_strength(current_context)
            
            # Get likely actions for this pattern
            likely_actions = await self._get_pattern_actions(pattern, user_history)
            
            for action_type, base_probability in likely_actions.items():
                if action_type not in action_scores:
                    action_scores[action_type] = 0.0
                
                action_scores[action_type] += pattern_strength * base_probability
        
        # Select action with highest score
        if action_scores:
            best_action = max(action_scores.items(), key=lambda x: x[1])
            action_type, probability = best_action
            
            # Generate action parameters
            action_parameters = await self._generate_action_parameters(
                action_type, current_context, applicable_patterns
            )
            
            # Calculate confidence
            confidence = min(1.0, probability * len(applicable_patterns) / 5.0)
            
            # Generate reasoning
            reasoning = await self._generate_reasoning(
                action_type, applicable_patterns, current_context
            )
            
            # Generate alternatives
            alternatives = await self._generate_alternatives(
                action_scores, action_type, current_context
            )
            
            return PredictedAction(
                action_type=action_type,
                action_parameters=action_parameters,
                probability=probability,
                confidence=confidence,
                reasoning=reasoning,
                alternative_actions=alternatives
            )
        
        return await self._predict_default_action(current_context)
    
    async def _get_pattern_actions(
        self, 
        pattern: BehaviorPattern, 
        user_history: UserHistory
    ) -> Dict[str, float]:
        """Get likely actions for a behavior pattern."""
        
        # Analyze historical actions for this pattern type
        pattern_actions = {}
        
        for interaction in user_history.interactions:
            context = interaction.get('context', {})
            
            if pattern.matches_context(context):
                action_type = interaction.get('action_type', 'unknown')
                success = interaction.get('satisfaction', 0.5) > 0.6
                
                if action_type not in pattern_actions:
                    pattern_actions[action_type] = []
                
                pattern_actions[action_type].append(1.0 if success else 0.0)
        
        # Calculate success rates for each action
        action_probabilities = {}
        for action_type, successes in pattern_actions.items():
            if len(successes) >= 2:  # Minimum observations
                success_rate = np.mean(successes)
                action_probabilities[action_type] = success_rate
        
        # Default actions if no historical data
        if not action_probabilities:
            if pattern.pattern_type == BehaviorPatternType.SEQUENTIAL:
                action_probabilities = {"continue_sequence": 0.7, "break_sequence": 0.3}
            elif pattern.pattern_type == BehaviorPatternType.CONTEXTUAL:
                action_probabilities = {"context_appropriate": 0.8, "explore_new": 0.2}
            else:
                action_probabilities = {"default_action": 0.5}
        
        return action_probabilities
    
    async def _generate_action_parameters(
        self, 
        action_type: str, 
        context: Dict[str, Any],
        patterns: List[BehaviorPattern]
    ) -> Dict[str, Any]:
        """Generate parameters for the predicted action."""
        
        parameters = {
            "action_type": action_type,
            "context_driven": True,
            "pattern_based": len(patterns) > 0
        }
        
        # Add context-specific parameters
        if "complexity" in context:
            parameters["complexity_level"] = context["complexity"]
        
        if "user_expertise" in context:
            parameters["expertise_level"] = context["user_expertise"]
        
        # Add pattern-specific parameters
        for pattern in patterns:
            if pattern.pattern_type == BehaviorPatternType.PREFERENCE_BASED:
                parameters["preference_aligned"] = True
            elif pattern.pattern_type == BehaviorPatternType.TEMPORAL:
                parameters["time_sensitive"] = True
        
        return parameters
    
    async def _generate_reasoning(
        self, 
        action_type: str, 
        patterns: List[BehaviorPattern],
        context: Dict[str, Any]
    ) -> str:
        """Generate reasoning for the predicted action."""
        
        reasons = []
        
        # Pattern-based reasoning
        for pattern in patterns:
            if pattern.confidence > 0.7:
                reasons.append(f"Strong {pattern.pattern_type.value} pattern detected")
            elif pattern.confidence > 0.5:
                reasons.append(f"Moderate {pattern.pattern_type.value} pattern observed")
        
        # Context-based reasoning
        if context.get("task_complexity", 0.5) > 0.7:
            reasons.append("High task complexity suggests detailed approach")
        elif context.get("task_complexity", 0.5) < 0.3:
            reasons.append("Low task complexity allows for quick action")
        
        if context.get("user_satisfaction", 0.5) < 0.4:
            reasons.append("Low satisfaction indicates need for different approach")
        
        # Default reasoning
        if not reasons:
            reasons.append(f"Predicted based on action type: {action_type}")
        
        return "; ".join(reasons)
    
    async def _generate_alternatives(
        self, 
        action_scores: Dict[str, float], 
        selected_action: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate alternative actions."""
        
        alternatives = []
        
        # Sort actions by score, excluding the selected one
        sorted_actions = sorted(
            [(action, score) for action, score in action_scores.items() if action != selected_action],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Take top 3 alternatives
        for action_type, score in sorted_actions[:3]:
            alternative = {
                "action_type": action_type,
                "probability": score,
                "reasoning": f"Alternative with {score:.2f} probability"
            }
            alternatives.append(alternative)
        
        return alternatives
    
    async def _predict_default_action(self, context: Dict[str, Any]) -> PredictedAction:
        """Predict default action when no patterns are available."""
        
        # Simple context-based default prediction
        if context.get("task_complexity", 0.5) > 0.7:
            action_type = "request_help"
            probability = 0.6
        elif context.get("user_satisfaction", 0.5) < 0.4:
            action_type = "change_approach"
            probability = 0.5
        else:
            action_type = "continue_current"
            probability = 0.4
        
        return PredictedAction(
            action_type=action_type,
            action_parameters={"default": True, "context_based": True},
            probability=probability,
            confidence=0.3,  # Low confidence for default predictions
            reasoning="Default prediction based on limited context",
            alternative_actions=[]
        )


class SatisfactionPredictor:
    """Predicts user satisfaction trajectory over time."""
    
    def __init__(self):
        self.satisfaction_models: Dict[str, Any] = {}
        self.trajectory_cache: Dict[str, SatisfactionTrajectory] = {}
    
    async def predict_satisfaction_trajectory(
        self, 
        user_history: UserHistory,
        current_context: Dict[str, Any],
        time_horizon_minutes: int = 60
    ) -> SatisfactionTrajectory:
        """Predict satisfaction trajectory over specified time horizon."""
        
        # Generate time points
        time_points = list(range(0, time_horizon_minutes + 1, 5))  # Every 5 minutes
        
        # Get baseline satisfaction
        baseline_satisfaction = await self._calculate_baseline_satisfaction(user_history)
        
        # Predict satisfaction at each time point
        satisfaction_values = []
        confidence_bands = []
        
        for time_point in time_points:
            predicted_satisfaction, confidence_interval = await self._predict_satisfaction_at_time(
                user_history, current_context, baseline_satisfaction, time_point
            )
            
            satisfaction_values.append(predicted_satisfaction)
            confidence_bands.append(confidence_interval)
        
        # Identify influencing factors
        influencing_factors = await self._identify_influencing_factors(
            user_history, current_context
        )
        
        trajectory = SatisfactionTrajectory(
            time_points=time_points,
            satisfaction_values=satisfaction_values,
            confidence_bands=confidence_bands,
            influencing_factors=influencing_factors
        )
        
        # Cache the trajectory
        cache_key = f"{user_history.user_id}_{datetime.now().timestamp()}"
        self.trajectory_cache[cache_key] = trajectory
        
        return trajectory
    
    async def _calculate_baseline_satisfaction(self, user_history: UserHistory) -> float:
        """Calculate baseline satisfaction from user history."""
        
        recent_interactions = user_history.get_recent_interactions(hours=24)
        
        if not recent_interactions:
            # Use overall history
            all_satisfactions = [
                interaction.get('satisfaction', 0.5)
                for interaction in user_history.interactions
            ]
        else:
            all_satisfactions = [
                interaction.get('satisfaction', 0.5)
                for interaction in recent_interactions
            ]
        
        if not all_satisfactions:
            return 0.5  # Neutral baseline
        
        # Weighted average with more recent interactions having higher weight
        if len(all_satisfactions) > 1:
            weights = np.linspace(0.5, 1.0, len(all_satisfactions))
            baseline = np.average(all_satisfactions, weights=weights)
        else:
            baseline = all_satisfactions[0]
        
        return max(0.0, min(1.0, baseline))
    
    async def _predict_satisfaction_at_time(
        self, 
        user_history: UserHistory,
        context: Dict[str, Any],
        baseline: float,
        time_minutes: int
    ) -> Tuple[float, Tuple[float, float]]:
        """Predict satisfaction at specific time point."""
        
        # Start with baseline
        predicted_satisfaction = baseline
        
        # Apply time-based decay/improvement
        time_factor = await self._calculate_time_factor(user_history, time_minutes)
        predicted_satisfaction *= time_factor
        
        # Apply context factors
        context_factor = await self._calculate_context_factor(context, time_minutes)
        predicted_satisfaction *= context_factor
        
        # Apply fatigue factor (satisfaction typically decreases over time)
        fatigue_factor = max(0.7, 1.0 - (time_minutes / 120.0) * 0.3)  # 30% decrease over 2 hours
        predicted_satisfaction *= fatigue_factor
        
        # Apply engagement boost (if user is highly engaged)
        engagement = context.get('engagement_score', 0.5)
        if engagement > 0.7:
            engagement_boost = 1.0 + (engagement - 0.7) * 0.2
            predicted_satisfaction *= engagement_boost
        
        # Ensure valid range
        predicted_satisfaction = max(0.0, min(1.0, predicted_satisfaction))
        
        # Calculate confidence interval
        uncertainty = 0.1 + (time_minutes / 60.0) * 0.1  # Increasing uncertainty over time
        lower_bound = max(0.0, predicted_satisfaction - uncertainty)
        upper_bound = min(1.0, predicted_satisfaction + uncertainty)
        
        return predicted_satisfaction, (lower_bound, upper_bound)
    
    async def _calculate_time_factor(self, user_history: UserHistory, time_minutes: int) -> float:
        """Calculate how satisfaction changes over time for this user."""
        
        # Analyze historical session patterns
        sessions = user_history.sessions
        
        if not sessions:
            return 1.0  # No change if no session data
        
        # Look for patterns in satisfaction over session duration
        satisfaction_changes = []
        
        for session in sessions:
            duration = session.get('duration', 60)
            start_satisfaction = session.get('start_satisfaction', 0.5)
            end_satisfaction = session.get('end_satisfaction', 0.5)
            
            if duration > 0:
                change_rate = (end_satisfaction - start_satisfaction) / duration
                satisfaction_changes.append(change_rate)
        
        if satisfaction_changes:
            avg_change_rate = np.mean(satisfaction_changes)
            # Apply the change rate to the time point
            time_factor = 1.0 + (avg_change_rate * time_minutes)
            return max(0.5, min(1.5, time_factor))  # Bound the factor
        
        return 1.0
    
    async def _calculate_context_factor(self, context: Dict[str, Any], time_minutes: int) -> float:
        """Calculate context impact on satisfaction."""
        
        factor = 1.0
        
        # Task complexity impact
        complexity = context.get('task_complexity', 0.5)
        if complexity > 0.7:
            # High complexity may decrease satisfaction over time
            factor *= (1.0 - (time_minutes / 120.0) * 0.2)
        elif complexity < 0.3:
            # Low complexity may maintain satisfaction
            factor *= (1.0 + 0.1)
        
        # User expertise impact
        expertise = context.get('user_expertise', 0.5)
        if expertise > 0.7:
            # High expertise users maintain satisfaction better
            factor *= (1.0 + 0.1)
        elif expertise < 0.3:
            # Low expertise users may get frustrated
            factor *= (1.0 - (time_minutes / 60.0) * 0.1)
        
        # Support availability impact
        support_available = context.get('support_available', True)
        if not support_available:
            factor *= 0.9  # Slight decrease if no support
        
        return max(0.5, min(1.5, factor))
    
    async def _identify_influencing_factors(
        self, 
        user_history: UserHistory,
        context: Dict[str, Any]
    ) -> List[str]:
        """Identify factors that influence satisfaction trajectory."""
        
        factors = []
        
        # Historical factors
        recent_interactions = user_history.get_recent_interactions(hours=6)
        if recent_interactions:
            avg_recent_satisfaction = np.mean([
                interaction.get('satisfaction', 0.5)
                for interaction in recent_interactions
            ])
            
            if avg_recent_satisfaction > 0.7:
                factors.append("recent_positive_interactions")
            elif avg_recent_satisfaction < 0.4:
                factors.append("recent_negative_interactions")
        
        # Context factors
        if context.get('task_complexity', 0.5) > 0.7:
            factors.append("high_task_complexity")
        
        if context.get('user_expertise', 0.5) < 0.3:
            factors.append("low_user_expertise")
        
        if context.get('time_pressure', False):
            factors.append("time_pressure")
        
        if context.get('support_available', True):
            factors.append("support_available")
        else:
            factors.append("no_support_available")
        
        # User state factors
        if context.get('user_fatigue', 0.5) > 0.7:
            factors.append("user_fatigue")
        
        if context.get('engagement_score', 0.5) > 0.7:
            factors.append("high_engagement")
        
        return factors


class UserBehaviorPredictor:
    """Main class for predicting user behavior patterns and actions."""
    
    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.action_predictor = ActionPredictor()
        self.satisfaction_predictor = SatisfactionPredictor()
        self.user_patterns_cache: Dict[str, List[BehaviorPattern]] = {}
    
    async def predict_next_action(
        self, 
        current_context: Dict[str, Any],
        user_history: UserHistory
    ) -> PredictedAction:
        """Predict the user's next likely action."""
        
        # Get or detect user patterns
        user_patterns = await self._get_user_patterns(user_history)
        
        # Predict next action
        predicted_action = await self.action_predictor.predict_next_action(
            current_context, user_patterns, user_history
        )
        
        return predicted_action
    
    async def predict_satisfaction_trajectory(
        self, 
        user_history: UserHistory,
        current_context: Dict[str, Any],
        time_horizon_minutes: int = 60
    ) -> SatisfactionTrajectory:
        """Predict user satisfaction trajectory."""
        
        return await self.satisfaction_predictor.predict_satisfaction_trajectory(
            user_history, current_context, time_horizon_minutes
        )
    
    async def identify_behavior_patterns(
        self, 
        user_history: UserHistory,
        force_refresh: bool = False
    ) -> List[BehaviorPattern]:
        """Identify behavior patterns for a user."""
        
        user_id = user_history.user_id
        
        # Check cache first
        if not force_refresh and user_id in self.user_patterns_cache:
            cached_patterns = self.user_patterns_cache[user_id]
            # Check if cache is recent (less than 1 hour old)
            if cached_patterns and hasattr(cached_patterns[0], 'last_observed'):
                time_since_update = datetime.now() - cached_patterns[0].last_observed
                if time_since_update < timedelta(hours=1):
                    return cached_patterns
        
        # Detect new patterns
        patterns = await self.pattern_detector.detect_patterns(user_history)
        
        # Cache the patterns
        self.user_patterns_cache[user_id] = patterns
        
        return patterns
    
    async def _get_user_patterns(self, user_history: UserHistory) -> List[BehaviorPattern]:
        """Get user patterns, using cache if available."""
        return await self.identify_behavior_patterns(user_history)
    
    async def update_pattern_from_observation(
        self, 
        user_id: str,
        context: Dict[str, Any],
        outcome_success: bool
    ):
        """Update behavior patterns based on new observations."""
        
        if user_id in self.user_patterns_cache:
            patterns = self.user_patterns_cache[user_id]
            
            for pattern in patterns:
                if pattern.matches_context(context):
                    pattern.update_from_observation(context, outcome_success)
    
    def get_prediction_confidence(
        self, 
        predicted_action: PredictedAction,
        user_patterns: List[BehaviorPattern]
    ) -> PredictionConfidence:
        """Determine confidence level for a prediction."""
        
        # Base confidence from the prediction
        base_confidence = predicted_action.confidence
        
        # Adjust based on number of supporting patterns
        pattern_support = len([p for p in user_patterns if p.confidence > 0.6])
        pattern_factor = min(1.0, pattern_support / 3.0)
        
        # Adjust based on prediction probability
        probability_factor = predicted_action.probability
        
        # Combined confidence
        combined_confidence = (base_confidence + pattern_factor + probability_factor) / 3.0
        
        if combined_confidence > 0.8:
            return PredictionConfidence.VERY_HIGH
        elif combined_confidence > 0.6:
            return PredictionConfidence.HIGH
        elif combined_confidence > 0.4:
            return PredictionConfidence.MEDIUM
        else:
            return PredictionConfidence.LOW
    
    def get_behavior_insights(self, user_history: UserHistory) -> Dict[str, Any]:
        """Get insights about user behavior patterns."""
        
        insights = {}
        
        # Session statistics
        session_stats = user_history.get_session_statistics()
        insights['session_statistics'] = session_stats
        
        # Pattern summary
        if user_history.user_id in self.user_patterns_cache:
            patterns = self.user_patterns_cache[user_history.user_id]
            
            pattern_summary = {
                'total_patterns': len(patterns),
                'pattern_types': {},
                'high_confidence_patterns': 0,
                'average_confidence': 0.0
            }
            
            if patterns:
                for pattern in patterns:
                    pattern_type = pattern.pattern_type.value
                    pattern_summary['pattern_types'][pattern_type] = \
                        pattern_summary['pattern_types'].get(pattern_type, 0) + 1
                    
                    if pattern.confidence > 0.7:
                        pattern_summary['high_confidence_patterns'] += 1
                
                pattern_summary['average_confidence'] = np.mean([p.confidence for p in patterns])
            
            insights['pattern_summary'] = pattern_summary
        
        # Behavioral trends
        if user_history.interactions:
            recent_satisfaction = np.mean([
                interaction.get('satisfaction', 0.5)
                for interaction in user_history.get_recent_interactions(hours=24)
            ]) if user_history.get_recent_interactions(hours=24) else 0.5
            
            overall_satisfaction = np.mean([
                interaction.get('satisfaction', 0.5)
                for interaction in user_history.interactions
            ])
            
            insights['behavioral_trends'] = {
                'recent_satisfaction': recent_satisfaction,
                'overall_satisfaction': overall_satisfaction,
                'satisfaction_trend': 'improving' if recent_satisfaction > overall_satisfaction else 'declining',
                'total_interactions': len(user_history.interactions)
            }
        
        return insights