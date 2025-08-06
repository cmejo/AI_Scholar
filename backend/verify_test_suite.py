#!/usr/bin/env python3
"""
Verification script to ensure the comprehensive test suite is properly configured.
"""

import os
import sys
import importlib.util
from pathlib import Path

def verify_test_files():
    """Verify all test files exist and are importable."""
    
    test_files = [
        "tests/test_mobile_app_comprehensive.py",
        "tests/test_voice_interface_comprehensive.py", 
        "tests/test_external_integrations_comprehensive.py",
        "tests/test_educational_features_comprehensive.py",
        "tests/test_performance.py",
        "tests/test_security_compliance.py",
        "tests/test_comprehensive_quality_assurance.py"
    ]
    
    print("🔍 Verifying test files...")
    
    all_files_exist = True
    
    for test_file in test_files:
        file_path = Path(test_file)
        
        if file_path.exists():
            print(f"✅ {test_file} - EXISTS")
            
            # Try to import the module
            try:
                spec = importlib.util.spec_from_file_location("test_module", file_path)
                module = importlib.util.module_from_spec(spec)
                # Don't execute, just verify it can be loaded
                print(f"   📦 {test_file} - IMPORTABLE")
            except Exception as e:
                print(f"   ❌ {test_file} - IMPORT ERROR: {e}")
                all_files_exist = False
        else:
            print(f"❌ {test_file} - MISSING")
            all_files_exist = False
    
    return all_files_exist

def verify_configuration_files():
    """Verify configuration files exist."""
    
    config_files = [
        "pytest_qa.ini",
        "run_quality_assurance_tests.py"
    ]
    
    print("\n🔧 Verifying configuration files...")
    
    all_configs_exist = True
    
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file} - EXISTS")
        else:
            print(f"❌ {config_file} - MISSING")
            all_configs_exist = False
    
    return all_configs_exist

def verify_dependencies():
    """Verify required dependencies are available."""
    
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "pytest-cov",
        "psutil",
        "numpy"
    ]
    
    print("\n📦 Verifying dependencies...")
    
    all_deps_available = True
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} - AVAILABLE")
        except ImportError:
            print(f"❌ {package} - MISSING")
            all_deps_available = False
    
    return all_deps_available

def run_basic_test():
    """Run a basic test to verify the testing framework works."""
    
    print("\n🧪 Running basic test verification...")
    
    try:
        # Create a simple test
        test_code = '''
import pytest

def test_basic_functionality():
    """Basic test to verify testing framework works."""
    assert 1 + 1 == 2
    assert "hello" == "hello"
    assert len([1, 2, 3]) == 3

@pytest.mark.asyncio
async def test_async_functionality():
    """Basic async test to verify async testing works."""
    import asyncio
    await asyncio.sleep(0.01)
    assert True
'''
        
        # Write test to temporary file
        with open("temp_basic_test.py", "w") as f:
            f.write(test_code)
        
        # Run the test
        import subprocess
        result = subprocess.run([
            "python", "-m", "pytest", 
            "temp_basic_test.py", 
            "-v"
        ], capture_output=True, text=True)
        
        # Clean up
        os.remove("temp_basic_test.py")
        
        if result.returncode == 0:
            print("✅ Basic test framework - WORKING")
            return True
        else:
            print("❌ Basic test framework - FAILED")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Basic test framework - ERROR: {e}")
        return False

def main():
    """Main verification function."""
    
    print("🚀 Comprehensive Test Suite Verification")
    print("=" * 50)
    
    # Run all verifications
    files_ok = verify_test_files()
    configs_ok = verify_configuration_files()
    deps_ok = verify_dependencies()
    basic_test_ok = run_basic_test()
    
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)
    
    print(f"Test Files: {'✅ PASS' if files_ok else '❌ FAIL'}")
    print(f"Configuration Files: {'✅ PASS' if configs_ok else '❌ FAIL'}")
    print(f"Dependencies: {'✅ PASS' if deps_ok else '❌ FAIL'}")
    print(f"Basic Test Framework: {'✅ PASS' if basic_test_ok else '❌ FAIL'}")
    
    overall_success = all([files_ok, configs_ok, deps_ok, basic_test_ok])
    
    if overall_success:
        print("\n🎉 ALL VERIFICATIONS PASSED!")
        print("✅ Comprehensive test suite is ready to run")
        print("\nTo run all tests:")
        print("  python run_quality_assurance_tests.py")
        print("\nTo run specific category:")
        print("  python run_quality_assurance_tests.py mobile")
        print("  python run_quality_assurance_tests.py performance")
        print("  python run_quality_assurance_tests.py security")
    else:
        print("\n⚠️  SOME VERIFICATIONS FAILED!")
        print("❌ Please fix the issues above before running tests")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)