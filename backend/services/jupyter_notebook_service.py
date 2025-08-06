"""
Jupyter Notebook Service for AI Scholar Advanced RAG System

This service provides Jupyter notebook execution, rendering, and management capabilities
with support for interactive widgets, collaborative editing, and secure execution.
Enhanced with kernel management, real-time collaboration, and interactive widgets.
"""

import asyncio
import json
import uuid
import tempfile
import shutil
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict
import weakref
# import nbformat
# from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell
import logging

logger = logging.getLogger(__name__)

@dataclass
class NotebookCell:
    """Represents a notebook cell with execution state"""
    cell_id: str
    cell_type: str  # 'code', 'markdown', 'raw'
    source: str
    outputs: List[Dict[str, Any]]
    execution_count: Optional[int]
    metadata: Dict[str, Any]
    execution_state: str = 'idle'  # 'idle', 'running', 'completed', 'error'
    execution_time: Optional[float] = None

@dataclass
class NotebookData:
    """Complete notebook data structure"""
    notebook_id: str
    title: str
    cells: List[NotebookCell]
    metadata: Dict[str, Any]
    kernel_spec: Dict[str, str]
    created_at: datetime
    modified_at: datetime
    owner_id: str
    collaborators: List[str]
    version: int = 1

@dataclass
class ExecutionResult:
    """Result of cell execution"""
    success: bool
    outputs: List[Dict[str, Any]]
    execution_count: int
    execution_time: float
    error_message: Optional[str] = None
    warnings: List[str] = None

@dataclass
class KernelInfo:
    """Information about a notebook kernel"""
    kernel_id: str
    kernel_name: str
    language: str
    status: str  # 'starting', 'idle', 'busy', 'dead'
    last_activity: datetime
    notebook_id: str
    process_id: Optional[int] = None
    memory_usage: float = 0.0
    cpu_usage: float = 0.0

@dataclass
class InteractiveWidget:
    """Interactive widget data structure"""
    widget_id: str
    widget_type: str  # 'slider', 'button', 'text', 'dropdown', etc.
    properties: Dict[str, Any]
    value: Any
    cell_id: str
    notebook_id: str
    created_at: datetime
    last_updated: datetime

@dataclass
class CollaborativeEdit:
    """Collaborative editing operation"""
    edit_id: str
    user_id: str
    notebook_id: str
    cell_id: str
    operation_type: str  # 'insert', 'delete', 'replace'
    position: int
    content: str
    timestamp: datetime
    applied: bool = False

@dataclass
class RealtimeSession:
    """Real-time collaboration session"""
    session_id: str
    notebook_id: str
    user_id: str
    connected_at: datetime
    last_activity: datetime
    cursor_position: Optional[Dict[str, Any]] = None
    active_cell: Optional[str] = None

