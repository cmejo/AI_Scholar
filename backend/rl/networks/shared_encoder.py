"""
Shared encoder components for RL networks.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any
import math
import logging

from ..core.config import NetworkConfig

logger = logging.getLogger(__name__)


class PositionalEncoding(nn.Module):
    """Positional encoding for transformer-based models."""
    
    def __init__(self, d_model: int, max_len: int = 5000):
        super().__init__()
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        
        self.register_buffer('pe', pe)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:x.size(0), :]


class MultiHeadAttention(nn.Module):
    """Multi-head attention mechanism."""
    
    def __init__(self, d_model: int, num_heads: int, dropout: float = 0.1):
        super().__init__()
        assert d_model % num_heads == 0
        
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        
        self.w_q = nn.Linear(d_model, d_model)
        self.w_k = nn.Linear(d_model, d_model)
        self.w_v = nn.Linear(d_model, d_model)
        self.w_o = nn.Linear(d_model, d_model)
        
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(d_model)
    
    def forward(
        self, 
        query: torch.Tensor, 
        key: torch.Tensor, 
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        
        batch_size = query.size(0)
        seq_len = query.size(1)
        
        # Linear transformations and reshape
        Q = self.w_q(query).view(batch_size, seq_len, self.num_heads, self.d_k).transpose(1, 2)
        K = self.w_k(key).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        V = self.w_v(value).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        
        # Attention
        attention_output = self._attention(Q, K, V, mask)
        
        # Concatenate heads and put through final linear layer
        attention_output = attention_output.transpose(1, 2).contiguous().view(
            batch_size, seq_len, self.d_model
        )
        
        output = self.w_o(attention_output)
        
        # Residual connection and layer norm
        return self.layer_norm(output + query)
    
    def _attention(
        self, 
        Q: torch.Tensor, 
        K: torch.Tensor, 
        V: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)
        
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)
        
        return torch.matmul(attention_weights, V)


class FeedForward(nn.Module):
    """Feed-forward network for transformer blocks."""
    
    def __init__(self, d_model: int, d_ff: int, dropout: float = 0.1):
        super().__init__()
        
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(d_model)
        self.activation = nn.GELU()
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        x = self.linear1(x)
        x = self.activation(x)
        x = self.dropout(x)
        x = self.linear2(x)
        x = self.dropout(x)
        return self.layer_norm(x + residual)


class TransformerBlock(nn.Module):
    """Single transformer block."""
    
    def __init__(self, d_model: int, num_heads: int, d_ff: int, dropout: float = 0.1):
        super().__init__()
        
        self.attention = MultiHeadAttention(d_model, num_heads, dropout)
        self.feed_forward = FeedForward(d_model, d_ff, dropout)
    
    def forward(
        self, 
        x: torch.Tensor, 
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        
        x = self.attention(x, x, x, mask)
        x = self.feed_forward(x)
        return x


class ConversationEncoder(nn.Module):
    """Encodes conversation history into context representations."""
    
    def __init__(self, config: NetworkConfig):
        super().__init__()
        
        self.config = config
        self.d_model = config.encoder_hidden_size
        
        # Input embeddings
        self.input_embedding = nn.Linear(config.state_dim, self.d_model)
        self.positional_encoding = PositionalEncoding(self.d_model)
        
        # Transformer layers
        self.transformer_layers = nn.ModuleList([
            TransformerBlock(
                self.d_model,
                config.encoder_num_heads,
                self.d_model * 4,
                config.encoder_dropout if hasattr(config, 'encoder_dropout') else 0.1
            )
            for _ in range(config.encoder_num_layers)
        ])
        
        # Output projection
        self.output_projection = nn.Linear(self.d_model, config.context_dim)
        self.dropout = nn.Dropout(0.1)
    
    def forward(
        self, 
        conversation_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Args:
            conversation_states: [batch_size, seq_len, state_dim]
            attention_mask: [batch_size, seq_len]
        
        Returns:
            context_representation: [batch_size, context_dim]
        """
        
        # Input embedding and positional encoding
        x = self.input_embedding(conversation_states)
        x = self.positional_encoding(x)
        x = self.dropout(x)
        
        # Apply transformer layers
        for layer in self.transformer_layers:
            x = layer(x, attention_mask)
        
        # Global pooling (mean over sequence length)
        if attention_mask is not None:
            # Masked mean pooling
            mask_expanded = attention_mask.unsqueeze(-1).expand_as(x)
            x_masked = x * mask_expanded
            context = x_masked.sum(dim=1) / mask_expanded.sum(dim=1)
        else:
            # Simple mean pooling
            context = x.mean(dim=1)
        
        # Output projection
        context = self.output_projection(context)
        
        return context


