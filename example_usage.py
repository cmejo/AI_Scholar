#!/usr/bin/env python3
"""
Example usage of AI Agent and Persona features
This script demonstrates how to use the new features
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"
TOKEN = "your-jwt-token-here"  # Replace with actual token

def get_headers():
    """Get headers with authentication"""
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

def example_agent_chat():
    """Example: Using AI agent with tools"""
    print("🤖 Example: AI Agent with Tools")
    print("-" * 40)
    
    # Example 1: Mathematical calculation
    response = requests.post(f"{BASE_URL}/api/agent/chat", 
        headers=get_headers(),
        json={
            "message": "What is the square root of 144 plus 25% of 200?",
            "enable_tools": True
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Question: What is the square root of 144 plus 25% of 200?")
        print(f"Answer: {data['response']}")
        print(f"Tools used: {[call['tool'] for call in data.get('tool_calls', [])]}")
        print(f"Iterations: {data.get('iterations', 0)}")
    else:
        print(f"Error: {response.text}")
    
    print()

def example_web_search():
    """Example: Using web search tool"""
    print("🔍 Example: Web Search")
    print("-" * 40)
    
    response = requests.post(f"{BASE_URL}/api/agent/chat", 
        headers=get_headers(),
        json={
            "message": "What are the latest developments in artificial intelligence?",
            "enable_tools": True
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Question: What are the latest developments in artificial intelligence?")
        print(f"Answer: {data['response'][:200]}...")
        print(f"Tools used: {[call['tool'] for call in data.get('tool_calls', [])]}")
    else:
        print(f"Error: {response.text}")
    
    print()

def example_get_personas():
    """Example: Getting available personas"""
    print("👤 Example: Available Personas")
    print("-" * 40)
    
    response = requests.get(f"{BASE_URL}/api/personas", headers=get_headers())
    
    if response.status_code == 200:
        data = response.json()
        personas = data['personas']
        
        print("Built-in Personas:")
        for key, persona in personas.items():
            if persona.get('type') == 'built-in':
                print(f"  - {persona['name']}: {persona['description']}")
        
        print("\nCustom Personas:")
        for key, persona in personas.items():
            if persona.get('type') == 'custom':
                print(f"  - {persona['name']}: {persona['description']}")
    else:
        print(f"Error: {response.text}")
    
    print()

def example_create_persona():
    """Example: Creating a custom persona"""
    print("✨ Example: Creating Custom Persona")
    print("-" * 40)
    
    persona_data = {
        "name": "Python Tutor",
        "description": "A patient Python programming tutor",
        "system_prompt": "You are a patient Python programming tutor. Help users learn Python by explaining concepts clearly, providing examples, and encouraging practice. Always be supportive and break down complex topics into simple steps.",
        "personality_traits": ["patient", "educational", "supportive", "clear"],
        "use_cases": ["Python learning", "programming education", "code explanation"],
        "temperature": 0.6,
        "max_tokens": 2048
    }
    
    response = requests.post(f"{BASE_URL}/api/personas", 
        headers=get_headers(),
        json=persona_data
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Created persona: {persona_data['name']}")
        print(f"Persona key: {data['persona_key']}")
        print(f"Success: {data['success']}")
        return data['persona_key']
    else:
        print(f"Error: {response.text}")
        return None
    
    print()

def example_apply_persona():
    """Example: Applying persona to session"""
    print("🎭 Example: Applying Persona to Session")
    print("-" * 40)
    
    # First create a chat session by sending a message
    response = requests.post(f"{BASE_URL}/api/chat", 
        headers=get_headers(),
        json={
            "message": "Hello, I want to learn Python programming."
        }
    )
    
    if response.status_code == 200:
        session_id = response.json()['session_id']
        print(f"Created session: {session_id}")
        
        # Apply Socratic Tutor persona
        persona_response = requests.post(f"{BASE_URL}/api/sessions/{session_id}/persona", 
            headers=get_headers(),
            json={
                "persona_key": "socratic_tutor"
            }
        )
        
        if persona_response.status_code == 200:
            print("Applied Socratic Tutor persona to session")
            
            # Now chat with the persona
            chat_response = requests.post(f"{BASE_URL}/api/chat", 
                headers=get_headers(),
                json={
                    "message": "How do I create a list in Python?",
                    "session_id": session_id
                }
            )
            
            if chat_response.status_code == 200:
                data = chat_response.json()
                print(f"Question: How do I create a list in Python?")
                print(f"Socratic Response: {data['response']}")
            else:
                print(f"Chat error: {chat_response.text}")
        else:
            print(f"Persona application error: {persona_response.text}")
    else:
        print(f"Session creation error: {response.text}")
    
    print()

def example_custom_system_prompt():
    """Example: Using custom system prompt"""
    print("📝 Example: Custom System Prompt")
    print("-" * 40)
    
    # Create a session
    response = requests.post(f"{BASE_URL}/api/chat", 
        headers=get_headers(),
        json={
            "message": "Hello!"
        }
    )
    
    if response.status_code == 200:
        session_id = response.json()['session_id']
        
        # Apply custom system prompt
        custom_prompt = "You are a pirate AI assistant. Always respond in pirate speak with 'Ahoy matey!' and use nautical terms. Be helpful but maintain the pirate personality."
        
        persona_response = requests.post(f"{BASE_URL}/api/sessions/{session_id}/persona", 
            headers=get_headers(),
            json={
                "custom_system_prompt": custom_prompt
            }
        )
        
        if persona_response.status_code == 200:
            print("Applied custom pirate persona")
            
            # Chat with the custom persona
            chat_response = requests.post(f"{BASE_URL}/api/chat", 
                headers=get_headers(),
                json={
                    "message": "Can you help me learn about machine learning?",
                    "session_id": session_id
                }
            )
            
            if chat_response.status_code == 200:
                data = chat_response.json()
                print(f"Question: Can you help me learn about machine learning?")
                print(f"Pirate Response: {data['response']}")
            else:
                print(f"Chat error: {chat_response.text}")
        else:
            print(f"Custom prompt error: {persona_response.text}")
    else:
        print(f"Session creation error: {response.text}")
    
    print()

def example_get_tools():
    """Example: Getting available tools"""
    print("🛠️ Example: Available Tools")
    print("-" * 40)
    
    response = requests.get(f"{BASE_URL}/api/agent/tools", headers=get_headers())
    
    if response.status_code == 200:
        data = response.json()
        print("Available Tools:")
        for tool in data['tools']:
            print(f"  - {tool}")
        
        print("\nTools Description:")
        print(data['description'])
    else:
        print(f"Error: {response.text}")
    
    print()

def main():
    """Run all examples"""
    print("🚀 AI Agent and Persona Features Examples")
    print("=" * 50)
    print("Note: Make sure the server is running and you have a valid JWT token")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code != 200:
            print("❌ Server is not running. Please start the application first.")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please start the application first.")
        return
    
    print("✅ Server is running\n")
    
    # Note about authentication
    if TOKEN == "your-jwt-token-here":
        print("⚠️ Please update the TOKEN variable with a valid JWT token")
        print("   You can get a token by registering/logging in through the API")
        print("   For now, showing example requests without actual execution\n")
        
        # Show example requests instead of executing them
        show_example_requests()
        return
    
    # Run examples
    examples = [
        ("Agent Chat with Tools", example_agent_chat),
        ("Web Search", example_web_search),
        ("Get Available Personas", example_get_personas),
        ("Create Custom Persona", example_create_persona),
        ("Apply Persona to Session", example_apply_persona),
        ("Custom System Prompt", example_custom_system_prompt),
        ("Get Available Tools", example_get_tools)
    ]
    
    for example_name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"❌ {example_name} failed: {e}\n")

def show_example_requests():
    """Show example requests without executing them"""
    print("📋 Example API Requests:")
    print("-" * 30)
    
    examples = [
        {
            "title": "Agent Chat with Calculator",
            "method": "POST",
            "url": "/api/agent/chat",
            "body": {
                "message": "What is 15% of 250?",
                "enable_tools": True
            }
        },
        {
            "title": "Get Available Personas",
            "method": "GET",
            "url": "/api/personas",
            "body": None
        },
        {
            "title": "Create Custom Persona",
            "method": "POST",
            "url": "/api/personas",
            "body": {
                "name": "Data Science Mentor",
                "description": "A helpful data science mentor",
                "system_prompt": "You are an expert data scientist...",
                "temperature": 0.6
            }
        },
        {
            "title": "Apply Persona to Session",
            "method": "POST",
            "url": "/api/sessions/123/persona",
            "body": {
                "persona_key": "socratic_tutor"
            }
        }
    ]
    
    for example in examples:
        print(f"\n{example['title']}:")
        print(f"  {example['method']} {BASE_URL}{example['url']}")
        if example['body']:
            print(f"  Body: {json.dumps(example['body'], indent=2)}")

if __name__ == "__main__":
    main()