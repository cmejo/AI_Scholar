"""Comprehensive metrics collection system for RL components."""

import asyncio
import time
import threading
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from enum import Enum
import numpy as np

from ..utils.logging_config import get_component_logger


class MetricType(Enum):
    """Types of metrics that can be collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"


@dataclass
class MetricValue:
    """Individual metric value with metadata."""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str]
    unit: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'value': self.value,
            'type': self.metric_type.value,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags,
            'unit': self.unit
        }


@dataclass
class MetricSummary:
    """Summary statistics for a metric over time."""
    name: str
    count: int
    sum: float
    min: float
    max: float
    mean: float
    std: float
    percentiles: Dict[str, float]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class BaseMetricsCollector(ABC):
    """Base class for metrics collectors."""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.logger = get_component_logger("metrics")
        self.metrics_buffer = deque(maxlen=10000)  # Buffer for recent metrics
        self.aggregated_metrics = defaultdict(list)
        self.collection_enabled = True
        self._lock = threading.Lock()
    
    @abstractmethod
    def collect_metrics(self) -> Dict[str, MetricValue]:
        """Collect current metrics. Must be implemented by subclasses."""
        pass
    
    def record_metric(self, name: str, value: Union[int, float], 
                     metric_type: MetricType, tags: Dict[str, str] = None,
                     unit: str = "") -> None:
        """Record a single metric value."""
        if not self.collection_enabled:
            return
        
        metric = MetricValue(
            name=f"{self.component_name}.{name}",
            value=value,
            metric_type=metric_type,
            timestamp=datetime.now(),
            tags=tags or {},
            unit=unit
        )
        
        with self._lock:
            self.metrics_buffer.append(metric)
            self.aggregated_metrics[metric.name].append(metric)
    
    def increment_counter(self, name: str, value: int = 1, 
                         tags: Dict[str, str] = None) -> None:
        """Increment a counter metric."""
        self.record_metric(name, value, MetricType.COUNTER, tags)
    
    def set_gauge(self, name: str, value: Union[int, float], 
                  tags: Dict[str, str] = None, unit: str = "") -> None:
        """Set a gauge metric value."""
        self.record_metric(name, value, MetricType.GAUGE, tags, unit)
    
    def record_histogram(self, name: str, value: float, 
                        tags: Dict[str, str] = None, unit: str = "") -> None:
        """Record a histogram metric value."""
        self.record_metric(name, value, MetricType.HISTOGRAM, tags, unit)
    
    def record_timer(self, name: str, duration: float, 
                    tags: Dict[str, str] = None) -> None:
        """Record a timer metric value."""
        self.record_metric(name, duration, MetricType.TIMER, tags, "seconds")
    
    def get_recent_metrics(self, limit: int = 100) -> List[MetricValue]:
        """Get recent metrics from buffer."""
        with self._lock:
            return list(self.metrics_buffer)[-limit:]
    
    def get_metric_summary(self, metric_name: str, 
                          time_window: timedelta = None) -> Optional[MetricSummary]:
        """Get summary statistics for a metric."""
        full_name = f"{self.component_name}.{metric_name}"
        
        with self._lock:
            if full_name not in self.aggregated_metrics:
                return None
            
            metrics = self.aggregated_metrics[full_name]
            
            # Filter by time window if specified
            if time_window:
                cutoff_time = datetime.now() - time_window
                metrics = [m for m in metrics if m.timestamp >= cutoff_time]
            
            if not metrics:
                return None
            
            values = [m.value for m in metrics]
            
            return MetricSummary(
                name=full_name,
                count=len(values),
                sum=sum(values),
                min=min(values),
                max=max(values),
                mean=np.mean(values),
                std=np.std(values),
                percentiles={
                    "p50": np.percentile(values, 50),
                    "p90": np.percentile(values, 90),
                    "p95": np.percentile(values, 95),
                    "p99": np.percentile(values, 99)
                },
                timestamp=datetime.now()
            )
    
    def clear_metrics(self, older_than: timedelta = None) -> None:
        """Clear metrics from buffer and aggregated storage."""
        with self._lock:
            if older_than:
                cutoff_time = datetime.now() - older_than
                # Clear old metrics from aggregated storage
                for metric_name in self.aggregated_metrics:
                    self.aggregated_metrics[metric_name] = [
                        m for m in self.aggregated_metrics[metric_name]
                        if m.timestamp >= cutoff_time
                    ]
            else:
                self.metrics_buffer.clear()
                self.aggregated_metrics.clear()
    
    def timer_context(self, name: str, tags: Dict[str, str] = None):
        """Context manager for timing operations."""
        class TimerContext:
            def __init__(self, collector, metric_name, metric_tags):
                self.collector = collector
                self.name = metric_name
                self.tags = metric_tags
                self.start_time = None
            
            def __enter__(self):
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                self.collector.record_timer(self.name, duration, self.tags)
        
        return TimerContext(self, name, tags)


class MultiModalMetricsCollector(BaseMetricsCollector):
    """Metrics collector for multi-modal processing components."""
    
    def __init__(self):
        super().__init__("multimodal")
        self.processing_stats = {
            "documents_processed": 0,
            "visual_elements_processed": 0,
            "feature_integrations": 0,
            "processing_errors": 0
        }
    
    def collect_metrics(self) -> Dict[str, MetricValue]:
        """Collect current multi-modal processing metrics."""
        metrics = {}
        
        # Processing volume metrics
        metrics["documents_processed_total"] = MetricValue(
            name="multimodal.documents_processed_total",
            value=self.processing_stats["documents_processed"],
            metric_type=MetricType.COUNTER,
            timestamp=datetime.now(),
            tags={"component": "visual_processor"},
            unit="documents"
        )
        
        metrics["visual_elements_processed_total"] = MetricValue(
            name="multimodal.visual_elements_processed_total",
            value=self.processing_stats["visual_elements_processed"],
            metric_type=MetricType.COUNTER,
            timestamp=datetime.now(),
            tags={"component": "visual_processor"},
            unit="elements"
        )
        
        metrics["feature_integrations_total"] = MetricValue(
            name="multimodal.feature_integrations_total",
            value=self.processing_stats["feature_integrations"],
            metric_type=MetricType.COUNTER,
            timestamp=datetime.now(),
            tags={"component": "feature_integrator"},
            unit="integrations"
        )
        
        # Error rate metrics
        total_operations = sum(self.processing_stats.values())
        error_rate = (self.processing_stats["processing_errors"] / total_operations 
                     if total_operations > 0 else 0)
        
        metrics["error_rate"] = MetricValue(
            name="multimodal.error_rate",
            value=error_rate,
            metric_type=MetricType.GAUGE,
            timestamp=datetime.now(),
            tags={},
            unit="ratio"
        )
        
        return metrics
    
    def record_document_processing(self, processing_time: float, 
                                 visual_elements_count: int,
                                 success: bool = True) -> None:
        """Record document processing metrics."""
        self.processing_stats["documents_processed"] += 1
        self.processing_stats["visual_elements_processed"] += visual_elements_count
        
        if not success:
            self.processing_stats["processing_errors"] += 1
        
        self.record_timer("document_processing_time", processing_time,
                         {"success": str(success)})
        self.set_gauge("visual_elements_per_document", visual_elements_count)
    
    def record_feature_integration(self, integration_time: float,
                                 text_features_count: int,
                                 visual_features_count: int,
                                 success: bool = True) -> None:
        """Record feature integration metrics."""
        self.processing_stats["feature_integrations"] += 1
        
        if not success:
            self.processing_stats["processing_errors"] += 1
        
        self.record_timer("feature_integration_time", integration_time,
                         {"success": str(success)})
        self.set_gauge("text_features_count", text_features_count)
        self.set_gauge("visual_features_count", visual_features_count)
    
    def record_visual_processing_quality(self, confidence_score: float,
                                       element_type: str) -> None:
        """Record visual processing quality metrics."""
        self.record_histogram("visual_processing_confidence", confidence_score,
                            {"element_type": element_type})


class PersonalizationMetricsCollector(BaseMetricsCollector):
    """Metrics collector for personalization system components."""
    
    def __init__(self):
        super().__init__("personalization")
        self.adaptation_stats = {
            "adaptations_applied": 0,
            "preference_updates": 0,
            "behavior_predictions": 0,
            "adaptation_failures": 0
        }
        self.user_metrics = defaultdict(dict)
    
    def collect_metrics(self) -> Dict[str, MetricValue]:
        """Collect current personalization metrics."""
        metrics = {}
        
        # Adaptation volume metrics
        metrics["adaptations_applied_total"] = MetricValue(
            name="personalization.adaptations_applied_total",
            value=self.adaptation_stats["adaptations_applied"],
            metric_type=MetricType.COUNTER,
            timestamp=datetime.now(),
            tags={"component": "adaptation_engine"},
            unit="adaptations"
        )
        
        metrics["preference_updates_total"] = MetricValue(
            name="personalization.preference_updates_total",
            value=self.adaptation_stats["preference_updates"],
            metric_type=MetricType.COUNTER,
            timestamp=datetime.now(),
            tags={"component": "preference_learner"},
            unit="updates"
        )
        
        metrics["behavior_predictions_total"] = MetricValue(
            name="personalization.behavior_predictions_total",
            value=self.adaptation_stats["behavior_predictions"],
            metric_type=MetricType.COUNTER,
            timestamp=datetime.now(),
            tags={"component": "behavior_predictor"},
            unit="predictions"
        )
        
        # Success rate metrics
        total_adaptations = self.adaptation_stats["adaptations_applied"]
        success_rate = ((total_adaptations - self.adaptation_stats["adaptation_failures"]) 
                       / total_adaptations if total_adaptations > 0 else 1.0)
        
        metrics["adaptation_success_rate"] = MetricValue(
            name="personalization.adaptation_success_rate",
            value=success_rate,
            metric_type=MetricType.GAUGE,
            timestamp=datetime.now(),
            tags={},
            unit="ratio"
        )
        
        # User engagement metrics
        if self.user_metrics:
            avg_engagement = np.mean([
                user_data.get("engagement_score", 0) 
                for user_data in self.user_metrics.values()
            ])
            
            metrics["average_user_engagement"] = MetricValue(
                name="personalization.average_user_engagement",
                value=avg_engagement,
                metric_type=MetricType.GAUGE,
                timestamp=datetime.now(),
                tags={},
                unit="score"
            )
        
        return metrics
    
    def record_adaptation(self, user_id: str, adaptation_type: str,
                         adaptation_time: float, success: bool = True,
                         improvement_score: float = None) -> None:
        """Record adaptation metrics."""
        self.adaptation_stats["adaptations_applied"] += 1
        
        if not success:
            self.adaptation_stats["adaptation_failures"] += 1
        
        self.record_timer("adaptation_time", adaptation_time,
                         {"type": adaptation_type, "success": str(success)})
        
        if improvement_score is not None:
            self.record_histogram("adaptation_improvement", improvement_score,
                                {"type": adaptation_type})
        
        # Update user-specific metrics
        if user_id not in self.user_metrics:
            self.user_metrics[user_id] = {}
        
        self.user_metrics[user_id]["last_adaptation"] = datetime.now()
        self.user_metrics[user_id]["adaptation_count"] = (
            self.user_metrics[user_id].get("adaptation_count", 0) + 1
        )
    
    def record_preference_learning(self, user_id: str, learning_time: float,
                                 preferences_updated: int,
                                 learning_accuracy: float) -> None:
        """Record preference learning metrics."""
        self.adaptation_stats["preference_updates"] += preferences_updated
        
        self.record_timer("preference_learning_time", learning_time)
        self.set_gauge("preferences_updated", preferences_updated)
        self.record_histogram("learning_accuracy", learning_accuracy)
        
        # Update user metrics
        if user_id not in self.user_metrics:
            self.user_metrics[user_id] = {}
        
        self.user_metrics[user_id]["learning_accuracy"] = learning_accuracy
        self.user_metrics[user_id]["preferences_count"] = preferences_updated
    
    def record_behavior_prediction(self, user_id: str, prediction_time: float,
                                 confidence: float, prediction_type: str) -> None:
        """Record behavior prediction metrics."""
        self.adaptation_stats["behavior_predictions"] += 1
        
        self.record_timer("behavior_prediction_time", prediction_time,
                         {"type": prediction_type})
        self.record_histogram("prediction_confidence", confidence,
                            {"type": prediction_type})
    
    def record_user_engagement(self, user_id: str, engagement_score: float,
                             session_duration: float) -> None:
        """Record user engagement metrics."""
        if user_id not in self.user_metrics:
            self.user_metrics[user_id] = {}
        
        self.user_metrics[user_id]["engagement_score"] = engagement_score
        self.user_metrics[user_id]["session_duration"] = session_duration
        
        self.record_histogram("user_engagement", engagement_score)
        self.record_histogram("session_duration", session_duration, unit="seconds")


class ResearchAssistantMetricsCollector(BaseMetricsCollector):
    """Metrics collector for research assistant components."""
    
    def __init__(self):
        super().__init__("research_assistant")
        self.workflow_stats = {
            "workflows_optimized": 0,
            "patterns_learned": 0,
            "bottlenecks_identified": 0,
            "optimization_failures": 0
        }
        self.efficiency_metrics = deque(maxlen=1000)
    
    def collect_metrics(self) -> Dict[str, MetricValue]:
        """Collect current research assistant metrics."""
        metrics = {}
        
        # Workflow optimization metrics
        metrics["workflows_optimized_total"] = MetricValue(
            name="research_assistant.workflows_optimized_total",
            value=self.workflow_stats["workflows_optimized"],
            metric_type=MetricType.COUNTER,
            timestamp=datetime.now(),
            tags={"component": "workflow_optimizer"},
            unit="workflows"
        )
        
        metrics["patterns_learned_total"] = MetricValue(
            name="research_assistant.patterns_learned_total",
            value=self.workflow_stats["patterns_learned"],
            metric_type=MetricType.COUNTER,
            timestamp=datetime.now(),
            tags={"component": "workflow_learner"},
            unit="patterns"
        )
        
        metrics["bottlenecks_identified_total"] = MetricValue(
            name="research_assistant.bottlenecks_identified_total",
            value=self.workflow_stats["bottlenecks_identified"],
            metric_type=MetricType.COUNTER,
            timestamp=datetime.now(),
            tags={"component": "bottleneck_analyzer"},
            unit="bottlenecks"
        )
        
        # Efficiency metrics
        if self.efficiency_metrics:
            avg_efficiency = np.mean(self.efficiency_metrics)
            metrics["average_workflow_efficiency"] = MetricValue(
                name="research_assistant.average_workflow_efficiency",
                value=avg_efficiency,
                metric_type=MetricType.GAUGE,
                timestamp=datetime.now(),
                tags={},
                unit="ratio"
            )
        
        # Success rate
        total_optimizations = self.workflow_stats["workflows_optimized"]
        success_rate = ((total_optimizations - self.workflow_stats["optimization_failures"])
                       / total_optimizations if total_optimizations > 0 else 1.0)
        
        metrics["optimization_success_rate"] = MetricValue(
            name="research_assistant.optimization_success_rate",
            value=success_rate,
            metric_type=MetricType.GAUGE,
            timestamp=datetime.now(),
            tags={},
            unit="ratio"
        )
        
        return metrics
    
    def record_workflow_optimization(self, workflow_id: str, optimization_time: float,
                                   efficiency_improvement: float,
                                   success: bool = True) -> None:
        """Record workflow optimization metrics."""
        self.workflow_stats["workflows_optimized"] += 1
        
        if not success:
            self.workflow_stats["optimization_failures"] += 1
        
        self.record_timer("workflow_optimization_time", optimization_time,
                         {"success": str(success)})
        
        if success and efficiency_improvement is not None:
            self.record_histogram("efficiency_improvement", efficiency_improvement)
            self.efficiency_metrics.append(efficiency_improvement)
    
    def record_pattern_learning(self, patterns_count: int, learning_time: float,
                              confidence: float, domain: str) -> None:
        """Record pattern learning metrics."""
        self.workflow_stats["patterns_learned"] += patterns_count
        
        self.record_timer("pattern_learning_time", learning_time,
                         {"domain": domain})
        self.set_gauge("patterns_learned_count", patterns_count,
                      {"domain": domain})
        self.record_histogram("pattern_confidence", confidence,
                            {"domain": domain})
    
    def record_bottleneck_identification(self, bottlenecks_count: int,
                                       analysis_time: float,
                                       workflow_complexity: int) -> None:
        """Record bottleneck identification metrics."""
        self.workflow_stats["bottlenecks_identified"] += bottlenecks_count
        
        self.record_timer("bottleneck_analysis_time", analysis_time)
        self.set_gauge("bottlenecks_per_workflow", bottlenecks_count)
        self.set_gauge("workflow_complexity", workflow_complexity)
    
    def record_workflow_efficiency(self, workflow_id: str, efficiency_score: float,
                                 task_count: int, completion_time: float) -> None:
        """Record workflow efficiency metrics."""
        self.efficiency_metrics.append(efficiency_score)
        
        self.record_histogram("workflow_efficiency", efficiency_score)
        self.set_gauge("workflow_task_count", task_count)
        self.record_histogram("workflow_completion_time", completion_time,
                            unit="seconds")


class MetricsAggregator:
    """Aggregates metrics from multiple collectors."""
    
    def __init__(self):
        self.collectors: Dict[str, BaseMetricsCollector] = {}
        self.logger = get_component_logger("metrics_aggregator")
        self.aggregation_enabled = True
        self._collection_interval = 60  # seconds
        self._collection_task = None
    
    def register_collector(self, name: str, collector: BaseMetricsCollector) -> None:
        """Register a metrics collector."""
        self.collectors[name] = collector
        self.logger.info(f"Registered metrics collector: {name}")
    
    def unregister_collector(self, name: str) -> None:
        """Unregister a metrics collector."""
        if name in self.collectors:
            del self.collectors[name]
            self.logger.info(f"Unregistered metrics collector: {name}")
    
    def collect_all_metrics(self) -> Dict[str, Dict[str, MetricValue]]:
        """Collect metrics from all registered collectors."""
        all_metrics = {}
        
        for collector_name, collector in self.collectors.items():
            try:
                collector_metrics = collector.collect_metrics()
                all_metrics[collector_name] = collector_metrics
            except Exception as e:
                self.logger.error(f"Failed to collect metrics from {collector_name}",
                                exception=e)
        
        return all_metrics
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get system-wide metrics summary."""
        all_metrics = self.collect_all_metrics()
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "collectors_count": len(self.collectors),
            "total_metrics": sum(len(metrics) for metrics in all_metrics.values()),
            "collectors": {}
        }
        
        for collector_name, metrics in all_metrics.items():
            collector_summary = {
                "metrics_count": len(metrics),
                "last_collection": datetime.now().isoformat(),
                "status": "active"
            }
            
            # Add collector-specific summaries
            if collector_name in self.collectors:
                collector = self.collectors[collector_name]
                recent_metrics = collector.get_recent_metrics(10)
                collector_summary["recent_metrics_count"] = len(recent_metrics)
            
            summary["collectors"][collector_name] = collector_summary
        
        return summary
    
    def start_periodic_collection(self, interval: int = None) -> None:
        """Start periodic metrics collection."""
        if interval:
            self._collection_interval = interval
        
        if self._collection_task is None or self._collection_task.done():
            self._collection_task = asyncio.create_task(self._periodic_collection())
            self.logger.info(f"Started periodic metrics collection (interval: {self._collection_interval}s)")
    
    def stop_periodic_collection(self) -> None:
        """Stop periodic metrics collection."""
        if self._collection_task and not self._collection_task.done():
            self._collection_task.cancel()
            self.logger.info("Stopped periodic metrics collection")
    
    async def _periodic_collection(self) -> None:
        """Periodic metrics collection task."""
        while self.aggregation_enabled:
            try:
                all_metrics = self.collect_all_metrics()
                
                # Log summary
                total_metrics = sum(len(metrics) for metrics in all_metrics.values())
                self.logger.info(f"Collected {total_metrics} metrics from {len(self.collectors)} collectors")
                
                await asyncio.sleep(self._collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Error in periodic metrics collection", exception=e)
                await asyncio.sleep(self._collection_interval)
    
    def export_metrics(self, format_type: str = "json") -> str:
        """Export all metrics in specified format."""
        all_metrics = self.collect_all_metrics()
        
        if format_type == "json":
            import json
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": {}
            }
            
            for collector_name, metrics in all_metrics.items():
                export_data["metrics"][collector_name] = {
                    name: metric.to_dict() for name, metric in metrics.items()
                }
            
            return json.dumps(export_data, indent=2)
        
        elif format_type == "prometheus":
            # Export in Prometheus format
            lines = []
            for collector_name, metrics in all_metrics.items():
                for metric_name, metric in metrics.items():
                    # Convert to Prometheus format
                    prom_name = metric_name.replace(".", "_")
                    tags_str = ",".join([f'{k}="{v}"' for k, v in metric.tags.items()])
                    if tags_str:
                        line = f"{prom_name}{{{tags_str}}} {metric.value}"
                    else:
                        line = f"{prom_name} {metric.value}"
                    lines.append(line)
            
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported export format: {format_type}")


# Global metrics collectors
multimodal_metrics = MultiModalMetricsCollector()
personalization_metrics = PersonalizationMetricsCollector()
research_assistant_metrics = ResearchAssistantMetricsCollector()

# Global metrics aggregator
metrics_aggregator = MetricsAggregator()
metrics_aggregator.register_collector("multimodal", multimodal_metrics)
metrics_aggregator.register_collector("personalization", personalization_metrics)
metrics_aggregator.register_collector("research_assistant", research_assistant_metrics)