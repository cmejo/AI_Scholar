"""Enhanced user models for advanced personalization features."""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union, Set
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

from ..models.user_models import UserProfile
from ..multimodal.models import VisualElement, VisualElementType
from ..research_assistant.workflow_optimizer import WorkflowPattern, Task, TaskType
from ..research_assistant.research_workflow_learner import BestPractice, WorkflowInsight

logger = logging.getLogger(__name__)


class PreferenceType(Enum):
    """Types of user preferences."""
    CONTENT = "content"
    VISUAL = "visual"
    INTERACTION = "interaction"
    WORKFLOW = "workflow"
    TEMPORAL = "temporal"
    COGNITIVE = "cognitive"


class LearningStyle(Enum):
    """User learning styles."""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"
    MULTIMODAL = "multimodal"


class ResearchBehaviorType(Enum):
    """Types of research behavior patterns."""
    SYSTEMATIC = "systematic"
    EXPLORATORY = "exploratory"
    FOCUSED = "focused"
    ITERATIVE = "iterative"
    COLLABORATIVE = "collaborative"


@dataclass
class VisualPreference:
    """User preferences for visual content."""
    preferred_chart_types: List[str] = field(default_factory=list)
    color_preferences: Dict[str, float] = field(default_factory=dict)
    complexity_tolerance: float = 0.5
    interaction_style: str = "moderate"
    attention_patterns: Dict[str, float] = field(default_factory=dict)
    visual_processing_speed: float = 1.0
    preferred_layout_styles: List[str] = field(default_factory=list)
    accessibility_needs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowPreference:
    """User preferences for research workflows."""
    preferred_task_sequence: List[TaskType] = field(default_factory=list)
    optimal_session_duration: float = 120.0  # minutes
    break_frequency: float = 30.0  # minutes
    multitasking_tolerance: float = 0.5
    interruption_sensitivity: float = 0.7
    planning_vs_execution_ratio: float = 0.2
    collaboration_preference: float = 0.3
    tool_switching_tolerance: float = 0.6


@dataclass
class CognitiveProfile:
    """User cognitive characteristics and preferences."""
    working_memory_capacity: float = 0.7
    attention_span: float = 0.8
    processing_speed: float = 0.75
    cognitive_load_tolerance: float = 0.6
    learning_style: LearningStyle = LearningStyle.MULTIMODAL
    information_processing_style: str = "sequential"  # or "holistic"
    decision_making_style: str = "analytical"  # or "intuitive"
    cognitive_flexibility: float = 0.7


@dataclass
class MultiModalPreferences:
    """User preferences for multi-modal content."""
    text_to_visual_ratio: float = 0.6
    preferred_visual_complexity: float = 0.5
    cross_modal_coherence_importance: float = 0.8
    visual_explanation_preference: float = 0.7
    interactive_element_preference: float = 0.6
    animation_tolerance: float = 0.5
    multimedia_engagement_level: float = 0.7


@dataclass
class ResearchWorkflowPattern:
    """User's research workflow patterns."""
    pattern_id: str
    pattern_name: str
    task_sequence: List[TaskType]
    typical_duration: float
    success_rate: float
    efficiency_score: float
    user_satisfaction: float
    context_conditions: Dict[str, Any] = field(default_factory=dict)
    frequency_of_use: int = 0
    last_used: Optional[datetime] = None
    adaptations_made: List[str] = field(default_factory=list)


@dataclass
class PersonalizationInsight:
    """Insights about user personalization."""
    insight_id: str
    insight_type: str
    description: str
    confidence: float
    impact_potential: float
    actionable_recommendations: List[str]
    supporting_evidence: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    applied: bool = False


@dataclass
class AdaptationHistory:
    """History of personalization adaptations."""
    adaptation_id: str
    adaptation_type: str
    description: str
    applied_at: datetime
    success_metrics: Dict[str, float]
    user_feedback: Optional[str] = None
    effectiveness_score: float = 0.0
    reverted: bool = False
    revert_reason: Optional[str] = None


