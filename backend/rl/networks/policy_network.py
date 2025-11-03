"""
Policy network implementation for the RL system.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

from ..core.config import NetworkConfig
from ..models.conversation_models import ActionType
from .shared_encoder import SharedEncoder

logger = logging.getLogger(__name__)


@dataclass
class PolicyOutput:
    """Output from the policy network."""
    action_logits: torch.Tensor
    action_probabilities: torch.Tensor
    strategy_logits: torch.Tensor
    strategy_probabilities: torch.Tensor
    response_parameters: Dict[str, torch.Tensor]
    attention_weights: Optional[torch.Tensor] = None
    hidden_state: Optional[torch.Tensor] = None


class ResponseStrategyHead(nn.Module):
    """Head for selecting response strategies."""
    
    def __init__(self, input_dim: int, num_strategies: int = 7):
        super().__init__()
        
        self.num_strategies = num_strategies
        
        self.strategy_head = nn.Sequential(
            nn.Linear(input_dim, input_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(input_dim // 2, num_strategies)
        )
        
        # Strategy-specific parameter heads
        self.complexity_head = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()  # Output between 0 and 1
        )
        
        self.length_head = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 3)  # short, medium, long
        )
        
        self.engagement_head = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Args:
            x: [batch_size, input_dim]
        
        Returns:
            strategy_logits: [batch_size, num_strategies]
            parameters: Dict of parameter tensors
        """
        
        strategy_logits = self.strategy_head(x)
        
        parameters = {
            "complexity_level": self.complexity_head(x).squeeze(-1),
            "response_length": self.length_head(x),
            "engagement_boost": self.engagement_head(x).squeeze(-1)
        }
        
        return strategy_logits, parameters


