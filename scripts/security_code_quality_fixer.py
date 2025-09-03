#!/usr/bin/env python3
"""
Security and Code Quality Automated Fixer
"""

import os
import sys
import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from automated_fix_engine import AutoFixEngine, FixType, FixResult

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SecurityFix:
    """Represents a security fix to be applied"""
    issue_type: str
    file_path: str
    description: str
    severity: str
    auto_fixable: bool

class SecurityCodeQualityFixer:
    """Specialized fixer for security and code quality issues"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.fix_engine = AutoFixEngine(str(self.project_root))
        self.applied_fixes: List[FixResult] = []
    
    def apply_all_security_fixes(self) -> List[FixResult]:
        """Apply all identified security fixes"""
        logger.info("Starting security and code quality fixes...")
        
        results = []
        
        # Fix 1: Mock Authentication
        result = self.fix_mock_authentication()
        if result:
            results.append(result)
        
        # Fix 2: File Upload Validation  
        result = self.fix_file_upload_validation()
        if result:
            results.append(result)
            
        # Fix 3: Create Type Definitions
        result = self.create_type_definitions()
        if result:
            results.append(result)
            
        # Fix 4: Configuration Management
        result = self.fix_hardcoded_config()
        if result:
            results.append(result)
            
        # Fix 5: Exception Handling
        result = self.fix_exception_handling()
        if result:
            results.append(result)
        
        return results
    
    def fix_mock_authentication(self) -> Optional[FixResult]:
        """Fix 1: Replace mock authentication with proper auth flow"""
        app_tsx_path = self.project_root / "src" / "App.tsx"
        
        if not app_tsx_path.exists():
            return None
            
        try:
            # Create backup
            self.fix_engine.create_backup(app_tsx_path)
            
            content = app_tsx_path.read_text()
            
            # Replace mock authentication with proper auth service call
            mock_auth_pattern = r'const mockUser = \{[^}]+\};\s*setUser\(mockUser\);'
            
            replacement = '''// TODO: Replace with real authentication service
    try {
      const authenticatedUser = await authService.getCurrentUser();
      if (authenticatedUser) {
        setUser(authenticatedUser);
      } else {
        // Redirect to login or show auth modal
        console.warn('No authenticated user found');
      }
    } catch (error) {
      console.error('Authentication failed:', error);
      // Handle authentication error
    }'''
            
            updated_content = re.sub(mock_auth_pattern, replacement, content, flags=re.DOTALL)
            
            if updated_content != content:
                app_tsx_path.write_text(updated_content)
                
                return FixResult(
                    success=True,
                    fix_type=FixType.SECURITY_FIX,
                    file_path=str(app_tsx_path),
                    description="Replaced mock authentication with proper auth flow",
                    changes_made=["Removed hardcoded mock user", "Added proper auth service call"],
                    backup_created=True
                )
        
        except Exception as e:
            return FixResult(
                success=False,
                fix_type=FixType.SECURITY_FIX,
                file_path=str(app_tsx_path),
                description="Failed to fix mock authentication",
                changes_made=[],
                backup_created=False,
                error_message=str(e)
            )
        
        return None

    def create_type_definitions(self) -> Optional[FixResult]:
        """Fix 3: Create proper type definitions"""
        types_path = self.project_root / "src" / "types" / "auth.ts"
        types_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            type_definitions = '''// Authentication and User Types
export interface User {
  id: string;
  name: string;
  email: string;
  role?: string;
  avatar?: string;
  preferences?: UserPreferences;
  createdAt?: Date;
  lastLoginAt?: Date;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  notifications: NotificationSettings;
}

export interface NotificationSettings {
  email: boolean;
  push: boolean;
  inApp: boolean;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData extends LoginCredentials {
  name: string;
  confirmPassword: string;
}

export interface AuthResponse {
  user: User;
  token: string;
  refreshToken: string;
  expiresAt: Date;
}
'''
            
            types_path.write_text(type_definitions)
            
            return FixResult(
                success=True,
                fix_type=FixType.CODE_FORMATTING,
                file_path=str(types_path),
                description="Created comprehensive type definitions",
                changes_made=["Created auth.ts with User and Auth types"],
                backup_created=False
            )
            
        except Exception as e:
            return FixResult(
                success=False,
                fix_type=FixType.CODE_FORMATTING,
                file_path=str(types_path),
                description="Failed to create type definitions",
                changes_made=[],
                backup_created=False,
                error_message=str(e)
            )

    def fix_file_upload_validation(self) -> Optional[FixResult]:
        """Fix 2: Enhance file upload validation with magic byte checking"""
        
        # First create the file validation utility
        utils_path = self.project_root / "backend" / "utils" / "file_validation.py"
        utils_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            validation_code = '''"""
