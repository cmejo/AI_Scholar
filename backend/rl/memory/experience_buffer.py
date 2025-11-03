"""
Experience buffer implementation for the RL system.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Iterator
import numpy as np
import random
from collections import deque
import heapq
from dataclasses import asdict
import pickle
import json

from ..models.conversation_models import ConversationExperience, ConversationState, Action
from ..models.reward_models import MultiObjectiveReward
from ..core.config import RLConfig

logger = logging.getLogger(__name__)


class ExperienceBuffer:
    """Basic experience buffer for storing conversation experiences."""
    
    def __init__(self, config: RLConfig, max_size: int = 10000):
        self.config = config
        self.max_size = max_size
        self.experiences: List[ConversationExperience] = []
        self.current_size = 0
        
    async def store_experience(self, experience: ConversationExperience) -> None:
        """Store a new experience in the buffer."""
        
        # Add experience
        self.experiences.append(experience)
        self.current_size += 1
        
        # Remove oldest if buffer is full
        if self.current_size > self.max_size:
            removed = self.experiences.pop(0)
            self.current_size -= 1
            logger.debug(f"Removed oldest experience: {removed.experience_id}")
        
        logger.debug(f"Stored experience: {experience.experience_id}")
    
    async def sample_batch(self, batch_size: int) -> List[ConversationExperience]:
        """Sample a random batch of experiences."""
        
        if self.current_size == 0:
            return []
        
        sample_size = min(batch_size, self.current_size)
        return random.sample(self.experiences, sample_size)
    
    async def get_recent_experiences(self, num_experiences: int) -> List[ConversationExperience]:
        """Get the most recent experiences."""
        
        return self.experiences[-num_experiences:] if self.experiences else []
    
    def get_size(self) -> int:
        """Get current buffer size."""
        return self.current_size
    
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return self.current_size == 0
    
    def clear(self) -> None:
        """Clear all experiences from buffer."""
        self.experiences.clear()
        self.current_size = 0
        logger.info("Experience buffer cleared")


class PrioritizedExperienceBuffer(ExperienceBuffer):
    """Prioritized experience replay buffer."""
    
    def __init__(self, config: RLConfig, max_size: int = 10000, alpha: float = 0.6):
        super().__init__(config, max_size)
        self.alpha = alpha  # Prioritization exponent
        self.priorities = []
        self.max_priority = 1.0
        
    async def store_experience(self, experience: ConversationExperience) -> None:
        """Store experience with initial priority."""
        
        # Calculate initial priority based on reward magnitude
        initial_priority = abs(experience.reward.total_reward) + 1e-6
        initial_priority = initial_priority ** self.alpha
        
        # Store experience
        await super().store_experience(experience)
        
        # Store priority
        self.priorities.append(initial_priority)
        self.max_priority = max(self.max_priority, initial_priority)
        
        # Remove oldest priority if buffer is full
        if len(self.priorities) > self.max_size:
            self.priorities.pop(0)
    
    async def sample_batch(
        self, 
        batch_size: int, 
        beta: float = 0.4
    ) -> Tuple[List[ConversationExperience], np.ndarray, np.ndarray]:
        """
        Sample batch with prioritized replay.
        
        Returns:
            experiences: Sampled experiences
            indices: Indices of sampled experiences
            weights: Importance sampling weights
        """
        
        if self.current_size == 0:
            return [], np.array([]), np.array([])
        
        sample_size = min(batch_size, self.current_size)
        
        # Calculate sampling probabilities
        priorities = np.array(self.priorities[:self.current_size])
        probabilities = priorities / priorities.sum()
        
        # Sample indices
        indices = np.random.choice(
            self.current_size, 
            size=sample_size, 
            p=probabilities,
            replace=False
        )
        
        # Calculate importance sampling weights
        weights = (self.current_size * probabilities[indices]) ** (-beta)
        weights = weights / weights.max()  # Normalize
        
        # Get sampled experiences
        sampled_experiences = [self.experiences[i] for i in indices]
        
        return sampled_experiences, indices, weights
    
    async def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray) -> None:
        """Update priorities based on TD errors."""
        
        for idx, td_error in zip(indices, td_errors):
            if 0 <= idx < len(self.priorities):
                priority = (abs(td_error) + 1e-6) ** self.alpha
                self.priorities[idx] = priority
                self.max_priority = max(self.max_priority, priority)
    
    def clear(self) -> None:
        """Clear buffer and priorities."""
        super().clear()
        self.priorities.clear()
        self.max_priority = 1.0


class ConversationExperienceBuffer(PrioritizedExperienceBuffer):
    """Specialized buffer for conversation-level experience management."""
    
    def __init__(self, config: RLConfig, max_size: int = 10000):
        super().__init__(config, max_size)
        self.conversation_groups: Dict[str, List[int]] = {}  # conversation_id -> experience indices
        self.user_experiences: Dict[str, List[int]] = {}     # user_id -> experience indices
        
    async def store_experience(self, experience: ConversationExperience) -> None:
        """Store experience with conversation grouping."""
        
        # Store experience
        await super().store_experience(experience)
        
        # Update conversation grouping
        conv_id = experience.state.conversation_id
        user_id = experience.state.user_id
        experience_idx = self.current_size - 1
        
        if conv_id not in self.conversation_groups:
            self.conversation_groups[conv_id] = []
        self.conversation_groups[conv_id].append(experience_idx)
        
        if user_id not in self.user_experiences:
            self.user_experiences[user_id] = []
        self.user_experiences[user_id].append(experience_idx)
        
        # Clean up old conversation groups
        await self._cleanup_conversation_groups()
    
    async def sample_conversation_batch(self, num_conversations: int) -> List[List[ConversationExperience]]:
        """Sample complete conversations."""
        
        if not self.conversation_groups:
            return []
        
        # Sample conversation IDs
        available_conversations = list(self.conversation_groups.keys())
        sample_size = min(num_conversations, len(available_conversations))
        sampled_conv_ids = random.sample(available_conversations, sample_size)
        
        # Get experiences for each conversation
        conversation_batches = []
        for conv_id in sampled_conv_ids:
            indices = self.conversation_groups[conv_id]
            # Filter valid indices
            valid_indices = [idx for idx in indices if idx < self.current_size]
            experiences = [self.experiences[idx] for idx in valid_indices]
            if experiences:
                conversation_batches.append(experiences)
        
        return conversation_batches
    
    async def sample_user_experiences(self, user_id: str, max_experiences: int = 50) -> List[ConversationExperience]:
        """Sample experiences for a specific user."""
        
        if user_id not in self.user_experiences:
            return []
        
        indices = self.user_experiences[user_id]
        # Filter valid indices
        valid_indices = [idx for idx in indices if idx < self.current_size]
        
        if not valid_indices:
            return []
        
        # Sample from user's experiences
        sample_size = min(max_experiences, len(valid_indices))
        sampled_indices = random.sample(valid_indices, sample_size)
        
        return [self.experiences[idx] for idx in sampled_indices]
    
    async def get_conversation_trajectory(self, conversation_id: str) -> List[ConversationExperience]:
        """Get complete trajectory for a conversation."""
        
        if conversation_id not in self.conversation_groups:
            return []
        
        indices = self.conversation_groups[conversation_id]
        # Filter valid indices and sort by timestamp
        valid_experiences = []
        for idx in indices:
            if idx < self.current_size:
                valid_experiences.append(self.experiences[idx])
        
        # Sort by timestamp
        valid_experiences.sort(key=lambda x: x.timestamp)
        return valid_experiences
    
    async def _cleanup_conversation_groups(self) -> None:
        """Clean up conversation groups with invalid indices."""
        
        # Remove conversation groups with no valid indices
        to_remove = []
        for conv_id, indices in self.conversation_groups.items():
            valid_indices = [idx for idx in indices if idx < self.current_size]
            if not valid_indices:
                to_remove.append(conv_id)
            else:
                self.conversation_groups[conv_id] = valid_indices
        
        for conv_id in to_remove:
            del self.conversation_groups[conv_id]
        
        # Clean up user experiences
        to_remove_users = []
        for user_id, indices in self.user_experiences.items():
            valid_indices = [idx for idx in indices if idx < self.current_size]
            if not valid_indices:
                to_remove_users.append(user_id)
            else:
                self.user_experiences[user_id] = valid_indices
        
        for user_id in to_remove_users:
            del self.user_experiences[user_id]
    
    def get_conversation_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored conversations."""
        
        total_conversations = len(self.conversation_groups)
        
        if total_conversations == 0:
            return {"total_conversations": 0}
        
        # Calculate conversation lengths
        conversation_lengths = []
        for indices in self.conversation_groups.values():
            valid_indices = [idx for idx in indices if idx < self.current_size]
            conversation_lengths.append(len(valid_indices))
        
        # Calculate user statistics
        total_users = len(self.user_experiences)
        user_experience_counts = []
        for indices in self.user_experiences.values():
            valid_indices = [idx for idx in indices if idx < self.current_size]
            user_experience_counts.append(len(valid_indices))
        
        return {
            "total_conversations": total_conversations,
            "total_users": total_users,
            "avg_conversation_length": np.mean(conversation_lengths) if conversation_lengths else 0,
            "max_conversation_length": max(conversation_lengths) if conversation_lengths else 0,
            "avg_user_experiences": np.mean(user_experience_counts) if user_experience_counts else 0,
            "total_experiences": self.current_size
        }
    
    def clear(self) -> None:
        """Clear buffer and conversation groups."""
        super().clear()
        self.conversation_groups.clear()
        self.user_experiences.clear()


