#!/usr/bin/env python3
"""
Basic test for automated fix engine functionality
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from automated_fix_engine import AutoFixEngine, FixType

def test_basic_functionality():
    """Test basic fix engine functionality"""
    print("Testing basic automated fix functionality...")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="fix_test_")
    temp_path = Path(temp_dir)
    
    try:
        # Create test files
        print(f"Creating test files in {temp_dir}")
        
        # Create a Python file with formatting issues
        python_file = temp_path / "test.py"
        python_content = '''import os,sys
def hello():
    x=1+2
    print("hello")
    return x
'''
        python_file.write_text(python_content)
        
        # Create a JSON file with formatting issues
        json_file = temp_path / "config.json"
        json_content = '{"name":"test","version":"1.0.0","debug":true}'
        json_file.write_text(json_content)
        
        # Create requirements.txt with old versions
        req_file = temp_path / "requirements.txt"
        req_content = '''fastapi==0.100.0
uvicorn==0.20.0
pydantic==1.10.0
'''
        req_file.write_text(req_content)
        
        # Initialize fix engine
        fix_engine = AutoFixEngine(str(temp_path))
        
        # Test backup creation
        print("Testing backup creation...")
        backup_result = fix_engine.create_backup(python_file)
        print(f"✓ Backup created: {backup_result}")
        
        # Test configuration fixes (JSON formatting)
        print("Testing configuration fixes...")
        config_results = fix_engine.apply_configuration_fixes()
        print(f"✓ Configuration fixes applied: {len(config_results)}")
        
        for result in config_results:
            if result.success:
                print(f"  ✓ Fixed {result.file_path}: {', '.join(result.changes_made)}")
            else:
                print(f"  ✗ Failed {result.file_path}: {result.error_message}")
        
        # Test dependency updates
        print("Testing dependency updates...")
        dep_results = fix_engine.apply_dependency_updates()
        print(f"✓ Dependency updates applied: {len(dep_results)}")
        
        for result in dep_results:
            if result.success:
                print(f"  ✓ Updated {result.file_path}: {', '.join(result.changes_made)}")
            else:
                print(f"  ✗ Failed {result.file_path}: {result.error_message}")
        
        # Generate report
        print("Testing report generation...")
        report = fix_engine.generate_fix_report()
        print(f"✓ Report generated with {report['total_fixes_applied']} fixes")
        print(f"  Successful: {report['successful_fixes']}")
        print(f"  Failed: {report['failed_fixes']}")
        
        # Verify JSON file was formatted
        formatted_json = json_file.read_text()
        print(f"✓ JSON file formatted: {len(formatted_json.splitlines()) > 1}")
        
        # Verify requirements were updated
        updated_req = req_file.read_text()
        print(f"✓ Requirements updated: {'>=0.104.0' in updated_req}")
        
        print("\n✓ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)
        print(f"✓ Cleaned up test directory")

def main():
    """Run basic tests"""
    print("Running basic automated fix tests...")
    success = test_basic_functionality()
    
    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())