"""
Basic test for student progress tracking service
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

async def test_student_progress_tracking_basic():
    """Test basic student progress tracking functionality"""
    print("Testing Student Progress Tracking Service...")
    
    # Initialize database
    await init_db()
    
    # Create test data
    db = next(get_db())
    
    try:
        # Create test institution
        institution = Institution(
            name="Test University",
            domain="test.edu",
            type="university",
            settings={"academic_year": "2024-2025"}
        )
        db.add(institution)
        db.commit()
        db.refresh(institution)
        
        # Create test users (student and advisor) with unique emails
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        student = User(
            email=f"student_{unique_id}@test.edu",
            name="Test Student",
            hashed_password="hashed_password"
        )
        advisor = User(
            email=f"advisor_{unique_id}@test.edu",
            name="Test Advisor",
            hashed_password="hashed_password"
        )
        db.add_all([student, advisor])
        db.commit()
        db.refresh(student)
        db.refresh(advisor)
        
        # Create user roles
        student_role = UserRole(
            user_id=student.id,
            institution_id=institution.id,
            role_name="student",
            department="Computer Science",
            permissions={"research_access": True}
        )
        advisor_role = UserRole(
            user_id=advisor.id,
            institution_id=institution.id,
            role_name="faculty",
            department="Computer Science",
            permissions={"advisor_access": True}
        )
        db.add_all([student_role, advisor_role])
        db.commit()
        
        # Create some learning activity data
        learning_progress = LearningProgress(
            user_id=student.id,
            topic="Machine Learning",
            competency_level=0.7,
            study_count=15,
            average_score=85.0
        )
        
        study_session = StudySession(
            user_id=student.id,
            session_type="research",
            started_at=datetime.now() - timedelta(hours=2),
            ended_at=datetime.now() - timedelta(hours=1),
            items_studied=5,
            performance_score=0.8
        )
        
        db.add_all([learning_progress, study_session])
        db.commit()
        
        # Test student progress tracking service
        progress_service = StudentProgressTrackingService()
        
        # Test 1: Create student progress record
        print("\n1. Testing student progress record creation...")
        project_details = {
            'title': 'AI-Based Research Assistant',
            'project_type': 'research',
            'research_area': 'Artificial Intelligence',
            'expected_completion': (datetime.now() + timedelta(days=365)).isoformat(),
            'keywords': ['AI', 'NLP', 'Machine Learning'],
            'initial_notes': 'Initial research project setup'
        }
        
        creation_result = await progress_service.create_student_progress_record(
            student.id, advisor.id, institution.id, project_details
        )
        
        print(f"Progress record created: {creation_result['progress_id']}")
        print(f"Project title: {creation_result['project_title']}")
        print(f"Number of milestones: {len(creation_result['milestones'])}")
        
        assert creation_result['status'] == 'created'
        assert len(creation_result['milestones']) > 0
        
        progress_id = creation_result['progress_id']
        
        # Test 2: Track student progress
        print("\n2. Testing student progress tracking...")
        progress_tracking = await progress_service.track_student_progress(
            student.id, institution.id
        )
        
        print(f"Progress status: {progress_tracking['progress_status']}")
        print(f"Completion percentage: {progress_tracking['completion_percentage']:.1f}%")
        print(f"Total milestones: {progress_tracking['milestones']['total']}")
        print(f"Performance metrics keys: {list(progress_tracking['performance_metrics'].keys())}")
        
        assert progress_tracking['student_id'] == student.id
        assert 'performance_metrics' in progress_tracking
        assert 'milestones' in progress_tracking
        assert 'recommendations' in progress_tracking
        
        # Test 3: Update milestone status
        print("\n3. Testing milestone status update...")
        milestone_name = list(creation_result['milestones'].keys())[0]  # Get first milestone
        
        milestone_update = await progress_service.update_milestone_status(
            progress_id, milestone_name, 'completed', 'Milestone completed successfully'
        )
        
        print(f"Updated milestone: {milestone_update['milestone_name']}")
        print(f"New status: {milestone_update['new_status']}")
        print(f"Updated completion: {milestone_update['completion_percentage']:.1f}%")
        
        assert milestone_update['new_status'] == 'completed'
        assert milestone_update['completion_percentage'] > 0
        
        # Test 4: Add advisor feedback
        print("\n4. Testing advisor feedback...")
        feedback_data = {
            'feedback_type': 'milestone_review',
            'feedback_text': 'Great progress on the literature review. Keep up the good work!',
            'rating': 4,
            'milestone_related': milestone_name,
            'action_required': True,
            'required_action': 'Submit detailed outline by next week',
            'action_deadline': (datetime.now() + timedelta(days=7)).isoformat(),
            'priority': 'medium',
            'tags': ['literature_review', 'positive']
        }
        
        feedback_result = await progress_service.add_advisor_feedback(
            progress_id, advisor.id, feedback_data
        )
        
        print(f"Feedback added: {feedback_result['feedback_id']}")
        print(f"Feedback type: {feedback_result['feedback_type']}")
        print(f"Rating: {feedback_result['rating']}")
        print(f"Action required: {feedback_result['action_required']}")
        
        assert feedback_result['feedback_type'] == 'milestone_review'
        assert feedback_result['rating'] == 4
        assert feedback_result['action_required'] == True
        
        # Test 5: Generate institutional report
        print("\n5. Testing institutional report generation...")
        institutional_report = await progress_service.generate_institutional_report(
            institution.id, 'summary'
        )
        
        print(f"Total students in report: {institutional_report['summary_statistics']['total_students']}")
        print(f"Average completion: {institutional_report['summary_statistics']['average_completion']:.1f}%")
        print(f"Department breakdown: {list(institutional_report['department_breakdown'].keys())}")
        print(f"At-risk students: {len(institutional_report['at_risk_students'])}")
        
        assert institutional_report['summary_statistics']['total_students'] == 1
        assert 'department_breakdown' in institutional_report
        assert 'milestone_analysis' in institutional_report
        assert 'performance_trends' in institutional_report
        
        # Test 6: Detailed institutional report
        print("\n6. Testing detailed institutional report...")
        detailed_report = await progress_service.generate_institutional_report(
            institution.id, 'detailed'
        )
        
        print(f"Individual progress records: {len(detailed_report.get('individual_progress', []))}")
        
        assert 'individual_progress' in detailed_report
        assert len(detailed_report['individual_progress']) == 1
        
        print("\n✅ All student progress tracking tests passed!")
        
        # Test edge cases
        print("\n7. Testing edge cases...")
        
        # Test with non-existent student
        try:
            await progress_service.track_student_progress("non-existent", institution.id)
            print("❌ Should have handled non-existent student")
        except:
            pass  # Expected to fail or return empty result
        
        # Test milestone update with invalid milestone
        try:
            await progress_service.update_milestone_status(
                progress_id, "invalid_milestone", "completed"
            )
            print("❌ Should have handled invalid milestone")
        except ValueError as e:
            print(f"✅ Correctly handled invalid milestone: {e}")
        
        # Test unauthorized advisor feedback
        try:
            await progress_service.add_advisor_feedback(
                progress_id, student.id, feedback_data  # Student trying to add feedback
            )
            print("❌ Should have prevented unauthorized feedback")
        except ValueError as e:
            print(f"✅ Correctly prevented unauthorized feedback: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = asyncio.run(test_student_progress_tracking_basic())
    if success:
        print("\n🎉 Student progress tracking service is working correctly!")
    else:
        print("\n💥 Student progress tracking service test failed!")