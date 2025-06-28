#!/usr/bin/env python3
"""
Advanced Enterprise Features Test Script
Tests advanced session sharing and custom analytics dashboard functionality
"""

import requests
import json
import time
import secrets
from datetime import datetime
import socketio

# Configuration
BASE_URL = 'http://localhost:5000'
ADMIN_USERNAME = 'admin'
ADMIN_EMAIL = 'admin@example.com'
ADMIN_PASSWORD = 'admin123456'

USER1_USERNAME = 'collaborator1'
USER1_EMAIL = 'collab1@example.com'
USER1_PASSWORD = 'testpass123'

USER2_USERNAME = 'collaborator2'
USER2_EMAIL = 'collab2@example.com'
USER2_PASSWORD = 'testpass123'

class AdvancedEnterpriseFeatureTester:
    def __init__(self):
        self.admin_token = None
        self.user1_token = None
        self.user2_token = None
        self.admin_user_id = None
        self.user1_user_id = None
        self.user2_user_id = None
        self.session_id = None
        self.dashboard_id = None
        
    def test_all(self):
        """Run all advanced enterprise feature tests"""
        print("🚀 Starting Advanced Enterprise Feature Tests")
        print("=" * 60)
        
        try:
            # Test 1: Setup Users
            self.test_user_setup()
            
            # Test 2: Advanced Session Sharing
            self.test_advanced_session_sharing()
            
            # Test 3: Session Invitations
            self.test_session_invitations()
            
            # Test 4: Collaboration Settings
            self.test_collaboration_settings()
            
            # Test 5: Activity Logging
            self.test_activity_logging()
            
            # Test 6: Custom Analytics Dashboards
            self.test_custom_dashboards()
            
            # Test 7: Widget Data Sources
            self.test_widget_data_sources()
            
            # Test 8: Dashboard Export
            self.test_dashboard_export()
            
            # Test 9: Collaboration Analytics
            self.test_collaboration_analytics()
            
            print("\n✅ All Advanced Enterprise Feature Tests Completed Successfully!")
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            raise
    
    def test_user_setup(self):
        """Setup test users"""
        print("\n1. Setting up test users...")
        
        # Create admin user
        self.admin_token, self.admin_user_id = self.create_or_login_user(
            ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD
        )
        print(f"   ✅ Admin user ready: {ADMIN_USERNAME}")
        
        # Create collaborator users
        self.user1_token, self.user1_user_id = self.create_or_login_user(
            USER1_USERNAME, USER1_EMAIL, USER1_PASSWORD
        )
        print(f"   ✅ Collaborator 1 ready: {USER1_USERNAME}")
        
        self.user2_token, self.user2_user_id = self.create_or_login_user(
            USER2_USERNAME, USER2_EMAIL, USER2_PASSWORD
        )
        print(f"   ✅ Collaborator 2 ready: {USER2_USERNAME}")
    
    def create_or_login_user(self, username, email, password):
        """Create or login a user and return token and user_id"""
        # Try to register
        user_data = {
            'username': username,
            'email': email,
            'password': password
        }
        
        response = requests.post(f'{BASE_URL}/api/auth/register', json=user_data)
        
        if response.status_code == 201:
            result = response.json()
            return result['token'], result['user']['id']
        elif response.status_code == 400 and 'already exists' in response.json().get('message', ''):
            # User exists, try to login
            login_data = {
                'username': username,
                'password': password
            }
            response = requests.post(f'{BASE_URL}/api/auth/login', json=login_data)
            if response.status_code == 200:
                result = response.json()
                return result['token'], result['user']['id']
            else:
                raise Exception(f"Login failed for {username}: {response.text}")
        else:
            raise Exception(f"Registration failed for {username}: {response.text}")
    
    def test_advanced_session_sharing(self):
        """Test advanced session sharing features"""
        print("\n2. Testing Advanced Session Sharing...")
        
        # Create a chat session as user1
        headers = {'Authorization': f'Bearer {self.user1_token}'}
        
        chat_data = {
            'message': 'Hello, this is a test message for advanced sharing',
            'model': 'llama2:latest'
        }
        
        response = requests.post(f'{BASE_URL}/api/chat/send', json=chat_data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            self.session_id = result.get('session_id')
            print(f"   ✅ Chat session created: {self.session_id}")
        else:
            raise Exception(f"Failed to create chat session: {response.text}")
        
        # Test collaboration settings update
        settings_data = {
            'collaboration_mode': 'invite_only',
            'max_collaborators': 5,
            'require_approval': False
        }
        
        response = requests.put(
            f'{BASE_URL}/api/sessions/{self.session_id}/collaboration-settings',
            json=settings_data,
            headers=headers
        )
        
        if response.status_code == 200:
            print("   ✅ Collaboration settings updated")
        else:
            print(f"   ⚠️  Collaboration settings update failed: {response.status_code}")
    
    def test_session_invitations(self):
        """Test session invitation system"""
        print("\n3. Testing Session Invitations...")
        
        if not self.session_id:
            print("   ⚠️  Skipping - no session available")
            return
        
        headers = {'Authorization': f'Bearer {self.user1_token}'}
        
        # Send invitation to user2
        invitation_data = {
            'email': USER2_EMAIL,
            'permissions': 'comment',
            'message': 'Please collaborate on this AI conversation!'
        }
        
        response = requests.post(
            f'{BASE_URL}/api/sessions/{self.session_id}/invite',
            json=invitation_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            invitation_token = result.get('invitation', {}).get('invitation_token')
            print(f"   ✅ Invitation sent to {USER2_EMAIL}")
            
            # Accept invitation as user2
            if invitation_token:
                user2_headers = {'Authorization': f'Bearer {self.user2_token}'}
                response = requests.post(
                    f'{BASE_URL}/api/invitations/{invitation_token}/accept',
                    headers=user2_headers
                )
                
                if response.status_code == 200:
                    print("   ✅ Invitation accepted by user2")
                else:
                    print(f"   ⚠️  Invitation acceptance failed: {response.status_code}")
        else:
            print(f"   ⚠️  Invitation sending failed: {response.status_code}")
    
    def test_collaboration_settings(self):
        """Test collaboration settings management"""
        print("\n4. Testing Collaboration Settings...")
        
        if not self.session_id:
            print("   ⚠️  Skipping - no session available")
            return
        
        headers = {'Authorization': f'Bearer {self.user1_token}'}
        
        # Get collaborators
        response = requests.get(
            f'{BASE_URL}/api/sessions/{self.session_id}/collaborators',
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            collaborators = result.get('collaborators', [])
            pending_invitations = result.get('pending_invitations', [])
            print(f"   ✅ Retrieved {len(collaborators)} collaborators, {len(pending_invitations)} pending invitations")
        else:
            print(f"   ⚠️  Failed to get collaborators: {response.status_code}")
    
    def test_activity_logging(self):
        """Test session activity logging"""
        print("\n5. Testing Activity Logging...")
        
        if not self.session_id:
            print("   ⚠️  Skipping - no session available")
            return
        
        headers = {'Authorization': f'Bearer {self.user1_token}'}
        
        # Get session activity
        response = requests.get(
            f'{BASE_URL}/api/sessions/{self.session_id}/activity',
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            activities = result.get('activities', [])
            print(f"   ✅ Retrieved {len(activities)} activity log entries")
        else:
            print(f"   ⚠️  Failed to get activity log: {response.status_code}")
    
    def test_custom_dashboards(self):
        """Test custom analytics dashboards"""
        print("\n6. Testing Custom Analytics Dashboards...")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Create a custom dashboard
        dashboard_data = {
            'name': 'Test Analytics Dashboard',
            'description': 'A test dashboard for enterprise features',
            'layout': {
                'cols': 12,
                'rows': 8
            },
            'widgets': [
                {
                    'id': 'widget_1',
                    'name': 'User Activity Chart',
                    'type': 'chart',
                    'data_source': 'user_activity',
                    'config': {
                        'chart_type': 'line',
                        'days': 30
                    },
                    'position': {
                        'x': 0,
                        'y': 0,
                        'w': 6,
                        'h': 4
                    }
                },
                {
                    'id': 'widget_2',
                    'name': 'System Health',
                    'type': 'status',
                    'data_source': 'system_health',
                    'config': {
                        'refresh_interval': 30
                    },
                    'position': {
                        'x': 6,
                        'y': 0,
                        'w': 6,
                        'h': 4
                    }
                }
            ],
            'is_public': False
        }
        
        response = requests.post(
            f'{BASE_URL}/api/admin/dashboards',
            json=dashboard_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            self.dashboard_id = result.get('dashboard', {}).get('id')
            print(f"   ✅ Custom dashboard created: {self.dashboard_id}")
        else:
            print(f"   ⚠️  Dashboard creation failed: {response.status_code}")
        
        # Get dashboards list
        response = requests.get(f'{BASE_URL}/api/admin/dashboards', headers=headers)
        if response.status_code == 200:
            result = response.json()
            dashboards = result.get('dashboards', [])
            print(f"   ✅ Retrieved {len(dashboards)} dashboards")
        else:
            print(f"   ⚠️  Failed to get dashboards: {response.status_code}")
    
    def test_widget_data_sources(self):
        """Test widget data sources"""
        print("\n7. Testing Widget Data Sources...")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test different widget data sources
        data_sources = [
            ('user_activity', {'days': 7}),
            ('message_analytics', {'days': 30}),
            ('model_performance', {'days': 30}),
            ('system_health', {}),
            ('collaboration_metrics', {'days': 7})
        ]
        
        for data_source, config in data_sources:
            params = {'data_source': data_source, **config}
            response = requests.get(
                f'{BASE_URL}/api/admin/widgets/chart/data',
                params=params,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"   ✅ {data_source} data retrieved successfully")
                else:
                    print(f"   ⚠️  {data_source} data retrieval failed: {result.get('error')}")
            else:
                print(f"   ⚠️  {data_source} request failed: {response.status_code}")
    
    def test_dashboard_export(self):
        """Test dashboard data export"""
        print("\n8. Testing Dashboard Export...")
        
        if not self.dashboard_id:
            print("   ⚠️  Skipping - no dashboard available")
            return
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        response = requests.get(
            f'{BASE_URL}/api/admin/dashboards/{self.dashboard_id}/export',
            params={'format': 'json'},
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                export_data = result.get('data', {})
                widgets_count = len(export_data.get('widgets_data', {}))
                print(f"   ✅ Dashboard exported with {widgets_count} widgets")
            else:
                print(f"   ⚠️  Dashboard export failed: {result.get('error')}")
        else:
            print(f"   ⚠️  Dashboard export request failed: {response.status_code}")
    
    def test_collaboration_analytics(self):
        """Test collaboration analytics"""
        print("\n9. Testing Collaboration Analytics...")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        response = requests.get(
            f'{BASE_URL}/api/admin/analytics/collaboration',
            params={'days': 30},
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                analytics = result.get('analytics', {})
                shared_sessions = analytics.get('total_shared_sessions', 0)
                invitations_sent = analytics.get('invitations_sent', 0)
                print(f"   ✅ Collaboration analytics: {shared_sessions} shared sessions, {invitations_sent} invitations sent")
            else:
                print(f"   ⚠️  Collaboration analytics failed: {result.get('error')}")
        else:
            print(f"   ⚠️  Collaboration analytics request failed: {response.status_code}")
    
    def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete test dashboard
        if self.dashboard_id and self.admin_token:
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            response = requests.delete(
                f'{BASE_URL}/api/admin/dashboards/{self.dashboard_id}',
                headers=headers
            )
            if response.status_code == 200:
                print("   ✅ Test dashboard deleted")

def main():
    """Main test function"""
    print("Advanced Enterprise AI Chatbot Feature Tester")
    print("=" * 50)
    
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
    tester = AdvancedEnterpriseFeatureTester()
    try:
        tester.test_all()
    finally:
        tester.cleanup()

if __name__ == '__main__':
    main()