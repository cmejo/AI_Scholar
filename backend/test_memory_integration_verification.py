#!/usr/bin/env python3
"""
Test script to verify memory integration in the RAG system
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.memory_service import (
    conversation_memory_manager,
    context_compressor,
    user_memory_store,
    MemoryItem,
    ConversationContext
)
from models.schemas import MemoryType

async def test_memory_integration():
    """Test the memory system integration"""
    print("Testing Memory System Integration...")
    
    # Test 1: ConversationMemoryManager
    print("\n1. Testing ConversationMemoryManager...")
    conversation_id = "test_conv_001"
    
    # Create test memory items
    memory_items = [
        MemoryItem(
            content="User asked about machine learning",
            memory_type=MemoryType.SHORT_TERM,
            importance_score=0.7,
            timestamp=datetime.now(),
            metadata={"entities": ["machine learning"], "intent": "question"}
        ),
        MemoryItem(
            content="User prefers detailed explanations",
            memory_type=MemoryType.PREFERENCE,
            importance_score=0.9,
            timestamp=datetime.now(),
            metadata={"preference_type": "explanation_style"}
        )
    ]
    
    # Store memory items
    success = await conversation_memory_manager.store_memory_items(conversation_id, memory_items)
    print(f"   ✓ Store memory items: {'SUCCESS' if success else 'FAILED'}")
    
    # Retrieve memory items
    retrieved_items = await conversation_memory_manager.retrieve_memory_items(conversation_id)
    print(f"   ✓ Retrieved {len(retrieved_items)} memory items")
    
    # Get conversation context
    context = await conversation_memory_manager.get_conversation_context(conversation_id)
    if context:
        print(f"   ✓ Conversation context retrieved with {len(context.short_term_memory)} memories")
    else:
        print("   ✗ Failed to retrieve conversation context")
    
    # Test 2: ContextCompressor
    print("\n2. Testing ContextCompressor...")
    if context and len(context.short_term_memory) > 0:
        # Test compression
        compressed_context = await context_compressor.compress_conversation_context(context)
        print(f"   ✓ Context compression: {len(context.short_term_memory)} -> {len(compressed_context.short_term_memory)} items")
        
        # Test relevance pruning
        pruned_memories = await context_compressor.prune_context_by_relevance(
            context.short_term_memory, 
            "machine learning algorithms",
            max_items=5
        )
        print(f"   ✓ Relevance pruning: {len(context.short_term_memory)} -> {len(pruned_memories)} relevant items")
    
    # Test 3: UserMemoryStore
    print("\n3. Testing UserMemoryStore...")
    user_id = "test_user_001"
    
    # Store user preference
    pref_success = await user_memory_store.store_user_preference(
        user_id, 
        "response_style", 
        "detailed",
        confidence=0.8,
        source="explicit"
    )
    print(f"   ✓ Store user preference: {'SUCCESS' if pref_success else 'FAILED'}")
    
    # Get user preferences
    preferences = await user_memory_store.get_user_preferences(user_id)
    print(f"   ✓ Retrieved {len(preferences)} user preferences")
    
    # Get personalized context
    personalized_context = await user_memory_store.get_personalized_context(
        user_id, 
        "Tell me about machine learning"
    )
    print(f"   ✓ Personalized context generated with {len(personalized_context)} components")
    
    # Update domain expertise
    expertise_success = await user_memory_store.update_domain_expertise(
        user_id, 
        "machine_learning", 
        0.1
    )
    print(f"   ✓ Update domain expertise: {'SUCCESS' if expertise_success else 'FAILED'}")
    
    # Test 4: Memory Importance Scoring
    print("\n4. Testing Memory Importance Scoring...")
    
    test_contents = [
        ("Regular question", MemoryType.SHORT_TERM),
        ("I prefer detailed explanations", MemoryType.PREFERENCE),
        ("That's wrong, the correct answer is X", MemoryType.SHORT_TERM),
        ("Important information to remember", MemoryType.LONG_TERM)
    ]
    
    for content, memory_type in test_contents:
        score = await conversation_memory_manager.calculate_importance_score(
            content, memory_type
        )
        print(f"   ✓ '{content[:30]}...' -> Importance: {score:.2f}")
    
    # Test 5: Memory Pruning
    print("\n5. Testing Memory Pruning...")
    
    # Test expired memory pruning
    pruned_count = await conversation_memory_manager.prune_expired_memories(conversation_id)
    print(f"   ✓ Pruned {pruned_count} expired memories")
    
    # Clean up
    await conversation_memory_manager.clear_conversation_memory(conversation_id)
    print(f"   ✓ Cleaned up test conversation memory")
    
    print("\n✅ Memory System Integration Test Complete!")
    return True

async def main():
    """Main test function"""
    try:
        success = await test_memory_integration()
        if success:
            print("\n🎉 All memory integration tests passed!")
            return 0
        else:
            print("\n❌ Some memory integration tests failed!")
            return 1
    except Exception as e:
        print(f"\n💥 Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)