class JupyterNotebookService:
    """Service for managing Jupyter notebooks with execution capabilities"""
    
    def __init__(self):
        self.notebooks: Dict[str, NotebookData] = {}
        self.kernels: Dict[str, KernelInfo] = {}
        self.execution_queue: Dict[str, List[str]] = {}  # notebook_id -> cell_ids
        self.temp_dir = tempfile.mkdtemp(prefix="jupyter_notebooks_")
        
        # Enhanced features
        self.widgets: Dict[str, InteractiveWidget] = {}  # widget_id -> widget
        self.realtime_sessions: Dict[str, RealtimeSession] = {}  # session_id -> session
        self.collaborative_edits: Dict[str, List[CollaborativeEdit]] = defaultdict(list)  # notebook_id -> edits
        self.kernel_managers: Dict[str, Any] = {}  # kernel_id -> kernel_manager
        self.widget_callbacks: Dict[str, List[Callable]] = defaultdict(list)  # widget_id -> callbacks
        
        # Kernel cleanup thread
        self._cleanup_thread = None
        self._shutdown_event = threading.Event()
        self._start_cleanup_thread()
        
        self.supported_kernels = {
            'python3': {
                'name': 'python3',
                'display_name': 'Python 3',
                'language': 'python',
                'executable': 'python3'
            },
            'javascript': {
                'name': 'javascript',
                'display_name': 'JavaScript (Node.js)',
                'language': 'javascript',
                'executable': 'node'
            },
            'r': {
                'name': 'r',
                'display_name': 'R',
                'language': 'r',
                'executable': 'R'
            }
        }
    
    def _start_cleanup_thread(self):
        """Start the kernel cleanup thread"""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._cleanup_thread = threading.Thread(target=self._kernel_cleanup_worker, daemon=True)
            self._cleanup_thread.start()
    
    def _kernel_cleanup_worker(self):
        """Background worker to clean up idle kernels"""
        while not self._shutdown_event.is_set():
            try:
                current_time = datetime.now()
                idle_timeout = timedelta(minutes=30)  # 30 minutes idle timeout
                
                kernels_to_cleanup = []
                for kernel_id, kernel_info in self.kernels.items():
                    if (current_time - kernel_info.last_activity) > idle_timeout:
                        kernels_to_cleanup.append(kernel_id)
                
                for kernel_id in kernels_to_cleanup:
                    asyncio.create_task(self._shutdown_kernel(kernel_id))
                
                # Sleep for 5 minutes before next cleanup
                self._shutdown_event.wait(300)
                
            except Exception as e:
                logger.error(f"Error in kernel cleanup worker: {str(e)}")
                self._shutdown_event.wait(60)  # Wait 1 minute on error
    
    async def _create_kernel(self, notebook_id: str, kernel_name: str) -> Optional[str]:
        """Create and start a new kernel for the notebook"""
        try:
            kernel_id = str(uuid.uuid4())
            
            # Create kernel info
            kernel_info = KernelInfo(
                kernel_id=kernel_id,
                kernel_name=kernel_name,
                language=self.supported_kernels[kernel_name]['language'],
                status='starting',
                last_activity=datetime.now(),
                notebook_id=notebook_id
            )
            
            self.kernels[kernel_id] = kernel_info
            
            # In a real implementation, this would start an actual kernel process
            # For now, we'll simulate kernel startup
            await asyncio.sleep(0.1)  # Simulate startup time
            
            kernel_info.status = 'idle'
            kernel_info.process_id = os.getpid()  # Simulate process ID
            
            logger.info(f"Created kernel {kernel_id} for notebook {notebook_id}")
            return kernel_id
            
        except Exception as e:
            logger.error(f"Error creating kernel: {str(e)}")
            return None
    
    async def _shutdown_kernel(self, kernel_id: str) -> bool:
        """Shutdown a kernel"""
        try:
            if kernel_id in self.kernels:
                kernel_info = self.kernels[kernel_id]
                kernel_info.status = 'dead'
                
                # Clean up kernel manager if exists
                if kernel_id in self.kernel_managers:
                    del self.kernel_managers[kernel_id]
                
                del self.kernels[kernel_id]
                logger.info(f"Shutdown kernel {kernel_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error shutting down kernel {kernel_id}: {str(e)}")
            return False
    
    async def get_kernel_for_notebook(self, notebook_id: str) -> Optional[KernelInfo]:
        """Get or create a kernel for the notebook"""
        try:
            # Find existing kernel for this notebook
            for kernel_info in self.kernels.values():
                if kernel_info.notebook_id == notebook_id and kernel_info.status != 'dead':
                    kernel_info.last_activity = datetime.now()
                    return kernel_info
            
            # No active kernel found, create a new one
            notebook = self.notebooks.get(notebook_id)
            if not notebook:
                return None
            
            kernel_name = notebook.kernel_spec.get('name', 'python3')
            kernel_id = await self._create_kernel(notebook_id, kernel_name)
            
            if kernel_id:
                return self.kernels[kernel_id]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting kernel for notebook {notebook_id}: {str(e)}")
            return None
        
    async def create_notebook(
        self,
        title: str,
        owner_id: str,
        kernel_name: str = 'python3',
        initial_cells: Optional[List[Dict[str, Any]]] = None
    ) -> NotebookData:
        """Create a new notebook"""
        try:
            notebook_id = str(uuid.uuid4())
            
            # Create initial cells if not provided
            if not initial_cells:
                initial_cells = [
                    {
                        'cell_type': 'markdown',
                        'source': f'# {title}\n\nWelcome to your new notebook!'
                    },
                    {
                        'cell_type': 'code',
                        'source': '# Your first code cell\nprint("Hello, World!")'
                    }
                ]
            
            # Convert initial cells to NotebookCell objects
            cells = []
            for i, cell_data in enumerate(initial_cells):
                cell = NotebookCell(
                    cell_id=str(uuid.uuid4()),
                    cell_type=cell_data.get('cell_type', 'code'),
                    source=cell_data.get('source', ''),
                    outputs=[],
                    execution_count=None,
                    metadata=cell_data.get('metadata', {})
                )
                cells.append(cell)
            
            # Create notebook data
            notebook = NotebookData(
                notebook_id=notebook_id,
                title=title,
                cells=cells,
                metadata={
                    'kernelspec': self.supported_kernels.get(kernel_name, self.supported_kernels['python3']),
                    'language_info': {
                        'name': self.supported_kernels.get(kernel_name, self.supported_kernels['python3'])['language']
                    }
                },
                kernel_spec=self.supported_kernels.get(kernel_name, self.supported_kernels['python3']),
                created_at=datetime.now(),
                modified_at=datetime.now(),
                owner_id=owner_id,
                collaborators=[]
            )
            
            self.notebooks[notebook_id] = notebook
            
            # Initialize execution queue
            self.execution_queue[notebook_id] = []
            
            # Create initial kernel
            await self._create_kernel(notebook_id, kernel_name)
            
            logger.info(f"Created notebook {notebook_id} for user {owner_id}")
            return notebook
            
        except Exception as e:
            logger.error(f"Error creating notebook: {str(e)}")
            raise Exception(f"Failed to create notebook: {str(e)}")
    
    async def get_notebook(self, notebook_id: str, user_id: str) -> Optional[NotebookData]:
        """Get notebook by ID with access control"""
        try:
            notebook = self.notebooks.get(notebook_id)
            if not notebook:
                return None
            
            # Check access permissions
            if notebook.owner_id != user_id and user_id not in notebook.collaborators:
                logger.warning(f"User {user_id} attempted to access notebook {notebook_id} without permission")
                return None
            
            return notebook
            
        except Exception as e:
            logger.error(f"Error getting notebook {notebook_id}: {str(e)}")
            return None
    
    async def update_cell(
        self,
        notebook_id: str,
        cell_id: str,
        source: str,
        user_id: str
    ) -> bool:
        """Update cell content"""
        try:
            notebook = await self.get_notebook(notebook_id, user_id)
            if not notebook:
                return False
            
            # Find and update the cell
            for cell in notebook.cells:
                if cell.cell_id == cell_id:
                    cell.source = source
                    notebook.modified_at = datetime.now()
                    logger.info(f"Updated cell {cell_id} in notebook {notebook_id}")
                    return True
            
            logger.warning(f"Cell {cell_id} not found in notebook {notebook_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error updating cell {cell_id}: {str(e)}")
            return False
    
    async def add_cell(
        self,
        notebook_id: str,
        cell_type: str,
        source: str,
        position: Optional[int] = None,
        user_id: str = None
    ) -> Optional[str]:
        """Add a new cell to the notebook"""
        try:
            notebook = await self.get_notebook(notebook_id, user_id)
            if not notebook:
                return None
            
            cell = NotebookCell(
                cell_id=str(uuid.uuid4()),
                cell_type=cell_type,
                source=source,
                outputs=[],
                execution_count=None,
                metadata={}
            )
            
            if position is None:
                notebook.cells.append(cell)
            else:
                notebook.cells.insert(position, cell)
            
            notebook.modified_at = datetime.now()
            logger.info(f"Added cell {cell.cell_id} to notebook {notebook_id}")
            return cell.cell_id
            
        except Exception as e:
            logger.error(f"Error adding cell to notebook {notebook_id}: {str(e)}")
            return None
    
    async def delete_cell(self, notebook_id: str, cell_id: str, user_id: str) -> bool:
        """Delete a cell from the notebook"""
        try:
            notebook = await self.get_notebook(notebook_id, user_id)
            if not notebook:
                return False
            
            # Find and remove the cell
            for i, cell in enumerate(notebook.cells):
                if cell.cell_id == cell_id:
                    notebook.cells.pop(i)
                    notebook.modified_at = datetime.now()
                    logger.info(f"Deleted cell {cell_id} from notebook {notebook_id}")
                    return True
            
            logger.warning(f"Cell {cell_id} not found in notebook {notebook_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error deleting cell {cell_id}: {str(e)}")
            return False
    
    async def create_widget(
        self,
        notebook_id: str,
        cell_id: str,
        widget_type: str,
        properties: Dict[str, Any],
        initial_value: Any = None,
        user_id: str = None
    ) -> Optional[str]:
        """Create an interactive widget"""
        try:
            # If no user_id provided, skip access check (for internal widget creation)
            if user_id is not None:
                notebook = await self.get_notebook(notebook_id, user_id)
                if not notebook:
                    return None
            else:
                # Internal widget creation - just check if notebook exists
                notebook = self.notebooks.get(notebook_id)
                if not notebook:
                    return None
            
            widget_id = str(uuid.uuid4())
            widget = InteractiveWidget(
                widget_id=widget_id,
                widget_type=widget_type,
                properties=properties,
                value=initial_value,
                cell_id=cell_id,
                notebook_id=notebook_id,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            self.widgets[widget_id] = widget
            logger.info(f"Created widget {widget_id} of type {widget_type}")
            return widget_id
            
        except Exception as e:
            logger.error(f"Error creating widget: {str(e)}")
            return None
    
    async def update_widget_value(
        self,
        widget_id: str,
        new_value: Any,
        user_id: str = None
    ) -> bool:
        """Update widget value and trigger callbacks"""
        try:
            widget = self.widgets.get(widget_id)
            if not widget:
                return False
            
            # Check access permissions
            notebook = await self.get_notebook(widget.notebook_id, user_id)
            if not notebook:
                return False
            
            old_value = widget.value
            widget.value = new_value
            widget.last_updated = datetime.now()
            
            # Trigger callbacks
            await self._trigger_widget_callbacks(widget_id, old_value, new_value)
            
            logger.info(f"Updated widget {widget_id} value from {old_value} to {new_value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating widget {widget_id}: {str(e)}")
            return False
    
    async def register_widget_callback(
        self,
        widget_id: str,
        callback: Callable[[str, Any, Any], None]
    ) -> bool:
        """Register a callback for widget value changes"""
        try:
            if widget_id not in self.widgets:
                return False
            
            self.widget_callbacks[widget_id].append(callback)
            logger.info(f"Registered callback for widget {widget_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering widget callback: {str(e)}")
            return False
    
    async def _trigger_widget_callbacks(
        self,
        widget_id: str,
        old_value: Any,
        new_value: Any
    ):
        """Trigger all callbacks for a widget"""
        try:
            callbacks = self.widget_callbacks.get(widget_id, [])
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(widget_id, old_value, new_value)
                    else:
                        callback(widget_id, old_value, new_value)
                except Exception as e:
                    logger.error(f"Error in widget callback: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error triggering widget callbacks: {str(e)}")
    
    async def get_notebook_widgets(self, notebook_id: str, user_id: str) -> List[InteractiveWidget]:
        """Get all widgets for a notebook"""
        try:
            notebook = await self.get_notebook(notebook_id, user_id)
            if not notebook:
                return []
            
            notebook_widgets = [
                widget for widget in self.widgets.values()
                if widget.notebook_id == notebook_id
            ]
            
            return notebook_widgets
            
        except Exception as e:
            logger.error(f"Error getting notebook widgets: {str(e)}")
            return []
    
    async def start_realtime_session(
        self,
        notebook_id: str,
        user_id: str
    ) -> Optional[str]:
        """Start a real-time collaboration session"""
        try:
            notebook = await self.get_notebook(notebook_id, user_id)
            if not notebook:
                return None
            
            session_id = str(uuid.uuid4())
            session = RealtimeSession(
                session_id=session_id,
                notebook_id=notebook_id,
                user_id=user_id,
                connected_at=datetime.now(),
                last_activity=datetime.now()
            )
            
            self.realtime_sessions[session_id] = session
            logger.info(f"Started real-time session {session_id} for user {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting real-time session: {str(e)}")
            return None
    
    async def end_realtime_session(self, session_id: str) -> bool:
        """End a real-time collaboration session"""
        try:
            if session_id in self.realtime_sessions:
                session = self.realtime_sessions[session_id]
                del self.realtime_sessions[session_id]
                logger.info(f"Ended real-time session {session_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error ending real-time session: {str(e)}")
            return False
    
    async def apply_collaborative_edit(
        self,
        notebook_id: str,
        cell_id: str,
        operation_type: str,
        position: int,
        content: str,
        user_id: str
    ) -> Optional[str]:
        """Apply a collaborative edit operation"""
        try:
            notebook = await self.get_notebook(notebook_id, user_id)
            if not notebook:
                return None
            
            edit_id = str(uuid.uuid4())
            edit = CollaborativeEdit(
                edit_id=edit_id,
                user_id=user_id,
                notebook_id=notebook_id,
                cell_id=cell_id,
                operation_type=operation_type,
                position=position,
                content=content,
                timestamp=datetime.now()
            )
            
            # Apply the edit to the cell
            success = await self._apply_edit_to_cell(edit)
            if success:
                edit.applied = True
                self.collaborative_edits[notebook_id].append(edit)
                
                # Notify other real-time sessions
                await self._broadcast_edit_to_sessions(edit)
                
                logger.info(f"Applied collaborative edit {edit_id}")
                return edit_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error applying collaborative edit: {str(e)}")
            return None
    
    async def _apply_edit_to_cell(self, edit: CollaborativeEdit) -> bool:
        """Apply an edit operation to a cell"""
        try:
            notebook = self.notebooks.get(edit.notebook_id)
            if not notebook:
                return False
            
            # Find the cell
            cell = None
            for c in notebook.cells:
                if c.cell_id == edit.cell_id:
                    cell = c
                    break
            
            if not cell:
                return False
            
            # Apply the operation
            if edit.operation_type == 'insert':
                # Insert content at position
                source = cell.source
                new_source = source[:edit.position] + edit.content + source[edit.position:]
                cell.source = new_source
                
            elif edit.operation_type == 'delete':
                # Delete content from position
                source = cell.source
                end_pos = edit.position + len(edit.content)
                new_source = source[:edit.position] + source[end_pos:]
                cell.source = new_source
                
            elif edit.operation_type == 'replace':
                # Replace entire content
                cell.source = edit.content
            
            notebook.modified_at = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"Error applying edit to cell: {str(e)}")
            return False
    
    async def _broadcast_edit_to_sessions(self, edit: CollaborativeEdit):
        """Broadcast edit to all active real-time sessions"""
        try:
            # Find all sessions for this notebook (except the editor)
            target_sessions = [
                session for session in self.realtime_sessions.values()
                if session.notebook_id == edit.notebook_id and session.user_id != edit.user_id
            ]
            
            # In a real implementation, this would send WebSocket messages
            # For now, we'll just log the broadcast
            for session in target_sessions:
                logger.info(f"Broadcasting edit {edit.edit_id} to session {session.session_id}")
                session.last_activity = datetime.now()
                
        except Exception as e:
            logger.error(f"Error broadcasting edit: {str(e)}")
    
    async def get_active_collaborators(self, notebook_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get list of active collaborators for a notebook"""
        try:
            notebook = await self.get_notebook(notebook_id, user_id)
            if not notebook:
                return []
            
            active_sessions = [
                session for session in self.realtime_sessions.values()
                if session.notebook_id == notebook_id
            ]
            
            collaborators = []
            for session in active_sessions:
                collaborators.append({
                    'user_id': session.user_id,
                    'session_id': session.session_id,
                    'connected_at': session.connected_at.isoformat(),
                    'last_activity': session.last_activity.isoformat(),
                    'active_cell': session.active_cell,
                    'cursor_position': session.cursor_position
                })
            
            return collaborators
            
        except Exception as e:
            logger.error(f"Error getting active collaborators: {str(e)}")
            return []
    
    async def update_user_cursor(
        self,
        session_id: str,
        cell_id: str,
        cursor_position: Dict[str, Any]
    ) -> bool:
        """Update user's cursor position for real-time collaboration"""
        try:
            session = self.realtime_sessions.get(session_id)
            if not session:
                return False
            
            session.active_cell = cell_id
            session.cursor_position = cursor_position
            session.last_activity = datetime.now()
            
            logger.debug(f"Updated cursor for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user cursor: {str(e)}")
            return False
    
    async def execute_cell(
        self,
        notebook_id: str,
        cell_id: str,
        user_id: str
    ) -> Optional[ExecutionResult]:
        """Execute a single cell with enhanced kernel management"""
        try:
            notebook = await self.get_notebook(notebook_id, user_id)
            if not notebook:
                return None
            
            # Find the cell
            cell = None
            for c in notebook.cells:
                if c.cell_id == cell_id:
                    cell = c
                    break
            
            if not cell:
                logger.warning(f"Cell {cell_id} not found in notebook {notebook_id}")
                return None
            
            if cell.cell_type != 'code':
                logger.warning(f"Cannot execute non-code cell {cell_id}")
                return ExecutionResult(
                    success=False,
                    outputs=[],
                    execution_count=0,
                    execution_time=0.0,
                    error_message="Cannot execute non-code cell"
                )
            
            # Get or create kernel for this notebook
            kernel_info = await self.get_kernel_for_notebook(notebook_id)
            if not kernel_info:
                logger.error(f"Failed to get kernel for notebook {notebook_id}")
                return ExecutionResult(
                    success=False,
                    outputs=[],
                    execution_count=0,
                    execution_time=0.0,
                    error_message="Failed to start kernel"
                )
            
            # Update kernel and cell state
            kernel_info.status = 'busy'
            kernel_info.last_activity = datetime.now()
            cell.execution_state = 'running'
            start_time = datetime.now()
            
            try:
                # Execute the code with kernel context
                result = await self._execute_code_with_kernel(
                    cell.source, 
                    kernel_info,
                    notebook_id,
                    cell_id
                )
                
                # Update cell with results
                execution_time = (datetime.now() - start_time).total_seconds()
                cell.execution_time = execution_time
                cell.outputs = result.outputs
                cell.execution_count = result.execution_count
                cell.execution_state = 'completed' if result.success else 'error'
                
                notebook.modified_at = datetime.now()
                
                logger.info(f"Executed cell {cell_id} in {execution_time:.2f}s")
                return result
                
            finally:
                # Reset kernel state
                kernel_info.status = 'idle'
                kernel_info.last_activity = datetime.now()
            
        except Exception as e:
            logger.error(f"Error executing cell {cell_id}: {str(e)}")
            return ExecutionResult(
                success=False,
                outputs=[],
                execution_count=0,
                execution_time=0.0,
                error_message=str(e)
            )
    
    async def _execute_code_with_kernel(
        self, 
        source: str, 
        kernel_info: KernelInfo,
        notebook_id: str,
        cell_id: str
    ) -> ExecutionResult:
        """Execute code with kernel context and widget support"""
        try:
            execution_count = len([c for nb in self.notebooks.values() for c in nb.cells if c.execution_count]) + 1
            
            # Update kernel resource usage
            kernel_info.memory_usage = self._get_kernel_memory_usage(kernel_info.kernel_id)
            kernel_info.cpu_usage = self._get_kernel_cpu_usage(kernel_info.kernel_id)
            
            # Check for widget creation in code
            widgets_created = await self._detect_and_create_widgets(source, notebook_id, cell_id)
            
            # Execute the code using the existing method but with kernel context
            result = await self._execute_code(source, kernel_info.language)
            
            # Update execution count for successful execution
            if result.success:
                result.execution_count = execution_count
            
            # Add widget information to outputs if widgets were created
            if widgets_created:
                widget_output = {
                    'output_type': 'display_data',
                    'data': {
                        'application/vnd.jupyter.widget-view+json': {
                            'model_id': widgets_created[0] if widgets_created else None,
                            'version_major': 2,
                            'version_minor': 0
                        }
                    },
                    'metadata': {}
                }
                result.outputs.append(widget_output)
            
            # Store execution context for kernel state management
            await self._update_kernel_context(kernel_info.kernel_id, source, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing code with kernel: {str(e)}")
            return ExecutionResult(
                success=False,
                outputs=[],
                execution_count=execution_count,
                execution_time=0.0,
                error_message=str(e)
            )
    
    def _get_kernel_memory_usage(self, kernel_id: str) -> float:
        """Get memory usage for kernel (simulated)"""
        try:
            # In a real implementation, this would query actual kernel process
            import random
            return random.uniform(10.0, 100.0)  # MB
        except:
            return 0.0
    
    def _get_kernel_cpu_usage(self, kernel_id: str) -> float:
        """Get CPU usage for kernel (simulated)"""
        try:
            # In a real implementation, this would query actual kernel process
            import random
            return random.uniform(0.0, 25.0)  # Percentage
        except:
            return 0.0
    
    async def _update_kernel_context(self, kernel_id: str, source: str, result: ExecutionResult):
        """Update kernel execution context"""
        try:
            # Store execution history for kernel state management
            if kernel_id not in self.kernel_managers:
                self.kernel_managers[kernel_id] = {
                    'execution_history': [],
                    'variables': {},
                    'imports': set()
                }
            
            context = self.kernel_managers[kernel_id]
            context['execution_history'].append({
                'source': source,
                'success': result.success,
                'execution_count': result.execution_count,
                'timestamp': datetime.now()
            })
            
            # Keep only last 100 executions
            if len(context['execution_history']) > 100:
                context['execution_history'] = context['execution_history'][-100:]
            
            # Extract variable assignments (simplified)
            if result.success and '=' in source:
                lines = source.split('\n')
                for line in lines:
                    if '=' in line and not line.strip().startswith('#'):
                        try:
                            var_name = line.split('=')[0].strip()
                            if var_name.isidentifier():
                                context['variables'][var_name] = True
                        except:
                            pass
            
            # Extract imports (simplified)
            if 'import ' in source:
                lines = source.split('\n')
                for line in lines:
                    if line.strip().startswith('import ') or line.strip().startswith('from '):
                        context['imports'].add(line.strip())
                        
        except Exception as e:
            logger.error(f"Error updating kernel context: {str(e)}")
    
    async def _detect_and_create_widgets(
        self, 
        source: str, 
        notebook_id: str, 
        cell_id: str
    ) -> List[str]:
        """Detect widget creation in code and create widget objects"""
        try:
            widgets_created = []
            
            # Enhanced pattern matching for common widget patterns
            widget_patterns = {
                'slider': [
                    r'(\w+)\s*=.*slider\s*\(',
                    r'(\w+)\s*=.*IntSlider\s*\(',
                    r'(\w+)\s*=.*FloatSlider\s*\('
                ],
                'button': [
                    r'(\w+)\s*=.*button\s*\(',
                    r'(\w+)\s*=.*Button\s*\('
                ],
                'text': [
                    r'(\w+)\s*=.*text\s*\(',
                    r'(\w+)\s*=.*Text\s*\(',
                    r'(\w+)\s*=.*Textarea\s*\('
                ],
                'dropdown': [
                    r'(\w+)\s*=.*dropdown\s*\(',
                    r'(\w+)\s*=.*Dropdown\s*\(',
                    r'(\w+)\s*=.*Select\s*\('
                ],
                'checkbox': [
                    r'(\w+)\s*=.*checkbox\s*\(',
                    r'(\w+)\s*=.*Checkbox\s*\('
                ],
                'output': [
                    r'(\w+)\s*=.*Output\s*\(',
                    r'(\w+)\s*=.*output\s*\('
                ]
            }
            
            import re
            for widget_type, patterns in widget_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, source, re.IGNORECASE)
                    for match in matches:
                        # Extract additional properties from the widget creation
                        properties = await self._extract_widget_properties(source, match, widget_type)
                        
                        widget_id = await self.create_widget(
                            notebook_id=notebook_id,
                            cell_id=cell_id,
                            widget_type=widget_type,
                            properties=properties,
                            initial_value=properties.get('value')
                        )
                        if widget_id:
                            widgets_created.append(widget_id)
            
            return widgets_created
            
        except Exception as e:
            logger.error(f"Error detecting widgets: {str(e)}")
            return []
    
    async def _extract_widget_properties(
        self, 
        source: str, 
        variable_name: str, 
        widget_type: str
    ) -> Dict[str, Any]:
        """Extract widget properties from source code"""
        try:
            properties = {
                'variable_name': variable_name,
                'widget_type': widget_type
            }
            
            # Find the line with the widget creation
            lines = source.split('\n')
            widget_line = None
            for line in lines:
                if variable_name in line and any(w in line.lower() for w in [widget_type, widget_type.capitalize()]):
                    widget_line = line
                    break
            
            if widget_line:
                # Extract common properties using regex
                import re
                
                # Extract value
                value_match = re.search(r'value\s*=\s*([^,)]+)', widget_line)
                if value_match:
                    try:
                        value_str = value_match.group(1).strip()
                        # Try to evaluate simple values
                        if value_str.isdigit():
                            properties['value'] = int(value_str)
                        elif value_str.replace('.', '').isdigit():
                            properties['value'] = float(value_str)
                        elif value_str.startswith('"') and value_str.endswith('"'):
                            properties['value'] = value_str[1:-1]
                        elif value_str.startswith("'") and value_str.endswith("'"):
                            properties['value'] = value_str[1:-1]
                        else:
                            properties['value'] = value_str
                    except:
                        properties['value'] = value_str
                
                # Extract min/max for sliders
                if widget_type in ['slider']:
                    min_match = re.search(r'min\s*=\s*([^,)]+)', widget_line)
                    if min_match:
                        try:
                            properties['min'] = float(min_match.group(1).strip())
                        except:
                            pass
                    
                    max_match = re.search(r'max\s*=\s*([^,)]+)', widget_line)
                    if max_match:
                        try:
                            properties['max'] = float(max_match.group(1).strip())
                        except:
                            pass
                
                # Extract description
                desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', widget_line)
                if desc_match:
                    properties['description'] = desc_match.group(1)
                
                # Extract options for dropdowns
                if widget_type in ['dropdown']:
                    options_match = re.search(r'options\s*=\s*(\[[^\]]+\])', widget_line)
                    if options_match:
                        try:
                            # Simple list parsing
                            options_str = options_match.group(1)
                            properties['options'] = options_str
                        except:
                            pass
            
            return properties
            
        except Exception as e:
            logger.error(f"Error extracting widget properties: {str(e)}")
            return {'variable_name': variable_name, 'widget_type': widget_type}
    
    async def _execute_code(self, source: str, language: str) -> ExecutionResult:
        """Execute code in the specified language using secure execution service"""
        try:
            execution_count = len([c for nb in self.notebooks.values() for c in nb.cells if c.execution_count]) + 1
            
            # Try to use secure code execution service if available
            try:
                from .secure_code_execution import (
                    secure_code_execution_service, 
                    CodeExecutionRequest, 
                    ExecutionLanguage,
                    ResourceLimits,
                    SecurityPolicy
                )
                
                # Map language names
                language_map = {
                    'python': ExecutionLanguage.PYTHON,
                    'javascript': ExecutionLanguage.JAVASCRIPT,
                    'r': ExecutionLanguage.R,
                    'bash': ExecutionLanguage.BASH
                }
                
                exec_language = language_map.get(language.lower())
                if exec_language:
                    # Create secure execution request
                    request = CodeExecutionRequest(
                        code=source,
                        language=exec_language,
                        resource_limits=ResourceLimits(
                            max_memory_mb=256,
                            max_cpu_percent=25.0,
                            max_execution_time_seconds=10
                        ),
                        security_policy=SecurityPolicy(
                            allow_network_access=False,
                            allow_file_system_access=False,
                            allow_subprocess_execution=False
                        )
                    )
                    
                    # Execute securely
                    secure_result = await secure_code_execution_service.execute_code(request)
                    
                    # Convert to notebook execution result
                    if secure_result.status.value == 'completed':
                        outputs = [{
                            'output_type': 'stream',
                            'name': 'stdout',
                            'text': secure_result.output
                        }] if secure_result.output else []
                        
                        return ExecutionResult(
                            success=True,
                            outputs=outputs,
                            execution_count=execution_count,
                            execution_time=secure_result.execution_time
                        )
                    else:
                        return ExecutionResult(
                            success=False,
                            outputs=[{
                                'output_type': 'error',
                                'ename': 'ExecutionError',
                                'evalue': secure_result.error or 'Unknown error',
                                'traceback': [secure_result.error or 'Unknown error']
                            }],
                            execution_count=execution_count,
                            execution_time=secure_result.execution_time,
                            error_message=secure_result.error
                        )
                
            except ImportError:
                logger.warning("Secure code execution service not available, falling back to simple execution")
            
            # Fallback to simple execution
            if language == 'python':
                return await self._execute_python_code(source, execution_count)
            elif language == 'javascript':
                return await self._execute_javascript_code(source, execution_count)
            elif language == 'r':
                return await self._execute_r_code(source, execution_count)
            else:
                return ExecutionResult(
                    success=False,
                    outputs=[],
                    execution_count=execution_count,
                    execution_time=0.0,
                    error_message=f"Unsupported language: {language}"
                )
                
        except Exception as e:
            return ExecutionResult(
                success=False,
                outputs=[],
                execution_count=execution_count,
                execution_time=0.0,
                error_message=str(e)
            )
    
    async def _execute_python_code(self, source: str, execution_count: int) -> ExecutionResult:
        """Execute Python code (simplified implementation)"""
        try:
            # This is a simplified implementation
            # In production, this would use a proper Jupyter kernel
            
            # Create a temporary file for execution
            temp_file = os.path.join(self.temp_dir, f"cell_{execution_count}.py")
            
            with open(temp_file, 'w') as f:
                f.write(source)
            
            # Simulate execution (in reality, would use subprocess or kernel)
            outputs = []
            
            # Simple pattern matching for common outputs
            if 'print(' in source:
                # Extract print statements (very basic)
                lines = source.split('\n')
                for line in lines:
                    if 'print(' in line:
                        # Very basic print extraction
                        try:
                            # This is a simplified demo - real implementation would execute properly
                            output_text = "Output from: " + line.strip()
                            outputs.append({
                                'output_type': 'stream',
                                'name': 'stdout',
                                'text': output_text + '\n'
                            })
                        except:
                            pass
            
            # Add execution result
            if not outputs:
                outputs.append({
                    'output_type': 'execute_result',
                    'execution_count': execution_count,
                    'data': {
                        'text/plain': 'Code executed successfully'
                    }
                })
            
            return ExecutionResult(
                success=True,
                outputs=outputs,
                execution_count=execution_count,
                execution_time=0.1  # Simulated execution time
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                outputs=[{
                    'output_type': 'error',
                    'ename': 'ExecutionError',
                    'evalue': str(e),
                    'traceback': [str(e)]
                }],
                execution_count=execution_count,
                execution_time=0.0,
                error_message=str(e)
            )
    
    async def _execute_javascript_code(self, source: str, execution_count: int) -> ExecutionResult:
        """Execute JavaScript code (simplified implementation)"""
        try:
            # Simplified JavaScript execution simulation
            outputs = []
            
            if 'console.log(' in source:
                lines = source.split('\n')
                for line in lines:
                    if 'console.log(' in line:
                        output_text = "JS Output from: " + line.strip()
                        outputs.append({
                            'output_type': 'stream',
                            'name': 'stdout',
                            'text': output_text + '\n'
                        })
            
            if not outputs:
                outputs.append({
                    'output_type': 'execute_result',
                    'execution_count': execution_count,
                    'data': {
                        'text/plain': 'JavaScript code executed successfully'
                    }
                })
            
            return ExecutionResult(
                success=True,
                outputs=outputs,
                execution_count=execution_count,
                execution_time=0.1
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                outputs=[{
                    'output_type': 'error',
                    'ename': 'JSExecutionError',
                    'evalue': str(e),
                    'traceback': [str(e)]
                }],
                execution_count=execution_count,
                execution_time=0.0,
                error_message=str(e)
            )
    
    async def _execute_r_code(self, source: str, execution_count: int) -> ExecutionResult:
        """Execute R code (simplified implementation)"""
        try:
            # Simplified R execution simulation
            outputs = []
            
            if 'print(' in source:
                lines = source.split('\n')
                for line in lines:
                    if 'print(' in line:
                        output_text = "R Output from: " + line.strip()
                        outputs.append({
                            'output_type': 'stream',
                            'name': 'stdout',
                            'text': output_text + '\n'
                        })
            
            if not outputs:
                outputs.append({
                    'output_type': 'execute_result',
                    'execution_count': execution_count,
                    'data': {
                        'text/plain': 'R code executed successfully'
                    }
                })
            
            return ExecutionResult(
                success=True,
                outputs=outputs,
                execution_count=execution_count,
                execution_time=0.1
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                outputs=[{
                    'output_type': 'error',
                    'ename': 'RExecutionError',
                    'evalue': str(e),
                    'traceback': [str(e)]
                }],
                execution_count=execution_count,
                execution_time=0.0,
                error_message=str(e)
            )
    
    async def execute_all_cells(self, notebook_id: str, user_id: str) -> List[ExecutionResult]:
        """Execute all cells in the notebook"""
        try:
            notebook = await self.get_notebook(notebook_id, user_id)
            if not notebook:
                return []
            
            results = []
            for cell in notebook.cells:
                if cell.cell_type == 'code':
                    result = await self.execute_cell(notebook_id, cell.cell_id, user_id)
                    if result:
                        results.append(result)
            
            logger.info(f"Executed all cells in notebook {notebook_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error executing all cells in notebook {notebook_id}: {str(e)}")
            return []
    
    async def add_collaborator(self, notebook_id: str, collaborator_id: str, owner_id: str) -> bool:
        """Add a collaborator to the notebook"""
        try:
            notebook = await self.get_notebook(notebook_id, owner_id)
            if not notebook:
                return False
            
            if collaborator_id not in notebook.collaborators:
                notebook.collaborators.append(collaborator_id)
                notebook.modified_at = datetime.now()
                logger.info(f"Added collaborator {collaborator_id} to notebook {notebook_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding collaborator to notebook {notebook_id}: {str(e)}")
            return False
    
    async def remove_collaborator(self, notebook_id: str, collaborator_id: str, owner_id: str) -> bool:
        """Remove a collaborator from the notebook"""
        try:
            notebook = await self.get_notebook(notebook_id, owner_id)
            if not notebook:
                return False
            
            if collaborator_id in notebook.collaborators:
                notebook.collaborators.remove(collaborator_id)
                notebook.modified_at = datetime.now()
                logger.info(f"Removed collaborator {collaborator_id} from notebook {notebook_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing collaborator from notebook {notebook_id}: {str(e)}")
            return False
    
    async def export_notebook(self, notebook_id: str, user_id: str, format: str = 'ipynb') -> Optional[Dict[str, Any]]:
        """Export notebook in specified format"""
        try:
            notebook = await self.get_notebook(notebook_id, user_id)
            if not notebook:
                return None
            
            if format == 'ipynb':
                # Convert to standard Jupyter notebook format (simplified)
                nb_data = {
                    "cells": [],
                    "metadata": notebook.metadata,
                    "nbformat": 4,
                    "nbformat_minor": 4
                }
                
                for cell in notebook.cells:
                    nb_cell = {
                        "cell_type": cell.cell_type,
                        "source": cell.source,
                        "metadata": cell.metadata
                    }
                    
                    if cell.cell_type == 'code':
                        nb_cell["execution_count"] = cell.execution_count
                        nb_cell["outputs"] = cell.outputs
                    
                    nb_data["cells"].append(nb_cell)
                
                return json.dumps(nb_data, indent=2)
            
            elif format == 'json':
                # Export as JSON
                return {
                    'notebook_id': notebook.notebook_id,
                    'title': notebook.title,
                    'cells': [asdict(cell) for cell in notebook.cells],
                    'metadata': notebook.metadata,
                    'created_at': notebook.created_at.isoformat(),
                    'modified_at': notebook.modified_at.isoformat(),
                    'owner_id': notebook.owner_id,
                    'collaborators': notebook.collaborators,
                    'version': notebook.version
                }
            
            else:
                logger.warning(f"Unsupported export format: {format}")
                return None
                
        except Exception as e:
            logger.error(f"Error exporting notebook {notebook_id}: {str(e)}")
            return None
    
    async def import_notebook(self, notebook_data: str, owner_id: str, format: str = 'ipynb') -> Optional[str]:
        """Import notebook from external format"""
        try:
            if format == 'ipynb':
                # Parse Jupyter notebook format (simplified)
                nb_data = json.loads(notebook_data)
                
                # Create cells
                cells = []
                for nb_cell in nb_data.get('cells', []):
                    cell = NotebookCell(
                        cell_id=str(uuid.uuid4()),
                        cell_type=nb_cell.get('cell_type', 'code'),
                        source=nb_cell.get('source', ''),
                        outputs=nb_cell.get('outputs', []),
                        execution_count=nb_cell.get('execution_count', None),
                        metadata=nb_cell.get('metadata', {})
                    )
                    cells.append(cell)
                
                # Create notebook
                notebook_id = str(uuid.uuid4())
                notebook = NotebookData(
                    notebook_id=notebook_id,
                    title=nb_data.get('metadata', {}).get('title', 'Imported Notebook'),
                    cells=cells,
                    metadata=nb_data.get('metadata', {}),
                    kernel_spec=nb_data.get('metadata', {}).get('kernelspec', self.supported_kernels['python3']),
                    created_at=datetime.now(),
                    modified_at=datetime.now(),
                    owner_id=owner_id,
                    collaborators=[]
                )
                
                self.notebooks[notebook_id] = notebook
                self.execution_queue[notebook_id] = []
                
                logger.info(f"Imported notebook {notebook_id} for user {owner_id}")
                return notebook_id
            
            else:
                logger.warning(f"Unsupported import format: {format}")
                return None
                
        except Exception as e:
            logger.error(f"Error importing notebook: {str(e)}")
            return None
    
    async def list_user_notebooks(self, user_id: str) -> List[Dict[str, Any]]:
        """List all notebooks accessible to the user"""
        try:
            user_notebooks = []
            
            for notebook in self.notebooks.values():
                if notebook.owner_id == user_id or user_id in notebook.collaborators:
                    user_notebooks.append({
                        'notebook_id': notebook.notebook_id,
                        'title': notebook.title,
                        'created_at': notebook.created_at.isoformat(),
                        'modified_at': notebook.modified_at.isoformat(),
                        'owner_id': notebook.owner_id,
                        'is_owner': notebook.owner_id == user_id,
                        'cell_count': len(notebook.cells),
                        'version': notebook.version
                    })
            
            return sorted(user_notebooks, key=lambda x: x['modified_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing notebooks for user {user_id}: {str(e)}")
            return []
    
    async def get_kernel_status(self, notebook_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get kernel status for a notebook"""
        try:
            notebook = await self.get_notebook(notebook_id, user_id)
            if not notebook:
                return None
            
            kernel_info = await self.get_kernel_for_notebook(notebook_id)
            if not kernel_info:
                return {
                    'status': 'no_kernel',
                    'message': 'No kernel available'
                }
            
            return {
                'kernel_id': kernel_info.kernel_id,
                'kernel_name': kernel_info.kernel_name,
                'language': kernel_info.language,
                'status': kernel_info.status,
                'last_activity': kernel_info.last_activity.isoformat(),
                'memory_usage': kernel_info.memory_usage,
                'cpu_usage': kernel_info.cpu_usage,
                'process_id': kernel_info.process_id
            }
            
        except Exception as e:
            logger.error(f"Error getting kernel status: {str(e)}")
            return None
    
    async def restart_kernel(self, notebook_id: str, user_id: str) -> bool:
        """Restart the kernel for a notebook"""
        try:
            notebook = await self.get_notebook(notebook_id, user_id)
            if not notebook:
                return False
            
            # Find and shutdown existing kernel
            kernel_info = await self.get_kernel_for_notebook(notebook_id)
            if kernel_info:
                await self._shutdown_kernel(kernel_info.kernel_id)
            
            # Create new kernel
            kernel_name = notebook.kernel_spec.get('name', 'python3')
            new_kernel_id = await self._create_kernel(notebook_id, kernel_name)
            
            if new_kernel_id:
                logger.info(f"Restarted kernel for notebook {notebook_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error restarting kernel: {str(e)}")
            return False
    
    async def interrupt_kernel(self, notebook_id: str, user_id: str) -> bool:
        """Interrupt kernel execution"""
        try:
            notebook = await self.get_notebook(notebook_id, user_id)
            if not notebook:
                return False
            
            kernel_info = await self.get_kernel_for_notebook(notebook_id)
            if not kernel_info:
                return False
            
            # In a real implementation, this would send interrupt signal to kernel
            kernel_info.status = 'idle'
            kernel_info.last_activity = datetime.now()
            
            logger.info(f"Interrupted kernel for notebook {notebook_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error interrupting kernel: {str(e)}")
            return False
    
    async def get_notebook_variables(self, notebook_id: str, user_id: str) -> Dict[str, Any]:
        """Get variables defined in the notebook kernel"""
        try:
            notebook = await self.get_notebook(notebook_id, user_id)
            if not notebook:
                return {}
            
            kernel_info = await self.get_kernel_for_notebook(notebook_id)
            if not kernel_info:
                return {}
            
            # Get variables from kernel context
            context = self.kernel_managers.get(kernel_info.kernel_id, {})
            variables = context.get('variables', {})
            
            return {
                'variables': list(variables.keys()),
                'imports': list(context.get('imports', set())),
                'execution_count': len(context.get('execution_history', []))
            }
            
        except Exception as e:
            logger.error(f"Error getting notebook variables: {str(e)}")
            return {}
    
    async def clear_notebook_output(self, notebook_id: str, user_id: str) -> bool:
        """Clear all cell outputs in the notebook"""
        try:
            notebook = await self.get_notebook(notebook_id, user_id)
            if not notebook:
                return False
            
            for cell in notebook.cells:
                if cell.cell_type == 'code':
                    cell.outputs = []
                    cell.execution_count = None
                    cell.execution_state = 'idle'
                    cell.execution_time = None
            
            notebook.modified_at = datetime.now()
            logger.info(f"Cleared outputs for notebook {notebook_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing notebook output: {str(e)}")
            return False
    
    async def duplicate_notebook(self, notebook_id: str, user_id: str, new_title: str = None) -> Optional[str]:
        """Create a duplicate of an existing notebook"""
        try:
            original_notebook = await self.get_notebook(notebook_id, user_id)
            if not original_notebook:
                return None
            
            # Create new cells (deep copy)
            new_cells = []
            for cell in original_notebook.cells:
                new_cell = NotebookCell(
                    cell_id=str(uuid.uuid4()),
                    cell_type=cell.cell_type,
                    source=cell.source,
                    outputs=[],  # Clear outputs in duplicate
                    execution_count=None,  # Reset execution count
                    metadata=cell.metadata.copy()
                )
                new_cells.append(new_cell)
            
            # Create duplicate notebook
            new_notebook_id = str(uuid.uuid4())
            duplicate_title = new_title or f"{original_notebook.title} (Copy)"
            
            duplicate_notebook = NotebookData(
                notebook_id=new_notebook_id,
                title=duplicate_title,
                cells=new_cells,
                metadata=original_notebook.metadata.copy(),
                kernel_spec=original_notebook.kernel_spec.copy(),
                created_at=datetime.now(),
                modified_at=datetime.now(),
                owner_id=user_id,
                collaborators=[]
            )
            
            self.notebooks[new_notebook_id] = duplicate_notebook
            self.execution_queue[new_notebook_id] = []
            
            logger.info(f"Duplicated notebook {notebook_id} as {new_notebook_id}")
            return new_notebook_id
            
        except Exception as e:
            logger.error(f"Error duplicating notebook: {str(e)}")
            return None
    
    async def get_notebook_statistics(self, notebook_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics about the notebook"""
        try:
            notebook = await self.get_notebook(notebook_id, user_id)
            if not notebook:
                return None
            
            stats = {
                'total_cells': len(notebook.cells),
                'code_cells': len([c for c in notebook.cells if c.cell_type == 'code']),
                'markdown_cells': len([c for c in notebook.cells if c.cell_type == 'markdown']),
                'executed_cells': len([c for c in notebook.cells if c.execution_count is not None]),
                'total_execution_time': sum(c.execution_time or 0 for c in notebook.cells),
                'last_execution': max((c.execution_count or 0 for c in notebook.cells), default=0),
                'collaborators_count': len(notebook.collaborators),
                'widgets_count': len([w for w in self.widgets.values() if w.notebook_id == notebook_id]),
                'created_at': notebook.created_at.isoformat(),
                'modified_at': notebook.modified_at.isoformat(),
                'version': notebook.version
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting notebook statistics: {str(e)}")
            return None
    
    def cleanup(self):
        """Clean up temporary files and resources"""
        try:
            # Shutdown cleanup thread
            if self._cleanup_thread and self._cleanup_thread.is_alive():
                self._shutdown_event.set()
                self._cleanup_thread.join(timeout=5)
            
            # Shutdown all kernels
            for kernel_id in list(self.kernels.keys()):
                asyncio.create_task(self._shutdown_kernel(kernel_id))
            
            # Clean up temporary directory
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            
            logger.info("Cleaned up Jupyter notebook service resources")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

# Global service instance
jupyter_service = JupyterNotebookService()