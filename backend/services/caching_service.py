"""
Advanced caching service for improved performance.
Implements multi-level caching with intelligent cache management.
"""
import hashlib
import json
import time
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
import asyncio
from collections import OrderedDict

from core.redis_client import RedisClient, get_redis_client
from core.config import settings

logger = logging.getLogger(__name__)

class CacheLevel:
    """Cache level enumeration."""
    MEMORY = "memory"
    REDIS = "redis"
    DATABASE = "database"

class CacheStrategy:
    """Cache strategy enumeration."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    ADAPTIVE = "adaptive"  # Adaptive based on usage patterns

class MemoryCache:
    """In-memory cache with configurable eviction strategies."""
    
    def __init__(self, max_size: int = 1000, strategy: str = CacheStrategy.LRU):
        self.max_size = max_size
        self.strategy = strategy
        self.cache = OrderedDict()
        self.access_counts = {}
        self.access_times = {}
        self.hit_count = 0
        self.miss_count = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        if key in self.cache:
            self.hit_count += 1
            self._update_access_stats(key)
            
            if self.strategy == CacheStrategy.LRU:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
            
            return self.cache[key]['value']
        
        self.miss_count += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in memory cache."""
        if key in self.cache:
            # Update existing key
            self.cache[key] = {
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl
            }
            if self.strategy == CacheStrategy.LRU:
                self.cache.move_to_end(key)
        else:
            # Add new key
            if len(self.cache) >= self.max_size:
                self._evict()
            
            self.cache[key] = {
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl
            }
        
        self._update_access_stats(key)
    
    def delete(self, key: str) -> bool:
        """Delete key from memory cache."""
        if key in self.cache:
            del self.cache[key]
            if key in self.access_counts:
                del self.access_counts[key]
            if key in self.access_times:
                del self.access_times[key]
            return True
        return False
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.access_counts.clear()
        self.access_times.clear()
        self.hit_count = 0
        self.miss_count = 0
    
    def _update_access_stats(self, key: str):
        """Update access statistics for the key."""
        self.access_counts[key] = self.access_counts.get(key, 0) + 1
        self.access_times[key] = time.time()
    
    def _evict(self):
        """Evict entries based on strategy."""
        if not self.cache:
            return
        
        if self.strategy == CacheStrategy.LRU:
            # Remove least recently used (first item)
            key_to_remove = next(iter(self.cache))
        elif self.strategy == CacheStrategy.LFU:
            # Remove least frequently used
            key_to_remove = min(self.access_counts.keys(), 
                              key=lambda k: self.access_counts.get(k, 0))
        elif self.strategy == CacheStrategy.TTL:
            # Remove expired entries first, then oldest
            current_time = time.time()
            expired_keys = [
                key for key, data in self.cache.items()
                if data.get('ttl') and (current_time - data['timestamp']) > data['ttl']
            ]
            if expired_keys:
                key_to_remove = expired_keys[0]
            else:
                key_to_remove = min(self.cache.keys(), 
                                  key=lambda k: self.cache[k]['timestamp'])
        else:  # ADAPTIVE
            # Adaptive strategy based on access patterns
            current_time = time.time()
            scores = {}
            for key in self.cache.keys():
                access_count = self.access_counts.get(key, 1)
                last_access = self.access_times.get(key, current_time)
                time_since_access = current_time - last_access
                
                # Score combines frequency and recency
                scores[key] = access_count / (1 + time_since_access)
            
            key_to_remove = min(scores.keys(), key=lambda k: scores[k])
        
        self.delete(key_to_remove)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': hit_rate,
            'strategy': self.strategy
        }