class ContextEncoder(nn.Module):
    """Encodes various context information (user profile, domain, etc.)."""
    
    def __init__(self, config: NetworkConfig):
        super().__init__()
        
        self.config = config
        
        # User profile encoding
        self.user_profile_encoder = nn.Sequential(
            nn.Linear(64, 128),  # Assuming 64-dim user profile features
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 256)
        )
        
        # Domain context encoding
        self.domain_encoder = nn.Sequential(
            nn.Linear(32, 64),   # Assuming 32-dim domain features
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 128)
        )
        
        # Personalization context encoding
        self.personalization_encoder = nn.Sequential(
            nn.Linear(16, 32),   # Assuming 16-dim personalization features
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(32, 64)
        )
        
        # Fusion layer
        self.fusion_layer = nn.Sequential(
            nn.Linear(256 + 128 + 64, config.context_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(config.context_dim, config.context_dim)
        )
    
    def forward(
        self,
        user_profile_features: torch.Tensor,
        domain_features: torch.Tensor,
        personalization_features: torch.Tensor
    ) -> torch.Tensor:
        """
        Args:
            user_profile_features: [batch_size, 64]
            domain_features: [batch_size, 32]
            personalization_features: [batch_size, 16]
        
        Returns:
            context_encoding: [batch_size, context_dim]
        """
        
        # Encode each context component
        user_encoded = self.user_profile_encoder(user_profile_features)
        domain_encoded = self.domain_encoder(domain_features)
        personalization_encoded = self.personalization_encoder(personalization_features)
        
        # Concatenate and fuse
        combined = torch.cat([user_encoded, domain_encoded, personalization_encoded], dim=-1)
        context_encoding = self.fusion_layer(combined)
        
        return context_encoding


class SharedEncoder(nn.Module):
    """Shared encoder that combines conversation and context encoding."""
    
    def __init__(self, config: NetworkConfig):
        super().__init__()
        
        self.config = config
        self.conversation_encoder = ConversationEncoder(config)
        self.context_encoder = ContextEncoder(config)
        
        # Final fusion layer
        self.final_fusion = nn.Sequential(
            nn.Linear(config.context_dim * 2, config.context_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(config.context_dim, config.context_dim)
        )
        
        # Layer normalization
        self.layer_norm = nn.LayerNorm(config.context_dim)
    
    def forward(
        self,
        conversation_states: torch.Tensor,
        user_profile_features: torch.Tensor,
        domain_features: torch.Tensor,
        personalization_features: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Args:
            conversation_states: [batch_size, seq_len, state_dim]
            user_profile_features: [batch_size, 64]
            domain_features: [batch_size, 32]
            personalization_features: [batch_size, 16]
            attention_mask: [batch_size, seq_len]
        
        Returns:
            shared_encoding: [batch_size, context_dim]
        """
        
        # Encode conversation history
        conversation_encoding = self.conversation_encoder(
            conversation_states, attention_mask
        )
        
        # Encode context information
        context_encoding = self.context_encoder(
            user_profile_features, domain_features, personalization_features
        )
        
        # Fuse conversation and context encodings
        combined = torch.cat([conversation_encoding, context_encoding], dim=-1)
        shared_encoding = self.final_fusion(combined)
        shared_encoding = self.layer_norm(shared_encoding)
        
        return shared_encoding
    
    def get_conversation_encoding(
        self,
        conversation_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Get only conversation encoding (useful for some applications)."""
        return self.conversation_encoder(conversation_states, attention_mask)
    
    def get_context_encoding(
        self,
        user_profile_features: torch.Tensor,
        domain_features: torch.Tensor,
        personalization_features: torch.Tensor
    ) -> torch.Tensor:
        """Get only context encoding (useful for some applications)."""
        return self.context_encoder(
            user_profile_features, domain_features, personalization_features
        )