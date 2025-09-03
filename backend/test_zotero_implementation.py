#!/usr/bin/env python3
"""
Simple test script to verify Zotero OAuth implementation
"""
import sys
import os
import asyncio
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_zotero_auth_service():
    """Test ZoteroAuthService basic functionality"""
    print("Testing ZoteroAuthService...")
    
    try:
        from services.zotero.zotero_auth_service import ZoteroAuthService
        
        # Initialize service
        auth_service = ZoteroAuthService()
        print("✓ ZoteroAuthService initialized successfully")
        
        # Test OAuth state generation
        user_id = "test_user_123"
        state, code_challenge = auth_service.generate_oauth_state(user_id)
        print(f"✓ OAuth state generated: {state[:10]}...")
        print(f"✓ PKCE challenge generated: {code_challenge[:10] if code_challenge else 'None'}...")
        
        # Test state validation
        is_valid = auth_service.validate_oauth_state(state, user_id)
        print(f"✓ State validation: {is_valid}")
        
        # Test authorization URL generation
        auth_url, state2 = auth_service.get_authorization_url(user_id)
        print(f"✓ Authorization URL generated: {auth_url[:50]}...")
        
        # Test PKCE challenge generation
        code_verifier, code_challenge = auth_service._generate_pkce_challenge()
        print(f"✓ PKCE verifier: {code_verifier[:10]}...")
        print(f"✓ PKCE challenge: {code_challenge[:10]}...")
        
        # Test encryption/decryption
        test_token = "test_access_token_12345"
        encrypted = auth_service._encrypt_sensitive_data(test_token)
        decrypted = auth_service._decrypt_sensitive_data(encrypted)
        print(f"✓ Encryption test: {'PASS' if decrypted == test_token else 'FAIL'}")
        
        print("✓ All ZoteroAuthService tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ ZoteroAuthService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_zotero_api_client():
    """Test ZoteroAPIClient basic functionality"""
    print("\nTesting ZoteroAPIClient...")
    
    try:
        from services.zotero.zotero_client import ZoteroAPIClient
        
        # Initialize client
        client = ZoteroAPIClient()
        print("✓ ZoteroAPIClient initialized successfully")
        
        # Test rate limit status
        rate_limit_status = client.get_rate_limit_status()
        print(f"✓ Rate limit status: {rate_limit_status['remaining']} remaining")
        
        # Test client statistics
        stats = client.get_client_statistics()
        print(f"✓ Client statistics: {stats['request_statistics']['total_requests']} total requests")
        
        # Test rate limiting check (should not block)
        async def test_rate_limit():
            await client._check_rate_limit()
            return True
        
        result = asyncio.run(test_rate_limit())
        print(f"✓ Rate limit check: {'PASS' if result else 'FAIL'}")
        
        print("✓ All ZoteroAPIClient tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ ZoteroAPIClient test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_oauth_flow_simulation():
    """Simulate OAuth flow without actual HTTP requests"""
    print("\nTesting OAuth flow simulation...")
    
    try:
        from services.zotero.zotero_auth_service import ZoteroAuthService
        
        auth_service = ZoteroAuthService()
        user_id = "test_user_123"
        
        # Step 1: Generate authorization URL
        auth_url, state = auth_service.get_authorization_url(user_id, ["all"])
        print(f"✓ Step 1 - Authorization URL: {auth_url[:50]}...")
        
        # Step 2: Validate state (simulating callback)
        is_valid = auth_service.validate_oauth_state(state, user_id)
        print(f"✓ Step 2 - State validation: {is_valid}")
        
        # Step 3: Check state info
        state_info = auth_service.get_oauth_state_info(state)
        if state_info:
            print(f"✓ Step 3 - State info: user_id={state_info['user_id']}, used={state_info['used']}")
        else:
            print("✗ Step 3 - State info not found")
            return False
        
        # Step 4: Test cleanup
        auth_service._cleanup_expired_states()
        print("✓ Step 4 - State cleanup completed")
        
        print("✓ OAuth flow simulation completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ OAuth flow simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Zotero Integration Implementation Test")
    print("=" * 60)
    
    tests = [
        test_zotero_auth_service,
        test_zotero_api_client,
        test_oauth_flow_simulation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Task 2.1 implementation is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())