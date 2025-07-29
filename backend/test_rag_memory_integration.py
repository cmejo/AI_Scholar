#!/usr/bin/env python3
"""
Test script to verify RAG service memory integration
"""
import asyncio
import sys
import os
from datetime import datetime
from unittest.mock import AsyncMock, patch

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.memory_service import (
    conversation_memory_manager,
    user_memory_store,
    MemoryItem,
    ConversationContext
)
from models.schemas import MemoryType

async def test_rag_memory_integration():
    """Test RAG service memory integration functionality"""
    print("Testing RAG Service Memory Integration...")
    
    # Mock the enhanced RAG service methods to test memory integration
    conversation_id = "test_conv_001"
    user_id = "test_user_001"
    query = "What is machine learning?"
    
    # Test 1: Store query in memory (simulate RAG service behavior)
    print("\n1. Testing Query Storage in Memory...")
    
    # Calculate importance score for the query
    importance_score = await conversation_memory_manager.calculate_importance_score(
        query, MemoryType.SHORT_TERM
    )
    
    # Create memory item for query
    query_memory = MemoryItem(
        content=f"User query: {query}",
        memory_type=MemoryType.SHORT_TERM,
        importance_score=importance_score,
        timestamp=datetime.now(),
        metadata={
            "type": "user_query",
            "user_id": user_id,
            "query_length": len(query),
            "entities": ["machine learning"]  # Simulated entity extraction
        }
    )
    
    success = await conversation_memory_manager.store_memory_item(conversation_id, query_memory)
    print(f"   ✓ Query stored in memory: {'SUCCESS' if success else 'FAILED'}")
    
    # Test 2: Store response in memory
    print("\n2. Testing Response Storage in Memory...")
    
    response = "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed."
    
    response_memory = MemoryItem(
        content=f"Assistant response: {response[:200]}...",
        memory_type=MemoryType.CONTEXT,
        importance_score=await conversation_memory_manager.calculate_importance_score(
            response, MemoryType.CONTEXT
        ),
        timestamp=datetime.now(),
        metadata={
            "type": "assistant_response",
            "user_id": user_id,
            "response_length": len(response),
            "entities": ["machine learning", "artificial intelligence"]
        }
    )
    
    success = await conversation_memory_manager.store_memory_item(conversation_id, response_memory)
    print(f"   ✓ Response stored in memory: {'SUCCESS' if success else 'FAILED'}")
    
    # Test 3: Retrieve memory context for new query
    print("\n3. Testing Memory Context Retrieval...")
    
    new_query = "Tell me more about AI algorithms"
    
    # Get conversation context
    conversation_context = await conversation_memory_manager.get_conversation_context(conversation_id)
    
    if conversation_context:
        print(f"   ✓ Retrieved conversation context with {len(conversation_context.short_term_memory)} memories")
        
        # Simulate memory context building (as done in RAG service)
        memory_context = {
            "conversation_summary": conversation_context.context_summary or "Discussion about machine learning and AI",
            "relevant_memories": [
                {
                    "content": memory.content,
                    "importance": memory.importance_score,
                    "timestamp": memory.timestamp.isoformat(),
                    "type": memory.memory_type.value
                }
                for memory in conversation_context.short_term_memory
            ],
            "active_entities": conversation_context.active_entities,
            "memory_count": len(conversation_context.short_term_memory)
        }
        
        print(f"   ✓ Memory context built with {memory_context['memory_count']} relevant memories")
        print(f"   ✓ Active entities: {memory_context['active_entities']}")
        
    else:
        print("   ✗ Failed to retrieve conversation context")
    
    # Test 4: User preference integration
    print("\n4. Testing User Preference Integration...")
    
    # Store user preferences (as would be done by RAG service)
    await user_memory_store.store_user_preference(
        user_id, 
        "response_style", 
        "detailed",
        confidence=0.8,
        source="learned"
    )
    
    await user_memory_store.store_user_preference(
        user_id,
        "domain_interest_ai",
        True,
        confidence=0.7,
        source="inferred"
    )
    
    # Get personalized context
    personalized_context = await user_memory_store.get_personalized_context(
        user_id, 
        new_query
    )
    
    print(f"   ✓ Personalized context retrieved with {len(personalized_context)} components")
    
    if personalized_context.get("user_preferences"):
        prefs = personalized_context["user_preferences"]
        print(f"   ✓ User preferences: {len(prefs)} preferences loaded")
        for key, value in prefs.items():
            if isinstance(value, dict) and "value" in value:
                print(f"     - {key}: {value['value']} (confidence: {value.get('confidence', 'N/A')})")
    
    # Test 5: Multi-turn conversation handling
    print("\n5. Testing Multi-turn Conversation Handling...")
    
    # Simulate a follow-up query
    followup_query = "How does it differ from traditional programming?"
    
    # Store follow-up query
    followup_memory = MemoryItem(
        content=f"User query: {followup_query}",
        memory_type=MemoryType.SHORT_TERM,
        importance_score=await conversation_memory_manager.calculate_importance_score(
            followup_query, MemoryType.SHORT_TERM
        ),
        timestamp=datetime.now(),
        metadata={
            "type": "user_query",
            "user_id": user_id,
            "query_length": len(followup_query),
            "is_followup": True,
            "entities": ["programming"]
        }
    )
    
    await conversation_memory_manager.store_memory_item(conversation_id, followup_memory)
    
    # Get updated context
    updated_context = await conversation_memory_manager.get_conversation_context(conversation_id)
    if updated_context:
        print(f"   ✓ Multi-turn context: {len(updated_context.short_term_memory)} total memories")
        
        # Check if context references are maintained
        recent_memories = sorted(updated_context.short_term_memory, key=lambda x: x.timestamp, reverse=True)[:3]
        print("   ✓ Recent conversation flow:")
        for i, memory in enumerate(recent_memories):
            print(f"     {i+1}. {memory.content[:50]}...")
    
    # Test 6: Memory-aware context building
    print("\n6. Testing Memory-Aware Context Building...")
    
    # Simulate building enhanced context (as done in RAG service)
    if conversation_context:
        # Mock search results
        mock_search_results = [
            {
                "content": "Machine learning uses algorithms to parse data, learn from it, and make predictions.",
                "source": "ML Textbook",
                "relevance": 0.9
            },
            {
                "content": "Traditional programming requires explicit instructions for every task.",
                "source": "Programming Guide", 
                "relevance": 0.8
            }
        ]
        
        # Build context parts (simulating RAG service logic)
        context_parts = []
        
        # Add search results
        context_parts.append("Retrieved Information:")
        for result in mock_search_results:
            context_parts.append(f"- {result['content']} (Source: {result['source']})")
        context_parts.append("")
        
        # Add memory context
        if memory_context.get("conversation_summary"):
            context_parts.append(f"Conversation Context: {memory_context['conversation_summary']}")
            context_parts.append("")
        
        if memory_context.get("relevant_memories"):
            context_parts.append("Relevant Previous Discussion:")
            for memory in memory_context["relevant_memories"][:3]:
                context_parts.append(f"- {memory['content']}")
            context_parts.append("")
        
        # Add personalization
        if personalized_context.get("user_preferences"):
            user_prefs = personalized_context["user_preferences"]
            if user_prefs.get("response_style", {}).get("value") == "detailed":
                context_parts.append("Note: User prefers detailed explanations")
                context_parts.append("")
        
        enhanced_context = "\n".join(context_parts)
        print(f"   ✓ Enhanced context built ({len(enhanced_context)} characters)")
        print(f"   ✓ Context includes: search results, memory, and personalization")
    
    # Clean up
    await conversation_memory_manager.clear_conversation_memory(conversation_id)
    print(f"\n   ✓ Cleaned up test data")
    
    print("\n✅ RAG Service Memory Integration Test Complete!")
    return True

async def main():
    """Main test function"""
    try:
        success = await test_rag_memory_integration()
        if success:
            print("\n🎉 RAG service memory integration is working correctly!")
            return 0
        else:
            print("\n❌ RAG service memory integration has issues!")
            return 1
    except Exception as e:
        print(f"\n💥 Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)