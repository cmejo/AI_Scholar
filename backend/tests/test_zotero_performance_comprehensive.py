"""
Comprehensive performance tests for Zotero integration.
Tests performance characteristics under various load conditions.
"""
import pytest
import asyncio
import time
import psutil
import os
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient

from app import app


@pytest.mark.performance
class TestZoteroSyncPerformance:
    """Performance tests for Zotero sync operations."""
    
    @pytest.fixture
    def performance_client(self, test_db_session, mock_redis):
        """Create test client optimized for performance testing."""
        app.dependency_overrides.clear()
        
        from core.database import get_db
        from core.redis_client import get_redis_client
        
        app.dependency_overrides[get_db] = lambda: test_db_session
        app.dependency_overrides[get_redis_client] = lambda: mock_redis
        
        with TestClient(app) as client:
            yield client
        
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def large_library_data(self):
        """Generate large library dataset for performance testing."""
        items = []
        collections = []
        
        # Generate collections
        for i in range(50):
            collections.append({
                'key': f'COLL{i:03d}',
                'name': f'Collection {i}',
                'parentCollection': f'COLL{i//10:03d}' if i >= 10 else None,
                'version': i + 1
            })
        
        # Generate items
        for i in range(10000):  # 10,000 items
            items.append({
                'key': f'ITEM{i:05d}',
                'version': i + 1,
                'itemType': 'journalArticle' if i % 3 == 0 else 'book' if i % 3 == 1 else 'thesis',
                'title': f'Performance Test Item {i}: {"A" * (50 + i % 100)}',  # Variable length titles
                'creators': [
                    {
                        'creatorType': 'author',
                        'firstName': f'FirstName{i % 1000}',
                        'lastName': f'LastName{i % 500}'
                    }
                    for _ in range(1 + i % 3)  # Variable number of authors
                ],
                'publicationTitle': f'Journal {i % 100}',
                'date': str(2000 + (i % 24)),
                'abstractNote': f'Abstract for item {i}: {"B" * (200 + i % 300)}',  # Variable length abstracts
                'tags': [
                    {'tag': f'tag{i % 200}'},
                    {'tag': f'category{i % 50}'},
                    {'tag': f'subject{i % 100}'}
                ],
                'collections': [f'COLL{i % 50:03d}'],
                'extra': f'Extra data for performance testing: {"C" * (i % 100)}'
            })
        
        return {
            'items': items,
            'collections': collections,
            'libraries': [
                {
                    'id': 'perf-lib-123',
                    'type': 'user',
                    'name': 'Performance Test Library',
                    'version': 10000
                }
            ]
        }
    
    def test_large_library_sync_performance(self, performance_client, large_library_data):
        """Test sync performance with large library (10,000 items)."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Mock API responses with large dataset
            mock_client_instance.get_libraries.return_value = large_library_data['libraries']
            mock_client_instance.get_collections.return_value = large_library_data['collections']
            mock_client_instance.get_items.return_value = large_library_data['items']
            
            user_id = "perf-test-user"
            connection_id = "perf-test-conn"
            
            # Setup connection
            connection_response = performance_client.post(
                "/api/zotero/auth/test-connection",
                json={"user_id": user_id, "access_token": "perf-test-token"}
            )
            
            # Measure memory before sync
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Measure sync performance
            start_time = time.time()
            
            sync_response = performance_client.post(
                f"/api/zotero/sync/{connection_id}/libraries",
                json={
                    "batch_size": 500,  # Process in larger batches for performance
                    "parallel_processing": True
                }
            )
            
            sync_duration = time.time() - start_time
            
            # Measure memory after sync
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = memory_after - memory_before
            
            # Performance assertions
            assert sync_response.status_code == 200
            assert sync_duration < 120.0  # Should complete within 2 minutes
            assert memory_increase < 1000  # Memory increase should be reasonable (< 1GB)
            
            sync_data = sync_response.json()
            assert sync_data["success"] is True
            
            # Verify processing rate
            items_per_second = len(large_library_data['items']) / sync_duration
            assert items_per_second > 50  # Should process at least 50 items per second
            
            print(f"Sync Performance Metrics:")
            print(f"  - Duration: {sync_duration:.2f} seconds")
            print(f"  - Items processed: {len(large_library_data['items'])}")
            print(f"  - Items per second: {items_per_second:.2f}")
            print(f"  - Memory increase: {memory_increase:.2f} MB")
            
            # Setup mock responses
            mock_client_instance.get_libraries.return_value = large_library_data['libraries']
            mock_client_instance.get_collections.return_value = large_library_data['collections']
            
            # Mock paginated item retrieval
            items_per_page = 100
            total_items = len(large_library_data['items'])
            
            def mock_get_items(library_id, start=0, limit=100, **kwargs):
                end = min(start + limit, total_items)
                return large_library_data['items'][start:end]
            
            mock_client_instance.get_items.side_effect = mock_get_items
            
            connection_id = "perf-test-conn"
            
            # Measure sync performance
            start_time = time.time()
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            sync_response = performance_client.post(
                f"/api/zotero/sync/{connection_id}/libraries",
                json={
                    "batch_size": items_per_page,
                    "parallel_processing": True,
                    "max_workers": 4
                }
            )
            
            sync_time = time.time() - start_time
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = final_memory - initial_memory
            
            # Performance assertions
            assert sync_response.status_code == 200
            assert sync_time < 120.0  # Should complete within 2 minutes
            assert memory_used < 1000  # Should use less than 1GB additional memory
            
            sync_data = sync_response.json()
            assert sync_data["success"] is True
            assert sync_data.get("items_processed", 0) == total_items
            
            # Calculate performance metrics
            items_per_second = total_items / sync_time
            assert items_per_second > 50  # Should process at least 50 items per second
            
            print(f"Sync Performance Metrics:")
            print(f"  Total time: {sync_time:.2f} seconds")
            print(f"  Items per second: {items_per_second:.2f}")
            print(f"  Memory used: {memory_used:.2f} MB")
    
    def test_incremental_sync_performance(self, performance_client, large_library_data):
        """Test incremental sync performance with updates."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Simulate incremental updates (10% of items changed)
            updated_items = large_library_data['items'][:1000]  # First 1000 items updated
            for i, item in enumerate(updated_items):
                item['version'] = item['version'] + 1000  # Increment version
                item['title'] = f"UPDATED: {item['title']}"
            
            mock_client_instance.get_updated_items.return_value = updated_items
            
            connection_id = "incremental-perf-conn"
            
            # Measure incremental sync performance
            start_time = time.time()
            
            incremental_response = performance_client.post(
                f"/api/zotero/sync/{connection_id}/incremental",
                json={"since_version": 10000}
            )
            
            incremental_time = time.time() - start_time
            
            # Performance assertions
            assert incremental_response.status_code == 200
            assert incremental_time < 30.0  # Should complete within 30 seconds
            
            incremental_data = incremental_response.json()
            assert incremental_data["success"] is True
            assert incremental_data.get("items_updated", 0) == 1000
            
            # Calculate incremental sync performance
            updates_per_second = 1000 / incremental_time
            assert updates_per_second > 20  # Should process at least 20 updates per second
            
            print(f"Incremental Sync Performance:")
            print(f"  Update time: {incremental_time:.2f} seconds")
            print(f"  Updates per second: {updates_per_second:.2f}")
    
    def test_concurrent_sync_performance(self, performance_client):
        """Test performance with multiple concurrent sync operations."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Mock smaller datasets for concurrent testing
            small_dataset = []
            for i in range(500):  # 500 items per user
                small_dataset.append({
                    'key': f'CONC{i:04d}',
                    'title': f'Concurrent Test Item {i}',
                    'version': i + 1
                })
            
            mock_client_instance.get_libraries.return_value = [
                {'id': 'concurrent-lib', 'type': 'user', 'name': 'Concurrent Test', 'version': 500}
            ]
            mock_client_instance.get_items.return_value = small_dataset
            
            # Test with multiple concurrent users
            num_concurrent_users = 10
            connection_ids = [f"concurrent-conn-{i}" for i in range(num_concurrent_users)]
            
            def sync_user_library(connection_id):
                return performance_client.post(
                    f"/api/zotero/sync/{connection_id}/libraries",
                    json={"batch_size": 50}
                )
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=num_concurrent_users) as executor:
                futures = [executor.submit(sync_user_library, conn_id) for conn_id in connection_ids]
                results = [future.result() for future in as_completed(futures)]
            
            concurrent_time = time.time() - start_time
            
            # Performance assertions
            assert all(result.status_code == 200 for result in results)
            assert concurrent_time < 60.0  # Should complete within 1 minute
            
            # Calculate concurrent performance
            total_items = num_concurrent_users * 500
            concurrent_throughput = total_items / concurrent_time
            assert concurrent_throughput > 100  # Should process at least 100 items per second total
            
            print(f"Concurrent Sync Performance:")
            print(f"  Total time: {concurrent_time:.2f} seconds")
            print(f"  Concurrent throughput: {concurrent_throughput:.2f} items/second")
            print(f"  Users processed: {num_concurrent_users}")


@pytest.mark.performance
class TestZoteroSearchPerformance:
    """Performance tests for Zotero search operations."""
    
    def test_search_performance_large_dataset(self, performance_client):
        """Test search performance with large dataset."""
        
        with patch('services.zotero.zotero_search_service.ZoteroSearchService') as mock_search:
            mock_search_instance = AsyncMock()
            mock_search.return_value = mock_search_instance
            
            # Mock large search results
            large_results = []
            for i in range(1000):
                large_results.append({
                    'key': f'SEARCH{i:04d}',
                    'title': f'Search Result {i}',
                    'relevance_score': 1.0 - (i * 0.001),
                    'snippet': f'Relevant content snippet for item {i}'
                })
            
            mock_search_instance.search_items.return_value = {
                'items': large_results,
                'total_count': 10000,
                'facets': {
                    'authors': [{'name': f'Author{i}', 'count': 100 - i} for i in range(50)],
                    'years': [{'year': str(2020 + i), 'count': 200 - i*10} for i in range(4)],
                    'tags': [{'tag': f'tag{i}', 'count': 150 - i*3} for i in range(30)]
                },
                'query_time': 0.5
            }
            
            search_queries = [
                "machine learning artificial intelligence",
                "neural networks deep learning",
                "natural language processing",
                "computer vision image recognition",
                "data mining knowledge discovery"
            ]
            
            total_search_time = 0
            
            for query in search_queries:
                start_time = time.time()
                
                search_response = performance_client.post(
                    "/api/zotero/search",
                    json={
                        "query": query,
                        "library_id": "search-perf-lib",
                        "limit": 100,
                        "include_facets": True,
                        "include_snippets": True
                    }
                )
                
                search_time = time.time() - start_time
                total_search_time += search_time
                
                # Performance assertions
                assert search_response.status_code == 200
                assert search_time < 2.0  # Each search should complete within 2 seconds
                
                search_data = search_response.json()
                assert len(search_data["items"]) <= 100
                assert "facets" in search_data
                assert "total_count" in search_data
            
            avg_search_time = total_search_time / len(search_queries)
            assert avg_search_time < 1.0  # Average search time should be under 1 second
            
            print(f"Search Performance Metrics:")
            print(f"  Average search time: {avg_search_time:.3f} seconds")
            print(f"  Total queries: {len(search_queries)}")
    
    def test_faceted_search_performance(self, performance_client):
        """Test performance of faceted search with complex filters."""
        
        with patch('services.zotero.zotero_search_service.ZoteroSearchService') as mock_search:
            mock_search_instance = AsyncMock()
            mock_search.return_value = mock_search_instance
            
            # Mock complex faceted search results
            mock_search_instance.faceted_search.return_value = {
                'items': [{'key': f'FAC{i:04d}', 'title': f'Faceted Result {i}'} for i in range(50)],
                'total_count': 500,
                'facets': {
                    'authors': [{'name': f'Author{i}', 'count': 25 - i} for i in range(20)],
                    'years': [{'year': str(2015 + i), 'count': 30 - i*2} for i in range(9)],
                    'item_types': [{'type': 'article', 'count': 200}, {'type': 'book', 'count': 150}],
                    'tags': [{'tag': f'tag{i}', 'count': 40 - i} for i in range(25)],
                    'collections': [{'name': f'Collection{i}', 'count': 35 - i*2} for i in range(15)]
                },
                'applied_filters': {
                    'authors': ['Author1', 'Author2'],
                    'years': ['2020', '2021', '2022'],
                    'tags': ['machine learning', 'AI']
                }
            }
            
            complex_filters = {
                "query": "artificial intelligence",
                "filters": {
                    "authors": ["Author1", "Author2", "Author3"],
                    "years": ["2020", "2021", "2022"],
                    "item_types": ["journalArticle", "book"],
                    "tags": ["machine learning", "AI", "neural networks"],
                    "collections": ["Research Papers", "AI Studies"]
                },
                "sort": "relevance",
                "limit": 50
            }
            
            start_time = time.time()
            
            faceted_response = performance_client.post(
                "/api/zotero/search/faceted",
                json=complex_filters
            )
            
            faceted_time = time.time() - start_time
            
            # Performance assertions
            assert faceted_response.status_code == 200
            assert faceted_time < 3.0  # Complex faceted search should complete within 3 seconds
            
            faceted_data = faceted_response.json()
            assert "items" in faceted_data
            assert "facets" in faceted_data
            assert "applied_filters" in faceted_data
            
            print(f"Faceted Search Performance:")
            print(f"  Complex search time: {faceted_time:.3f} seconds")
    
    def test_concurrent_search_performance(self, performance_client):
        """Test search performance with concurrent queries."""
        
        with patch('services.zotero.zotero_search_service.ZoteroSearchService') as mock_search:
            mock_search_instance = AsyncMock()
            mock_search.return_value = mock_search_instance
            
            mock_search_instance.search_items.return_value = {
                'items': [{'key': f'CONC{i:03d}', 'title': f'Concurrent Result {i}'} for i in range(20)],
                'total_count': 100,
                'facets': {},
                'query_time': 0.1
            }
            
            search_queries = [
                f"query {i} machine learning" for i in range(20)
            ]
            
            def execute_search(query):
                return performance_client.post(
                    "/api/zotero/search",
                    json={
                        "query": query,
                        "library_id": "concurrent-search-lib",
                        "limit": 20
                    }
                )
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(execute_search, query) for query in search_queries]
                results = [future.result() for future in as_completed(futures)]
            
            concurrent_search_time = time.time() - start_time
            
            # Performance assertions
            assert all(result.status_code == 200 for result in results)
            assert concurrent_search_time < 10.0  # All searches should complete within 10 seconds
            
            queries_per_second = len(search_queries) / concurrent_search_time
            assert queries_per_second > 2  # Should handle at least 2 queries per second
            
            print(f"Concurrent Search Performance:")
            print(f"  Total time: {concurrent_search_time:.2f} seconds")
            print(f"  Queries per second: {queries_per_second:.2f}")


@pytest.mark.performance
class TestZoteroCitationPerformance:
    """Performance tests for Zotero citation generation."""
    
    def test_bulk_citation_generation_performance(self, performance_client):
        """Test performance of bulk citation generation."""
        
        with patch('services.zotero.zotero_citation_service.ZoteroCitationService') as mock_citation:
            mock_citation_instance = AsyncMock()
            mock_citation.return_value = mock_citation_instance
            
            # Mock bulk citation generation
            def generate_bulk_citations(item_keys, style, format_type):
                return [
                    {
                        'item_key': key,
                        'citation': f'{style.upper()} citation for {key}',
                        'style': style,
                        'format': format_type
                    }
                    for key in item_keys
                ]
            
            mock_citation_instance.generate_citations.side_effect = generate_bulk_citations
            
            # Test different batch sizes
            batch_sizes = [10, 50, 100, 500, 1000]
            citation_styles = ['apa', 'mla', 'chicago', 'ieee']
            
            performance_results = {}
            
            for batch_size in batch_sizes:
                item_keys = [f'CITE{i:05d}' for i in range(batch_size)]
                
                for style in citation_styles:
                    start_time = time.time()
                    
                    citation_response = performance_client.post(
                        "/api/zotero/citations/generate",
                        json={
                            "item_keys": item_keys,
                            "style": style,
                            "format": "text"
                        }
                    )
                    
                    citation_time = time.time() - start_time
                    
                    # Performance assertions
                    assert citation_response.status_code == 200
                    
                    citation_data = citation_response.json()
                    assert len(citation_data["citations"]) == batch_size
                    
                    # Store performance data
                    key = f"{batch_size}_{style}"
                    performance_results[key] = {
                        'batch_size': batch_size,
                        'style': style,
                        'time': citation_time,
                        'citations_per_second': batch_size / citation_time
                    }
                    
                    # Performance thresholds
                    if batch_size <= 100:
                        assert citation_time < 5.0  # Small batches should complete quickly
                    elif batch_size <= 500:
                        assert citation_time < 15.0  # Medium batches
                    else:
                        assert citation_time < 30.0  # Large batches
            
            # Print performance summary
            print("Citation Generation Performance:")
            for key, result in performance_results.items():
                print(f"  {result['batch_size']} items ({result['style']}): "
                      f"{result['time']:.2f}s, {result['citations_per_second']:.1f} citations/sec")
    
    def test_bibliography_generation_performance(self, performance_client):
        """Test performance of bibliography generation."""
        
        with patch('services.zotero.zotero_citation_service.ZoteroCitationService') as mock_citation:
            mock_citation_instance = AsyncMock()
            mock_citation.return_value = mock_citation_instance
            
            # Mock bibliography generation
            def generate_bibliography(item_keys, style, format_type):
                bibliography_entries = []
                for i, key in enumerate(item_keys):
                    bibliography_entries.append(f"[{i+1}] {style.upper()} bibliography entry for {key}")
                
                return {
                    'bibliography': '\n'.join(bibliography_entries),
                    'format': format_type,
                    'style': style,
                    'entry_count': len(item_keys)
                }
            
            mock_citation_instance.generate_bibliography.side_effect = generate_bibliography
            
            # Test bibliography with different sizes
            bibliography_sizes = [25, 100, 250, 500]
            
            for size in bibliography_sizes:
                item_keys = [f'BIB{i:04d}' for i in range(size)]
                
                start_time = time.time()
                
                bibliography_response = performance_client.post(
                    "/api/zotero/citations/bibliography",
                    json={
                        "item_keys": item_keys,
                        "style": "apa",
                        "format": "html"
                    }
                )
                
                bibliography_time = time.time() - start_time
                
                # Performance assertions
                assert bibliography_response.status_code == 200
                assert bibliography_time < 20.0  # Should complete within 20 seconds
                
                bibliography_data = bibliography_response.json()
                assert "bibliography" in bibliography_data
                assert bibliography_data["entry_count"] == size
                
                entries_per_second = size / bibliography_time
                assert entries_per_second > 10  # Should process at least 10 entries per second
                
                print(f"Bibliography Performance ({size} entries): "
                      f"{bibliography_time:.2f}s, {entries_per_second:.1f} entries/sec")


@pytest.mark.performance
class TestZoteroMemoryPerformance:
    """Memory performance tests for Zotero operations."""
    
    def test_memory_usage_during_large_sync(self, performance_client):
        """Test memory usage patterns during large sync operations."""
        
        import gc
        
        with patch('services.zotero.zotero_sync_service.ZoteroSyncService') as mock_sync:
            mock_sync_instance = AsyncMock()
            mock_sync.return_value = mock_sync_instance
            
            # Create memory-intensive mock data
            large_items = []
            for i in range(5000):
                large_items.append({
                    'key': f'MEM{i:05d}',
                    'title': 'A' * 200,  # Large title
                    'abstractNote': 'B' * 1000,  # Large abstract
                    'creators': [
                        {'firstName': f'First{j}', 'lastName': f'Last{j}'}
                        for j in range(5)  # Multiple creators
                    ],
                    'tags': [{'tag': f'tag{j}'} for j in range(10)],  # Multiple tags
                    'extra': 'C' * 500  # Large extra field
                })
            
            mock_sync_instance.sync_items.return_value = {
                'success': True,
                'items_processed': len(large_items),
                'items_added': len(large_items),
                'errors': []
            }
            
            # Monitor memory usage
            process = psutil.Process(os.getpid())
            
            # Force garbage collection before test
            gc.collect()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Perform sync
            sync_response = performance_client.post(
                "/api/zotero/sync/memory-test-conn/libraries",
                json={"batch_size": 500}
            )
            
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Force garbage collection after test
            gc.collect()
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Memory performance assertions
            assert sync_response.status_code == 200
            
            memory_increase = peak_memory - initial_memory
            memory_retained = final_memory - initial_memory
            
            # Should not use excessive memory
            assert memory_increase < 2000  # Less than 2GB peak increase
            assert memory_retained < 500   # Less than 500MB retained after GC
            
            print(f"Memory Usage During Large Sync:")
            print(f"  Initial memory: {initial_memory:.1f} MB")
            print(f"  Peak memory: {peak_memory:.1f} MB")
            print(f"  Final memory: {final_memory:.1f} MB")
            print(f"  Memory increase: {memory_increase:.1f} MB")
            print(f"  Memory retained: {memory_retained:.1f} MB")
    
    def test_memory_leak_detection(self, performance_client):
        """Test for memory leaks during repeated operations."""
        
        import gc
        
        with patch('services.zotero.zotero_search_service.ZoteroSearchService') as mock_search:
            mock_search_instance = AsyncMock()
            mock_search.return_value = mock_search_instance
            
            mock_search_instance.search_items.return_value = {
                'items': [{'key': f'LEAK{i:03d}', 'title': f'Leak Test {i}'} for i in range(100)],
                'total_count': 100,
                'facets': {}
            }
            
            process = psutil.Process(os.getpid())
            memory_measurements = []
            
            # Perform repeated operations
            for iteration in range(20):
                # Force garbage collection
                gc.collect()
                
                # Measure memory before operation
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
                
                # Perform search operation
                search_response = performance_client.post(
                    "/api/zotero/search",
                    json={
                        "query": f"leak test {iteration}",
                        "library_id": "leak-test-lib",
                        "limit": 100
                    }
                )
                
                assert search_response.status_code == 200
                
                # Measure memory after operation
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                
                memory_measurements.append({
                    'iteration': iteration,
                    'memory_before': memory_before,
                    'memory_after': memory_after,
                    'memory_diff': memory_after - memory_before
                })
            
            # Analyze memory usage trend
            initial_memory = memory_measurements[0]['memory_before']
            final_memory = memory_measurements[-1]['memory_after']
            total_increase = final_memory - initial_memory
            
            # Calculate average memory increase per operation
            avg_increase = sum(m['memory_diff'] for m in memory_measurements) / len(memory_measurements)
            
            # Memory leak detection
            assert total_increase < 100  # Total increase should be less than 100MB
            assert avg_increase < 5     # Average increase per operation should be less than 5MB
            
            print(f"Memory Leak Detection Results:")
            print(f"  Initial memory: {initial_memory:.1f} MB")
            print(f"  Final memory: {final_memory:.1f} MB")
            print(f"  Total increase: {total_increase:.1f} MB")
            print(f"  Average increase per operation: {avg_increase:.2f} MB")
            print(f"  Operations performed: {len(memory_measurements)}")


@pytest.mark.performance
class TestZoteroScalabilityLimits:
    """Tests to determine scalability limits of Zotero integration."""
    
    def test_maximum_concurrent_users(self, performance_client):
        """Test maximum number of concurrent users the system can handle."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            mock_client_instance.get_items.return_value = [
                {'key': 'SCALE123', 'title': 'Scalability Test Item'}
            ]
            
            # Test increasing numbers of concurrent users
            user_counts = [10, 25, 50, 100]
            results = {}
            
            for user_count in user_counts:
                user_ids = [f"scale-user-{i}" for i in range(user_count)]
                
                def user_operation(user_id):
                    try:
                        response = performance_client.post(
                            "/api/zotero/search",
                            json={
                                "query": "scalability test",
                                "library_id": f"{user_id}-lib",
                                "limit": 10
                            }
                        )
                        return response.status_code == 200
                    except Exception:
                        return False
                
                start_time = time.time()
                
                with ThreadPoolExecutor(max_workers=user_count) as executor:
                    futures = [executor.submit(user_operation, user_id) for user_id in user_ids]
                    success_results = [future.result() for future in as_completed(futures)]
                
                operation_time = time.time() - start_time
                success_rate = sum(success_results) / len(success_results)
                
                results[user_count] = {
                    'success_rate': success_rate,
                    'operation_time': operation_time,
                    'users_per_second': user_count / operation_time
                }
                
                print(f"Concurrent Users Test ({user_count} users):")
                print(f"  Success rate: {success_rate:.2%}")
                print(f"  Operation time: {operation_time:.2f}s")
                print(f"  Users per second: {results[user_count]['users_per_second']:.1f}")
                
                # Stop testing if success rate drops below 80%
                if success_rate < 0.8:
                    print(f"  Maximum concurrent users: {user_count}")
                    break
    
    def test_maximum_library_size(self, performance_client):
        """Test maximum library size that can be handled efficiently."""
        
        with patch('services.zotero.zotero_sync_service.ZoteroSyncService') as mock_sync:
            mock_sync_instance = AsyncMock()
            mock_sync.return_value = mock_sync_instance
            
            # Test increasing library sizes
            library_sizes = [1000, 5000, 10000, 25000, 50000]
            
            for size in library_sizes:
                # Mock sync response for different sizes
                mock_sync_instance.sync_items.return_value = {
                    'success': True,
                    'items_processed': size,
                    'items_added': size,
                    'errors': []
                }
                
                start_time = time.time()
                process = psutil.Process(os.getpid())
                initial_memory = process.memory_info().rss / 1024 / 1024  # MB
                
                sync_response = performance_client.post(
                    f"/api/zotero/sync/size-test-{size}/libraries",
                    json={"batch_size": min(1000, size // 10)}
                )
                
                sync_time = time.time() - start_time
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_used = final_memory - initial_memory
                
                success = sync_response.status_code == 200
                items_per_second = size / sync_time if sync_time > 0 else 0
                
                print(f"Library Size Test ({size:,} items):")
                print(f"  Success: {success}")
                print(f"  Sync time: {sync_time:.1f}s")
                print(f"  Items per second: {items_per_second:.1f}")
                print(f"  Memory used: {memory_used:.1f} MB")
                
                # Define acceptable performance thresholds
                acceptable_time = size * 0.01  # 0.01 seconds per item
                acceptable_memory = size * 0.1  # 0.1 MB per item
                
                if not success or sync_time > acceptable_time or memory_used > acceptable_memory:
                    print(f"  Performance limit reached at {size:,} items")
                    break    
 
   def test_concurrent_sync_performance(self, performance_client, large_library_data):
        """Test performance with multiple concurrent sync operations."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            mock_client_instance.get_libraries.return_value = large_library_data['libraries']
            mock_client_instance.get_collections.return_value = large_library_data['collections']
            mock_client_instance.get_items.return_value = large_library_data['items'][:1000]  # Smaller dataset for concurrent test
            
            # Create multiple test users
            num_concurrent_users = 5
            user_ids = [f"concurrent-perf-user-{i}" for i in range(num_concurrent_users)]
            
            def perform_sync(user_id):
                """Perform sync operation for a single user."""
                connection_id = f"{user_id}-conn"
                
                # Setup connection
                performance_client.post(
                    "/api/zotero/auth/test-connection",
                    json={"user_id": user_id, "access_token": f"token-{user_id}"}
                )
                
                # Perform sync
                start_time = time.time()
                sync_response = performance_client.post(
                    f"/api/zotero/sync/{connection_id}/libraries",
                    json={"batch_size": 200}
                )
                duration = time.time() - start_time
                
                return {
                    'user_id': user_id,
                    'status_code': sync_response.status_code,
                    'duration': duration,
                    'success': sync_response.status_code == 200
                }
            
            # Execute concurrent syncs
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=num_concurrent_users) as executor:
                futures = [executor.submit(perform_sync, user_id) for user_id in user_ids]
                results = [future.result() for future in as_completed(futures)]
            
            total_duration = time.time() - start_time
            
            # Performance assertions
            assert all(result['success'] for result in results)
            assert total_duration < 180.0  # All syncs should complete within 3 minutes
            
            # Check individual sync performance
            avg_duration = sum(result['duration'] for result in results) / len(results)
            max_duration = max(result['duration'] for result in results)
            
            assert avg_duration < 60.0  # Average sync should be under 1 minute
            assert max_duration < 90.0  # No sync should take more than 1.5 minutes
            
            print(f"Concurrent Sync Performance Metrics:")
            print(f"  - Total duration: {total_duration:.2f} seconds")
            print(f"  - Average sync duration: {avg_duration:.2f} seconds")
            print(f"  - Max sync duration: {max_duration:.2f} seconds")
            print(f"  - Concurrent users: {num_concurrent_users}")
    
    def test_search_performance_large_dataset(self, performance_client, large_library_data):
        """Test search performance with large dataset."""
        
        with patch('services.zotero.zotero_search_service.ZoteroSearchService') as mock_search:
            mock_search_instance = AsyncMock()
            mock_search.return_value = mock_search_instance
            
            # Mock search to simulate large dataset search
            def mock_search_function(query, **kwargs):
                # Simulate search processing time based on dataset size
                time.sleep(0.1)  # Simulate database query time
                
                # Return realistic search results
                matching_items = [
                    item for item in large_library_data['items'][:1000]  # Limit for performance
                    if query.lower() in item['title'].lower() or 
                       query.lower() in item.get('abstractNote', '').lower()
                ][:100]  # Limit results
                
                return {
                    'items': matching_items,
                    'total_count': len(matching_items),
                    'facets': {
                        'authors': [{'name': f'Author{i}', 'count': 10} for i in range(10)],
                        'years': [{'year': str(2020 + i), 'count': 50} for i in range(4)],
                        'tags': [{'tag': f'tag{i}', 'count': 25} for i in range(20)]
                    },
                    'processing_time': 0.1
                }
            
            mock_search_instance.search_items.side_effect = mock_search_function
            
            # Test various search scenarios
            search_queries = [
                "machine learning",
                "artificial intelligence",
                "neural networks",
                "deep learning",
                "natural language processing",
                "computer vision",
                "data science",
                "algorithm",
                "optimization",
                "statistics"
            ]
            
            search_times = []
            
            for query in search_queries:
                start_time = time.time()
                
                search_response = performance_client.post(
                    "/api/zotero/search",
                    json={
                        "query": query,
                        "library_id": "perf-lib-123",
                        "limit": 100,
                        "include_facets": True,
                        "sort_by": "relevance"
                    }
                )
                
                search_time = time.time() - start_time
                search_times.append(search_time)
                
                assert search_response.status_code == 200
                assert search_time < 3.0  # Each search should complete within 3 seconds
                
                search_data = search_response.json()
                assert "items" in search_data
                assert "total_count" in search_data
                assert "facets" in search_data
            
            # Performance metrics
            avg_search_time = sum(search_times) / len(search_times)
            max_search_time = max(search_times)
            
            assert avg_search_time < 1.5  # Average search time should be under 1.5 seconds
            assert max_search_time < 3.0   # No search should take more than 3 seconds
            
            print(f"Search Performance Metrics:")
            print(f"  - Average search time: {avg_search_time:.3f} seconds")
            print(f"  - Max search time: {max_search_time:.3f} seconds")
            print(f"  - Total queries tested: {len(search_queries)}")


@pytest.mark.performance
class TestZoteroCitationPerformance:
    """Performance tests for citation generation."""
    
    @pytest.fixture
    def citation_test_data(self):
        """Generate test data for citation performance testing."""
        items = []
        for i in range(1000):
            items.append({
                'key': f'CITE{i:04d}',
                'itemType': 'journalArticle' if i % 2 == 0 else 'book',
                'title': f'Citation Performance Test Item {i}',
                'creators': [
                    {'creatorType': 'author', 'firstName': f'First{i}', 'lastName': f'Last{i}'}
                    for _ in range(1 + i % 3)
                ],
                'publicationTitle': f'Journal {i % 50}' if i % 2 == 0 else None,
                'publisher': f'Publisher {i % 20}' if i % 2 == 1 else None,
                'date': str(2000 + (i % 24)),
                'pages': f'{100 + i}-{120 + i}',
                'volume': str(i % 50 + 1),
                'issue': str(i % 12 + 1),
                'DOI': f'10.1000/citation.{i:04d}',
                'ISBN': f'978-0-{i:04d}-000-0' if i % 2 == 1 else None
            })
        return items
    
    def test_bulk_citation_generation_performance(self, performance_client, citation_test_data):
        """Test performance of bulk citation generation."""
        
        with patch('services.zotero.zotero_citation_service.ZoteroCitationService') as mock_citation:
            mock_citation_instance = AsyncMock()
            mock_citation.return_value = mock_citation_instance
            
            def mock_generate_citations(item_keys, style, format_type):
                # Simulate citation generation processing time
                processing_time = len(item_keys) * 0.01  # 10ms per citation
                time.sleep(processing_time)
                
                return [
                    {
                        'item_key': key,
                        'citation': f'{style.upper()} citation for {key}',
                        'style': style,
                        'format': format_type
                    }
                    for key in item_keys
                ]
            
            mock_citation_instance.generate_citations.side_effect = mock_generate_citations
            
            # Test different batch sizes
            batch_sizes = [10, 50, 100, 250, 500]
            citation_styles = ['apa', 'mla', 'chicago', 'ieee']
            
            for batch_size in batch_sizes:
                for style in citation_styles:
                    item_keys = [f'CITE{i:04d}' for i in range(batch_size)]
                    
                    start_time = time.time()
                    
                    citation_response = performance_client.post(
                        "/api/zotero/citations/generate",
                        json={
                            "item_keys": item_keys,
                            "style": style,
                            "format": "text"
                        }
                    )
                    
                    generation_time = time.time() - start_time
                    
                    assert citation_response.status_code == 200
                    
                    # Performance assertions based on batch size
                    max_time = batch_size * 0.02 + 1.0  # 20ms per citation + 1s overhead
                    assert generation_time < max_time
                    
                    citation_data = citation_response.json()
                    assert len(citation_data["citations"]) == batch_size
                    
                    # Calculate citations per second
                    citations_per_second = batch_size / generation_time
                    
                    print(f"Citation Performance - Batch: {batch_size}, Style: {style}")
                    print(f"  - Time: {generation_time:.3f}s")
                    print(f"  - Rate: {citations_per_second:.1f} citations/second")
    
    def test_bibliography_generation_performance(self, performance_client, citation_test_data):
        """Test performance of bibliography generation."""
        
        with patch('services.zotero.zotero_citation_service.ZoteroCitationService') as mock_citation:
            mock_citation_instance = AsyncMock()
            mock_citation.return_value = mock_citation_instance
            
            def mock_generate_bibliography(item_keys, style, format_type):
                # Simulate bibliography generation processing time
                processing_time = len(item_keys) * 0.015 + 0.5  # 15ms per item + formatting overhead
                time.sleep(processing_time)
                
                bibliography_entries = [
                    f'{style.upper()} bibliography entry for {key}'
                    for key in item_keys
                ]
                
                return {
                    'bibliography': '\n'.join(bibliography_entries),
                    'style': style,
                    'format': format_type,
                    'entry_count': len(item_keys)
                }
            
            mock_citation_instance.generate_bibliography.side_effect = mock_generate_bibliography
            
            # Test bibliography generation with different sizes
            bibliography_sizes = [25, 100, 250, 500]
            
            for size in bibliography_sizes:
                item_keys = [f'CITE{i:04d}' for i in range(size)]
                
                start_time = time.time()
                
                bibliography_response = performance_client.post(
                    "/api/zotero/citations/bibliography",
                    json={
                        "item_keys": item_keys,
                        "style": "apa",
                        "format": "html"
                    }
                )
                
                generation_time = time.time() - start_time
                
                assert bibliography_response.status_code == 200
                
                # Performance assertion
                max_time = size * 0.025 + 2.0  # 25ms per entry + 2s overhead
                assert generation_time < max_time
                
                bibliography_data = bibliography_response.json()
                assert "bibliography" in bibliography_data
                assert bibliography_data["entry_count"] == size
                
                print(f"Bibliography Performance - Size: {size}")
                print(f"  - Time: {generation_time:.3f}s")
                print(f"  - Rate: {size / generation_time:.1f} entries/second")


@pytest.mark.performance
class TestZoteroAIPerformance:
    """Performance tests for AI-enhanced features."""
    
    @pytest.fixture
    def ai_test_data(self):
        """Generate test data for AI performance testing."""
        items = []
        for i in range(500):
            items.append({
                'key': f'AI{i:04d}',
                'title': f'AI Performance Test Paper {i}: Machine Learning Applications',
                'abstractNote': f'This paper explores machine learning applications in domain {i}. ' * 10,  # Longer abstracts
                'creators': [{'firstName': f'AI{i}', 'lastName': f'Researcher{i}'}],
                'tags': [{'tag': f'ai{i % 20}'}, {'tag': f'ml{i % 15}'}, {'tag': f'domain{i % 10}'}],
                'date': str(2020 + (i % 4))
            })
        return items
    
    def test_ai_analysis_performance(self, performance_client, ai_test_data):
        """Test performance of AI content analysis."""
        
        with patch('services.zotero.zotero_ai_analysis_service.ZoteroAIAnalysisService') as mock_ai:
            mock_ai_instance = AsyncMock()
            mock_ai.return_value = mock_ai_instance
            
            def mock_analyze_content(item_key, content):
                # Simulate AI processing time based on content length
                processing_time = len(content) / 10000  # 1 second per 10k characters
                time.sleep(min(processing_time, 2.0))  # Cap at 2 seconds
                
                return {
                    'topics': ['machine learning', 'artificial intelligence', 'data science'],
                    'keywords': ['ML', 'AI', 'algorithm', 'model', 'training'],
                    'summary': f'AI-generated summary for {item_key}',
                    'sentiment': 'positive',
                    'complexity_score': 0.7,
                    'processing_time': processing_time
                }
            
            mock_ai_instance.analyze_content.side_effect = mock_analyze_content
            
            # Test batch AI analysis
            batch_sizes = [5, 10, 25, 50]
            
            for batch_size in batch_sizes:
                item_keys = [f'AI{i:04d}' for i in range(batch_size)]
                
                start_time = time.time()
                
                # Simulate batch analysis
                analysis_responses = []
                for item_key in item_keys:
                    response = performance_client.post(
                        f"/api/zotero/ai/analyze/{item_key}"
                    )
                    analysis_responses.append(response)
                
                total_time = time.time() - start_time
                
                # Performance assertions
                assert all(resp.status_code == 200 for resp in analysis_responses)
                
                # Should process items efficiently
                max_time = batch_size * 2.5  # 2.5 seconds per item max
                assert total_time < max_time
                
                avg_time_per_item = total_time / batch_size
                
                print(f"AI Analysis Performance - Batch: {batch_size}")
                print(f"  - Total time: {total_time:.2f}s")
                print(f"  - Avg time per item: {avg_time_per_item:.2f}s")
    
    def test_similarity_search_performance(self, performance_client, ai_test_data):
        """Test performance of similarity search."""
        
        with patch('services.zotero.zotero_similarity_service.ZoteroSimilarityService') as mock_similarity:
            mock_similarity_instance = AsyncMock()
            mock_similarity.return_value = mock_similarity_instance
            
            def mock_find_similar(item_key, limit=10):
                # Simulate similarity computation time
                time.sleep(0.5)  # 500ms for similarity computation
                
                return [
                    {
                        'item_key': f'SIM{i:04d}',
                        'similarity_score': 0.9 - (i * 0.1),
                        'title': f'Similar paper {i}'
                    }
                    for i in range(min(limit, 10))
                ]
            
            mock_similarity_instance.find_similar_items.side_effect = mock_find_similar
            
            # Test similarity search for multiple items
            test_items = [f'AI{i:04d}' for i in range(20)]
            
            similarity_times = []
            
            for item_key in test_items:
                start_time = time.time()
                
                similarity_response = performance_client.post(
                    f"/api/zotero/ai/similar/{item_key}",
                    json={"limit": 10}
                )
                
                similarity_time = time.time() - start_time
                similarity_times.append(similarity_time)
                
                assert similarity_response.status_code == 200
                assert similarity_time < 2.0  # Should complete within 2 seconds
                
                similarity_data = similarity_response.json()
                assert "similar_items" in similarity_data
            
            avg_similarity_time = sum(similarity_times) / len(similarity_times)
            max_similarity_time = max(similarity_times)
            
            print(f"Similarity Search Performance:")
            print(f"  - Average time: {avg_similarity_time:.3f}s")
            print(f"  - Max time: {max_similarity_time:.3f}s")
            print(f"  - Items tested: {len(test_items)}")