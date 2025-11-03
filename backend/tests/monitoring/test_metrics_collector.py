"""Unit tests for metrics collection system."""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from collections import defaultdict

from backend.rl.monitoring.metrics_collector import (
    MetricType, MetricValue, MetricSummary, BaseMetricsCollector,
    MultiModalMetricsCollector, PersonalizationMetricsCollector,
    ResearchAssistantMetricsCollector, MetricsAggregator
)


class TestMetricValue:
    """Test cases for MetricValue class."""
    
    def test_metric_value_creation(self):
        """Test MetricValue creation and properties."""
        timestamp = datetime.now()
        tags = {"component": "test", "version": "1.0"}
        
        metric = MetricValue(
            name="test.metric",
            value=42.5,
            metric_type=MetricType.GAUGE,
            timestamp=timestamp,
            tags=tags,
            unit="seconds"
        )
        
        assert metric.name == "test.metric"
        assert metric.value == 42.5
        assert metric.metric_type == MetricType.GAUGE
        assert metric.timestamp == timestamp
        assert metric.tags == tags
        assert metric.unit == "seconds"
    
    def test_metric_value_to_dict(self):
        """Test MetricValue to_dict conversion."""
        timestamp = datetime.now()
        tags = {"env": "test"}
        
        metric = MetricValue(
            name="test.counter",
            value=10,
            metric_type=MetricType.COUNTER,
            timestamp=timestamp,
            tags=tags
        )
        
        metric_dict = metric.to_dict()
        
        assert metric_dict["name"] == "test.counter"
        assert metric_dict["value"] == 10
        assert metric_dict["type"] == "counter"
        assert metric_dict["timestamp"] == timestamp.isoformat()
        assert metric_dict["tags"] == tags
        assert metric_dict["unit"] == ""


class TestMetricSummary:
    """Test cases for MetricSummary class."""
    
    def test_metric_summary_creation(self):
        """Test MetricSummary creation."""
        timestamp = datetime.now()
        percentiles = {"p50": 5.0, "p90": 9.0, "p95": 9.5, "p99": 9.9}
        
        summary = MetricSummary(
            name="test.summary",
            count=100,
            sum=500.0,
            min=1.0,
            max=10.0,
            mean=5.0,
            std=2.5,
            percentiles=percentiles,
            timestamp=timestamp
        )
        
        assert summary.name == "test.summary"
        assert summary.count == 100
        assert summary.sum == 500.0
        assert summary.min == 1.0
        assert summary.max == 10.0
        assert summary.mean == 5.0
        assert summary.std == 2.5
        assert summary.percentiles == percentiles
        assert summary.timestamp == timestamp
    
    def test_metric_summary_to_dict(self):
        """Test MetricSummary to_dict conversion."""
        timestamp = datetime.now()
        percentiles = {"p50": 5.0, "p90": 9.0}
        
        summary = MetricSummary(
            name="test.summary",
            count=50,
            sum=250.0,
            min=2.0,
            max=8.0,
            mean=5.0,
            std=1.5,
            percentiles=percentiles,
            timestamp=timestamp
        )
        
        summary_dict = summary.to_dict()
        
        assert summary_dict["name"] == "test.summary"
        assert summary_dict["count"] == 50
        assert summary_dict["sum"] == 250.0
        assert summary_dict["percentiles"] == percentiles


