"""
Data models for research assistant mode.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from datetime import datetime, timedelta


class ResearchDomain(Enum):
    """Research domains for specialized optimization."""
    MACHINE_LEARNING = "machine_learning"
    COMPUTER_SCIENCE = "computer_science"
    MATHEMATICS = "mathematics"
    PHYSICS = "physics"
    BIOLOGY = "biology"
    CHEMISTRY = "chemistry"
    ENGINEERING = "engineering"
    SOCIAL_SCIENCES = "social_sciences"
    HUMANITIES = "humanities"
    INTERDISCIPLINARY = "interdisciplinary"


class TaskType(Enum):
    """Types of research tasks."""
    LITERATURE_REVIEW = "literature_review"
    DATA_COLLECTION = "data_collection"
    ANALYSIS = "analysis"
    EXPERIMENTATION = "experimentation"
    WRITING = "writing"
    PRESENTATION = "presentation"
    COLLABORATION = "collaboration"
    LEARNING = "learning"
    PLANNING = "planning"
    VALIDATION = "validation"


class TaskPriority(Enum):
    """Priority levels for research tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OptimizationType(Enum):
    """Types of workflow optimizations."""
    TIME_EFFICIENCY = "time_efficiency"
    QUALITY_IMPROVEMENT = "quality_improvement"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    COLLABORATION_ENHANCEMENT = "collaboration_enhancement"
    LEARNING_ACCELERATION = "learning_acceleration"
    BOTTLENECK_REMOVAL = "bottleneck_removal"


class WorkflowStatus(Enum):
    """Status of workflow execution."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


@dataclass
class TaskDependency:
    """Dependency relationship between tasks."""
    prerequisite_task_id: str
    dependent_task_id: str
    dependency_type: str  # "hard", "soft", "preferred"
    delay_required: Optional[timedelta] = None
    
    def __post_init__(self):
        """Validate dependency."""
        if self.prerequisite_task_id == self.dependent_task_id:
            raise ValueError("Task cannot depend on itself")
        if self.dependency_type not in ["hard", "soft", "preferred"]:
            raise ValueError("Invalid dependency type")


@dataclass
class ResearchTask:
    """Individual research task within a workflow."""
    task_id: str
    task_type: TaskType
    title: str
    description: str
    estimated_duration: timedelta
    priority: TaskPriority
    required_resources: List[str] = field(default_factory=list)
    skills_required: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    
    # Execution tracking
    actual_duration: Optional[timedelta] = None
    completion_percentage: float = 0.0
    quality_score: Optional[float] = None
    difficulty_rating: Optional[float] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate task data."""
        if not self.task_id:
            raise ValueError("Task ID cannot be empty")
        if self.estimated_duration.total_seconds() <= 0:
            raise ValueError("Estimated duration must be positive")
        if not 0 <= self.completion_percentage <= 100:
            raise ValueError("Completion percentage must be between 0 and 100")
    
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.completion_percentage >= 100.0 and self.completed_at is not None
    
    def get_efficiency_ratio(self) -> Optional[float]:
        """Calculate efficiency ratio (estimated vs actual duration)."""
        if self.actual_duration is None or self.estimated_duration.total_seconds() == 0:
            return None
        
        return self.estimated_duration.total_seconds() / self.actual_duration.total_seconds()
    
    def update_progress(self, completion_percentage: float, quality_score: Optional[float] = None):
        """Update task progress."""
        self.completion_percentage = max(0.0, min(100.0, completion_percentage))
        if quality_score is not None:
            self.quality_score = max(0.0, min(1.0, quality_score))
        self.last_updated = datetime.now()
        
        if self.completion_percentage >= 100.0 and self.completed_at is None:
            self.completed_at = datetime.now()
            if self.started_at:
                self.actual_duration = self.completed_at - self.started_at


@dataclass
class WorkflowStep:
    """Step in a research workflow."""
    step_id: str
    step_name: str
    tasks: List[ResearchTask]
    parallel_execution: bool = False
    optional: bool = False
    
    def get_total_estimated_duration(self) -> timedelta:
        """Get total estimated duration for this step."""
        if self.parallel_execution:
            # For parallel tasks, duration is the maximum
            return max((task.estimated_duration for task in self.tasks), 
                      default=timedelta(0))
        else:
            # For sequential tasks, duration is the sum
            return sum((task.estimated_duration for task in self.tasks), 
                      timedelta(0))
    
    def get_completion_percentage(self) -> float:
        """Get overall completion percentage for this step."""
        if not self.tasks:
            return 100.0 if self.optional else 0.0
        
        total_completion = sum(task.completion_percentage for task in self.tasks)
        return total_completion / len(self.tasks)
    
    def is_completed(self) -> bool:
        """Check if step is completed."""
        if self.optional and not self.tasks:
            return True
        return all(task.is_completed() for task in self.tasks)


