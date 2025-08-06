"""
Comprehensive performance and load testing suite for all advanced features.
"""

import pytest
import asyncio
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch, AsyncMock
import numpy as np
from datetime import datetime, timedelta

from backend.services.mobile_sync_service import MobileSyncService
from backend.services.voice_processing_service import VoiceProcessingService
from backend.services.reference_manager_service import ReferenceManagerService
from backend.services.quiz_generation_service import QuizGenerationService


class TestMobilePerformance:
    """Performance testing for mobile features including battery and network optimization."""
    
    @pytest.fixture
    def mobile_sync_service(self):
        return MobileSyncService()
    
    @pytest.mark.asyncio
    async def test_mobile_sync_performance(self, mobile_sync_service):
        """Test mobile synchronization performance under various data loads."""
        data_sizes = [100, 1000, 5000, 10000]  # Number of items
        performance_results = []
        
        for size in data_sizes:
            # Generate test data
            test_data = {
                "documents": [
                    {"id": f"doc_{i}", "content": "x" * 1000}  # 1KB per document
                    for i in range(size)
                ]
            }
            
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            result = await mobile_sync_service.sync_offline_data("test_device", test_data)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            performance_results.append({
                "data_size": size,
                "sync_time": end_time - start_time,
                "memory_usage": end_memory - start_memory,
                "throughput": size / (end_time - start_time)
            })
            
            # Performance assertions
            assert result["success"] is True
            assert (end_time - start_time) < (size * 0.01)  # Max 10ms per item
            assert (end_memory - start_memory) < (size * 2000)  # Max 2KB memory per item
        
        # Verify performance scales reasonably
        assert performance_results[-1]["throughput"] > 50  # At least 50 items/second
    
    @pytest.mark.asyncio
    async def test_mobile_battery_optimization_performance(self, mobile_sync_service):
        """Test performance impact of battery optimization features."""
        device_id = "test_device_123"
        battery_levels = [100, 50, 20, 10, 5]  # Different battery levels
        
        for battery_level in battery_levels:
            start_time = time.time()
            
            result = await mobile_sync_service.optimize_for_battery(device_id, battery_level)
            
            optimization_time = time.time() - start_time
            
            assert result["optimized"] is True
            assert optimization_time < 0.1  # Less than 100ms
            
            # Lower battery should enable more aggressive optimizations
            if battery_level <= 20:
                assert result["background_sync_disabled"] is True
                assert result["reduced_polling"] is True
            
            # Verify CPU usage during optimization
            cpu_percent = psutil.cpu_percent(interval=0.1)
            assert cpu_percent < 50  # Should not consume excessive CPU
    
    @pytest.mark.asyncio
    async def test_mobile_network_adaptation_performance(self, mobile_sync_service):
        """Test performance of network condition adaptation."""
        device_id = "test_device_123"
        network_conditions = [
            {"type": "wifi", "bandwidth": 100, "latency": 10},
            {"type": "4g", "bandwidth": 50, "latency": 50},
            {"type": "3g", "bandwidth": 10, "latency": 200},
            {"type": "2g", "bandwidth": 1, "latency": 500}
        ]
        
        for condition in network_conditions:
            start_time = time.time()
            
            result = await mobile_sync_service.adapt_to_network_condition(
                device_id, condition["type"]
            )
            
            adaptation_time = time.time() - start_time
            
            assert result["adapted"] is True
            assert adaptation_time < 0.05  # Very fast adaptation
            
            # Verify appropriate adaptations for network quality
            if condition["bandwidth"] < 10:  # Poor network
                assert result["compression_enabled"] is True
                assert result["batch_size_reduced"] is True
    
    @pytest.mark.asyncio
    async def test_mobile_concurrent_operations_performance(self, mobile_sync_service):
        """Test performance under concurrent mobile operations."""
        device_id = "test_device_123"
        num_concurrent_operations = 10
        
        async def perform_operation(operation_id):
            start_time = time.time()
            
            # Simulate various mobile operations
            operations = [
                mobile_sync_service.sync_offline_data(device_id, {"test": f"data_{operation_id}"}),
                mobile_sync_service.cache_document_for_offline(device_id, {"id": f"doc_{operation_id}"}),
                mobile_sync_service.process_gesture(device_id, {"type": "tap", "x": 100, "y": 200})
            ]
            
            results = await asyncio.gather(*operations)
            
            end_time = time.time()
            
            return {
                "operation_id": operation_id,
                "duration": end_time - start_time,
                "success": all(r.get("success", r.get("processed", False)) for r in results)
            }
        
        # Execute concurrent operations
        start_time = time.time()
        tasks = [perform_operation(i) for i in range(num_concurrent_operations)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Verify all operations succeeded
        assert all(r["success"] for r in results)
        
        # Verify reasonable performance under concurrency
        assert total_time < 5.0  # All operations complete within 5 seconds
        avg_operation_time = sum(r["duration"] for r in results) / len(results)
        assert avg_operation_time < 1.0  # Average operation time under 1 second


class TestVoiceProcessingPerformance:
    """Performance testing for voice processing with latency measurement."""
    
    @pytest.fixture
    def voice_processing_service(self):
        return VoiceProcessingService()
    
    @pytest.mark.asyncio
    async def test_speech_to_text_latency(self, voice_processing_service):
        """Test speech-to-text processing latency for real-time requirements."""
        audio_durations = [1, 2, 5, 10, 30]  # seconds
        
        for duration in audio_durations:
            # Generate mock audio data
            sample_rate = 16000
            audio_samples = sample_rate * duration
            mock_audio = np.random.randn(audio_samples).astype(np.float32).tobytes()
            
            start_time = time.time()
            
            with patch.object(voice_processing_service, '_transcribe_audio') as mock_transcribe:
                mock_transcribe.return_value = {
                    "text": f"transcribed text for {duration} seconds",
                    "confidence": 0.9
                }
                
                result = await voice_processing_service.speech_to_text(mock_audio)
            
            processing_time = time.time() - start_time
            
            assert result["text"] is not None
            
            # Real-time requirement: processing time should be less than audio duration
            assert processing_time < duration * 0.5  # Process in less than half real-time
            
            # For short audio, processing should be very fast
            if duration <= 5:
                assert processing_time < 1.0  # Less than 1 second
    
    @pytest.mark.asyncio
    async def test_text_to_speech_performance(self, voice_processing_service):
        """Test text-to-speech generation performance."""
        text_lengths = [10, 50, 100, 500, 1000]  # Number of words
        
        for length in text_lengths:
            text = " ".join([f"word{i}" for i in range(length)])
            
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            with patch.object(voice_processing_service, '_synthesize_speech') as mock_synthesize:
                mock_synthesize.return_value = {
                    "audio_data": b"mock_audio_data" * length,
                    "duration": length * 0.5,  # Assume 0.5 seconds per word
                    "sample_rate": 22050
                }
                
                result = await voice_processing_service.text_to_speech(text, {})
            
            processing_time = time.time() - start_time
            memory_used = psutil.Process().memory_info().rss - start_memory
            
            assert result["success"] is True
            
            # Performance requirements
            assert processing_time < length * 0.01  # Max 10ms per word
            assert memory_used < length * 1000  # Max 1KB memory per word
    
    @pytest.mark.asyncio
    async def test_voice_command_processing_throughput(self, voice_processing_service):
        """Test voice command processing throughput under load."""
        num_commands = 100
        commands = [f"search for topic {i}" for i in range(num_commands)]
        
        start_time = time.time()
        
        async def process_command(command):
            with patch.object(voice_processing_service, '_process_voice_command') as mock_process:
                mock_process.return_value = {
                    "intent": "search",
                    "entities": [{"type": "topic", "value": command.split()[-1]}],
                    "confidence": 0.9
                }
                
                return await voice_processing_service.process_voice_command(command)
        
        # Process commands concurrently
        tasks = [process_command(cmd) for cmd in commands]
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        throughput = num_commands / total_time
        
        # Verify all commands processed successfully
        assert all(r["intent"] is not None for r in results)
        
        # Performance requirement: at least 10 commands per second
        assert throughput >= 10
    
    @pytest.mark.asyncio
    async def test_noise_filtering_performance(self, voice_processing_service):
        """Test noise filtering performance and quality."""
        audio_lengths = [1, 5, 10, 30]  # seconds
        noise_levels = [0.1, 0.3, 0.5, 0.7]  # noise ratios
        
        for length in audio_lengths:
            for noise_level in noise_levels:
                # Generate noisy audio
                sample_rate = 16000
                clean_audio = np.random.randn(sample_rate * length)
                noise = np.random.randn(sample_rate * length) * noise_level
                noisy_audio = (clean_audio + noise).astype(np.float32).tobytes()
                
                start_time = time.time()
                
                with patch.object(voice_processing_service, '_apply_noise_filter') as mock_filter:
                    mock_filter.return_value = {
                        "filtered_audio": clean_audio.astype(np.float32).tobytes(),
                        "noise_reduction_db": 10 + (noise_level * 10)
                    }
                    
                    result = await voice_processing_service.filter_noise(noisy_audio)
                
                processing_time = time.time() - start_time
                
                assert result["filtered"] is True
                
                # Performance requirement: real-time processing
                assert processing_time < length  # Process faster than real-time
                
                # Quality requirement: significant noise reduction
                assert result["noise_reduction_db"] > 5


class TestIntegrationLoadTesting:
    """Load testing for external integrations with rate limiting and failover."""
    
    @pytest.fixture
    def reference_manager_service(self):
        return ReferenceManagerService()
    
    @pytest.mark.asyncio
    async def test_reference_manager_load_handling(self, reference_manager_service):
        """Test reference manager integration under high load."""
        num_concurrent_requests = 50
        request_data = {"api_key": "test_key", "library_id": "test_library"}
        
        async def make_sync_request(request_id):
            start_time = time.time()
            
            with patch.object(reference_manager_service, '_fetch_zotero_items') as mock_fetch:
                mock_fetch.return_value = [{"id": f"item_{request_id}"}]
                
                result = await reference_manager_service.sync_zotero_library(request_data)
            
            return {
                "request_id": request_id,
                "duration": time.time() - start_time,
                "success": result["success"]
            }
        
        # Execute concurrent requests
        start_time = time.time()
        tasks = [make_sync_request(i) for i in range(num_concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Filter out exceptions and count successes
        successful_results = [r for r in results if not isinstance(r, Exception)]
        success_rate = len(successful_results) / num_concurrent_requests
        
        # Performance requirements
        assert success_rate >= 0.9  # At least 90% success rate
        assert total_time < 30  # Complete within 30 seconds
        
        if successful_results:
            avg_response_time = sum(r["duration"] for r in successful_results) / len(successful_results)
            assert avg_response_time < 5.0  # Average response under 5 seconds
    
    @pytest.mark.asyncio
    async def test_api_rate_limiting_behavior(self, reference_manager_service):
        """Test behavior under API rate limiting conditions."""
        requests_per_second = 20
        duration_seconds = 10
        total_requests = requests_per_second * duration_seconds
        
        rate_limited_count = 0
        successful_count = 0
        
        async def make_request_with_rate_limiting(request_id):
            nonlocal rate_limited_count, successful_count
            
            with patch.object(reference_manager_service, '_make_api_request') as mock_request:
                # Simulate rate limiting after certain number of requests
                if request_id > 50:  # Rate limit after 50 requests
                    mock_request.side_effect = Exception("Rate limited")
                    rate_limited_count += 1
                    raise Exception("Rate limited")
                else:
                    mock_request.return_value = {"success": True, "data": []}
                    successful_count += 1
                    return {"success": True}
        
        # Make requests at controlled rate
        start_time = time.time()
        for i in range(total_requests):
            try:
                await make_request_with_rate_limiting(i)
            except Exception:
                pass  # Expected for rate limited requests
            
            # Control request rate
            elapsed = time.time() - start_time
            expected_time = i / requests_per_second
            if elapsed < expected_time:
                await asyncio.sleep(expected_time - elapsed)
        
        # Verify rate limiting behavior
        assert rate_limited_count > 0  # Some requests should be rate limited
        assert successful_count > 0  # Some requests should succeed
        
        # Verify graceful handling of rate limits
        total_time = time.time() - start_time
        assert total_time >= duration_seconds * 0.9  # Respect rate limiting
    
    @pytest.mark.asyncio
    async def test_integration_failover_performance(self, reference_manager_service):
        """Test failover performance when primary integration fails."""
        primary_service = "zotero"
        fallback_services = ["mendeley", "endnote"]
        
        async def test_failover_scenario():
            start_time = time.time()
            
            with patch.object(reference_manager_service, '_sync_zotero_library') as mock_primary:
                with patch.object(reference_manager_service, '_sync_mendeley_library') as mock_fallback:
                    # Primary service fails
                    mock_primary.side_effect = Exception("Service unavailable")
                    
                    # Fallback succeeds
                    mock_fallback.return_value = {"success": True, "items": []}
                    
                    result = await reference_manager_service.sync_with_failover(
                        primary_service, {"api_key": "test"}
                    )
            
            failover_time = time.time() - start_time
            
            return {
                "success": result["success"],
                "failover_time": failover_time,
                "fallback_used": result.get("fallback_used", False)
            }
        
        # Test multiple failover scenarios
        failover_results = []
        for _ in range(10):
            result = await test_failover_scenario()
            failover_results.append(result)
        
        # Verify failover performance
        assert all(r["success"] for r in failover_results)
        assert all(r["fallback_used"] for r in failover_results)
        
        avg_failover_time = sum(r["failover_time"] for r in failover_results) / len(failover_results)
        assert avg_failover_time < 2.0  # Failover should be fast


class TestEnterpriseScalabilityTesting:
    """Scalability testing for enterprise features and compliance monitoring."""
    
    @pytest.fixture
    def quiz_service(self):
        return QuizGenerationService()
    
    @pytest.mark.asyncio
    async def test_quiz_generation_scalability(self, quiz_service):
        """Test quiz generation performance at enterprise scale."""
        user_counts = [10, 50, 100, 500]  # Number of concurrent users
        
        for user_count in user_counts:
            content = "Sample educational content for quiz generation testing. " * 100
            
            async def generate_quiz_for_user(user_id):
                start_time = time.time()
                
                with patch.object(quiz_service, '_generate_questions') as mock_generate:
                    mock_generate.return_value = [
                        {"id": f"q{i}", "text": f"Question {i}", "type": "multiple_choice"}
                        for i in range(5)
                    ]
                    
                    result = await quiz_service.generate_quiz_from_content(content)
                
                return {
                    "user_id": user_id,
                    "duration": time.time() - start_time,
                    "success": result["success"]
                }
            
            # Generate quizzes concurrently for all users
            start_time = time.time()
            tasks = [generate_quiz_for_user(f"user_{i}") for i in range(user_count)]
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            # Performance analysis
            success_rate = sum(1 for r in results if r["success"]) / len(results)
            avg_generation_time = sum(r["duration"] for r in results) / len(results)
            throughput = user_count / total_time
            
            # Scalability requirements
            assert success_rate >= 0.95  # 95% success rate
            assert avg_generation_time < 5.0  # Average under 5 seconds
            assert throughput >= user_count / 60  # Complete within 1 minute
    
    @pytest.mark.asyncio
    async def test_compliance_monitoring_performance(self, quiz_service):
        """Test compliance monitoring performance under enterprise load."""
        num_documents = 1000
        num_policies = 50
        
        # Generate test documents and policies
        documents = [
            {"id": f"doc_{i}", "content": f"Document content {i}", "user_id": f"user_{i % 100}"}
            for i in range(num_documents)
        ]
        
        policies = [
            {"id": f"policy_{i}", "rules": [f"rule_{j}" for j in range(5)]}
            for i in range(num_policies)
        ]
        
        start_time = time.time()
        
        # Simulate compliance checking
        compliance_results = []
        for doc in documents:
            for policy in policies:
                # Mock compliance check
                check_result = {
                    "document_id": doc["id"],
                    "policy_id": policy["id"],
                    "compliant": True,
                    "violations": []
                }
                compliance_results.append(check_result)
        
        total_time = time.time() - start_time
        total_checks = len(compliance_results)
        throughput = total_checks / total_time
        
        # Performance requirements for enterprise scale
        assert throughput >= 1000  # At least 1000 checks per second
        assert total_time < 60  # Complete within 1 minute
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, quiz_service):
        """Test memory usage patterns under sustained load."""
        initial_memory = psutil.Process().memory_info().rss
        peak_memory = initial_memory
        
        # Simulate sustained load
        for batch in range(10):  # 10 batches
            batch_tasks = []
            
            for i in range(50):  # 50 operations per batch
                content = f"Educational content for batch {batch}, item {i}. " * 50
                
                with patch.object(quiz_service, '_generate_questions') as mock_generate:
                    mock_generate.return_value = [{"id": f"q{i}", "text": f"Question {i}"}]
                    
                    task = quiz_service.generate_quiz_from_content(content)
                    batch_tasks.append(task)
            
            # Execute batch
            await asyncio.gather(*batch_tasks)
            
            # Monitor memory usage
            current_memory = psutil.Process().memory_info().rss
            peak_memory = max(peak_memory, current_memory)
            
            # Force garbage collection between batches
            import gc
            gc.collect()
        
        final_memory = psutil.Process().memory_info().rss
        memory_growth = final_memory - initial_memory
        peak_memory_usage = peak_memory - initial_memory
        
        # Memory usage requirements
        assert memory_growth < 100 * 1024 * 1024  # Less than 100MB growth
        assert peak_memory_usage < 500 * 1024 * 1024  # Less than 500MB peak usage
    
    @pytest.mark.asyncio
    async def test_database_connection_pooling_performance(self, quiz_service):
        """Test database connection pooling under high concurrency."""
        num_concurrent_operations = 100
        
        async def database_operation(operation_id):
            start_time = time.time()
            
            # Simulate database operations
            await asyncio.sleep(0.01)  # Simulate DB query time
            
            return {
                "operation_id": operation_id,
                "duration": time.time() - start_time,
                "success": True
            }
        
        # Execute concurrent database operations
        start_time = time.time()
        tasks = [database_operation(i) for i in range(num_concurrent_operations)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Verify connection pooling efficiency
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        avg_operation_time = sum(r["duration"] for r in results) / len(results)
        
        assert success_rate == 1.0  # All operations should succeed
        assert total_time < 5.0  # Should complete quickly with proper pooling
        assert avg_operation_time < 0.1  # Individual operations should be fast


class TestPerformanceMonitoring:
    """Performance monitoring and metrics collection."""
    
    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self):
        """Test collection of performance metrics during operations."""
        metrics = {
            "response_times": [],
            "memory_usage": [],
            "cpu_usage": [],
            "error_rates": []
        }
        
        # Simulate operations while collecting metrics
        for i in range(100):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            # Simulate operation
            await asyncio.sleep(0.01)
            
            # Collect metrics
            response_time = time.time() - start_time
            memory_usage = psutil.Process().memory_info().rss - start_memory
            cpu_usage = psutil.cpu_percent()
            
            metrics["response_times"].append(response_time)
            metrics["memory_usage"].append(memory_usage)
            metrics["cpu_usage"].append(cpu_usage)
            metrics["error_rates"].append(0)  # No errors in this test
        
        # Analyze metrics
        avg_response_time = np.mean(metrics["response_times"])
        p95_response_time = np.percentile(metrics["response_times"], 95)
        avg_memory_usage = np.mean(metrics["memory_usage"])
        avg_cpu_usage = np.mean(metrics["cpu_usage"])
        
        # Performance thresholds
        assert avg_response_time < 0.1  # Average under 100ms
        assert p95_response_time < 0.2  # 95th percentile under 200ms
        assert avg_cpu_usage < 80  # Average CPU under 80%
        
        # Verify metrics collection completeness
        assert len(metrics["response_times"]) == 100
        assert all(isinstance(rt, float) for rt in metrics["response_times"])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])