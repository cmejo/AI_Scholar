"""
Memory Management Service for conversation memory, context compression, and user preferences
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from core.redis_client import redis_client
from core.database import SessionLocal, ConversationMemory, UserProfile
from models.schemas import (
    ConversationMemoryCreate, 
    ConversationMemoryResponse,
    MemoryType,
    UserPreferences
)

logger = logging.getLogger(__name__)

class MemoryImportance(Enum):
    LOW = 0.2
    MEDIUM = 0.5
    HIGH = 0.8
    CRITICAL = 1.0

@dataclass
class MemoryItem:
    """Individual memory item with metadata"""
    content: str
    memory_type: MemoryType
    importance_score: float
    timestamp: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ConversationContext:
    """Conversation context with memory items"""
    conversation_id: str
    short_term_memory: List[MemoryItem]
    context_summary: str
    active_entities: List[str]
    last_updated: datetime
    total_tokens: int = 0

class ConversationMemoryManager:
    """Manages conversation memory with Redis backend and importance scoring"""
    
    def __init__(self):
        self.redis_client = redis_client
        self.max_short_term_items = 50
        self.max_context_tokens = 4000
        self.memory_retention_hours = 24
        
    async def store_memory_item(
        self, 
        conversation_id: str, 
        memory_item: MemoryItem
    ) -> bool:
        """Store a single memory item in Redis and database"""
        try:
            # Store in Redis for fast access
            redis_key = f"conversation_memory:{conversation_id}"
            
            # Get existing memory items
            existing_context = await self._get_redis_context(conversation_id)
            if not existing_context:
                existing_context = {
                    "short_term_memory": [],
                    "context_summary": "",
                    "active_entities": [],
                    "last_updated": datetime.now().isoformat(),
                    "total_tokens": 0
                }
            
            # Add new memory item
            memory_dict = {
                "content": memory_item.content,
                "memory_type": memory_item.memory_type.value,
                "importance_score": memory_item.importance_score,
                "timestamp": memory_item.timestamp.isoformat(),
                "expires_at": memory_item.expires_at.isoformat() if memory_item.expires_at else None,
                "metadata": memory_item.metadata
            }
            
            existing_context["short_term_memory"].append(memory_dict)
            existing_context["last_updated"] = datetime.now().isoformat()
            
            # Prune if necessary
            existing_context = await self._prune_memory_items(existing_context)
            
            # Store back in Redis
            expire_seconds = int(self.memory_retention_hours * 3600)
            success = await self.redis_client.set(redis_key, existing_context, expire=expire_seconds)
            
            # Also store in database for persistence
            if success:
                await self._store_in_database(conversation_id, memory_item)
            
            return success
            
        except Exception as e:
            logger.error(f"Error storing memory item: {e}")
            return False
    
    async def store_memory_items(
        self, 
        conversation_id: str, 
        memory_items: List[MemoryItem]
    ) -> bool:
        """Store multiple memory items efficiently"""
        try:
            redis_key = f"conversation_memory:{conversation_id}"
            
            # Get existing context
            existing_context = await self._get_redis_context(conversation_id)
            if not existing_context:
                existing_context = {
                    "short_term_memory": [],
                    "context_summary": "",
                    "active_entities": [],
                    "last_updated": datetime.now().isoformat(),
                    "total_tokens": 0
                }
            
            # Add all memory items
            for memory_item in memory_items:
                memory_dict = {
                    "content": memory_item.content,
                    "memory_type": memory_item.memory_type.value,
                    "importance_score": memory_item.importance_score,
                    "timestamp": memory_item.timestamp.isoformat(),
                    "expires_at": memory_item.expires_at.isoformat() if memory_item.expires_at else None,
                    "metadata": memory_item.metadata
                }
                existing_context["short_term_memory"].append(memory_dict)
            
            existing_context["last_updated"] = datetime.now().isoformat()
            
            # Prune if necessary
            existing_context = await self._prune_memory_items(existing_context)
            
            # Store in Redis
            expire_seconds = int(self.memory_retention_hours * 3600)
            success = await self.redis_client.set(redis_key, existing_context, expire=expire_seconds)
            
            # Store in database
            if success:
                for memory_item in memory_items:
                    await self._store_in_database(conversation_id, memory_item)
            
            return success
            
        except Exception as e:
            logger.error(f"Error storing memory items: {e}")
            return False
    
    async def retrieve_memory_items(
        self, 
        conversation_id: str, 
        memory_type: Optional[MemoryType] = None,
        limit: Optional[int] = None
    ) -> List[MemoryItem]:
        """Retrieve memory items from Redis"""
        try:
            context = await self._get_redis_context(conversation_id)
            if not context:
                return []
            
            memory_items = []
            for item_dict in context.get("short_term_memory", []):
                # Filter by memory type if specified
                if memory_type and item_dict.get("memory_type") != memory_type.value:
                    continue
                
                memory_item = MemoryItem(
                    content=item_dict["content"],
                    memory_type=MemoryType(item_dict["memory_type"]),
                    importance_score=item_dict["importance_score"],
                    timestamp=datetime.fromisoformat(item_dict["timestamp"]),
                    expires_at=datetime.fromisoformat(item_dict["expires_at"]) if item_dict.get("expires_at") else None,
                    metadata=item_dict.get("metadata", {})
                )
                memory_items.append(memory_item)
            
            # Sort by importance and timestamp
            memory_items.sort(key=lambda x: (x.importance_score, x.timestamp), reverse=True)
            
            # Apply limit if specified
            if limit:
                memory_items = memory_items[:limit]
            
            return memory_items
            
        except Exception as e:
            logger.error(f"Error retrieving memory items: {e}")
            return []
    
    async def get_conversation_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get full conversation context"""
        try:
            context_data = await self._get_redis_context(conversation_id)
            if not context_data:
                return None
            
            # Convert memory items
            memory_items = []
            for item_dict in context_data.get("short_term_memory", []):
                memory_item = MemoryItem(
                    content=item_dict["content"],
                    memory_type=MemoryType(item_dict["memory_type"]),
                    importance_score=item_dict["importance_score"],
                    timestamp=datetime.fromisoformat(item_dict["timestamp"]),
                    expires_at=datetime.fromisoformat(item_dict["expires_at"]) if item_dict.get("expires_at") else None,
                    metadata=item_dict.get("metadata", {})
                )
                memory_items.append(memory_item)
            
            return ConversationContext(
                conversation_id=conversation_id,
                short_term_memory=memory_items,
                context_summary=context_data.get("context_summary", ""),
                active_entities=context_data.get("active_entities", []),
                last_updated=datetime.fromisoformat(context_data["last_updated"]),
                total_tokens=context_data.get("total_tokens", 0)
            )
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return None
    
    async def calculate_importance_score(
        self, 
        content: str, 
        memory_type: MemoryType,
        context: Dict[str, Any] = None
    ) -> float:
        """Calculate importance score for memory item"""
        try:
            # Base score based on memory type
            type_weights = {
                MemoryType.SHORT_TERM: 0.3,
                MemoryType.LONG_TERM: 0.7,
                MemoryType.CONTEXT: 0.6,
                MemoryType.PREFERENCE: 0.85
            }
            base_score = type_weights.get(memory_type, 0.5)
            
            # Adjust based on content characteristics
            content_lower = content.lower()
            
            # Higher importance for user preferences and corrections (highest priority)
            if any(word in content_lower for word in ["prefer", "like", "dislike", "correct", "wrong"]):
                base_score += 0.2
            
            # Higher importance for questions and decisions
            elif any(word in content_lower for word in ["?", "decide", "important", "remember", "note"]):
                base_score += 0.15
            
            # Higher importance for specific entities or technical terms
            if context and context.get("entities"):
                base_score += min(0.15, len(context["entities"]) * 0.03)
            
            # Length factor (moderate length gets higher score)
            content_length = len(content.split())
            if 10 <= content_length <= 50:
                base_score += 0.05
            elif content_length > 100:
                base_score -= 0.05
            
            # Ensure score is within bounds
            return max(0.0, min(1.0, base_score))
            
        except Exception as e:
            logger.error(f"Error calculating importance score: {e}")
            return 0.5
    
    async def prune_expired_memories(self, conversation_id: str) -> int:
        """Remove expired memory items"""
        try:
            context = await self._get_redis_context(conversation_id)
            if not context:
                return 0
            
            current_time = datetime.now()
            original_count = len(context.get("short_term_memory", []))
            
            # Filter out expired items
            active_memories = []
            for item_dict in context.get("short_term_memory", []):
                expires_at = item_dict.get("expires_at")
                if expires_at:
                    expires_datetime = datetime.fromisoformat(expires_at)
                    if expires_datetime > current_time:
                        active_memories.append(item_dict)
                else:
                    active_memories.append(item_dict)
            
            context["short_term_memory"] = active_memories
            context["last_updated"] = current_time.isoformat()
            
            # Update Redis
            redis_key = f"conversation_memory:{conversation_id}"
            expire_seconds = int(self.memory_retention_hours * 3600)
            await self.redis_client.set(redis_key, context, expire=expire_seconds)
            
            pruned_count = original_count - len(active_memories)
            if pruned_count > 0:
                logger.info(f"Pruned {pruned_count} expired memories from conversation {conversation_id}")
            
            return pruned_count
            
        except Exception as e:
            logger.error(f"Error pruning expired memories: {e}")
            return 0
    
    async def clear_conversation_memory(self, conversation_id: str) -> bool:
        """Clear all memory for a conversation"""
        try:
            redis_key = f"conversation_memory:{conversation_id}"
            return await self.redis_client.delete(redis_key)
        except Exception as e:
            logger.error(f"Error clearing conversation memory: {e}")
            return False
    
    async def _get_redis_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation context from Redis"""
        redis_key = f"conversation_memory:{conversation_id}"
        return await self.redis_client.get(redis_key)
    
    async def _prune_memory_items(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prune memory items based on importance and count limits"""
        memory_items = context.get("short_term_memory", [])
        
        if len(memory_items) <= self.max_short_term_items:
            return context
        
        # Sort by importance score and timestamp
        memory_items.sort(
            key=lambda x: (x["importance_score"], x["timestamp"]), 
            reverse=True
        )
        
        # Keep only the most important items
        context["short_term_memory"] = memory_items[:self.max_short_term_items]
        
        logger.info(f"Pruned memory items to {self.max_short_term_items} most important items")
        return context
    
    async def _store_in_database(self, conversation_id: str, memory_item: MemoryItem) -> bool:
        """Store memory item in database for persistence"""
        try:
            db = SessionLocal()
            
            db_memory = ConversationMemory(
                conversation_id=conversation_id,
                memory_type=memory_item.memory_type.value,
                content=memory_item.content,
                importance_score=memory_item.importance_score,
                timestamp=memory_item.timestamp,
                expires_at=memory_item.expires_at,
                memory_metadata=memory_item.metadata
            )
            
            db.add(db_memory)
            db.commit()
            db.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing memory in database: {e}")
            if 'db' in locals():
                db.close()
            return False

