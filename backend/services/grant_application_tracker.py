"""
Grant Application Tracker Service

This service implements comprehensive application deadline monitoring, status tracking,
document management, and collaboration features for multi-investigator proposals.
"""

import asyncio
import json
import logging
import os
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from core.database import (
    get_db, GrantApplication, ApplicationDeadlineReminder, ApplicationDocument,
    ApplicationCollaborator, FundingOpportunity, User
)

logger = logging.getLogger(__name__)

@dataclass
class ApplicationSummary:
    """Summary of grant application"""
    application_id: str
    title: str
    funding_agency: str
    requested_amount: float
    deadline: datetime
    status: str
    days_until_deadline: int
    completion_percentage: float

@dataclass
class DeadlineReminder:
    """Deadline reminder information"""
    reminder_id: str
    application_id: str
    application_title: str
    reminder_type: str
    reminder_date: datetime
    message: str
    is_sent: bool

@dataclass
class ApplicationDocument:
    """Application document information"""
    document_id: str
    application_id: str
    document_type: str
    document_name: str
    version: int
    upload_date: datetime
    is_required: bool
    is_submitted: bool
    file_size: int
    file_path: str

@dataclass
class CollaboratorInfo:
    """Collaborator information"""
    collaborator_id: str
    application_id: str
    name: str
    email: str
    institution: str
    role: str
    access_level: str
    invitation_status: str
    contribution_description: str

@dataclass
class ApplicationStatusUpdate:
    """Application status update information"""
    application_id: str
    old_status: str
    new_status: str
    update_date: datetime
    notes: str
    updated_by: str

