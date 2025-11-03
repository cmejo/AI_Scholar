"""
PPO training implementation for the RL system.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

from ..core.config import RLConfig, TrainingConfig
from ..networks.policy_network import PolicyNetwork
from ..networks.value_network import ValueNetwork
from ..memory.experience_buffer import ExperienceBufferManager
from ..models.conversation_models import ConversationExperience

logger = logging.getLogger(__name__)


@dataclass
class TrainingMetrics:
    """Training metrics for monitoring."""
    epoch: int
    policy_loss: float
    value_loss: float
    entropy_loss: float
    total_loss: float
    average_reward: float
    learning_rate: float
    gradient_norm: float
    timestamp: datetime


class PPOTrainer:
    """Proximal Policy Optimization trainer."""
    
    def __init__(
        self,
        config: RLConfig,
        policy_network: PolicyNetwork,
        value_network: ValueNetwork,
        experience_buffer: ExperienceBufferManager
    ):
        self.config = config
        self.training_config = config.training
        self.policy_network = policy_network
        self.value_network = value_network
        self.experience_buffer = experience_buffer
        
        # Optimizers
        self.policy_optimizer = optim.Adam(
            self.policy_network.parameters(),
            lr=self.training_config.learning_rate
        )
        self.value_optimizer = optim.Adam(
            self.value_network.parameters(),
            lr=self.training_config.learning_rate
        )
        
        # Training state
        self.current_epoch = 0
        self.training_metrics: List[TrainingMetrics] = []
        self.best_reward = float('-inf')
        
    async def train_step(self) -> TrainingMetrics:
        """Perform one training step."""
        
        # Sample training batch
        experiences, indices, weights = await self.experience_buffer.sample_training_batch(
            self.training_config.batch_size
        )
        
        if not experiences:
            logger.warning("No experiences available for training")
            return self._create_empty_metrics()
        
        # Prepare training data
        states, actions, rewards, next_states, dones = self._prepare_training_data(experiences)
        
        # Calculate advantages
        with torch.no_grad():
            values = self.value_network.estimate_value(**states)
            next_values = self.value_network.estimate_value(**next_states)
            
            advantages = self.value_network.calculate_advantage(
                rewards, values, next_values, dones,
                self.training_config.gamma,
                self.training_config.gae_lambda
            )
            
            returns = advantages + values
        
        # PPO training loop
        policy_losses = []
        value_losses = []
        entropy_losses = []
        
        for _ in range(self.training_config.num_epochs):
            # Policy update
            policy_output = self.policy_network(**states)
            
            # Calculate policy loss
            action_log_probs = self.policy_network.get_action_log_probs(
                policy_output, actions['action_types'], actions['strategies']
            )
            
            old_log_probs = actions['old_log_probs']
            ratio = torch.exp(action_log_probs - old_log_probs)
            
            # PPO clipped objective
            surr1 = ratio * advantages
            surr2 = torch.clamp(
                ratio,
                1 - self.training_config.clip_epsilon,
                1 + self.training_config.clip_epsilon
            ) * advantages
            
            policy_loss = -torch.min(surr1, surr2).mean()
            
            # Entropy bonus
            entropy = self.policy_network.get_entropy(policy_output)
            entropy_loss = -self.training_config.entropy_coef * entropy.mean()
            
            # Value loss
            value_output = self.value_network(**states)
            value_loss = nn.MSELoss()(value_output.state_value, returns)
            
            # Total loss
            total_loss = (
                policy_loss + 
                self.training_config.value_loss_coef * value_loss + 
                entropy_loss
            )
            
            # Backward pass
            self.policy_optimizer.zero_grad()
            self.value_optimizer.zero_grad()
            
            total_loss.backward()
            
            # Gradient clipping
            policy_grad_norm = torch.nn.utils.clip_grad_norm_(
                self.policy_network.parameters(),
                self.training_config.max_grad_norm
            )
            
            value_grad_norm = torch.nn.utils.clip_grad_norm_(
                self.value_network.parameters(),
                self.training_config.max_grad_norm
            )
            
            self.policy_optimizer.step()
            self.value_optimizer.step()
            
            # Store losses
            policy_losses.append(policy_loss.item())
            value_losses.append(value_loss.item())
            entropy_losses.append(entropy_loss.item())
        
        # Update priorities in experience buffer
        td_errors = torch.abs(returns - values).detach().cpu().numpy()
        await self.experience_buffer.update_priorities(indices, td_errors)
        
        # Create metrics
        metrics = TrainingMetrics(
            epoch=self.current_epoch,
            policy_loss=np.mean(policy_losses),
            value_loss=np.mean(value_losses),
            entropy_loss=np.mean(entropy_losses),
            total_loss=np.mean(policy_losses) + np.mean(value_losses) + np.mean(entropy_losses),
            average_reward=rewards.mean().item(),
            learning_rate=self.training_config.learning_rate,
            gradient_norm=float(policy_grad_norm + value_grad_norm),
            timestamp=datetime.now()
        )
        
        self.training_metrics.append(metrics)
        self.current_epoch += 1
        
        # Update best reward
        if metrics.average_reward > self.best_reward:
            self.best_reward = metrics.average_reward
        
        return metrics
    
    def _prepare_training_data(
        self, 
        experiences: List[ConversationExperience]
    ) -> Tuple[Dict[str, torch.Tensor], Dict[str, torch.Tensor], torch.Tensor, Dict[str, torch.Tensor], torch.Tensor]:
        """Prepare training data from experiences."""
        
        device = torch.device(self.config.network.device)
        batch_size = len(experiences)
        
        # Prepare states (simplified)
        states = {
            "conversation_states": torch.zeros(batch_size, 1, self.config.network.state_dim).to(device),
            "user_profile_features": torch.zeros(batch_size, 64).to(device),
            "domain_features": torch.zeros(batch_size, 32).to(device),
            "personalization_features": torch.zeros(batch_size, 16).to(device)
        }
        
        # Prepare next states
        next_states = {
            "conversation_states": torch.zeros(batch_size, 1, self.config.network.state_dim).to(device),
            "user_profile_features": torch.zeros(batch_size, 64).to(device),
            "domain_features": torch.zeros(batch_size, 32).to(device),
            "personalization_features": torch.zeros(batch_size, 16).to(device)
        }
        
        # Prepare actions and rewards
        action_types = torch.zeros(batch_size, dtype=torch.long).to(device)
        strategies = torch.zeros(batch_size, dtype=torch.long).to(device)
        old_log_probs = torch.zeros(batch_size).to(device)
        rewards = torch.zeros(batch_size).to(device)
        dones = torch.zeros(batch_size).to(device)
        
        for i, exp in enumerate(experiences):
            # Fill in actual data (simplified)
            rewards[i] = exp.reward.total_reward
            dones[i] = 1.0 if exp.done else 0.0
            
            # Action data (would need proper encoding)
            action_types[i] = 0  # Placeholder
            strategies[i] = 0    # Placeholder
            old_log_probs[i] = -1.0  # Placeholder
        
        actions = {
            "action_types": action_types,
            "strategies": strategies,
            "old_log_probs": old_log_probs
        }
        
        return states, actions, rewards, next_states, dones
    
    def _create_empty_metrics(self) -> TrainingMetrics:
        """Create empty metrics when no training data available."""
        return TrainingMetrics(
            epoch=self.current_epoch,
            policy_loss=0.0,
            value_loss=0.0,
            entropy_loss=0.0,
            total_loss=0.0,
            average_reward=0.0,
            learning_rate=self.training_config.learning_rate,
            gradient_norm=0.0,
            timestamp=datetime.now()
        )
    
    def get_training_statistics(self) -> Dict[str, Any]:
        """Get training statistics."""
        
        if not self.training_metrics:
            return {"no_training_data": True}
        
        recent_metrics = self.training_metrics[-10:]  # Last 10 epochs
        
        return {
            "current_epoch": self.current_epoch,
            "total_training_steps": len(self.training_metrics),
            "best_reward": self.best_reward,
            "recent_average_reward": np.mean([m.average_reward for m in recent_metrics]),
            "recent_policy_loss": np.mean([m.policy_loss for m in recent_metrics]),
            "recent_value_loss": np.mean([m.value_loss for m in recent_metrics]),
            "learning_rate": self.training_config.learning_rate
        }


@dataclass
class TrainingSession:
    """Represents a training session."""
    session_id: str
    started_at: datetime
    config: TrainingConfig
    status: str = "running"
    metrics: List[TrainingMetrics] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = []