"""
Institutional Role Management Service for Enterprise Features
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import json
from collections import defaultdict

from core.database import (
    get_db, Institution, User, UserRole, AuditLog
)

class InstitutionalRoleManagementService:
    """Service for managing hierarchical role-based access control and institutional user management"""
    
    def __init__(self):
        self.role_hierarchy = {
            'admin': {
                'level': 5,
                'permissions': ['all'],
                'can_manage': ['faculty', 'staff', 'student', 'guest']
            },
            'faculty': {
                'level': 4,
                'permissions': ['research', 'teaching', 'advising', 'resource_access'],
                'can_manage': ['student']
            },
            'staff': {
                'level': 3,
                'permissions': ['administrative', 'resource_access'],
                'can_manage': ['student']
            },
            'student': {
                'level': 2,
                'permissions': ['learning', 'basic_research'],
                'can_manage': []
            },
            'guest': {
                'level': 1,
                'permissions': ['read_only'],
                'can_manage': []
            }
        }
        
        self.department_permissions = {
            'Computer Science': ['ai_tools', 'programming_resources', 'research_databases'],
            'Biology': ['lab_equipment', 'research_databases', 'specimen_access'],
            'Physics': ['lab_equipment', 'research_databases', 'simulation_tools'],
            'Mathematics': ['research_databases', 'computational_resources'],
            'Engineering': ['design_tools', 'lab_equipment', 'research_databases']
        }
    
    async def create_hierarchical_role_system(self, institution_id: str, 
                                            role_definitions: Dict[str, Any]) -> Dict[str, Any]:
        """Create hierarchical role-based access control system"""
        db = next(get_db())
        try:
            # Validate institution exists
            institution = db.query(Institution).filter(
                Institution.id == institution_id
            ).first()
            
            if not institution:
                raise ValueError("Institution not found")
            
            # Update institution settings with role definitions
            current_settings = institution.settings or {}
            current_settings['role_system'] = {
                'hierarchy': role_definitions.get('hierarchy', self.role_hierarchy),
                'department_permissions': role_definitions.get('department_permissions', self.department_permissions),
                'custom_roles': role_definitions.get('custom_roles', {}),
                'created_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            institution.settings = current_settings
            institution.updated_at = datetime.now()
            db.commit()
            
            # Log the role system creation
            await self._log_role_management_action(
                None, institution_id, 'create_role_system', 
                {'role_definitions': role_definitions}, db
            )
            
            return {
                'institution_id': institution_id,
                'role_system_created': True,
                'hierarchy_levels': len(role_definitions.get('hierarchy', self.role_hierarchy)),
                'departments_configured': len(role_definitions.get('department_permissions', self.department_permissions)),
                'custom_roles': len(role_definitions.get('custom_roles', {})),
                'created_at': datetime.now()
            }
            
        finally:
            db.close()
    
    async def manage_department_permissions(self, institution_id: str, department: str, 
                                          permissions: List[str], action: str = 'update') -> Dict[str, Any]:
        """Implement department and faculty-level permissions management"""
        db = next(get_db())
        try:
            # Get institution
            institution = db.query(Institution).filter(
                Institution.id == institution_id
            ).first()
            
            if not institution:
                raise ValueError("Institution not found")
            
            settings = institution.settings or {}
            role_system = settings.get('role_system', {})
            dept_permissions = role_system.get('department_permissions', {})
            
            if action == 'update':
                dept_permissions[department] = permissions
            elif action == 'add':
                existing = dept_permissions.get(department, [])
                dept_permissions[department] = list(set(existing + permissions))
            elif action == 'remove':
                existing = dept_permissions.get(department, [])
                dept_permissions[department] = [p for p in existing if p not in permissions]
            elif action == 'delete':
                dept_permissions.pop(department, None)
            
            # Update institution settings
            role_system['department_permissions'] = dept_permissions
            settings['role_system'] = role_system
            institution.settings = settings
            institution.updated_at = datetime.now()
            db.commit()
            
            # Update all users in the department
            affected_users = db.query(UserRole).filter(
                and_(
                    UserRole.institution_id == institution_id,
                    UserRole.department == department
                )
            ).all()
            
            for user_role in affected_users:
                user_permissions = user_role.permissions or {}
                user_permissions['department_permissions'] = dept_permissions.get(department, [])
                user_role.permissions = user_permissions
            
            db.commit()
            
            # Log the permission change
            await self._log_role_management_action(
                None, institution_id, f'department_permissions_{action}',
                {
                    'department': department,
                    'permissions': permissions,
                    'affected_users': len(affected_users)
                }, db
            )
            
            return {
                'department': department,
                'action': action,
                'permissions': dept_permissions.get(department, []),
                'affected_users': len(affected_users),
                'updated_at': datetime.now()
            }
            
        finally:
            db.close()
    
    async def provision_user(self, institution_id: str, user_data: Dict[str, Any], 
                           assigned_by: str) -> Dict[str, Any]:
        """Build institutional user provisioning workflows"""
        db = next(get_db())
        try:
            # Validate assigner has permission
            assigner_role = db.query(UserRole).filter(
                and_(
                    UserRole.user_id == assigned_by,
                    UserRole.institution_id == institution_id,
                    UserRole.is_active == True
                )
            ).first()
            
            if not assigner_role:
                raise ValueError("Assigner not found or not authorized")
            
            # Check if assigner can manage the requested role
            requested_role = user_data.get('role_name', 'student')
            if not await self._can_manage_role(assigner_role.role_name, requested_role):
                raise ValueError(f"Insufficient permissions to assign role: {requested_role}")
            
            # Create or get user
            user_email = user_data.get('email')
            user = db.query(User).filter(User.email == user_email).first()
            
            if not user:
                # Create new user
                user = User(
                    email=user_email,
                    name=user_data.get('name', ''),
                    hashed_password=user_data.get('hashed_password', 'temp_password'),
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                user_created = True
            else:
                user_created = False
            
            # Check if user already has a role in this institution
            existing_role = db.query(UserRole).filter(
                and_(
                    UserRole.user_id == user.id,
                    UserRole.institution_id == institution_id
                )
            ).first()
            
            if existing_role:
                raise ValueError("User already has a role in this institution")
            
            # Get role permissions
            role_permissions = await self._get_role_permissions(
                institution_id, requested_role, user_data.get('department'), db
            )
            
            # Create user role
            user_role = UserRole(
                user_id=user.id,
                institution_id=institution_id,
                role_name=requested_role,
                department=user_data.get('department'),
                permissions=role_permissions,
                is_active=True,
                expires_at=user_data.get('expires_at')
            )
            
            db.add(user_role)
            db.commit()
            db.refresh(user_role)
            
            # Log the provisioning
            await self._log_role_management_action(
                assigned_by, institution_id, 'user_provisioning',
                {
                    'user_id': user.id,
                    'user_email': user_email,
                    'role_name': requested_role,
                    'department': user_data.get('department'),
                    'user_created': user_created
                }, db
            )
            
            return {
                'user_id': user.id,
                'user_email': user_email,
                'role_id': user_role.id,
                'role_name': requested_role,
                'department': user_data.get('department'),
                'permissions': role_permissions,
                'user_created': user_created,
                'assigned_by': assigned_by,
                'assigned_at': user_role.assigned_at
            }
            
        finally:
            db.close()
    
    async def deprovision_user(self, institution_id: str, user_id: str, 
                             deprovisioned_by: str, reason: str = '') -> Dict[str, Any]:
        """Build institutional user deprovisioning workflows"""
        db = next(get_db())
        try:
            # Validate deprovisioner has permission
            deprovisioner_role = db.query(UserRole).filter(
                and_(
                    UserRole.user_id == deprovisioned_by,
                    UserRole.institution_id == institution_id,
                    UserRole.is_active == True
                )
            ).first()
            
            if not deprovisioner_role:
                raise ValueError("Deprovisioner not found or not authorized")
            
            # Get user role to be deprovisioned
            user_role = db.query(UserRole).filter(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.institution_id == institution_id,
                    UserRole.is_active == True
                )
            ).first()
            
            if not user_role:
                raise ValueError("User role not found or already deprovisioned")
            
            # Check if deprovisioner can manage the user's role
            if not await self._can_manage_role(deprovisioner_role.role_name, user_role.role_name):
                raise ValueError(f"Insufficient permissions to deprovision role: {user_role.role_name}")
            
            # Deactivate the role
            user_role.is_active = False
            user_role.expires_at = datetime.now()
            
            # Archive permissions for audit purposes
            archived_permissions = user_role.permissions or {}
            archived_permissions['deprovisioned_at'] = datetime.now().isoformat()
            archived_permissions['deprovisioned_by'] = deprovisioned_by
            archived_permissions['reason'] = reason
            user_role.permissions = archived_permissions
            
            db.commit()
            
            # Log the deprovisioning
            await self._log_role_management_action(
                deprovisioned_by, institution_id, 'user_deprovisioning',
                {
                    'user_id': user_id,
                    'role_name': user_role.role_name,
                    'department': user_role.department,
                    'reason': reason
                }, db
            )
            
            return {
                'user_id': user_id,
                'role_id': user_role.id,
                'role_name': user_role.role_name,
                'department': user_role.department,
                'deprovisioned_by': deprovisioned_by,
                'deprovisioned_at': datetime.now(),
                'reason': reason
            }
            
        finally:
            db.close()
    
    async def get_institutional_access_logs(self, institution_id: str, 
                                          filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add audit logging for institutional access and activity monitoring"""
        db = next(get_db())
        try:
            # Base query for audit logs
            query = db.query(AuditLog).filter(
                AuditLog.institution_id == institution_id
            )
            
            # Apply filters
            if filters:
                if 'start_date' in filters:
                    query = query.filter(AuditLog.timestamp >= filters['start_date'])
                if 'end_date' in filters:
                    query = query.filter(AuditLog.timestamp <= filters['end_date'])
                if 'user_id' in filters:
                    query = query.filter(AuditLog.user_id == filters['user_id'])
                if 'action' in filters:
                    query = query.filter(AuditLog.action.contains(filters['action']))
                if 'success' in filters:
                    query = query.filter(AuditLog.success == filters['success'])
            
            # Get logs with pagination
            limit = filters.get('limit', 100) if filters else 100
            offset = filters.get('offset', 0) if filters else 0
            
            logs = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
            total_count = query.count()
            
            # Analyze access patterns
            access_patterns = await self._analyze_access_patterns(logs)
            
            # Get user activity summary
            user_activity = await self._get_user_activity_summary(institution_id, filters, db)
            
            # Get security alerts
            security_alerts = await self._detect_security_issues(logs)
            
            return {
                'institution_id': institution_id,
                'total_logs': total_count,
                'logs_returned': len(logs),
                'logs': [
                    {
                        'id': log.id,
                        'user_id': log.user_id,
                        'action': log.action,
                        'resource_type': log.resource_type,
                        'resource_id': log.resource_id,
                        'success': log.success,
                        'timestamp': log.timestamp,
                        'ip_address': log.ip_address,
                        'error_message': log.error_message
                    } for log in logs
                ],
                'access_patterns': access_patterns,
                'user_activity': user_activity,
                'security_alerts': security_alerts,
                'generated_at': datetime.now()
            }
            
        finally:
            db.close()
    
    async def get_role_management_dashboard(self, institution_id: str) -> Dict[str, Any]:
        """Generate comprehensive role management dashboard"""
        db = next(get_db())
        try:
            # Get all active user roles
            user_roles = db.query(UserRole).filter(
                and_(
                    UserRole.institution_id == institution_id,
                    UserRole.is_active == True
                )
            ).all()
            
            # Role distribution
            role_distribution = defaultdict(int)
            department_distribution = defaultdict(int)
            
            for role in user_roles:
                role_distribution[role.role_name] += 1
                if role.department:
                    department_distribution[role.department] += 1
            
            # Get recent role changes
            recent_changes = db.query(AuditLog).filter(
                and_(
                    AuditLog.institution_id == institution_id,
                    AuditLog.action.in_(['user_provisioning', 'user_deprovisioning', 'role_update']),
                    AuditLog.timestamp >= datetime.now() - timedelta(days=30)
                )
            ).order_by(AuditLog.timestamp.desc()).limit(20).all()
            
            # Get expiring roles
            expiring_roles = db.query(UserRole).filter(
                and_(
                    UserRole.institution_id == institution_id,
                    UserRole.is_active == True,
                    UserRole.expires_at.isnot(None),
                    UserRole.expires_at <= datetime.now() + timedelta(days=30)
                )
            ).all()
            
            # Permission analysis
            permission_usage = defaultdict(int)
            for role in user_roles:
                permissions = role.permissions or {}
                for perm_category, perms in permissions.items():
                    if isinstance(perms, list):
                        for perm in perms:
                            permission_usage[perm] += 1
            
            # Get institution role system configuration
            institution = db.query(Institution).filter(
                Institution.id == institution_id
            ).first()
            
            role_system_config = {}
            if institution and institution.settings:
                role_system_config = institution.settings.get('role_system', {})
            
            return {
                'institution_id': institution_id,
                'total_active_users': len(user_roles),
                'role_distribution': dict(role_distribution),
                'department_distribution': dict(department_distribution),
                'recent_changes': [
                    {
                        'id': change.id,
                        'action': change.action,
                        'user_id': change.user_id,
                        'timestamp': change.timestamp,
                        'success': change.success,
                        'metadata': change.audit_metadata
                    } for change in recent_changes
                ],
                'expiring_roles': [
                    {
                        'user_id': role.user_id,
                        'role_name': role.role_name,
                        'department': role.department,
                        'expires_at': role.expires_at,
                        'days_until_expiry': (role.expires_at - datetime.now()).days if role.expires_at else None
                    } for role in expiring_roles
                ],
                'permission_usage': dict(permission_usage),
                'role_system_config': role_system_config,
                'generated_at': datetime.now()
            }
            
        finally:
            db.close()
    
    async def _can_manage_role(self, manager_role: str, target_role: str) -> bool:
        """Check if a role can manage another role"""
        manager_config = self.role_hierarchy.get(manager_role, {})
        can_manage = manager_config.get('can_manage', [])
        
        return target_role in can_manage or 'all' in manager_config.get('permissions', [])
    
    async def _get_role_permissions(self, institution_id: str, role_name: str, 
                                  department: Optional[str], db: Session) -> Dict[str, Any]:
        """Get permissions for a role"""
        # Base role permissions
        base_permissions = self.role_hierarchy.get(role_name, {}).get('permissions', [])
        
        # Department-specific permissions
        dept_permissions = []
        if department:
            # Get from institution settings
            institution = db.query(Institution).filter(
                Institution.id == institution_id
            ).first()
            
            if institution and institution.settings:
                role_system = institution.settings.get('role_system', {})
                dept_perms = role_system.get('department_permissions', {})
                dept_permissions = dept_perms.get(department, [])
        
        return {
            'base_permissions': base_permissions,
            'department_permissions': dept_permissions,
            'role_level': self.role_hierarchy.get(role_name, {}).get('level', 1),
            'assigned_at': datetime.now().isoformat()
        }
    
    async def _log_role_management_action(self, user_id: Optional[str], institution_id: str,
                                        action: str, metadata: Dict[str, Any], db: Session):
        """Log role management actions for audit purposes"""
        audit_log = AuditLog(
            user_id=user_id,
            institution_id=institution_id,
            action=action,
            resource_type='role_management',
            resource_id=f"{institution_id}_{action}",
            success=True,
            audit_metadata=metadata
        )
        
        db.add(audit_log)
        db.commit()
    
    async def _analyze_access_patterns(self, logs: List[AuditLog]) -> Dict[str, Any]:
        """Analyze access patterns from audit logs"""
        patterns = {
            'peak_hours': defaultdict(int),
            'common_actions': defaultdict(int),
            'failed_attempts': 0,
            'unique_users': set(),
            'resource_access': defaultdict(int)
        }
        
        for log in logs:
            # Peak hours
            if log.timestamp:
                hour = log.timestamp.hour
                patterns['peak_hours'][hour] += 1
            
            # Common actions
            patterns['common_actions'][log.action] += 1
            
            # Failed attempts
            if not log.success:
                patterns['failed_attempts'] += 1
            
            # Unique users
            if log.user_id:
                patterns['unique_users'].add(log.user_id)
            
            # Resource access
            if log.resource_type:
                patterns['resource_access'][log.resource_type] += 1
        
        # Convert sets to counts
        patterns['unique_users'] = len(patterns['unique_users'])
        
        # Sort peak hours
        patterns['peak_hours'] = dict(sorted(patterns['peak_hours'].items(), 
                                           key=lambda x: x[1], reverse=True)[:5])
        
        return patterns
    
    async def _get_user_activity_summary(self, institution_id: str, 
                                       filters: Optional[Dict[str, Any]], db: Session) -> Dict[str, Any]:
        """Get user activity summary"""
        # Get active users
        active_users = db.query(UserRole).filter(
            and_(
                UserRole.institution_id == institution_id,
                UserRole.is_active == True
            )
        ).count()
        
        # Get recent activity
        time_filter = datetime.now() - timedelta(days=7)
        recent_activity = db.query(AuditLog).filter(
            and_(
                AuditLog.institution_id == institution_id,
                AuditLog.timestamp >= time_filter
            )
        ).count()
        
        return {
            'active_users': active_users,
            'recent_activity_7_days': recent_activity,
            'activity_rate': recent_activity / active_users if active_users > 0 else 0
        }
    
    async def _detect_security_issues(self, logs: List[AuditLog]) -> List[Dict[str, Any]]:
        """Detect potential security issues from logs"""
        alerts = []
        
        # Track failed login attempts by user
        failed_attempts = defaultdict(int)
        suspicious_ips = defaultdict(int)
        
        for log in logs:
            if not log.success and 'login' in log.action.lower():
                if log.user_id:
                    failed_attempts[log.user_id] += 1
                if log.ip_address:
                    suspicious_ips[log.ip_address] += 1
        
        # Alert for multiple failed attempts
        for user_id, attempts in failed_attempts.items():
            if attempts >= 5:
                alerts.append({
                    'type': 'multiple_failed_logins',
                    'severity': 'high',
                    'user_id': user_id,
                    'attempts': attempts,
                    'description': f'User {user_id} has {attempts} failed login attempts'
                })
        
        # Alert for suspicious IP addresses
        for ip, attempts in suspicious_ips.items():
            if attempts >= 10:
                alerts.append({
                    'type': 'suspicious_ip_activity',
                    'severity': 'medium',
                    'ip_address': ip,
                    'attempts': attempts,
                    'description': f'IP {ip} has {attempts} failed attempts'
                })
        
        return alerts