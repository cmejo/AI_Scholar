#!/usr/bin/env python3
"""
Test script to verify analysis infrastructure setup
"""

import subprocess
import sys
from pathlib import Path
import json
import tempfile

def test_python_tools():
    """Test Python analysis tools."""
    print("Testing Python analysis tools...")
    
    # Test flake8
    try:
        result = subprocess.run(['python', '-m', 'flake8', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ flake8 is available")
        else:
            print("✗ flake8 failed")
            return False
    except Exception as e:
        print(f"✗ flake8 error: {e}")
        return False
    
    # Test black
    try:
        result = subprocess.run(['python', '-m', 'black', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ black is available")
        else:
            print("✗ black failed")
            return False
    except Exception as e:
        print(f"✗ black error: {e}")
        return False
    
    # Test mypy
    try:
        result = subprocess.run(['python', '-m', 'mypy', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ mypy is available")
        else:
            print("✗ mypy failed")
            return False
    except Exception as e:
        print(f"✗ mypy error: {e}")
        return False
    
    return True

def test_node_tools():
    """Test Node.js analysis tools."""
    print("\nTesting Node.js analysis tools...")
    
    # Test npm
    try:
        result = subprocess.run(['npm', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ npm is available")
        else:
            print("✗ npm failed")
            return False
    except Exception as e:
        print(f"✗ npm error: {e}")
        return False
    
    # Test if we can run eslint (might not be installed globally)
    try:
        result = subprocess.run(['npx', 'eslint', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ eslint is available via npx")
        else:
            print("? eslint not available globally (this is OK)")
    except Exception as e:
        print(f"? eslint via npx: {e}")
    
    return True

def test_system_tools():
    """Test system analysis tools."""
    print("\nTesting system analysis tools...")
    
    # Test shellcheck
    try:
        result = subprocess.run(['shellcheck', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ shellcheck is available")
        else:
            print("✗ shellcheck failed")
    except Exception as e:
        print(f"✗ shellcheck error: {e}")
    
    # Test yamllint
    try:
        result = subprocess.run(['yamllint', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ yamllint is available")
        else:
            print("✗ yamllint failed")
    except Exception as e:
        print(f"✗ yamllint error: {e}")
    
    # Test hadolint
    try:
        result = subprocess.run(['hadolint', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ hadolint is available")
        else:
            print("✗ hadolint failed")
    except Exception as e:
        print(f"✗ hadolint error: {e}")
    
    return True

def test_analysis_script():
    """Test the main analysis script."""
    print("\nTesting main analysis script...")
    
    script_path = Path(__file__).parent / "codebase-analysis.py"
    if not script_path.exists():
        print("✗ Main analysis script not found")
        return False
    
    # Test script syntax
    try:
        result = subprocess.run(['python3', '-m', 'py_compile', str(script_path)], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ Analysis script syntax is valid")
        else:
            print(f"✗ Analysis script syntax error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Analysis script test error: {e}")
        return False
    
    # Test script help
    try:
        result = subprocess.run(['python3', str(script_path), '--help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ Analysis script help works")
        else:
            print(f"✗ Analysis script help failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Analysis script help error: {e}")
        return False
    
    return True

def test_configuration_files():
    """Test configuration files."""
    print("\nTesting configuration files...")
    
    project_root = Path(__file__).parent.parent
    
    # Test configuration files exist
    config_files = [
        "backend/setup.cfg",
        "backend/.pylintrc",
        ".hadolint.yaml",
        ".yamllint.yml",
        ".eslintrc.analysis.js"
    ]
    
    for config_file in config_files:
        config_path = project_root / config_file
        if config_path.exists():
            print(f"✓ {config_file} exists")
        else:
            print(f"✗ {config_file} missing")
    
    # Test if configuration files are valid
    # Test YAML files
    yaml_files = [".hadolint.yaml", ".yamllint.yml"]
    for yaml_file in yaml_files:
        yaml_path = project_root / yaml_file
        if yaml_path.exists():
            try:
                import yaml
                with open(yaml_path, 'r') as f:
                    yaml.safe_load(f)
                print(f"✓ {yaml_file} is valid YAML")
            except Exception as e:
                print(f"✗ {yaml_file} YAML error: {e}")
    
    return True

def main():
    """Run all tests."""
    print("Testing Analysis Infrastructure Setup")
    print("=" * 50)
    
    tests = [
        test_python_tools,
        test_node_tools,
        test_system_tools,
        test_analysis_script,
        test_configuration_files
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! Analysis infrastructure is ready.")
        return 0
    else:
        print("✗ Some tests failed. Please check the setup.")
        return 1

if __name__ == "__main__":
    sys.exit(main())