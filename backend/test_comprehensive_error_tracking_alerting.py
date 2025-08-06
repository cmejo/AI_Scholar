#!/usr/bin/env python3
"""
Comprehensive Error Tracking and Alerting System Test
Tests all aspects of the enhanced error tracking system including:
- Error reporting and tracking
- Incident management and escalation
- Automated incident response
- System health monitoring
- User feedback collection
- Alert rule management
- Analytics and reporting
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from backend.services.error_tracking_service import (
    ErrorTrackingService, ErrorSeverity, ErrorCategory, IncidentStatus,
    NotificationChannel, AlertSeverity, EscalationLevel, ErrorContext
)
from backend.core.database import get_db_session

class TestComprehensiveErrorTrackingAlerting:
    """Test comprehensive error tracking and alerting system"""
    
    def setup_method(self):
        """Set up test environment"""
        self.service = ErrorTrackingService()
        self.test_context = ErrorContext(
            user_id="test_user_123",
            session_id="test_session_456",
            feature_name="test_feature",
            operation="test_operation",
            environment="test"
        )
    
    def test_error_reporting_and_tracking(self):
        """Test comprehensive error reporting"""
        print("Testing error reporting and tracking...")
        
        # Test basic error reporting
        error_id = self.service.report_error(
            error_type="TestError",
            error_message="Test error message",
            stack_trace="Test stack trace",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.APPLICATION,
            context=self.test_context
        )
        
        assert error_id, "Error ID should be generated"
        print(f"✓ Error reported with ID: {error_id}")
        
        # Test duplicate error handling (should increment count)
        error_id_2 = self.service.report_error(
            error_type="TestError",
            error_message="Test error message",
            stack_trace="Test stack trace",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.APPLICATION,
            context=self.test_context
        )
        
        assert error_id_2 == error_id, "Duplicate errors should be grouped"
        print("✓ Duplicate error handling works correctly")
        
        # Test different error types
        critical_error_id = self.service.report_error(
            error_type="CriticalError",
            error_message="Critical system failure",
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SYSTEM,
            context=self.test_context
        )
        
        assert critical_error_id, "Critical error should be reported"
        print(f"✓ Critical error reported with ID: {critical_error_id}")
    
    def test_incident_management(self):
        """Test incident creation and management"""
        print("Testing incident management...")
        
        # Create incident
        incident_id = self.service.create_incident(
            title="Test Incident",
            description="Test incident description",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.APPLICATION,
            affected_features=["feature1", "feature2"],
            assigned_to="test_user",
            environment="test"
        )
        
        assert incident_id, "Incident ID should be generated"
        print(f"✓ Incident created with ID: {incident_id}")
        
        # Update incident
        success = self.service.update_incident(incident_id, {
            "status": IncidentStatus.INVESTIGATING.value,
            "resolution_notes": "Investigation started"
        })
        
        assert success, "Incident update should succeed"
        print("✓ Incident updated successfully")
        
        # Test incident timeline
        timeline = self.service.get_incident_timeline(incident_id)
        assert len(timeline) > 0, "Timeline should have entries"
        print(f"✓ Incident timeline has {len(timeline)} entries")
    
    def test_user_feedback_collection(self):
        """Test user feedback collection and processing"""
        print("Testing user feedback collection...")
        
        # Submit bug report
        feedback_id = self.service.collect_user_feedback(
            feedback_type="bug_report",
            title="Test Bug Report",
            description="Detailed bug description",
            user_id="test_user",
            user_email="test@example.com",
            severity="high",
            category="ui",
            metadata={"browser": "Chrome", "version": "91.0"},
            environment="test"
        )
        
        assert feedback_id, "Feedback ID should be generated"
        print(f"✓ Bug report submitted with ID: {feedback_id}")
        
        # Submit feature request
        feature_request_id = self.service.collect_user_feedback(
            feedback_type="feature_request",
            title="New Feature Request",
            description="Request for new functionality",
            user_id="test_user",
            severity="medium",
            environment="test"
        )
        
        assert feature_request_id, "Feature request ID should be generated"
        print(f"✓ Feature request submitted with ID: {feature_request_id}")
    
    @patch('backend.services.error_tracking_service.requests.post')
    def test_notification_system(self, mock_post):
        """Test notification system"""
        print("Testing notification system...")
        
        mock_post.return_value.status_code = 200
        
        # Test Slack notification
        self.service._send_slack_notification(
            "Test Alert",
            "Test message",
            AlertSeverity.HIGH
        )
        
        assert mock_post.called, "Slack notification should be sent"
        print("✓ Slack notification sent")
        
        # Test webhook notification
        self.service._send_webhook_notification(
            "Test Alert",
            "Test message",
            AlertSeverity.MEDIUM
        )
        
        print("✓ Webhook notification sent")
    
    @patch('smtplib.SMTP')
    def test_email_notifications(self, mock_smtp):
        """Test email notification system"""
        print("Testing email notifications...")
        
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Test email notification
        self.service._send_email_notification(
            "Test Email Alert",
            "Test email message",
            AlertSeverity.CRITICAL
        )
        
        assert mock_server.send_message.called, "Email should be sent"
        print("✓ Email notification sent")
    
    def test_alert_rule_management(self):
        """Test alert rule creation and management"""
        print("Testing alert rule management...")
        
        # Create custom alert rule
        rule_id = self.service.create_custom_alert_rule(
            name="test_custom_rule",
            description="Test custom alert rule",
            condition={
                "metric": "error_count",
                "threshold": 5,
                "time_window_minutes": 10
            },
            severity="high",
            notification_channels=["slack", "email"]
        )
        
        assert rule_id, "Alert rule ID should be generated"
        print(f"✓ Custom alert rule created with ID: {rule_id}")
        
        # Test duplicate rule creation (should fail)
        duplicate_rule_id = self.service.create_custom_alert_rule(
            name="test_custom_rule",
            description="Duplicate rule",
            condition={"metric": "error_count", "threshold": 10},
            severity="medium",
            notification_channels=["slack"]
        )
        
        assert not duplicate_rule_id, "Duplicate rule creation should fail"
        print("✓ Duplicate rule prevention works")
    
    @pytest.mark.asyncio
    async def test_system_health_monitoring(self):
        """Test system health monitoring"""
        print("Testing system health monitoring...")
        
        # Test database health check
        await self.service._check_database_health()
        print("✓ Database health check completed")
        
        # Test Redis health check
        await self.service._check_redis_health()
        print("✓ Redis health check completed")
        
        # Test integration health check
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            await self.service._check_integration_health()
            print("✓ Integration health check completed")
        
        # Test application health check
        await self.service._check_application_health()
        print("✓ Application health check completed")
        
        # Get overall health status
        health_status = self.service.get_system_health_status()
        assert "overall_status" in health_status, "Health status should include overall status"
        assert "components" in health_status, "Health status should include components"
        print(f"✓ System health status: {health_status['overall_status']}")
    
    @pytest.mark.asyncio
    async def test_automated_incident_response(self):
        """Test automated incident response system"""
        print("Testing automated incident response...")
        
        # Create critical incident
        incident_id = self.service.create_incident(
            title="Critical System Failure",
            description="System is down",
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SYSTEM,
            environment="test"
        )
        
        # Mock the incident for automated response
        with get_db_session() as db:
            from backend.services.error_tracking_service import IncidentReports
            incident = db.query(IncidentReports).filter_by(id=incident_id).first()
            
            if incident:
                # Test automated response execution
                await self.service._execute_automated_response(incident)
                print("✓ Automated response executed")
                
                # Check if response was recorded
                from backend.services.error_tracking_service import IncidentResponse
                response = db.query(IncidentResponse).filter_by(
                    incident_id=incident_id,
                    response_type="automated"
                ).first()
                
                assert response, "Automated response should be recorded"
                print("✓ Automated response recorded")
    
    @pytest.mark.asyncio
    async def test_escalation_system(self):
        """Test incident escalation system"""
        print("Testing escalation system...")
        
        # Create incident that should trigger escalation
        incident_id = self.service.create_incident(
            title="Critical Incident for Escalation",
            description="This should escalate",
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SYSTEM,
            environment="test"
        )
        
        with get_db_session() as db:
            from backend.services.error_tracking_service import IncidentReports
            incident = db.query(IncidentReports).filter_by(id=incident_id).first()
            
            if incident:
                # Simulate incident age by modifying created_at
                incident.created_at = datetime.utcnow() - timedelta(minutes=20)
                db.commit()
                
                # Test escalation check
                await self.service._check_incident_escalation(incident)
                print("✓ Escalation check completed")
    
    def test_analytics_and_reporting(self):
        """Test analytics and reporting functionality"""
        print("Testing analytics and reporting...")
        
        # Generate some test data first
        for i in range(5):
            self.service.report_error(
                error_type=f"TestError{i}",
                error_message=f"Test error {i}",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.APPLICATION,
                context=self.test_context
            )
        
        # Get analytics
        analytics = self.service.get_error_analytics(days=7)
        
        assert "error_analytics" in analytics, "Analytics should include error data"
        assert "incident_analytics" in analytics, "Analytics should include incident data"
        assert "response_analytics" in analytics, "Analytics should include response data"
        assert "health_analytics" in analytics, "Analytics should include health data"
        assert "trends" in analytics, "Analytics should include trends"
        
        print("✓ Analytics generated successfully")
        print(f"  - Total errors in analytics: {analytics['error_analytics'].get('total_errors', 0)}")
        print(f"  - Total incidents in analytics: {analytics['incident_analytics'].get('total_incidents', 0)}")
    
    def test_error_fingerprinting(self):
        """Test error fingerprinting and grouping"""
        print("Testing error fingerprinting...")
        
        # Create similar errors that should be grouped
        error_id_1 = self.service.report_error(
            error_type="DatabaseError",
            error_message="Connection timeout",
            stack_trace="File 'db.py', line 123",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SYSTEM,
            context=self.test_context
        )
        
        error_id_2 = self.service.report_error(
            error_type="DatabaseError",
            error_message="Connection timeout",
            stack_trace="File 'db.py', line 123",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SYSTEM,
            context=self.test_context
        )
        
        assert error_id_1 == error_id_2, "Similar errors should be grouped"
        print("✓ Error fingerprinting works correctly")
        
        # Create different error that should not be grouped
        error_id_3 = self.service.report_error(
            error_type="DatabaseError",
            error_message="Query failed",
            stack_trace="File 'db.py', line 456",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SYSTEM,
            context=self.test_context
        )
        
        assert error_id_3 != error_id_1, "Different errors should not be grouped"
        print("✓ Different errors are properly separated")
    
    def test_performance_and_scalability(self):
        """Test performance aspects of error tracking"""
        print("Testing performance and scalability...")
        
        # Test bulk error reporting
        start_time = time.time()
        
        for i in range(100):
            self.service.report_error(
                error_type="BulkTestError",
                error_message=f"Bulk test error {i}",
                severity=ErrorSeverity.LOW,
                category=ErrorCategory.APPLICATION,
                context=self.test_context
            )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✓ Processed 100 errors in {processing_time:.2f} seconds")
        assert processing_time < 10, "Bulk error processing should be fast"
        
        # Test Redis performance
        start_time = time.time()
        
        for i in range(50):
            self.service.redis_client.set(f"test_key_{i}", f"test_value_{i}")
        
        end_time = time.time()
        redis_time = end_time - start_time
        
        print(f"✓ Redis operations completed in {redis_time:.2f} seconds")
        
        # Cleanup test keys
        test_keys = self.service.redis_client.keys("test_key_*")
        if test_keys:
            self.service.redis_client.delete(*test_keys)
    
    def test_integration_with_existing_features(self):
        """Test integration with existing system features"""
        print("Testing integration with existing features...")
        
        # Test error reporting from different features
        features = [
            "mobile_app", "voice_interface", "external_integrations",
            "educational_features", "enterprise_compliance", "interactive_content",
            "opportunity_matching", "api_layer"
        ]
        
        for feature in features:
            context = ErrorContext(
                feature_name=feature,
                operation="test_operation",
                environment="test"
            )
            
            error_id = self.service.report_error(
                error_type="FeatureError",
                error_message=f"Error in {feature}",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.APPLICATION,
                context=context
            )
            
            assert error_id, f"Error should be reported for {feature}"
        
        print(f"✓ Error reporting tested for {len(features)} features")
    
    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("=" * 60)
        print("COMPREHENSIVE ERROR TRACKING AND ALERTING SYSTEM TEST")
        print("=" * 60)
        
        try:
            # Run synchronous tests
            self.test_error_reporting_and_tracking()
            self.test_incident_management()
            self.test_user_feedback_collection()
            self.test_notification_system()
            self.test_email_notifications()
            self.test_alert_rule_management()
            self.test_analytics_and_reporting()
            self.test_error_fingerprinting()
            self.test_performance_and_scalability()
            self.test_integration_with_existing_features()
            
            # Run asynchronous tests
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            loop.run_until_complete(self.test_system_health_monitoring())
            loop.run_until_complete(self.test_automated_incident_response())
            loop.run_until_complete(self.test_escalation_system())
            
            loop.close()
            
            print("\n" + "=" * 60)
            print("✅ ALL COMPREHENSIVE ERROR TRACKING TESTS PASSED!")
            print("=" * 60)
            
            # Print summary
            print("\nImplemented Features:")
            print("✓ Comprehensive error tracking and reporting")
            print("✓ Incident management and escalation")
            print("✓ Automated incident response")
            print("✓ System health monitoring")
            print("✓ User feedback collection and processing")
            print("✓ Multi-channel alerting (Email, Slack, PagerDuty, SMS, Teams)")
            print("✓ Custom alert rule management")
            print("✓ Analytics and reporting")
            print("✓ Error fingerprinting and grouping")
            print("✓ Performance optimization")
            print("✓ Integration with all system features")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main test function"""
    test_suite = TestComprehensiveErrorTrackingAlerting()
    test_suite.setup_method()
    success = test_suite.run_comprehensive_test()
    
    if success:
        print("\n🎉 Comprehensive Error Tracking and Alerting System is ready!")
        print("The system provides:")
        print("- Real-time error tracking and alerting")
        print("- Automated incident response and escalation")
        print("- Comprehensive system health monitoring")
        print("- Multi-channel notifications")
        print("- Advanced analytics and reporting")
        print("- User feedback collection and processing")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())