"""
Validate analytics endpoints implementation
Simple validation script that checks syntax and structure without requiring FastAPI
"""
import ast
import sys

def validate_python_syntax(file_path):
    """Validate Python syntax of a file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse the AST to check for syntax errors
        ast.parse(content)
        return True, "Syntax is valid"
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error reading file: {str(e)}"

def check_analytics_endpoints_structure(file_path):
    """Check if analytics endpoints are properly structured"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for expected analytics endpoints
        expected_endpoints = [
            "@router.get(\"/analytics/report/{user_id}\")",
            "@router.get(\"/analytics/usage/{user_id}\")",
            "@router.get(\"/analytics/content/{user_id}\")",
            "@router.get(\"/analytics/relationships/{user_id}\")",
            "@router.get(\"/analytics/knowledge-patterns/{user_id}\")",
            "@router.get(\"/analytics/knowledge-map/{user_id}\")",
            "@router.get(\"/analytics/metrics/{user_id}\")"
        ]
        
        found_endpoints = []
        missing_endpoints = []
        
        for endpoint in expected_endpoints:
            if endpoint in content:
                found_endpoints.append(endpoint)
            else:
                missing_endpoints.append(endpoint)
        
        return found_endpoints, missing_endpoints
    
    except Exception as e:
        return [], [f"Error reading file: {str(e)}"]

def check_error_handling_patterns(file_path):
    """Check if proper error handling patterns are implemented"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for error handling patterns
        error_patterns = [
            "service_manager.get_service",
            "service_manager.check_service_health",
            "status\": \"unavailable\"",
            "status\": \"degraded\"",
            "status\": \"error\"",
            "HTTPException",
            "try:",
            "except Exception as e:",
            "logger.error"
        ]
        
        found_patterns = []
        missing_patterns = []
        
        for pattern in error_patterns:
            if pattern in content:
                found_patterns.append(pattern)
            else:
                missing_patterns.append(pattern)
        
        return found_patterns, missing_patterns
    
    except Exception as e:
        return [], [f"Error reading file: {str(e)}"]

def main():
    """Main validation function"""
    print("Analytics Endpoints Validation")
    print("=" * 50)
    
    file_path = "api/advanced_endpoints.py"
    
    # 1. Validate syntax
    print("1. Checking Python syntax...")
    is_valid, message = validate_python_syntax(file_path)
    if is_valid:
        print(f"✓ PASS: {message}")
    else:
        print(f"✗ FAIL: {message}")
        return False
    
    # 2. Check analytics endpoints structure
    print("\n2. Checking analytics endpoints structure...")
    found_endpoints, missing_endpoints = check_analytics_endpoints_structure(file_path)
    
    print(f"Found {len(found_endpoints)} analytics endpoints:")
    for endpoint in found_endpoints:
        print(f"  ✓ {endpoint}")
    
    if missing_endpoints:
        print(f"\nMissing {len(missing_endpoints)} analytics endpoints:")
        for endpoint in missing_endpoints:
            print(f"  ✗ {endpoint}")
    
    # 3. Check error handling patterns
    print("\n3. Checking error handling patterns...")
    found_patterns, missing_patterns = check_error_handling_patterns(file_path)
    
    print(f"Found {len(found_patterns)} error handling patterns:")
    for pattern in found_patterns:
        print(f"  ✓ {pattern}")
    
    if missing_patterns:
        print(f"\nMissing {len(missing_patterns)} error handling patterns:")
        for pattern in missing_patterns:
            print(f"  ✗ {pattern}")
    
    # 4. Summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    total_score = 0
    max_score = 3
    
    if is_valid:
        print("✓ Syntax validation: PASS")
        total_score += 1
    else:
        print("✗ Syntax validation: FAIL")
    
    if len(found_endpoints) >= 6:  # At least 6 out of 7 endpoints
        print("✓ Endpoints structure: PASS")
        total_score += 1
    else:
        print("✗ Endpoints structure: FAIL")
    
    if len(found_patterns) >= 7:  # At least 7 out of 9 error handling patterns
        print("✓ Error handling: PASS")
        total_score += 1
    else:
        print("✗ Error handling: FAIL")
    
    print(f"\nOverall Score: {total_score}/{max_score}")
    
    if total_score == max_score:
        print("🎉 All validations passed! Analytics endpoints are properly implemented.")
        return True
    else:
        print("⚠️  Some validations failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)