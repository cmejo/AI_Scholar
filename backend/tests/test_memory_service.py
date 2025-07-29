"""
Tests for Memory Service - Conversation Memory Storage
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from services.memory_service import (
    ConversationMemoryManager,
    MemoryItem,
    ConversationContext,
    MemoryImportance,
    conversation_memory_manager
)
from models.schemas import MemoryType


class TestConversationMemoryManager:
    """Test cases for ConversationMemoryManager"""
    
    @pytest.fixture
    def memory_manager(self):
        """Create a memory manager instance for testing"""
        return ConversationMemoryManager()
    
    @pytest.fixture
    def sample_memory_item(self):
        """Create a sample memory item for testing"""
        return MemoryItem(
            content="User asked about machine learning algorithms",
            memory_type=MemoryType.SHORT_TERM,
            importance_score=0.7,
            timestamp=datetime.now(),
            metadata={"entities": ["machine learning", "algorithms"], "intent": "question"}
        )
    
    @pytest.fixture
    def sample_memory_items(self):
        """Create multiple sample memory items"""
        now = datetime.now()
        return [
            MemoryItem(
                content="User prefers detailed explanations",
                memory_type=MemoryType.PREFERENCE,
                importance_score=0.9,
                timestamp=now - timedelta(minutes=5),
                metadata={"preference_type": "explanation_style"}
            ),
            MemoryItem(
                content="Discussed neural networks in previous conversation",
                memory_type=MemoryType.CONTEXT,
                importance_score=0.6,
                timestamp=now - timedelta(minutes=10),
                metadata={"topic": "neural networks"}
            ),
            MemoryItem(
                content="User corrected information about Python syntax",
                memory_type=MemoryType.SHORT_TERM,
                importance_score=0.8,
                timestamp=now - timedelta(minutes=2),
                metadata={"correction": True, "topic": "Python"}
            )
        ]
    
    @pytest.mark.asyncio
    async def test_store_single_memory_item(self, memory_manager, sample_memory_item):
        """Test storing a single memory item"""
        conversation_id = "test_conv_001"
        
        with patch.object(memory_manager.redis_client, 'get', return_value=None), \
             patch.object(memory_manager.redis_client, 'set', return_value=True), \
             patch.object(memory_manager, '_store_in_database', return_value=True):
            
            result = await memory_manager.store_memory_item(conversation_id, sample_memory_item)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_store_multiple_memory_items(self, memory_manager, sample_memory_items):
        """Test storing multiple memory items"""
        conversation_id = "test_conv_002"
        
        with patch.object(memory_manager.redis_client, 'get', return_value=None), \
             patch.object(memory_manager.redis_client, 'set', return_value=True), \
             patch.object(memory_manager, '_store_in_database', return_value=True):
            
            result = await memory_manager.store_memory_items(conversation_id, sample_memory_items)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_retrieve_memory_items_all(self, memory_manager, sample_memory_items):
        """Test retrieving all memory items"""
        conversation_id = "test_conv_003"
        
        # Mock Redis context data
        mock_context = {
            "short_term_memory": [
                {
                    "content": item.content,
                    "memory_type": item.memory_type.value,
                    "importance_score": item.importance_score,
                    "timestamp": item.timestamp.isoformat(),
                    "expires_at": item.expires_at.isoformat() if item.expires_at else None,
                    "metadata": item.metadata
                }
                for item in sample_memory_items
            ],
            "context_summary": "",
            "active_entities": [],
            "last_updated": datetime.now().isoformat(),
            "total_tokens": 0
        }
        
        with patch.object(memory_manager, '_get_redis_context', return_value=mock_context):
            retrieved_items = await memory_manager.retrieve_memory_items(conversation_id)
            
            assert len(retrieved_items) == 3
            assert all(isinstance(item, MemoryItem) for item in retrieved_items)
            
            # Check sorting by importance score (descending)
            importance_scores = [item.importance_score for item in retrieved_items]
            assert importance_scores == sorted(importance_scores, reverse=True)
    
    @pytest.mark.asyncio
    async def test_retrieve_memory_items_by_type(self, memory_manager, sample_memory_items):
        """Test retrieving memory items filtered by type"""
        conversation_id = "test_conv_004"
        
        mock_context = {
            "short_term_memory": [
                {
                    "content": item.content,
                    "memory_type": item.memory_type.value,
                    "importance_score": item.importance_score,
                    "timestamp": item.timestamp.isoformat(),
                    "expires_at": item.expires_at.isoformat() if item.expires_at else None,
                    "metadata": item.metadata
                }
                for item in sample_memory_items
            ]
        }
        
        with patch.object(memory_manager, '_get_redis_context', return_value=mock_context):
            # Test filtering by PREFERENCE type
            preference_items = await memory_manager.retrieve_memory_items(
                conversation_id, 
                memory_type=MemoryType.PREFERENCE
            )
            
            assert len(preference_items) == 1
            assert preference_items[0].memory_type == MemoryType.PREFERENCE
            assert "prefers detailed explanations" in preference_items[0].content
    
    @pytest.mark.asyncio
    async def test_retrieve_memory_items_with_limit(self, memory_manager, sample_memory_items):
        """Test retrieving memory items with limit"""
        conversation_id = "test_conv_005"
        
        mock_context = {
            "short_term_memory": [
                {
                    "content": item.content,
                    "memory_type": item.memory_type.value,
                    "importance_score": item.importance_score,
                    "timestamp": item.timestamp.isoformat(),
                    "expires_at": item.expires_at.isoformat() if item.expires_at else None,
                    "metadata": item.metadata
                }
                for item in sample_memory_items
            ]
        }
        
        with patch.object(memory_manager, '_get_redis_context', return_value=mock_context):
            limited_items = await memory_manager.retrieve_memory_items(conversation_id, limit=2)
            
            assert len(limited_items) == 2
            # Should return the 2 most important items
            assert limited_items[0].importance_score >= limited_items[1].importance_score
    
    @pytest.mark.asyncio
    async def test_get_conversation_context(self, memory_manager, sample_memory_items):
        """Test getting full conversation context"""
        conversation_id = "test_conv_006"
        
        mock_context = {
            "short_term_memory": [
                {
                    "content": item.content,
                    "memory_type": item.memory_type.value,
                    "importance_score": item.importance_score,
                    "timestamp": item.timestamp.isoformat(),
                    "expires_at": item.expires_at.isoformat() if item.expires_at else None,
                    "metadata": item.metadata
                }
                for item in sample_memory_items
            ],
            "context_summary": "Discussion about machine learning and Python",
            "active_entities": ["machine learning", "Python", "neural networks"],
            "last_updated": datetime.now().isoformat(),
            "total_tokens": 150
        }
        
        with patch.object(memory_manager, '_get_redis_context', return_value=mock_context):
            context = await memory_manager.get_conversation_context(conversation_id)
            
            assert isinstance(context, ConversationContext)
            assert context.conversation_id == conversation_id
            assert len(context.short_term_memory) == 3
            assert context.context_summary == "Discussion about machine learning and Python"
            assert len(context.active_entities) == 3
            assert context.total_tokens == 150
    
    @pytest.mark.asyncio
    async def test_calculate_importance_score_basic(self, memory_manager):
        """Test basic importance score calculation"""
        # Test different memory types
        score_short = await memory_manager.calculate_importance_score(
            "Regular message", MemoryType.SHORT_TERM
        )
        score_preference = await memory_manager.calculate_importance_score(
            "User preference", MemoryType.PREFERENCE
        )
        score_long = await memory_manager.calculate_importance_score(
            "Important information", MemoryType.LONG_TERM
        )
        
        assert score_preference > score_long > score_short
        assert 0.0 <= score_short <= 1.0
        assert 0.0 <= score_preference <= 1.0
        assert 0.0 <= score_long <= 1.0
    
    @pytest.mark.asyncio
    async def test_calculate_importance_score_content_factors(self, memory_manager):
        """Test importance score calculation with content factors"""
        # Test question content
        question_score = await memory_manager.calculate_importance_score(
            "What is the best approach for this problem?", MemoryType.SHORT_TERM
        )
        
        # Test preference content
        preference_score = await memory_manager.calculate_importance_score(
            "I prefer detailed explanations over brief ones", MemoryType.SHORT_TERM
        )
        
        # Test correction content
        correction_score = await memory_manager.calculate_importance_score(
            "That's wrong, the correct answer is X", MemoryType.SHORT_TERM
        )
        
        # Test regular content
        regular_score = await memory_manager.calculate_importance_score(
            "This is a regular statement", MemoryType.SHORT_TERM
        )
        
        assert preference_score > question_score > regular_score
        assert correction_score > regular_score
    
    @pytest.mark.asyncio
    async def test_calculate_importance_score_with_entities(self, memory_manager):
        """Test importance score calculation with entity context"""
        context_with_entities = {
            "entities": ["machine learning", "neural networks", "Python"]
        }
        
        score_with_entities = await memory_manager.calculate_importance_score(
            "Discussion about machine learning", 
            MemoryType.SHORT_TERM,
            context=context_with_entities
        )
        
        score_without_entities = await memory_manager.calculate_importance_score(
            "Discussion about machine learning", 
            MemoryType.SHORT_TERM
        )
        
        assert score_with_entities > score_without_entities
    
    @pytest.mark.asyncio
    async def test_prune_expired_memories(self, memory_manager):
        """Test pruning expired memory items"""
        conversation_id = "test_conv_007"
        
        # Create mock context with expired and active memories
        now = datetime.now()
        expired_time = now - timedelta(hours=2)
        future_time = now + timedelta(hours=1)
        
        mock_context = {
            "short_term_memory": [
                {
                    "content": "Active memory",
                    "memory_type": MemoryType.SHORT_TERM.value,
                    "importance_score": 0.5,
                    "timestamp": now.isoformat(),
                    "expires_at": future_time.isoformat(),
                    "metadata": {}
                },
                {
                    "content": "Expired memory",
                    "memory_type": MemoryType.SHORT_TERM.value,
                    "importance_score": 0.5,
                    "timestamp": expired_time.isoformat(),
                    "expires_at": expired_time.isoformat(),
                    "metadata": {}
                },
                {
                    "content": "No expiration memory",
                    "memory_type": MemoryType.LONG_TERM.value,
                    "importance_score": 0.8,
                    "timestamp": now.isoformat(),
                    "expires_at": None,
                    "metadata": {}
                }
            ],
            "last_updated": now.isoformat()
        }
        
        with patch.object(memory_manager, '_get_redis_context', return_value=mock_context), \
             patch.object(memory_manager.redis_client, 'set', return_value=True):
            
            pruned_count = await memory_manager.prune_expired_memories(conversation_id)
            
            assert pruned_count == 1  # One expired memory should be pruned
    
    @pytest.mark.asyncio
    async def test_clear_conversation_memory(self, memory_manager):
        """Test clearing all conversation memory"""
        conversation_id = "test_conv_008"
        
        with patch.object(memory_manager.redis_client, 'delete', return_value=True):
            result = await memory_manager.clear_conversation_memory(conversation_id)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_memory_pruning_by_count(self, memory_manager):
        """Test memory pruning when count exceeds limit"""
        # Set a low limit for testing
        memory_manager.max_short_term_items = 2
        
        # Create context with more items than limit
        mock_context = {
            "short_term_memory": [
                {
                    "content": f"Memory item {i}",
                    "memory_type": MemoryType.SHORT_TERM.value,
                    "importance_score": 0.1 * i,  # Increasing importance
                    "timestamp": datetime.now().isoformat(),
                    "expires_at": None,
                    "metadata": {}
                }
                for i in range(1, 6)  # 5 items, limit is 2
            ]
        }
        
        pruned_context = await memory_manager._prune_memory_items(mock_context)
        
        assert len(pruned_context["short_term_memory"]) == 2
        # Should keep the most important items (highest scores)
        kept_scores = [item["importance_score"] for item in pruned_context["short_term_memory"]]
        assert kept_scores == [0.5, 0.4]  # Highest importance scores
    
    @pytest.mark.asyncio
    async def test_error_handling_redis_failure(self, memory_manager, sample_memory_item):
        """Test error handling when Redis operations fail"""
        conversation_id = "test_conv_009"
        
        with patch.object(memory_manager.redis_client, 'get', side_effect=Exception("Redis error")):
            # Should handle Redis errors gracefully
            result = await memory_manager.store_memory_item(conversation_id, sample_memory_item)
            assert result is False
            
            retrieved_items = await memory_manager.retrieve_memory_items(conversation_id)
            assert retrieved_items == []
    
    @pytest.mark.asyncio
    async def test_memory_item_serialization(self, memory_manager):
        """Test proper serialization and deserialization of memory items"""
        conversation_id = "test_conv_010"
        
        # Create memory item with complex metadata
        memory_item = MemoryItem(
            content="Complex memory with metadata",
            memory_type=MemoryType.CONTEXT,
            importance_score=0.75,
            timestamp=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1),
            metadata={
                "entities": ["entity1", "entity2"],
                "sentiment": "positive",
                "confidence": 0.85,
                "nested": {"key": "value", "number": 42}
            }
        )
        
        with patch.object(memory_manager.redis_client, 'get', return_value=None), \
             patch.object(memory_manager.redis_client, 'set', return_value=True), \
             patch.object(memory_manager, '_store_in_database', return_value=True):
            
            # Store the memory item
            store_result = await memory_manager.store_memory_item(conversation_id, memory_item)
            assert store_result is True
        
        # Mock the stored data for retrieval test
        mock_stored_data = {
            "short_term_memory": [{
                "content": memory_item.content,
                "memory_type": memory_item.memory_type.value,
                "importance_score": memory_item.importance_score,
                "timestamp": memory_item.timestamp.isoformat(),
                "expires_at": memory_item.expires_at.isoformat(),
                "metadata": memory_item.metadata
            }]
        }
        
        with patch.object(memory_manager, '_get_redis_context', return_value=mock_stored_data):
            retrieved_items = await memory_manager.retrieve_memory_items(conversation_id)
            
            assert len(retrieved_items) == 1
            retrieved_item = retrieved_items[0]
            
            assert retrieved_item.content == memory_item.content
            assert retrieved_item.memory_type == memory_item.memory_type
            assert retrieved_item.importance_score == memory_item.importance_score
            assert retrieved_item.metadata == memory_item.metadata


class TestMemoryImportance:
    """Test memory importance scoring"""
    
    def test_memory_importance_enum(self):
        """Test memory importance enum values"""
        assert MemoryImportance.LOW.value == 0.2
        assert MemoryImportance.MEDIUM.value == 0.5
        assert MemoryImportance.HIGH.value == 0.8
        assert MemoryImportance.CRITICAL.value == 1.0


class TestMemoryItem:
    """Test MemoryItem dataclass"""
    
    def test_memory_item_creation(self):
        """Test creating a memory item"""
        now = datetime.now()
        item = MemoryItem(
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            importance_score=0.7,
            timestamp=now
        )
        
        assert item.content == "Test content"
        assert item.memory_type == MemoryType.SHORT_TERM
        assert item.importance_score == 0.7
        assert item.timestamp == now
        assert item.expires_at is None
        assert item.metadata == {}
    
    def test_memory_item_with_metadata(self):
        """Test creating a memory item with metadata"""
        metadata = {"key": "value", "entities": ["entity1"]}
        item = MemoryItem(
            content="Test content",
            memory_type=MemoryType.CONTEXT,
            importance_score=0.5,
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        assert item.metadata == metadata


class TestConversationContext:
    """Test ConversationContext dataclass"""
    
    def test_conversation_context_creation(self):
        """Test creating conversation context"""
        now = datetime.now()
        memory_items = [
            MemoryItem("Test 1", MemoryType.SHORT_TERM, 0.5, now),
            MemoryItem("Test 2", MemoryType.CONTEXT, 0.7, now)
        ]
        
        context = ConversationContext(
            conversation_id="test_conv",
            short_term_memory=memory_items,
            context_summary="Test summary",
            active_entities=["entity1", "entity2"],
            last_updated=now,
            total_tokens=100
        )
        
        assert context.conversation_id == "test_conv"
        assert len(context.short_term_memory) == 2
        assert context.context_summary == "Test summary"
        assert len(context.active_entities) == 2
        assert context.total_tokens == 100


class TestContextCompressor:
    """Test cases for ContextCompressor"""
    
    @pytest.fixture
    def context_compressor(self):
        """Create a context compressor instance for testing"""
        from services.memory_service import ContextCompressor
        return ContextCompressor()
    
    @pytest.fixture
    def large_conversation_context(self):
        """Create a large conversation context for compression testing"""
        now = datetime.now()
        memory_items = []
        
        # Create many memory items to simulate a long conversation
        for i in range(20):
            memory_items.append(MemoryItem(
                content=f"This is memory item {i} discussing topic {i % 3}",
                memory_type=MemoryType.SHORT_TERM,
                importance_score=0.3 + (i % 5) * 0.1,  # Varying importance
                timestamp=now - timedelta(minutes=i * 2),
                metadata={"topic": f"topic_{i % 3}", "entities": [f"entity_{i}"]}
            ))
        
        return ConversationContext(
            conversation_id="large_conv_001",
            short_term_memory=memory_items,
            context_summary="Long conversation about various topics",
            active_entities=["entity_1", "entity_2", "entity_3"],
            last_updated=now,
            total_tokens=5000  # Exceeds max_context_length
        )
    
    @pytest.fixture
    def related_memories(self):
        """Create related memory items for grouping tests"""
        now = datetime.now()
        return [
            MemoryItem(
                content="User asked about machine learning algorithms",
                memory_type=MemoryType.SHORT_TERM,
                importance_score=0.6,
                timestamp=now - timedelta(minutes=1),
                metadata={"entities": ["machine learning", "algorithms"]}
            ),
            MemoryItem(
                content="Discussed neural networks and deep learning",
                memory_type=MemoryType.CONTEXT,
                importance_score=0.7,
                timestamp=now - timedelta(minutes=2),
                metadata={"entities": ["neural networks", "deep learning"]}
            ),
            MemoryItem(
                content="User prefers detailed technical explanations",
                memory_type=MemoryType.PREFERENCE,
                importance_score=0.9,
                timestamp=now - timedelta(minutes=30),  # Different time window
                metadata={"preference_type": "explanation_style"}
            )
        ]
    
    @pytest.mark.asyncio
    async def test_compress_conversation_context_basic(self, context_compressor, large_conversation_context):
        """Test basic context compression"""
        compressed_context = await context_compressor.compress_conversation_context(
            large_conversation_context
        )
        
        assert isinstance(compressed_context, ConversationContext)
        assert compressed_context.conversation_id == large_conversation_context.conversation_id
        assert len(compressed_context.short_term_memory) < len(large_conversation_context.short_term_memory)
        assert compressed_context.total_tokens < large_conversation_context.total_tokens
        assert compressed_context.context_summary != ""
    
    @pytest.mark.asyncio
    async def test_compress_conversation_context_no_compression_needed(self, context_compressor):
        """Test compression when context is already small enough"""
        small_context = ConversationContext(
            conversation_id="small_conv",
            short_term_memory=[
                MemoryItem("Small memory", MemoryType.SHORT_TERM, 0.5, datetime.now())
            ],
            context_summary="Small context",
            active_entities=[],
            last_updated=datetime.now(),
            total_tokens=100  # Below threshold
        )
        
        compressed_context = await context_compressor.compress_conversation_context(small_context)
        
        # Should return the same context
        assert compressed_context.total_tokens == small_context.total_tokens
        assert len(compressed_context.short_term_memory) == len(small_context.short_term_memory)
    
    @pytest.mark.asyncio
    async def test_filter_by_importance(self, context_compressor, related_memories):
        """Test filtering memories by importance threshold"""
        # Set a high threshold
        context_compressor.min_importance_threshold = 0.8
        
        filtered_memories = await context_compressor._filter_by_importance(related_memories)
        
        # Only the preference memory (0.9) should pass the threshold
        assert len(filtered_memories) == 1
        assert filtered_memories[0].memory_type == MemoryType.PREFERENCE
        assert filtered_memories[0].importance_score == 0.9
    
    @pytest.mark.asyncio
    async def test_group_related_memories(self, context_compressor, related_memories):
        """Test grouping related memories"""
        # Modify timestamps to make first two memories close in time
        now = datetime.now()
        related_memories[0].timestamp = now - timedelta(minutes=1)
        related_memories[1].timestamp = now - timedelta(minutes=2)
        
        groups = await context_compressor._group_related_memories(related_memories)
        
        assert len(groups) >= 1
        # Should have at least one group with multiple items or separate groups
        total_items = sum(len(group) for group in groups)
        assert total_items == len(related_memories)
    
    @pytest.mark.asyncio
    async def test_are_memories_related_time_proximity(self, context_compressor):
        """Test memory relationship detection based on time proximity"""
        now = datetime.now()
        
        # Close in time
        memory1 = MemoryItem("Content 1", MemoryType.SHORT_TERM, 0.5, now)
        memory2 = MemoryItem("Content 2", MemoryType.SHORT_TERM, 0.5, now - timedelta(minutes=5))
        
        related = await context_compressor._are_memories_related(memory1, memory2)
        assert related is True
        
        # Far apart in time
        memory3 = MemoryItem("Content 3", MemoryType.SHORT_TERM, 0.5, now - timedelta(hours=1))
        
        not_related = await context_compressor._are_memories_related(memory1, memory3)
        assert not_related is False
    
    @pytest.mark.asyncio
    async def test_are_memories_related_content_similarity(self, context_compressor):
        """Test memory relationship detection based on content similarity"""
        now = datetime.now()
        
        # Similar content
        memory1 = MemoryItem(
            "machine learning algorithms neural networks", 
            MemoryType.SHORT_TERM, 0.5, now
        )
        memory2 = MemoryItem(
            "neural networks deep learning algorithms", 
            MemoryType.SHORT_TERM, 0.5, now - timedelta(minutes=2)
        )
        
        related = await context_compressor._are_memories_related(memory1, memory2)
        assert related is True
        
        # Dissimilar content
        memory3 = MemoryItem(
            "weather forecast sunny day", 
            MemoryType.SHORT_TERM, 0.5, now - timedelta(minutes=2)
        )
        
        not_related = await context_compressor._are_memories_related(memory1, memory3)
        assert not_related is False
    
    @pytest.mark.asyncio
    async def test_summarize_memory_group_single_item(self, context_compressor):
        """Test summarizing a group with single memory item"""
        memory = MemoryItem("Single memory", MemoryType.SHORT_TERM, 0.5, datetime.now())
        
        summary = await context_compressor._summarize_memory_group([memory])
        
        assert summary == memory
    
    @pytest.mark.asyncio
    async def test_summarize_memory_group_multiple_items(self, context_compressor):
        """Test summarizing a group with multiple memory items"""
        now = datetime.now()
        memory_group = [
            MemoryItem(
                "User asked about Python programming", 
                MemoryType.SHORT_TERM, 0.6, now - timedelta(minutes=1),
                metadata={"entities": ["Python"]}
            ),
            MemoryItem(
                "Discussed Python syntax and best practices", 
                MemoryType.CONTEXT, 0.7, now,
                metadata={"entities": ["Python", "syntax"]}
            )
        ]
        
        summary = await context_compressor._summarize_memory_group(memory_group)
        
        assert isinstance(summary, MemoryItem)
        assert summary.memory_type == MemoryType.CONTEXT  # Should pick the higher priority type
        assert summary.importance_score > max(item.importance_score for item in memory_group)
        assert summary.metadata["summarized"] is True
        assert summary.metadata["original_count"] == 2
        assert "Python" in summary.content
    
    @pytest.mark.asyncio
    async def test_generate_memory_summary_single_content(self, context_compressor):
        """Test generating summary from single content"""
        content_list = ["This is a single piece of content"]
        
        summary = await context_compressor._generate_memory_summary(content_list)
        
        assert summary == content_list[0]
    
    @pytest.mark.asyncio
    async def test_generate_memory_summary_multiple_content(self, context_compressor):
        """Test generating summary from multiple content pieces"""
        content_list = [
            "User asked about machine learning. This is important information.",
            "Discussed neural networks and algorithms. User prefers detailed explanations.",
            "Covered deep learning concepts. Remember user's preference for technical details."
        ]
        
        summary = await context_compressor._generate_memory_summary(content_list)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        # Should contain key information from the content
        assert any(keyword in summary.lower() for keyword in ["machine learning", "neural networks", "prefer", "important"])
    
    @pytest.mark.asyncio
    async def test_generate_context_summary(self, context_compressor):
        """Test generating overall context summary"""
        now = datetime.now()
        memories = [
            MemoryItem(
                "User prefers detailed explanations", 
                MemoryType.PREFERENCE, 0.9, now,
                metadata={"entities": ["explanations"]}
            ),
            MemoryItem(
                "Discussed machine learning algorithms", 
                MemoryType.CONTEXT, 0.8, now,
                metadata={"entities": ["machine learning", "algorithms"]}
            ),
            MemoryItem(
                "Important note about Python syntax", 
                MemoryType.SHORT_TERM, 0.7, now,
                metadata={"entities": ["Python", "syntax"]}
            )
        ]
        
        summary = await context_compressor._generate_context_summary(memories, "Previous discussion")
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "Previous discussion" in summary
        assert "Topics discussed" in summary
        assert "preferences" in summary.lower()
    
    @pytest.mark.asyncio
    async def test_estimate_token_count(self, context_compressor):
        """Test token count estimation"""
        memories = [
            MemoryItem("Short memory", MemoryType.SHORT_TERM, 0.5, datetime.now()),
            MemoryItem("This is a longer memory with more content", MemoryType.CONTEXT, 0.7, datetime.now())
        ]
        context_summary = "This is a context summary"
        
        token_count = await context_compressor._estimate_token_count(memories, context_summary)
        
        assert isinstance(token_count, int)
        assert token_count > 0
        # Should be roughly proportional to content length
        total_chars = len(context_summary) + sum(len(m.content) for m in memories)
        expected_tokens = total_chars // 4
        assert abs(token_count - expected_tokens) <= 5  # Allow some variance
    
    @pytest.mark.asyncio
    async def test_prune_context_by_relevance(self, context_compressor):
        """Test pruning context based on relevance to query"""
        now = datetime.now()
        memories = [
            MemoryItem(
                "Python programming language syntax", 
                MemoryType.SHORT_TERM, 0.6, now - timedelta(minutes=1)
            ),
            MemoryItem(
                "Machine learning algorithms discussion", 
                MemoryType.CONTEXT, 0.7, now - timedelta(minutes=5)
            ),
            MemoryItem(
                "Weather forecast for tomorrow", 
                MemoryType.SHORT_TERM, 0.5, now - timedelta(minutes=10)
            ),
            MemoryItem(
                "Python libraries and frameworks", 
                MemoryType.CONTEXT, 0.8, now - timedelta(hours=1)
            )
        ]
        
        query = "Python programming help"
        pruned_memories = await context_compressor.prune_context_by_relevance(
            memories, query, max_items=2
        )
        
        assert len(pruned_memories) == 2
        # Should prioritize Python-related memories
        python_related = sum(1 for memory in pruned_memories if "python" in memory.content.lower())
        assert python_related >= 1
    
    @pytest.mark.asyncio
    async def test_prune_context_no_pruning_needed(self, context_compressor):
        """Test pruning when no pruning is needed"""
        memories = [
            MemoryItem("Memory 1", MemoryType.SHORT_TERM, 0.5, datetime.now()),
            MemoryItem("Memory 2", MemoryType.CONTEXT, 0.7, datetime.now())
        ]
        
        query = "test query"
        pruned_memories = await context_compressor.prune_context_by_relevance(
            memories, query, max_items=5
        )
        
        # Should return all memories since count is below limit
        assert len(pruned_memories) == len(memories)
        assert pruned_memories == memories


class TestUserMemoryStore:
    """Test cases for UserMemoryStore"""
    
    @pytest.fixture
    def user_memory_store(self):
        """Create a user memory store instance for testing"""
        from services.memory_service import UserMemoryStore
        return UserMemoryStore()
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing"""
        return "test_user_123"
    
    @pytest.fixture
    def sample_preferences(self):
        """Sample user preferences for testing"""
        return {
            "response_style": {
                "value": "detailed",
                "confidence": 0.8,
                "source": "explicit",
                "updated_at": datetime.now().isoformat(),
                "interaction_count": 5
            },
            "citation_preference": {
                "value": "inline",
                "confidence": 0.9,
                "source": "learned",
                "updated_at": datetime.now().isoformat(),
                "interaction_count": 3
            }
        }
    
    @pytest.mark.asyncio
    async def test_store_user_preference(self, user_memory_store, sample_user_id):
        """Test storing user preference"""
        with patch.object(user_memory_store, 'get_user_preferences', return_value={}), \
             patch.object(user_memory_store.redis_client, 'set', return_value=True), \
             patch.object(user_memory_store, '_store_preferences_in_db', return_value=True):
            
            result = await user_memory_store.store_user_preference(
                sample_user_id, 
                "response_style", 
                "detailed",
                confidence=0.8,
                source="explicit"
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_user_preferences_from_redis(self, user_memory_store, sample_user_id, sample_preferences):
        """Test getting user preferences from Redis"""
        with patch.object(user_memory_store.redis_client, 'get', return_value=sample_preferences):
            
            preferences = await user_memory_store.get_user_preferences(sample_user_id)
            
            assert preferences == sample_preferences
            assert "response_style" in preferences
            assert preferences["response_style"]["value"] == "detailed"
    
    @pytest.mark.asyncio
    async def test_get_user_preferences_fallback_to_db(self, user_memory_store, sample_user_id, sample_preferences):
        """Test getting user preferences with fallback to database"""
        with patch.object(user_memory_store.redis_client, 'get', return_value=None), \
             patch.object(user_memory_store, '_load_preferences_from_db', return_value=sample_preferences), \
             patch.object(user_memory_store.redis_client, 'set', return_value=True):
            
            preferences = await user_memory_store.get_user_preferences(sample_user_id)
            
            assert preferences == sample_preferences
    
    @pytest.mark.asyncio
    async def test_get_user_preference_specific(self, user_memory_store, sample_user_id):
        """Test getting specific user preference"""
        mock_preferences = {
            "response_style": {
                "value": "detailed",
                "confidence": 0.8
            }
        }
        
        with patch.object(user_memory_store, 'get_user_preferences', return_value=mock_preferences):
            
            preference_value = await user_memory_store.get_user_preference(
                sample_user_id, 
                "response_style"
            )
            
            assert preference_value == "detailed"
    
    @pytest.mark.asyncio
    async def test_get_user_preference_with_default(self, user_memory_store, sample_user_id):
        """Test getting user preference with default value"""
        with patch.object(user_memory_store, 'get_user_preferences', return_value={}):
            
            preference_value = await user_memory_store.get_user_preference(
                sample_user_id, 
                "nonexistent_preference",
                default="default_value"
            )
            
            assert preference_value == "default_value"
    
    @pytest.mark.asyncio
    async def test_learn_preference_from_interaction(self, user_memory_store, sample_user_id):
        """Test learning preferences from interaction data"""
        interaction_data = {
            "response_length": 600,  # Long response
            "citation_requested": True,
            "technical_terms_used": 8,
            "query_domain": "machine_learning",
            "user_feedback": {
                "rating": 5,
                "response_characteristics": {
                    "detail_level": "high"
                }
            }
        }
        
        # Mock current preferences to simulate threshold reached
        mock_current_preferences = {
            "response_style": {"interaction_count": 3}  # Above threshold
        }
        
        with patch.object(user_memory_store, 'get_user_preferences', return_value=mock_current_preferences), \
             patch.object(user_memory_store, 'store_user_preference', return_value=True), \
             patch.object(user_memory_store, '_store_interaction_signal', return_value=True):
            
            learned_preferences = await user_memory_store.learn_preference_from_interaction(
                sample_user_id, 
                interaction_data
            )
            
            assert isinstance(learned_preferences, list)
            # Should learn some preferences based on the interaction data
    
    @pytest.mark.asyncio
    async def test_store_user_context(self, user_memory_store, sample_user_id):
        """Test storing user context"""
        context_data = {
            "recent_topics": ["machine learning", "python"],
            "current_project": "chatbot development"
        }
        
        with patch.object(user_memory_store, 'get_user_context', return_value={}), \
             patch.object(user_memory_store.redis_client, 'set', return_value=True), \
             patch.object(user_memory_store, '_store_context_in_db', return_value=True):
            
            result = await user_memory_store.store_user_context(
                sample_user_id, 
                "current_session", 
                context_data
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_user_context(self, user_memory_store, sample_user_id):
        """Test getting user context"""
        mock_context = {
            "current_session": {
                "data": {"recent_topics": ["AI", "ML"]},
                "stored_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=1)).isoformat()
            }
        }
        
        with patch.object(user_memory_store.redis_client, 'get', return_value=mock_context), \
             patch.object(user_memory_store, '_filter_expired_context', return_value=mock_context):
            
            context = await user_memory_store.get_user_context(sample_user_id)
            
            assert context == mock_context
            assert "current_session" in context
    
    @pytest.mark.asyncio
    async def test_get_personalized_context(self, user_memory_store, sample_user_id):
        """Test getting personalized context for query"""
        mock_preferences = {"response_style": {"value": "detailed", "confidence": 0.8}}
        mock_context = {"recent_topics": {"data": {"topics": ["AI"]}}}
        
        with patch.object(user_memory_store, 'get_user_preferences', return_value=mock_preferences), \
             patch.object(user_memory_store, 'get_user_context', return_value=mock_context), \
             patch.object(user_memory_store, '_get_relevant_conversation_memories', return_value=[]), \
             patch.object(user_memory_store, '_calculate_personalization_level', return_value=0.7):
            
            personalized_context = await user_memory_store.get_personalized_context(
                sample_user_id, 
                "Tell me about AI"
            )
            
            assert isinstance(personalized_context, dict)
            assert "user_preferences" in personalized_context
            assert "user_context" in personalized_context
            assert "conversation_history" in personalized_context
            assert "personalization_level" in personalized_context
            assert personalized_context["personalization_level"] == 0.7
    
    @pytest.mark.asyncio
    async def test_update_domain_expertise(self, user_memory_store, sample_user_id):
        """Test updating domain expertise"""
        mock_preferences = {
            "domain_expertise": {
                "machine_learning": 0.5,
                "python": 0.7
            }
        }
        
        with patch.object(user_memory_store, 'get_user_preferences', return_value=mock_preferences), \
             patch.object(user_memory_store, 'store_user_preference', return_value=True):
            
            result = await user_memory_store.update_domain_expertise(
                sample_user_id, 
                "machine_learning", 
                0.2  # Increase expertise
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_user_domain_expertise(self, user_memory_store, sample_user_id):
        """Test getting user domain expertise"""
        domain_expertise = {
            "machine_learning": 0.8,
            "python": 0.6,
            "data_science": 0.4
        }
        
        with patch.object(user_memory_store, 'get_user_preference', return_value=domain_expertise):
            
            expertise = await user_memory_store.get_user_domain_expertise(sample_user_id)
            
            assert expertise == domain_expertise
            assert expertise["machine_learning"] == 0.8
    
    @pytest.mark.asyncio
    async def test_extract_preference_signals(self, user_memory_store):
        """Test extracting preference signals from interaction"""
        interaction_data = {
            "response_length": 600,  # Should signal detailed preference
            "citation_requested": True,  # Should signal citation preference
            "technical_terms_used": 8,  # Should signal advanced technical level
            "query_domain": "machine_learning"
        }
        
        signals = await user_memory_store._extract_preference_signals(interaction_data)
        
        assert isinstance(signals, list)
        assert len(signals) > 0
        
        # Check for expected signals
        signal_keys = [signal["key"] for signal in signals]
        assert "response_style" in signal_keys
        assert "citation_preference" in signal_keys
        assert "technical_level" in signal_keys
        assert "domain_interest_machine_learning" in signal_keys
    
    @pytest.mark.asyncio
    async def test_filter_expired_context(self, user_memory_store):
        """Test filtering expired context items"""
        now = datetime.now()
        expired_time = now - timedelta(hours=1)
        future_time = now + timedelta(hours=1)
        
        context = {
            "active_item": {
                "data": {"key": "value"},
                "expires_at": future_time.isoformat()
            },
            "expired_item": {
                "data": {"key": "value"},
                "expires_at": expired_time.isoformat()
            },
            "no_expiry_item": {
                "data": {"key": "value"}
            }
        }
        
        filtered_context = await user_memory_store._filter_expired_context(context)
        
        assert "active_item" in filtered_context
        assert "expired_item" not in filtered_context
        assert "no_expiry_item" in filtered_context
    
    @pytest.mark.asyncio
    async def test_format_preferences_for_context(self, user_memory_store):
        """Test formatting preferences for context use"""
        preferences = {
            "response_style": {
                "value": "detailed",
                "confidence": 0.8,
                "source": "explicit"
            },
            "simple_pref": "simple_value"
        }
        
        formatted = await user_memory_store._format_preferences_for_context(preferences)
        
        assert "response_style" in formatted
        assert formatted["response_style"]["value"] == "detailed"
        assert formatted["response_style"]["confidence"] == 0.8
        
        assert "simple_pref" in formatted
        assert formatted["simple_pref"]["value"] == "simple_value"
        assert formatted["simple_pref"]["confidence"] == 1.0
    
    @pytest.mark.asyncio
    async def test_select_relevant_context(self, user_memory_store):
        """Test selecting relevant context for query"""
        user_context = {
            "python_project": {
                "data": {"language": "python", "type": "web_development"},
                "stored_at": datetime.now().isoformat()
            },
            "machine_learning_study": {
                "data": {"topic": "neural networks", "progress": "intermediate"},
                "stored_at": datetime.now().isoformat()
            },
            "unrelated_context": {
                "data": {"topic": "cooking", "skill": "beginner"},
                "stored_at": datetime.now().isoformat()
            }
        }
        
        query = "python machine learning project"
        
        relevant_context = await user_memory_store._select_relevant_context(
            user_context, query, max_items=2
        )
        
        assert len(relevant_context) <= 2
        # Should prioritize python and machine learning related context
        assert "python_project" in relevant_context or "machine_learning_study" in relevant_context
    
    @pytest.mark.asyncio
    async def test_calculate_personalization_level(self, user_memory_store, sample_user_id):
        """Test calculating personalization level"""
        mock_preferences = {"pref1": "value1", "pref2": "value2"}  # 2 preferences
        mock_context = {"ctx1": "value1"}  # 1 context item
        
        with patch.object(user_memory_store, 'get_user_preferences', return_value=mock_preferences), \
             patch.object(user_memory_store, 'get_user_context', return_value=mock_context):
            
            level = await user_memory_store._calculate_personalization_level(sample_user_id)
            
            assert isinstance(level, float)
            assert 0.0 <= level <= 1.0
            # Should be based on amount of preference and context data
            expected_pref_score = min(1.0, 2 / 10)  # 2 preferences out of max 10
            expected_ctx_score = min(1.0, 1 / 5)    # 1 context out of max 5
            expected_level = (expected_pref_score + expected_ctx_score) / 2
            assert abs(level - expected_level) < 0.01


if __name__ == "__main__":
    pytest.main([__file__])