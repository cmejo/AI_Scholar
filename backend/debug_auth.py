#!/usr/bin/env python3
"""
Debug script to test auth database methods
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth.database import AuthDatabase
from auth.security import SecurityManager
import json

def test_user_retrieval():
    """Test user retrieval and serialization"""
    auth_db = AuthDatabase()
    security = SecurityManager()
    
    # Create a test token
    test_payload = {"sub": "test-user-id"}
    token = security.create_access_token(test_payload)
    print(f"Created token: {token}")
    
    # Try to verify it
    try:
        payload = security.verify_token(token, "access")
        print(f"Token payload: {payload}")
        user_id = payload.get("sub")
        
        # Try to get user
        user = auth_db.get_user_by_id(user_id)
        print(f"User data: {user}")
        
        # Try to serialize to JSON
        if user:
            json_str = json.dumps(user)
            print(f"JSON serialization successful: {json_str}")
        else:
            print("User not found")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_retrieval()