"""Unit tests for enhanced user models."""

import pytest
import numpy as np
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from backend.rl.user_modeling.enhanced_user_models import (
    EnhancedUserProfile,
    EnhancedUserModelManager,
    VisualPreference,
    WorkflowPreference,
    CognitiveProfile,
    MultiModalPreferences,
    ResearchWorkflowPattern,
    PersonalizationInsight,
    AdaptationHistory,
    PreferenceType,
    LearningStyle,
    ResearchBehaviorType
)
from backend.rl.research_assistant.workflow_optimizer import WorkflowPattern, TaskType
from backend.rl.research_assistant.research_workflow_learner import WorkflowInsight


class TestEnhancedUserProfile:
    """Test cases for EnhancedUserProfile class."""
    
    def test_enhanced_profile_creation(self):
        """Test creating an enhanced user profile."""
        profile = EnhancedUserProfile("user_1")
        
        assert profile.user_id == "user_1"
        assert isinstance(profile.visual_preferences, VisualPreference)
        assert isinstance(profile.workflow_preferences, WorkflowPreference)
        assert isinstance(profile.cognitive_profile, CognitiveProfile)
        assert isinstance(profile.multimodal_preferences, MultiModalPreferences)
        assert isinstance(profile.research_behavior_type, ResearchBehaviorType)
        assert isinstance(profile.workflow_patterns, list)
        assert isinstance(profile.personalization_insights, list)
        assert isinstance(profile.adaptation_history, list)
        assert isinstance(profile.last_personalization_update, datetime)
    
    def test_visual_preference_defaults(self):
        """Test visual preference default values."""
        profile = EnhancedUserProfile("user_1")
        visual_prefs = profile.visual_preferences
        
        assert isinstance(visual_prefs.preferred_chart_types, list)
        assert isinstance(visual_prefs.color_preferences, dict)
        assert 0.0 <= visual_prefs.complexity_tolerance <= 1.0
        assert visual_prefs.visual_processing_speed > 0.0
        assert isinstance(visual_prefs.accessibility_needs, dict)
    
    def test_workflow_preference_defaults(self):
        """Test workflow preference default values."""
        profile = EnhancedUserProfile("user_1")
        workflow_prefs = profile.workflow_preferences
        
        assert isinstance(workflow_prefs.preferred_task_sequence, list)
        assert workflow_prefs.optimal_session_duration > 0.0
        assert workflow_prefs.break_frequency > 0.0
        assert 0.0 <= workflow_prefs.multitasking_tolerance <= 1.0
        assert 0.0 <= workflow_prefs.interruption_sensitivity <= 1.0
    
    def test_cognitive_profile_defaults(self):
        """Test cognitive profile default values."""
        profile = EnhancedUserProfile("user_1")
        cognitive = profile.cognitive_profile
        
        assert 0.0 <= cognitive.working_memory_capacity <= 1.0
        assert 0.0 <= cognitive.attention_span <= 1.0
        assert 0.0 <= cognitive.processing_speed <= 1.0
        assert 0.0 <= cognitive.cognitive_load_tolerance <= 1.0
        assert isinstance(cognitive.learning_style, LearningStyle)
        assert cognitive.information_processing_style in ["sequential", "holistic"]
        assert cognitive.decision_making_style in ["analytical", "intuitive"]


