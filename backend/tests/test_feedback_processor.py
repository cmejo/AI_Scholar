"""
Tests for Feedback Processing System
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from services.feedback_processor import FeedbackProcessor, FeedbackAnalyzer, FeedbackLoop
from models.schemas import FeedbackType, UserFeedbackCreate
from core.database import UserFeedback, User, Message, UserProfile, AnalyticsEvent

class TestFeedbackProcessor:
    """Test cases for FeedbackProcessor class."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def feedback_processor(self, mock_db):
        """Create FeedbackProcessor instance with mocked dependencies."""
        processor = FeedbackProcessor(mock_db)
        processor.profile_manager = AsyncMock()
        processor.interaction_tracker = AsyncMock()
        return processor
    
    @pytest.mark.asyncio
    async def test_process_thumbs_feedback_positive(self, feedback_processor, mock_db):
        """Test processing positive thumbs feedback."""
        # Setup
        user_id = "test-user-123"
        message_id = "test-message-456"
        
        # Mock database operations
        mock_feedback = UserFeedback(
            id="feedback-123",
            user_id=user_id,
            message_id=message_id,
            feedback_type="rating",
            feedback_value={"rating": 1.0, "feedback_method": "thumbs"},
            processed=False,
            created_at=datetime.utcnow()
        )
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_feedback
        
        # Execute
        result = await feedback_processor.process_thumbs_feedback(
            user_id=user_id,
            message_id=message_id,
            is_positive=True
        )
        
        # Verify
        assert result.user_id == user_id
        assert result.message_id == message_id
        assert result.feedback_type == "rating"
        assert result.feedback_value["rating"] == 1.0
        assert result.feedback_value["feedback_method"] == "thumbs"
        
        # Verify interaction tracking was called
        feedback_processor.interaction_tracker.track_feedback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_thumbs_feedback_negative(self, feedback_processor, mock_db):
        """Test processing negative thumbs feedback."""
        # Setup
        user_id = "test-user-123"
        message_id = "test-message-456"
        
        # Mock database operations
        mock_feedback = UserFeedback(
            id="feedback-123",
            user_id=user_id,
            message_id=message_id,
            feedback_type="rating",
            feedback_value={"rating": 0.0, "feedback_method": "thumbs"},
            processed=False,
            created_at=datetime.utcnow()
        )
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_feedback
        
        # Execute
        result = await feedback_processor.process_thumbs_feedback(
            user_id=user_id,
            message_id=message_id,
            is_positive=False
        )
        
        # Verify
        assert result.feedback_value["rating"] == 0.0
        assert result.feedback_value["feedback_method"] == "thumbs"
    
    @pytest.mark.asyncio
    async def test_process_detailed_rating(self, feedback_processor, mock_db):
        """Test processing detailed rating feedback."""
        # Setup
        user_id = "test-user-123"
        message_id = "test-message-456"
        rating = 0.8
        aspects = {
            "accuracy": 0.9,
            "relevance": 0.7,
            "completeness": 0.8,
            "clarity": 0.9
        }
        comment = "Great response, very helpful!"
        
        # Mock database operations
        mock_feedback = UserFeedback(
            id="feedback-123",
            user_id=user_id,
            message_id=message_id,
            feedback_type="rating",
            feedback_value={
                "rating": rating,
                "aspects": aspects,
                "comment": comment,
                "feedback_method": "detailed"
            },
            processed=False,
            created_at=datetime.utcnow()
        )
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_feedback
        
        # Execute
        result = await feedback_processor.process_detailed_rating(
            user_id=user_id,
            message_id=message_id,
            rating=rating,
            aspects=aspects,
            comment=comment
        )
        
        # Verify
        assert result.feedback_value["rating"] == rating
        assert result.feedback_value["aspects"] == aspects
        assert result.feedback_value["comment"] == comment
        assert result.feedback_value["feedback_method"] == "detailed"
    
    @pytest.mark.asyncio
    async def test_process_correction_feedback(self, feedback_processor, mock_db):
        """Test processing correction feedback."""
        # Setup
        user_id = "test-user-123"
        message_id = "test-message-456"
        feedback_value = {
            "correction": "The correct answer is X, not Y",
            "original": "The answer is Y",
            "type": "factual"
        }
        
        # Mock database operations
        mock_feedback = UserFeedback(
            id="feedback-123",
            user_id=user_id,
            message_id=message_id,
            feedback_type="correction",
            feedback_value=feedback_value,
            processed=False,
            created_at=datetime.utcnow()
        )
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_feedback
        
        # Execute
        result = await feedback_processor.process_feedback(
            user_id=user_id,
            feedback_type=FeedbackType.CORRECTION,
            feedback_value=feedback_value,
            message_id=message_id
        )
        
        # Verify
        assert result.feedback_type == "correction"
        assert result.feedback_value["correction"] == feedback_value["correction"]
        assert result.feedback_value["type"] == "factual"
    
    @pytest.mark.asyncio
    async def test_process_preference_feedback(self, feedback_processor, mock_db):
        """Test processing preference feedback."""
        # Setup
        user_id = "test-user-123"
        feedback_value = {
            "type": "response_style",
            "value": "concise",
            "strength": 0.8
        }
        
        # Mock user profile
        feedback_processor.profile_manager.get_user_profile.return_value = Mock(
            user_id=user_id,
            preferences={"response_style": "detailed"}
        )
        
        # Mock database operations
        mock_feedback = UserFeedback(
            id="feedback-123",
            user_id=user_id,
            message_id=None,
            feedback_type="preference",
            feedback_value=feedback_value,
            processed=False,
            created_at=datetime.utcnow()
        )
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_feedback
        
        # Execute
        result = await feedback_processor.process_feedback(
            user_id=user_id,
            feedback_type=FeedbackType.PREFERENCE,
            feedback_value=feedback_value
        )
        
        # Verify
        assert result.feedback_type == "preference"
        assert result.feedback_value["type"] == "response_style"
        assert result.feedback_value["value"] == "concise"
    
    @pytest.mark.asyncio
    async def test_process_relevance_feedback(self, feedback_processor, mock_db):
        """Test processing relevance feedback."""
        # Setup
        user_id = "test-user-123"
        message_id = "test-message-456"
        feedback_value = {
            "relevance": 0.6,
            "sources": {
                "source-1": 0.8,
                "source-2": 0.4
            },
            "query": "What is machine learning?"
        }
        
        # Mock database operations
        mock_feedback = UserFeedback(
            id="feedback-123",
            user_id=user_id,
            message_id=message_id,
            feedback_type="relevance",
            feedback_value=feedback_value,
            processed=False,
            created_at=datetime.utcnow()
        )
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_feedback
        
        # Execute
        result = await feedback_processor.process_feedback(
            user_id=user_id,
            feedback_type=FeedbackType.RELEVANCE,
            feedback_value=feedback_value,
            message_id=message_id
        )
        
        # Verify
        assert result.feedback_type == "relevance"
        assert result.feedback_value["relevance"] == 0.6
        assert result.feedback_value["sources"]["source-1"] == 0.8
    
    @pytest.mark.asyncio
    async def test_update_user_satisfaction(self, feedback_processor, mock_db):
        """Test updating user satisfaction metrics."""
        # Setup
        user_id = "test-user-123"
        rating = 0.8
        aspects = {"accuracy": 0.9, "relevance": 0.7}
        
        # Mock user profile
        mock_profile = Mock()
        mock_profile.user_id = user_id
        mock_profile.interaction_history = {
            "satisfaction_history": [
                {"timestamp": "2024-01-01T00:00:00", "overall_rating": 0.7, "aspects": {}}
            ]
        }
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_profile
        mock_db.commit.return_value = None
        
        # Execute
        await feedback_processor._update_user_satisfaction(user_id, rating, aspects)
        
        # Verify
        mock_db.commit.assert_called_once()
        assert mock_profile.interaction_history["avg_satisfaction"] == 0.75  # Average of 0.7 and 0.8
    
    @pytest.mark.asyncio
    async def test_analyze_message_feedback_poor_performance(self, feedback_processor, mock_db):
        """Test analyzing message feedback for poor performance."""
        # Setup
        user_id = "test-user-123"
        message_id = "test-message-456"
        rating = 0.3
        aspects = {"accuracy": 0.2, "relevance": 0.4}
        
        # Mock message
        mock_message = Mock()
        mock_message.id = message_id
        mock_message.content = "Test response content"
        mock_message.sources = json.dumps([{"document_id": "doc-1", "relevance": 0.5}])
        mock_message.message_metadata = "{}"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_message
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        
        # Execute
        await feedback_processor._analyze_message_feedback(user_id, message_id, rating, aspects, None)
        
        # Verify
        mock_db.commit.assert_called()
        # Verify analytics event was added
        mock_db.add.assert_called()
    
    @pytest.mark.asyncio
    async def test_analyze_message_feedback_excellent_performance(self, feedback_processor, mock_db):
        """Test analyzing message feedback for excellent performance."""
        # Setup
        user_id = "test-user-123"
        message_id = "test-message-456"
        rating = 0.9
        aspects = {"accuracy": 0.9, "relevance": 0.9, "clarity": 0.8}
        
        # Mock message
        mock_message = Mock()
        mock_message.id = message_id
        mock_message.content = "Excellent response content"
        mock_message.sources = json.dumps([{"document_id": "doc-1", "relevance": 0.9}])
        mock_message.message_metadata = "{}"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_message
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        
        # Execute
        await feedback_processor._analyze_message_feedback(user_id, message_id, rating, aspects, None)
        
        # Verify
        mock_db.commit.assert_called()
        # Verify analytics event was added for excellent performance
        mock_db.add.assert_called()
    
    @pytest.mark.asyncio
    async def test_error_handling_in_process_feedback(self, feedback_processor, mock_db):
        """Test error handling in feedback processing."""
        # Setup
        user_id = "test-user-123"
        feedback_value = {"rating": 0.8}
        
        # Mock database error
        mock_db.add.side_effect = Exception("Database error")
        mock_db.rollback.return_value = None
        
        # Execute and verify exception is raised
        with pytest.raises(Exception, match="Database error"):
            await feedback_processor.process_feedback(
                user_id=user_id,
                feedback_type=FeedbackType.RATING,
                feedback_value=feedback_value
            )
        
        # Verify rollback was called
        mock_db.rollback.assert_called_once()