class TestBaseMetricsCollector:
    """Test cases for BaseMetricsCollector class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        class TestCollector(BaseMetricsCollector):
            def collect_metrics(self):
                return {
                    "test_metric": MetricValue(
                        name="test.metric",
                        value=1.0,
                        metric_type=MetricType.GAUGE,
                        timestamp=datetime.now(),
                        tags={}
                    )
                }
        
        self.collector = TestCollector("test_component")
    
    def test_collector_initialization(self):
        """Test collector initialization."""
        assert self.collector.component_name == "test_component"
        assert self.collector.collection_enabled is True
        assert len(self.collector.metrics_buffer) == 0
        assert len(self.collector.aggregated_metrics) == 0
    
    def test_record_metric(self):
        """Test recording a metric."""
        tags = {"test": "value"}
        
        self.collector.record_metric(
            "test_metric", 42.0, MetricType.GAUGE, tags, "units"
        )
        
        assert len(self.collector.metrics_buffer) == 1
        
        metric = self.collector.metrics_buffer[0]
        assert metric.name == "test_component.test_metric"
        assert metric.value == 42.0
        assert metric.metric_type == MetricType.GAUGE
        assert metric.tags == tags
        assert metric.unit == "units"
    
    def test_increment_counter(self):
        """Test incrementing a counter metric."""
        self.collector.increment_counter("requests", 5, {"endpoint": "/api"})
        
        assert len(self.collector.metrics_buffer) == 1
        
        metric = self.collector.metrics_buffer[0]
        assert metric.name == "test_component.requests"
        assert metric.value == 5
        assert metric.metric_type == MetricType.COUNTER
        assert metric.tags == {"endpoint": "/api"}
    
    def test_set_gauge(self):
        """Test setting a gauge metric."""
        self.collector.set_gauge("memory_usage", 85.5, {"unit": "MB"}, "megabytes")
        
        assert len(self.collector.metrics_buffer) == 1
        
        metric = self.collector.metrics_buffer[0]
        assert metric.name == "test_component.memory_usage"
        assert metric.value == 85.5
        assert metric.metric_type == MetricType.GAUGE
        assert metric.unit == "megabytes"
    
    def test_record_histogram(self):
        """Test recording a histogram metric."""
        self.collector.record_histogram("response_time", 0.125, {"method": "GET"}, "seconds")
        
        assert len(self.collector.metrics_buffer) == 1
        
        metric = self.collector.metrics_buffer[0]
        assert metric.name == "test_component.response_time"
        assert metric.value == 0.125
        assert metric.metric_type == MetricType.HISTOGRAM
        assert metric.unit == "seconds"
    
    def test_record_timer(self):
        """Test recording a timer metric."""
        self.collector.record_timer("operation_duration", 2.5, {"operation": "process"})
        
        assert len(self.collector.metrics_buffer) == 1
        
        metric = self.collector.metrics_buffer[0]
        assert metric.name == "test_component.operation_duration"
        assert metric.value == 2.5
        assert metric.metric_type == MetricType.TIMER
        assert metric.unit == "seconds"
    
    def test_get_recent_metrics(self):
        """Test getting recent metrics."""
        # Add multiple metrics
        for i in range(10):
            self.collector.increment_counter(f"metric_{i}", 1)
        
        # Get recent metrics
        recent = self.collector.get_recent_metrics(5)
        
        assert len(recent) == 5
        assert all(isinstance(m, MetricValue) for m in recent)
        
        # Should get the last 5 metrics
        assert recent[-1].name == "test_component.metric_9"
    
    def test_get_metric_summary(self):
        """Test getting metric summary."""
        # Add multiple values for the same metric
        for i in range(10):
            self.collector.record_histogram("test_histogram", float(i))
        
        summary = self.collector.get_metric_summary("test_histogram")
        
        assert summary is not None
        assert summary.name == "test_component.test_histogram"
        assert summary.count == 10
        assert summary.sum == 45.0  # 0+1+2+...+9
        assert summary.min == 0.0
        assert summary.max == 9.0
        assert summary.mean == 4.5
        assert "p50" in summary.percentiles
        assert "p90" in summary.percentiles
        assert "p95" in summary.percentiles
        assert "p99" in summary.percentiles
    
    def test_get_metric_summary_with_time_window(self):
        """Test getting metric summary with time window."""
        # Add old metrics
        old_time = datetime.now() - timedelta(hours=2)
        for i in range(5):
            metric = MetricValue(
                name="test_component.old_metric",
                value=float(i),
                metric_type=MetricType.HISTOGRAM,
                timestamp=old_time,
                tags={}
            )
            self.collector.aggregated_metrics["test_component.old_metric"].append(metric)
        
        # Add recent metrics
        for i in range(5, 10):
            self.collector.record_histogram("old_metric", float(i))
        
        # Get summary for last hour
        summary = self.collector.get_metric_summary("old_metric", timedelta(hours=1))
        
        assert summary is not None
        assert summary.count == 5  # Only recent metrics
        assert summary.min == 5.0
        assert summary.max == 9.0
    
    def test_get_metric_summary_nonexistent(self):
        """Test getting summary for non-existent metric."""
        summary = self.collector.get_metric_summary("nonexistent_metric")
        assert summary is None
    
    def test_clear_metrics(self):
        """Test clearing metrics."""
        # Add some metrics
        for i in range(5):
            self.collector.increment_counter(f"metric_{i}", 1)
        
        assert len(self.collector.metrics_buffer) == 5
        assert len(self.collector.aggregated_metrics) == 5
        
        # Clear all metrics
        self.collector.clear_metrics()
        
        assert len(self.collector.metrics_buffer) == 0
        assert len(self.collector.aggregated_metrics) == 0
    
    def test_clear_metrics_with_time_window(self):
        """Test clearing metrics with time window."""
        # Add old metrics
        old_time = datetime.now() - timedelta(hours=2)
        for i in range(3):
            metric = MetricValue(
                name="test_component.old_metric",
                value=float(i),
                metric_type=MetricType.COUNTER,
                timestamp=old_time,
                tags={}
            )
            self.collector.aggregated_metrics["test_component.old_metric"].append(metric)
        
        # Add recent metrics
        for i in range(3, 6):
            self.collector.increment_counter("old_metric", 1)
        
        # Clear metrics older than 1 hour
        self.collector.clear_metrics(timedelta(hours=1))
        
        # Should only have recent metrics
        assert len(self.collector.aggregated_metrics["test_component.old_metric"]) == 3
    
    def test_timer_context(self):
        """Test timer context manager."""
        with self.collector.timer_context("test_operation", {"type": "test"}):
            time.sleep(0.01)  # Small delay
        
        assert len(self.collector.metrics_buffer) == 1
        
        metric = self.collector.metrics_buffer[0]
        assert metric.name == "test_component.test_operation"
        assert metric.metric_type == MetricType.TIMER
        assert metric.value > 0.01  # Should be at least the sleep time
        assert metric.tags == {"type": "test"}
        assert metric.unit == "seconds"
    
    def test_collection_disabled(self):
        """Test that metrics are not collected when disabled."""
        self.collector.collection_enabled = False
        
        self.collector.increment_counter("disabled_metric", 1)
        
        assert len(self.collector.metrics_buffer) == 0
        assert len(self.collector.aggregated_metrics) == 0


class TestMultiModalMetricsCollector:
    """Test cases for MultiModalMetricsCollector."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.collector = MultiModalMetricsCollector()
    
    def test_initialization(self):
        """Test collector initialization."""
        assert self.collector.component_name == "multimodal"
        assert self.collector.processing_stats["documents_processed"] == 0
        assert self.collector.processing_stats["visual_elements_processed"] == 0
        assert self.collector.processing_stats["feature_integrations"] == 0
        assert self.collector.processing_stats["processing_errors"] == 0
    
    def test_collect_metrics(self):
        """Test collecting multi-modal metrics."""
        # Set some processing stats
        self.collector.processing_stats["documents_processed"] = 10
        self.collector.processing_stats["visual_elements_processed"] = 25
        self.collector.processing_stats["feature_integrations"] = 8
        self.collector.processing_stats["processing_errors"] = 1
        
        metrics = self.collector.collect_metrics()
        
        assert "documents_processed_total" in metrics
        assert "visual_elements_processed_total" in metrics
        assert "feature_integrations_total" in metrics
        assert "error_rate" in metrics
        
        # Check values
        assert metrics["documents_processed_total"].value == 10
        assert metrics["visual_elements_processed_total"].value == 25
        assert metrics["feature_integrations_total"].value == 8
        
        # Error rate should be 1/44 (1 error out of 44 total operations)
        expected_error_rate = 1 / 44
        assert abs(metrics["error_rate"].value - expected_error_rate) < 0.001
    
    def test_record_document_processing(self):
        """Test recording document processing metrics."""
        self.collector.record_document_processing(
            processing_time=2.5,
            visual_elements_count=3,
            success=True
        )
        
        assert self.collector.processing_stats["documents_processed"] == 1
        assert self.collector.processing_stats["visual_elements_processed"] == 3
        assert self.collector.processing_stats["processing_errors"] == 0
        
        # Check recorded metrics
        assert len(self.collector.metrics_buffer) == 2  # timer + gauge
        
        timer_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.TIMER]
        assert len(timer_metrics) == 1
        assert timer_metrics[0].value == 2.5
        assert timer_metrics[0].tags["success"] == "True"
    
    def test_record_document_processing_failure(self):
        """Test recording failed document processing."""
        self.collector.record_document_processing(
            processing_time=1.0,
            visual_elements_count=2,
            success=False
        )
        
        assert self.collector.processing_stats["documents_processed"] == 1
        assert self.collector.processing_stats["processing_errors"] == 1
        
        timer_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.TIMER]
        assert timer_metrics[0].tags["success"] == "False"
    
    def test_record_feature_integration(self):
        """Test recording feature integration metrics."""
        self.collector.record_feature_integration(
            integration_time=0.5,
            text_features_count=100,
            visual_features_count=50,
            success=True
        )
        
        assert self.collector.processing_stats["feature_integrations"] == 1
        assert self.collector.processing_stats["processing_errors"] == 0
        
        # Check recorded metrics
        timer_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.TIMER]
        gauge_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.GAUGE]
        
        assert len(timer_metrics) == 1
        assert len(gauge_metrics) == 2  # text and visual features count
        
        assert timer_metrics[0].value == 0.5
        assert timer_metrics[0].tags["success"] == "True"
    
    def test_record_visual_processing_quality(self):
        """Test recording visual processing quality metrics."""
        self.collector.record_visual_processing_quality(0.85, "chart")
        
        histogram_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.HISTOGRAM]
        assert len(histogram_metrics) == 1
        
        metric = histogram_metrics[0]
        assert metric.value == 0.85
        assert metric.tags["element_type"] == "chart"


