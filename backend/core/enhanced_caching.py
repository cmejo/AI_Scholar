"""
Enhanced caching system for AI Scholar
Provides multi-level caching with Redis, in-memory, and application-level caches
"""
import asyncio
import hashlib
import json
import pickle
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass
import logging

try:
    import redis.asyncio as redis
    from cachetools import TTLCache, LRUCache
except ImportError:
    redis = None
    TTLCache = None
    LRUCache = None

logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """Cache configuration"""
    ttl: int = 3600  # Time to live in seconds
    max_size: int = 1000  # Maximum cache size
    serialize_method: str = 'json'  # 'json', 'pickle', 'string'
    key_prefix: str = ''
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class MultiLevelCache:
    """Multi-level caching system with L1 (memory), L2 (TTL), and L3 (Redis)"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        
        # L1 Cache: In-memory LRU (fastest access)
        if LRUCache:
            self.l1_cache = LRUCache(maxsize=500)
        else:
            self.l1_cache = {}
        
        # L2 Cache: In-memory with TTL
        if TTLCache:
            self.l2_cache = TTLCache(maxsize=2000, ttl=3600)
        else:
            self.l2_cache = {}
        
        # L3 Cache: Redis (persistent across restarts)
        # Redis client is L3
        
        self.stats = {
            'l1_hits': 0,
            'l2_hits': 0,
            'l3_hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0
        }
    
    async def get(self, key: str, config: CacheConfig = None) -> Optional[Any]:
        """Get value from cache with fallback through levels"""
        config = config or CacheConfig()
        cache_key = f"{config.key_prefix}{key}"
        
        try:
            # L1 Cache check (fastest)
            if cache_key in self.l1_cache:
                self.stats['l1_hits'] += 1
                return self.l1_cache[cache_key]
            
            # L2 Cache check
            if cache_key in self.l2_cache:
                value = self.l2_cache[cache_key]
                # Promote to L1
                self.l1_cache[cache_key] = value
                self.stats['l2_hits'] += 1
                return value
            
            # L3 Cache (Redis) check
            if self.redis:
                try:
                    redis_value = await self.redis.get(cache_key)
                    if redis_value:
                        value = self._deserialize(redis_value, config.serialize_method)
                        # Promote to L2 and L1
                        self.l2_cache[cache_key] = value
                        self.l1_cache[cache_key] = value
                        self.stats['l3_hits'] += 1
                        return value
                except Exception as e:
                    logger.warning(f"Redis cache error for key {cache_key}: {e}")
                    self.stats['errors'] += 1
            
            self.stats['misses'] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {cache_key}: {e}")
            self.stats['errors'] += 1
            return None
    
    async def set(self, key: str, value: Any, config: CacheConfig = None) -> bool:
        """Set value in all cache levels"""
        config = config or CacheConfig()
        cache_key = f"{config.key_prefix}{key}"
        
        try:
            # Set in L1 and L2
            self.l1_cache[cache_key] = value
            self.l2_cache[cache_key] = value
            
            # Set in Redis with TTL
            if self.redis:
                try:
                    serialized_value = self._serialize(value, config.serialize_method)
                    await self.redis.setex(cache_key, config.ttl, serialized_value)
                    
                    # Add tags for cache invalidation
                    if config.tags:
                        for tag in config.tags:
                            await self.redis.sadd(f"tag:{tag}", cache_key)
                            # Set expiration for tag sets too
                            await self.redis.expire(f"tag:{tag}", config.ttl + 3600)
                            
                except Exception as e:
                    logger.warning(f"Redis cache set error for key {cache_key}: {e}")
                    self.stats['errors'] += 1
            
            self.stats['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {cache_key}: {e}")
            self.stats['errors'] += 1
            return False
    
    async def delete(self, key: str, config: CacheConfig = None) -> bool:
        """Delete from all cache levels"""
        config = config or CacheConfig()
        cache_key = f"{config.key_prefix}{key}"
        
        try:
            # Remove from L1 and L2
            self.l1_cache.pop(cache_key, None)
            self.l2_cache.pop(cache_key, None)
            
            # Remove from Redis
            if self.redis:
                try:
                    await self.redis.delete(cache_key)
                except Exception as e:
                    logger.warning(f"Redis cache delete error for key {cache_key}: {e}")
                    self.stats['errors'] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for key {cache_key}: {e}")
            self.stats['errors'] += 1
            return False
    
    async def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all cache entries with a specific tag"""
        invalidated_count = 0
        
        if not self.redis:
            return invalidated_count
        
        try:
            # Get all keys with this tag
            keys = await self.redis.smembers(f"tag:{tag}")
            if keys:
                # Remove from all levels
                for key in keys:
                    key_str = key.decode() if isinstance(key, bytes) else key
                    self.l1_cache.pop(key_str, None)
                    self.l2_cache.pop(key_str, None)
                
                # Remove from Redis
                await self.redis.delete(*keys)
                await self.redis.delete(f"tag:{tag}")
                
                invalidated_count = len(keys)
                logger.info(f"Invalidated {invalidated_count} cache entries with tag '{tag}'")
                
        except Exception as e:
            logger.error(f"Tag invalidation error for tag '{tag}': {e}")
            self.stats['errors'] += 1
        
        return invalidated_count
    
    async def clear_all(self) -> bool:
        """Clear all cache levels"""
        try:
            # Clear L1 and L2
            self.l1_cache.clear()
            self.l2_cache.clear()
            
            # Clear Redis (only our keys)
            if self.redis:
                try:
                    # This is dangerous in production - only clear our prefixed keys
                    # In a real implementation, you'd want to track your keys
                    logger.warning("Redis cache clear not implemented for safety")
                except Exception as e:
                    logger.warning(f"Redis cache clear error: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def _serialize(self, value: Any, method: str) -> Union[str, bytes]:
        """Serialize value for storage"""
        try:
            if method == 'json':
                return json.dumps(value, default=str)
            elif method == 'pickle':
                return pickle.dumps(value)
            else:
                return str(value)
        except Exception as e:
            logger.error(f"Serialization error with method '{method}': {e}")
            return json.dumps(str(value))
    
    def _deserialize(self, value: Union[str, bytes], method: str) -> Any:
        """Deserialize value from storage"""
        try:
            if method == 'json':
                return json.loads(value)
            elif method == 'pickle':
                return pickle.loads(value)
            else:
                return value.decode() if isinstance(value, bytes) else value
        except Exception as e:
            logger.error(f"Deserialization error with method '{method}': {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = sum([
            self.stats['l1_hits'], 
            self.stats['l2_hits'], 
            self.stats['l3_hits'], 
            self.stats['misses']
        ])
        
        hit_rate = (total_requests - self.stats['misses']) / total_requests if total_requests > 0 else 0
        
        return {
            **self.stats,
            'total_requests': total_requests,
            'hit_rate': round(hit_rate, 3),
            'l1_size': len(self.l1_cache),
            'l2_size': len(self.l2_cache),
            'redis_available': self.redis is not None
        }
    
    def reset_stats(self):
        """Reset cache statistics"""
        self.stats = {
            'l1_hits': 0,
            'l2_hits': 0,
            'l3_hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0
        }

