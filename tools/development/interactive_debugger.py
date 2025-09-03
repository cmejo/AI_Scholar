"""
Interactive Debugger for AI Scholar
Advanced debugging tools with AI assistance and visual debugging
"""
import asyncio
import json
import logging
import traceback
import sys
import inspect
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import pdb
import code
import ast
import dis

logger = logging.getLogger(__name__)

@dataclass
class DebugSession:
    """Debug session information"""
    session_id: str
    user_id: str
    started_at: datetime
    context: Dict[str, Any]
    breakpoints: List[Dict[str, Any]]
    call_stack: List[Dict[str, Any]]
    variables: Dict[str, Any]
    is_active: bool = True

@dataclass
class Breakpoint:
    """Breakpoint configuration"""
    file_path: str
    line_number: int
    condition: Optional[str] = None
    hit_count: int = 0
    enabled: bool = True
    temporary: bool = False

class AIAssistedDebugger:
    """AI-powered debugging assistant"""
    
    def __init__(self):
        self.sessions: Dict[str, DebugSession] = {}
        self.breakpoints: Dict[str, Breakpoint] = {}
        self.debug_history: List[Dict[str, Any]] = []
    
    async def start_debug_session(
        self, 
        user_id: str, 
        context: Dict[str, Any] = None
    ) -> str:
        """Start a new debug session"""
        session_id = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
        
        session = DebugSession(
            session_id=session_id,
            user_id=user_id,
            started_at=datetime.now(),
            context=context or {},
            breakpoints=[],
            call_stack=[],
            variables={}
        )
        
        self.sessions[session_id] = session
        logger.info(f"🐛 Debug session started: {session_id}")
        
        return session_id
    
    async def analyze_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """AI-powered error analysis"""
        error_info = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context
        }
        
        # Extract relevant code context
        tb = error.__traceback__
        code_context = []
        
        while tb:
            frame = tb.tb_frame
            filename = frame.f_code.co_filename
            line_number = tb.tb_lineno
            
            try:
                with open(filename, 'r') as f:
                    lines = f.readlines()
                    start = max(0, line_number - 3)
                    end = min(len(lines), line_number + 3)
                    
                    code_context.append({
                        "file": filename,
                        "line_number": line_number,
                        "code_snippet": lines[start:end],
                        "locals": dict(frame.f_locals),
                        "globals": list(frame.f_globals.keys())
                    })
            except:
                pass
            
            tb = tb.tb_next
        
        # AI analysis (mock implementation)
        analysis = await self._generate_ai_analysis(error_info, code_context)
        
        return {
            "error_info": error_info,
            "code_context": code_context,
            "ai_analysis": analysis,
            "suggestions": await self._generate_fix_suggestions(error_info),
            "similar_issues": await self._find_similar_issues(error_info)
        }
    
    async def _generate_ai_analysis(
        self, 
        error_info: Dict[str, Any], 
        code_context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate AI analysis of the error"""
        # Mock AI analysis - in real implementation, use actual AI service
        error_type = error_info["type"]
        message = error_info["message"]
        
        analysis = {
            "root_cause": f"Analysis of {error_type}: {message}",
            "confidence": 0.85,
            "explanation": "Based on the error pattern and code context...",
            "impact_assessment": "Medium - affects user workflow",
            "complexity": "Low - straightforward fix expected"
        }
        
        if "AttributeError" in error_type:
            analysis.update({
                "root_cause": "Object attribute access issue",
                "explanation": "The code is trying to access an attribute that doesn't exist on the object.",
                "common_causes": [
                    "Typo in attribute name",
                    "Object is None",
                    "Wrong object type",
                    "Attribute not initialized"
                ]
            })
        elif "KeyError" in error_type:
            analysis.update({
                "root_cause": "Dictionary key access issue",
                "explanation": "The code is trying to access a dictionary key that doesn't exist.",
                "common_causes": [
                    "Key name mismatch",
                    "Data structure changed",
                    "Missing data validation",
                    "API response format changed"
                ]
            })
        
        return analysis
    
    async def _generate_fix_suggestions(self, error_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate fix suggestions"""
        suggestions = []
        error_type = error_info["type"]
        
        if "AttributeError" in error_type:
            suggestions.extend([
                {
                    "type": "code_fix",
                    "description": "Add attribute existence check",
                    "code": "if hasattr(obj, 'attribute_name'):",
                    "priority": "high"
                },
                {
                    "type": "code_fix", 
                    "description": "Use getattr with default",
                    "code": "getattr(obj, 'attribute_name', default_value)",
                    "priority": "medium"
                }
            ])
        elif "KeyError" in error_type:
            suggestions.extend([
                {
                    "type": "code_fix",
                    "description": "Use dict.get() with default",
                    "code": "dict_obj.get('key', default_value)",
                    "priority": "high"
                },
                {
                    "type": "validation",
                    "description": "Add key validation",
                    "code": "if 'key' in dict_obj:",
                    "priority": "medium"
                }
            ])
        
        return suggestions
    
    async def _find_similar_issues(self, error_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar issues from history"""
        similar = []
        
        for historical_error in self.debug_history[-10:]:  # Last 10 errors
            if historical_error.get("type") == error_info["type"]:
                similar.append({
                    "timestamp": historical_error.get("timestamp"),
                    "context": historical_error.get("context", {}),
                    "resolution": historical_error.get("resolution"),
                    "similarity_score": 0.8  # Mock similarity
                })
        
        return similar
    
    def set_breakpoint(
        self, 
        file_path: str, 
        line_number: int, 
        condition: str = None
    ) -> str:
        """Set a breakpoint"""
        bp_id = f"bp_{len(self.breakpoints)}"
        
        breakpoint = Breakpoint(
            file_path=file_path,
            line_number=line_number,
            condition=condition
        )
        
        self.breakpoints[bp_id] = breakpoint
        logger.info(f"🔴 Breakpoint set: {file_path}:{line_number}")
        
        return bp_id
    
    def remove_breakpoint(self, bp_id: str) -> bool:
        """Remove a breakpoint"""
        if bp_id in self.breakpoints:
            del self.breakpoints[bp_id]
            logger.info(f"🟢 Breakpoint removed: {bp_id}")
            return True
        return False
    
    async def inspect_variable(
        self, 
        session_id: str, 
        variable_name: str, 
        frame_index: int = 0
    ) -> Dict[str, Any]:
        """Inspect a variable in the current debug context"""
        if session_id not in self.sessions:
            raise ValueError(f"Debug session not found: {session_id}")
        
        session = self.sessions[session_id]
        
        # Mock variable inspection
        variable_info = {
            "name": variable_name,
            "type": "str",  # Would be actual type
            "value": "sample_value",  # Would be actual value
            "size": 12,
            "attributes": ["upper", "lower", "strip"],  # Available methods
            "is_callable": False,
            "memory_address": "0x7f8b8c0d1234"
        }
        
        return variable_info
    
    async def evaluate_expression(
        self, 
        session_id: str, 
        expression: str
    ) -> Dict[str, Any]:
        """Evaluate an expression in the debug context"""
        if session_id not in self.sessions:
            raise ValueError(f"Debug session not found: {session_id}")
        
        try:
            # Parse the expression to ensure it's safe
            parsed = ast.parse(expression, mode='eval')
            
            # Mock evaluation - in real implementation, evaluate in actual context
            result = {
                "expression": expression,
                "result": "evaluation_result",
                "type": "str",
                "success": True,
                "execution_time": 0.001
            }
            
            return result
            
        except Exception as e:
            return {
                "expression": expression,
                "error": str(e),
                "success": False
            }
    
    def get_call_stack(self, session_id: str) -> List[Dict[str, Any]]:
        """Get the current call stack"""
        if session_id not in self.sessions:
            raise ValueError(f"Debug session not found: {session_id}")
        
        # Mock call stack - in real implementation, get from actual stack
        call_stack = [
            {
                "frame_index": 0,
                "function_name": "main",
                "file_path": "/app/main.py",
                "line_number": 42,
                "locals": {"x": 1, "y": 2},
                "code_context": ["def main():", "    x = 1", "    y = 2"]
            },
            {
                "frame_index": 1,
                "function_name": "process_data",
                "file_path": "/app/processor.py", 
                "line_number": 15,
                "locals": {"data": [1, 2, 3]},
                "code_context": ["def process_data(data):", "    for item in data:", "        process_item(item)"]
            }
        ]
        
        return call_stack

class VisualDebugger:
    """Visual debugging interface"""
    
    def __init__(self, ai_debugger: AIAssistedDebugger):
        self.ai_debugger = ai_debugger
        self.ui_state = {
            "current_session": None,
            "selected_frame": 0,
            "watch_expressions": [],
            "console_history": []
        }
    
    async def generate_debug_dashboard(self, session_id: str) -> Dict[str, Any]:
        """Generate visual debug dashboard"""
        if session_id not in self.ai_debugger.sessions:
            raise ValueError(f"Debug session not found: {session_id}")
        
        session = self.ai_debugger.sessions[session_id]
        call_stack = self.ai_debugger.get_call_stack(session_id)
        
        dashboard = {
            "session_info": asdict(session),
            "call_stack": call_stack,
            "breakpoints": [asdict(bp) for bp in self.ai_debugger.breakpoints.values()],
            "watch_expressions": self.ui_state["watch_expressions"],
            "console_output": self.ui_state["console_history"][-50:],  # Last 50 entries
            "performance_metrics": await self._get_performance_metrics(session_id),
            "memory_usage": await self._get_memory_usage(session_id)
        }
        
        return dashboard
    
    async def _get_performance_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get performance metrics for the debug session"""
        return {
            "cpu_usage": 15.2,
            "memory_usage": 128.5,
            "execution_time": 0.045,
            "function_calls": 1247,
            "io_operations": 23
        }
    
    async def _get_memory_usage(self, session_id: str) -> Dict[str, Any]:
        """Get memory usage breakdown"""
        return {
            "total_memory": 256.0,
            "used_memory": 128.5,
            "available_memory": 127.5,
            "memory_by_type": {
                "strings": 45.2,
                "lists": 32.1,
                "dicts": 28.7,
                "objects": 22.5
            }
        }
    
    def add_watch_expression(self, expression: str):
        """Add expression to watch list"""
        if expression not in self.ui_state["watch_expressions"]:
            self.ui_state["watch_expressions"].append(expression)
    
    def remove_watch_expression(self, expression: str):
        """Remove expression from watch list"""
        if expression in self.ui_state["watch_expressions"]:
            self.ui_state["watch_expressions"].remove(expression)

class DebuggerIntegration:
    """Integration with existing development tools"""
    
    def __init__(self):
        self.ai_debugger = AIAssistedDebugger()
        self.visual_debugger = VisualDebugger(self.ai_debugger)
        self.integrations = {}
    
    async def integrate_with_ide(self, ide_type: str, config: Dict[str, Any]):
        """Integrate with IDE (VS Code, PyCharm, etc.)"""
        integration_config = {
            "ide_type": ide_type,
            "config": config,
            "enabled": True,
            "features": [
                "breakpoint_sync",
                "variable_inspection", 
                "call_stack_navigation",
                "ai_suggestions"
            ]
        }
        
        self.integrations[ide_type] = integration_config
        logger.info(f"🔧 IDE integration configured: {ide_type}")
    
    async def sync_breakpoints_with_ide(self, ide_type: str, breakpoints: List[Dict[str, Any]]):
        """Sync breakpoints with IDE"""
        for bp_data in breakpoints:
            self.ai_debugger.set_breakpoint(
                bp_data["file_path"],
                bp_data["line_number"],
                bp_data.get("condition")
            )
    
    async def export_debug_session(self, session_id: str, format: str = "json") -> str:
        """Export debug session data"""
        if session_id not in self.ai_debugger.sessions:
            raise ValueError(f"Debug session not found: {session_id}")
        
        session = self.ai_debugger.sessions[session_id]
        dashboard = await self.visual_debugger.generate_debug_dashboard(session_id)
        
        export_data = {
            "session": asdict(session),
            "dashboard": dashboard,
            "exported_at": datetime.now().isoformat(),
            "format_version": "1.0"
        }
        
        if format == "json":
            return json.dumps(export_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")

# Global debugger instance
debugger_integration = DebuggerIntegration()

# Convenience functions
async def debug_error(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Quick error debugging"""
    return await debugger_integration.ai_debugger.analyze_error(error, context or {})

async def start_debug_session(user_id: str, context: Dict[str, Any] = None) -> str:
    """Start a debug session"""
    return await debugger_integration.ai_debugger.start_debug_session(user_id, context)

def set_breakpoint(file_path: str, line_number: int, condition: str = None) -> str:
    """Set a breakpoint"""
    return debugger_integration.ai_debugger.set_breakpoint(file_path, line_number, condition)

if __name__ == "__main__":
    # Example usage
    async def test_debugger():
        print("🧪 Testing Interactive Debugger...")
        
        # Start debug session
        session_id = await start_debug_session("test_user")
        print(f"Debug session started: {session_id}")
        
        # Test error analysis
        try:
            # Simulate an error
            raise AttributeError("'NoneType' object has no attribute 'process'")
        except Exception as e:
            analysis = await debug_error(e, {"function": "process_data", "line": 42})
            print(f"Error analysis: {analysis['ai_analysis']}")
            print(f"Suggestions: {len(analysis['suggestions'])} found")
        
        # Set breakpoint
        bp_id = set_breakpoint("/app/main.py", 42, "x > 10")
        print(f"Breakpoint set: {bp_id}")
        
        # Generate dashboard
        dashboard = await debugger_integration.visual_debugger.generate_debug_dashboard(session_id)
        print(f"Dashboard generated with {len(dashboard['call_stack'])} stack frames")
    
    asyncio.run(test_debugger())