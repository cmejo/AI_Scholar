"""
Performance tests for the AI Scholar RAG system.
Tests scalability, response times, and resource usage.
"""
import pytest
import asyncio
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, patch
from services.enhanced_rag_service import EnhancedRAGService
from services.memory_service import ConversationMemoryManager
from services.analytics_service import AnalyticsService


@pytest.mark.performance
class TestRAGServicePerformance:
    """Performance tests for RAG service."""
    
    @pytest.fixture
    def performance_rag_service(self, test_db_session, mock_redis):
        """Create RAG service for performance testing."""
        with patch('services.enhanced_rag_service.VectorStore') as mock_vector_store:
            mock_vector_store.return_value.similarity_search.return_value = [
                {
                    'content': f'Test content {i}',
                    'metadata': {'source': f'doc{i}.pdf'},
                    'score': 0.9 - (i * 0.1)
                }
                for i in range(5)
            ]
            
            return EnhancedRAGService(
                db_session=test_db_session,
                redis_client=mock_redis
            )
    
    @pytest.mark.asyncio
    async def test_single_query_response_time(self, performance_rag_service, performance_timer):
        """Test single query response time."""
        query = "What is machine learning?"
        user_id = "perf-test-user"
        
        performance_timer.start()
        
        response = await performance_rag_service.generate_response(
            query=query,
            user_id=user_id
        )
        
        performance_timer.stop()
        
        # Verify response
        assert 'response' in response
        
        # Performance assertion: should respond within 5 seconds
        assert performance_timer.elapsed < 5.0, f"Response took {performance_timer.elapsed:.2f}s"
        
        print(f"Single query response time: {performance_timer.elapsed:.3f}s")
    
    @pytest.mark.asyncio
    async def test_concurrent_queries_performance(self, performance_rag_service, performance_timer):
        """Test performance with concurrent queries."""
        queries = [
            "What is machine learning?",
            "Explain neural networks",
            "How does deep learning work?",
            "What are the applications of AI?",
            "Describe supervised learning",
            "What is unsupervised learning?",
            "Explain reinforcement learning",
            "How do transformers work?",
            "What is natural language processing?",
            "Describe computer vision"
        ]
        
        user_id = "perf-test-user"
        
        performance_timer.start()
        
        # Execute queries concurrently
        tasks = [
            performance_rag_service.generate_response(query=query, user_id=user_id)
            for query in queries
        ]
        
        responses = await asyncio.gather(*tasks)
        
        performance_timer.stop()
        
        # Verify all responses
        assert len(responses) == len(queries)
        assert all('response' in r for r in responses)
        
        # Performance assertion: 10 concurrent queries should complete within 15 seconds
        assert performance_timer.elapsed < 15.0, f"Concurrent queries took {performance_timer.elapsed:.2f}s"
        
        avg_time_per_query = performance_timer.elapsed / len(queries)
        print(f"Concurrent queries total time: {performance_timer.elapsed:.3f}s")
        print(f"Average time per query: {avg_time_per_query:.3f}s")
    
    @pytest.mark.asyncio
    async def test_memory_usage_during_queries(self, performance_rag_service):
        """Test memory usage during query processing."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        queries = [f"Test query number {i}" for i in range(50)]
        user_id = "perf-test-user"
        
        # Execute queries and monitor memory
        memory_samples = []
        
        for i, query in enumerate(queries):
            await performance_rag_service.generate_response(query=query, user_id=user_id)
            
            if i % 10 == 0:  # Sample every 10 queries
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_samples.append(current_memory)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"Final memory: {final_memory:.2f} MB")
        print(f"Memory increase: {memory_increase:.2f} MB")
        
        # Performance assertion: memory increase should be reasonable (< 100MB for 50 queries)
        assert memory_increase < 100, f"Memory increased by {memory_increase:.2f} MB"
    
    @pytest.mark.asyncio
    async def test_query_throughput(self, performance_rag_service):
        """Test query throughput (queries per second)."""
        duration_seconds = 10
        query_count = 0
        user_id = "perf-test-user"
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        while time.time() < end_time:
            await performance_rag_service.generate_response(
                query=f"Test query {query_count}",
                user_id=user_id
            )
            query_count += 1
        
        actual_duration = time.time() - start_time
        throughput = query_count / actual_duration
        
        print(f"Processed {query_count} queries in {actual_duration:.2f}s")
        print(f"Throughput: {throughput:.2f} queries/second")
        
        # Performance assertion: should handle at least 1 query per second
        assert throughput >= 1.0, f"Throughput too low: {throughput:.2f} queries/second"


@pytest.mark.performance
class TestMemoryServicePerformance:
    """Performance tests for memory service."""
    
    @pytest.fixture
    def performance_memory_service(self, mock_redis, test_db_session):
        """Create memory service for performance testing."""
        return ConversationMemoryManager(
            redis_client=mock_redis,
            db_session=test_db_session
        )
    
    @pytest.mark.asyncio
    async def test_memory_storage_performance(self, performance_memory_service, performance_timer):
        """Test memory storage performance."""
        conversation_id = "perf-conv-123"
        memory_items = [
            {
                'content': f'Memory item {i}',
                'importance_score': 0.5,
                'timestamp': time.time()
            }
            for i in range(1000)
        ]
        
        performance_timer.start()
        
        # Store memory items
        for item in memory_items:
            await performance_memory_service.store_memory_item(conversation_id, item)
        
        performance_timer.stop()
        
        avg_time_per_item = performance_timer.elapsed / len(memory_items)
        
        print(f"Stored {len(memory_items)} memory items in {performance_timer.elapsed:.3f}s")
        print(f"Average time per item: {avg_time_per_item:.6f}s")
        
        # Performance assertion: should store 1000 items within 10 seconds
        assert performance_timer.elapsed < 10.0, f"Memory storage took {performance_timer.elapsed:.2f}s"
    
    @pytest.mark.asyncio
    async def test_memory_retrieval_performance(self, performance_memory_service, performance_timer):
        """Test memory retrieval performance."""
        conversation_id = "perf-conv-456"
        
        # Mock stored memory data
        mock_memory_data = {
            'short_term_memory': [
                {
                    'content': f'Memory item {i}',
                    'importance_score': 0.5,
                    'timestamp': time.time()
                }
                for i in range(1000)
            ]
        }
        
        with patch.object(performance_memory_service, '_get_redis_context', return_value=mock_memory_data):
            performance_timer.start()
            
            # Retrieve memory multiple times
            for _ in range(100):
                await performance_memory_service.retrieve_memory_items(conversation_id)
            
            performance_timer.stop()
        
        avg_time_per_retrieval = performance_timer.elapsed / 100
        
        print(f"Retrieved memory 100 times in {performance_timer.elapsed:.3f}s")
        print(f"Average time per retrieval: {avg_time_per_retrieval:.6f}s")
        
        # Performance assertion: should retrieve memory within reasonable time
        assert avg_time_per_retrieval < 0.1, f"Memory retrieval too slow: {avg_time_per_retrieval:.6f}s"


@pytest.mark.performance
class TestAnalyticsServicePerformance:
    """Performance tests for analytics service."""
    
    @pytest.fixture
    def performance_analytics_service(self, test_db_session, mock_redis):
        """Create analytics service for performance testing."""
        return AnalyticsService(
            db_session=test_db_session,
            redis_client=mock_redis
        )
    
    @pytest.mark.asyncio
    async def test_analytics_tracking_performance(self, performance_analytics_service, performance_timer):
        """Test analytics event tracking performance."""
        user_id = "perf-user-123"
        events = [
            {
                'event_type': 'query',
                'data': {
                    'query': f'Test query {i}',
                    'response_time': 1.5,
                    'confidence': 0.8
                }
            }
            for i in range(1000)
        ]
        
        performance_timer.start()
        
        # Track events
        for event in events:
            await performance_analytics_service.track_event(
                user_id=user_id,
                event_type=event['event_type'],
                data=event['data']
            )
        
        performance_timer.stop()
        
        avg_time_per_event = performance_timer.elapsed / len(events)
        
        print(f"Tracked {len(events)} events in {performance_timer.elapsed:.3f}s")
        print(f"Average time per event: {avg_time_per_event:.6f}s")
        
        # Performance assertion: should track 1000 events within 5 seconds
        assert performance_timer.elapsed < 5.0, f"Event tracking took {performance_timer.elapsed:.2f}s"
    
    @pytest.mark.asyncio
    async def test_analytics_report_generation_performance(self, performance_analytics_service, performance_timer):
        """Test analytics report generation performance."""
        user_id = "perf-user-456"
        
        # Mock analytics data
        with patch.object(performance_analytics_service, '_get_analytics_data') as mock_get_data:
            mock_get_data.return_value = {
                'queries': [{'query': f'Query {i}', 'timestamp': time.time()} for i in range(10000)],
                'feedback': [{'rating': 5, 'timestamp': time.time()} for _ in range(1000)]
            }
            
            performance_timer.start()
            
            report = await performance_analytics_service.generate_usage_report(
                user_id=user_id,
                time_range='30d'
            )
            
            performance_timer.stop()
        
        print(f"Generated analytics report in {performance_timer.elapsed:.3f}s")
        
        # Verify report structure
        assert 'query_count' in report
        assert 'average_response_time' in report
        
        # Performance assertion: should generate report within 3 seconds
        assert performance_timer.elapsed < 3.0, f"Report generation took {performance_timer.elapsed:.2f}s"


@pytest.mark.performance
class TestScalabilityTests:
    """Scalability tests for the system."""
    
    @pytest.mark.asyncio
    async def test_user_scalability(self, test_db_session, mock_redis):
        """Test system performance with multiple users."""
        num_users = 50
        queries_per_user = 10
        
        with patch('services.enhanced_rag_service.VectorStore') as mock_vector_store:
            mock_vector_store.return_value.similarity_search.return_value = [
                {'content': 'Test content', 'metadata': {}, 'score': 0.9}
            ]
            
            rag_service = EnhancedRAGService(
                db_session=test_db_session,
                redis_client=mock_redis
            )
            
            async def user_session(user_id):
                """Simulate a user session with multiple queries."""
                for i in range(queries_per_user):
                    await rag_service.generate_response(
                        query=f"User {user_id} query {i}",
                        user_id=f"user-{user_id}"
                    )
            
            start_time = time.time()
            
            # Create tasks for all users
            tasks = [user_session(user_id) for user_id in range(num_users)]
            
            # Execute all user sessions concurrently
            await asyncio.gather(*tasks)
            
            end_time = time.time()
            total_time = end_time - start_time
            total_queries = num_users * queries_per_user
            
            print(f"Handled {num_users} users with {queries_per_user} queries each")
            print(f"Total queries: {total_queries}")
            print(f"Total time: {total_time:.2f}s")
            print(f"Queries per second: {total_queries / total_time:.2f}")
            
            # Performance assertion: should handle the load within reasonable time
            assert total_time < 60.0, f"Scalability test took {total_time:.2f}s"
    
    @pytest.mark.asyncio
    async def test_document_processing_scalability(self, test_db_session, mock_redis):
        """Test document processing with multiple documents."""
        num_documents = 20
        
        with patch('services.document_processor.HierarchicalChunkingService') as mock_chunking:
            mock_chunking.return_value.chunk_document.return_value = [
                {'id': f'chunk-{i}', 'content': f'Chunk {i}', 'metadata': {}}
                for i in range(10)
            ]
            
            from services.document_processor import DocumentProcessor
            processor = DocumentProcessor(
                db_session=test_db_session,
                redis_client=mock_redis
            )
            
            async def process_document(doc_id):
                """Process a single document."""
                return await processor.process_document(
                    content=f"Document {doc_id} content with multiple paragraphs and sections.",
                    user_id="test-user",
                    title=f"Document {doc_id}"
                )
            
            start_time = time.time()
            
            # Process documents concurrently
            tasks = [process_document(doc_id) for doc_id in range(num_documents)]
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Verify all documents processed successfully
            assert all(result['success'] for result in results)
            
            print(f"Processed {num_documents} documents in {total_time:.2f}s")
            print(f"Average time per document: {total_time / num_documents:.2f}s")
            
            # Performance assertion: should process documents within reasonable time
            assert total_time < 30.0, f"Document processing took {total_time:.2f}s"


@pytest.mark.performance
class TestResourceUsageTests:
    """Tests for resource usage monitoring."""
    
    @pytest.mark.asyncio
    async def test_cpu_usage_monitoring(self, test_db_session, mock_redis):
        """Monitor CPU usage during intensive operations."""
        with patch('services.enhanced_rag_service.VectorStore') as mock_vector_store:
            mock_vector_store.return_value.similarity_search.return_value = [
                {'content': 'Test content', 'metadata': {}, 'score': 0.9}
            ]
            
            rag_service = EnhancedRAGService(
                db_session=test_db_session,
                redis_client=mock_redis
            )
            
            # Monitor CPU usage
            cpu_samples = []
            
            def monitor_cpu():
                """Monitor CPU usage in background."""
                for _ in range(10):  # Sample for 10 seconds
                    cpu_samples.append(psutil.cpu_percent(interval=1))
            
            # Start CPU monitoring in background
            monitor_thread = threading.Thread(target=monitor_cpu)
            monitor_thread.start()
            
            # Perform intensive operations
            tasks = [
                rag_service.generate_response(
                    query=f"Intensive query {i}",
                    user_id="test-user"
                )
                for i in range(100)
            ]
            
            await asyncio.gather(*tasks)
            
            # Wait for monitoring to complete
            monitor_thread.join()
            
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
            max_cpu = max(cpu_samples)
            
            print(f"Average CPU usage: {avg_cpu:.2f}%")
            print(f"Maximum CPU usage: {max_cpu:.2f}%")
            
            # Performance assertion: CPU usage should be reasonable
            assert avg_cpu < 80.0, f"Average CPU usage too high: {avg_cpu:.2f}%"
    
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, test_db_session, mock_redis):
        """Test for memory leaks during extended operation."""
        with patch('services.enhanced_rag_service.VectorStore') as mock_vector_store:
            mock_vector_store.return_value.similarity_search.return_value = [
                {'content': 'Test content', 'metadata': {}, 'score': 0.9}
            ]
            
            rag_service = EnhancedRAGService(
                db_session=test_db_session,
                redis_client=mock_redis
            )
            
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Perform many operations
            for batch in range(10):  # 10 batches
                tasks = [
                    rag_service.generate_response(
                        query=f"Batch {batch} query {i}",
                        user_id="test-user"
                    )
                    for i in range(50)  # 50 queries per batch
                ]
                
                await asyncio.gather(*tasks)
                
                # Force garbage collection
                import gc
                gc.collect()
                
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                
                print(f"Batch {batch}: Memory usage {current_memory:.2f} MB (+{memory_increase:.2f} MB)")
                
                # Check for excessive memory growth
                if memory_increase > 200:  # More than 200MB increase
                    pytest.fail(f"Potential memory leak detected: {memory_increase:.2f} MB increase")
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            total_increase = final_memory - initial_memory
            
            print(f"Total memory increase: {total_increase:.2f} MB")
            
            # Performance assertion: total memory increase should be reasonable
            assert total_increase < 300, f"Memory increase too high: {total_increase:.2f} MB"


@pytest.mark.performance
@pytest.mark.slow
class TestLoadTests:
    """Load tests for stress testing the system."""
    
    @pytest.mark.asyncio
    async def test_sustained_load(self, test_db_session, mock_redis):
        """Test system under sustained load."""
        duration_minutes = 2  # 2 minute load test
        target_qps = 5  # 5 queries per second
        
        with patch('services.enhanced_rag_service.VectorStore') as mock_vector_store:
            mock_vector_store.return_value.similarity_search.return_value = [
                {'content': 'Load test content', 'metadata': {}, 'score': 0.9}
            ]
            
            rag_service = EnhancedRAGService(
                db_session=test_db_session,
                redis_client=mock_redis
            )
            
            start_time = time.time()
            end_time = start_time + (duration_minutes * 60)
            query_count = 0
            errors = 0
            
            while time.time() < end_time:
                batch_start = time.time()
                
                # Send batch of queries
                tasks = [
                    rag_service.generate_response(
                        query=f"Load test query {query_count + i}",
                        user_id=f"load-user-{i % 10}"  # 10 different users
                    )
                    for i in range(target_qps)
                ]
                
                try:
                    await asyncio.gather(*tasks)
                    query_count += target_qps
                except Exception as e:
                    errors += 1
                    print(f"Error in batch: {e}")
                
                # Wait to maintain target QPS
                batch_duration = time.time() - batch_start
                if batch_duration < 1.0:
                    await asyncio.sleep(1.0 - batch_duration)
            
            actual_duration = time.time() - start_time
            actual_qps = query_count / actual_duration
            error_rate = errors / (query_count / target_qps) if query_count > 0 else 0
            
            print(f"Load test completed:")
            print(f"Duration: {actual_duration:.2f}s")
            print(f"Total queries: {query_count}")
            print(f"Actual QPS: {actual_qps:.2f}")
            print(f"Error rate: {error_rate:.2%}")
            
            # Performance assertions
            assert actual_qps >= target_qps * 0.8, f"QPS too low: {actual_qps:.2f}"
            assert error_rate < 0.05, f"Error rate too high: {error_rate:.2%}"