# Cache decorators
def cached(config: CacheConfig = None):
    """Decorator for caching function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_data = {
                'func': func.__name__,
                'module': func.__module__,
                'args': args,
                'kwargs': kwargs
            }
            
            # Create a hash of the key data
            key_str = json.dumps(key_data, sort_keys=True, default=str)
            key_hash = hashlib.md5(key_str.encode()).hexdigest()
            
            # Try to get from cache
            if cache_instance:
                cached_result = await cache_instance.get(key_hash, config)
                if cached_result is not None:
                    return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            
            if cache_instance:
                await cache_instance.set(key_hash, result, config)
            
            return result
        return wrapper
    return decorator

def cache_with_tags(*tags: str, ttl: int = 3600):
    """Decorator for caching with tags for easy invalidation"""
    config = CacheConfig(ttl=ttl, tags=list(tags))
    return cached(config)

# Global cache instance
cache_instance: Optional[MultiLevelCache] = None

def init_cache(redis_client: Optional[redis.Redis] = None):
    """Initialize global cache instance"""
    global cache_instance
    cache_instance = MultiLevelCache(redis_client)
    logger.info("Cache system initialized")

def get_cache() -> Optional[MultiLevelCache]:
    """Get the global cache instance"""
    return cache_instance

# Usage examples and common patterns
@cache_with_tags("embeddings", "documents", ttl=1800)
async def get_document_embeddings(document_id: str) -> List[float]:
    """Cached embedding generation"""
    # This would be your actual embedding computation
    logger.info(f"Computing embeddings for document {document_id}")
    # Simulate expensive computation
    await asyncio.sleep(0.1)
    return [0.1, 0.2, 0.3]  # Mock embeddings

@cache_with_tags("search", "documents", ttl=3600)
async def search_documents(query: str, user_id: str, limit: int = 10) -> List[Dict]:
    """Cached document search"""
    logger.info(f"Searching documents for query: {query}")
    # This would be your actual search logic
    await asyncio.sleep(0.05)
    return [{"id": "doc1", "title": "Sample Document"}]  # Mock results

@cached(CacheConfig(ttl=7200, key_prefix="user:", tags=["users"]))
async def get_user_profile(user_id: str) -> Dict:
    """Cached user profile retrieval"""
    logger.info(f"Loading user profile for {user_id}")
    # This would be your actual user loading logic
    return {"id": user_id, "name": "Sample User"}

# Cache warming utilities
class CacheWarmer:
    """Utility for warming up caches with commonly accessed data"""
    
    def __init__(self, cache: MultiLevelCache):
        self.cache = cache
    
    async def warm_embeddings_cache(self, document_ids: List[str]):
        """Pre-compute and cache embeddings for documents"""
        logger.info(f"Warming embeddings cache for {len(document_ids)} documents")
        
        tasks = []
        for doc_id in document_ids:
            task = get_document_embeddings(doc_id)
            tasks.append(task)
        
        # Execute in batches to avoid overwhelming the system
        batch_size = 10
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            await asyncio.gather(*batch, return_exceptions=True)
            await asyncio.sleep(0.1)  # Small delay between batches
    
    async def warm_search_cache(self, common_queries: List[str], user_id: str):
        """Pre-compute and cache common search queries"""
        logger.info(f"Warming search cache for {len(common_queries)} queries")
        
        for query in common_queries:
            try:
                await search_documents(query, user_id)
                await asyncio.sleep(0.05)  # Small delay between queries
            except Exception as e:
                logger.warning(f"Failed to warm cache for query '{query}': {e}")

# Cache monitoring and maintenance
class CacheMonitor:
    """Monitor cache performance and health"""
    
    def __init__(self, cache: MultiLevelCache):
        self.cache = cache
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive cache health report"""
        stats = self.cache.get_stats()
        
        # Calculate health metrics
        hit_rate = stats['hit_rate']
        error_rate = stats['errors'] / max(stats['total_requests'], 1)
        
        health_score = 10.0
        issues = []
        
        if hit_rate < 0.5:
            health_score -= 3
            issues.append(f"Low hit rate: {hit_rate:.1%}")
        
        if error_rate > 0.05:
            health_score -= 2
            issues.append(f"High error rate: {error_rate:.1%}")
        
        if stats['l1_size'] > 400:  # Near L1 limit
            health_score -= 1
            issues.append("L1 cache near capacity")
        
        return {
            'health_score': max(0, health_score),
            'stats': stats,
            'issues': issues,
            'recommendations': self._get_recommendations(stats, issues)
        }
    
    def _get_recommendations(self, stats: Dict, issues: List[str]) -> List[str]:
        """Generate recommendations based on cache performance"""
        recommendations = []
        
        if stats['hit_rate'] < 0.5:
            recommendations.append("Consider increasing cache TTL or size")
        
        if stats['errors'] > 0:
            recommendations.append("Check Redis connectivity and error logs")
        
        if stats['l1_size'] > 400:
            recommendations.append("Consider increasing L1 cache size")
        
        if not recommendations:
            recommendations.append("Cache performance is healthy")
        
        return recommendations

if __name__ == "__main__":
    # Example usage and testing
    async def test_cache():
        # Initialize cache without Redis for testing
        init_cache()
        
        if cache_instance:
            # Test basic operations
            await cache_instance.set("test_key", "test_value")
            value = await cache_instance.get("test_key")
            print(f"Cache test: {value}")
            
            # Test decorated functions
            result1 = await get_document_embeddings("doc123")
            result2 = await get_document_embeddings("doc123")  # Should be cached
            
            print(f"Embeddings (first call): {result1}")
            print(f"Embeddings (cached): {result2}")
            
            # Print stats
            stats = cache_instance.get_stats()
            print(f"Cache stats: {stats}")
            
            # Test cache monitor
            monitor = CacheMonitor(cache_instance)
            health = monitor.get_health_report()
            print(f"Cache health: {health}")
    
    # Run test
    asyncio.run(test_cache())