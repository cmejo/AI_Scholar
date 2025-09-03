"""
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