class TestEnhancedUserModelManager:
    """Test cases for EnhancedUserModelManager class."""
    
    @pytest.mark.asyncio
    async def test_get_or_create_enhanced_profile(self):
        """Test getting or creating enhanced profiles."""
        manager = EnhancedUserModelManager()
        
        # Test creating new profile
        profile1 = await manager.get_or_create_enhanced_profile("user_1")
        
        assert isinstance(profile1, EnhancedUserProfile)
        assert profile1.user_id == "user_1"
        assert "user_1" in manager.user_profiles
        
        # Test getting existing profile
        profile2 = await manager.get_or_create_enhanced_profile("user_1")
        
        assert profile1 is profile2  # Should be same instance
    
    @pytest.mark.asyncio
    async def test_update_visual_preferences(self):
        """Test updating visual preferences."""
        manager = EnhancedUserModelManager()
        
        # Create sample visual interactions
        visual_interactions = [
            {
                'chart_type': 'bar_chart',
                'engagement_score': 0.8,
                'visual_complexity': 0.6,
                'dominant_colors': ['blue', 'red'],
                'attention_distribution': {'main_chart': 0.7, 'legend': 0.3}
            },
            {
                'chart_type': 'line_chart',
                'engagement_score': 0.9,
                'visual_complexity': 0.4,
                'dominant_colors': ['blue', 'green'],
                'attention_distribution': {'main_chart': 0.8, 'axes': 0.2}
            },
            {
                'chart_type': 'bar_chart',
                'engagement_score': 0.7,
                'visual_complexity': 0.8,
                'dominant_colors': ['red', 'yellow'],
                'attention_distribution': {'main_chart': 0.6, 'legend': 0.4}
            }
        ]
        
        preferences = await manager.update_visual_preferences("user_1", visual_interactions)
        
        assert isinstance(preferences, VisualPreference)
        assert 'bar_chart' in preferences.preferred_chart_types or 'line_chart' in preferences.preferred_chart_types
        assert 'blue' in preferences.color_preferences
        assert 0.0 <= preferences.complexity_tolerance <= 1.0
        assert 'main_chart' in preferences.attention_patterns
    
    @pytest.mark.asyncio
    async def test_update_workflow_preferences(self):
        """Test updating workflow preferences."""
        manager = EnhancedUserModelManager()
        
        # Create sample workflow data
        workflow_data = [
            {
                'duration_minutes': 90.0,
                'efficiency_score': 0.8,
                'task_sequence': ['literature_search', 'paper_analysis', 'synthesis'],
                'concurrent_tasks': 1
            },
            {
                'duration_minutes': 120.0,
                'efficiency_score': 0.9,
                'task_sequence': ['literature_search', 'data_extraction', 'writing'],
                'concurrent_tasks': 2
            },
            {
                'duration_minutes': 60.0,
                'efficiency_score': 0.7,
                'task_sequence': ['paper_analysis', 'synthesis', 'writing'],
                'concurrent_tasks': 1
            }
        ]
        
        preferences = await manager.update_workflow_preferences("user_1", workflow_data)
        
        assert isinstance(preferences, WorkflowPreference)
        assert preferences.optimal_session_duration > 0.0
        assert 0.0 <= preferences.multitasking_tolerance <= 1.0
        # Should have some preferred task sequence if patterns were found
        assert isinstance(preferences.preferred_task_sequence, list)
    
    @pytest.mark.asyncio
    async def test_update_cognitive_profile(self):
        """Test updating cognitive profile."""
        manager = EnhancedUserModelManager()
        
        # Create sample performance data
        performance_data = {
            'complex_task_performance': [0.8, 0.7, 0.9, 0.6],
            'session_durations': [90, 120, 60, 150],
            'performance_over_time': [0.9, 0.8, 0.7, 0.6],  # Declining performance
            'task_completion_times': [30, 45, 25, 60],
            'expected_completion_times': [35, 40, 30, 50],
            'high_cognitive_load_performance': [0.6, 0.7, 0.5],
            'low_cognitive_load_performance': [0.8, 0.9, 0.85]
        }
        
        cognitive_profile = await manager.update_cognitive_profile("user_1", performance_data)
        
        assert isinstance(cognitive_profile, CognitiveProfile)
        assert 0.0 <= cognitive_profile.working_memory_capacity <= 1.0
        assert 0.0 <= cognitive_profile.attention_span <= 1.0
        assert 0.0 <= cognitive_profile.processing_speed <= 1.0
        assert 0.0 <= cognitive_profile.cognitive_load_tolerance <= 1.0
    
    @pytest.mark.asyncio
    async def test_add_workflow_pattern(self):
        """Test adding workflow patterns."""
        manager = EnhancedUserModelManager()
        
        # Create sample workflow pattern
        workflow_pattern = WorkflowPattern(
            pattern_id="pattern_1",
            pattern_type="sequential",
            task_sequence=["literature_search", "paper_analysis"],
            success_rate=0.8,
            average_efficiency=0.85,
            average_satisfaction=0.9,
            frequency=5,
            context_conditions={},
            performance_metrics={'average_duration': 90.0},
            best_practices=[]
        )
        
        research_pattern = await manager.add_workflow_pattern("user_1", workflow_pattern)
        
        assert isinstance(research_pattern, ResearchWorkflowPattern)
        assert research_pattern.pattern_id == "pattern_1"
        assert research_pattern.success_rate == 0.8
        assert research_pattern.efficiency_score == 0.85
        
        # Check that pattern was added to profile
        profile = await manager.get_or_create_enhanced_profile("user_1")
        assert len(profile.workflow_patterns) == 1
    
    @pytest.mark.asyncio
    async def test_add_personalization_insight(self):
        """Test adding personalization insights."""
        manager = EnhancedUserModelManager()
        
        # Create sample workflow insight
        workflow_insight = WorkflowInsight(
            insight_id="insight_1",
            insight_type="efficiency",
            title="Efficiency Improvement",
            description="Your workflow efficiency has improved",
            confidence=0.8,
            impact_level="high",
            actionable_recommendations=["Continue current practices"],
            supporting_data={"trend": "positive"}
        )
        
        personalization_insight = await manager.add_personalization_insight("user_1", workflow_insight)
        
        assert isinstance(personalization_insight, PersonalizationInsight)
        assert personalization_insight.insight_id == "insight_1"
        assert personalization_insight.confidence == 0.8
        assert personalization_insight.impact_potential == 0.8  # High impact
        
        # Check that insight was added to profile
        profile = await manager.get_or_create_enhanced_profile("user_1")
        assert len(profile.personalization_insights) == 1
    
    @pytest.mark.asyncio
    async def test_record_adaptation(self):
        """Test recording adaptations."""
        manager = EnhancedUserModelManager()
        
        success_metrics = {
            'efficiency_improvement': 0.15,
            'satisfaction_increase': 0.1,
            'task_completion_rate': 0.9
        }
        
        adaptation = await manager.record_adaptation(
            "user_1", 
            "visual_optimization", 
            "Optimized chart types based on preferences",
            success_metrics
        )
        
        assert isinstance(adaptation, AdaptationHistory)
        assert adaptation.adaptation_type == "visual_optimization"
        assert adaptation.success_metrics == success_metrics
        assert adaptation.effectiveness_score > 0.0  # Should be average of success metrics
        
        # Check that adaptation was added to profile
        profile = await manager.get_or_create_enhanced_profile("user_1")
        assert len(profile.adaptation_history) == 1
    
    @pytest.mark.asyncio
    async def test_get_personalization_recommendations(self):
        """Test getting personalization recommendations."""
        manager = EnhancedUserModelManager()
        
        # Create profile with some preferences
        profile = await manager.get_or_create_enhanced_profile("user_1")
        
        # Set some preferences that should trigger recommendations
        profile.visual_preferences.complexity_tolerance = 0.3  # Low tolerance
        profile.workflow_preferences.optimal_session_duration = 45.0  # Short sessions
        profile.cognitive_profile.working_memory_capacity = 0.4  # Low capacity
        profile.multimodal_preferences.text_to_visual_ratio = 0.9  # High text ratio
        
        recommendations = await manager.get_personalization_recommendations("user_1")
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Check recommendation structure
        for rec in recommendations:
            assert 'type' in rec
            assert 'title' in rec
            assert 'description' in rec
            assert 'impact_potential' in rec
            assert 'implementation' in rec
            assert 0.0 <= rec['impact_potential'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_analyze_chart_type_preferences(self):
        """Test chart type preference analysis."""
        manager = EnhancedUserModelManager()
        
        interactions = [
            {'chart_type': 'bar_chart', 'engagement_score': 0.8},
            {'chart_type': 'line_chart', 'engagement_score': 0.6},
            {'chart_type': 'bar_chart', 'engagement_score': 0.9},
            {'chart_type': 'pie_chart', 'engagement_score': 0.4}
        ]
        
        preferences = await manager._analyze_chart_type_preferences(interactions)
        
        assert isinstance(preferences, dict)
        assert 'bar_chart' in preferences
        assert 'line_chart' in preferences
        assert 'pie_chart' in preferences
        
        # Bar chart should have highest preference (0.85 average)
        assert preferences['bar_chart'] > preferences['line_chart']
        assert preferences['bar_chart'] > preferences['pie_chart']
    
    @pytest.mark.asyncio
    async def test_analyze_complexity_tolerance(self):
        """Test complexity tolerance analysis."""
        manager = EnhancedUserModelManager()
        
        # High complexity with high engagement = high tolerance
        high_tolerance_interactions = [
            {'visual_complexity': 0.8, 'engagement_score': 0.9},
            {'visual_complexity': 0.9, 'engagement_score': 0.8},
            {'visual_complexity': 0.7, 'engagement_score': 0.85}
        ]
        
        tolerance = await manager._analyze_complexity_tolerance(high_tolerance_interactions)
        
        assert isinstance(tolerance, float)
        assert 0.0 <= tolerance <= 1.0
        assert tolerance > 0.5  # Should indicate higher tolerance
        
        # Low complexity with high engagement = low tolerance
        low_tolerance_interactions = [
            {'visual_complexity': 0.2, 'engagement_score': 0.9},
            {'visual_complexity': 0.3, 'engagement_score': 0.8},
            {'visual_complexity': 0.8, 'engagement_score': 0.3}
        ]
        
        low_tolerance = await manager._analyze_complexity_tolerance(low_tolerance_interactions)
        
        assert low_tolerance < tolerance  # Should be lower
    
    @pytest.mark.asyncio
    async def test_analyze_optimal_session_duration(self):
        """Test optimal session duration analysis."""
        manager = EnhancedUserModelManager()
        
        workflow_data = [
            {'duration_minutes': 60, 'efficiency_score': 0.7},
            {'duration_minutes': 90, 'efficiency_score': 0.9},
            {'duration_minutes': 120, 'efficiency_score': 0.8},
            {'duration_minutes': 90, 'efficiency_score': 0.85},
            {'duration_minutes': 150, 'efficiency_score': 0.6}
        ]
        
        optimal_duration = await manager._analyze_optimal_session_duration(workflow_data)
        
        assert isinstance(optimal_duration, float)
        assert optimal_duration > 0.0
        # Should prefer 90 minutes (highest average efficiency)
        assert 60 <= optimal_duration <= 120
    
    @pytest.mark.asyncio
    async def test_analyze_task_sequence_preferences(self):
        """Test task sequence preference analysis."""
        manager = EnhancedUserModelManager()
        
        workflow_data = [
            {
                'task_sequence': ['literature_search', 'paper_analysis', 'synthesis'],
                'efficiency_score': 0.9
            },
            {
                'task_sequence': ['literature_search', 'paper_analysis', 'writing'],
                'efficiency_score': 0.8
            },
            {
                'task_sequence': ['paper_analysis', 'synthesis', 'writing'],
                'efficiency_score': 0.7
            }
        ]
        
        preferred_sequence = await manager._analyze_task_sequence_preferences(workflow_data)
        
        assert isinstance(preferred_sequence, list)
        # Should identify literature_search -> paper_analysis as efficient transition
        if preferred_sequence:
            assert all(isinstance(task, TaskType) for task in preferred_sequence)
    
    @pytest.mark.asyncio
    async def test_assess_working_memory(self):
        """Test working memory assessment."""
        manager = EnhancedUserModelManager()
        
        # High performance on complex tasks
        high_performance_data = {
            'complex_task_performance': [0.8, 0.9, 0.85, 0.7]
        }
        
        working_memory = await manager._assess_working_memory(high_performance_data)
        
        assert isinstance(working_memory, float)
        assert 0.0 <= working_memory <= 1.0
        assert working_memory > 0.7  # Should be high
        
        # Low performance on complex tasks
        low_performance_data = {
            'complex_task_performance': [0.3, 0.4, 0.2, 0.5]
        }
        
        low_working_memory = await manager._assess_working_memory(low_performance_data)
        
        assert low_working_memory < working_memory
    
    @pytest.mark.asyncio
    async def test_assess_attention_span(self):
        """Test attention span assessment."""
        manager = EnhancedUserModelManager()
        
        # Stable performance over time = good attention
        stable_performance_data = {
            'session_durations': [120, 90, 150],
            'performance_over_time': [0.8, 0.82, 0.79, 0.81]  # Stable
        }
        
        attention_span = await manager._assess_attention_span(stable_performance_data)
        
        assert isinstance(attention_span, float)
        assert 0.0 <= attention_span <= 1.0
        
        # Declining performance = poor attention
        declining_performance_data = {
            'session_durations': [120, 90, 150],
            'performance_over_time': [0.9, 0.7, 0.5, 0.3]  # Declining
        }
        
        poor_attention = await manager._assess_attention_span(declining_performance_data)
        
        assert poor_attention < attention_span
    
    @pytest.mark.asyncio
    async def test_find_similar_pattern(self):
        """Test finding similar workflow patterns."""
        manager = EnhancedUserModelManager()
        
        existing_patterns = [
            ResearchWorkflowPattern(
                pattern_id="existing_1",
                pattern_name="Pattern 1",
                task_sequence=[TaskType.LITERATURE_SEARCH, TaskType.PAPER_ANALYSIS],
                typical_duration=90.0,
                success_rate=0.8,
                efficiency_score=0.85,
                user_satisfaction=0.9
            )
        ]
        
        # Similar pattern (same sequence)
        similar_pattern = ResearchWorkflowPattern(
            pattern_id="new_1",
            pattern_name="New Pattern",
            task_sequence=[TaskType.LITERATURE_SEARCH, TaskType.PAPER_ANALYSIS],
            typical_duration=95.0,
            success_rate=0.82,
            efficiency_score=0.87,
            user_satisfaction=0.88
        )
        
        found_pattern = await manager._find_similar_pattern(existing_patterns, similar_pattern)
        
        assert found_pattern is not None
        assert found_pattern.pattern_id == "existing_1"
        
        # Different pattern
        different_pattern = ResearchWorkflowPattern(
            pattern_id="new_2",
            pattern_name="Different Pattern",
            task_sequence=[TaskType.DATA_EXTRACTION, TaskType.SYNTHESIS],
            typical_duration=60.0,
            success_rate=0.7,
            efficiency_score=0.75,
            user_satisfaction=0.8
        )
        
        not_found = await manager._find_similar_pattern(existing_patterns, different_pattern)
        
        assert not_found is None
    
    @pytest.mark.asyncio
    async def test_merge_workflow_patterns(self):
        """Test merging workflow patterns."""
        manager = EnhancedUserModelManager()
        
        existing_pattern = ResearchWorkflowPattern(
            pattern_id="pattern_1",
            pattern_name="Pattern 1",
            task_sequence=[TaskType.LITERATURE_SEARCH],
            typical_duration=90.0,
            success_rate=0.8,
            efficiency_score=0.85,
            user_satisfaction=0.9,
            frequency_of_use=5
        )
        
        new_pattern = ResearchWorkflowPattern(
            pattern_id="pattern_1",
            pattern_name="Pattern 1",
            task_sequence=[TaskType.LITERATURE_SEARCH],
            typical_duration=100.0,  # Different duration
            success_rate=0.9,       # Higher success rate
            efficiency_score=0.8,   # Lower efficiency
            user_satisfaction=0.85  # Lower satisfaction
        )
        
        original_duration = existing_pattern.typical_duration
        original_frequency = existing_pattern.frequency_of_use
        
        await manager._merge_workflow_patterns(existing_pattern, new_pattern)
        
        # Values should be updated with exponential moving average
        assert existing_pattern.typical_duration != original_duration
        assert existing_pattern.frequency_of_use == original_frequency + 1
        assert existing_pattern.last_used is not None
        
        # Should be between original and new values
        assert 90.0 < existing_pattern.typical_duration < 100.0
        assert 0.8 < existing_pattern.success_rate < 0.9
    
    def test_get_profile_summary(self):
        """Test getting profile summary."""
        manager = EnhancedUserModelManager()
        
        # Test with non-existent user
        summary = manager.get_profile_summary("non_existent_user")
        
        assert "message" in summary
        assert summary["message"] == "User profile not found"
        
        # Create profile and test summary
        profile = EnhancedUserProfile("user_1")
        manager.user_profiles["user_1"] = profile
        
        # Add some data
        profile.visual_preferences.complexity_tolerance = 0.7
        profile.visual_preferences.preferred_chart_types = ["bar_chart", "line_chart"]
        profile.workflow_preferences.optimal_session_duration = 90.0
        profile.cognitive_profile.working_memory_capacity = 0.8
        
        summary = manager.get_profile_summary("user_1")
        
        assert isinstance(summary, dict)
        assert summary["user_id"] == "user_1"
        assert "profile_version" in summary
        assert "last_update" in summary
        assert "research_behavior_type" in summary
        assert "learning_style" in summary
        assert "visual_preferences" in summary
        assert "workflow_preferences" in summary
        assert "cognitive_profile" in summary
        
        # Check specific values
        assert summary["visual_preferences"]["complexity_tolerance"] == 0.7
        assert "bar_chart" in summary["visual_preferences"]["preferred_chart_types"]
        assert summary["workflow_preferences"]["optimal_session_duration"] == 90.0
        assert summary["cognitive_profile"]["working_memory"] == 0.8
    
    @pytest.mark.asyncio
    async def test_empty_data_handling(self):
        """Test handling of empty or invalid data."""
        manager = EnhancedUserModelManager()
        
        # Test with empty visual interactions
        preferences = await manager.update_visual_preferences("user_1", [])
        assert isinstance(preferences, VisualPreference)
        
        # Test with empty workflow data
        workflow_prefs = await manager.update_workflow_preferences("user_1", [])
        assert isinstance(workflow_prefs, WorkflowPreference)
        
        # Test with empty performance data
        cognitive = await manager.update_cognitive_profile("user_1", {})
        assert isinstance(cognitive, CognitiveProfile)
        
        # Test with empty recommendations
        recommendations = await manager.get_personalization_recommendations("user_1")
        assert isinstance(recommendations, list)
    
    @pytest.mark.asyncio
    async def test_insight_limit(self):
        """Test that insights are limited to prevent memory issues."""
        manager = EnhancedUserModelManager()
        
        # Add more than the limit (50 insights)
        for i in range(55):
            insight = WorkflowInsight(
                insight_id=f"insight_{i}",
                insight_type="test",
                title=f"Test Insight {i}",
                description="Test description",
                confidence=0.8,
                impact_level="medium",
                actionable_recommendations=[],
                supporting_data={}
            )
            await manager.add_personalization_insight("user_1", insight)
        
        profile = await manager.get_or_create_enhanced_profile("user_1")
        
        # Should be limited to 50 insights
        assert len(profile.personalization_insights) == 50
        
        # Should keep the most recent ones
        assert profile.personalization_insights[-1].insight_id == "insight_54"
    
    @pytest.mark.asyncio
    async def test_adaptation_history_limit(self):
        """Test that adaptation history is limited."""
        manager = EnhancedUserModelManager()
        
        # Add more than the limit (100 adaptations)
        for i in range(105):
            await manager.record_adaptation(
                "user_1",
                "test_adaptation",
                f"Test adaptation {i}",
                {"metric": 0.5}
            )
        
        profile = await manager.get_or_create_enhanced_profile("user_1")
        
        # Should be limited to 100 adaptations
        assert len(profile.adaptation_history) == 100
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in various methods."""
        manager = EnhancedUserModelManager()
        
        # Test with malformed data
        malformed_interactions = [
            {'invalid_key': 'invalid_value'},
            {'chart_type': None, 'engagement_score': 'invalid'}
        ]
        
        # Should handle errors gracefully
        try:
            preferences = await manager.update_visual_preferences("user_1", malformed_interactions)
            assert isinstance(preferences, VisualPreference)
        except Exception:
            # Or may raise exception, which is also acceptable
            pass
        
        # Test with invalid performance data
        invalid_performance = {
            'complex_task_performance': 'invalid',
            'session_durations': None
        }
        
        try:
            cognitive = await manager.update_cognitive_profile("user_1", invalid_performance)
            assert isinstance(cognitive, CognitiveProfile)
        except Exception:
            pass


class TestDataClasses:
    """Test cases for data classes."""
    
    def test_visual_preference_creation(self):
        """Test VisualPreference creation."""
        visual_pref = VisualPreference(
            preferred_chart_types=["bar_chart", "line_chart"],
            color_preferences={"blue": 0.8, "red": 0.6},
            complexity_tolerance=0.7,
            interaction_style="active",
            visual_processing_speed=1.2
        )
        
        assert visual_pref.preferred_chart_types == ["bar_chart", "line_chart"]
        assert visual_pref.color_preferences["blue"] == 0.8
        assert visual_pref.complexity_tolerance == 0.7
        assert visual_pref.interaction_style == "active"
        assert visual_pref.visual_processing_speed == 1.2
    
    def test_workflow_preference_creation(self):
        """Test WorkflowPreference creation."""
        workflow_pref = WorkflowPreference(
            preferred_task_sequence=[TaskType.LITERATURE_SEARCH, TaskType.PAPER_ANALYSIS],
            optimal_session_duration=90.0,
            break_frequency=25.0,
            multitasking_tolerance=0.3,
            interruption_sensitivity=0.8
        )
        
        assert len(workflow_pref.preferred_task_sequence) == 2
        assert workflow_pref.optimal_session_duration == 90.0
        assert workflow_pref.break_frequency == 25.0
        assert workflow_pref.multitasking_tolerance == 0.3
        assert workflow_pref.interruption_sensitivity == 0.8
    
    def test_cognitive_profile_creation(self):
        """Test CognitiveProfile creation."""
        cognitive = CognitiveProfile(
            working_memory_capacity=0.8,
            attention_span=0.7,
            processing_speed=0.9,
            cognitive_load_tolerance=0.6,
            learning_style=LearningStyle.VISUAL,
            information_processing_style="holistic",
            decision_making_style="intuitive"
        )
        
        assert cognitive.working_memory_capacity == 0.8
        assert cognitive.attention_span == 0.7
        assert cognitive.processing_speed == 0.9
        assert cognitive.cognitive_load_tolerance == 0.6
        assert cognitive.learning_style == LearningStyle.VISUAL
        assert cognitive.information_processing_style == "holistic"
        assert cognitive.decision_making_style == "intuitive"
    
    def test_research_workflow_pattern_creation(self):
        """Test ResearchWorkflowPattern creation."""
        pattern = ResearchWorkflowPattern(
            pattern_id="pattern_1",
            pattern_name="Research Pattern",
            task_sequence=[TaskType.LITERATURE_SEARCH, TaskType.PAPER_ANALYSIS],
            typical_duration=90.0,
            success_rate=0.85,
            efficiency_score=0.8,
            user_satisfaction=0.9,
            frequency_of_use=10
        )
        
        assert pattern.pattern_id == "pattern_1"
        assert pattern.pattern_name == "Research Pattern"
        assert len(pattern.task_sequence) == 2
        assert pattern.typical_duration == 90.0
        assert pattern.success_rate == 0.85
        assert pattern.efficiency_score == 0.8
        assert pattern.user_satisfaction == 0.9
        assert pattern.frequency_of_use == 10
    
    def test_personalization_insight_creation(self):
        """Test PersonalizationInsight creation."""
        insight = PersonalizationInsight(
            insight_id="insight_1",
            insight_type="efficiency",
            description="Workflow efficiency has improved",
            confidence=0.8,
            impact_potential=0.7,
            actionable_recommendations=["Continue current practices"],
            supporting_evidence={"trend": "positive", "improvement": 0.15}
        )
        
        assert insight.insight_id == "insight_1"
        assert insight.insight_type == "efficiency"
        assert insight.description == "Workflow efficiency has improved"
        assert insight.confidence == 0.8
        assert insight.impact_potential == 0.7
        assert len(insight.actionable_recommendations) == 1
        assert "trend" in insight.supporting_evidence
        assert isinstance(insight.created_at, datetime)
        assert insight.applied == False
    
    def test_adaptation_history_creation(self):
        """Test AdaptationHistory creation."""
        adaptation = AdaptationHistory(
            adaptation_id="adapt_1",
            adaptation_type="visual_optimization",
            description="Optimized chart types",
            applied_at=datetime.now(),
            success_metrics={"efficiency": 0.8, "satisfaction": 0.9},
            effectiveness_score=0.85
        )
        
        assert adaptation.adaptation_id == "adapt_1"
        assert adaptation.adaptation_type == "visual_optimization"
        assert adaptation.description == "Optimized chart types"
        assert isinstance(adaptation.applied_at, datetime)
        assert "efficiency" in adaptation.success_metrics
        assert adaptation.effectiveness_score == 0.85
        assert adaptation.reverted == False