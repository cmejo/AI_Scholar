#!/usr/bin/env python3
"""
Test script for Docker setup
Verifies that all services are running correctly
"""

import requests
import json
import time
import sys

def test_service(url, name, timeout=30):
    """Test if a service is responding"""
    print(f"Testing {name}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name} is responding")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    
    print(f"❌ {name} is not responding after {timeout}s")
    return False

def test_ollama():
    """Test Ollama service"""
    if not test_service("http://localhost:11434/api/tags", "Ollama"):
        return False
    
    try:
        response = requests.get("http://localhost:11434/api/tags")
        data = response.json()
        models = [model['name'] for model in data.get('models', [])]
        print(f"📦 Available models: {', '.join(models) if models else 'None'}")
        return True
    except Exception as e:
        print(f"❌ Error checking Ollama models: {e}")
        return False

def test_backend():
    """Test backend service"""
    if not test_service("http://localhost:5000/api/health", "Backend"):
        return False
    
    try:
        response = requests.get("http://localhost:5000/api/health")
        data = response.json()
        print(f"🏥 Backend status: {data.get('status')}")
        print(f"🤖 Ollama connection: {data.get('services', {}).get('ollama', {}).get('status')}")
        return True
    except Exception as e:
        print(f"❌ Error checking backend health: {e}")
        return False

def test_models_endpoint():
    """Test models endpoint"""
    try:
        response = requests.get("http://localhost:5000/api/models/simple")
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            default_model = data.get('default_model')
            print(f"🎯 Default model: {default_model}")
            print(f"📋 Models via backend: {', '.join(models) if models else 'None'}")
            return True
        else:
            print(f"❌ Models endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing models endpoint: {e}")
        return False

def test_auth():
    """Test authentication"""
    try:
        # Test registration
        user_data = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "testpassword123"
        }
        
        response = requests.post("http://localhost:5000/api/auth/register", json=user_data)
        if response.status_code == 201:
            print("✅ User registration works")
            data = response.json()
            token = data.get('token')
            
            # Test protected endpoint
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get("http://localhost:5000/api/auth/me", headers=headers)
            if response.status_code == 200:
                print("✅ Authentication works")
                return True
            else:
                print(f"❌ Protected endpoint failed: {response.status_code}")
                return False
        else:
            print(f"❌ Registration failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing authentication: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Docker Setup")
    print("=" * 40)
    
    tests = [
        ("Ollama Service", test_ollama),
        ("Backend Service", test_backend),
        ("Models Endpoint", test_models_endpoint),
        ("Authentication", test_auth),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}")
        print("-" * 20)
        if test_func():
            passed += 1
        else:
            print(f"💥 {test_name} failed")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Docker setup is working correctly.")
        print("\n🚀 Your AI Scholar Chatbot is ready to use!")
        print("📋 Next steps:")
        print("  1. Access the API at http://localhost:5000")
        print("  2. Start your React frontend")
        print("  3. Begin chatting with your local AI models!")
        return True
    else:
        print("❌ Some tests failed. Please check the Docker logs:")
        print("  docker-compose -f docker-compose.ollama.yml logs")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)