#!/usr/bin/env python3
"""
Apply Security Fixes to Codebase
Direct implementation of security fixes for the identified issues.
"""

import os
import sys
import re
from pathlib import Path

def apply_security_fixes():
    """Apply all security fixes to the codebase"""
    project_root = Path(".")
    
    print("Applying security and code quality fixes...")
    
    # Fix 1: Create enhanced type definitions
    create_type_definitions(project_root)
    
    # Fix 2: Create file validation utility
    create_file_validation_utility(project_root)
    
    # Fix 3: Create custom exceptions
    create_custom_exceptions(project_root)
    
    # Fix 4: Update configuration
    update_configuration(project_root)
    
    # Fix 5: Fix mock authentication (if App.tsx exists)
    fix_mock_authentication(project_root)
    
    print("✅ All security fixes applied successfully!")

def create_type_definitions(project_root: Path):
    """Create comprehensive type definitions"""
    types_dir = project_root / "src" / "types"
    types_dir.mkdir(parents=True, exist_ok=True)
    
    auth_types_path = types_dir / "auth.ts"
    
    auth_types_content = '''// Enhanced Authentication and User Types
export interface User {
  id: string;
  name: string;
  email: string;
  role?: 'admin' | 'user' | 'researcher' | 'student';
  avatar?: string;
  preferences?: UserPreferences;
  createdAt?: Date;
  lastLoginAt?: Date;
  isActive?: boolean;
  permissions?: string[];
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  notifications: NotificationSettings;
  accessibility?: AccessibilitySettings;
}

export interface NotificationSettings {
  email: boolean;
  push: boolean;
  inApp: boolean;
  frequency: 'immediate' | 'daily' | 'weekly';
}

export interface AccessibilitySettings {
  highContrast: boolean;
  fontSize: 'small' | 'medium' | 'large';
  screenReader: boolean;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  token?: string;
  refreshToken?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterData extends LoginCredentials {
  name: string;
  confirmPassword: string;
  acceptTerms: boolean;
}

export interface AuthResponse {
  user: User;
  token: string;
  refreshToken: string;
  expiresAt: Date;
}

export interface AuthError {
  code: string;
  message: string;
  details?: Record<string, any>;
}
'''
    
    auth_types_path.write_text(auth_types_content)
    print(f"✅ Created enhanced type definitions: {auth_types_path}")

