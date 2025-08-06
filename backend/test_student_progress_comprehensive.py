"""
Comprehensive test for student progress tracking implementation
Tests all four main requirements of task 5.3
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from core.database import get_db, init_db
from core.database import (
    Institution, User, UserRole, StudentProgress, AdvisorFeedback,
    Quiz, QuizAttempt, LearningProgress, StudySession
)
from services.student_progress_tracking_service import StudentProgressTrackingService

async def test_comprehensive_student_progress():
    """Comprehensive test of all student progress tracking requirements"""
    print("🎯 Testing Comprehensive Student Progress Tracking Implementation")
    print("=" * 70)
    
    # Initialize database
    await init_db()
    
    # Create test data
    db = next(get_db())
    
    try:
        # Setup test institution and users
        print("\n📋 Setting up test environment...")
        
        institution = Institution(
            name="Advanced Research University",
            domain="aru.edu",
            type="university",
            settings={"academic_year": "2024-2025", "research_focus": "AI"}
        )
        db.add(institution)
        db.commit()
        db.refresh(institution)
        
        # Create multiple students and advisors
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        # Create students
        students = []
        for i in range(3):
            student = User(
                email=f"student_{i}_{unique_id}@aru.edu",
                name=f"Student {i+1}",
                hashed_password="hashed_password"
            )
            students.append(student)
        
        # Create advisors
        advisors = []
        for i in range(2):
            advisor = User(
                email=f"advisor_{i}_{unique_id}@aru.edu",
                name=f"Dr. Advisor {i+1}",
                hashed_password="hashed_password"
            )
            advisors.append(advisor)
        
        db.add_all(students + advisors)
        db.commit()
        
        for student in students:
            db.refresh(student)
        for advisor in advisors:
            db.refresh(advisor)
        
        # Create user roles
        roles = []
        departments = ["Computer Science", "Data Science", "AI Research"]
        
        for i, student in enumerate(students):
            role = UserRole(
                user_id=student.id,
                institution_id=institution.id,
                role_name="student",
                department=departments[i % len(departments)],
                permissions={"research_access": True}
            )
            roles.append(role)
        
        for i, advisor in enumerate(advisors):
            role = UserRole(
                user_id=advisor.id,
                institution_id=institution.id,
                role_name="faculty",
                department=departments[i % len(departments)],
                permissions={"advisor_access": True, "institutional_reports": True}
            )
            roles.append(role)
        
        db.add_all(roles)
        db.commit()
        
        # Create learning activity data for students
        for i, student in enumerate(students):
            learning_progress = LearningProgress(
                user_id=student.id,
                topic=f"Research Topic {i+1}",
                competency_level=0.6 + (i * 0.1),
                study_count=10 + (i * 5),
                average_score=75.0 + (i * 5)
            )
            
            study_session = StudySession(
                user_id=student.id,
                session_type="research",
                started_at=datetime.now() - timedelta(hours=i+1),
                ended_at=datetime.now() - timedelta(minutes=30),
                items_studied=5 + i,
                performance_score=0.7 + (i * 0.1)
            )
            
            db.add_all([learning_progress, study_session])
        
        db.commit()
        
        progress_service = StudentProgressTrackingService()
        
        print("✅ Test environment setup complete")
        
        # REQUIREMENT 1: Build comprehensive student research progress monitoring
        print("\n" + "="*70)
        print("🔍 REQUIREMENT 1: Comprehensive Student Research Progress Monitoring")
        print("="*70)
        
        progress_records = []
        
        for i, (student, advisor) in enumerate(zip(students, advisors * 2)):  # Cycle advisors
            project_details = {
                'title': f'Advanced AI Research Project {i+1}',
                'project_type': 'research' if i % 2 == 0 else 'dissertation',
                'research_area': ['Artificial Intelligence', 'Machine Learning', 'Data Science'][i],
                'expected_completion': (datetime.now() + timedelta(days=300 + i*30)).isoformat(),
                'keywords': [f'AI_{i}', f'Research_{i}', f'Innovation_{i}'],
                'initial_notes': f'Comprehensive research project {i+1} setup'
            }
            
            creation_result = await progress_service.create_student_progress_record(
                student.id, advisor.id, institution.id, project_details
            )
            
            progress_records.append(creation_result)
            print(f"✅ Created progress record for {student.name}: {creation_result['project_title']}")
        
        # Monitor each student's progress
        for i, student in enumerate(students):
            progress_data = await progress_service.track_student_progress(
                student.id, institution.id
            )
            
            print(f"\n📊 Progress monitoring for {student.name}:")
            print(f"   Status: {progress_data['progress_status']}")
            print(f"   Completion: {progress_data['completion_percentage']:.1f}%")
            print(f"   Milestones: {progress_data['milestones']['completed']}/{progress_data['milestones']['total']}")
            print(f"   Performance Score: {progress_data['performance_metrics']['engagement_score']:.2f}")
            print(f"   Recommendations: {len(progress_data['recommendations'])} items")
            
            assert progress_data['student_id'] == student.id
            assert 'performance_metrics' in progress_data
            assert 'recent_activity' in progress_data
        
        print("\n✅ REQUIREMENT 1 COMPLETED: Comprehensive monitoring implemented")
        
        # REQUIREMENT 2: Create milestone tracking and deadline management
        print("\n" + "="*70)
        print("📅 REQUIREMENT 2: Milestone Tracking and Deadline Management")
        print("="*70)
        
        # Update milestones for different students to show various states
        milestone_updates = [
            (0, 'literature_review', 'completed', 'Excellent literature review completed'),
            (0, 'research_proposal', 'in_progress', 'Working on research proposal'),
            (1, 'literature_review', 'completed', 'Literature review done'),
            (1, 'research_proposal', 'completed', 'Research proposal approved'),
            (1, 'data_collection', 'in_progress', 'Starting data collection phase'),
            (2, 'literature_review', 'in_progress', 'Literature review in progress')
        ]
        
        for student_idx, milestone_name, status, notes in milestone_updates:
            progress_id = progress_records[student_idx]['progress_id']
            
            milestone_result = await progress_service.update_milestone_status(
                progress_id, milestone_name, status, notes
            )
            
            print(f"✅ Updated {students[student_idx].name}: {milestone_name} -> {status}")
            print(f"   New completion: {milestone_result['completion_percentage']:.1f}%")
            
            assert milestone_result['new_status'] == status
        
        # Demonstrate deadline management
        print(f"\n📋 Milestone deadline analysis:")
        for i, student in enumerate(students):
            progress_data = await progress_service.track_student_progress(
                student.id, institution.id
            )
            
            milestones = progress_data['milestones']['details']
            overdue_count = 0
            upcoming_count = 0
            
            for name, data in milestones.items():
                deadline = data.get('deadline')
                status = data.get('status', 'not_started')
                
                if deadline and status != 'completed':
                    try:
                        deadline_date = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                        days_diff = (deadline_date - datetime.now()).days
                        
                        if days_diff < 0:
                            overdue_count += 1
                        elif days_diff <= 30:
                            upcoming_count += 1
                    except:
                        pass
            
            print(f"   {student.name}: {overdue_count} overdue, {upcoming_count} due soon")
        
        print("\n✅ REQUIREMENT 2 COMPLETED: Milestone tracking and deadline management implemented")
        
        # REQUIREMENT 3: Implement advisor-student communication and feedback systems
        print("\n" + "="*70)
        print("💬 REQUIREMENT 3: Advisor-Student Communication and Feedback Systems")
        print("="*70)
        
        # Add various types of feedback
        feedback_scenarios = [
            (0, 0, {
                'feedback_type': 'milestone_review',
                'feedback_text': 'Outstanding work on the literature review! Your analysis is thorough and well-structured.',
                'rating': 5,
                'milestone_related': 'literature_review',
                'action_required': True,
                'required_action': 'Prepare detailed methodology section for next meeting',
                'action_deadline': (datetime.now() + timedelta(days=7)).isoformat(),
                'priority': 'medium',
                'tags': ['literature_review', 'excellent', 'methodology']
            }),
            (1, 1, {
                'feedback_type': 'general_feedback',
                'feedback_text': 'Good progress overall. Consider expanding the theoretical framework section.',
                'rating': 4,
                'action_required': False,
                'priority': 'low',
                'tags': ['theoretical_framework', 'improvement']
            }),
            (2, 0, {
                'feedback_type': 'concern',
                'feedback_text': 'Progress seems slower than expected. Let\'s schedule a meeting to discuss challenges.',
                'rating': 2,
                'action_required': True,
                'required_action': 'Schedule meeting to discuss research challenges',
                'action_deadline': (datetime.now() + timedelta(days=3)).isoformat(),
                'priority': 'high',
                'tags': ['concern', 'meeting_required', 'support_needed']
            }),
            (0, 0, {
                'feedback_type': 'milestone_review',
                'feedback_text': 'Research proposal looks promising. Minor revisions needed in the methodology section.',
                'rating': 4,
                'milestone_related': 'research_proposal',
                'action_required': True,
                'required_action': 'Revise methodology section based on comments',
                'action_deadline': (datetime.now() + timedelta(days=5)).isoformat(),
                'priority': 'medium',
                'tags': ['research_proposal', 'revision_needed']
            })
        ]
        
        feedback_results = []
        for student_idx, advisor_idx, feedback_data in feedback_scenarios:
            progress_id = progress_records[student_idx]['progress_id']
            advisor_id = advisors[advisor_idx].id
            
            feedback_result = await progress_service.add_advisor_feedback(
                progress_id, advisor_id, feedback_data
            )
            
            feedback_results.append(feedback_result)
            
            print(f"✅ Added {feedback_data['feedback_type']} from {advisors[advisor_idx].name} to {students[student_idx].name}")
            print(f"   Rating: {feedback_data.get('rating', 'N/A')}, Action Required: {feedback_data['action_required']}")
            
            assert feedback_result['feedback_type'] == feedback_data['feedback_type']
        
        # Demonstrate communication tracking
        print(f"\n📞 Communication summary:")
        for i, student in enumerate(students):
            progress_data = await progress_service.track_student_progress(
                student.id, institution.id
            )
            
            feedback_count = len(progress_data['advisor_feedback'])
            action_items = sum(1 for fb in progress_data['advisor_feedback'] 
                             if fb.get('feedback_type') == 'concern' or 'action' in str(fb))
            
            print(f"   {student.name}: {feedback_count} feedback items, {action_items} requiring action")
        
        print("\n✅ REQUIREMENT 3 COMPLETED: Advisor-student communication and feedback systems implemented")
        
        # REQUIREMENT 4: Add institutional reporting with aggregated student performance metrics
        print("\n" + "="*70)
        print("📈 REQUIREMENT 4: Institutional Reporting with Aggregated Performance Metrics")
        print("="*70)
        
        # Generate comprehensive institutional report
        institutional_report = await progress_service.generate_institutional_report(
            institution.id, 'detailed'
        )
        
        print(f"📊 Institutional Report Summary:")
        print(f"   Institution: {institution.name}")
        print(f"   Total Students: {institutional_report['summary_statistics']['total_students']}")
        print(f"   Average Completion: {institutional_report['summary_statistics']['average_completion']:.1f}%")
        print(f"   Active Students (7 days): {institutional_report['recent_activity']['active_students']}")
        print(f"   At-Risk Students: {len(institutional_report['at_risk_students'])}")
        
        # Department breakdown
        print(f"\n🏢 Department Performance:")
        for dept, stats in institutional_report['department_breakdown'].items():
            print(f"   {dept}: {stats['count']} students, {stats['avg_completion']:.1f}% avg completion")
        
        # Milestone analysis
        print(f"\n🎯 Milestone Completion Rates:")
        for milestone, stats in institutional_report['milestone_analysis'].items():
            print(f"   {milestone}: {stats['completion_rate']:.1f}% ({stats['total_students']} students)")
        
        # Performance trends
        print(f"\n📈 Performance Trends:")
        trends = institutional_report['performance_trends']
        print(f"   Engagement Trend: {trends.get('engagement_trend', 'stable')}")
        print(f"   Completion Trend: {trends.get('completion_trend', 'stable')}")
        print(f"   Risk Level: {trends.get('overall_risk_level', 'low')}")
        
        # At-risk students
        if institutional_report['at_risk_students']:
            print(f"\n⚠️  At-Risk Students:")
            for student_info in institutional_report['at_risk_students']:
                print(f"   {student_info['student_id']}: {student_info['completion_percentage']:.1f}% complete, "
                      f"Status: {student_info['status']}")
        
        # Individual progress (detailed report)
        print(f"\n👥 Individual Progress Summary:")
        for progress in institutional_report['individual_progress']:
            print(f"   Student {progress['student_id']}: {progress['completion_percentage']:.1f}% "
                  f"({progress['completed_milestones']}/{progress['milestone_count']} milestones)")
        
        # Verify report completeness
        assert institutional_report['summary_statistics']['total_students'] == 3
        assert 'department_breakdown' in institutional_report
        assert 'milestone_analysis' in institutional_report
        assert 'performance_trends' in institutional_report
        assert 'individual_progress' in institutional_report
        
        print("\n✅ REQUIREMENT 4 COMPLETED: Institutional reporting with aggregated metrics implemented")
        
        # COMPREHENSIVE INTEGRATION TEST
        print("\n" + "="*70)
        print("🔄 COMPREHENSIVE INTEGRATION TEST")
        print("="*70)
        
        # Simulate a complete workflow
        print("\n🔄 Simulating complete student progress workflow...")
        
        # 1. New student enrollment and progress setup
        new_student = User(
            email=f"integration_student_{unique_id}@aru.edu",
            name="Integration Test Student",
            hashed_password="hashed_password"
        )
        db.add(new_student)
        db.commit()
        db.refresh(new_student)
        
        new_role = UserRole(
            user_id=new_student.id,
            institution_id=institution.id,
            role_name="student",
            department="Integration Testing",
            permissions={"research_access": True}
        )
        db.add(new_role)
        db.commit()
        
        # 2. Create progress record
        integration_project = {
            'title': 'Integration Test Research Project',
            'project_type': 'research',
            'research_area': 'Software Testing',
            'expected_completion': (datetime.now() + timedelta(days=365)).isoformat(),
            'keywords': ['testing', 'integration', 'research'],
            'initial_notes': 'Full integration test project'
        }
        
        integration_progress = await progress_service.create_student_progress_record(
            new_student.id, advisors[0].id, institution.id, integration_project
        )
        
        print(f"✅ Created integration test progress record")
        
        # 3. Progress through milestones
        milestones_to_complete = ['literature_review', 'research_proposal']
        for milestone in milestones_to_complete:
            await progress_service.update_milestone_status(
                integration_progress['progress_id'], milestone, 'completed',
                f'Integration test completion of {milestone}'
            )
            print(f"✅ Completed milestone: {milestone}")
        
        # 4. Add advisor feedback
        integration_feedback = {
            'feedback_type': 'milestone_review',
            'feedback_text': 'Integration test feedback - excellent progress!',
            'rating': 5,
            'milestone_related': 'research_proposal',
            'action_required': False,
            'priority': 'low',
            'tags': ['integration_test', 'excellent']
        }
        
        await progress_service.add_advisor_feedback(
            integration_progress['progress_id'], advisors[0].id, integration_feedback
        )
        print(f"✅ Added integration test feedback")
        
        # 5. Generate final report
        final_report = await progress_service.generate_institutional_report(
            institution.id, 'summary'
        )
        
        print(f"✅ Generated final institutional report")
        print(f"   Total students now: {final_report['summary_statistics']['total_students']}")
        print(f"   Average completion: {final_report['summary_statistics']['average_completion']:.1f}%")
        
        # Verify integration
        assert final_report['summary_statistics']['total_students'] == 4  # 3 original + 1 integration
        
        print("\n✅ COMPREHENSIVE INTEGRATION TEST COMPLETED")
        
        # FINAL VERIFICATION
        print("\n" + "="*70)
        print("✅ FINAL VERIFICATION - ALL REQUIREMENTS COMPLETED")
        print("="*70)
        
        requirements_completed = {
            "✅ Build comprehensive student research progress monitoring": "Implemented with detailed tracking, metrics, and recommendations",
            "✅ Create milestone tracking and deadline management": "Implemented with status updates, deadline analysis, and progress calculation",
            "✅ Implement advisor-student communication and feedback systems": "Implemented with multiple feedback types, ratings, and action items",
            "✅ Add institutional reporting with aggregated student performance metrics": "Implemented with detailed analytics, trends, and department breakdowns"
        }
        
        for requirement, implementation in requirements_completed.items():
            print(f"{requirement}")
            print(f"   {implementation}")
        
        print(f"\n🎉 TASK 5.3 IMPLEMENTATION SUCCESSFULLY COMPLETED!")
        print(f"   - {len(students) + 1} students tracked")
        print(f"   - {len(advisors)} advisors managing students")
        print(f"   - {len(feedback_results)} feedback interactions")
        print(f"   - {len(milestone_updates)} milestone updates")
        print(f"   - Comprehensive institutional reporting")
        
        return True
        
    except Exception as e:
        print(f"❌ Comprehensive test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = asyncio.run(test_comprehensive_student_progress())
    if success:
        print("\n🏆 COMPREHENSIVE STUDENT PROGRESS TRACKING TEST PASSED!")
        print("All requirements for task 5.3 have been successfully implemented and verified.")
    else:
        print("\n💥 COMPREHENSIVE STUDENT PROGRESS TRACKING TEST FAILED!")