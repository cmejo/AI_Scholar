#!/usr/bin/env python3
"""
Script to create the admin user for AI Scholar
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from auth.database import get_db_session
from auth.models import User
from auth.security import get_password_hash
from sqlalchemy.orm import Session

async def create_admin_user():
    """Create the admin user with specified credentials"""
    
    # Admin user details
    admin_data = {
        'username': 'cmejo',
        'email': 'account@cmejo.com',
        'password': '1@clingy.hague.murmur.LOVING',
        'name': 'Admin User',
        'role': 'admin'
    }
    
    try:
        # Get database session
        db_gen = get_db_session()
        db: Session = next(db_gen)
        
        # Check if admin user already exists
        existing_user = db.query(User).filter(
            (User.email == admin_data['email']) | 
            (User.username == admin_data['username'])
        ).first()
        
        if existing_user:
            print(f"Admin user already exists:")
            print(f"  Username: {existing_user.username}")
            print(f"  Email: {existing_user.email}")
            print(f"  Role: {existing_user.role}")
            
            # Update password if needed
            hashed_password = get_password_hash(admin_data['password'])
            existing_user.hashed_password = hashed_password
            existing_user.role = 'admin'  # Ensure admin role
            db.commit()
            print("✅ Admin password updated successfully!")
            return
        
        # Create new admin user
        hashed_password = get_password_hash(admin_data['password'])
        
        admin_user = User(
            username=admin_data['username'],
            email=admin_data['email'],
            hashed_password=hashed_password,
            name=admin_data['name'],
            role=admin_data['role'],
            is_active=True,
            is_verified=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Admin user created successfully!")
        print(f"  Username: {admin_user.username}")
        print(f"  Email: {admin_user.email}")
        print(f"  Role: {admin_user.role}")
        print(f"  User ID: {admin_user.id}")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def validate_password(password: str) -> bool:
    """Validate password meets requirements"""
    if len(password) < 1:
        return False
    
    has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
    has_number = any(c.isdigit() for c in password)
    
    return has_special and has_number

if __name__ == "__main__":
    # Validate the admin password meets requirements
    admin_password = '1@clingy.hague.murmur.LOVING'
    
    if not validate_password(admin_password):
        print("❌ Admin password does not meet requirements:")
        print("  - At least 1 character")
        print("  - At least one special character")
        print("  - At least one number")
        sys.exit(1)
    
    print("🚀 Creating admin user for AI Scholar...")
    print("Password validation: ✅ Passed")
    
    asyncio.run(create_admin_user())