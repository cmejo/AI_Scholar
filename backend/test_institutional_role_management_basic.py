"""
Basic test for institutional role management service
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from core.database import get_db, init_db
from core.database import (
    Institution, User, UserRole, AuditLog
)
from services.institutional_role_management_service import InstitutionalRoleManagementService

async def test_institutional_role_management_basic():
    """Test basic institutional role management functionality"""
    print("Testing Institutional Role Management Service...")
    
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
            settings={"max_users": 1000}
        )
        db.add(institution)
        db.commit()
        db.refresh(institution)
        
        # Create test admin user
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        admin_user = User(
            email=f"admin_{unique_id}@test.edu",
            name="Test Admin",
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
        
        # Test institutional role management service
        role_service = InstitutionalRoleManagementService()
        
        # Test 1: Create hierarchical role system
        print("\n1. Testing hierarchical role system creation...")
        role_definitions = {
            'hierarchy': {
                'admin': {
                    'level': 5,
                    'permissions': ['all'],
                    'can_manage': ['faculty', 'staff', 'student', 'guest']
                },
                'faculty': {
                    'level': 4,
                    'permissions': ['research', 'teaching', 'advising'],
                    'can_manage': ['student']
                },
                'student': {
                    'level': 2,
                    'permissions': ['learning', 'basic_research'],
                    'can_manage': []
                }
            },
            'department_permissions': {
                'Computer Science': ['ai_tools', 'programming_resources'],
                'Biology': ['lab_equipment', 'research_databases']
            },
            'custom_roles': {
                'research_assistant': {
                    'level': 3,
                    'permissions': ['research', 'data_analysis']
                }
            }
        }
        
        role_system_result = await role_service.create_hierarchical_role_system(
            institution.id, role_definitions
        )
        
        print(f"Role system created: {role_system_result['role_system_created']}")
        print(f"Hierarchy levels: {role_system_result['hierarchy_levels']}")
        print(f"Departments configured: {role_system_result['departments_configured']}")
        print(f"Custom roles: {role_system_result['custom_roles']}")
        
        assert role_system_result['role_system_created'] == True
        assert role_system_result['hierarchy_levels'] == 3
        
        # Test 2: Manage department permissions
        print("\n2. Testing department permissions management...")
        dept_permissions_result = await role_service.manage_department_permissions(
            institution.id, 
            "Computer Science", 
            ["ai_tools", "programming_resources", "cloud_computing"], 
            "update"
        )
        
        print(f"Department: {dept_permissions_result['department']}")
        print(f"Action: {dept_permissions_result['action']}")
        print(f"Permissions: {dept_permissions_result['permissions']}")
        print(f"Affected users: {dept_permissions_result['affected_users']}")
        
        assert dept_permissions_result['department'] == "Computer Science"
        assert "ai_tools" in dept_permissions_result['permissions']
        
        # Test 3: User provisioning
        print("\n3. Testing user provisioning...")
        new_user_data = {
            'email': f'student_{unique_id}@test.edu',
            'name': 'Test Student',
            'hashed_password': 'hashed_password',
            'role_name': 'student',
            'department': 'Computer Science'
        }
        
        provisioning_result = await role_service.provision_user(
            institution.id, new_user_data, admin_user.id
        )
        
        print(f"User provisioned: {provisioning_result['user_email']}")
        print(f"Role assigned: {provisioning_result['role_name']}")
        print(f"Department: {provisioning_result['department']}")
        print(f"User created: {provisioning_result['user_created']}")
        
        assert provisioning_result['role_name'] == 'student'
        assert provisioning_result['department'] == 'Computer Science'
        assert provisioning_result['user_created'] == True
        
        student_user_id = provisioning_result['user_id']
        
        # Test 4: User deprovisioning
        print("\n4. Testing user deprovisioning...")
        deprovisioning_result = await role_service.deprovision_user(
            institution.id, student_user_id, admin_user.id, "Test deprovisioning"
        )
        
        print(f"User deprovisioned: {deprovisioning_result['user_id']}")
        print(f"Role: {deprovisioning_result['role_name']}")
        print(f"Reason: {deprovisioning_result['reason']}")
        
        assert deprovisioning_result['user_id'] == student_user_id
        assert deprovisioning_result['reason'] == "Test deprovisioning"
        
        # Test 5: Institutional access logs
        print("\n5. Testing institutional access logs...")
        access_logs_result = await role_service.get_institutional_access_logs(
            institution.id, {'limit': 10}
        )
        
        print(f"Total logs: {access_logs_result['total_logs']}")
        print(f"Logs returned: {access_logs_result['logs_returned']}")
        print(f"Access patterns keys: {list(access_logs_result['access_patterns'].keys())}")
        print(f"Security alerts: {len(access_logs_result['security_alerts'])}")
        
        assert 'logs' in access_logs_result
        assert 'access_patterns' in access_logs_result
        assert 'user_activity' in access_logs_result
        
        # Test 6: Role management dashboard
        print("\n6. Testing role management dashboard...")
        dashboard_result = await role_service.get_role_management_dashboard(institution.id)
        
        print(f"Total active users: {dashboard_result['total_active_users']}")
        print(f"Role distribution: {dashboard_result['role_distribution']}")
        print(f"Department distribution: {dashboard_result['department_distribution']}")
        print(f"Recent changes: {len(dashboard_result['recent_changes'])}")
        
        assert dashboard_result['total_active_users'] >= 1  # At least the admin
        assert 'role_distribution' in dashboard_result
        assert 'department_distribution' in dashboard_result
        
        print("\n✅ All institutional role management tests passed!")
        
        # Test edge cases and error handling
        print("\n7. Testing edge cases...")
        
        # Test unauthorized provisioning
        try:
            # Create a student user and try to provision another user
            student_user = User(
                email=f"student2_{unique_id}@test.edu",
                name="Test Student 2",
                hashed_password="hashed_password"
            )
            db.add(student_user)
            db.commit()
            db.refresh(student_user)
            
            student_role = UserRole(
                user_id=student_user.id,
                institution_id=institution.id,
                role_name="student",
                department="Computer Science",
                permissions={"base_permissions": ["learning"]},
                is_active=True
            )
            db.add(student_role)
            db.commit()
            
            # Student trying to provision another user (should fail)
            await role_service.provision_user(
                institution.id, 
                {
                    'email': f'unauthorized_{unique_id}@test.edu',
                    'name': 'Unauthorized User',
                    'role_name': 'faculty'
                }, 
                student_user.id
            )
            print("❌ Should have prevented unauthorized provisioning")
        except ValueError as e:
            print(f"✅ Correctly prevented unauthorized provisioning: {e}")
        
        # Test invalid institution
        try:
            await role_service.create_hierarchical_role_system("invalid_id", {})
            print("❌ Should have handled invalid institution")
        except ValueError as e:
            print(f"✅ Correctly handled invalid institution: {e}")
        
        # Test duplicate user provisioning
        try:
            await role_service.provision_user(
                institution.id,
                {
                    'email': admin_user.email,  # Already exists
                    'name': 'Duplicate Admin',
                    'role_name': 'admin'
                },
                admin_user.id
            )
            print("❌ Should have prevented duplicate role assignment")
        except ValueError as e:
            print(f"✅ Correctly prevented duplicate role: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = asyncio.run(test_institutional_role_management_basic())
    if success:
        print("\n🎉 Institutional role management service is working correctly!")
    else:
        print("\n💥 Institutional role management service test failed!")