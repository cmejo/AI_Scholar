"""
API endpoints for institutional role management
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from services.institutional_role_management_service import InstitutionalRoleManagementService

router = APIRouter(prefix="/api/institutional-role-management", tags=["institutional-role-management"])

# Pydantic models for request/response
class RoleDefinition(BaseModel):
    hierarchy: Dict[str, Any]
    department_permissions: Dict[str, List[str]]
    custom_roles: Optional[Dict[str, Any]] = {}

class UserProvisioningRequest(BaseModel):
    email: str
    name: str
    hashed_password: str
    role_name: str
    department: Optional[str] = None
    expires_at: Optional[datetime] = None

class DepartmentPermissionsRequest(BaseModel):
    department: str
    permissions: List[str]
    action: str = "update"  # update, add, remove, delete

class AccessLogFilters(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[str] = None
    action: Optional[str] = None
    success: Optional[bool] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0

# Initialize service
role_service = InstitutionalRoleManagementService()

@router.post("/institutions/{institution_id}/role-system")
async def create_role_system(
    institution_id: str,
    role_definitions: RoleDefinition
):
    """Create hierarchical role-based access control system"""
    try:
        result = await role_service.create_hierarchical_role_system(
            institution_id, role_definitions.dict()
        )
        return {
            "success": True,
            "data": result,
            "message": "Role system created successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/institutions/{institution_id}/department-permissions")
async def manage_department_permissions(
    institution_id: str,
    request: DepartmentPermissionsRequest
):
    """Implement department and faculty-level permissions management"""
    try:
        result = await role_service.manage_department_permissions(
            institution_id, 
            request.department, 
            request.permissions, 
            request.action
        )
        return {
            "success": True,
            "data": result,
            "message": f"Department permissions {request.action}d successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/institutions/{institution_id}/users/provision")
async def provision_user(
    institution_id: str,
    user_data: UserProvisioningRequest,
    assigned_by: str = Query(..., description="ID of the user assigning the role")
):
    """Build institutional user provisioning workflows"""
    try:
        result = await role_service.provision_user(
            institution_id, user_data.dict(), assigned_by
        )
        return {
            "success": True,
            "data": result,
            "message": "User provisioned successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/institutions/{institution_id}/users/{user_id}/deprovision")
async def deprovision_user(
    institution_id: str,
    user_id: str,
    deprovisioned_by: str = Query(..., description="ID of the user performing deprovisioning"),
    reason: str = Query("", description="Reason for deprovisioning")
):
    """Build institutional user deprovisioning workflows"""
    try:
        result = await role_service.deprovision_user(
            institution_id, user_id, deprovisioned_by, reason
        )
        return {
            "success": True,
            "data": result,
            "message": "User deprovisioned successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/institutions/{institution_id}/access-logs")
async def get_access_logs(
    institution_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for log filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for log filtering"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    limit: int = Query(100, description="Maximum number of logs to return"),
    offset: int = Query(0, description="Number of logs to skip")
):
    """Add audit logging for institutional access and activity monitoring"""
    try:
        filters = {}
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        if user_id:
            filters['user_id'] = user_id
        if action:
            filters['action'] = action
        if success is not None:
            filters['success'] = success
        filters['limit'] = limit
        filters['offset'] = offset
        
        result = await role_service.get_institutional_access_logs(
            institution_id, filters
        )
        return {
            "success": True,
            "data": result,
            "message": "Access logs retrieved successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/institutions/{institution_id}/role-management-dashboard")
async def get_role_management_dashboard(institution_id: str):
    """Generate comprehensive role management dashboard"""
    try:
        result = await role_service.get_role_management_dashboard(institution_id)
        return {
            "success": True,
            "data": result,
            "message": "Role management dashboard generated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/institutions/{institution_id}/users/{user_id}/permissions")
async def get_user_permissions(institution_id: str, user_id: str):
    """Get detailed permissions for a specific user"""
    try:
        from core.database import get_db, UserRole
        from sqlalchemy import and_
        
        db = next(get_db())
        try:
            user_role = db.query(UserRole).filter(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.institution_id == institution_id,
                    UserRole.is_active == True
                )
            ).first()
            
            if not user_role:
                raise HTTPException(status_code=404, detail="User role not found")
            
            return {
                "success": True,
                "data": {
                    "user_id": user_id,
                    "institution_id": institution_id,
                    "role_name": user_role.role_name,
                    "department": user_role.department,
                    "permissions": user_role.permissions,
                    "is_active": user_role.is_active,
                    "assigned_at": user_role.assigned_at,
                    "expires_at": user_role.expires_at
                },
                "message": "User permissions retrieved successfully"
            }
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/institutions/{institution_id}/roles")
async def get_institution_roles(institution_id: str):
    """Get all roles and their configurations for an institution"""
    try:
        from core.database import get_db, Institution
        
        db = next(get_db())
        try:
            institution = db.query(Institution).filter(
                Institution.id == institution_id
            ).first()
            
            if not institution:
                raise HTTPException(status_code=404, detail="Institution not found")
            
            settings = institution.settings or {}
            role_system = settings.get('role_system', {})
            
            return {
                "success": True,
                "data": {
                    "institution_id": institution_id,
                    "role_hierarchy": role_system.get('hierarchy', {}),
                    "department_permissions": role_system.get('department_permissions', {}),
                    "custom_roles": role_system.get('custom_roles', {}),
                    "created_at": role_system.get('created_at'),
                    "version": role_system.get('version')
                },
                "message": "Institution roles retrieved successfully"
            }
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/institutions/{institution_id}/users")
async def get_institution_users(
    institution_id: str,
    role_name: Optional[str] = Query(None, description="Filter by role name"),
    department: Optional[str] = Query(None, description="Filter by department"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, description="Maximum number of users to return"),
    offset: int = Query(0, description="Number of users to skip")
):
    """Get all users and their roles for an institution"""
    try:
        from core.database import get_db, UserRole, User
        from sqlalchemy import and_
        
        db = next(get_db())
        try:
            # Build query
            query = db.query(UserRole, User).join(User, UserRole.user_id == User.id).filter(
                UserRole.institution_id == institution_id
            )
            
            # Apply filters
            if role_name:
                query = query.filter(UserRole.role_name == role_name)
            if department:
                query = query.filter(UserRole.department == department)
            if is_active is not None:
                query = query.filter(UserRole.is_active == is_active)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            results = query.offset(offset).limit(limit).all()
            
            users_data = []
            for user_role, user in results:
                users_data.append({
                    "user_id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "role_name": user_role.role_name,
                    "department": user_role.department,
                    "permissions": user_role.permissions,
                    "is_active": user_role.is_active,
                    "assigned_at": user_role.assigned_at,
                    "expires_at": user_role.expires_at,
                    "last_login": user.last_login
                })
            
            return {
                "success": True,
                "data": {
                    "institution_id": institution_id,
                    "total_users": total_count,
                    "users_returned": len(users_data),
                    "users": users_data
                },
                "message": "Institution users retrieved successfully"
            }
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/institutions/{institution_id}/users/{user_id}/role")
async def update_user_role(
    institution_id: str,
    user_id: str,
    new_role_name: str = Query(..., description="New role name"),
    new_department: Optional[str] = Query(None, description="New department"),
    updated_by: str = Query(..., description="ID of the user making the update")
):
    """Update a user's role and permissions"""
    try:
        from core.database import get_db, UserRole
        from sqlalchemy import and_
        
        db = next(get_db())
        try:
            # Check if updater has permission
            updater_role = db.query(UserRole).filter(
                and_(
                    UserRole.user_id == updated_by,
                    UserRole.institution_id == institution_id,
                    UserRole.is_active == True
                )
            ).first()
            
            if not updater_role:
                raise HTTPException(status_code=403, detail="Updater not authorized")
            
            # Get user role to update
            user_role = db.query(UserRole).filter(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.institution_id == institution_id,
                    UserRole.is_active == True
                )
            ).first()
            
            if not user_role:
                raise HTTPException(status_code=404, detail="User role not found")
            
            # Check if updater can manage the new role
            if not await role_service._can_manage_role(updater_role.role_name, new_role_name):
                raise HTTPException(status_code=403, detail=f"Insufficient permissions to assign role: {new_role_name}")
            
            # Update role
            old_role_name = user_role.role_name
            old_department = user_role.department
            
            user_role.role_name = new_role_name
            if new_department is not None:
                user_role.department = new_department
            
            # Get new permissions
            new_permissions = await role_service._get_role_permissions(
                institution_id, new_role_name, user_role.department, db
            )
            user_role.permissions = new_permissions
            
            db.commit()
            
            # Log the role update
            await role_service._log_role_management_action(
                updated_by, institution_id, 'role_update',
                {
                    'user_id': user_id,
                    'old_role': old_role_name,
                    'new_role': new_role_name,
                    'old_department': old_department,
                    'new_department': user_role.department
                }, db
            )
            
            return {
                "success": True,
                "data": {
                    "user_id": user_id,
                    "old_role": old_role_name,
                    "new_role": new_role_name,
                    "old_department": old_department,
                    "new_department": user_role.department,
                    "updated_by": updated_by,
                    "updated_at": datetime.now()
                },
                "message": "User role updated successfully"
            }
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")