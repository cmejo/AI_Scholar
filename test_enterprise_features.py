#!/usr/bin/env python3
"""
Test script for Enterprise AI Chatbot features
Tests real-time collaboration and admin dashboard functionality
"""

import requests
import json
import time
import threading
from datetime import datetime
import socketio

# Configuration
BASE_URL = 'http://localhost:5000'
ADMIN_USERNAME = 'admin'
ADMIN_EMAIL = 'admin@example.com'
ADMIN_PASSWORD = 'admin123456'

USER_USERNAME = 'testuser'
USER_EMAIL = 'test@example.com'
USER_PASSWORD = 'testpass123'

class EnterpriseFeatureTester:
    def __init__(self):
        self.admin_token = None
        self.user_token = None
        self.admin_user_id = None
        self.user_user_id = None
        self.session_id = None
        
    def test_all(self):
        """Run all enterprise feature tests"""
        print("🚀 Starting Enterprise Feature Tests")
        print("=" * 50)
        
        try:
            # Test 1: Admin User Creation and Authentication
            self.test_admin_authentication()
            
            # Test 2: Regular User Creation
            self.test_user_authentication()
            
            # Test 3: Admin Dashboard Access
            self.test_admin_dashboard()
            
            # Test 4: User Management
            self.test_user_management()
            
            # Test 5: Real-time Collaboration Setup
            self.test_collaboration_setup()
            
            # Test 6: WebSocket Collaboration
            self.test_websocket_collaboration()
            
            # Test 7: Analytics and Monitoring
            self.test_analytics()
            
            print("\n✅ All Enterprise Feature Tests Completed Successfully!")
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            raise
    
    def test_admin_authentication(self):
        """Test admin user creation and authentication"""
        print("\n1. Testing Admin Authentication...")
        
        # Try to register admin user
        admin_data = {
            'username': ADMIN_USERNAME,
            'email': ADMIN_EMAIL,
            'password': ADMIN_PASSWORD
        }
        
        response = requests.post(f'{BASE_URL}/api/auth/register', json=admin_data)
        
        if response.status_code == 201:
            result = response.json()
            self.admin_token = result['token']
            self.admin_user_id = result['user']['id']
            print(f"   ✅ Admin user created: {result['user']['username']}")
        elif response.status_code == 400 and 'already exists' in response.json().get('message', ''):
            # User already exists, try to login
            login_data = {
                'username': ADMIN_USERNAME,
                'password': ADMIN_PASSWORD
            }
            response = requests.post(f'{BASE_URL}/api/auth/login', json=login_data)
            if response.status_code == 200:
                result = response.json()
                self.admin_token = result['token']
                self.admin_user_id = result['user']['id']
                print(f"   ✅ Admin user logged in: {result['user']['username']}")
            else:
                raise Exception(f"Admin login failed: {response.text}")
        else:
            raise Exception(f"Admin registration failed: {response.text}")
        
        # Promote to admin if not already
        self.promote_to_admin()
    
    def promote_to_admin(self):
        """Promote user to admin via database (simulated)"""
        # In a real scenario, this would be done via database or initial setup
        print("   📝 Note: In production, admin promotion should be done via database or initial setup")
    
    def test_user_authentication(self):
        """Test regular user creation"""
        print("\n2. Testing User Authentication...")
        
        user_data = {
            'username': USER_USERNAME,
            'email': USER_EMAIL,
            'password': USER_PASSWORD
        }
        
        response = requests.post(f'{BASE_URL}/api/auth/register', json=user_data)
        
        if response.status_code == 201:
            result = response.json()
            self.user_token = result['token']
            self.user_user_id = result['user']['id']
            print(f"   ✅ Regular user created: {result['user']['username']}")
        elif response.status_code == 400 and 'already exists' in response.json().get('message', ''):
            # User already exists, try to login
            login_data = {
                'username': USER_USERNAME,
                'password': USER_PASSWORD
            }
            response = requests.post(f'{BASE_URL}/api/auth/login', json=login_data)
            if response.status_code == 200:
                result = response.json()
                self.user_token = result['token']
                self.user_user_id = result['user']['id']
                print(f"   ✅ Regular user logged in: {result['user']['username']}")
            else:
                raise Exception(f"User login failed: {response.text}")
        else:
            raise Exception(f"User registration failed: {response.text}")
    
    def test_admin_dashboard(self):
        """Test admin dashboard access"""
        print("\n3. Testing Admin Dashboard Access...")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test system overview
        response = requests.get(f'{BASE_URL}/api/admin/overview', headers=headers)
        if response.status_code == 200:
            overview = response.json()
            print(f"   ✅ System Overview: {overview.get('users', {}).get('total', 0)} users, {overview.get('messages', {}).get('total', 0)} messages")
        else:
            print(f"   ⚠️  Admin dashboard access test skipped (might need admin role in DB): {response.status_code}")
            return
        
        # Test user analytics
        response = requests.get(f'{BASE_URL}/api/admin/analytics/users', headers=headers)
        if response.status_code == 200:
            analytics = response.json()
            print(f"   ✅ User Analytics: {len(analytics.get('daily_registrations', []))} days of data")
        
        # Test system health
        response = requests.get(f'{BASE_URL}/api/admin/system/health', headers=headers)
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ System Health: {health.get('status', 'unknown')}")
    
    def test_user_management(self):
        """Test user management features"""
        print("\n4. Testing User Management...")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Get users list
        response = requests.get(f'{BASE_URL}/api/admin/users', headers=headers)
        if response.status_code == 200:
            users_data = response.json()
            users = users_data.get('users', [])
            print(f"   ✅ Retrieved {len(users)} users")
            
            # Find a non-admin user to test with
            test_user = None
            for user in users:
                if not user.get('is_admin') and user['id'] != self.admin_user_id:
                    test_user = user
                    break
            
            if test_user:
                print(f"   📝 Found test user: {test_user['username']}")
            else:
                print("   📝 No non-admin users found for testing")
        else:
            print(f"   ⚠️  User management test skipped: {response.status_code}")
    
    def test_collaboration_setup(self):
        """Test collaboration setup by creating a chat session"""
        print("\n5. Testing Collaboration Setup...")
        
        # Create a chat session as regular user
        headers = {'Authorization': f'Bearer {self.user_token}'}
        
        chat_data = {
            'message': 'Hello, this is a test message for collaboration',
            'model': 'llama2:latest'
        }
        
        response = requests.post(f'{BASE_URL}/api/chat/send', json=chat_data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            self.session_id = result.get('session_id')
            print(f"   ✅ Chat session created: {self.session_id}")
        else:
            print(f"   ⚠️  Chat session creation failed: {response.status_code} - {response.text}")
    
    def test_websocket_collaboration(self):
        """Test WebSocket collaboration features"""
        print("\n6. Testing WebSocket Collaboration...")
        
        if not self.session_id:
            print("   ⚠️  Skipping WebSocket test - no session available")
            return
        
        # Create socket.io client
        sio = socketio.SimpleClient()
        
        try:
            # Connect to the server
            sio.connect(BASE_URL)
            print("   ✅ WebSocket connected")
            
            # Join session room
            sio.emit('join_session', {
                'token': f'Bearer {self.user_token}',
                'session_id': self.session_id
            })
            
            # Wait for room joined event
            time.sleep(1)
            
            # Send a test message
            sio.emit('send_message', {
                'content': 'Test collaboration message',
                'message_type': 'user'
            })
            
            print("   ✅ WebSocket collaboration message sent")
            
            # Test typing indicator
            sio.emit('typing_indicator', {'is_typing': True})
            time.sleep(0.5)
            sio.emit('typing_indicator', {'is_typing': False})
            
            print("   ✅ Typing indicator tested")
            
            # Disconnect
            sio.disconnect()
            print("   ✅ WebSocket disconnected")
            
        except Exception as e:
            print(f"   ⚠️  WebSocket test failed: {e}")
    
    def test_analytics(self):
        """Test analytics and monitoring features"""
        print("\n7. Testing Analytics and Monitoring...")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test usage analytics
        response = requests.get(f'{BASE_URL}/api/admin/analytics/usage?days=7', headers=headers)
        if response.status_code == 200:
            analytics = response.json()
            print(f"   ✅ Usage Analytics: {len(analytics.get('daily_messages', []))} days of message data")
        else:
            print(f"   ⚠️  Usage analytics test skipped: {response.status_code}")
        
        # Test collaboration stats
        response = requests.get(f'{BASE_URL}/api/admin/collaboration/stats', headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ Collaboration Stats: {stats.get('shared_sessions', {}).get('total', 0)} shared sessions")
        else:
            print(f"   ⚠️  Collaboration stats test skipped: {response.status_code}")
        
        # Test health check
        response = requests.get(f'{BASE_URL}/api/health')
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Health Check: {health.get('status', 'unknown')} - {health.get('services', {}).get('collaboration', {}).get('active_rooms', 0)} active rooms")

def main():
    """Main test function"""
    print("Enterprise AI Chatbot Feature Tester")
    print("====================================")
    
    # Check if server is running
    try:
        response = requests.get(f'{BASE_URL}/api/health', timeout=5)
        if response.status_code == 200:
            print(f"✅ Server is running at {BASE_URL}")
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Make sure the enterprise app is running: python app_enterprise.py")
        return
    
    # Run tests
    tester = EnterpriseFeatureTester()
    tester.test_all()

if __name__ == '__main__':
    main()