class EnhancedUserProfile(UserProfile):
    """Enhanced user profile with advanced personalization features."""
    
    def __init__(self, user_id: str, **kwargs):
        super().__init__(user_id, **kwargs)
        
        # Advanced preference components
        self.visual_preferences: VisualPreference = VisualPreference()
        self.workflow_preferences: WorkflowPreference = WorkflowPreference()
        self.cognitive_profile: CognitiveProfile = CognitiveProfile()
        self.multimodal_preferences: MultiModalPreferences = MultiModalPreferences()
        
        # Research behavior and patterns
        self.research_behavior_type: ResearchBehaviorType = ResearchBehaviorType.SYSTEMATIC
        self.workflow_patterns: List[ResearchWorkflowPattern] = []
        self.best_practices: List[BestPractice] = []
        
        # Personalization insights and history
        self.personalization_insights: List[PersonalizationInsight] = []
        self.adaptation_history: List[AdaptationHistory] = []
        
        # Advanced metrics
        self.engagement_metrics: Dict[str, float] = {}
        self.learning_effectiveness: Dict[str, float] = {}
        self.satisfaction_trends: List[Tuple[datetime, float]] = []
        
        # Temporal patterns
        self.activity_patterns: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.seasonal_preferences: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Cross-session learning
        self.knowledge_state: Dict[str, float] = {}
        self.skill_progression: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        
        # Metadata
        self.last_personalization_update: datetime = datetime.now()
        self.personalization_version: str = "1.0"