class AttentionBlock(nn.Module):
    """Attention block for focusing on relevant conversation parts."""
    
    def __init__(self, hidden_dim: int, num_heads: int = 8):
        super().__init__()
        
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        
        assert hidden_dim % num_heads == 0
        
        self.query_projection = nn.Linear(hidden_dim, hidden_dim)
        self.key_projection = nn.Linear(hidden_dim, hidden_dim)
        self.value_projection = nn.Linear(hidden_dim, hidden_dim)
        self.output_projection = nn.Linear(hidden_dim, hidden_dim)
        
        self.dropout = nn.Dropout(0.1)
        self.layer_norm = nn.LayerNorm(hidden_dim)
    
    def forward(
        self, 
        query: torch.Tensor, 
        key: torch.Tensor, 
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            query: [batch_size, seq_len_q, hidden_dim]
            key: [batch_size, seq_len_k, hidden_dim]
            value: [batch_size, seq_len_v, hidden_dim]
            mask: [batch_size, seq_len_q, seq_len_k]
        
        Returns:
            output: [batch_size, seq_len_q, hidden_dim]
            attention_weights: [batch_size, num_heads, seq_len_q, seq_len_k]
        """
        
        batch_size, seq_len_q, _ = query.shape
        seq_len_k = key.shape[1]
        
        # Linear projections
        Q = self.query_projection(query)
        K = self.key_projection(key)
        V = self.value_projection(value)
        
        # Reshape for multi-head attention
        Q = Q.view(batch_size, seq_len_q, self.num_heads, self.head_dim).transpose(1, 2)
        K = K.view(batch_size, seq_len_k, self.num_heads, self.head_dim).transpose(1, 2)
        V = V.view(batch_size, seq_len_k, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Scaled dot-product attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / (self.head_dim ** 0.5)
        
        if mask is not None:
            scores = scores.masked_fill(mask.unsqueeze(1) == 0, -1e9)
        
        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)
        
        # Apply attention to values
        attended = torch.matmul(attention_weights, V)
        
        # Concatenate heads
        attended = attended.transpose(1, 2).contiguous().view(
            batch_size, seq_len_q, self.hidden_dim
        )
        
        # Output projection
        output = self.output_projection(attended)
        
        # Residual connection and layer norm
        output = self.layer_norm(output + query)
        
        return output, attention_weights


class ConstitutionalConstraintLayer(nn.Module):
    """Layer that enforces constitutional AI constraints."""
    
    def __init__(self, input_dim: int):
        super().__init__()
        
        # Safety constraint heads
        self.safety_head = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 1),
            nn.Sigmoid()  # Safety score between 0 and 1
        )
        
        self.bias_head = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 1),
            nn.Sigmoid()  # Bias score between 0 and 1
        )
        
        self.helpfulness_head = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 1),
            nn.Sigmoid()  # Helpfulness score between 0 and 1
        )
        
        # Constraint enforcement
        self.constraint_gate = nn.Sequential(
            nn.Linear(3, 16),  # 3 constraint scores
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Args:
            x: [batch_size, input_dim]
        
        Returns:
            gated_output: [batch_size, input_dim]
            constraint_scores: Dict of constraint scores
        """
        
        # Calculate constraint scores
        safety_score = self.safety_head(x)
        bias_score = self.bias_head(x)
        helpfulness_score = self.helpfulness_head(x)
        
        # Combine constraint scores
        constraint_scores = torch.cat([safety_score, bias_score, helpfulness_score], dim=-1)
        gate_value = self.constraint_gate(constraint_scores)
        
        # Apply gating to input
        gated_output = x * gate_value
        
        constraint_dict = {
            "safety_score": safety_score.squeeze(-1),
            "bias_score": bias_score.squeeze(-1),
            "helpfulness_score": helpfulness_score.squeeze(-1),
            "gate_value": gate_value.squeeze(-1)
        }
        
        return gated_output, constraint_dict


class PolicyNetwork(nn.Module):
    """Main policy network for RL agent."""
    
    def __init__(self, config: NetworkConfig):
        super().__init__()
        
        self.config = config
        
        # Shared encoder
        self.shared_encoder = SharedEncoder(config)
        
        # Policy-specific layers
        self.policy_layers = nn.ModuleList([
            nn.Sequential(
                nn.Linear(
                    config.context_dim if i == 0 else config.policy_hidden_size,
                    config.policy_hidden_size
                ),
                nn.ReLU(),
                nn.Dropout(config.policy_dropout)
            )
            for i in range(config.policy_num_layers)
        ])
        
        # Attention mechanism for conversation focus
        self.attention_block = AttentionBlock(config.policy_hidden_size, config.policy_num_heads)
        
        # Constitutional constraint layer
        self.constitutional_layer = ConstitutionalConstraintLayer(config.policy_hidden_size)
        
        # Action type head (technical, explanatory, creative, etc.)
        num_action_types = len(ActionType)
        self.action_head = nn.Sequential(
            nn.Linear(config.policy_hidden_size, config.policy_hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(config.policy_hidden_size // 2, num_action_types)
        )
        
        # Response strategy head
        self.strategy_head = ResponseStrategyHead(config.policy_hidden_size)
        
        # Value estimation head (for actor-critic)
        self.value_head = nn.Sequential(
            nn.Linear(config.policy_hidden_size, config.policy_hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(config.policy_hidden_size // 2, 1)
        )
    
    def forward(
        self,
        conversation_states: torch.Tensor,
        user_profile_features: torch.Tensor,
        domain_features: torch.Tensor,
        personalization_features: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> PolicyOutput:
        """
        Args:
            conversation_states: [batch_size, seq_len, state_dim]
            user_profile_features: [batch_size, 64]
            domain_features: [batch_size, 32]
            personalization_features: [batch_size, 16]
            attention_mask: [batch_size, seq_len]
        
        Returns:
            PolicyOutput with action probabilities and parameters
        """
        
        # Shared encoding
        shared_encoding = self.shared_encoder(
            conversation_states,
            user_profile_features,
            domain_features,
            personalization_features,
            attention_mask
        )
        
        # Policy-specific processing
        x = shared_encoding
        for layer in self.policy_layers:
            x = layer(x)
        
        # Apply attention (self-attention on the hidden state)
        x_expanded = x.unsqueeze(1)  # [batch_size, 1, hidden_dim]
        attended_x, attention_weights = self.attention_block(
            x_expanded, x_expanded, x_expanded
        )
        x = attended_x.squeeze(1)  # [batch_size, hidden_dim]
        
        # Apply constitutional constraints
        constrained_x, constraint_scores = self.constitutional_layer(x)
        
        # Generate action logits
        action_logits = self.action_head(constrained_x)
        action_probabilities = F.softmax(action_logits, dim=-1)
        
        # Generate strategy logits and parameters
        strategy_logits, response_parameters = self.strategy_head(constrained_x)
        strategy_probabilities = F.softmax(strategy_logits, dim=-1)
        
        # Add constraint scores to response parameters
        response_parameters.update(constraint_scores)
        
        return PolicyOutput(
            action_logits=action_logits,
            action_probabilities=action_probabilities,
            strategy_logits=strategy_logits,
            strategy_probabilities=strategy_probabilities,
            response_parameters=response_parameters,
            attention_weights=attention_weights,
            hidden_state=constrained_x
        )
    
    def sample_action(self, policy_output: PolicyOutput) -> Tuple[int, int, Dict[str, Any]]:
        """
        Sample action from policy output.
        
        Returns:
            action_type_idx: Index of selected action type
            strategy_idx: Index of selected strategy
            parameters: Sampled parameters
        """
        
        # Sample action type
        action_dist = torch.distributions.Categorical(policy_output.action_probabilities)
        action_type_idx = action_dist.sample().item()
        
        # Sample strategy
        strategy_dist = torch.distributions.Categorical(policy_output.strategy_probabilities)
        strategy_idx = strategy_dist.sample().item()
        
        # Extract parameters (convert tensors to values)
        parameters = {}
        for key, value in policy_output.response_parameters.items():
            if isinstance(value, torch.Tensor):
                if value.dim() == 0:  # Scalar tensor
                    parameters[key] = value.item()
                else:  # Multi-dimensional tensor
                    parameters[key] = value.cpu().numpy()
            else:
                parameters[key] = value
        
        return action_type_idx, strategy_idx, parameters
    
    def get_action_log_probs(
        self, 
        policy_output: PolicyOutput, 
        action_type_idx: torch.Tensor,
        strategy_idx: torch.Tensor
    ) -> torch.Tensor:
        """Get log probabilities for given actions."""
        
        action_log_probs = F.log_softmax(policy_output.action_logits, dim=-1)
        strategy_log_probs = F.log_softmax(policy_output.strategy_logits, dim=-1)
        
        # Gather log probabilities for selected actions
        selected_action_log_probs = action_log_probs.gather(1, action_type_idx.unsqueeze(1))
        selected_strategy_log_probs = strategy_log_probs.gather(1, strategy_idx.unsqueeze(1))
        
        # Combine log probabilities
        total_log_probs = selected_action_log_probs + selected_strategy_log_probs
        
        return total_log_probs.squeeze(1)
    
    def get_entropy(self, policy_output: PolicyOutput) -> torch.Tensor:
        """Calculate entropy of the policy distribution."""
        
        action_entropy = -(policy_output.action_probabilities * 
                          F.log_softmax(policy_output.action_logits, dim=-1)).sum(dim=-1)
        
        strategy_entropy = -(policy_output.strategy_probabilities * 
                           F.log_softmax(policy_output.strategy_logits, dim=-1)).sum(dim=-1)
        
        return action_entropy + strategy_entropy
    
    def save_checkpoint(self, path: str) -> None:
        """Save model checkpoint."""
        torch.save({
            'model_state_dict': self.state_dict(),
            'config': self.config
        }, path)
        logger.info(f"Policy network checkpoint saved to {path}")
    
    @classmethod
    def load_checkpoint(cls, path: str, config: NetworkConfig) -> 'PolicyNetwork':
        """Load model from checkpoint."""
        checkpoint = torch.load(path, map_location='cpu')
        
        model = cls(config)
        model.load_state_dict(checkpoint['model_state_dict'])
        
        logger.info(f"Policy network loaded from {path}")
        return model