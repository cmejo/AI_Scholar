"""
Student Progress Tracking Service for Enterprise Features
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import json
import statistics
from collections import defaultdict

from core.database import (
    get_db, Institution, StudentProgress, AdvisorFeedback, User, UserRole,
    Quiz, QuizAttempt, LearningProgress, StudySession, Document, Message
)

class StudentProgressTrackingService:
    """Service for tracking and managing student research progress"""
    
    def __init__(self):
        self.milestone_types = {
            'literature_review': {'weight': 0.15, 'typical_duration_days': 30},
            'research_proposal': {'weight': 0.20, 'typical_duration_days': 45},
            'data_collection': {'weight': 0.25, 'typical_duration_days': 60},
            'analysis': {'weight': 0.20, 'typical_duration_days': 45},
            'writing': {'weight': 0.15, 'typical_duration_days': 30},
            'defense_preparation': {'weight': 0.05, 'typical_duration_days': 14}
        }
    
    async def create_student_progress_record(self, student_id: str, advisor_id: str, 
                                           institution_id: str, project_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new student progress tracking record"""
        db = next(get_db())
        try:
            # Validate student and advisor exist
            student = db.query(User).filter(User.id == student_id).first()
            advisor = db.query(User).filter(User.id == advisor_id).first()
            
            if not student or not advisor:
                raise ValueError("Student or advisor not found")
            
            # Generate default milestones based on project type
            project_type = project_details.get('project_type', 'research')
            milestones = await self._generate_default_milestones(project_type, project_details)
            
            # Create progress record
            progress_record = StudentProgress(
                student_id=student_id,
                advisor_id=advisor_id,
                institution_id=institution_id,
                research_project=project_details.get('title', 'Untitled Research Project'),
                milestones=milestones,
                progress_status='on_track',
                completion_percentage=0.0,
                notes=project_details.get('initial_notes', ''),
                progress_metadata={
                    'project_type': project_type,
                    'start_date': datetime.now().isoformat(),
                    'expected_completion': project_details.get('expected_completion'),
                    'research_area': project_details.get('research_area'),
                    'keywords': project_details.get('keywords', [])
                }
            )
            
            db.add(progress_record)
            db.commit()
            db.refresh(progress_record)
            
            return {
                'progress_id': progress_record.id,
                'student_id': student_id,
                'advisor_id': advisor_id,
                'project_title': progress_record.research_project,
                'milestones': milestones,
                'status': 'created',
                'created_at': progress_record.last_update
            }
            
        finally:
            db.close()
    
    async def track_student_progress(self, student_id: str, institution_id: str) -> Dict[str, Any]:
        """Build comprehensive student research progress monitoring"""
        db = next(get_db())
        try:
            # Get student progress record
            progress_record = db.query(StudentProgress).filter(
                and_(
                    StudentProgress.student_id == student_id,
                    StudentProgress.institution_id == institution_id
                )
            ).first()
            
            if not progress_record:
                return {
                    'student_id': student_id,
                    'status': 'no_progress_record',
                    'message': 'No progress record found for student'
                }
            
            # Get student's learning activities
            learning_progress = db.query(LearningProgress).filter(
                LearningProgress.user_id == student_id
            ).all()
            
            study_sessions = db.query(StudySession).filter(
                StudySession.user_id == student_id
            ).order_by(StudySession.started_at.desc()).limit(10).all()
            
            quiz_attempts = db.query(QuizAttempt).filter(
                QuizAttempt.user_id == student_id
            ).order_by(QuizAttempt.started_at.desc()).limit(10).all()
            
            # Get documents uploaded by student
            documents = db.query(Document).filter(
                Document.user_id == student_id
            ).order_by(Document.created_at.desc()).limit(10).all()
            
            # Calculate progress metrics
            milestones = progress_record.milestones or {}
            completed_milestones = sum(1 for m in milestones.values() if m.get('status') == 'completed')
            total_milestones = len(milestones)
            
            # Calculate weighted completion percentage
            weighted_completion = 0.0
            for milestone_name, milestone_data in milestones.items():
                if milestone_data.get('status') == 'completed':
                    weight = self.milestone_types.get(milestone_name, {}).get('weight', 1.0 / total_milestones)
                    weighted_completion += weight
            
            # Analyze recent activity
            recent_activity = await self._analyze_recent_activity(
                student_id, study_sessions, quiz_attempts, documents
            )
            
            # Calculate performance metrics
            performance_metrics = await self._calculate_performance_metrics(
                learning_progress, quiz_attempts, study_sessions
            )
            
            # Determine progress status
            progress_status = await self._determine_progress_status(
                progress_record, milestones, recent_activity, performance_metrics
            )
            
            # Get advisor feedback
            advisor_feedback = db.query(AdvisorFeedback).filter(
                AdvisorFeedback.student_progress_id == progress_record.id
            ).order_by(AdvisorFeedback.created_at.desc()).limit(5).all()
            
            return {
                'student_id': student_id,
                'progress_record_id': progress_record.id,
                'project_title': progress_record.research_project,
                'advisor_id': progress_record.advisor_id,
                'progress_status': progress_status,
                'completion_percentage': weighted_completion * 100,
                'milestones': {
                    'total': total_milestones,
                    'completed': completed_milestones,
                    'details': milestones
                },
                'performance_metrics': performance_metrics,
                'recent_activity': recent_activity,
                'advisor_feedback': [
                    {
                        'id': fb.id,
                        'feedback_type': fb.feedback_type,
                        'feedback_text': fb.feedback_text,
                        'rating': fb.rating,
                        'created_at': fb.created_at
                    } for fb in advisor_feedback
                ],
                'last_updated': progress_record.last_update,
                'recommendations': await self._generate_progress_recommendations(
                    progress_record, performance_metrics, recent_activity
                )
            }
            
        finally:
            db.close()
    
    async def update_milestone_status(self, progress_id: str, milestone_name: str, 
                                    status: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Create milestone tracking and deadline management for research projects"""
        db = next(get_db())
        try:
            progress_record = db.query(StudentProgress).filter(
                StudentProgress.id == progress_id
            ).first()
            
            if not progress_record:
                raise ValueError("Progress record not found")
            
            milestones = progress_record.milestones or {}
            
            if milestone_name not in milestones:
                raise ValueError(f"Milestone '{milestone_name}' not found")
            
            # Update milestone status
            milestones[milestone_name]['status'] = status
            milestones[milestone_name]['updated_at'] = datetime.now().isoformat()
            
            if notes:
                milestones[milestone_name]['notes'] = notes
            
            if status == 'completed':
                milestones[milestone_name]['completed_at'] = datetime.now().isoformat()
            
            # Update progress record
            progress_record.milestones = milestones
            progress_record.last_update = datetime.now()
            
            # Recalculate completion percentage
            completed_count = sum(1 for m in milestones.values() if m.get('status') == 'completed')
            total_count = len(milestones)
            
            # Calculate weighted completion
            weighted_completion = 0.0
            for m_name, m_data in milestones.items():
                if m_data.get('status') == 'completed':
                    weight = self.milestone_types.get(m_name, {}).get('weight', 1.0 / total_count)
                    weighted_completion += weight
            
            progress_record.completion_percentage = weighted_completion
            
            # Update overall progress status
            if weighted_completion >= 1.0:
                progress_record.progress_status = 'completed'
            elif weighted_completion >= 0.8:
                progress_record.progress_status = 'ahead'
            elif self._is_behind_schedule(milestones):
                progress_record.progress_status = 'behind'
            else:
                progress_record.progress_status = 'on_track'
            
            db.commit()
            
            return {
                'progress_id': progress_id,
                'milestone_name': milestone_name,
                'new_status': status,
                'completion_percentage': weighted_completion * 100,
                'overall_status': progress_record.progress_status,
                'updated_at': progress_record.last_update
            }
            
        finally:
            db.close()
    
    async def add_advisor_feedback(self, progress_id: str, advisor_id: str, 
                                 feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Implement advisor-student communication and feedback systems"""
        db = next(get_db())
        try:
            # Validate progress record and advisor
            progress_record = db.query(StudentProgress).filter(
                StudentProgress.id == progress_id
            ).first()
            
            if not progress_record:
                raise ValueError("Progress record not found")
            
            if progress_record.advisor_id != advisor_id:
                raise ValueError("Advisor not authorized for this student")
            
            # Create feedback record
            feedback = AdvisorFeedback(
                student_progress_id=progress_id,
                advisor_id=advisor_id,
                feedback_type=feedback_data.get('feedback_type', 'general_feedback'),
                feedback_text=feedback_data.get('feedback_text', ''),
                rating=feedback_data.get('rating'),
                feedback_metadata={
                    'milestone_related': feedback_data.get('milestone_related'),
                    'action_required': feedback_data.get('action_required', False),
                    'priority': feedback_data.get('priority', 'medium'),
                    'tags': feedback_data.get('tags', [])
                }
            )
            
            db.add(feedback)
            db.commit()
            db.refresh(feedback)
            
            # Update progress record with feedback summary
            if feedback_data.get('action_required'):
                progress_metadata = progress_record.progress_metadata or {}
                progress_metadata['pending_actions'] = progress_metadata.get('pending_actions', [])
                progress_metadata['pending_actions'].append({
                    'feedback_id': feedback.id,
                    'action': feedback_data.get('required_action'),
                    'deadline': feedback_data.get('action_deadline'),
                    'created_at': datetime.now().isoformat()
                })
                progress_record.progress_metadata = progress_metadata
                progress_record.last_update = datetime.now()
                db.commit()
            
            return {
                'feedback_id': feedback.id,
                'progress_id': progress_id,
                'feedback_type': feedback.feedback_type,
                'rating': feedback.rating,
                'action_required': feedback_data.get('action_required', False),
                'created_at': feedback.created_at
            }
            
        finally:
            db.close()
    
    async def generate_institutional_report(self, institution_id: str, 
                                          report_type: str = 'summary') -> Dict[str, Any]:
        """Add institutional reporting with aggregated student performance metrics"""
        db = next(get_db())
        try:
            # Get all student progress records for the institution
            progress_records = db.query(StudentProgress).filter(
                StudentProgress.institution_id == institution_id
            ).all()
            
            if not progress_records:
                return {
                    'institution_id': institution_id,
                    'report_type': report_type,
                    'message': 'No student progress records found',
                    'generated_at': datetime.now()
                }
            
            # Calculate aggregate metrics
            total_students = len(progress_records)
            completion_rates = [p.completion_percentage for p in progress_records]
            avg_completion = statistics.mean(completion_rates) if completion_rates else 0
            
            # Status distribution
            status_distribution = defaultdict(int)
            for record in progress_records:
                status_distribution[record.progress_status] += 1
            
            # Department breakdown
            department_stats = defaultdict(lambda: {'count': 0, 'avg_completion': 0, 'completions': []})
            
            for record in progress_records:
                # Get student's department
                student_role = db.query(UserRole).filter(
                    and_(
                        UserRole.user_id == record.student_id,
                        UserRole.institution_id == institution_id
                    )
                ).first()
                
                dept = student_role.department if student_role else 'Unknown'
                department_stats[dept]['count'] += 1
                department_stats[dept]['completions'].append(record.completion_percentage)
            
            # Calculate department averages
            for dept, stats in department_stats.items():
                if stats['completions']:
                    stats['avg_completion'] = statistics.mean(stats['completions'])
                    stats['completion_range'] = {
                        'min': min(stats['completions']),
                        'max': max(stats['completions'])
                    }
                del stats['completions']  # Remove raw data from report
            
            # Milestone analysis
            milestone_completion_rates = defaultdict(list)
            for record in progress_records:
                milestones = record.milestones or {}
                for milestone_name, milestone_data in milestones.items():
                    is_completed = milestone_data.get('status') == 'completed'
                    milestone_completion_rates[milestone_name].append(is_completed)
            
            milestone_stats = {}
            for milestone_name, completions in milestone_completion_rates.items():
                completion_rate = sum(completions) / len(completions) * 100 if completions else 0
                milestone_stats[milestone_name] = {
                    'completion_rate': completion_rate,
                    'total_students': len(completions)
                }
            
            # Recent activity analysis
            recent_feedback = db.query(AdvisorFeedback).filter(
                AdvisorFeedback.created_at >= datetime.now() - timedelta(days=30)
            ).join(StudentProgress).filter(
                StudentProgress.institution_id == institution_id
            ).all()
            
            # Performance trends
            performance_trends = await self._analyze_institutional_trends(
                progress_records, recent_feedback, db
            )
            
            # At-risk students identification
            at_risk_students = []
            for record in progress_records:
                if (record.progress_status == 'behind' or 
                    record.completion_percentage < 0.3 or
                    (datetime.now() - record.last_update).days > 14):
                    
                    at_risk_students.append({
                        'student_id': record.student_id,
                        'project_title': record.research_project,
                        'completion_percentage': record.completion_percentage,
                        'status': record.progress_status,
                        'days_since_update': (datetime.now() - record.last_update).days,
                        'advisor_id': record.advisor_id
                    })
            
            report = {
                'institution_id': institution_id,
                'report_type': report_type,
                'generated_at': datetime.now(),
                'summary_statistics': {
                    'total_students': total_students,
                    'average_completion': avg_completion,
                    'status_distribution': dict(status_distribution),
                    'completion_rate_range': {
                        'min': min(completion_rates) if completion_rates else 0,
                        'max': max(completion_rates) if completion_rates else 0
                    }
                },
                'department_breakdown': dict(department_stats),
                'milestone_analysis': milestone_stats,
                'performance_trends': performance_trends,
                'at_risk_students': at_risk_students,
                'recent_activity': {
                    'feedback_count_30_days': len(recent_feedback),
                    'active_students': len([r for r in progress_records 
                                          if (datetime.now() - r.last_update).days <= 7])
                }
            }
            
            # Add detailed breakdown if requested
            if report_type == 'detailed':
                report['individual_progress'] = [
                    {
                        'student_id': record.student_id,
                        'project_title': record.research_project,
                        'advisor_id': record.advisor_id,
                        'completion_percentage': record.completion_percentage,
                        'status': record.progress_status,
                        'last_update': record.last_update,
                        'milestone_count': len(record.milestones or {}),
                        'completed_milestones': sum(1 for m in (record.milestones or {}).values() 
                                                  if m.get('status') == 'completed')
                    } for record in progress_records
                ]
            
            return report
            
        finally:
            db.close()
    
    async def _generate_default_milestones(self, project_type: str, 
                                         project_details: Dict[str, Any]) -> Dict[str, Any]:
        """Generate default milestones based on project type"""
        base_milestones = {
            'literature_review': {
                'title': 'Literature Review',
                'description': 'Complete comprehensive literature review',
                'status': 'not_started',
                'deadline': (datetime.now() + timedelta(days=30)).isoformat(),
                'weight': 0.15
            },
            'research_proposal': {
                'title': 'Research Proposal',
                'description': 'Submit research proposal for approval',
                'status': 'not_started',
                'deadline': (datetime.now() + timedelta(days=75)).isoformat(),
                'weight': 0.20
            },
            'data_collection': {
                'title': 'Data Collection',
                'description': 'Collect and organize research data',
                'status': 'not_started',
                'deadline': (datetime.now() + timedelta(days=135)).isoformat(),
                'weight': 0.25
            },
            'analysis': {
                'title': 'Data Analysis',
                'description': 'Analyze collected data and generate insights',
                'status': 'not_started',
                'deadline': (datetime.now() + timedelta(days=180)).isoformat(),
                'weight': 0.20
            },
            'writing': {
                'title': 'Thesis Writing',
                'description': 'Write and revise thesis document',
                'status': 'not_started',
                'deadline': (datetime.now() + timedelta(days=210)).isoformat(),
                'weight': 0.15
            },
            'defense_preparation': {
                'title': 'Defense Preparation',
                'description': 'Prepare for thesis defense',
                'status': 'not_started',
                'deadline': (datetime.now() + timedelta(days=224)).isoformat(),
                'weight': 0.05
            }
        }
        
        # Customize based on project type
        if project_type == 'coursework':
            # Shorter timeline for coursework projects
            for milestone in base_milestones.values():
                current_deadline = datetime.fromisoformat(milestone['deadline'])
                new_deadline = datetime.now() + (current_deadline - datetime.now()) * 0.5
                milestone['deadline'] = new_deadline.isoformat()
        
        elif project_type == 'dissertation':
            # Longer timeline for dissertation
            for milestone in base_milestones.values():
                current_deadline = datetime.fromisoformat(milestone['deadline'])
                new_deadline = datetime.now() + (current_deadline - datetime.now()) * 2
                milestone['deadline'] = new_deadline.isoformat()
        
        return base_milestones
    
    async def _analyze_recent_activity(self, student_id: str, study_sessions: List, 
                                     quiz_attempts: List, documents: List) -> Dict[str, Any]:
        """Analyze student's recent activity"""
        recent_activity = {
            'study_sessions': {
                'count_7_days': 0,
                'count_30_days': len(study_sessions),
                'avg_session_duration': 0,
                'total_study_time': 0
            },
            'quiz_performance': {
                'attempts_7_days': 0,
                'attempts_30_days': len(quiz_attempts),
                'avg_score': 0,
                'improvement_trend': 'stable'
            },
            'document_activity': {
                'uploads_7_days': 0,
                'uploads_30_days': len(documents),
                'total_documents': len(documents)
            }
        }
        
        # Analyze study sessions
        week_ago = datetime.now() - timedelta(days=7)
        recent_sessions = [s for s in study_sessions if s.started_at >= week_ago]
        recent_activity['study_sessions']['count_7_days'] = len(recent_sessions)
        
        if study_sessions:
            durations = []
            for session in study_sessions:
                if session.ended_at:
                    duration = (session.ended_at - session.started_at).total_seconds() / 60
                    durations.append(duration)
            
            if durations:
                recent_activity['study_sessions']['avg_session_duration'] = statistics.mean(durations)
                recent_activity['study_sessions']['total_study_time'] = sum(durations)
        
        # Analyze quiz performance
        recent_quizzes = [q for q in quiz_attempts if q.started_at >= week_ago]
        recent_activity['quiz_performance']['attempts_7_days'] = len(recent_quizzes)
        
        if quiz_attempts:
            scores = [q.score for q in quiz_attempts if q.score is not None]
            if scores:
                recent_activity['quiz_performance']['avg_score'] = statistics.mean(scores)
                
                # Calculate improvement trend
                if len(scores) >= 3:
                    recent_scores = scores[-3:]
                    early_scores = scores[:-3] if len(scores) > 3 else scores[:1]
                    
                    if statistics.mean(recent_scores) > statistics.mean(early_scores):
                        recent_activity['quiz_performance']['improvement_trend'] = 'improving'
                    elif statistics.mean(recent_scores) < statistics.mean(early_scores):
                        recent_activity['quiz_performance']['improvement_trend'] = 'declining'
        
        # Analyze document activity
        recent_docs = [d for d in documents if d.created_at >= week_ago]
        recent_activity['document_activity']['uploads_7_days'] = len(recent_docs)
        
        return recent_activity
    
    async def _calculate_performance_metrics(self, learning_progress: List, 
                                           quiz_attempts: List, study_sessions: List) -> Dict[str, Any]:
        """Calculate student performance metrics"""
        metrics = {
            'learning_competency': 0.0,
            'engagement_score': 0.0,
            'consistency_score': 0.0,
            'improvement_rate': 0.0
        }
        
        # Calculate learning competency
        if learning_progress:
            competency_levels = [lp.competency_level for lp in learning_progress if lp.competency_level]
            if competency_levels:
                metrics['learning_competency'] = statistics.mean(competency_levels)
        
        # Calculate engagement score based on activity frequency
        total_activities = len(quiz_attempts) + len(study_sessions)
        days_active = len(set(
            [qa.started_at.date() for qa in quiz_attempts] +
            [ss.started_at.date() for ss in study_sessions]
        ))
        
        if days_active > 0:
            metrics['engagement_score'] = min(1.0, total_activities / (days_active * 2))  # Normalize to 0-1
        
        # Calculate consistency score
        if study_sessions:
            session_dates = [s.started_at.date() for s in study_sessions]
            date_range = (max(session_dates) - min(session_dates)).days + 1
            unique_days = len(set(session_dates))
            metrics['consistency_score'] = unique_days / date_range if date_range > 0 else 0
        
        # Calculate improvement rate
        if quiz_attempts and len(quiz_attempts) >= 2:
            scores = [qa.score for qa in quiz_attempts if qa.score is not None]
            if len(scores) >= 2:
                # Simple linear trend
                x_values = list(range(len(scores)))
                y_values = scores
                
                if len(x_values) > 1:
                    # Calculate slope
                    n = len(x_values)
                    x_mean = statistics.mean(x_values)
                    y_mean = statistics.mean(y_values)
                    
                    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
                    denominator = sum((x - x_mean) ** 2 for x in x_values)
                    
                    if denominator != 0:
                        slope = numerator / denominator
                        metrics['improvement_rate'] = max(-1.0, min(1.0, slope / 10))  # Normalize
        
        return metrics
    
    async def _determine_progress_status(self, progress_record: StudentProgress, 
                                       milestones: Dict, recent_activity: Dict, 
                                       performance_metrics: Dict) -> str:
        """Determine overall progress status"""
        # Check if behind schedule
        if self._is_behind_schedule(milestones):
            return 'behind'
        
        # Check if ahead of schedule
        if progress_record.completion_percentage > 0.8:
            return 'ahead'
        
        # Check engagement and activity levels
        if (recent_activity['study_sessions']['count_7_days'] == 0 and
            recent_activity['quiz_performance']['attempts_7_days'] == 0 and
            recent_activity['document_activity']['uploads_7_days'] == 0):
            return 'inactive'
        
        # Check performance trends
        if (performance_metrics['improvement_rate'] < -0.2 or
            performance_metrics['engagement_score'] < 0.3):
            return 'at_risk'
        
        return 'on_track'
    
    def _is_behind_schedule(self, milestones: Dict) -> bool:
        """Check if student is behind schedule based on milestone deadlines"""
        now = datetime.now()
        
        for milestone_data in milestones.values():
            deadline_str = milestone_data.get('deadline')
            status = milestone_data.get('status', 'not_started')
            
            if deadline_str and status != 'completed':
                try:
                    deadline = datetime.fromisoformat(deadline_str)
                    if now > deadline:
                        return True
                except ValueError:
                    continue
        
        return False
    
    async def _generate_progress_recommendations(self, progress_record: StudentProgress,
                                               performance_metrics: Dict, 
                                               recent_activity: Dict) -> List[Dict[str, Any]]:
        """Generate recommendations for student progress improvement"""
        recommendations = []
        
        # Low engagement recommendations
        if performance_metrics['engagement_score'] < 0.4:
            recommendations.append({
                'type': 'engagement',
                'priority': 'high',
                'title': 'Increase Study Activity',
                'description': 'Your engagement score is low. Try to study more regularly.',
                'suggested_actions': [
                    'Set daily study goals',
                    'Use the quiz system more frequently',
                    'Upload research documents regularly'
                ]
            })
        
        # Consistency recommendations
        if performance_metrics['consistency_score'] < 0.3:
            recommendations.append({
                'type': 'consistency',
                'priority': 'medium',
                'title': 'Improve Study Consistency',
                'description': 'Try to maintain a more regular study schedule.',
                'suggested_actions': [
                    'Create a weekly study schedule',
                    'Set reminders for study sessions',
                    'Track your daily progress'
                ]
            })
        
        # Performance improvement recommendations
        if performance_metrics['improvement_rate'] < 0:
            recommendations.append({
                'type': 'performance',
                'priority': 'high',
                'title': 'Focus on Learning Improvement',
                'description': 'Your recent performance shows a declining trend.',
                'suggested_actions': [
                    'Review challenging topics',
                    'Seek help from advisor',
                    'Use additional learning resources'
                ]
            })
        
        # Milestone-based recommendations
        milestones = progress_record.milestones or {}
        overdue_milestones = []
        
        for name, data in milestones.items():
            if data.get('status') != 'completed':
                deadline_str = data.get('deadline')
                if deadline_str:
                    try:
                        deadline = datetime.fromisoformat(deadline_str)
                        if datetime.now() > deadline:
                            overdue_milestones.append(name)
                    except ValueError:
                        continue
        
        if overdue_milestones:
            recommendations.append({
                'type': 'milestone',
                'priority': 'critical',
                'title': 'Address Overdue Milestones',
                'description': f'You have {len(overdue_milestones)} overdue milestones.',
                'suggested_actions': [
                    f'Focus on completing: {", ".join(overdue_milestones)}',
                    'Discuss timeline adjustments with advisor',
                    'Break down large milestones into smaller tasks'
                ]
            })
        
        return recommendations
    
    async def _analyze_institutional_trends(self, progress_records: List, 
                                          recent_feedback: List, db: Session) -> Dict[str, Any]:
        """Analyze institutional performance trends"""
        trends = {
            'completion_trend': 'stable',
            'engagement_trend': 'stable',
            'feedback_frequency': 0,
            'common_challenges': []
        }
        
        # Analyze completion trends over time
        if len(progress_records) > 1:
            recent_completions = [p.completion_percentage for p in progress_records 
                                if (datetime.now() - p.last_update).days <= 30]
            older_completions = [p.completion_percentage for p in progress_records 
                               if (datetime.now() - p.last_update).days > 30]
            
            if recent_completions and older_completions:
                recent_avg = statistics.mean(recent_completions)
                older_avg = statistics.mean(older_completions)
                
                if recent_avg > older_avg * 1.1:
                    trends['completion_trend'] = 'improving'
                elif recent_avg < older_avg * 0.9:
                    trends['completion_trend'] = 'declining'
        
        # Analyze feedback frequency
        trends['feedback_frequency'] = len(recent_feedback) / len(progress_records) if progress_records else 0
        
        # Identify common challenges from feedback
        challenge_keywords = defaultdict(int)
        for feedback in recent_feedback:
            if feedback.feedback_text:
                text = feedback.feedback_text.lower()
                # Simple keyword extraction
                keywords = ['deadline', 'behind', 'struggling', 'difficulty', 'challenge', 'problem']
                for keyword in keywords:
                    if keyword in text:
                        challenge_keywords[keyword] += 1
        
        # Get top challenges
        trends['common_challenges'] = sorted(challenge_keywords.items(), 
                                           key=lambda x: x[1], reverse=True)[:5]
        
        return trends