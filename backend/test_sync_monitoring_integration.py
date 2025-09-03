#!/usr/bin/env python3
"""
Integration test for Zotero sync monitoring and notifications system
Tests the complete workflow of sync progress tracking, error reporting, and audit logging
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncMonitoringIntegrationTest:
    """Integration test for sync monitoring system"""
    
    def __init__(self):
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
    
    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        self.test_results['total_tests'] += 1
        if passed:
            self.test_results['passed_tests'] += 1
            logger.info(f"✅ {test_name}: PASSED")
        else:
            self.test_results['failed_tests'] += 1
            logger.error(f"❌ {test_name}: FAILED - {details}")
        
        self.test_results['test_details'].append({
            'test_name': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def test_sync_progress_tracking(self):
        """Test sync progress tracking workflow"""
        test_name = "Sync Progress Tracking"
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from models.zotero_models import Base
            from services.zotero.zotero_sync_monitoring_service import ZoteroSyncMonitoringService
            
            # Create in-memory database for testing
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            SessionLocal = sessionmaker(bind=engine)
            db = SessionLocal()
            
            monitoring_service = ZoteroSyncMonitoringService(db)
            
            # Test progress notification creation
            connection_id = "test-conn-123"
            job_id = "test-job-123"
            
            # Create initial progress notification
            notification_id = monitoring_service.create_progress_notification(
                connection_id=connection_id,
                job_id=job_id,
                progress_percentage=25,
                items_processed=25,
                total_items=100,
                current_operation="Fetching items from Zotero"
            )
            
            assert notification_id is not None, "Failed to create progress notification"
            
            # Update progress notification
            updated_notification_id = monitoring_service.create_progress_notification(
                connection_id=connection_id,
                job_id=job_id,
                progress_percentage=75,
                items_processed=75,
                total_items=100,
                current_operation="Processing items"
            )
            
            # Should return same notification ID (updated existing)
            assert notification_id == updated_notification_id, "Progress notification should be updated, not created new"
            
            # Verify notification content
            notifications = monitoring_service.get_sync_notifications(connection_id)
            assert notifications['total_count'] == 1, "Should have exactly one progress notification"
            
            notification = notifications['notifications'][0]
            assert notification['progress_percentage'] == 75, "Progress should be updated to 75%"
            assert "Processing items" in notification['message'], "Message should reflect current operation"
            
            db.close()
            self.log_test_result(test_name, True)
            
        except Exception as e:
            self.log_test_result(test_name, False, str(e))
    
    async def test_error_reporting_and_recovery(self):
        """Test error reporting and recovery workflow"""
        test_name = "Error Reporting and Recovery"
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from models.zotero_models import Base
            from services.zotero.zotero_sync_monitoring_service import ZoteroSyncMonitoringService
            
            # Create in-memory database for testing
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            SessionLocal = sessionmaker(bind=engine)
            db = SessionLocal()
            
            monitoring_service = ZoteroSyncMonitoringService(db)
            
            connection_id = "test-conn-123"
            job_id = "test-job-123"
            
            # Create error notification
            error_notification_id = monitoring_service.create_error_notification(
                connection_id=connection_id,
                job_id=job_id,
                error_message="Network timeout occurred during sync",
                error_details={
                    "timeout_seconds": 30,
                    "endpoint": "/api/items",
                    "http_status": 408
                },
                retry_count=2
            )
            
            assert error_notification_id is not None, "Failed to create error notification"
            
            # Create warning notification
            warning_notification_id = monitoring_service.create_warning_notification(
                connection_id=connection_id,
                job_id=job_id,
                warning_message="Some items were skipped due to validation errors",
                warning_details={
                    "skipped_items": 5,
                    "validation_errors": ["Missing title", "Invalid date format"]
                }
            )
            
            assert warning_notification_id is not None, "Failed to create warning notification"
            
            # Get error summary
            error_summary = monitoring_service.get_error_summary(connection_id, days=1)
            
            assert error_summary['total_error_notifications'] >= 1, "Should have at least one error notification"
            assert 'Network/Connection' in error_summary['error_categories'], "Should categorize network errors"
            
            # Test error categorization
            assert monitoring_service._categorize_error("Network timeout") == "Network/Connection"
            assert monitoring_service._categorize_error("Authentication failed") == "Authentication"
            assert monitoring_service._categorize_error("Rate limit exceeded") == "Rate Limiting"
            
            db.close()
            self.log_test_result(test_name, True)
            
        except Exception as e:
            self.log_test_result(test_name, False, str(e))
    
    async def test_sync_history_and_audit_logging(self):
        """Test sync history and audit logging"""
        test_name = "Sync History and Audit Logging"
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from models.zotero_models import Base
            from services.zotero.zotero_sync_monitoring_service import ZoteroSyncMonitoringService
            
            # Create in-memory database for testing
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            SessionLocal = sessionmaker(bind=engine)
            db = SessionLocal()
            
            monitoring_service = ZoteroSyncMonitoringService(db)
            
            connection_id = "test-conn-123"
            job_id = "test-job-123"
            user_id = "test-user-123"
            
            # Log various audit events
            audit_events = [
                {
                    'action': 'sync_started',
                    'target_type': 'library',
                    'target_id': 'lib-123',
                    'new_data': {'job_type': 'incremental_sync', 'started_at': datetime.utcnow().isoformat()}
                },
                {
                    'action': 'item_added',
                    'target_type': 'item',
                    'target_id': 'item-123',
                    'new_data': {'title': 'New Research Paper', 'authors': ['John Doe']}
                },
                {
                    'action': 'item_updated',
                    'target_type': 'item',
                    'target_id': 'item-124',
                    'old_data': {'title': 'Old Title'},
                    'new_data': {'title': 'Updated Title'}
                },
                {
                    'action': 'sync_completed',
                    'target_type': 'library',
                    'target_id': 'lib-123',
                    'new_data': {
                        'items_processed': 150,
                        'items_added': 10,
                        'items_updated': 5,
                        'duration_seconds': 45.2
                    }
                }
            ]
            
            audit_ids = []
            for event in audit_events:
                audit_id = monitoring_service.log_sync_audit_event(
                    connection_id=connection_id,
                    sync_job_id=job_id,
                    action=event['action'],
                    target_type=event['target_type'],
                    target_id=event['target_id'],
                    old_data=event.get('old_data'),
                    new_data=event.get('new_data'),
                    user_id=user_id,
                    ip_address="192.168.1.100",
                    user_agent="AI Scholar Test Client",
                    metadata={'test_run': True}
                )
                audit_ids.append(audit_id)
            
            assert len(audit_ids) == 4, "Should have logged 4 audit events"
            assert all(audit_id is not None for audit_id in audit_ids), "All audit IDs should be valid"
            
            # Get sync history
            history = monitoring_service.get_sync_history(connection_id, limit=10)
            
            assert history['total_count'] == 4, "Should have 4 history entries"
            assert len(history['history']) == 4, "Should return 4 history entries"
            
            # Verify history entries are ordered by creation time (newest first)
            history_entries = history['history']
            for i in range(len(history_entries) - 1):
                current_time = datetime.fromisoformat(history_entries[i]['created_at'])
                next_time = datetime.fromisoformat(history_entries[i + 1]['created_at'])
                assert current_time >= next_time, "History should be ordered by creation time (newest first)"
            
            # Test filtering by action
            filtered_history = monitoring_service.get_sync_history(
                connection_id, 
                action_filter='item_added'
            )
            
            assert filtered_history['total_count'] == 1, "Should have 1 item_added event"
            assert filtered_history['history'][0]['action'] == 'item_added', "Filtered result should match action"
            
            db.close()
            self.log_test_result(test_name, True)
            
        except Exception as e:
            self.log_test_result(test_name, False, str(e))
    
    async def test_real_time_sync_status(self):
        """Test real-time sync status monitoring"""
        test_name = "Real-time Sync Status"
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from models.zotero_models import Base, ZoteroSyncJob, ZoteroConnection
            from services.zotero.zotero_sync_monitoring_service import ZoteroSyncMonitoringService
            
            # Create in-memory database for testing
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            SessionLocal = sessionmaker(bind=engine)
            db = SessionLocal()
            
            # Create test connection
            connection = ZoteroConnection(
                id="test-conn-123",
                user_id="test-user-123",
                zotero_user_id="12345",
                access_token="test-token",
                refresh_token="test-refresh",
                token_expires_at=datetime.utcnow() + timedelta(hours=1),
                connection_status="active"
            )
            db.add(connection)
            
            # Create active sync job
            sync_job = ZoteroSyncJob(
                id="test-job-123",
                connection_id="test-conn-123",
                job_type="incremental_sync",
                job_status="running",
                progress_percentage=60,
                items_processed=120,
                total_items=200,
                started_at=datetime.utcnow()
            )
            db.add(sync_job)
            db.commit()
            
            monitoring_service = ZoteroSyncMonitoringService(db)
            
            # Create progress notification
            monitoring_service.create_progress_notification(
                connection_id="test-conn-123",
                job_id="test-job-123",
                progress_percentage=60,
                items_processed=120,
                total_items=200,
                current_operation="Syncing collections"
            )
            
            # Get real-time status
            status = monitoring_service.get_real_time_sync_status("test-conn-123")
            
            assert status['is_syncing'] is True, "Should indicate sync is in progress"
            assert len(status['active_jobs']) == 1, "Should have one active job"
            
            active_job = status['active_jobs'][0]
            assert active_job['id'] == "test-job-123", "Active job ID should match"
            assert active_job['job_type'] == "incremental_sync", "Job type should match"
            assert active_job['status'] == "running", "Job status should be running"
            assert active_job['progress_percentage'] == 60, "Progress should be 60%"
            assert active_job['items_processed'] == 120, "Items processed should be 120"
            
            assert len(status['progress_notifications']) == 1, "Should have one progress notification"
            progress_notif = status['progress_notifications'][0]
            assert progress_notif['progress_percentage'] == 60, "Progress notification should show 60%"
            assert "Syncing collections" in progress_notif['message'], "Should show current operation"
            
            assert 'last_updated' in status, "Should include last updated timestamp"
            
            db.close()
            self.log_test_result(test_name, True)
            
        except Exception as e:
            self.log_test_result(test_name, False, str(e))
    
    async def test_notification_lifecycle(self):
        """Test complete notification lifecycle"""
        test_name = "Notification Lifecycle"
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from models.zotero_models import Base
            from services.zotero.zotero_sync_monitoring_service import ZoteroSyncMonitoringService
            
            # Create in-memory database for testing
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            SessionLocal = sessionmaker(bind=engine)
            db = SessionLocal()
            
            monitoring_service = ZoteroSyncMonitoringService(db)
            
            connection_id = "test-conn-123"
            job_id = "test-job-123"
            
            # Create various types of notifications
            progress_id = monitoring_service.create_progress_notification(
                connection_id=connection_id,
                job_id=job_id,
                progress_percentage=50,
                items_processed=50,
                total_items=100,
                current_operation="Syncing items"
            )
            
            completion_id = monitoring_service.create_completion_notification(
                connection_id=connection_id,
                job_id=job_id,
                items_processed=100,
                items_added=20,
                items_updated=10,
                items_deleted=2,
                sync_duration=30.5
            )
            
            # Get all notifications
            notifications = monitoring_service.get_sync_notifications(connection_id)
            assert notifications['total_count'] == 2, "Should have 2 notifications"
            assert notifications['unread_count'] == 2, "Should have 2 unread notifications"
            
            # Mark one notification as read
            success = monitoring_service.mark_notification_as_read(progress_id, connection_id)
            assert success is True, "Should successfully mark notification as read"
            
            # Check unread count
            updated_notifications = monitoring_service.get_sync_notifications(connection_id)
            assert updated_notifications['unread_count'] == 1, "Should have 1 unread notification"
            
            # Mark all as read
            marked_count = monitoring_service.mark_all_notifications_as_read(connection_id)
            assert marked_count == 1, "Should mark 1 remaining notification as read"
            
            # Check all are read
            final_notifications = monitoring_service.get_sync_notifications(connection_id)
            assert final_notifications['unread_count'] == 0, "Should have 0 unread notifications"
            
            # Delete a notification
            delete_success = monitoring_service.delete_notification(completion_id, connection_id)
            assert delete_success is True, "Should successfully delete notification"
            
            # Verify deletion
            remaining_notifications = monitoring_service.get_sync_notifications(connection_id)
            assert remaining_notifications['total_count'] == 1, "Should have 1 notification remaining"
            
            db.close()
            self.log_test_result(test_name, True)
            
        except Exception as e:
            self.log_test_result(test_name, False, str(e))
    
    async def test_sync_statistics_and_analytics(self):
        """Test sync statistics and analytics"""
        test_name = "Sync Statistics and Analytics"
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from models.zotero_models import Base, ZoteroSyncJob, ZoteroConnection, ZoteroWebhookEvent
            from services.zotero.zotero_sync_monitoring_service import ZoteroSyncMonitoringService
            
            # Create in-memory database for testing
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            SessionLocal = sessionmaker(bind=engine)
            db = SessionLocal()
            
            # Create test connection
            connection = ZoteroConnection(
                id="test-conn-123",
                user_id="test-user-123",
                zotero_user_id="12345",
                access_token="test-token",
                refresh_token="test-refresh",
                token_expires_at=datetime.utcnow() + timedelta(hours=1),
                connection_status="active"
            )
            db.add(connection)
            
            # Create test sync jobs with different statuses
            jobs = [
                ZoteroSyncJob(
                    id=f"job-{i}",
                    connection_id="test-conn-123",
                    job_type="incremental_sync",
                    job_status="completed",
                    items_processed=100,
                    items_added=10,
                    items_updated=5,
                    items_deleted=1,
                    errors_count=0,
                    started_at=datetime.utcnow() - timedelta(minutes=30),
                    completed_at=datetime.utcnow() - timedelta(minutes=25)
                ) for i in range(3)
            ]
            
            # Add one failed job
            jobs.append(ZoteroSyncJob(
                id="job-failed",
                connection_id="test-conn-123",
                job_type="full_sync",
                job_status="failed",
                items_processed=50,
                errors_count=5,
                error_details=[
                    {"error": "Network timeout", "timestamp": datetime.utcnow().isoformat()},
                    {"error": "Authentication failed", "timestamp": datetime.utcnow().isoformat()}
                ],
                started_at=datetime.utcnow() - timedelta(minutes=20),
                completed_at=datetime.utcnow() - timedelta(minutes=15)
            ))
            
            for job in jobs:
                db.add(job)
            
            db.commit()
            
            monitoring_service = ZoteroSyncMonitoringService(db)
            
            # Get statistics
            stats = monitoring_service.get_sync_statistics("test-conn-123", days=1)
            
            assert stats['period_days'] == 1, "Period should be 1 day"
            assert stats['sync_jobs']['total'] == 4, "Should have 4 total jobs"
            assert stats['sync_jobs']['completed'] == 3, "Should have 3 completed jobs"
            assert stats['sync_jobs']['failed'] == 1, "Should have 1 failed job"
            assert stats['sync_jobs']['success_rate'] == 75.0, "Success rate should be 75%"
            
            assert stats['items']['total_processed'] == 350, "Should have processed 350 items total"
            assert stats['items']['total_added'] == 30, "Should have added 30 items total"
            assert stats['items']['total_updated'] == 15, "Should have updated 15 items total"
            assert stats['items']['total_deleted'] == 3, "Should have deleted 3 items total"
            assert stats['items']['total_errors'] == 5, "Should have 5 total errors"
            
            db.close()
            self.log_test_result(test_name, True)
            
        except Exception as e:
            self.log_test_result(test_name, False, str(e))
    
    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("🚀 Starting Zotero Sync Monitoring Integration Tests")
        
        test_methods = [
            self.test_sync_progress_tracking,
            self.test_error_reporting_and_recovery,
            self.test_sync_history_and_audit_logging,
            self.test_real_time_sync_status,
            self.test_notification_lifecycle,
            self.test_sync_statistics_and_analytics
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                logger.error(f"Test method {test_method.__name__} failed with exception: {str(e)}")
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("📊 TEST SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"Passed: {self.test_results['passed_tests']}")
        logger.info(f"Failed: {self.test_results['failed_tests']}")
        
        if self.test_results['failed_tests'] > 0:
            logger.info("\n❌ FAILED TESTS:")
            for test in self.test_results['test_details']:
                if not test['passed']:
                    logger.info(f"  - {test['test_name']}: {test['details']}")
        
        success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests']) * 100
        logger.info(f"\n✅ Success Rate: {success_rate:.1f}%")
        
        return self.test_results


async def main():
    """Main test runner"""
    test_runner = SyncMonitoringIntegrationTest()
    results = await test_runner.run_all_tests()
    
    # Save results to file
    with open('sync_monitoring_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n📄 Test results saved to: sync_monitoring_test_results.json")
    
    # Exit with appropriate code
    exit_code = 0 if results['failed_tests'] == 0 else 1
    return exit_code


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)