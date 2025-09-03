"""
AI-Specific Caching Manager for AI Scholar
Optimizes caching for AI operations like embeddings, RAG responses, and model outputs
"""

import asyncio
import hashlib
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

from core.enhanced_caching import cache_with_tags, CacheConfig, get_cache

logger = logging.getLogger(__name__)

@dataclass
class AIOperationMetrics:
    """Metrics for AI operations"""
    operation_type: str
    execution_time: float
    cache_hit: bool
    model_used: str
    input_size: int
    timestamp: float

class AICacheManager:
    """Specialized caching for AI operations"""
    
    def __init__(self):
        self.cache = get_cache()
        self.metrics = []
        self.model_versions = {
            "embedding": "sentence-transformers/all-MiniLM-L6-v2",
            "llm": "gpt-4-turbo-preview",
            "summarization": "facebook/bart-large-cnn"
        }
    
    def _generate_cache_key(self, operation: str, inputs: Dict[str, Any], model: str) -> str:
        """Generate deterministic cache key for AI operations"""
        key_data = {
            "operation": operation,
            "model": model,
            "model_version": self.model_versions.get(model, "unknown"),
            "inputs": inputs
        }
        
        # Create hash of the key data
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    @cache_with_tags("embeddings", "ai_operations", ttl=7200)
    async def get_smart_embeddings(self, text: str, model: str = "default") -> List[float]:
        """Cache embeddings with model-specific keys"""
        start_time = time.time()
        
        try:
            # This would be your actual embedding generation
            # For now, we'll simulate it
            await asyncio.sleep(0.1)  # Simulate processing time
            
            # Mock embeddings - replace with actual embedding generation
            embeddings = [0.1 * i for i in range(384)]  # 384-dimensional embeddings
            
            execution_time = time.time() - start_time
            
            # Record metrics
            self._record_metrics(AIOperationMetrics(
                operation_type="embedding_generation",
                execution_time=execution_time,
                cache_hit=False,  # This will be True on cache hits
                model_used=model,
                input_size=len(text),
                timestamp=time.time()
            ))
            
            logger.info(f"Generated embeddings for text length {len(text)} in {execution_time:.3f}s")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    @cache_with_tags("rag_responses", "ai_operations", ttl=3600)
    async def get_rag_response(self, query: str, context_hash: str, model: str = "default") -> Dict[str, Any]:
        """Cache RAG responses based on query + context"""
        start_time = time.time()
        
        try:
            # This would be your actual RAG processing
            await asyncio.sleep(0.2)  # Simulate processing time
            
            # Mock RAG response - replace with actual RAG logic
            response = {
                "answer": f"Based on the context, here's the answer to: {query}",
                "confidence": 0.85,
                "sources": ["doc1.pdf", "doc2.pdf"],
                "context_used": context_hash[:10] + "..."
            }
            
            execution_time = time.time() - start_time
            
            # Record metrics
            self._record_metrics(AIOperationMetrics(
                operation_type="rag_response",
                execution_time=execution_time,
                cache_hit=False,
                model_used=model,
                input_size=len(query),
                timestamp=time.time()
            ))
            
            logger.info(f"Generated RAG response for query length {len(query)} in {execution_time:.3f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            raise
    
    @cache_with_tags("document_summaries", "ai_operations", ttl=14400)  # 4 hours
    async def get_document_summary(self, document_id: str, content_hash: str, model: str = "default") -> Dict[str, Any]:
        """Cache document summaries"""
        start_time = time.time()
        
        try:
            # This would be your actual summarization
            await asyncio.sleep(0.15)  # Simulate processing time
            
            # Mock summary - replace with actual summarization
            summary = {
                "summary": f"This document (ID: {document_id}) contains important research findings...",
                "key_points": [
                    "Main finding 1",
                    "Main finding 2", 
                    "Main finding 3"
                ],
                "word_count": 150,
                "confidence": 0.92
            }
            
            execution_time = time.time() - start_time
            
            # Record metrics
            self._record_metrics(AIOperationMetrics(
                operation_type="document_summary",
                execution_time=execution_time,
                cache_hit=False,
                model_used=model,
                input_size=len(content_hash),
                timestamp=time.time()
            ))
            
            logger.info(f"Generated summary for document {document_id} in {execution_time:.3f}s")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating document summary: {e}")
            raise
    
    async def invalidate_document_cache(self, document_id: str):
        """Invalidate all cached data for a specific document"""
        if self.cache:
            # Invalidate by tags
            await self.cache.invalidate_by_tag(f"document_{document_id}")
            logger.info(f"Invalidated cache for document {document_id}")
    
    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all cached data for a specific user"""
        if self.cache:
            await self.cache.invalidate_by_tag(f"user_{user_id}")
            logger.info(f"Invalidated cache for user {user_id}")
    
    def _record_metrics(self, metrics: AIOperationMetrics):
        """Record AI operation metrics"""
        self.metrics.append(metrics)
        
        # Keep only last 1000 metrics to prevent memory issues
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]
    
    def get_ai_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive AI performance metrics"""
        if not self.metrics:
            return {"message": "No metrics available"}
        
        # Calculate metrics by operation type
        metrics_by_type = {}
        for metric in self.metrics:
            op_type = metric.operation_type
            if op_type not in metrics_by_type:
                metrics_by_type[op_type] = {
                    "count": 0,
                    "total_time": 0,
                    "cache_hits": 0,
                    "avg_input_size": 0
                }
            
            metrics_by_type[op_type]["count"] += 1
            metrics_by_type[op_type]["total_time"] += metric.execution_time
            if metric.cache_hit:
                metrics_by_type[op_type]["cache_hits"] += 1
            metrics_by_type[op_type]["avg_input_size"] += metric.input_size
        
        # Calculate averages and rates
        for op_type, data in metrics_by_type.items():
            count = data["count"]
            data["avg_execution_time"] = data["total_time"] / count
            data["cache_hit_rate"] = data["cache_hits"] / count
            data["avg_input_size"] = data["avg_input_size"] / count
        
        return {
            "total_operations": len(self.metrics),
            "operations_by_type": metrics_by_type,
            "overall_cache_hit_rate": sum(1 for m in self.metrics if m.cache_hit) / len(self.metrics),
            "avg_execution_time": sum(m.execution_time for m in self.metrics) / len(self.metrics)
        }
    
    async def warm_cache_for_user(self, user_id: str, common_queries: List[str]):
        """Pre-warm cache with common user queries"""
        logger.info(f"Warming cache for user {user_id} with {len(common_queries)} queries")
        
        tasks = []
        for query in common_queries:
            # Generate a mock context hash for cache warming
            context_hash = hashlib.md5(f"user_{user_id}_context".encode()).hexdigest()
            task = self.get_rag_response(query, context_hash)
            tasks.append(task)
        
        # Execute in batches to avoid overwhelming the system
        batch_size = 5
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
                await asyncio.sleep(0.1)  # Small delay between batches
            except Exception as e:
                logger.warning(f"Error in cache warming batch: {e}")
    
    async def cleanup_old_cache_entries(self, max_age_hours: int = 24):
        """Clean up old cache entries to free memory"""
        if self.cache:
            # This would implement cache cleanup logic
            # For now, we'll just log the action
            logger.info(f"Cleaning up cache entries older than {max_age_hours} hours")
            
            # Remove old metrics
            cutoff_time = time.time() - (max_age_hours * 3600)
            self.metrics = [m for m in self.metrics if m.timestamp > cutoff_time]

# Global AI cache manager instance
ai_cache_manager = AICacheManager()

# Convenience functions for easy access
async def get_cached_embeddings(text: str, model: str = "default") -> List[float]:
    """Get cached embeddings"""
    return await ai_cache_manager.get_smart_embeddings(text, model)

async def get_cached_rag_response(query: str, context_hash: str, model: str = "default") -> Dict[str, Any]:
    """Get cached RAG response"""
    return await ai_cache_manager.get_rag_response(query, context_hash, model)

async def get_cached_document_summary(document_id: str, content_hash: str, model: str = "default") -> Dict[str, Any]:
    """Get cached document summary"""
    return await ai_cache_manager.get_document_summary(document_id, content_hash, model)

# Usage examples for integration
if __name__ == "__main__":
    async def test_ai_cache():
        # Test embedding caching
        embeddings1 = await get_cached_embeddings("This is a test document")
        embeddings2 = await get_cached_embeddings("This is a test document")  # Should be cached
        
        # Test RAG response caching
        context_hash = hashlib.md5("test context".encode()).hexdigest()
        response1 = await get_cached_rag_response("What is the main point?", context_hash)
        response2 = await get_cached_rag_response("What is the main point?", context_hash)  # Should be cached
        
        # Get performance metrics
        metrics = ai_cache_manager.get_ai_performance_metrics()
        print(f"AI Performance Metrics: {json.dumps(metrics, indent=2)}")
    
    # Run test
    asyncio.run(test_ai_cache())