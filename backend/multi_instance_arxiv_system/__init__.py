"""
Multi-Instance ArXiv System

This package extends the existing ArXiv RAG Enhancement system to support
multiple scholar instances (AI Scholar and Quant Scholar) with automated
monthly updates, comprehensive monitoring, and robust infrastructure.
"""

__version__ = "1.0.0"
__author__ = "AI Scholar Team"

# Import main components for easy access
from .shared.instance_manager import InstanceManager
from .shared.multi_instance_state_manager import MultiInstanceStateManager
from .shared.multi_instance_progress_tracker import MultiInstanceProgressTracker
from .shared.multi_instance_error_handler import MultiInstanceErrorHandler
from .config.instance_config_manager import InstanceConfigManager

__all__ = [
    'InstanceManager',
    'MultiInstanceStateManager', 
    'MultiInstanceProgressTracker',
    'MultiInstanceErrorHandler',
    'InstanceConfigManager'
]