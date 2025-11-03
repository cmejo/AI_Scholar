"""
Configuration management for the RL system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import os
import json
from pathlib import Path


@dataclass
class NetworkConfig:
    """Configuration for neural networks."""
    # Policy network
    policy_hidden_size: int = 512
    policy_num_layers: int = 6
    policy_num_heads: int = 8
    policy_dropout: float = 0.1
    policy_activation: str = "gelu"
    
    # Value network
    value_hidden_size: int = 256
    value_num_layers: int = 4
    value_dropout: float = 0.1
    
    # Shared encoder
    encoder_hidden_size: int = 768
    encoder_num_layers: int = 12
    encoder_num_heads: int = 12
    
    # Input/output dimensions
    state_dim: int = 512
    action_dim: int = 256
    context_dim: int = 768
    
    # Device configuration
    device: str = "cuda" if os.environ.get("CUDA_AVAILABLE", "false").lower() == "true" else "cpu"
    mixed_precision: bool = True


@dataclass
class TrainingConfig:
    """Configuration for RL training."""
    # PPO hyperparameters
    learning_rate: float = 3e-4
    batch_size: int = 64
    mini_batch_size: int = 16
    num_epochs: int = 4
    clip_epsilon: float = 0.2
    value_loss_coef: float = 0.5
    entropy_coef: float = 0.01
    max_grad_norm: float = 0.5
    
    # Experience collection
    rollout_length: int = 2048
    num_envs: int = 1
    gae_lambda: float = 0.95
    gamma: float = 0.99
    
    # Training schedule
    total_timesteps: int = 1000000
    save_frequency: int = 10000
    eval_frequency: int = 5000
    log_frequency: int = 1000
    
    # Experience buffer
    buffer_size: int = 100000
    prioritized_replay: bool = True
    priority_alpha: float = 0.6
    priority_beta: float = 0.4
    priority_beta_increment: float = 0.001
    
    # Model management
    max_model_versions: int = 10
    auto_deploy_threshold: float = 0.05  # Performance improvement threshold
    rollback_threshold: float = -0.1     # Performance degradation threshold
    
    # Safety constraints
    max_training_hours: int = 24
    convergence_patience: int = 10
    min_improvement_threshold: float = 0.001


@dataclass
class RewardConfig:
    """Configuration for reward calculation."""
    # Reward component weights
    helpfulness_weight: float = 0.25
    accuracy_weight: float = 0.25
    engagement_weight: float = 0.15
    safety_weight: float = 0.15
    learning_effectiveness_weight: float = 0.1
    personalization_weight: float = 0.05
    efficiency_weight: float = 0.03
    creativity_weight: float = 0.02
    
    # Reward scaling
    reward_scale: float = 1.0
    reward_clip_min: float = -1.0
    reward_clip_max: float = 1.0
    
    # Reward calculation
    use_advantage_normalization: bool = True
    reward_smoothing_factor: float = 0.1
    
    # Safety penalties
    safety_penalty_factor: float = 0.5
    bias_penalty_factor: float = 0.3
    harmful_content_penalty: float = -1.0
    
    # Feedback processing
    explicit_feedback_weight: float = 1.0
    implicit_feedback_weight: float = 0.5
    quality_assessment_weight: float = 0.8
    
    # Temporal considerations
    immediate_reward_weight: float = 0.7
    delayed_reward_weight: float = 0.3
    conversation_completion_bonus: float = 0.1


@dataclass
class SafetyConfig:
    """Configuration for safety constraints and monitoring."""
    # Constitutional AI constraints
    enable_constitutional_ai: bool = True
    constitutional_principles: List[str] = field(default_factory=lambda: [
        "Be helpful and harmless",
        "Provide accurate information",
        "Respect user privacy",
        "Avoid harmful or biased content",
        "Maintain professional boundaries"
    ])
    
    # Content filtering
    enable_content_filtering: bool = True
    toxicity_threshold: float = 0.1
    bias_threshold: float = 0.2
    harmful_content_threshold: float = 0.05
    
    # Response validation
    enable_response_validation: bool = True
    max_response_length: int = 2000
    min_response_length: int = 10
    require_factual_grounding: bool = True
    
    # Fallback mechanisms
    enable_fallback_responses: bool = True
    fallback_confidence_threshold: float = 0.3
    max_consecutive_fallbacks: int = 3
    
    # Monitoring and alerting
    enable_safety_monitoring: bool = True
    safety_alert_threshold: float = 0.1
    anomaly_detection_sensitivity: float = 0.05
    
    # Privacy protection
    enable_privacy_protection: bool = True
    data_retention_days: int = 90
    anonymize_stored_data: bool = True
    require_user_consent: bool = True


@dataclass
class RLConfig:
    """Main RL system configuration."""
    # Sub-configurations
    network: NetworkConfig = field(default_factory=NetworkConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    reward: RewardConfig = field(default_factory=RewardConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    
    # System settings
    environment: str = "development"  # development, staging, production
    debug_mode: bool = True
    verbose_logging: bool = True
    
    # Integration settings
    enable_real_time_learning: bool = False  # Start with batch learning
    enable_personalization: bool = True
    enable_a_b_testing: bool = False
    
    # Performance settings
    max_concurrent_conversations: int = 100
    response_timeout_seconds: int = 30
    training_timeout_hours: int = 6
    
    # Storage settings
    model_storage_path: str = "models/rl/"
    experience_storage_path: str = "data/rl/experiences/"
    logs_storage_path: str = "logs/rl/"
    
    # API settings
    api_rate_limit: int = 1000  # requests per hour per user
    enable_api_authentication: bool = True
    
    def validate(self) -> List[str]:
        """Validate configuration and return any errors."""
        errors = []
        
        # Validate reward weights sum to reasonable range
        total_weight = (
            self.reward.helpfulness_weight + self.reward.accuracy_weight +
            self.reward.engagement_weight + self.reward.safety_weight +
            self.reward.learning_effectiveness_weight + self.reward.personalization_weight +
            self.reward.efficiency_weight + self.reward.creativity_weight
        )
        
        if abs(total_weight - 1.0) > 0.1:
            errors.append(f"Reward weights sum to {total_weight}, should be close to 1.0")
        
        # Validate training parameters
        if self.training.batch_size < self.training.mini_batch_size:
            errors.append("Batch size must be >= mini batch size")
        
        if self.training.learning_rate <= 0 or self.training.learning_rate > 1:
            errors.append("Learning rate must be between 0 and 1")
        
        # Validate safety thresholds
        if not (0 <= self.safety.toxicity_threshold <= 1):
            errors.append("Toxicity threshold must be between 0 and 1")
        
        # Validate network dimensions
        if self.network.state_dim <= 0 or self.network.action_dim <= 0:
            errors.append("Network dimensions must be positive")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "network": {
                "policy_hidden_size": self.network.policy_hidden_size,
                "policy_num_layers": self.network.policy_num_layers,
                "policy_num_heads": self.network.policy_num_heads,
                "policy_dropout": self.network.policy_dropout,
                "value_hidden_size": self.network.value_hidden_size,
                "value_num_layers": self.network.value_num_layers,
                "state_dim": self.network.state_dim,
                "action_dim": self.network.action_dim,
                "device": self.network.device
            },
            "training": {
                "learning_rate": self.training.learning_rate,
                "batch_size": self.training.batch_size,
                "num_epochs": self.training.num_epochs,
                "clip_epsilon": self.training.clip_epsilon,
                "buffer_size": self.training.buffer_size,
                "prioritized_replay": self.training.prioritized_replay
            },
            "reward": {
                "helpfulness_weight": self.reward.helpfulness_weight,
                "accuracy_weight": self.reward.accuracy_weight,
                "engagement_weight": self.reward.engagement_weight,
                "safety_weight": self.reward.safety_weight,
                "reward_scale": self.reward.reward_scale
            },
            "safety": {
                "enable_constitutional_ai": self.safety.enable_constitutional_ai,
                "enable_content_filtering": self.safety.enable_content_filtering,
                "toxicity_threshold": self.safety.toxicity_threshold,
                "enable_fallback_responses": self.safety.enable_fallback_responses
            },
            "system": {
                "environment": self.environment,
                "debug_mode": self.debug_mode,
                "enable_personalization": self.enable_personalization,
                "max_concurrent_conversations": self.max_concurrent_conversations
            }
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'RLConfig':
        """Create configuration from dictionary."""
        config = cls()
        
        # Update network config
        if "network" in config_dict:
            net_config = config_dict["network"]
            for key, value in net_config.items():
                if hasattr(config.network, key):
                    setattr(config.network, key, value)
        
        # Update training config
        if "training" in config_dict:
            train_config = config_dict["training"]
            for key, value in train_config.items():
                if hasattr(config.training, key):
                    setattr(config.training, key, value)
        
        # Update reward config
        if "reward" in config_dict:
            reward_config = config_dict["reward"]
            for key, value in reward_config.items():
                if hasattr(config.reward, key):
                    setattr(config.reward, key, value)
        
        # Update safety config
        if "safety" in config_dict:
            safety_config = config_dict["safety"]
            for key, value in safety_config.items():
                if hasattr(config.safety, key):
                    setattr(config.safety, key, value)
        
        # Update system settings
        if "system" in config_dict:
            system_config = config_dict["system"]
            for key, value in system_config.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        return config


def load_config_from_file(config_path: str) -> RLConfig:
    """Load configuration from JSON file."""
    config_file = Path(config_path)
    
    if not config_file.exists():
        # Return default configuration if file doesn't exist
        return RLConfig()
    
    try:
        with open(config_file, 'r') as f:
            config_dict = json.load(f)
        return RLConfig.from_dict(config_dict)
    except Exception as e:
        print(f"Error loading config from {config_path}: {e}")
        return RLConfig()


def save_config_to_file(config: RLConfig, config_path: str) -> None:
    """Save configuration to JSON file."""
    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config.to_dict(), f, indent=2)
    except Exception as e:
        print(f"Error saving config to {config_path}: {e}")


def get_rl_config(environment: Optional[str] = None) -> RLConfig:
    """Get RL configuration for the specified environment."""
    if environment is None:
        environment = os.getenv("RL_ENVIRONMENT", "development")
    
    # Try to load environment-specific config
    config_path = f"backend/rl/config/{environment}.json"
    config = load_config_from_file(config_path)
    
    # Set environment
    config.environment = environment
    
    # Environment-specific overrides
    if environment == "production":
        config.debug_mode = False
        config.verbose_logging = False
        config.safety.enable_constitutional_ai = True
        config.safety.enable_content_filtering = True
        config.training.save_frequency = 5000
        config.enable_real_time_learning = True
    elif environment == "staging":
        config.debug_mode = False
        config.verbose_logging = True
        config.enable_a_b_testing = True
    else:  # development
        config.debug_mode = True
        config.verbose_logging = True
        config.training.total_timesteps = 10000  # Smaller for dev
    
    # Validate configuration
    errors = config.validate()
    if errors:
        print(f"Configuration validation errors: {errors}")
    
    return config