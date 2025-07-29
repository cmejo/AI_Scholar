#!/usr/bin/env python3
"""
Test Redis connection and basic functionality
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.redis_client import redis_client, store_conversation_context, get_conversation_context
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_redis_connection():
    """Test Redis connection and basic operations"""
    try:
        logger.info("Testing Redis connection...")
        
        # Connect to Redis
        await redis_client.connect()
        
        # Test basic set/get operations
        test_key = "test_key"
        test_value = {"message": "Hello Redis!", "timestamp": "2025-07-18"}
        
        logger.info("Testing basic set/get operations...")
        success = await redis_client.set(test_key, test_value, expire=60)
        if success:
            logger.info("✓ Set operation successful")
        else:
            logger.error("✗ Set operation failed")
            return False
        
        retrieved_value = await redis_client.get(test_key)
        if retrieved_value == test_value:
            logger.info("✓ Get operation successful")
        else:
            logger.error(f"✗ Get operation failed. Expected: {test_value}, Got: {retrieved_value}")
            return False
        
        # Test conversation context functions
        logger.info("Testing conversation context functions...")
        conversation_id = "test_conversation_123"
        context_data = {
            "short_term_memory": ["User asked about AI", "System responded about machine learning"],
            "active_entities": ["AI", "machine learning", "neural networks"],
            "context_summary": "Discussion about artificial intelligence concepts"
        }
        
        success = await store_conversation_context(conversation_id, context_data)
        if success:
            logger.info("✓ Store conversation context successful")
        else:
            logger.error("✗ Store conversation context failed")
            return False
        
        retrieved_context = await get_conversation_context(conversation_id)
        if retrieved_context and "short_term_memory" in retrieved_context:
            logger.info("✓ Get conversation context successful")
        else:
            logger.error("✗ Get conversation context failed")
            return False
        
        # Test hash operations
        logger.info("Testing hash operations...")
        hash_name = "test_hash"
        hash_data = {
            "query_count": 5,
            "response_times": [0.5, 0.7, 0.3, 0.9, 0.6],
            "satisfaction_scores": [4, 5, 3, 4, 5]
        }
        
        success = await redis_client.hset(hash_name, hash_data)
        if success:
            logger.info("✓ Hash set operation successful")
        else:
            logger.error("✗ Hash set operation failed")
            return False
        
        retrieved_hash = await redis_client.hgetall(hash_name)
        if retrieved_hash and "query_count" in retrieved_hash:
            logger.info("✓ Hash get operation successful")
        else:
            logger.error("✗ Hash get operation failed")
            return False
        
        # Clean up test data
        await redis_client.delete(test_key)
        await redis_client.delete(f"conversation_context:{conversation_id}")
        await redis_client.delete(hash_name)
        
        logger.info("✓ All Redis tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Redis test failed: {e}")
        return False
    finally:
        await redis_client.disconnect()

async def main():
    """Main test function"""
    logger.info("Starting Redis connection tests...")
    
    success = await test_redis_connection()
    if success:
        logger.info("All Redis tests completed successfully!")
        sys.exit(0)
    else:
        logger.error("Redis tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())