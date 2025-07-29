"""
Demo script for Enhanced Analytics Service
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from core.database import get_db, User, Document, AnalyticsEvent, UserProfile, UserFeedback, DocumentTag
from services.analytics_service import EnhancedAnalyticsService, EventType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_sample_data(db: Session):
    """Create sample data for analytics testing"""
    logger.info("Creating sample data for analytics testing...")
    
    # Create test user
    test_user = User(
        id="analytics-test-user",
        email="analytics@test.com",
        name="Analytics Test User",
        hashed_password="hashed_password"
    )
    db.add(test_user)
    
    # Create test documents
    documents = []
    for i in range(5):
        doc = Document(
            id=f"analytics-doc-{i}",
            user_id=test_user.id,
            name=f"Test Document {i}",
            file_path=f"/test/doc_{i}.pdf",
            content_type="application/pdf",
            size=1024 * (i + 1),
            status="completed"
        )
        documents.append(doc)
        db.add(doc)
    
    # Create user profile
    profile = UserProfile(
        user_id=test_user.id,
        preferences={"language": "en", "response_style": "detailed"},
        domain_expertise={"AI": 0.8, "Machine Learning": 0.7, "Data Science": 0.6},
        learning_style="visual"
    )
    db.add(profile)
    
    # Create document tags
    tag_names = ["AI", "Machine Learning", "Research", "Tutorial", "Advanced"]
    for i, doc in enumerate(documents):
        tag = DocumentTag(
            document_id=doc.id,
            tag_name=tag_names[i],
            tag_type="topic",
            confidence_score=0.8 + (i * 0.05),
            generated_by="llm"
        )
        db.add(tag)
    
    # Create user feedback
    feedback = UserFeedback(
        user_id=test_user.id,
        feedback_type="rating",
        feedback_value={"rating": 4.5, "comment": "Great response!"},
        processed=False
    )
    db.add(feedback)
    
    db.commit()
    logger.info("✓ Sample data created successfully")
    return test_user, documents

async def generate_analytics_events(db: Session, analytics_service: EnhancedAnalyticsService, user_id: str, documents: list):
    """Generate various analytics events for testing"""
    logger.info("Generating analytics events...")
    
    base_time = datetime.utcnow() - timedelta(days=30)
    
    # Generate query events
    queries = [
        "What is machine learning?",
        "Explain neural networks",
        "How does deep learning work?",
        "What are the applications of AI?",
        "Compare supervised and unsupervised learning"
    ]
    
    for i, query in enumerate(queries * 4):  # 20 queries total
        await analytics_service.track_event(
            event_type=EventType.QUERY_EXECUTED,
            user_id=user_id,
            event_data={
                "query": query,
                "response_time": 1.5 + (i * 0.1),
                "success": True,
                "complexity": "medium" if i % 2 == 0 else "high",
                "tokens_used": 150 + (i * 10),
                "sources_found": 3 + (i % 3)
            },
            session_id=f"session-{i // 5}"
        )
    
    # Generate document access events
    for i, doc in enumerate(documents * 3):  # 15 access events
        await analytics_service.track_event(
            event_type=EventType.DOCUMENT_ACCESSED,
            user_id=user_id,
            event_data={
                "document_id": doc.id,
                "document_name": doc.name,
                "access_type": "view",
                "duration": 120 + (i * 30)
            },
            session_id=f"session-{i // 3}"
        )
    
    # Generate document upload events
    for i, doc in enumerate(documents):
        await analytics_service.track_event(
            event_type=EventType.DOCUMENT_UPLOADED,
            user_id=user_id,
            event_data={
                "document_id": doc.id,
                "document_name": doc.name,
                "file_size": doc.size,
                "content_type": doc.content_type,
                "processing_time": 5.0 + (i * 0.5)
            },
            session_id=f"upload-session-{i}"
        )
    
    # Generate session events
    for i in range(8):
        # Session start
        await analytics_service.track_event(
            event_type=EventType.USER_SESSION_START,
            user_id=user_id,
            event_data={"user_agent": "Mozilla/5.0", "ip_address": "192.168.1.1"},
            session_id=f"session-{i}"
        )
        
        # Session end (after some time)
        await analytics_service.track_event(
            event_type=EventType.USER_SESSION_END,
            user_id=user_id,
            event_data={"session_duration": 1800 + (i * 300)},  # 30-70 minutes
            session_id=f"session-{i}"
        )
    
    # Generate performance events
    for i in range(10):
        await analytics_service.track_event(
            event_type=EventType.PERFORMANCE_METRIC,
            user_id=user_id,
            event_data={
                "memory_usage": {
                    "heap": 100 + (i * 5),
                    "stack": 50 + (i * 2),
                    "total": 150 + (i * 7)
                },
                "cache_hit_rate": 0.75 + (i * 0.02),
                "db_query_time": 0.1 + (i * 0.01),
                "response_time": 1.2 + (i * 0.05)
            },
            session_id=f"session-{i // 2}"
        )
    
    # Generate some error events
    for i in range(3):
        await analytics_service.track_event(
            event_type=EventType.ERROR_OCCURRED,
            user_id=user_id,
            event_data={
                "error_type": "timeout" if i % 2 == 0 else "validation_error",
                "error_message": f"Test error {i}",
                "stack_trace": f"Stack trace for error {i}",
                "request_id": f"req-{i}"
            },
            session_id=f"session-{i}"
        )
    
    # Generate knowledge graph events
    for i in range(5):
        await analytics_service.track_event(
            event_type=EventType.KNOWLEDGE_GRAPH_QUERIED,
            user_id=user_id,
            event_data={
                "query_type": "entity_search",
                "entities_found": 5 + i,
                "relationships_explored": 10 + (i * 2),
                "query_complexity": "medium"
            },
            session_id=f"session-{i}"
        )
    
    # Generate reasoning events
    for i in range(7):
        await analytics_service.track_event(
            event_type=EventType.REASONING_APPLIED,
            user_id=user_id,
            event_data={
                "reasoning_type": "causal" if i % 2 == 0 else "analogical",
                "confidence_score": 0.7 + (i * 0.05),
                "reasoning_steps": 3 + (i % 3),
                "processing_time": 0.5 + (i * 0.1)
            },
            session_id=f"session-{i // 2}"
        )
    
    logger.info("✓ Analytics events generated successfully")

async def demonstrate_analytics_features(analytics_service: EnhancedAnalyticsService, user_id: str):
    """Demonstrate various analytics features"""
    logger.info("\n" + "="*60)
    logger.info("ANALYTICS DEMONSTRATION")
    logger.info("="*60)
    
    # 1. Query Metrics
    logger.info("\n1. QUERY METRICS")
    logger.info("-" * 30)
    query_metrics = await analytics_service.get_query_metrics(user_id=user_id)
    logger.info(f"Total Queries: {query_metrics.total_queries}")
    logger.info(f"Average Response Time: {query_metrics.avg_response_time:.2f}s")
    logger.info(f"Success Rate: {query_metrics.success_rate:.2%}")
    logger.info(f"Peak Usage Hours: {query_metrics.peak_usage_hours}")
    logger.info(f"Most Common Queries: {query_metrics.most_common_queries[:3]}")
    logger.info(f"Complexity Distribution: {query_metrics.query_complexity_distribution}")
    
    # 2. Document Metrics
    logger.info("\n2. DOCUMENT METRICS")
    logger.info("-" * 30)
    doc_metrics = await analytics_service.get_document_metrics(user_id=user_id)
    logger.info(f"Total Documents: {doc_metrics.total_documents}")
    logger.info(f"Average Document Size: {doc_metrics.avg_document_size:.0f} bytes")
    logger.info(f"Document Type Distribution: {doc_metrics.document_type_distribution}")
    logger.info(f"Most Accessed Documents: {doc_metrics.most_accessed_documents[:3]}")
    logger.info(f"Tag Popularity: {doc_metrics.tag_popularity}")
    logger.info(f"Upload Trends: {list(doc_metrics.upload_trends.items())[:3]}")
    
    # 3. User Behavior Metrics
    logger.info("\n3. USER BEHAVIOR METRICS")
    logger.info("-" * 30)
    behavior_metrics = await analytics_service.get_user_behavior_metrics()
    logger.info(f"Active Users: {behavior_metrics.active_users}")
    logger.info(f"Average Session Duration: {behavior_metrics.avg_session_duration:.0f} seconds")
    logger.info(f"User Retention Rate: {behavior_metrics.user_retention_rate:.2%}")
    logger.info(f"Feature Usage: {dict(list(behavior_metrics.feature_usage.items())[:5])}")
    logger.info(f"Satisfaction Scores: {behavior_metrics.satisfaction_scores}")
    logger.info(f"Domain Preferences: {behavior_metrics.domain_preferences}")
    
    # 4. Performance Metrics
    logger.info("\n4. PERFORMANCE METRICS")
    logger.info("-" * 30)
    perf_metrics = await analytics_service.get_performance_metrics()
    logger.info(f"Average Response Time: {perf_metrics.avg_response_time:.2f}s")
    logger.info(f"Error Rate: {perf_metrics.error_rate:.2%}")
    logger.info(f"Throughput: {perf_metrics.throughput:.2f} events/hour")
    logger.info(f"Cache Hit Rate: {perf_metrics.cache_hit_rate:.2%}")
    logger.info(f"Memory Usage: {perf_metrics.memory_usage}")
    logger.info(f"DB Performance: {perf_metrics.database_query_performance}")
    
    # 5. Comprehensive Insights
    logger.info("\n5. COMPREHENSIVE INSIGHTS")
    logger.info("-" * 30)
    insights = await analytics_service.get_comprehensive_insights(user_id=user_id)
    logger.info(f"Trends: {list(insights.trends.keys())}")
    logger.info("Recommendations:")
    for i, rec in enumerate(insights.recommendations[:5], 1):
        logger.info(f"  {i}. {rec}")
    
    # 6. Real-time Metrics
    logger.info("\n6. REAL-TIME METRICS")
    logger.info("-" * 30)
    realtime_metrics = await analytics_service.get_real_time_metrics()
    logger.info(f"Real-time Metrics: {realtime_metrics}")
    
    # 7. Export Data
    logger.info("\n7. DATA EXPORT")
    logger.info("-" * 30)
    export_data = await analytics_service.export_analytics_data(user_id=user_id)
    logger.info(f"Export timestamp: {export_data['export_timestamp']}")
    logger.info(f"Export data keys: {list(export_data.keys())}")
    logger.info(f"Query metrics in export: {export_data['query_metrics']['total_queries']} queries")

async def test_time_range_filtering(analytics_service: EnhancedAnalyticsService, user_id: str):
    """Test time range filtering functionality"""
    logger.info("\n8. TIME RANGE FILTERING TEST")
    logger.info("-" * 30)
    
    # Test last 7 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    time_range = (start_date, end_date)
    
    metrics_7d = await analytics_service.get_query_metrics(user_id=user_id, time_range=time_range)
    logger.info(f"Queries in last 7 days: {metrics_7d.total_queries}")
    
    # Test last 1 day
    start_date = end_date - timedelta(days=1)
    time_range = (start_date, end_date)
    
    metrics_1d = await analytics_service.get_query_metrics(user_id=user_id, time_range=time_range)
    logger.info(f"Queries in last 1 day: {metrics_1d.total_queries}")
    
    # Test all time (no time range)
    metrics_all = await analytics_service.get_query_metrics(user_id=user_id)
    logger.info(f"All time queries: {metrics_all.total_queries}")

async def test_error_scenarios(analytics_service: EnhancedAnalyticsService):
    """Test error handling scenarios"""
    logger.info("\n9. ERROR HANDLING TEST")
    logger.info("-" * 30)
    
    # Test with non-existent user
    try:
        metrics = await analytics_service.get_query_metrics(user_id="non-existent-user")
        logger.info(f"Non-existent user metrics: {metrics.total_queries} queries (should be 0)")
    except Exception as e:
        logger.error(f"Error with non-existent user: {e}")
    
    # Test with invalid time range
    try:
        future_date = datetime.utcnow() + timedelta(days=1)
        past_date = datetime.utcnow() - timedelta(days=1)
        invalid_range = (future_date, past_date)  # Start after end
        
        metrics = await analytics_service.get_query_metrics(time_range=invalid_range)
        logger.info(f"Invalid time range metrics: {metrics.total_queries} queries")
    except Exception as e:
        logger.error(f"Error with invalid time range: {e}")

async def main():
    """Main demo function"""
    logger.info("Starting Enhanced Analytics Service Demo")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Clean up any existing test data
        db.query(AnalyticsEvent).filter(AnalyticsEvent.user_id == "analytics-test-user").delete()
        db.query(UserFeedback).filter(UserFeedback.user_id == "analytics-test-user").delete()
        db.query(DocumentTag).filter(DocumentTag.document_id.like("analytics-doc-%")).delete()
        db.query(UserProfile).filter(UserProfile.user_id == "analytics-test-user").delete()
        db.query(Document).filter(Document.user_id == "analytics-test-user").delete()
        db.query(User).filter(User.id == "analytics-test-user").delete()
        db.commit()
        
        # Create analytics service
        analytics_service = EnhancedAnalyticsService(db)
        
        # Create sample data
        test_user, documents = await create_sample_data(db)
        
        # Generate analytics events
        await generate_analytics_events(db, analytics_service, test_user.id, documents)
        
        # Demonstrate analytics features
        await demonstrate_analytics_features(analytics_service, test_user.id)
        
        # Test time range filtering
        await test_time_range_filtering(analytics_service, test_user.id)
        
        # Test error scenarios
        await test_error_scenarios(analytics_service)
        
        logger.info("\n" + "="*60)
        logger.info("DEMO COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())