"""
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
        'magic_bytes': [b'PK\x03\x04'],  # ZIP-based format
        'extensions': ['.docx'],
        'description': 'Word Document',
        'max_size_mb': 25
    },
    'application/msword': {
        'magic_bytes': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],
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
        dangerous_patterns = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
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
