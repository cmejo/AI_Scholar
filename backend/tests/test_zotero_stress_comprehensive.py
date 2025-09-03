"""
Comprehensive stress tests for Zotero integration.
Tests system behavior under extreme load conditions.
"""
import pytest
import asyncio
import time
import random
import threading
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from fastapi.testclient import TestClient
import psutil
import os
from pathlib import Path

from app import app


@pytest.mark.stress
class TestZoteroHighLoadStress:
    """Stress tests for high load scenarios."""
    
    @pytest.fixture
    def stress_client(self, test_db_session, mock_redis):
        """Create test client for stress testing."""
        app.dependency_overrides.clear()
        
        from core.database import get_db
        from core.redis_client import get_redis_client
        
        app.dependency_overrides[get_db] = lambda: test_db_session
        app.dependency_overrides[get_redis_client] = lambda: mock_redis
        
        with TestClient(app) as client:
            yield client
        
        app.dependency_overrides.clear()
    
    def test_extreme_concurrent_sync_operations(self, stress_client):
        """Test system behavior with extreme number of concurrent sync operations."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Mock sync data
            sync_items = [
                {
                    'key': f'STRESS{i:05d}',
                    'title': f'Stress Test Item {i}',
                    'version': i,
                    'itemType': 'journalArticle',
                    'creators': [{'firstName': f'Author{i}', 'lastName': f'Test{i}'}],
                    'abstractNote': f'Stress test abstract {i}' * 10,  # Larger content
                    'tags': [{'tag': f'stress{i % 100}'}, {'tag': f'test{i % 50}'}]
                }
                for i in range(1000)
            ]
            
            mock_client_instance.get_libraries.return_value = [
                {'id': 'stress-lib', 'type': 'user', 'name': 'Stress Test Library', 'version': 1000}
            ]
            mock_client_instance.get_items.return_value = sync_items
            
            # Test with extreme concurrency (50 simultaneous users)
            num_concurrent_users = 50
            user_ids = [f"stress-user-{i}" for i in range(num_concurrent_users)]
            
            def perform_stress_sync(user_id):
                """Perform sync operation under stress conditions."""
                try:
                    connection_id = f"{user_id}-conn"
                    
                    # Setup connection
                    conn_response = stress_client.post(
                        "/api/zotero/auth/test-connection",
                        json={"user_id": user_id, "access_token": f"stress-token-{user_id}"}
                    )
                    
                    # Perform sync
                    start_time = time.time()
                    sync_response = stress_client.post(
                        f"/api/zotero/sync/{connection_id}/libraries",
                        json={"batch_size": 100}
                    )
                    duration = time.time() - start_time
                    
                    return {
                        'user_id': user_id,
                        'success': sync_response.status_code == 200,
                        'duration': duration,
                        'status_code': sync_response.status_code,
                        'error': None
                    }
                    
                except Exception as e:
                    return {
                        'user_id': user_id,
                        'success': False,
                        'duration': 0,
                        'status_code': 500,
                        'error': str(e)
                    }
            
            # Monitor system resources during stress test
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            initial_cpu = process.cpu_percent()
            
            start_time = time.time()
            
            # Execute extreme concurrent load
            with ThreadPoolExecutor(max_workers=num_concurrent_users) as executor:
                futures = [executor.submit(perform_stress_sync, user_id) for user_id in user_ids]
                results = [future.result() for future in as_completed(futures)]
            
            total_duration = time.time() - start_time
            
            # Monitor final system state
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Analyze results
            successful_syncs = [r for r in results if r['success']]
            failed_syncs = [r for r in results if not r['success']]
            
            success_rate = len(successful_syncs) / len(results) * 100
            avg_duration = sum(r['duration'] for r in successful_syncs) / len(successful_syncs) if successful_syncs else 0
            
            # Stress test assertions
            assert success_rate >= 80.0  # At least 80% success rate under extreme load
            assert total_duration < 600.0  # Should complete within 10 minutes
            assert memory_increase < 2000  # Memory increase should be manageable (< 2GB)
            
            print(f"Extreme Concurrent Sync Stress Test Results:")
            print(f"  - Concurrent users: {num_concurrent_users}")
            print(f"  - Success rate: {success_rate:.1f}%")
            print(f"  - Total duration: {total_duration:.2f}s")
            print(f"  - Average sync duration: {avg_duration:.2f}s")
            print(f"  - Memory increase: {memory_increase:.2f}MB")
            print(f"  - Failed syncs: {len(failed_syncs)}")
    
    def test_sustained_load_endurance(self, stress_client):
        """Test system behavior under sustained load over extended period."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Mock smaller dataset for sustained testing
            sustained_items = [
                {
                    'key': f'SUST{i:04d}',
                    'title': f'Sustained Test Item {i}',
                    'version': i,
                    'itemType': 'journalArticle'
                }
                for i in range(100)
            ]
            
            mock_client_instance.get_libraries.return_value = [
                {'id': 'sustained-lib', 'type': 'user', 'name': 'Sustained Test Library', 'version': 100}
            ]
            mock_client_instance.get_items.return_value = sustained_items
            
            # Test parameters
            test_duration = 300  # 5 minutes of sustained load
            operations_per_minute = 60  # 1 operation per second
            concurrent_users = 10
            
            def sustained_user_activity(user_id, stop_event):
                """Simulate sustained user activity."""
                operations = []
                operation_count = 0
                
                while not stop_event.is_set():
                    try:
                        # Randomize operation types
                        operation_type = random.choice(['sync', 'search', 'citation'])
                        start_time = time.time()
                        
                        if operation_type == 'sync':
                            response = stress_client.post(
                                f"/api/zotero/sync/{user_id}-conn/libraries"
                            )
                        elif operation_type == 'search':
                            response = stress_client.post(
                                "/api/zotero/search",
                                json={"query": f"test {random.randint(1, 100)}", "library_id": "sustained-lib"}
                            )
                        else:  # citation
                            response = stress_client.post(
                                "/api/zotero/citations/generate",
                                json={"item_keys": [f"SUST{random.randint(0, 99):04d}"], "style": "apa"}
                            )
                        
                        duration = time.time() - start_time
                        operation_count += 1
                        
                        operations.append({
                            'type': operation_type,
                            'success': response.status_code == 200,
                            'duration': duration,
                            'timestamp': datetime.now()
                        })
                        
                        # Rate limiting to maintain consistent load
                        time.sleep(1.0)  # 1 operation per second
                        
                    except Exception as e:
                        operations.append({
                            'type': 'error',
                            'success': False,
                            'duration': 0,
                            'error': str(e),
                            'timestamp': datetime.now()
                        })
                
                return operations
            
            # Setup users
            for i in range(concurrent_users):
                user_id = f"sustained-user-{i}"
                stress_client.post(
                    "/api/zotero/auth/test-connection",
                    json={"user_id": user_id, "access_token": f"sustained-token-{i}"}
                )
            
            # Start sustained load test
            stop_event = threading.Event()
            user_threads = []
            
            start_time = time.time()
            
            # Start user activity threads
            for i in range(concurrent_users):
                user_id = f"sustained-user-{i}"
                thread = threading.Thread(
                    target=lambda uid=user_id: sustained_user_activity(uid, stop_event),
                    daemon=True
                )
                thread.start()
                user_threads.append(thread)
            
            # Monitor system resources during test
            resource_samples = []
            
            def monitor_resources():
                while not stop_event.is_set():
                    process = psutil.Process(os.getpid())
                    resource_samples.append({
                        'timestamp': time.time(),
                        'memory_mb': process.memory_info().rss / 1024 / 1024,
                        'cpu_percent': process.cpu_percent(),
                        'threads': process.num_threads()
                    })
                    time.sleep(10)  # Sample every 10 seconds
            
            monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
            monitor_thread.start()
            
            # Run for specified duration
            time.sleep(test_duration)
            
            # Stop all activities
            stop_event.set()
            
            # Wait for threads to complete
            for thread in user_threads:
                thread.join(timeout=5)
            
            total_test_duration = time.time() - start_time
            
            # Analyze resource usage
            if resource_samples:
                avg_memory = sum(s['memory_mb'] for s in resource_samples) / len(resource_samples)
                max_memory = max(s['memory_mb'] for s in resource_samples)
                avg_cpu = sum(s['cpu_percent'] for s in resource_samples) / len(resource_samples)
                max_cpu = max(s['cpu_percent'] for s in resource_samples)
                
                # Endurance test assertions
                assert max_memory < 1500  # Memory should stay under 1.5GB
                assert avg_cpu < 80.0     # Average CPU should stay under 80%
                assert total_test_duration >= test_duration * 0.95  # Should run for nearly full duration
                
                print(f"Sustained Load Endurance Test Results:")
                print(f"  - Test duration: {total_test_duration:.1f}s")
                print(f"  - Concurrent users: {concurrent_users}")
                print(f"  - Average memory: {avg_memory:.1f}MB")
                print(f"  - Max memory: {max_memory:.1f}MB")
                print(f"  - Average CPU: {avg_cpu:.1f}%")
                print(f"  - Max CPU: {max_cpu:.1f}%")
                print(f"  - Resource samples: {len(resource_samples)}")
    
    def test_memory_leak_detection(self, stress_client):
        """Test for memory leaks during repeated operations."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Mock data for memory leak testing
            leak_test_items = [
                {
                    'key': f'LEAK{i:04d}',
                    'title': f'Memory Leak Test Item {i}',
                    'abstractNote': 'A' * 1000,  # 1KB per item
                    'version': i
                }
                for i in range(100)
            ]
            
            mock_client_instance.get_libraries.return_value = [
                {'id': 'leak-lib', 'type': 'user', 'name': 'Memory Leak Test Library', 'version': 100}
            ]
            mock_client_instance.get_items.return_value = leak_test_items
            
            # Setup test user
            user_id = "memory-leak-user"
            connection_id = f"{user_id}-conn"
            
            stress_client.post(
                "/api/zotero/auth/test-connection",
                json={"user_id": user_id, "access_token": "leak-test-token"}
            )
            
            # Perform repeated operations to detect memory leaks
            num_iterations = 50
            memory_samples = []
            
            process = psutil.Process(os.getpid())
            
            for iteration in range(num_iterations):
                # Measure memory before operation
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
                
                # Perform sync operation
                sync_response = stress_client.post(
                    f"/api/zotero/sync/{connection_id}/libraries"
                )
                
                # Perform search operation
                search_response = stress_client.post(
                    "/api/zotero/search",
                    json={"query": f"test {iteration}", "library_id": "leak-lib"}
                )
                
                # Perform citation operation
                citation_response = stress_client.post(
                    "/api/zotero/citations/generate",
                    json={"item_keys": [f"LEAK{iteration % 100:04d}"], "style": "apa"}
                )
                
                # Measure memory after operations
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                
                memory_samples.append({
                    'iteration': iteration,
                    'memory_before': memory_before,
                    'memory_after': memory_after,
                    'memory_diff': memory_after - memory_before,
                    'sync_success': sync_response.status_code == 200,
                    'search_success': search_response.status_code == 200,
                    'citation_success': citation_response.status_code == 200
                })
                
                # Small delay between iterations
                time.sleep(0.1)
            
            # Analyze memory usage patterns
            initial_memory = memory_samples[0]['memory_before']
            final_memory = memory_samples[-1]['memory_after']
            total_memory_increase = final_memory - initial_memory
            
            # Calculate memory growth trend
            memory_values = [sample['memory_after'] for sample in memory_samples]
            
            # Simple linear regression to detect memory growth trend
            n = len(memory_values)
            sum_x = sum(range(n))
            sum_y = sum(memory_values)
            sum_xy = sum(i * memory_values[i] for i in range(n))
            sum_x2 = sum(i * i for i in range(n))
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            # Memory leak detection assertions
            assert total_memory_increase < 200  # Total increase should be less than 200MB
            assert slope < 2.0  # Memory growth slope should be minimal (< 2MB per iteration)
            
            # Check operation success rates
            sync_success_rate = sum(1 for s in memory_samples if s['sync_success']) / len(memory_samples) * 100
            search_success_rate = sum(1 for s in memory_samples if s['search_success']) / len(memory_samples) * 100
            citation_success_rate = sum(1 for s in memory_samples if s['citation_success']) / len(memory_samples) * 100
            
            assert sync_success_rate >= 95.0
            assert search_success_rate >= 95.0
            assert citation_success_rate >= 95.0
            
            print(f"Memory Leak Detection Test Results:")
            print(f"  - Iterations: {num_iterations}")
            print(f"  - Initial memory: {initial_memory:.1f}MB")
            print(f"  - Final memory: {final_memory:.1f}MB")
            print(f"  - Total increase: {total_memory_increase:.1f}MB")
            print(f"  - Growth slope: {slope:.3f}MB/iteration")
            print(f"  - Sync success rate: {sync_success_rate:.1f}%")
            print(f"  - Search success rate: {search_success_rate:.1f}%")
            print(f"  - Citation success rate: {citation_success_rate:.1f}%")


@pytest.mark.stress
class TestZoteroDataVolumeStress:
    """Stress tests for handling large data volumes."""
    
    @pytest.fixture
    def massive_dataset(self):
        """Generate massive dataset for volume stress testing."""
        # Generate 50,000 items for extreme volume testing
        items = []
        collections = []
        
        # Generate collections
        for i in range(500):
            collections.append({
                'key': f'VOLCOLL{i:04d}',
                'name': f'Volume Test Collection {i}',
                'parentCollection': f'VOLCOLL{i//10:04d}' if i >= 10 else None,
                'version': i + 1
            })
        
        # Generate massive item dataset
        for i in range(50000):
            items.append({
                'key': f'VOL{i:06d}',
                'version': i + 1,
                'itemType': ['journalArticle', 'book', 'thesis', 'conferencePaper'][i % 4],
                'title': f'Volume Stress Test Item {i}: {"Long Title " * (i % 10 + 1)}',
                'creators': [
                    {
                        'creatorType': 'author',
                        'firstName': f'FirstName{i % 1000}',
                        'lastName': f'LastName{i % 500}'
                    }
                    for _ in range(1 + i % 5)  # Variable number of authors
                ],
                'publicationTitle': f'Journal {i % 200}' if i % 4 == 0 else None,
                'publisher': f'Publisher {i % 100}' if i % 4 == 1 else None,
                'date': str(1990 + (i % 34)),
                'abstractNote': f'Volume test abstract {i}: {"Abstract content " * (i % 20 + 5)}',
                'tags': [
                    {'tag': f'volume{i % 1000}'},
                    {'tag': f'stress{i % 500}'},
                    {'tag': f'test{i % 250}'},
                    {'tag': f'category{i % 100}'}
                ],
                'collections': [f'VOLCOLL{i % 500:04d}'],
                'extra': f'Extra metadata for volume testing: {"Data " * (i % 50)}'
            })
        
        return {
            'items': items,
            'collections': collections,
            'libraries': [
                {
                    'id': 'volume-stress-lib',
                    'type': 'user',
                    'name': 'Volume Stress Test Library',
                    'version': 50000
                }
            ]
        }
    
    def test_massive_library_sync_stress(self, stress_client, massive_dataset):
        """Test sync performance with massive library (50,000 items)."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Mock massive dataset responses
            mock_client_instance.get_libraries.return_value = massive_dataset['libraries']
            mock_client_instance.get_collections.return_value = massive_dataset['collections']
            
            # Split items into chunks to simulate paginated API responses
            chunk_size = 1000
            item_chunks = [
                massive_dataset['items'][i:i + chunk_size]
                for i in range(0, len(massive_dataset['items']), chunk_size)
            ]
            
            mock_client_instance.get_items.side_effect = item_chunks
            
            user_id = "volume-stress-user"
            connection_id = f"{user_id}-conn"
            
            # Setup connection
            stress_client.post(
                "/api/zotero/auth/test-connection",
                json={"user_id": user_id, "access_token": "volume-stress-token"}
            )
            
            # Monitor system resources
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Perform massive sync
            start_time = time.time()
            
            sync_response = stress_client.post(
                f"/api/zotero/sync/{connection_id}/libraries",
                json={
                    "batch_size": 1000,  # Large batch size for efficiency
                    "parallel_processing": True,
                    "memory_optimization": True
                }
            )
            
            sync_duration = time.time() - start_time
            
            # Monitor final memory state
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Volume stress test assertions
            assert sync_response.status_code == 200
            assert sync_duration < 1800.0  # Should complete within 30 minutes
            assert memory_increase < 3000   # Memory increase should be manageable (< 3GB)
            
            sync_data = sync_response.json()
            assert sync_data["success"] is True
            
            # Calculate processing metrics
            items_per_second = len(massive_dataset['items']) / sync_duration
            memory_per_item = memory_increase / len(massive_dataset['items']) * 1024  # KB per item
            
            assert items_per_second > 25  # Should process at least 25 items per second
            assert memory_per_item < 50   # Should use less than 50KB per item
            
            print(f"Massive Library Sync Stress Test Results:")
            print(f"  - Items processed: {len(massive_dataset['items']):,}")
            print(f"  - Collections processed: {len(massive_dataset['collections']):,}")
            print(f"  - Sync duration: {sync_duration:.1f}s ({sync_duration/60:.1f}m)")
            print(f"  - Processing rate: {items_per_second:.1f} items/second")
            print(f"  - Memory increase: {memory_increase:.1f}MB")
            print(f"  - Memory per item: {memory_per_item:.2f}KB")
    
    def test_search_performance_massive_dataset(self, stress_client, massive_dataset):
        """Test search performance with massive dataset."""
        
        with patch('services.zotero.zotero_search_service.ZoteroSearchService') as mock_search:
            mock_search_instance = AsyncMock()
            mock_search.return_value = mock_search_instance
            
            def mock_massive_search(query, **kwargs):
                # Simulate realistic search processing time for massive dataset
                base_time = 0.5  # Base search time
                complexity_factor = len(query) / 100  # Query complexity
                dataset_factor = len(massive_dataset['items']) / 100000  # Dataset size factor
                
                processing_time = base_time + complexity_factor + dataset_factor
                time.sleep(min(processing_time, 5.0))  # Cap at 5 seconds
                
                # Simulate realistic search results
                matching_items = [
                    item for item in massive_dataset['items'][:5000]  # Search subset
                    if query.lower() in item['title'].lower() or 
                       query.lower() in item.get('abstractNote', '').lower()
                ][:200]  # Limit results
                
                return {
                    'items': matching_items,
                    'total_count': len(matching_items),
                    'facets': {
                        'authors': [{'name': f'Author{i}', 'count': random.randint(10, 100)} for i in range(50)],
                        'years': [{'year': str(1990 + i), 'count': random.randint(50, 500)} for i in range(34)],
                        'tags': [{'tag': f'tag{i}', 'count': random.randint(25, 250)} for i in range(100)],
                        'types': [{'type': t, 'count': random.randint(100, 1000)} for t in ['journalArticle', 'book', 'thesis']]
                    },
                    'processing_time': processing_time
                }
            
            mock_search_instance.search_items.side_effect = mock_massive_search
            
            # Test complex search scenarios
            complex_queries = [
                "machine learning artificial intelligence",
                "neural networks deep learning optimization",
                "natural language processing computational linguistics",
                "computer vision image recognition pattern",
                "data mining knowledge discovery database",
                "algorithm complexity computational theory",
                "software engineering design patterns architecture",
                "distributed systems cloud computing scalability",
                "cybersecurity cryptography network security protocols",
                "human computer interaction user experience design"
            ]
            
            search_results = []
            
            for query in complex_queries:
                start_time = time.time()
                
                search_response = stress_client.post(
                    "/api/zotero/search",
                    json={
                        "query": query,
                        "library_id": "volume-stress-lib",
                        "limit": 200,
                        "include_facets": True,
                        "sort_by": "relevance",
                        "filters": {
                            "item_types": ["journalArticle", "book"],
                            "date_range": {"start": "2000", "end": "2024"}
                        }
                    }
                )
                
                search_time = time.time() - start_time
                
                search_results.append({
                    'query': query,
                    'success': search_response.status_code == 200,
                    'duration': search_time,
                    'results_count': len(search_response.json().get('items', [])) if search_response.status_code == 200 else 0
                })
                
                # Stress test assertions for each search
                assert search_response.status_code == 200
                assert search_time < 10.0  # Each search should complete within 10 seconds
                
                search_data = search_response.json()
                assert "items" in search_data
                assert "facets" in search_data
                assert "total_count" in search_data
            
            # Analyze overall search performance
            successful_searches = [r for r in search_results if r['success']]
            avg_search_time = sum(r['duration'] for r in successful_searches) / len(successful_searches)
            max_search_time = max(r['duration'] for r in successful_searches)
            total_results = sum(r['results_count'] for r in successful_searches)
            
            assert len(successful_searches) == len(complex_queries)  # All searches should succeed
            assert avg_search_time < 5.0  # Average search time should be reasonable
            assert max_search_time < 10.0  # No search should take more than 10 seconds
            
            print(f"Massive Dataset Search Stress Test Results:")
            print(f"  - Dataset size: {len(massive_dataset['items']):,} items")
            print(f"  - Complex queries tested: {len(complex_queries)}")
            print(f"  - Successful searches: {len(successful_searches)}")
            print(f"  - Average search time: {avg_search_time:.2f}s")
            print(f"  - Max search time: {max_search_time:.2f}s")
            print(f"  - Total results returned: {total_results:,}")
            print(f"  - Average results per query: {total_results / len(successful_searches):.1f}")
            ]
            
            mock_client_instance.get_libraries.return_value = [
                {'id': 'stress-lib', 'type': 'user', 'name': 'Stress Test Library', 'version': 1000}
            ]
            mock_client_instance.get_items.return_value = sync_items
            
            # Create many concurrent sync operations
            num_concurrent_syncs = 50
            connection_ids = [f"stress-conn-{i}" for i in range(num_concurrent_syncs)]
            
            def perform_sync_operation(connection_id):
                """Perform a sync operation with random delays."""
                try:
                    # Add random delay to simulate real-world conditions
                    time.sleep(random.uniform(0.1, 0.5))
                    
                    response = stress_client.post(
                        f"/api/zotero/sync/{connection_id}/libraries",
                        json={"batch_size": random.randint(50, 200)}
                    )
                    
                    return {
                        'connection_id': connection_id,
                        'status_code': response.status_code,
                        'success': response.status_code == 200,
                        'response_time': time.time()
                    }
                except Exception as e:
                    return {
                        'connection_id': connection_id,
                        'status_code': 500,
                        'success': False,
                        'error': str(e),
                        'response_time': time.time()
                    }
            
            # Monitor system resources
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            initial_cpu = process.cpu_percent()
            
            start_time = time.time()
            
            # Execute concurrent operations
            with ThreadPoolExecutor(max_workers=num_concurrent_syncs) as executor:
                futures = [executor.submit(perform_sync_operation, conn_id) for conn_id in connection_ids]
                results = [future.result() for future in as_completed(futures)]
            
            total_time = time.time() - start_time
            
            # Analyze results
            successful_operations = [r for r in results if r['success']]
            failed_operations = [r for r in results if not r['success']]
            
            success_rate = len(successful_operations) / len(results)
            avg_response_time = total_time / len(results)
            
            # Resource usage after operations
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            final_cpu = process.cpu_percent()
            
            # Stress test assertions
            assert success_rate > 0.7  # At least 70% success rate under extreme load
            assert total_time < 300.0  # Should complete within 5 minutes
            assert final_memory - initial_memory < 2000  # Memory increase < 2GB
            
            print(f"Extreme Concurrent Sync Stress Test Results:")
            print(f"  Concurrent operations: {num_concurrent_syncs}")
            print(f"  Success rate: {success_rate:.2%}")
            print(f"  Total time: {total_time:.2f} seconds")
            print(f"  Average response time: {avg_response_time:.3f} seconds")
            print(f"  Memory increase: {final_memory - initial_memory:.1f} MB")
            print(f"  Failed operations: {len(failed_operations)}")
    
    def test_sustained_high_load_operations(self, stress_client):
        """Test system behavior under sustained high load."""
        
        with patch('services.zotero.zotero_search_service.ZoteroSearchService') as mock_search:
            mock_search_instance = AsyncMock()
            mock_search.return_value = mock_search_instance
            
            mock_search_instance.search_items.return_value = {
                'items': [{'key': f'SUST{i:03d}', 'title': f'Sustained Test {i}'} for i in range(50)],
                'total_count': 1000,
                'facets': {}
            }
            
            # Sustained load parameters
            duration_minutes = 2  # Run for 2 minutes
            operations_per_second = 10
            total_operations = duration_minutes * 60 * operations_per_second
            
            operation_results = []
            start_time = time.time()
            end_time = start_time + (duration_minutes * 60)
            
            operation_count = 0
            
            def sustained_operation():
                """Perform a single operation."""
                nonlocal operation_count
                operation_count += 1
                
                op_start = time.time()
                
                try:
                    response = stress_client.post(
                        "/api/zotero/search",
                        json={
                            "query": f"sustained test {operation_count}",
                            "library_id": "sustained-lib",
                            "limit": 20
                        }
                    )
                    
                    op_time = time.time() - op_start
                    
                    return {
                        'operation_id': operation_count,
                        'success': response.status_code == 200,
                        'response_time': op_time,
                        'timestamp': time.time()
                    }
                except Exception as e:
                    op_time = time.time() - op_start
                    return {
                        'operation_id': operation_count,
                        'success': False,
                        'response_time': op_time,
                        'error': str(e),
                        'timestamp': time.time()
                    }
            
            # Execute sustained operations
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = []
                
                while time.time() < end_time:
                    # Submit operations at target rate
                    for _ in range(operations_per_second):
                        if time.time() >= end_time:
                            break
                        futures.append(executor.submit(sustained_operation))
                    
                    # Wait for next second
                    time.sleep(1.0)
                
                # Collect all results
                operation_results = [future.result() for future in as_completed(futures)]
            
            # Analyze sustained load results
            successful_ops = [op for op in operation_results if op['success']]
            failed_ops = [op for op in operation_results if not op['success']]
            
            success_rate = len(successful_ops) / len(operation_results)
            avg_response_time = sum(op['response_time'] for op in successful_ops) / len(successful_ops)
            
            # Calculate operations per second achieved
            actual_duration = max(op['timestamp'] for op in operation_results) - min(op['timestamp'] for op in operation_results)
            actual_ops_per_second = len(operation_results) / actual_duration
            
            # Sustained load assertions
            assert success_rate > 0.8  # At least 80% success rate under sustained load
            assert avg_response_time < 5.0  # Average response time under 5 seconds
            assert actual_ops_per_second > operations_per_second * 0.7  # Achieved at least 70% of target rate
            
            print(f"Sustained High Load Test Results:")
            print(f"  Duration: {actual_duration:.1f} seconds")
            print(f"  Total operations: {len(operation_results)}")
            print(f"  Success rate: {success_rate:.2%}")
            print(f"  Average response time: {avg_response_time:.3f} seconds")
            print(f"  Target ops/sec: {operations_per_second}")
            print(f"  Actual ops/sec: {actual_ops_per_second:.1f}")
            print(f"  Failed operations: {len(failed_ops)}")
    
    def test_memory_pressure_stress(self, stress_client):
        """Test system behavior under memory pressure."""
        
        import gc
        
        with patch('services.zotero.zotero_sync_service.ZoteroSyncService') as mock_sync:
            mock_sync_instance = AsyncMock()
            mock_sync.return_value = mock_sync_instance
            
            # Create memory-intensive mock data
            def create_large_dataset(size):
                return [
                    {
                        'key': f'MEM{i:06d}',
                        'title': 'X' * 500,  # Large title
                        'abstractNote': 'Y' * 2000,  # Large abstract
                        'creators': [
                            {'firstName': f'First{j}', 'lastName': f'Last{j}'}
                            for j in range(10)  # Many creators
                        ],
                        'tags': [{'tag': f'tag{j}'} for j in range(20)],  # Many tags
                        'extra': 'Z' * 1000,  # Large extra field
                        'collections': [f'COLL{j}' for j in range(5)]  # Multiple collections
                    }
                    for i in range(size)
                ]
            
            # Monitor memory usage
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Gradually increase memory pressure
            dataset_sizes = [1000, 2000, 5000, 10000]
            memory_results = []
            
            for size in dataset_sizes:
                gc.collect()  # Force garbage collection
                
                large_dataset = create_large_dataset(size)
                mock_sync_instance.sync_items.return_value = {
                    'success': True,
                    'items_processed': size,
                    'items_added': size,
                    'errors': []
                }
                
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
                
                # Perform sync operation
                sync_response = stress_client.post(
                    f"/api/zotero/sync/memory-stress-{size}/libraries",
                    json={"batch_size": min(500, size // 5)}
                )
                
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = memory_after - memory_before
                
                memory_results.append({
                    'dataset_size': size,
                    'memory_before': memory_before,
                    'memory_after': memory_after,
                    'memory_increase': memory_increase,
                    'success': sync_response.status_code == 200
                })
                
                print(f"Memory Pressure Test (size: {size:,}):")
                print(f"  Memory before: {memory_before:.1f} MB")
                print(f"  Memory after: {memory_after:.1f} MB")
                print(f"  Memory increase: {memory_increase:.1f} MB")
                print(f"  Success: {sync_response.status_code == 200}")
                
                # Clean up large dataset
                del large_dataset
                gc.collect()
                
                # Stop if memory usage becomes excessive
                if memory_after > initial_memory + 3000:  # 3GB increase
                    print(f"  Memory limit reached at dataset size: {size:,}")
                    break
            
            # Verify system recovered after operations
            gc.collect()
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_retained = final_memory - initial_memory
            
            assert memory_retained < 1000  # Should retain less than 1GB after cleanup
            assert all(result['success'] for result in memory_results)  # All operations should succeed
    
    def test_rapid_connection_cycling_stress(self, stress_client):
        """Test rapid connection creation and destruction."""
        
        with patch('services.zotero.zotero_auth_service.ZoteroAuthService') as mock_auth:
            mock_auth_instance = AsyncMock()
            mock_auth.return_value = mock_auth_instance
            
            mock_auth_instance.create_connection.return_value = {
                'connection_id': 'test-conn',
                'success': True
            }
            
            mock_auth_instance.disconnect.return_value = {
                'success': True
            }
            
            # Rapid connection cycling parameters
            num_cycles = 100
            connections_per_cycle = 5
            
            cycle_results = []
            
            for cycle in range(num_cycles):
                cycle_start = time.time()
                connection_ids = []
                
                # Create multiple connections rapidly
                for i in range(connections_per_cycle):
                    try:
                        conn_response = stress_client.post(
                            "/api/zotero/auth/test-connection",
                            json={
                                "user_id": f"cycle-user-{cycle}-{i}",
                                "access_token": f"token-{cycle}-{i}"
                            }
                        )
                        
                        if conn_response.status_code == 200:
                            conn_data = conn_response.json()
                            connection_ids.append(conn_data.get("connection_id", f"conn-{cycle}-{i}"))
                    except Exception as e:
                        print(f"Connection creation failed: {e}")
                
                # Immediately disconnect all connections
                disconnect_successes = 0
                for conn_id in connection_ids:
                    try:
                        disconnect_response = stress_client.delete(
                            f"/api/zotero/auth/disconnect/{conn_id}"
                        )
                        if disconnect_response.status_code == 200:
                            disconnect_successes += 1
                    except Exception as e:
                        print(f"Disconnection failed: {e}")
                
                cycle_time = time.time() - cycle_start
                
                cycle_results.append({
                    'cycle': cycle,
                    'connections_created': len(connection_ids),
                    'connections_disconnected': disconnect_successes,
                    'cycle_time': cycle_time
                })
                
                # Brief pause between cycles
                time.sleep(0.01)
            
            # Analyze connection cycling results
            total_connections_created = sum(r['connections_created'] for r in cycle_results)
            total_connections_disconnected = sum(r['connections_disconnected'] for r in cycle_results)
            avg_cycle_time = sum(r['cycle_time'] for r in cycle_results) / len(cycle_results)
            
            connection_success_rate = total_connections_disconnected / total_connections_created if total_connections_created > 0 else 0
            
            # Connection cycling assertions
            assert connection_success_rate > 0.9  # At least 90% successful connection cycles
            assert avg_cycle_time < 1.0  # Average cycle time under 1 second
            
            print(f"Rapid Connection Cycling Stress Test Results:")
            print(f"  Total cycles: {num_cycles}")
            print(f"  Connections per cycle: {connections_per_cycle}")
            print(f"  Total connections created: {total_connections_created}")
            print(f"  Total connections disconnected: {total_connections_disconnected}")
            print(f"  Success rate: {connection_success_rate:.2%}")
            print(f"  Average cycle time: {avg_cycle_time:.3f} seconds")


@pytest.mark.stress
class TestZoteroDataIntegrityStress:
    """Stress tests for data integrity under load."""
    
    def test_concurrent_write_operations_integrity(self, stress_client):
        """Test data integrity with concurrent write operations."""
        
        with patch('services.zotero.zotero_sync_service.ZoteroSyncService') as mock_sync:
            mock_sync_instance = AsyncMock()
            mock_sync.return_value = mock_sync_instance
            
            # Shared data structure to track operations
            operation_log = []
            operation_lock = threading.Lock()
            
            def mock_sync_with_logging(library_id, items, **kwargs):
                """Mock sync that logs operations for integrity checking."""
                with operation_lock:
                    operation_log.append({
                        'library_id': library_id,
                        'item_count': len(items),
                        'timestamp': time.time(),
                        'thread_id': threading.current_thread().ident
                    })
                
                return {
                    'success': True,
                    'items_processed': len(items),
                    'items_added': len(items),
                    'errors': []
                }
            
            mock_sync_instance.sync_items.side_effect = mock_sync_with_logging
            
            # Create concurrent write operations
            num_writers = 20
            items_per_writer = 100
            
            def concurrent_write_operation(writer_id):
                """Perform concurrent write operations."""
                items = [
                    {
                        'key': f'WRITE{writer_id:02d}{i:03d}',
                        'title': f'Writer {writer_id} Item {i}',
                        'version': i + 1
                    }
                    for i in range(items_per_writer)
                ]
                
                try:
                    response = stress_client.post(
                        f"/api/zotero/sync/integrity-test-{writer_id}/libraries",
                        json={"items": items}
                    )
                    
                    return {
                        'writer_id': writer_id,
                        'success': response.status_code == 200,
                        'items_written': items_per_writer
                    }
                except Exception as e:
                    return {
                        'writer_id': writer_id,
                        'success': False,
                        'error': str(e),
                        'items_written': 0
                    }
            
            # Execute concurrent writes
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=num_writers) as executor:
                futures = [executor.submit(concurrent_write_operation, i) for i in range(num_writers)]
                write_results = [future.result() for future in as_completed(futures)]
            
            total_time = time.time() - start_time
            
            # Analyze data integrity
            successful_writes = [r for r in write_results if r['success']]
            total_items_written = sum(r['items_written'] for r in successful_writes)
            
            # Check operation log integrity
            with operation_lock:
                logged_operations = len(operation_log)
                logged_items = sum(op['item_count'] for op in operation_log)
                unique_threads = len(set(op['thread_id'] for op in operation_log))
            
            # Data integrity assertions
            assert len(successful_writes) == num_writers  # All writes should succeed
            assert total_items_written == num_writers * items_per_writer  # All items should be written
            assert logged_operations == num_writers  # All operations should be logged
            assert logged_items == total_items_written  # Logged items should match written items
            assert unique_threads <= num_writers  # Should not exceed number of writers
            
            print(f"Concurrent Write Operations Integrity Test:")
            print(f"  Concurrent writers: {num_writers}")
            print(f"  Items per writer: {items_per_writer}")
            print(f"  Total items written: {total_items_written}")
            print(f"  Successful writes: {len(successful_writes)}")
            print(f"  Logged operations: {logged_operations}")
            print(f"  Unique threads: {unique_threads}")
            print(f"  Total time: {total_time:.2f} seconds")
    
    def test_race_condition_detection(self, stress_client):
        """Test for race conditions in concurrent operations."""
        
        with patch('services.zotero.zotero_citation_service.ZoteroCitationService') as mock_citation:
            mock_citation_instance = AsyncMock()
            mock_citation.return_value = mock_citation_instance
            
            # Shared counter to detect race conditions
            citation_counter = {'count': 0}
            counter_lock = threading.Lock()
            race_conditions = []
            
            def mock_generate_with_race_detection(item_keys, style, format_type):
                """Mock citation generation that can detect race conditions."""
                # Simulate race condition scenario
                current_count = citation_counter['count']
                time.sleep(0.001)  # Small delay to increase race condition probability
                
                with counter_lock:
                    citation_counter['count'] += 1
                    new_count = citation_counter['count']
                
                # Check for race condition
                if new_count != current_count + 1:
                    race_conditions.append({
                        'expected': current_count + 1,
                        'actual': new_count,
                        'thread_id': threading.current_thread().ident,
                        'timestamp': time.time()
                    })
                
                return [
                    {
                        'item_key': key,
                        'citation': f'{style} citation {new_count} for {key}',
                        'style': style
                    }
                    for key in item_keys
                ]
            
            mock_citation_instance.generate_citations.side_effect = mock_generate_with_race_detection
            
            # Create concurrent citation operations
            num_concurrent_operations = 50
            
            def concurrent_citation_operation(operation_id):
                """Perform concurrent citation generation."""
                item_keys = [f'RACE{operation_id:02d}{i:02d}' for i in range(5)]
                
                try:
                    response = stress_client.post(
                        "/api/zotero/citations/generate",
                        json={
                            "item_keys": item_keys,
                            "style": "apa",
                            "format": "text"
                        }
                    )
                    
                    return {
                        'operation_id': operation_id,
                        'success': response.status_code == 200,
                        'thread_id': threading.current_thread().ident
                    }
                except Exception as e:
                    return {
                        'operation_id': operation_id,
                        'success': False,
                        'error': str(e),
                        'thread_id': threading.current_thread().ident
                    }
            
            # Execute concurrent operations
            with ThreadPoolExecutor(max_workers=num_concurrent_operations) as executor:
                futures = [executor.submit(concurrent_citation_operation, i) for i in range(num_concurrent_operations)]
                operation_results = [future.result() for future in as_completed(futures)]
            
            # Analyze race condition results
            successful_operations = [r for r in operation_results if r['success']]
            unique_threads = len(set(r['thread_id'] for r in operation_results))
            
            # Race condition assertions
            assert len(race_conditions) == 0  # No race conditions should be detected
            assert len(successful_operations) == num_concurrent_operations  # All operations should succeed
            assert citation_counter['count'] == num_concurrent_operations  # Counter should be accurate
            
            print(f"Race Condition Detection Test:")
            print(f"  Concurrent operations: {num_concurrent_operations}")
            print(f"  Successful operations: {len(successful_operations)}")
            print(f"  Race conditions detected: {len(race_conditions)}")
            print(f"  Final counter value: {citation_counter['count']}")
            print(f"  Unique threads: {unique_threads}")
    
    def test_deadlock_detection_stress(self, stress_client):
        """Test for deadlocks in concurrent operations."""
        
        with patch('services.zotero.zotero_sync_service.ZoteroSyncService') as mock_sync, \
             patch('services.zotero.zotero_search_service.ZoteroSearchService') as mock_search:
            
            # Create mock services that could potentially deadlock
            mock_sync_instance = AsyncMock()
            mock_sync.return_value = mock_sync_instance
            
            mock_search_instance = AsyncMock()
            mock_search.return_value = mock_search_instance
            
            # Simulate operations that might cause deadlocks
            operation_locks = {
                'sync_lock': threading.Lock(),
                'search_lock': threading.Lock()
            }
            
            def mock_sync_with_locks(library_id, **kwargs):
                """Mock sync that uses locks in specific order."""
                with operation_locks['sync_lock']:
                    time.sleep(0.01)  # Hold lock briefly
                    with operation_locks['search_lock']:
                        time.sleep(0.01)
                        return {'success': True, 'items_processed': 100}
            
            def mock_search_with_locks(query, **kwargs):
                """Mock search that uses locks in reverse order."""
                with operation_locks['search_lock']:
                    time.sleep(0.01)  # Hold lock briefly
                    with operation_locks['sync_lock']:
                        time.sleep(0.01)
                        return {'items': [], 'total_count': 0}
            
            mock_sync_instance.sync_items.side_effect = mock_sync_with_locks
            mock_search_instance.search_items.side_effect = mock_search_with_locks
            
            # Create operations that could deadlock
            num_sync_operations = 25
            num_search_operations = 25
            
            def sync_operation(operation_id):
                """Perform sync operation."""
                try:
                    response = stress_client.post(
                        f"/api/zotero/sync/deadlock-test-{operation_id}/libraries"
                    )
                    return {'type': 'sync', 'id': operation_id, 'success': response.status_code == 200}
                except Exception as e:
                    return {'type': 'sync', 'id': operation_id, 'success': False, 'error': str(e)}
            
            def search_operation(operation_id):
                """Perform search operation."""
                try:
                    response = stress_client.post(
                        "/api/zotero/search",
                        json={"query": f"deadlock test {operation_id}", "library_id": "deadlock-lib"}
                    )
                    return {'type': 'search', 'id': operation_id, 'success': response.status_code == 200}
                except Exception as e:
                    return {'type': 'search', 'id': operation_id, 'success': False, 'error': str(e)}
            
            # Execute mixed operations concurrently
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = []
                
                # Submit sync operations
                for i in range(num_sync_operations):
                    futures.append(executor.submit(sync_operation, i))
                
                # Submit search operations
                for i in range(num_search_operations):
                    futures.append(executor.submit(search_operation, i))
                
                # Collect results with timeout to detect deadlocks
                results = []
                for future in as_completed(futures, timeout=30):  # 30 second timeout
                    results.append(future.result())
            
            total_time = time.time() - start_time
            
            # Analyze deadlock test results
            sync_results = [r for r in results if r['type'] == 'sync']
            search_results = [r for r in results if r['type'] == 'search']
            
            successful_syncs = [r for r in sync_results if r['success']]
            successful_searches = [r for r in search_results if r['success']]
            
            # Deadlock detection assertions
            assert len(results) == num_sync_operations + num_search_operations  # All operations completed
            assert total_time < 30.0  # No deadlock timeout occurred
            assert len(successful_syncs) > 0  # Some sync operations succeeded
            assert len(successful_searches) > 0  # Some search operations succeeded
            
            print(f"Deadlock Detection Stress Test:")
            print(f"  Total operations: {len(results)}")
            print(f"  Sync operations: {len(sync_results)} (successful: {len(successful_syncs)})")
            print(f"  Search operations: {len(search_results)} (successful: {len(successful_searches)})")
            print(f"  Total time: {total_time:.2f} seconds")
            print(f"  No deadlocks detected: {total_time < 30.0}")


@pytest.mark.stress
class TestZoteroResourceExhaustionStress:
    """Stress tests for resource exhaustion scenarios."""
    
    def test_database_connection_exhaustion(self, stress_client):
        """Test behavior when database connections are exhausted."""
        
        with patch('services.zotero.zotero_search_service.ZoteroSearchService') as mock_search:
            mock_search_instance = AsyncMock()
            mock_search.return_value = mock_search_instance
            
            mock_search_instance.search_items.return_value = {
                'items': [{'key': 'DB123', 'title': 'DB Test'}],
                'total_count': 1
            }
            
            # Create many concurrent database operations
            num_db_operations = 200  # Exceed typical connection pool size
            
            def database_intensive_operation(operation_id):
                """Perform database-intensive operation."""
                try:
                    # Multiple operations that would use database connections
                    responses = []
                    
                    for i in range(5):  # 5 operations per thread
                        response = stress_client.post(
                            "/api/zotero/search",
                            json={
                                "query": f"db test {operation_id} {i}",
                                "library_id": f"db-lib-{operation_id}"
                            }
                        )
                        responses.append(response.status_code)
                        time.sleep(0.01)  # Brief delay between operations
                    
                    return {
                        'operation_id': operation_id,
                        'responses': responses,
                        'success': all(code == 200 for code in responses)
                    }
                except Exception as e:
                    return {
                        'operation_id': operation_id,
                        'success': False,
                        'error': str(e)
                    }
            
            # Execute database-intensive operations
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=num_db_operations) as executor:
                futures = [executor.submit(database_intensive_operation, i) for i in range(num_db_operations)]
                db_results = [future.result() for future in as_completed(futures)]
            
            total_time = time.time() - start_time
            
            # Analyze database exhaustion results
            successful_operations = [r for r in db_results if r['success']]
            failed_operations = [r for r in db_results if not r['success']]
            
            success_rate = len(successful_operations) / len(db_results)
            
            # Database exhaustion assertions
            assert success_rate > 0.5  # At least 50% should succeed even under exhaustion
            assert total_time < 120.0  # Should complete within 2 minutes
            
            print(f"Database Connection Exhaustion Test:")
            print(f"  Total operations: {num_db_operations}")
            print(f"  Successful operations: {len(successful_operations)}")
            print(f"  Failed operations: {len(failed_operations)}")
            print(f"  Success rate: {success_rate:.2%}")
            print(f"  Total time: {total_time:.2f} seconds")
    
    def test_file_descriptor_exhaustion(self, stress_client):
        """Test behavior when file descriptors are exhausted."""
        
        with patch('services.zotero.zotero_attachment_service.ZoteroAttachmentService') as mock_attachment:
            mock_attachment_instance = AsyncMock()
            mock_attachment.return_value = mock_attachment_instance
            
            mock_attachment_instance.download_attachment.return_value = {
                'success': True,
                'file_path': '/tmp/test_attachment.pdf',
                'file_size': 1024
            }
            
            # Create many concurrent file operations
            num_file_operations = 500
            
            def file_intensive_operation(operation_id):
                """Perform file-intensive operation."""
                try:
                    response = stress_client.post(
                        f"/api/zotero/attachments/download",
                        json={
                            "item_key": f"FILE{operation_id:04d}",
                            "attachment_key": f"ATT{operation_id:04d}"
                        }
                    )
                    
                    return {
                        'operation_id': operation_id,
                        'success': response.status_code == 200
                    }
                except Exception as e:
                    return {
                        'operation_id': operation_id,
                        'success': False,
                        'error': str(e)
                    }
            
            # Execute file operations
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=100) as executor:
                futures = [executor.submit(file_intensive_operation, i) for i in range(num_file_operations)]
                file_results = [future.result() for future in as_completed(futures)]
            
            total_time = time.time() - start_time
            
            # Analyze file descriptor results
            successful_operations = [r for r in file_results if r['success']]
            failed_operations = [r for r in file_results if not r['success']]
            
            success_rate = len(successful_operations) / len(file_results)
            
            # File descriptor exhaustion assertions
            assert success_rate > 0.6  # At least 60% should succeed
            assert total_time < 180.0  # Should complete within 3 minutes
            
            print(f"File Descriptor Exhaustion Test:")
            print(f"  Total file operations: {num_file_operations}")
            print(f"  Successful operations: {len(successful_operations)}")
            print(f"  Failed operations: {len(failed_operations)}")
            print(f"  Success rate: {success_rate:.2%}")
            print(f"  Total time: {total_time:.2f} seconds")