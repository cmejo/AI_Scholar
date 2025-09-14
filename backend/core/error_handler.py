"""
Comprehensive error handling utilities for API endpoints
"""
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
from functools import wraps

# Conditional imports for FastAPI dependencies
try:
    from fastapi import HTTPException, Request
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    # Fallback for when FastAPI is not available
    FASTAPI_AVAILABLE = False
    
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        def dict(self):
            return {key: value for key, value in self.__dict__.items()}
    
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)


logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    request_id: Optional[str] = None
    service_status: Optional[Dict[str, str]] = None


class ServiceUnavailableError(Exception):
    """Exception raised when a required service is unavailable"""
    def __init__(self, service_name: str, message: str = None):
        self.service_name = service_name
        self.message = message or f"Service {service_name} is unavailable"
        super().__init__(self.message)


class ValidationError(Exception):
    """Exception raised for request validation errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class EndpointErrorHandler:
    """
    Centralized error handling for API endpoints
    """
    
    @staticmethod
    def create_error_response(
        error_type: str,
        message: str,
        details: Dict[str, Any] = None,
        request_id: str = None,
        service_status: Dict[str, str] = None
    ) -> ErrorResponse:
        """
        Create a standardized error response
        
        Args:
            error_type: Type of error (e.g., "service_unavailable", "validation_error")
            message: Human-readable error message
            details: Additional error details
            request_id: Request ID for tracking
            service_status: Status of related services
            
        Returns:
            ErrorResponse: Standardized error response
        """
        return ErrorResponse(
            error=error_type,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            request_id=request_id,
            service_status=service_status
        )
    
    @staticmethod
    def log_error(
        endpoint_name: str,
        error: Exception,
        request_data: Dict[str, Any] = None,
        user_id: str = None,
        request_id: str = None
    ) -> None:
        """
        Log endpoint errors with comprehensive context
        
        Args:
            endpoint_name: Name of the endpoint where error occurred
            error: The exception that occurred
            request_data: Request data that caused the error
            user_id: User ID if available
            request_id: Request ID for tracking
        """
        error_context = {
            "endpoint": endpoint_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "user_id": user_id,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if request_data:
            # Sanitize sensitive data
            sanitized_data = EndpointErrorHandler._sanitize_request_data(request_data)
            error_context["request_data"] = sanitized_data
        
        logger.error(
            f"Endpoint error in {endpoint_name}: {str(error)}",
            extra=error_context,
            exc_info=True
        )
    
    @staticmethod
    def _sanitize_request_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize request data to remove sensitive information
        
        Args:
            data: Request data to sanitize
            
        Returns:
            Dict: Sanitized request data
        """
        sensitive_keys = {
            'password', 'token', 'api_key', 'secret', 'auth', 'authorization',
            'private_key', 'access_token', 'refresh_token', 'session_id'
        }
        
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = EndpointErrorHandler._sanitize_request_data(value)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                sanitized[key] = [EndpointErrorHandler._sanitize_request_data(item) for item in value]
            else:
                sanitized[key] = value
        
        return sanitized
    
    @staticmethod
    def get_service_status_context(service_manager, service_names: List[str]) -> Dict[str, str]:
        """
        Get status context for multiple services
        
        Args:
            service_manager: Service manager instance
            service_names: List of service names to check
            
        Returns:
            Dict: Service status information
        """
        status_context = {}
        
        for service_name in service_names:
            try:
                if service_manager.is_service_healthy(service_name):
                    status_context[service_name] = "healthy"
                else:
                    health = service_manager.health_status.get(service_name)
                    if health:
                        status_context[service_name] = health.status.value
                        if health.error_message:
                            status_context[f"{service_name}_error"] = health.error_message
                    else:
                        status_context[service_name] = "not_initialized"
            except Exception as e:
                status_context[service_name] = f"error: {str(e)}"
        
        return status_context