class TestFeedbackAnalyzer:
    """Test cases for FeedbackAnalyzer class."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def feedback_analyzer(self, mock_db):
        """Create FeedbackAnalyzer instance."""
        return FeedbackAnalyzer(mock_db)
    
    @pytest.mark.asyncio
    async def test_analyze_feedback_trends_with_data(self, feedback_analyzer, mock_db):
        """Test analyzing feedback trends with available data."""
        # Setup mock feedback records
        mock_feedback_records = [
            Mock(
                feedback_type="rating",
                feedback_value={"rating": 0.8},
                created_at=datetime.utcnow() - timedelta(days=1)
            ),
            Mock(
                feedback_type="rating",
                feedback_value={"rating": 0.6},
                created_at=datetime.utcnow() - timedelta(days=2)
            ),
            Mock(
                feedback_type="correction",
                feedback_value={"correction": "Fix this"},
                created_at=datetime.utcnow() - timedelta(days=3)
            )
        ]
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_feedback_records
        mock_db.query.return_value = mock_query
        
        # Execute
        result = await feedback_analyzer.analyze_feedback_trends(
            user_id="test-user-123",
            time_range=7
        )
        
        # Verify
        assert result["total_feedback"] == 3
        assert result["time_range_days"] == 7
        assert "feedback_by_type" in result
        assert "rating_trends" in result
        assert result["feedback_by_type"]["distribution"]["rating"] == 2
        assert result["feedback_by_type"]["distribution"]["correction"] == 1
        assert result["rating_trends"]["average_rating"] == 0.7  # (0.8 + 0.6) / 2
    
    @pytest.mark.asyncio
    async def test_analyze_feedback_trends_no_data(self, feedback_analyzer, mock_db):
        """Test analyzing feedback trends with no data."""
        # Setup empty query result
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # Execute
        result = await feedback_analyzer.analyze_feedback_trends()
        
        # Verify
        assert "message" in result
        assert "No feedback data available" in result["message"]
    
    def test_analyze_by_type(self, feedback_analyzer):
        """Test analyzing feedback distribution by type."""
        # Setup mock feedback records
        mock_records = [
            Mock(feedback_type="rating"),
            Mock(feedback_type="rating"),
            Mock(feedback_type="correction"),
            Mock(feedback_type="preference")
        ]
        
        # Execute
        result = feedback_analyzer._analyze_by_type(mock_records)
        
        # Verify
        assert result["distribution"]["rating"] == 2
        assert result["distribution"]["correction"] == 1
        assert result["distribution"]["preference"] == 1
        assert result["most_common"][0] == "rating"
        assert result["most_common"][1] == 2
    
    def test_analyze_rating_trends(self, feedback_analyzer):
        """Test analyzing rating trends."""
        # Setup mock feedback records
        mock_records = [
            Mock(feedback_type="rating", feedback_value={"rating": 0.9}),
            Mock(feedback_type="rating", feedback_value={"rating": 0.7}),
            Mock(feedback_type="rating", feedback_value={"rating": 0.3}),
            Mock(feedback_type="correction", feedback_value={"correction": "test"})
        ]
        
        # Execute
        result = feedback_analyzer._analyze_rating_trends(mock_records)
        
        # Verify
        assert result["average_rating"] == pytest.approx(0.633, rel=1e-2)
        assert result["rating_count"] == 3
        assert result["rating_distribution"]["excellent"] == 1  # > 0.8
        assert result["rating_distribution"]["good"] == 1  # 0.6 < r <= 0.8
        assert result["rating_distribution"]["poor"] == 1  # <= 0.4

class TestFeedbackLoop:
    """Test cases for FeedbackLoop class."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def feedback_loop(self, mock_db):
        """Create FeedbackLoop instance with mocked dependencies."""
        loop = FeedbackLoop(mock_db)
        loop.feedback_analyzer = AsyncMock()
        loop.feedback_processor = AsyncMock()
        return loop
    
    @pytest.mark.asyncio
    async def test_run_improvement_cycle(self, feedback_loop):
        """Test running a complete improvement cycle."""
        # Setup mock analysis results
        mock_analysis = {
            "total_feedback": 50,
            "rating_trends": {"average_rating": 0.7},
            "improvement_areas": ["accuracy", "relevance"]
        }
        
        feedback_loop.feedback_analyzer.analyze_feedback_trends.return_value = mock_analysis
        feedback_loop._identify_improvements = AsyncMock(return_value=[
            {"type": "accuracy_improvement", "priority": "high"},
            {"type": "relevance_improvement", "priority": "medium"}
        ])
        feedback_loop._apply_improvements = AsyncMock(return_value=[
            {"type": "accuracy_improvement", "status": "applied"},
            {"type": "relevance_improvement", "status": "applied"}
        ])
        feedback_loop._log_improvement_cycle = AsyncMock()
        
        # Execute
        result = await feedback_loop.run_improvement_cycle()
        
        # Verify
        assert "feedback_analysis" in result
        assert result["improvements_identified"] == 2
        assert result["improvements_applied"] == 2
        assert "cycle_timestamp" in result
        
        # Verify methods were called
        feedback_loop.feedback_analyzer.analyze_feedback_trends.assert_called_once_with(time_range=7)
        feedback_loop._identify_improvements.assert_called_once()
        feedback_loop._apply_improvements.assert_called_once()
        feedback_loop._log_improvement_cycle.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_improvement_cycle_error_handling(self, feedback_loop):
        """Test error handling in improvement cycle."""
        # Setup error in analysis
        feedback_loop.feedback_analyzer.analyze_feedback_trends.side_effect = Exception("Analysis error")
        
        # Execute
        result = await feedback_loop.run_improvement_cycle()
        
        # Verify error handling
        assert "error" in result
        assert "Analysis error" in result["error"]

class TestIntegration:
    """Integration tests for feedback processing system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_feedback_processing(self):
        """Test complete feedback processing workflow."""
        # This would be an integration test with real database
        # For now, we'll create a placeholder
        pass
    
    @pytest.mark.asyncio
    async def test_feedback_impact_on_user_profile(self):
        """Test that feedback properly impacts user profile."""
        # This would test the integration between feedback processor and user profile service
        pass
    
    @pytest.mark.asyncio
    async def test_feedback_impact_on_retrieval(self):
        """Test that feedback impacts retrieval system."""
        # This would test the integration between feedback processor and adaptive retrieval
        pass

if __name__ == "__main__":
    pytest.main([__file__])