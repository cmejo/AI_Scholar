"""
Configuration management for arXiv RAG Enhancement system.

This module provides centralized configuration management for all three
processing scripts, including YAML/JSON configuration files, command-line
argument parsing, and environment variable support.
"""

from .config_manager import ConfigManager
from .default_config import DEFAULT_CONFIG

__all__ = [
    'ConfigManager',
    'DEFAULT_CONFIG'
]