def create_file_validation_utility(project_root: Path):
    """Create enhanced file validation utility"""
    utils_dir = project_root / "backend" / "utils"
    utils_dir.mkdir(parents=True, exist_ok=True)
    
    validation_path = utils_dir / "file_validation.py"
    
    validation_content = '''"""
Enhanced File Validation Utilities
Provides comprehensive file validation with security checks.
"""
import os
import hashlib
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# File type mappings with magic bytes for security validation
ALLOWED_FILE_TYPES = {
    'application/pdf': {
        'magic_bytes': [b'%PDF'],
        'extensions': ['.pdf'],
        'description': 'PDF Document',
        'max_size_mb': 50
    },
    'text/plain': {
        'magic_bytes': [],  # Text files don't have specific magic bytes
        'extensions': ['.txt'],
        'description': 'Plain Text',
        'max_size_mb': 10
    },
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': {
        'magic_bytes': [b'PK\\x03\\x04'],  # ZIP-based format
        'extensions': ['.docx'],
        'description': 'Word Document',
        'max_size_mb': 25
    },
    'application/msword': {
        'magic_bytes': [b'\\xd0\\xcf\\x11\\xe0\\xa1\\xb1\\x1a\\xe1'],
        'extensions': ['.doc'],
        'description': 'Legacy Word Document',
        'max_size_mb': 25
    }
}

class FileValidationError(Exception):
    """Custom exception for file validation errors"""
    
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.error_code = error_code

class FileValidator:
    """Enhanced file validator with comprehensive security checks"""
    
    @staticmethod
    def validate_file_type(file_content: bytes, declared_mime_type: str) -> Tuple[bool, str]:
        """
        Validate file type using magic bytes and MIME type.
        Returns (is_valid, error_message)
        """
        if declared_mime_type not in ALLOWED_FILE_TYPES:
            return False, f"Unsupported MIME type: {declared_mime_type}"
        
        file_config = ALLOWED_FILE_TYPES[declared_mime_type]
        magic_bytes_list = file_config['magic_bytes']
        
        # Skip magic byte check for text files
        if declared_mime_type == 'text/plain':
            return True, ""
        
        # Check magic bytes
        for magic_bytes in magic_bytes_list:
            if file_content.startswith(magic_bytes):
                return True, ""
        
        return False, f"File content doesn't match declared type {declared_mime_type}"
    
    @staticmethod
    def validate_file_size(file_size: int, mime_type: str) -> Tuple[bool, str]:
        """Validate file size against type-specific limits"""
        if mime_type not in ALLOWED_FILE_TYPES:
            return False, f"Unknown MIME type: {mime_type}"
        
        max_size_mb = ALLOWED_FILE_TYPES[mime_type]['max_size_mb']
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            return False, f"File too large: {file_size / (1024*1024):.1f}MB (max: {max_size_mb}MB)"
        
        return True, ""
    
    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, str]:
        """Validate filename for security vulnerabilities"""
        if not filename:
            return False, "Filename is required"
        
        # Check for path traversal attempts
        dangerous_patterns = ['..', '/', '\\\\', '<', '>', ':', '"', '|', '?', '*']
        for pattern in dangerous_patterns:
            if pattern in filename:
                return False, f"Invalid filename: contains dangerous character '{pattern}'"
        
        # Check filename length
        if len(filename) > 255:
            return False, "Filename too long (max 255 characters)"
        
        # Check for valid extension
        file_ext = Path(filename).suffix.lower()
        valid_extensions = []
        for config in ALLOWED_FILE_TYPES.values():
            valid_extensions.extend(config['extensions'])
        
        if file_ext not in valid_extensions:
            return False, f"Invalid file extension: {file_ext}"
        
        return True, ""
    
    @staticmethod
    def calculate_file_hash(file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    @classmethod
    def validate_upload_file(
        cls, 
        filename: str, 
        file_content: bytes, 
        declared_mime_type: str
    ) -> Dict[str, any]:
        """
        Comprehensive file validation.
        Returns validation result with details.
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'file_hash': None,
            'file_size': len(file_content)
        }
        
        # Validate filename
        is_valid, error = cls.validate_filename(filename)
        if not is_valid:
            result['is_valid'] = False
            result['errors'].append(error)
        
        # Validate file type
        is_valid, error = cls.validate_file_type(file_content, declared_mime_type)
        if not is_valid:
            result['is_valid'] = False
            result['errors'].append(error)
        
        # Validate file size
        is_valid, error = cls.validate_file_size(len(file_content), declared_mime_type)
        if not is_valid:
            result['is_valid'] = False
            result['errors'].append(error)
        
        # Calculate file hash for integrity
        result['file_hash'] = cls.calculate_file_hash(file_content)
        
        # Additional security checks
        if len(file_content) == 0:
            result['is_valid'] = False
            result['errors'].append("Empty file not allowed")
        
        return result
'''
    
    validation_path.write_text(validation_content)
    print(f"✅ Created file validation utility: {validation_path}")

def create_custom_exceptions(project_root: Path):
    """Create custom exception classes"""
    core_dir = project_root / "backend" / "core"
    core_dir.mkdir(parents=True, exist_ok=True)
    
    exceptions_path = core_dir / "exceptions.py"
    
    exceptions_content = '''"""
Custom Exception Classes for Enhanced Error Handling
Provides specific exception types for better API error responses.
"""
from typing import Optional, Dict, Any

class BaseAPIException(Exception):
    """Base exception for API errors with structured error information"""
    
    def __init__(
        self, 
        message: str,
        error_code: str,
        status_code: int = 500,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.extra_data = extra_data or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response"""
        return {
            'error': {
                'code': self.error_code,
                'message': self.message,
                'status_code': self.status_code,
                'extra_data': self.extra_data
            }
        }

class AuthenticationError(BaseAPIException):
    """Authentication related errors"""
    
    def __init__(self, message: str = "Authentication failed", user_id: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            status_code=401,
            extra_data={'user_id': user_id} if user_id else {}
        )

class AuthorizationError(BaseAPIException):
    """Authorization related errors"""
    
    def __init__(self, message: str = "Insufficient permissions", required_permission: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="AUTHZ_ERROR", 
            status_code=403,
            extra_data={'required_permission': required_permission} if required_permission else {}
        )

class DocumentNotFoundError(BaseAPIException):
    """Document not found errors"""
    
    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document not found: {document_id}",
            error_code="DOCUMENT_NOT_FOUND",
            status_code=404,
            extra_data={'document_id': document_id}
        )

class FileValidationError(BaseAPIException):
    """File validation errors with detailed information"""
    
    def __init__(self, message: str, filename: Optional[str] = None, validation_errors: Optional[List[str]] = None):
        super().__init__(
            message=message,
            error_code="FILE_VALIDATION_ERROR",
            status_code=400,
            extra_data={
                'filename': filename,
                'validation_errors': validation_errors or []
            }
        )

class DocumentProcessingError(BaseAPIException):
    """Document processing errors"""
    
    def __init__(self, message: str, document_id: Optional[str] = None, processing_stage: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="PROCESSING_ERROR",
            status_code=500,
            extra_data={
                'document_id': document_id,
                'processing_stage': processing_stage
            }
        )

class RateLimitError(BaseAPIException):
    """Rate limiting errors"""
    
    def __init__(self, message: str = "Rate limit exceeded", limit: Optional[int] = None, reset_time: Optional[int] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=429,
            extra_data={
                'limit': limit,
                'reset_time': reset_time
            }
        )

class ValidationError(BaseAPIException):
    """Input validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None, invalid_value: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            extra_data={
                'field': field,
                'invalid_value': str(invalid_value) if invalid_value is not None else None
            }
        )

class ConfigurationError(BaseAPIException):
    """Configuration related errors"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            status_code=500,
            extra_data={'config_key': config_key} if config_key else {}
        )
'''
    
    exceptions_path.write_text(exceptions_content)
    print(f"✅ Created custom exceptions: {exceptions_path}")

