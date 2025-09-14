"""
Authentication API routes
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from auth.models import (
    UserRegister, UserLogin, UserUpdate, PasswordChange, 
    PasswordReset, PasswordResetConfirm, TokenResponse, 
    RefreshTokenRequest, UserResponse
)
from auth.database import AuthDatabase
from auth.security import SecurityManager
from auth.dependencies import get_current_user, get_admin_user, get_current_active_user

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Initialize services
auth_db = AuthDatabase()
security = SecurityManager()

@router.post("/register")
async def register(user_data: UserRegister, request: Request):
    """Register a new user"""
    try:
        # Validate password strength
        password_validation = security.validate_password_strength(user_data.password)
        if not password_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Password does not meet requirements",
                    "errors": password_validation["errors"]
                }
            )
        
        # Create user
        user = auth_db.create_user(
            name=user_data.name,
            email=user_data.email,
            password=user_data.password,
            role=user_data.role
        )
        
        # Create session
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        session_data = auth_db.create_session(user["id"], client_ip, user_agent)
        
        # Create JWT tokens
        access_token = security.create_access_token({"sub": user["id"]})
        refresh_token = security.create_refresh_token({"sub": user["id"]})
        
        response_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 30 * 60,  # 30 minutes
            "user": user
        }
        return JSONResponse(content=response_data)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login")
async def login(login_data: UserLogin, request: Request):
    """Login user"""
    try:
        # Authenticate user
        user = auth_db.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create session
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        session_data = auth_db.create_session(user["id"], client_ip, user_agent)
        
        # Create JWT tokens
        token_expires = timedelta(hours=24) if login_data.remember_me else timedelta(minutes=30)
        access_token = security.create_access_token(
            {"sub": user["id"]}, 
            expires_delta=token_expires
        )
        refresh_token = security.create_refresh_token({"sub": user["id"]})
        
        expires_in = int(token_expires.total_seconds())
        
        response_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "user": user
        }
        return JSONResponse(content=response_data)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh")
async def refresh_token(refresh_data: RefreshTokenRequest):
    """Refresh access token"""
    try:
        # Verify refresh token
        payload = security.verify_token(refresh_data.refresh_token, "refresh")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = auth_db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new tokens
        access_token = security.create_access_token({"sub": user_id})
        new_refresh_token = security.create_refresh_token({"sub": user_id})
        
        response_data = {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": 30 * 60,  # 30 minutes
            "user": user
        }
        return JSONResponse(content=response_data)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user (invalidate session)"""
    try:
        # In a real implementation, you'd invalidate the session
        # For JWT tokens, you might maintain a blacklist
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return JSONResponse(content=current_user)

@router.get("/validate")
async def validate_token(current_user: dict = Depends(get_current_user)):
    """Validate current token"""
    return JSONResponse(content={
        "valid": True,
        "user": current_user
    })

@router.patch("/profile")
async def update_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    try:
        # Only allow users to update their own profile (unless admin)
        user_id = current_user["id"]
        
        # Update user with all provided fields
        update_data = {}
        if user_update.name is not None:
            update_data["name"] = user_update.name
        if user_update.email is not None:
            update_data["email"] = user_update.email
        if user_update.bio is not None:
            update_data["bio"] = user_update.bio
        if user_update.location is not None:
            update_data["location"] = user_update.location
        if user_update.website is not None:
            update_data["website"] = user_update.website
        
        updated_user = auth_db.update_user(user_id, **update_data)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return JSONResponse(content=updated_user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(e)}"
        )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user)
):
    """Change user password"""
    try:
        # Validate new password strength
        password_validation = security.validate_password_strength(password_data.new_password)
        if not password_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "New password does not meet requirements",
                    "errors": password_validation["errors"]
                }
            )
        
        # Change password
        success = auth_db.change_password(
            current_user["id"],
            password_data.current_password,
            password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        return {"message": "Password changed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset):
    """Request password reset"""
    try:
        # In a real implementation, you'd send an email with reset link
        # For now, just return success
        return {"message": "Password reset email sent (if email exists)"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )

# Admin endpoints
@router.get("/users")
async def list_users(admin_user: dict = Depends(get_admin_user)):
    """List all users (admin only)"""
    try:
        # This would need to be implemented in AuthDatabase
        return []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.patch("/users/{user_id}")
async def update_user_admin(
    user_id: str,
    user_update: UserUpdate,
    admin_user: dict = Depends(get_admin_user)
):
    """Update any user (admin only)"""
    try:
        updated_user = auth_db.update_user(
            user_id,
            name=user_update.name,
            email=user_update.email,
            role=user_update.role.value if user_update.role else None,
            is_active=user_update.is_active
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return JSONResponse(content=updated_user)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed"
        )