class ContextCompressor:
    """Handles context compression and summarization for long conversations"""
    
    def __init__(self):
        self.max_context_length = 4000  # tokens
        self.compression_ratio = 0.3  # Target compression ratio
        self.min_importance_threshold = 0.4
        
    async def compress_conversation_context(
        self, 
        conversation_context: ConversationContext,
        target_length: Optional[int] = None
    ) -> ConversationContext:
        """Compress conversation context by summarizing and pruning"""
        try:
            target_length = target_length or self.max_context_length
            
            if conversation_context.total_tokens <= target_length:
                return conversation_context
            
            # Step 1: Remove low-importance items
            filtered_memories = await self._filter_by_importance(
                conversation_context.short_term_memory
            )
            
            # Step 2: Group related memories for summarization
            memory_groups = await self._group_related_memories(filtered_memories)
            
            # Step 3: Summarize each group
            compressed_memories = []
            for group in memory_groups:
                if len(group) > 1:
                    summary = await self._summarize_memory_group(group)
                    compressed_memories.append(summary)
                else:
                    compressed_memories.extend(group)
            
            # Step 4: Generate overall context summary
            context_summary = await self._generate_context_summary(
                compressed_memories, 
                conversation_context.context_summary
            )
            
            # Step 5: Calculate new token count (approximation)
            new_token_count = await self._estimate_token_count(
                compressed_memories, 
                context_summary
            )
            
            return ConversationContext(
                conversation_id=conversation_context.conversation_id,
                short_term_memory=compressed_memories,
                context_summary=context_summary,
                active_entities=conversation_context.active_entities,
                last_updated=datetime.now(),
                total_tokens=new_token_count
            )
            
        except Exception as e:
            logger.error(f"Error compressing conversation context: {e}")
            return conversation_context
    
    async def _filter_by_importance(
        self, 
        memories: List[MemoryItem]
    ) -> List[MemoryItem]:
        """Filter memories by importance threshold"""
        return [
            memory for memory in memories 
            if memory.importance_score >= self.min_importance_threshold
        ]
    
    async def _group_related_memories(
        self, 
        memories: List[MemoryItem]
    ) -> List[List[MemoryItem]]:
        """Group related memories for efficient summarization"""
        groups = []
        processed = set()
        
        for i, memory in enumerate(memories):
            if i in processed:
                continue
                
            group = [memory]
            processed.add(i)
            
            # Find related memories based on content similarity and time proximity
            for j, other_memory in enumerate(memories[i+1:], i+1):
                if j in processed:
                    continue
                
                if await self._are_memories_related(memory, other_memory):
                    group.append(other_memory)
                    processed.add(j)
            
            groups.append(group)
        
        return groups
    
    async def _are_memories_related(
        self, 
        memory1: MemoryItem, 
        memory2: MemoryItem
    ) -> bool:
        """Check if two memories are related and can be grouped"""
        # Time proximity (within 10 minutes)
        time_diff = abs((memory1.timestamp - memory2.timestamp).total_seconds())
        if time_diff > 600:  # 10 minutes
            return False
        
        # Content similarity (simple keyword overlap)
        words1 = set(memory1.content.lower().split())
        words2 = set(memory2.content.lower().split())
        
        # Remove common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should"}
        words1 = words1 - stop_words
        words2 = words2 - stop_words
        
        if not words1 or not words2:
            return False
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        similarity = intersection / union if union > 0 else 0
        
        return similarity > 0.3  # 30% similarity threshold
    
    async def _summarize_memory_group(
        self, 
        memory_group: List[MemoryItem]
    ) -> MemoryItem:
        """Summarize a group of related memories into a single memory item"""
        if len(memory_group) == 1:
            return memory_group[0]
        
        # Combine content from all memories
        combined_content = []
        combined_metadata = {}
        max_importance = 0
        latest_timestamp = memory_group[0].timestamp
        memory_types = set()
        
        for memory in memory_group:
            combined_content.append(memory.content)
            max_importance = max(max_importance, memory.importance_score)
            latest_timestamp = max(latest_timestamp, memory.timestamp)
            memory_types.add(memory.memory_type)
            
            # Merge metadata
            if memory.metadata:
                for key, value in memory.metadata.items():
                    if key in combined_metadata:
                        if isinstance(combined_metadata[key], list):
                            if isinstance(value, list):
                                combined_metadata[key].extend(value)
                            else:
                                combined_metadata[key].append(value)
                        else:
                            combined_metadata[key] = [combined_metadata[key], value]
                    else:
                        combined_metadata[key] = value
        
        # Create summary content
        summary_content = await self._generate_memory_summary(combined_content)
        
        # Determine primary memory type
        primary_type = MemoryType.CONTEXT
        if MemoryType.PREFERENCE in memory_types:
            primary_type = MemoryType.PREFERENCE
        elif MemoryType.LONG_TERM in memory_types:
            primary_type = MemoryType.LONG_TERM
        
        # Add summarization metadata
        combined_metadata["summarized"] = True
        combined_metadata["original_count"] = len(memory_group)
        combined_metadata["compression_timestamp"] = datetime.now().isoformat()
        
        return MemoryItem(
            content=summary_content,
            memory_type=primary_type,
            importance_score=min(1.0, max_importance + 0.1),  # Slight boost for summarized content
            timestamp=latest_timestamp,
            metadata=combined_metadata
        )
    
    async def _generate_memory_summary(self, content_list: List[str]) -> str:
        """Generate a summary from multiple memory contents"""
        # Simple extractive summarization for now
        # In a real implementation, this would use an LLM
        
        if len(content_list) == 1:
            return content_list[0]
        
        # Find the most informative sentences
        all_sentences = []
        for content in content_list:
            sentences = content.split('. ')
            all_sentences.extend(sentences)
        
        # Remove duplicates and very short sentences
        unique_sentences = []
        seen = set()
        for sentence in all_sentences:
            sentence = sentence.strip()
            if len(sentence) > 10 and sentence.lower() not in seen:
                unique_sentences.append(sentence)
                seen.add(sentence.lower())
        
        # Take the most informative sentences (simple heuristic)
        if len(unique_sentences) <= 3:
            return '. '.join(unique_sentences)
        
        # Score sentences by length and keyword density
        scored_sentences = []
        for sentence in unique_sentences:
            words = sentence.split()
            # Prefer moderate length sentences with important keywords
            score = len(words) * 0.1
            if any(word.lower() in ["important", "prefer", "remember", "note", "correct", "wrong"] for word in words):
                score += 2
            scored_sentences.append((score, sentence))
        
        # Take top 3 sentences
        scored_sentences.sort(reverse=True)
        top_sentences = [sentence for _, sentence in scored_sentences[:3]]
        
        return '. '.join(top_sentences)
    
    async def _generate_context_summary(
        self, 
        memories: List[MemoryItem], 
        existing_summary: str
    ) -> str:
        """Generate overall context summary"""
        # Extract key topics and themes
        topics = set()
        preferences = []
        important_facts = []
        
        for memory in memories:
            # Extract entities from metadata
            if memory.metadata and "entities" in memory.metadata:
                if isinstance(memory.metadata["entities"], list):
                    topics.update(memory.metadata["entities"])
            
            # Categorize by memory type
            if memory.memory_type == MemoryType.PREFERENCE:
                preferences.append(memory.content)
            elif memory.importance_score > 0.7:
                important_facts.append(memory.content)
        
        # Build summary components
        summary_parts = []
        
        if topics:
            topic_list = list(topics)[:5]  # Top 5 topics
            summary_parts.append(f"Topics discussed: {', '.join(topic_list)}")
        
        if preferences:
            summary_parts.append(f"User preferences: {len(preferences)} preferences noted")
        
        if important_facts:
            summary_parts.append(f"Key information: {len(important_facts)} important facts")
        
        # Combine with existing summary if available
        if existing_summary and existing_summary.strip():
            summary_parts.insert(0, f"Previous context: {existing_summary}")
        
        return ". ".join(summary_parts) if summary_parts else "No significant context available"
    
    async def _estimate_token_count(
        self, 
        memories: List[MemoryItem], 
        context_summary: str
    ) -> int:
        """Estimate token count for memories and summary"""
        # Simple approximation: 1 token ≈ 4 characters
        total_chars = len(context_summary)
        
        for memory in memories:
            total_chars += len(memory.content)
            if memory.metadata:
                total_chars += len(str(memory.metadata))
        
        return total_chars // 4
    
    async def prune_context_by_relevance(
        self, 
        memories: List[MemoryItem], 
        current_query: str,
        max_items: int = 20
    ) -> List[MemoryItem]:
        """Prune context based on relevance to current query"""
        if len(memories) <= max_items:
            return memories
        
        # Score memories by relevance to current query
        query_words = set(current_query.lower().split())
        scored_memories = []
        
        for memory in memories:
            memory_words = set(memory.content.lower().split())
            
            # Calculate relevance score
            relevance_score = 0
            
            # Word overlap
            overlap = len(query_words.intersection(memory_words))
            relevance_score += overlap * 0.3
            
            # Importance score
            relevance_score += memory.importance_score * 0.4
            
            # Recency (more recent = higher score)
            hours_ago = (datetime.now() - memory.timestamp).total_seconds() / 3600
            recency_score = max(0, 1 - (hours_ago / 24))  # Decay over 24 hours
            relevance_score += recency_score * 0.3
            
            scored_memories.append((relevance_score, memory))
        
        # Sort by relevance and take top items
        scored_memories.sort(reverse=True)
        return [memory for _, memory in scored_memories[:max_items]]


