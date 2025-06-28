#!/usr/bin/env python3
"""
Test script for Advanced Interaction Paradigms - Interactive & Visual Outputs
Tests the visualization generation and rendering capabilities
"""

import json
import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_visualization_service():
    """Test the visualization service"""
    print("Testing Visualization Service...")
    
    try:
        from services.visualization_service import visualization_service
        
        # Test data
        test_data = [
            {'category': 'A', 'value': 28, 'region': 'North'},
            {'category': 'B', 'value': 55, 'region': 'South'},
            {'category': 'C', 'value': 43, 'region': 'East'},
            {'category': 'D', 'value': 91, 'region': 'West'}
        ]
        
        # Test bar chart generation
        print("  ✓ Testing bar chart generation...")
        bar_spec = visualization_service.generate_visualization(
            chart_type='bar',
            data=test_data,
            x_field='category',
            y_field='value',
            title='Test Bar Chart'
        )
        
        if bar_spec and bar_spec.spec:
            print("    ✓ Bar chart generated successfully")
            print(f"    ✓ Chart has {len(bar_spec.data)} data points")
        else:
            print("    ✗ Bar chart generation failed")
            return False
        
        # Test line chart generation
        print("  ✓ Testing line chart generation...")
        line_data = [
            {'date': '2023-01', 'value': 100},
            {'date': '2023-02', 'value': 120},
            {'date': '2023-03', 'value': 140},
            {'date': '2023-04', 'value': 110}
        ]
        
        line_spec = visualization_service.generate_visualization(
            chart_type='line',
            data=line_data,
            x_field='date',
            y_field='value',
            title='Test Line Chart'
        )
        
        if line_spec and line_spec.spec:
            print("    ✓ Line chart generated successfully")
        else:
            print("    ✗ Line chart generation failed")
            return False
        
        # Test table generation
        print("  ✓ Testing table generation...")
        table_spec = visualization_service.generate_visualization(
            chart_type='table',
            data=test_data,
            title='Test Table'
        )
        
        if table_spec and table_spec.data:
            print("    ✓ Table generated successfully")
        else:
            print("    ✗ Table generation failed")
            return False
        
        # Test auto-detection
        print("  ✓ Testing chart type auto-detection...")
        auto_spec = visualization_service.generate_visualization(
            chart_type='auto',
            data=test_data,
            x_field='category',
            y_field='value',
            title='Auto-detected Chart'
        )
        
        if auto_spec:
            print("    ✓ Auto-detection working")
        else:
            print("    ✗ Auto-detection failed")
            return False
        
        print("✓ Visualization Service tests passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Visualization service not available: {e}")
        return False
    except Exception as e:
        print(f"✗ Visualization service test failed: {e}")
        return False

def test_agent_service():
    """Test the agent service with visualization tools"""
    print("\nTesting Agent Service with Visualization Tools...")
    
    try:
        from services.agent_service import agent_service
        
        # Check if visualization tool is registered
        available_tools = agent_service.get_available_tools()
        print(f"  ✓ Available tools: {available_tools}")
        
        if 'generate_visualization' in available_tools:
            print("    ✓ Visualization tool is registered")
        else:
            print("    ✗ Visualization tool not found")
            return False
        
        # Test tool description
        tools_desc = agent_service.get_tools_description()
        if 'generate_visualization' in tools_desc:
            print("    ✓ Visualization tool has description")
        else:
            print("    ✗ Visualization tool description missing")
            return False
        
        print("✓ Agent Service tests passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Agent service not available: {e}")
        return False
    except Exception as e:
        print(f"✗ Agent service test failed: {e}")
        return False

def test_database_models():
    """Test database models for visualization support"""
    print("\nTesting Database Models...")
    
    try:
        from models import VisualizationRequest, ChatMessage
        
        # Test VisualizationRequest model
        print("  ✓ Testing VisualizationRequest model...")
        viz_req = VisualizationRequest(
            message_id=1,
            user_id=1,
            visualization_type='bar',
            data=[{'x': 1, 'y': 2}],
            config={'width': 400},
            title='Test Viz',
            description='Test description'
        )
        
        viz_dict = viz_req.to_dict()
        if viz_dict and 'visualization_type' in viz_dict:
            print("    ✓ VisualizationRequest model working")
        else:
            print("    ✗ VisualizationRequest model failed")
            return False
        
        # Test ChatMessage with metadata
        print("  ✓ Testing ChatMessage with metadata...")
        chat_msg = ChatMessage(
            session_id=1,
            user_id=1,
            message_type='bot',
            content='Test message',
            metadata=json.dumps({'has_visualization': True})
        )
        
        msg_dict = chat_msg.to_dict()
        if msg_dict and 'metadata' in msg_dict:
            print("    ✓ ChatMessage metadata support working")
        else:
            print("    ✗ ChatMessage metadata support failed")
            return False
        
        print("✓ Database Models tests passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Database models not available: {e}")
        return False
    except Exception as e:
        print(f"✗ Database models test failed: {e}")
        return False

def test_frontend_components():
    """Test if frontend components exist"""
    print("\nTesting Frontend Components...")
    
    components = [
        'frontend/src/components/VisualizationRenderer.js',
        'frontend/src/components/InteractiveTable.js',
        'frontend/src/components/VisualizationDemo.js'
    ]
    
    all_exist = True
    for component in components:
        if os.path.exists(component):
            print(f"  ✓ {component} exists")
        else:
            print(f"  ✗ {component} missing")
            all_exist = False
    
    # Check package.json for dependencies
    package_json_path = 'frontend/package.json'
    if os.path.exists(package_json_path):
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
            deps = package_data.get('dependencies', {})
            
            required_deps = ['vega', 'vega-lite']
            for dep in required_deps:
                if dep in deps:
                    print(f"  ✓ {dep} dependency found")
                else:
                    print(f"  ✗ {dep} dependency missing")
                    all_exist = False
    else:
        print(f"  ✗ {package_json_path} not found")
        all_exist = False
    
    if all_exist:
        print("✓ Frontend Components tests passed!")
    else:
        print("✗ Some frontend components are missing")
    
    return all_exist

def test_api_endpoints():
    """Test if API endpoints are properly configured"""
    print("\nTesting API Endpoints...")
    
    try:
        # Check if app_minimal.py has the demo endpoint
        with open('app_minimal.py', 'r') as f:
            app_content = f.read()
            
        if '/api/demo/visualization' in app_content:
            print("  ✓ Demo visualization endpoint found")
        else:
            print("  ✗ Demo visualization endpoint missing")
            return False
        
        if 'metadata' in app_content:
            print("  ✓ Metadata support in chat API found")
        else:
            print("  ✗ Metadata support in chat API missing")
            return False
        
        if 'agent_service' in app_content:
            print("  ✓ Agent service integration found")
        else:
            print("  ✗ Agent service integration missing")
            return False
        
        print("✓ API Endpoints tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ API endpoints test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Advanced Interaction Paradigms - Interactive & Visual Outputs")
    print("=" * 70)
    
    tests = [
        test_visualization_service,
        test_agent_service,
        test_database_models,
        test_frontend_components,
        test_api_endpoints
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 70)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Advanced Interaction Paradigms are ready!")
        print("\nNext Steps:")
        print("1. Run: python migrate_minimal_db.py")
        print("2. Install frontend dependencies: cd frontend && npm install")
        print("3. Start the backend: python app_minimal.py")
        print("4. Start the frontend: cd frontend && npm start")
        print("5. Test visualizations with queries like:")
        print("   - 'Show me a bar chart of sales data'")
        print("   - 'Create a comparison table'")
        print("   - 'Generate a line chart showing trends'")
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())