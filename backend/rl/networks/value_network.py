"""
Value network implementation for the RL system.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

from ..core.config import NetworkConfig
from .shared_encoder import SharedEncoder

logger = logging.getLogger(__name__)


@dataclass
class ValueOutput:
    """Output from the value network."""
    state_value: torch.Tensor
    component_values: Dict[str, torch.Tensor]
    confidence: torch.Tensor
    hidden_state: Optional[torch.Tensor] = None


class MultiObjectiveValueHead(nn.Module):
    """Head for multi-objective value estimation."""
    
    def __init__(self, input_dim: int):
        super().__init__()
        
        # Individual value component heads
        self.helpfulness_head = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 1)
        )
        
        self.accuracy_head = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 1)
        )
        
        self.engagement_head = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 1)
        )
        
        self.safety_head = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 1)
        )
        
        self.learning_effectiveness_head = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 1)
        )
        
        self.personalization_head = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 1)
        )
        
        # Confidence estimation head
        self.confidence_head = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 1),
            nn.Sigmoid()  # Confidence between 0 and 1
        )
        
        # Aggregation weights (learnable)
        self.aggregation_weights = nn.Parameter(torch.ones(6) / 6)  # 6 components
        
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor], torch.Tensor]:
        """
        Args:
            x: [batch_size, input_dim]
        
        Returns:
            aggregated_value: [batch_size, 1]
            component_values: Dict of component values
            confidence: [batch_size, 1]
        """
        
        # Calculate individual component values
        helpfulness_value = self.helpfulness_head(x)
        accuracy_value = self.accuracy_head(x)
        engagement_value = self.engagement_head(x)
        safety_value = self.safety_head(x)
        learning_value = self.learning_effectiveness_head(x)
        personalization_value = self.personalization_head(x)
        
        # Stack component values
        component_values_tensor = torch.stack([
            helpfulness_value.squeeze(-1),
            accuracy_value.squeeze(-1),
            engagement_value.squeeze(-1),
            safety_value.squeeze(-1),
            learning_value.squeeze(-1),
            personalization_value.squeeze(-1)
        ], dim=-1)  # [batch_size, 6]
        
        # Normalize aggregation weights
        normalized_weights = F.softmax(self.aggregation_weights, dim=0)
        
        # Calculate weighted sum
        aggregated_value = torch.sum(
            component_values_tensor * normalized_weights.unsqueeze(0), 
            dim=-1, 
            keepdim=True
        )
        
        # Calculate confidence
        confidence = self.confidence_head(x)
        
        # Prepare component values dictionary
        component_values = {
            "helpfulness": helpfulness_value.squeeze(-1),
            "accuracy": accuracy_value.squeeze(-1),
            "engagement": engagement_value.squeeze(-1),
            "safety": safety_value.squeeze(-1),
            "learning_effectiveness": learning_value.squeeze(-1),
            "personalization": personalization_value.squeeze(-1)
        }
        
        return aggregated_value, component_values, confidence


class TemporalValueHead(nn.Module):
    """Head for temporal value estimation (short-term vs long-term)."""
    
    def __init__(self, input_dim: int):
        super().__init__()
        
        # Short-term value (immediate reward prediction)
        self.short_term_head = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 1)
        )
        
        # Long-term value (future reward prediction)
        self.long_term_head = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 1)
        )
        
        # Temporal weighting (how much to weight short vs long term)
        self.temporal_weight_head = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()  # Weight between 0 and 1
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Args:
            x: [batch_size, input_dim]
        
        Returns:
            temporal_value: [batch_size, 1]
            temporal_components: Dict of temporal components
        """
        
        short_term_value = self.short_term_head(x)
        long_term_value = self.long_term_head(x)
        temporal_weight = self.temporal_weight_head(x)
        
        # Combine short-term and long-term values
        temporal_value = (
            temporal_weight * short_term_value + 
            (1 - temporal_weight) * long_term_value
        )
        
        temporal_components = {
            "short_term": short_term_value.squeeze(-1),
            "long_term": long_term_value.squeeze(-1),
            "temporal_weight": temporal_weight.squeeze(-1)
        }
        
        return temporal_value, temporal_components


