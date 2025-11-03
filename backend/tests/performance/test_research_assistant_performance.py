"""Performance and scalability tests for research assistant system."""

import pytest
import asyncio
import time
import psutil
import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from unittest.mock import Mock
from datetime import datetime, timedelta

from backend.rl.research_assistant.workflow_optimizer import WorkflowOptimizer
from backend.rl.research_assistant.research_workflow_learner import ResearchWorkflowLearner
from backend.rl.models.research_models import (
    ResearchWorkflow, ResearchTask, WorkflowSession,
    OptimizationOpportunity, WorkflowPattern
)
from backend.rl.utils import performance_logger


class TestResearchAssistantPerformance:
    """Performance tests for research assistant system components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.workflow_optimizer = WorkflowOptimizer()
        self.workflow_learner = ResearchWorkflowLearner()
        
        # Performance tracking
        self.process = psutil.Process(os.getpid())
        self.performance_metrics = {}
    
    def measure_performance(self, operation_name: str):
        """Context manager for measuring performance."""
        class PerformanceMeasurer:
            def __init__(self, test_instance, name):
                self.test_instance = test_instance
                self.name = name
                self.start_time = None
                self.start_memory = None
            
            def __enter__(self):
                self.start_time = time.time()
                self.start_memory = self.test_instance.process.memory_info().rss / 1024 / 1024
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                end_time = time.time()
                end_memory = self.test_instance.process.memory_info().rss / 1024 / 1024
                
                metrics = {
                    'duration': end_time - self.start_time,
                    'memory_start': self.start_memory,
                    'memory_end': end_memory,
                    'memory_delta': end_memory - self.start_memory
                }
                
                self.test_instance.performance_metrics[self.name] = metrics
                
                performance_logger.log_processing_time(
                    operation=self.name,
                    component="research_assistant",
                    processing_time=metrics['duration']
                )
        
        return PerformanceMeasurer(self, operation_name)
    
    def create_workflow_sessions(self, count: int, tasks_per_session: int = 5) -> List[WorkflowSession]:
        """Create test workflow sessions."""
        sessions = []
        base_time = datetime.now() - timedelta(days=30)
        
        for i in range(count):
            session = WorkflowSession(
                session_id=f"perf_session_{i:06d}",
                workflow_id=f"workflow_{i % 10}",  # Reuse workflow IDs
                user_id=f"researcher_{i % 50}",   # Reuse user IDs
                start_time=base_time + timedelta(hours=i*2),
                end_time=base_time + timedelta(hours=i*2 + 4),
                tasks_completed=[
                    {
                        "task_id": f"task_{j}",
                        "actual_duration": timedelta(minutes=30 + j*15),
                        "efficiency_score": 0.6 + (j % 4) * 0.1,
                        "quality_score": 0.7 + (j % 3) * 0.1
                    }
                    for j in range(tasks_per_session)
                ],
                success_metrics_achieved={
                    "papers_reviewed": 10 + (i % 20),
                    "insights_generated": 2 + (i % 5)
                },
                bottlenecks_encountered=[
                    {
                        "bottleneck_type": ["search", "analysis", "synthesis"][j % 3],
                        "impact_severity": 0.3 + (j % 3) * 0.2,
                        "time_lost": timedelta(minutes=10 + j*5)
                    }
                    for j in range(i % 3)  # Variable number of bottlenecks
                ]
            )
            sessions.append(session)
        
        return sessions
    
    def create_research_workflow(self, task_count: int) -> ResearchWorkflow:
        """Create test research workflow."""
        tasks = []
        for i in range(task_count):
            task = ResearchTask(
                task_id=f"task_{i:03d}",
                task_type=["search", "analysis", "synthesis", "writing"][i % 4],
                description=f"Research task {i}",
                estimated_duration=timedelta(hours=1 + (i % 4)),
                dependencies=[f"task_{j:03d}" for j in range(max(0, i-2), i)],  # Depend on previous tasks
                priority=i % 5 + 1
            )
            tasks.append(task)
        
        return ResearchWorkflow(
            workflow_id=f"perf_workflow_{task_count}",
            research_domain="machine_learning",
            task_sequence=tasks,
            estimated_duration=timedelta(hours=task_count * 2),
            success_metrics=[
                {"metric": "papers_reviewed", "target": task_count * 5},
                {"metric": "insights_generated", "target": task_count}
            ],
            optimization_opportunities=[]
        )
    
    @pytest.mark.asyncio
    async def test_workflow_efficiency_analysis_performance_small(self):
        """Test workflow efficiency analysis performance with small dataset."""
        sessions = self.create_workflow_sessions(50, 3)
        
        with self.measure_performance("workflow_analysis_small"):
            efficiency_analysis = await self.workflow_optimizer.analyze_workflow_efficiency(sessions)
        
        # Verify results
        assert efficiency_analysis is not None
        assert efficiency_analysis.overall_efficiency > 0
        
        # Performance assertions
        metrics = self.performance_metrics["workflow_analysis_small"]
        assert metrics['duration'] < 2.0, f"Small dataset analysis too slow: {metrics['duration']}s"
        assert metrics['memory_delta'] < 50, f"Memory usage too high: {metrics['memory_delta']}MB"
    
    @pytest.mark.asyncio
    async def test_workflow_efficiency_analysis_performance_large(self):
        """Test workflow efficiency analysis performance with large dataset."""
        sessions = self.create_workflow_sessions(2000, 8)  # Large dataset
        
        with self.measure_performance("workflow_analysis_large"):
            efficiency_analysis = await self.workflow_optimizer.analyze_workflow_efficiency(sessions)
        
        # Verify results
        assert efficiency_analysis is not None
        assert len(efficiency_analysis.bottlenecks) >= 0
        
        # Performance assertions
        metrics = self.performance_metrics["workflow_analysis_large"]
        assert metrics['duration'] < 15.0, f"Large dataset analysis too slow: {metrics['duration']}s"
        assert metrics['memory_delta'] < 200, f"Memory usage too high: {metrics['memory_delta']}MB"
        
        # Calculate throughput
        throughput = len(sessions) / metrics['duration']
        performance_logger.log_throughput(
            component="research_assistant",
            operation="workflow_analysis",
            items_processed=len(sessions),
            time_elapsed=metrics['duration']
        )
        
        assert throughput > 100, f"Analysis throughput too low: {throughput} sessions/sec"
    
    @pytest.mark.asyncio
    async def test_task_sequence_optimization_performance(self):
        """Test task sequence optimization performance."""
        # Create workflows with varying complexity
        workflow_sizes = [10, 50, 100, 200]
        optimization_results = {}
        
        for size in workflow_sizes:
            workflow = self.create_research_workflow(size)
            
            with self.measure_performance(f"task_optimization_{size}"):
                optimized_sequence = await self.workflow_optimizer.optimize_task_sequence(
                    workflow.task_sequence
                )
            
            metrics = self.performance_metrics[f"task_optimization_{size}"]
            optimization_results[size] = {
                "duration": metrics['duration'],
                "memory_delta": metrics['memory_delta'],
                "tasks_per_second": size / metrics['duration']
            }
            
            # Verify results
            assert optimized_sequence is not None
            assert len(optimized_sequence.optimized_tasks) == size
            
            performance_logger.info(
                f"Task optimization performance with {size} tasks",
                task_count=size,
                processing_time=metrics['duration'],
                tasks_per_second=size / metrics['duration']
            )
        
        # Verify scalability
        for size in workflow_sizes:
            result = optimization_results[size]
            assert result["duration"] < size * 0.01, \
                f"Task optimization too slow for {size} tasks: {result['duration']}s"
    
    @pytest.mark.asyncio
    async def test_pattern_learning_performance_batch(self):
        """Test pattern learning performance with batch processing."""
        # Create multiple batches of workflow sessions
        batch_sizes = [100, 500, 1000]
        learning_results = {}
        
        for batch_size in batch_sizes:
            sessions = self.create_workflow_sessions(batch_size, 6)
            
            with self.measure_performance(f"pattern_learning_{batch_size}"):
                workflow_patterns = await self.workflow_learner.learn_from_successful_workflows(sessions)
            
            metrics = self.performance_metrics[f"pattern_learning_{batch_size}"]
            learning_results[batch_size] = {
                "duration": metrics['duration'],
                "sessions_per_second": batch_size / metrics['duration'],
                "patterns_learned": len(workflow_patterns.patterns) if workflow_patterns else 0
            }
            
            # Verify results
            assert workflow_patterns is not None
            assert len(workflow_patterns.patterns) > 0
            
            performance_logger.info(
                f"Pattern learning performance with {batch_size} sessions",
                session_count=batch_size,
                processing_time=metrics['duration'],
                patterns_learned=len(workflow_patterns.patterns)
            )
        
        # Verify reasonable performance scaling
        for batch_size in batch_sizes:
            result = learning_results[batch_size]
            assert result["sessions_per_second"] > 50, \
                f"Pattern learning throughput too low: {result['sessions_per_second']} sessions/sec"
    
    @pytest.mark.asyncio
    async def test_bottleneck_identification_performance(self):
        """Test bottleneck identification performance."""
        # Create sessions with many bottlenecks
        sessions = []
        for i in range(500):
            session = WorkflowSession(
                session_id=f"bottleneck_session_{i:04d}",
                workflow_id=f"workflow_{i % 20}",
                user_id=f"researcher_{i % 100}",
                start_time=datetime.now() - timedelta(hours=i),
                end_time=datetime.now() - timedelta(hours=i-4),
                tasks_completed=[
                    {
                        "task_id": f"task_{j}",
                        "actual_duration": timedelta(minutes=60 + j*30),  # Longer than expected
                        "efficiency_score": 0.4 + (j % 3) * 0.1,  # Lower efficiency
                        "quality_score": 0.6 + (j % 2) * 0.2
                    }
                    for j in range(5)
                ],
                success_metrics_achieved={
                    "papers_reviewed": 5 + (i % 10),  # Lower achievement
                    "insights_generated": 1 + (i % 3)
                },
                bottlenecks_encountered=[
                    {
                        "bottleneck_type": ["search_inefficient", "analysis_paralysis", "synthesis_block"][j % 3],
                        "impact_severity": 0.5 + (j % 3) * 0.2,
                        "time_lost": timedelta(minutes=30 + j*15)
                    }
                    for j in range(3 + (i % 3))  # Multiple bottlenecks per session
                ]
            )
            sessions.append(session)
        
        workflow_analysis_data = {
            "sessions": sessions,
            "workflow": self.create_research_workflow(10),
            "performance_metrics": {
                "average_efficiency": 0.5,
                "completion_rate": 0.7
            }
        }
        
        with self.measure_performance("bottleneck_identification"):
            bottlenecks = await self.workflow_learner.identify_bottlenecks(workflow_analysis_data)
        
        # Verify results
        assert bottlenecks is not None
        assert len(bottlenecks) > 0
        
        # Performance assertions
        metrics = self.performance_metrics["bottleneck_identification"]
        assert metrics['duration'] < 10.0, f"Bottleneck identification too slow: {metrics['duration']}s"
        
        # Should process sessions efficiently
        sessions_per_second = len(sessions) / metrics['duration']
        assert sessions_per_second > 50, f"Bottleneck identification throughput too low: {sessions_per_second} sessions/sec"
    
    @pytest.mark.asyncio
    async def test_workflow_improvement_generation_performance(self):
        """Test workflow improvement generation performance."""
        # Create complex workflows for improvement generation
        workflows = [self.create_research_workflow(20 + i*10) for i in range(10)]
        
        with self.measure_performance("improvement_generation"):
            all_improvements = []
            for workflow in workflows:
                improvements = await self.workflow_optimizer.suggest_workflow_improvements(workflow)
                all_improvements.extend(improvements)
        
        # Verify results
        assert len(all_improvements) > 0
        
        # Performance assertions
        metrics = self.performance_metrics["improvement_generation"]
        assert metrics['duration'] < 8.0, f"Improvement generation too slow: {metrics['duration']}s"
        
        # Calculate throughput
        workflows_per_second = len(workflows) / metrics['duration']
        assert workflows_per_second > 1, f"Improvement generation throughput too low: {workflows_per_second} workflows/sec"
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_processing_performance(self):
        """Test concurrent workflow processing performance."""
        # Create multiple workflows for concurrent processing
        workflows = [self.create_research_workflow(15) for _ in range(20)]
        
        async def process_workflow(workflow):
            # Simulate complete workflow processing
            efficiency_sessions = self.create_workflow_sessions(10, 4)
            efficiency_analysis = await self.workflow_optimizer.analyze_workflow_efficiency(efficiency_sessions)
            improvements = await self.workflow_optimizer.suggest_workflow_improvements(workflow)
            optimized_sequence = await self.workflow_optimizer.optimize_task_sequence(workflow.task_sequence)
            
            return {
                "workflow_id": workflow.workflow_id,
                "efficiency_analysis": efficiency_analysis,
                "improvements": improvements,
                "optimized_sequence": optimized_sequence
            }
        
        with self.measure_performance("concurrent_workflow_processing"):
            # Process workflows concurrently
            tasks = [process_workflow(workflow) for workflow in workflows]
            concurrent_results = await asyncio.gather(*tasks)
        
        # Verify results
        assert len(concurrent_results) == 20
        assert all(result is not None for result in concurrent_results)
        
        # Performance assertions
        metrics = self.performance_metrics["concurrent_workflow_processing"]
        
        # Concurrent processing should be faster than sequential
        sequential_estimate = len(workflows) * 2.0  # Estimated 2s per workflow
        assert metrics['duration'] < sequential_estimate * 0.6, \
            f"Concurrent processing not efficient: {metrics['duration']}s vs estimated {sequential_estimate}s"
        
        # Concurrent throughput should be reasonable
        throughput = len(workflows) / metrics['duration']
        assert throughput > 2, f"Concurrent throughput too low: {throughput} workflows/sec"
    
    @pytest.mark.asyncio
    async def test_real_time_optimization_performance(self):
        """Test real-time optimization performance."""
        # Simulate real-time optimization requests
        optimization_requests = []
        for i in range(100):
            workflow = self.create_research_workflow(8)  # Smaller workflows for real-time
            sessions = self.create_workflow_sessions(5, 3)  # Recent session data
            
            optimization_requests.append({
                "workflow": workflow,
                "sessions": sessions,
                "timestamp": datetime.now() - timedelta(seconds=i)
            })
        
        with self.measure_performance("real_time_optimization"):
            optimization_results = []
            for request in optimization_requests:
                # Real-time optimization pipeline
                start_time = time.time()
                
                efficiency_analysis = await self.workflow_optimizer.analyze_workflow_efficiency(
                    request["sessions"]
                )
                improvements = await self.workflow_optimizer.suggest_workflow_improvements(
                    request["workflow"]
                )
                
                response_time = time.time() - start_time
                optimization_results.append({
                    "response_time": response_time,
                    "efficiency_analysis": efficiency_analysis,
                    "improvements": improvements
                })
        
        # Verify results
        assert len(optimization_results) == 100
        
        # Real-time performance assertions
        metrics = self.performance_metrics["real_time_optimization"]
        avg_response_time = metrics['duration'] / len(optimization_requests)
        
        assert avg_response_time < 0.1, f"Real-time optimization too slow: {avg_response_time}s per request"
        
        # Check individual response times
        response_times = [result["response_time"] for result in optimization_results]
        max_response_time = max(response_times)
        assert max_response_time < 0.2, f"Max response time too high: {max_response_time}s"
        
        # Real-time throughput
        throughput = len(optimization_requests) / metrics['duration']
        assert throughput > 10, f"Real-time throughput too low: {throughput} requests/sec"
    
    @pytest.mark.asyncio
    async def test_memory_efficiency_large_workflow_history(self):
        """Test memory efficiency with large workflow history."""
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large workflow history
        large_session_history = self.create_workflow_sessions(5000, 10)  # Very large history
        
        with self.measure_performance("memory_efficiency_large_history"):
            # Process large history
            efficiency_analysis = await self.workflow_optimizer.analyze_workflow_efficiency(
                large_session_history
            )
            
            # Learn patterns from large history
            workflow_patterns = await self.workflow_learner.learn_from_successful_workflows(
                large_session_history
            )
            
            # Generate improvements based on patterns
            sample_workflow = self.create_research_workflow(20)
            improvements = await self.workflow_optimizer.suggest_workflow_improvements(sample_workflow)
        
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory efficiency assertions
        assert memory_increase < 400, f"Memory increase too high: {memory_increase}MB"
        
        # Memory per session should be reasonable
        memory_per_session = memory_increase / len(large_session_history)
        assert memory_per_session < 0.08, f"Memory per session too high: {memory_per_session}MB"
        
        # Verify processing completed successfully
        assert efficiency_analysis is not None
        assert workflow_patterns is not None
        assert improvements is not None
        
        performance_logger.info(
            "Large workflow history memory efficiency test",
            initial_memory_mb=initial_memory,
            final_memory_mb=final_memory,
            memory_increase_mb=memory_increase,
            session_count=len(large_session_history),
            memory_per_session_kb=memory_per_session * 1024
        )
    
    def test_cpu_intensive_optimization_performance(self):
        """Test CPU performance during intensive optimization operations."""
        import threading
        import queue
        
        cpu_measurements = queue.Queue()
        stop_monitoring = threading.Event()
        
        def monitor_cpu():
            while not stop_monitoring.is_set():
                cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_measurements.put(cpu_percent)
                time.sleep(0.1)
        
        # Start CPU monitoring
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()
        
        try:
            start_time = time.time()
            
            # Perform CPU-intensive optimization operations
            for i in range(50):
                # Simulate complex optimization calculations
                workflow = self.create_research_workflow(30)
                
                # Simulate dependency analysis (CPU intensive)
                dependency_matrix = np.random.rand(30, 30)
                eigenvalues = np.linalg.eigvals(dependency_matrix)
                
                # Simulate optimization search (CPU intensive)
                optimization_space = np.random.rand(100, 30)
                distances = np.linalg.norm(optimization_space, axis=1)
                optimal_indices = np.argsort(distances)[:10]
            
            processing_time = time.time() - start_time
            
        finally:
            stop_monitoring.set()
            monitor_thread.join()
        
        # Analyze CPU usage
        cpu_values = []
        while not cpu_measurements.empty():
            cpu_values.append(cpu_measurements.get())
        
        if cpu_values:
            avg_cpu = sum(cpu_values) / len(cpu_values)
            max_cpu = max(cpu_values)
            
            performance_logger.info(
                "CPU utilization during intensive optimization",
                processing_time=processing_time,
                average_cpu_percent=avg_cpu,
                max_cpu_percent=max_cpu,
                optimization_iterations=50
            )
            
            # CPU utilization should be reasonable
            assert avg_cpu < 85, f"Average CPU usage too high: {avg_cpu}%"
            assert processing_time < 30, f"Intensive optimization too slow: {processing_time}s"


class TestResearchAssistantScalability:
    """Scalability tests for research assistant system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.workflow_optimizer = WorkflowOptimizer()
        self.workflow_learner = ResearchWorkflowLearner()
    
    @pytest.mark.asyncio
    async def test_scalability_workflow_complexity(self):
        """Test scalability with increasing workflow complexity."""
        task_counts = [5, 20, 50, 100, 200]
        scalability_results = {}
        
        for task_count in task_counts:
            # Create workflow with specified complexity
            workflow = ResearchWorkflow(
                workflow_id=f"complex_workflow_{task_count}",
                research_domain="machine_learning",
                task_sequence=[
                    ResearchTask(
                        task_id=f"complex_task_{i:03d}",
                        task_type=["search", "analysis", "synthesis", "writing", "review"][i % 5],
                        description=f"Complex task {i}",
                        estimated_duration=timedelta(hours=1 + (i % 3)),
                        dependencies=[f"complex_task_{j:03d}" for j in range(max(0, i-3), i)],
                        priority=(i % 5) + 1
                    )
                    for i in range(task_count)
                ],
                estimated_duration=timedelta(hours=task_count * 2),
                success_metrics=[{"metric": "completion", "target": 1.0}],
                optimization_opportunities=[]
            )
            
            # Measure optimization time
            start_time = time.time()
            optimized_sequence = await self.workflow_optimizer.optimize_task_sequence(
                workflow.task_sequence
            )
            optimization_time = time.time() - start_time
            
            scalability_results[task_count] = {
                "optimization_time": optimization_time,
                "time_per_task": optimization_time / task_count,
                "complexity_factor": task_count * np.log(task_count)  # Expected complexity
            }
            
            performance_logger.info(
                f"Workflow complexity scalability test with {task_count} tasks",
                task_count=task_count,
                optimization_time=optimization_time,
                time_per_task=optimization_time / task_count
            )
        
        # Analyze scalability
        for i in range(1, len(task_counts)):
            prev_count = task_counts[i-1]
            curr_count = task_counts[i]
            
            prev_time = scalability_results[prev_count]["optimization_time"]
            curr_time = scalability_results[curr_count]["optimization_time"]
            
            # Time should not scale worse than O(n log n)
            time_ratio = curr_time / prev_time
            complexity_ratio = scalability_results[curr_count]["complexity_factor"] / scalability_results[prev_count]["complexity_factor"]
            
            assert time_ratio <= complexity_ratio * 1.5, \
                f"Poor scalability: {curr_count} tasks took {time_ratio:.2f}x time vs {complexity_ratio:.2f}x complexity"
    
    @pytest.mark.asyncio
    async def test_scalability_session_history_size(self):
        """Test scalability with increasing session history size."""
        history_sizes = [100, 500, 1000, 2000, 5000]
        scalability_results = {}
        
        for size in history_sizes:
            # Create workflow sessions
            sessions = []
            base_time = datetime.now() - timedelta(days=size//10)
            
            for i in range(size):
                session = WorkflowSession(
                    session_id=f"history_session_{i:06d}",
                    workflow_id=f"workflow_{i % 50}",
                    user_id=f"researcher_{i % 200}",
                    start_time=base_time + timedelta(hours=i),
                    end_time=base_time + timedelta(hours=i+3),
                    tasks_completed=[
                        {
                            "task_id": f"task_{j}",
                            "actual_duration": timedelta(minutes=45 + j*10),
                            "efficiency_score": 0.6 + (j % 4) * 0.1,
                            "quality_score": 0.7 + (j % 3) * 0.1
                        }
                        for j in range(5)
                    ],
                    success_metrics_achieved={"papers_reviewed": 10 + (i % 15)},
                    bottlenecks_encountered=[]
                )
                sessions.append(session)
            
            # Measure pattern learning time
            start_time = time.time()
            workflow_patterns = await self.workflow_learner.learn_from_successful_workflows(sessions)
            learning_time = time.time() - start_time
            
            scalability_results[size] = {
                "learning_time": learning_time,
                "sessions_per_second": size / learning_time,
                "patterns_learned": len(workflow_patterns.patterns) if workflow_patterns else 0
            }
            
            performance_logger.info(
                f"Session history scalability test with {size} sessions",
                history_size=size,
                learning_time=learning_time,
                sessions_per_second=size / learning_time
            )
        
        # Verify scalability
        for size in history_sizes:
            result = scalability_results[size]
            assert result["sessions_per_second"] > 100, \
                f"Learning throughput too low for {size} sessions: {result['sessions_per_second']} sessions/sec"
    
    @pytest.mark.asyncio
    async def test_scalability_concurrent_users(self):
        """Test scalability with increasing number of concurrent users."""
        user_counts = [5, 10, 25, 50]
        scalability_results = {}
        
        for user_count in user_counts:
            # Create workflows for multiple users
            user_workflows = [
                (
                    f"user_{i:03d}",
                    ResearchWorkflow(
                        workflow_id=f"user_{i:03d}_workflow",
                        research_domain=["ml", "cv", "nlp"][i % 3],
                        task_sequence=[
                            ResearchTask(
                                task_id=f"user_{i:03d}_task_{j}",
                                task_type=["search", "analysis", "synthesis"][j % 3],
                                description=f"Task {j} for user {i}",
                                estimated_duration=timedelta(hours=1),
                                dependencies=[],
                                priority=j + 1
                            )
                            for j in range(10)
                        ],
                        estimated_duration=timedelta(hours=10),
                        success_metrics=[],
                        optimization_opportunities=[]
                    )
                )
                for i in range(user_count)
            ]
            
            async def optimize_user_workflow(user_id, workflow):
                # Simulate user-specific optimization
                sessions = [
                    WorkflowSession(
                        session_id=f"{user_id}_session_{j}",
                        workflow_id=workflow.workflow_id,
                        user_id=user_id,
                        start_time=datetime.now() - timedelta(hours=j*4),
                        end_time=datetime.now() - timedelta(hours=j*4-3),
                        tasks_completed=[
                            {
                                "task_id": f"task_{k}",
                                "actual_duration": timedelta(minutes=60),
                                "efficiency_score": 0.8,
                                "quality_score": 0.9
                            }
                            for k in range(3)
                        ],
                        success_metrics_achieved={},
                        bottlenecks_encountered=[]
                    )
                    for j in range(5)
                ]
                
                efficiency_analysis = await self.workflow_optimizer.analyze_workflow_efficiency(sessions)
                improvements = await self.workflow_optimizer.suggest_workflow_improvements(workflow)
                
                return {
                    "user_id": user_id,
                    "efficiency_analysis": efficiency_analysis,
                    "improvements": improvements
                }
            
            # Measure concurrent processing time
            start_time = time.time()
            tasks = [optimize_user_workflow(user_id, workflow) for user_id, workflow in user_workflows]
            concurrent_results = await asyncio.gather(*tasks)
            processing_time = time.time() - start_time
            
            scalability_results[user_count] = {
                "processing_time": processing_time,
                "users_per_second": user_count / processing_time,
                "avg_time_per_user": processing_time / user_count
            }
            
            performance_logger.info(
                f"Concurrent users scalability test with {user_count} users",
                user_count=user_count,
                processing_time=processing_time,
                users_per_second=user_count / processing_time
            )
        
        # Verify concurrent scalability
        for user_count in user_counts:
            result = scalability_results[user_count]
            assert result["avg_time_per_user"] < 2.0, \
                f"Average time per user too high: {result['avg_time_per_user']}s"
    
    @pytest.mark.asyncio
    async def test_scalability_optimization_search_space(self):
        """Test scalability with increasing optimization search space."""
        search_space_sizes = [10, 50, 100, 500, 1000]
        scalability_results = {}
        
        for space_size in search_space_sizes:
            # Create workflow with large optimization space
            workflow = ResearchWorkflow(
                workflow_id=f"search_space_workflow_{space_size}",
                research_domain="machine_learning",
                task_sequence=[
                    ResearchTask(
                        task_id=f"search_task_{i:04d}",
                        task_type=f"type_{i % 10}",  # Many task types
                        description=f"Search space task {i}",
                        estimated_duration=timedelta(minutes=30 + (i % 60)),
                        dependencies=[f"search_task_{j:04d}" for j in range(max(0, i-5), i) if np.random.rand() > 0.7],
                        priority=(i % 10) + 1
                    )
                    for i in range(space_size)
                ],
                estimated_duration=timedelta(hours=space_size // 10),
                success_metrics=[],
                optimization_opportunities=[]
            )
            
            # Measure optimization time
            start_time = time.time()
            optimized_sequence = await self.workflow_optimizer.optimize_task_sequence(
                workflow.task_sequence
            )
            optimization_time = time.time() - start_time
            
            scalability_results[space_size] = {
                "optimization_time": optimization_time,
                "tasks_per_second": space_size / optimization_time,
                "search_efficiency": space_size / (optimization_time ** 2)  # Efficiency metric
            }
            
            performance_logger.info(
                f"Search space scalability test with {space_size} tasks",
                search_space_size=space_size,
                optimization_time=optimization_time,
                tasks_per_second=space_size / optimization_time
            )
        
        # Verify search space scalability
        for space_size in search_space_sizes:
            result = scalability_results[space_size]
            assert result["optimization_time"] < space_size * 0.01, \
                f"Optimization too slow for search space {space_size}: {result['optimization_time']}s"


if __name__ == "__main__":
    pytest.main([__file__])