class UserMemoryStore:
    """Manages long-term user memory and preferences"""
    
    def __init__(self):
        self.redis_client = redis_client
        self.preference_learning_threshold = 3  # Number of interactions to establish preference
        self.memory_retention_days = 30
        
    async def store_user_preference(
        self, 
        user_id: str, 
        preference_key: str, 
        preference_value: Any,
        confidence: float = 1.0,
        source: str = "explicit"
    ) -> bool:
        """Store or update user preference"""
        try:
            # Get existing preferences
            preferences = await self.get_user_preferences(user_id)
            
            # Update preference with metadata
            preferences[preference_key] = {
                "value": preference_value,
                "confidence": confidence,
                "source": source,  # explicit, learned, inferred
                "updated_at": datetime.now().isoformat(),
                "interaction_count": preferences.get(preference_key, {}).get("interaction_count", 0) + 1
            }
            
            # Store in Redis for fast access
            redis_key = f"user_preferences:{user_id}"
            success = await self.redis_client.set(redis_key, preferences)
            
            # Also store in database for persistence
            if success:
                await self._store_preferences_in_db(user_id, preferences)
            
            return success
            
        except Exception as e:
            logger.error(f"Error storing user preference: {e}")
            return False
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get all user preferences"""
        try:
            # Try Redis first
            redis_key = f"user_preferences:{user_id}"
            preferences = await self.redis_client.get(redis_key)
            
            if preferences:
                return preferences
            
            # Fallback to database
            preferences = await self._load_preferences_from_db(user_id)
            
            # Cache in Redis
            if preferences:
                await self.redis_client.set(redis_key, preferences, expire=3600)
            
            return preferences or {}
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return {}
    
    async def get_user_preference(
        self, 
        user_id: str, 
        preference_key: str, 
        default: Any = None
    ) -> Any:
        """Get specific user preference"""
        preferences = await self.get_user_preferences(user_id)
        preference_data = preferences.get(preference_key)
        
        if preference_data and isinstance(preference_data, dict):
            return preference_data.get("value", default)
        
        return preference_data or default
    
    async def learn_preference_from_interaction(
        self, 
        user_id: str, 
        interaction_data: Dict[str, Any]
    ) -> List[str]:
        """Learn user preferences from interaction patterns"""
        try:
            learned_preferences = []
            
            # Analyze interaction for preference signals
            preference_signals = await self._extract_preference_signals(interaction_data)
            
            for signal in preference_signals:
                preference_key = signal["key"]
                preference_value = signal["value"]
                confidence = signal["confidence"]
                
                # Get current preference data
                current_preferences = await self.get_user_preferences(user_id)
                current_pref = current_preferences.get(preference_key, {})
                
                # Update interaction count
                interaction_count = current_pref.get("interaction_count", 0) + 1
                
                # Only establish learned preference after threshold interactions
                if interaction_count >= self.preference_learning_threshold:
                    await self.store_user_preference(
                        user_id, 
                        preference_key, 
                        preference_value,
                        confidence=confidence,
                        source="learned"
                    )
                    learned_preferences.append(preference_key)
                else:
                    # Store interaction data for future learning
                    await self._store_interaction_signal(user_id, preference_key, signal)
            
            return learned_preferences
            
        except Exception as e:
            logger.error(f"Error learning preferences from interaction: {e}")
            return []
    
    async def store_user_context(
        self, 
        user_id: str, 
        context_key: str, 
        context_data: Dict[str, Any],
        expires_in_days: Optional[int] = None
    ) -> bool:
        """Store user context information"""
        try:
            expires_in_days = expires_in_days or self.memory_retention_days
            
            # Get existing context
            user_context = await self.get_user_context(user_id)
            
            # Update context
            user_context[context_key] = {
                "data": context_data,
                "stored_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=expires_in_days)).isoformat()
            }
            
            # Store in Redis
            redis_key = f"user_context:{user_id}"
            expire_seconds = expires_in_days * 24 * 3600
            success = await self.redis_client.set(redis_key, user_context, expire=expire_seconds)
            
            # Store in database
            if success:
                await self._store_context_in_db(user_id, context_key, context_data, expires_in_days)
            
            return success
            
        except Exception as e:
            logger.error(f"Error storing user context: {e}")
            return False
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get user context information"""
        try:
            # Try Redis first
            redis_key = f"user_context:{user_id}"
            context = await self.redis_client.get(redis_key)
            
            if context:
                # Filter out expired context
                return await self._filter_expired_context(context)
            
            # Fallback to database
            context = await self._load_context_from_db(user_id)
            
            # Cache in Redis
            if context:
                await self.redis_client.set(redis_key, context, expire=3600)
            
            return context or {}
            
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return {}
    
    async def get_personalized_context(
        self, 
        user_id: str, 
        query: str,
        max_context_items: int = 10
    ) -> Dict[str, Any]:
        """Get personalized context for query response"""
        try:
            # Get user preferences
            preferences = await self.get_user_preferences(user_id)
            
            # Get relevant user context
            user_context = await self.get_user_context(user_id)
            
            # Get conversation history context
            conversation_memories = await self._get_relevant_conversation_memories(user_id, query)
            
            # Build personalized context
            personalized_context = {
                "user_preferences": await self._format_preferences_for_context(preferences),
                "user_context": await self._select_relevant_context(user_context, query, max_context_items),
                "conversation_history": conversation_memories,
                "personalization_level": await self._calculate_personalization_level(user_id)
            }
            
            return personalized_context
            
        except Exception as e:
            logger.error(f"Error getting personalized context: {e}")
            return {}
    
    async def update_domain_expertise(
        self, 
        user_id: str, 
        domain: str, 
        expertise_delta: float
    ) -> bool:
        """Update user's domain expertise level"""
        try:
            preferences = await self.get_user_preferences(user_id)
            
            # Get current domain expertise
            domain_expertise = preferences.get("domain_expertise", {})
            if not isinstance(domain_expertise, dict):
                domain_expertise = {}
            
            # Update expertise level
            current_level = domain_expertise.get(domain, 0.0)
            new_level = max(0.0, min(1.0, current_level + expertise_delta))
            domain_expertise[domain] = new_level
            
            # Store updated expertise
            return await self.store_user_preference(
                user_id, 
                "domain_expertise", 
                domain_expertise,
                source="learned"
            )
            
        except Exception as e:
            logger.error(f"Error updating domain expertise: {e}")
            return False
    
    async def get_user_domain_expertise(self, user_id: str) -> Dict[str, float]:
        """Get user's domain expertise levels"""
        domain_expertise = await self.get_user_preference(user_id, "domain_expertise", {})
        return domain_expertise if isinstance(domain_expertise, dict) else {}
    
    async def _extract_preference_signals(
        self, 
        interaction_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract preference signals from interaction data"""
        signals = []
        
        # Response style preferences
        if "response_length" in interaction_data:
            length = interaction_data["response_length"]
            if length > 500:
                signals.append({
                    "key": "response_style",
                    "value": "detailed",
                    "confidence": 0.7
                })
            elif length < 200:
                signals.append({
                    "key": "response_style",
                    "value": "concise",
                    "confidence": 0.7
                })
        
        # Citation preferences
        if "citation_requested" in interaction_data:
            if interaction_data["citation_requested"]:
                signals.append({
                    "key": "citation_preference",
                    "value": "always",
                    "confidence": 0.8
                })
        
        # Technical level preferences
        if "technical_terms_used" in interaction_data:
            term_count = interaction_data["technical_terms_used"]
            if term_count > 5:
                signals.append({
                    "key": "technical_level",
                    "value": "advanced",
                    "confidence": 0.6
                })
            elif term_count == 0:
                signals.append({
                    "key": "technical_level",
                    "value": "beginner",
                    "confidence": 0.6
                })
        
        # Domain interest
        if "query_domain" in interaction_data:
            domain = interaction_data["query_domain"]
            signals.append({
                "key": f"domain_interest_{domain}",
                "value": True,
                "confidence": 0.5
            })
        
        # Feedback-based preferences
        if "user_feedback" in interaction_data:
            feedback = interaction_data["user_feedback"]
            if feedback.get("rating", 0) >= 4:
                # Positive feedback - reinforce current approach
                if "response_characteristics" in feedback:
                    for char, value in feedback["response_characteristics"].items():
                        signals.append({
                            "key": char,
                            "value": value,
                            "confidence": 0.9
                        })
        
        return signals
    
    async def _store_interaction_signal(
        self, 
        user_id: str, 
        preference_key: str, 
        signal: Dict[str, Any]
    ) -> bool:
        """Store interaction signal for future preference learning"""
        try:
            redis_key = f"interaction_signals:{user_id}:{preference_key}"
            
            # Get existing signals
            existing_signals = await self.redis_client.get(redis_key) or []
            
            # Add new signal
            signal["timestamp"] = datetime.now().isoformat()
            existing_signals.append(signal)
            
            # Keep only recent signals (last 50)
            if len(existing_signals) > 50:
                existing_signals = existing_signals[-50:]
            
            # Store back
            return await self.redis_client.set(redis_key, existing_signals, expire=86400 * 7)  # 7 days
            
        except Exception as e:
            logger.error(f"Error storing interaction signal: {e}")
            return False
    
    async def _store_preferences_in_db(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Store preferences in database"""
        try:
            db = SessionLocal()
            
            # Check if user profile exists
            from core.database import UserProfile
            user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            if user_profile:
                user_profile.preferences = preferences
                user_profile.updated_at = datetime.now()
            else:
                user_profile = UserProfile(
                    user_id=user_id,
                    preferences=preferences
                )
                db.add(user_profile)
            
            db.commit()
            db.close()
            return True
            
        except Exception as e:
            logger.error(f"Error storing preferences in database: {e}")
            if 'db' in locals():
                db.close()
            return False
    
    async def _load_preferences_from_db(self, user_id: str) -> Dict[str, Any]:
        """Load preferences from database"""
        try:
            db = SessionLocal()
            
            from core.database import UserProfile
            user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            if user_profile and user_profile.preferences:
                preferences = user_profile.preferences
                db.close()
                return preferences
            
            db.close()
            return {}
            
        except Exception as e:
            logger.error(f"Error loading preferences from database: {e}")
            if 'db' in locals():
                db.close()
            return {}
    
    async def _store_context_in_db(
        self, 
        user_id: str, 
        context_key: str, 
        context_data: Dict[str, Any],
        expires_in_days: int
    ) -> bool:
        """Store context in database"""
        # For now, we'll rely on Redis for context storage
        # In a production system, you might want to store important context in DB
        return True
    
    async def _load_context_from_db(self, user_id: str) -> Dict[str, Any]:
        """Load context from database"""
        # For now, we'll rely on Redis for context storage
        return {}
    
    async def _filter_expired_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Filter out expired context items"""
        current_time = datetime.now()
        filtered_context = {}
        
        for key, value in context.items():
            if isinstance(value, dict) and "expires_at" in value:
                expires_at = datetime.fromisoformat(value["expires_at"])
                if expires_at > current_time:
                    filtered_context[key] = value
            else:
                filtered_context[key] = value
        
        return filtered_context
    
    async def _get_relevant_conversation_memories(
        self, 
        user_id: str, 
        query: str
    ) -> List[Dict[str, Any]]:
        """Get relevant conversation memories for the user"""
        # This would integrate with conversation memory manager
        # For now, return empty list
        return []
    
    async def _format_preferences_for_context(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Format preferences for use in context"""
        formatted = {}
        
        for key, value in preferences.items():
            if isinstance(value, dict) and "value" in value:
                # Extract just the value and confidence for context
                formatted[key] = {
                    "value": value["value"],
                    "confidence": value.get("confidence", 1.0)
                }
            else:
                formatted[key] = {"value": value, "confidence": 1.0}
        
        return formatted
    
    async def _select_relevant_context(
        self, 
        user_context: Dict[str, Any], 
        query: str, 
        max_items: int
    ) -> Dict[str, Any]:
        """Select most relevant context items for the query"""
        # Simple relevance scoring based on keyword overlap
        query_words = set(query.lower().split())
        scored_context = []
        
        for key, value in user_context.items():
            if isinstance(value, dict) and "data" in value:
                context_text = str(value["data"]).lower()
                context_words = set(context_text.split())
                
                # Calculate relevance score
                overlap = len(query_words.intersection(context_words))
                relevance_score = overlap / len(query_words) if query_words else 0
                
                scored_context.append((relevance_score, key, value))
        
        # Sort by relevance and take top items
        scored_context.sort(reverse=True)
        
        relevant_context = {}
        for _, key, value in scored_context[:max_items]:
            relevant_context[key] = value
        
        return relevant_context
    
    async def _calculate_personalization_level(self, user_id: str) -> float:
        """Calculate how much personalization data is available for user"""
        preferences = await self.get_user_preferences(user_id)
        context = await self.get_user_context(user_id)
        
        # Simple scoring based on amount of data available
        preference_score = min(1.0, len(preferences) / 10)  # Max score at 10 preferences
        context_score = min(1.0, len(context) / 5)  # Max score at 5 context items
        
        return (preference_score + context_score) / 2


# Global instances
conversation_memory_manager = ConversationMemoryManager()
context_compressor = ContextCompressor()
user_memory_store = UserMemoryStore()