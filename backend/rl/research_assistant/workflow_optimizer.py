"""Workflow optimizer for research assistant mode."""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of research tasks."""
    LITERATURE_SEARCH = "literature_search"
    PAPER_ANALYSIS = "paper_analysis"
    DATA_EXTRACTION = "data_extraction"
    SYNTHESIS = "synthesis"
    WRITING = "writing"
    REVIEW = "review"
    CITATION_MANAGEMENT = "citation_management"
    METHODOLOGY_DESIGN = "methodology_design"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class WorkflowStage(Enum):
    """Stages in research workflow."""
    PLANNING = "planning"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    WRITING = "writing"
    REVIEW = "review"
    FINALIZATION = "finalization"


@dataclass
class Task:
    """Represents a research task."""
    task_id: str
    task_type: TaskType
    priority: TaskPriority
    estimated_duration: float  # in hours
    dependencies: List[str] = field(default_factory=list)
    resources_required: List[str] = field(default_factory=list)
    complexity_score: float = 1.0
    user_preference_score: float = 0.0
    deadline: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStep:
    """Represents a step in a workflow."""
    step_id: str
    task: Task
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    actual_duration: Optional[float] = None
    efficiency_score: float = 0.0
    user_satisfaction: float = 0.0
    bottlenecks: List[str] = field(default_factory=list)


@dataclass
class Workflow:
    """Represents a complete research workflow."""
    workflow_id: str
    user_id: str
    stage: WorkflowStage
    steps: List[WorkflowStep] = field(default_factory=list)
    total_estimated_duration: float = 0.0
    total_actual_duration: float = 0.0
    efficiency_score: float = 0.0
    completion_rate: float = 0.0
    user_satisfaction: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class OptimizationSuggestion:
    """Represents a workflow optimization suggestion."""
    suggestion_id: str
    suggestion_type: str
    description: str
    expected_improvement: float
    confidence: float
    implementation_effort: str  # "low", "medium", "high"
    affected_tasks: List[str]
    rationale: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EfficiencyMetrics:
    """Metrics for workflow efficiency analysis."""
    time_efficiency: float
    resource_utilization: float
    task_completion_rate: float
    user_satisfaction: float
    bottleneck_frequency: float
    context_switch_penalty: float
    overall_efficiency: float


class WorkflowOptimizer:
    """Optimizes research workflows for efficiency and user satisfaction."""
    
    def __init__(self):
        self.workflow_history: Dict[str, List[Workflow]] = defaultdict(list)
        self.task_performance_data: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        self.optimization_patterns: Dict[str, List[OptimizationSuggestion]] = defaultdict(list)
        self.user_preferences: Dict[str, Dict[str, float]] = defaultdict(dict)
    
    async def analyze_workflow_efficiency(self, workflow: Workflow) -> EfficiencyMetrics:
        """Analyze the efficiency of a workflow."""
        try:
            # Calculate time efficiency
            time_efficiency = await self._calculate_time_efficiency(workflow)
            
            # Calculate resource utilization
            resource_utilization = await self._calculate_resource_utilization(workflow)
            
            # Calculate task completion rate
            completion_rate = await self._calculate_completion_rate(workflow)
            
            # Calculate user satisfaction
            user_satisfaction = await self._calculate_user_satisfaction(workflow)
            
            # Calculate bottleneck frequency
            bottleneck_frequency = await self._calculate_bottleneck_frequency(workflow)
            
            # Calculate context switch penalty
            context_switch_penalty = await self._calculate_context_switch_penalty(workflow)
            
            # Calculate overall efficiency
            overall_efficiency = await self._calculate_overall_efficiency(
                time_efficiency, resource_utilization, completion_rate,
                user_satisfaction, bottleneck_frequency, context_switch_penalty
            )
            
            metrics = EfficiencyMetrics(
                time_efficiency=time_efficiency,
                resource_utilization=resource_utilization,
                task_completion_rate=completion_rate,
                user_satisfaction=user_satisfaction,
                bottleneck_frequency=bottleneck_frequency,
                context_switch_penalty=context_switch_penalty,
                overall_efficiency=overall_efficiency
            )
            
            logger.info(f"Analyzed workflow {workflow.workflow_id} efficiency: {overall_efficiency:.3f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error analyzing workflow efficiency: {str(e)}")
            return EfficiencyMetrics(0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0)
    
    async def suggest_workflow_improvements(self, workflow: Workflow, user_preferences: Dict[str, float]) -> List[OptimizationSuggestion]:
        """Suggest improvements for a workflow based on analysis."""
        try:
            suggestions = []
            
            # Analyze current workflow
            metrics = await self.analyze_workflow_efficiency(workflow)
            
            # Task reordering suggestions
            reorder_suggestions = await self._suggest_task_reordering(workflow, metrics)
            suggestions.extend(reorder_suggestions)
            
            # Resource optimization suggestions
            resource_suggestions = await self._suggest_resource_optimization(workflow, metrics)
            suggestions.extend(resource_suggestions)
            
            # Time management suggestions
            time_suggestions = await self._suggest_time_optimization(workflow, metrics)
            suggestions.extend(time_suggestions)
            
            # Bottleneck resolution suggestions
            bottleneck_suggestions = await self._suggest_bottleneck_resolution(workflow, metrics)
            suggestions.extend(bottleneck_suggestions)
            
            # User preference-based suggestions
            preference_suggestions = await self._suggest_preference_optimizations(workflow, user_preferences)
            suggestions.extend(preference_suggestions)
            
            # Sort suggestions by expected improvement
            suggestions.sort(key=lambda s: s.expected_improvement, reverse=True)
            
            logger.info(f"Generated {len(suggestions)} optimization suggestions for workflow {workflow.workflow_id}")
            return suggestions[:10]  # Return top 10 suggestions
            
        except Exception as e:
            logger.error(f"Error generating workflow suggestions: {str(e)}")
            return []
    
    async def optimize_task_sequence(self, tasks: List[Task], constraints: Dict[str, Any]) -> List[Task]:
        """Optimize the sequence of tasks for maximum efficiency."""
        try:
            if not tasks:
                return []
            
            # Create dependency graph
            dependency_graph = await self._build_dependency_graph(tasks)
            
            # Apply topological sorting with optimization
            optimized_sequence = await self._optimize_topological_sort(tasks, dependency_graph, constraints)
            
            # Apply additional optimizations
            optimized_sequence = await self._apply_sequence_optimizations(optimized_sequence, constraints)
            
            logger.info(f"Optimized sequence for {len(tasks)} tasks")
            return optimized_sequence
            
        except Exception as e:
            logger.error(f"Error optimizing task sequence: {str(e)}")
            return tasks  # Return original sequence on error
    
    async def _calculate_time_efficiency(self, workflow: Workflow) -> float:
        """Calculate time efficiency of workflow."""
        if not workflow.steps or workflow.total_estimated_duration == 0:
            return 0.0
        
        # Calculate ratio of estimated to actual time
        completed_steps = [step for step in workflow.steps if step.actual_duration is not None]
        if not completed_steps:
            return 0.0
        
        total_estimated = sum(step.task.estimated_duration for step in completed_steps)
        total_actual = sum(step.actual_duration for step in completed_steps)
        
        if total_actual == 0:
            return 1.0
        
        # Efficiency is better when actual time is close to or less than estimated
        efficiency = min(1.0, total_estimated / total_actual)
        return max(0.0, efficiency)
    
    async def _calculate_resource_utilization(self, workflow: Workflow) -> float:
        """Calculate resource utilization efficiency."""
        if not workflow.steps:
            return 0.0
        
        # Analyze resource usage patterns
        resource_usage = defaultdict(float)
        total_time = 0.0
        
        for step in workflow.steps:
            if step.actual_duration:
                total_time += step.actual_duration
                for resource in step.task.resources_required:
                    resource_usage[resource] += step.actual_duration
        
        if total_time == 0:
            return 0.0
        
        # Calculate average utilization across resources
        if not resource_usage:
            return 1.0  # No specific resources required
        
        utilizations = [usage / total_time for usage in resource_usage.values()]
        return np.mean(utilizations)
    
    async def _calculate_completion_rate(self, workflow: Workflow) -> float:
        """Calculate task completion rate."""
        if not workflow.steps:
            return 0.0
        
        completed_steps = sum(1 for step in workflow.steps if step.end_time is not None)
        return completed_steps / len(workflow.steps)
    
    async def _calculate_user_satisfaction(self, workflow: Workflow) -> float:
        """Calculate average user satisfaction."""
        if not workflow.steps:
            return 0.0
        
        satisfaction_scores = [step.user_satisfaction for step in workflow.steps if step.user_satisfaction > 0]
        if not satisfaction_scores:
            return 0.0
        
        return np.mean(satisfaction_scores)
    
    async def _calculate_bottleneck_frequency(self, workflow: Workflow) -> float:
        """Calculate frequency of bottlenecks."""
        if not workflow.steps:
            return 0.0
        
        steps_with_bottlenecks = sum(1 for step in workflow.steps if step.bottlenecks)
        return steps_with_bottlenecks / len(workflow.steps)
    
    async def _calculate_context_switch_penalty(self, workflow: Workflow) -> float:
        """Calculate penalty from context switching between different task types."""
        if len(workflow.steps) < 2:
            return 0.0
        
        context_switches = 0
        for i in range(1, len(workflow.steps)):
            prev_type = workflow.steps[i-1].task.task_type
            curr_type = workflow.steps[i].task.task_type
            if prev_type != curr_type:
                context_switches += 1
        
        # Normalize by number of possible switches
        max_switches = len(workflow.steps) - 1
        return context_switches / max_switches if max_switches > 0 else 0.0
    
    async def _calculate_overall_efficiency(self, time_eff: float, resource_eff: float, 
                                          completion_rate: float, satisfaction: float,
                                          bottleneck_freq: float, context_penalty: float) -> float:
        """Calculate overall efficiency score."""
        # Weighted combination of efficiency metrics
        weights = {
            'time': 0.25,
            'resource': 0.20,
            'completion': 0.25,
            'satisfaction': 0.15,
            'bottleneck': 0.10,  # Lower is better
            'context': 0.05     # Lower is better
        }
        
        # Invert bottleneck frequency and context penalty (lower is better)
        bottleneck_score = 1.0 - bottleneck_freq
        context_score = 1.0 - context_penalty
        
        overall = (
            weights['time'] * time_eff +
            weights['resource'] * resource_eff +
            weights['completion'] * completion_rate +
            weights['satisfaction'] * satisfaction +
            weights['bottleneck'] * bottleneck_score +
            weights['context'] * context_score
        )
        
        return max(0.0, min(1.0, overall))
    
    async def _suggest_task_reordering(self, workflow: Workflow, metrics: EfficiencyMetrics) -> List[OptimizationSuggestion]:
        """Suggest task reordering optimizations."""
        suggestions = []
        
        if metrics.context_switch_penalty > 0.3:  # High context switching
            suggestion = OptimizationSuggestion(
                suggestion_id=f"reorder_context_{workflow.workflow_id}",
                suggestion_type="task_reordering",
                description="Group similar tasks together to reduce context switching",
                expected_improvement=0.15 * metrics.context_switch_penalty,
                confidence=0.8,
                implementation_effort="low",
                affected_tasks=[step.step_id for step in workflow.steps],
                rationale="High context switching detected between different task types"
            )
            suggestions.append(suggestion)
        
        # Check for dependency optimization opportunities
        if metrics.time_efficiency < 0.7:
            suggestion = OptimizationSuggestion(
                suggestion_id=f"reorder_dependencies_{workflow.workflow_id}",
                suggestion_type="dependency_optimization",
                description="Reorder tasks to minimize waiting time and maximize parallelization",
                expected_improvement=0.2 * (1.0 - metrics.time_efficiency),
                confidence=0.7,
                implementation_effort="medium",
                affected_tasks=[step.step_id for step in workflow.steps],
                rationale="Low time efficiency suggests suboptimal task ordering"
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    async def _suggest_resource_optimization(self, workflow: Workflow, metrics: EfficiencyMetrics) -> List[OptimizationSuggestion]:
        """Suggest resource optimization improvements."""
        suggestions = []
        
        if metrics.resource_utilization < 0.6:
            suggestion = OptimizationSuggestion(
                suggestion_id=f"resource_opt_{workflow.workflow_id}",
                suggestion_type="resource_optimization",
                description="Optimize resource allocation to improve utilization",
                expected_improvement=0.25 * (1.0 - metrics.resource_utilization),
                confidence=0.75,
                implementation_effort="medium",
                affected_tasks=[step.step_id for step in workflow.steps if step.task.resources_required],
                rationale="Low resource utilization indicates inefficient resource allocation"
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    async def _suggest_time_optimization(self, workflow: Workflow, metrics: EfficiencyMetrics) -> List[OptimizationSuggestion]:
        """Suggest time management optimizations."""
        suggestions = []
        
        if metrics.time_efficiency < 0.8:
            suggestion = OptimizationSuggestion(
                suggestion_id=f"time_opt_{workflow.workflow_id}",
                suggestion_type="time_optimization",
                description="Improve time estimation and task duration management",
                expected_improvement=0.2 * (1.0 - metrics.time_efficiency),
                confidence=0.7,
                implementation_effort="low",
                affected_tasks=[step.step_id for step in workflow.steps],
                rationale="Tasks are taking longer than estimated, suggesting need for better time management"
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    async def _suggest_bottleneck_resolution(self, workflow: Workflow, metrics: EfficiencyMetrics) -> List[OptimizationSuggestion]:
        """Suggest bottleneck resolution strategies."""
        suggestions = []
        
        if metrics.bottleneck_frequency > 0.2:
            # Identify most common bottlenecks
            bottleneck_counts = defaultdict(int)
            for step in workflow.steps:
                for bottleneck in step.bottlenecks:
                    bottleneck_counts[bottleneck] += 1
            
            if bottleneck_counts:
                most_common_bottleneck = max(bottleneck_counts.keys(), key=lambda k: bottleneck_counts[k])
                
                suggestion = OptimizationSuggestion(
                    suggestion_id=f"bottleneck_res_{workflow.workflow_id}",
                    suggestion_type="bottleneck_resolution",
                    description=f"Address recurring bottleneck: {most_common_bottleneck}",
                    expected_improvement=0.3 * metrics.bottleneck_frequency,
                    confidence=0.8,
                    implementation_effort="high",
                    affected_tasks=[step.step_id for step in workflow.steps if most_common_bottleneck in step.bottlenecks],
                    rationale=f"Bottleneck '{most_common_bottleneck}' occurs frequently and impacts workflow efficiency"
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    async def _suggest_preference_optimizations(self, workflow: Workflow, user_preferences: Dict[str, float]) -> List[OptimizationSuggestion]:
        """Suggest optimizations based on user preferences."""
        suggestions = []
        
        # Analyze task types vs user preferences
        task_type_distribution = defaultdict(int)
        for step in workflow.steps:
            task_type_distribution[step.task.task_type.value] += 1
        
        # Check if workflow aligns with user preferences
        for task_type, count in task_type_distribution.items():
            preference_score = user_preferences.get(task_type, 0.5)
            task_ratio = count / len(workflow.steps)
            
            if preference_score < 0.3 and task_ratio > 0.3:  # Low preference but high occurrence
                suggestion = OptimizationSuggestion(
                    suggestion_id=f"pref_opt_{task_type}_{workflow.workflow_id}",
                    suggestion_type="preference_optimization",
                    description=f"Reduce or optimize {task_type} tasks based on user preferences",
                    expected_improvement=0.15 * (0.5 - preference_score),
                    confidence=0.6,
                    implementation_effort="medium",
                    affected_tasks=[step.step_id for step in workflow.steps if step.task.task_type.value == task_type],
                    rationale=f"User has low preference for {task_type} tasks but they comprise a large portion of workflow"
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    async def _build_dependency_graph(self, tasks: List[Task]) -> Dict[str, List[str]]:
        """Build dependency graph for tasks."""
        graph = defaultdict(list)
        task_ids = {task.task_id for task in tasks}
        
        for task in tasks:
            for dependency in task.dependencies:
                if dependency in task_ids:
                    graph[dependency].append(task.task_id)
        
        return dict(graph)
    
    async def _optimize_topological_sort(self, tasks: List[Task], dependency_graph: Dict[str, List[str]], 
                                       constraints: Dict[str, Any]) -> List[Task]:
        """Perform optimized topological sorting of tasks."""
        # Create task lookup
        task_lookup = {task.task_id: task for task in tasks}
        
        # Calculate in-degrees
        in_degree = defaultdict(int)
        for task in tasks:
            in_degree[task.task_id] = len(task.dependencies)
        
        # Priority queue for tasks with no dependencies
        available_tasks = [task for task in tasks if in_degree[task.task_id] == 0]
        
        # Sort available tasks by priority and other factors
        available_tasks.sort(key=lambda t: (
            -t.priority.value,  # Higher priority first
            t.complexity_score,  # Lower complexity first for quick wins
            -t.user_preference_score  # Higher user preference first
        ))
        
        result = []
        
        while available_tasks:
            # Select next task based on optimization criteria
            current_task = available_tasks.pop(0)
            result.append(current_task)
            
            # Update dependencies
            for dependent_id in dependency_graph.get(current_task.task_id, []):
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    dependent_task = task_lookup[dependent_id]
                    # Insert in sorted position
                    self._insert_sorted_task(available_tasks, dependent_task)
        
        return result
    
    def _insert_sorted_task(self, task_list: List[Task], task: Task):
        """Insert task in sorted position based on optimization criteria."""
        insert_pos = 0
        for i, existing_task in enumerate(task_list):
            if (task.priority.value > existing_task.priority.value or
                (task.priority.value == existing_task.priority.value and 
                 task.complexity_score < existing_task.complexity_score)):
                insert_pos = i
                break
            insert_pos = i + 1
        
        task_list.insert(insert_pos, task)
    
    async def _apply_sequence_optimizations(self, tasks: List[Task], constraints: Dict[str, Any]) -> List[Task]:
        """Apply additional sequence optimizations."""
        if len(tasks) < 2:
            return tasks
        
        # Group similar tasks together to reduce context switching
        optimized_tasks = []
        remaining_tasks = tasks.copy()
        
        while remaining_tasks:
            current_task = remaining_tasks.pop(0)
            optimized_tasks.append(current_task)
            
            # Look for similar tasks that can be grouped
            similar_tasks = []
            i = 0
            while i < len(remaining_tasks):
                if (remaining_tasks[i].task_type == current_task.task_type and
                    not self._has_blocking_dependencies(remaining_tasks[i], optimized_tasks)):
                    similar_tasks.append(remaining_tasks.pop(i))
                else:
                    i += 1
            
            # Add similar tasks immediately after current task
            optimized_tasks.extend(similar_tasks)
        
        return optimized_tasks
    
    def _has_blocking_dependencies(self, task: Task, completed_tasks: List[Task]) -> bool:
        """Check if task has dependencies that haven't been completed."""
        completed_ids = {t.task_id for t in completed_tasks}
        return any(dep not in completed_ids for dep in task.dependencies)
    
    def record_workflow_completion(self, workflow: Workflow):
        """Record completed workflow for learning."""
        self.workflow_history[workflow.user_id].append(workflow)
        
        # Update task performance data
        for step in workflow.steps:
            if step.actual_duration is not None:
                task_type = step.task.task_type.value
                self.task_performance_data[workflow.user_id][task_type].append(step.actual_duration)
        
        logger.info(f"Recorded workflow completion for user {workflow.user_id}")
    
    def get_optimization_summary(self, user_id: str) -> Dict[str, Any]:
        """Get optimization summary for a user."""
        user_workflows = self.workflow_history.get(user_id, [])
        
        if not user_workflows:
            return {"message": "No workflow history available"}
        
        # Calculate average efficiency metrics
        recent_workflows = user_workflows[-10:]  # Last 10 workflows
        
        avg_efficiency = np.mean([w.efficiency_score for w in recent_workflows if w.efficiency_score > 0])
        avg_satisfaction = np.mean([w.user_satisfaction for w in recent_workflows if w.user_satisfaction > 0])
        avg_completion_rate = np.mean([w.completion_rate for w in recent_workflows])
        
        # Most common optimization suggestions
        all_suggestions = []
        for suggestions in self.optimization_patterns[user_id]:
            all_suggestions.extend(suggestions)
        
        suggestion_types = defaultdict(int)
        for suggestion in all_suggestions:
            suggestion_types[suggestion.suggestion_type] += 1
        
        return {
            "user_id": user_id,
            "total_workflows": len(user_workflows),
            "recent_avg_efficiency": float(avg_efficiency) if not np.isnan(avg_efficiency) else 0.0,
            "recent_avg_satisfaction": float(avg_satisfaction) if not np.isnan(avg_satisfaction) else 0.0,
            "recent_avg_completion_rate": float(avg_completion_rate) if not np.isnan(avg_completion_rate) else 0.0,
            "common_optimization_areas": dict(suggestion_types),
            "total_optimizations_suggested": len(all_suggestions)
        }