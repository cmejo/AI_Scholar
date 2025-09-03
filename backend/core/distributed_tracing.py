"""
Distributed Tracing System for AI Scholar
Implements OpenTelemetry-based tracing for performance monitoring and debugging
"""

import time
import uuid
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from functools import wraps
import logging
import json

logger = logging.getLogger(__name__)

@dataclass
class SpanContext:
    """Span context for tracing"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Span:
    """Distributed tracing span"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "ok"  # ok, error, timeout
    duration: Optional[float] = None

class DistributedTracer:
    """Distributed tracing implementation"""
    
    def __init__(self, service_name: str = "ai-scholar"):
        self.service_name = service_name
        self.active_spans: Dict[str, Span] = {}
        self.completed_spans: List[Span] = []
        self.span_processors: List[Callable[[Span], None]] = []
        
        # Sampling configuration
        self.sampling_rate = 1.0  # Sample 100% by default
        
        # Context storage (thread-local equivalent for async)
        self.current_context: Optional[SpanContext] = None
    
    def start_span(self, operation_name: str, parent_context: Optional[SpanContext] = None) -> Span:
        """Start a new span"""
        trace_id = parent_context.trace_id if parent_context else self._generate_trace_id()
        span_id = self._generate_span_id()
        parent_span_id = parent_context.span_id if parent_context else None
        
        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=time.time()
        )
        
        # Add service information
        span.tags.update({
            "service.name": self.service_name,
            "span.kind": "internal"
        })
        
        self.active_spans[span_id] = span
        return span
    
    def finish_span(self, span: Span, status: str = "ok", error: Optional[Exception] = None):
        """Finish a span"""
        span.end_time = time.time()
        span.duration = span.end_time - span.start_time
        span.status = status
        
        if error:
            span.tags["error"] = True
            span.tags["error.message"] = str(error)
            span.tags["error.type"] = type(error).__name__
        
        # Remove from active spans
        if span.span_id in self.active_spans:
            del self.active_spans[span.span_id]
        
        # Add to completed spans
        self.completed_spans.append(span)
        
        # Process span through processors
        for processor in self.span_processors:
            try:
                processor(span)
            except Exception as e:
                logger.error(f"Error in span processor: {e}")
        
        # Keep only recent completed spans to prevent memory issues
        if len(self.completed_spans) > 1000:
            self.completed_spans = self.completed_spans[-1000:]
    
    def add_span_processor(self, processor: Callable[[Span], None]):
        """Add a span processor"""
        self.span_processors.append(processor)
    
    def _generate_trace_id(self) -> str:
        """Generate a unique trace ID"""
        return uuid.uuid4().hex
    
    def _generate_span_id(self) -> str:
        """Generate a unique span ID"""
        return uuid.uuid4().hex[:16]
    
    @asynccontextmanager
    async def trace_operation(self, operation_name: str, **tags):
        """Context manager for tracing operations"""
        span = self.start_span(operation_name)
        
        # Add tags
        for key, value in tags.items():
            span.tags[key] = value
        
        try:
            yield span
            self.finish_span(span, "ok")
        except Exception as e:
            self.finish_span(span, "error", e)
            raise
    
    def get_trace_stats(self) -> Dict[str, Any]:
        """Get tracing statistics"""
        total_spans = len(self.completed_spans)
        if total_spans == 0:
            return {"message": "No spans recorded"}
        
        # Calculate statistics
        durations = [span.duration for span in self.completed_spans if span.duration]
        error_count = sum(1 for span in self.completed_spans if span.status == "error")
        
        operations = {}
        for span in self.completed_spans:
            op_name = span.operation_name
            if op_name not in operations:
                operations[op_name] = {"count": 0, "total_duration": 0, "errors": 0}
            
            operations[op_name]["count"] += 1
            if span.duration:
                operations[op_name]["total_duration"] += span.duration
            if span.status == "error":
                operations[op_name]["errors"] += 1
        
        # Calculate averages
        for op_data in operations.values():
            if op_data["count"] > 0:
                op_data["avg_duration"] = op_data["total_duration"] / op_data["count"]
                op_data["error_rate"] = op_data["errors"] / op_data["count"]
        
        return {
            "total_spans": total_spans,
            "active_spans": len(self.active_spans),
            "error_rate": error_count / total_spans,
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "operations": operations
        }

