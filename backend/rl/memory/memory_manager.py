"""
Memory management and privacy protection for the RL system.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import hashlib
import json
import re
from dataclasses import asdict, replace
from enum import Enum
import uuid

from ..models.conversation_models import ConversationExperience, ConversationState
from ..models.user_models import UserProfile
from ..core.config import RLConfig, SafetyConfig
from .experience_buffer import ExperienceBufferManager

logger = logging.getLogger(__name__)


class ConsentLevel(Enum):
    """Levels of user consent for data usage."""
    NONE = "none"
    BASIC = "basic"
    ANALYTICS = "analytics"
    TRAINING = "training"
    FULL = "full"


class DataCategory(Enum):
    """Categories of data for privacy management."""
    CONVERSATION_CONTENT = "conversation_content"
    USER_PROFILE = "user_profile"
    FEEDBACK_DATA = "feedback_data"
    BEHAVIORAL_PATTERNS = "behavioral_patterns"
    PERFORMANCE_METRICS = "performance_metrics"


class PrivacyManager:
    """Manages privacy protection and user consent."""
    
    def __init__(self, config: SafetyConfig):
        self.config = config
        self.user_consents: Dict[str, Dict[DataCategory, ConsentLevel]] = {}
        self.anonymization_keys: Dict[str, str] = {}  # user_id -> anonymized_id
        self.data_retention_policies: Dict[DataCategory, int] = {
            DataCategory.CONVERSATION_CONTENT: config.data_retention_days,
            DataCategory.USER_PROFILE: config.data_retention_days * 2,
            DataCategory.FEEDBACK_DATA: config.data_retention_days,
            DataCategory.BEHAVIORAL_PATTERNS: config.data_retention_days // 2,
            DataCategory.PERFORMANCE_METRICS: config.data_retention_days * 3
        }
    
    async def request_consent(
        self,
        user_id: str,
        data_categories: List[DataCategory],
        purpose: str
    ) -> Dict[DataCategory, bool]:
        """Request user consent for data usage."""
        
        # In a real system, this would present a consent form to the user
        # For now, we'll simulate based on configuration
        
        consent_results = {}
        
        for category in data_categories:
            # Default consent based on configuration
            if self.config.require_user_consent:
                # Simulate user consent (in practice, this would be user input)
                if category in [DataCategory.PERFORMANCE_METRICS, DataCategory.BEHAVIORAL_PATTERNS]:
                    consent_results[category] = True  # Usually granted for analytics
                else:
                    consent_results[category] = False  # More sensitive data requires explicit consent
            else:
                consent_results[category] = True  # Consent not required
        
        # Store consent
        if user_id not in self.user_consents:
            self.user_consents[user_id] = {}
        
        for category, granted in consent_results.items():
            consent_level = ConsentLevel.TRAINING if granted else ConsentLevel.NONE
            self.user_consents[user_id][category] = consent_level
        
        logger.info(f"Consent requested for user {user_id}: {consent_results}")
        return consent_results
    
    def check_consent(self, user_id: str, data_category: DataCategory, required_level: ConsentLevel) -> bool:
        """Check if user has given required consent level."""
        
        if not self.config.require_user_consent:
            return True
        
        if user_id not in self.user_consents:
            return False
        
        user_consent = self.user_consents[user_id].get(data_category, ConsentLevel.NONE)
        
        # Define consent hierarchy
        consent_hierarchy = {
            ConsentLevel.NONE: 0,
            ConsentLevel.BASIC: 1,
            ConsentLevel.ANALYTICS: 2,
            ConsentLevel.TRAINING: 3,
            ConsentLevel.FULL: 4
        }
        
        return consent_hierarchy[user_consent] >= consent_hierarchy[required_level]
    
    async def anonymize_user_data(self, user_id: str) -> str:
        """Generate anonymized ID for user."""
        
        if user_id in self.anonymization_keys:
            return self.anonymization_keys[user_id]
        
        # Generate consistent anonymized ID
        anonymized_id = hashlib.sha256(f"{user_id}_salt_{self.config}".encode()).hexdigest()[:16]
        self.anonymization_keys[user_id] = anonymized_id
        
        return anonymized_id
    
    async def anonymize_conversation_experience(
        self,
        experience: ConversationExperience
    ) -> ConversationExperience:
        """Anonymize a conversation experience."""
        
        if not self.config.anonymize_stored_data:
            return experience
        
        # Anonymize user ID
        anonymized_user_id = await self.anonymize_user_data(experience.state.user_id)
        
        # Create anonymized state
        anonymized_state = replace(
            experience.state,
            user_id=anonymized_user_id,
            user_profile_id=anonymized_user_id
        )
        
        # Anonymize conversation content
        anonymized_history = []
        for turn in experience.state.conversation_history:
            anonymized_turn = replace(
                turn,
                user_input=self._anonymize_text(turn.user_input),
                agent_response=self._anonymize_text(turn.agent_response)
            )
            anonymized_history.append(anonymized_turn)
        
        anonymized_state.conversation_history = anonymized_history
        anonymized_state.current_user_input = self._anonymize_text(anonymized_state.current_user_input)
        
        # Create anonymized experience
        anonymized_experience = replace(
            experience,
            state=anonymized_state
        )
        
        return anonymized_experience
    
    def _anonymize_text(self, text: str) -> str:
        """Anonymize sensitive information in text."""
        
        if not text:
            return text
        
        anonymized = text
        
        # Remove email addresses
        anonymized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', anonymized)
        
        # Remove phone numbers
        anonymized = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', anonymized)
        
        # Remove potential names (simple heuristic)
        anonymized = re.sub(r'\bmy name is \w+\b', 'my name is [NAME]', anonymized, flags=re.IGNORECASE)
        anonymized = re.sub(r'\bi am \w+\b', 'i am [NAME]', anonymized, flags=re.IGNORECASE)
        
        # Remove addresses (simple patterns)
        anonymized = re.sub(r'\b\d+\s+\w+\s+(street|st|avenue|ave|road|rd|drive|dr)\b', '[ADDRESS]', anonymized, flags=re.IGNORECASE)
        
        # Remove social security numbers
        anonymized = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', anonymized)
        
        # Remove credit card numbers
        anonymized = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CREDIT_CARD]', anonymized)
        
        return anonymized
    
    async def revoke_consent(self, user_id: str, data_categories: List[DataCategory]) -> None:
        """Revoke user consent for specified data categories."""
        
        if user_id in self.user_consents:
            for category in data_categories:
                self.user_consents[user_id][category] = ConsentLevel.NONE
        
        logger.info(f"Consent revoked for user {user_id}: {data_categories}")
    
    def get_consent_status(self, user_id: str) -> Dict[DataCategory, ConsentLevel]:
        """Get current consent status for user."""
        
        return self.user_consents.get(user_id, {})


class DataRetentionManager:
    """Manages data retention and automatic cleanup."""
    
    def __init__(self, config: SafetyConfig, privacy_manager: PrivacyManager):
        self.config = config
        self.privacy_manager = privacy_manager
        self.retention_policies = privacy_manager.data_retention_policies
        self.cleanup_schedule: Dict[str, datetime] = {}
    
    async def schedule_data_cleanup(self, user_id: str, data_category: DataCategory) -> None:
        """Schedule data cleanup for a user and category."""
        
        retention_days = self.retention_policies[data_category]
        cleanup_date = datetime.now() + timedelta(days=retention_days)
        
        cleanup_key = f"{user_id}_{data_category.value}"
        self.cleanup_schedule[cleanup_key] = cleanup_date
        
        logger.info(f"Scheduled cleanup for {cleanup_key} on {cleanup_date}")
    
    async def check_and_cleanup_expired_data(
        self,
        experience_buffer: ExperienceBufferManager
    ) -> Dict[str, int]:
        """Check for and cleanup expired data."""
        
        current_time = datetime.now()
        cleanup_stats = {
            "experiences_removed": 0,
            "users_processed": 0,
            "categories_cleaned": 0
        }
        
        # Check scheduled cleanups
        expired_cleanups = []
        for cleanup_key, cleanup_date in self.cleanup_schedule.items():
            if current_time >= cleanup_date:
                expired_cleanups.append(cleanup_key)
        
        # Process expired cleanups
        for cleanup_key in expired_cleanups:
            user_id, category_str = cleanup_key.split('_', 1)
            data_category = DataCategory(category_str)
            
            await self._cleanup_user_data(user_id, data_category, experience_buffer)
            
            del self.cleanup_schedule[cleanup_key]
            cleanup_stats["categories_cleaned"] += 1
        
        # General cleanup of old experiences
        removed_count = await self._cleanup_old_experiences(experience_buffer)
        cleanup_stats["experiences_removed"] = removed_count
        
        return cleanup_stats
    
    async def _cleanup_user_data(
        self,
        user_id: str,
        data_category: DataCategory,
        experience_buffer: ExperienceBufferManager
    ) -> None:
        """Cleanup specific user data category."""
        
        if data_category == DataCategory.CONVERSATION_CONTENT:
            # Remove user's conversation experiences
            user_experiences = await experience_buffer.get_user_experiences(user_id, max_experiences=1000)
            
            # Remove from buffers (simplified - would need more sophisticated removal)
            logger.info(f"Would remove {len(user_experiences)} experiences for user {user_id}")
        
        elif data_category == DataCategory.USER_PROFILE:
            # Remove user profile data
            if user_id in self.privacy_manager.user_consents:
                del self.privacy_manager.user_consents[user_id]
            
            if user_id in self.privacy_manager.anonymization_keys:
                del self.privacy_manager.anonymization_keys[user_id]
        
        logger.info(f"Cleaned up {data_category.value} for user {user_id}")
    
    async def _cleanup_old_experiences(self, experience_buffer: ExperienceBufferManager) -> int:
        """Cleanup experiences older than retention policy."""
        
        retention_days = self.retention_policies[DataCategory.CONVERSATION_CONTENT]
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # Get buffer statistics to understand what needs cleanup
        stats = experience_buffer.get_buffer_statistics()
        
        # In a real implementation, this would remove old experiences
        # For now, we'll just log what would be removed
        logger.info(f"Would cleanup experiences older than {cutoff_date}")
        
        return 0  # Placeholder
    
    async def force_cleanup_user_data(self, user_id: str) -> None:
        """Force immediate cleanup of all user data (e.g., for GDPR deletion request)."""
        
        # Remove all scheduled cleanups for user
        to_remove = [key for key in self.cleanup_schedule.keys() if key.startswith(f"{user_id}_")]
        for key in to_remove:
            del self.cleanup_schedule[key]
        
        # Remove user consent data
        if user_id in self.privacy_manager.user_consents:
            del self.privacy_manager.user_consents[user_id]
        
        # Remove anonymization key
        if user_id in self.privacy_manager.anonymization_keys:
            del self.privacy_manager.anonymization_keys[user_id]
        
        logger.info(f"Force cleanup completed for user {user_id}")


class MemoryManager:
    """Main memory management system coordinating all memory components."""
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.privacy_manager = PrivacyManager(config.safety)
        self.retention_manager = DataRetentionManager(config.safety, self.privacy_manager)
        self.experience_buffer = ExperienceBufferManager(config)
        
        # Background cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        self.cleanup_interval = timedelta(hours=24)  # Daily cleanup
    
    async def initialize(self) -> None:
        """Initialize memory management system."""
        
        # Start background cleanup task
        self.cleanup_task = asyncio.create_task(self._background_cleanup())
        
        logger.info("Memory management system initialized")
    
    async def store_experience_with_privacy(
        self,
        experience: ConversationExperience,
        user_consent_check: bool = True
    ) -> bool:
        """Store experience with privacy protection."""
        
        user_id = experience.state.user_id
        
        # Check consent if required
        if user_consent_check and self.config.safety.require_user_consent:
            has_consent = self.privacy_manager.check_consent(
                user_id,
                DataCategory.CONVERSATION_CONTENT,
                ConsentLevel.TRAINING
            )
            
            if not has_consent:
                logger.warning(f"Cannot store experience for user {user_id}: no consent")
                return False
        
        # Anonymize if required
        if self.config.safety.anonymize_stored_data:
            experience = await self.privacy_manager.anonymize_conversation_experience(experience)
        
        # Store experience
        await self.experience_buffer.store_experience(experience)
        
        # Schedule cleanup
        await self.retention_manager.schedule_data_cleanup(
            user_id,
            DataCategory.CONVERSATION_CONTENT
        )
        
        return True
    
    async def get_user_experiences_with_privacy(
        self,
        user_id: str,
        max_experiences: int = 50
    ) -> List[ConversationExperience]:
        """Get user experiences with privacy checks."""
        
        # Check consent
        has_consent = self.privacy_manager.check_consent(
            user_id,
            DataCategory.CONVERSATION_CONTENT,
            ConsentLevel.ANALYTICS
        )
        
        if not has_consent:
            logger.warning(f"Cannot retrieve experiences for user {user_id}: no consent")
            return []
        
        return await self.experience_buffer.get_user_experiences(user_id, max_experiences)
    
    async def request_user_consent(
        self,
        user_id: str,
        data_categories: List[DataCategory],
        purpose: str
    ) -> Dict[DataCategory, bool]:
        """Request user consent for data usage."""
        
        return await self.privacy_manager.request_consent(user_id, data_categories, purpose)
    
    async def handle_data_deletion_request(self, user_id: str) -> None:
        """Handle user request to delete all their data (GDPR right to be forgotten)."""
        
        await self.retention_manager.force_cleanup_user_data(user_id)
        
        logger.info(f"Data deletion request processed for user {user_id}")
    
    async def _background_cleanup(self) -> None:
        """Background task for periodic data cleanup."""
        
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval.total_seconds())
                
                cleanup_stats = await self.retention_manager.check_and_cleanup_expired_data(
                    self.experience_buffer
                )
                
                logger.info(f"Background cleanup completed: {cleanup_stats}")
                
            except Exception as e:
                logger.error(f"Error in background cleanup: {e}")
    
    def get_privacy_statistics(self) -> Dict[str, Any]:
        """Get privacy and data management statistics."""
        
        total_users = len(self.privacy_manager.user_consents)
        
        # Count consent levels
        consent_stats = {}
        for user_consents in self.privacy_manager.user_consents.values():
            for category, level in user_consents.items():
                category_key = category.value
                if category_key not in consent_stats:
                    consent_stats[category_key] = {}
                
                level_key = level.value
                consent_stats[category_key][level_key] = consent_stats[category_key].get(level_key, 0) + 1
        
        # Buffer statistics
        buffer_stats = self.experience_buffer.get_buffer_statistics()
        
        return {
            "privacy_protection_enabled": self.config.safety.require_user_consent,
            "anonymization_enabled": self.config.safety.anonymize_stored_data,
            "total_users_with_consent": total_users,
            "consent_statistics": consent_stats,
            "scheduled_cleanups": len(self.retention_manager.cleanup_schedule),
            "buffer_statistics": buffer_stats,
            "data_retention_days": self.config.safety.data_retention_days
        }
    
    async def shutdown(self) -> None:
        """Shutdown memory management system."""
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Memory management system shutdown")