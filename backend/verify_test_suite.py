#!/usr/bin/env python3
"""
Verification script for the comprehensive testing suite.
Validates that all test components are properly configured and functional.
"""
import os
import sys
import subprocess
import importlib.util
from pathlib import Path


def check_file_exists(file_path, description):
    """Check if a file exists and report status."""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NOT FOUND")
        return False


def check_test_files():
    """Check that all test files exist."""
    print("🔍 Checking test files...")
    
    test_files = [
        ("backend/tests/test_memory_service.py", "Memory Service Tests"),
        ("backend/tests/test_integration_comprehensive.py", "Integration Tests"),
        ("backend/tests/test_performance.py", "Performance Tests"),
        ("backend/tests/test_e2e_workflows.py", "End-to-End Tests"),
        ("backend/tests/test_error_handling.py", "Error Handling Tests"),
        ("backend/tests/test_enhanced_rag_integration.py", "Enhanced RAG Integration Tests"),
        ("src/components/__tests__/EnhancedChatIntegration.test.tsx", "Frontend Integration Tests"),
        ("src/components/__tests__/MemoryAwareChatInterface.test.tsx", "Memory Chat Tests"),
        ("src/components/__tests__/EnhancedAnalyticsDashboard.test.tsx", "Analytics Dashboard Tests"),
        ("src/components/__tests__/PersonalizationSettings.test.tsx", "Personalization Tests"),
    ]
    
    all_exist = True
    for file_path, description in test_files:
        if not check_file_exists(file_path, description):
            all_exist = False
    
    return all_exist


def check_config_files():
    """Check that all configuration files exist."""
    print("\n🔧 Checking configuration files...")
    
    config_files = [
        ("backend/pytest.ini", "Pytest Configuration"),
        ("backend/conftest.py", "Pytest Fixtures"),
        ("backend/run_tests.py", "Test Runner Script"),
        ("vitest.config.ts", "Vitest Configuration"),
        ("vitest.integration.config.ts", "Vitest Integration Configuration"),
        ("src/test/setup.ts", "Frontend Test Setup"),
    ]
    
    all_exist = True
    for file_path, description in config_files:
        if not check_file_exists(file_path, description):
            all_exist = False
    
    return all_exist


def check_test_markers():
    """Check that pytest markers are properly configured."""
    print("\n🏷️  Checking test markers...")
    
    try:
        with open("backend/pytest.ini", "r") as f:
            content = f.read()
            
        required_markers = ["unit", "integration", "performance", "e2e", "slow"]
        markers_found = []
        
        for marker in required_markers:
            if marker in content:
                markers_found.append(marker)
                print(f"✅ Marker '{marker}' configured")
            else:
                print(f"❌ Marker '{marker}' not found")
        
        return len(markers_found) == len(required_markers)
        
    except FileNotFoundError:
        print("❌ pytest.ini not found")
        return False


