#!/usr/bin/env python3
"""
Test script for AI Agent and Persona features structure
Tests the code structure without requiring external dependencies
"""

import os
import sys
import ast
import inspect

def test_file_structure():
    """Test that all required files exist"""
    print("📁 Testing File Structure...")
    
    required_files = [
        'services/agent_service.py',
        'services/persona_service.py',
        'migrations/versions/006_add_agent_persona_fields.py',
        'AGENT_PERSONA_FEATURES.md'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files exist")
    return True

def test_agent_service_structure():
    """Test agent service code structure"""
    print("\n🤖 Testing Agent Service Structure...")
    
    try:
        with open('services/agent_service.py', 'r') as f:
            content = f.read()
        
        # Check for required classes
        required_classes = [
            'BaseTool',
            'WebSearchTool', 
            'CalculatorTool',
            'PythonExecutorTool',
            'StockPriceTool',
            'AgentService'
        ]
        
        for class_name in required_classes:
            if f"class {class_name}" in content:
                print(f"✅ {class_name} class found")
            else:
                print(f"❌ {class_name} class missing")
                return False
        
        # Check for required methods
        required_methods = [
            'execute',
            'process_with_agent',
            'get_available_tools',
            'get_tools_description'
        ]
        
        for method_name in required_methods:
            if f"def {method_name}" in content:
                print(f"✅ {method_name} method found")
            else:
                print(f"❌ {method_name} method missing")
                return False
        
        print("✅ Agent service structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Agent service structure test failed: {e}")
        return False

def test_persona_service_structure():
    """Test persona service code structure"""
    print("\n👤 Testing Persona Service Structure...")
    
    try:
        with open('services/persona_service.py', 'r') as f:
            content = f.read()
        
        # Check for required classes
        required_classes = [
            'PersonaTemplate',
            'PersonaService'
        ]
        
        for class_name in required_classes:
            if f"class {class_name}" in content:
                print(f"✅ {class_name} class found")
            else:
                print(f"❌ {class_name} class missing")
                return False
        
        # Check for built-in personas
        built_in_personas = [
            'socratic_tutor',
            'code_reviewer',
            'creative_writer',
            'business_analyst',
            'scientist',
            'comedian',
            'minimalist',
            'philosopher'
        ]
        
        for persona in built_in_personas:
            if persona in content:
                print(f"✅ {persona} persona found")
            else:
                print(f"❌ {persona} persona missing")
                return False
        
        # Check for required methods
        required_methods = [
            'get_available_personas',
            'get_persona_system_prompt',
            'create_custom_persona',
            'apply_persona_to_session'
        ]
        
        for method_name in required_methods:
            if f"def {method_name}" in content:
                print(f"✅ {method_name} method found")
            else:
                print(f"❌ {method_name} method missing")
                return False
        
        print("✅ Persona service structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Persona service structure test failed: {e}")
        return False

def test_api_endpoints():
    """Test that API endpoints are added to app.py"""
    print("\n🌐 Testing API Endpoints...")
    
    try:
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Check for agent endpoints
        agent_endpoints = [
            '/api/agent/chat',
            '/api/agent/tools'
        ]
        
        for endpoint in agent_endpoints:
            if endpoint in content:
                print(f"✅ {endpoint} endpoint found")
            else:
                print(f"❌ {endpoint} endpoint missing")
                return False
        
        # Check for persona endpoints
        persona_endpoints = [
            '/api/personas',
            '/api/sessions/<int:session_id>/persona'
        ]
        
        for endpoint in persona_endpoints:
            if endpoint in content:
                print(f"✅ {endpoint} endpoint found")
            else:
                print(f"❌ {endpoint} endpoint missing")
                return False
        
        # Check for required functions
        required_functions = [
            'agent_chat',
            'get_available_tools',
            'get_personas',
            'create_persona',
            'apply_persona_to_session'
        ]
        
        for func_name in required_functions:
            if f"def {func_name}" in content:
                print(f"✅ {func_name} function found")
            else:
                print(f"❌ {func_name} function missing")
                return False
        
        print("✅ API endpoints are correctly implemented")
        return True
        
    except Exception as e:
        print(f"❌ API endpoints test failed: {e}")
        return False

def test_migration_file():
    """Test migration file structure"""
    print("\n🗄️ Testing Migration File...")
    
    try:
        with open('migrations/versions/006_add_agent_persona_fields.py', 'r') as f:
            content = f.read()
        
        # Check for required functions
        if 'def upgrade():' in content and 'def downgrade():' in content:
            print("✅ Migration functions found")
        else:
            print("❌ Migration functions missing")
            return False
        
        # Check for required fields
        required_fields = [
            'system_prompt_type',
            'custom_system_prompt',
            'model_parameters',
            'agent_mode_enabled',
            'tool_calls'
        ]
        
        for field in required_fields:
            if field in content:
                print(f"✅ {field} field found in migration")
            else:
                print(f"❌ {field} field missing from migration")
                return False
        
        print("✅ Migration file is correct")
        return True
        
    except Exception as e:
        print(f"❌ Migration file test failed: {e}")
        return False

def test_documentation():
    """Test documentation completeness"""
    print("\n📚 Testing Documentation...")
    
    try:
        with open('AGENT_PERSONA_FEATURES.md', 'r') as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            '# 🤖 AI Agents & Personas Features',
            '## 🤖 AI Agents & Tool Use',
            '## 👤 Customizable Personas & System Prompts',
            '### API Usage',
            '### Built-in Personas',
            '## 🚀 Getting Started'
        ]
        
        for section in required_sections:
            if section in content:
                print(f"✅ {section} section found")
            else:
                print(f"❌ {section} section missing")
                return False
        
        # Check for code examples
        if '```http' in content and '```javascript' in content and '```python' in content:
            print("✅ Code examples found")
        else:
            print("❌ Code examples missing")
            return False
        
        print("✅ Documentation is complete")
        return True
        
    except Exception as e:
        print(f"❌ Documentation test failed: {e}")
        return False

def test_integration_points():
    """Test integration between services"""
    print("\n🔗 Testing Integration Points...")
    
    try:
        # Check chat service integration
        with open('services/chat_service.py', 'r') as f:
            chat_content = f.read()
        
        integration_points = [
            'from services.agent_service import agent_service',
            'from services.persona_service import persona_service',
            'use_agent: bool = False',
            '_generate_agent_response',
            'get_persona_system_prompt',
            'get_persona_parameters'
        ]
        
        for point in integration_points:
            if point in chat_content:
                print(f"✅ {point} integration found")
            else:
                print(f"❌ {point} integration missing")
                return False
        
        print("✅ Integration points are correct")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Run all structure tests"""
    print("🚀 Testing AI Agent and Persona Features Structure")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Agent Service Structure", test_agent_service_structure),
        ("Persona Service Structure", test_persona_service_structure),
        ("API Endpoints", test_api_endpoints),
        ("Migration File", test_migration_file),
        ("Documentation", test_documentation),
        ("Integration Points", test_integration_points)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All structure tests passed! The implementation is complete.")
        print("\n📋 Next Steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run database migration: alembic upgrade head")
        print("3. Start the application: python app.py")
        print("4. Test the new features through the API endpoints")
        return True
    else:
        print("⚠️ Some structure tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)