"""
Error Analysis and Reporting System for Multi-Instance ArXiv System.

This module provides comprehensive error categorization, trend analysis,
pattern detection, impact assessment, and automated resolution suggestions.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import asyncio
import json
import statistics
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.error_handling.error_models import (
        ProcessingError, ErrorType, ErrorCategory, ErrorSeverity, ErrorSummary
    )
except ImportError as e:
    print(f"Import error: {e}")
    # Create minimal fallback classes for testing
    class ProcessingError:
        def __init__(self, *args, **kwargs): pass
    class ErrorType:
        HTTP_ERROR = "http_error"
    class ErrorCategory:
        NETWORK = "network"
    class ErrorSeverity:
        HIGH = "high"
    class ErrorSummary:
        def __init__(self, *args, **kwargs): pass

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Trend direction for error analysis."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


class ImpactLevel(Enum):
    """Impact level for error assessment."""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorPattern:
    """Represents a detected error pattern."""
    
    pattern_id: str
    pattern_type: str
    description: str
    frequency: int
    first_occurrence: datetime
    last_occurrence: datetime
    affected_operations: List[str]
    error_types: List[ErrorType]
    confidence_score: float
    
    @property
    def duration(self) -> timedelta:
        """Get the duration of this pattern."""
        return self.last_occurrence - self.first_occurrence
    
    @property
    def frequency_per_day(self) -> float:
        """Calculate frequency per day."""
        duration_days = max(1, self.duration.days)
        return self.frequency / duration_days


@dataclass
class ErrorTrend:
    """Represents an error trend analysis."""
    
    error_type: ErrorType
    time_period: timedelta
    direction: TrendDirection
    change_rate: float  # Percentage change
    current_frequency: float
    previous_frequency: float
    confidence: float
    
    @property
    def is_concerning(self) -> bool:
        """Check if this trend is concerning."""
        return (self.direction == TrendDirection.INCREASING and 
                self.change_rate > 50.0 and 
                self.confidence > 0.7)


@dataclass
class ErrorImpactAssessment:
    """Assessment of error impact on system operations."""
    
    error_type: ErrorType
    impact_level: ImpactLevel
    affected_instances: List[str]
    affected_operations: List[str]
    estimated_downtime_minutes: float
    data_loss_risk: bool
    user_impact_score: float  # 0-10 scale
    business_impact_score: float  # 0-10 scale
    
    @property
    def overall_impact_score(self) -> float:
        """Calculate overall impact score."""
        base_score = (self.user_impact_score + self.business_impact_score) / 2
        
        # Adjust for downtime
        if self.estimated_downtime_minutes > 60:
            base_score += 2
        elif self.estimated_downtime_minutes > 15:
            base_score += 1
        
        # Adjust for data loss risk
        if self.data_loss_risk:
            base_score += 2
        
        return min(10.0, base_score)


@dataclass
class ResolutionSuggestion:
    """Automated resolution suggestion for errors."""
    
    suggestion_id: str
    error_types: List[ErrorType]
    title: str
    description: str
    implementation_steps: List[str]
    estimated_effort_hours: float
    success_probability: float
    risk_level: str  # "low", "medium", "high"
    prerequisites: List[str] = field(default_factory=list)
    
    @property
    def priority_score(self) -> float:
        """Calculate priority score for this suggestion."""
        base_score = self.success_probability * 10
        
        # Adjust for effort (lower effort = higher priority)
        effort_factor = max(0.1, 1.0 - (self.estimated_effort_hours / 40))
        base_score *= effort_factor
        
        # Adjust for risk (lower risk = higher priority)
        risk_factors = {"low": 1.0, "medium": 0.8, "high": 0.5}
        base_score *= risk_factors.get(self.risk_level, 0.5)
        
        return base_score


class ErrorAnalyzer:
    """
    Comprehensive error analyzer with pattern detection, trend analysis,
    and automated resolution suggestions.
    """
    
    def __init__(self, instance_name: str):
        self.instance_name = instance_name
        
        # Analysis data
        self.error_history: List[ProcessingError] = []
        self.detected_patterns: List[ErrorPattern] = []
        self.trend_analysis: Dict[ErrorType, ErrorTrend] = {}
        self.impact_assessments: Dict[ErrorType, ErrorImpactAssessment] = {}
        self.resolution_suggestions: List[ResolutionSuggestion] = []
        
        # Analysis configuration
        self.pattern_detection_window = timedelta(days=7)
        self.trend_analysis_window = timedelta(days=30)
        self.min_pattern_frequency = 3
        self.min_trend_confidence = 0.6
        
        # Initialize resolution knowledge base
        self._initialize_resolution_knowledge_base()
        
        logger.info(f"ErrorAnalyzer initialized for {instance_name}")
    
    def add_error(self, error: ProcessingError) -> None:
        """Add an error to the analysis dataset."""
        
        self.error_history.append(error)
        
        # Keep only recent errors for analysis
        cutoff_time = datetime.now() - timedelta(days=90)
        self.error_history = [
            e for e in self.error_history 
            if e.timestamp >= cutoff_time
        ]
        
        logger.debug(f"Added error to analysis: {error.error_type.value}")
    
    async def perform_comprehensive_analysis(self) -> Dict[str, Any]:
        """Perform comprehensive error analysis."""
        
        logger.info(f"Starting comprehensive error analysis for {self.instance_name}")
        
        # Clear previous analysis results
        self.detected_patterns.clear()
        self.trend_analysis.clear()
        self.impact_assessments.clear()
        self.resolution_suggestions.clear()
        
        # Perform different types of analysis
        await self._detect_error_patterns()
        await self._analyze_error_trends()
        await self._assess_error_impacts()
        await self._generate_resolution_suggestions()
        
        # Compile comprehensive report
        analysis_report = {
            'instance_name': self.instance_name,
            'analysis_timestamp': datetime.now().isoformat(),
            'total_errors_analyzed': len(self.error_history),
            'analysis_period_days': 90,
            'patterns_detected': len(self.detected_patterns),
            'trends_analyzed': len(self.trend_analysis),
            'impact_assessments': len(self.impact_assessments),
            'resolution_suggestions': len(self.resolution_suggestions),
            'summary': await self._generate_analysis_summary()
        }
        
        logger.info(f"Comprehensive analysis completed for {self.instance_name}")
        return analysis_report
    
    async def _detect_error_patterns(self) -> None:
        """Detect recurring error patterns."""
        
        logger.info("Detecting error patterns")
        
        if len(self.error_history) < self.min_pattern_frequency:
            return
        
        # Group errors by various criteria
        patterns_by_type = self._group_errors_by_type()
        patterns_by_operation = self._group_errors_by_operation()
        patterns_by_time = self._group_errors_by_time_pattern()
        
        # Analyze each pattern group
        for pattern_type, groups in [
            ("error_type", patterns_by_type),
            ("operation", patterns_by_operation),
            ("time_pattern", patterns_by_time)
        ]:
            for group_key, errors in groups.items():
                if len(errors) >= self.min_pattern_frequency:
                    pattern = await self._create_error_pattern(
                        pattern_type, group_key, errors
                    )
                    if pattern:
                        self.detected_patterns.append(pattern)
        
        # Sort patterns by frequency
        self.detected_patterns.sort(key=lambda p: p.frequency, reverse=True)
        
        logger.info(f"Detected {len(self.detected_patterns)} error patterns")
    
    def _group_errors_by_type(self) -> Dict[str, List[ProcessingError]]:
        """Group errors by error type."""
        
        groups = defaultdict(list)
        for error in self.error_history:
            groups[error.error_type.value].append(error)
        return dict(groups)
    
    def _group_errors_by_operation(self) -> Dict[str, List[ProcessingError]]:
        """Group errors by operation type."""
        
        groups = defaultdict(list)
        for error in self.error_history:
            operation = error.context.operation if hasattr(error, 'context') else 'unknown'
            groups[operation].append(error)
        return dict(groups)
    
    def _group_errors_by_time_pattern(self) -> Dict[str, List[ProcessingError]]:
        """Group errors by time patterns (hour of day, day of week)."""
        
        groups = defaultdict(list)
        for error in self.error_history:
            # Group by hour of day
            hour_key = f"hour_{error.timestamp.hour}"
            groups[hour_key].append(error)
            
            # Group by day of week
            day_key = f"weekday_{error.timestamp.weekday()}"
            groups[day_key].append(error)
        
        return dict(groups)
    
    async def _create_error_pattern(
        self, 
        pattern_type: str, 
        group_key: str, 
        errors: List[ProcessingError]
    ) -> Optional[ErrorPattern]:
        """Create an error pattern from a group of errors."""
        
        if not errors:
            return None
        
        # Calculate pattern statistics
        timestamps = [e.timestamp for e in errors]
        operations = list(set(e.context.operation for e in errors if hasattr(e, 'context')))
        error_types = list(set(e.error_type for e in errors))
        
        # Calculate confidence score based on frequency and consistency
        frequency = len(errors)
        time_span = (max(timestamps) - min(timestamps)).total_seconds()
        consistency = frequency / max(1, time_span / 3600)  # Errors per hour
        confidence = min(1.0, consistency / 10)  # Normalize to 0-1
        
        pattern_id = f"{self.instance_name}_{pattern_type}_{group_key}_{int(datetime.now().timestamp())}"
        
        return ErrorPattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            description=f"Recurring {pattern_type} pattern: {group_key}",
            frequency=frequency,
            first_occurrence=min(timestamps),
            last_occurrence=max(timestamps),
            affected_operations=operations,
            error_types=error_types,
            confidence_score=confidence
        )
    
    async def _analyze_error_trends(self) -> None:
        """Analyze error trends over time."""
        
        logger.info("Analyzing error trends")
        
        # Get errors from the trend analysis window
        cutoff_time = datetime.now() - self.trend_analysis_window
        recent_errors = [e for e in self.error_history if e.timestamp >= cutoff_time]
        
        if len(recent_errors) < 10:  # Need minimum data for trend analysis
            return
        
        # Group errors by type and analyze trends
        error_groups = self._group_errors_by_type()
        
        for error_type_str, errors in error_groups.items():
            try:
                error_type = ErrorType(error_type_str)
                trend = await self._calculate_error_trend(error_type, errors)
                if trend and trend.confidence >= self.min_trend_confidence:
                    self.trend_analysis[error_type] = trend
            except ValueError:
                continue  # Skip invalid error types
        
        logger.info(f"Analyzed trends for {len(self.trend_analysis)} error types")
    
    async def _calculate_error_trend(
        self, 
        error_type: ErrorType, 
        errors: List[ProcessingError]
    ) -> Optional[ErrorTrend]:
        """Calculate trend for a specific error type."""
        
        # Filter errors within trend analysis window
        cutoff_time = datetime.now() - self.trend_analysis_window
        recent_errors = [e for e in errors if e.timestamp >= cutoff_time]
        
        if len(recent_errors) < 3:
            return None
        
        # Split time period in half for comparison
        mid_time = cutoff_time + (self.trend_analysis_window / 2)
        
        first_half_errors = [e for e in recent_errors if e.timestamp < mid_time]
        second_half_errors = [e for e in recent_errors if e.timestamp >= mid_time]
        
        # Calculate frequencies
        first_half_freq = len(first_half_errors) / (self.trend_analysis_window.days / 2)
        second_half_freq = len(second_half_errors) / (self.trend_analysis_window.days / 2)
        
        # Calculate change rate
        if first_half_freq == 0:
            change_rate = 100.0 if second_half_freq > 0 else 0.0
        else:
            change_rate = ((second_half_freq - first_half_freq) / first_half_freq) * 100
        
        # Determine trend direction
        if abs(change_rate) < 10:
            direction = TrendDirection.STABLE
        elif change_rate > 0:
            direction = TrendDirection.INCREASING
        else:
            direction = TrendDirection.DECREASING
        
        # Calculate confidence based on data consistency
        confidence = min(1.0, len(recent_errors) / 20)  # More data = higher confidence
        
        return ErrorTrend(
            error_type=error_type,
            time_period=self.trend_analysis_window,
            direction=direction,
            change_rate=change_rate,
            current_frequency=second_half_freq,
            previous_frequency=first_half_freq,
            confidence=confidence
        )
    
    async def _assess_error_impacts(self) -> None:
        """Assess the impact of different error types."""
        
        logger.info("Assessing error impacts")
        
        error_groups = self._group_errors_by_type()
        
        for error_type_str, errors in error_groups.items():
            try:
                error_type = ErrorType(error_type_str)
                impact = await self._calculate_error_impact(error_type, errors)
                if impact:
                    self.impact_assessments[error_type] = impact
            except ValueError:
                continue
        
        logger.info(f"Assessed impacts for {len(self.impact_assessments)} error types")
    
    async def _calculate_error_impact(
        self, 
        error_type: ErrorType, 
        errors: List[ProcessingError]
    ) -> Optional[ErrorImpactAssessment]:
        """Calculate impact assessment for an error type."""
        
        if not errors:
            return None
        
        # Analyze affected instances and operations
        affected_instances = list(set(e.instance_name for e in errors))
        affected_operations = list(set(
            e.context.operation for e in errors 
            if hasattr(e, 'context') and e.context.operation
        ))
        
        # Estimate downtime based on error type and frequency
        downtime_estimates = {
            ErrorType.DISK_FULL: 30.0,
            ErrorType.MEMORY_ERROR: 15.0,
            ErrorType.CONNECTION_TIMEOUT: 2.0,
            ErrorType.PDF_CORRUPT: 0.1,
            ErrorType.PERMISSION_DENIED: 5.0
        }
        
        estimated_downtime = downtime_estimates.get(error_type, 1.0) * len(errors)
        
        # Assess data loss risk
        data_loss_risks = {
            ErrorType.DISK_FULL: True,
            ErrorType.IO_ERROR: True,
            ErrorType.PERMISSION_DENIED: True
        }
        data_loss_risk = data_loss_risks.get(error_type, False)
        
        # Calculate impact scores
        user_impact = self._calculate_user_impact_score(error_type, errors)
        business_impact = self._calculate_business_impact_score(error_type, errors)
        
        # Determine impact level
        overall_score = (user_impact + business_impact) / 2
        if overall_score >= 8:
            impact_level = ImpactLevel.CRITICAL
        elif overall_score >= 6:
            impact_level = ImpactLevel.HIGH
        elif overall_score >= 4:
            impact_level = ImpactLevel.MODERATE
        elif overall_score >= 2:
            impact_level = ImpactLevel.LOW
        else:
            impact_level = ImpactLevel.MINIMAL
        
        return ErrorImpactAssessment(
            error_type=error_type,
            impact_level=impact_level,
            affected_instances=affected_instances,
            affected_operations=affected_operations,
            estimated_downtime_minutes=estimated_downtime,
            data_loss_risk=data_loss_risk,
            user_impact_score=user_impact,
            business_impact_score=business_impact
        )
    
    def _calculate_user_impact_score(self, error_type: ErrorType, errors: List[ProcessingError]) -> float:
        """Calculate user impact score (0-10)."""
        
        base_scores = {
            ErrorType.DISK_FULL: 8.0,
            ErrorType.MEMORY_ERROR: 7.0,
            ErrorType.CONNECTION_TIMEOUT: 4.0,
            ErrorType.HTTP_ERROR: 3.0,
            ErrorType.PDF_CORRUPT: 1.0,
            ErrorType.PERMISSION_DENIED: 6.0
        }
        
        base_score = base_scores.get(error_type, 3.0)
        
        # Adjust based on frequency
        frequency_factor = min(2.0, len(errors) / 10)
        
        return min(10.0, base_score + frequency_factor)
    
    def _calculate_business_impact_score(self, error_type: ErrorType, errors: List[ProcessingError]) -> float:
        """Calculate business impact score (0-10)."""
        
        base_scores = {
            ErrorType.DISK_FULL: 9.0,
            ErrorType.MEMORY_ERROR: 8.0,
            ErrorType.CONNECTION_TIMEOUT: 5.0,
            ErrorType.HTTP_ERROR: 4.0,
            ErrorType.PDF_CORRUPT: 2.0,
            ErrorType.PERMISSION_DENIED: 7.0
        }
        
        base_score = base_scores.get(error_type, 4.0)
        
        # Adjust based on affected operations
        critical_operations = ['download_paper', 'process_pdf', 'store_embeddings']
        affected_operations = list(set(
            e.context.operation for e in errors 
            if hasattr(e, 'context') and e.context.operation
        ))
        
        critical_affected = sum(1 for op in affected_operations if op in critical_operations)
        operation_factor = critical_affected * 0.5
        
        return min(10.0, base_score + operation_factor)
    
    async def _generate_resolution_suggestions(self) -> None:
        """Generate automated resolution suggestions."""
        
        logger.info("Generating resolution suggestions")
        
        # Generate suggestions based on detected patterns and trends
        for pattern in self.detected_patterns:
            suggestions = await self._get_pattern_suggestions(pattern)
            self.resolution_suggestions.extend(suggestions)
        
        for error_type, trend in self.trend_analysis.items():
            if trend.is_concerning:
                suggestions = await self._get_trend_suggestions(error_type, trend)
                self.resolution_suggestions.extend(suggestions)
        
        for error_type, impact in self.impact_assessments.items():
            if impact.impact_level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]:
                suggestions = await self._get_impact_suggestions(error_type, impact)
                self.resolution_suggestions.extend(suggestions)
        
        # Remove duplicates and sort by priority
        unique_suggestions = {}
        for suggestion in self.resolution_suggestions:
            if suggestion.suggestion_id not in unique_suggestions:
                unique_suggestions[suggestion.suggestion_id] = suggestion
        
        self.resolution_suggestions = list(unique_suggestions.values())
        self.resolution_suggestions.sort(key=lambda s: s.priority_score, reverse=True)
        
        logger.info(f"Generated {len(self.resolution_suggestions)} resolution suggestions")
    
    async def _get_pattern_suggestions(self, pattern: ErrorPattern) -> List[ResolutionSuggestion]:
        """Get resolution suggestions for a detected pattern."""
        
        suggestions = []
        
        # Pattern-specific suggestions
        if pattern.pattern_type == "time_pattern":
            if "hour_" in pattern.description:
                suggestions.append(ResolutionSuggestion(
                    suggestion_id=f"schedule_maintenance_{pattern.pattern_id}",
                    error_types=pattern.error_types,
                    title="Schedule Maintenance During Low-Error Periods",
                    description=f"Pattern shows errors occur frequently during specific hours. Schedule maintenance during low-error periods.",
                    implementation_steps=[
                        "Analyze error frequency by hour",
                        "Identify low-error time windows",
                        "Schedule maintenance and updates during these windows",
                        "Monitor error rates after implementation"
                    ],
                    estimated_effort_hours=4.0,
                    success_probability=0.7,
                    risk_level="low"
                ))
        
        elif pattern.frequency > 10:
            suggestions.append(ResolutionSuggestion(
                suggestion_id=f"investigate_root_cause_{pattern.pattern_id}",
                error_types=pattern.error_types,
                title="Investigate Root Cause of Recurring Pattern",
                description=f"High-frequency pattern detected ({pattern.frequency} occurrences). Root cause analysis needed.",
                implementation_steps=[
                    "Collect detailed logs for pattern occurrences",
                    "Analyze common factors across occurrences",
                    "Identify root cause",
                    "Implement targeted fix",
                    "Monitor for pattern recurrence"
                ],
                estimated_effort_hours=8.0,
                success_probability=0.8,
                risk_level="medium"
            ))
        
        return suggestions
    
    async def _get_trend_suggestions(self, error_type: ErrorType, trend: ErrorTrend) -> List[ResolutionSuggestion]:
        """Get resolution suggestions for concerning trends."""
        
        suggestions = []
        
        if trend.direction == TrendDirection.INCREASING:
            suggestions.append(ResolutionSuggestion(
                suggestion_id=f"address_increasing_trend_{error_type.value}",
                error_types=[error_type],
                title=f"Address Increasing {error_type.value} Trend",
                description=f"Error rate increasing by {trend.change_rate:.1f}%. Immediate attention required.",
                implementation_steps=[
                    "Implement enhanced monitoring for this error type",
                    "Increase retry attempts and timeout values",
                    "Add circuit breaker patterns",
                    "Review and optimize related code paths",
                    "Set up automated alerts for threshold breaches"
                ],
                estimated_effort_hours=12.0,
                success_probability=0.75,
                risk_level="medium"
            ))
        
        return suggestions
    
    async def _get_impact_suggestions(self, error_type: ErrorType, impact: ErrorImpactAssessment) -> List[ResolutionSuggestion]:
        """Get resolution suggestions for high-impact errors."""
        
        suggestions = []
        
        if impact.impact_level == ImpactLevel.CRITICAL:
            suggestions.append(ResolutionSuggestion(
                suggestion_id=f"critical_impact_mitigation_{error_type.value}",
                error_types=[error_type],
                title=f"Critical Impact Mitigation for {error_type.value}",
                description=f"Critical impact error requiring immediate mitigation (Impact Score: {impact.overall_impact_score:.1f}).",
                implementation_steps=[
                    "Implement immediate error prevention measures",
                    "Add comprehensive monitoring and alerting",
                    "Create automated recovery procedures",
                    "Implement graceful degradation",
                    "Set up 24/7 monitoring for this error type"
                ],
                estimated_effort_hours=20.0,
                success_probability=0.9,
                risk_level="high",
                prerequisites=["Management approval", "Emergency change process"]
            ))
        
        return suggestions
    
    def _initialize_resolution_knowledge_base(self) -> None:
        """Initialize the knowledge base of resolution strategies."""
        
        # This would be expanded with more sophisticated resolution strategies
        # based on historical data and expert knowledge
        pass
    
    async def _generate_analysis_summary(self) -> Dict[str, Any]:
        """Generate a summary of the analysis results."""
        
        # Most frequent error types
        error_type_counts = Counter(e.error_type for e in self.error_history)
        most_frequent_errors = error_type_counts.most_common(5)
        
        # Most concerning trends
        concerning_trends = [
            trend for trend in self.trend_analysis.values()
            if trend.is_concerning
        ]
        
        # Highest impact errors
        high_impact_errors = [
            error_type.value for error_type, impact in self.impact_assessments.items()
            if impact.impact_level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]
        ]
        
        # Top priority suggestions
        top_suggestions = self.resolution_suggestions[:3]
        
        return {
            'most_frequent_errors': [
                {'error_type': error_type.value, 'count': count}
                for error_type, count in most_frequent_errors
            ],
            'concerning_trends_count': len(concerning_trends),
            'high_impact_errors': high_impact_errors,
            'top_priority_suggestions': [
                {
                    'title': suggestion.title,
                    'priority_score': suggestion.priority_score,
                    'estimated_effort_hours': suggestion.estimated_effort_hours
                }
                for suggestion in top_suggestions
            ],
            'overall_error_rate': len(self.error_history) / max(1, self.trend_analysis_window.days),
            'pattern_detection_effectiveness': len(self.detected_patterns) / max(1, len(self.error_history)) * 100
        }
    
    def get_patterns(self) -> List[ErrorPattern]:
        """Get detected error patterns."""
        return self.detected_patterns.copy()
    
    def get_trends(self) -> Dict[ErrorType, ErrorTrend]:
        """Get error trend analysis."""
        return self.trend_analysis.copy()
    
    def get_impact_assessments(self) -> Dict[ErrorType, ErrorImpactAssessment]:
        """Get error impact assessments."""
        return self.impact_assessments.copy()
    
    def get_resolution_suggestions(self) -> List[ResolutionSuggestion]:
        """Get resolution suggestions."""
        return self.resolution_suggestions.copy()
    
    def export_analysis_report(self, file_path: str) -> None:
        """Export comprehensive analysis report to file."""
        
        report = {
            'instance_name': self.instance_name,
            'analysis_timestamp': datetime.now().isoformat(),
            'total_errors_analyzed': len(self.error_history),
            'patterns': [
                {
                    'pattern_id': p.pattern_id,
                    'pattern_type': p.pattern_type,
                    'description': p.description,
                    'frequency': p.frequency,
                    'confidence_score': p.confidence_score,
                    'duration_days': p.duration.days
                }
                for p in self.detected_patterns
            ],
            'trends': [
                {
                    'error_type': trend.error_type.value,
                    'direction': trend.direction.value,
                    'change_rate': trend.change_rate,
                    'confidence': trend.confidence,
                    'is_concerning': trend.is_concerning
                }
                for trend in self.trend_analysis.values()
            ],
            'impact_assessments': [
                {
                    'error_type': impact.error_type.value,
                    'impact_level': impact.impact_level.value,
                    'overall_impact_score': impact.overall_impact_score,
                    'estimated_downtime_minutes': impact.estimated_downtime_minutes,
                    'data_loss_risk': impact.data_loss_risk
                }
                for impact in self.impact_assessments.values()
            ],
            'resolution_suggestions': [
                {
                    'suggestion_id': suggestion.suggestion_id,
                    'title': suggestion.title,
                    'description': suggestion.description,
                    'priority_score': suggestion.priority_score,
                    'estimated_effort_hours': suggestion.estimated_effort_hours,
                    'success_probability': suggestion.success_probability,
                    'risk_level': suggestion.risk_level
                }
                for suggestion in self.resolution_suggestions
            ]
        }
        
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Analysis report exported to {file_path}")
        
        except Exception as e:
            logger.error(f"Failed to export analysis report: {e}")