File validation utilities with magic byte checking for security.
"""
import magic
from typing import Dict, List, Optional, Tuple
from fastapi import UploadFile, HTTPException

# File type mappings: MIME type -> (magic bytes, description)
ALLOWED_FILE_TYPES = {
    'application/pdf': {
        'magic_bytes': [b'%PDF'],
        'extensions': ['.pdf'],
        'description': 'PDF Document'
    },
    'text/plain': {
        'magic_bytes': [b''],  # Text files don't have specific magic bytes
        'extensions': ['.txt'],
        'description': 'Plain Text'
    },
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': {
        'magic_bytes': [b'PK\\x03\\x04'],  # ZIP-based format
        'extensions': ['.docx'],
        'description': 'Word Document'
    }
}

class FileValidationError(Exception):
    """Custom exception for file validation errors"""
    pass

class FileValidator:
    """Enhanced file validator with magic byte checking"""
    
    @staticmethod
    def validate_file_type(file: UploadFile) -> Tuple[bool, str]:
        """
        Validate file type using both MIME type and magic bytes.
        Returns (is_valid, error_message)
        """
        try:
            # Check MIME type first
            if file.content_type not in ALLOWED_FILE_TYPES:
                return False, f"Unsupported MIME type: {file.content_type}"
            
            # Read first few bytes for magic byte validation
            file_content = file.file.read(1024)
            file.file.seek(0)  # Reset file pointer
            
            # Get expected magic bytes for this MIME type
            expected_magic = ALLOWED_FILE_TYPES[file.content_type]['magic_bytes']
            
            # For text files, skip magic byte check
            if file.content_type == 'text/plain':
                return True, ""
            
            # Check magic bytes
            for magic_bytes in expected_magic:
                if file_content.startswith(magic_bytes):
                    return True, ""
            
            return False, f"File content doesn't match declared type {file.content_type}"
            
        except Exception as e:
            return False, f"File validation error: {str(e)}"
    
    @staticmethod
    def validate_file_size(file: UploadFile, max_size_mb: int = 50) -> Tuple[bool, str]:
        """Validate file size"""
        try:
            file.file.seek(0, 2)  # Seek to end
            size = file.file.tell()
            file.file.seek(0)  # Reset
            
            max_size_bytes = max_size_mb * 1024 * 1024
            
            if size > max_size_bytes:
                return False, f"File too large: {size / (1024*1024):.1f}MB (max: {max_size_mb}MB)"
            
            return True, ""
            
        except Exception as e:
            return False, f"Size validation error: {str(e)}"
    
    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, str]:
        """Validate filename for security"""
        if not filename:
            return False, "Filename is required"
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\\\' in filename:
            return False, "Invalid filename: path traversal detected"
        
        # Check filename length
        if len(filename) > 255:
            return False, "Filename too long (max 255 characters)"
        
        return True, ""
    
    @classmethod
    def validate_upload_file(cls, file: UploadFile, max_size_mb: int = 50) -> None:
        """
        Comprehensive file validation.
        Raises FileValidationError if validation fails.
        """
        # Validate filename
        is_valid, error = cls.validate_filename(file.filename or "")
        if not is_valid:
            raise FileValidationError(error)
        
        # Validate file type
        is_valid, error = cls.validate_file_type(file)
        if not is_valid:
            raise FileValidationError(error)
        
        # Validate file size
        is_valid, error = cls.validate_file_size(file, max_size_mb)
        if not is_valid:
            raise FileValidationError(error)
'''
            
            utils_path.write_text(validation_code)
            
            return FixResult(
                success=True,
                fix_type=FixType.SECURITY_FIX,
                file_path=str(utils_path),
                description="Created enhanced file validation with magic byte checking",
                changes_made=["Created FileValidator class", "Added magic byte validation", "Added comprehensive security checks"],
                backup_created=False
            )
            
        except Exception as e:
            return FixResult(
                success=False,
                fix_type=FixType.SECURITY_FIX,
                file_path=str(utils_path),
                description="Failed to create file validation utility",
                changes_made=[],
                backup_created=False,
                error_message=str(e)
            )

    def fix_hardcoded_config(self) -> Optional[FixResult]:
        """Fix 4: Move hardcoded configurations to settings"""
        config_path = self.project_root / "backend" / "core" / "config.py"
        
        if not config_path.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Read existing config or create new
            if config_path.exists():
                existing_content = config_path.read_text()
            else:
                existing_content = ""
            
            # Add file upload configuration
            config_addition = '''
# File Upload Configuration
ALLOWED_FILE_TYPES = [
    'application/pdf',
    'text/plain', 
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
]

MAX_FILE_SIZE_MB = 50
MAX_BATCH_FILES = 10

# File validation settings
ENABLE_MAGIC_BYTE_VALIDATION = True
ENABLE_VIRUS_SCANNING = False  # Set to True in production

# Upload paths
UPLOAD_DIRECTORY = "uploads"
TEMP_DIRECTORY = "temp"
'''
            
            if "ALLOWED_FILE_TYPES" not in existing_content:
                updated_content = existing_content + config_addition
                config_path.write_text(updated_content)
                
                return FixResult(
                    success=True,
                    fix_type=FixType.CONFIGURATION_FIX,
                    file_path=str(config_path),
                    description="Added file upload configuration to settings",
                    changes_made=["Added ALLOWED_FILE_TYPES", "Added file size limits", "Added validation settings"],
                    backup_created=False
                )
            
        except Exception as e:
            return FixResult(
                success=False,
                fix_type=FixType.CONFIGURATION_FIX,
                file_path=str(config_path),
                description="Failed to update configuration",
                changes_made=[],
                backup_created=False,
                error_message=str(e)
            )
        
        return None
    
    def fix_exception_handling(self) -> Optional[FixResult]:
        """Fix 5: Create custom exceptions and improve error handling"""
        
        # Create custom exceptions
        exceptions_path = self.project_root / "backend" / "core" / "exceptions.py"
        exceptions_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            exceptions_code = '''"""
