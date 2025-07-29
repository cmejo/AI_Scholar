#!/usr/bin/env python3
"""
Test enhanced Redis integration with advanced RAG features
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.redis_client import (
    redis_client, store_conversation_context, get_conversation_context,
    store_user_session, get_user_session, store_analytics_buffer,
    get_analytics_buffer, store_user_preferences, get_user_preferences
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enhanced_redis_features():
    """Test enhanced Redis features for advanced RAG"""
    try:
        logger.info("Testing enhanced Redis features...")
        
        # Connect to Redis
        await redis_client.connect()
        
        # Test conversation context with memory
        logger.info("Testing conversation context with memory...")
        conversation_id = "conv_enhanced_123"
        enhanced_context = {
            "short_term_memory": [
                {
                    "type": "user_query",
                    "content": "What is machine learning?",
                    "timestamp": datetime.now().isoformat(),
                    "importance": 0.8
                },
                {
                    "type": "system_response",
                    "content": "Machine learning is a subset of AI...",
                    "timestamp": datetime.now().isoformat(),
                    "importance": 0.7
                }
            ],
            "active_entities": [
                {"name": "machine learning", "type": "concept", "importance": 0.9},
                {"name": "artificial intelligence", "type": "concept", "importance": 0.8},
                {"name": "neural networks", "type": "concept", "importance": 0.7}
            ],
            "context_summary": "User is learning about machine learning fundamentals",
            "reasoning_chain": [
                {"step": 1, "type": "retrieval", "description": "Retrieved relevant documents"},
                {"step": 2, "type": "analysis", "description": "Analyzed content for ML concepts"},
                {"step": 3, "type": "synthesis", "description": "Generated comprehensive response"}
            ],
            "uncertainty_scores": {
                "overall_confidence": 0.85,
                "source_reliability": 0.9,
                "factual_accuracy": 0.8
            }
        }
        
        success = await store_conversation_context(conversation_id, enhanced_context)
        if success:
            logger.info("✓ Enhanced conversation context stored successfully")
        else:
            logger.error("✗ Failed to store enhanced conversation context")
            return False
        
        retrieved_context = await get_conversation_context(conversation_id)
        if retrieved_context and "reasoning_chain" in retrieved_context:
            logger.info("✓ Enhanced conversation context retrieved successfully")
        else:
            logger.error("✗ Failed to retrieve enhanced conversation context")
            return False
        
        # Test user session with personalization data
        logger.info("Testing user session with personalization...")
        user_id = "user_enhanced_456"
        session_data = {
            "current_preferences": {
                "language": "en",
                "response_style": "detailed",
                "domain_focus": ["AI", "ML", "NLP"],
                "citation_preference": "inline",
                "reasoning_display": True,
                "uncertainty_tolerance": 0.6
            },
            "active_documents": [
                {"id": "doc_1", "name": "ML Fundamentals", "relevance": 0.9},
                {"id": "doc_2", "name": "Deep Learning", "relevance": 0.8}
            ],
            "query_history": [
                {"query": "What is machine learning?", "timestamp": datetime.now().isoformat()},
                {"query": "Explain neural networks", "timestamp": datetime.now().isoformat()}
            ],
            "personalization_weights": {
                "domain_expertise": {"AI": 0.7, "ML": 0.8, "NLP": 0.6},
                "interaction_patterns": {"prefers_examples": 0.9, "likes_visuals": 0.7},
                "feedback_scores": {"accuracy": 4.5, "relevance": 4.2, "clarity": 4.8}
            },
            "adaptive_settings": {
                "chunk_size_preference": 512,
                "context_window": 2000,
                "retrieval_strategy": "hybrid"
            }
        }
        
        success = await store_user_session(user_id, session_data)
        if success:
            logger.info("✓ Enhanced user session stored successfully")
        else:
            logger.error("✗ Failed to store enhanced user session")
            return False
        
        retrieved_session = await get_user_session(user_id)
        if retrieved_session and "personalization_weights" in retrieved_session:
            logger.info("✓ Enhanced user session retrieved successfully")
        else:
            logger.error("✗ Failed to retrieve enhanced user session")
            return False
        
        # Test analytics buffer with detailed metrics
        logger.info("Testing analytics buffer with detailed metrics...")
        date_str = datetime.now().strftime("%Y-%m-%d")
        analytics_data = {
            "query_count": 15,
            "response_times": [0.5, 0.7, 0.3, 0.9, 0.6, 0.4, 0.8, 0.2, 1.1, 0.5],
            "satisfaction_scores": [5, 4, 5, 3, 4, 5, 4, 5, 3, 4],
            "reasoning_usage": {
                "causal_reasoning": 8,
                "analogical_reasoning": 5,
                "fact_checking": 12,
                "summarization": 10
            },
            "knowledge_graph_queries": 6,
            "memory_retrievals": 20,
            "personalization_applied": 15,
            "uncertainty_scores": [0.8, 0.9, 0.7, 0.6, 0.85, 0.75, 0.9, 0.8, 0.65, 0.88],
            "document_usage": {
                "doc_1": {"hits": 8, "relevance_avg": 0.85},
                "doc_2": {"hits": 5, "relevance_avg": 0.78},
                "doc_3": {"hits": 3, "relevance_avg": 0.92}
            },
            "feature_usage": {
                "hierarchical_chunking": 15,
                "chain_of_thought": 8,
                "citation_generation": 12,
                "auto_tagging": 15
            }
        }
        
        success = await store_analytics_buffer(user_id, date_str, analytics_data)
        if success:
            logger.info("✓ Enhanced analytics buffer stored successfully")
        else:
            logger.error("✗ Failed to store enhanced analytics buffer")
            return False
        
        retrieved_analytics = await get_analytics_buffer(user_id, date_str)
        if retrieved_analytics and "reasoning_usage" in retrieved_analytics:
            logger.info("✓ Enhanced analytics buffer retrieved successfully")
        else:
            logger.error("✗ Failed to retrieve enhanced analytics buffer")
            return False
        
        # Test user preferences with advanced settings
        logger.info("Testing user preferences with advanced settings...")
        advanced_preferences = {
            "language": "en",
            "response_style": "detailed",
            "domain_focus": ["AI", "ML", "NLP", "computer_vision"],
            "citation_preference": "inline",
            "reasoning_display": True,
            "uncertainty_tolerance": 0.6,
            "personalization_level": 0.8,
            "adaptive_learning": True,
            "memory_retention_days": 30,
            "knowledge_graph_depth": 2,
            "chunk_overlap_preference": 0.2,
            "retrieval_strategies": ["semantic", "keyword", "hybrid"],
            "feedback_frequency": "after_each_response",
            "visualization_preferences": {
                "show_confidence_scores": True,
                "display_reasoning_steps": True,
                "highlight_uncertainties": True,
                "show_source_quality": True
            },
            "domain_adaptations": {
                "technical_depth": 0.8,
                "example_preference": 0.9,
                "mathematical_notation": 0.7,
                "code_examples": 0.8
            }
        }
        
        success = await store_user_preferences(user_id, advanced_preferences)
        if success:
            logger.info("✓ Advanced user preferences stored successfully")
        else:
            logger.error("✗ Failed to store advanced user preferences")
            return False
        
        retrieved_preferences = await get_user_preferences(user_id)
        if retrieved_preferences and "visualization_preferences" in retrieved_preferences:
            logger.info("✓ Advanced user preferences retrieved successfully")
        else:
            logger.error("✗ Failed to retrieve advanced user preferences")
            return False
        
        # Test knowledge graph caching
        logger.info("Testing knowledge graph caching...")
        kg_cache_key = f"kg_entities:{user_id}"
        kg_entities = {
            "machine_learning": {
                "type": "concept",
                "importance": 0.9,
                "connections": ["artificial_intelligence", "neural_networks", "deep_learning"],
                "metadata": {"category": "technology", "complexity": "medium"}
            },
            "neural_networks": {
                "type": "concept", 
                "importance": 0.8,
                "connections": ["machine_learning", "deep_learning", "backpropagation"],
                "metadata": {"category": "technology", "complexity": "high"}
            },
            "artificial_intelligence": {
                "type": "concept",
                "importance": 0.95,
                "connections": ["machine_learning", "natural_language_processing", "computer_vision"],
                "metadata": {"category": "technology", "complexity": "high"}
            }
        }
        
        success = await redis_client.set(kg_cache_key, kg_entities, expire=1800)  # 30 minutes
        if success:
            logger.info("✓ Knowledge graph entities cached successfully")
        else:
            logger.error("✗ Failed to cache knowledge graph entities")
            return False
        
        cached_entities = await redis_client.get(kg_cache_key)
        if cached_entities and "machine_learning" in cached_entities:
            logger.info("✓ Knowledge graph entities retrieved from cache successfully")
        else:
            logger.error("✗ Failed to retrieve knowledge graph entities from cache")
            return False
        
        # Test reasoning results caching
        logger.info("Testing reasoning results caching...")
        reasoning_cache_key = f"reasoning_results:{user_id}:ml_query"
        reasoning_results = {
            "causal_reasoning": {
                "confidence": 0.85,
                "explanation": "Machine learning enables pattern recognition through data analysis",
                "supporting_evidence": ["statistical learning theory", "empirical risk minimization"],
                "chain": ["data → patterns → predictions → insights"]
            },
            "analogical_reasoning": {
                "confidence": 0.78,
                "analogies": [
                    {"source": "human learning", "target": "machine learning", "similarity": 0.7},
                    {"source": "pattern recognition", "target": "feature extraction", "similarity": 0.8}
                ],
                "explanation": "Like humans learn from experience, ML learns from data"
            },
            "uncertainty_quantification": {
                "overall_confidence": 0.82,
                "uncertainty_factors": ["data quality", "model complexity", "domain specificity"],
                "reliability_score": 0.88,
                "source_quality": 0.85
            }
        }
        
        success = await redis_client.set(reasoning_cache_key, reasoning_results, expire=600)  # 10 minutes
        if success:
            logger.info("✓ Reasoning results cached successfully")
        else:
            logger.error("✗ Failed to cache reasoning results")
            return False
        
        cached_reasoning = await redis_client.get(reasoning_cache_key)
        if cached_reasoning and "causal_reasoning" in cached_reasoning:
            logger.info("✓ Reasoning results retrieved from cache successfully")
        else:
            logger.error("✗ Failed to retrieve reasoning results from cache")
            return False
        
        # Clean up test data
        await redis_client.delete(f"conversation_context:{conversation_id}")
        await redis_client.delete(f"user_session:{user_id}")
        await redis_client.delete(f"analytics_buffer:{user_id}:{date_str}")
        await redis_client.delete(f"user_preferences:{user_id}")
        await redis_client.delete(kg_cache_key)
        await redis_client.delete(reasoning_cache_key)
        
        logger.info("✓ All enhanced Redis integration tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Enhanced Redis integration test failed: {e}")
        return False
    finally:
        await redis_client.disconnect()

async def main():
    """Main test function"""
    logger.info("Starting enhanced Redis integration tests...")
    
    success = await test_enhanced_redis_features()
    if success:
        logger.info("All enhanced Redis integration tests completed successfully!")
        sys.exit(0)
    else:
        logger.error("Enhanced Redis integration tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())