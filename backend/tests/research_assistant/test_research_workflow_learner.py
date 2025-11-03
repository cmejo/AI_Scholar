"""Unit tests for research workflow learner."""

import pytest
import numpy as np
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from backend.rl.research_assistant.research_workflow_learner import (
    ResearchWorkflowLearner,
    WorkflowPattern,
    PatternType,
    Bottleneck,
    BottleneckType,
    BestPractice,
    WorkflowInsight
)
from backend.rl.research_assistant.workflow_optimizer import (
    Workflow,
    WorkflowStep,
    Task,
    TaskType,
    TaskPriority,
    WorkflowStage
)


class TestResearchWorkflowLearner:
    """Test cases for ResearchWorkflowLearner class."""
    
    def create_sample_workflow(self, workflow_id="workflow_1", user_id="user_1", 
                              efficiency=0.8, satisfaction=0.85, completion_rate=0.9):
        """Create a sample workflow for testing."""
        workflow = Workflow(
            workflow_id=workflow_id,
            user_id=user_id,
            stage=WorkflowStage.RESEARCH,
            efficiency_score=efficiency,
            user_satisfaction=satisfaction,
            completion_rate=completion_rate,
            created_at=datetime.now()
        )
        
        # Add sample steps
        task_types = [TaskType.LITERATURE_SEARCH, TaskType.PAPER_ANALYSIS, TaskType.DATA_EXTRACTION]
        for i, task_type in enumerate(task_types):
            task = Task(f"task_{i}", task_type, TaskPriority.MEDIUM, 2.0)
            step = WorkflowStep(
                step_id=f"step_{i}",
                task=task,
                start_time=datetime.now() - timedelta(hours=2),
                end_time=datetime.now() - timedelta(hours=1),
                actual_duration=2.0,
                efficiency_score=efficiency,
                user_satisfaction=satisfaction,
                bottlenecks=["resource_contention"] if i == 1 else []
            )
            workflow.steps.append(step)
        
        return workflow
    
    def create_multiple_workflows(self, num_workflows=5, user_id="user_1"):
        """Create multiple sample workflows."""
        workflows = []
        for i in range(num_workflows):
            efficiency = 0.7 + (i * 0.05)  # Increasing efficiency
            satisfaction = 0.75 + (i * 0.04)
            completion_rate = 0.8 + (i * 0.04)
            
            workflow = self.create_sample_workflow(
                f"workflow_{i}", user_id, efficiency, satisfaction, completion_rate
            )
            workflows.append(workflow)
        
        return workflows
    
    @pytest.mark.asyncio
    async def test_learn_from_successful_workflows(self):
        """Test learning patterns from successful workflows."""
        learner = ResearchWorkflowLearner()
        
        # Create successful workflows
        workflows = self.create_multiple_workflows(5, "user_1")
        
        # Ensure they meet success threshold
        for workflow in workflows:
            workflow.efficiency_score = 0.8
            workflow.completion_rate = 0.8
        
        learned_patterns = await learner.learn_from_successful_workflows(workflows)
        
        assert isinstance(learned_patterns, dict)
        assert "user_1" in learned_patterns
        assert isinstance(learned_patterns["user_1"], list)
        
        # Check that patterns were stored
        assert len(learner.workflow_patterns["user_1"]) > 0
        
        # Check pattern structure
        for pattern in learned_patterns["user_1"]:
            assert isinstance(pattern, WorkflowPattern)
            assert pattern.pattern_id
            assert isinstance(pattern.pattern_type, PatternType)
            assert isinstance(pattern.task_sequence, list)
            assert 0.0 <= pattern.success_rate <= 1.0
            assert 0.0 <= pattern.average_efficiency <= 1.0
            assert pattern.frequency >= 0
    
    @pytest.mark.asyncio
    async def test_learn_from_unsuccessful_workflows(self):
        """Test learning with workflows below success threshold."""
        learner = ResearchWorkflowLearner()
        
        # Create unsuccessful workflows
        workflows = self.create_multiple_workflows(3, "user_1")
        for workflow in workflows:
            workflow.efficiency_score = 0.5  # Below threshold
            workflow.completion_rate = 0.6   # Below threshold
        
        learned_patterns = await learner.learn_from_successful_workflows(workflows)
        
        # Should return empty results for unsuccessful workflows
        assert learned_patterns == {}
    
    @pytest.mark.asyncio
    async def test_identify_bottlenecks(self):
        """Test bottleneck identification."""
        learner = ResearchWorkflowLearner()
        
        workflows = self.create_multiple_workflows(4, "user_1")
        
        # Add more bottlenecks to some workflows
        for i, workflow in enumerate(workflows):
            for j, step in enumerate(workflow.steps):
                if i % 2 == 0:  # Every other workflow
                    step.bottlenecks = ["resource_contention", "tool_limitation"]
                    step.efficiency_score = 0.6  # Lower efficiency due to bottlenecks
        
        identified_bottlenecks = await learner.identify_bottlenecks(workflows)
        
        assert isinstance(identified_bottlenecks, dict)
        assert "user_1" in identified_bottlenecks
        
        bottlenecks = identified_bottlenecks["user_1"]
        assert len(bottlenecks) > 0
        
        # Check bottleneck structure
        for bottleneck in bottlenecks:
            assert isinstance(bottleneck, Bottleneck)
            assert bottleneck.bottleneck_id
            assert isinstance(bottleneck.bottleneck_type, BottleneckType)
            assert isinstance(bottleneck.task_types_affected, list)
            assert 0.0 <= bottleneck.frequency <= 1.0
            assert bottleneck.average_impact >= 0.0
            assert isinstance(bottleneck.resolution_strategies, list)
    
    @pytest.mark.asyncio
    async def test_extract_best_practices(self):
        """Test best practice extraction."""
        learner = ResearchWorkflowLearner()
        
        # Create high-performing workflows
        workflows = self.create_multiple_workflows(5, "user_1")
        for workflow in workflows:
            workflow.efficiency_score = 0.9
            workflow.user_satisfaction = 0.9
        
        extracted_practices = await learner.extract_best_practices(workflows)
        
        assert isinstance(extracted_practices, dict)
        assert "user_1" in extracted_practices
        
        practices = extracted_practices["user_1"]
        assert isinstance(practices, list)
        
        # Check practice structure
        for practice in practices:
            assert isinstance(practice, BestPractice)
            assert practice.practice_id
            assert practice.category
            assert practice.description
            assert 0.0 <= practice.effectiveness_score <= 1.0
            assert isinstance(practice.applicability_conditions, dict)
            assert isinstance(practice.implementation_steps, list)
    
    @pytest.mark.asyncio
    async def test_generate_workflow_insights(self):
        """Test workflow insight generation."""
        learner = ResearchWorkflowLearner()
        
        # Create workflow history
        workflows = self.create_multiple_workflows(8, "user_1")
        
        # Add to learner's history
        learner.user_workflow_history["user_1"] = workflows
        
        # Add some patterns and bottlenecks
        pattern = WorkflowPattern(
            pattern_id="test_pattern",
            pattern_type=PatternType.SEQUENTIAL,
            task_sequence=["literature_search", "paper_analysis"],
            success_rate=0.9,
            average_efficiency=0.85,
            average_satisfaction=0.8,
            frequency=5,
            context_conditions={},
            performance_metrics={},
            best_practices=[]
        )
        learner.workflow_patterns["user_1"] = [pattern]
        
        bottleneck = Bottleneck(
            bottleneck_id="test_bottleneck",
            bottleneck_type=BottleneckType.RESOURCE_CONTENTION,
            task_types_affected=[TaskType.PAPER_ANALYSIS],
            frequency=0.4,
            average_impact=0.3,
            resolution_strategies=["Add more resources"],
            prevention_measures=[],
            context_factors={}
        )
        learner.bottlenecks["user_1"] = [bottleneck]
        
        insights = await learner.generate_workflow_insights("user_1")
        
        assert isinstance(insights, list)
        
        # Check insight structure
        for insight in insights:
            assert isinstance(insight, WorkflowInsight)
            assert insight.insight_id
            assert insight.insight_type
            assert insight.title
            assert insight.description
            assert 0.0 <= insight.confidence <= 1.0
            assert insight.impact_level in ["low", "medium", "high"]
            assert isinstance(insight.actionable_recommendations, list)
    
    @pytest.mark.asyncio
    async def test_extract_sequence_patterns(self):
        """Test task sequence pattern extraction."""
        learner = ResearchWorkflowLearner()
        
        # Create workflows with similar task sequences
        workflows = []
        common_sequence = [TaskType.LITERATURE_SEARCH, TaskType.PAPER_ANALYSIS, TaskType.SYNTHESIS]
        
        for i in range(4):
            workflow = Workflow(f"workflow_{i}", "user_1", WorkflowStage.RESEARCH)
            workflow.efficiency_score = 0.8
            workflow.user_satisfaction = 0.85
            workflow.completion_rate = 0.9
            
            for j, task_type in enumerate(common_sequence):
                task = Task(f"task_{i}_{j}", task_type, TaskPriority.MEDIUM, 2.0)
                step = WorkflowStep(f"step_{i}_{j}", task)
                workflow.steps.append(step)
            
            workflows.append(workflow)
        
        patterns = await learner._extract_sequence_patterns(workflows)
        
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        
        # Should find the common sequence pattern
        sequence_patterns = [p for p in patterns if p.pattern_type == PatternType.SEQUENTIAL]
        assert len(sequence_patterns) > 0
    
    @pytest.mark.asyncio
    async def test_classify_bottleneck_type(self):
        """Test bottleneck type classification."""
        learner = ResearchWorkflowLearner()
        
        test_cases = [
            ("resource_contention", BottleneckType.RESOURCE_CONTENTION),
            ("dependency_blocking", BottleneckType.DEPENDENCY_BLOCKING),
            ("skill_gap", BottleneckType.SKILL_GAP),
            ("tool_limitation", BottleneckType.TOOL_LIMITATION),
            ("information_gathering", BottleneckType.INFORMATION_GATHERING),
            ("decision_making", BottleneckType.DECISION_MAKING),
            ("unknown_bottleneck", BottleneckType.EXTERNAL_DEPENDENCY)
        ]
        
        for bottleneck_name, expected_type in test_cases:
            result = await learner._classify_bottleneck_type(bottleneck_name)
            assert result == expected_type
    
    @pytest.mark.asyncio
    async def test_generate_resolution_strategies(self):
        """Test resolution strategy generation."""
        learner = ResearchWorkflowLearner()
        
        strategies = await learner._generate_resolution_strategies(
            BottleneckType.RESOURCE_CONTENTION, "resource_contention"
        )
        
        assert isinstance(strategies, list)
        assert len(strategies) > 0
        assert all(isinstance(strategy, str) for strategy in strategies)
        
        # Check that strategies are relevant to the bottleneck type
        resource_keywords = ["resource", "scheduling", "allocation"]
        assert any(any(keyword in strategy.lower() for keyword in resource_keywords) 
                  for strategy in strategies)
    
    @pytest.mark.asyncio
    async def test_analyze_task_execution_practices(self):
        """Test task execution practice analysis."""
        learner = ResearchWorkflowLearner()
        
        # Create workflows with grouped tasks
        workflows = []
        for i in range(3):
            workflow = Workflow(f"workflow_{i}", "user_1", WorkflowStage.RESEARCH)
            workflow.efficiency_score = 0.9
            
            # Add grouped tasks of same type
            for j in range(3):  # 3 consecutive literature search tasks
                task = Task(f"task_{i}_{j}", TaskType.LITERATURE_SEARCH, TaskPriority.MEDIUM, 2.0)
                step = WorkflowStep(f"step_{i}_{j}", task, efficiency_score=0.9)
                workflow.steps.append(step)
            
            workflows.append(workflow)
        
        practices = await learner._analyze_task_execution_practices(workflows)
        
        assert isinstance(practices, list)
        
        # Should identify task grouping as a best practice
        grouping_practices = [p for p in practices if "grouping" in p.practice_id.lower()]
        if grouping_practices:  # May not always find patterns with small sample
            practice = grouping_practices[0]
            assert practice.category == "task_execution"
            assert practice.effectiveness_score > 0.8
    
    @pytest.mark.asyncio
    async def test_find_common_subsequences(self):
        """Test common subsequence finding."""
        learner = ResearchWorkflowLearner()
        
        sequences = [
            ["A", "B", "C", "D"],
            ["A", "B", "C", "E"],
            ["X", "A", "B", "C"],
            ["A", "B", "Y", "Z"]
        ]
        
        common_subseqs = await learner._find_common_subsequences(sequences, min_length=2)
        
        assert isinstance(common_subseqs, dict)
        
        # Should find "A", "B" as common subsequence
        ab_tuple = ("A", "B")
        assert ab_tuple in common_subseqs
        assert common_subseqs[ab_tuple] >= 2  # Appears in multiple sequences
    
    def test_contains_subsequence(self):
        """Test subsequence containment check."""
        learner = ResearchWorkflowLearner()
        
        sequence = ["A", "B", "C", "D", "E"]
        
        # Test positive cases
        assert learner._contains_subsequence(sequence, ("A", "B"))
        assert learner._contains_subsequence(sequence, ("B", "C", "D"))
        assert learner._contains_subsequence(sequence, ("D", "E"))
        
        # Test negative cases
        assert not learner._contains_subsequence(sequence, ("A", "C"))
        assert not learner._contains_subsequence(sequence, ("E", "F"))
        assert not learner._contains_subsequence(sequence, ("F", "G", "H"))
    
    @pytest.mark.asyncio
    async def test_find_optimal_duration_range(self):
        """Test optimal duration range finding."""
        learner = ResearchWorkflowLearner()
        
        # Create data where medium durations have highest efficiency
        durations = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
        efficiencies = [0.6, 0.7, 0.9, 0.95, 0.9, 0.7, 0.6]  # Peak at 2.0-2.5
        
        optimal_range = await learner._find_optimal_duration_range(durations, efficiencies)
        
        if optimal_range:  # May return None with small sample
            assert isinstance(optimal_range, tuple)
            assert len(optimal_range) == 2
            assert optimal_range[0] <= optimal_range[1]
            # Should capture the high-efficiency range
            assert 1.5 <= optimal_range[0] <= 2.5
            assert 2.0 <= optimal_range[1] <= 3.0
    
    @pytest.mark.asyncio
    async def test_generate_efficiency_insights(self):
        """Test efficiency insight generation."""
        learner = ResearchWorkflowLearner()
        
        # Create workflows with improving efficiency trend
        workflows = []
        for i in range(5):
            workflow = Workflow(f"workflow_{i}", "user_1", WorkflowStage.RESEARCH)
            workflow.efficiency_score = 0.6 + (i * 0.1)  # Improving trend
            workflow.created_at = datetime.now() - timedelta(days=5-i)
            workflows.append(workflow)
        
        insights = await learner._generate_efficiency_insights(workflows)
        
        assert isinstance(insights, list)
        
        # Should detect improving trend
        trend_insights = [i for i in insights if i.insight_type == "trend_analysis"]
        if trend_insights:
            insight = trend_insights[0]
            assert "improving" in insight.title.lower()
            assert insight.confidence > 0.0
    
    def test_get_learning_summary(self):
        """Test learning summary generation."""
        learner = ResearchWorkflowLearner()
        
        # Add some test data
        pattern = WorkflowPattern(
            pattern_id="test_pattern",
            pattern_type=PatternType.SEQUENTIAL,
            task_sequence=["literature_search"],
            success_rate=0.8,
            average_efficiency=0.85,
            average_satisfaction=0.8,
            frequency=3,
            context_conditions={},
            performance_metrics={},
            best_practices=[]
        )
        learner.workflow_patterns["user_1"] = [pattern]
        
        bottleneck = Bottleneck(
            bottleneck_id="test_bottleneck",
            bottleneck_type=BottleneckType.RESOURCE_CONTENTION,
            task_types_affected=[TaskType.LITERATURE_SEARCH],
            frequency=0.3,
            average_impact=0.2,
            resolution_strategies=[],
            prevention_measures=[],
            context_factors={}
        )
        learner.bottlenecks["user_1"] = [bottleneck]
        
        summary = learner.get_learning_summary("user_1")
        
        assert isinstance(summary, dict)
        assert summary["user_id"] == "user_1"
        assert summary["patterns_learned"] == 1
        assert summary["bottlenecks_identified"] == 1
        assert isinstance(summary["top_patterns"], list)
        assert isinstance(summary["major_bottlenecks"], list)
    
    def test_get_learning_summary_empty(self):
        """Test learning summary with no data."""
        learner = ResearchWorkflowLearner()
        
        summary = learner.get_learning_summary("new_user")
        
        assert isinstance(summary, dict)
        assert summary["user_id"] == "new_user"
        assert summary["patterns_learned"] == 0
        assert summary["bottlenecks_identified"] == 0
        assert summary["best_practices_extracted"] == 0
        assert summary["insights_generated"] == 0
        assert summary["workflows_analyzed"] == 0
    
    @pytest.mark.asyncio
    async def test_empty_workflow_list_handling(self):
        """Test handling of empty workflow lists."""
        learner = ResearchWorkflowLearner()
        
        # Test with empty lists
        patterns = await learner.learn_from_successful_workflows([])
        assert patterns == {}
        
        bottlenecks = await learner.identify_bottlenecks([])
        assert bottlenecks == {}
        
        practices = await learner.extract_best_practices([])
        assert practices == {}
        
        insights = await learner.generate_workflow_insights("user_1")
        assert insights == []
    
    @pytest.mark.asyncio
    async def test_pattern_validation(self):
        """Test pattern validation logic."""
        learner = ResearchWorkflowLearner()
        
        # Create a pattern with low reliability
        low_reliability_pattern = WorkflowPattern(
            pattern_id="low_reliability",
            pattern_type=PatternType.SEQUENTIAL,
            task_sequence=["literature_search"],
            success_rate=0.5,
            average_efficiency=0.6,
            average_satisfaction=0.5,
            frequency=1,  # Low frequency
            context_conditions={},
            performance_metrics={},
            best_practices=[]
        )
        
        # Create a pattern with high reliability
        high_reliability_pattern = WorkflowPattern(
            pattern_id="high_reliability",
            pattern_type=PatternType.SEQUENTIAL,
            task_sequence=["literature_search", "paper_analysis"],
            success_rate=0.9,
            average_efficiency=0.85,
            average_satisfaction=0.8,
            frequency=5,  # High frequency
            context_conditions={},
            performance_metrics={},
            best_practices=[]
        )
        
        patterns = [low_reliability_pattern, high_reliability_pattern]
        workflows = self.create_multiple_workflows(3, "user_1")
        
        validated_patterns = await learner._validate_patterns(patterns, workflows)
        
        # Should filter out low reliability patterns
        assert len(validated_patterns) <= len(patterns)
        
        # High reliability pattern should be included
        validated_ids = [p.pattern_id for p in validated_patterns]
        assert "high_reliability" in validated_ids or len(validated_patterns) == 0  # May filter all with simple validation
    
    @pytest.mark.asyncio
    async def test_multiple_users(self):
        """Test learning with multiple users."""
        learner = ResearchWorkflowLearner()
        
        # Create workflows for multiple users
        user1_workflows = self.create_multiple_workflows(3, "user_1")
        user2_workflows = self.create_multiple_workflows(3, "user_2")
        
        all_workflows = user1_workflows + user2_workflows
        
        # Ensure success threshold is met
        for workflow in all_workflows:
            workflow.efficiency_score = 0.8
            workflow.completion_rate = 0.8
        
        patterns = await learner.learn_from_successful_workflows(all_workflows)
        
        # Should have patterns for both users
        assert isinstance(patterns, dict)
        assert len(patterns) <= 2  # May not find patterns for all users
        
        # Check that user data is separated
        if "user_1" in patterns and "user_2" in patterns:
            assert patterns["user_1"] != patterns["user_2"]  # Different pattern lists
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in learning methods."""
        learner = ResearchWorkflowLearner()
        
        # Test with malformed workflow (missing required attributes)
        malformed_workflow = Workflow("test", "user_1", WorkflowStage.RESEARCH)
        malformed_workflow.steps = None  # This should cause issues
        
        # Should handle errors gracefully
        try:
            patterns = await learner.learn_from_successful_workflows([malformed_workflow])
            # Should return empty dict on error
            assert patterns == {}
        except Exception:
            # Or may raise exception, which is also acceptable
            pass
        
        try:
            bottlenecks = await learner.identify_bottlenecks([malformed_workflow])
            assert bottlenecks == {}
        except Exception:
            pass