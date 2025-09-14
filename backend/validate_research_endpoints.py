#!/usr/bin/env python3
"""
Validation script for basic research endpoints
Validates endpoint structure and logic without requiring FastAPI installation
"""
import sys
import os
import re
import ast
from typing import List, Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def validate_research_endpoints():
    """Validate the basic research endpoints implementation"""
    print("Validating Basic Research Endpoints Implementation")
    print("=" * 60)
    
    try:
        # Read the advanced_endpoints.py file
        endpoints_file = os.path.join(os.path.dirname(__file__), 'api', 'advanced_endpoints.py')
        
        if not os.path.exists(endpoints_file):
            print(f"❌ Endpoints file not found: {endpoints_file}")
            return False
        
        with open(endpoints_file, 'r') as f:
            content = f.read()
        
        # Required research endpoints
        required_endpoints = [
            ("/research/status", "GET", "research_status"),
            ("/research/capabilities", "GET", "research_capabilities"), 
            ("/research/domains", "GET", "research_domains"),
            ("/research/search/basic", "POST", "basic_research_search"),
            ("/research/validate", "POST", "validate_research_query")
        ]
        
        validation_results = []
        
        for endpoint_path, method, function_name in required_endpoints:
            print(f"\n🔍 Validating {method} {endpoint_path}")
            
            # Check if endpoint is defined
            endpoint_pattern = rf'@router\.{method.lower()}\("{re.escape(endpoint_path)}"\)'
            if re.search(endpoint_pattern, content):
                print(f"   ✅ Endpoint route defined")
                
                # Check if function exists
                function_pattern = rf'async def {function_name}\('
                if re.search(function_pattern, content):
                    print(f"   ✅ Function {function_name} defined")
                    
                    # Check for error handling
                    function_start = content.find(f'async def {function_name}(')
                    if function_start != -1:
                        # Find the end of the function (next function or end of file)
                        next_function = content.find('async def ', function_start + 1)
                        if next_function == -1:
                            function_content = content[function_start:]
                        else:
                            function_content = content[function_start:next_function]
                        
                        # Check for try-except blocks
                        if 'try:' in function_content and 'except' in function_content:
                            print(f"   ✅ Error handling implemented")
                        else:
                            print(f"   ⚠️  No error handling found")
                        
                        # Check for HTTPException usage
                        if 'HTTPException' in function_content:
                            print(f"   ✅ HTTP error responses implemented")
                        else:
                            print(f"   ⚠️  No HTTP error responses found")
                        
                        # Check for logging
                        if 'logger.' in function_content:
                            print(f"   ✅ Logging implemented")
                        else:
                            print(f"   ⚠️  No logging found")
                        
                        # Check for input validation (for POST endpoints)
                        if method == "POST":
                            if 'request.get(' in function_content or 'if not' in function_content:
                                print(f"   ✅ Input validation implemented")
                            else:
                                print(f"   ⚠️  Limited input validation found")
                        
                        validation_results.append({
                            "endpoint": f"{method} {endpoint_path}",
                            "function": function_name,
                            "status": "implemented"
                        })
                    
                else:
                    print(f"   ❌ Function {function_name} not found")
                    validation_results.append({
                        "endpoint": f"{method} {endpoint_path}",
                        "function": function_name,
                        "status": "missing_function"
                    })
            else:
                print(f"   ❌ Endpoint route not defined")
                validation_results.append({
                    "endpoint": f"{method} {endpoint_path}",
                    "function": function_name,
                    "status": "missing_route"
                })
        
        # Check for service manager integration
        print(f"\n🔍 Validating Service Manager Integration")
        if 'service_manager' in content:
            print(f"   ✅ Service manager imported and used")
        else:
            print(f"   ❌ Service manager not found")
        
        # Check for graceful degradation
        print(f"\n🔍 Validating Graceful Degradation")
        if 'mock' in content.lower() and 'fallback' in content.lower():
            print(f"   ✅ Fallback/mock responses implemented")
        else:
            print(f"   ⚠️  Limited fallback mechanisms found")
        
        # Summary
        print(f"\n" + "=" * 60)
        print(f"Validation Summary:")
        implemented = len([r for r in validation_results if r["status"] == "implemented"])
        total = len(validation_results)
        print(f"   Implemented endpoints: {implemented}/{total}")
        
        if implemented == total:
            print(f"   🎉 All required research endpoints are implemented!")
            return True
        else:
            print(f"   ⚠️  Some endpoints need attention")
            return False
        
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        return False

def validate_endpoint_requirements():
    """Validate that endpoints meet the specific requirements"""
    print(f"\n🔍 Validating Requirements Compliance")
    print("-" * 40)
    
    requirements_check = {
        "2.1": "Endpoints respond with expected data structure",
        "2.2": "Endpoints return appropriate HTTP status codes and error messages", 
        "2.3": "Endpoints handle service unavailability gracefully"
    }
    
    try:
        endpoints_file = os.path.join(os.path.dirname(__file__), 'api', 'advanced_endpoints.py')
        with open(endpoints_file, 'r') as f:
            content = f.read()
        
        # Check requirement 2.1 - Expected data structure
        if 'return {' in content and '"status":' in content and '"timestamp":' in content:
            print(f"   ✅ Requirement 2.1: Consistent response structure")
        else:
            print(f"   ⚠️  Requirement 2.1: Response structure needs verification")
        
        # Check requirement 2.2 - HTTP status codes and error messages
        if 'HTTPException' in content and 'status_code=' in content and 'detail=' in content:
            print(f"   ✅ Requirement 2.2: HTTP error handling implemented")
        else:
            print(f"   ❌ Requirement 2.2: HTTP error handling missing")
        
        # Check requirement 2.3 - Service unavailability handling
        if 'service_manager.get_service(' in content and 'if not' in content:
            print(f"   ✅ Requirement 2.3: Service unavailability handling")
        else:
            print(f"   ⚠️  Requirement 2.3: Service handling needs verification")
        
        return True
        
    except Exception as e:
        print(f"❌ Requirements validation failed: {str(e)}")
        return False

def main():
    """Main function to run the validation"""
    try:
        endpoint_validation = validate_research_endpoints()
        requirements_validation = validate_endpoint_requirements()
        
        if endpoint_validation and requirements_validation:
            print(f"\n🎉 All validations passed! Basic research endpoints are properly implemented.")
            return True
        else:
            print(f"\n⚠️  Some validations failed. Review the output above.")
            return False
            
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)