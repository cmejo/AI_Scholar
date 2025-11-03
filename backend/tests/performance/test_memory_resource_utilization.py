"""
Memory usage and resource utilization tests.
"""

import pytest
import asyncio
import tempfile
import shutil
import time
import psutil
import statistics
import gc
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
    from multi_instance_arxiv_system.monitoring.memory_manager import MemoryManager
    from multi_instance_arxiv_system.monitoring.performance_monitor import PerformanceMonitor
    from multi_instance_arxiv_system.scheduling.monthly_update_orchestrator import MonthlyUpdateOrchestrator
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class TestMemoryResourceUtilization:
    """Tests for memory usage and resource utilization."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def memory_config(self, temp_dir):
        """Create configuration for memory testing."""
        return InstanceConfig(
            instance_name="memory_test",
            storage_path=str(temp_dir),
            arxiv_categories=["cs.AI"],
            processing_batch_size=25,
            memory_limit_gb=2.0,
            concurrent_downloads=5
        )
    
    @pytest.fixture
    def memory_manager(self):
        """Create memory manager instance."""
        return MemoryManager()
    
    def create_memory_test_dataset(self, temp_dir: Path, num_papers: int, paper_size_kb: int = 10):
        """Create dataset for memory testing with specified paper sizes."""
        papers_dir = temp_dir / "papers"
        papers_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_dir = temp_dir / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        for i in range(num_papers):
            paper_id = f'memory_test_{i:04d}'
            
            # Create PDF with specified size
            pdf_content = b'X' * (paper_size_kb * 1024)
            pdf_path = papers_dir / f"{paper_id}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(pdf_content)
            
            # Create metadata
            metadata = {
                'paper_id': paper_id,
                'title': f'Memory Test Paper {i}',
                'authors': [f'Author {i}'],
                'abstract': f'Abstract for memory test paper {i}' * 10,
                'categories': ['cs.AI'],
                'instance_name': 'memory_test',
                'downloaded_at': datetime.now().isoformat(),
                'file_size_kb': paper_size_kb
            }
            
            metadata_path = metadata_dir / f"{paper_id}.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
    
    @pytest.mark.asyncio
    async def test_memory_usage_patterns(self, memory_config, memory_manager, temp_dir):
        """Test memory usage patterns during processing."""
        
        num_papers = 200
        self.create_memory_test_dataset(temp_dir, num_papers, paper_size_kb=20)
        
        processor = AIScholarProcessor(memory_config)
        
        # Track detailed memory usage
        memory_samples = []
        gc_collections = []
        
        async def memory_tracker():
            while True:
                # Get memory info
                process = psutil.Process()
                memory_info = process.memory_info()
                memory_percent = process.memory_percent()
                
                # Get garbage collection stats
                gc_stats = gc.get_stats()
                
                sample = {
                    'timestamp': time.time(),
                    'rss_mb': memory_info.rss / 1024 / 1024,
                    'vms_mb': memory_info.vms / 1024 / 1024,
                    'memory_percent': memory_percent,
                    'gc_collections': sum(stat['collections'] for stat in gc_stats)
                }
                memory_samples.append(sample)
                await asyncio.sleep(0.2)
        
        with patch.object(processor.vector_store, 'add_documents') as mock_add_docs, \
             patch.object(processor.pdf_processor, 'extract_text') as mock_extract_text:
            
            # Mock text extraction with memory allocation
            def mock_text_extraction(pdf_path):
                # Simulate memory allocation during text extraction
                file_size = pdf_path.stat().st_size
                text_length = file_size * 2  # Simulate extracted text being larger
                return 'X' * min(text_length, 100000)  # Cap at 100KB
            
            mock_extract_text.side_effect = mock_text_extraction
            mock_add_docs.return_value = True
            
            # Start memory tracking
            tracker_task = asyncio.create_task(memory_tracker())
            
            try:
                start_time = time.time()
                initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
                
                result = await processor.process_downloaded_papers()
                
                end_time = time.time()
                final_memory = psutil.Process().memory_info().rss / 1024 / 1024
                
            finally:
                tracker_task.cancel()
                try:
                    await tracker_task
                except asyncio.CancelledError:
                    pass
            
            # Analyze memory usage patterns
            if memory_samples:
                rss_values = [s['rss_mb'] for s in memory_samples]
                vms_values = [s['vms_mb'] for s in memory_samples]
                
                peak_rss = max(rss_values)
                avg_rss = statistics.mean(rss_values)
                memory_growth = final_memory - initial_memory
                
                # Calculate memory stability (variance)
                rss_variance = statistics.variance(rss_values) if len(rss_values) > 1 else 0
                
                print(f"Memory Usage Pattern Analysis:")
                print(f"  Papers processed: {num_papers}")
                print(f"  Initial memory: {initial_memory:.2f} MB")
                print(f"  Final memory: {final_memory:.2f} MB")
                print(f"  Peak RSS: {peak_rss:.2f} MB")
                print(f"  Average RSS: {avg_rss:.2f} MB")
                print(f"  Memory growth: {memory_growth:.2f} MB")
                print(f"  Memory variance: {rss_variance:.2f}")
                
                # Memory usage benchmarks
                assert memory_growth < 500, f"Memory growth too high: {memory_growth:.2f} MB"
                assert peak_rss < initial_memory + 800, f"Peak memory too high: {peak_rss:.2f} MB"
                assert rss_variance < 10000, f"Memory usage too unstable: {rss_variance:.2f}"
                
                # Check for memory leaks (final should be close to initial)
                memory_leak = final_memory - initial_memory
                assert memory_leak < 200, f"Potential memory leak: {memory_leak:.2f} MB"
            
            # Verify successful processing
            assert result['success'] == True
            assert result['papers_processed'] == num_papers
    
    @pytest.mark.asyncio
    async def test_memory_limit_enforcement(self, memory_manager, temp_dir):
        """Test memory limit enforcement and cleanup."""
        
        # Create config with strict memory limit
        strict_config = InstanceConfig(
            instance_name="memory_limit_test",
            storage_path=str(temp_dir),
            memory_limit_gb=1.0,  # Strict 1GB limit
            processing_batch_size=10
        )
        
        # Create large dataset that would exceed memory limit
        num_papers = 100
        self.create_memory_test_dataset(temp_dir, num_papers, paper_size_kb=50)  # Larger papers
        
        processor = AIScholarProcessor(strict_config)
        
        # Track memory limit violations
        memory_violations = []
        
        async def memory_limit_monitor():
            limit_mb = strict_config.memory_limit_gb * 1024
            while True:
                current_mb = psutil.Process().memory_info().rss / 1024 / 1024
                if current_mb > limit_mb:
                    memory_violations.append({
                        'timestamp': time.time(),
                        'memory_mb': current_mb,
                        'limit_mb': limit_mb,
                        'violation_mb': current_mb - limit_mb
                    })
                await asyncio.sleep(0.1)
        
        with patch.object(processor.vector_store, 'add_documents') as mock_add_docs, \
             patch.object(processor.pdf_processor, 'extract_text') as mock_extract_text:
            
            # Mock memory-intensive text extraction
            def memory_intensive_extraction(pdf_path):
                # Simulate memory-intensive processing
                file_size = pdf_path.stat().st_size
                # Create large text content
                return 'Large extracted text content ' * (file_size // 100)
            
            mock_extract_text.side_effect = memory_intensive_extraction
            mock_add_docs.return_value = True
            
            # Start memory monitoring
            monitor_task = asyncio.create_task(memory_limit_monitor())
            
            try:
                result = await processor.process_downloaded_papers()
                
            finally:
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
            
            # Analyze memory limit enforcement
            if memory_violations:
                max_violation = max(v['violation_mb'] for v in memory_violations)
                avg_violation = statistics.mean(v['violation_mb'] for v in memory_violations)
                
                print(f"Memory Limit Enforcement:")
                print(f"  Memory limit: {strict_config.memory_limit_gb} GB")
                print(f"  Violations detected: {len(memory_violations)}")
                print(f"  Max violation: {max_violation:.2f} MB")
                print(f"  Average violation: {avg_violation:.2f} MB")
                
                # Memory limit should be enforced (violations should be minimal)
                assert max_violation < 200, f"Memory limit violation too high: {max_violation:.2f} MB"
                assert len(memory_violations) < 10, f"Too many memory violations: {len(memory_violations)}"
            
            # Processing should still succeed with memory management
            assert result['success'] == True
    
    @pytest.mark.asyncio
    async def test_garbage_collection_efficiency(self, memory_config, temp_dir):
        """Test garbage collection efficiency during processing."""
        
        num_papers = 300
        self.create_memory_test_dataset(temp_dir, num_papers, paper_size_kb=15)
        
        processor = AIScholarProcessor(memory_config)
        
        # Track garbage collection
        initial_gc_stats = gc.get_stats()
        gc_samples = []
        
        async def gc_monitor():
            while True:
                current_stats = gc.get_stats()
                total_collections = sum(stat['collections'] for stat in current_stats)
                total_collected = sum(stat['collected'] for stat in current_stats)
                
                gc_samples.append({
                    'timestamp': time.time(),
                    'total_collections': total_collections,
                    'total_collected': total_collected,
                    'memory_mb': psutil.Process().memory_info().rss / 1024 / 1024
                })
                await asyncio.sleep(0.5)
        
        with patch.object(processor.vector_store, 'add_documents') as mock_add_docs, \
             patch.object(processor.pdf_processor, 'extract_text') as mock_extract_text:
            
            # Mock text extraction that creates temporary objects
            def create_temporary_objects(pdf_path):
                # Create temporary objects that should be garbage collected
                temp_data = []
                for i in range(100):
                    temp_data.append(f'Temporary object {i} for {pdf_path.name}' * 10)
                
                # Return extracted text (temp_data will be eligible for GC)
                return f'Extracted text from {pdf_path.name}'
            
            mock_extract_text.side_effect = create_temporary_objects
            mock_add_docs.return_value = True
            
            # Start GC monitoring
            monitor_task = asyncio.create_task(gc_monitor())
            
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
            
            # Analyze garbage collection efficiency
            final_gc_stats = gc.get_stats()
            
            if gc_samples and len(gc_samples) > 1:
                initial_collections = gc_samples[0]['total_collections']
                final_collections = gc_samples[-1]['total_collections']
                collections_during_processing = final_collections - initial_collections
                
                initial_collected = gc_samples[0]['total_collected']
                final_collected = gc_samples[-1]['total_collected']
                objects_collected = final_collected - initial_collected
                
                processing_time = end_time - start_time
                gc_frequency = collections_during_processing / processing_time if processing_time > 0 else 0
                
                print(f"Garbage Collection Efficiency:")
                print(f"  Processing time: {processing_time:.2f} seconds")
                print(f"  GC collections: {collections_during_processing}")
                print(f"  Objects collected: {objects_collected}")
                print(f"  GC frequency: {gc_frequency:.2f} collections/second")
                
                # GC efficiency benchmarks
                assert gc_frequency < 5.0, f"GC frequency too high: {gc_frequency:.2f} collections/sec"
                assert objects_collected > 0, "No objects were garbage collected"
                
                # Memory should be relatively stable despite temporary object creation
                memory_values = [s['memory_mb'] for s in gc_samples]
                if len(memory_values) > 1:
                    memory_variance = statistics.variance(memory_values)
                    assert memory_variance < 5000, f"Memory too unstable despite GC: {memory_variance:.2f}"
            
            # Verify successful processing
            assert result['success'] == True
            assert result['papers_processed'] == num_papers
    
    @pytest.mark.asyncio
    async def test_cpu_utilization_efficiency(self, memory_config, temp_dir):
        """Test CPU utilization efficiency during processing."""
        
        num_papers = 150
        self.create_memory_test_dataset(temp_dir, num_papers, paper_size_kb=25)
        
        processor = AIScholarProcessor(memory_config)
        
        # Track CPU utilization
        cpu_samples = []
        
        async def cpu_monitor():
            while True:
                cpu_percent = psutil.cpu_percent(interval=None)
                cpu_times = psutil.Process().cpu_times()
                
                cpu_samples.append({
                    'timestamp': time.time(),
                    'cpu_percent': cpu_percent,
                    'user_time': cpu_times.user,
                    'system_time': cpu_times.system
                })
                await asyncio.sleep(0.2)
        
        with patch.object(processor.vector_store, 'add_documents') as mock_add_docs, \
             patch.object(processor.pdf_processor, 'extract_text') as mock_extract_text:
            
            # Mock CPU-intensive text extraction
            async def cpu_intensive_extraction(pdf_path):
                # Simulate CPU-intensive processing
                await asyncio.sleep(0.001)  # Small delay to simulate work
                
                # Simulate text processing work
                text_content = f'Extracted text from {pdf_path.name}' * 100
                processed_text = text_content.upper().lower()  # Simple CPU work
                
                return processed_text
            
            mock_extract_text.side_effect = cpu_intensive_extraction
            mock_add_docs.return_value = True
            
            # Start CPU monitoring
            monitor_task = asyncio.create_task(cpu_monitor())
            
            try:
                start_time = time.time()
                start_cpu_times = psutil.Process().cpu_times()
                
                result = await processor.process_downloaded_papers()
                
                end_time = time.time()
                end_cpu_times = psutil.Process().cpu_times()
                
            finally:
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
            
            # Analyze CPU utilization
            total_time = end_time - start_time
            cpu_user_time = end_cpu_times.user - start_cpu_times.user
            cpu_system_time = end_cpu_times.system - start_cpu_times.system
            total_cpu_time = cpu_user_time + cpu_system_time
            
            cpu_efficiency = (total_cpu_time / total_time) * 100 if total_time > 0 else 0
            
            if cpu_samples:
                cpu_percentages = [s['cpu_percent'] for s in cpu_samples if s['cpu_percent'] is not None]
                
                if cpu_percentages:
                    avg_cpu = statistics.mean(cpu_percentages)
                    max_cpu = max(cpu_percentages)
                    
                    print(f"CPU Utilization Efficiency:")
                    print(f"  Processing time: {total_time:.2f} seconds")
                    print(f"  CPU user time: {cpu_user_time:.2f} seconds")
                    print(f"  CPU system time: {cpu_system_time:.2f} seconds")
                    print(f"  CPU efficiency: {cpu_efficiency:.1f}%")
                    print(f"  Average CPU: {avg_cpu:.1f}%")
                    print(f"  Peak CPU: {max_cpu:.1f}%")
                    
                    # CPU efficiency benchmarks
                    assert cpu_efficiency > 10, f"CPU efficiency too low: {cpu_efficiency:.1f}%"
                    assert cpu_efficiency < 200, f"CPU efficiency suspiciously high: {cpu_efficiency:.1f}%"
                    assert avg_cpu > 5, f"Average CPU usage too low: {avg_cpu:.1f}%"
                    assert max_cpu < 100, f"CPU usage peaked at 100%: {max_cpu:.1f}%"
            
            # Verify successful processing
            assert result['success'] == True
            assert result['papers_processed'] == num_papers
    
    @pytest.mark.asyncio
    async def test_resource_cleanup_after_processing(self, memory_config, temp_dir):
        """Test resource cleanup after processing completion."""
        
        num_papers = 100
        self.create_memory_test_dataset(temp_dir, num_papers, paper_size_kb=30)
        
        processor = AIScholarProcessor(memory_config)
        
        # Measure resources before processing
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        initial_open_files = len(psutil.Process().open_files())
        
        with patch.object(processor.vector_store, 'add_documents') as mock_add_docs, \
             patch.object(processor.pdf_processor, 'extract_text') as mock_extract_text:
            
            mock_extract_text.side_effect = lambda path: f'Extracted text from {path.name}'
            mock_add_docs.return_value = True
            
            # Process papers
            result = await processor.process_downloaded_papers()
            
            # Force garbage collection
            gc.collect()
            
            # Wait a moment for cleanup
            await asyncio.sleep(1.0)
            
            # Measure resources after processing
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            final_open_files = len(psutil.Process().open_files())
            
            # Analyze resource cleanup
            memory_difference = final_memory - initial_memory
            file_difference = final_open_files - initial_open_files
            
            print(f"Resource Cleanup Analysis:")
            print(f"  Initial memory: {initial_memory:.2f} MB")
            print(f"  Final memory: {final_memory:.2f} MB")
            print(f"  Memory difference: {memory_difference:.2f} MB")
            print(f"  Initial open files: {initial_open_files}")
            print(f"  Final open files: {final_open_files}")
            print(f"  File handle difference: {file_difference}")
            
            # Resource cleanup benchmarks
            assert memory_difference < 100, f"Memory not properly cleaned up: {memory_difference:.2f} MB"
            assert file_difference <= 5, f"File handles not properly closed: {file_difference}"
            
            # Verify successful processing
            assert result['success'] == True
            assert result['papers_processed'] == num_papers
    
    @pytest.mark.asyncio
    async def test_long_running_stability(self, memory_config, temp_dir):
        """Test system stability during long-running operations."""
        
        # Simulate long-running operation with multiple batches
        batches = 5
        papers_per_batch = 50
        
        processor = AIScholarProcessor(memory_config)
        
        # Track stability metrics across batches
        batch_results = []
        memory_progression = []
        
        for batch_num in range(batches):
            # Create batch dataset
            batch_dir = temp_dir / f"batch_{batch_num}"
            batch_dir.mkdir(exist_ok=True)
            
            self.create_memory_test_dataset(batch_dir, papers_per_batch, paper_size_kb=20)
            
            # Update processor config for this batch
            batch_config = memory_config
            batch_config.storage_path = str(batch_dir)
            processor.config = batch_config
            
            with patch.object(processor.vector_store, 'add_documents') as mock_add_docs, \
                 patch.object(processor.pdf_processor, 'extract_text') as mock_extract_text:
                
                mock_extract_text.side_effect = lambda path: f'Extracted text from {path.name}'
                mock_add_docs.return_value = True
                
                # Measure resources before batch
                pre_batch_memory = psutil.Process().memory_info().rss / 1024 / 1024
                
                start_time = time.time()
                
                # Process batch
                result = await processor.process_downloaded_papers()
                
                end_time = time.time()
                
                # Measure resources after batch
                post_batch_memory = psutil.Process().memory_info().rss / 1024 / 1024
                
                batch_time = end_time - start_time
                memory_growth = post_batch_memory - pre_batch_memory
                
                batch_results.append({
                    'batch_num': batch_num,
                    'processing_time': batch_time,
                    'memory_growth': memory_growth,
                    'papers_processed': result['papers_processed'],
                    'success': result['success']
                })
                
                memory_progression.append(post_batch_memory)
                
                print(f"Batch {batch_num}: {batch_time:.2f}s, "
                      f"Memory: {post_batch_memory:.2f}MB (+{memory_growth:.2f}MB)")
                
                # Force cleanup between batches
                gc.collect()
                await asyncio.sleep(0.5)
        
        # Analyze long-running stability
        processing_times = [b['processing_time'] for b in batch_results]
        memory_growths = [b['memory_growth'] for b in batch_results]
        
        # Check processing time stability
        if len(processing_times) > 1:
            time_variance = statistics.variance(processing_times)
            avg_time = statistics.mean(processing_times)
            
            print(f"Long-Running Stability Analysis:")
            print(f"  Batches processed: {batches}")
            print(f"  Average batch time: {avg_time:.2f} seconds")
            print(f"  Time variance: {time_variance:.4f}")
            print(f"  Memory progression: {memory_progression}")
            
            # Stability benchmarks
            assert time_variance < 10.0, f"Processing time too unstable: {time_variance:.4f}"
            
            # Memory should not grow indefinitely
            total_memory_growth = sum(memory_growths)
            assert total_memory_growth < 200, f"Total memory growth too high: {total_memory_growth:.2f} MB"
            
            # Check for memory leaks (memory should stabilize)
            if len(memory_progression) >= 3:
                recent_growth = memory_progression[-1] - memory_progression[-3]
                assert recent_growth < 50, f"Recent memory growth suggests leak: {recent_growth:.2f} MB"
        
        # Verify all batches processed successfully
        for batch_result in batch_results:
            assert batch_result['success'] == True
            assert batch_result['papers_processed'] == papers_per_batch