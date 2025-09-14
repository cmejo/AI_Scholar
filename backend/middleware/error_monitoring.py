"""
Error monitoring and request tracking middleware
"""
import uuid
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger(__name__)


class ErrorMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for error monitoring and request tracking
    """
    
    def __init__(self, app, enable_request_logging: bool = True):
        super().__init__(app)
        self.enable_request_logging = enable_request_logging
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with error monitoring and tracking
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Response: HTTP response
        """
        # Generate request ID if not present
        request_id = request.headers.get('x-request-id') or str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Record request start time
        start_time = time.time()
        
        # Log request if enabled
        if self.enable_request_logging:
            logger.info(
                f"Request started: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "query_params": dict(request.query_params),
                    "client_ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent")
                }
            )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Add request ID to response headers
            response.headers["x-request-id"] = request_id
            response.headers["x-processing-time"] = f"{processing_time:.3f}s"
            
            # Log successful request completion
            if self.enable_request_logging:
                logger.info(
                    f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": str(request.url.path),
                        "status_code": response.status_code,
                        "processing_time": processing_time
                    }
                )
            
            return response
            
        except Exception as e:
            # Calculate processing time for failed requests
            processing_time = time.time() - start_time
            
            # Log request failure
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "processing_time": processing_time,
                    "exception_type": type(e).__name__,
                    "exception_message": str(e)
                },
                exc_info=True
            )
            
            # Re-raise the exception to be handled by global exception handlers
            raise


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting request metrics
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.request_count = 0
        self.error_count = 0
        self.total_processing_time = 0.0
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and collect metrics
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Response: HTTP response
        """
        start_time = time.time()
        self.request_count += 1
        
        try:
            response = await call_next(request)
            
            # Record processing time
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time
            
            # Add metrics to response headers
            response.headers["x-request-count"] = str(self.request_count)
            response.headers["x-avg-processing-time"] = f"{self.total_processing_time / self.request_count:.3f}s"
            
            return response
            
        except Exception as e:
            self.error_count += 1
            
            # Record processing time for failed requests
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time
            
            # Log metrics for failed request
            logger.warning(
                f"Request metrics - Total: {self.request_count}, Errors: {self.error_count}, "
                f"Error Rate: {(self.error_count / self.request_count) * 100:.2f}%"
            )
            
            raise
    
    def get_metrics(self) -> dict:
        """
        Get current request metrics
        
        Returns:
            dict: Current metrics
        """
        return {
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": (self.error_count / self.request_count) * 100 if self.request_count > 0 else 0,
            "average_processing_time": self.total_processing_time / self.request_count if self.request_count > 0 else 0
        }