"""
Performance monitoring and optimization middleware.
"""
import time
import logging
import asyncio
from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import json

from services.monitoring_service import get_performance_monitor, get_performance_benchmark
from services.caching_service import get_caching_service
from core.database_optimization import db_optimizer

logger = logging.getLogger(__name__)

class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring and optimization."""
    
    def __init__(self, app, enable_detailed_logging: bool = False):
        super().__init__(app)
        self.enable_detailed_logging = enable_detailed_logging
        self.performance_monitor = get_performance_monitor()
        self.performance_benchmark = get_performance_benchmark()
        self.caching_service = get_caching_service()
        
        # Track request patterns
        self.request_patterns = {}
        self.slow_requests = []
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with performance monitoring."""
        start_time = time.time()
        request_id = f"{request.method}_{request.url.path}_{int(start_time * 1000)}"
        
        # Extract request metadata
        request_metadata = {
            'method': request.method,
            'path': request.url.path,
            'query_params': str(request.query_params),
            'user_agent': request.headers.get('user-agent', ''),
            'content_length': request.headers.get('content-length', 0),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add request tracking
        self._track_request_pattern(request.url.path, request.method)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Record performance metrics
            await self._record_performance_metrics(
                request_id, request_metadata, response, response_time
            )
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            response.headers["X-Request-ID"] = request_id
            
            # Log slow requests
            if response_time > 2.0:  # 2 second threshold
                await self._log_slow_request(request_metadata, response_time, response.status_code)
            
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            
            # Record error metrics
            await self._record_error_metrics(request_id, request_metadata, str(e), response_time)
            
            logger.error(f"Request {request_id} failed after {response_time:.3f}s: {e}")
            raise
    
    def _track_request_pattern(self, path: str, method: str):
        """Track request patterns for optimization insights."""
        pattern_key = f"{method}:{path}"
        
        if pattern_key not in self.request_patterns:
            self.request_patterns[pattern_key] = {
                'count': 0,
                'first_seen': datetime.now(),
                'last_seen': datetime.now(),
                'total_response_time': 0.0,
                'error_count': 0
            }
        
        self.request_patterns[pattern_key]['count'] += 1
        self.request_patterns[pattern_key]['last_seen'] = datetime.now()
    
    async def _record_performance_metrics(self, request_id: str, request_metadata: Dict[str, Any], 
                                        response: Response, response_time: float):
        """Record performance metrics for monitoring."""
        try:
            # Record benchmark data
            endpoint = request_metadata['path']
            
            if '/api/chat/' in endpoint:
                self.performance_benchmark.record_performance(
                    'query_response_time', response_time
                )
            elif '/api/documents/upload' in endpoint:
                self.performance_benchmark.record_performance(
                    'document_processing_time', response_time
                )
            
            # Update request pattern metrics
            pattern_key = f"{request_metadata['method']}:{endpoint}"
            if pattern_key in self.request_patterns:
                self.request_patterns[pattern_key]['total_response_time'] += response_time
                
                if response.status_code >= 400:
                    self.request_patterns[pattern_key]['error_count'] += 1
            
            # Log detailed metrics if enabled
            if self.enable_detailed_logging:
                logger.info(f"Request {request_id}: {response_time:.3f}s, "
                           f"Status: {response.status_code}, "
                           f"Path: {endpoint}")
        
        except Exception as e:
            logger.warning(f"Failed to record performance metrics: {e}")
    
    async def _record_error_metrics(self, request_id: str, request_metadata: Dict[str, Any], 
                                  error: str, response_time: float):
        """Record error metrics for monitoring."""
        try:
            # Update request pattern error count
            pattern_key = f"{request_metadata['method']}:{request_metadata['path']}"
            if pattern_key in self.request_patterns:
                self.request_patterns[pattern_key]['error_count'] += 1
            
            # Log error details
            logger.error(f"Request {request_id} error: {error}, "
                        f"Response time: {response_time:.3f}s, "
                        f"Path: {request_metadata['path']}")
        
        except Exception as e:
            logger.warning(f"Failed to record error metrics: {e}")
    
    async def _log_slow_request(self, request_metadata: Dict[str, Any], response_time: float, status_code: int):
        """Log slow requests for analysis."""
        slow_request = {
            'path': request_metadata['path'],
            'method': request_metadata['method'],
            'response_time': response_time,
            'status_code': status_code,
            'timestamp': request_metadata['timestamp'],
            'query_params': request_metadata['query_params']
        }
        
        self.slow_requests.append(slow_request)
        
        # Keep only last 100 slow requests
        if len(self.slow_requests) > 100:
            self.slow_requests = self.slow_requests[-100:]
        
        logger.warning(f"Slow request detected: {request_metadata['method']} {request_metadata['path']} "
                      f"took {response_time:.3f}s (Status: {status_code})")
    
    def get_request_patterns(self) -> Dict[str, Any]:
        """Get request pattern analysis."""
        patterns_analysis = {}
        
        for pattern_key, data in self.request_patterns.items():
            avg_response_time = (data['total_response_time'] / data['count']) if data['count'] > 0 else 0
            error_rate = (data['error_count'] / data['count']) if data['count'] > 0 else 0
            
            patterns_analysis[pattern_key] = {
                'request_count': data['count'],
                'average_response_time': avg_response_time,
                'error_rate': error_rate,
                'first_seen': data['first_seen'].isoformat(),
                'last_seen': data['last_seen'].isoformat(),
                'total_errors': data['error_count']
            }
        
        return patterns_analysis
    
    def get_slow_requests(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent slow requests."""
        return sorted(self.slow_requests, key=lambda x: x['response_time'], reverse=True)[:limit]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary from middleware data."""
        total_requests = sum(data['count'] for data in self.request_patterns.values())
        total_errors = sum(data['error_count'] for data in self.request_patterns.values())
        
        if total_requests == 0:
            return {
                'total_requests': 0,
                'error_rate': 0,
                'average_response_time': 0,
                'slow_requests_count': len(self.slow_requests)
            }
        
        total_response_time = sum(data['total_response_time'] for data in self.request_patterns.values())
        average_response_time = total_response_time / total_requests
        error_rate = total_errors / total_requests
        
        return {
            'total_requests': total_requests,
            'error_rate': error_rate,
            'average_response_time': average_response_time,
            'slow_requests_count': len(self.slow_requests),
            'unique_endpoints': len(self.request_patterns)
        }

class CacheOptimizationMiddleware(BaseHTTPMiddleware):
    """Middleware for intelligent caching optimization."""
    
    def __init__(self, app):
        super().__init__(app)
        self.caching_service = get_caching_service()
        self.cache_patterns = {
            '/api/analytics/dashboard': {'ttl': 300, 'cache_key_params': ['time_range']},
            '/api/knowledge-graph': {'ttl': 1800, 'cache_key_params': ['document_id', 'max_depth']},
            '/api/search/semantic': {'ttl': 600, 'cache_key_params': ['query', 'limit']},
            '/api/documents': {'ttl': 900, 'cache_key_params': []},
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with intelligent caching."""
        # Check if this endpoint should be cached
        cache_config = self._get_cache_config(request.url.path)
        
        if not cache_config or request.method != 'GET':
            # No caching for this endpoint or non-GET requests
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request, cache_config)
        
        # Try to get from cache
        cached_response = await self.caching_service.cache.get(cache_key)
        
        if cached_response:
            # Return cached response
            response = Response(
                content=cached_response['content'],
                status_code=cached_response['status_code'],
                headers=cached_response.get('headers', {}),
                media_type=cached_response.get('media_type', 'application/json')
            )
            response.headers["X-Cache"] = "HIT"
            return response
        
        # Process request normally
        response = await call_next(request)
        
        # Cache successful responses
        if 200 <= response.status_code < 300:
            await self._cache_response(cache_key, response, cache_config['ttl'])
            response.headers["X-Cache"] = "MISS"
        
        return response
    
    def _get_cache_config(self, path: str) -> Optional[Dict[str, Any]]:
        """Get cache configuration for a path."""
        for pattern, config in self.cache_patterns.items():
            if pattern in path:
                return config
        return None
    
    def _generate_cache_key(self, request: Request, cache_config: Dict[str, Any]) -> str:
        """Generate cache key for request."""
        key_parts = [request.url.path]
        
        # Add specified query parameters
        for param in cache_config.get('cache_key_params', []):
            if param in request.query_params:
                key_parts.append(f"{param}:{request.query_params[param]}")
        
        # Add user context if available (from headers or auth)
        user_id = request.headers.get('X-User-ID', 'anonymous')
        key_parts.append(f"user:{user_id}")
        
        return "http_cache:" + "_".join(key_parts)
    
    async def _cache_response(self, cache_key: str, response: Response, ttl: int):
        """Cache response data."""
        try:
            # Read response content
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Prepare cache data
            cache_data = {
                'content': response_body.decode('utf-8'),
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'media_type': response.media_type
            }
            
            # Store in cache
            await self.caching_service.cache.set(cache_key, cache_data, ttl)
            
            # Recreate response with same content
            response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=response.headers,
                media_type=response.media_type
            )
            
        except Exception as e:
            logger.warning(f"Failed to cache response for key {cache_key}: {e}")

class DatabaseOptimizationMiddleware(BaseHTTPMiddleware):
    """Middleware for database query optimization."""
    
    def __init__(self, app):
        super().__init__(app)
        self.query_tracker = {}
        self.slow_query_threshold = 1.0  # 1 second
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with database optimization tracking."""
        # Track database-heavy endpoints
        if self._is_database_heavy_endpoint(request.url.path):
            start_time = time.time()
            
            response = await call_next(request)
            
            execution_time = time.time() - start_time
            
            # Record query performance
            db_optimizer.record_query_performance(
                query_id=f"{request.method}_{request.url.path}_{int(start_time)}",
                execution_time=execution_time,
                query=f"{request.method} {request.url.path}"
            )
            
            # Add database timing header
            response.headers["X-DB-Time"] = f"{execution_time:.3f}s"
            
            return response
        
        return await call_next(request)
    
    def _is_database_heavy_endpoint(self, path: str) -> bool:
        """Check if endpoint is database-heavy."""
        db_heavy_patterns = [
            '/api/documents',
            '/api/chat/',
            '/api/analytics/',
            '/api/knowledge-graph',
            '/api/search/'
        ]
        
        return any(pattern in path for pattern in db_heavy_patterns)

# Global middleware instances
performance_middleware = None
cache_middleware = None
db_middleware = None

def get_performance_middleware(enable_detailed_logging: bool = False):
    """Get performance middleware instance."""
    global performance_middleware
    if performance_middleware is None:
        performance_middleware = PerformanceMiddleware(None, enable_detailed_logging)
    return performance_middleware

def get_cache_middleware():
    """Get cache middleware instance."""
    global cache_middleware
    if cache_middleware is None:
        cache_middleware = CacheOptimizationMiddleware(None)
    return cache_middleware

def get_database_middleware():
    """Get database middleware instance."""
    global db_middleware
    if db_middleware is None:
        db_middleware = DatabaseOptimizationMiddleware(None)
    return db_middleware