class TestPersonalizationMetricsCollector:
    """Test cases for PersonalizationMetricsCollector."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.collector = PersonalizationMetricsCollector()
    
    def test_initialization(self):
        """Test collector initialization."""
        assert self.collector.component_name == "personalization"
        assert self.collector.adaptation_stats["adaptations_applied"] == 0
        assert self.collector.adaptation_stats["preference_updates"] == 0
        assert self.collector.adaptation_stats["behavior_predictions"] == 0
        assert self.collector.adaptation_stats["adaptation_failures"] == 0
        assert len(self.collector.user_metrics) == 0
    
    def test_collect_metrics(self):
        """Test collecting personalization metrics."""
        # Set some stats
        self.collector.adaptation_stats["adaptations_applied"] = 20
        self.collector.adaptation_stats["preference_updates"] = 15
        self.collector.adaptation_stats["behavior_predictions"] = 30
        self.collector.adaptation_stats["adaptation_failures"] = 2
        
        # Add user engagement data
        self.collector.user_metrics["user1"] = {"engagement_score": 0.8}
        self.collector.user_metrics["user2"] = {"engagement_score": 0.9}
        
        metrics = self.collector.collect_metrics()
        
        assert "adaptations_applied_total" in metrics
        assert "preference_updates_total" in metrics
        assert "behavior_predictions_total" in metrics
        assert "adaptation_success_rate" in metrics
        assert "average_user_engagement" in metrics
        
        # Check values
        assert metrics["adaptations_applied_total"].value == 20
        assert metrics["preference_updates_total"].value == 15
        assert metrics["behavior_predictions_total"].value == 30
        
        # Success rate should be (20-2)/20 = 0.9
        assert metrics["adaptation_success_rate"].value == 0.9
        
        # Average engagement should be (0.8+0.9)/2 = 0.85
        assert metrics["average_user_engagement"].value == 0.85
    
    def test_record_adaptation(self):
        """Test recording adaptation metrics."""
        self.collector.record_adaptation(
            user_id="user123",
            adaptation_type="preference_learning",
            adaptation_time=1.2,
            success=True,
            improvement_score=0.15
        )
        
        assert self.collector.adaptation_stats["adaptations_applied"] == 1
        assert self.collector.adaptation_stats["adaptation_failures"] == 0
        
        # Check user metrics
        assert "user123" in self.collector.user_metrics
        assert self.collector.user_metrics["user123"]["adaptation_count"] == 1
        
        # Check recorded metrics
        timer_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.TIMER]
        histogram_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.HISTOGRAM]
        
        assert len(timer_metrics) == 1
        assert len(histogram_metrics) == 1
        
        assert timer_metrics[0].value == 1.2
        assert timer_metrics[0].tags["type"] == "preference_learning"
        assert timer_metrics[0].tags["success"] == "True"
        
        assert histogram_metrics[0].value == 0.15
    
    def test_record_adaptation_failure(self):
        """Test recording failed adaptation."""
        self.collector.record_adaptation(
            user_id="user456",
            adaptation_type="behavior_prediction",
            adaptation_time=0.8,
            success=False
        )
        
        assert self.collector.adaptation_stats["adaptations_applied"] == 1
        assert self.collector.adaptation_stats["adaptation_failures"] == 1
        
        timer_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.TIMER]
        assert timer_metrics[0].tags["success"] == "False"
    
    def test_record_preference_learning(self):
        """Test recording preference learning metrics."""
        self.collector.record_preference_learning(
            user_id="user789",
            learning_time=2.0,
            preferences_updated=5,
            learning_accuracy=0.92
        )
        
        assert self.collector.adaptation_stats["preference_updates"] == 5
        
        # Check user metrics
        assert "user789" in self.collector.user_metrics
        assert self.collector.user_metrics["user789"]["learning_accuracy"] == 0.92
        assert self.collector.user_metrics["user789"]["preferences_count"] == 5
        
        # Check recorded metrics
        timer_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.TIMER]
        gauge_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.GAUGE]
        histogram_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.HISTOGRAM]
        
        assert len(timer_metrics) == 1
        assert len(gauge_metrics) == 1
        assert len(histogram_metrics) == 1
        
        assert timer_metrics[0].value == 2.0
        assert gauge_metrics[0].value == 5
        assert histogram_metrics[0].value == 0.92
    
    def test_record_behavior_prediction(self):
        """Test recording behavior prediction metrics."""
        self.collector.record_behavior_prediction(
            user_id="user101",
            prediction_time=0.3,
            confidence=0.88,
            prediction_type="next_action"
        )
        
        assert self.collector.adaptation_stats["behavior_predictions"] == 1
        
        timer_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.TIMER]
        histogram_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.HISTOGRAM]
        
        assert len(timer_metrics) == 1
        assert len(histogram_metrics) == 1
        
        assert timer_metrics[0].value == 0.3
        assert timer_metrics[0].tags["type"] == "next_action"
        
        assert histogram_metrics[0].value == 0.88
        assert histogram_metrics[0].tags["type"] == "next_action"
    
    def test_record_user_engagement(self):
        """Test recording user engagement metrics."""
        self.collector.record_user_engagement(
            user_id="user202",
            engagement_score=0.75,
            session_duration=1800.0
        )
        
        # Check user metrics
        assert "user202" in self.collector.user_metrics
        assert self.collector.user_metrics["user202"]["engagement_score"] == 0.75
        assert self.collector.user_metrics["user202"]["session_duration"] == 1800.0
        
        # Check recorded metrics
        histogram_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.HISTOGRAM]
        assert len(histogram_metrics) == 2  # engagement and session duration
        
        engagement_metrics = [m for m in histogram_metrics if "engagement" in m.name]
        duration_metrics = [m for m in histogram_metrics if "duration" in m.name]
        
        assert len(engagement_metrics) == 1
        assert len(duration_metrics) == 1
        
        assert engagement_metrics[0].value == 0.75
        assert duration_metrics[0].value == 1800.0
        assert duration_metrics[0].unit == "seconds"


class TestResearchAssistantMetricsCollector:
    """Test cases for ResearchAssistantMetricsCollector."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.collector = ResearchAssistantMetricsCollector()
    
    def test_initialization(self):
        """Test collector initialization."""
        assert self.collector.component_name == "research_assistant"
        assert self.collector.workflow_stats["workflows_optimized"] == 0
        assert self.collector.workflow_stats["patterns_learned"] == 0
        assert self.collector.workflow_stats["bottlenecks_identified"] == 0
        assert self.collector.workflow_stats["optimization_failures"] == 0
        assert len(self.collector.efficiency_metrics) == 0
    
    def test_collect_metrics(self):
        """Test collecting research assistant metrics."""
        # Set some stats
        self.collector.workflow_stats["workflows_optimized"] = 15
        self.collector.workflow_stats["patterns_learned"] = 8
        self.collector.workflow_stats["bottlenecks_identified"] = 12
        self.collector.workflow_stats["optimization_failures"] = 1
        
        # Add efficiency data
        self.collector.efficiency_metrics.extend([0.8, 0.9, 0.85])
        
        metrics = self.collector.collect_metrics()
        
        assert "workflows_optimized_total" in metrics
        assert "patterns_learned_total" in metrics
        assert "bottlenecks_identified_total" in metrics
        assert "average_workflow_efficiency" in metrics
        assert "optimization_success_rate" in metrics
        
        # Check values
        assert metrics["workflows_optimized_total"].value == 15
        assert metrics["patterns_learned_total"].value == 8
        assert metrics["bottlenecks_identified_total"].value == 12
        
        # Average efficiency should be (0.8+0.9+0.85)/3 = 0.85
        assert abs(metrics["average_workflow_efficiency"].value - 0.85) < 0.001
        
        # Success rate should be (15-1)/15 = 0.933...
        expected_success_rate = 14 / 15
        assert abs(metrics["optimization_success_rate"].value - expected_success_rate) < 0.001
    
    def test_record_workflow_optimization(self):
        """Test recording workflow optimization metrics."""
        self.collector.record_workflow_optimization(
            workflow_id="workflow123",
            optimization_time=3.5,
            efficiency_improvement=0.2,
            success=True
        )
        
        assert self.collector.workflow_stats["workflows_optimized"] == 1
        assert self.collector.workflow_stats["optimization_failures"] == 0
        assert len(self.collector.efficiency_metrics) == 1
        assert self.collector.efficiency_metrics[0] == 0.2
        
        # Check recorded metrics
        timer_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.TIMER]
        histogram_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.HISTOGRAM]
        
        assert len(timer_metrics) == 1
        assert len(histogram_metrics) == 1
        
        assert timer_metrics[0].value == 3.5
        assert timer_metrics[0].tags["success"] == "True"
        
        assert histogram_metrics[0].value == 0.2
    
    def test_record_workflow_optimization_failure(self):
        """Test recording failed workflow optimization."""
        self.collector.record_workflow_optimization(
            workflow_id="workflow456",
            optimization_time=1.0,
            efficiency_improvement=None,
            success=False
        )
        
        assert self.collector.workflow_stats["workflows_optimized"] == 1
        assert self.collector.workflow_stats["optimization_failures"] == 1
        assert len(self.collector.efficiency_metrics) == 0  # No improvement recorded
        
        timer_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.TIMER]
        assert timer_metrics[0].tags["success"] == "False"
    
    def test_record_pattern_learning(self):
        """Test recording pattern learning metrics."""
        self.collector.record_pattern_learning(
            patterns_count=5,
            learning_time=2.8,
            confidence=0.92,
            domain="machine_learning"
        )
        
        assert self.collector.workflow_stats["patterns_learned"] == 5
        
        # Check recorded metrics
        timer_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.TIMER]
        gauge_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.GAUGE]
        histogram_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.HISTOGRAM]
        
        assert len(timer_metrics) == 1
        assert len(gauge_metrics) == 1
        assert len(histogram_metrics) == 1
        
        assert timer_metrics[0].value == 2.8
        assert timer_metrics[0].tags["domain"] == "machine_learning"
        
        assert gauge_metrics[0].value == 5
        assert gauge_metrics[0].tags["domain"] == "machine_learning"
        
        assert histogram_metrics[0].value == 0.92
        assert histogram_metrics[0].tags["domain"] == "machine_learning"
    
    def test_record_bottleneck_identification(self):
        """Test recording bottleneck identification metrics."""
        self.collector.record_bottleneck_identification(
            bottlenecks_count=3,
            analysis_time=1.5,
            workflow_complexity=10
        )
        
        assert self.collector.workflow_stats["bottlenecks_identified"] == 3
        
        # Check recorded metrics
        timer_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.TIMER]
        gauge_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.GAUGE]
        
        assert len(timer_metrics) == 1
        assert len(gauge_metrics) == 2  # bottlenecks per workflow + complexity
        
        assert timer_metrics[0].value == 1.5
    
    def test_record_workflow_efficiency(self):
        """Test recording workflow efficiency metrics."""
        self.collector.record_workflow_efficiency(
            workflow_id="workflow789",
            efficiency_score=0.88,
            task_count=8,
            completion_time=3600.0
        )
        
        assert len(self.collector.efficiency_metrics) == 1
        assert self.collector.efficiency_metrics[0] == 0.88
        
        # Check recorded metrics
        gauge_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.GAUGE]
        histogram_metrics = [m for m in self.collector.metrics_buffer if m.metric_type == MetricType.HISTOGRAM]
        
        assert len(gauge_metrics) == 1
        assert len(histogram_metrics) == 2  # efficiency + completion time
        
        assert gauge_metrics[0].value == 8  # task count


