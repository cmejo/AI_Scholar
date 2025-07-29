"""
Authentication service
"""
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db, User
from models.schemas import UserCreate, UserResponse

class AuthService:
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user"""
        db = next(get_db())
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == user_data.email).first()
            if existing_user:
                raise ValueError("User with this email already exists")
            
            # Hash password
            hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
            
            # Create user
            user = User(
                email=user_data.email,
                name=user_data.name,
                hashed_password=hashed_password.decode('utf-8')
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                created_at=user.created_at
            )
            
        finally:
            db.close()
    
    async def authenticate_user(self, email: str, password: str) -> dict:
        """Authenticate user and return token"""
        db = next(get_db())
        try:
            # Get user
            user = db.query(User).filter(User.email == email).first()
            if not user:
                raise ValueError("Invalid credentials")
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
                raise ValueError("Invalid credentials")
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()
            
            # Generate token
            token_data = {
                "sub": user.id,
                "email": user.email,
                "exp": datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            }
            
            token = jwt.encode(token_data, self.secret_key, algorithm=self.algorithm)
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": UserResponse(
                    id=user.id,
                    email=user.email,
                    name=user.name,
                    created_at=user.created_at
                )
            }
            
        finally:
            db.close()
    
    async def verify_token(self, token: str) -> UserResponse:
        """Verify JWT token and return user"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            
            if user_id is None:
                raise ValueError("Invalid token")
            
            db = next(get_db())
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if user is None:
                    raise ValueError("User not found")
                
                return UserResponse(
                    id=user.id,
                    email=user.email,
                    name=user.name,
                    created_at=user.created_at
                )
            finally:
                db.close()
                
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.JWTError:
            raise ValueError("Invalid token")