def handle_endpoint_errors(
    endpoint_name: str,
    required_services: List[str] = None,
    fallback_response: Any = None
):
    """
    Decorator for comprehensive endpoint error handling
    
    Args:
        endpoint_name: Name of the endpoint for logging
        required_services: List of services required by this endpoint
        fallback_response: Response to return if services are unavailable
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Only import service_manager when needed to avoid circular imports
            try:
                from core.service_manager import service_manager
            except ImportError:
                logger.warning("Service manager not available - skipping service checks")
                service_manager = None
            
            request_id = None
            user_id = None
            request_data = {}
            
            try:
                # Extract request information if available
                for arg in args:
                    if hasattr(arg, 'headers'):  # FastAPI Request object
                        request_id = arg.headers.get('x-request-id')
                        break
                
                # Extract request data from kwargs
                if 'request' in kwargs:
                    request_data = kwargs['request'] if isinstance(kwargs['request'], dict) else {}
                
                # Check required services if service manager is available
                if required_services and service_manager:
                    unavailable_services = []
                    service_status = {}
                    
                    for service_name in required_services:
                        if not service_manager.is_service_healthy(service_name):
                            unavailable_services.append(service_name)
                        
                        # Get service status for context
                        health = service_manager.health_status.get(service_name)
                        if health:
                            service_status[service_name] = health.status.value
                        else:
                            service_status[service_name] = "not_initialized"
                    
                    if unavailable_services:
                        error_msg = f"Required services unavailable: {unavailable_services}"
                        
                        # Log the service unavailability
                        EndpointErrorHandler.log_error(
                            endpoint_name=endpoint_name,
                            error=ServiceUnavailableError(", ".join(unavailable_services)),
                            request_data=request_data,
                            user_id=user_id,
                            request_id=request_id
                        )
                        
                        if fallback_response is not None:
                            logger.info(f"Returning fallback response for {endpoint_name}")
                            return fallback_response
                        else:
                            error_response = EndpointErrorHandler.create_error_response(
                                error_type="service_unavailable",
                                message=error_msg,
                                details={"unavailable_services": unavailable_services},
                                request_id=request_id,
                                service_status=service_status
                            )
                            if FASTAPI_AVAILABLE:
                                raise HTTPException(
                                    status_code=503,
                                    detail=error_response.dict()
                                )
                            else:
                                raise ServiceUnavailableError(", ".join(unavailable_services), error_msg)
                
                # Execute the endpoint function
                return await func(*args, **kwargs)
                
            except Exception as e:
                # Handle all exceptions
                if FASTAPI_AVAILABLE and isinstance(e, HTTPException):
                    # Re-raise HTTP exceptions as-is
                    raise
                
                # Log the error
                EndpointErrorHandler.log_error(
                    endpoint_name=endpoint_name,
                    error=e,
                    request_data=request_data,
                    user_id=user_id,
                    request_id=request_id
                )
                
                if isinstance(e, ValidationError):
                    # Handle validation errors
                    error_response = EndpointErrorHandler.create_error_response(
                        error_type="validation_error",
                        message=e.message,
                        details=e.details,
                        request_id=request_id
                    )
                    if FASTAPI_AVAILABLE:
                        raise HTTPException(
                            status_code=400,
                            detail=error_response.dict()
                        )
                    else:
                        raise
                        
                elif isinstance(e, ServiceUnavailableError):
                    # Handle service unavailable errors
                    service_status = None
                    if service_manager:
                        service_status = EndpointErrorHandler.get_service_status_context(
                            service_manager, [e.service_name]
                        )
                    
                    error_response = EndpointErrorHandler.create_error_response(
                        error_type="service_unavailable",
                        message=e.message,
                        details={"service_name": e.service_name},
                        request_id=request_id,
                        service_status=service_status
                    )
                    if FASTAPI_AVAILABLE:
                        raise HTTPException(
                            status_code=503,
                            detail=error_response.dict()
                        )
                    else:
                        raise
                        
                else:
                    # Handle unexpected errors
                    service_status = None
                    if required_services and service_manager:
                        service_status = EndpointErrorHandler.get_service_status_context(
                            service_manager, required_services
                        )
                    
                    error_response = EndpointErrorHandler.create_error_response(
                        error_type="internal_error",
                        message="An unexpected error occurred",
                        details={"error_type": type(e).__name__, "error_message": str(e)},
                        request_id=request_id,
                        service_status=service_status
                    )
                    if FASTAPI_AVAILABLE:
                        raise HTTPException(
                            status_code=500,
                            detail=error_response.dict()
                        )
                    else:
                        raise
        
        return wrapper
    return decorator


def validate_request_data(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate request data for required fields
    
    Args:
        data: Request data to validate
        required_fields: List of required field names
        
    Raises:
        ValidationError: If validation fails
    """
    missing_fields = []
    invalid_fields = []
    
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
        elif data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            invalid_fields.append(field)
    
    if missing_fields or invalid_fields:
        details = {}
        if missing_fields:
            details["missing_fields"] = missing_fields
        if invalid_fields:
            details["invalid_fields"] = invalid_fields
        
        raise ValidationError(
            message="Request validation failed",
            details=details
        )


def create_fallback_response(
    message: str = "Service temporarily unavailable",
    data: Any = None,
    status: str = "degraded"
) -> Dict[str, Any]:
    """
    Create a standardized fallback response
    
    Args:
        message: Fallback message
        data: Fallback data
        status: Response status
        
    Returns:
        Dict: Fallback response
    """
    return {
        "status": status,
        "message": message,
        "data": data or [],
        "timestamp": datetime.utcnow(),
        "fallback": True
    }