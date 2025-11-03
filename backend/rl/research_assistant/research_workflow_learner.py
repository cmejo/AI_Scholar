"""Research workflow learner for pattern extraction and best practices."""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union, Set
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from .workflow_optimizer import (
    Workflow, WorkflowStep, Task, TaskType, TaskPriority, 
    WorkflowStage, EfficiencyMetrics
)

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of workflow patterns."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ITERATIVE = "iterative"
    BRANCHING = "branching"
    CONVERGENT = "convergent"


class BottleneckType(Enum):
    """Types of workflow bottlenecks."""
    RESOURCE_CONTENTION = "resource_contention"
    DEPENDENCY_BLOCKING = "dependency_blocking"
    SKILL_GAP = "skill_gap"
    TOOL_LIMITATION = "tool_limitation"
    INFORMATION_GATHERING = "information_gathering"
    DECISION_MAKING = "decision_making"
    EXTERNAL_DEPENDENCY = "external_dependency"


@dataclass
class WorkflowPattern:
    """Represents a learned workflow pattern."""
    pattern_id: str
    pattern_type: PatternType
    task_sequence: List[str]  # Task type sequence
    success_rate: float
    average_efficiency: float
    average_satisfaction: float
    frequency: int
    context_conditions: Dict[str, Any]
    performance_metrics: Dict[str, float]
    best_practices: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Bottleneck:
    """Represents a workflow bottleneck."""
    bottleneck_id: str
    bottleneck_type: BottleneckType
    task_types_affected: List[TaskType]
    frequency: float
    average_impact: float  # Impact on efficiency
    resolution_strategies: List[str]
    prevention_measures: List[str]
    context_factors: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BestPractice:
    """Represents a best practice extracted from successful workflows."""
    practice_id: str
    category: str
    description: str
    effectiveness_score: float
    applicability_conditions: Dict[str, Any]
    supporting_evidence: List[str]
    implementation_steps: List[str]
    success_metrics: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowInsight:
    """Represents an insight derived from workflow analysis."""
    insight_id: str
    insight_type: str
    title: str
    description: str
    confidence: float
    impact_level: str  # "low", "medium", "high"
    actionable_recommendations: List[str]
    supporting_data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResearchWorkflowLearner:
    """Learns patterns and best practices from research workflows."""
    
    def __init__(self):
        self.workflow_patterns: Dict[str, List[WorkflowPattern]] = defaultdict(list)
        self.bottlenecks: Dict[str, List[Bottleneck]] = defaultdict(list)
        self.best_practices: Dict[str, List[BestPractice]] = defaultdict(list)
        self.workflow_insights: Dict[str, List[WorkflowInsight]] = defaultdict(list)
        self.user_workflow_history: Dict[str, List[Workflow]] = defaultdict(list)
        self.pattern_clusters: Dict[str, Any] = {}
    
    async def learn_from_successful_workflows(self, workflows: List[Workflow], 
                                            success_threshold: float = 0.7) -> Dict[str, List[WorkflowPattern]]:
        """Learn patterns from successful workflows."""
        try:
            # Filter successful workflows
            successful_workflows = [
                w for w in workflows 
                if w.efficiency_score >= success_threshold and w.completion_rate >= success_threshold
            ]
            
            if not successful_workflows:
                logger.warning("No successful workflows found for learning")
                return {}
            
            # Group workflows by user
            user_workflows = defaultdict(list)
            for workflow in successful_workflows:
                user_workflows[workflow.user_id].append(workflow)
            
            learned_patterns = {}
            
            for user_id, user_workflows_list in user_workflows.items():
                # Extract patterns for this user
                user_patterns = await self._extract_workflow_patterns(user_workflows_list)
                
                # Validate and score patterns
                validated_patterns = await self._validate_patterns(user_patterns, user_workflows_list)
                
                # Store patterns
                self.workflow_patterns[user_id].extend(validated_patterns)
                learned_patterns[user_id] = validated_patterns
                
                # Update workflow history
                self.user_workflow_history[user_id].extend(user_workflows_list)
            
            logger.info(f"Learned patterns from {len(successful_workflows)} successful workflows")
            return learned_patterns
            
        except Exception as e:
            logger.error(f"Error learning from successful workflows: {str(e)}")
            return {}
    
    async def identify_bottlenecks(self, workflows: List[Workflow]) -> Dict[str, List[Bottleneck]]:
        """Identify common bottlenecks in workflows."""
        try:
            # Group workflows by user
            user_workflows = defaultdict(list)
            for workflow in workflows:
                user_workflows[workflow.user_id].append(workflow)
            
            identified_bottlenecks = {}
            
            for user_id, user_workflows_list in user_workflows.items():
                # Analyze bottlenecks for this user
                user_bottlenecks = await self._analyze_bottlenecks(user_workflows_list)
                
                # Store bottlenecks
                self.bottlenecks[user_id].extend(user_bottlenecks)
                identified_bottlenecks[user_id] = user_bottlenecks
            
            logger.info(f"Identified bottlenecks from {len(workflows)} workflows")
            return identified_bottlenecks
            
        except Exception as e:
            logger.error(f"Error identifying bottlenecks: {str(e)}")
            return {}
    
    async def extract_best_practices(self, workflows: List[Workflow], 
                                   efficiency_threshold: float = 0.8) -> Dict[str, List[BestPractice]]:
        """Extract best practices from high-performing workflows."""
        try:
            # Filter high-performing workflows
            high_performing = [
                w for w in workflows 
                if w.efficiency_score >= efficiency_threshold and 
                   w.user_satisfaction >= efficiency_threshold
            ]
            
            if not high_performing:
                logger.warning("No high-performing workflows found for best practice extraction")
                return {}
            
            # Group by user
            user_workflows = defaultdict(list)
            for workflow in high_performing:
                user_workflows[workflow.user_id].append(workflow)
            
            extracted_practices = {}
            
            for user_id, user_workflows_list in user_workflows.items():
                # Extract practices for this user
                user_practices = await self._extract_best_practices(user_workflows_list)
                
                # Store practices
                self.best_practices[user_id].extend(user_practices)
                extracted_practices[user_id] = user_practices
            
            logger.info(f"Extracted best practices from {len(high_performing)} high-performing workflows")
            return extracted_practices
            
        except Exception as e:
            logger.error(f"Error extracting best practices: {str(e)}")
            return {}
    
    async def generate_workflow_insights(self, user_id: str) -> List[WorkflowInsight]:
        """Generate actionable insights from workflow analysis."""
        try:
            insights = []
            
            # Get user's workflow data
            user_workflows = self.user_workflow_history.get(user_id, [])
            user_patterns = self.workflow_patterns.get(user_id, [])
            user_bottlenecks = self.bottlenecks.get(user_id, [])
            user_practices = self.best_practices.get(user_id, [])
            
            if not user_workflows:
                return []
            
            # Generate efficiency insights
            efficiency_insights = await self._generate_efficiency_insights(user_workflows)
            insights.extend(efficiency_insights)
            
            # Generate pattern-based insights
            pattern_insights = await self._generate_pattern_insights(user_patterns)
            insights.extend(pattern_insights)
            
            # Generate bottleneck insights
            bottleneck_insights = await self._generate_bottleneck_insights(user_bottlenecks)
            insights.extend(bottleneck_insights)
            
            # Generate best practice insights
            practice_insights = await self._generate_practice_insights(user_practices)
            insights.extend(practice_insights)
            
            # Generate comparative insights
            comparative_insights = await self._generate_comparative_insights(user_id, user_workflows)
            insights.extend(comparative_insights)
            
            # Sort by impact and confidence
            insights.sort(key=lambda i: (
                {"high": 3, "medium": 2, "low": 1}[i.impact_level] * i.confidence
            ), reverse=True)
            
            # Store insights
            self.workflow_insights[user_id] = insights
            
            logger.info(f"Generated {len(insights)} insights for user {user_id}")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating workflow insights: {str(e)}")
            return []
    
    async def _extract_workflow_patterns(self, workflows: List[Workflow]) -> List[WorkflowPattern]:
        """Extract patterns from workflows."""
        patterns = []
        
        # Extract task sequence patterns
        sequence_patterns = await self._extract_sequence_patterns(workflows)
        patterns.extend(sequence_patterns)
        
        # Extract timing patterns
        timing_patterns = await self._extract_timing_patterns(workflows)
        patterns.extend(timing_patterns)
        
        # Extract resource usage patterns
        resource_patterns = await self._extract_resource_patterns(workflows)
        patterns.extend(resource_patterns)
        
        # Extract stage transition patterns
        stage_patterns = await self._extract_stage_patterns(workflows)
        patterns.extend(stage_patterns)
        
        return patterns
    
    async def _extract_sequence_patterns(self, workflows: List[Workflow]) -> List[WorkflowPattern]:
        """Extract task sequence patterns."""
        patterns = []
        
        # Collect task sequences
        sequences = []
        sequence_metrics = []
        
        for workflow in workflows:
            if len(workflow.steps) >= 3:  # Minimum sequence length
                task_sequence = [step.task.task_type.value for step in workflow.steps]
                sequences.append(task_sequence)
                sequence_metrics.append({
                    'efficiency': workflow.efficiency_score,
                    'satisfaction': workflow.user_satisfaction,
                    'completion_rate': workflow.completion_rate
                })
        
        # Find common subsequences
        common_sequences = await self._find_common_subsequences(sequences, min_length=3)
        
        for seq, frequency in common_sequences.items():
            if frequency >= 2:  # Appears at least twice
                # Calculate average metrics for this sequence
                matching_indices = [i for i, s in enumerate(sequences) if self._contains_subsequence(s, seq)]
                
                if matching_indices:
                    avg_efficiency = np.mean([sequence_metrics[i]['efficiency'] for i in matching_indices])
                    avg_satisfaction = np.mean([sequence_metrics[i]['satisfaction'] for i in matching_indices])
                    success_rate = np.mean([sequence_metrics[i]['completion_rate'] for i in matching_indices])
                    
                    pattern = WorkflowPattern(
                        pattern_id=f"seq_{hash(seq)}",
                        pattern_type=PatternType.SEQUENTIAL,
                        task_sequence=list(seq),
                        success_rate=success_rate,
                        average_efficiency=avg_efficiency,
                        average_satisfaction=avg_satisfaction,
                        frequency=frequency,
                        context_conditions={},
                        performance_metrics={
                            'efficiency': avg_efficiency,
                            'satisfaction': avg_satisfaction,
                            'completion_rate': success_rate
                        },
                        best_practices=[]
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _extract_timing_patterns(self, workflows: List[Workflow]) -> List[WorkflowPattern]:
        """Extract timing-based patterns."""
        patterns = []
        
        # Analyze task duration patterns
        task_durations = defaultdict(list)
        
        for workflow in workflows:
            for step in workflow.steps:
                if step.actual_duration is not None:
                    task_type = step.task.task_type.value
                    task_durations[task_type].append({
                        'duration': step.actual_duration,
                        'efficiency': step.efficiency_score,
                        'satisfaction': step.user_satisfaction
                    })
        
        # Find optimal duration ranges for each task type
        for task_type, durations in task_durations.items():
            if len(durations) >= 5:  # Minimum sample size
                duration_values = [d['duration'] for d in durations]
                efficiency_values = [d['efficiency'] for d in durations]
                
                # Find duration range with highest efficiency
                optimal_range = await self._find_optimal_duration_range(duration_values, efficiency_values)
                
                if optimal_range:
                    avg_efficiency = np.mean([d['efficiency'] for d in durations 
                                            if optimal_range[0] <= d['duration'] <= optimal_range[1]])
                    
                    pattern = WorkflowPattern(
                        pattern_id=f"timing_{task_type}",
                        pattern_type=PatternType.SEQUENTIAL,
                        task_sequence=[task_type],
                        success_rate=0.8,  # Estimated
                        average_efficiency=avg_efficiency,
                        average_satisfaction=0.8,  # Estimated
                        frequency=len(durations),
                        context_conditions={'optimal_duration_range': optimal_range},
                        performance_metrics={'optimal_duration': optimal_range},
                        best_practices=[f"Optimal duration for {task_type}: {optimal_range[0]:.1f}-{optimal_range[1]:.1f} hours"]
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _extract_resource_patterns(self, workflows: List[Workflow]) -> List[WorkflowPattern]:
        """Extract resource usage patterns."""
        patterns = []
        
        # Analyze resource combinations
        resource_combinations = defaultdict(list)
        
        for workflow in workflows:
            for step in workflow.steps:
                if step.task.resources_required:
                    resource_combo = tuple(sorted(step.task.resources_required))
                    resource_combinations[resource_combo].append({
                        'efficiency': step.efficiency_score,
                        'satisfaction': step.user_satisfaction,
                        'task_type': step.task.task_type.value
                    })
        
        # Find effective resource combinations
        for combo, usage_data in resource_combinations.items():
            if len(usage_data) >= 3:  # Minimum usage count
                avg_efficiency = np.mean([d['efficiency'] for d in usage_data])
                avg_satisfaction = np.mean([d['satisfaction'] for d in usage_data])
                
                if avg_efficiency > 0.7:  # High efficiency threshold
                    pattern = WorkflowPattern(
                        pattern_id=f"resource_{hash(combo)}",
                        pattern_type=PatternType.PARALLEL,
                        task_sequence=[d['task_type'] for d in usage_data],
                        success_rate=0.8,
                        average_efficiency=avg_efficiency,
                        average_satisfaction=avg_satisfaction,
                        frequency=len(usage_data),
                        context_conditions={'resource_combination': list(combo)},
                        performance_metrics={'resource_efficiency': avg_efficiency},
                        best_practices=[f"Effective resource combination: {', '.join(combo)}"]
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _extract_stage_patterns(self, workflows: List[Workflow]) -> List[WorkflowPattern]:
        """Extract workflow stage transition patterns."""
        patterns = []
        
        # Analyze stage transitions
        stage_transitions = []
        
        for workflow in workflows:
            if hasattr(workflow, 'stage_history'):
                # If stage history is available
                stage_transitions.append({
                    'transitions': workflow.stage_history,
                    'efficiency': workflow.efficiency_score,
                    'satisfaction': workflow.user_satisfaction
                })
        
        # For now, create a simple pattern based on current stage
        stage_performance = defaultdict(list)
        
        for workflow in workflows:
            stage_performance[workflow.stage.value].append({
                'efficiency': workflow.efficiency_score,
                'satisfaction': workflow.user_satisfaction,
                'completion_rate': workflow.completion_rate
            })
        
        for stage, performance_data in stage_performance.items():
            if len(performance_data) >= 3:
                avg_efficiency = np.mean([d['efficiency'] for d in performance_data])
                avg_satisfaction = np.mean([d['satisfaction'] for d in performance_data])
                avg_completion = np.mean([d['completion_rate'] for d in performance_data])
                
                pattern = WorkflowPattern(
                    pattern_id=f"stage_{stage}",
                    pattern_type=PatternType.SEQUENTIAL,
                    task_sequence=[stage],
                    success_rate=avg_completion,
                    average_efficiency=avg_efficiency,
                    average_satisfaction=avg_satisfaction,
                    frequency=len(performance_data),
                    context_conditions={'workflow_stage': stage},
                    performance_metrics={'stage_efficiency': avg_efficiency},
                    best_practices=[]
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _validate_patterns(self, patterns: List[WorkflowPattern], 
                                workflows: List[Workflow]) -> List[WorkflowPattern]:
        """Validate and score patterns."""
        validated_patterns = []
        
        for pattern in patterns:
            # Calculate pattern reliability
            reliability = await self._calculate_pattern_reliability(pattern, workflows)
            
            # Only keep reliable patterns
            if reliability > 0.6:
                pattern.metadata['reliability'] = reliability
                validated_patterns.append(pattern)
        
        return validated_patterns
    
    async def _calculate_pattern_reliability(self, pattern: WorkflowPattern, 
                                          workflows: List[Workflow]) -> float:
        """Calculate reliability score for a pattern."""
        # Simple reliability calculation based on frequency and performance consistency
        if pattern.frequency < 2:
            return 0.0
        
        # Check performance consistency
        performance_variance = 0.1  # Placeholder - would calculate actual variance
        consistency_score = max(0.0, 1.0 - performance_variance)
        
        # Frequency score
        frequency_score = min(1.0, pattern.frequency / 10.0)
        
        # Combined reliability
        reliability = (consistency_score * 0.7) + (frequency_score * 0.3)
        
        return reliability
    
    async def _analyze_bottlenecks(self, workflows: List[Workflow]) -> List[Bottleneck]:
        """Analyze bottlenecks in workflows."""
        bottlenecks = []
        
        # Collect bottleneck data
        bottleneck_data = defaultdict(list)
        
        for workflow in workflows:
            for step in workflow.steps:
                for bottleneck_name in step.bottlenecks:
                    bottleneck_data[bottleneck_name].append({
                        'task_type': step.task.task_type,
                        'efficiency_impact': 1.0 - step.efficiency_score,
                        'workflow_id': workflow.workflow_id
                    })
        
        # Analyze each bottleneck type
        for bottleneck_name, occurrences in bottleneck_data.items():
            if len(occurrences) >= 2:  # Minimum occurrences
                # Determine bottleneck type
                bottleneck_type = await self._classify_bottleneck_type(bottleneck_name)
                
                # Calculate metrics
                frequency = len(occurrences) / len(workflows)
                avg_impact = np.mean([occ['efficiency_impact'] for occ in occurrences])
                affected_task_types = list(set([occ['task_type'] for occ in occurrences]))
                
                # Generate resolution strategies
                resolution_strategies = await self._generate_resolution_strategies(bottleneck_type, bottleneck_name)
                
                bottleneck = Bottleneck(
                    bottleneck_id=f"bottleneck_{hash(bottleneck_name)}",
                    bottleneck_type=bottleneck_type,
                    task_types_affected=affected_task_types,
                    frequency=frequency,
                    average_impact=avg_impact,
                    resolution_strategies=resolution_strategies,
                    prevention_measures=[],
                    context_factors={'name': bottleneck_name}
                )
                bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    async def _classify_bottleneck_type(self, bottleneck_name: str) -> BottleneckType:
        """Classify bottleneck type based on name and context."""
        name_lower = bottleneck_name.lower()
        
        if 'resource' in name_lower or 'contention' in name_lower:
            return BottleneckType.RESOURCE_CONTENTION
        elif 'dependency' in name_lower or 'blocking' in name_lower:
            return BottleneckType.DEPENDENCY_BLOCKING
        elif 'skill' in name_lower or 'knowledge' in name_lower:
            return BottleneckType.SKILL_GAP
        elif 'tool' in name_lower or 'software' in name_lower:
            return BottleneckType.TOOL_LIMITATION
        elif 'information' in name_lower or 'data' in name_lower:
            return BottleneckType.INFORMATION_GATHERING
        elif 'decision' in name_lower or 'approval' in name_lower:
            return BottleneckType.DECISION_MAKING
        else:
            return BottleneckType.EXTERNAL_DEPENDENCY
    
    async def _generate_resolution_strategies(self, bottleneck_type: BottleneckType, 
                                            bottleneck_name: str) -> List[str]:
        """Generate resolution strategies for bottleneck type."""
        strategies = {
            BottleneckType.RESOURCE_CONTENTION: [
                "Implement resource scheduling system",
                "Add additional resources during peak times",
                "Optimize resource allocation algorithms"
            ],
            BottleneckType.DEPENDENCY_BLOCKING: [
                "Parallelize independent tasks",
                "Implement dependency management system",
                "Create alternative task paths"
            ],
            BottleneckType.SKILL_GAP: [
                "Provide targeted training",
                "Create knowledge sharing sessions",
                "Implement mentoring programs"
            ],
            BottleneckType.TOOL_LIMITATION: [
                "Upgrade to more capable tools",
                "Implement tool integration",
                "Create custom automation scripts"
            ],
            BottleneckType.INFORMATION_GATHERING: [
                "Create information repositories",
                "Implement automated data collection",
                "Establish information sharing protocols"
            ],
            BottleneckType.DECISION_MAKING: [
                "Implement decision frameworks",
                "Delegate decision authority",
                "Create decision support systems"
            ],
            BottleneckType.EXTERNAL_DEPENDENCY: [
                "Establish SLAs with external parties",
                "Create backup alternatives",
                "Implement early warning systems"
            ]
        }
        
        return strategies.get(bottleneck_type, ["Analyze root cause and implement targeted solution"])
    
    async def _extract_best_practices(self, workflows: List[Workflow]) -> List[BestPractice]:
        """Extract best practices from high-performing workflows."""
        practices = []
        
        # Analyze task execution practices
        task_practices = await self._analyze_task_execution_practices(workflows)
        practices.extend(task_practices)
        
        # Analyze resource management practices
        resource_practices = await self._analyze_resource_management_practices(workflows)
        practices.extend(resource_practices)
        
        # Analyze timing practices
        timing_practices = await self._analyze_timing_practices(workflows)
        practices.extend(timing_practices)
        
        # Analyze workflow organization practices
        organization_practices = await self._analyze_organization_practices(workflows)
        practices.extend(organization_practices)
        
        return practices
    
    async def _analyze_task_execution_practices(self, workflows: List[Workflow]) -> List[BestPractice]:
        """Analyze task execution best practices."""
        practices = []
        
        # Analyze task grouping effectiveness
        task_groupings = defaultdict(list)
        
        for workflow in workflows:
            # Group consecutive tasks of same type
            current_group = []
            current_type = None
            
            for step in workflow.steps:
                if step.task.task_type == current_type:
                    current_group.append(step)
                else:
                    if len(current_group) > 1:
                        # Calculate group efficiency
                        group_efficiency = np.mean([s.efficiency_score for s in current_group])
                        task_groupings[current_type].append(group_efficiency)
                    
                    current_group = [step]
                    current_type = step.task.task_type
            
            # Handle last group
            if len(current_group) > 1:
                group_efficiency = np.mean([s.efficiency_score for s in current_group])
                task_groupings[current_type].append(group_efficiency)
        
        # Find effective task grouping practices
        for task_type, efficiencies in task_groupings.items():
            if len(efficiencies) >= 3 and np.mean(efficiencies) > 0.8:
                practice = BestPractice(
                    practice_id=f"grouping_{task_type.value}",
                    category="task_execution",
                    description=f"Group consecutive {task_type.value} tasks for improved efficiency",
                    effectiveness_score=np.mean(efficiencies),
                    applicability_conditions={'task_type': task_type.value},
                    supporting_evidence=[f"Average efficiency: {np.mean(efficiencies):.2f}"],
                    implementation_steps=[
                        f"Identify consecutive {task_type.value} tasks",
                        "Schedule them in sequence",
                        "Minimize context switching"
                    ],
                    success_metrics={'efficiency_improvement': np.mean(efficiencies) - 0.7}
                )
                practices.append(practice)
        
        return practices
    
    async def _analyze_resource_management_practices(self, workflows: List[Workflow]) -> List[BestPractice]:
        """Analyze resource management best practices."""
        practices = []
        
        # Analyze resource allocation patterns
        resource_usage = defaultdict(list)
        
        for workflow in workflows:
            workflow_resources = set()
            workflow_efficiency = workflow.efficiency_score
            
            for step in workflow.steps:
                workflow_resources.update(step.task.resources_required)
            
            if workflow_resources:
                resource_usage[tuple(sorted(workflow_resources))].append(workflow_efficiency)
        
        # Find effective resource combinations
        for resources, efficiencies in resource_usage.items():
            if len(efficiencies) >= 3 and np.mean(efficiencies) > 0.8:
                practice = BestPractice(
                    practice_id=f"resources_{hash(resources)}",
                    category="resource_management",
                    description=f"Effective resource combination: {', '.join(resources)}",
                    effectiveness_score=np.mean(efficiencies),
                    applicability_conditions={'required_resources': list(resources)},
                    supporting_evidence=[f"Average efficiency: {np.mean(efficiencies):.2f}"],
                    implementation_steps=[
                        "Ensure all required resources are available",
                        "Coordinate resource access",
                        "Monitor resource utilization"
                    ],
                    success_metrics={'resource_efficiency': np.mean(efficiencies)}
                )
                practices.append(practice)
        
        return practices
    
    async def _analyze_timing_practices(self, workflows: List[Workflow]) -> List[BestPractice]:
        """Analyze timing-related best practices."""
        practices = []
        
        # Analyze optimal task durations
        task_durations = defaultdict(list)
        
        for workflow in workflows:
            for step in workflow.steps:
                if step.actual_duration is not None and step.efficiency_score > 0.8:
                    task_durations[step.task.task_type].append(step.actual_duration)
        
        # Find optimal duration ranges
        for task_type, durations in task_durations.items():
            if len(durations) >= 5:
                optimal_duration = np.median(durations)
                duration_range = (np.percentile(durations, 25), np.percentile(durations, 75))
                
                practice = BestPractice(
                    practice_id=f"timing_{task_type.value}",
                    category="timing",
                    description=f"Optimal duration for {task_type.value}: {optimal_duration:.1f} hours",
                    effectiveness_score=0.8,  # Based on high efficiency threshold
                    applicability_conditions={'task_type': task_type.value},
                    supporting_evidence=[f"Median duration from {len(durations)} high-efficiency instances"],
                    implementation_steps=[
                        f"Allocate approximately {optimal_duration:.1f} hours for {task_type.value} tasks",
                        f"Allow flexibility within {duration_range[0]:.1f}-{duration_range[1]:.1f} hour range",
                        "Monitor actual vs planned duration"
                    ],
                    success_metrics={'optimal_duration': optimal_duration}
                )
                practices.append(practice)
        
        return practices
    
    async def _analyze_organization_practices(self, workflows: List[Workflow]) -> List[BestPractice]:
        """Analyze workflow organization best practices."""
        practices = []
        
        # Analyze workflow length effectiveness
        workflow_lengths = []
        workflow_efficiencies = []
        
        for workflow in workflows:
            workflow_lengths.append(len(workflow.steps))
            workflow_efficiencies.append(workflow.efficiency_score)
        
        if len(workflow_lengths) >= 5:
            # Find optimal workflow length
            optimal_length_range = await self._find_optimal_range(workflow_lengths, workflow_efficiencies)
            
            if optimal_length_range:
                practice = BestPractice(
                    practice_id="workflow_length",
                    category="organization",
                    description=f"Optimal workflow length: {optimal_length_range[0]}-{optimal_length_range[1]} tasks",
                    effectiveness_score=0.8,
                    applicability_conditions={},
                    supporting_evidence=["Analysis of workflow length vs efficiency correlation"],
                    implementation_steps=[
                        f"Aim for {optimal_length_range[0]}-{optimal_length_range[1]} tasks per workflow",
                        "Break down large workflows into smaller chunks",
                        "Combine very small workflows when appropriate"
                    ],
                    success_metrics={'optimal_length_range': optimal_length_range}
                )
                practices.append(practice)
        
        return practices
    
    async def _generate_efficiency_insights(self, workflows: List[Workflow]) -> List[WorkflowInsight]:
        """Generate insights about efficiency trends."""
        insights = []
        
        if len(workflows) < 3:
            return insights
        
        # Analyze efficiency trend
        recent_workflows = sorted(workflows, key=lambda w: w.created_at)[-10:]
        efficiency_scores = [w.efficiency_score for w in recent_workflows]
        
        if len(efficiency_scores) >= 3:
            # Calculate trend
            x = np.arange(len(efficiency_scores))
            trend = np.polyfit(x, efficiency_scores, 1)[0]
            
            if abs(trend) > 0.05:  # Significant trend
                trend_direction = "improving" if trend > 0 else "declining"
                
                insight = WorkflowInsight(
                    insight_id="efficiency_trend",
                    insight_type="trend_analysis",
                    title=f"Workflow Efficiency is {trend_direction.title()}",
                    description=f"Your workflow efficiency has been {trend_direction} by {abs(trend)*100:.1f}% per workflow over recent sessions.",
                    confidence=0.8,
                    impact_level="medium" if abs(trend) > 0.1 else "low",
                    actionable_recommendations=[
                        "Continue current practices" if trend > 0 else "Review recent workflow changes",
                        "Identify factors contributing to the trend",
                        "Adjust workflow strategies accordingly"
                    ],
                    supporting_data={'trend_slope': trend, 'recent_scores': efficiency_scores}
                )
                insights.append(insight)
        
        return insights
    
    async def _generate_pattern_insights(self, patterns: List[WorkflowPattern]) -> List[WorkflowInsight]:
        """Generate insights from workflow patterns."""
        insights = []
        
        if not patterns:
            return insights
        
        # Find most effective pattern
        best_pattern = max(patterns, key=lambda p: p.average_efficiency)
        
        if best_pattern.average_efficiency > 0.8:
            insight = WorkflowInsight(
                insight_id="best_pattern",
                insight_type="pattern_recommendation",
                title="High-Performance Pattern Identified",
                description=f"Your most effective workflow pattern achieves {best_pattern.average_efficiency:.1%} efficiency.",
                confidence=0.9,
                impact_level="high",
                actionable_recommendations=[
                    f"Use the task sequence: {' → '.join(best_pattern.task_sequence)}",
                    "Apply this pattern to similar workflows",
                    "Monitor performance when using this pattern"
                ],
                supporting_data={'pattern': best_pattern.__dict__}
            )
            insights.append(insight)
        
        return insights
    
    async def _generate_bottleneck_insights(self, bottlenecks: List[Bottleneck]) -> List[WorkflowInsight]:
        """Generate insights from bottleneck analysis."""
        insights = []
        
        if not bottlenecks:
            return insights
        
        # Find most impactful bottleneck
        major_bottleneck = max(bottlenecks, key=lambda b: b.frequency * b.average_impact)
        
        if major_bottleneck.frequency > 0.3:  # Affects >30% of workflows
            insight = WorkflowInsight(
                insight_id="major_bottleneck",
                insight_type="bottleneck_analysis",
                title="Major Bottleneck Identified",
                description=f"A {major_bottleneck.bottleneck_type.value} bottleneck affects {major_bottleneck.frequency:.1%} of your workflows.",
                confidence=0.8,
                impact_level="high",
                actionable_recommendations=major_bottleneck.resolution_strategies[:3],
                supporting_data={'bottleneck': major_bottleneck.__dict__}
            )
            insights.append(insight)
        
        return insights
    
    async def _generate_practice_insights(self, practices: List[BestPractice]) -> List[WorkflowInsight]:
        """Generate insights from best practices."""
        insights = []
        
        if not practices:
            return insights
        
        # Find most impactful practice
        top_practice = max(practices, key=lambda p: p.effectiveness_score)
        
        if top_practice.effectiveness_score > 0.8:
            insight = WorkflowInsight(
                insight_id="top_practice",
                insight_type="best_practice",
                title="High-Impact Best Practice",
                description=f"Implementing '{top_practice.description}' shows {top_practice.effectiveness_score:.1%} effectiveness.",
                confidence=0.8,
                impact_level="medium",
                actionable_recommendations=top_practice.implementation_steps[:3],
                supporting_data={'practice': top_practice.__dict__}
            )
            insights.append(insight)
        
        return insights
    
    async def _generate_comparative_insights(self, user_id: str, workflows: List[Workflow]) -> List[WorkflowInsight]:
        """Generate comparative insights against other users or benchmarks."""
        insights = []
        
        if len(workflows) < 5:
            return insights
        
        # Calculate user's average metrics
        avg_efficiency = np.mean([w.efficiency_score for w in workflows])
        avg_satisfaction = np.mean([w.user_satisfaction for w in workflows])
        
        # Compare against benchmarks (simplified - would use actual benchmark data)
        benchmark_efficiency = 0.75  # Placeholder benchmark
        benchmark_satisfaction = 0.80  # Placeholder benchmark
        
        if avg_efficiency > benchmark_efficiency + 0.1:
            insight = WorkflowInsight(
                insight_id="above_benchmark",
                insight_type="comparative_analysis",
                title="Above-Average Performance",
                description=f"Your workflow efficiency ({avg_efficiency:.1%}) exceeds the benchmark by {(avg_efficiency - benchmark_efficiency)*100:.1f}%.",
                confidence=0.7,
                impact_level="medium",
                actionable_recommendations=[
                    "Continue current successful practices",
                    "Share insights with others",
                    "Document your effective strategies"
                ],
                supporting_data={'user_avg': avg_efficiency, 'benchmark': benchmark_efficiency}
            )
            insights.append(insight)
        
        return insights
    
    # Helper methods
    
    async def _find_common_subsequences(self, sequences: List[List[str]], min_length: int = 3) -> Dict[tuple, int]:
        """Find common subsequences in task sequences."""
        subsequence_counts = defaultdict(int)
        
        for sequence in sequences:
            # Generate all subsequences of minimum length
            for i in range(len(sequence) - min_length + 1):
                for j in range(i + min_length, len(sequence) + 1):
                    subseq = tuple(sequence[i:j])
                    subsequence_counts[subseq] += 1
        
        # Filter by minimum frequency
        return {seq: count for seq, count in subsequence_counts.items() if count >= 2}
    
    def _contains_subsequence(self, sequence: List[str], subsequence: tuple) -> bool:
        """Check if sequence contains subsequence."""
        subseq_list = list(subsequence)
        for i in range(len(sequence) - len(subseq_list) + 1):
            if sequence[i:i+len(subseq_list)] == subseq_list:
                return True
        return False
    
    async def _find_optimal_duration_range(self, durations: List[float], 
                                         efficiencies: List[float]) -> Optional[Tuple[float, float]]:
        """Find optimal duration range for maximum efficiency."""
        if len(durations) < 5:
            return None
        
        # Sort by duration
        sorted_pairs = sorted(zip(durations, efficiencies))
        
        # Find range with highest average efficiency
        best_range = None
        best_efficiency = 0
        
        for i in range(len(sorted_pairs) - 2):
            for j in range(i + 2, len(sorted_pairs)):
                range_efficiencies = [eff for dur, eff in sorted_pairs[i:j+1]]
                avg_efficiency = np.mean(range_efficiencies)
                
                if avg_efficiency > best_efficiency:
                    best_efficiency = avg_efficiency
                    best_range = (sorted_pairs[i][0], sorted_pairs[j][0])
        
        return best_range
    
    async def _find_optimal_range(self, values: List[float], outcomes: List[float]) -> Optional[Tuple[int, int]]:
        """Find optimal range of values for best outcomes."""
        if len(values) < 5:
            return None
        
        # Simple approach: find quartile range with highest average outcome
        sorted_pairs = sorted(zip(values, outcomes))
        
        # Calculate quartiles
        q1_idx = len(sorted_pairs) // 4
        q3_idx = 3 * len(sorted_pairs) // 4
        
        q1_q3_outcomes = [outcome for _, outcome in sorted_pairs[q1_idx:q3_idx]]
        
        if np.mean(q1_q3_outcomes) > np.mean(outcomes):
            return (int(sorted_pairs[q1_idx][0]), int(sorted_pairs[q3_idx][0]))
        
        return None
    
    def get_learning_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of learned patterns and insights for a user."""
        return {
            "user_id": user_id,
            "patterns_learned": len(self.workflow_patterns.get(user_id, [])),
            "bottlenecks_identified": len(self.bottlenecks.get(user_id, [])),
            "best_practices_extracted": len(self.best_practices.get(user_id, [])),
            "insights_generated": len(self.workflow_insights.get(user_id, [])),
            "workflows_analyzed": len(self.user_workflow_history.get(user_id, [])),
            "top_patterns": [p.pattern_id for p in sorted(
                self.workflow_patterns.get(user_id, []), 
                key=lambda x: x.average_efficiency, 
                reverse=True
            )[:3]],
            "major_bottlenecks": [b.bottleneck_type.value for b in sorted(
                self.bottlenecks.get(user_id, []), 
                key=lambda x: x.frequency * x.average_impact, 
                reverse=True
            )[:3]]
        }