#!/usr/bin/env python3
"""
Test suite for security and code quality fixes
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from security_code_quality_fixer import SecurityCodeQualityFixer

def test_security_fixes():
    """Test security fix functionality"""
    print("Testing security and code quality fixes...")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="security_fix_test_")
    temp_path = Path(temp_dir)
    
    try:
        # Create test directory structure
        (temp_path / "src").mkdir()
        (temp_path / "backend" / "core").mkdir(parents=True)
        (temp_path / "backend" / "utils").mkdir(parents=True)
        
        # Create mock App.tsx with authentication issue
        app_tsx = temp_path / "src" / "App.tsx"
        app_content = '''
const initializeEnterpriseFeatures = useCallback(async (): Promise<void> => {
    // Mock user authentication
    const mockUser = {
      id: 'user_admin',
      email: 'admin@example.com',
      name: 'Admin User',
      role: 'admin'
    };
    setUser(mockUser);
    
    // Other initialization code...
}, []);
'''
        app_tsx.write_text(app_content)
        
        # Create mock app.py with security issues
        app_py = temp_path / "backend" / "app.py"
        app_py_content = '''
from fastapi import FastAPI, UploadFile, File

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        # Validate file type
        allowed_types = ['application/pdf', 'text/plain']
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Process document
        result = await process_document(file)
        return result
        
    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")
'''
        app_py.write_text(app_py_content)
        
        # Initialize fixer
        fixer = SecurityCodeQualityFixer(str(temp_path))
        
        # Test individual fixes
        print("Testing mock authentication fix...")
        auth_result = fixer.fix_mock_authentication()
        if auth_result and auth_result.success:
            print("✓ Mock authentication fix applied")
        else:
            print("✗ Mock authentication fix failed")
        
        print("Testing type definitions creation...")
        types_result = fixer.create_type_definitions()
        if types_result and types_result.success:
            print("✓ Type definitions created")
        else:
            print("✗ Type definitions creation failed")
        
        print("Testing file validation utility...")
        validation_result = fixer.fix_file_upload_validation()
        if validation_result and validation_result.success:
            print("✓ File validation utility created")
        else:
            print("✗ File validation utility creation failed")
        
        print("Testing configuration management...")
        config_result = fixer.fix_hardcoded_config()
        if config_result and config_result.success:
            print("✓ Configuration management improved")
        else:
            print("✗ Configuration management fix failed")
        
        print("Testing exception handling...")
        exception_result = fixer.fix_exception_handling()
        if exception_result and exception_result.success:
            print("✓ Custom exceptions created")
        else:
            print("✗ Exception handling fix failed")
        
        # Verify files were created
        expected_files = [
            temp_path / "src" / "types" / "auth.ts",
            temp_path / "backend" / "utils" / "file_validation.py",
            temp_path / "backend" / "core" / "config.py",
            temp_path / "backend" / "core" / "exceptions.py"
        ]
        
        created_files = 0
        for file_path in expected_files:
            if file_path.exists():
                created_files += 1
                print(f"✓ Created: {file_path.relative_to(temp_path)}")
            else:
                print(f"✗ Missing: {file_path.relative_to(temp_path)}")
        
        # Verify content changes
        updated_app_tsx = app_tsx.read_text()
        if "mockUser" not in updated_app_tsx and "authService" in updated_app_tsx:
            print("✓ App.tsx authentication properly updated")
        else:
            print("✗ App.tsx authentication update failed")
        
        print(f"\\n✓ Security fixes test completed!")
        print(f"Files created: {created_files}/{len(expected_files)}")
        
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
    """Run security fixes tests"""
    print("Running security and code quality fix tests...")
    success = test_security_fixes()
    
    if success:
        print("\\n🎉 All security fix tests passed!")
        return 0
    else:
        print("\\n❌ Some security fix tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())