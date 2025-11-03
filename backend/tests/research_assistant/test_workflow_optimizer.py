"""Unit tests for workflow optimizer."""

import pytest
import numpy as np
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from backend.rl.research_assistant.workflow_optimizer import (
    WorkflowOptimizer,
    Task,
    TaskType,
    TaskPriority,
    WorkflowStage,
    WorkflowStep,
    Workflow,
    OptimizationSuggestion,
    EfficiencyMetrics
)


class TestTask:
    """Test cases for Task class."""
    
    def test_task_creation(self):
        """Test creating a task."""
        task = Task(
            task_id="task_1",
            task_type=TaskType.LITERATURE_SEARCH,
            priority=TaskPriority.HIGH,
            estimated_duration=2.0,
            dependencies=["task_0"],
            resources_required=["database_access"],
            complexity_score=0.7
        )
        
        assert task.task_id == "task_1"
        assert task.task_type == TaskType.LITERATURE_SEARCH
        assert task.priority == TaskPriority.HIGH
        assert task.estimated_duration == 2.0
        assert task.dependencies == ["task_0"]
        assert task.resources_required == ["database_access"]
        assert task.complexity_score == 0.7
        assert task.user_preference_score == 0.0
        assert isinstance(task.metadata, dict)


class TestWorkflowStep:
    """Test cases for WorkflowStep class."""
    
    def test_workflow_step_creation(self):
        """Test creating a workflow step."""
        task = Task("task_1", TaskType.PAPER_ANALYSIS, TaskPriority.MEDIUM, 1.5)
        step = WorkflowStep(
            step_id="step_1",
            task=task,
            start_time=datetime.now(),
            actual_duration=1.8,
            efficiency_score=0.83,
            user_satisfaction=0.9
        )
        
        assert step.step_id == "step_1"
        assert step.task == task
        assert step.actual_duration == 1.8
        assert step.efficiency_score == 0.83
        assert step.user_satisfaction == 0.9
        assert isinstance(step.bottlenecks, list)


class TestWorkflow:
    """Test cases for Workflow class."""
    
    def create_sample_workflow(self, user_id="user_1", num_steps=3):
        """Create a sample workflow for testing."""
        workflow = Workflow(
            workflow_id="workflow_1",
            user_id=user_id,
            stage=WorkflowStage.RESEARCH,
            total_estimated_duration=6.0,
            total_actual_duration=7.2,
            efficiency_score=0.75,
            completion_rate=0.8,
            user_satisfaction=0.85
        )
        
        for i in range(num_steps):
            task = Task(f"task_{i}", TaskType.LITERATURE_SEARCH, TaskPriority.MEDIUM, 2.0)
            step = WorkflowStep(
                step_id=f"step_{i}",
                task=task,
                start_time=datetime.now() - timedelta(hours=i),
                end_time=datetime.now() - timedelta(hours=i-1) if i < num_steps-1 else None,
                actual_duration=2.4 if i < num_steps-1 else None,
                efficiency_score=0.8,
                user_satisfaction=0.85
            )
            workflow.steps.append(step)
        
        return workflow
    
    def test_workflow_creation(self):
        """Test creating a workflow."""
        workflow = self.create_sample_workflow()
        
        assert workflow.workflow_id == "workflow_1"
        assert workflow.user_id == "user_1"
        assert workflow.stage == WorkflowStage.RESEARCH
        assert len(workflow.steps) == 3
        assert workflow.efficiency_score == 0.75
        assert isinstance(workflow.created_at, datetime)


