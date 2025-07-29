"""
Tests for Enhanced Analytics Service
"""
import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base, AnalyticsEvent, User, Document, UserProfile, UserFeedback, DocumentTag
from services.analytics_service import (
    EnhancedAnalyticsService, EventType, QueryMetrics, DocumentMetrics,
    UserBehaviorMetrics, PerformanceMetrics, AnalyticsInsights
)

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_analytics.db"
test_engine = create_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def analytics_service(db_session):
    """Create analytics service with test database"""
    return EnhancedAnalyticsService(db_session)

@pytest.fixture
def sample_user(db_session):
    """Create sample user for testing"""
    user = User(
        id="test-user-1",
        email="test@example.com",
        name="Test User",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def sample_document(db_session, sample_user):
    """Create sample document for testing"""
    document = Document(
        id="test-doc-1",
        user_id=sample_user.id,
        name="Test Document",
        file_path="/test/path",
        content_type="application/pdf",
        size=1024,
        status="completed"
    )
    db_session.add(document)
    db_session.commit()
    return document

@pytest.fixture
def sample_analytics_events(db_session, sample_user, sample_document):
    """Create sample analytics events for testing"""
    events = []
    base_time = datetime.utcnow() - timedelta(days=7)
    
    # Query events
    for i in range(10):
        event = AnalyticsEvent(
            user_id=sample_user.id,
            event_type=EventType.QUERY_EXECUTED,
            event_data={
                "query": f"test query {i}",
                "response_time": 2.5 + (i * 0.1),
                "success": True,
                "complexity": "medium"
            },
            timestamp=base_time + timedelta(hours=i),
            session_id=f"session-{i // 3}"
        )
        events.append(event)
        db_session.add(event)
    
    # Document access events
    for i in range(5):
        event = AnalyticsEvent(
            user_id=sample_user.id,
            event_type=EventType.DOCUMENT_ACCESSED,
            event_data={
                "document_id": sample_document.id,
                "access_type": "view"
            },
            timestamp=base_time + timedelta(hours=i * 2),
            session_id=f"session-{i}"
        )
        events.append(event)
        db_session.add(event)
    
    # Performance events
    for i in range(3):
        event = AnalyticsEvent(
            user_id=sample_user.id,
            event_type=EventType.PERFORMANCE_METRIC,
            event_data={
                "memory_usage": {"heap": 100 + i * 10, "stack": 50 + i * 5},
                "cache_hit_rate": 0.8 + (i * 0.05),
                "db_query_time": 0.1 + (i * 0.02)
            },
            timestamp=base_time + timedelta(hours=i * 4),
            session_id=f"session-{i}"
        )
        events.append(event)
        db_session.add(event)
    
    # Session events
    for i in range(3):
        start_event = AnalyticsEvent(
            user_id=sample_user.id,
            event_type=EventType.USER_SESSION_START,
            event_data={},
            timestamp=base_time + timedelta(hours=i * 8),
            session_id=f"session-{i}"
        )
        end_event = AnalyticsEvent(
            user_id=sample_user.id,
            event_type=EventType.USER_SESSION_END,
            event_data={},
            timestamp=base_time + timedelta(hours=i * 8, minutes=30),
            session_id=f"session-{i}"
        )
        events.extend([start_event, end_event])
        db_session.add(start_event)
        db_session.add(end_event)
    
    db_session.commit()
    return events

class TestEnhancedAnalyticsService:
    """Test cases for Enhanced Analytics Service"""
    
    @pytest.mark.asyncio
    async def test_track_event(self, analytics_service, sample_user):
        """Test event tracking functionality"""
        event_data = {
            "query": "test query",
            "response_time": 1.5,
            "success": True
        }
        
        event_id = await analytics_service.track_event(
            event_type=EventType.QUERY_EXECUTED,
            user_id=sample_user.id,
            event_data=event_data,
            session_id="test-session"
        )
        
        assert event_id is not None
        
        # Verify event was stored
        stored_event = analytics_service.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.id == event_id
        ).first()
        
        assert stored_event is not None
        assert stored_event.user_id == sample_user.id
        assert stored_event.event_type == EventType.QUERY_EXECUTED
        assert stored_event.event_data == event_data
        assert stored_event.session_id == "test-session"

    @pytest.mark.asyncio
    async def test_get_query_metrics(self, analytics_service, sample_analytics_events, sample_user):
        """Test query metrics calculation"""
        metrics = await analytics_service.get_query_metrics(user_id=sample_user.id)
        
        assert isinstance(metrics, QueryMetrics)
        assert metrics.total_queries == 10
        assert metrics.avg_response_time > 0
        assert metrics.success_rate == 1.0  # All test queries are successful
        assert len(metrics.most_common_queries) > 0
        assert len(metrics.peak_usage_hours) > 0
        assert "medium" in metrics.query_complexity_distribution

    @pytest.mark.asyncio
    async def test_get_document_metrics(self, analytics_service, sample_analytics_events, sample_user, sample_document):
        """Test document metrics calculation"""
        metrics = await analytics_service.get_document_metrics(user_id=sample_user.id)
        
        assert isinstance(metrics, DocumentMetrics)
        assert metrics.total_documents >= 1
        assert len(metrics.most_accessed_documents) > 0
        assert sample_document.id in [doc[0] for doc in metrics.most_accessed_documents]
        assert metrics.avg_document_size > 0
        assert "application/pdf" in metrics.document_type_distribution

    @pytest.mark.asyncio
    async def test_get_user_behavior_metrics(self, analytics_service, sample_analytics_events):
        """Test user behavior metrics calculation"""
        metrics = await analytics_service.get_user_behavior_metrics()
        
        assert isinstance(metrics, UserBehaviorMetrics)
        assert metrics.active_users >= 1
        assert metrics.avg_session_duration > 0  # Should have session duration from test data
        assert len(metrics.feature_usage) > 0
        assert EventType.QUERY_EXECUTED in metrics.feature_usage

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, analytics_service, sample_analytics_events):
        """Test performance metrics calculation"""
        metrics = await analytics_service.get_performance_metrics()
        
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.avg_response_time > 0
        assert metrics.error_rate >= 0
        assert metrics.throughput >= 0
        assert metrics.cache_hit_rate >= 0

    @pytest.mark.asyncio
    async def test_get_comprehensive_insights(self, analytics_service, sample_analytics_events, sample_user):
        """Test comprehensive insights generation"""
        insights = await analytics_service.get_comprehensive_insights(user_id=sample_user.id)
        
        assert isinstance(insights, AnalyticsInsights)
        assert isinstance(insights.query_metrics, QueryMetrics)
        assert isinstance(insights.document_metrics, DocumentMetrics)
        assert isinstance(insights.user_behavior, UserBehaviorMetrics)
        assert isinstance(insights.performance, PerformanceMetrics)
        assert isinstance(insights.trends, dict)
        assert isinstance(insights.recommendations, list)

    @pytest.mark.asyncio
    async def test_analyze_trends(self, analytics_service, sample_analytics_events, sample_user):
        """Test trend analysis functionality"""
        time_range = (datetime.utcnow() - timedelta(days=10), datetime.utcnow())
        trends = await analytics_service._analyze_trends(user_id=sample_user.id, time_range=time_range)
        
        assert isinstance(trends, dict)
        assert "daily_query_volume" in trends
        assert "daily_avg_response_time" in trends
        assert len(trends["daily_query_volume"]) > 0

    @pytest.mark.asyncio
    async def test_generate_recommendations(self, analytics_service):
        """Test recommendation generation"""
        # Create mock metrics with specific values to trigger recommendations
        query_metrics = QueryMetrics(
            total_queries=100,
            avg_response_time=2.0,
            success_rate=0.85,  # Below 0.9 threshold
            most_common_queries=[],
            query_complexity_distribution={},
            peak_usage_hours=[]
        )
        
        document_metrics = DocumentMetrics(
            total_documents=100,
            most_accessed_documents=[],
            document_type_distribution={},
            avg_document_size=1000,
            upload_trends={},
            tag_popularity={}
        )
        
        user_behavior = UserBehaviorMetrics(
            active_users=10,
            avg_session_duration=200,  # Below 300 threshold
            user_retention_rate=0.3,  # Below 0.5 threshold
            feature_usage={},
            satisfaction_scores={},
            domain_preferences={}
        )
        
        performance = PerformanceMetrics(
            avg_response_time=6.0,  # Above 5.0 threshold
            error_rate=0.1,  # Above 0.05 threshold
            throughput=100,
            memory_usage={},
            cache_hit_rate=0.8,
            database_query_performance={}
        )
        
        recommendations = await analytics_service._generate_recommendations(
            query_metrics, document_metrics, user_behavior, performance
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Check for specific recommendations based on our test data
        recommendation_text = " ".join(recommendations).lower()
        assert "response time" in recommendation_text
        assert "error rate" in recommendation_text
        assert "success rate" in recommendation_text

    @pytest.mark.asyncio
    async def test_export_analytics_data(self, analytics_service, sample_analytics_events, sample_user):
        """Test analytics data export functionality"""
        export_data = await analytics_service.export_analytics_data(user_id=sample_user.id)
        
        assert isinstance(export_data, dict)
        assert "export_timestamp" in export_data
        assert "query_metrics" in export_data
        assert "document_metrics" in export_data
        assert "user_behavior" in export_data
        assert "performance" in export_data
        assert "trends" in export_data
        assert "recommendations" in export_data
        
        # Verify data structure
        assert isinstance(export_data["query_metrics"], dict)
        assert "total_queries" in export_data["query_metrics"]
        assert export_data["query_metrics"]["total_queries"] > 0

    @pytest.mark.asyncio
    @patch('services.analytics_service.get_redis_client')
    async def test_real_time_metrics(self, mock_redis, analytics_service):
        """Test real-time metrics from Redis buffer"""
        # Mock Redis client
        mock_redis_client = AsyncMock()
        mock_redis.return_value = mock_redis_client
        
        # Mock Redis data
        sample_events = [
            json.dumps({
                "user_id": "user1",
                "event_type": EventType.QUERY_EXECUTED,
                "event_data": {"response_time": 1.5}
            }),
            json.dumps({
                "user_id": "user2",
                "event_type": EventType.QUERY_EXECUTED,
                "event_data": {"response_time": 2.0}
            })
        ]
        
        mock_redis_client.lrange.return_value = sample_events
        analytics_service.redis_client = mock_redis_client
        
        metrics = await analytics_service.get_real_time_metrics()
        
        assert isinstance(metrics, dict)
        assert "active_users" in metrics
        assert "queries_per_hour" in metrics
        assert "avg_response_time" in metrics
        assert metrics["active_users"] == 2
        assert metrics["queries_per_hour"] == 2
        assert metrics["avg_response_time"] == 1.75

    @pytest.mark.asyncio
    async def test_time_range_filtering(self, analytics_service, sample_analytics_events, sample_user):
        """Test time range filtering in metrics"""
        # Test with specific time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=1)
        time_range = (start_time, end_time)
        
        metrics = await analytics_service.get_query_metrics(
            user_id=sample_user.id,
            time_range=time_range
        )
        
        assert isinstance(metrics, QueryMetrics)
        # Should have fewer queries due to time range restriction
        assert metrics.total_queries >= 0

    @pytest.mark.asyncio
    async def test_error_handling(self, analytics_service):
        """Test error handling in analytics service"""
        # Test with invalid user ID
        metrics = await analytics_service.get_query_metrics(user_id="invalid-user")
        
        assert isinstance(metrics, QueryMetrics)
        assert metrics.total_queries == 0
        assert metrics.success_rate == 0

    def test_event_type_enum(self):
        """Test EventType enum values"""
        assert EventType.QUERY_EXECUTED == "query_executed"
        assert EventType.DOCUMENT_UPLOADED == "document_uploaded"
        assert EventType.USER_SESSION_START == "user_session_start"
        assert EventType.PERFORMANCE_METRIC == "performance_metric"

    @pytest.mark.asyncio
    async def test_metrics_data_classes(self):
        """Test metrics data classes"""
        query_metrics = QueryMetrics(
            total_queries=100,
            avg_response_time=2.5,
            success_rate=0.95,
            most_common_queries=[("test", 10)],
            query_complexity_distribution={"medium": 50},
            peak_usage_hours=[9, 10, 11]
        )
        
        assert query_metrics.total_queries == 100
        assert query_metrics.avg_response_time == 2.5
        assert query_metrics.success_rate == 0.95

    @pytest.mark.asyncio
    async def test_buffer_real_time_event(self, analytics_service):
        """Test real-time event buffering"""
        # Create mock event
        event = AnalyticsEvent(
            id="test-event",
            user_id="test-user",
            event_type=EventType.QUERY_EXECUTED,
            event_data={"test": "data"},
            timestamp=datetime.utcnow(),
            session_id="test-session"
        )
        
        # Mock Redis client
        analytics_service.redis_client = AsyncMock()
        
        # Test buffering
        await analytics_service._buffer_real_time_event(event)
        
        # Verify Redis calls were made
        analytics_service.redis_client.lpush.assert_called_once()
        analytics_service.redis_client.expire.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__])