class EnhancedUserModelManager:
    """Manager for enhanced user models with advanced personalization."""
    
    def __init__(self):
        self.user_profiles: Dict[str, EnhancedUserProfile] = {}
        self.personalization_algorithms: Dict[str, Any] = {}
        self.adaptation_strategies: Dict[str, Any] = {}
        self.insight_generators: List[Any] = []
    
    async def get_or_create_enhanced_profile(self, user_id: str) -> EnhancedUserProfile:
        """Get or create an enhanced user profile."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = EnhancedUserProfile(user_id)
            logger.info(f"Created enhanced profile for user {user_id}")
        
        return self.user_profiles[user_id]
    
    async def update_visual_preferences(self, user_id: str, 
                                      visual_interactions: List[Dict[str, Any]]) -> VisualPreference:
        """Update user's visual preferences based on interactions."""
        try:
            profile = await self.get_or_create_enhanced_profile(user_id)
            
            # Analyze visual interactions
            chart_type_preferences = await self._analyze_chart_type_preferences(visual_interactions)
            color_preferences = await self._analyze_color_preferences(visual_interactions)
            complexity_tolerance = await self._analyze_complexity_tolerance(visual_interactions)
            attention_patterns = await self._analyze_attention_patterns(visual_interactions)
            
            # Update preferences with exponential moving average
            alpha = 0.1  # Learning rate
            
            # Update chart type preferences
            for chart_type, preference in chart_type_preferences.items():
                if chart_type not in profile.visual_preferences.preferred_chart_types:
                    if preference > 0.6:  # Threshold for adding to preferences
                        profile.visual_preferences.preferred_chart_types.append(chart_type)
            
            # Update color preferences
            for color, preference in color_preferences.items():
                current = profile.visual_preferences.color_preferences.get(color, 0.5)
                profile.visual_preferences.color_preferences[color] = (
                    alpha * preference + (1 - alpha) * current
                )
            
            # Update complexity tolerance
            current_complexity = profile.visual_preferences.complexity_tolerance
            profile.visual_preferences.complexity_tolerance = (
                alpha * complexity_tolerance + (1 - alpha) * current_complexity
            )
            
            # Update attention patterns
            for pattern, strength in attention_patterns.items():
                current = profile.visual_preferences.attention_patterns.get(pattern, 0.5)
                profile.visual_preferences.attention_patterns[pattern] = (
                    alpha * strength + (1 - alpha) * current
                )
            
            profile.last_personalization_update = datetime.now()
            
            logger.info(f"Updated visual preferences for user {user_id}")
            return profile.visual_preferences
            
        except Exception as e:
            logger.error(f"Error updating visual preferences: {str(e)}")
            return VisualPreference()
    
    async def update_workflow_preferences(self, user_id: str, 
                                        workflow_data: List[Dict[str, Any]]) -> WorkflowPreference:
        """Update user's workflow preferences based on workflow data."""
        try:
            profile = await self.get_or_create_enhanced_profile(user_id)
            
            # Analyze workflow patterns
            optimal_duration = await self._analyze_optimal_session_duration(workflow_data)
            task_sequence_preferences = await self._analyze_task_sequence_preferences(workflow_data)
            multitasking_analysis = await self._analyze_multitasking_patterns(workflow_data)
            
            # Update preferences
            alpha = 0.1
            
            # Update session duration
            current_duration = profile.workflow_preferences.optimal_session_duration
            profile.workflow_preferences.optimal_session_duration = (
                alpha * optimal_duration + (1 - alpha) * current_duration
            )
            
            # Update task sequence preferences
            if task_sequence_preferences:
                profile.workflow_preferences.preferred_task_sequence = task_sequence_preferences
            
            # Update multitasking tolerance
            current_multitasking = profile.workflow_preferences.multitasking_tolerance
            profile.workflow_preferences.multitasking_tolerance = (
                alpha * multitasking_analysis + (1 - alpha) * current_multitasking
            )
            
            profile.last_personalization_update = datetime.now()
            
            logger.info(f"Updated workflow preferences for user {user_id}")
            return profile.workflow_preferences
            
        except Exception as e:
            logger.error(f"Error updating workflow preferences: {str(e)}")
            return WorkflowPreference()
    
    async def update_cognitive_profile(self, user_id: str, 
                                     performance_data: Dict[str, Any]) -> CognitiveProfile:
        """Update user's cognitive profile based on performance data."""
        try:
            profile = await self.get_or_create_enhanced_profile(user_id)
            
            # Analyze cognitive characteristics
            working_memory = await self._assess_working_memory(performance_data)
            attention_span = await self._assess_attention_span(performance_data)
            processing_speed = await self._assess_processing_speed(performance_data)
            cognitive_load = await self._assess_cognitive_load_tolerance(performance_data)
            
            # Update cognitive profile
            alpha = 0.05  # Slower learning rate for cognitive characteristics
            
            current_wm = profile.cognitive_profile.working_memory_capacity
            profile.cognitive_profile.working_memory_capacity = (
                alpha * working_memory + (1 - alpha) * current_wm
            )
            
            current_attention = profile.cognitive_profile.attention_span
            profile.cognitive_profile.attention_span = (
                alpha * attention_span + (1 - alpha) * current_attention
            )
            
            current_speed = profile.cognitive_profile.processing_speed
            profile.cognitive_profile.processing_speed = (
                alpha * processing_speed + (1 - alpha) * current_speed
            )
            
            current_load = profile.cognitive_profile.cognitive_load_tolerance
            profile.cognitive_profile.cognitive_load_tolerance = (
                alpha * cognitive_load + (1 - alpha) * current_load
            )
            
            profile.last_personalization_update = datetime.now()
            
            logger.info(f"Updated cognitive profile for user {user_id}")
            return profile.cognitive_profile
            
        except Exception as e:
            logger.error(f"Error updating cognitive profile: {str(e)}")
            return CognitiveProfile()
    
    async def add_workflow_pattern(self, user_id: str, pattern: WorkflowPattern) -> ResearchWorkflowPattern:
        """Add a new workflow pattern to user's profile."""
        try:
            profile = await self.get_or_create_enhanced_profile(user_id)
            
            # Convert WorkflowPattern to ResearchWorkflowPattern
            research_pattern = ResearchWorkflowPattern(
                pattern_id=pattern.pattern_id,
                pattern_name=f"Pattern_{len(profile.workflow_patterns) + 1}",
                task_sequence=[TaskType(task) for task in pattern.task_sequence if task in [t.value for t in TaskType]],
                typical_duration=pattern.performance_metrics.get('average_duration', 120.0),
                success_rate=pattern.success_rate,
                efficiency_score=pattern.average_efficiency,
                user_satisfaction=pattern.average_satisfaction,
                context_conditions=pattern.context_conditions,
                frequency_of_use=pattern.frequency,
                last_used=datetime.now()
            )
            
            # Check if similar pattern already exists
            existing_pattern = await self._find_similar_pattern(profile.workflow_patterns, research_pattern)
            
            if existing_pattern:
                # Update existing pattern
                await self._merge_workflow_patterns(existing_pattern, research_pattern)
                logger.info(f"Updated existing workflow pattern for user {user_id}")
            else:
                # Add new pattern
                profile.workflow_patterns.append(research_pattern)
                logger.info(f"Added new workflow pattern for user {user_id}")
            
            profile.last_personalization_update = datetime.now()
            return research_pattern
            
        except Exception as e:
            logger.error(f"Error adding workflow pattern: {str(e)}")
            return ResearchWorkflowPattern("", "", [], 0.0, 0.0, 0.0, 0.0)
    
    async def add_personalization_insight(self, user_id: str, insight: WorkflowInsight) -> PersonalizationInsight:
        """Add a personalization insight to user's profile."""
        try:
            profile = await self.get_or_create_enhanced_profile(user_id)
            
            # Convert WorkflowInsight to PersonalizationInsight
            personalization_insight = PersonalizationInsight(
                insight_id=insight.insight_id,
                insight_type=insight.insight_type,
                description=insight.description,
                confidence=insight.confidence,
                impact_potential={"high": 0.8, "medium": 0.5, "low": 0.2}[insight.impact_level],
                actionable_recommendations=insight.actionable_recommendations,
                supporting_evidence=insight.supporting_data
            )
            
            profile.personalization_insights.append(personalization_insight)
            
            # Keep only recent insights (last 50)
            if len(profile.personalization_insights) > 50:
                profile.personalization_insights = profile.personalization_insights[-50:]
            
            profile.last_personalization_update = datetime.now()
            
            logger.info(f"Added personalization insight for user {user_id}")
            return personalization_insight
            
        except Exception as e:
            logger.error(f"Error adding personalization insight: {str(e)}")
            return PersonalizationInsight("", "", "", 0.0, 0.0, [], {})
    
    async def record_adaptation(self, user_id: str, adaptation_type: str, 
                              description: str, success_metrics: Dict[str, float]) -> AdaptationHistory:
        """Record a personalization adaptation."""
        try:
            profile = await self.get_or_create_enhanced_profile(user_id)
            
            adaptation = AdaptationHistory(
                adaptation_id=f"adapt_{len(profile.adaptation_history) + 1}",
                adaptation_type=adaptation_type,
                description=description,
                applied_at=datetime.now(),
                success_metrics=success_metrics,
                effectiveness_score=np.mean(list(success_metrics.values())) if success_metrics else 0.0
            )
            
            profile.adaptation_history.append(adaptation)
            
            # Keep only recent adaptations (last 100)
            if len(profile.adaptation_history) > 100:
                profile.adaptation_history = profile.adaptation_history[-100:]
            
            logger.info(f"Recorded adaptation for user {user_id}: {adaptation_type}")
            return adaptation
            
        except Exception as e:
            logger.error(f"Error recording adaptation: {str(e)}")
            return AdaptationHistory("", "", "", datetime.now(), {})
    
    async def get_personalization_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get personalization recommendations for a user."""
        try:
            profile = await self.get_or_create_enhanced_profile(user_id)
            recommendations = []
            
            # Visual preference recommendations
            visual_recs = await self._generate_visual_recommendations(profile)
            recommendations.extend(visual_recs)
            
            # Workflow preference recommendations
            workflow_recs = await self._generate_workflow_recommendations(profile)
            recommendations.extend(workflow_recs)
            
            # Cognitive profile recommendations
            cognitive_recs = await self._generate_cognitive_recommendations(profile)
            recommendations.extend(cognitive_recs)
            
            # Multi-modal recommendations
            multimodal_recs = await self._generate_multimodal_recommendations(profile)
            recommendations.extend(multimodal_recs)
            
            # Sort by impact potential
            recommendations.sort(key=lambda r: r.get('impact_potential', 0.0), reverse=True)
            
            logger.info(f"Generated {len(recommendations)} personalization recommendations for user {user_id}")
            return recommendations[:10]  # Return top 10
            
        except Exception as e:
            logger.error(f"Error generating personalization recommendations: {str(e)}")
            return []
    
    # Helper methods for analysis
    
    async def _analyze_chart_type_preferences(self, interactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze user preferences for different chart types."""
        chart_interactions = defaultdict(list)
        
        for interaction in interactions:
            chart_type = interaction.get('chart_type')
            engagement = interaction.get('engagement_score', 0.5)
            
            if chart_type:
                chart_interactions[chart_type].append(engagement)
        
        preferences = {}
        for chart_type, engagements in chart_interactions.items():
            preferences[chart_type] = np.mean(engagements)
        
        return preferences
    
    async def _analyze_color_preferences(self, interactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze user color preferences from visual interactions."""
        color_interactions = defaultdict(list)
        
        for interaction in interactions:
            colors = interaction.get('dominant_colors', [])
            engagement = interaction.get('engagement_score', 0.5)
            
            for color in colors:
                color_interactions[color].append(engagement)
        
        preferences = {}
        for color, engagements in color_interactions.items():
            preferences[color] = np.mean(engagements)
        
        return preferences
    
    async def _analyze_complexity_tolerance(self, interactions: List[Dict[str, Any]]) -> float:
        """Analyze user tolerance for visual complexity."""
        complexity_engagements = []
        
        for interaction in interactions:
            complexity = interaction.get('visual_complexity', 0.5)
            engagement = interaction.get('engagement_score', 0.5)
            
            # Weight by complexity - higher engagement with complex visuals indicates higher tolerance
            complexity_engagements.append((complexity, engagement))
        
        if not complexity_engagements:
            return 0.5
        
        # Calculate correlation between complexity and engagement
        complexities = [ce[0] for ce in complexity_engagements]
        engagements = [ce[1] for ce in complexity_engagements]
        
        if len(complexities) > 1:
            correlation = np.corrcoef(complexities, engagements)[0, 1]
            # Convert correlation to tolerance (0.5 + correlation/2 to keep in 0-1 range)
            tolerance = max(0.0, min(1.0, 0.5 + correlation / 2))
        else:
            tolerance = 0.5
        
        return tolerance
    
    async def _analyze_attention_patterns(self, interactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze user attention patterns in visual content."""
        attention_data = defaultdict(list)
        
        for interaction in interactions:
            attention_map = interaction.get('attention_distribution', {})
            
            for region, attention_score in attention_map.items():
                attention_data[region].append(attention_score)
        
        patterns = {}
        for region, scores in attention_data.items():
            patterns[region] = np.mean(scores)
        
        return patterns
    
    async def _analyze_optimal_session_duration(self, workflow_data: List[Dict[str, Any]]) -> float:
        """Analyze optimal session duration for user."""
        duration_efficiency = []
        
        for session in workflow_data:
            duration = session.get('duration_minutes', 60.0)
            efficiency = session.get('efficiency_score', 0.5)
            
            duration_efficiency.append((duration, efficiency))
        
        if not duration_efficiency:
            return 120.0  # Default 2 hours
        
        # Find duration with highest average efficiency
        duration_groups = defaultdict(list)
        
        for duration, efficiency in duration_efficiency:
            # Group into 30-minute buckets
            bucket = int(duration // 30) * 30
            duration_groups[bucket].append(efficiency)
        
        best_duration = 120.0
        best_efficiency = 0.0
        
        for duration, efficiencies in duration_groups.items():
            avg_efficiency = np.mean(efficiencies)
            if avg_efficiency > best_efficiency:
                best_efficiency = avg_efficiency
                best_duration = duration
        
        return best_duration
    
    async def _analyze_task_sequence_preferences(self, workflow_data: List[Dict[str, Any]]) -> List[TaskType]:
        """Analyze preferred task sequences."""
        sequence_efficiency = defaultdict(list)
        
        for workflow in workflow_data:
            task_sequence = workflow.get('task_sequence', [])
            efficiency = workflow.get('efficiency_score', 0.5)
            
            if len(task_sequence) >= 2:
                # Analyze pairs of consecutive tasks
                for i in range(len(task_sequence) - 1):
                    pair = (task_sequence[i], task_sequence[i + 1])
                    sequence_efficiency[pair].append(efficiency)
        
        # Find most efficient task transitions
        best_pairs = []
        for pair, efficiencies in sequence_efficiency.items():
            if len(efficiencies) >= 2:  # Minimum sample size
                avg_efficiency = np.mean(efficiencies)
                if avg_efficiency > 0.7:  # High efficiency threshold
                    best_pairs.append((pair, avg_efficiency))
        
        # Sort by efficiency and extract sequence
        best_pairs.sort(key=lambda x: x[1], reverse=True)
        
        if best_pairs:
            # Build sequence from best pairs
            sequence = [best_pairs[0][0][0], best_pairs[0][0][1]]
            
            # Try to extend sequence
            for pair, _ in best_pairs[1:]:
                if pair[0] == sequence[-1]:
                    sequence.append(pair[1])
                elif pair[1] == sequence[0]:
                    sequence.insert(0, pair[0])
            
            # Convert to TaskType enum
            try:
                return [TaskType(task) for task in sequence if task in [t.value for t in TaskType]]
            except ValueError:
                return []
        
        return []
    
    async def _analyze_multitasking_patterns(self, workflow_data: List[Dict[str, Any]]) -> float:
        """Analyze user's multitasking tolerance."""
        multitask_efficiency = []
        
        for workflow in workflow_data:
            concurrent_tasks = workflow.get('concurrent_tasks', 1)
            efficiency = workflow.get('efficiency_score', 0.5)
            
            # Higher concurrent tasks indicate multitasking
            multitask_score = min(1.0, (concurrent_tasks - 1) / 3.0)  # Normalize to 0-1
            multitask_efficiency.append((multitask_score, efficiency))
        
        if not multitask_efficiency:
            return 0.5
        
        # Calculate correlation between multitasking and efficiency
        multitask_scores = [me[0] for me in multitask_efficiency]
        efficiencies = [me[1] for me in multitask_efficiency]
        
        if len(multitask_scores) > 1:
            correlation = np.corrcoef(multitask_scores, efficiencies)[0, 1]
            # Convert to tolerance (positive correlation = higher tolerance)
            tolerance = max(0.0, min(1.0, 0.5 + correlation / 2))
        else:
            tolerance = 0.5
        
        return tolerance
    
    async def _assess_working_memory(self, performance_data: Dict[str, Any]) -> float:
        """Assess working memory capacity from performance data."""
        # Analyze performance on tasks requiring working memory
        complex_task_performance = performance_data.get('complex_task_performance', [])
        
        if not complex_task_performance:
            return 0.7  # Default
        
        # Working memory correlates with performance on complex tasks
        return np.mean(complex_task_performance)
    
    async def _assess_attention_span(self, performance_data: Dict[str, Any]) -> float:
        """Assess attention span from performance data."""
        session_durations = performance_data.get('session_durations', [])
        performance_over_time = performance_data.get('performance_over_time', [])
        
        if not session_durations or not performance_over_time:
            return 0.8  # Default
        
        # Attention span correlates with sustained performance
        # Look for performance decline over session duration
        if len(performance_over_time) > 1:
            # Calculate performance trend (negative slope indicates attention decline)
            x = np.arange(len(performance_over_time))
            slope = np.polyfit(x, performance_over_time, 1)[0]
            
            # Convert slope to attention span (less decline = better attention)
            attention_span = max(0.0, min(1.0, 0.8 + slope))
        else:
            attention_span = 0.8
        
        return attention_span
    
    async def _assess_processing_speed(self, performance_data: Dict[str, Any]) -> float:
        """Assess processing speed from performance data."""
        task_completion_times = performance_data.get('task_completion_times', [])
        expected_times = performance_data.get('expected_completion_times', [])
        
        if not task_completion_times or not expected_times:
            return 0.75  # Default
        
        # Processing speed is inverse of completion time ratio
        time_ratios = []
        for actual, expected in zip(task_completion_times, expected_times):
            if expected > 0:
                ratio = expected / actual  # Higher ratio = faster processing
                time_ratios.append(min(2.0, ratio))  # Cap at 2x expected speed
        
        if time_ratios:
            avg_ratio = np.mean(time_ratios)
            # Convert to 0-1 scale (1.0 ratio = 0.5 processing speed)
            processing_speed = min(1.0, avg_ratio / 2.0)
        else:
            processing_speed = 0.75
        
        return processing_speed
    
    async def _assess_cognitive_load_tolerance(self, performance_data: Dict[str, Any]) -> float:
        """Assess cognitive load tolerance from performance data."""
        high_load_performance = performance_data.get('high_cognitive_load_performance', [])
        low_load_performance = performance_data.get('low_cognitive_load_performance', [])
        
        if not high_load_performance or not low_load_performance:
            return 0.6  # Default
        
        # Tolerance is ratio of high-load to low-load performance
        high_avg = np.mean(high_load_performance)
        low_avg = np.mean(low_load_performance)
        
        if low_avg > 0:
            tolerance = high_avg / low_avg
        else:
            tolerance = 0.6
        
        return max(0.0, min(1.0, tolerance))
    
    async def _find_similar_pattern(self, existing_patterns: List[ResearchWorkflowPattern], 
                                  new_pattern: ResearchWorkflowPattern) -> Optional[ResearchWorkflowPattern]:
        """Find similar existing workflow pattern."""
        for pattern in existing_patterns:
            # Check task sequence similarity
            if len(pattern.task_sequence) == len(new_pattern.task_sequence):
                matches = sum(1 for a, b in zip(pattern.task_sequence, new_pattern.task_sequence) if a == b)
                similarity = matches / len(pattern.task_sequence)
                
                if similarity > 0.8:  # 80% similarity threshold
                    return pattern
        
        return None
    
    async def _merge_workflow_patterns(self, existing: ResearchWorkflowPattern, 
                                     new: ResearchWorkflowPattern):
        """Merge new pattern data into existing pattern."""
        # Update with exponential moving average
        alpha = 0.2
        
        existing.typical_duration = alpha * new.typical_duration + (1 - alpha) * existing.typical_duration
        existing.success_rate = alpha * new.success_rate + (1 - alpha) * existing.success_rate
        existing.efficiency_score = alpha * new.efficiency_score + (1 - alpha) * existing.efficiency_score
        existing.user_satisfaction = alpha * new.user_satisfaction + (1 - alpha) * existing.user_satisfaction
        
        existing.frequency_of_use += 1
        existing.last_used = datetime.now()
    
    async def _generate_visual_recommendations(self, profile: EnhancedUserProfile) -> List[Dict[str, Any]]:
        """Generate visual preference recommendations."""
        recommendations = []
        
        # Chart type recommendations
        if profile.visual_preferences.preferred_chart_types:
            recommendations.append({
                'type': 'visual_chart_types',
                'title': 'Optimize Chart Types',
                'description': f'Focus on {", ".join(profile.visual_preferences.preferred_chart_types[:3])} charts',
                'impact_potential': 0.7,
                'implementation': 'Prioritize preferred chart types in content selection'
            })
        
        # Complexity recommendations
        if profile.visual_preferences.complexity_tolerance < 0.4:
            recommendations.append({
                'type': 'visual_complexity',
                'title': 'Simplify Visual Content',
                'description': 'Use simpler charts and diagrams to improve comprehension',
                'impact_potential': 0.8,
                'implementation': 'Filter out high-complexity visual content'
            })
        elif profile.visual_preferences.complexity_tolerance > 0.7:
            recommendations.append({
                'type': 'visual_complexity',
                'title': 'Increase Visual Complexity',
                'description': 'You can handle more complex visualizations effectively',
                'impact_potential': 0.6,
                'implementation': 'Include more detailed and complex visual content'
            })
        
        return recommendations
    
    async def _generate_workflow_recommendations(self, profile: EnhancedUserProfile) -> List[Dict[str, Any]]:
        """Generate workflow preference recommendations."""
        recommendations = []
        
        # Session duration recommendations
        optimal_duration = profile.workflow_preferences.optimal_session_duration
        if optimal_duration < 60:
            recommendations.append({
                'type': 'workflow_duration',
                'title': 'Shorter Work Sessions',
                'description': f'Optimize for {optimal_duration:.0f}-minute work sessions',
                'impact_potential': 0.7,
                'implementation': 'Break work into shorter, focused sessions'
            })
        elif optimal_duration > 180:
            recommendations.append({
                'type': 'workflow_duration',
                'title': 'Extended Work Sessions',
                'description': f'You work best in {optimal_duration:.0f}-minute sessions',
                'impact_potential': 0.6,
                'implementation': 'Plan for longer, uninterrupted work periods'
            })
        
        # Multitasking recommendations
        if profile.workflow_preferences.multitasking_tolerance < 0.3:
            recommendations.append({
                'type': 'workflow_focus',
                'title': 'Single-Task Focus',
                'description': 'Focus on one task at a time for better performance',
                'impact_potential': 0.8,
                'implementation': 'Minimize task switching and interruptions'
            })
        
        return recommendations
    
    async def _generate_cognitive_recommendations(self, profile: EnhancedUserProfile) -> List[Dict[str, Any]]:
        """Generate cognitive profile recommendations."""
        recommendations = []
        
        # Working memory recommendations
        if profile.cognitive_profile.working_memory_capacity < 0.5:
            recommendations.append({
                'type': 'cognitive_memory',
                'title': 'Reduce Cognitive Load',
                'description': 'Break complex tasks into smaller steps',
                'impact_potential': 0.8,
                'implementation': 'Provide external memory aids and step-by-step guidance'
            })
        
        # Attention span recommendations
        if profile.cognitive_profile.attention_span < 0.6:
            recommendations.append({
                'type': 'cognitive_attention',
                'title': 'Frequent Breaks',
                'description': 'Take regular breaks to maintain focus',
                'impact_potential': 0.7,
                'implementation': 'Schedule breaks every 25-30 minutes'
            })
        
        return recommendations
    
    async def _generate_multimodal_recommendations(self, profile: EnhancedUserProfile) -> List[Dict[str, Any]]:
        """Generate multi-modal preference recommendations."""
        recommendations = []
        
        # Text-visual ratio recommendations
        text_visual_ratio = profile.multimodal_preferences.text_to_visual_ratio
        if text_visual_ratio > 0.8:
            recommendations.append({
                'type': 'multimodal_balance',
                'title': 'Add More Visual Content',
                'description': 'Include more charts and diagrams to enhance understanding',
                'impact_potential': 0.6,
                'implementation': 'Increase visual content ratio to 60-70%'
            })
        elif text_visual_ratio < 0.4:
            recommendations.append({
                'type': 'multimodal_balance',
                'title': 'Balance with Text',
                'description': 'Add more textual explanations alongside visuals',
                'impact_potential': 0.5,
                'implementation': 'Provide detailed text descriptions for visual content'
            })
        
        return recommendations
    
    def get_profile_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of enhanced user profile."""
        if user_id not in self.user_profiles:
            return {"message": "User profile not found"}
        
        profile = self.user_profiles[user_id]
        
        return {
            "user_id": user_id,
            "profile_version": profile.personalization_version,
            "last_update": profile.last_personalization_update.isoformat(),
            "research_behavior_type": profile.research_behavior_type.value,
            "learning_style": profile.cognitive_profile.learning_style.value,
            "workflow_patterns_count": len(profile.workflow_patterns),
            "personalization_insights_count": len(profile.personalization_insights),
            "adaptation_history_count": len(profile.adaptation_history),
            "visual_preferences": {
                "complexity_tolerance": profile.visual_preferences.complexity_tolerance,
                "preferred_chart_types": profile.visual_preferences.preferred_chart_types[:3],
                "processing_speed": profile.visual_preferences.visual_processing_speed
            },
            "workflow_preferences": {
                "optimal_session_duration": profile.workflow_preferences.optimal_session_duration,
                "multitasking_tolerance": profile.workflow_preferences.multitasking_tolerance,
                "preferred_task_count": len(profile.workflow_preferences.preferred_task_sequence)
            },
            "cognitive_profile": {
                "working_memory": profile.cognitive_profile.working_memory_capacity,
                "attention_span": profile.cognitive_profile.attention_span,
                "processing_speed": profile.cognitive_profile.processing_speed,
                "cognitive_load_tolerance": profile.cognitive_profile.cognitive_load_tolerance
            }
        }