class TestWorkflowOptimizer:
    """Test cases for WorkflowOptimizer class."""
    
    def create_sample_tasks(self, num_tasks=5):
        """Create sample tasks for testing."""
        tasks = []
        task_types = list(TaskType)
        priorities = list(TaskPriority)
        
        for i in range(num_tasks):
            task = Task(
                task_id=f"task_{i}",
                task_type=task_types[i % len(task_types)],
                priority=priorities[i % len(priorities)],
                estimated_duration=np.random.uniform(1.0, 4.0),
                dependencies=[f"task_{j}" for j in range(max(0, i-2), i)],
                complexity_score=np.random.uniform(0.3, 1.0),
                user_preference_score=np.random.uniform(0.0, 1.0)
            )
            tasks.append(task)
        
        return tasks
    
    @pytest.mark.asyncio
    async def test_analyze_workflow_efficiency(self):
        """Test workflow efficiency analysis."""
        optimizer = WorkflowOptimizer()
        
        # Create workflow with completed steps
        workflow = Workflow(
            workflow_id="test_workflow",
            user_id="user_1",
            stage=WorkflowStage.ANALYSIS,
            total_estimated_duration=6.0,
            total_actual_duration=7.0
        )
        
        # Add completed steps
        for i in range(3):
            task = Task(f"task_{i}", TaskType.PAPER_ANALYSIS, TaskPriority.MEDIUM, 2.0)
            step = WorkflowStep(
                step_id=f"step_{i}",
                task=task,
                start_time=datetime.now() - timedelta(hours=2),
                end_time=datetime.now() - timedelta(hours=1),
                actual_duration=2.3,
                efficiency_score=0.87,
                user_satisfaction=0.8,
                bottlenecks=["resource_contention"] if i == 1 else []
            )
            workflow.steps.append(step)
        
        metrics = await optimizer.analyze_workflow_efficiency(workflow)
        
        assert isinstance(metrics, EfficiencyMetrics)
        assert 0.0 <= metrics.time_efficiency <= 1.0
        assert 0.0 <= metrics.resource_utilization <= 1.0
        assert 0.0 <= metrics.task_completion_rate <= 1.0
        assert 0.0 <= metrics.user_satisfaction <= 1.0
        assert 0.0 <= metrics.bottleneck_frequency <= 1.0
        assert 0.0 <= metrics.overall_efficiency <= 1.0
        
        # Check specific calculations
        assert metrics.task_completion_rate == 1.0  # All steps completed
        assert metrics.user_satisfaction == 0.8  # Average satisfaction
        assert metrics.bottleneck_frequency == 1/3  # One step has bottlenecks
    
    @pytest.mark.asyncio
    async def test_suggest_workflow_improvements(self):
        """Test workflow improvement suggestions."""
        optimizer = WorkflowOptimizer()
        
        # Create workflow with inefficiencies
        workflow = Workflow("test_workflow", "user_1", WorkflowStage.RESEARCH)
        
        # Add steps with different task types (high context switching)
        task_types = [TaskType.LITERATURE_SEARCH, TaskType.PAPER_ANALYSIS, 
                     TaskType.LITERATURE_SEARCH, TaskType.WRITING]
        
        for i, task_type in enumerate(task_types):
            task = Task(f"task_{i}", task_type, TaskPriority.MEDIUM, 2.0)
            step = WorkflowStep(
                step_id=f"step_{i}",
                task=task,
                actual_duration=3.0,  # Longer than estimated
                efficiency_score=0.6,
                user_satisfaction=0.7,
                bottlenecks=["resource_contention"] if i % 2 == 0 else []
            )
            workflow.steps.append(step)
        
        user_preferences = {
            "literature_search": 0.8,
            "paper_analysis": 0.6,
            "writing": 0.2  # Low preference
        }
        
        suggestions = await optimizer.suggest_workflow_improvements(workflow, user_preferences)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Check suggestion structure
        for suggestion in suggestions:
            assert isinstance(suggestion, OptimizationSuggestion)
            assert suggestion.suggestion_id
            assert suggestion.suggestion_type
            assert suggestion.description
            assert 0.0 <= suggestion.expected_improvement <= 1.0
            assert 0.0 <= suggestion.confidence <= 1.0
            assert suggestion.implementation_effort in ["low", "medium", "high"]
            assert isinstance(suggestion.affected_tasks, list)
            assert suggestion.rationale
        
        # Should suggest context switching reduction
        context_suggestions = [s for s in suggestions if "context" in s.suggestion_type]
        assert len(context_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_optimize_task_sequence(self):
        """Test task sequence optimization."""
        optimizer = WorkflowOptimizer()
        
        # Create tasks with dependencies
        tasks = [
            Task("task_1", TaskType.LITERATURE_SEARCH, TaskPriority.HIGH, 2.0, []),
            Task("task_2", TaskType.PAPER_ANALYSIS, TaskPriority.MEDIUM, 3.0, ["task_1"]),
            Task("task_3", TaskType.DATA_EXTRACTION, TaskPriority.LOW, 1.5, ["task_1"]),
            Task("task_4", TaskType.SYNTHESIS, TaskPriority.HIGH, 2.5, ["task_2", "task_3"]),
            Task("task_5", TaskType.WRITING, TaskPriority.MEDIUM, 4.0, ["task_4"])
        ]
        
        constraints = {"max_parallel_tasks": 2}
        
        optimized_sequence = await optimizer.optimize_task_sequence(tasks, constraints)
        
        assert len(optimized_sequence) == len(tasks)
        assert all(isinstance(task, Task) for task in optimized_sequence)
        
        # Check that dependencies are respected
        task_positions = {task.task_id: i for i, task in enumerate(optimized_sequence)}
        
        for task in optimized_sequence:
            for dependency in task.dependencies:
                assert task_positions[dependency] < task_positions[task.task_id]
        
        # First task should have no dependencies
        assert len(optimized_sequence[0].dependencies) == 0
    
    @pytest.mark.asyncio
    async def test_calculate_time_efficiency(self):
        """Test time efficiency calculation."""
        optimizer = WorkflowOptimizer()
        
        workflow = Workflow("test", "user_1", WorkflowStage.ANALYSIS)
        
        # Add steps with known durations
        steps_data = [
            (2.0, 2.0),  # Perfect estimate
            (3.0, 2.5),  # Better than estimate
            (1.5, 2.0),  # Worse than estimate
        ]
        
        for i, (estimated, actual) in enumerate(steps_data):
            task = Task(f"task_{i}", TaskType.PAPER_ANALYSIS, TaskPriority.MEDIUM, estimated)
            step = WorkflowStep(f"step_{i}", task, actual_duration=actual)
            workflow.steps.append(step)
        
        time_efficiency = await optimizer._calculate_time_efficiency(workflow)
        
        # Expected: (2.0 + 3.0 + 1.5) / (2.0 + 2.5 + 2.0) = 6.5 / 6.5 = 1.0
        # But actual calculation: min(1.0, 6.5 / 6.5) = 1.0
        assert isinstance(time_efficiency, float)
        assert 0.0 <= time_efficiency <= 1.0
    
    @pytest.mark.asyncio
    async def test_calculate_resource_utilization(self):
        """Test resource utilization calculation."""
        optimizer = WorkflowOptimizer()
        
        workflow = Workflow("test", "user_1", WorkflowStage.RESEARCH)
        
        # Add steps with resource requirements
        resources_data = [
            (["database", "compute"], 2.0),
            (["database"], 1.5),
            (["compute", "storage"], 3.0),
        ]
        
        for i, (resources, duration) in enumerate(resources_data):
            task = Task(f"task_{i}", TaskType.DATA_EXTRACTION, TaskPriority.MEDIUM, 
                       duration, resources_required=resources)
            step = WorkflowStep(f"step_{i}", task, actual_duration=duration)
            workflow.steps.append(step)
        
        utilization = await optimizer._calculate_resource_utilization(workflow)
        
        assert isinstance(utilization, float)
        assert 0.0 <= utilization <= 1.0
    
    @pytest.mark.asyncio
    async def test_calculate_completion_rate(self):
        """Test completion rate calculation."""
        optimizer = WorkflowOptimizer()
        
        workflow = Workflow("test", "user_1", WorkflowStage.WRITING)
        
        # Add mix of completed and incomplete steps
        for i in range(5):
            task = Task(f"task_{i}", TaskType.WRITING, TaskPriority.MEDIUM, 2.0)
            step = WorkflowStep(
                f"step_{i}", 
                task, 
                end_time=datetime.now() if i < 3 else None  # First 3 completed
            )
            workflow.steps.append(step)
        
        completion_rate = await optimizer._calculate_completion_rate(workflow)
        
        assert completion_rate == 0.6  # 3 out of 5 completed
    
    @pytest.mark.asyncio
    async def test_calculate_context_switch_penalty(self):
        """Test context switch penalty calculation."""
        optimizer = WorkflowOptimizer()
        
        workflow = Workflow("test", "user_1", WorkflowStage.ANALYSIS)
        
        # Create sequence with high context switching
        task_types = [
            TaskType.LITERATURE_SEARCH,
            TaskType.PAPER_ANALYSIS,
            TaskType.LITERATURE_SEARCH,  # Switch back
            TaskType.WRITING,
            TaskType.PAPER_ANALYSIS      # Switch again
        ]
        
        for i, task_type in enumerate(task_types):
            task = Task(f"task_{i}", task_type, TaskPriority.MEDIUM, 2.0)
            step = WorkflowStep(f"step_{i}", task)
            workflow.steps.append(step)
        
        penalty = await optimizer._calculate_context_switch_penalty(workflow)
        
        # Should have 4 switches out of 4 possible = 1.0
        assert penalty == 1.0
    
    @pytest.mark.asyncio
    async def test_build_dependency_graph(self):
        """Test dependency graph building."""
        optimizer = WorkflowOptimizer()
        
        tasks = [
            Task("A", TaskType.LITERATURE_SEARCH, TaskPriority.HIGH, 1.0, []),
            Task("B", TaskType.PAPER_ANALYSIS, TaskPriority.MEDIUM, 2.0, ["A"]),
            Task("C", TaskType.DATA_EXTRACTION, TaskPriority.LOW, 1.5, ["A"]),
            Task("D", TaskType.SYNTHESIS, TaskPriority.HIGH, 3.0, ["B", "C"])
        ]
        
        graph = await optimizer._build_dependency_graph(tasks)
        
        assert graph["A"] == ["B", "C"]
        assert graph["B"] == ["D"]
        assert graph["C"] == ["D"]
        assert "D" not in graph  # No dependents
    
    def test_record_workflow_completion(self):
        """Test recording workflow completion."""
        optimizer = WorkflowOptimizer()
        
        workflow = Workflow("test", "user_1", WorkflowStage.FINALIZATION)
        
        # Add completed steps
        for i in range(3):
            task = Task(f"task_{i}", TaskType.WRITING, TaskPriority.MEDIUM, 2.0)
            step = WorkflowStep(f"step_{i}", task, actual_duration=2.5)
            workflow.steps.append(step)
        
        optimizer.record_workflow_completion(workflow)
        
        assert len(optimizer.workflow_history["user_1"]) == 1
        assert optimizer.workflow_history["user_1"][0] == workflow
        
        # Check task performance data
        assert "writing" in optimizer.task_performance_data["user_1"]
        assert len(optimizer.task_performance_data["user_1"]["writing"]) == 3
    
    def test_get_optimization_summary(self):
        """Test getting optimization summary."""
        optimizer = WorkflowOptimizer()
        
        # Add some workflow history
        for i in range(3):
            workflow = Workflow(
                f"workflow_{i}", 
                "user_1", 
                WorkflowStage.FINALIZATION,
                efficiency_score=0.8 + i * 0.05,
                user_satisfaction=0.75 + i * 0.1,
                completion_rate=0.9
            )
            optimizer.workflow_history["user_1"].append(workflow)
        
        summary = optimizer.get_optimization_summary("user_1")
        
        assert summary["user_id"] == "user_1"
        assert summary["total_workflows"] == 3
        assert isinstance(summary["recent_avg_efficiency"], float)
        assert isinstance(summary["recent_avg_satisfaction"], float)
        assert isinstance(summary["recent_avg_completion_rate"], float)
        assert isinstance(summary["common_optimization_areas"], dict)
    
    def test_get_optimization_summary_no_history(self):
        """Test getting optimization summary with no history."""
        optimizer = WorkflowOptimizer()
        
        summary = optimizer.get_optimization_summary("new_user")
        
        assert "message" in summary
        assert summary["message"] == "No workflow history available"
    
    @pytest.mark.asyncio
    async def test_empty_workflow_handling(self):
        """Test handling of empty workflows."""
        optimizer = WorkflowOptimizer()
        
        empty_workflow = Workflow("empty", "user_1", WorkflowStage.PLANNING)
        
        metrics = await optimizer.analyze_workflow_efficiency(empty_workflow)
        
        # Should handle empty workflow gracefully
        assert metrics.time_efficiency == 0.0
        assert metrics.resource_utilization == 0.0
        assert metrics.task_completion_rate == 0.0
        assert metrics.user_satisfaction == 0.0
        assert metrics.bottleneck_frequency == 0.0
        assert metrics.context_switch_penalty == 0.0
        assert metrics.overall_efficiency == 0.0
    
    @pytest.mark.asyncio
    async def test_single_task_optimization(self):
        """Test optimization with single task."""
        optimizer = WorkflowOptimizer()
        
        single_task = [Task("task_1", TaskType.LITERATURE_SEARCH, TaskPriority.HIGH, 2.0)]
        constraints = {}
        
        optimized = await optimizer.optimize_task_sequence(single_task, constraints)
        
        assert len(optimized) == 1
        assert optimized[0] == single_task[0]
    
    @pytest.mark.asyncio
    async def test_circular_dependency_handling(self):
        """Test handling of circular dependencies."""
        optimizer = WorkflowOptimizer()
        
        # Create tasks with circular dependency (should be handled gracefully)
        tasks = [
            Task("A", TaskType.LITERATURE_SEARCH, TaskPriority.HIGH, 1.0, ["B"]),
            Task("B", TaskType.PAPER_ANALYSIS, TaskPriority.MEDIUM, 2.0, ["A"])
        ]
        
        constraints = {}
        
        # Should not crash and return some ordering
        result = await optimizer.optimize_task_sequence(tasks, constraints)
        
        assert len(result) <= len(tasks)  # May filter out circular dependencies
    
    @pytest.mark.asyncio
    async def test_priority_based_ordering(self):
        """Test that high priority tasks are ordered first when possible."""
        optimizer = WorkflowOptimizer()
        
        tasks = [
            Task("low", TaskType.LITERATURE_SEARCH, TaskPriority.LOW, 1.0, []),
            Task("high", TaskType.PAPER_ANALYSIS, TaskPriority.HIGH, 2.0, []),
            Task("medium", TaskType.DATA_EXTRACTION, TaskPriority.MEDIUM, 1.5, [])
        ]
        
        constraints = {}
        
        optimized = await optimizer.optimize_task_sequence(tasks, constraints)
        
        # High priority task should come first
        assert optimized[0].task_id == "high"
        assert optimized[0].priority == TaskPriority.HIGH