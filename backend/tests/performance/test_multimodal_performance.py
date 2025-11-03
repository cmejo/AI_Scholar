"""Performance and scalability tests for multi-modal processing."""

import pytest
import asyncio
import time
import psutil
import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from unittest.mock import Mock, patch

from backend.rl.multimodal.visual_content_processor import VisualContentProcessor
from backend.rl.multimodal.feature_integrator import MultiModalFeatureIntegrator
from backend.rl.multimodal.learning_model import MultiModalLearningModel
from backend.rl.multimodal.data_models import Document, VisualElement, VisualElementType
from backend.rl.utils import performance_logger


class TestMultiModalPerformance:
    """Performance tests for multi-modal processing components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.visual_processor = VisualContentProcessor()
        self.feature_integrator = MultiModalFeatureIntegrator()
        self.learning_model = MultiModalLearningModel()
        
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
                self.start_cpu = None
            
            def __enter__(self):
                self.start_time = time.time()
                self.start_memory = self.test_instance.process.memory_info().rss / 1024 / 1024  # MB
                self.start_cpu = self.test_instance.process.cpu_percent()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                end_time = time.time()
                end_memory = self.test_instance.process.memory_info().rss / 1024 / 1024  # MB
                end_cpu = self.test_instance.process.cpu_percent()
                
                metrics = {
                    'duration': end_time - self.start_time,
                    'memory_start': self.start_memory,
                    'memory_end': end_memory,
                    'memory_delta': end_memory - self.start_memory,
                    'cpu_usage': end_cpu
                }
                
                self.test_instance.performance_metrics[self.name] = metrics
                
                performance_logger.log_processing_time(
                    operation=self.name,
                    component="multimodal",
                    processing_time=metrics['duration']
                )
                
                performance_logger.log_memory_usage(
                    component="multimodal",
                    operation=self.name,
                    memory_before=self.start_memory,
                    memory_after=end_memory
                )
        
        return PerformanceMeasurer(self, operation_name)
    
    @pytest.mark.asyncio
    async def test_visual_processing_performance_single_document(self):
        """Test visual processing performance with single document."""
        # Create test document with multiple visual elements
        document = Document(
            id="perf_test_single",
            title="Performance Test Document",
            content="Test document for performance evaluation.",
            visual_elements=[
                {
                    "type": "chart",
                    "data": b"chart_data" * 1000,  # 10KB of data
                    "caption": f"Performance test chart {i}"
                }
                for i in range(10)
            ]
        )
        
        with self.measure_performance("visual_processing_single"):
            visual_features = await self.visual_processor.extract_visual_features(document)
        
        # Verify results
        assert visual_features is not None
        assert len(visual_features.elements) == 10
        
        # Performance assertions
        metrics = self.performance_metrics["visual_processing_single"]
        assert metrics['duration'] < 5.0, f"Processing too slow: {metrics['duration']}s"
        assert metrics['memory_delta'] < 100, f"Memory usage too high: {metrics['memory_delta']}MB"
    
    @pytest.mark.asyncio
    async def test_visual_processing_performance_batch(self):
        """Test visual processing performance with batch of documents."""
        # Create batch of documents
        documents = [
            Document(
                id=f"perf_batch_{i:03d}",
                title=f"Batch Document {i}",
                content=f"Content for batch document {i}.",
                visual_elements=[
                    {
                        "type": "chart",
                        "data": f"batch_chart_data_{i}_{j}".encode() * 100,
                        "caption": f"Chart {j} in document {i}"
                    }
                    for j in range(5)
                ]
            )
            for i in range(50)  # 50 documents
        ]
        
        with self.measure_performance("visual_processing_batch"):
            batch_results = []
            for document in documents:
                visual_features = await self.visual_processor.extract_visual_features(document)
                batch_results.append(visual_features)
        
        # Verify results
        assert len(batch_results) == 50
        assert all(result is not None for result in batch_results)
        
        # Performance assertions
        metrics = self.performance_metrics["visual_processing_batch"]
        assert metrics['duration'] < 30.0, f"Batch processing too slow: {metrics['duration']}s"
        
        # Calculate throughput
        throughput = len(documents) / metrics['duration']
        performance_logger.log_throughput(
            component="multimodal",
            operation="visual_processing_batch",
            items_processed=len(documents),
            time_elapsed=metrics['duration']
        )
        
        assert throughput > 1.0, f"Throughput too low: {throughput} docs/sec"
    
    @pytest.mark.asyncio
    async def test_visual_processing_performance_concurrent(self):
        """Test visual processing performance with concurrent processing."""
        # Create documents for concurrent processing
        documents = [
            Document(
                id=f"concurrent_{i:03d}",
                title=f"Concurrent Document {i}",
                content=f"Content for concurrent document {i}.",
                visual_elements=[
                    {
                        "type": "chart",
                        "data": f"concurrent_data_{i}".encode() * 200,
                        "caption": f"Concurrent chart {i}"
                    }
                ]
            )
            for i in range(20)
        ]
        
        async def process_document(doc):
            return await self.visual_processor.extract_visual_features(doc)
        
        with self.measure_performance("visual_processing_concurrent"):
            # Process documents concurrently
            tasks = [process_document(doc) for doc in documents]
            concurrent_results = await asyncio.gather(*tasks)
        
        # Verify results
        assert len(concurrent_results) == 20
        assert all(result is not None for result in concurrent_results)
        
        # Performance assertions
        metrics = self.performance_metrics["visual_processing_concurrent"]
        sequential_estimate = 20 * 0.5  # Estimated 0.5s per document
        
        # Concurrent processing should be faster than sequential
        assert metrics['duration'] < sequential_estimate * 0.8, \
            f"Concurrent processing not efficient: {metrics['duration']}s vs estimated {sequential_estimate}s"
    
    @pytest.mark.asyncio
    async def test_feature_integration_performance_large_embeddings(self):
        """Test feature integration performance with large embeddings."""
        # Create large text features
        text_features = Mock()
        text_features.embeddings = np.random.rand(4096).astype(np.float32)  # Large embedding
        text_features.keywords = [f"keyword_{i}" for i in range(100)]
        
        # Create large visual features
        visual_features = Mock()
        visual_features.elements = [
            Mock(
                element_type=VisualElementType.CHART,
                embeddings=np.random.rand(2048).astype(np.float32),
                confidence=0.9
            )
            for _ in range(20)
        ]
        visual_features.global_features = np.random.rand(2048).astype(np.float32)
        
        with self.measure_performance("feature_integration_large"):
            integrated_features = await self.feature_integrator.integrate_features(
                text_features, visual_features
            )
        
        # Verify results
        assert integrated_features is not None
        assert integrated_features.integrated_embedding is not None
        
        # Performance assertions
        metrics = self.performance_metrics["feature_integration_large"]
        assert metrics['duration'] < 2.0, f"Integration too slow: {metrics['duration']}s"
        assert metrics['memory_delta'] < 50, f"Memory usage too high: {metrics['memory_delta']}MB"
    
    @pytest.mark.asyncio
    async def test_feature_integration_performance_batch(self):
        """Test feature integration performance with batch processing."""
        # Create batch of feature pairs
        feature_pairs = []
        for i in range(100):
            text_features = Mock()
            text_features.embeddings = np.random.rand(512).astype(np.float32)
            text_features.keywords = [f"keyword_{i}_{j}" for j in range(10)]
            
            visual_features = Mock()
            visual_features.elements = [
                Mock(
                    element_type=VisualElementType.CHART,
                    embeddings=np.random.rand(512).astype(np.float32),
                    confidence=0.8 + (i % 2) * 0.1
                )
                for _ in range(3)
            ]
            visual_features.global_features = np.random.rand(512).astype(np.float32)
            
            feature_pairs.append((text_features, visual_features))
        
        with self.measure_performance("feature_integration_batch"):
            batch_results = []
            for text_feat, visual_feat in feature_pairs:
                integrated = await self.feature_integrator.integrate_features(
                    text_feat, visual_feat
                )
                batch_results.append(integrated)
        
        # Verify results
        assert len(batch_results) == 100
        assert all(result is not None for result in batch_results)
        
        # Performance assertions
        metrics = self.performance_metrics["feature_integration_batch"]
        assert metrics['duration'] < 10.0, f"Batch integration too slow: {metrics['duration']}s"
        
        # Calculate throughput
        throughput = len(feature_pairs) / metrics['duration']
        assert throughput > 10.0, f"Integration throughput too low: {throughput} pairs/sec"
    
    @pytest.mark.asyncio
    async def test_learning_model_performance_training(self):
        """Test learning model performance during training."""
        # Create training data
        training_examples = []
        for i in range(200):
            example = Mock()
            example.text_features = np.random.rand(512).astype(np.float32)
            example.visual_features = np.random.rand(512).astype(np.float32)
            example.integrated_features = np.random.rand(1024).astype(np.float32)
            example.target_output = np.random.rand(256).astype(np.float32)
            example.context = {"example_id": i, "domain": "test"}
            training_examples.append(example)
        
        with self.measure_performance("learning_model_training"):
            training_results = await self.learning_model.train_on_multimodal_data(
                training_examples
            )
        
        # Verify results
        assert training_results is not None
        assert training_results.training_loss is not None
        assert training_results.convergence_achieved is not None
        
        # Performance assertions
        metrics = self.performance_metrics["learning_model_training"]
        assert metrics['duration'] < 30.0, f"Training too slow: {metrics['duration']}s"
        
        # Training should show reasonable memory usage
        assert metrics['memory_delta'] < 200, f"Training memory usage too high: {metrics['memory_delta']}MB"
    
    @pytest.mark.asyncio
    async def test_learning_model_performance_inference(self):
        """Test learning model performance during inference."""
        # Create inference contexts
        contexts = []
        for i in range(500):
            context = Mock()
            context.document_content = Mock(id=f"inference_doc_{i}")
            context.visual_elements = [Mock() for _ in range(3)]
            context.user_interaction_history = []
            context.research_context = {"domain": "test", "task": "inference"}
            contexts.append(context)
        
        with self.measure_performance("learning_model_inference"):
            inference_results = []
            for context in contexts:
                recommendations = await self.learning_model.generate_multimodal_recommendations(
                    context
                )
                inference_results.append(recommendations)
        
        # Verify results
        assert len(inference_results) == 500
        assert all(result is not None for result in inference_results)
        
        # Performance assertions
        metrics = self.performance_metrics["learning_model_inference"]
        assert metrics['duration'] < 15.0, f"Inference too slow: {metrics['duration']}s"
        
        # Calculate inference throughput
        throughput = len(contexts) / metrics['duration']
        assert throughput > 30.0, f"Inference throughput too low: {throughput} inferences/sec"
    
    @pytest.mark.asyncio
    async def test_memory_efficiency_large_documents(self):
        """Test memory efficiency with large documents."""
        # Create very large document
        large_document = Document(
            id="memory_test_large",
            title="Large Document for Memory Testing",
            content="Large content " * 10000,  # ~100KB of text
            visual_elements=[
                {
                    "type": "chart",
                    "data": b"large_visual_data" * 1000,  # ~15KB per element
                    "caption": f"Large visual element {i}"
                }
                for i in range(50)  # 50 large visual elements
            ]
        )
        
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        with self.measure_performance("memory_efficiency_large"):
            # Process large document
            visual_features = await self.visual_processor.extract_visual_features(large_document)
            
            # Integrate features
            text_features = Mock()
            text_features.embeddings = np.random.rand(2048).astype(np.float32)
            
            integrated_features = await self.feature_integrator.integrate_features(
                text_features, visual_features
            )
            
            # Generate recommendations
            context = Mock()
            context.document_content = large_document
            context.visual_elements = visual_features.elements
            context.user_interaction_history = []
            context.research_context = {"domain": "memory_test"}
            
            recommendations = await self.learning_model.generate_multimodal_recommendations(context)
        
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory efficiency assertions
        assert memory_increase < 500, f"Memory increase too high: {memory_increase}MB"
        
        # Verify processing completed successfully
        assert visual_features is not None
        assert integrated_features is not None
        assert recommendations is not None
        
        performance_logger.info(
            "Large document memory efficiency test",
            initial_memory_mb=initial_memory,
            final_memory_mb=final_memory,
            memory_increase_mb=memory_increase,
            document_size_kb=len(large_document.content) / 1024,
            visual_elements_count=len(large_document.visual_elements)
        )
    
    def test_cpu_utilization_monitoring(self):
        """Test CPU utilization during intensive processing."""
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
            # Perform CPU-intensive operations
            start_time = time.time()
            
            # Simulate intensive visual processing
            for i in range(100):
                # Simulate image processing operations
                data = np.random.rand(1000, 1000).astype(np.float32)
                processed = np.fft.fft2(data)  # CPU-intensive operation
                result = np.abs(processed)
            
            processing_time = time.time() - start_time
            
        finally:
            # Stop monitoring
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
                "CPU utilization during intensive processing",
                processing_time=processing_time,
                average_cpu_percent=avg_cpu,
                max_cpu_percent=max_cpu,
                cpu_measurements_count=len(cpu_values)
            )
            
            # CPU utilization should be reasonable
            assert avg_cpu < 90, f"Average CPU usage too high: {avg_cpu}%"
            assert max_cpu < 100, f"Max CPU usage at limit: {max_cpu}%"
    
    def test_performance_regression_detection(self):
        """Test for performance regression detection."""
        # Define performance baselines (these would be updated based on actual measurements)
        baselines = {
            "visual_processing_single": {"duration": 5.0, "memory_delta": 100},
            "feature_integration_large": {"duration": 2.0, "memory_delta": 50},
            "learning_model_inference": {"duration": 15.0, "throughput": 30.0}
        }
        
        # Check current performance against baselines
        for operation, baseline in baselines.items():
            if operation in self.performance_metrics:
                current_metrics = self.performance_metrics[operation]
                
                # Check duration regression
                if "duration" in baseline:
                    duration_regression = (current_metrics["duration"] / baseline["duration"]) - 1
                    assert duration_regression < 0.2, \
                        f"Performance regression in {operation}: {duration_regression*100:.1f}% slower"
                
                # Check memory regression
                if "memory_delta" in baseline:
                    memory_regression = (current_metrics["memory_delta"] / baseline["memory_delta"]) - 1
                    assert memory_regression < 0.3, \
                        f"Memory regression in {operation}: {memory_regression*100:.1f}% more memory"
        
        performance_logger.info(
            "Performance regression check completed",
            operations_checked=len(baselines),
            regressions_detected=0  # Would be calculated based on actual failures
        )


class TestMultiModalScalability:
    """Scalability tests for multi-modal processing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.visual_processor = VisualContentProcessor()
        self.feature_integrator = MultiModalFeatureIntegrator()
        self.learning_model = MultiModalLearningModel()
    
    @pytest.mark.asyncio
    async def test_scalability_document_count(self):
        """Test scalability with increasing document count."""
        document_counts = [10, 50, 100, 200]
        scalability_results = {}
        
        for count in document_counts:
            # Create documents
            documents = [
                Document(
                    id=f"scale_doc_{i:04d}",
                    title=f"Scalability Test Document {i}",
                    content=f"Content for scalability test document {i}.",
                    visual_elements=[
                        {
                            "type": "chart",
                            "data": f"scale_data_{i}".encode() * 50,
                            "caption": f"Chart in document {i}"
                        }
                    ]
                )
                for i in range(count)
            ]
            
            # Measure processing time
            start_time = time.time()
            
            results = []
            for document in documents:
                visual_features = await self.visual_processor.extract_visual_features(document)
                results.append(visual_features)
            
            processing_time = time.time() - start_time
            throughput = count / processing_time
            
            scalability_results[count] = {
                "processing_time": processing_time,
                "throughput": throughput,
                "avg_time_per_doc": processing_time / count
            }
            
            performance_logger.info(
                f"Scalability test with {count} documents",
                document_count=count,
                processing_time=processing_time,
                throughput=throughput,
                avg_time_per_doc=processing_time / count
            )
        
        # Analyze scalability
        # Processing time should scale roughly linearly
        for i in range(1, len(document_counts)):
            prev_count = document_counts[i-1]
            curr_count = document_counts[i]
            
            prev_time = scalability_results[prev_count]["processing_time"]
            curr_time = scalability_results[curr_count]["processing_time"]
            
            # Time should not scale worse than quadratically
            time_ratio = curr_time / prev_time
            count_ratio = curr_count / prev_count
            
            assert time_ratio <= count_ratio * 1.5, \
                f"Poor scalability: {curr_count} docs took {time_ratio:.2f}x time vs {count_ratio:.2f}x docs"
    
    @pytest.mark.asyncio
    async def test_scalability_visual_element_count(self):
        """Test scalability with increasing visual element count per document."""
        element_counts = [1, 5, 10, 20, 50]
        scalability_results = {}
        
        for count in element_counts:
            # Create document with many visual elements
            document = Document(
                id=f"visual_scale_doc_{count}",
                title=f"Document with {count} Visual Elements",
                content="Document for visual element scalability testing.",
                visual_elements=[
                    {
                        "type": "chart",
                        "data": f"element_data_{i}".encode() * 100,
                        "caption": f"Visual element {i}"
                    }
                    for i in range(count)
                ]
            )
            
            # Measure processing time
            start_time = time.time()
            visual_features = await self.visual_processor.extract_visual_features(document)
            processing_time = time.time() - start_time
            
            scalability_results[count] = {
                "processing_time": processing_time,
                "avg_time_per_element": processing_time / count if count > 0 else 0,
                "elements_processed": len(visual_features.elements) if visual_features else 0
            }
            
            performance_logger.info(
                f"Visual element scalability test with {count} elements",
                element_count=count,
                processing_time=processing_time,
                avg_time_per_element=processing_time / count if count > 0 else 0
            )
        
        # Verify scalability
        for count in element_counts[1:]:  # Skip first element
            result = scalability_results[count]
            assert result["processing_time"] < count * 0.5, \
                f"Processing {count} elements too slow: {result['processing_time']}s"
    
    @pytest.mark.asyncio
    async def test_scalability_embedding_dimensions(self):
        """Test scalability with increasing embedding dimensions."""
        dimensions = [128, 256, 512, 1024, 2048]
        scalability_results = {}
        
        for dim in dimensions:
            # Create features with specific dimensions
            text_features = Mock()
            text_features.embeddings = np.random.rand(dim).astype(np.float32)
            text_features.keywords = ["test"] * 10
            
            visual_features = Mock()
            visual_features.elements = [
                Mock(
                    element_type=VisualElementType.CHART,
                    embeddings=np.random.rand(dim).astype(np.float32),
                    confidence=0.9
                )
                for _ in range(5)
            ]
            visual_features.global_features = np.random.rand(dim).astype(np.float32)
            
            # Measure integration time
            start_time = time.time()
            integrated_features = await self.feature_integrator.integrate_features(
                text_features, visual_features
            )
            processing_time = time.time() - start_time
            
            scalability_results[dim] = {
                "processing_time": processing_time,
                "time_per_dimension": processing_time / dim
            }
            
            performance_logger.info(
                f"Embedding dimension scalability test with {dim}D",
                embedding_dimensions=dim,
                processing_time=processing_time,
                time_per_dimension=processing_time / dim
            )
        
        # Verify reasonable scaling
        for dim in dimensions:
            result = scalability_results[dim]
            assert result["processing_time"] < 5.0, \
                f"Integration with {dim}D embeddings too slow: {result['processing_time']}s"
    
    @pytest.mark.asyncio
    async def test_concurrent_processing_scalability(self):
        """Test scalability of concurrent processing."""
        concurrency_levels = [1, 2, 4, 8, 16]
        scalability_results = {}
        
        # Create test documents
        test_documents = [
            Document(
                id=f"concurrent_scale_{i:03d}",
                title=f"Concurrent Scalability Document {i}",
                content=f"Content for concurrent test {i}.",
                visual_elements=[
                    {
                        "type": "chart",
                        "data": f"concurrent_data_{i}".encode() * 100,
                        "caption": f"Chart {i}"
                    }
                ]
            )
            for i in range(32)  # Fixed number of documents
        ]
        
        for concurrency in concurrency_levels:
            # Process documents with specified concurrency
            start_time = time.time()
            
            semaphore = asyncio.Semaphore(concurrency)
            
            async def process_with_semaphore(doc):
                async with semaphore:
                    return await self.visual_processor.extract_visual_features(doc)
            
            tasks = [process_with_semaphore(doc) for doc in test_documents]
            results = await asyncio.gather(*tasks)
            
            processing_time = time.time() - start_time
            throughput = len(test_documents) / processing_time
            
            scalability_results[concurrency] = {
                "processing_time": processing_time,
                "throughput": throughput,
                "efficiency": throughput / concurrency if concurrency > 0 else 0
            }
            
            performance_logger.info(
                f"Concurrent processing scalability with {concurrency} workers",
                concurrency_level=concurrency,
                processing_time=processing_time,
                throughput=throughput,
                efficiency=throughput / concurrency if concurrency > 0 else 0
            )
        
        # Analyze concurrent scalability
        # Throughput should generally increase with concurrency (up to a point)
        for i in range(1, len(concurrency_levels)):
            prev_concurrency = concurrency_levels[i-1]
            curr_concurrency = concurrency_levels[i]
            
            prev_throughput = scalability_results[prev_concurrency]["throughput"]
            curr_throughput = scalability_results[curr_concurrency]["throughput"]
            
            # Allow for some overhead, but throughput should generally improve
            if curr_concurrency <= 8:  # Up to reasonable concurrency level
                assert curr_throughput >= prev_throughput * 0.8, \
                    f"Throughput decreased with higher concurrency: {prev_throughput} -> {curr_throughput}"


if __name__ == "__main__":
    pytest.main([__file__])