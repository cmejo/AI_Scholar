#!/usr/bin/env python3
"""
Test script for the enhanced voice command system
Tests NLP processing, intent recognition, entity extraction, and command routing
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from services.voice_command_router import VoiceCommandRouter
    from services.voice_nlp_service import VoiceNLPService
except ImportError:
    # Handle relative import issues for testing
    import sys
    import os
    
    # Add current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # Mock the config import
    class MockConfig:
        def __init__(self):
            pass
    
    # Create a mock config module
    import types
    config_module = types.ModuleType('config')
    config_module.Config = MockConfig
    sys.modules['core.config'] = config_module
    sys.modules['backend.core.config'] = config_module
    
    # Now try importing again
    from services.voice_command_router import VoiceCommandRouter
    from services.voice_nlp_service import VoiceNLPService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VoiceCommandSystemTester:
    """Test suite for the voice command system"""
    
    def __init__(self):
        self.nlp_service = VoiceNLPService()
        self.command_router = VoiceCommandRouter()
        self.test_session_id = "test_session_" + str(int(datetime.now().timestamp()))
    
    async def test_nlp_processing(self):
        """Test NLP processing capabilities"""
        print("\n" + "="*60)
        print("TESTING NLP PROCESSING")
        print("="*60)
        
        test_commands = [
            "search for machine learning papers",
            "go to the documents page",
            "upload a new research paper",
            "explain neural networks to me",
            "help me with voice commands",
            "speak louder please",
            "what is deep learning?",
            "open document called thesis draft",
            "delete file old notes",
            "summarize the current document"
        ]
        
        for command_text in test_commands:
            try:
                print(f"\nProcessing: '{command_text}'")
                command = await self.nlp_service.process_command(command_text, self.test_session_id)
                
                print(f"  Intent: {command.intent.name} (confidence: {command.intent.confidence:.2f})")
                print(f"  Entities: {len(command.entities)}")
                for entity in command.entities:
                    print(f"    - {entity.type}: '{entity.value}' (confidence: {entity.confidence:.2f})")
                print(f"  Overall confidence: {command.confidence:.2f}")
                
            except Exception as e:
                print(f"  ERROR: {str(e)}")
    
    async def test_command_routing(self):
        """Test command routing and execution"""
        print("\n" + "="*60)
        print("TESTING COMMAND ROUTING AND EXECUTION")
        print("="*60)
        
        test_commands = [
            "search for artificial intelligence research",
            "navigate to settings page",
            "upload a document",
            "ask about machine learning algorithms",
            "help me understand the interface",
            "read this text aloud",
            "what can you do for me?",
            "open my research notes",
            "find papers about neural networks"
        ]
        
        for command_text in test_commands:
            try:
                print(f"\nExecuting: '{command_text}'")
                result = await self.command_router.process_voice_command(
                    command_text, 
                    self.test_session_id
                )
                
                print(f"  Success: {result.success}")
                print(f"  Message: {result.message}")
                if result.data:
                    print(f"  Data keys: {list(result.data.keys()) if isinstance(result.data, dict) else 'Non-dict data'}")
                if result.follow_up_actions:
                    print(f"  Follow-up actions: {result.follow_up_actions}")
                if result.context_updates:
                    print(f"  Context updates: {list(result.context_updates.keys())}")
                if result.execution_time:
                    print(f"  Execution time: {result.execution_time:.3f}s")
                if result.error:
                    print(f"  Error: {result.error}")
                
            except Exception as e:
                print(f"  ERROR: {str(e)}")
    
    async def test_conversation_context(self):
        """Test conversation context management"""
        print("\n" + "="*60)
        print("TESTING CONVERSATION CONTEXT MANAGEMENT")
        print("="*60)
        
        # Simulate a multi-turn conversation
        conversation_turns = [
            "search for machine learning papers",
            "show me the first result",
            "open that document",
            "summarize it for me",
            "what are the key findings?",
            "compare it with deep learning approaches",
            "save this analysis"
        ]
        
        for i, turn in enumerate(conversation_turns, 1):
            try:
                print(f"\nTurn {i}: '{turn}'")
                result = await self.command_router.process_voice_command(
                    turn, 
                    self.test_session_id
                )
                
                print(f"  Result: {result.message}")
                
                # Get conversation state
                state = self.command_router.get_conversation_state(self.test_session_id)
                if state:
                    print(f"  Turn count: {state.turn_count}")
                    print(f"  Current intent: {state.current_intent}")
                    print(f"  Context variables: {len(state.context_variables)}")
                    print(f"  Conversation flow: {state.conversation_flow[-3:]}")  # Last 3 intents
                
            except Exception as e:
                print(f"  ERROR: {str(e)}")
    
    async def test_entity_extraction(self):
        """Test entity extraction capabilities"""
        print("\n" + "="*60)
        print("TESTING ENTITY EXTRACTION")
        print("="*60)
        
        test_cases = [
            {
                'text': 'open document "research paper on AI"',
                'expected_entities': ['document_name']
            },
            {
                'text': 'search for papers about neural networks',
                'expected_entities': ['topic']
            },
            {
                'text': 'go to the analytics page',
                'expected_entities': ['page_section']
            },
            {
                'text': 'upload 5 documents today',
                'expected_entities': ['number', 'date_time']
            },
            {
                'text': 'delete file called "old notes.pdf"',
                'expected_entities': ['action', 'document_name']
            }
        ]
        
        for test_case in test_cases:
            try:
                print(f"\nTesting: '{test_case['text']}'")
                command = await self.nlp_service.process_command(test_case['text'], self.test_session_id)
                
                extracted_types = [entity.type for entity in command.entities]
                print(f"  Expected entities: {test_case['expected_entities']}")
                print(f"  Extracted entities: {extracted_types}")
                
                for entity in command.entities:
                    print(f"    - {entity.type}: '{entity.value}' (confidence: {entity.confidence:.2f}, pos: {entity.start}-{entity.end})")
                
                # Check if expected entities were found
                found_expected = set(extracted_types) & set(test_case['expected_entities'])
                print(f"  Match rate: {len(found_expected)}/{len(test_case['expected_entities'])}")
                
            except Exception as e:
                print(f"  ERROR: {str(e)}")
    
    async def test_intent_classification(self):
        """Test intent classification accuracy"""
        print("\n" + "="*60)
        print("TESTING INTENT CLASSIFICATION")
        print("="*60)
        
        test_cases = [
            # Search intents
            {'text': 'find papers about AI', 'expected': 'search'},
            {'text': 'search for machine learning', 'expected': 'search'},
            {'text': 'what is neural network?', 'expected': 'search'},
            {'text': 'show me documents about deep learning', 'expected': 'search'},
            
            # Navigation intents
            {'text': 'go to settings', 'expected': 'navigate'},
            {'text': 'open documents page', 'expected': 'navigate'},
            {'text': 'take me to analytics', 'expected': 'navigate'},
            {'text': 'navigate to chat interface', 'expected': 'navigate'},
            
            # Document intents
            {'text': 'upload a file', 'expected': 'document'},
            {'text': 'delete document', 'expected': 'document'},
            {'text': 'open my research paper', 'expected': 'document'},
            {'text': 'summarize this document', 'expected': 'document'},
            
            # Chat intents
            {'text': 'explain this concept', 'expected': 'chat'},
            {'text': 'tell me about algorithms', 'expected': 'chat'},
            {'text': 'what does this mean?', 'expected': 'chat'},
            {'text': 'compare these approaches', 'expected': 'chat'},
            
            # System intents
            {'text': 'help me', 'expected': 'system'},
            {'text': 'what can you do?', 'expected': 'system'},
            {'text': 'stop listening', 'expected': 'system'},
            {'text': 'open settings', 'expected': 'system'},
            
            # Voice control intents
            {'text': 'speak louder', 'expected': 'voice_control'},
            {'text': 'read this text', 'expected': 'voice_control'},
            {'text': 'mute voice', 'expected': 'voice_control'},
            {'text': 'change voice settings', 'expected': 'voice_control'}
        ]
        
        correct_predictions = 0
        total_predictions = len(test_cases)
        
        for test_case in test_cases:
            try:
                command = await self.nlp_service.process_command(test_case['text'], self.test_session_id)
                predicted = command.intent.name
                expected = test_case['expected']
                
                is_correct = predicted == expected
                correct_predictions += is_correct
                
                status = "✓" if is_correct else "✗"
                print(f"{status} '{test_case['text']}'")
                print(f"    Expected: {expected}, Predicted: {predicted} (confidence: {command.intent.confidence:.2f})")
                
                if not is_correct:
                    print(f"    MISMATCH!")
                
            except Exception as e:
                print(f"✗ '{test_case['text']}' - ERROR: {str(e)}")
        
        accuracy = correct_predictions / total_predictions
        print(f"\nIntent Classification Accuracy: {accuracy:.2%} ({correct_predictions}/{total_predictions})")
    
    async def test_conversation_analytics(self):
        """Test conversation analytics"""
        print("\n" + "="*60)
        print("TESTING CONVERSATION ANALYTICS")
        print("="*60)
        
        # Generate some conversation activity
        test_commands = [
            "search for AI papers",
            "go to documents",
            "upload a file",
            "help me",
            "search for more papers",
            "explain neural networks"
        ]
        
        for command in test_commands:
            await self.command_router.process_voice_command(command, self.test_session_id)
        
        # Get analytics
        try:
            analytics = self.command_router.get_conversation_analytics(self.test_session_id)
            
            print(f"Session ID: {analytics['session_id']}")
            print(f"Turn count: {analytics['turn_count']}")
            print(f"Conversation duration: {analytics['conversation_duration']:.2f}s")
            print(f"Intent distribution: {analytics['intent_distribution']}")
            print(f"Context variables: {analytics['context_variables_count']}")
            print(f"Pending clarifications: {analytics['pending_clarifications']}")
            print(f"Last activity: {analytics['last_activity']}")
            print(f"Is active: {analytics['is_active']}")
            
        except Exception as e:
            print(f"ERROR getting analytics: {str(e)}")
    
    async def test_health_checks(self):
        """Test health check functionality"""
        print("\n" + "="*60)
        print("TESTING HEALTH CHECKS")
        print("="*60)
        
        # Test NLP service health
        try:
            nlp_health = self.nlp_service.health_check()
            print("NLP Service Health:")
            for key, value in nlp_health.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"NLP health check error: {str(e)}")
        
        print()
        
        # Test command router health
        try:
            router_health = self.command_router.health_check()
            print("Command Router Health:")
            for key, value in router_health.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"Router health check error: {str(e)}")
    
    async def run_all_tests(self):
        """Run all test suites"""
        print("VOICE COMMAND SYSTEM TEST SUITE")
        print("="*60)
        print(f"Test session ID: {self.test_session_id}")
        print(f"Start time: {datetime.now().isoformat()}")
        
        try:
            await self.test_nlp_processing()
            await self.test_intent_classification()
            await self.test_entity_extraction()
            await self.test_command_routing()
            await self.test_conversation_context()
            await self.test_conversation_analytics()
            await self.test_health_checks()
            
            print("\n" + "="*60)
            print("ALL TESTS COMPLETED")
            print("="*60)
            
        except Exception as e:
            print(f"\nTEST SUITE ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

async def main():
    """Main test function"""
    tester = VoiceCommandSystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())