class AIOperationTracer:
    """Specialized tracer for AI operations"""
    
    def __init__(self, tracer: DistributedTracer):
        self.tracer = tracer
    
    @asynccontextmanager
    async def trace_embedding_generation(self, text_length: int, model: str):
        """Trace embedding generation"""
        async with self.tracer.trace_operation(
            "ai.embedding.generate",
            **{
                "ai.model": model,
                "ai.input.length": text_length,
                "ai.operation": "embedding"
            }
        ) as span:
            yield span
    
    @asynccontextmanager
    async def trace_rag_query(self, query: str, context_count: int):
        """Trace RAG query processing"""
        async with self.tracer.trace_operation(
            "ai.rag.query",
            **{
                "ai.query.length": len(query),
                "ai.context.count": context_count,
                "ai.operation": "rag"
            }
        ) as span:
            yield span
    
    @asynccontextmanager
    async def trace_document_processing(self, document_id: str, document_size: int):
        """Trace document processing"""
        async with self.tracer.trace_operation(
            "ai.document.process",
            **{
                "document.id": document_id,
                "document.size": document_size,
                "ai.operation": "document_processing"
            }
        ) as span:
            yield span
    
    @asynccontextmanager
    async def trace_search_operation(self, query: str, result_count: int):
        """Trace search operations"""
        async with self.tracer.trace_operation(
            "ai.search.execute",
            **{
                "search.query": query[:100],  # Truncate for privacy
                "search.result_count": result_count,
                "ai.operation": "search"
            }
        ) as span:
            yield span

class PerformanceMetrics:
    """Performance metrics collector"""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}
    
    def record_duration(self, metric_name: str, duration: float):
        """Record a duration metric"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        self.metrics[metric_name].append(duration)
        
        # Keep only recent metrics
        if len(self.metrics[metric_name]) > 1000:
            self.metrics[metric_name] = self.metrics[metric_name][-1000:]
    
    def increment_counter(self, counter_name: str, value: int = 1):
        """Increment a counter"""
        if counter_name not in self.counters:
            self.counters[counter_name] = 0
        self.counters[counter_name] += value
    
    def set_gauge(self, gauge_name: str, value: float):
        """Set a gauge value"""
        self.gauges[gauge_name] = value
    
    def record_histogram(self, histogram_name: str, value: float):
        """Record a histogram value"""
        if histogram_name not in self.histograms:
            self.histograms[histogram_name] = []
        
        self.histograms[histogram_name].append(value)
        
        # Keep only recent values
        if len(self.histograms[histogram_name]) > 1000:
            self.histograms[histogram_name] = self.histograms[histogram_name][-1000:]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        summary = {
            "counters": self.counters.copy(),
            "gauges": self.gauges.copy(),
            "durations": {},
            "histograms": {}
        }
        
        # Calculate duration statistics
        for name, durations in self.metrics.items():
            if durations:
                summary["durations"][name] = {
                    "count": len(durations),
                    "avg": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations),
                    "p50": self._percentile(durations, 50),
                    "p95": self._percentile(durations, 95),
                    "p99": self._percentile(durations, 99)
                }
        
        # Calculate histogram statistics
        for name, values in self.histograms.items():
            if values:
                summary["histograms"][name] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "p50": self._percentile(values, 50),
                    "p95": self._percentile(values, 95),
                    "p99": self._percentile(values, 99)
                }
        
        return summary
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]

class SpanProcessor:
    """Base span processor"""
    
    def process(self, span: Span):
        """Process a completed span"""
        raise NotImplementedError

class ConsoleSpanProcessor(SpanProcessor):
    """Console span processor for debugging"""
    
    def process(self, span: Span):
        """Print span to console"""
        print(f"SPAN: {span.operation_name} [{span.trace_id[:8]}] "
              f"{span.duration:.3f}s {span.status}")

class MetricsSpanProcessor(SpanProcessor):
    """Span processor that collects metrics"""
    
    def __init__(self, metrics: PerformanceMetrics):
        self.metrics = metrics
    
    def process(self, span: Span):
        """Process span into metrics"""
        # Record duration
        if span.duration:
            self.metrics.record_duration(f"span.{span.operation_name}.duration", span.duration)
        
        # Increment counters
        self.metrics.increment_counter(f"span.{span.operation_name}.count")
        
        if span.status == "error":
            self.metrics.increment_counter(f"span.{span.operation_name}.errors")
        
        # Record AI-specific metrics
        if "ai.operation" in span.tags:
            ai_operation = span.tags["ai.operation"]
            if span.duration:
                self.metrics.record_duration(f"ai.{ai_operation}.duration", span.duration)
            self.metrics.increment_counter(f"ai.{ai_operation}.count")

class JSONSpanProcessor(SpanProcessor):
    """JSON span processor for structured logging"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def process(self, span: Span):
        """Log span as JSON"""
        span_data = {
            "trace_id": span.trace_id,
            "span_id": span.span_id,
            "parent_span_id": span.parent_span_id,
            "operation_name": span.operation_name,
            "start_time": span.start_time,
            "end_time": span.end_time,
            "duration": span.duration,
            "status": span.status,
            "tags": span.tags,
            "logs": span.logs
        }
        
        self.logger.info(f"SPAN_COMPLETE: {json.dumps(span_data)}")

