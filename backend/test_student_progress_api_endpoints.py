"""
Test student progress tracking API endpoints
"""
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import app
from core.database import get_db, init_db
from core.database import (
    Institution, User, UserRole, StudentProgress, AdvisorFeedback,
    Quiz, QuizAttempt, LearningProgress, StudySession
)

client = TestClient(app)

async def test_student_progress_api_endpoints():
    """Test all student progress tracking API endpoints"""
    print("Testing Student Progress API Endpoints...")
    
    # Initialize database
    await init_db()
    
    # Create test data
    db = next(get_db())
    
    try:
        # Create test institution
        institution = Institution(
            name="Test University API",
            domain="testapi.edu",
            type="university",
            settings={"academic_year": "2024-2025"}
        )
        db.add(institution)
        db.commit()
        db.refresh(institution)
        
        # Create test users with unique emails
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        student = User(
            email=f"student_api_{unique_id}@test.edu",
            name="Test Student API",
            hashed_password="hashed_password"
        )
        advisor = User(
            email=f"advisor_api_{unique_id}@test.edu",
            name="Test Advisor API",
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
            topic="Machine Learning API",
            competency_level=0.8,
            study_count=20,
            average_score=88.0
        )
        
        study_session = StudySession(
            user_id=student.id,
            session_type="research",
            started_at=datetime.now() - timedelta(hours=3),
            ended_at=datetime.now() - timedelta(hours=2),
            items_studied=8,
            performance_score=0.85
        )
        
        db.add_all([learning_progress, study_session])
        db.commit()
        
        # Test 1: Create student progress record via API
        print("\n1. Testing POST /api/student-progress/create...")
        
        create_request = {
            "student_id": student.id,
            "advisor_id": advisor.id,
            "institution_id": institution.id,
            "project_details": {
                "title": "Advanced AI Research System",
                "project_type": "research",
                "research_area": "Artificial Intelligence",
                "expected_completion": (datetime.now() + timedelta(days=300)).isoformat(),
                "keywords": ["AI", "Machine Learning", "Research"],
                "initial_notes": "API test project setup"
            }
        }
        
        response = client.post("/api/student-progress/create", json=create_request)
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        create_data = response.json()
        
        print(f"Created progress ID: {create_data['progress_id']}")
        print(f"Project title: {create_data['project_title']}")
        print(f"Milestones count: {len(create_data['milestones'])}")
        
        assert create_data['status'] == 'created'
        assert create_data['student_id'] == student.id
        assert create_data['advisor_id'] == advisor.id
        
        progress_id = create_data['progress_id']
        
        # Test 2: Get student progress via API
        print("\n2. Testing GET /api/student-progress/student/{student_id}...")
        
        response = client.get(
            f"/api/student-progress/student/{student.id}",
            params={"institution_id": institution.id}
        )
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        progress_data = response.json()
        
        print(f"Progress status: {progress_data['progress_status']}")
        print(f"Completion percentage: {progress_data['completion_percentage']:.1f}%")
        print(f"Performance metrics keys: {list(progress_data['performance_metrics'].keys())}")
        
        assert progress_data['student_id'] == student.id
        assert 'milestones' in progress_data
        assert 'performance_metrics' in progress_data
        assert 'recommendations' in progress_data
        
        # Test 3: Update milestone status via API
        print("\n3. Testing PUT /api/student-progress/milestone/{progress_id}...")
        
        # Get first milestone name
        milestone_name = list(create_data['milestones'].keys())[0]
        
        milestone_request = {
            "milestone_name": milestone_name,
            "status": "completed",
            "notes": "API test milestone completion"
        }
        
        response = client.put(
            f"/api/student-progress/milestone/{progress_id}",
            json=milestone_request
        )
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        milestone_data = response.json()
        
        print(f"Updated milestone: {milestone_data['milestone_name']}")
        print(f"New status: {milestone_data['new_status']}")
        print(f"Updated completion: {milestone_data['completion_percentage']:.1f}%")
        
        assert milestone_data['new_status'] == 'completed'
        assert milestone_data['completion_percentage'] > 0
        
        # Test 4: Add advisor feedback via API
        print("\n4. Testing POST /api/student-progress/feedback/{progress_id}...")
        
        feedback_request = {
            "feedback_type": "milestone_review",
            "feedback_text": "Excellent work on the literature review via API!",
            "rating": 5,
            "milestone_related": milestone_name,
            "action_required": True,
            "required_action": "Prepare detailed methodology section",
            "action_deadline": (datetime.now() + timedelta(days=10)).isoformat(),
            "priority": "high",
            "tags": ["literature_review", "excellent"]
        }
        
        response = client.post(
            f"/api/student-progress/feedback/{progress_id}",
            params={"advisor_id": advisor.id},
            json=feedback_request
        )
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        feedback_data = response.json()
        
        print(f"Feedback ID: {feedback_data['feedback_id']}")
        print(f"Feedback type: {feedback_data['feedback_type']}")
        print(f"Rating: {feedback_data['rating']}")
        print(f"Action required: {feedback_data['action_required']}")
        
        assert feedback_data['feedback_type'] == 'milestone_review'
        assert feedback_data['rating'] == 5
        assert feedback_data['action_required'] == True
        
        # Test 5: Generate institutional report via API
        print("\n5. Testing GET /api/student-progress/institution/{institution_id}/report...")
        
        response = client.get(
            f"/api/student-progress/institution/{institution.id}/report",
            params={"report_type": "summary"}
        )
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        report_data = response.json()
        
        print(f"Total students: {report_data['summary_statistics']['total_students']}")
        print(f"Average completion: {report_data['summary_statistics']['average_completion']:.1f}%")
        print(f"Department count: {len(report_data['department_breakdown'])}")
        print(f"At-risk students: {len(report_data['at_risk_students'])}")
        
        assert report_data['summary_statistics']['total_students'] == 1
        assert 'milestone_analysis' in report_data
        assert 'performance_trends' in report_data
        
        # Test 6: Get detailed institutional report
        print("\n6. Testing detailed institutional report...")
        
        response = client.get(
            f"/api/student-progress/institution/{institution.id}/report",
            params={"report_type": "detailed"}
        )
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        detailed_report = response.json()
        
        print(f"Individual progress records: {len(detailed_report.get('individual_progress', []))}")
        
        assert 'individual_progress' in detailed_report
        assert len(detailed_report['individual_progress']) == 1
        
        # Test 7: Get student milestones
        print("\n7. Testing GET /api/student-progress/student/{student_id}/milestones...")
        
        response = client.get(
            f"/api/student-progress/student/{student.id}/milestones",
            params={"institution_id": institution.id}
        )
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        milestones_data = response.json()
        
        print(f"Project title: {milestones_data['project_title']}")
        print(f"Milestones count: {len(milestones_data['milestones'])}")
        print(f"Overall completion: {milestones_data['overall_completion']:.1f}%")
        
        assert milestones_data['student_id'] == student.id
        assert len(milestones_data['milestones']) > 0
        
        # Check milestone details
        first_milestone = milestones_data['milestones'][0]
        print(f"First milestone: {first_milestone['name']} - {first_milestone['status']}")
        
        # Test 8: Get advisor students
        print("\n8. Testing GET /api/student-progress/advisor/{advisor_id}/students...")
        
        response = client.get(
            f"/api/student-progress/advisor/{advisor.id}/students",
            params={"institution_id": institution.id}
        )
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        advisor_data = response.json()
        
        print(f"Total students for advisor: {advisor_data['total_students']}")
        print(f"Students list length: {len(advisor_data['students'])}")
        
        assert advisor_data['total_students'] == 1
        assert len(advisor_data['students']) == 1
        
        student_summary = advisor_data['students'][0]
        print(f"Student project: {student_summary['project_title']}")
        print(f"Student completion: {student_summary['completion_percentage']:.1f}%")
        
        # Test 9: Get at-risk students
        print("\n9. Testing GET /api/student-progress/institution/{institution_id}/at-risk...")
        
        response = client.get(
            f"/api/student-progress/institution/{institution.id}/at-risk",
            params={"threshold_days": 14, "completion_threshold": 0.3}
        )
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        at_risk_data = response.json()
        
        print(f"Total at-risk students: {at_risk_data['total_at_risk']}")
        print(f"Criteria - threshold days: {at_risk_data['criteria']['threshold_days']}")
        
        # Test 10: Get institutional dashboard
        print("\n10. Testing GET /api/student-progress/institution/{institution_id}/dashboard...")
        
        response = client.get(f"/api/student-progress/institution/{institution.id}/dashboard")
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        dashboard_data = response.json()
        
        print(f"Dashboard overview: {dashboard_data['overview']}")
        print(f"Status distribution: {dashboard_data['status_distribution']}")
        print(f"Department performance keys: {list(dashboard_data['department_performance'].keys())}")
        
        assert 'overview' in dashboard_data
        assert 'status_distribution' in dashboard_data
        assert 'milestone_completion_rates' in dashboard_data
        
        print("\n✅ All student progress API endpoint tests passed!")
        
        # Test error cases
        print("\n11. Testing error cases...")
        
        # Test with non-existent student
        response = client.get(
            "/api/student-progress/student/non-existent",
            params={"institution_id": institution.id}
        )
        print(f"Non-existent student status: {response.status_code}")
        assert response.status_code == 404
        
        # Test with invalid milestone
        invalid_milestone_request = {
            "milestone_name": "invalid_milestone",
            "status": "completed"
        }
        
        response = client.put(
            f"/api/student-progress/milestone/{progress_id}",
            json=invalid_milestone_request
        )
        print(f"Invalid milestone status: {response.status_code}")
        assert response.status_code == 400
        
        # Test unauthorized advisor feedback
        response = client.post(
            f"/api/student-progress/feedback/{progress_id}",
            params={"advisor_id": student.id},  # Student trying to add feedback
            json=feedback_request
        )
        print(f"Unauthorized feedback status: {response.status_code}")
        assert response.status_code == 400
        
        # Test invalid report type
        response = client.get(
            f"/api/student-progress/institution/{institution.id}/report",
            params={"report_type": "invalid"}
        )
        print(f"Invalid report type status: {response.status_code}")
        assert response.status_code == 400
        
        print("\n✅ Error case tests passed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = asyncio.run(test_student_progress_api_endpoints())
    if success:
        print("\n🎉 Student progress API endpoints are working correctly!")
    else:
        print("\n💥 Student progress API endpoints test failed!")