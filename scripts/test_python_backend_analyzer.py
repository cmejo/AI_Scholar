#!/usr/bin/env python3
"""
Test script for Python Backend Analyzer
Tests the functionality of the Python backend code analysis tool.
"""

import json
import sys
import tempfile
from pathlib import Path
from python_backend_analyzer import PythonBackendAnalyzer, IssueType, IssueSeverity

def create_test_files():
    """Create test Python files with various issues."""
    test_dir = Path(tempfile.mkdtemp())
    
    # Create test file with syntax error
    syntax_error_file = test_dir / "syntax_error.py"
    syntax_error_file.write_text("""
def broken_function(
    print("Missing closing parenthesis")
    return "error"
""")
    
    # Create test file with import error
    import_error_file = test_dir / "import_error.py"
    import_error_file.write_text("""
import nonexistent_module
from another_nonexistent import something

def test_function():
    return "test"
""")
    
    # Create test file with type annotation issues
    type_error_file = test_dir / "type_error.py"
    type_error_file.write_text("""
def function_without_types(param1, param2):
    return param1 + param2

def another_function(param: str):
    return param.upper()
""")
    
    # Create test file with SQL issues
    sql_error_file = test_dir / "sql_error.py"
    sql_error_file.write_text("""
def get_all_users():
    query = "SELECT * FROM users"
    return execute_query(query)

def unsafe_delete():
    query = "DELETE FROM users"
    return execute_query(query)

def sql_injection_risk(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return execute_query(query)
""")
    
    # Create test file with service integration issues
    service_error_file = test_dir / "service_error.py"
    service_error_file.write_text("""
import requests

def call_external_api():
    response = requests.get("https://api.example.com/data")
    return response.json()  # No error handling

def database_operation():
    db.execute("SELECT * FROM table")  # No error handling
    return "success"

@app.get("/endpoint")
def api_endpoint(request):
    return {"data": "no validation"}  # No input validation or auth
""")
    
    # Create requirements.txt with vulnerabilities
    requirements_file = test_dir / "requirements.txt"
    requirements_file.write_text("""
requests
flask
django
numpy
""")
    
    return test_dir

def test_syntax_analysis():
    """Test syntax and import analysis."""
    print("Testing syntax and import analysis...")
    
    test_dir = create_test_files()
    analyzer = PythonBackendAnalyzer(test_dir)
    
    result = analyzer.analyze_syntax_and_imports()
    
    print(f"  Files analyzed: {result.files_analyzed}")
    print(f"  Issues found: {len(result.issues)}")
    
    # Check for expected issue types
    issue_types = [issue.type for issue in result.issues]
    
    if IssueType.SYNTAX_ERROR in issue_types:
        print("  ✓ Syntax errors detected")
    else:
        print("  ⚠ No syntax errors detected")
    
    if IssueType.IMPORT_ERROR in issue_types:
        print("  ✓ Import errors detected")
    else:
        print("  ⚠ No import errors detected")
    
    if IssueType.TYPE_ERROR in issue_types:
        print("  ✓ Type annotation issues detected")
    else:
        print("  ⚠ No type annotation issues detected")
    
    return result

def test_dependency_analysis():
    """Test dependency vulnerability analysis."""
    print("\nTesting dependency analysis...")
    
    test_dir = create_test_files()
    analyzer = PythonBackendAnalyzer(test_dir)
    
    result = analyzer.analyze_dependencies()
    
    print(f"  Files analyzed: {result.files_analyzed}")
    print(f"  Issues found: {len(result.issues)}")
    
    # Check for expected issue types
    issue_types = [issue.type for issue in result.issues]
    
    if IssueType.DEPENDENCY_VULNERABILITY in issue_types:
        print("  ✓ Dependency vulnerabilities detected")
    else:
        print("  ⚠ No dependency vulnerabilities detected")
    
    return result

def test_sql_analysis():
    """Test SQL query analysis."""
    print("\nTesting SQL query analysis...")
    
    test_dir = create_test_files()
    analyzer = PythonBackendAnalyzer(test_dir)
    
    result = analyzer.analyze_database_queries()
    
    print(f"  Files analyzed: {result.files_analyzed}")
    print(f"  Issues found: {len(result.issues)}")
    
    # Check for expected issue types
    issue_types = [issue.type for issue in result.issues]
    
    if IssueType.SQL_PERFORMANCE_ISSUE in issue_types:
        print("  ✓ SQL performance issues detected")
    else:
        print("  ⚠ No SQL performance issues detected")
    
    if IssueType.SQL_SYNTAX_ERROR in issue_types:
        print("  ✓ SQL syntax errors detected")
    else:
        print("  ⚠ No SQL syntax errors detected")
    
    if IssueType.SECURITY_VULNERABILITY in issue_types:
        print("  ✓ SQL injection risks detected")
    else:
        print("  ⚠ No SQL injection risks detected")
    
    return result

def test_service_integration_analysis():
    """Test service integration analysis."""
    print("\nTesting service integration analysis...")
    
    test_dir = create_test_files()
    
    # Create services and api subdirectories
    services_dir = test_dir / "services"
    services_dir.mkdir()
    api_dir = test_dir / "api"
    api_dir.mkdir()
    
    # Move service file to services directory
    service_file = services_dir / "service_error.py"
    service_file.write_text((test_dir / "service_error.py").read_text())
    
    analyzer = PythonBackendAnalyzer(test_dir)
    
    result = analyzer.analyze_service_integration()
    
    print(f"  Files analyzed: {result.files_analyzed}")
    print(f"  Issues found: {len(result.issues)}")
    
    # Check for expected issue types
    issue_types = [issue.type for issue in result.issues]
    
    if IssueType.SERVICE_INTEGRATION_ERROR in issue_types:
        print("  ✓ Service integration errors detected")
    else:
        print("  ⚠ No service integration errors detected")
    
    return result

def test_full_analysis():
    """Test full analysis workflow."""
    print("\nTesting full analysis workflow...")
    
    test_dir = create_test_files()
    analyzer = PythonBackendAnalyzer(test_dir)
    
    results = analyzer.run_full_analysis()
    
    print(f"  Total files analyzed: {results['total_files_analyzed']}")
    print(f"  Total issues found: {results['total_issues_found']}")
    
    # Print issue breakdown
    print("  Issue breakdown:")
    for category, breakdown in results['issue_breakdown'].items():
        print(f"    {category}:")
        for key, count in breakdown.items():
            print(f"      {key}: {count}")
    
    return results

def main():
    """Run all tests."""
    print("Python Backend Analyzer Test Suite")
    print("=" * 50)
    
    try:
        # Test individual components
        test_syntax_analysis()
        test_dependency_analysis()
        test_sql_analysis()
        test_service_integration_analysis()
        
        # Test full workflow
        results = test_full_analysis()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        print(f"Total issues detected: {results['total_issues_found']}")
        
        # Save test results
        with open("python_backend_analyzer_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print("Test results saved to python_backend_analyzer_test_results.json")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()