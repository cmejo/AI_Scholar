"""
API endpoints for student progress tracking and institutional reporting
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from core.database import get_db
from services.student_progress_tracking_service import StudentProgressTrackingService

router = APIRouter(prefix="/api/student-progress", tags=["student-progress"])
progress_service = StudentProgressTrackingService()

# Request/Response Models
class CreateProgressRecordRequest(BaseModel):
    student_id: str
    advisor_id: str
    institution_id: str
    project_details: Dict[str, Any]

class CreateProgressRecordResponse(BaseModel):
    progress_id: str
    student_id: str
    advisor_id: str
    project_title: str
    milestones: Dict[str, Any]
    status: str
    created_at: datetime

class StudentProgressResponse(BaseModel):
    student_id: str
    progress_record_id: str
    project_title: str
    advisor_id: str
    progress_status: str
    completion_percentage: float
    milestones: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    recent_activity: Dict[str, Any]
    advisor_feedback: List[Dict[str, Any]]
    last_updated: datetime
    recommendations: List[str]

class UpdateMilestoneRequest(BaseModel):
    milestone_name: str
    status: str
    notes: Optional[str] = None

class UpdateMilestoneResponse(BaseModel):
    progress_id: str
    milestone_name: str
    new_status: str
    completion_percentage: float
    overall_status: str
    updated_at: datetime

class AddFeedbackRequest(BaseModel):
    feedback_type: str
    feedback_text: str
    rating: Optional[int] = None
    milestone_related: Optional[str] = None
    action_required: bool = False
    required_action: Optional[str] = None
    action_deadline: Optional[str] = None
    priority: str = "medium"
    tags: List[str] = []

class AddFeedbackResponse(BaseModel):
    feedback_id: str
    progress_id: str
    feedback_type: str
    rating: Optional[int]
    action_required: bool
    created_at: datetime

class InstitutionalReportResponse(BaseModel):
    institution_id: str
    report_type: str
    generated_at: datetime
    summary_statistics: Dict[str, Any]
    department_breakdown: Dict[str, Any]
    milestone_analysis: Dict[str, Any]
    performance_trends: Dict[str, Any]
    at_risk_students: List[Dict[str, Any]]
    recent_activity: Dict[str, Any]
    individual_progress: Optional[List[Dict[str, Any]]] = None

@router.post("/create", response_model=CreateProgressRecordResponse)
async def create_student_progress_record(
    request: CreateProgressRecordRequest,
    db: Session = Depends(get_db)
):
    """Create a new student progress tracking record"""
    try:
        result = await progress_service.create_student_progress_record(
            request.student_id,
            request.advisor_id,
            request.institution_id,
            request.project_details
        )
        return CreateProgressRecordResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create progress record: {str(e)}")

@router.get("/student/{student_id}", response_model=StudentProgressResponse)
async def get_student_progress(
    student_id: str,
    institution_id: str = Query(..., description="Institution ID"),
    db: Session = Depends(get_db)
):
    """Build comprehensive student research progress monitoring"""
    try:
        result = await progress_service.track_student_progress(student_id, institution_id)
        
        if result.get('status') == 'no_progress_record':
            raise HTTPException(status_code=404, detail="No progress record found for student")
        
        return StudentProgressResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get student progress: {str(e)}")

@router.put("/milestone/{progress_id}", response_model=UpdateMilestoneResponse)
async def update_milestone_status(
    progress_id: str,
    request: UpdateMilestoneRequest,
    db: Session = Depends(get_db)
):
    """Create milestone tracking and deadline management for research projects"""
    try:
        result = await progress_service.update_milestone_status(
            progress_id,
            request.milestone_name,
            request.status,
            request.notes
        )
        return UpdateMilestoneResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update milestone: {str(e)}")

@router.post("/feedback/{progress_id}", response_model=AddFeedbackResponse)
async def add_advisor_feedback(
    progress_id: str,
    advisor_id: str,
    request: AddFeedbackRequest,
    db: Session = Depends(get_db)
):
    """Implement advisor-student communication and feedback systems"""
    try:
        feedback_data = request.dict()
        result = await progress_service.add_advisor_feedback(
            progress_id,
            advisor_id,
            feedback_data
        )
        return AddFeedbackResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add feedback: {str(e)}")

@router.get("/institution/{institution_id}/report", response_model=InstitutionalReportResponse)
async def generate_institutional_report(
    institution_id: str,
    report_type: str = Query("summary", description="Report type: summary or detailed"),
    db: Session = Depends(get_db)
):
    """Add institutional reporting with aggregated student performance metrics"""
    try:
        if report_type not in ["summary", "detailed"]:
            raise HTTPException(status_code=400, detail="Report type must be 'summary' or 'detailed'")
        
        result = await progress_service.generate_institutional_report(institution_id, report_type)
        return InstitutionalReportResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@router.get("/student/{student_id}/milestones")
async def get_student_milestones(
    student_id: str,
    institution_id: str = Query(..., description="Institution ID"),
    db: Session = Depends(get_db)
):
    """Get detailed milestone information for a student"""
    try:
        progress_data = await progress_service.track_student_progress(student_id, institution_id)
        
        if progress_data.get('status') == 'no_progress_record':
            raise HTTPException(status_code=404, detail="No progress record found for student")
        
        milestones = progress_data.get('milestones', {}).get('details', {})
        
        # Add deadline analysis
        milestone_analysis = []
        for name, data in milestones.items():
            deadline = data.get('deadline')
            status = data.get('status', 'not_started')
            
            analysis = {
                'name': name,
                'title': data.get('title', name),
                'description': data.get('description', ''),
                'status': status,
                'deadline': deadline,
                'weight': data.get('weight', 0),
                'notes': data.get('notes', ''),
                'is_overdue': False,
                'days_until_deadline': None
            }
            
            if deadline:
                try:
                    deadline_date = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                    now = datetime.now()
                    days_diff = (deadline_date - now).days
                    
                    analysis['days_until_deadline'] = days_diff
                    analysis['is_overdue'] = days_diff < 0 and status != 'completed'
                except:
                    pass
            
            milestone_analysis.append(analysis)
        
        # Sort by deadline
        milestone_analysis.sort(key=lambda x: x.get('deadline', '9999-12-31'))
        
        return {
            'student_id': student_id,
            'project_title': progress_data.get('project_title'),
            'milestones': milestone_analysis,
            'overall_completion': progress_data.get('completion_percentage', 0),
            'progress_status': progress_data.get('progress_status')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get milestones: {str(e)}")

@router.get("/advisor/{advisor_id}/students")
async def get_advisor_students(
    advisor_id: str,
    institution_id: str = Query(..., description="Institution ID"),
    db: Session = Depends(get_db)
):
    """Get all students assigned to an advisor with their progress summary"""
    try:
        from core.database import StudentProgress
        
        db_session = next(get_db())
        try:
            # Get all students for this advisor
            student_records = db_session.query(StudentProgress).filter(
                StudentProgress.advisor_id == advisor_id,
                StudentProgress.institution_id == institution_id
            ).all()
            
            students_summary = []
            for record in student_records:
                # Get detailed progress for each student
                progress_data = await progress_service.track_student_progress(
                    record.student_id, institution_id
                )
                
                if progress_data.get('status') != 'no_progress_record':
                    students_summary.append({
                        'student_id': record.student_id,
                        'progress_id': record.id,
                        'project_title': record.research_project,
                        'completion_percentage': progress_data.get('completion_percentage', 0),
                        'progress_status': progress_data.get('progress_status'),
                        'last_updated': record.last_update,
                        'milestones_completed': progress_data.get('milestones', {}).get('completed', 0),
                        'milestones_total': progress_data.get('milestones', {}).get('total', 0),
                        'recent_activity_score': progress_data.get('performance_metrics', {}).get('engagement_score', 0)
                    })
            
            return {
                'advisor_id': advisor_id,
                'institution_id': institution_id,
                'total_students': len(students_summary),
                'students': students_summary
            }
            
        finally:
            db_session.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get advisor students: {str(e)}")

@router.get("/institution/{institution_id}/at-risk")
async def get_at_risk_students(
    institution_id: str,
    threshold_days: int = Query(14, description="Days since last update to consider at-risk"),
    completion_threshold: float = Query(0.3, description="Completion percentage threshold"),
    db: Session = Depends(get_db)
):
    """Get students who are at risk based on various criteria"""
    try:
        report = await progress_service.generate_institutional_report(institution_id, "summary")
        
        at_risk_students = report.get('at_risk_students', [])
        
        # Add additional analysis
        for student in at_risk_students:
            # Get detailed progress
            try:
                progress_data = await progress_service.track_student_progress(
                    student['student_id'], institution_id
                )
                
                student['performance_metrics'] = progress_data.get('performance_metrics', {})
                student['recent_activity'] = progress_data.get('recent_activity', {})
                student['recommendations'] = progress_data.get('recommendations', [])
                
            except:
                pass  # Continue with basic info if detailed fetch fails
        
        return {
            'institution_id': institution_id,
            'criteria': {
                'threshold_days': threshold_days,
                'completion_threshold': completion_threshold
            },
            'total_at_risk': len(at_risk_students),
            'at_risk_students': at_risk_students,
            'generated_at': datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get at-risk students: {str(e)}")

@router.get("/institution/{institution_id}/dashboard")
async def get_institutional_dashboard(
    institution_id: str,
    db: Session = Depends(get_db)
):
    """Get comprehensive institutional dashboard data"""
    try:
        # Get detailed institutional report
        report = await progress_service.generate_institutional_report(institution_id, "detailed")
        
        # Calculate additional dashboard metrics
        dashboard_data = {
            'institution_id': institution_id,
            'generated_at': report['generated_at'],
            'overview': {
                'total_students': report['summary_statistics']['total_students'],
                'average_completion': report['summary_statistics']['average_completion'],
                'active_students': report['recent_activity']['active_students'],
                'at_risk_count': len(report['at_risk_students'])
            },
            'status_distribution': report['summary_statistics']['status_distribution'],
            'department_performance': report['department_breakdown'],
            'milestone_completion_rates': report['milestone_analysis'],
            'recent_trends': report['performance_trends'],
            'at_risk_students': report['at_risk_students'][:10],  # Top 10 at-risk
            'top_performers': []
        }
        
        # Identify top performers
        if 'individual_progress' in report:
            top_performers = sorted(
                report['individual_progress'],
                key=lambda x: x['completion_percentage'],
                reverse=True
            )[:10]
            
            dashboard_data['top_performers'] = top_performers
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")