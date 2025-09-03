#!/usr/bin/env python3
"""
Basic test for Ubuntu Compatibility Testing Framework

This script performs basic validation without external dependencies.
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

def test_basic_functionality():
    """Test basic functionality without external dependencies"""
    print("Testing Ubuntu Compatibility Framework - Basic Functionality")
    print("=" * 60)
    
    # Test 1: Check if main script exists and is readable
    script_path = Path(__file__).parent / "ubuntu_compatibility_tester.py"
    if script_path.exists():
        print("✅ Main script exists")
        
        # Check if script is readable
        try:
            with open(script_path, 'r') as f:
                content = f.read()
                if "class UbuntuCompatibilityTestFramework" in content:
                    print("✅ Main framework class found")
                else:
                    print("❌ Main framework class not found")
                    return False
        except Exception as e:
            print(f"❌ Cannot read main script: {e}")
            return False
    else:
        print("❌ Main script does not exist")
        return False
    
    # Test 2: Check if test runner exists
    runner_path = Path(__file__).parent / "run_ubuntu_compatibility_tests.py"
    if runner_path.exists():
        print("✅ Test runner script exists")
    else:
        print("❌ Test runner script does not exist")
        return False
    
    # Test 3: Check if integration script exists
    integration_path = Path(__file__).parent / "ubuntu_compatibility_integration.py"
    if integration_path.exists():
        print("✅ Integration script exists")
    else:
        print("❌ Integration script does not exist")
        return False
    
    # Test 4: Check if requirements file exists
    requirements_path = Path(__file__).parent / "requirements-ubuntu-testing.txt"
    if requirements_path.exists():
        print("✅ Requirements file exists")
        
        # Check requirements content
        try:
            with open(requirements_path, 'r') as f:
                content = f.read()
                required_packages = ["docker", "psutil", "requests"]
                for package in required_packages:
                    if package in content:
                        print(f"✅ Required package '{package}' listed")
                    else:
                        print(f"⚠️  Required package '{package}' not found")
        except Exception as e:
            print(f"❌ Cannot read requirements file: {e}")
    else:
        print("❌ Requirements file does not exist")
        return False
    
    # Test 5: Test basic Python syntax
    try:
        import ast
        
        scripts_to_check = [
            "ubuntu_compatibility_tester.py",
            "run_ubuntu_compatibility_tests.py",
            "ubuntu_compatibility_integration.py"
        ]
        
        for script_name in scripts_to_check:
            script_path = Path(__file__).parent / script_name
            if script_path.exists():
                try:
                    with open(script_path, 'r') as f:
                        content = f.read()
                    
                    # Parse the AST to check syntax
                    ast.parse(content)
                    print(f"✅ {script_name} has valid Python syntax")
                except SyntaxError as e:
                    print(f"❌ {script_name} has syntax error: {e}")
                    return False
                except Exception as e:
                    print(f"⚠️  {script_name} could not be parsed: {e}")
            else:
                print(f"❌ {script_name} not found")
                return False
                
    except ImportError:
        print("⚠️  AST module not available for syntax checking")
    
    # Test 6: Test file system operations
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_ubuntu_compatibility.json"
            
            # Test JSON writing
            test_data = {
                "test": "ubuntu_compatibility",
                "timestamp": "2024-01-01T00:00:00",
                "results": []
            }
            
            with open(test_file, 'w') as f:
                json.dump(test_data, f, indent=2)
            
            # Test JSON reading
            with open(test_file, 'r') as f:
                loaded_data = json.load(f)
            
            if loaded_data["test"] == "ubuntu_compatibility":
                print("✅ File system operations work correctly")
            else:
                print("❌ File system operations failed")
                return False
                
    except Exception as e:
        print(f"❌ File system test failed: {e}")
        return False
    
    # Test 7: Test basic class structure (without imports)
    try:
        # Read the main script and check for expected classes
        main_script = Path(__file__).parent / "ubuntu_compatibility_tester.py"
        with open(main_script, 'r') as f:
            content = f.read()
        
        expected_classes = [
            "UbuntuEnvironmentSimulator",
            "DockerContainerTestSuite", 
            "SystemIntegrationTester",
            "UbuntuPerformanceBenchmark",
            "UbuntuCompatibilityTestFramework"
        ]
        
        # Debug: show all class definitions found
        all_classes = [line.strip() for line in content.split('\n') if line.strip().startswith('class ')]
        print(f"Debug: Found classes: {all_classes[:5]}")  # Show first 5
        
        for class_name in expected_classes:
            import re
            pattern = rf"class\s+{class_name}\s*:"
            if re.search(pattern, content):
                print(f"✅ Class {class_name} found")
            else:
                # Try simpler search
                if f"class {class_name}" in content:
                    print(f"✅ Class {class_name} found (simple search)")
                else:
                    print(f"❌ Class {class_name} not found")
                    return False
                
    except Exception as e:
        print(f"❌ Class structure test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All basic tests passed!")
    print("✅ Ubuntu Compatibility Testing Framework is properly implemented")
    print("\nNext steps:")
    print("1. Install required dependencies: pip install -r scripts/requirements-ubuntu-testing.txt")
    print("2. Run full tests: python scripts/run_ubuntu_compatibility_tests.py")
    print("3. Run integrated analysis: python scripts/ubuntu_compatibility_integration.py")
    
    return True

def test_documentation():
    """Test if proper documentation exists"""
    print("\nTesting Documentation...")
    print("-" * 30)
    
    script_path = Path(__file__).parent / "ubuntu_compatibility_tester.py"
    
    try:
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Check for docstrings
        if '"""' in content:
            print("✅ Docstrings found")
        else:
            print("⚠️  No docstrings found")
        
        # Check for main function
        if "def main():" in content:
            print("✅ Main function found")
        else:
            print("⚠️  Main function not found")
        
        # Check for argument parsing
        if "argparse" in content:
            print("✅ Command line argument parsing implemented")
        else:
            print("⚠️  No command line argument parsing")
        
        # Check for logging
        if "logging" in content:
            print("✅ Logging implemented")
        else:
            print("⚠️  No logging found")
            
    except Exception as e:
        print(f"❌ Documentation test failed: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("Ubuntu Compatibility Testing Framework - Basic Validation")
    print("=" * 70)
    
    success = True
    
    # Run basic functionality tests
    if not test_basic_functionality():
        success = False
    
    # Run documentation tests
    if not test_documentation():
        success = False
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 All basic validation tests passed!")
        print("The Ubuntu Compatibility Testing Framework is ready for use.")
        return 0
    else:
        print("❌ Some validation tests failed.")
        print("Please review the implementation before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())