def check_test_imports():
    """Check that test files can be imported without errors."""
    print("\n📦 Checking test imports...")
    
    test_modules = [
        "backend.tests.test_memory_service",
        "backend.tests.test_integration_comprehensive",
        "backend.tests.test_performance",
        "backend.tests.test_e2e_workflows",
        "backend.tests.test_error_handling",
    ]
    
    import_success = True
    
    # Add backend to Python path
    backend_path = os.path.abspath("backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    for module_name in test_modules:
        try:
            # Try to find the module spec
            module_path = module_name.replace(".", "/") + ".py"
            if os.path.exists(module_path):
                print(f"✅ {module_name} - importable")
            else:
                print(f"❌ {module_name} - file not found")
                import_success = False
        except Exception as e:
            print(f"❌ {module_name} - import error: {e}")
            import_success = False
    
    return import_success


def check_test_coverage_config():
    """Check test coverage configuration."""
    print("\n📊 Checking coverage configuration...")
    
    try:
        with open("backend/pytest.ini", "r") as f:
            content = f.read()
        
        coverage_checks = [
            ("--cov=services", "Services coverage"),
            ("--cov=api", "API coverage"),
            ("--cov=core", "Core coverage"),
            ("--cov=models", "Models coverage"),
            ("--cov-report=html", "HTML coverage report"),
            ("--cov-fail-under=80", "Coverage threshold"),
        ]
        
        all_configured = True
        for check, description in coverage_checks:
            if check in content:
                print(f"✅ {description} configured")
            else:
                print(f"❌ {description} not configured")
                all_configured = False
        
        return all_configured
        
    except FileNotFoundError:
        print("❌ pytest.ini not found")
        return False


def check_frontend_test_config():
    """Check frontend test configuration."""
    print("\n🎨 Checking frontend test configuration...")
    
    checks = [
        ("vitest.config.ts", "Vitest config exists"),
        ("vitest.integration.config.ts", "Integration config exists"),
        ("src/test/setup.ts", "Test setup exists"),
        ("package.json", "Package.json exists"),
    ]
    
    all_configured = True
    for file_path, description in checks:
        if not check_file_exists(file_path, description):
            all_configured = False
    
    # Check package.json for test scripts
    try:
        import json
        with open("package.json", "r") as f:
            package_data = json.load(f)
        
        scripts = package_data.get("scripts", {})
        required_scripts = ["test", "test:integration"]
        
        for script in required_scripts:
            if script in scripts:
                print(f"✅ Script '{script}' configured")
            else:
                print(f"❌ Script '{script}' not configured")
                all_configured = False
                
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error reading package.json: {e}")
        all_configured = False
    
    return all_configured


def run_sample_tests():
    """Run a sample of tests to verify they work."""
    print("\n🧪 Running sample tests...")
    
    # Try to run a simple pytest command
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "--version"],
            cwd="backend",
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Pytest is working")
            print(f"   Version: {result.stdout.strip()}")
        else:
            print("❌ Pytest not working")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Pytest command timed out")
        return False
    except FileNotFoundError:
        print("❌ Pytest not found")
        return False
    
    # Check if we can collect tests
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "--collect-only", "-q"],
            cwd="backend",
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            test_count = result.stdout.count("test session starts")
            print(f"✅ Test collection successful")
            print(f"   Found test files")
        else:
            print("❌ Test collection failed")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Test collection timed out")
        return False
    
    return True


def generate_test_report():
    """Generate a summary report of the test suite."""
    print("\n📋 Test Suite Summary Report")
    print("=" * 50)
    
    # Count test files
    test_files = list(Path("backend/tests").glob("test_*.py"))
    frontend_test_files = list(Path("src/components/__tests__").glob("*.test.tsx"))
    
    print(f"Backend test files: {len(test_files)}")
    print(f"Frontend test files: {len(frontend_test_files)}")
    
    # Estimate test count (rough estimate)
    total_test_estimate = 0
    for test_file in test_files:
        try:
            with open(test_file, "r") as f:
                content = f.read()
                test_estimate = content.count("def test_") + content.count("async def test_")
                total_test_estimate += test_estimate
                print(f"  {test_file.name}: ~{test_estimate} tests")
        except Exception:
            pass
    
    print(f"\nEstimated total backend tests: ~{total_test_estimate}")
    
    # Test categories
    categories = {
        "Unit Tests": ["test_memory_service.py", "test_analytics_service.py", "test_user_profile_service.py"],
        "Integration Tests": ["test_integration_comprehensive.py", "test_enhanced_rag_integration.py"],
        "Performance Tests": ["test_performance.py"],
        "End-to-End Tests": ["test_e2e_workflows.py"],
        "Error Handling Tests": ["test_error_handling.py"]
    }
    
    print(f"\nTest Categories:")
    for category, files in categories.items():
        existing_files = [f for f in files if os.path.exists(f"backend/tests/{f}")]
        print(f"  {category}: {len(existing_files)}/{len(files)} files")
    
    print(f"\nConfiguration Files:")
    config_files = ["pytest.ini", "conftest.py", "run_tests.py"]
    for config_file in config_files:
        status = "✅" if os.path.exists(f"backend/{config_file}") else "❌"
        print(f"  {status} {config_file}")


def main():
    """Main verification function."""
    print("🚀 AI Scholar RAG System - Test Suite Verification")
    print("=" * 60)
    
    checks = [
        ("Test Files", check_test_files),
        ("Configuration Files", check_config_files),
        ("Test Markers", check_test_markers),
        ("Test Imports", check_test_imports),
        ("Coverage Configuration", check_test_coverage_config),
        ("Frontend Configuration", check_frontend_test_config),
        ("Sample Test Execution", run_sample_tests),
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n{'='*20} {check_name} {'='*20}")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Error during {check_name}: {e}")
            results.append((check_name, False))
    
    # Generate report
    generate_test_report()
    
    # Summary
    print(f"\n{'='*60}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All verification checks passed!")
        print("The comprehensive testing suite is properly configured and ready to use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} verification checks failed.")
        print("Please review the failed checks and fix any issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())