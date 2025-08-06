"""
Redis client configuration and utilities for caching and session management
"""
import json
import redis.asyncio as redis
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import logging

from core.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client for caching and session management"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis server"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis server"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set a key-value pair with optional expiration"""
        if not self.redis_client:
            return False
        
        try:
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            result = await self.redis_client.set(key, serialized_value, ex=expire)
            return result
        except Exception as e:
            logger.error(f"Error setting Redis key {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value is None:
                return None
            
            # Try to deserialize JSON, fallback to string
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Error getting Redis key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key"""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting Redis key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error checking Redis key existence {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for a key"""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.expire(key, seconds)
            return result
        except Exception as e:
            logger.error(f"Error setting expiration for Redis key {key}: {e}")
            return False
    
    async def hset(self, name: str, mapping: Dict[str, Any]) -> bool:
        """Set hash fields"""
        if not self.redis_client:
            return False
        
        try:
            # Serialize values that are not strings
            serialized_mapping = {}
            for k, v in mapping.items():
                serialized_mapping[k] = json.dumps(v) if not isinstance(v, str) else v
            
            result = await self.redis_client.hset(name, mapping=serialized_mapping)
            return result > 0
        except Exception as e:
            logger.error(f"Error setting Redis hash {name}: {e}")
            return False
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Get hash field value"""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.hget(name, key)
            if value is None:
                return None
            
            # Try to deserialize JSON, fallback to string
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Error getting Redis hash field {name}:{key}: {e}")
            return None
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all hash fields"""
        if not self.redis_client:
            return {}
        
        try:
            result = await self.redis_client.hgetall(name)
            # Try to deserialize JSON values
            deserialized_result = {}
            for k, v in result.items():
                try:
                    deserialized_result[k] = json.loads(v)
                except json.JSONDecodeError:
                    deserialized_result[k] = v
            return deserialized_result
        except Exception as e:
            logger.error(f"Error getting Redis hash {name}: {e}")
            return {}
    
    async def hdel(self, name: str, *keys: str) -> bool:
        """Delete hash fields"""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.hdel(name, *keys)
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting Redis hash fields {name}: {e}")
            return False
    
    async def lpush(self, key: str, *values: Any) -> int:
        """Push values to the left of a list"""
        if not self.redis_client:
            return 0
        
        try:
            # Serialize values that are not strings
            serialized_values = []
            for value in values:
                if isinstance(value, str):
                    serialized_values.append(value)
                else:
                    serialized_values.append(json.dumps(value))
            
            result = await self.redis_client.lpush(key, *serialized_values)
            return result
        except Exception as e:
            logger.error(f"Error pushing to Redis list {key}: {e}")
            return 0
    
    async def lrange(self, key: str, start: int, end: int) -> List[Any]:
        """Get a range of elements from a list"""
        if not self.redis_client:
            return []
        
        try:
            result = await self.redis_client.lrange(key, start, end)
            # Try to deserialize JSON values
            deserialized_result = []
            for value in result:
                try:
                    deserialized_result.append(json.loads(value))
                except json.JSONDecodeError:
                    deserialized_result.append(value)
            return deserialized_result
        except Exception as e:
            logger.error(f"Error getting Redis list range {key}: {e}")
            return []
    
    async def llen(self, key: str) -> int:
        """Get the length of a list"""
        if not self.redis_client:
            return 0
        
        try:
            result = await self.redis_client.llen(key)
            return result
        except Exception as e:
            logger.error(f"Error getting Redis list length {key}: {e}")
            return 0
    
    async def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim a list to the specified range"""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.ltrim(key, start, end)
            return result
        except Exception as e:
            logger.error(f"Error trimming Redis list {key}: {e}")
            return False
    
    async def brpop(self, key: str, timeout: int = 0) -> Optional[tuple]:
        """Block and pop from the right of a list"""
        if not self.redis_client:
            return None
        
        try:
            result = await self.redis_client.brpop(key, timeout=timeout)
            if result:
                # result is (key, value)
                key_name, value = result
                try:
                    deserialized_value = json.loads(value)
                except json.JSONDecodeError:
                    deserialized_value = value
                return (key_name, deserialized_value)
            return None
        except Exception as e:
            logger.error(f"Error blocking pop from Redis list {key}: {e}")
            return None
    
    async def sadd(self, key: str, *values: Any) -> int:
        """Add members to a set"""
        if not self.redis_client:
            return 0
        
        try:
            # Serialize values that are not strings
            serialized_values = []
            for value in values:
                if isinstance(value, str):
                    serialized_values.append(value)
                else:
                    serialized_values.append(json.dumps(value))
            
            result = await self.redis_client.sadd(key, *serialized_values)
            return result
        except Exception as e:
            logger.error(f"Error adding to Redis set {key}: {e}")
            return 0
    
    async def smembers(self, key: str) -> set:
        """Get all members of a set"""
        if not self.redis_client:
            return set()
        
        try:
            result = await self.redis_client.smembers(key)
            # Try to deserialize JSON values
            deserialized_result = set()
            for value in result:
                try:
                    deserialized_result.add(json.loads(value))
                except json.JSONDecodeError:
                    deserialized_result.add(value)
            return deserialized_result
        except Exception as e:
            logger.error(f"Error getting Redis set members {key}: {e}")
            return set()
    
    async def srem(self, key: str, *values: Any) -> int:
        """Remove members from a set"""
        if not self.redis_client:
            return 0
        
        try:
            # Serialize values that are not strings
            serialized_values = []
            for value in values:
                if isinstance(value, str):
                    serialized_values.append(value)
                else:
                    serialized_values.append(json.dumps(value))
            
            result = await self.redis_client.srem(key, *serialized_values)
            return result
        except Exception as e:
            logger.error(f"Error removing from Redis set {key}: {e}")
            return 0
    
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching a pattern"""
        if not self.redis_client:
            return []
        
        try:
            result = await self.redis_client.keys(pattern)
            return result
        except Exception as e:
            logger.error(f"Error getting Redis keys with pattern {pattern}: {e}")
            return []
    
    async def setex(self, key: str, seconds: int, value: Any) -> bool:
        """Set key with expiration time"""
        if not self.redis_client:
            return False
        
        try:
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            result = await self.redis_client.setex(key, seconds, serialized_value)
            return result
        except Exception as e:
            logger.error(f"Error setting Redis key with expiration {key}: {e}")
            return False
    
    async def ping(self) -> bool:
        """Ping Redis server"""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.ping()
            return result
        except Exception as e:
            logger.error(f"Error pinging Redis: {e}")
            return False
    
    async def publish(self, channel: str, message: Any) -> int:
        """Publish message to a channel"""
        if not self.redis_client:
            return 0
        
        try:
            serialized_message = json.dumps(message) if not isinstance(message, str) else message
            result = await self.redis_client.publish(channel, serialized_message)
            return result
        except Exception as e:
            logger.error(f"Error publishing to Redis channel {channel}: {e}")
            return 0
    
    def pubsub(self):
        """Get pubsub instance"""
        if not self.redis_client:
            return None
        
        try:
            return self.redis_client.pubsub()
        except Exception as e:
            logger.error(f"Error getting Redis pubsub: {e}")
            return None
    
    async def flushdb(self) -> bool:
        """Flush current database"""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.flushdb()
            return result
        except Exception as e:
            logger.error(f"Error flushing Redis database: {e}")
            return False

# Global Redis client instance
redis_client = RedisClient()

def get_redis_client() -> RedisClient:
    """Get the global Redis client instance"""
    return redis_client

# Convenience functions for specific use cases

async def store_conversation_context(conversation_id: str, context: Dict[str, Any], expire_seconds: int = 3600):
    """Store conversation context in Redis"""
    key = f"conversation_context:{conversation_id}"
    context["last_updated"] = datetime.now().isoformat()
    return await redis_client.set(key, context, expire=expire_seconds)

async def get_conversation_context(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Get conversation context from Redis"""
    key = f"conversation_context:{conversation_id}"
    return await redis_client.get(key)

async def store_user_session(user_id: str, session_data: Dict[str, Any], expire_seconds: int = 1800):
    """Store user session data in Redis"""
    key = f"user_session:{user_id}"
    session_data["last_activity"] = datetime.now().isoformat()
    return await redis_client.set(key, session_data, expire=expire_seconds)

async def get_user_session(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user session data from Redis"""
    key = f"user_session:{user_id}"
    return await redis_client.get(key)

async def store_analytics_buffer(user_id: str, date: str, analytics_data: Dict[str, Any]):
    """Store real-time analytics data in Redis"""
    key = f"analytics_buffer:{user_id}:{date}"
    return await redis_client.hset(key, analytics_data)

async def get_analytics_buffer(user_id: str, date: str) -> Dict[str, Any]:
    """Get analytics buffer data from Redis"""
    key = f"analytics_buffer:{user_id}:{date}"
    return await redis_client.hgetall(key)

async def cache_query_result(query_hash: str, result: Dict[str, Any], expire_seconds: int = 300):
    """Cache query results for faster retrieval"""
    key = f"query_cache:{query_hash}"
    return await redis_client.set(key, result, expire=expire_seconds)

async def get_cached_query_result(query_hash: str) -> Optional[Dict[str, Any]]:
    """Get cached query result"""
    key = f"query_cache:{query_hash}"
    return await redis_client.get(key)

async def store_user_preferences(user_id: str, preferences: Dict[str, Any]):
    """Store user preferences in Redis for quick access"""
    key = f"user_preferences:{user_id}"
    return await redis_client.set(key, preferences)

async def get_user_preferences(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user preferences from Redis"""
    key = f"user_preferences:{user_id}"
    return await redis_client.get(key)