@dataclass
class ResearchWorkflow:
    """Complete research workflow with tasks and dependencies."""
    workflow_id: str
    title: str
    description: str
    research_domain: ResearchDomain
    steps: List[WorkflowStep]
    dependencies: List[TaskDependency] = field(default_factory=list)
    
    # Workflow metadata
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    status: WorkflowStatus = WorkflowStatus.NOT_STARTED
    
    # Optimization tracking
    optimization_history: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate workflow data."""
        if not self.workflow_id:
            raise ValueError("Workflow ID cannot be empty")
        if not self.steps:
            raise ValueError("Workflow must have at least one step")
    
    def get_all_tasks(self) -> List[ResearchTask]:
        """Get all tasks from all steps."""
        all_tasks = []
        for step in self.steps:
            all_tasks.extend(step.tasks)
        return all_tasks
    
    def get_task_by_id(self, task_id: str) -> Optional[ResearchTask]:
        """Get task by ID."""
        for task in self.get_all_tasks():
            if task.task_id == task_id:
                return task
        return None
    
    def get_total_estimated_duration(self) -> timedelta:
        """Get total estimated duration for the workflow."""
        total_duration = timedelta(0)
        for step in self.steps:
            total_duration += step.get_total_estimated_duration()
        return total_duration
    
    def get_completion_percentage(self) -> float:
        """Get overall workflow completion percentage."""
        if not self.steps:
            return 100.0
        
        total_completion = sum(step.get_completion_percentage() for step in self.steps)
        return total_completion / len(self.steps)
    
    def is_completed(self) -> bool:
        """Check if workflow is completed."""
        return all(step.is_completed() for step in self.steps)
    
    def get_critical_path(self) -> List[ResearchTask]:
        """Get critical path through the workflow."""
        # Simplified critical path calculation
        # In practice, would use proper critical path method (CPM)
        
        critical_tasks = []
        
        # Find tasks with hard dependencies
        dependent_tasks = {dep.dependent_task_id for dep in self.dependencies 
                          if dep.dependency_type == "hard"}
        
        # Start with tasks that have no dependencies
        current_tasks = [task for task in self.get_all_tasks() 
                        if task.task_id not in dependent_tasks]
        
        while current_tasks:
            # Find task with longest duration
            longest_task = max(current_tasks, key=lambda t: t.estimated_duration.total_seconds())
            critical_tasks.append(longest_task)
            
            # Find next tasks that depend on this one
            next_task_ids = [dep.dependent_task_id for dep in self.dependencies 
                           if dep.prerequisite_task_id == longest_task.task_id]
            
            current_tasks = [self.get_task_by_id(tid) for tid in next_task_ids 
                           if self.get_task_by_id(tid) is not None]
        
        return critical_tasks
    
    def validate_dependencies(self) -> List[str]:
        """Validate workflow dependencies and return any errors."""
        errors = []
        task_ids = {task.task_id for task in self.get_all_tasks()}
        
        for dependency in self.dependencies:
            # Check if referenced tasks exist
            if dependency.prerequisite_task_id not in task_ids:
                errors.append(f"Prerequisite task {dependency.prerequisite_task_id} not found")
            
            if dependency.dependent_task_id not in task_ids:
                errors.append(f"Dependent task {dependency.dependent_task_id} not found")
        
        # Check for circular dependencies (simplified check)
        # In practice, would use proper cycle detection algorithm
        dependency_graph = {}
        for dep in self.dependencies:
            if dep.prerequisite_task_id not in dependency_graph:
                dependency_graph[dep.prerequisite_task_id] = []
            dependency_graph[dep.prerequisite_task_id].append(dep.dependent_task_id)
        
        # Simple cycle detection using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in dependency_graph.get(node, []):
                if has_cycle(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for task_id in task_ids:
            if task_id not in visited:
                if has_cycle(task_id):
                    errors.append("Circular dependency detected in workflow")
                    break
        
        return errors


@dataclass
class WorkflowMetrics:
    """Metrics for workflow performance analysis."""
    workflow_id: str
    
    # Time metrics
    total_planned_duration: timedelta
    total_actual_duration: Optional[timedelta] = None
    average_task_efficiency: Optional[float] = None
    
    # Quality metrics
    average_quality_score: Optional[float] = None
    completion_rate: float = 0.0
    on_time_completion_rate: float = 0.0
    
    # Resource metrics
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    bottleneck_tasks: List[str] = field(default_factory=list)
    
    # Learning metrics
    skill_development_score: Optional[float] = None
    knowledge_acquisition_rate: Optional[float] = None
    
    # Collaboration metrics
    collaboration_effectiveness: Optional[float] = None
    communication_frequency: Optional[float] = None
    
    # Calculated at
    calculated_at: datetime = field(default_factory=datetime.now)
    
    def calculate_efficiency_score(self) -> float:
        """Calculate overall efficiency score."""
        scores = []
        
        if self.average_task_efficiency is not None:
            scores.append(self.average_task_efficiency)
        
        if self.completion_rate is not None:
            scores.append(self.completion_rate)
        
        if self.on_time_completion_rate is not None:
            scores.append(self.on_time_completion_rate)
        
        if self.average_quality_score is not None:
            scores.append(self.average_quality_score)
        
        return np.mean(scores) if scores else 0.0


@dataclass
class WorkflowOptimization:
    """Optimization recommendation for a workflow."""
    optimization_id: str
    workflow_id: str
    optimization_type: OptimizationType
    title: str
    description: str
    
    # Optimization details
    affected_tasks: List[str]
    recommended_changes: List[str]
    expected_improvement: Dict[str, float]  # metric -> improvement percentage
    implementation_effort: str  # "low", "medium", "high"
    risk_level: str  # "low", "medium", "high"
    
    # Validation
    success_criteria: List[str]
    measurement_metrics: List[str]
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    priority_score: float = 0.5
    
    def __post_init__(self):
        """Validate optimization data."""
        if not self.optimization_id:
            raise ValueError("Optimization ID cannot be empty")
        if not 0 <= self.priority_score <= 1:
            raise ValueError("Priority score must be between 0 and 1")
        if self.implementation_effort not in ["low", "medium", "high"]:
            raise ValueError("Implementation effort must be low, medium, or high")
        if self.risk_level not in ["low", "medium", "high"]:
            raise ValueError("Risk level must be low, medium, or high")
    
    def get_impact_score(self) -> float:
        """Calculate impact score based on expected improvements."""
        if not self.expected_improvement:
            return 0.0
        
        # Weight different metrics
        weights = {
            "time_efficiency": 0.3,
            "quality": 0.25,
            "resource_utilization": 0.2,
            "learning_effectiveness": 0.15,
            "collaboration": 0.1
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for metric, improvement in self.expected_improvement.items():
            weight = weights.get(metric, 0.1)  # Default weight for unknown metrics
            weighted_score += improvement * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def get_roi_estimate(self) -> float:
        """Estimate return on investment for this optimization."""
        impact = self.get_impact_score()
        
        # Adjust for implementation effort and risk
        effort_penalty = {"low": 0.1, "medium": 0.3, "high": 0.5}[self.implementation_effort]
        risk_penalty = {"low": 0.05, "medium": 0.15, "high": 0.3}[self.risk_level]
        
        roi = impact - effort_penalty - risk_penalty
        return max(0.0, roi)


@dataclass
class ResearchSession:
    """Individual research session within a workflow."""
    session_id: str
    workflow_id: str
    user_id: str
    
    # Session details
    start_time: datetime
    end_time: Optional[datetime] = None
    tasks_worked_on: List[str] = field(default_factory=list)
    
    # Performance metrics
    productivity_score: Optional[float] = None
    focus_score: Optional[float] = None
    satisfaction_score: Optional[float] = None
    
    # Context
    environment_factors: Dict[str, Any] = field(default_factory=dict)
    interruptions: List[Dict[str, Any]] = field(default_factory=list)
    
    def get_duration(self) -> Optional[timedelta]:
        """Get session duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.end_time is None
    
    def end_session(self, productivity_score: Optional[float] = None, 
                   satisfaction_score: Optional[float] = None):
        """End the session with optional scores."""
        self.end_time = datetime.now()
        if productivity_score is not None:
            self.productivity_score = max(0.0, min(1.0, productivity_score))
        if satisfaction_score is not None:
            self.satisfaction_score = max(0.0, min(1.0, satisfaction_score))