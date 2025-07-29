"""
Verification script for Task 8.1: Implement comprehensive analytics tracking
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from core.database import get_db, User, Document, AnalyticsEvent, UserProfile, UserFeedback
from services.analytics_service import (
    EnhancedAnalyticsService, EventType, QueryMetrics, DocumentMetrics,
    UserBehaviorMetrics, PerformanceMetrics, AnalyticsInsights
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Task8_1Verifier:
    """Verifier for Task 8.1 implementation"""
    
    def __init__(self):
        self.db = next(get_db())
        self.analytics_service = EnhancedAnalyticsService(self.db)
        self.test_user_id = "task-8-1-test-user"
        self.verification_results = []
    
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log verification result"""
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
        if details:
            logger.info(f"    Details: {details}")
        self.verification_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    async def setup_test_data(self):
        """Set up test data for verification"""
        logger.info("Setting up test data...")
        
        try:
            # Clean up existing test data
            self.db.query(AnalyticsEvent).filter(AnalyticsEvent.user_id == self.test_user_id).delete()
            self.db.query(UserFeedback).filter(UserFeedback.user_id == self.test_user_id).delete()
            self.db.query(UserProfile).filter(UserProfile.user_id == self.test_user_id).delete()
            self.db.query(Document).filter(Document.user_id == self.test_user_id).delete()
            self.db.query(User).filter(User.id == self.test_user_id).delete()
            self.db.commit()
            
            # Create test user
            test_user = User(
                id=self.test_user_id,
                email="task8test@example.com",
                name="Task 8.1 Test User",
                hashed_password="hashed_password"
            )
            self.db.add(test_user)
            
            # Create test document
            test_doc = Document(
                id="task-8-1-test-doc",
                user_id=self.test_user_id,
                name="Test Document",
                file_path="/test/path.pdf",
                content_type="application/pdf",
                size=2048,
                status="completed"
            )
            self.db.add(test_doc)
            
            # Create user profile
            profile = UserProfile(
                user_id=self.test_user_id,
                preferences={"language": "en"},
                domain_expertise={"AI": 0.8},
                learning_style="visual"
            )
            self.db.add(profile)
            
            # Create user feedback
            feedback = UserFeedback(
                user_id=self.test_user_id,
                feedback_type="rating",
                feedback_value={"rating": 4.0},
                processed=False
            )
            self.db.add(feedback)
            
            self.db.commit()
            logger.info("✓ Test data setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup test data: {e}")
            return False
    
    async def verify_event_tracking(self):
        """Verify event tracking functionality"""
        logger.info("\n--- Verifying Event Tracking ---")
        
        try:
            # Test basic event tracking
            event_data = {
                "query": "test query",
                "response_time": 1.5,
                "success": True
            }
            
            event_id = await self.analytics_service.track_event(
                event_type=EventType.QUERY_EXECUTED,
                user_id=self.test_user_id,
                event_data=event_data,
                session_id="test-session"
            )
            
            # Verify event was stored
            stored_event = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.id == event_id
            ).first()
            
            if stored_event and stored_event.event_type == EventType.QUERY_EXECUTED:
                self.log_result("Event tracking basic functionality", True, f"Event ID: {event_id}")
            else:
                self.log_result("Event tracking basic functionality", False, "Event not stored correctly")
                return False
            
            # Test different event types
            event_types_to_test = [
                EventType.DOCUMENT_ACCESSED,
                EventType.USER_SESSION_START,
                EventType.PERFORMANCE_METRIC,
                EventType.ERROR_OCCURRED
            ]
            
            for event_type in event_types_to_test:
                test_event_id = await self.analytics_service.track_event(
                    event_type=event_type,
                    user_id=self.test_user_id,
                    event_data={"test": "data"},
                    session_id="test-session"
                )
                
                if test_event_id:
                    self.log_result(f"Event tracking for {event_type}", True)
                else:
                    self.log_result(f"Event tracking for {event_type}", False)
            
            return True
            
        except Exception as e:
            self.log_result("Event tracking functionality", False, str(e))
            return False
    
    async def verify_query_metrics(self):
        """Verify query metrics calculation"""
        logger.info("\n--- Verifying Query Metrics ---")
        
        try:
            # Generate sample query events
            for i in range(5):
                await self.analytics_service.track_event(
                    event_type=EventType.QUERY_EXECUTED,
                    user_id=self.test_user_id,
                    event_data={
                        "query": f"test query {i}",
                        "response_time": 1.0 + (i * 0.2),
                        "success": True,
                        "complexity": "medium"
                    },
                    session_id=f"session-{i}"
                )
            
            # Get query metrics
            metrics = await self.analytics_service.get_query_metrics(user_id=self.test_user_id)
            
            # Verify metrics structure
            if isinstance(metrics, QueryMetrics):
                self.log_result("Query metrics data structure", True)
            else:
                self.log_result("Query metrics data structure", False, f"Got {type(metrics)}")
                return False
            
            # Verify metrics values
            if metrics.total_queries >= 5:
                self.log_result("Query count tracking", True, f"Total queries: {metrics.total_queries}")
            else:
                self.log_result("Query count tracking", False, f"Expected >= 5, got {metrics.total_queries}")
            
            if metrics.avg_response_time > 0:
                self.log_result("Response time calculation", True, f"Avg time: {metrics.avg_response_time:.2f}s")
            else:
                self.log_result("Response time calculation", False, "Response time not calculated")
            
            if metrics.success_rate >= 0 and metrics.success_rate <= 1:
                self.log_result("Success rate calculation", True, f"Success rate: {metrics.success_rate:.2%}")
            else:
                self.log_result("Success rate calculation", False, f"Invalid success rate: {metrics.success_rate}")
            
            return True
            
        except Exception as e:
            self.log_result("Query metrics calculation", False, str(e))
            return False
    
    async def verify_document_metrics(self):
        """Verify document metrics calculation"""
        logger.info("\n--- Verifying Document Metrics ---")
        
        try:
            # Generate document access events
            for i in range(3):
                await self.analytics_service.track_event(
                    event_type=EventType.DOCUMENT_ACCESSED,
                    user_id=self.test_user_id,
                    event_data={
                        "document_id": "task-8-1-test-doc",
                        "access_type": "view"
                    },
                    session_id=f"session-{i}"
                )
            
            # Get document metrics
            metrics = await self.analytics_service.get_document_metrics(user_id=self.test_user_id)
            
            # Verify metrics structure
            if isinstance(metrics, DocumentMetrics):
                self.log_result("Document metrics data structure", True)
            else:
                self.log_result("Document metrics data structure", False, f"Got {type(metrics)}")
                return False
            
            # Verify metrics values
            if metrics.total_documents >= 1:
                self.log_result("Document count tracking", True, f"Total documents: {metrics.total_documents}")
            else:
                self.log_result("Document count tracking", False, f"Expected >= 1, got {metrics.total_documents}")
            
            if metrics.avg_document_size > 0:
                self.log_result("Document size calculation", True, f"Avg size: {metrics.avg_document_size:.0f} bytes")
            else:
                self.log_result("Document size calculation", False, "Document size not calculated")
            
            if len(metrics.most_accessed_documents) > 0:
                self.log_result("Document access tracking", True, f"Tracked {len(metrics.most_accessed_documents)} accessed docs")
            else:
                self.log_result("Document access tracking", False, "No document access tracked")
            
            return True
            
        except Exception as e:
            self.log_result("Document metrics calculation", False, str(e))
            return False
    
    async def verify_user_behavior_metrics(self):
        """Verify user behavior metrics calculation"""
        logger.info("\n--- Verifying User Behavior Metrics ---")
        
        try:
            # Generate session events
            for i in range(2):
                await self.analytics_service.track_event(
                    event_type=EventType.USER_SESSION_START,
                    user_id=self.test_user_id,
                    event_data={},
                    session_id=f"behavior-session-{i}"
                )
                
                await self.analytics_service.track_event(
                    event_type=EventType.USER_SESSION_END,
                    user_id=self.test_user_id,
                    event_data={"session_duration": 1800},
                    session_id=f"behavior-session-{i}"
                )
            
            # Get user behavior metrics
            metrics = await self.analytics_service.get_user_behavior_metrics()
            
            # Verify metrics structure
            if isinstance(metrics, UserBehaviorMetrics):
                self.log_result("User behavior metrics data structure", True)
            else:
                self.log_result("User behavior metrics data structure", False, f"Got {type(metrics)}")
                return False
            
            # Verify metrics values
            if metrics.active_users >= 1:
                self.log_result("Active users tracking", True, f"Active users: {metrics.active_users}")
            else:
                self.log_result("Active users tracking", False, f"Expected >= 1, got {metrics.active_users}")
            
            if isinstance(metrics.feature_usage, dict):
                self.log_result("Feature usage tracking", True, f"Tracked {len(metrics.feature_usage)} features")
            else:
                self.log_result("Feature usage tracking", False, "Feature usage not tracked properly")
            
            return True
            
        except Exception as e:
            self.log_result("User behavior metrics calculation", False, str(e))
            return False
    
    async def verify_performance_metrics(self):
        """Verify performance metrics calculation"""
        logger.info("\n--- Verifying Performance Metrics ---")
        
        try:
            # Generate performance events
            for i in range(3):
                await self.analytics_service.track_event(
                    event_type=EventType.PERFORMANCE_METRIC,
                    user_id=self.test_user_id,
                    event_data={
                        "memory_usage": {"heap": 100 + i * 10},
                        "cache_hit_rate": 0.8 + (i * 0.05),
                        "db_query_time": 0.1 + (i * 0.02)
                    },
                    session_id=f"perf-session-{i}"
                )
            
            # Get performance metrics
            metrics = await self.analytics_service.get_performance_metrics()
            
            # Verify metrics structure
            if isinstance(metrics, PerformanceMetrics):
                self.log_result("Performance metrics data structure", True)
            else:
                self.log_result("Performance metrics data structure", False, f"Got {type(metrics)}")
                return False
            
            # Verify metrics values
            if metrics.avg_response_time >= 0:
                self.log_result("Response time tracking", True, f"Avg response time: {metrics.avg_response_time:.2f}s")
            else:
                self.log_result("Response time tracking", False, "Invalid response time")
            
            if metrics.error_rate >= 0 and metrics.error_rate <= 1:
                self.log_result("Error rate calculation", True, f"Error rate: {metrics.error_rate:.2%}")
            else:
                self.log_result("Error rate calculation", False, f"Invalid error rate: {metrics.error_rate}")
            
            if metrics.throughput >= 0:
                self.log_result("Throughput calculation", True, f"Throughput: {metrics.throughput:.2f} events/hour")
            else:
                self.log_result("Throughput calculation", False, "Invalid throughput")
            
            return True
            
        except Exception as e:
            self.log_result("Performance metrics calculation", False, str(e))
            return False
    
    async def verify_comprehensive_insights(self):
        """Verify comprehensive insights generation"""
        logger.info("\n--- Verifying Comprehensive Insights ---")
        
        try:
            # Get comprehensive insights
            insights = await self.analytics_service.get_comprehensive_insights(user_id=self.test_user_id)
            
            # Verify insights structure
            if isinstance(insights, AnalyticsInsights):
                self.log_result("Comprehensive insights data structure", True)
            else:
                self.log_result("Comprehensive insights data structure", False, f"Got {type(insights)}")
                return False
            
            # Verify all components are present
            components = [
                ("query_metrics", QueryMetrics),
                ("document_metrics", DocumentMetrics),
                ("user_behavior", UserBehaviorMetrics),
                ("performance", PerformanceMetrics)
            ]
            
            for component_name, expected_type in components:
                component = getattr(insights, component_name)
                if isinstance(component, expected_type):
                    self.log_result(f"Insights {component_name} component", True)
                else:
                    self.log_result(f"Insights {component_name} component", False, f"Expected {expected_type}, got {type(component)}")
            
            # Verify trends and recommendations
            if isinstance(insights.trends, dict):
                self.log_result("Trends analysis", True, f"Generated {len(insights.trends)} trend categories")
            else:
                self.log_result("Trends analysis", False, "Trends not generated properly")
            
            if isinstance(insights.recommendations, list):
                self.log_result("Recommendations generation", True, f"Generated {len(insights.recommendations)} recommendations")
            else:
                self.log_result("Recommendations generation", False, "Recommendations not generated properly")
            
            return True
            
        except Exception as e:
            self.log_result("Comprehensive insights generation", False, str(e))
            return False
    
    async def verify_real_time_analytics(self):
        """Verify real-time analytics functionality"""
        logger.info("\n--- Verifying Real-time Analytics ---")
        
        try:
            # Test real-time metrics (may not work without Redis, but should not crash)
            realtime_metrics = await self.analytics_service.get_real_time_metrics()
            
            if isinstance(realtime_metrics, dict):
                self.log_result("Real-time metrics structure", True, f"Keys: {list(realtime_metrics.keys())}")
            else:
                self.log_result("Real-time metrics structure", False, f"Expected dict, got {type(realtime_metrics)}")
            
            return True
            
        except Exception as e:
            self.log_result("Real-time analytics functionality", False, str(e))
            return False
    
    async def verify_data_export(self):
        """Verify data export functionality"""
        logger.info("\n--- Verifying Data Export ---")
        
        try:
            # Test data export
            export_data = await self.analytics_service.export_analytics_data(user_id=self.test_user_id)
            
            if isinstance(export_data, dict):
                self.log_result("Data export structure", True)
            else:
                self.log_result("Data export structure", False, f"Expected dict, got {type(export_data)}")
                return False
            
            # Verify required keys
            required_keys = [
                "export_timestamp", "query_metrics", "document_metrics",
                "user_behavior", "performance", "trends", "recommendations"
            ]
            
            for key in required_keys:
                if key in export_data:
                    self.log_result(f"Export contains {key}", True)
                else:
                    self.log_result(f"Export contains {key}", False)
            
            return True
            
        except Exception as e:
            self.log_result("Data export functionality", False, str(e))
            return False
    
    async def verify_time_range_filtering(self):
        """Verify time range filtering functionality"""
        logger.info("\n--- Verifying Time Range Filtering ---")
        
        try:
            # Test with specific time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=1)
            time_range = (start_time, end_time)
            
            metrics = await self.analytics_service.get_query_metrics(
                user_id=self.test_user_id,
                time_range=time_range
            )
            
            if isinstance(metrics, QueryMetrics):
                self.log_result("Time range filtering", True, f"Filtered metrics: {metrics.total_queries} queries")
            else:
                self.log_result("Time range filtering", False, "Time range filtering failed")
            
            return True
            
        except Exception as e:
            self.log_result("Time range filtering functionality", False, str(e))
            return False
    
    async def run_verification(self):
        """Run all verification tests"""
        logger.info("="*60)
        logger.info("TASK 8.1 VERIFICATION: Enhanced Analytics Service")
        logger.info("="*60)
        
        try:
            # Setup test data
            if not await self.setup_test_data():
                logger.error("Failed to setup test data. Aborting verification.")
                return False
            
            # Run verification tests
            verification_tests = [
                self.verify_event_tracking,
                self.verify_query_metrics,
                self.verify_document_metrics,
                self.verify_user_behavior_metrics,
                self.verify_performance_metrics,
                self.verify_comprehensive_insights,
                self.verify_real_time_analytics,
                self.verify_data_export,
                self.verify_time_range_filtering
            ]
            
            for test in verification_tests:
                await test()
            
            # Summary
            logger.info("\n" + "="*60)
            logger.info("VERIFICATION SUMMARY")
            logger.info("="*60)
            
            passed_tests = sum(1 for result in self.verification_results if result["passed"])
            total_tests = len(self.verification_results)
            
            logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
            logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            if passed_tests == total_tests:
                logger.info("🎉 ALL TESTS PASSED! Task 8.1 implementation is verified.")
                return True
            else:
                logger.warning("⚠️  Some tests failed. Review the implementation.")
                
                # Show failed tests
                failed_tests = [result for result in self.verification_results if not result["passed"]]
                if failed_tests:
                    logger.info("\nFailed Tests:")
                    for test in failed_tests:
                        logger.info(f"  - {test['test']}: {test['details']}")
                
                return False
                
        except Exception as e:
            logger.error(f"Verification failed with error: {e}")
            return False
        finally:
            # Cleanup
            try:
                self.db.query(AnalyticsEvent).filter(AnalyticsEvent.user_id == self.test_user_id).delete()
                self.db.query(UserFeedback).filter(UserFeedback.user_id == self.test_user_id).delete()
                self.db.query(UserProfile).filter(UserProfile.user_id == self.test_user_id).delete()
                self.db.query(Document).filter(Document.user_id == self.test_user_id).delete()
                self.db.query(User).filter(User.id == self.test_user_id).delete()
                self.db.commit()
                logger.info("✓ Test data cleanup completed")
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")
            finally:
                self.db.close()

async def main():
    """Main verification function"""
    verifier = Task8_1Verifier()
    success = await verifier.run_verification()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)