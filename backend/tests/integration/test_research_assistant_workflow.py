"""End-to-end integration tests for research assistant workflow."""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from backend.rl.research_assistant.workflow_optimizer import WorkflowOptimizer
from backend.rl.research_assistant.research_workflow_learner import ResearchWorkflowLearner
from backend.rl.models.research_models import (
    ResearchWorkflow, ResearchTask, WorkflowSession,
    OptimizationOpportunity, WorkflowPattern, BestPractice
)
from backend.rl.utils import research_assistant_logger, handle_errors
from backend.rl.exceptions.advanced_exceptions import ResearchAssistantError


class TestResearchAssistantWorkflowIntegration:
    """Integration tests for complete research assistant workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.workflow_optimizer = WorkflowOptimizer()
        self.workflow_learner = ResearchWorkflowLearner()
        
        # Create test research workflow
        self.test_workflow = ResearchWorkflow(
            workflow_id="test_workflow_001",
            research_domain="machine_learning",
            task_sequence=[
                ResearchTask(
                    task_id="task_001",
                    task_type="literature_search",
                    description="Search for relevant papers",
                    estimated_duration=timedelta(hours=2),
                    dependencies=[],
                    priority=1
                ),
                ResearchTask(
                    task_id="task_002",
                    task_type="paper_analysis",
                    description="Analyze selected papers",
                    estimated_duration=timedelta(hours=4),
                    dependencies=["task_001"],
                    priority=2
                ),
                ResearchTask(
                    task_id="task_003",
                    task_type="synthesis",
                    description="Synthesize findings",
                    estimated_duration=timedelta(hours=3),
                    dependencies=["task_002"],
                    priority=3
                )
            ],
            estimated_duration=timedelta(hours=9),
            success_metrics=[
                {"metric": "papers_reviewed", "target": 20},
                {"metric": "insights_generated", "target": 5}
            ],
            optimization_opportunities=[]
        )
    
    @pytest.mark.asyncio
    async def test_complete_research_assistant_workflow_success(self):
        """Test complete research assistant workflow from analysis to optimization."""
        # Step 1: Analyze workflow efficiency
        workflow_sessions = [
            WorkflowSession(
                session_id="session_001",
                workflow_id=self.test_workflow.workflow_id,
                user_id="researcher_001",
                start_time=datetime.now() - timedelta(hours=10),
                end_time=datetime.now() - timedelta(hours=1),
                tasks_completed=[
                    {
                        "task_id": "task_001",
                        "actual_duration": timedelta(hours=2.5),
                        "efficiency_score": 0.8,
                        "quality_score": 0.9
                    },
                    {
                        "task_id": "task_002",
                        "actual_duration": timedelta(hours=5),
                        "efficiency_score": 0.7,
                        "quality_score": 0.85
                    },
                    {
                        "task_id": "task_003",
                        "actual_duration": timedelta(hours=2.5),
                        "efficiency_score": 0.9,
                        "quality_score": 0.95
                    }
                ],
                success_metrics_achieved={
                    "papers_reviewed": 18,
                    "insights_generated": 6
                },
                bottlenecks_encountered=[
                    {"task_id": "task_002", "bottleneck_type": "information_overload"}
                ]
            )
        ]
        
        efficiency_analysis = await self.workflow_optimizer.analyze_workflow_efficiency(
            workflow_sessions
        )
        
        assert efficiency_analysis is not None
        assert efficiency_analysis.overall_efficiency > 0
        assert efficiency_analysis.task_efficiencies is not None
        assert len(efficiency_analysis.bottlenecks) > 0
        assert efficiency_analysis.improvement_potential > 0
        
        # Step 2: Generate workflow improvements
        workflow_improvements = await self.workflow_optimizer.suggest_workflow_improvements(
            self.test_workflow
        )
        
        assert workflow_improvements is not None
        assert len(workflow_improvements) > 0
        
        for improvement in workflow_improvements:
            assert improvement.improvement_type is not None
            assert improvement.expected_benefit > 0
            assert improvement.implementation_effort > 0
            assert improvement.confidence > 0
        
        # Step 3: Optimize task sequence
        optimized_sequence = await self.workflow_optimizer.optimize_task_sequence(
            self.test_workflow.task_sequence
        )
        
        assert optimized_sequence is not None
        assert optimized_sequence.optimized_tasks is not None
        assert len(optimized_sequence.optimized_tasks) == len(self.test_workflow.task_sequence)
        assert optimized_sequence.efficiency_improvement >= 0
        assert optimized_sequence.optimization_rationale is not None
        
        # Step 4: Learn from successful workflows
        successful_workflows = [workflow_sessions[0]]  # Treat as successful
        
        workflow_patterns = await self.workflow_learner.learn_from_successful_workflows(
            successful_workflows
        )
        
        assert workflow_patterns is not None
        assert len(workflow_patterns.patterns) > 0
        assert workflow_patterns.confidence > 0
        assert workflow_patterns.applicability_scope is not None
        
        # Step 5: Extract best practices
        domain_workflows = [workflow_sessions[0]]
        
        best_practices = await self.workflow_learner.extract_best_practices(
            domain_workflows
        )
        
        assert best_practices is not None
        assert len(best_practices) > 0
        
        for practice in best_practices:
            assert practice.practice_type is not None
            assert practice.description is not None
            assert practice.effectiveness_score > 0
            assert practice.applicability_conditions is not None
    
    @pytest.mark.asyncio
    async def test_research_assistant_workflow_with_bottleneck_identification(self):
        """Test research assistant workflow with bottleneck identification and resolution."""
        # Create workflow session with multiple bottlenecks
        bottleneck_session = WorkflowSession(
            session_id="bottleneck_session_001",
            workflow_id=self.test_workflow.workflow_id,
            user_id="researcher_002",
            start_time=datetime.now() - timedelta(hours=12),
            end_time=datetime.now() - timedelta(hours=2),
            tasks_completed=[
                {
                    "task_id": "task_001",
                    "actual_duration": timedelta(hours=4),  # 2x expected
                    "efficiency_score": 0.5,
                    "quality_score": 0.7
                },
                {
                    "task_id": "task_002",
                    "actual_duration": timedelta(hours=6),  # 1.5x expected
                    "efficiency_score": 0.6,
                    "quality_score": 0.8
                }
            ],
            success_metrics_achieved={
                "papers_reviewed": 12,  # Below target
                "insights_generated": 3   # Below target
            },
            bottlenecks_encountered=[
                {
                    "task_id": "task_001",
                    "bottleneck_type": "search_strategy_inefficient",
                    "impact_severity": 0.8,
                    "time_lost": timedelta(hours=2)
                },
                {
                    "task_id": "task_002",
                    "bottleneck_type": "analysis_paralysis",
                    "impact_severity": 0.6,
                    "time_lost": timedelta(hours=1.5)
                }
            ]
        )
        
        # Identify bottlenecks
        workflow_analysis_data = {
            "sessions": [bottleneck_session],
            "workflow": self.test_workflow,
            "performance_metrics": {
                "average_efficiency": 0.55,
                "completion_rate": 0.67
            }
        }
        
        bottlenecks = await self.workflow_learner.identify_bottlenecks(workflow_analysis_data)
        
        assert bottlenecks is not None
        assert len(bottlenecks) >= 2
        
        # Verify bottleneck details
        search_bottleneck = next(
            (b for b in bottlenecks if b.bottleneck_type == "search_strategy_inefficient"),
            None
        )
        assert search_bottleneck is not None
        assert search_bottleneck.severity > 0.5
        assert search_bottleneck.frequency > 0
        
        analysis_bottleneck = next(
            (b for b in bottlenecks if b.bottleneck_type == "analysis_paralysis"),
            None
        )
        assert analysis_bottleneck is not None
        assert analysis_bottleneck.resolution_strategies is not None
        assert len(analysis_bottleneck.resolution_strategies) > 0
        
        # Generate bottleneck resolution strategies
        resolution_strategies = await self.workflow_optimizer.generate_bottleneck_resolutions(
            bottlenecks
        )
        
        assert resolution_strategies is not None
        assert len(resolution_strategies) > 0
        
        for strategy in resolution_strategies:
            assert strategy.bottleneck_type is not None
            assert strategy.resolution_approach is not None
            assert strategy.expected_improvement > 0
            assert strategy.implementation_complexity > 0
    
    @pytest.mark.asyncio
    async def test_research_assistant_workflow_with_domain_adaptation(self):
        """Test research assistant workflow with domain-specific adaptation."""
        # Create workflows from different research domains
        ml_workflow = self.test_workflow  # Machine learning domain
        
        biology_workflow = ResearchWorkflow(
            workflow_id="biology_workflow_001",
            research_domain="biology",
            task_sequence=[
                ResearchTask(
                    task_id="bio_task_001",
                    task_type="hypothesis_formation",
                    description="Form research hypothesis",
                    estimated_duration=timedelta(hours=1),
                    dependencies=[],
                    priority=1
                ),
                ResearchTask(
                    task_id="bio_task_002",
                    task_type="experiment_design",
                    description="Design experiments",
                    estimated_duration=timedelta(hours=3),
                    dependencies=["bio_task_001"],
                    priority=2
                ),
                ResearchTask(
                    task_id="bio_task_003",
                    task_type="data_collection",
                    description="Collect experimental data",
                    estimated_duration=timedelta(hours=8),
                    dependencies=["bio_task_002"],
                    priority=3
                )
            ],
            estimated_duration=timedelta(hours=12),
            success_metrics=[
                {"metric": "experiments_completed", "target": 5},
                {"metric": "data_points_collected", "target": 1000}
            ],
            optimization_opportunities=[]
        )
        
        # Create domain-specific workflow sessions
        ml_sessions = [
            WorkflowSession(
                session_id="ml_session_001",
                workflow_id=ml_workflow.workflow_id,
                user_id="ml_researcher_001",
                start_time=datetime.now() - timedelta(days=1),
                end_time=datetime.now() - timedelta(hours=12),
                tasks_completed=[
                    {
                        "task_id": "task_001",
                        "actual_duration": timedelta(hours=2),
                        "efficiency_score": 0.9,
                        "quality_score": 0.85
                    }
                ],
                success_metrics_achieved={"papers_reviewed": 25},
                bottlenecks_encountered=[]
            )
        ]
        
        biology_sessions = [
            WorkflowSession(
                session_id="bio_session_001",
                workflow_id=biology_workflow.workflow_id,
                user_id="bio_researcher_001",
                start_time=datetime.now() - timedelta(days=2),
                end_time=datetime.now() - timedelta(days=1),
                tasks_completed=[
                    {
                        "task_id": "bio_task_001",
                        "actual_duration": timedelta(hours=1.5),
                        "efficiency_score": 0.8,
                        "quality_score": 0.9
                    }
                ],
                success_metrics_achieved={"experiments_completed": 3},
                bottlenecks_encountered=[]
            )
        ]
        
        # Learn domain-specific patterns
        ml_patterns = await self.workflow_learner.learn_from_successful_workflows(ml_sessions)
        biology_patterns = await self.workflow_learner.learn_from_successful_workflows(biology_sessions)
        
        assert ml_patterns.domain == "machine_learning"
        assert biology_patterns.domain == "biology"
        
        # Verify domain-specific adaptations
        assert ml_patterns.patterns != biology_patterns.patterns
        
        # Apply domain-specific optimizations
        ml_optimizations = await self.workflow_optimizer.apply_domain_specific_optimizations(
            ml_workflow, ml_patterns
        )
        
        biology_optimizations = await self.workflow_optimizer.apply_domain_specific_optimizations(
            biology_workflow, biology_patterns
        )
        
        assert ml_optimizations is not None
        assert biology_optimizations is not None
        assert ml_optimizations.optimization_strategies != biology_optimizations.optimization_strategies
    
    @pytest.mark.asyncio
    async def test_research_assistant_workflow_with_collaborative_patterns(self):
        """Test research assistant workflow with collaborative research patterns."""
        # Create collaborative workflow session
        collaborative_session = WorkflowSession(
            session_id="collab_session_001",
            workflow_id=self.test_workflow.workflow_id,
            user_id="team_lead_001",
            start_time=datetime.now() - timedelta(hours=8),
            end_time=datetime.now() - timedelta(hours=1),
            tasks_completed=[
                {
                    "task_id": "task_001",
                    "actual_duration": timedelta(hours=1),  # Faster due to collaboration
                    "efficiency_score": 0.95,
                    "quality_score": 0.9,
                    "collaboration_metrics": {
                        "team_members_involved": 3,
                        "knowledge_sharing_events": 5,
                        "parallel_work_percentage": 0.7
                    }
                },
                {
                    "task_id": "task_002",
                    "actual_duration": timedelta(hours=3),
                    "efficiency_score": 0.85,
                    "quality_score": 0.95,
                    "collaboration_metrics": {
                        "team_members_involved": 2,
                        "knowledge_sharing_events": 8,
                        "parallel_work_percentage": 0.5
                    }
                }
            ],
            success_metrics_achieved={
                "papers_reviewed": 30,  # Higher due to team effort
                "insights_generated": 8
            },
            bottlenecks_encountered=[],
            collaboration_data={
                "team_size": 3,
                "coordination_overhead": 0.1,
                "knowledge_synergy_score": 0.8
            }
        )
        
        # Learn collaborative patterns
        collaborative_patterns = await self.workflow_learner.learn_collaborative_patterns(
            [collaborative_session]
        )
        
        assert collaborative_patterns is not None
        assert collaborative_patterns.team_size_optimization is not None
        assert collaborative_patterns.coordination_strategies is not None
        assert collaborative_patterns.knowledge_sharing_patterns is not None
        
        # Apply collaborative optimizations
        collaborative_optimizations = await self.workflow_optimizer.optimize_for_collaboration(
            self.test_workflow, collaborative_patterns
        )
        
        assert collaborative_optimizations is not None
        assert collaborative_optimizations.parallel_task_opportunities is not None
        assert collaborative_optimizations.coordination_improvements is not None
        assert collaborative_optimizations.expected_efficiency_gain > 0
    
    @pytest.mark.asyncio
    async def test_research_assistant_workflow_error_recovery(self):
        """Test research assistant workflow error handling and recovery."""
        # Test with invalid workflow data
        invalid_workflow = ResearchWorkflow(
            workflow_id="invalid_workflow",
            research_domain="",  # Empty domain
            task_sequence=[],    # No tasks
            estimated_duration=timedelta(hours=-1),  # Invalid duration
            success_metrics=[],
            optimization_opportunities=[]
        )
        
        # Should handle invalid workflow gracefully
        with pytest.raises(ResearchAssistantError):
            await self.workflow_optimizer.analyze_workflow_efficiency([])
        
        # Test error recovery with fallback strategies
        @handle_errors(
            component="research_assistant",
            recovery_strategy="fallback",
            fallback_function=lambda e, ctx: {"fallback": True, "error": str(e)}
        )
        async def optimize_with_fallback():
            raise ResearchAssistantError("Optimization service unavailable")
        
        result = await optimize_with_fallback()
        assert result["fallback"] is True
        assert "Optimization service unavailable" in result["error"]
    
    @pytest.mark.asyncio
    async def test_research_assistant_workflow_performance_monitoring(self):
        """Test research assistant workflow with performance monitoring."""
        import time
        
        # Create large-scale workflow data for performance testing
        large_workflow_sessions = [
            WorkflowSession(
                session_id=f"perf_session_{i:03d}",
                workflow_id=self.test_workflow.workflow_id,
                user_id=f"researcher_{i:03d}",
                start_time=datetime.now() - timedelta(hours=24-i),
                end_time=datetime.now() - timedelta(hours=20-i),
                tasks_completed=[
                    {
                        "task_id": f"task_{j:03d}",
                        "actual_duration": timedelta(minutes=30 + j*10),
                        "efficiency_score": 0.7 + (j % 3) * 0.1,
                        "quality_score": 0.8 + (j % 2) * 0.1
                    }
                    for j in range(5)
                ],
                success_metrics_achieved={
                    "papers_reviewed": 15 + i,
                    "insights_generated": 3 + (i % 3)
                },
                bottlenecks_encountered=[]
            )
            for i in range(100)  # Large dataset
        ]
        
        # Measure performance of workflow analysis
        start_time = time.time()
        efficiency_analysis = await self.workflow_optimizer.analyze_workflow_efficiency(
            large_workflow_sessions
        )
        analysis_time = time.time() - start_time
        
        # Measure performance of pattern learning
        start_time = time.time()
        workflow_patterns = await self.workflow_learner.learn_from_successful_workflows(
            large_workflow_sessions
        )
        learning_time = time.time() - start_time
        
        # Log performance metrics
        research_assistant_logger.info(
            "Research assistant workflow performance",
            analysis_time=analysis_time,
            learning_time=learning_time,
            sessions_processed=len(large_workflow_sessions),
            patterns_learned=len(workflow_patterns.patterns)
        )
        
        # Verify performance is acceptable
        assert analysis_time < 5.0, f"Workflow analysis too slow: {analysis_time}s"
        assert learning_time < 3.0, f"Pattern learning too slow: {learning_time}s"
        
        # Verify results quality
        assert efficiency_analysis is not None
        assert workflow_patterns is not None
        assert len(workflow_patterns.patterns) > 0
    
    @pytest.mark.asyncio
    async def test_research_assistant_workflow_adaptive_learning(self):
        """Test research assistant workflow with adaptive learning capabilities."""
        # Simulate evolving research patterns over time
        time_periods = [
            ("early", datetime.now() - timedelta(days=30)),
            ("middle", datetime.now() - timedelta(days=15)),
            ("recent", datetime.now() - timedelta(days=5))
        ]
        
        adaptive_sessions = []
        
        for period_name, base_time in time_periods:
            # Create sessions with evolving patterns
            for i in range(10):
                session = WorkflowSession(
                    session_id=f"{period_name}_session_{i:02d}",
                    workflow_id=self.test_workflow.workflow_id,
                    user_id=f"adaptive_researcher_{i:02d}",
                    start_time=base_time + timedelta(hours=i),
                    end_time=base_time + timedelta(hours=i+4),
                    tasks_completed=[
                        {
                            "task_id": "task_001",
                            "actual_duration": timedelta(hours=2 - (0.1 * len(adaptive_sessions))),  # Improving over time
                            "efficiency_score": 0.6 + (0.01 * len(adaptive_sessions)),  # Improving
                            "quality_score": 0.7 + (0.005 * len(adaptive_sessions))   # Improving
                        }
                    ],
                    success_metrics_achieved={
                        "papers_reviewed": 10 + len(adaptive_sessions),  # Increasing
                        "insights_generated": 2 + (len(adaptive_sessions) // 10)
                    },
                    bottlenecks_encountered=[],
                    temporal_context={
                        "period": period_name,
                        "experience_level": len(adaptive_sessions) // 10
                    }
                )
                adaptive_sessions.append(session)
        
        # Learn adaptive patterns
        adaptive_patterns = await self.workflow_learner.learn_adaptive_patterns(
            adaptive_sessions
        )
        
        assert adaptive_patterns is not None
        assert adaptive_patterns.temporal_evolution is not None
        assert adaptive_patterns.learning_trajectory is not None
        assert adaptive_patterns.adaptation_rate > 0
        
        # Verify learning progression
        assert adaptive_patterns.learning_trajectory.initial_efficiency < adaptive_patterns.learning_trajectory.final_efficiency
        assert adaptive_patterns.learning_trajectory.improvement_rate > 0
        
        # Apply adaptive optimizations
        adaptive_optimizations = await self.workflow_optimizer.apply_adaptive_optimizations(
            self.test_workflow, adaptive_patterns
        )
        
        assert adaptive_optimizations is not None
        assert adaptive_optimizations.personalized_recommendations is not None
        assert adaptive_optimizations.learning_acceleration_strategies is not None


class TestResearchAssistantWorkflowEdgeCases:
    """Test edge cases and boundary conditions in research assistant workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.workflow_optimizer = WorkflowOptimizer()
        self.workflow_learner = ResearchWorkflowLearner()
    
    @pytest.mark.asyncio
    async def test_workflow_with_circular_dependencies(self):
        """Test workflow with circular task dependencies."""
        circular_workflow = ResearchWorkflow(
            workflow_id="circular_workflow",
            research_domain="test",
            task_sequence=[
                ResearchTask(
                    task_id="circular_task_1",
                    task_type="analysis",
                    description="Task 1",
                    estimated_duration=timedelta(hours=1),
                    dependencies=["circular_task_3"],  # Circular dependency
                    priority=1
                ),
                ResearchTask(
                    task_id="circular_task_2",
                    task_type="synthesis",
                    description="Task 2",
                    estimated_duration=timedelta(hours=1),
                    dependencies=["circular_task_1"],
                    priority=2
                ),
                ResearchTask(
                    task_id="circular_task_3",
                    task_type="review",
                    description="Task 3",
                    estimated_duration=timedelta(hours=1),
                    dependencies=["circular_task_2"],  # Completes the circle
                    priority=3
                )
            ],
            estimated_duration=timedelta(hours=3),
            success_metrics=[],
            optimization_opportunities=[]
        )
        
        # Should detect and handle circular dependencies
        optimized_sequence = await self.workflow_optimizer.optimize_task_sequence(
            circular_workflow.task_sequence
        )
        
        assert optimized_sequence is not None
        # Should break circular dependencies
        assert optimized_sequence.circular_dependencies_resolved is True
        assert len(optimized_sequence.dependency_conflicts) > 0
    
    @pytest.mark.asyncio
    async def test_workflow_with_zero_duration_tasks(self):
        """Test workflow with zero or negative duration tasks."""
        invalid_duration_workflow = ResearchWorkflow(
            workflow_id="invalid_duration_workflow",
            research_domain="test",
            task_sequence=[
                ResearchTask(
                    task_id="zero_duration_task",
                    task_type="instant",
                    description="Zero duration task",
                    estimated_duration=timedelta(seconds=0),
                    dependencies=[],
                    priority=1
                ),
                ResearchTask(
                    task_id="negative_duration_task",
                    task_type="impossible",
                    description="Negative duration task",
                    estimated_duration=timedelta(hours=-1),
                    dependencies=[],
                    priority=2
                )
            ],
            estimated_duration=timedelta(hours=1),
            success_metrics=[],
            optimization_opportunities=[]
        )
        
        # Should handle invalid durations gracefully
        optimized_sequence = await self.workflow_optimizer.optimize_task_sequence(
            invalid_duration_workflow.task_sequence
        )
        
        assert optimized_sequence is not None
        # Should normalize invalid durations
        for task in optimized_sequence.optimized_tasks:
            assert task.estimated_duration.total_seconds() > 0
    
    @pytest.mark.asyncio
    async def test_workflow_with_extremely_long_sessions(self):
        """Test workflow with extremely long session durations."""
        long_session = WorkflowSession(
            session_id="extremely_long_session",
            workflow_id="test_workflow",
            user_id="marathon_researcher",
            start_time=datetime.now() - timedelta(days=30),  # 30 days ago
            end_time=datetime.now(),  # Just finished
            tasks_completed=[
                {
                    "task_id": "marathon_task",
                    "actual_duration": timedelta(days=25),  # 25 days
                    "efficiency_score": 0.1,  # Very low efficiency
                    "quality_score": 0.9   # But high quality
                }
            ],
            success_metrics_achieved={"papers_reviewed": 1000},
            bottlenecks_encountered=[
                {
                    "bottleneck_type": "perfectionism",
                    "impact_severity": 0.9,
                    "time_lost": timedelta(days=20)
                }
            ]
        )
        
        # Should handle extreme durations appropriately
        efficiency_analysis = await self.workflow_optimizer.analyze_workflow_efficiency(
            [long_session]
        )
        
        assert efficiency_analysis is not None
        # Should identify efficiency issues
        assert efficiency_analysis.overall_efficiency < 0.5
        assert len(efficiency_analysis.bottlenecks) > 0
        
        # Should suggest time management improvements
        improvements = await self.workflow_optimizer.suggest_workflow_improvements(
            ResearchWorkflow(
                workflow_id="test_workflow",
                research_domain="test",
                task_sequence=[],
                estimated_duration=timedelta(days=1),
                success_metrics=[],
                optimization_opportunities=[]
            )
        )
        
        time_management_improvements = [
            imp for imp in improvements
            if "time" in imp.improvement_type.lower()
        ]
        assert len(time_management_improvements) > 0


if __name__ == "__main__":
    pytest.main([__file__])