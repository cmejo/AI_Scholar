"""
Main RL agent controller that orchestrates all RL components.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import torch
import numpy as np

from ..core.config import RLConfig
from ..models.conversation_models import (
    ConversationState, ConversationTurn, Action, ActionType
)
from ..models.user_models import UserProfile, PersonalizationContext
from ..models.feedback_models import UserFeedback
from ..models.reward_models import MultiObjectiveReward
from ..networks.policy_network import PolicyNetwork, PolicyOutput
from ..networks.value_network import ValueNetwork, ValueOutput
from ..user_modeling.user_modeling_system import UserModelingSystem
from ..user_modeling.personalization_engine import PersonalizationEngine
from ..feedback.collectors import FeedbackProcessor
from ..feedback.reward_system import MultiObjectiveRewardCalculator
from ..safety.constitutional_ai import ConstitutionalAI
from ..safety.safety_monitor import SafetyMonitor
from ..memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """States of the RL agent."""
    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    LEARNING = "learning"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class RLResponse:
    """Response from the RL agent."""
    response_text: str
    action: Action
    confidence: float
    personalization_applied: bool
    safety_score: float
    processing_time: float
    metadata: Dict[str, Any]


class RLAgentController:
    """Main controller that orchestrates all RL components."""
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.state = AgentState.INITIALIZING
        
        # Core components
        self.policy_network: Optional[PolicyNetwork] = None
        self.value_network: Optional[ValueNetwork] = None
        self.user_modeling_system: Optional[UserModelingSystem] = None
        self.personalization_engine: Optional[PersonalizationEngine] = None
        self.feedback_processor: Optional[FeedbackProcessor] = None
        self.reward_calculator: Optional[MultiObjectiveRewardCalculator] = None
        self.constitutional_ai: Optional[ConstitutionalAI] = None
        self.safety_monitor: Optional[SafetyMonitor] = None
        self.memory_manager: Optional[MemoryManager] = None
        
        # Performance tracking
        self.response_count = 0
        self.total_processing_time = 0.0
        self.error_count = 0
        self.last_error: Optional[Exception] = None
        
        # Fallback system
        self.fallback_responses = [
            "I understand you're looking for help. Let me provide you with a thoughtful response.",
            "That's an interesting question. Let me think about the best way to help you with that.",
            "I want to make sure I give you the most helpful response possible. Let me consider your question carefully."
        ]
    
    async def initialize(self) -> None:
        """Initialize all RL components."""
        
        try:
            logger.info("Initializing RL Agent Controller...")
            
            # Initialize networks
            self.policy_network = PolicyNetwork(self.config.network)
            self.value_network = ValueNetwork(self.config.network)
            
            # Initialize user modeling
            self.user_modeling_system = UserModelingSystem(self.config)
            self.personalization_engine = PersonalizationEngine(self.config)
            
            # Initialize feedback and reward systems
            self.feedback_processor = FeedbackProcessor(self.config)
            await self.feedback_processor.initialize()
            
            self.reward_calculator = MultiObjectiveRewardCalculator(self.config)
            
            # Initialize safety systems
            self.constitutional_ai = ConstitutionalAI(self.config.safety)
            self.safety_monitor = SafetyMonitor(self.config.safety)
            
            # Initialize memory management
            self.memory_manager = MemoryManager(self.config)
            await self.memory_manager.initialize()
            
            # Move networks to appropriate device
            device = torch.device(self.config.network.device)
            self.policy_network.to(device)
            self.value_network.to(device)
            
            self.state = AgentState.READY
            logger.info("RL Agent Controller initialized successfully")
            
        except Exception as e:
            self.state = AgentState.ERROR
            self.last_error = e
            logger.error(f"Failed to initialize RL Agent Controller: {e}")
            raise
    
    async def generate_response(
        self,
        user_input: str,
        conversation_context: ConversationState,
        user_profile: Optional[UserProfile] = None
    ) -> RLResponse:
        """Generate a response using the RL system."""
        
        start_time = datetime.now()
        
        try:
            if self.state != AgentState.READY:
                return await self._fallback_response(user_input, "Agent not ready")
            
            self.state = AgentState.PROCESSING
            
            # Update conversation state
            conversation_context.current_user_input = user_input
            conversation_context.turn_number += 1
            
            # Get or create user profile
            if user_profile is None:
                user_profile = await self.user_modeling_system.get_or_create_user_profile(
                    conversation_context.user_id
                )
            
            # Generate personalization context
            personalization_context = await self.personalization_engine.generate_personalized_response_config(
                user_profile.get_personalization_context(conversation_context.domain_context),
                conversation_context
            )
            
            # Prepare network inputs
            network_inputs = await self._prepare_network_inputs(
                conversation_context, user_profile, personalization_context
            )
            
            # Generate policy output
            policy_output = await self._generate_policy_output(network_inputs)
            
            # Sample action from policy
            action_type_idx, strategy_idx, parameters = self.policy_network.sample_action(policy_output)
            
            # Create action
            action = Action(
                action_type=list(ActionType)[action_type_idx],
                response_text="",  # Will be filled by response generation
                confidence=policy_output.response_parameters.get("gate_value", 0.8),
                strategy_parameters=parameters
            )
            
            # Generate actual response text
            response_text = await self._generate_response_text(
                action, conversation_context, personalization_context
            )
            action.response_text = response_text
            
            # Safety validation
            is_safe, safety_score, filtered_response, safety_issues = await self.constitutional_ai.evaluate_response(
                response_text, conversation_context, action
            )
            
            if not is_safe:
                logger.warning(f"Unsafe response detected: {safety_issues}")
                return await self._fallback_response(user_input, "Safety violation")
            
            # Create response
            processing_time = (datetime.now() - start_time).total_seconds()
            
            rl_response = RLResponse(
                response_text=filtered_response,
                action=action,
                confidence=action.confidence,
                personalization_applied=True,
                safety_score=safety_score,
                processing_time=processing_time,
                metadata={
                    "policy_output": {
                        "action_probabilities": policy_output.action_probabilities.tolist(),
                        "strategy_probabilities": policy_output.strategy_probabilities.tolist()
                    },
                    "personalization_config": personalization_context,
                    "safety_issues": safety_issues
                }
            )
            
            # Update conversation history
            turn = ConversationTurn(
                user_input=user_input,
                agent_response=filtered_response,
                action=action,
                timestamp=datetime.now()
            )
            conversation_context.add_turn(turn)
            
            # Track performance
            self.response_count += 1
            self.total_processing_time += processing_time
            
            self.state = AgentState.READY
            return rl_response
            
        except Exception as e:
            self.error_count += 1
            self.last_error = e
            self.state = AgentState.ERROR
            logger.error(f"Error generating response: {e}")
            return await self._fallback_response(user_input, f"Error: {str(e)}")
    
    async def process_feedback(
        self,
        feedback: UserFeedback,
        conversation_id: str,
        update_immediately: bool = False
    ) -> None:
        """Process user feedback and update the system."""
        
        try:
            # Get conversation context
            conversation_experiences = await self.memory_manager.get_user_experiences_with_privacy(
                feedback.user_id, max_experiences=10
            )
            
            # Find relevant experience
            relevant_experience = None
            for exp in conversation_experiences:
                if exp.state.conversation_id == conversation_id:
                    relevant_experience = exp
                    break
            
            if relevant_experience is None:
                logger.warning(f"No experience found for conversation {conversation_id}")
                return
            
            # Calculate reward
            reward = await self.reward_calculator.calculate_reward(
                relevant_experience.state,
                relevant_experience.action,
                [feedback]
            )
            
            # Update experience with new reward
            relevant_experience.reward = reward
            
            # Store updated experience
            await self.memory_manager.store_experience_with_privacy(relevant_experience)
            
            # Update user profile
            await self.user_modeling_system.update_user_profile(
                feedback.user_id,
                relevant_experience.state,
                feedback
            )
            
            # Monitor for safety issues
            await self.safety_monitor.monitor_interaction(
                relevant_experience.state,
                relevant_experience.action,
                relevant_experience.action.response_text,
                reward
            )
            
            # Update personalization effectiveness
            if hasattr(relevant_experience.action, 'strategy_parameters'):
                strategy = relevant_experience.action.strategy_parameters.get('strategy', 'balanced_approach')
                feedback_score = feedback.get_feedback_strength()
                
                # This would be a ResponseStrategy enum in practice
                # await self.personalization_engine.update_personalization_effectiveness(
                #     feedback.user_id, strategy, feedback_score
                # )
            
            logger.info(f"Processed feedback for conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
    
    async def _prepare_network_inputs(
        self,
        conversation_state: ConversationState,
        user_profile: UserProfile,
        personalization_context: Dict[str, Any]
    ) -> Dict[str, torch.Tensor]:
        """Prepare inputs for neural networks."""
        
        device = torch.device(self.config.network.device)
        
        # Convert conversation state to tensor
        conversation_tensor = conversation_state.to_tensor().unsqueeze(0).to(device)
        
        # Create user profile features (simplified)
        user_features = torch.zeros(64).to(device)  # Placeholder
        user_features[0] = user_profile.get_success_rate()
        user_features[1] = user_profile.personalization_effectiveness
        user_features[2] = len(user_profile.expertise_levels) / 10.0  # Normalize
        
        # Create domain features
        domain_features = torch.zeros(32).to(device)  # Placeholder
        if conversation_state.domain_context:
            # Simple domain encoding (would be more sophisticated in practice)
            domain_hash = hash(conversation_state.domain_context) % 32
            domain_features[domain_hash] = 1.0
        
        # Create personalization features
        personalization_features = torch.zeros(16).to(device)  # Placeholder
        if personalization_context:
            personalization_features[0] = personalization_context.get('complexity_level', 0.5)
            personalization_features[1] = 1.0 if personalization_context.get('include_examples', False) else 0.0
            personalization_features[2] = 1.0 if personalization_context.get('step_by_step', False) else 0.0
        
        return {
            "conversation_states": conversation_tensor.unsqueeze(1),  # Add sequence dimension
            "user_profile_features": user_features.unsqueeze(0),
            "domain_features": domain_features.unsqueeze(0),
            "personalization_features": personalization_features.unsqueeze(0)
        }
    
    async def _generate_policy_output(self, network_inputs: Dict[str, torch.Tensor]) -> PolicyOutput:
        """Generate policy output from network."""
        
        with torch.no_grad():
            policy_output = self.policy_network(**network_inputs)
        
        return policy_output
    
    async def _generate_response_text(
        self,
        action: Action,
        conversation_context: ConversationState,
        personalization_config: Dict[str, Any]
    ) -> str:
        """Generate actual response text based on action and context."""
        
        # This is a simplified version - in practice, this would interface
        # with the existing AI Scholar text generation system
        
        base_response = f"Based on your question about {conversation_context.current_user_input}, "
        
        if action.action_type == ActionType.TECHNICAL_RESPONSE:
            response = base_response + "here's a technical explanation: [Technical content would be generated here]"
        elif action.action_type == ActionType.EXPLANATORY_RESPONSE:
            response = base_response + "let me explain this step by step: [Explanatory content would be generated here]"
        elif action.action_type == ActionType.CREATIVE_RESPONSE:
            response = base_response + "here's a creative approach: [Creative content would be generated here]"
        elif action.action_type == ActionType.CLARIFYING_QUESTION:
            response = "To better help you, could you clarify: [Clarifying question would be generated here]"
        else:
            response = base_response + "here's what I can help you with: [General content would be generated here]"
        
        # Apply personalization
        if personalization_config.get('include_examples', False):
            response += " For example: [Example would be added here]"
        
        if personalization_config.get('step_by_step', False):
            response += " Step 1: [Step-by-step breakdown would be added here]"
        
        return response
    
    async def _fallback_response(self, user_input: str, reason: str) -> RLResponse:
        """Generate fallback response when RL system fails."""
        
        import random
        fallback_text = random.choice(self.fallback_responses)
        
        fallback_action = Action(
            action_type=ActionType.EXPLANATORY_RESPONSE,
            response_text=fallback_text,
            confidence=0.5
        )
        
        return RLResponse(
            response_text=fallback_text,
            action=fallback_action,
            confidence=0.5,
            personalization_applied=False,
            safety_score=1.0,
            processing_time=0.1,
            metadata={"fallback_reason": reason}
        )
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and statistics."""
        
        avg_processing_time = (
            self.total_processing_time / self.response_count 
            if self.response_count > 0 else 0.0
        )
        
        return {
            "state": self.state.value,
            "response_count": self.response_count,
            "error_count": self.error_count,
            "average_processing_time": avg_processing_time,
            "last_error": str(self.last_error) if self.last_error else None,
            "components_initialized": {
                "policy_network": self.policy_network is not None,
                "value_network": self.value_network is not None,
                "user_modeling": self.user_modeling_system is not None,
                "personalization": self.personalization_engine is not None,
                "feedback_processor": self.feedback_processor is not None,
                "constitutional_ai": self.constitutional_ai is not None,
                "safety_monitor": self.safety_monitor is not None,
                "memory_manager": self.memory_manager is not None
            }
        }
    
    async def shutdown(self) -> None:
        """Shutdown the RL agent controller."""
        
        self.state = AgentState.MAINTENANCE
        
        try:
            if self.memory_manager:
                await self.memory_manager.shutdown()
            
            logger.info("RL Agent Controller shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        self.state = AgentState.ERROR if self.last_error else AgentState.READY