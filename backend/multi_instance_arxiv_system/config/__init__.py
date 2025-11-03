"""
Configuration management for multi-instance ArXiv system.

This module provides configuration management capabilities for multiple scholar
instances with YAML support, validation, and environment variable integration.
"""

from .instance_config_manager import InstanceConfigManager
from .default_instance_configs import DEFAULT_AI_SCHOLAR_CONFIG, DEFAULT_QUANT_SCHOLAR_CONFIG

__all__ = [
    'InstanceConfigManager',
    'DEFAULT_AI_SCHOLAR_CONFIG',
    'DEFAULT_QUANT_SCHOLAR_CONFIG'
]