class GrantApplicationTrackerService:
    """Service for tracking grant applications and deadlines"""
    
    def __init__(self):
        self.status_priorities = {
            'draft': 1,
            'in_progress': 2,
            'submitted': 3,
            'under_review': 4,
            'awarded': 5,
            'rejected': 6,
            'withdrawn': 7
        }
        self.document_storage_path = "data/grant_documents"
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'localhost'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'smtp_username': os.getenv('SMTP_USERNAME', ''),
            'smtp_password': os.getenv('SMTP_PASSWORD', ''),
            'from_email': os.getenv('FROM_EMAIL', 'noreply@aischolar.com')
        }
        
        # Ensure document storage directory exists
        os.makedirs(self.document_storage_path, exist_ok=True)
    
    async def create_application(
        self,
        user_id: str,
        funding_opportunity_id: str,
        application_title: str,
        project_description: str,
        requested_amount: float,
        project_duration_months: int
    ) -> str:
        """Create a new grant application"""
        try:
            db = next(get_db())
            
            # Get funding opportunity details
            opportunity = db.query(FundingOpportunity).filter(
                FundingOpportunity.id == funding_opportunity_id
            ).first()
            
            if not opportunity:
                raise ValueError(f"Funding opportunity {funding_opportunity_id} not found")
            
            application = GrantApplication(
                user_id=user_id,
                funding_opportunity_id=funding_opportunity_id,
                application_title=application_title,
                project_description=project_description,
                requested_amount=requested_amount,
                project_duration_months=project_duration_months,
                application_deadline=opportunity.application_deadline,
                status='draft',
                principal_investigator=user_id,
                co_investigators=[],
                documents=[],
                budget_breakdown={}
            )
            
            db.add(application)
            db.commit()
            db.refresh(application)
            
            # Create deadline reminders
            await self._create_deadline_reminders(db, application)
            
            return application.id
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating application: {str(e)}")
            raise
        finally:
            db.close()
    
    async def get_user_applications(
        self,
        user_id: str,
        status_filter: Optional[str] = None
    ) -> List[ApplicationSummary]:
        """Get user's grant applications"""
        try:
            db = next(get_db())
            
            query = db.query(GrantApplication, FundingOpportunity).join(
                FundingOpportunity, GrantApplication.funding_opportunity_id == FundingOpportunity.id
            ).filter(GrantApplication.user_id == user_id)
            
            if status_filter:
                query = query.filter(GrantApplication.status == status_filter)
            
            applications = query.order_by(GrantApplication.application_deadline).all()
            
            summaries = []
            for app, opportunity in applications:
                days_until_deadline = (app.application_deadline - datetime.now()).days
                completion_percentage = await self._calculate_completion_percentage(db, app.id)
                
                summary = ApplicationSummary(
                    application_id=app.id,
                    title=app.application_title,
                    funding_agency=opportunity.funding_agency,
                    requested_amount=app.requested_amount,
                    deadline=app.application_deadline,
                    status=app.status,
                    days_until_deadline=days_until_deadline,
                    completion_percentage=completion_percentage
                )
                summaries.append(summary)
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error getting user applications: {str(e)}")
            raise
        finally:
            db.close()
    
    async def _calculate_completion_percentage(self, db: Session, application_id: str) -> float:
        """Calculate application completion percentage"""
        # This is a simplified calculation - in practice would be more sophisticated
        app = db.query(GrantApplication).filter(GrantApplication.id == application_id).first()
        if not app:
            return 0.0
        
        completion_factors = []
        
        # Check if basic info is complete
        if app.application_title and app.project_description:
            completion_factors.append(1.0)
        else:
            completion_factors.append(0.0)
        
        # Check if budget is complete
        if app.budget_breakdown and len(app.budget_breakdown) > 0:
            completion_factors.append(1.0)
        else:
            completion_factors.append(0.0)
        
        # Check document completion
        documents = db.query(ApplicationDocument).filter(
            ApplicationDocument.application_id == application_id
        ).all()
        
        if documents:
            submitted_docs = sum(1 for doc in documents if doc.is_submitted)
            doc_completion = submitted_docs / len(documents)
            completion_factors.append(doc_completion)
        else:
            completion_factors.append(0.0)
        
        return sum(completion_factors) / len(completion_factors) * 100
    
    async def _create_deadline_reminders(self, db: Session, application: GrantApplication):
        """Create deadline reminders for application"""
        try:
            deadline = application.application_deadline
            
            # Create reminders at different intervals
            reminder_intervals = [30, 14, 7, 3, 1]  # days before deadline
            
            for days_before in reminder_intervals:
                reminder_date = deadline - timedelta(days=days_before)
                
                if reminder_date > datetime.now():
                    reminder = ApplicationDeadlineReminder(
                        user_id=application.user_id,
                        application_id=application.id,
                        reminder_type='deadline_approaching',
                        reminder_date=reminder_date,
                        message=f"Grant application '{application.application_title}' deadline in {days_before} days"
                    )
                    db.add(reminder)
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating deadline reminders: {str(e)}")
            raise
    
    async def get_pending_reminders(self, user_id: Optional[str] = None) -> List[DeadlineReminder]:
        """Get pending deadline reminders"""
        try:
            db = next(get_db())
            
            query = db.query(ApplicationDeadlineReminder).filter(
                ApplicationDeadlineReminder.is_sent == False,
                ApplicationDeadlineReminder.reminder_date <= datetime.now()
            )
            
            if user_id:
                query = query.filter(ApplicationDeadlineReminder.user_id == user_id)
            
            reminders = query.all()
            
            return [
                DeadlineReminder(
                    reminder_id=reminder.id,
                    application_id=reminder.application_id,
                    application_title="",  # Will be populated from application
                    reminder_type=reminder.reminder_type,
                    reminder_date=reminder.reminder_date,
                    message=reminder.message,
                    is_sent=reminder.is_sent
                )
                for reminder in reminders
            ]
            
        except Exception as e:
            logger.error(f"Error getting pending reminders: {str(e)}")
            raise
        finally:
            db.close()
    
    async def send_deadline_reminders(self) -> int:
        """Send pending deadline reminders"""
        try:
            reminders = await self.get_pending_reminders()
            sent_count = 0
            
            for reminder in reminders:
                try:
                    # Get application and user details
                    db = next(get_db())
                    
                    app = db.query(GrantApplication).filter(
                        GrantApplication.id == reminder.application_id
                    ).first()
                    
                    if not app:
                        continue
                    
                    user = db.query(User).filter(User.id == app.user_id).first()
                    if not user:
                        continue
                    
                    # Send email reminder
                    await self._send_email_reminder(user.email, reminder, app)
                    
                    # Mark reminder as sent
                    db_reminder = db.query(ApplicationDeadlineReminder).filter(
                        ApplicationDeadlineReminder.id == reminder.reminder_id
                    ).first()
                    
                    if db_reminder:
                        db_reminder.is_sent = True
                        db_reminder.sent_at = datetime.now()
                        db.commit()
                        sent_count += 1
                    
                    db.close()
                    
                except Exception as e:
                    logger.error(f"Error sending reminder {reminder.reminder_id}: {str(e)}")
                    continue
            
            return sent_count
            
        except Exception as e:
            logger.error(f"Error sending deadline reminders: {str(e)}")
            raise
    
    async def _send_email_reminder(self, email: str, reminder: DeadlineReminder, application: GrantApplication):
        """Send email reminder to user"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = email
            msg['Subject'] = f"Grant Application Deadline Reminder: {application.application_title}"
            
            body = f"""
            Dear Researcher,
            
            This is a reminder about your grant application:
            
            Application: {application.application_title}
            Deadline: {application.application_deadline.strftime('%Y-%m-%d %H:%M')}
            Status: {application.status}
            
            {reminder.message}
            
            Please log in to your account to review and update your application.
            
            Best regards,
            AI Scholar Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email (if SMTP is configured)
            if self.email_config['smtp_username']:
                server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
                server.starttls()
                server.login(self.email_config['smtp_username'], self.email_config['smtp_password'])
                text = msg.as_string()
                server.sendmail(self.email_config['from_email'], email, text)
                server.quit()
                
                logger.info(f"Reminder email sent to {email} for application {application.id}")
            else:
                logger.info(f"Email reminder would be sent to {email} (SMTP not configured)")
                
        except Exception as e:
            logger.error(f"Error sending email reminder: {str(e)}")
            raise
    
    async def update_application_status(
        self,
        application_id: str,
        new_status: str,
        user_id: str,
        notes: Optional[str] = None,
        external_application_id: Optional[str] = None
    ) -> ApplicationStatusUpdate:
        """Update application status with tracking"""
        try:
            db = next(get_db())
            
            application = db.query(GrantApplication).filter(
                GrantApplication.id == application_id
            ).first()
            
            if not application:
                raise ValueError(f"Application {application_id} not found")
            
            old_status = application.status
            application.status = new_status
            application.updated_at = datetime.now()
            
            if notes:
                application.notes = notes
            
            if external_application_id:
                application.external_application_id = external_application_id
            
            # Set submission date if status is submitted
            if new_status == 'submitted' and not application.submission_date:
                application.submission_date = datetime.now()
            
            # Set decision date if status is awarded or rejected
            if new_status in ['awarded', 'rejected'] and not application.decision_date:
                application.decision_date = datetime.now()
            
            db.commit()
            db.refresh(application)
            
            # Create status update record
            status_update = ApplicationStatusUpdate(
                application_id=application_id,
                old_status=old_status,
                new_status=new_status,
                update_date=datetime.now(),
                notes=notes or "",
                updated_by=user_id
            )
            
            # Send notification to collaborators if status changed significantly
            if old_status != new_status:
                await self._notify_collaborators_status_change(db, application, old_status, new_status)
            
            return status_update
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating application status: {str(e)}")
            raise
        finally:
            db.close()
    
    async def _notify_collaborators_status_change(
        self,
        db: Session,
        application: GrantApplication,
        old_status: str,
        new_status: str
    ):
        """Notify collaborators of status changes"""
        try:
            collaborators = db.query(ApplicationCollaborator).filter(
                ApplicationCollaborator.application_id == application.id,
                ApplicationCollaborator.invitation_status == 'accepted'
            ).all()
            
            for collaborator in collaborators:
                if collaborator.collaborator_email:
                    await self._send_status_change_notification(
                        collaborator.collaborator_email,
                        application,
                        old_status,
                        new_status
                    )
                    
        except Exception as e:
            logger.error(f"Error notifying collaborators: {str(e)}")
    
    async def _send_status_change_notification(
        self,
        email: str,
        application: GrantApplication,
        old_status: str,
        new_status: str
    ):
        """Send status change notification email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = email
            msg['Subject'] = f"Grant Application Status Update: {application.application_title}"
            
            body = f"""
            Dear Collaborator,
            
            The status of the grant application you are collaborating on has been updated:
            
            Application: {application.application_title}
            Previous Status: {old_status}
            New Status: {new_status}
            Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            
            Please log in to your account to view the updated application details.
            
            Best regards,
            AI Scholar Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email (if SMTP is configured)
            if self.email_config['smtp_username']:
                server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
                server.starttls()
                server.login(self.email_config['smtp_username'], self.email_config['smtp_password'])
                text = msg.as_string()
                server.sendmail(self.email_config['from_email'], email, text)
                server.quit()
                
                logger.info(f"Status change notification sent to {email}")
            else:
                logger.info(f"Status change notification would be sent to {email} (SMTP not configured)")
                
        except Exception as e:
            logger.error(f"Error sending status change notification: {str(e)}")
    
    async def get_applications_by_agency(self, user_id: str) -> Dict[str, List[ApplicationSummary]]:
        """Get applications grouped by funding agency"""
        try:
            db = next(get_db())
            
            applications = db.query(GrantApplication, FundingOpportunity).join(
                FundingOpportunity, GrantApplication.funding_opportunity_id == FundingOpportunity.id
            ).filter(GrantApplication.user_id == user_id).all()
            
            agency_groups = {}
            
            for app, opportunity in applications:
                agency = opportunity.funding_agency
                if agency not in agency_groups:
                    agency_groups[agency] = []
                
                days_until_deadline = (app.application_deadline - datetime.now()).days
                completion_percentage = await self._calculate_completion_percentage(db, app.id)
                
                summary = ApplicationSummary(
                    application_id=app.id,
                    title=app.application_title,
                    funding_agency=agency,
                    requested_amount=app.requested_amount,
                    deadline=app.application_deadline,
                    status=app.status,
                    days_until_deadline=days_until_deadline,
                    completion_percentage=completion_percentage
                )
                
                agency_groups[agency].append(summary)
            
            return agency_groups
            
        except Exception as e:
            logger.error(f"Error getting applications by agency: {str(e)}")
            raise
        finally:
            db.close()  
  
    # Document Management Methods
    
    async def upload_application_document(
        self,
        application_id: str,
        document_type: str,
        document_name: str,
        file_content: bytes,
        user_id: str,
        is_required: bool = True
    ) -> str:
        """Upload application document with version control"""
        try:
            db = next(get_db())
            
            # Verify application exists and user has access
            application = db.query(GrantApplication).filter(
                GrantApplication.id == application_id
            ).first()
            
            if not application:
                raise ValueError(f"Application {application_id} not found")
            
            # Check if user has access (owner or collaborator)
            has_access = await self._check_user_access(db, application_id, user_id)
            if not has_access:
                raise ValueError("User does not have access to this application")
            
            # Check for existing document of same type
            existing_doc = db.query(ApplicationDocument).filter(
                ApplicationDocument.application_id == application_id,
                ApplicationDocument.document_type == document_type
            ).order_by(desc(ApplicationDocument.version)).first()
            
            # Determine version number
            version = 1 if not existing_doc else existing_doc.version + 1
            
            # Create file path
            file_extension = document_name.split('.')[-1] if '.' in document_name else 'pdf'
            file_name = f"{application_id}_{document_type}_v{version}.{file_extension}"
            file_path = os.path.join(self.document_storage_path, file_name)
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Create document record
            document = ApplicationDocument(
                application_id=application_id,
                document_type=document_type,
                document_name=document_name,
                file_path=file_path,
                version=version,
                is_required=is_required,
                is_submitted=False,
                file_size=len(file_content),
                file_type=file_extension,
                document_metadata={
                    'uploaded_by': user_id,
                    'upload_timestamp': datetime.now().isoformat(),
                    'original_filename': document_name
                }
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            logger.info(f"Document uploaded: {document.id} for application {application_id}")
            return document.id
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error uploading document: {str(e)}")
            raise
        finally:
            db.close()
    
    async def get_application_documents(self, application_id: str, user_id: str) -> List[ApplicationDocument]:
        """Get all documents for an application"""
        try:
            db = next(get_db())
            
            # Check user access
            has_access = await self._check_user_access(db, application_id, user_id)
            if not has_access:
                raise ValueError("User does not have access to this application")
            
            documents = db.query(ApplicationDocument).filter(
                ApplicationDocument.application_id == application_id
            ).order_by(ApplicationDocument.document_type, desc(ApplicationDocument.version)).all()
            
            return [
                ApplicationDocument(
                    document_id=doc.id,
                    application_id=doc.application_id,
                    document_type=doc.document_type,
                    document_name=doc.document_name,
                    version=doc.version,
                    upload_date=doc.upload_date,
                    is_required=doc.is_required,
                    is_submitted=doc.is_submitted,
                    file_size=doc.file_size,
                    file_path=doc.file_path
                )
                for doc in documents
            ]
            
        except Exception as e:
            logger.error(f"Error getting application documents: {str(e)}")
            raise
        finally:
            db.close()
    
    async def submit_document(self, document_id: str, user_id: str) -> bool:
        """Mark document as submitted"""
        try:
            db = next(get_db())
            
            document = db.query(ApplicationDocument).filter(
                ApplicationDocument.id == document_id
            ).first()
            
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # Check user access
            has_access = await self._check_user_access(db, document.application_id, user_id)
            if not has_access:
                raise ValueError("User does not have access to this document")
            
            document.is_submitted = True
            db.commit()
            
            logger.info(f"Document {document_id} marked as submitted")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error submitting document: {str(e)}")
            raise
        finally:
            db.close()
    
    async def get_document_versions(self, application_id: str, document_type: str, user_id: str) -> List[ApplicationDocument]:
        """Get all versions of a specific document type"""
        try:
            db = next(get_db())
            
            # Check user access
            has_access = await self._check_user_access(db, application_id, user_id)
            if not has_access:
                raise ValueError("User does not have access to this application")
            
            documents = db.query(ApplicationDocument).filter(
                ApplicationDocument.application_id == application_id,
                ApplicationDocument.document_type == document_type
            ).order_by(desc(ApplicationDocument.version)).all()
            
            return [
                ApplicationDocument(
                    document_id=doc.id,
                    application_id=doc.application_id,
                    document_type=doc.document_type,
                    document_name=doc.document_name,
                    version=doc.version,
                    upload_date=doc.upload_date,
                    is_required=doc.is_required,
                    is_submitted=doc.is_submitted,
                    file_size=doc.file_size,
                    file_path=doc.file_path
                )
                for doc in documents
            ]
            
        except Exception as e:
            logger.error(f"Error getting document versions: {str(e)}")
            raise
        finally:
            db.close()
    
    async def download_document(self, document_id: str, user_id: str) -> Tuple[bytes, str, str]:
        """Download document content"""
        try:
            db = next(get_db())
            
            document = db.query(ApplicationDocument).filter(
                ApplicationDocument.id == document_id
            ).first()
            
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # Check user access
            has_access = await self._check_user_access(db, document.application_id, user_id)
            if not has_access:
                raise ValueError("User does not have access to this document")
            
            # Read file content
            if not os.path.exists(document.file_path):
                raise ValueError("Document file not found on disk")
            
            with open(document.file_path, 'rb') as f:
                content = f.read()
            
            return content, document.document_name, document.file_type
            
        except Exception as e:
            logger.error(f"Error downloading document: {str(e)}")
            raise
        finally:
            db.close()
    
    # Collaboration Methods
    
    async def add_collaborator(
        self,
        application_id: str,
        collaborator_name: str,
        collaborator_email: str,
        institution: str,
        role: str,
        contribution_description: str,
        access_level: str,
        inviter_user_id: str
    ) -> str:
        """Add collaborator to grant application"""
        try:
            db = next(get_db())
            
            # Verify application exists and user has admin access
            application = db.query(GrantApplication).filter(
                GrantApplication.id == application_id
            ).first()
            
            if not application:
                raise ValueError(f"Application {application_id} not found")
            
            # Check if inviter is the principal investigator or has admin access
            is_pi = application.user_id == inviter_user_id
            has_admin_access = await self._check_admin_access(db, application_id, inviter_user_id)
            
            if not (is_pi or has_admin_access):
                raise ValueError("User does not have permission to add collaborators")
            
            # Check if collaborator already exists
            existing = db.query(ApplicationCollaborator).filter(
                ApplicationCollaborator.application_id == application_id,
                ApplicationCollaborator.collaborator_email == collaborator_email
            ).first()
            
            if existing:
                raise ValueError("Collaborator already exists for this application")
            
            # Check if collaborator is a system user
            collaborator_user = db.query(User).filter(User.email == collaborator_email).first()
            collaborator_user_id = collaborator_user.id if collaborator_user else None
            
            collaborator = ApplicationCollaborator(
                application_id=application_id,
                collaborator_user_id=collaborator_user_id,
                collaborator_name=collaborator_name,
                collaborator_email=collaborator_email,
                institution=institution,
                role=role,
                contribution_description=contribution_description,
                access_level=access_level,
                invitation_status='pending',
                collaborator_metadata={
                    'invited_by': inviter_user_id,
                    'invitation_timestamp': datetime.now().isoformat()
                }
            )
            
            db.add(collaborator)
            db.commit()
            db.refresh(collaborator)
            
            # Send invitation email
            await self._send_collaboration_invitation(collaborator, application)
            
            logger.info(f"Collaborator {collaborator.id} added to application {application_id}")
            return collaborator.id
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding collaborator: {str(e)}")
            raise
        finally:
            db.close()
    
    async def get_application_collaborators(self, application_id: str, user_id: str) -> List[CollaboratorInfo]:
        """Get collaborators for an application"""
        try:
            db = next(get_db())
            
            # Check user access
            has_access = await self._check_user_access(db, application_id, user_id)
            if not has_access:
                raise ValueError("User does not have access to this application")
            
            collaborators = db.query(ApplicationCollaborator).filter(
                ApplicationCollaborator.application_id == application_id
            ).all()
            
            return [
                CollaboratorInfo(
                    collaborator_id=collab.id,
                    application_id=collab.application_id,
                    name=collab.collaborator_name,
                    email=collab.collaborator_email,
                    institution=collab.institution,
                    role=collab.role,
                    access_level=collab.access_level,
                    invitation_status=collab.invitation_status,
                    contribution_description=collab.contribution_description
                )
                for collab in collaborators
            ]
            
        except Exception as e:
            logger.error(f"Error getting collaborators: {str(e)}")
            raise
        finally:
            db.close()
    
    async def respond_to_collaboration_invitation(
        self,
        collaborator_id: str,
        response: str,  # 'accepted' or 'declined'
        user_id: str
    ) -> bool:
        """Respond to collaboration invitation"""
        try:
            db = next(get_db())
            
            collaborator = db.query(ApplicationCollaborator).filter(
                ApplicationCollaborator.id == collaborator_id
            ).first()
            
            if not collaborator:
                raise ValueError(f"Collaborator {collaborator_id} not found")
            
            # Verify user is the invited collaborator
            if collaborator.collaborator_user_id != user_id:
                # Check by email if user_id doesn't match
                user = db.query(User).filter(User.id == user_id).first()
                if not user or user.email != collaborator.collaborator_email:
                    raise ValueError("User is not authorized to respond to this invitation")
            
            collaborator.invitation_status = response
            collaborator.responded_at = datetime.now()
            db.commit()
            
            # Notify principal investigator
            application = db.query(GrantApplication).filter(
                GrantApplication.id == collaborator.application_id
            ).first()
            
            if application:
                await self._notify_invitation_response(application, collaborator, response)
            
            logger.info(f"Collaboration invitation {collaborator_id} {response}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error responding to invitation: {str(e)}")
            raise
        finally:
            db.close()
    
    async def update_collaborator_access(
        self,
        collaborator_id: str,
        new_access_level: str,
        user_id: str
    ) -> bool:
        """Update collaborator access level"""
        try:
            db = next(get_db())
            
            collaborator = db.query(ApplicationCollaborator).filter(
                ApplicationCollaborator.id == collaborator_id
            ).first()
            
            if not collaborator:
                raise ValueError(f"Collaborator {collaborator_id} not found")
            
            # Check if user has admin access
            has_admin_access = await self._check_admin_access(db, collaborator.application_id, user_id)
            if not has_admin_access:
                raise ValueError("User does not have permission to update collaborator access")
            
            collaborator.access_level = new_access_level
            db.commit()
            
            logger.info(f"Collaborator {collaborator_id} access updated to {new_access_level}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating collaborator access: {str(e)}")
            raise
        finally:
            db.close()
    
    # Helper Methods
    
    async def _check_user_access(self, db: Session, application_id: str, user_id: str) -> bool:
        """Check if user has access to application"""
        # Check if user is the owner
        application = db.query(GrantApplication).filter(
            GrantApplication.id == application_id,
            GrantApplication.user_id == user_id
        ).first()
        
        if application:
            return True
        
        # Check if user is a collaborator
        collaborator = db.query(ApplicationCollaborator).filter(
            ApplicationCollaborator.application_id == application_id,
            ApplicationCollaborator.collaborator_user_id == user_id,
            ApplicationCollaborator.invitation_status == 'accepted'
        ).first()
        
        return collaborator is not None
    
    async def _check_admin_access(self, db: Session, application_id: str, user_id: str) -> bool:
        """Check if user has admin access to application"""
        # Check if user is the owner
        application = db.query(GrantApplication).filter(
            GrantApplication.id == application_id,
            GrantApplication.user_id == user_id
        ).first()
        
        if application:
            return True
        
        # Check if user is a collaborator with admin access
        collaborator = db.query(ApplicationCollaborator).filter(
            ApplicationCollaborator.application_id == application_id,
            ApplicationCollaborator.collaborator_user_id == user_id,
            ApplicationCollaborator.access_level == 'admin',
            ApplicationCollaborator.invitation_status == 'accepted'
        ).first()
        
        return collaborator is not None
    
    async def _send_collaboration_invitation(self, collaborator: ApplicationCollaborator, application: GrantApplication):
        """Send collaboration invitation email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = collaborator.collaborator_email
            msg['Subject'] = f"Collaboration Invitation: {application.application_title}"
            
            body = f"""
            Dear {collaborator.collaborator_name},
            
            You have been invited to collaborate on a grant application:
            
            Application: {application.application_title}
            Role: {collaborator.role}
            Institution: {collaborator.institution}
            Access Level: {collaborator.access_level}
            
            Contribution Description:
            {collaborator.contribution_description}
            
            Please log in to your account to accept or decline this invitation.
            
            Best regards,
            AI Scholar Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email (if SMTP is configured)
            if self.email_config['smtp_username']:
                server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
                server.starttls()
                server.login(self.email_config['smtp_username'], self.email_config['smtp_password'])
                text = msg.as_string()
                server.sendmail(self.email_config['from_email'], collaborator.collaborator_email, text)
                server.quit()
                
                logger.info(f"Collaboration invitation sent to {collaborator.collaborator_email}")
            else:
                logger.info(f"Collaboration invitation would be sent to {collaborator.collaborator_email} (SMTP not configured)")
                
        except Exception as e:
            logger.error(f"Error sending collaboration invitation: {str(e)}")
    
    async def _notify_invitation_response(self, application: GrantApplication, collaborator: ApplicationCollaborator, response: str):
        """Notify principal investigator of invitation response"""
        try:
            db = next(get_db())
            pi_user = db.query(User).filter(User.id == application.user_id).first()
            
            if not pi_user:
                return
            
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = pi_user.email
            msg['Subject'] = f"Collaboration Invitation {response.title()}: {application.application_title}"
            
            body = f"""
            Dear Principal Investigator,
            
            {collaborator.collaborator_name} has {response} your collaboration invitation for:
            
            Application: {application.application_title}
            Collaborator: {collaborator.collaborator_name} ({collaborator.collaborator_email})
            Role: {collaborator.role}
            Response: {response.title()}
            
            Please log in to your account to view the updated collaboration status.
            
            Best regards,
            AI Scholar Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email (if SMTP is configured)
            if self.email_config['smtp_username']:
                server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
                server.starttls()
                server.login(self.email_config['smtp_username'], self.email_config['smtp_password'])
                text = msg.as_string()
                server.sendmail(self.email_config['from_email'], pi_user.email, text)
                server.quit()
                
                logger.info(f"Invitation response notification sent to {pi_user.email}")
            else:
                logger.info(f"Invitation response notification would be sent to {pi_user.email} (SMTP not configured)")
                
            db.close()
                
        except Exception as e:
            logger.error(f"Error sending invitation response notification: {str(e)}")