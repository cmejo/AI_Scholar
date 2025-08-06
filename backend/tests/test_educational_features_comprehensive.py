"""
Comprehensive test suite for educational features including learning outcome validation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json

from services.quiz_generation_service import QuizGenerationService
from services.spaced_repetition_service import SpacedRepetitionService
from services.learning_progress_service import LearningProgressService
from services.gamification_service import GamificationService


class TestQuizGenerationFeatures:
    """Test suite for quiz generation functionality."""
    
    @pytest.fixture
    def quiz_service(self):
        return QuizGenerationService()
    
    @pytest.fixture
    def sample_document_content(self):
        return """
        Machine learning is a subset of artificial intelligence that focuses on algorithms
        that can learn from and make predictions on data. There are three main types of
        machine learning: supervised learning, unsupervised learning, and reinforcement learning.
        
        Supervised learning uses labeled training data to learn a mapping from inputs to outputs.
        Common supervised learning algorithms include linear regression, decision trees, and
        neural networks. The goal is to make accurate predictions on new, unseen data.
        
        Unsupervised learning finds patterns in data without labeled examples. Clustering
        and dimensionality reduction are common unsupervised learning tasks.
        """
    
    @pytest.mark.asyncio
    async def test_automatic_quiz_generation(self, quiz_service, sample_document_content):
        """Test automatic quiz generation from document content."""
        result = await quiz_service.generate_quiz_from_content(
            content=sample_document_content,
            num_questions=5,
            difficulty="medium"
        )
        
        assert result["success"] is True
        assert len(result["questions"]) == 5
        assert all(q["type"] in ["multiple_choice", "short_answer", "true_false"] 
                  for q in result["questions"])
        
        # Verify question quality
        for question in result["questions"]:
            assert len(question["question_text"]) > 10
            assert question["difficulty"] == "medium"
            if question["type"] == "multiple_choice":
                assert len(question["options"]) >= 3
                assert "correct_answer" in question
    
    @pytest.mark.asyncio
    async def test_multiple_choice_question_generation(self, quiz_service, sample_document_content):
        """Test generation of multiple choice questions with distractors."""
        result = await quiz_service.create_multiple_choice_questions(
            content=sample_document_content,
            num_questions=3
        )
        
        assert result["success"] is True
        assert len(result["questions"]) == 3
        
        for question in result["questions"]:
            assert question["type"] == "multiple_choice"
            assert len(question["options"]) == 4  # Standard 4 options
            assert question["correct_answer"] in ["A", "B", "C", "D"]
            
            # Verify distractors are plausible
            assert all(len(option) > 5 for option in question["options"])
    
    @pytest.mark.asyncio
    async def test_short_answer_question_generation(self, quiz_service, sample_document_content):
        """Test generation of short answer questions."""
        result = await quiz_service.create_short_answer_questions(
            content=sample_document_content,
            num_questions=3
        )
        
        assert result["success"] is True
        assert len(result["questions"]) == 3
        
        for question in result["questions"]:
            assert question["type"] == "short_answer"
            assert "expected_answer" in question
            assert "keywords" in question
            assert len(question["keywords"]) > 0
    
    @pytest.mark.asyncio
    async def test_essay_question_generation(self, quiz_service, sample_document_content):
        """Test generation of essay questions with rubrics."""
        result = await quiz_service.create_essay_questions(
            content=sample_document_content,
            num_questions=2
        )
        
        assert result["success"] is True
        assert len(result["questions"]) == 2
        
        for question in result["questions"]:
            assert question["type"] == "essay"
            assert "rubric" in question
            assert "key_points" in question
            assert len(question["key_points"]) >= 3
    
    @pytest.mark.asyncio
    async def test_difficulty_assessment(self, quiz_service, sample_document_content):
        """Test automatic difficulty assessment of generated questions."""
        difficulties = ["easy", "medium", "hard"]
        
        for difficulty in difficulties:
            result = await quiz_service.generate_quiz_from_content(
                content=sample_document_content,
                num_questions=3,
                difficulty=difficulty
            )
            
            assert result["success"] is True
            
            for question in result["questions"]:
                assert question["difficulty"] == difficulty
                
                # Verify difficulty-appropriate characteristics
                if difficulty == "easy":
                    assert question["cognitive_level"] in ["remember", "understand"]
                elif difficulty == "hard":
                    assert question["cognitive_level"] in ["analyze", "evaluate", "create"]
    
    @pytest.mark.asyncio
    async def test_quiz_evaluation_accuracy(self, quiz_service):
        """Test accuracy of quiz response evaluation."""
        quiz_responses = {
            "question_1": {
                "type": "multiple_choice",
                "user_answer": "B",
                "correct_answer": "B",
                "question": "What is machine learning?"
            },
            "question_2": {
                "type": "short_answer",
                "user_answer": "supervised learning uses labeled data",
                "expected_answer": "supervised learning uses labeled training data",
                "keywords": ["supervised", "labeled", "data"]
            },
            "question_3": {
                "type": "essay",
                "user_answer": "Machine learning has three types: supervised, unsupervised, and reinforcement learning. Each has different applications...",
                "key_points": ["three types", "supervised", "unsupervised", "reinforcement"],
                "rubric": {"content": 40, "organization": 30, "examples": 30}
            }
        }
        
        result = await quiz_service.evaluate_quiz_responses(quiz_responses)
        
        assert result["success"] is True
        assert result["overall_score"] > 0
        assert len(result["question_scores"]) == 3
        
        # Check individual question evaluation
        assert result["question_scores"]["question_1"]["score"] == 100  # Correct MC
        assert result["question_scores"]["question_2"]["score"] > 80   # Good short answer
        assert result["question_scores"]["question_3"]["score"] > 70   # Decent essay


class TestSpacedRepetitionSystem:
    """Test suite for spaced repetition algorithm and scheduling."""
    
    @pytest.fixture
    def spaced_repetition_service(self):
        return SpacedRepetitionService()
    
    @pytest.fixture
    def sample_study_items(self):
        return [
            {
                "id": "item1",
                "content": "What is supervised learning?",
                "answer": "Learning with labeled training data",
                "difficulty": 2.5,
                "last_reviewed": datetime.now() - timedelta(days=1),
                "review_count": 3,
                "success_rate": 0.8
            },
            {
                "id": "item2",
                "content": "Define neural networks",
                "answer": "Networks inspired by biological neural networks",
                "difficulty": 3.2,
                "last_reviewed": datetime.now() - timedelta(days=3),
                "review_count": 1,
                "success_rate": 0.5
            }
        ]
    
    @pytest.mark.asyncio
    async def test_supermemo_algorithm_implementation(self, spaced_repetition_service, sample_study_items):
        """Test SuperMemo-based spaced repetition algorithm."""
        for item in sample_study_items:
            # Simulate correct response
            performance = {"correct": True, "response_time": 5.2, "confidence": 0.8}
            
            result = await spaced_repetition_service.calculate_next_review_date(item, performance)
            
            assert result["next_review_date"] > datetime.now()
            assert result["interval_days"] > 0
            assert result["easiness_factor"] > 1.0
            
            # Verify interval increases for correct responses
            if item["success_rate"] > 0.7:
                assert result["interval_days"] >= item.get("last_interval", 1)
    
    @pytest.mark.asyncio
    async def test_adaptive_difficulty_adjustment(self, spaced_repetition_service):
        """Test adaptive difficulty adjustment based on performance."""
        study_item = {
            "id": "adaptive_item",
            "difficulty": 2.5,
            "performance_history": [
                {"correct": True, "response_time": 3.0},
                {"correct": True, "response_time": 2.5},
                {"correct": False, "response_time": 8.0},
                {"correct": True, "response_time": 4.0}
            ]
        }
        
        result = await spaced_repetition_service.adjust_difficulty_based_on_performance(study_item)
        
        assert result["adjusted"] is True
        assert "new_difficulty" in result
        assert result["adjustment_reason"] is not None
        
        # Difficulty should adjust based on recent performance
        recent_success_rate = 0.75  # 3 out of 4 correct
        if recent_success_rate > 0.8:
            assert result["new_difficulty"] < study_item["difficulty"]
        elif recent_success_rate < 0.6:
            assert result["new_difficulty"] > study_item["difficulty"]
    
    @pytest.mark.asyncio
    async def test_personalized_study_schedule_generation(self, spaced_repetition_service):
        """Test generation of personalized study schedules."""
        user_goals = {
            "daily_study_time": 30,  # minutes
            "target_retention": 0.85,
            "preferred_times": ["09:00", "14:00", "19:00"],
            "difficulty_preference": "adaptive"
        }
        
        study_items = [
            {"id": f"item_{i}", "difficulty": 2.0 + i * 0.5, "priority": i % 3}
            for i in range(10)
        ]
        
        result = await spaced_repetition_service.generate_study_schedule(user_goals, study_items)
        
        assert result["success"] is True
        assert len(result["schedule"]) > 0
        assert result["estimated_daily_time"] <= user_goals["daily_study_time"]
        
        # Verify schedule optimization
        for session in result["schedule"]:
            assert session["time"] in user_goals["preferred_times"]
            assert len(session["items"]) > 0
            assert session["estimated_duration"] <= user_goals["daily_study_time"]
    
    @pytest.mark.asyncio
    async def test_retention_rate_tracking(self, spaced_repetition_service):
        """Test tracking and analysis of retention rates."""
        user_id = "test_user_123"
        
        # Simulate study sessions over time
        study_sessions = [
            {
                "date": datetime.now() - timedelta(days=7),
                "items_reviewed": 10,
                "items_correct": 8,
                "average_response_time": 4.5
            },
            {
                "date": datetime.now() - timedelta(days=3),
                "items_reviewed": 12,
                "items_correct": 10,
                "average_response_time": 3.8
            },
            {
                "date": datetime.now() - timedelta(days=1),
                "items_reviewed": 8,
                "items_correct": 7,
                "average_response_time": 3.2
            }
        ]
        
        result = await spaced_repetition_service.track_learning_progress(user_id, study_sessions)
        
        assert result["success"] is True
        assert "retention_rate" in result
        assert "improvement_trend" in result
        assert result["retention_rate"] > 0.7  # Good retention
        
        # Check trend analysis
        assert result["improvement_trend"] in ["improving", "stable", "declining"]


class TestLearningProgressTracking:
    """Test suite for learning progress tracking and analytics."""
    
    @pytest.fixture
    def learning_progress_service(self):
        return LearningProgressService()
    
    @pytest.mark.asyncio
    async def test_comprehensive_learning_analytics(self, learning_progress_service):
        """Test comprehensive learning analytics and metrics."""
        user_id = "test_user_123"
        
        learning_data = {
            "study_sessions": 25,
            "total_study_time": 1200,  # minutes
            "topics_covered": ["machine_learning", "neural_networks", "deep_learning"],
            "quiz_scores": [85, 78, 92, 88, 90],
            "difficulty_progression": [2.0, 2.3, 2.8, 3.1, 3.2]
        }
        
        result = await learning_progress_service.generate_learning_analytics(user_id, learning_data)
        
        assert result["success"] is True
        assert "average_score" in result
        assert "learning_velocity" in result
        assert "knowledge_gaps" in result
        assert "recommendations" in result
        
        # Verify analytics accuracy
        expected_avg_score = sum(learning_data["quiz_scores"]) / len(learning_data["quiz_scores"])
        assert abs(result["average_score"] - expected_avg_score) < 1.0
    
    @pytest.mark.asyncio
    async def test_knowledge_gap_identification(self, learning_progress_service):
        """Test identification of knowledge gaps and targeted recommendations."""
        user_performance = {
            "topics": {
                "supervised_learning": {"score": 90, "confidence": 0.9},
                "unsupervised_learning": {"score": 65, "confidence": 0.6},
                "reinforcement_learning": {"score": 45, "confidence": 0.4},
                "neural_networks": {"score": 85, "confidence": 0.8}
            }
        }
        
        result = await learning_progress_service.identify_knowledge_gaps(user_performance)
        
        assert result["success"] is True
        assert len(result["knowledge_gaps"]) > 0
        
        # Should identify reinforcement learning as a major gap
        gap_topics = [gap["topic"] for gap in result["knowledge_gaps"]]
        assert "reinforcement_learning" in gap_topics
        
        # Should provide targeted recommendations
        for gap in result["knowledge_gaps"]:
            assert "recommendations" in gap
            assert len(gap["recommendations"]) > 0
    
    @pytest.mark.asyncio
    async def test_learning_trajectory_visualization(self, learning_progress_service):
        """Test learning trajectory visualization data generation."""
        user_id = "test_user_123"
        
        # Simulate learning progress over time
        progress_data = [
            {"date": "2023-01-01", "score": 60, "topics": ["basics"]},
            {"date": "2023-01-15", "score": 70, "topics": ["basics", "intermediate"]},
            {"date": "2023-02-01", "score": 78, "topics": ["intermediate"]},
            {"date": "2023-02-15", "score": 85, "topics": ["intermediate", "advanced"]},
            {"date": "2023-03-01", "score": 88, "topics": ["advanced"]}
        ]
        
        result = await learning_progress_service.generate_trajectory_visualization(user_id, progress_data)
        
        assert result["success"] is True
        assert "trajectory_data" in result
        assert "trend_analysis" in result
        assert "milestones" in result
        
        # Verify upward trend
        assert result["trend_analysis"]["direction"] == "upward"
        assert result["trend_analysis"]["slope"] > 0
    
    @pytest.mark.asyncio
    async def test_competency_mapping(self, learning_progress_service):
        """Test competency mapping and skill development tracking."""
        user_skills = {
            "machine_learning_fundamentals": {
                "current_level": 3,
                "target_level": 4,
                "evidence": ["quiz_scores", "project_completion"],
                "last_assessed": datetime.now() - timedelta(days=7)
            },
            "data_preprocessing": {
                "current_level": 4,
                "target_level": 5,
                "evidence": ["practical_exercises", "peer_review"],
                "last_assessed": datetime.now() - timedelta(days=3)
            }
        }
        
        result = await learning_progress_service.map_competencies(user_skills)
        
        assert result["success"] is True
        assert "competency_map" in result
        assert "development_plan" in result
        
        for skill, data in result["competency_map"].items():
            assert "current_level" in data
            assert "progress_to_target" in data
            assert "next_steps" in data


class TestGamificationFeatures:
    """Test suite for gamification and personalization features."""
    
    @pytest.fixture
    def gamification_service(self):
        return GamificationService()
    
    @pytest.mark.asyncio
    async def test_achievement_system(self, gamification_service):
        """Test achievement system with badges and progress rewards."""
        user_id = "test_user_123"
        
        # Simulate user activities
        activities = [
            {"type": "quiz_completed", "score": 90, "topic": "machine_learning"},
            {"type": "study_streak", "days": 7},
            {"type": "topic_mastered", "topic": "neural_networks", "mastery_level": 0.9},
            {"type": "peer_help", "helped_users": 3}
        ]
        
        for activity in activities:
            result = await gamification_service.process_achievement(user_id, activity)
            
            assert result["processed"] is True
            if result["achievement_unlocked"]:
                assert "badge" in result
                assert "points_earned" in result
                assert result["points_earned"] > 0
    
    @pytest.mark.asyncio
    async def test_personalized_study_recommendations(self, gamification_service):
        """Test personalized study recommendations based on learning patterns."""
        user_profile = {
            "learning_style": "visual",
            "preferred_difficulty": "medium",
            "study_time_preference": "morning",
            "interests": ["machine_learning", "data_science"],
            "performance_history": {
                "strong_areas": ["supervised_learning"],
                "weak_areas": ["unsupervised_learning"],
                "learning_pace": "moderate"
            }
        }
        
        result = await gamification_service.generate_personalized_recommendations(user_profile)
        
        assert result["success"] is True
        assert "study_recommendations" in result
        assert "content_suggestions" in result
        assert "schedule_optimization" in result
        
        # Verify personalization
        recommendations = result["study_recommendations"]
        assert any("visual" in rec["format"] for rec in recommendations)
        assert any("unsupervised_learning" in rec["topic"] for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_social_learning_features(self, gamification_service):
        """Test social learning features with peer comparison and collaboration."""
        user_id = "test_user_123"
        peer_group = ["user_456", "user_789", "user_101"]
        
        # Test peer comparison
        comparison_result = await gamification_service.generate_peer_comparison(user_id, peer_group)
        
        assert comparison_result["success"] is True
        assert "ranking" in comparison_result
        assert "peer_stats" in comparison_result
        assert "collaboration_opportunities" in comparison_result
        
        # Test study group formation
        study_group_result = await gamification_service.suggest_study_groups(user_id)
        
        assert study_group_result["success"] is True
        assert "suggested_groups" in study_group_result
        assert len(study_group_result["suggested_groups"]) > 0
    
    @pytest.mark.asyncio
    async def test_adaptive_content_difficulty(self, gamification_service):
        """Test adaptive content difficulty based on individual learning curves."""
        user_id = "test_user_123"
        
        learning_curve_data = {
            "initial_performance": 0.6,
            "current_performance": 0.8,
            "learning_rate": 0.05,
            "plateau_detection": False,
            "challenge_preference": "moderate"
        }
        
        result = await gamification_service.adapt_content_difficulty(user_id, learning_curve_data)
        
        assert result["adapted"] is True
        assert "new_difficulty_level" in result
        assert "adaptation_reason" in result
        
        # Verify appropriate difficulty adjustment
        if learning_curve_data["current_performance"] > 0.85:
            assert result["new_difficulty_level"] > learning_curve_data.get("current_difficulty", 2.5)
        elif learning_curve_data["current_performance"] < 0.65:
            assert result["new_difficulty_level"] < learning_curve_data.get("current_difficulty", 2.5)


class TestLearningOutcomeValidation:
    """Test suite for learning outcome validation and assessment."""
    
    @pytest.fixture
    def learning_progress_service(self):
        return LearningProgressService()
    
    @pytest.mark.asyncio
    async def test_learning_objective_achievement(self, learning_progress_service):
        """Test validation of learning objective achievement."""
        learning_objectives = [
            {
                "id": "obj1",
                "description": "Understand supervised learning concepts",
                "success_criteria": {
                    "quiz_score_threshold": 80,
                    "practical_application": True,
                    "concept_explanation": True
                }
            },
            {
                "id": "obj2",
                "description": "Apply neural network algorithms",
                "success_criteria": {
                    "implementation_project": True,
                    "performance_benchmark": 0.85,
                    "peer_review_score": 4.0
                }
            }
        ]
        
        user_evidence = {
            "obj1": {
                "quiz_scores": [85, 88, 82],
                "practical_application": True,
                "concept_explanation": True
            },
            "obj2": {
                "implementation_project": True,
                "performance_benchmark": 0.87,
                "peer_review_score": 4.2
            }
        }
        
        result = await learning_progress_service.validate_learning_outcomes(
            learning_objectives, user_evidence
        )
        
        assert result["success"] is True
        assert result["objectives_achieved"] == 2
        assert all(obj["achieved"] for obj in result["objective_results"])
    
    @pytest.mark.asyncio
    async def test_skill_transfer_assessment(self, learning_progress_service):
        """Test assessment of skill transfer to new contexts."""
        base_skills = ["linear_regression", "data_preprocessing", "model_evaluation"]
        transfer_contexts = [
            {"context": "medical_diagnosis", "similarity": 0.7},
            {"context": "financial_prediction", "similarity": 0.8},
            {"context": "image_classification", "similarity": 0.4}
        ]
        
        result = await learning_progress_service.assess_skill_transfer(base_skills, transfer_contexts)
        
        assert result["success"] is True
        assert "transfer_predictions" in result
        assert "recommended_contexts" in result
        
        # Higher similarity contexts should have better transfer predictions
        high_sim_contexts = [ctx for ctx in transfer_contexts if ctx["similarity"] > 0.7]
        for ctx in high_sim_contexts:
            transfer_pred = next(
                pred for pred in result["transfer_predictions"] 
                if pred["context"] == ctx["context"]
            )
            assert transfer_pred["transfer_likelihood"] > 0.7
    
    @pytest.mark.asyncio
    async def test_long_term_retention_validation(self, learning_progress_service):
        """Test validation of long-term knowledge retention."""
        user_id = "test_user_123"
        
        # Simulate learning and retention data over time
        retention_data = {
            "initial_learning": {
                "date": datetime.now() - timedelta(days=90),
                "topics": ["supervised_learning", "neural_networks"],
                "initial_scores": [85, 78]
            },
            "retention_tests": [
                {
                    "date": datetime.now() - timedelta(days=60),
                    "scores": [80, 75]  # Slight decline
                },
                {
                    "date": datetime.now() - timedelta(days=30),
                    "scores": [82, 77]  # Slight recovery
                },
                {
                    "date": datetime.now() - timedelta(days=7),
                    "scores": [84, 79]  # Good retention
                }
            ]
        }
        
        result = await learning_progress_service.validate_long_term_retention(user_id, retention_data)
        
        assert result["success"] is True
        assert "retention_rate" in result
        assert "forgetting_curve" in result
        assert "intervention_needed" in result
        
        # Good retention should be detected
        assert result["retention_rate"] > 0.8
        assert result["intervention_needed"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])