class ExperienceBufferManager:
    """Manages multiple experience buffers and provides unified interface."""
    
    def __init__(self, config: RLConfig):
        self.config = config
        
        # Create different types of buffers
        self.main_buffer = ConversationExperienceBuffer(
            config, 
            max_size=config.training.buffer_size
        )
        
        # Separate buffer for high-quality experiences
        self.high_quality_buffer = PrioritizedExperienceBuffer(
            config,
            max_size=config.training.buffer_size // 4
        )
        
        # Buffer for safety violations (for analysis)
        self.safety_buffer = ExperienceBuffer(
            config,
            max_size=1000
        )
        
        self.quality_threshold = 0.7  # Threshold for high-quality experiences
        self.safety_threshold = 0.5   # Threshold for safety violations
    
    async def store_experience(self, experience: ConversationExperience) -> None:
        """Store experience in appropriate buffers."""
        
        # Always store in main buffer
        await self.main_buffer.store_experience(experience)
        
        # Store in high-quality buffer if reward is high
        if experience.reward.total_reward >= self.quality_threshold:
            await self.high_quality_buffer.store_experience(experience)
        
        # Store in safety buffer if safety score is low
        if experience.reward.safety <= self.safety_threshold:
            await self.safety_buffer.store_experience(experience)
        
        logger.debug(f"Stored experience {experience.experience_id} in appropriate buffers")
    
    async def sample_training_batch(
        self, 
        batch_size: int,
        high_quality_ratio: float = 0.3
    ) -> Tuple[List[ConversationExperience], np.ndarray, np.ndarray]:
        """
        Sample training batch with mix of regular and high-quality experiences.
        
        Args:
            batch_size: Total batch size
            high_quality_ratio: Ratio of high-quality experiences in batch
        
        Returns:
            experiences: Mixed batch of experiences
            indices: Indices (for priority updates)
            weights: Importance sampling weights
        """
        
        high_quality_size = int(batch_size * high_quality_ratio)
        regular_size = batch_size - high_quality_size
        
        all_experiences = []
        all_indices = []
        all_weights = []
        
        # Sample from high-quality buffer
        if high_quality_size > 0 and not self.high_quality_buffer.is_empty():
            hq_experiences, hq_indices, hq_weights = await self.high_quality_buffer.sample_batch(
                high_quality_size
            )
            all_experiences.extend(hq_experiences)
            all_indices.extend(hq_indices)
            all_weights.extend(hq_weights)
        
        # Sample from main buffer
        if regular_size > 0 and not self.main_buffer.is_empty():
            reg_experiences, reg_indices, reg_weights = await self.main_buffer.sample_batch(
                regular_size
            )
            all_experiences.extend(reg_experiences)
            all_indices.extend(reg_indices + len(self.high_quality_buffer.experiences))  # Offset indices
            all_weights.extend(reg_weights)
        
        return all_experiences, np.array(all_indices), np.array(all_weights)
    
    async def sample_conversation_batch(self, num_conversations: int) -> List[List[ConversationExperience]]:
        """Sample complete conversations for trajectory-based training."""
        return await self.main_buffer.sample_conversation_batch(num_conversations)
    
    async def get_user_experiences(self, user_id: str, max_experiences: int = 50) -> List[ConversationExperience]:
        """Get experiences for a specific user."""
        return await self.main_buffer.sample_user_experiences(user_id, max_experiences)
    
    async def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray) -> None:
        """Update priorities in appropriate buffers."""
        
        # Split indices between buffers
        hq_buffer_size = len(self.high_quality_buffer.experiences)
        
        hq_mask = indices < hq_buffer_size
        main_mask = indices >= hq_buffer_size
        
        if np.any(hq_mask):
            hq_indices = indices[hq_mask]
            hq_errors = td_errors[hq_mask]
            await self.high_quality_buffer.update_priorities(hq_indices, hq_errors)
        
        if np.any(main_mask):
            main_indices = indices[main_mask] - hq_buffer_size
            main_errors = td_errors[main_mask]
            await self.main_buffer.update_priorities(main_indices, main_errors)
    
    def get_buffer_statistics(self) -> Dict[str, Any]:
        """Get comprehensive buffer statistics."""
        
        main_stats = self.main_buffer.get_conversation_statistics()
        
        return {
            "main_buffer": {
                "size": self.main_buffer.get_size(),
                "max_size": self.main_buffer.max_size,
                **main_stats
            },
            "high_quality_buffer": {
                "size": self.high_quality_buffer.get_size(),
                "max_size": self.high_quality_buffer.max_size
            },
            "safety_buffer": {
                "size": self.safety_buffer.get_size(),
                "max_size": self.safety_buffer.max_size
            },
            "total_experiences": (
                self.main_buffer.get_size() + 
                self.high_quality_buffer.get_size() + 
                self.safety_buffer.get_size()
            )
        }
    
    async def save_buffer_state(self, filepath: str) -> None:
        """Save buffer state to disk."""
        
        buffer_state = {
            "main_buffer_experiences": [asdict(exp) for exp in self.main_buffer.experiences],
            "main_buffer_priorities": self.main_buffer.priorities,
            "high_quality_experiences": [asdict(exp) for exp in self.high_quality_buffer.experiences],
            "high_quality_priorities": self.high_quality_buffer.priorities,
            "safety_experiences": [asdict(exp) for exp in self.safety_buffer.experiences],
            "conversation_groups": self.main_buffer.conversation_groups,
            "user_experiences": self.main_buffer.user_experiences,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(buffer_state, f)
        
        logger.info(f"Buffer state saved to {filepath}")
    
    async def load_buffer_state(self, filepath: str) -> None:
        """Load buffer state from disk."""
        
        try:
            with open(filepath, 'rb') as f:
                buffer_state = pickle.load(f)
            
            # Reconstruct experiences (simplified - would need proper deserialization)
            logger.info(f"Buffer state loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to load buffer state: {e}")
    
    def clear_all_buffers(self) -> None:
        """Clear all buffers."""
        self.main_buffer.clear()
        self.high_quality_buffer.clear()
        self.safety_buffer.clear()
        logger.info("All experience buffers cleared")