class MultiLevelCache:
    """Multi-level cache with memory, Redis, and database layers."""
    
    def __init__(self, redis_client: Optional[RedisClient] = None):
        self.memory_cache = MemoryCache(max_size=500, strategy=CacheStrategy.ADAPTIVE)
        self.redis_client = redis_client or get_redis_client()
        self.cache_stats = {
            'memory_hits': 0,
            'redis_hits': 0,
            'database_hits': 0,
            'total_requests': 0
        }
    
    async def get(self, key: str, fetch_function: Optional[Callable] = None) -> Optional[Any]:
        """Get value from multi-level cache."""
        self.cache_stats['total_requests'] += 1
        
        # Level 1: Memory cache
        value = self.memory_cache.get(key)
        if value is not None:
            self.cache_stats['memory_hits'] += 1
            return value
        
        # Level 2: Redis cache
        try:
            value = await self.redis_client.get(key)
            if value is not None:
                self.cache_stats['redis_hits'] += 1
                # Promote to memory cache
                self.memory_cache.set(key, value, ttl=300)  # 5 minutes in memory
                return value
        except Exception as e:
            logger.warning(f"Redis cache error for key {key}: {e}")
        
        # Level 3: Database/fetch function
        if fetch_function:
            try:
                value = await fetch_function() if asyncio.iscoroutinefunction(fetch_function) else fetch_function()
                if value is not None:
                    self.cache_stats['database_hits'] += 1
                    # Store in all cache levels
                    await self.set(key, value)
                    return value
            except Exception as e:
                logger.error(f"Fetch function error for key {key}: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in multi-level cache."""
        # Set in memory cache
        self.memory_cache.set(key, value, ttl=min(ttl or 300, 300))  # Max 5 minutes in memory
        
        # Set in Redis cache
        try:
            await self.redis_client.set(key, value, expire=ttl or 3600)  # Default 1 hour in Redis
        except Exception as e:
            logger.warning(f"Redis cache set error for key {key}: {e}")
    
    async def delete(self, key: str):
        """Delete key from all cache levels."""
        self.memory_cache.delete(key)
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            logger.warning(f"Redis cache delete error for key {key}: {e}")
    
    async def clear(self, pattern: Optional[str] = None):
        """Clear cache entries."""
        self.memory_cache.clear()
        # Note: Redis pattern deletion would require additional implementation
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        memory_stats = self.memory_cache.get_stats()
        
        total_requests = self.cache_stats['total_requests']
        if total_requests > 0:
            memory_hit_rate = self.cache_stats['memory_hits'] / total_requests
            redis_hit_rate = self.cache_stats['redis_hits'] / total_requests
            database_hit_rate = self.cache_stats['database_hits'] / total_requests
            overall_cache_hit_rate = (self.cache_stats['memory_hits'] + self.cache_stats['redis_hits']) / total_requests
        else:
            memory_hit_rate = redis_hit_rate = database_hit_rate = overall_cache_hit_rate = 0
        
        return {
            'memory_cache': memory_stats,
            'redis_hits': self.cache_stats['redis_hits'],
            'database_hits': self.cache_stats['database_hits'],
            'total_requests': total_requests,
            'memory_hit_rate': memory_hit_rate,
            'redis_hit_rate': redis_hit_rate,
            'database_hit_rate': database_hit_rate,
            'overall_cache_hit_rate': overall_cache_hit_rate
        }

class CachingService:
    """Main caching service with intelligent cache management."""
    
    def __init__(self, redis_client: Optional[RedisClient] = None):
        self.cache = MultiLevelCache(redis_client)
        self.cache_patterns = {
            'user_profile': {'ttl': 1800, 'prefix': 'user_profile'},
            'document_chunks': {'ttl': 3600, 'prefix': 'doc_chunks'},
            'query_results': {'ttl': 300, 'prefix': 'query'},
            'knowledge_graph': {'ttl': 7200, 'prefix': 'kg'},
            'analytics': {'ttl': 600, 'prefix': 'analytics'},
            'embeddings': {'ttl': 86400, 'prefix': 'embeddings'}
        }
    
    def _generate_cache_key(self, pattern: str, identifier: str, **kwargs) -> str:
        """Generate cache key with pattern and identifier."""
        prefix = self.cache_patterns.get(pattern, {}).get('prefix', pattern)
        
        # Include additional parameters in key
        if kwargs:
            param_str = '_'.join(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            return f"{prefix}:{identifier}:{param_str}"
        
        return f"{prefix}:{identifier}"
    
    def _get_cache_ttl(self, pattern: str) -> int:
        """Get TTL for cache pattern."""
        return self.cache_patterns.get(pattern, {}).get('ttl', 3600)
    
    async def get_user_profile(self, user_id: str, fetch_function: Optional[Callable] = None) -> Optional[Dict[str, Any]]:
        """Get user profile with caching."""
        key = self._generate_cache_key('user_profile', user_id)
        return await self.cache.get(key, fetch_function)
    
    async def set_user_profile(self, user_id: str, profile: Dict[str, Any]):
        """Set user profile in cache."""
        key = self._generate_cache_key('user_profile', user_id)
        ttl = self._get_cache_ttl('user_profile')
        await self.cache.set(key, profile, ttl)
    
    async def get_document_chunks(self, document_id: str, fetch_function: Optional[Callable] = None) -> Optional[List[Dict[str, Any]]]:
        """Get document chunks with caching."""
        key = self._generate_cache_key('document_chunks', document_id)
        return await self.cache.get(key, fetch_function)
    
    async def set_document_chunks(self, document_id: str, chunks: List[Dict[str, Any]]):
        """Set document chunks in cache."""
        key = self._generate_cache_key('document_chunks', document_id)
        ttl = self._get_cache_ttl('document_chunks')
        await self.cache.set(key, chunks, ttl)
    
    async def get_query_result(self, query: str, user_id: str, **params) -> Optional[Dict[str, Any]]:
        """Get cached query result."""
        # Create hash of query and parameters for consistent key
        query_data = {'query': query, 'user_id': user_id, **params}
        query_hash = hashlib.md5(json.dumps(query_data, sort_keys=True).encode()).hexdigest()
        
        key = self._generate_cache_key('query_results', query_hash)
        return await self.cache.get(key)
    
    async def set_query_result(self, query: str, user_id: str, result: Dict[str, Any], **params):
        """Set query result in cache."""
        query_data = {'query': query, 'user_id': user_id, **params}
        query_hash = hashlib.md5(json.dumps(query_data, sort_keys=True).encode()).hexdigest()
        
        key = self._generate_cache_key('query_results', query_hash)
        ttl = self._get_cache_ttl('query_results')
        await self.cache.set(key, result, ttl)
    
    async def get_knowledge_graph_data(self, entity_id: str, depth: int = 1, fetch_function: Optional[Callable] = None) -> Optional[Dict[str, Any]]:
        """Get knowledge graph data with caching."""
        key = self._generate_cache_key('knowledge_graph', entity_id, depth=depth)
        return await self.cache.get(key, fetch_function)
    
    async def set_knowledge_graph_data(self, entity_id: str, data: Dict[str, Any], depth: int = 1):
        """Set knowledge graph data in cache."""
        key = self._generate_cache_key('knowledge_graph', entity_id, depth=depth)
        ttl = self._get_cache_ttl('knowledge_graph')
        await self.cache.set(key, data, ttl)
    
    async def get_analytics_data(self, user_id: str, metric: str, time_range: str, fetch_function: Optional[Callable] = None) -> Optional[Dict[str, Any]]:
        """Get analytics data with caching."""
        key = self._generate_cache_key('analytics', user_id, metric=metric, range=time_range)
        return await self.cache.get(key, fetch_function)
    
    async def set_analytics_data(self, user_id: str, metric: str, time_range: str, data: Dict[str, Any]):
        """Set analytics data in cache."""
        key = self._generate_cache_key('analytics', user_id, metric=metric, range=time_range)
        ttl = self._get_cache_ttl('analytics')
        await self.cache.set(key, data, ttl)
    
    async def get_embeddings(self, content_hash: str, fetch_function: Optional[Callable] = None) -> Optional[List[float]]:
        """Get embeddings with caching."""
        key = self._generate_cache_key('embeddings', content_hash)
        return await self.cache.get(key, fetch_function)
    
    async def set_embeddings(self, content_hash: str, embeddings: List[float]):
        """Set embeddings in cache."""
        key = self._generate_cache_key('embeddings', content_hash)
        ttl = self._get_cache_ttl('embeddings')
        await self.cache.set(key, embeddings, ttl)
    
    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache entries for a user."""
        patterns_to_clear = ['user_profile', 'query_results', 'analytics']
        
        for pattern in patterns_to_clear:
            key = self._generate_cache_key(pattern, user_id)
            await self.cache.delete(key)
    
    async def invalidate_document_cache(self, document_id: str):
        """Invalidate all cache entries for a document."""
        patterns_to_clear = ['document_chunks', 'knowledge_graph']
        
        for pattern in patterns_to_clear:
            key = self._generate_cache_key(pattern, document_id)
            await self.cache.delete(key)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        return self.cache.get_stats()

# Decorator for automatic caching
def cached(pattern: str, ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """Decorator for automatic function result caching."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5('_'.join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            caching_service = CachingService()
            key = caching_service._generate_cache_key(pattern, cache_key)
            
            cached_result = await caching_service.cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            if result is not None:
                cache_ttl = ttl or caching_service._get_cache_ttl(pattern)
                await caching_service.cache.set(key, result, cache_ttl)
            
            return result
        
        return wrapper
    return decorator

# Global caching service instance
caching_service = CachingService()

def get_caching_service() -> CachingService:
    """Get the global caching service instance."""
    return caching_service