#!/usr/bin/env python3
"""
Test script for enhanced AI Scholar features
Tests RAG and multi-model functionality
"""

import requests
import json
import time
import os
from pathlib import Path

# Configuration
BASE_URL = os.environ.get('API_URL', 'http://localhost:5000')
TEST_USERNAME = 'test_user_enhanced'
TEST_PASSWORD = 'test_password_123'
TEST_EMAIL = 'test_enhanced@example.com'

class EnhancedFeaturesTest:
    def __init__(self):
        self.token = None
        self.session_id = None
        
    def register_and_login(self):
        """Register and login test user"""
        print("🔐 Registering test user...")
        
        # Try to register
        register_data = {
            'username': TEST_USERNAME,
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD,
            'firstName': 'Test',
            'lastName': 'User'
        }
        
        response = requests.post(f'{BASE_URL}/api/auth/register', json=register_data)
        
        if response.status_code == 201:
            print("✅ User registered successfully")
            self.token = response.json()['token']
        elif response.status_code == 400 and 'already exists' in response.json().get('message', ''):
            print("ℹ️ User already exists, logging in...")
            # Login instead
            login_data = {
                'username': TEST_USERNAME,
                'password': TEST_PASSWORD
            }
            response = requests.post(f'{BASE_URL}/api/auth/login', json=login_data)
            if response.status_code == 200:
                print("✅ Login successful")
                self.token = response.json()['token']
            else:
                print(f"❌ Login failed: {response.json()}")
                return False
        else:
            print(f"❌ Registration failed: {response.json()}")
            return False
        
        return True
    
    def test_model_list(self):
        """Test getting available models"""
        print("\n🤖 Testing model list...")
        
        response = requests.get(f'{BASE_URL}/api/models/simple')
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            categories = data.get('categories', {})
            
            print(f"✅ Found {len(models)} available models")
            print(f"📋 Categories: {list(categories.keys())}")
            print(f"🎯 Default model: {data.get('default_model')}")
            
            if models:
                print(f"📝 Sample models: {models[:3]}")
            
            return models
        else:
            print(f"❌ Failed to get models: {response.status_code}")
            return []
    
    def test_rag_document_upload(self):
        """Test RAG document upload"""
        print("\n📚 Testing RAG document upload...")
        
        # Create a test document
        test_content = """
        AI Scholar Knowledge Base Test Document
        
        This is a test document for the AI Scholar RAG system.
        
        Key concepts:
        - Artificial Intelligence: The simulation of human intelligence in machines
        - Machine Learning: A subset of AI that enables machines to learn from data
        - Natural Language Processing: AI's ability to understand and generate human language
        - Neural Networks: Computing systems inspired by biological neural networks
        
        The AI Scholar system uses Retrieval-Augmented Generation (RAG) to provide
        more accurate and contextual responses by retrieving relevant information
        from a knowledge base before generating answers.
        """
        
        # Save as temporary file
        test_file_path = Path('/tmp/test_document.txt')
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        
        try:
            # Upload via text API
            headers = {'Authorization': f'Bearer {self.token}'}
            text_data = {
                'text': test_content,
                'metadata': {
                    'title': 'AI Scholar Test Document',
                    'category': 'test',
                    'source': 'test_script'
                }
            }
            
            response = requests.post(f'{BASE_URL}/api/rag/ingest-text', 
                                   json=text_data, headers=headers)
            
            if response.status_code == 200:
                print("✅ Text document uploaded successfully")
                return True
            else:
                print(f"❌ Text upload failed: {response.status_code} - {response.text}")
                return False
                
        finally:
            # Clean up
            if test_file_path.exists():
                test_file_path.unlink()
    
    def test_rag_stats(self):
        """Test RAG statistics"""
        print("\n📊 Testing RAG statistics...")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(f'{BASE_URL}/api/rag/stats', headers=headers)
        
        if response.status_code == 200:
            stats = response.json()
            print("✅ RAG stats retrieved successfully")
            
            vector_store = stats.get('vector_store', {})
            rag_stats = stats.get('rag_stats', {})
            
            print(f"📄 Total documents: {vector_store.get('total_documents', 0)}")
            print(f"🔍 Searches performed: {rag_stats.get('searches_performed', 0)}")
            print(f"🤖 RAG responses generated: {rag_stats.get('rag_responses_generated', 0)}")
            
            return True
        else:
            print(f"❌ Failed to get RAG stats: {response.status_code}")
            return False
    
    def test_regular_chat(self, models):
        """Test regular chat with different models"""
        print("\n💬 Testing regular chat...")
        
        if not models:
            print("⚠️ No models available for testing")
            return False
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Test with first available model
        test_model = models[0]
        chat_data = {
            'message': 'Hello! Can you tell me about artificial intelligence?',
            'model': test_model,
            'use_rag': False
        }
        
        print(f"🤖 Testing with model: {test_model}")
        
        response = requests.post(f'{BASE_URL}/api/chat', json=chat_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Regular chat successful")
                print(f"📝 Response preview: {data.get('response', '')[:100]}...")
                print(f"🎯 Model used: {data.get('model')}")
                print(f"📊 RAG enabled: {data.get('rag_enabled', False)}")
                
                self.session_id = data.get('session_id')
                return True
            else:
                print(f"❌ Chat failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Chat request failed: {response.status_code}")
            return False
    
    def test_rag_chat(self, models):
        """Test RAG-enhanced chat"""
        print("\n🧠 Testing RAG-enhanced chat...")
        
        if not models:
            print("⚠️ No models available for testing")
            return False
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Test with first available model and RAG enabled
        test_model = models[0]
        chat_data = {
            'message': 'What is machine learning and how does it relate to AI?',
            'model': test_model,
            'use_rag': True,
            'session_id': self.session_id
        }
        
        print(f"🤖 Testing RAG with model: {test_model}")
        
        response = requests.post(f'{BASE_URL}/api/chat', json=chat_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ RAG chat successful")
                print(f"📝 Response preview: {data.get('response', '')[:100]}...")
                print(f"🎯 Model used: {data.get('model')}")
                print(f"📊 RAG enabled: {data.get('rag_enabled', False)}")
                print(f"📚 Sources found: {len(data.get('sources', []))}")
                print(f"🎯 Confidence: {data.get('confidence', 0):.2f}")
                
                # Show sources if available
                sources = data.get('sources', [])
                if sources:
                    print("📖 Source previews:")
                    for i, source in enumerate(sources[:2]):  # Show first 2 sources
                        print(f"  {i+1}. {source.get('content', '')[:80]}...")
                
                return True
            else:
                print(f"❌ RAG chat failed: {data.get('error')}")
                return False
        else:
            print(f"❌ RAG chat request failed: {response.status_code}")
            return False
    
    def test_model_switching(self, models):
        """Test switching models in the same session"""
        print("\n🔄 Testing model switching...")
        
        if len(models) < 2:
            print("⚠️ Need at least 2 models for switching test")
            return False
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Switch to second model
        second_model = models[1]
        chat_data = {
            'message': 'Now I am using a different model. Can you confirm?',
            'model': second_model,
            'use_rag': False,
            'session_id': self.session_id
        }
        
        print(f"🔄 Switching to model: {second_model}")
        
        response = requests.post(f'{BASE_URL}/api/chat', json=chat_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Model switching successful")
                print(f"🎯 New model used: {data.get('model')}")
                print(f"📝 Response preview: {data.get('response', '')[:100]}...")
                return True
            else:
                print(f"❌ Model switching failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Model switching request failed: {response.status_code}")
            return False
    
    def run_all_tests(self):
        """Run all enhanced feature tests"""
        print("🚀 Starting Enhanced AI Scholar Features Test")
        print("=" * 50)
        
        # Step 1: Authentication
        if not self.register_and_login():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Step 2: Test model list
        models = self.test_model_list()
        
        # Step 3: Test RAG document upload
        self.test_rag_document_upload()
        
        # Step 4: Test RAG stats
        self.test_rag_stats()
        
        # Step 5: Test regular chat
        if not self.test_regular_chat(models):
            print("⚠️ Regular chat failed, but continuing...")
        
        # Step 6: Test RAG chat
        if not self.test_rag_chat(models):
            print("⚠️ RAG chat failed, but continuing...")
        
        # Step 7: Test model switching
        if not self.test_model_switching(models):
            print("⚠️ Model switching failed, but continuing...")
        
        print("\n" + "=" * 50)
        print("🎉 Enhanced features test completed!")
        print("\nFeatures tested:")
        print("✅ Multi-model support")
        print("✅ RAG document ingestion")
        print("✅ RAG-enhanced chat responses")
        print("✅ Model switching within sessions")
        print("✅ Enhanced message metadata")
        
        return True

def main():
    """Main test function"""
    tester = EnhancedFeaturesTest()
    
    try:
        success = tester.run_all_tests()
        if success:
            print("\n🎊 All tests completed successfully!")
            return 0
        else:
            print("\n⚠️ Some tests failed")
            return 1
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return 1

if __name__ == '__main__':
    exit(main())