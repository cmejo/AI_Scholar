#!/usr/bin/env python3
"""
Test script for multimodal AI vision support
"""

import requests
import base64
import json
import os
from pathlib import Path

def test_vision_api():
    """Test the vision API endpoint"""
    
    # API configuration
    api_url = "http://localhost:5001"
    
    # Test credentials (you'll need to register first)
    test_user = {
        "username": "test_vision_user",
        "email": "test@example.com", 
        "password": "testpassword123"
    }
    
    print("🔍 Testing Multimodal AI Vision Support")
    print("=" * 50)
    
    # Step 1: Register or login
    print("1. Authenticating...")
    try:
        # Try to register
        response = requests.post(f"{api_url}/api/auth/register", json=test_user)
        if response.status_code == 201:
            print("✅ User registered successfully")
            token = response.json()['token']
        else:
            # Try to login if user already exists
            response = requests.post(f"{api_url}/api/auth/login", json={
                "username": test_user["username"],
                "password": test_user["password"]
            })
            if response.status_code == 200:
                print("✅ User logged in successfully")
                token = response.json()['token']
            else:
                print(f"❌ Authentication failed: {response.text}")
                return
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return
    
    # Step 2: Check available models
    print("\n2. Checking available models...")
    try:
        response = requests.get(f"{api_url}/api/models/simple")
        if response.status_code == 200:
            models_data = response.json()
            models = models_data.get('models', [])
            vision_models = models_data.get('vision_models', [])
            
            print(f"✅ Found {len(models)} total models")
            print(f"✅ Found {len(vision_models)} vision models: {vision_models}")
            
            if not vision_models:
                print("⚠️  No vision models available. Please install a vision model like LLaVA:")
                print("   ollama pull llava")
                return
                
            selected_model = vision_models[0]
            print(f"🎯 Using model: {selected_model}")
        else:
            print(f"❌ Failed to get models: {response.text}")
            return
    except Exception as e:
        print(f"❌ Models check error: {e}")
        return
    
    # Step 3: Create a test image (simple colored square)
    print("\n3. Creating test image...")
    try:
        # Create a simple test image using PIL if available
        try:
            from PIL import Image, ImageDraw
            import io
            
            # Create a simple test image
            img = Image.new('RGB', (200, 200), color='red')
            draw = ImageDraw.Draw(img)
            draw.rectangle([50, 50, 150, 150], fill='blue')
            draw.text((75, 175), "TEST", fill='white')
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            image_data_url = f"data:image/png;base64,{image_base64}"
            
            print("✅ Test image created (red background with blue square)")
            
        except ImportError:
            print("⚠️  PIL not available, using a simple base64 placeholder")
            # Use a minimal PNG placeholder
            image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            image_data_url = f"data:image/png;base64,{image_base64}"
            
    except Exception as e:
        print(f"❌ Image creation error: {e}")
        return
    
    # Step 4: Test vision API
    print("\n4. Testing vision API...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "message": "What do you see in this image? Describe it in detail.",
            "model": selected_model,
            "images": [image_data_url]
        }
        
        print(f"📤 Sending image to {selected_model}...")
        response = requests.post(f"{api_url}/api/chat", json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Vision API test successful!")
                print(f"🤖 AI Response: {result['response']}")
                print(f"🔍 Vision used: {result.get('vision_used', False)}")
            else:
                print(f"❌ API returned error: {result.get('error')}")
        else:
            print(f"❌ API request failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Vision API test error: {e}")
        return
    
    print("\n🎉 Vision support test completed!")
    print("\nNext steps:")
    print("1. Install a vision model: ollama pull llava")
    print("2. Start the frontend: cd frontend && npm start")
    print("3. Upload images in the chat interface")

if __name__ == "__main__":
    test_vision_api()