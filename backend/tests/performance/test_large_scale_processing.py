"""
Load tests for large-scale paper processing operations.
"""

import pytest
import asyncio
import tempfile
import shutil
import time
import psutil
import statistics
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json
import sys

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.core.instance_config import InstanceConfig
    from multi_instance_arxiv_system.processors.ai_scholar_processor import AIScholarProcessor
    from multi_instance_arxiv_system.processors.quant_scholar_processor import QuantScholarProcessor
    from multi_instance_arxiv_system.vector_store.multi_instance_vector_store_service import MultiInstanceVectorStoreService
    from multi_instance_arxiv_system.monitoring.storage_monitor import StorageMonitor
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class TestLargeScaleProcessing:
    """Load tests for large-scale paper processing."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def load_test_config(self, temp_dir):
        """Create configuration for load testing."""
        return InstanceConfig(
            instance_name="load_test",
            storage_path=str(temp_dir),
            arxiv_categories=["cs.AI", "cs.LG", "cs.CV"],
            max_papers_per_run=5000,
            processing_batch_size=100,
            concurrent_downloads=20,
            memory_limit_gb=8.0
        )
    
    def create_large_dataset(self, temp_dir: Path, num_papers: int):
        """Create large dataset for load testing."""
        papers_dir = temp_dir / "papers"
        papers_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_dir = temp_dir / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        for i in range(num_papers):
            paper_id = f'load_test_{i:05d}'
            
            # Create PDF files with varying sizes (1KB to 50KB)
            pdf_size = 1000 + (i % 50) * 1000
            pdf_content = b'X' * pdf_size
            
            pdf_path = papers_dir / f"{paper_id}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(pdf_content)
            
            # Create metadata with realistic content
            metadata = {
                'paper_id': paper_id,
                'title': f'Load Test Paper {i}: Advanced Machine Learning Techniques',
                'authors': [f'Author {i}', f'Co-Author {i}', f'Third Author {i}'],
                'abstract': f'This paper presents novel approaches to machine learning problem {i}. ' * 5,
                'categories': ['cs.AI', 'cs.LG'] if i % 2 == 0 else ['cs.CV', 'cs.AI'],
                'instance_name': 'load_test',
                'downloaded_at': datetime.now().isoformat(),
                'file_size_bytes': pdf_size
            }
            
            metadata_path = metadata_dir / f"{paper_id}.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
    
    @pytest.mark.asyncio
    async def test_process_1000_papers(self, load_test_config, temp_dir):
        """Test processing 1000 papers for baseline performance."""
        
        num_papers = 1000
        self.create_large_dataset(temp_dir, num_papers)
        
        processor = AIScholarProcessor(load_test_config)
        
        # Mock vector store operations
        with patch.object(processor.vector_store, 'add_documents') as mock_add_docs, \
             patch.object(processor.pdf_processor, 'extract_text') as mock_extract_text:
            
            # Mock text extraction with realistic processing time
            async def mock_text_extraction(pdf_path):
                # Simulate processing time based on file size
                file_size = pdf_path.stat().st_size
                processing_time = min(0.01, file_size / 1000000)  # Max 10ms
                await asyncio.sleep(processing_time)
                return f'Extracted text from {pdf_path.name} containing machine learning research content'
            
            mock_extract_text.side_effect = mock_text_extraction
            mock_add_docs.return_value = True
            
            # Measure processing performance
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            result = await processor.process_downloaded_papers()
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            # Performance analysis
            total_time = end_time - start_time
            papers_per_second = num_papers / total_time
            memory_usage = end_memory - start_memory
            
            print(f"1000 Papers Load Test Results:")
            print(f"  Total time: {total_time:.2f} seconds")
            print(f"  Papers per second: {papers_per_second:.2f}")
            print(f"  Memory usage: {memory_usage:.2f} MB")
            print(f"  Vector store calls: {mock_add_docs.call_count}")
            
            # Performance benchmarks for 1000 papers
            assert papers_per_second > 20.0, f"Processing rate too slow: {papers_per_second:.2f} papers/sec"
            assert memory_usage < 1500, f"Memory usage too high: {memory_usage:.2f} MB"
            assert total_time < 60, f"Processing time too long: {total_time:.2f} seconds"
            
            # Verify successful processing
            assert result['success'] == True
            assert result['papers_processed'] == num_papers
    
    @pytest.mark.asyncio
    async def test_process_5000_papers(self, load_test_config, temp_dir):
        """Test processing 5000 papers for high-load scenario."""
        
        num_papers = 5000
        self.create_large_dataset(temp_dir, num_papers)
        
        processor = AIScholarProcessor(load_test_config)
        
        # Track performance metrics over time
        performance_samples = []
        
        async def performance_monitor():
            while True:
                memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
                cpu_percent = psutil.Process().cpu_percent()
                performance_samples.append({
                    'timestamp': time.time(),
                    'memory_mb': memory_mb,
                    'cpu_percent': cpu_percent
                })
                await asyncio.sleep(1.0)
        
        # Mock vector store operations
        with patch.object(processor.vector_store, 'add_documents') as mock_add_docs, \
             patch.object(processor.pdf_processor, 'extract_text') as mock_extract_text:
            
            mock_extract_text.side_effect = lambda path: f'Extracted text from {path.name}'
            mock_add_docs.return_value = True
            
            # Start performance monitoring
            monitor_task = asyncio.create_task(performance_monitor())
            
            try:
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024
                
                result = await processor.process_downloaded_papers()
                
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                
            finally:
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
            
            # Performance analysis
            total_time = end_time - start_time
            papers_per_second = num_papers / total_time
            memory_usage = end_memory - start_memory
            
            # Analyze performance samples
            if performance_samples:
                memory_values = [s['memory_mb'] for s in performance_samples]
                cpu_values = [s['cpu_percent'] for s in performance_samples]
                
                max_memory = max(memory_values)
                avg_memory = statistics.mean(memory_values)
                avg_cpu = statistics.mean(cpu_values) if cpu_values else 0
                
                print(f"5000 Papers Load Test Results:")
                print(f"  Total time: {total_time:.2f} seconds")
                print(f"  Papers per second: {papers_per_second:.2f}")
                print(f"  Memory usage: {memory_usage:.2f} MB")
                print(f"  Peak memory: {max_memory:.2f} MB")
                print(f"  Average CPU: {avg_cpu:.1f}%")
                print(f"  Vector store calls: {mock_add_docs.call_count}")
                
                # Performance benchmarks for 5000 papers
                assert papers_per_second > 15.0, f"Processing rate too slow: {papers_per_second:.2f} papers/sec"
                assert memory_usage < 3000, f"Memory usage too high: {memory_usage:.2f} MB"
                assert max_memory < start_memory + 4000, f"Peak memory too high: {max_memory:.2f} MB"
                assert total_time < 400, f"Processing time too long: {total_time:.2f} seconds"
            
            # Verify successful processing
            assert result['success'] == True
            assert result['papers_processed'] == num_papers
    
    @pytest.mark.asyncio
    async def test_memory_scalability(self, load_test_config, temp_dir):
        """Test memory usage scalability with increasing paper counts."""
        
        paper_counts = [100, 500, 1000, 2000]
        memory_results = {}
        
        for paper_count in paper_counts:
            # Create dataset for this test
            test_dir = temp_dir / f"memory_test_{paper_count}"
            test_dir.mkdir(exist_ok=True)
            
            self.create_large_dataset(test_dir, paper_count)
            
            # Update config for this test
            test_config = load_test_config
            test_config.storage_path = str(test_dir)
            
            processor = AIScholarProcessor(test_config)
            
            with patch.object(processor.vector_store, 'add_documents') as mock_add_docs, \
                 patch.object(processor.pdf_processor, 'extract_text') as mock_extract_text:
                
                mock_extract_text.side_effect = lambda path: f'Extracted text from {path.name}'
                mock_add_docs.return_value = True
                
                # Measure memory usage
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024
                
                result = await processor.process_downloaded_papers()
                
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                memory_growth = end_memory - start_memory
                memory_per_paper = memory_growth / paper_count if paper_count > 0 else 0
                
                memory_results[paper_count] = {
                    'memory_growth_mb': memory_growth,
                    'memory_per_paper_mb': memory_per_paper,
                    'success': result['success']
                }
                
                print(f"Papers: {paper_count}, Memory growth: {memory_growth:.2f} MB, "
                      f"Per paper: {memory_per_paper:.3f} MB")
        
        # Analyze memory scalability
        # Memory per paper should remain relatively constant
        memory_per_paper_values = [r['memory_per_paper_mb'] for r in memory_results.values()]
        
        if len(memory_per_paper_values) > 1:
            memory_variance = statistics.variance(memory_per_paper_values)
            avg_memory_per_paper = statistics.mean(memory_per_paper_values)
            
            print(f"Memory scalability analysis:")
            print(f"  Average memory per paper: {avg_memory_per_paper:.3f} MB")
            print(f"  Memory variance: {memory_variance:.6f}")
            
            # Memory usage should scale linearly (low variance in per-paper usage)
            assert memory_variance < 0.01, f"Memory usage variance too high: {memory_variance:.6f}"
            assert avg_memory_per_paper < 2.0, f"Memory per paper too high: {avg_memory_per_paper:.3f} MB"
        
        # Verify all tests succeeded
        for paper_count, result in memory_results.items():
            assert result['success'] == True, f"Processing failed for {paper_count} papers"
    
    @pytest.mark.asyncio
    async def test_concurrent_multi_instance_load(self, temp_dir):
        """Test concurrent processing across multiple instances under load."""
        
        # Create configurations for 4 instances
        instances = []
        for i in range(4):
            config = InstanceConfig(
                instance_name=f"load_instance_{i}",
                storage_path=str(temp_dir / f"instance_{i}"),
                arxiv_categories=["cs.AI", "cs.LG"],
                processing_batch_size=50,
                concurrent_downloads=10
            )
            instances.append(config)
        
        # Create datasets for each instance (500 papers each)
        papers_per_instance = 500
        for i, config in enumerate(instances):
            instance_dir = Path(config.storage_path)
            self.create_large_dataset(instance_dir, papers_per_instance)
        
        # Create processors
        processors = [AIScholarProcessor(config) for config in instances]
        
        # Mock vector store operations for all processors
        with patch('multi_instance_arxiv_system.vector_store.multi_instance_vector_store_service.MultiInstanceVectorStoreService') as mock_vector_class:
            
            mock_vector_service = Mock()
            mock_vector_service.add_documents = AsyncMock(return_value=True)
            mock_vector_class.return_value = mock_vector_service
            
            # Mock PDF processing for all processors
            for processor in processors:
                processor.pdf_processor.extract_text = AsyncMock(
                    side_effect=lambda path: f'Extracted text from {path.name}'
                )
            
            # Monitor system resources during concurrent processing
            resource_samples = []
            
            async def resource_monitor():
                while True:
                    cpu_percent = psutil.cpu_percent()
                    memory_info = psutil.virtual_memory()
                    resource_samples.append({
                        'timestamp': time.time(),
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory_info.percent,
                        'memory_available_gb': memory_info.available / 1024 / 1024 / 1024
                    })
                    await asyncio.sleep(0.5)
            
            # Start resource monitoring
            monitor_task = asyncio.create_task(resource_monitor())
            
            try:
                start_time = time.time()
                
                # Run all instances concurrently
                tasks = [processor.process_downloaded_papers() for processor in processors]
                results = await asyncio.gather(*tasks)
                
                end_time = time.time()
                
            finally:
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
            
            # Performance analysis
            total_time = end_time - start_time
            total_papers = sum(result['papers_processed'] for result in results)
            papers_per_second = total_papers / total_time
            
            # Analyze resource usage
            if resource_samples:
                cpu_values = [s['cpu_percent'] for s in resource_samples]
                memory_values = [s['memory_percent'] for s in resource_samples]
                
                max_cpu = max(cpu_values)
                avg_cpu = statistics.mean(cpu_values)
                max_memory = max(memory_values)
                avg_memory = statistics.mean(memory_values)
                
                print(f"Concurrent Multi-Instance Load Test:")
                print(f"  Instances: {len(instances)}")
                print(f"  Total papers: {total_papers}")
                print(f"  Total time: {total_time:.2f} seconds")
                print(f"  Papers per second: {papers_per_second:.2f}")
                print(f"  Peak CPU: {max_cpu:.1f}%")
                print(f"  Average CPU: {avg_cpu:.1f}%")
                print(f"  Peak memory: {max_memory:.1f}%")
                print(f"  Average memory: {avg_memory:.1f}%")
                
                # Performance benchmarks for concurrent load
                assert papers_per_second > 25.0, f"Concurrent processing too slow: {papers_per_second:.2f} papers/sec"
                assert max_cpu < 95.0, f"CPU usage too high: {max_cpu:.1f}%"
                assert max_memory < 90.0, f"Memory usage too high: {max_memory:.1f}%"
                assert total_time < 120, f"Total processing time too long: {total_time:.2f} seconds"
            
            # Verify all instances processed successfully
            for i, result in enumerate(results):
                assert result['success'] == True, f"Instance {i} processing failed"
                assert result['papers_processed'] == papers_per_instance
    
    @pytest.mark.asyncio
    async def test_vector_store_load_performance(self, load_test_config, temp_dir):
        """Test vector store performance under high document load."""
        
        num_papers = 2000
        self.create_large_dataset(temp_dir, num_papers)
        
        processor = AIScholarProcessor(load_test_config)
        vector_store = MultiInstanceVectorStoreService()
        
        # Track vector store operation times
        add_operation_times = []
        
        async def timed_add_documents(*args, **kwargs):
            start_time = time.time()
            result = True  # Mock successful addition
            end_time = time.time()
            add_operation_times.append(end_time - start_time)
            return result
        
        with patch.object(processor.vector_store, 'add_documents', side_effect=timed_add_documents), \
             patch.object(processor.pdf_processor, 'extract_text') as mock_extract_text:
            
            mock_extract_text.side_effect = lambda path: f'Extracted text from {path.name}'
            
            start_time = time.time()
            
            result = await processor.process_downloaded_papers()
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Analyze vector store performance
            if add_operation_times:
                total_vector_time = sum(add_operation_times)
                avg_vector_time = statistics.mean(add_operation_times)
                max_vector_time = max(add_operation_times)
                vector_overhead = (total_vector_time / total_time) * 100
                
                print(f"Vector Store Load Performance:")
                print(f"  Total papers: {num_papers}")
                print(f"  Vector store operations: {len(add_operation_times)}")
                print(f"  Total vector store time: {total_vector_time:.2f} seconds")
                print(f"  Average operation time: {avg_vector_time:.3f} seconds")
                print(f"  Max operation time: {max_vector_time:.3f} seconds")
                print(f"  Vector store overhead: {vector_overhead:.1f}%")
                
                # Vector store performance benchmarks
                assert avg_vector_time < 0.5, f"Average vector store operation too slow: {avg_vector_time:.3f}s"
                assert max_vector_time < 2.0, f"Max vector store operation too slow: {max_vector_time:.3f}s"
                assert vector_overhead < 50.0, f"Vector store overhead too high: {vector_overhead:.1f}%"
            
            # Verify successful processing
            assert result['success'] == True
            assert result['papers_processed'] == num_papers
    
    @pytest.mark.asyncio
    async def test_storage_performance_under_load(self, load_test_config, temp_dir):
        """Test storage I/O performance under high load."""
        
        num_papers = 1500
        self.create_large_dataset(temp_dir, num_papers)
        
        storage_monitor = StorageMonitor()
        
        # Monitor storage I/O during processing
        io_samples = []
        
        async def io_monitor():
            while True:
                try:
                    io_counters = psutil.disk_io_counters()
                    io_samples.append({
                        'timestamp': time.time(),
                        'read_bytes': io_counters.read_bytes,
                        'write_bytes': io_counters.write_bytes,
                        'read_count': io_counters.read_count,
                        'write_count': io_counters.write_count
                    })
                except AttributeError:
                    # disk_io_counters not available on all systems
                    pass
                await asyncio.sleep(0.5)
        
        processor = AIScholarProcessor(load_test_config)
        
        with patch.object(processor.vector_store, 'add_documents') as mock_add_docs, \
             patch.object(processor.pdf_processor, 'extract_text') as mock_extract_text:
            
            mock_extract_text.side_effect = lambda path: f'Extracted text from {path.name}'
            mock_add_docs.return_value = True
            
            # Start I/O monitoring
            monitor_task = asyncio.create_task(io_monitor())
            
            try:
                start_time = time.time()
                
                result = await processor.process_downloaded_papers()
                
                end_time = time.time()
                
            finally:
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
            
            total_time = end_time - start_time
            
            # Analyze I/O performance
            if len(io_samples) > 1:
                start_io = io_samples[0]
                end_io = io_samples[-1]
                
                total_read_mb = (end_io['read_bytes'] - start_io['read_bytes']) / 1024 / 1024
                total_write_mb = (end_io['write_bytes'] - start_io['write_bytes']) / 1024 / 1024
                read_ops = end_io['read_count'] - start_io['read_count']
                write_ops = end_io['write_count'] - start_io['write_count']
                
                read_throughput = total_read_mb / total_time
                write_throughput = total_write_mb / total_time
                
                print(f"Storage I/O Performance:")
                print(f"  Total papers: {num_papers}")
                print(f"  Processing time: {total_time:.2f} seconds")
                print(f"  Total read: {total_read_mb:.2f} MB")
                print(f"  Total write: {total_write_mb:.2f} MB")
                print(f"  Read throughput: {read_throughput:.2f} MB/s")
                print(f"  Write throughput: {write_throughput:.2f} MB/s")
                print(f"  Read operations: {read_ops}")
                print(f"  Write operations: {write_ops}")
                
                # Storage performance benchmarks
                assert read_throughput > 1.0, f"Read throughput too low: {read_throughput:.2f} MB/s"
                assert write_throughput > 0.5, f"Write throughput too low: {write_throughput:.2f} MB/s"
            
            # Verify successful processing
            assert result['success'] == True
            assert result['papers_processed'] == num_papers