class UncertaintyEstimationHead(nn.Module):
    """Head for estimating uncertainty in value predictions."""
    
    def __init__(self, input_dim: int):
        super().__init__()
        
        # Aleatoric uncertainty (data uncertainty)
        self.aleatoric_head = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 1),
            nn.Softplus()  # Ensure positive values
        )
        
        # Epistemic uncertainty (model uncertainty)
        self.epistemic_head = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 1),
            nn.Softplus()  # Ensure positive values
        )
    
    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Args:
            x: [batch_size, input_dim]
        
        Returns:
            uncertainty_estimates: Dict of uncertainty components
        """
        
        aleatoric_uncertainty = self.aleatoric_head(x)
        epistemic_uncertainty = self.epistemic_head(x)
        
        # Total uncertainty (combination of both types)
        total_uncertainty = torch.sqrt(
            aleatoric_uncertainty ** 2 + epistemic_uncertainty ** 2
        )
        
        return {
            "aleatoric": aleatoric_uncertainty.squeeze(-1),
            "epistemic": epistemic_uncertainty.squeeze(-1),
            "total": total_uncertainty.squeeze(-1)
        }


class ValueNetwork(nn.Module):
    """Main value network for RL agent."""
    
    def __init__(self, config: NetworkConfig):
        super().__init__()
        
        self.config = config
        
        # Shared encoder (same as policy network)
        self.shared_encoder = SharedEncoder(config)
        
        # Value-specific layers
        self.value_layers = nn.ModuleList([
            nn.Sequential(
                nn.Linear(
                    config.context_dim if i == 0 else config.value_hidden_size,
                    config.value_hidden_size
                ),
                nn.ReLU(),
                nn.Dropout(config.value_dropout if hasattr(config, 'value_dropout') else 0.1)
            )
            for i in range(config.value_num_layers)
        ])
        
        # Multi-objective value head
        self.multi_objective_head = MultiObjectiveValueHead(config.value_hidden_size)
        
        # Temporal value head
        self.temporal_head = TemporalValueHead(config.value_hidden_size)
        
        # Uncertainty estimation head
        self.uncertainty_head = UncertaintyEstimationHead(config.value_hidden_size)
        
        # Final value aggregation
        self.final_value_head = nn.Sequential(
            nn.Linear(config.value_hidden_size, config.value_hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(config.value_hidden_size // 2, 1)
        )
    
    def forward(
        self,
        conversation_states: torch.Tensor,
        user_profile_features: torch.Tensor,
        domain_features: torch.Tensor,
        personalization_features: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> ValueOutput:
        """
        Args:
            conversation_states: [batch_size, seq_len, state_dim]
            user_profile_features: [batch_size, 64]
            domain_features: [batch_size, 32]
            personalization_features: [batch_size, 16]
            attention_mask: [batch_size, seq_len]
        
        Returns:
            ValueOutput with state value and component breakdowns
        """
        
        # Shared encoding
        shared_encoding = self.shared_encoder(
            conversation_states,
            user_profile_features,
            domain_features,
            personalization_features,
            attention_mask
        )
        
        # Value-specific processing
        x = shared_encoding
        for layer in self.value_layers:
            x = layer(x)
        
        # Multi-objective value estimation
        multi_obj_value, component_values, confidence = self.multi_objective_head(x)
        
        # Temporal value estimation
        temporal_value, temporal_components = self.temporal_head(x)
        
        # Uncertainty estimation
        uncertainty_estimates = self.uncertainty_head(x)
        
        # Final state value (can be multi-objective value or a combination)
        state_value = self.final_value_head(x)
        
        # Combine all component values
        all_component_values = {
            **component_values,
            **temporal_components,
            **uncertainty_estimates
        }
        
        return ValueOutput(
            state_value=state_value.squeeze(-1),
            component_values=all_component_values,
            confidence=confidence.squeeze(-1),
            hidden_state=x
        )
    
    def estimate_value(
        self,
        conversation_states: torch.Tensor,
        user_profile_features: torch.Tensor,
        domain_features: torch.Tensor,
        personalization_features: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Simplified value estimation (returns only state value).
        
        Returns:
            state_values: [batch_size]
        """
        
        value_output = self.forward(
            conversation_states,
            user_profile_features,
            domain_features,
            personalization_features,
            attention_mask
        )
        
        return value_output.state_value
    
    def predict_outcome(
        self,
        current_state: torch.Tensor,
        proposed_action_features: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        Predict outcome of a proposed action.
        
        Args:
            current_state: Current conversation state encoding
            proposed_action_features: Features of proposed action
        
        Returns:
            outcome_prediction: Dict with predicted outcomes
        """
        
        # Combine current state with proposed action
        combined_features = torch.cat([current_state, proposed_action_features], dim=-1)
        
        # Simple MLP for outcome prediction
        outcome_head = nn.Sequential(
            nn.Linear(combined_features.shape[-1], 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 6)  # 6 outcome dimensions
        ).to(combined_features.device)
        
        outcome_logits = outcome_head(combined_features)
        outcome_probs = F.softmax(outcome_logits, dim=-1)
        
        return {
            "outcome_probabilities": outcome_probs,
            "predicted_reward": outcome_probs.mean(dim=-1),
            "confidence": outcome_probs.max(dim=-1)[0]
        }
    
    def calculate_advantage(
        self,
        rewards: torch.Tensor,
        values: torch.Tensor,
        next_values: torch.Tensor,
        dones: torch.Tensor,
        gamma: float = 0.99,
        gae_lambda: float = 0.95
    ) -> torch.Tensor:
        """
        Calculate Generalized Advantage Estimation (GAE).
        
        Args:
            rewards: [batch_size, seq_len]
            values: [batch_size, seq_len]
            next_values: [batch_size, seq_len]
            dones: [batch_size, seq_len]
            gamma: Discount factor
            gae_lambda: GAE lambda parameter
        
        Returns:
            advantages: [batch_size, seq_len]
        """
        
        batch_size, seq_len = rewards.shape
        advantages = torch.zeros_like(rewards)
        
        # Calculate TD errors
        td_errors = rewards + gamma * next_values * (1 - dones) - values
        
        # Calculate GAE
        gae = 0
        for t in reversed(range(seq_len)):
            gae = td_errors[:, t] + gamma * gae_lambda * (1 - dones[:, t]) * gae
            advantages[:, t] = gae
        
        return advantages
    
    def save_checkpoint(self, path: str) -> None:
        """Save model checkpoint."""
        torch.save({
            'model_state_dict': self.state_dict(),
            'config': self.config
        }, path)
        logger.info(f"Value network checkpoint saved to {path}")
    
    @classmethod
    def load_checkpoint(cls, path: str, config: NetworkConfig) -> 'ValueNetwork':
        """Load model from checkpoint."""
        checkpoint = torch.load(path, map_location='cpu')
        
        model = cls(config)
        model.load_state_dict(checkpoint['model_state_dict'])
        
        logger.info(f"Value network loaded from {path}")
        return model