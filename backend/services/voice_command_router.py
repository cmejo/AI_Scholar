"""
Voice Command Router and Execution Framework
Handles routing and execution of voice commands with contextual conversation management
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import uuid
from enum import Enum

from .voice_nlp_service import VoiceNLPService, VoiceCommand, ConversationContext

try:
    from ..core.config import Config
except ImportError:
    # Fallback for testing
    class Config:
        def __init__(self):
            pass

logger = logging.getLogger(__name__)

class CommandStatus(Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CommandPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class CommandExecution:
    """Represents a command execution instance"""
    execution_id: str
    command: VoiceCommand
    status: CommandStatus
    priority: CommandPriority
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class CommandResult:
    """Represents the result of a command execution"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    follow_up_actions: List[str] = None
    context_updates: Dict[str, Any] = None

@dataclass
class ConversationState:
    """Enhanced conversation state with multi-turn support"""
    session_id: str
    user_id: Optional[str]
    current_intent: Optional[str]
    pending_clarifications: List[str]
    context_variables: Dict[str, Any]
    conversation_flow: List[str]
    last_activity: datetime
    is_active: bool = True
    turn_count: int = 0

class VoiceCommandRouter:
    """Enhanced voice command router with execution framework and conversation management"""
    
    def __init__(self):
        self.config = Config()
        self.nlp_service = VoiceNLPService()
        
        # Command handlers registry
        self.command_handlers: Dict[str, Callable] = {}
        self.middleware_stack: List[Callable] = []
        
        # Execution management
        self.active_executions: Dict[str, CommandExecution] = {}
        self.execution_queue: asyncio.Queue = asyncio.Queue()
        self.conversation_states: Dict[str, ConversationState] = {}
        
        # Configuration
        self.max_concurrent_executions = 5
        self.command_timeout = 30.0  # seconds
        self.conversation_timeout = 1800.0  # 30 minutes
        
        # Initialize built-in handlers
        self._initialize_builtin_handlers()
        self._initialize_middleware()
        
        # Start background tasks
        asyncio.create_task(self._execution_worker())
        asyncio.create_task(self._cleanup_worker())
    
    def _initialize_builtin_handlers(self):
        """Initialize built-in command handlers"""
        
        # Search command handler
        @self.register_handler('search')
        async def handle_search(command: VoiceCommand, context: ConversationState) -> CommandResult:
            """Handle search commands with context awareness"""
            try:
                # Extract search query from entities or text
                query = self._extract_search_query(command, context)
                
                if not query:
                    return CommandResult(
                        success=False,
                        message="I need more information. What would you like to search for?",
                        follow_up_actions=["request_clarification"]
                    )
                
                # Perform contextual search
                search_results = await self._perform_contextual_search(query, context)
                
                # Update conversation context
                context_updates = {
                    'last_search_query': query,
                    'search_results_count': len(search_results.get('results', [])),
                    'current_intent': 'search'
                }
                
                return CommandResult(
                    success=True,
                    message=f"Found {len(search_results.get('results', []))} results for '{query}'",
                    data=search_results,
                    context_updates=context_updates,
                    follow_up_actions=["display_search_results"]
                )
                
            except Exception as e:
                logger.error(f"Search command execution failed: {str(e)}")
                return CommandResult(
                    success=False,
                    message="I encountered an error while searching. Please try again.",
                    error=str(e)
                )
        
        # Navigation command handler
        @self.register_handler('navigate')
        async def handle_navigate(command: VoiceCommand, context: ConversationState) -> CommandResult:
            """Handle navigation commands with context awareness"""
            try:
                # Extract navigation target
                target = self._extract_navigation_target(command, context)
                
                if not target:
                    return CommandResult(
                        success=False,
                        message="Where would you like to go?",
                        follow_up_actions=["request_clarification"]
                    )
                
                # Validate navigation target
                valid_targets = await self._get_valid_navigation_targets(context)
                
                if target not in valid_targets:
                    suggestions = self._get_navigation_suggestions(target, valid_targets)
                    return CommandResult(
                        success=False,
                        message=f"I couldn't find '{target}'. Did you mean: {', '.join(suggestions[:3])}?",
                        data={'suggestions': suggestions},
                        follow_up_actions=["provide_suggestions"]
                    )
                
                # Execute navigation
                navigation_result = await self._execute_navigation(target, context)
                
                context_updates = {
                    'current_page': target,
                    'navigation_history': context.context_variables.get('navigation_history', []) + [target],
                    'current_intent': 'navigate'
                }
                
                return CommandResult(
                    success=True,
                    message=f"Navigating to {target}",
                    data=navigation_result,
                    context_updates=context_updates,
                    follow_up_actions=["navigate_to_page"]
                )
                
            except Exception as e:
                logger.error(f"Navigation command execution failed: {str(e)}")
                return CommandResult(
                    success=False,
                    message="I couldn't navigate to that location. Please try again.",
                    error=str(e)
                )
        
        # Document command handler
        @self.register_handler('document')
        async def handle_document(command: VoiceCommand, context: ConversationState) -> CommandResult:
            """Handle document commands with context awareness"""
            try:
                # Extract document action and target
                action, document_info = self._extract_document_action(command, context)
                
                if not action:
                    return CommandResult(
                        success=False,
                        message="What would you like to do with the document?",
                        follow_up_actions=["request_clarification"]
                    )
                
                # Execute document action based on type
                if action == 'upload':
                    result = await self._handle_document_upload(document_info, context)
                elif action == 'open':
                    result = await self._handle_document_open(document_info, context)
                elif action == 'delete':
                    result = await self._handle_document_delete(document_info, context)
                elif action == 'summarize':
                    result = await self._handle_document_summarize(document_info, context)
                else:
                    return CommandResult(
                        success=False,
                        message=f"I don't know how to {action} documents yet.",
                        error=f"Unsupported document action: {action}"
                    )
                
                context_updates = {
                    'last_document_action': action,
                    'current_document': document_info.get('name'),
                    'current_intent': 'document'
                }
                
                return CommandResult(
                    success=result['success'],
                    message=result['message'],
                    data=result.get('data'),
                    error=result.get('error'),
                    context_updates=context_updates,
                    follow_up_actions=result.get('follow_up_actions', [])
                )
                
            except Exception as e:
                logger.error(f"Document command execution failed: {str(e)}")
                return CommandResult(
                    success=False,
                    message="I encountered an error with the document operation. Please try again.",
                    error=str(e)
                )
        
        # Chat command handler
        @self.register_handler('chat')
        async def handle_chat(command: VoiceCommand, context: ConversationState) -> CommandResult:
            """Handle chat/question commands with conversation context"""
            try:
                # Extract question or chat query
                query = self._extract_chat_query(command, context)
                
                if not query:
                    return CommandResult(
                        success=False,
                        message="What would you like to know?",
                        follow_up_actions=["request_clarification"]
                    )
                
                # Process chat query with conversation context
                chat_response = await self._process_chat_query(query, context)
                
                context_updates = {
                    'last_question': query,
                    'conversation_topic': chat_response.get('topic'),
                    'current_intent': 'chat'
                }
                
                return CommandResult(
                    success=True,
                    message=chat_response['response'],
                    data=chat_response,
                    context_updates=context_updates,
                    follow_up_actions=["display_chat_response"]
                )
                
            except Exception as e:
                logger.error(f"Chat command execution failed: {str(e)}")
                return CommandResult(
                    success=False,
                    message="I'm having trouble processing your question. Could you rephrase it?",
                    error=str(e)
                )
        
        # System command handler
        @self.register_handler('system')
        async def handle_system(command: VoiceCommand, context: ConversationState) -> CommandResult:
            """Handle system commands"""
            try:
                system_action = self._extract_system_action(command)
                
                if system_action == 'help':
                    help_content = await self._generate_contextual_help(context)
                    return CommandResult(
                        success=True,
                        message="Here's what I can help you with:",
                        data=help_content,
                        follow_up_actions=["display_help"]
                    )
                
                elif system_action == 'settings':
                    return CommandResult(
                        success=True,
                        message="Opening settings",
                        follow_up_actions=["open_settings"]
                    )
                
                elif system_action in ['stop', 'cancel', 'quit']:
                    await self._cleanup_conversation_state(context.session_id)
                    return CommandResult(
                        success=True,
                        message="Voice commands stopped",
                        follow_up_actions=["stop_voice_interface"]
                    )
                
                elif system_action == 'repeat':
                    last_result = context.context_variables.get('last_command_result')
                    if last_result:
                        return CommandResult(
                            success=True,
                            message=last_result.get('message', 'Repeating last action'),
                            data=last_result,
                            follow_up_actions=["repeat_last_action"]
                        )
                    else:
                        return CommandResult(
                            success=False,
                            message="There's nothing to repeat",
                            follow_up_actions=["request_clarification"]
                        )
                
                else:
                    return CommandResult(
                        success=False,
                        message=f"I don't understand the system command: {system_action}",
                        error=f"Unknown system action: {system_action}"
                    )
                
            except Exception as e:
                logger.error(f"System command execution failed: {str(e)}")
                return CommandResult(
                    success=False,
                    message="I encountered a system error. Please try again.",
                    error=str(e)
                )
        
        # Voice control command handler
        @self.register_handler('voice_control')
        async def handle_voice_control(command: VoiceCommand, context: ConversationState) -> CommandResult:
            """Handle voice control commands"""
            try:
                voice_action = self._extract_voice_action(command)
                
                if voice_action in ['speak', 'read', 'say']:
                    content = self._extract_speech_content(command)
                    return CommandResult(
                        success=True,
                        message=f"Speaking: {content}",
                        data={'content': content, 'action': 'speak'},
                        follow_up_actions=["text_to_speech"]
                    )
                
                elif voice_action in ['louder', 'quieter', 'faster', 'slower']:
                    adjustment = self._map_voice_adjustment(voice_action)
                    return CommandResult(
                        success=True,
                        message=f"Adjusting voice {voice_action}",
                        data={'adjustment': adjustment},
                        follow_up_actions=["adjust_voice_settings"]
                    )
                
                elif voice_action in ['mute', 'unmute']:
                    return CommandResult(
                        success=True,
                        message=f"Voice {voice_action}d",
                        data={'action': voice_action},
                        follow_up_actions=["toggle_voice_mute"]
                    )
                
                else:
                    return CommandResult(
                        success=False,
                        message=f"I don't understand the voice control command: {voice_action}",
                        error=f"Unknown voice action: {voice_action}"
                    )
                
            except Exception as e:
                logger.error(f"Voice control command execution failed: {str(e)}")
                return CommandResult(
                    success=False,
                    message="I encountered an error with voice control. Please try again.",
                    error=str(e)
                )
    
    def _initialize_middleware(self):
        """Initialize middleware stack for command processing"""
        
        # Authentication middleware
        async def auth_middleware(command: VoiceCommand, context: ConversationState, next_handler):
            """Authenticate user and validate permissions"""
            # In a real implementation, this would check user authentication
            # For now, we'll just pass through
            return await next_handler(command, context)
        
        # Rate limiting middleware
        async def rate_limit_middleware(command: VoiceCommand, context: ConversationState, next_handler):
            """Apply rate limiting to prevent abuse"""
            # Check if user has exceeded rate limits
            current_time = datetime.now()
            last_command_time = context.context_variables.get('last_command_time')
            
            if last_command_time:
                time_diff = (current_time - last_command_time).total_seconds()
                if time_diff < 1.0:  # Minimum 1 second between commands
                    return CommandResult(
                        success=False,
                        message="Please wait a moment before sending another command",
                        error="Rate limit exceeded"
                    )
            
            context.context_variables['last_command_time'] = current_time
            return await next_handler(command, context)
        
        # Logging middleware
        async def logging_middleware(command: VoiceCommand, context: ConversationState, next_handler):
            """Log command execution for monitoring and debugging"""
            start_time = datetime.now()
            
            logger.info(f"Executing command: {command.intent.name} for session {context.session_id}")
            
            try:
                result = await next_handler(command, context)
                execution_time = (datetime.now() - start_time).total_seconds()
                
                logger.info(f"Command completed in {execution_time:.2f}s: {result.success}")
                result.execution_time = execution_time
                
                return result
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.error(f"Command failed after {execution_time:.2f}s: {str(e)}")
                raise
        
        # Add middleware to stack
        self.middleware_stack = [
            auth_middleware,
            rate_limit_middleware,
            logging_middleware
        ]
    
    def register_handler(self, intent: str):
        """Decorator to register command handlers"""
        def decorator(handler_func):
            self.command_handlers[intent] = handler_func
            return handler_func
        return decorator
    
    def add_middleware(self, middleware_func: Callable):
        """Add middleware to the processing stack"""
        self.middleware_stack.append(middleware_func)
    
    async def process_voice_command(self, text: str, session_id: str = "default", 
                                   user_id: Optional[str] = None) -> CommandResult:
        """
        Process a voice command with full NLP, routing, and execution
        
        Args:
            text: Voice command text
            session_id: Conversation session ID
            user_id: Optional user ID for personalization
            
        Returns:
            CommandResult with execution details
        """
        try:
            # Process command with NLP service
            command = await self.nlp_service.process_command(text, session_id)
            
            # Get or create conversation state
            conversation_state = self._get_or_create_conversation_state(session_id, user_id)
            
            # Update conversation state
            conversation_state.turn_count += 1
            conversation_state.last_activity = datetime.now()
            conversation_state.conversation_flow.append(command.intent.name)
            
            # Create command execution
            execution = CommandExecution(
                execution_id=str(uuid.uuid4()),
                command=command,
                status=CommandStatus.PENDING,
                priority=self._determine_command_priority(command, conversation_state),
                created_at=datetime.now(),
                context={'session_id': session_id, 'user_id': user_id}
            )
            
            # Add to execution queue
            await self.execution_queue.put(execution)
            self.active_executions[execution.execution_id] = execution
            
            # Execute command with middleware stack
            result = await self._execute_command_with_middleware(command, conversation_state)
            
            # Update execution status
            execution.status = CommandStatus.COMPLETED if result.success else CommandStatus.FAILED
            execution.completed_at = datetime.now()
            execution.result = asdict(result)
            
            # Update conversation state with result
            if result.context_updates:
                conversation_state.context_variables.update(result.context_updates)
            
            conversation_state.context_variables['last_command_result'] = asdict(result)
            
            # Store updated conversation state
            self.conversation_states[session_id] = conversation_state
            
            return result
            
        except Exception as e:
            logger.error(f"Voice command processing failed: {str(e)}")
            return CommandResult(
                success=False,
                message="I encountered an error processing your command. Please try again.",
                error=str(e)
            )
    
    async def _execute_command_with_middleware(self, command: VoiceCommand, 
                                             context: ConversationState) -> CommandResult:
        """Execute command through middleware stack"""
        
        async def execute_handler(cmd: VoiceCommand, ctx: ConversationState) -> CommandResult:
            """Final handler execution"""
            handler = self.command_handlers.get(cmd.intent.name)
            
            if not handler:
                return CommandResult(
                    success=False,
                    message=f"I don't know how to handle '{cmd.intent.name}' commands yet.",
                    error=f"No handler registered for intent: {cmd.intent.name}"
                )
            
            return await handler(cmd, ctx)
        
        # Build middleware chain
        handler = execute_handler
        for middleware in reversed(self.middleware_stack):
            current_handler = handler
            handler = lambda cmd, ctx, h=current_handler, m=middleware: m(cmd, ctx, h)
        
        return await handler(command, context)
    
    def _get_or_create_conversation_state(self, session_id: str, 
                                         user_id: Optional[str] = None) -> ConversationState:
        """Get existing or create new conversation state"""
        if session_id not in self.conversation_states:
            self.conversation_states[session_id] = ConversationState(
                session_id=session_id,
                user_id=user_id,
                current_intent=None,
                pending_clarifications=[],
                context_variables={},
                conversation_flow=[],
                last_activity=datetime.now(),
                turn_count=0
            )
        
        return self.conversation_states[session_id]
    
    def _determine_command_priority(self, command: VoiceCommand, 
                                   context: ConversationState) -> CommandPriority:
        """Determine command execution priority based on intent and context"""
        
        # System commands get high priority
        if command.intent.name == 'system':
            return CommandPriority.HIGH
        
        # Commands with high confidence get normal priority
        if command.confidence > 0.8:
            return CommandPriority.NORMAL
        
        # Low confidence commands get low priority
        return CommandPriority.LOW
    
    async def _execution_worker(self):
        """Background worker to process command execution queue"""
        while True:
            try:
                # Get next execution from queue
                execution = await self.execution_queue.get()
                
                # Check if we have capacity for more executions
                active_count = sum(1 for e in self.active_executions.values() 
                                 if e.status == CommandStatus.EXECUTING)
                
                if active_count >= self.max_concurrent_executions:
                    # Put back in queue and wait
                    await self.execution_queue.put(execution)
                    await asyncio.sleep(0.1)
                    continue
                
                # Update execution status
                execution.status = CommandStatus.EXECUTING
                execution.started_at = datetime.now()
                
                # Process execution (this would be handled by the main process_voice_command method)
                # This worker is mainly for queue management
                
            except Exception as e:
                logger.error(f"Execution worker error: {str(e)}")
                await asyncio.sleep(1)
    
    async def _cleanup_worker(self):
        """Background worker to clean up old executions and conversation states"""
        while True:
            try:
                current_time = datetime.now()
                
                # Clean up old executions
                expired_executions = []
                for exec_id, execution in self.active_executions.items():
                    if execution.status in [CommandStatus.COMPLETED, CommandStatus.FAILED, CommandStatus.CANCELLED]:
                        if (current_time - execution.completed_at).total_seconds() > 3600:  # 1 hour
                            expired_executions.append(exec_id)
                
                for exec_id in expired_executions:
                    del self.active_executions[exec_id]
                
                # Clean up inactive conversation states
                expired_sessions = []
                for session_id, state in self.conversation_states.items():
                    if (current_time - state.last_activity).total_seconds() > self.conversation_timeout:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    await self._cleanup_conversation_state(session_id)
                
                # Sleep for 5 minutes before next cleanup
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Cleanup worker error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _cleanup_conversation_state(self, session_id: str):
        """Clean up conversation state for a session"""
        if session_id in self.conversation_states:
            logger.info(f"Cleaning up conversation state for session: {session_id}")
            del self.conversation_states[session_id]
    
    # Helper methods for command processing
    def _extract_search_query(self, command: VoiceCommand, context: ConversationState) -> Optional[str]:
        """Extract search query from command and context"""
        # Look for topic entities first
        topic_entities = [e for e in command.entities if e.type == 'topic']
        if topic_entities:
            return topic_entities[0].value
        
        # Extract from command text patterns
        import re
        patterns = [
            r'(?:search|find|look for)\s+(.+)',
            r'(?:what|tell me about)\s+(.+)',
            r'(?:show me)\s+(.+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command.text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Check conversation context for implicit queries
        if context.current_intent == 'search' and context.context_variables.get('awaiting_search_query'):
            return command.text.strip()
        
        return None
    
    def _extract_navigation_target(self, command: VoiceCommand, context: ConversationState) -> Optional[str]:
        """Extract navigation target from command"""
        # Look for page/section entities
        page_entities = [e for e in command.entities if e.type == 'page_section']
        if page_entities:
            return page_entities[0].value
        
        # Extract from command text patterns
        import re
        patterns = [
            r'(?:go to|open|navigate to)\s+(?:the\s+)?(.+?)(?:\s+(?:page|section|tab))?$',
            r'(?:show me|take me to)\s+(?:the\s+)?(.+?)(?:\s+(?:page|section|tab))?$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command.text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_document_action(self, command: VoiceCommand, context: ConversationState) -> Tuple[Optional[str], Dict[str, Any]]:
        """Extract document action and information from command"""
        # Look for action entities
        action_entities = [e for e in command.entities if e.type == 'action']
        document_entities = [e for e in command.entities if e.type == 'document_name']
        
        action = None
        document_info = {}
        
        if action_entities:
            action = action_entities[0].value
        else:
            # Extract from command text
            import re
            action_patterns = {
                'upload': r'\b(upload|add|import)\b',
                'open': r'\b(open|view|read)\b',
                'delete': r'\b(delete|remove)\b',
                'summarize': r'\b(summarize|summary)\b'
            }
            
            for act, pattern in action_patterns.items():
                if re.search(pattern, command.text, re.IGNORECASE):
                    action = act
                    break
        
        if document_entities:
            document_info['name'] = document_entities[0].value
        
        return action, document_info
    
    def _extract_chat_query(self, command: VoiceCommand, context: ConversationState) -> Optional[str]:
        """Extract chat query from command"""
        # Remove chat trigger words
        import re
        query = re.sub(r'^(ask|question|query|explain|describe|tell me)\s+', '', command.text, flags=re.IGNORECASE)
        return query.strip() if query != command.text else command.text
    
    def _extract_system_action(self, command: VoiceCommand) -> Optional[str]:
        """Extract system action from command"""
        text = command.text.lower()
        
        if any(word in text for word in ['help', 'assistance', 'what can you do']):
            return 'help'
        elif any(word in text for word in ['settings', 'preferences', 'configuration']):
            return 'settings'
        elif any(word in text for word in ['stop', 'pause', 'cancel', 'quit']):
            return 'stop'
        elif any(word in text for word in ['repeat', 'say again', 'what did you say']):
            return 'repeat'
        
        return None
    
    def _extract_voice_action(self, command: VoiceCommand) -> Optional[str]:
        """Extract voice control action from command"""
        text = command.text.lower()
        
        if any(word in text for word in ['speak', 'read', 'say']):
            return 'speak'
        elif 'louder' in text:
            return 'louder'
        elif 'quieter' in text:
            return 'quieter'
        elif 'faster' in text:
            return 'faster'
        elif 'slower' in text:
            return 'slower'
        elif 'mute' in text and 'unmute' not in text:
            return 'mute'
        elif 'unmute' in text:
            return 'unmute'
        
        return None
    
    def _extract_speech_content(self, command: VoiceCommand) -> str:
        """Extract content to be spoken from command"""
        import re
        match = re.search(r'(?:speak|read|say)\s+(.+)', command.text, re.IGNORECASE)
        return match.group(1) if match else command.text
    
    def _map_voice_adjustment(self, action: str) -> Dict[str, Any]:
        """Map voice action to adjustment parameters"""
        adjustments = {
            'louder': {'volume': 0.1},
            'quieter': {'volume': -0.1},
            'faster': {'rate': 0.2},
            'slower': {'rate': -0.2}
        }
        return adjustments.get(action, {})
    
    # Placeholder methods for actual implementation
    async def _perform_contextual_search(self, query: str, context: ConversationState) -> Dict[str, Any]:
        """Perform contextual search (placeholder)"""
        return {
            'query': query,
            'results': [
                {'title': f'Result for {query}', 'relevance': 0.9},
                {'title': f'Related to {query}', 'relevance': 0.8}
            ],
            'context_used': bool(context.context_variables)
        }
    
    async def _get_valid_navigation_targets(self, context: ConversationState) -> List[str]:
        """Get valid navigation targets (placeholder)"""
        return ['documents', 'chat', 'settings', 'analytics', 'search', 'help']
    
    def _get_navigation_suggestions(self, target: str, valid_targets: List[str]) -> List[str]:
        """Get navigation suggestions based on similarity (placeholder)"""
        # Simple similarity matching
        suggestions = []
        target_lower = target.lower()
        
        for valid_target in valid_targets:
            if target_lower in valid_target.lower() or valid_target.lower() in target_lower:
                suggestions.append(valid_target)
        
        return suggestions[:5]
    
    async def _execute_navigation(self, target: str, context: ConversationState) -> Dict[str, Any]:
        """Execute navigation (placeholder)"""
        return {'target': target, 'success': True}
    
    async def _handle_document_upload(self, document_info: Dict[str, Any], context: ConversationState) -> Dict[str, Any]:
        """Handle document upload (placeholder)"""
        return {
            'success': True,
            'message': 'Document upload initiated',
            'follow_up_actions': ['open_file_dialog']
        }
    
    async def _handle_document_open(self, document_info: Dict[str, Any], context: ConversationState) -> Dict[str, Any]:
        """Handle document open (placeholder)"""
        doc_name = document_info.get('name', 'document')
        return {
            'success': True,
            'message': f'Opening {doc_name}',
            'data': {'document_name': doc_name},
            'follow_up_actions': ['open_document']
        }
    
    async def _handle_document_delete(self, document_info: Dict[str, Any], context: ConversationState) -> Dict[str, Any]:
        """Handle document delete (placeholder)"""
        doc_name = document_info.get('name', 'document')
        return {
            'success': True,
            'message': f'Deleting {doc_name}',
            'data': {'document_name': doc_name},
            'follow_up_actions': ['confirm_delete', 'delete_document']
        }
    
    async def _handle_document_summarize(self, document_info: Dict[str, Any], context: ConversationState) -> Dict[str, Any]:
        """Handle document summarize (placeholder)"""
        doc_name = document_info.get('name', 'current document')
        return {
            'success': True,
            'message': f'Generating summary for {doc_name}',
            'data': {'document_name': doc_name},
            'follow_up_actions': ['generate_summary']
        }
    
    async def _process_chat_query(self, query: str, context: ConversationState) -> Dict[str, Any]:
        """Process chat query with context (placeholder)"""
        return {
            'response': f'I understand you\'re asking about: {query}',
            'topic': query,
            'confidence': 0.8,
            'context_used': bool(context.context_variables)
        }
    
    async def _generate_contextual_help(self, context: ConversationState) -> Dict[str, Any]:
        """Generate contextual help based on conversation state (placeholder)"""
        available_commands = list(self.command_handlers.keys())
        
        return {
            'available_commands': available_commands,
            'examples': {
                'search': 'Search for machine learning papers',
                'navigate': 'Go to documents page',
                'document': 'Open my research notes',
                'chat': 'Explain neural networks',
                'system': 'Help me with voice commands'
            },
            'context_aware': bool(context.context_variables)
        }
    
    # Public API methods
    def get_conversation_state(self, session_id: str) -> Optional[ConversationState]:
        """Get conversation state for a session"""
        return self.conversation_states.get(session_id)
    
    def get_active_executions(self) -> Dict[str, CommandExecution]:
        """Get all active command executions"""
        return self.active_executions.copy()
    
    def get_execution_status(self, execution_id: str) -> Optional[CommandExecution]:
        """Get status of a specific command execution"""
        return self.active_executions.get(execution_id)
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a command execution"""
        execution = self.active_executions.get(execution_id)
        if execution and execution.status in [CommandStatus.PENDING, CommandStatus.EXECUTING]:
            execution.status = CommandStatus.CANCELLED
            execution.completed_at = datetime.now()
            return True
        return False
    
    def get_conversation_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get analytics for a conversation session"""
        state = self.conversation_states.get(session_id)
        if not state:
            return {}
        
        return {
            'session_id': session_id,
            'turn_count': state.turn_count,
            'conversation_duration': (datetime.now() - (datetime.now() - timedelta(seconds=state.turn_count * 30))).total_seconds(),
            'intent_distribution': self._calculate_intent_distribution(state.conversation_flow),
            'context_variables_count': len(state.context_variables),
            'pending_clarifications': len(state.pending_clarifications),
            'last_activity': state.last_activity.isoformat(),
            'is_active': state.is_active
        }
    
    def _calculate_intent_distribution(self, conversation_flow: List[str]) -> Dict[str, int]:
        """Calculate distribution of intents in conversation"""
        distribution = {}
        for intent in conversation_flow:
            distribution[intent] = distribution.get(intent, 0) + 1
        return distribution
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for voice command router"""
        return {
            'status': 'healthy',
            'registered_handlers': len(self.command_handlers),
            'middleware_count': len(self.middleware_stack),
            'active_conversations': len(self.conversation_states),
            'active_executions': len(self.active_executions),
            'queue_size': self.execution_queue.qsize(),
            'supported_intents': list(self.command_handlers.keys())
        }