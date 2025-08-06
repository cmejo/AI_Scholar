"""
Test API endpoints for institutional role management
"""
import asyncio
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json
import uuid

from app import app
from core.database import get_db, init_db
from core.database import Institution, User, UserRole, AuditLog

client = TestClient(app)

async def test_institutional_role_management_api_endpoints():
    """Test all institutional role management API endpoints"""
    print("Testing Institutional Role Management API Endpoints...")
    
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
            settings={"max_users": 1000}
        )
        db.add(institution)
        db.commit()
        db.refresh(institution)
        
        # Create test admin user
        unique_id = str(uuid.uuid4())[:8]
        
        admin_user = User(
            email=f"admin_api_{unique_id}@testapi.edu",
            name="Test Admin API",
            hashed_password="hashed_password"
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        # Create admin role
        admin_role = UserRole(
            user_id=admin_user.id,
            institution_id=institution.id,
            role_name="admin",
            department="Administration",
            permissions={"base_permissions": ["all"]},
            is_active=True
        )
        db.add(admin_role)
        db.commit()
        
        # Test 1: Create role system
        print("\n1. Testing role system creation endpoint...")
        role_definitions = {
            "hierarchy": {
                "admin": {
                    "level": 5,
                    "permissions": ["all"],
                    "can_manage": ["faculty", "staff", "student", "guest"]
                },
                "faculty": {
                    "level": 4,
                    "permissions": ["research", "teaching", "advising"],
                    "can_manage": ["student"]
                },
                "student": {
                    "level": 2,
                    "permissions": ["learning", "basic_research"],
                    "can_manage": []
                }
            },
            "department_permissions": {
                "Computer Science": ["ai_tools", "programming_resources"],
                "Biology": ["lab_equipment", "research_databases"]
            },
            "custom_roles": {
                "research_assistant": {
                    "level": 3,
                    "permissions": ["research", "data_analysis"]
                }
            }
        }
        
        response = client.post(
            f"/api/institutional-role-management/institutions/{institution.id}/role-system",
            json=role_definitions
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] == True
        assert result["data"]["role_system_created"] == True
        assert result["data"]["hierarchy_levels"] == 3
        
        # Test 2: Manage department permissions
        print("\n2. Testing department permissions management endpoint...")
        dept_permissions_data = {
            "department": "Computer Science",
            "permissions": ["ai_tools", "programming_resources", "cloud_computing"],
            "action": "update"
        }
        
        response = client.put(
            f"/api/institutional-role-management/institutions/{institution.id}/department-permissions",
            json=dept_permissions_data
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] == True
        assert result["data"]["department"] == "Computer Science"
        assert "cloud_computing" in result["data"]["permissions"]
        
        # Test 3: User provisioning
        print("\n3. Testing user provisioning endpoint...")
        user_data = {
            "email": f"student_api_{unique_id}@testapi.edu",
            "name": "Test Student API",
            "hashed_password": "hashed_password",
            "role_name": "student",
            "department": "Computer Science"
        }
        
        response = client.post(
            f"/api/institutional-role-management/institutions/{institution.id}/users/provision",
            json=user_data,
            params={"assigned_by": admin_user.id}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] == True
        assert result["data"]["role_name"] == "student"
        assert result["data"]["department"] == "Computer Science"
        
        student_user_id = result["data"]["user_id"]
        
        # Test 4: Get user permissions
        print("\n4. Testing get user permissions endpoint...")
        response = client.get(
            f"/api/institutional-role-management/institutions/{institution.id}/users/{student_user_id}/permissions"
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] == True
        assert result["data"]["role_name"] == "student"
        assert result["data"]["department"] == "Computer Science"
        
        # Test 5: Get institution roles
        print("\n5. Testing get institution roles endpoint...")
        response = client.get(
            f"/api/institutional-role-management/institutions/{institution.id}/roles"
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] == True
        assert "admin" in result["data"]["role_hierarchy"]
        assert "Computer Science" in result["data"]["department_permissions"]
        
        # Test 6: Get institution users
        print("\n6. Testing get institution users endpoint...")
        response = client.get(
            f"/api/institutional-role-management/institutions/{institution.id}/users",
            params={"limit": 10, "offset": 0}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] == True
        assert result["data"]["total_users"] >= 2  # Admin and student
        assert len(result["data"]["users"]) >= 2
        
        # Test 7: Update user role
        print("\n7. Testing update user role endpoint...")
        response = client.put(
            f"/api/institutional-role-management/institutions/{institution.id}/users/{student_user_id}/role",
            params={
                "new_role_name": "faculty",
                "new_department": "Biology",
                "updated_by": admin_user.id
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] == True
        assert result["data"]["new_role"] == "faculty"
        assert result["data"]["new_department"] == "Biology"
        
        # Test 8: Get access logs
        print("\n8. Testing get access logs endpoint...")
        response = client.get(
            f"/api/institutional-role-management/institutions/{institution.id}/access-logs",
            params={"limit": 20, "offset": 0}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] == True
        assert "logs" in result["data"]
        assert "access_patterns" in result["data"]
        assert "user_activity" in result["data"]
        
        # Test 9: Get role management dashboard
        print("\n9. Testing role management dashboard endpoint...")
        response = client.get(
            f"/api/institutional-role-management/institutions/{institution.id}/role-management-dashboard"
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] == True
        assert result["data"]["total_active_users"] >= 2
        assert "role_distribution" in result["data"]
        assert "department_distribution" in result["data"]
        
        # Test 10: User deprovisioning
        print("\n10. Testing user deprovisioning endpoint...")
        response = client.delete(
            f"/api/institutional-role-management/institutions/{institution.id}/users/{student_user_id}/deprovision",
            params={
                "deprovisioned_by": admin_user.id,
                "reason": "API test deprovisioning"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] == True
        assert result["data"]["user_id"] == student_user_id
        assert result["data"]["reason"] == "API test deprovisioning"
        
        print("\n✅ All institutional role management API endpoint tests passed!")
        
        # Test error cases
        print("\n11. Testing error cases...")
        
        # Test invalid institution ID
        response = client.get("/api/institutional-role-management/institutions/invalid_id/roles")
        print(f"Invalid institution status: {response.status_code}")
        assert response.status_code == 404
        
        # Test unauthorized user provisioning
        student_user2 = User(
            email=f"student2_api_{unique_id}@testapi.edu",
            name="Test Student 2 API",
            hashed_password="hashed_password"
        )
        db.add(student_user2)
        db.commit()
        db.refresh(student_user2)
        
        student_role2 = UserRole(
            user_id=student_user2.id,
            institution_id=institution.id,
            role_name="student",
            department="Computer Science",
            permissions={"base_permissions": ["learning"]},
            is_active=True
        )
        db.add(student_role2)
        db.commit()
        
        # Student trying to provision another user (should fail)
        response = client.post(
            f"/api/institutional-role-management/institutions/{institution.id}/users/provision",
            json={
                "email": f"unauthorized_api_{unique_id}@testapi.edu",
                "name": "Unauthorized User API",
                "hashed_password": "hashed_password",
                "role_name": "faculty"
            },
            params={"assigned_by": student_user2.id}
        )
        
        print(f"Unauthorized provisioning status: {response.status_code}")
        assert response.status_code == 400  # Should be rejected
        
        # Test non-existent user permissions
        response = client.get(
            f"/api/institutional-role-management/institutions/{institution.id}/users/nonexistent_user/permissions"
        )
        print(f"Non-existent user status: {response.status_code}")
        assert response.status_code == 404
        
        print("\n✅ All error case tests passed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = asyncio.run(test_institutional_role_management_api_endpoints())
    if success:
        print("\n🎉 Institutional role management API endpoints are working correctly!")
    else:
        print("\n💥 Institutional role management API endpoint tests failed!")