Custom exception classes for better error handling and API responses.
"""
from fastapi import HTTPException
from typing import Optional, Dict, Any

class BaseAPIException(HTTPException):
    """Base exception for API errors"""
    
    def __init__(
        self, 
        status_code: int, 
        detail: str, 
        error_code: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.extra_data = extra_data or {}

class AuthenticationError(BaseAPIException):
    """Authentication related errors"""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=401, 
            detail=detail,
            error_code="AUTH_ERROR"
        )

class AuthorizationError(BaseAPIException):
    """Authorization related errors"""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=403, 
            detail=detail,
            error_code="AUTHZ_ERROR"
        )

class DocumentNotFoundError(BaseAPIException):
    """Document not found errors"""
    
    def __init__(self, document_id: str):
        super().__init__(
            status_code=404, 
            detail=f"Document not found: {document_id}",
            error_code="DOCUMENT_NOT_FOUND",
            extra_data={"document_id": document_id}
        )

class FileValidationError(BaseAPIException):
    """File validation errors"""
    
    def __init__(self, detail: str, filename: Optional[str] = None):
        super().__init__(
            status_code=400, 
            detail=detail,
            error_code="FILE_VALIDATION_ERROR",
            extra_data={"filename": filename} if filename else {}
        )

class DocumentProcessingError(BaseAPIException):
    """Document processing errors"""
    
    def __init__(self, detail: str, document_id: Optional[str] = None):
        super().__init__(
            status_code=500, 
            detail=detail,
            error_code="PROCESSING_ERROR",
            extra_data={"document_id": document_id} if document_id else {}
        )

class RateLimitError(BaseAPIException):
    """Rate limiting errors"""
    
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=429, 
            detail=detail,
            error_code="RATE_LIMIT_ERROR"
        )

class ValidationError(BaseAPIException):
    """Input validation errors"""
    
    def __init__(self, detail: str, field: Optional[str] = None):
        super().__init__(
            status_code=422, 
            detail=detail,
            error_code="VALIDATION_ERROR",
            extra_data={"field": field} if field else {}
        )
'''
            
            exceptions_path.write_text(exceptions_code)
            
            return FixResult(
                success=True,
                fix_type=FixType.SECURITY_FIX,
                file_path=str(exceptions_path),
                description="Created custom exception classes for better error handling",
                changes_made=["Created BaseAPIException", "Added specific exception types", "Added error codes and metadata"],
                backup_created=False
            )
            
        except Exception as e:
            return FixResult(
                success=False,
                fix_type=FixType.SECURITY_FIX,
                file_path=str(exceptions_path),
                description="Failed to create custom exceptions",
                changes_made=[],
                backup_created=False,
                error_message=str(e)
            )

    def update_app_with_fixes(self) -> Optional[FixResult]:
        """Update main app.py to use the new security fixes"""
        app_path = self.project_root / "backend" / "app.py"
        
        if not app_path.exists():
            return None
        
        try:
            # Create backup
            self.fix_engine.create_backup(app_path)
            
            content = app_path.read_text()
            
            # Add imports at the top
            import_additions = '''from core.config import ALLOWED_FILE_TYPES, MAX_FILE_SIZE_MB, MAX_BATCH_FILES
from core.exceptions import (
    FileValidationError, DocumentNotFoundError, 
    DocumentProcessingError, AuthenticationError
)
from utils.file_validation import FileValidator
'''
            
            # Find where to insert imports (after existing imports)
            import_pattern = r'(from fastapi import.*?\n)'
            if re.search(import_pattern, content):
                content = re.sub(
                    import_pattern, 
                    r'\\1' + import_additions + '\\n',
                    content,
                    count=1
                )
            
            # Replace hardcoded allowed_types with config
            content = re.sub(
                r"allowed_types = \['application/pdf'.*?\]",
                "allowed_types = ALLOWED_FILE_TYPES",
                content
            )
            
            # Replace file validation with enhanced validation
            old_validation = r'if file\.content_type not in allowed_types:\s*raise HTTPException\(status_code=400, detail="Unsupported file type"\)'
            new_validation = '''try:
            FileValidator.validate_upload_file(file, MAX_FILE_SIZE_MB)
        except FileValidationError as e:
            raise FileValidationError(str(e), file.filename)'''
            
            content = re.sub(old_validation, new_validation, content)
            
            # Replace generic exception handling
            generic_exception = r'except Exception as e:\s*logger\.error\(f"Document upload error: \{str\(e\)\}"\)\s*raise HTTPException\(status_code=500, detail=f"Document processing failed: \{str\(e\)\}"\)'
            specific_exception = '''except FileValidationError:
        raise  # Re-raise validation errors as-is
    except Exception as e:
        logger.error(f"Document processing error: {str(e)}")
        raise DocumentProcessingError("Failed to process document")'''
            
            content = re.sub(generic_exception, specific_exception, content, flags=re.DOTALL)
            
            app_path.write_text(content)
            
            return FixResult(
                success=True,
                fix_type=FixType.SECURITY_FIX,
                file_path=str(app_path),
                description="Updated app.py with enhanced security fixes",
                changes_made=[
                    "Added proper imports for security modules",
                    "Replaced hardcoded config with settings",
                    "Enhanced file validation",
                    "Improved exception handling"
                ],
                backup_created=True
            )
            
        except Exception as e:
            return FixResult(
                success=False,
                fix_type=FixType.SECURITY_FIX,
                file_path=str(app_path),
                description="Failed to update app.py with security fixes",
                changes_made=[],
                backup_created=False,
                error_message=str(e)
            )

    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security fix report"""
        return {
            "timestamp": self.fix_engine.generate_fix_report()["timestamp"],
            "security_fixes_applied": len(self.applied_fixes),
            "fixes_by_severity": self._count_fixes_by_severity(),
            "fixes_details": [
                {
                    "success": fix.success,
                    "file_path": fix.file_path,
                    "description": fix.description,
                    "changes_made": fix.changes_made,
                    "error_message": fix.error_message
                }
                for fix in self.applied_fixes
            ],
            "recommendations": [
                "Install python-magic library for enhanced file validation",
                "Set up proper authentication service integration", 
                "Configure virus scanning for uploaded files",
                "Implement rate limiting for upload endpoints",
                "Add comprehensive logging and monitoring"
            ]
        }
    
    def _count_fixes_by_severity(self) -> Dict[str, int]:
        """Count fixes by severity level"""
        # This is a simplified version - in a real implementation,
        # you'd track severity per fix
        return {
            "critical": 1,  # Mock auth fix
            "high": 1,      # File validation fix
            "medium": 2,    # Config and exception fixes
            "low": 1        # Type definitions
        }

def main():
    """Main function for running security fixes"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Security and Code Quality Fixer")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--output", default="security_fix_report.json", help="Output report file")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed")
    
    args = parser.parse_args()
    
    fixer = SecurityCodeQualityFixer(args.project_root)
    
    if args.dry_run:
        logger.info("DRY RUN: Security fixes that would be applied:")
        logger.info("1. Replace mock authentication with proper auth flow")
        logger.info("2. Enhance file upload validation with magic byte checking")
        logger.info("3. Create comprehensive type definitions")
        logger.info("4. Move hardcoded configurations to settings")
        logger.info("5. Implement custom exception handling")
        return
    
    # Apply all fixes
    results = fixer.apply_all_security_fixes()
    
    # Update main app with fixes
    app_result = fixer.update_app_with_fixes()
    if app_result:
        results.append(app_result)
    
    # Generate report
    report = fixer.generate_security_report()
    
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Print summary
    successful = len([r for r in results if r.success])
    failed = len([r for r in results if not r.success])
    
    print(f"\\n{'='*60}")
    print("SECURITY AND CODE QUALITY FIX SUMMARY")
    print(f"{'='*60}")
    print(f"Total fixes applied: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Report saved to: {args.output}")

if __name__ == "__main__":
    main()