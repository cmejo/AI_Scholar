"""
Grant Application API Endpoints

This module provides REST API endpoints for grant application tracking and management.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
try:
    from fastapi import UploadFile, File, Form
except ImportError:
    # Fallback for environments without python-multipart
    UploadFile = None
    File = None
    Form = None
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import io

from services.grant_application_tracker import GrantApplicationTrackerService

router = APIRouter(prefix="/api/grants", tags=["grants"])
grant_service = GrantApplicationTrackerService()

# Request/Response Models

class ApplicationCreate(BaseModel):
    """Model for creating grant application"""
    funding_opportunity_id: str = Field(..., description="Funding opportunity ID")
    application_title: str = Field(..., description="Application title")
    project_description: str = Field(..., description="Project description")
    requested_amount: float = Field(..., description="Requested funding amount")
    project_duration_months: int = Field(..., description="Project duration in months")

class ApplicationSummaryResponse(BaseModel):
    """Model for application summary response"""
    application_id: str
    title: str
    funding_agency: str
    requested_amount: float
    deadline: datetime
    status: str
    days_until_deadline: int
    completion_percentage: float

class StatusUpdateRequest(BaseModel):
    """Model for updating application status"""
    new_status: str = Field(..., description="New application status")
    notes: Optional[str] = Field(None, description="Update notes")
    external_application_id: Optional[str] = Field(None, description="External application ID")

class DeadlineReminderResponse(BaseModel):
    """Model for deadline reminder response"""
    reminder_id: str
    application_id: str
    application_title: str
    reminder_type: str
    reminder_date: datetime
    message: str
    is_sent: bool

class DocumentResponse(BaseModel):
    """Model for document response"""
    document_id: str
    application_id: str
    document_type: str
    document_name: str
    version: int
    upload_date: datetime
    is_required: bool
    is_submitted: bool
    file_size: int

class CollaboratorRequest(BaseModel):
    """Model for adding collaborator"""
    collaborator_name: str = Field(..., description="Collaborator name")
    collaborator_email: str = Field(..., description="Collaborator email")
    institution: str = Field(..., description="Collaborator institution")
    role: str = Field(..., description="Collaborator role")
    contribution_description: str = Field(..., description="Contribution description")
    access_level: str = Field(..., description="Access level (view, edit, admin)")

class CollaboratorResponse(BaseModel):
    """Model for collaborator response"""
    collaborator_id: str
    application_id: str
    name: str
    email: str
    institution: str
    role: str
    access_level: str
    invitation_status: str
    contribution_description: str

class InvitationResponse(BaseModel):
    """Model for invitation response"""
    response: str = Field(..., description="Response (accepted or declined)")

# API Endpoints

@router.post("/applications", response_model=Dict[str, str])
async def create_application(
    application: ApplicationCreate,
    user_id: str = Query(..., description="User ID")
):
    """Create a new grant application"""
    try:
        application_id = await grant_service.create_application(
            user_id=user_id,
            funding_opportunity_id=application.funding_opportunity_id,
            application_title=application.application_title,
            project_description=application.project_description,
            requested_amount=application.requested_amount,
            project_duration_months=application.project_duration_months
        )
        
        return {"application_id": application_id, "message": "Grant application created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating application: {str(e)}")

@router.get("/applications", response_model=List[ApplicationSummaryResponse])
async def get_applications(
    user_id: str = Query(..., description="User ID"),
    status_filter: Optional[str] = Query(None, description="Filter by status")
):
    """Get user's grant applications"""
    try:
        applications = await grant_service.get_user_applications(
            user_id=user_id,
            status_filter=status_filter
        )
        
        return [
            ApplicationSummaryResponse(
                application_id=app.application_id,
                title=app.title,
                funding_agency=app.funding_agency,
                requested_amount=app.requested_amount,
                deadline=app.deadline,
                status=app.status,
                days_until_deadline=app.days_until_deadline,
                completion_percentage=app.completion_percentage
            )
            for app in applications
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting applications: {str(e)}")

@router.get("/applications/by-agency", response_model=Dict[str, List[ApplicationSummaryResponse]])
async def get_applications_by_agency(
    user_id: str = Query(..., description="User ID")
):
    """Get applications grouped by funding agency"""
    try:
        agency_groups = await grant_service.get_applications_by_agency(user_id)
        
        result = {}
        for agency, apps in agency_groups.items():
            result[agency] = [
                ApplicationSummaryResponse(
                    application_id=app.application_id,
                    title=app.title,
                    funding_agency=app.funding_agency,
                    requested_amount=app.requested_amount,
                    deadline=app.deadline,
                    status=app.status,
                    days_until_deadline=app.days_until_deadline,
                    completion_percentage=app.completion_percentage
                )
                for app in apps
            ]
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting applications by agency: {str(e)}")

@router.put("/applications/{application_id}/status", response_model=Dict[str, str])
async def update_application_status(
    application_id: str,
    status_update: StatusUpdateRequest,
    user_id: str = Query(..., description="User ID")
):
    """Update application status"""
    try:
        await grant_service.update_application_status(
            application_id=application_id,
            new_status=status_update.new_status,
            user_id=user_id,
            notes=status_update.notes,
            external_application_id=status_update.external_application_id
        )
        
        return {"message": "Application status updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")

@router.get("/reminders", response_model=List[DeadlineReminderResponse])
async def get_pending_reminders(
    user_id: str = Query(..., description="User ID")
):
    """Get pending deadline reminders for user"""
    try:
        reminders = await grant_service.get_pending_reminders(user_id)
        
        return [
            DeadlineReminderResponse(
                reminder_id=reminder.reminder_id,
                application_id=reminder.application_id,
                application_title=reminder.application_title,
                reminder_type=reminder.reminder_type,
                reminder_date=reminder.reminder_date,
                message=reminder.message,
                is_sent=reminder.is_sent
            )
            for reminder in reminders
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting reminders: {str(e)}")

@router.post("/reminders/send", response_model=Dict[str, Any])
async def send_deadline_reminders():
    """Send pending deadline reminders (admin endpoint)"""
    try:
        sent_count = await grant_service.send_deadline_reminders()
        return {"sent_count": sent_count, "message": f"Sent {sent_count} deadline reminders"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending reminders: {str(e)}")

# Document Management Endpoints

@router.post("/applications/{application_id}/documents", response_model=Dict[str, str])
async def upload_document(
    application_id: str,
    user_id: str = Query(..., description="User ID")
):
    """Upload application document (requires multipart form data)"""
    if not all([UploadFile, File, Form]):
        raise HTTPException(
            status_code=501, 
            detail="Document upload requires python-multipart to be installed"
        )
    
    # This endpoint would be properly implemented with multipart support
    raise HTTPException(
        status_code=501,
        detail="Document upload endpoint requires multipart form data support"
    )

@router.get("/applications/{application_id}/documents", response_model=List[DocumentResponse])
async def get_application_documents(
    application_id: str,
    user_id: str = Query(..., description="User ID")
):
    """Get all documents for an application"""
    try:
        documents = await grant_service.get_application_documents(application_id, user_id)
        
        return [
            DocumentResponse(
                document_id=doc.document_id,
                application_id=doc.application_id,
                document_type=doc.document_type,
                document_name=doc.document_name,
                version=doc.version,
                upload_date=doc.upload_date,
                is_required=doc.is_required,
                is_submitted=doc.is_submitted,
                file_size=doc.file_size
            )
            for doc in documents
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting documents: {str(e)}")

@router.get("/applications/{application_id}/documents/{document_type}/versions", response_model=List[DocumentResponse])
async def get_document_versions(
    application_id: str,
    document_type: str,
    user_id: str = Query(..., description="User ID")
):
    """Get all versions of a specific document type"""
    try:
        documents = await grant_service.get_document_versions(application_id, document_type, user_id)
        
        return [
            DocumentResponse(
                document_id=doc.document_id,
                application_id=doc.application_id,
                document_type=doc.document_type,
                document_name=doc.document_name,
                version=doc.version,
                upload_date=doc.upload_date,
                is_required=doc.is_required,
                is_submitted=doc.is_submitted,
                file_size=doc.file_size
            )
            for doc in documents
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting document versions: {str(e)}")

@router.put("/documents/{document_id}/submit", response_model=Dict[str, str])
async def submit_document(
    document_id: str,
    user_id: str = Query(..., description="User ID")
):
    """Mark document as submitted"""
    try:
        await grant_service.submit_document(document_id, user_id)
        return {"message": "Document submitted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting document: {str(e)}")

@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    user_id: str = Query(..., description="User ID")
):
    """Download document"""
    try:
        content, filename, file_type = await grant_service.download_document(document_id, user_id)
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type=f"application/{file_type}",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading document: {str(e)}")

# Collaboration Endpoints

@router.post("/applications/{application_id}/collaborators", response_model=Dict[str, str])
async def add_collaborator(
    application_id: str,
    collaborator: CollaboratorRequest,
    user_id: str = Query(..., description="User ID")
):
    """Add collaborator to grant application"""
    try:
        collaborator_id = await grant_service.add_collaborator(
            application_id=application_id,
            collaborator_name=collaborator.collaborator_name,
            collaborator_email=collaborator.collaborator_email,
            institution=collaborator.institution,
            role=collaborator.role,
            contribution_description=collaborator.contribution_description,
            access_level=collaborator.access_level,
            inviter_user_id=user_id
        )
        
        return {"collaborator_id": collaborator_id, "message": "Collaborator added successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding collaborator: {str(e)}")

@router.get("/applications/{application_id}/collaborators", response_model=List[CollaboratorResponse])
async def get_application_collaborators(
    application_id: str,
    user_id: str = Query(..., description="User ID")
):
    """Get collaborators for an application"""
    try:
        collaborators = await grant_service.get_application_collaborators(application_id, user_id)
        
        return [
            CollaboratorResponse(
                collaborator_id=collab.collaborator_id,
                application_id=collab.application_id,
                name=collab.name,
                email=collab.email,
                institution=collab.institution,
                role=collab.role,
                access_level=collab.access_level,
                invitation_status=collab.invitation_status,
                contribution_description=collab.contribution_description
            )
            for collab in collaborators
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting collaborators: {str(e)}")

@router.put("/collaborators/{collaborator_id}/respond", response_model=Dict[str, str])
async def respond_to_invitation(
    collaborator_id: str,
    invitation_response: InvitationResponse,
    user_id: str = Query(..., description="User ID")
):
    """Respond to collaboration invitation"""
    try:
        await grant_service.respond_to_collaboration_invitation(
            collaborator_id=collaborator_id,
            response=invitation_response.response,
            user_id=user_id
        )
        
        return {"message": f"Invitation {invitation_response.response} successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error responding to invitation: {str(e)}")

@router.put("/collaborators/{collaborator_id}/access", response_model=Dict[str, str])
async def update_collaborator_access(
    collaborator_id: str,
    new_access_level: str = Query(..., description="New access level"),
    user_id: str = Query(..., description="User ID")
):
    """Update collaborator access level"""
    try:
        await grant_service.update_collaborator_access(
            collaborator_id=collaborator_id,
            new_access_level=new_access_level,
            user_id=user_id
        )
        
        return {"message": "Collaborator access updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating collaborator access: {str(e)}")