class TestMetricsAggregator:
    """Test cases for MetricsAggregator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.aggregator = MetricsAggregator()
        
        # Create mock collectors
        self.mock_collector1 = Mock(spec=BaseMetricsCollector)
        self.mock_collector1.collect_metrics.return_value = {
            "metric1": MetricValue("test.metric1", 1.0, MetricType.GAUGE, datetime.now(), {})
        }
        
        self.mock_collector2 = Mock(spec=BaseMetricsCollector)
        self.mock_collector2.collect_metrics.return_value = {
            "metric2": MetricValue("test.metric2", 2.0, MetricType.COUNTER, datetime.now(), {})
        }
    
    def test_register_collector(self):
        """Test registering a collector."""
        self.aggregator.register_collector("test1", self.mock_collector1)
        
        assert "test1" in self.aggregator.collectors
        assert self.aggregator.collectors["test1"] == self.mock_collector1
    
    def test_unregister_collector(self):
        """Test unregistering a collector."""
        self.aggregator.register_collector("test1", self.mock_collector1)
        self.aggregator.unregister_collector("test1")
        
        assert "test1" not in self.aggregator.collectors
    
    def test_collect_all_metrics(self):
        """Test collecting metrics from all collectors."""
        self.aggregator.register_collector("collector1", self.mock_collector1)
        self.aggregator.register_collector("collector2", self.mock_collector2)
        
        all_metrics = self.aggregator.collect_all_metrics()
        
        assert "collector1" in all_metrics
        assert "collector2" in all_metrics
        assert "metric1" in all_metrics["collector1"]
        assert "metric2" in all_metrics["collector2"]
        
        self.mock_collector1.collect_metrics.assert_called_once()
        self.mock_collector2.collect_metrics.assert_called_once()
    
    def test_collect_all_metrics_with_error(self):
        """Test collecting metrics when one collector fails."""
        self.mock_collector1.collect_metrics.side_effect = Exception("Collection failed")
        
        self.aggregator.register_collector("collector1", self.mock_collector1)
        self.aggregator.register_collector("collector2", self.mock_collector2)
        
        all_metrics = self.aggregator.collect_all_metrics()
        
        # Should still collect from working collector
        assert "collector2" in all_metrics
        assert "collector1" not in all_metrics  # Failed collector excluded
    
    def test_get_system_summary(self):
        """Test getting system summary."""
        self.aggregator.register_collector("collector1", self.mock_collector1)
        self.aggregator.register_collector("collector2", self.mock_collector2)
        
        # Mock get_recent_metrics
        self.mock_collector1.get_recent_metrics.return_value = [Mock(), Mock()]
        self.mock_collector2.get_recent_metrics.return_value = [Mock()]
        
        summary = self.aggregator.get_system_summary()
        
        assert "timestamp" in summary
        assert summary["collectors_count"] == 2
        assert summary["total_metrics"] == 2  # 1 from each collector
        assert "collectors" in summary
        assert "collector1" in summary["collectors"]
        assert "collector2" in summary["collectors"]
        
        # Check collector summaries
        collector1_summary = summary["collectors"]["collector1"]
        assert collector1_summary["metrics_count"] == 1
        assert collector1_summary["status"] == "active"
        assert collector1_summary["recent_metrics_count"] == 2
    
    @pytest.mark.asyncio
    async def test_periodic_collection(self):
        """Test periodic metrics collection."""
        self.aggregator.register_collector("collector1", self.mock_collector1)
        
        # Start periodic collection with short interval
        self.aggregator.start_periodic_collection(0.1)
        
        # Wait for a few collection cycles
        await asyncio.sleep(0.25)
        
        # Stop collection
        self.aggregator.stop_periodic_collection()
        
        # Should have called collect_metrics multiple times
        assert self.mock_collector1.collect_metrics.call_count >= 2
    
    def test_export_metrics_json(self):
        """Test exporting metrics in JSON format."""
        self.aggregator.register_collector("collector1", self.mock_collector1)
        
        json_export = self.aggregator.export_metrics("json")
        
        # Should be valid JSON
        data = json.loads(json_export)
        
        assert "timestamp" in data
        assert "metrics" in data
        assert "collector1" in data["metrics"]
        assert "metric1" in data["metrics"]["collector1"]
    
    def test_export_metrics_prometheus(self):
        """Test exporting metrics in Prometheus format."""
        self.aggregator.register_collector("collector1", self.mock_collector1)
        
        prometheus_export = self.aggregator.export_metrics("prometheus")
        
        # Should contain Prometheus-formatted metrics
        assert "test_metric1" in prometheus_export
        assert "1.0" in prometheus_export
    
    def test_export_metrics_unsupported_format(self):
        """Test exporting metrics with unsupported format."""
        with pytest.raises(ValueError, match="Unsupported export format"):
            self.aggregator.export_metrics("unsupported_format")


if __name__ == "__main__":
    pytest.main([__file__])