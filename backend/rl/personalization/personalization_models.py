"""
Data models for advanced personalization system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from datetime import datetime


class AdaptationStrategyType(Enum):
    """Types of adaptation strategies."""
    GRADUAL_ADJUSTMENT = "gradual_adjustment"
    RAPID_ADAPTATION = "rapid_adaptation"
    CONSERVATIVE_CHANGE = "conservative_change"
    EXPLORATORY_ADAPTATION = "exploratory_adaptation"
    ROLLBACK_STRATEGY = "rollback_strategy"


class BehaviorPatternType(Enum):
    """Types of behavior patterns."""
    SEQUENTIAL = "sequential"
    CYCLICAL = "cyclical"
    CONTEXTUAL = "contextual"
    PREFERENCE_BASED = "preference_based"
    TEMPORAL = "temporal"
    INTERACTION_BASED = "interaction_based"


class RiskLevel(Enum):
    """Risk levels for adaptation strategies."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TemporalPreference:
    """Preference that changes over time."""
    preference_key: str
    time_period: str  # "morning", "afternoon", "evening", "weekday", "weekend"
    preference_value: float
    confidence: float
    last_updated: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate temporal preference."""
        if not 0 <= self.preference_value <= 1:
            raise ValueError("Preference value must be between 0 and 1")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")


@dataclass
class ContextCondition:
    """Condition that defines when a pattern applies."""
    condition_type: str  # "time", "location", "task", "mood", "performance"
    condition_value: Any
    operator: str = "equals"  # "equals", "greater_than", "less_than", "contains"
    
    def matches(self, context: Dict[str, Any]) -> bool:
        """Check if context matches this condition."""
        if self.condition_type not in context:
            return False
        
        context_value = context[self.condition_type]
        
        if self.operator == "equals":
            return context_value == self.condition_value
        elif self.operator == "greater_than":
            return context_value > self.condition_value
        elif self.operator == "less_than":
            return context_value < self.condition_value
        elif self.operator == "contains":
            return self.condition_value in str(context_value)
        else:
            return False


@dataclass
class SuccessIndicator:
    """Indicator of successful adaptation."""
    metric_name: str
    target_value: float
    current_value: float
    improvement_threshold: float = 0.05
    
    def is_successful(self) -> bool:
        """Check if adaptation was successful."""
        return (self.current_value - self.target_value) >= self.improvement_threshold


@dataclass
class RiskAssessment:
    """Assessment of risks associated with an adaptation strategy."""
    risk_level: RiskLevel
    risk_factors: List[str]
    mitigation_strategies: List[str]
    rollback_probability: float
    impact_assessment: Dict[str, float]
    
    def __post_init__(self):
        """Validate risk assessment."""
        if not 0 <= self.rollback_probability <= 1:
            raise ValueError("Rollback probability must be between 0 and 1")


@dataclass
class RollbackCondition:
    """Condition that triggers a rollback of adaptation."""
    condition_name: str
    metric_threshold: float
    time_window: int  # seconds
    consecutive_failures: int = 3
    
    def should_rollback(self, recent_metrics: List[Tuple[datetime, float]]) -> bool:
        """Check if rollback should be triggered."""
        if len(recent_metrics) < self.consecutive_failures:
            return False
        
        # Check recent failures
        recent_failures = 0
        for timestamp, value in recent_metrics[-self.consecutive_failures:]:
            if value < self.metric_threshold:
                recent_failures += 1
        
        return recent_failures >= self.consecutive_failures


@dataclass
class DeepPreferenceModel:
    """Deep learning model for user preferences."""
    preference_embeddings: np.ndarray
    preference_weights: Dict[str, float]
    temporal_preferences: List[TemporalPreference]
    contextual_modifiers: Dict[str, float]
    confidence_intervals: Dict[str, Tuple[float, float]]
    model_version: str = "1.0"
    last_updated: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate deep preference model."""
        if self.preference_embeddings.size == 0:
            raise ValueError("Preference embeddings cannot be empty")
        
        # Validate preference weights
        for key, weight in self.preference_weights.items():
            if not 0 <= weight <= 1:
                raise ValueError(f"Preference weight for {key} must be between 0 and 1")
        
        # Validate confidence intervals
        for key, (lower, upper) in self.confidence_intervals.items():
            if lower > upper:
                raise ValueError(f"Invalid confidence interval for {key}: lower > upper")
    
    def get_preference_for_context(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Get preferences adjusted for specific context."""
        adjusted_preferences = self.preference_weights.copy()
        
        # Apply contextual modifiers
        for modifier_key, modifier_value in self.contextual_modifiers.items():
            if modifier_key in context:
                context_strength = context.get(modifier_key, 0.0)
                for pref_key in adjusted_preferences:
                    adjusted_preferences[pref_key] *= (1 + modifier_value * context_strength)
        
        # Apply temporal preferences
        current_time = datetime.now()
        time_period = self._get_time_period(current_time)
        
        for temp_pref in self.temporal_preferences:
            if temp_pref.time_period == time_period and temp_pref.preference_key in adjusted_preferences:
                # Blend temporal preference with base preference
                base_pref = adjusted_preferences[temp_pref.preference_key]
                temporal_weight = temp_pref.confidence
                adjusted_preferences[temp_pref.preference_key] = (
                    base_pref * (1 - temporal_weight) + 
                    temp_pref.preference_value * temporal_weight
                )
        
        # Normalize to ensure values stay in [0, 1]
        for key in adjusted_preferences:
            adjusted_preferences[key] = max(0.0, min(1.0, adjusted_preferences[key]))
        
        return adjusted_preferences
    
    def _get_time_period(self, timestamp: datetime) -> str:
        """Get time period for temporal preferences."""
        hour = timestamp.hour
        weekday = timestamp.weekday()
        
        if weekday >= 5:  # Weekend
            return "weekend"
        elif hour < 12:
            return "morning"
        elif hour < 18:
            return "afternoon"
        else:
            return "evening"
    
    def update_preference(self, preference_key: str, new_value: float, confidence: float = 1.0):
        """Update a preference value."""
        if preference_key in self.preference_weights:
            # Exponential moving average update
            current_value = self.preference_weights[preference_key]
            self.preference_weights[preference_key] = (
                current_value * (1 - confidence) + new_value * confidence
            )
        else:
            self.preference_weights[preference_key] = new_value
        
        self.last_updated = datetime.now()


@dataclass
class AdaptationStrategy:
    """Strategy for adapting user experience."""
    strategy_id: str
    strategy_type: AdaptationStrategyType
    parameters: Dict[str, Any]
    expected_improvement: float
    risk_assessment: RiskAssessment
    rollback_conditions: List[RollbackCondition]
    implementation_steps: List[str]
    success_metrics: List[str]
    
    def __post_init__(self):
        """Validate adaptation strategy."""
        if not 0 <= self.expected_improvement <= 1:
            raise ValueError("Expected improvement must be between 0 and 1")
        if not self.strategy_id:
            raise ValueError("Strategy ID cannot be empty")
    
    def can_implement(self, current_context: Dict[str, Any]) -> bool:
        """Check if strategy can be implemented in current context."""
        # Check risk level
        if self.risk_assessment.risk_level == RiskLevel.CRITICAL:
            return False
        
        # Check if context supports implementation
        required_params = self.parameters.get("required_context", [])
        for param in required_params:
            if param not in current_context:
                return False
        
        return True
    
    def estimate_impact(self, user_profile: Dict[str, Any]) -> Dict[str, float]:
        """Estimate impact of strategy on user experience."""
        impact = {}
        
        # Base impact from expected improvement
        impact["satisfaction"] = self.expected_improvement
        impact["engagement"] = self.expected_improvement * 0.8
        impact["efficiency"] = self.expected_improvement * 0.6
        
        # Adjust based on strategy type
        if self.strategy_type == AdaptationStrategyType.RAPID_ADAPTATION:
            impact["satisfaction"] *= 1.2  # Higher immediate impact
            impact["risk"] = 0.3  # But higher risk
        elif self.strategy_type == AdaptationStrategyType.CONSERVATIVE_CHANGE:
            impact["satisfaction"] *= 0.8  # Lower immediate impact
            impact["risk"] = 0.1  # But lower risk
        elif self.strategy_type == AdaptationStrategyType.EXPLORATORY_ADAPTATION:
            impact["learning"] = 0.7  # High learning potential
            impact["risk"] = 0.4  # Moderate risk
        
        # Adjust based on user profile
        user_adaptability = user_profile.get("adaptability", 0.5)
        for key in impact:
            if key != "risk":
                impact[key] *= (0.5 + user_adaptability * 0.5)
        
        return impact


@dataclass
class BehaviorPattern:
    """Pattern in user behavior."""
    pattern_id: str
    pattern_type: BehaviorPatternType
    frequency: float  # How often this pattern occurs (0-1)
    context_conditions: List[ContextCondition]
    predictive_features: List[str]
    success_indicators: List[SuccessIndicator]
    confidence: float
    last_observed: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate behavior pattern."""
        if not 0 <= self.frequency <= 1:
            raise ValueError("Frequency must be between 0 and 1")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        if not self.pattern_id:
            raise ValueError("Pattern ID cannot be empty")
    
    def matches_context(self, context: Dict[str, Any]) -> bool:
        """Check if pattern matches current context."""
        if not self.context_conditions:
            return True  # No conditions means always matches
        
        # All conditions must match
        for condition in self.context_conditions:
            if not condition.matches(context):
                return False
        
        return True
    
    def get_prediction_strength(self, context: Dict[str, Any]) -> float:
        """Get strength of prediction for this pattern in given context."""
        if not self.matches_context(context):
            return 0.0
        
        # Base strength from frequency and confidence
        base_strength = self.frequency * self.confidence
        
        # Adjust based on how well predictive features are present
        feature_strength = 0.0
        available_features = 0
        
        for feature in self.predictive_features:
            if feature in context:
                available_features += 1
                feature_value = context[feature]
                if isinstance(feature_value, (int, float)):
                    feature_strength += min(1.0, abs(feature_value))
                else:
                    feature_strength += 1.0  # Binary feature present
        
        if available_features > 0:
            feature_strength /= available_features
        
        return base_strength * (0.5 + feature_strength * 0.5)
    
    def update_from_observation(self, context: Dict[str, Any], outcome_success: bool):
        """Update pattern based on new observation."""
        if self.matches_context(context):
            # Update frequency (exponential moving average)
            alpha = 0.1  # Learning rate
            if outcome_success:
                self.frequency = self.frequency * (1 - alpha) + 1.0 * alpha
            else:
                self.frequency = self.frequency * (1 - alpha) + 0.0 * alpha
            
            # Update confidence based on prediction accuracy
            if outcome_success:
                self.confidence = min(1.0, self.confidence + 0.05)
            else:
                self.confidence = max(0.0, self.confidence - 0.02)
            
            self.last_observed = datetime.now()


@dataclass
class PredictedAction:
    """Predicted user action."""
    action_type: str
    action_parameters: Dict[str, Any]
    probability: float
    confidence: float
    reasoning: str
    alternative_actions: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate predicted action."""
        if not 0 <= self.probability <= 1:
            raise ValueError("Probability must be between 0 and 1")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")


@dataclass
class SatisfactionTrajectory:
    """Predicted trajectory of user satisfaction."""
    time_points: List[int]  # Time points in minutes from now
    satisfaction_values: List[float]  # Predicted satisfaction at each time point
    confidence_bands: List[Tuple[float, float]]  # Confidence intervals
    influencing_factors: List[str]
    
    def __post_init__(self):
        """Validate satisfaction trajectory."""
        if len(self.time_points) != len(self.satisfaction_values):
            raise ValueError("Time points and satisfaction values must have same length")
        if len(self.satisfaction_values) != len(self.confidence_bands):
            raise ValueError("Satisfaction values and confidence bands must have same length")
        
        for satisfaction in self.satisfaction_values:
            if not 0 <= satisfaction <= 1:
                raise ValueError("Satisfaction values must be between 0 and 1")
    
    def get_satisfaction_at_time(self, target_time: int) -> Tuple[float, Tuple[float, float]]:
        """Get predicted satisfaction at specific time point."""
        if not self.time_points:
            return 0.5, (0.0, 1.0)
        
        # Find closest time points
        if target_time <= self.time_points[0]:
            return self.satisfaction_values[0], self.confidence_bands[0]
        elif target_time >= self.time_points[-1]:
            return self.satisfaction_values[-1], self.confidence_bands[-1]
        
        # Interpolate between closest points
        for i in range(len(self.time_points) - 1):
            if self.time_points[i] <= target_time <= self.time_points[i + 1]:
                # Linear interpolation
                t1, t2 = self.time_points[i], self.time_points[i + 1]
                s1, s2 = self.satisfaction_values[i], self.satisfaction_values[i + 1]
                c1, c2 = self.confidence_bands[i], self.confidence_bands[i + 1]
                
                weight = (target_time - t1) / (t2 - t1)
                satisfaction = s1 * (1 - weight) + s2 * weight
                confidence_lower = c1[0] * (1 - weight) + c2[0] * weight
                confidence_upper = c1[1] * (1 - weight) + c2[1] * weight
                
                return satisfaction, (confidence_lower, confidence_upper)
        
        return 0.5, (0.0, 1.0)  # Fallback
    
    def get_peak_satisfaction_time(self) -> Tuple[int, float]:
        """Get time point with highest predicted satisfaction."""
        if not self.satisfaction_values:
            return 0, 0.5
        
        max_idx = np.argmax(self.satisfaction_values)
        return self.time_points[max_idx], self.satisfaction_values[max_idx]
    
    def get_trend(self) -> str:
        """Get overall trend of satisfaction trajectory."""
        if len(self.satisfaction_values) < 2:
            return "stable"
        
        start_satisfaction = np.mean(self.satisfaction_values[:2])
        end_satisfaction = np.mean(self.satisfaction_values[-2:])
        
        diff = end_satisfaction - start_satisfaction
        
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        else:
            return "stable"