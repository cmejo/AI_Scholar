"""
Authentication database operations
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.sql import func
import uuid

from core.database import Base, SessionLocal, engine
from auth.models import UserRole, UserStatus
from auth.security import SecurityManager

# Extend the existing User model with authentication fields
class UserAuth(Base):
    __tablename__ = "users_auth"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, unique=True)  # References users.id
    role = Column(String, default=UserRole.USER.value)
    status = Column(String, default=UserStatus.ACTIVE.value)
    password_hash = Column(String, nullable=False)
    password_reset_token = Column(String, nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    preferences = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    session_token = Column(String, nullable=False, unique=True)
    refresh_token = Column(String, nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    last_used_at = Column(DateTime, default=func.now())
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

class AuthDatabase:
    """Database operations for authentication"""
    
    def __init__(self):
        self.security = SecurityManager()
    
    def get_db(self) -> Session:
        """Get database session"""
        db = SessionLocal()
        try:
            return db
        finally:
            pass  # Don't close here, let the caller handle it
    
    def create_user(self, name: str, email: str, password: str, role: UserRole = UserRole.USER) -> dict:
        """Create a new user with authentication data"""
        db = SessionLocal()
        try:
            # First, check if user already exists
            from core.database import User
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                raise ValueError("User with this email already exists")
            
            # Create main user record
            user_id = str(uuid.uuid4())
            user = User(
                id=user_id,
                name=name,
                email=email,
                hashed_password="",  # We'll store the real hash in UserAuth
                is_active=True
            )
            db.add(user)
            
            # Create authentication record
            password_hash = self.security.hash_password(password)
            user_auth = UserAuth(
                user_id=user_id,
                role=role.value,
                password_hash=password_hash,
                email_verified=True  # Auto-verify for now
            )
            db.add(user_auth)
            
            db.commit()
            
            return {
                "id": user_id,
                "name": name,
                "email": email,
                "role": role.value,
                "is_active": True,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        """Authenticate user with email and password"""
        db = SessionLocal()
        try:
            from core.database import User
            
            # Get user and auth data
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return None
            
            user_auth = db.query(UserAuth).filter(UserAuth.user_id == user.id).first()
            if not user_auth:
                return None
            
            # Check if account is locked
            if user_auth.locked_until and user_auth.locked_until > datetime.utcnow():
                raise ValueError("Account is temporarily locked due to failed login attempts")
            
            # Verify password
            if not self.security.verify_password(password, user_auth.password_hash):
                # Increment failed attempts
                user_auth.failed_login_attempts += 1
                if user_auth.failed_login_attempts >= 5:
                    user_auth.locked_until = datetime.utcnow() + timedelta(minutes=30)
                db.commit()
                return None
            
            # Reset failed attempts on successful login
            user_auth.failed_login_attempts = 0
            user_auth.locked_until = None
            user.last_login = datetime.utcnow()
            db.commit()
            
            return {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "bio": user.bio,
                "location": user.location,
                "website": user.website,
                "role": user_auth.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login_at": user.last_login.isoformat() if user.last_login else None
            }
        finally:
            db.close()
    
    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID"""
        db = SessionLocal()
        try:
            from core.database import User
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            user_auth = db.query(UserAuth).filter(UserAuth.user_id == user.id).first()
            
            return {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "bio": user.bio,
                "location": user.location,
                "website": user.website,
                "role": user_auth.role if user_auth else UserRole.USER.value,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login_at": user.last_login.isoformat() if user.last_login else None
            }
        finally:
            db.close()
    
    def update_user(self, user_id: str, **kwargs) -> Optional[dict]:
        """Update user information"""
        db = SessionLocal()
        try:
            from core.database import User
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            user_auth = db.query(UserAuth).filter(UserAuth.user_id == user.id).first()
            
            # Update main user fields
            if "name" in kwargs:
                user.name = kwargs["name"]
            if "email" in kwargs:
                user.email = kwargs["email"]
            if "bio" in kwargs:
                user.bio = kwargs["bio"]
            if "location" in kwargs:
                user.location = kwargs["location"]
            if "website" in kwargs:
                user.website = kwargs["website"]
            if "is_active" in kwargs:
                user.is_active = kwargs["is_active"]
            
            # Update auth fields
            if user_auth and "role" in kwargs:
                user_auth.role = kwargs["role"]
            
            db.commit()
            
            return {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "bio": user.bio,
                "location": user.location,
                "website": user.website,
                "role": user_auth.role if user_auth else UserRole.USER.value,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login_at": user.last_login.isoformat() if user.last_login else None
            }
        finally:
            db.close()
    
    def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password"""
        db = SessionLocal()
        try:
            user_auth = db.query(UserAuth).filter(UserAuth.user_id == user_id).first()
            if not user_auth:
                return False
            
            # Verify current password
            if not self.security.verify_password(current_password, user_auth.password_hash):
                return False
            
            # Update password
            user_auth.password_hash = self.security.hash_password(new_password)
            db.commit()
            return True
        finally:
            db.close()
    
    def create_session(self, user_id: str, ip_address: str = None, user_agent: str = None) -> dict:
        """Create a new user session"""
        db = SessionLocal()
        try:
            session_token = self.security.generate_session_id()
            refresh_token = self.security.generate_session_id()
            expires_at = datetime.utcnow() + timedelta(days=7)
            
            session = UserSession(
                user_id=user_id,
                session_token=session_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.add(session)
            db.commit()
            
            return {
                "session_token": session_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at
            }
        finally:
            db.close()
    
    def get_session(self, session_token: str) -> Optional[dict]:
        """Get session by token"""
        db = SessionLocal()
        try:
            session = db.query(UserSession).filter(
                UserSession.session_token == session_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            ).first()
            
            if session:
                # Update last used time
                session.last_used_at = datetime.utcnow()
                db.commit()
                
                return {
                    "id": session.id,
                    "user_id": session.user_id,
                    "session_token": session.session_token,
                    "refresh_token": session.refresh_token,
                    "expires_at": session.expires_at
                }
            return None
        finally:
            db.close()
    
    def refresh_session(self, refresh_token: str) -> Optional[dict]:
        """Refresh a session using refresh token"""
        db = SessionLocal()
        try:
            session = db.query(UserSession).filter(
                UserSession.refresh_token == refresh_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            ).first()
            
            if session:
                # Generate new tokens
                new_session_token = self.security.generate_session_id()
                new_refresh_token = self.security.generate_session_id()
                new_expires_at = datetime.utcnow() + timedelta(days=7)
                
                session.session_token = new_session_token
                session.refresh_token = new_refresh_token
                session.expires_at = new_expires_at
                session.last_used_at = datetime.utcnow()
                
                db.commit()
                
                return {
                    "session_token": new_session_token,
                    "refresh_token": new_refresh_token,
                    "expires_at": new_expires_at,
                    "user_id": session.user_id
                }
            return None
        finally:
            db.close()
    
    def invalidate_session(self, session_token: str) -> bool:
        """Invalidate a session"""
        db = SessionLocal()
        try:
            session = db.query(UserSession).filter(
                UserSession.session_token == session_token
            ).first()
            
            if session:
                session.is_active = False
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    def invalidate_all_user_sessions(self, user_id: str) -> bool:
        """Invalidate all sessions for a user"""
        db = SessionLocal()
        try:
            db.query(UserSession).filter(
                UserSession.user_id == user_id
            ).update({"is_active": False})
            db.commit()
            return True
        finally:
            db.close()

# Initialize database tables
def init_auth_db():
    """Initialize authentication database tables"""
    Base.metadata.create_all(bind=engine)

# Create default admin user
def create_admin_user():
    """Create default admin user"""
    auth_db = AuthDatabase()
    try:
        admin_data = auth_db.create_user(
            name="Christopher Mejo",
            email="account@cmejo.com",
            password="Admin123!",
            role=UserRole.ADMIN
        )
        print(f"✅ Admin user created successfully!")
        print(f"📧 Email: account@cmejo.com")
        print(f"🔑 Password: Admin123!")
        print(f"👤 User ID: {admin_data['id']}")
        return admin_data
    except ValueError as e:
        if "already exists" in str(e):
            print("ℹ️  Admin user already exists")
            return None
        else:
            print(f"❌ Error creating admin user: {e}")
            raise e