"""
Comprehensive Test Suite for Grant Application Tracking

This test suite verifies all aspects of the grant application tracking system:
- Deadline monitoring and reminders
- Status tracking across multiple agencies
- Document management and version control
- Collaboration features for multi-investigator proposals
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from services.grant_application_tracker import GrantApplicationTrackerService
from core.database import get_db, GrantApplication, ApplicationDeadlineReminder, ApplicationDocument, ApplicationCollaborator, FundingOpportunity, User

class TestGrantApplicationTracking:
    """Test grant application tracking functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.service = GrantApplicationTrackerService()
        self.test_user_id = "test_user_123"
        self.test_application_id = "test_app_123"
        self.test_opportunity_id = "test_opp_123"
    
    @pytest.mark.asyncio
    async def test_create_application_with_reminders(self):
        """Test creating application with automatic deadline reminders"""
        with patch('services.grant_application_tracker.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock funding opportunity
            mock_opportunity = Mock()
            mock_opportunity.id = self.test_opportunity_id
            mock_opportunity.application_deadline = datetime.now() + timedelta(days=30)
            mock_opportunity.funding_agency = "NSF"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_opportunity
            
            # Mock application creation
            mock_application = Mock()
            mock_application.id = self.test_application_id
            mock_application.user_id = self.test_user_id
            mock_application.application_deadline = mock_opportunity.application_deadline
            
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            # Test application creation
            result = await self.service.create_application(
                user_id=self.test_user_id,
                funding_opportunity_id=self.test_opportunity_id,
                application_title="Test Grant Application",
                project_description="Test project description",
                requested_amount=100000.0,
                project_duration_months=24
            )
            
            # Verify application was created
            assert result == self.test_application_id
            mock_db.add.assert_called()
            mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_deadline_reminder_system(self):
        """Test deadline reminder creation and sending"""
        with patch('services.grant_application_tracker.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock pending reminders
            mock_reminder = Mock()
            mock_reminder.id = "reminder_123"
            mock_reminder.application_id = self.test_application_id
            mock_reminder.reminder_type = "deadline_approaching"
            mock_reminder.reminder_date = datetime.now() - timedelta(hours=1)
            mock_reminder.message = "Deadline in 7 days"
            mock_reminder.is_sent = False
            
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_reminder]
            
            # Test getting pending reminders
            reminders = await self.service.get_pending_reminders(self.test_user_id)
            
            assert len(reminders) == 1
            assert reminders[0].reminder_id == "reminder_123"
            assert reminders[0].application_id == self.test_application_id
    
    @pytest.mark.asyncio
    async def test_status_tracking_across_agencies(self):
        """Test application status tracking across multiple funding agencies"""
        with patch('services.grant_application_tracker.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock applications from different agencies
            mock_app1 = Mock()
            mock_app1.id = "app1"
            mock_app1.application_title = "NSF Application"
            mock_app1.status = "submitted"
            mock_app1.application_deadline = datetime.now() + timedelta(days=15)
            mock_app1.requested_amount = 150000.0
            
            mock_app2 = Mock()
            mock_app2.id = "app2"
            mock_app2.application_title = "NIH Application"
            mock_app2.status = "under_review"
            mock_app2.application_deadline = datetime.now() + timedelta(days=45)
            mock_app2.requested_amount = 200000.0
            
            mock_opp1 = Mock()
            mock_opp1.funding_agency = "NSF"
            
            mock_opp2 = Mock()
            mock_opp2.funding_agency = "NIH"
            
            mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [
                (mock_app1, mock_opp1),
                (mock_app2, mock_opp2)
            ]
            
            # Mock completion percentage calculation
            with patch.object(self.service, '_calculate_completion_percentage', return_value=75.0):
                # Test getting applications by agency
                agency_groups = await self.service.get_applications_by_agency(self.test_user_id)
                
                assert "NSF" in agency_groups
                assert "NIH" in agency_groups
                assert len(agency_groups["NSF"]) == 1
                assert len(agency_groups["NIH"]) == 1
                assert agency_groups["NSF"][0].title == "NSF Application"
                assert agency_groups["NIH"][0].title == "NIH Application"
    
    @pytest.mark.asyncio
    async def test_status_update_with_notifications(self):
        """Test application status updates with collaborator notifications"""
        with patch('services.grant_application_tracker.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock application
            mock_application = Mock()
            mock_application.id = self.test_application_id
            mock_application.status = "submitted"
            mock_application.submission_date = None
            mock_application.decision_date = None
            mock_application.notes = ""
            mock_application.external_application_id = None
            mock_application.updated_at = datetime.now()
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_application
            
            # Mock collaborator notification
            with patch.object(self.service, '_notify_collaborators_status_change') as mock_notify:
                # Test status update
                status_update = await self.service.update_application_status(
                    application_id=self.test_application_id,
                    new_status="awarded",
                    user_id=self.test_user_id,
                    notes="Application awarded with full funding"
                )
                
                assert status_update.old_status == "submitted"
                assert status_update.new_status == "awarded"
                assert status_update.notes == "Application awarded with full funding"
                mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_document_upload_and_version_control(self):
        """Test document upload with version control"""
        with patch('services.grant_application_tracker.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock application
            mock_application = Mock()
            mock_application.id = self.test_application_id
            mock_db.query.return_value.filter.return_value.first.return_value = mock_application
            
            # Mock user access check
            with patch.object(self.service, '_check_user_access', return_value=True):
                # Mock existing document for version control
                mock_existing_doc = Mock()
                mock_existing_doc.version = 1
                mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_existing_doc
                
                # Mock document creation
                mock_new_doc = Mock()
                mock_new_doc.id = "doc_123"
                mock_db.add.return_value = None
                mock_db.commit.return_value = None
                mock_db.refresh.return_value = None
                
                # Create temporary file for testing
                test_content = b"Test document content"
                
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.write.return_value = None
                    
                    # Test document upload
                    document_id = await self.service.upload_application_document(
                        application_id=self.test_application_id,
                        document_type="proposal",
                        document_name="test_proposal.pdf",
                        file_content=test_content,
                        user_id=self.test_user_id,
                        is_required=True
                    )
                    
                    # Verify document was created with correct version
                    mock_db.add.assert_called()
                    mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_document_version_history(self):
        """Test retrieving document version history"""
        with patch('services.grant_application_tracker.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock user access check
            with patch.object(self.service, '_check_user_access', return_value=True):
                # Mock document versions
                mock_doc_v1 = Mock()
                mock_doc_v1.id = "doc_v1"
                mock_doc_v1.application_id = self.test_application_id
                mock_doc_v1.document_type = "proposal"
                mock_doc_v1.document_name = "proposal_v1.pdf"
                mock_doc_v1.version = 1
                mock_doc_v1.upload_date = datetime.now() - timedelta(days=5)
                mock_doc_v1.is_required = True
                mock_doc_v1.is_submitted = False
                mock_doc_v1.file_size = 1024
                mock_doc_v1.file_path = "/path/to/doc_v1.pdf"
                
                mock_doc_v2 = Mock()
                mock_doc_v2.id = "doc_v2"
                mock_doc_v2.application_id = self.test_application_id
                mock_doc_v2.document_type = "proposal"
                mock_doc_v2.document_name = "proposal_v2.pdf"
                mock_doc_v2.version = 2
                mock_doc_v2.upload_date = datetime.now()
                mock_doc_v2.is_required = True
                mock_doc_v2.is_submitted = True
                mock_doc_v2.file_size = 2048
                mock_doc_v2.file_path = "/path/to/doc_v2.pdf"
                
                mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
                    mock_doc_v2, mock_doc_v1  # Ordered by version desc
                ]
                
                # Test getting document versions
                versions = await self.service.get_document_versions(
                    application_id=self.test_application_id,
                    document_type="proposal",
                    user_id=self.test_user_id
                )
                
                assert len(versions) == 2
                assert versions[0].version == 2  # Latest version first
                assert versions[1].version == 1
                assert versions[0].is_submitted == True
                assert versions[1].is_submitted == False
    
    @pytest.mark.asyncio
    async def test_collaborator_invitation_system(self):
        """Test collaborator invitation and response system"""
        with patch('services.grant_application_tracker.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock application
            mock_application = Mock()
            mock_application.id = self.test_application_id
            mock_application.user_id = self.test_user_id
            mock_application.application_title = "Test Grant"
            mock_db.query.return_value.filter.return_value.first.return_value = mock_application
            
            # Mock no existing collaborator
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_application,  # Application exists
                None,  # No existing collaborator
                None   # Collaborator is not a system user
            ]
            
            # Mock collaborator creation
            mock_collaborator = Mock()
            mock_collaborator.id = "collab_123"
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            # Mock email sending
            with patch.object(self.service, '_send_collaboration_invitation') as mock_send_email:
                # Test adding collaborator
                collaborator_id = await self.service.add_collaborator(
                    application_id=self.test_application_id,
                    collaborator_name="Dr. Jane Smith",
                    collaborator_email="jane.smith@university.edu",
                    institution="University of Science",
                    role="co_investigator",
                    contribution_description="Statistical analysis and data interpretation",
                    access_level="edit",
                    inviter_user_id=self.test_user_id
                )
                
                # Verify collaborator was added and invitation sent
                mock_db.add.assert_called()
                mock_db.commit.assert_called()
                mock_send_email.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_collaboration_invitation_response(self):
        """Test responding to collaboration invitations"""
        with patch('services.grant_application_tracker.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock collaborator
            mock_collaborator = Mock()
            mock_collaborator.id = "collab_123"
            mock_collaborator.application_id = self.test_application_id
            mock_collaborator.collaborator_user_id = self.test_user_id
            mock_collaborator.collaborator_name = "Dr. Jane Smith"
            mock_collaborator.collaborator_email = "jane.smith@university.edu"
            mock_collaborator.invitation_status = "pending"
            mock_collaborator.responded_at = None
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_collaborator
            
            # Mock application for notification
            mock_application = Mock()
            mock_application.id = self.test_application_id
            mock_application.application_title = "Test Grant"
            
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_collaborator,  # First call for collaborator
                mock_application    # Second call for application
            ]
            
            # Mock notification sending
            with patch.object(self.service, '_notify_invitation_response') as mock_notify:
                # Test accepting invitation
                result = await self.service.respond_to_collaboration_invitation(
                    collaborator_id="collab_123",
                    response="accepted",
                    user_id=self.test_user_id
                )
                
                assert result == True
                assert mock_collaborator.invitation_status == "accepted"
                mock_db.commit.assert_called()
                mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_multi_investigator_access_control(self):
        """Test access control for multi-investigator proposals"""
        with patch('services.grant_application_tracker.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Test principal investigator access
            mock_application = Mock()
            mock_application.id = self.test_application_id
            mock_application.user_id = self.test_user_id
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_application
            
            has_access = await self.service._check_user_access(mock_db, self.test_application_id, self.test_user_id)
            assert has_access == True
            
            # Test collaborator access
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                None,  # Not the owner
                Mock()  # Is a collaborator
            ]
            
            has_access = await self.service._check_user_access(mock_db, self.test_application_id, "other_user")
            assert has_access == True
            
            # Test no access
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                None,  # Not the owner
                None   # Not a collaborator
            ]
            
            has_access = await self.service._check_user_access(mock_db, self.test_application_id, "unauthorized_user")
            assert has_access == False
    
    @pytest.mark.asyncio
    async def test_admin_access_control(self):
        """Test admin access control for collaboration management"""
        with patch('services.grant_application_tracker.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Test principal investigator admin access
            mock_application = Mock()
            mock_application.id = self.test_application_id
            mock_application.user_id = self.test_user_id
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_application
            
            has_admin_access = await self.service._check_admin_access(mock_db, self.test_application_id, self.test_user_id)
            assert has_admin_access == True
            
            # Test collaborator with admin access
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                None,  # Not the owner
                Mock()  # Is a collaborator with admin access
            ]
            
            has_admin_access = await self.service._check_admin_access(mock_db, self.test_application_id, "admin_collab")
            assert has_admin_access == True
    
    @pytest.mark.asyncio
    async def test_document_download_security(self):
        """Test document download with security checks"""
        with patch('services.grant_application_tracker.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock document
            mock_document = Mock()
            mock_document.id = "doc_123"
            mock_document.application_id = self.test_application_id
            mock_document.document_name = "test_document.pdf"
            mock_document.file_type = "pdf"
            mock_document.file_path = "/path/to/test_document.pdf"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_document
            
            # Mock user access check
            with patch.object(self.service, '_check_user_access', return_value=True):
                # Mock file existence and content
                with patch('os.path.exists', return_value=True):
                    with patch('builtins.open', create=True) as mock_open:
                        mock_open.return_value.__enter__.return_value.read.return_value = b"PDF content"
                        
                        # Test document download
                        content, filename, file_type = await self.service.download_document(
                            document_id="doc_123",
                            user_id=self.test_user_id
                        )
                        
                        assert content == b"PDF content"
                        assert filename == "test_document.pdf"
                        assert file_type == "pdf"
            
            # Test unauthorized access
            with patch.object(self.service, '_check_user_access', return_value=False):
                with pytest.raises(ValueError, match="User does not have access"):
                    await self.service.download_document(
                        document_id="doc_123",
                        user_id="unauthorized_user"
                    )

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])