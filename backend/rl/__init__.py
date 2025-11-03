"""
Reinforcement Learning System for AI Scholar Chatbot

This package implements a comprehensive reinforcement learning system that enhances
the AI Scholar chatbot with adaptive learning, personalization, and safety features.

Key Components:
- Policy and Value Networks with Constitutional AI constraints
- Multi-objective reward system with safety validation
- User modeling and personalization engine
- Experience buffer with privacy protection
- Training infrastructure with PPO algorithm
- Safety monitoring and constitutional AI
- Real-time API endpoints and WebSocket support

Usage:
    from backend.rl import RLSystem
    
    # Initialize RL system
    rl_system = RLSystem()
    await rl_system.initialize()
    
    # Generate RL-enhanced response
    response = await rl_system.generate_response(user_input, context)
"""

from .core.config import RLConfig, get_rl_config
from .agent.rl_agent_controller import RLAgentController, RLResponse
from .agent.conversation_manager import ConversationManager
from .api.rl_endpoints import rl_router
from .api.websocket_handler import websocket_manager

__version__ = "1.0.0"
__author__ = "AI Scholar RL Team"

__all__ = [
    "RLConfig",
    "get_rl_config", 
    "RLAgentController",
    "RLResponse",
    "ConversationManager",
    "rl_router",
    "websocket_manager"
]


class RLSystem:
    """Main RL system class that coordinates all components."""
    
    def __init__(self, config: RLConfig = None):
        self.config = config or get_rl_config()
        self.agent_controller = RLAgentController(self.config)
        self.conversation_manager = ConversationManager(self.config, self.agent_controller)
    
    async def initialize(self):
        """Initialize the RL system."""
        await self.agent_controller.initialize()
        await self.conversation_manager.initialize()
    
    async def generate_response(self, user_input: str, context: dict):
        """Generate RL-enhanced response."""
        # Implementation would use conversation_manager
        pass
    
    async def shutdown(self):
        """Shutdown the RL system."""
        await self.conversation_manager.shutdown()
        await self.agent_controller.shutdown()