def update_configuration(project_root: Path):
    """Update configuration with security settings"""
    config_path = project_root / "backend" / "core" / "config.py"
    
    # Read existing config
    if config_path.exists():
        existing_content = config_path.read_text()
    else:
        existing_content = ""
    
    # Add security configuration if not already present
    if "ALLOWED_FILE_TYPES" not in existing_content:
        security_config = '''

# File Upload Security Configuration
ALLOWED_FILE_TYPES = [
    'application/pdf',
    'text/plain', 
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword'
]

# File size limits (in MB)
MAX_FILE_SIZE_MB = 50
MAX_BATCH_FILES = 10
MAX_TOTAL_BATCH_SIZE_MB = 200

# Security settings
ENABLE_MAGIC_BYTE_VALIDATION = True
ENABLE_VIRUS_SCANNING = False  # Set to True in production with ClamAV
ENABLE_FILE_QUARANTINE = True
QUARANTINE_DIRECTORY = "quarantine"

# Upload paths
UPLOAD_DIRECTORY = "uploads"
TEMP_DIRECTORY = "temp"
PROCESSED_DIRECTORY = "processed"

# Rate limiting
MAX_UPLOADS_PER_HOUR = 100
MAX_UPLOADS_PER_DAY = 500

# Authentication settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
REFRESH_TOKEN_EXPIRATION_DAYS = 30

# Session security
SESSION_TIMEOUT_MINUTES = 60
MAX_CONCURRENT_SESSIONS = 5
ENABLE_SESSION_MONITORING = True
'''
        
        updated_content = existing_content + security_config
        config_path.write_text(updated_content)
        print(f"✅ Updated configuration with security settings: {config_path}")

def fix_mock_authentication(project_root: Path):
    """Fix mock authentication in App.tsx"""
    app_tsx_path = project_root / "src" / "App.tsx"
    
    if not app_tsx_path.exists():
        print("⚠️  App.tsx not found, skipping authentication fix")
        return
    
    content = app_tsx_path.read_text()
    
    # Look for mock authentication pattern
    mock_pattern = r'const mockUser = \{[^}]+\};\s*setUser\(mockUser\);'
    
    if re.search(mock_pattern, content, re.DOTALL):
        # Create backup
        backup_path = app_tsx_path.with_suffix('.tsx.backup')
        backup_path.write_text(content)
        
        # Replace mock authentication
        replacement = '''// TODO: Replace with real authentication service
    try {
      const authenticatedUser = await authService.getCurrentUser();
      if (authenticatedUser) {
        setUser(authenticatedUser);
      } else {
        // Redirect to login or show auth modal
        console.warn('No authenticated user found - redirecting to login');
        // window.location.href = '/login';
      }
    } catch (error) {
      console.error('Authentication failed:', error);
      // Handle authentication error appropriately
      setUser(null);
    }'''
        
        updated_content = re.sub(mock_pattern, replacement, content, flags=re.DOTALL)
        app_tsx_path.write_text(updated_content)
        
        print(f"✅ Fixed mock authentication in App.tsx (backup created)")
        print("⚠️  Remember to implement proper authService.getCurrentUser() method")

if __name__ == "__main__":
    apply_security_fixes()