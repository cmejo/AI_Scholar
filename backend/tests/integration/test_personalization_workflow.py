"""End-to-end integration tests for advanced personalization workflow."""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from backend.rl.user_modeling.enhanced_user_models import EnhancedUserProfile
from backend.rl.user_modeling.personalization_engine import PersonalizationEngine
from backend.rl.personalization.advanced_adaptation_algorithms import AdvancedAdaptationAlgorithms
from backend.rl.personalization.user_behavior_predictor import UserBehaviorPredictor
from backend.rl.models.user_models import UserInteraction, UserContext, UserHistory
from backend.rl.utils import personalization_logger, handle_errors
from backend.rl.exceptions.advanced_exceptions import PersonalizationError


class TestPersonalizationWorkflowIntegration:
    """Integration tests for complete advanced personalization workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.personalization_engine = PersonalizationEngine()
        self.adaptation_algorithms = AdvancedAdaptationAlgorithms()
        self.behavior_predictor = UserBehaviorPredictor()
        
        # Create test user profile
        self.test_user_id = "test_user_001"
        self.test_user_profile = EnhancedUserProfile(
            user_id=self.test_user_id,
            preferences={
                "research_domains": ["machine_learning", "computer_vision"],
                "content_types": ["papers", "tutorials"],
                "interaction_style": "detailed"
            },
            behavior_patterns=[],
            adaptation_history=[],
            multi_modal_preferences={
                "visual_content": 0.8,
                "text_content": 0.9,
                "interactive_elements": 0.6
            }
        )
    
    @pytest.mark.asyncio
    async def test_complete_personalization_workflow_success(self):
        """Test complete personalization workflow from user interaction to adaptation."""
        # Step 1: Collect user interactions
        user_interactions = [
            UserInteraction(
                user_id=self.test_user_id,
                interaction_type="document_view",
                content_id="doc_001",
                timestamp=datetime.now() - timedelta(minutes=30),
                duration=300,  # 5 minutes
                feedback_score=4.5,
                context={"domain": "machine_learning", "content_type": "paper"}
            ),
            UserInteraction(
                user_id=self.test_user_id,
                interaction_type="visual_element_click",
                content_id="chart_001",
                timestamp=datetime.now() - timedelta(minutes=25),
                duration=60,
                feedback_score=4.0,
                context={"element_type": "chart", "chart_type": "bar_chart"}
            ),
            UserInteraction(
                user_id=self.test_user_id,
                interaction_type="recommendation_rating",
                content_id="rec_001",
                timestamp=datetime.now() - timedelta(minutes=20),
                duration=10,
                feedback_score=5.0,
                context={"recommendation_type": "similar_papers"}
            )
        ]
        
        # Step 2: Deep preference learning
        preference_model = await self.adaptation_algorithms.deep_preference_learning(
            user_interactions
        )
        
        assert preference_model is not None
        assert preference_model.preference_embeddings is not None
        assert len(preference_model.preference_weights) > 0
        assert preference_model.confidence_intervals is not None
        
        # Step 3: Behavior prediction
        current_context = UserContext(
            user_id=self.test_user_id,
            current_task="literature_review",
            research_domain="machine_learning",
            session_context={"time_of_day": "morning", "device": "desktop"},
            interaction_history=user_interactions[-3:]
        )
        
        predicted_action = await self.behavior_predictor.predict_next_action(current_context)
        
        assert predicted_action is not None
        assert predicted_action.action_type is not None
        assert predicted_action.confidence > 0
        assert predicted_action.expected_outcome is not None
        
        # Step 4: Contextual bandit optimization
        available_actions = [
            {"type": "recommend_paper", "domain": "machine_learning"},
            {"type": "show_visual_summary", "content_type": "chart"},
            {"type": "suggest_workflow", "workflow_type": "literature_review"}
        ]
        
        optimal_action = await self.adaptation_algorithms.contextual_bandit_optimization(
            current_context, available_actions
        )
        
        assert optimal_action is not None
        assert optimal_action.action in available_actions
        assert optimal_action.expected_reward > 0
        assert optimal_action.confidence > 0
        
        # Step 5: Apply personalization
        personalized_experience = await self.personalization_engine.personalize_experience(
            self.test_user_profile, current_context, optimal_action
        )
        
        assert personalized_experience is not None
        assert personalized_experience.user_id == self.test_user_id
        assert personalized_experience.personalization_score > 0
        assert len(personalized_experience.applied_adaptations) > 0
    
    @pytest.mark.asyncio
    async def test_personalization_workflow_with_meta_learning(self):
        """Test personalization workflow incorporating meta-learning from similar users."""
        # Create similar user profiles
        similar_users = [
            EnhancedUserProfile(
                user_id="similar_user_001",
                preferences={
                    "research_domains": ["machine_learning", "deep_learning"],
                    "content_types": ["papers", "code"],
                    "interaction_style": "detailed"
                },
                behavior_patterns=[
                    {"pattern_type": "reading_preference", "strength": 0.8},
                    {"pattern_type": "visual_preference", "strength": 0.7}
                ],
                adaptation_history=[],
                multi_modal_preferences={
                    "visual_content": 0.9,
                    "text_content": 0.8,
                    "interactive_elements": 0.5
                }
            ),
            EnhancedUserProfile(
                user_id="similar_user_002",
                preferences={
                    "research_domains": ["computer_vision", "machine_learning"],
                    "content_types": ["papers", "tutorials"],
                    "interaction_style": "comprehensive"
                },
                behavior_patterns=[
                    {"pattern_type": "exploration_preference", "strength": 0.9},
                    {"pattern_type": "depth_preference", "strength": 0.6}
                ],
                adaptation_history=[],
                multi_modal_preferences={
                    "visual_content": 0.85,
                    "text_content": 0.95,
                    "interactive_elements": 0.7
                }
            )
        ]
        
        # Apply meta-learning adaptation
        adaptation_strategy = await self.adaptation_algorithms.meta_learning_adaptation(
            self.test_user_profile, similar_users
        )
        
        assert adaptation_strategy is not None
        assert adaptation_strategy.strategy_type is not None
        assert adaptation_strategy.expected_improvement > 0
        assert adaptation_strategy.risk_assessment is not None
        assert len(adaptation_strategy.parameters) > 0
        
        # Apply meta-learning insights to personalization
        enhanced_profile = await self.personalization_engine.apply_meta_learning_insights(
            self.test_user_profile, adaptation_strategy
        )
        
        assert enhanced_profile is not None
        assert enhanced_profile.user_id == self.test_user_id
        # Profile should be enhanced with meta-learning insights
        assert len(enhanced_profile.behavior_patterns) >= len(self.test_user_profile.behavior_patterns)
    
    @pytest.mark.asyncio
    async def test_personalization_workflow_with_satisfaction_prediction(self):
        """Test personalization workflow with satisfaction trajectory prediction."""
        # Create interaction sequence for satisfaction prediction
        interaction_sequence = [
            UserInteraction(
                user_id=self.test_user_id,
                interaction_type="search_query",
                content_id="query_001",
                timestamp=datetime.now() - timedelta(minutes=60),
                duration=30,
                feedback_score=3.0,
                context={"query": "machine learning papers", "results_count": 50}
            ),
            UserInteraction(
                user_id=self.test_user_id,
                interaction_type="document_view",
                content_id="doc_002",
                timestamp=datetime.now() - timedelta(minutes=55),
                duration=180,
                feedback_score=3.5,
                context={"relevance": "medium", "complexity": "high"}
            ),
            UserInteraction(
                user_id=self.test_user_id,
                interaction_type="document_view",
                content_id="doc_003",
                timestamp=datetime.now() - timedelta(minutes=50),
                duration=420,
                feedback_score=4.5,
                context={"relevance": "high", "complexity": "medium"}
            )
        ]
        
        # Predict satisfaction trajectory
        satisfaction_trajectory = await self.behavior_predictor.predict_satisfaction_trajectory(
            interaction_sequence
        )
        
        assert satisfaction_trajectory is not None
        assert satisfaction_trajectory.current_satisfaction > 0
        assert satisfaction_trajectory.predicted_satisfaction is not None
        assert len(satisfaction_trajectory.trajectory_points) > 0
        assert satisfaction_trajectory.trend_direction in ["increasing", "decreasing", "stable"]
        
        # Use satisfaction prediction for proactive adaptation
        if satisfaction_trajectory.trend_direction == "decreasing":
            # Apply intervention strategy
            intervention_strategy = await self.adaptation_algorithms.generate_intervention_strategy(
                self.test_user_profile, satisfaction_trajectory
            )
            
            assert intervention_strategy is not None
            assert intervention_strategy.intervention_type is not None
            assert intervention_strategy.urgency_level > 0
    
    @pytest.mark.asyncio
    async def test_personalization_workflow_with_behavior_patterns(self):
        """Test personalization workflow with behavior pattern identification."""
        # Create comprehensive user history
        user_history = UserHistory(
            user_id=self.test_user_id,
            interactions=[
                # Morning reading pattern
                UserInteraction(
                    user_id=self.test_user_id,
                    interaction_type="document_view",
                    content_id=f"morning_doc_{i}",
                    timestamp=datetime.now().replace(hour=9, minute=i*10),
                    duration=300 + i*30,
                    feedback_score=4.0 + i*0.1,
                    context={"time_period": "morning", "content_type": "paper"}
                )
                for i in range(5)
            ] + [
                # Afternoon visual content pattern
                UserInteraction(
                    user_id=self.test_user_id,
                    interaction_type="visual_element_click",
                    content_id=f"afternoon_visual_{i}",
                    timestamp=datetime.now().replace(hour=14, minute=i*15),
                    duration=120 + i*20,
                    feedback_score=3.5 + i*0.15,
                    context={"time_period": "afternoon", "element_type": "chart"}
                )
                for i in range(4)
            ],
            preferences_evolution=[],
            session_patterns=[]
        )
        
        # Identify behavior patterns
        behavior_patterns = await self.behavior_predictor.identify_behavior_patterns(user_history)
        
        assert behavior_patterns is not None
        assert len(behavior_patterns) > 0
        
        # Should identify temporal patterns
        temporal_patterns = [p for p in behavior_patterns if p.pattern_type == "temporal"]
        assert len(temporal_patterns) > 0
        
        # Should identify content preference patterns
        content_patterns = [p for p in behavior_patterns if p.pattern_type == "content_preference"]
        assert len(content_patterns) > 0
        
        # Apply pattern-based personalization
        pattern_based_adaptations = await self.personalization_engine.apply_pattern_based_adaptations(
            self.test_user_profile, behavior_patterns
        )
        
        assert pattern_based_adaptations is not None
        assert len(pattern_based_adaptations) > 0
        
        for adaptation in pattern_based_adaptations:
            assert adaptation.adaptation_type is not None
            assert adaptation.confidence > 0
            assert adaptation.expected_impact > 0
    
    @pytest.mark.asyncio
    async def test_personalization_workflow_error_handling(self):
        """Test personalization workflow error handling and graceful degradation."""
        # Test with invalid user interactions
        invalid_interactions = [
            UserInteraction(
                user_id="invalid_user",
                interaction_type="invalid_type",
                content_id=None,
                timestamp=None,
                duration=-1,
                feedback_score=10.0,  # Invalid score
                context={}
            )
        ]
        
        # Should handle invalid data gracefully
        with patch.object(
            self.adaptation_algorithms,
            'deep_preference_learning',
            side_effect=PersonalizationError("Invalid interaction data")
        ):
            # Test error recovery
            try:
                await self.adaptation_algorithms.deep_preference_learning(invalid_interactions)
                assert False, "Should have raised PersonalizationError"
            except PersonalizationError as e:
                assert "Invalid interaction data" in str(e)
        
        # Test graceful degradation
        @handle_errors(component="personalization", recovery_strategy="graceful_degradation")
        async def personalize_with_fallback():
            raise PersonalizationError("Personalization service unavailable")
        
        # Should not raise exception due to graceful degradation
        result = await personalize_with_fallback()
        # Result should be None or default value due to graceful degradation
    
    @pytest.mark.asyncio
    async def test_personalization_workflow_performance_optimization(self):
        """Test personalization workflow performance optimization."""
        import time
        
        # Create large-scale user interaction data
        large_interaction_set = [
            UserInteraction(
                user_id=self.test_user_id,
                interaction_type="document_view",
                content_id=f"doc_{i:06d}",
                timestamp=datetime.now() - timedelta(minutes=i),
                duration=60 + (i % 300),
                feedback_score=3.0 + (i % 3),
                context={"batch_id": i // 100, "content_type": "paper"}
            )
            for i in range(1000)  # Large dataset
        ]
        
        # Measure performance of preference learning
        start_time = time.time()
        preference_model = await self.adaptation_algorithms.deep_preference_learning(
            large_interaction_set
        )
        preference_learning_time = time.time() - start_time
        
        # Measure performance of behavior prediction
        start_time = time.time()
        user_history = UserHistory(
            user_id=self.test_user_id,
            interactions=large_interaction_set,
            preferences_evolution=[],
            session_patterns=[]
        )
        behavior_patterns = await self.behavior_predictor.identify_behavior_patterns(user_history)
        pattern_identification_time = time.time() - start_time
        
        # Log performance metrics
        personalization_logger.info(
            "Personalization workflow performance",
            preference_learning_time=preference_learning_time,
            pattern_identification_time=pattern_identification_time,
            interaction_count=len(large_interaction_set),
            patterns_identified=len(behavior_patterns)
        )
        
        # Verify performance is acceptable
        assert preference_learning_time < 10.0, f"Preference learning too slow: {preference_learning_time}s"
        assert pattern_identification_time < 5.0, f"Pattern identification too slow: {pattern_identification_time}s"
        
        # Verify results quality
        assert preference_model is not None
        assert len(behavior_patterns) > 0
    
    @pytest.mark.asyncio
    async def test_personalization_workflow_real_time_adaptation(self):
        """Test real-time personalization adaptation during user session."""
        # Simulate real-time user session
        session_interactions = []
        
        # Initial context
        current_context = UserContext(
            user_id=self.test_user_id,
            current_task="research_exploration",
            research_domain="machine_learning",
            session_context={"session_start": datetime.now()},
            interaction_history=[]
        )
        
        # Simulate 10 interactions in real-time
        for i in range(10):
            # Predict next action based on current context
            predicted_action = await self.behavior_predictor.predict_next_action(current_context)
            
            # Simulate user interaction
            interaction = UserInteraction(
                user_id=self.test_user_id,
                interaction_type=predicted_action.action_type,
                content_id=f"realtime_content_{i}",
                timestamp=datetime.now(),
                duration=60 + i*10,
                feedback_score=3.0 + (i % 3) * 0.5,
                context={"interaction_sequence": i, "predicted": True}
            )
            
            session_interactions.append(interaction)
            
            # Update context with new interaction
            current_context.interaction_history.append(interaction)
            
            # Real-time adaptation every 3 interactions
            if (i + 1) % 3 == 0:
                # Update preference model
                updated_preference_model = await self.adaptation_algorithms.deep_preference_learning(
                    session_interactions
                )
                
                # Apply real-time personalization
                personalized_experience = await self.personalization_engine.personalize_experience(
                    self.test_user_profile, current_context, predicted_action
                )
                
                assert personalized_experience is not None
                assert personalized_experience.adaptation_timestamp is not None
                
                # Log real-time adaptation
                personalization_logger.info(
                    f"Real-time adaptation applied at interaction {i+1}",
                    user_id=self.test_user_id,
                    interaction_count=len(session_interactions),
                    personalization_score=personalized_experience.personalization_score
                )
        
        # Verify session-level learning
        assert len(session_interactions) == 10
        
        # Final session analysis
        session_patterns = await self.behavior_predictor.analyze_session_patterns(session_interactions)
        assert session_patterns is not None
        assert len(session_patterns) > 0


class TestPersonalizationWorkflowEdgeCases:
    """Test edge cases and boundary conditions in personalization workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.personalization_engine = PersonalizationEngine()
        self.adaptation_algorithms = AdvancedAdaptationAlgorithms()
        self.behavior_predictor = UserBehaviorPredictor()
    
    @pytest.mark.asyncio
    async def test_workflow_with_new_user(self):
        """Test personalization workflow with completely new user."""
        new_user_id = "new_user_001"
        new_user_profile = EnhancedUserProfile(
            user_id=new_user_id,
            preferences={},  # Empty preferences
            behavior_patterns=[],  # No patterns yet
            adaptation_history=[],
            multi_modal_preferences={}  # No multi-modal preferences
        )
        
        # Should handle new user gracefully
        current_context = UserContext(
            user_id=new_user_id,
            current_task="onboarding",
            research_domain="unknown",
            session_context={"first_session": True},
            interaction_history=[]
        )
        
        # Predict action for new user (should use defaults)
        predicted_action = await self.behavior_predictor.predict_next_action(current_context)
        
        assert predicted_action is not None
        assert predicted_action.confidence < 0.5  # Low confidence for new user
        assert predicted_action.action_type in ["explore", "onboard", "tutorial"]
    
    @pytest.mark.asyncio
    async def test_workflow_with_conflicting_preferences(self):
        """Test personalization workflow with conflicting user preferences."""
        conflicting_user_profile = EnhancedUserProfile(
            user_id="conflicting_user",
            preferences={
                "content_types": ["papers", "tutorials"],  # Detailed content
                "interaction_style": "quick",  # But quick interaction
                "research_domains": ["machine_learning", "biology"]  # Unrelated domains
            },
            behavior_patterns=[
                {"pattern_type": "depth_preference", "strength": 0.9},  # Likes depth
                {"pattern_type": "speed_preference", "strength": 0.8}   # But also speed
            ],
            adaptation_history=[],
            multi_modal_preferences={
                "visual_content": 0.9,  # High visual preference
                "text_content": 0.1    # Low text preference (conflicting)
            }
        )
        
        # Should resolve conflicts intelligently
        current_context = UserContext(
            user_id="conflicting_user",
            current_task="research",
            research_domain="machine_learning",
            session_context={},
            interaction_history=[]
        )
        
        # Adaptation should handle conflicts
        available_actions = [
            {"type": "show_detailed_paper", "content_type": "text"},
            {"type": "show_visual_summary", "content_type": "visual"},
            {"type": "show_quick_overview", "content_type": "mixed"}
        ]
        
        optimal_action = await self.adaptation_algorithms.contextual_bandit_optimization(
            current_context, available_actions
        )
        
        assert optimal_action is not None
        # Should choose action that balances conflicting preferences
        assert optimal_action.confidence > 0
    
    @pytest.mark.asyncio
    async def test_workflow_with_extreme_feedback_scores(self):
        """Test personalization workflow with extreme feedback scores."""
        extreme_interactions = [
            UserInteraction(
                user_id="extreme_user",
                interaction_type="document_view",
                content_id="extreme_doc_1",
                timestamp=datetime.now(),
                duration=10,
                feedback_score=1.0,  # Very negative
                context={"content_quality": "poor"}
            ),
            UserInteraction(
                user_id="extreme_user",
                interaction_type="document_view",
                content_id="extreme_doc_2",
                timestamp=datetime.now(),
                duration=600,
                feedback_score=5.0,  # Very positive
                context={"content_quality": "excellent"}
            )
        ]
        
        # Should handle extreme scores appropriately
        preference_model = await self.adaptation_algorithms.deep_preference_learning(
            extreme_interactions
        )
        
        assert preference_model is not None
        # Should show clear preference distinction
        assert max(preference_model.preference_weights.values()) > 0.7
        assert min(preference_model.preference_weights.values()) < 0.3
    
    @pytest.mark.asyncio
    async def test_workflow_with_sparse_interaction_data(self):
        """Test personalization workflow with very sparse interaction data."""
        sparse_interactions = [
            UserInteraction(
                user_id="sparse_user",
                interaction_type="document_view",
                content_id="sparse_doc_1",
                timestamp=datetime.now() - timedelta(days=30),
                duration=120,
                feedback_score=3.5,
                context={"frequency": "rare"}
            )
        ]
        
        # Should handle sparse data gracefully
        preference_model = await self.adaptation_algorithms.deep_preference_learning(
            sparse_interactions
        )
        
        assert preference_model is not None
        # Should have low confidence due to sparse data
        assert all(
            interval[1] - interval[0] > 0.5  # Wide confidence intervals
            for interval in preference_model.confidence_intervals.values()
        )


if __name__ == "__main__":
    pytest.main([__file__])