# Tracing decorators
def trace_function(operation_name: str = None, tracer: DistributedTracer = None):
    """Decorator to trace function execution"""
    def decorator(func: Callable) -> Callable:
        nonlocal operation_name
        if operation_name is None:
            operation_name = f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                current_tracer = tracer or global_tracer
                async with current_tracer.trace_operation(operation_name) as span:
                    # Add function metadata
                    span.tags["function.name"] = func.__name__
                    span.tags["function.module"] = func.__module__
                    
                    result = await func(*args, **kwargs)
                    return result
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                current_tracer = tracer or global_tracer
                # For sync functions, we'll use a simple span without context manager
                span = current_tracer.start_span(operation_name)
                span.tags["function.name"] = func.__name__
                span.tags["function.module"] = func.__module__
                
                try:
                    result = func(*args, **kwargs)
                    current_tracer.finish_span(span, "ok")
                    return result
                except Exception as e:
                    current_tracer.finish_span(span, "error", e)
                    raise
            return sync_wrapper
    return decorator

def trace_ai_operation(operation_type: str):
    """Decorator specifically for AI operations"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with ai_tracer.tracer.trace_operation(
                f"ai.{operation_type}",
                **{"ai.operation": operation_type}
            ) as span:
                result = await func(*args, **kwargs)
                
                # Add result metadata if available
                if isinstance(result, dict):
                    if "confidence" in result:
                        span.tags["ai.confidence"] = result["confidence"]
                    if "model" in result:
                        span.tags["ai.model"] = result["model"]
                
                return result
        return wrapper
    return decorator

# Global instances
global_tracer = DistributedTracer("ai-scholar-backend")
performance_metrics = PerformanceMetrics()
ai_tracer = AIOperationTracer(global_tracer)

# Set up span processors
console_processor = ConsoleSpanProcessor()
metrics_processor = MetricsSpanProcessor(performance_metrics)
json_processor = JSONSpanProcessor(logger)

global_tracer.add_span_processor(console_processor.process)
global_tracer.add_span_processor(metrics_processor.process)
global_tracer.add_span_processor(json_processor.process)

# Convenience functions
async def trace_operation(operation_name: str, **tags):
    """Convenience function for tracing operations"""
    return global_tracer.trace_operation(operation_name, **tags)

def get_performance_report() -> Dict[str, Any]:
    """Get comprehensive performance report"""
    return {
        "tracing": global_tracer.get_trace_stats(),
        "metrics": performance_metrics.get_metrics_summary(),
        "timestamp": time.time()
    }

# Usage examples
if __name__ == "__main__":
    async def test_tracing():
        # Test basic tracing
        async with trace_operation("test.operation", user_id="123") as span:
            await asyncio.sleep(0.1)
            span.tags["result"] = "success"
        
        # Test AI operation tracing
        async with ai_tracer.trace_embedding_generation(1000, "test-model") as span:
            await asyncio.sleep(0.05)
            span.tags["embedding_dim"] = 384
        
        # Test function decorator
        @trace_function("test.decorated_function")
        async def test_function():
            await asyncio.sleep(0.02)
            return "test result"
        
        result = await test_function()
        
        # Get performance report
        report = get_performance_report()
        print(f"Performance Report: {json.dumps(report, indent=2)}")
    
    # Run test
    asyncio.run(test_tracing())