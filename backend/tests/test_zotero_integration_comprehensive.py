"""
Comprehensive integration tests for Zotero integration.
Tests complete end-to-end workflows for Zotero features.
"""
import pytest
import asyncio
import json
import time
import psutil
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from app import app
from models.zotero_models import ZoteroConnection, ZoteroLibrary, ZoteroItem, ZoteroCollection
from services.zotero.zotero_auth_service import ZoteroAuthService
from services.zotero.zotero_sync_service import ZoteroSyncService
from services.zotero.zotero_citation_service import ZoteroCitationService


@pytest.mark.integration
class TestZoteroEndToEndWorkflows:
    """End-to-end integration tests for complete Zotero workflows."""
    
    @pytest.fixture
    def test_client_zotero(self, test_db_session, mock_redis):
        """Create test client for Zotero integration tests."""
        app.dependency_overrides.clear()
        
        from core.database import get_db
        from core.redis_client import get_redis_client
        
        app.dependency_overrides[get_db] = lambda: test_db_session
        app.dependency_overrides[get_redis_client] = lambda: mock_redis
        
        with TestClient(app) as client:
            yield client
        
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def mock_zotero_api(self):
        """Mock Zotero API responses."""
        return {
            'oauth_token': 'test-oauth-token',
            'oauth_token_secret': 'test-oauth-secret',
            'access_token': 'test-access-token',
            'user_id': '12345',
            'libraries': [
                {
                    'id': 'user-lib-123',
                    'type': 'user',
                    'name': 'My Library',
                    'version': 100
                }
            ],
            'collections': [
                {
                    'key': 'ABCD1234',
                    'name': 'Research Papers',
                    'parentCollection': None,
                    'version': 50
                }
            ],
            'items': [
                {
                    'key': 'ITEM1234',
                    'version': 25,
                    'itemType': 'journalArticle',
                    'title': 'Machine Learning in Healthcare',
                    'creators': [
                        {'creatorType': 'author', 'firstName': 'John', 'lastName': 'Doe'}
                    ],
                    'publicationTitle': 'AI Journal',
                    'date': '2023',
                    'abstractNote': 'This paper discusses ML applications in healthcare.',
                    'tags': [{'tag': 'machine learning'}, {'tag': 'healthcare'}]
                }
            ]
        }
    
    def test_complete_zotero_connection_workflow(self, test_client_zotero, mock_zotero_api):
        """Test complete workflow from OAuth connection to library sync."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            # Setup mock client
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Mock OAuth flow
            mock_client_instance.initiate_oauth.return_value = {
                'oauth_token': mock_zotero_api['oauth_token'],
                'oauth_token_secret': mock_zotero_api['oauth_token_secret'],
                'authorization_url': 'https://www.zotero.org/oauth/authorize?oauth_token=test'
            }
            
            mock_client_instance.complete_oauth.return_value = {
                'access_token': mock_zotero_api['access_token'],
                'user_id': mock_zotero_api['user_id']
            }
            
            mock_client_instance.get_libraries.return_value = mock_zotero_api['libraries']
            mock_client_instance.get_collections.return_value = mock_zotero_api['collections']
            mock_client_instance.get_items.return_value = mock_zotero_api['items']
            
            user_id = "test-user-123"
            
            # Step 1: Initiate OAuth
            oauth_response = test_client_zotero.post(
                "/api/zotero/auth/initiate",
                json={"user_id": user_id}
            )
            
            assert oauth_response.status_code == 200
            oauth_data = oauth_response.json()
            assert "authorization_url" in oauth_data
            assert "oauth_token" in oauth_data
            
            # Step 2: Complete OAuth (simulate callback)
            callback_response = test_client_zotero.post(
                "/api/zotero/auth/callback",
                json={
                    "user_id": user_id,
                    "oauth_token": mock_zotero_api['oauth_token'],
                    "oauth_verifier": "test-verifier"
                }
            )
            
            assert callback_response.status_code == 200
            callback_data = callback_response.json()
            assert callback_data["success"] is True
            assert "connection_id" in callback_data
            
            connection_id = callback_data["connection_id"]
            
            # Step 3: Sync libraries
            sync_response = test_client_zotero.post(
                f"/api/zotero/sync/{connection_id}/libraries"
            )
            
            assert sync_response.status_code == 200
            sync_data = sync_response.json()
            assert sync_data["success"] is True
            assert "sync_id" in sync_data
            
            # Step 4: Check sync status
            sync_id = sync_data["sync_id"]
            status_response = test_client_zotero.get(
                f"/api/zotero/sync/{sync_id}/status"
            )
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert "status" in status_data
            
            # Step 5: Get synced items
            items_response = test_client_zotero.get(
                f"/api/zotero/libraries/{connection_id}/items"
            )
            
            assert items_response.status_code == 200
            items_data = items_response.json()
            assert "items" in items_data
            assert len(items_data["items"]) > 0
    
    def test_large_library_sync_performance(self, test_client_zotero, mock_zotero_api):
        """Test performance with large library sync operations."""
        
        # Create large dataset
        large_items = []
        for i in range(1000):  # 1000 items
            large_items.append({
                'key': f'ITEM{i:04d}',
                'version': i + 1,
                'itemType': 'journalArticle',
                'title': f'Research Paper {i}',
                'creators': [
                    {'creatorType': 'author', 'firstName': f'Author{i}', 'lastName': f'Lastname{i}'}
                ],
                'publicationTitle': f'Journal {i % 10}',
                'date': str(2020 + (i % 4)),
                'abstractNote': f'Abstract for paper {i}',
                'tags': [{'tag': f'tag{i % 20}'}, {'tag': f'category{i % 5}'}]
            })
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Mock large dataset responses
            mock_client_instance.get_libraries.return_value = mock_zotero_api['libraries']
            mock_client_instance.get_collections.return_value = mock_zotero_api['collections']
            mock_client_instance.get_items.return_value = large_items
            
            user_id = "perf-test-user"
            
            # Setup connection (simplified)
            connection_response = test_client_zotero.post(
                "/api/zotero/auth/test-connection",
                json={
                    "user_id": user_id,
                    "access_token": "test-token"
                }
            )
            
            connection_id = connection_response.json().get("connection_id", "test-conn")
            
            # Measure sync performance
            start_time = time.time()
            
            sync_response = test_client_zotero.post(
                f"/api/zotero/sync/{connection_id}/libraries",
                json={"batch_size": 100}  # Process in batches
            )
            
            sync_time = time.time() - start_time
            
            assert sync_response.status_code == 200
            assert sync_time < 30.0  # Should complete within 30 seconds
            
            # Verify all items were processed
            items_response = test_client_zotero.get(
                f"/api/zotero/libraries/{connection_id}/items?limit=1000"
            )
            
            assert items_response.status_code == 200
            items_data = items_response.json()
            assert len(items_data["items"]) == 1000
    
    def test_concurrent_sync_operations(self, test_client_zotero, mock_zotero_api):
        """Test system behavior with concurrent sync operations."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            mock_client_instance.get_libraries.return_value = mock_zotero_api['libraries']
            mock_client_instance.get_collections.return_value = mock_zotero_api['collections']
            mock_client_instance.get_items.return_value = mock_zotero_api['items']
            
            # Create multiple users
            user_ids = [f"concurrent-user-{i}" for i in range(5)]
            connection_ids = []
            
            # Setup connections for all users
            for user_id in user_ids:
                connection_response = test_client_zotero.post(
                    "/api/zotero/auth/test-connection",
                    json={
                        "user_id": user_id,
                        "access_token": f"test-token-{user_id}"
                    }
                )
                connection_ids.append(connection_response.json().get("connection_id", f"conn-{user_id}"))
            
            # Perform concurrent syncs
            def sync_library(connection_id):
                return test_client_zotero.post(
                    f"/api/zotero/sync/{connection_id}/libraries"
                )
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(sync_library, conn_id) for conn_id in connection_ids]
                results = [future.result() for future in as_completed(futures)]
            
            concurrent_time = time.time() - start_time
            
            # Verify all syncs completed successfully
            assert all(result.status_code == 200 for result in results)
            assert concurrent_time < 60.0  # Should complete within 1 minute
            
            # Verify no data corruption
            for connection_id in connection_ids:
                items_response = test_client_zotero.get(
                    f"/api/zotero/libraries/{connection_id}/items"
                )
                assert items_response.status_code == 200
                items_data = items_response.json()
                assert len(items_data["items"]) > 0
    
    def test_citation_generation_workflow(self, test_client_zotero, mock_zotero_api):
        """Test complete citation generation workflow."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            mock_client_instance.get_items.return_value = mock_zotero_api['items']
            
            user_id = "citation-test-user"
            connection_id = "citation-test-conn"
            
            # Setup test connection
            test_client_zotero.post(
                "/api/zotero/auth/test-connection",
                json={
                    "user_id": user_id,
                    "access_token": "test-token"
                }
            )
            
            # Sync items
            test_client_zotero.post(
                f"/api/zotero/sync/{connection_id}/libraries"
            )
            
            item_key = mock_zotero_api['items'][0]['key']
            
            # Test different citation styles
            citation_styles = ['apa', 'mla', 'chicago', 'ieee']
            
            for style in citation_styles:
                citation_response = test_client_zotero.post(
                    f"/api/zotero/citations/generate",
                    json={
                        "item_keys": [item_key],
                        "style": style,
                        "format": "text"
                    }
                )
                
                assert citation_response.status_code == 200
                citation_data = citation_response.json()
                assert "citations" in citation_data
                assert len(citation_data["citations"]) == 1
                assert citation_data["citations"][0]["style"] == style
            
            # Test bibliography generation
            bibliography_response = test_client_zotero.post(
                f"/api/zotero/citations/bibliography",
                json={
                    "item_keys": [item_key],
                    "style": "apa",
                    "format": "html"
                }
            )
            
            assert bibliography_response.status_code == 200
            bibliography_data = bibliography_response.json()
            assert "bibliography" in bibliography_data
            assert "html" in bibliography_data["bibliography"]
    
    def test_ai_analysis_integration_workflow(self, test_client_zotero, mock_zotero_api):
        """Test AI analysis integration with Zotero items."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client, \
             patch('services.zotero.zotero_ai_analysis_service.ZoteroAIAnalysisService') as mock_ai:
            
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.get_items.return_value = mock_zotero_api['items']
            
            mock_ai_instance = AsyncMock()
            mock_ai.return_value = mock_ai_instance
            mock_ai_instance.analyze_content.return_value = {
                'topics': ['machine learning', 'healthcare', 'artificial intelligence'],
                'keywords': ['ML', 'AI', 'medical', 'diagnosis'],
                'summary': 'This paper explores ML applications in healthcare.',
                'sentiment': 'positive',
                'complexity_score': 0.7
            }
            
            mock_ai_instance.find_similar_items.return_value = [
                {
                    'item_key': 'SIMILAR1',
                    'similarity_score': 0.85,
                    'title': 'AI in Medical Diagnosis'
                }
            ]
            
            user_id = "ai-test-user"
            connection_id = "ai-test-conn"
            
            # Setup and sync
            test_client_zotero.post(
                "/api/zotero/auth/test-connection",
                json={"user_id": user_id, "access_token": "test-token"}
            )
            
            test_client_zotero.post(
                f"/api/zotero/sync/{connection_id}/libraries"
            )
            
            item_key = mock_zotero_api['items'][0]['key']
            
            # Test content analysis
            analysis_response = test_client_zotero.post(
                f"/api/zotero/ai/analyze/{item_key}"
            )
            
            assert analysis_response.status_code == 200
            analysis_data = analysis_response.json()
            assert "topics" in analysis_data
            assert "keywords" in analysis_data
            assert "summary" in analysis_data
            
            # Test similarity search
            similarity_response = test_client_zotero.post(
                f"/api/zotero/ai/similar/{item_key}",
                json={"limit": 5}
            )
            
            assert similarity_response.status_code == 200
            similarity_data = similarity_response.json()
            assert "similar_items" in similarity_data
            assert len(similarity_data["similar_items"]) > 0
            
            # Test research insights
            insights_response = test_client_zotero.get(
                f"/api/zotero/ai/insights/{connection_id}"
            )
            
            assert insights_response.status_code == 200
            insights_data = insights_response.json()
            assert "topic_clusters" in insights_data
            assert "research_gaps" in insights_data
    
    def test_real_time_sync_workflow(self, test_client_zotero, mock_zotero_api):
        """Test real-time synchronization workflow."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client, \
             patch('services.zotero.zotero_webhook_service.ZoteroWebhookService') as mock_webhook:
            
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            mock_webhook_instance = AsyncMock()
            mock_webhook.return_value = mock_webhook_instance
            
            user_id = "realtime-test-user"
            connection_id = "realtime-test-conn"
            
            # Setup webhook
            webhook_response = test_client_zotero.post(
                f"/api/zotero/webhooks/setup/{connection_id}",
                json={"events": ["item_created", "item_updated", "item_deleted"]}
            )
            
            assert webhook_response.status_code == 200
            webhook_data = webhook_response.json()
            assert "webhook_url" in webhook_data
            
            # Simulate webhook notification
            webhook_payload = {
                "event": "item_created",
                "library_id": "user-lib-123",
                "item_key": "NEWITEM123",
                "version": 101,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            webhook_notification_response = test_client_zotero.post(
                f"/api/zotero/webhooks/notify",
                json=webhook_payload,
                headers={"X-Zotero-Webhook-Signature": "test-signature"}
            )
            
            assert webhook_notification_response.status_code == 200
            
            # Verify background sync was triggered
            time.sleep(1)  # Allow background processing
            
            sync_status_response = test_client_zotero.get(
                f"/api/zotero/sync/{connection_id}/status"
            )
            
            assert sync_status_response.status_code == 200
            status_data = sync_status_response.json()
            assert "last_sync" in status_data
    
    def test_collaborative_features_workflow(self, test_client_zotero, mock_zotero_api):
        """Test collaborative features workflow."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Mock group library
            group_library = {
                'id': 'group-lib-456',
                'type': 'group',
                'name': 'Research Team Library',
                'version': 200
            }
            
            mock_client_instance.get_libraries.return_value = [
                mock_zotero_api['libraries'][0],
                group_library
            ]
            
            mock_client_instance.get_items.return_value = mock_zotero_api['items']
            
            user_id = "collab-test-user"
            connection_id = "collab-test-conn"
            
            # Setup connection and sync
            test_client_zotero.post(
                "/api/zotero/auth/test-connection",
                json={"user_id": user_id, "access_token": "test-token"}
            )
            
            test_client_zotero.post(
                f"/api/zotero/sync/{connection_id}/libraries"
            )
            
            # Test group library access
            group_items_response = test_client_zotero.get(
                f"/api/zotero/libraries/group-lib-456/items"
            )
            
            assert group_items_response.status_code == 200
            group_data = group_items_response.json()
            assert "items" in group_data
            
            # Test reference sharing
            item_key = mock_zotero_api['items'][0]['key']
            
            share_response = test_client_zotero.post(
                f"/api/zotero/sharing/share",
                json={
                    "item_keys": [item_key],
                    "target_user_id": "collaborator-user",
                    "permissions": ["read", "annotate"]
                }
            )
            
            assert share_response.status_code == 200
            share_data = share_response.json()
            assert share_data["success"] is True
            
            # Test collaborative annotations
            annotation_response = test_client_zotero.post(
                f"/api/zotero/annotations/create",
                json={
                    "item_key": item_key,
                    "annotation_type": "highlight",
                    "content": "Important finding",
                    "position": {"page": 1, "x": 100, "y": 200}
                }
            )
            
            assert annotation_response.status_code == 200
            annotation_data = annotation_response.json()
            assert "annotation_id" in annotation_data


@pytest.mark.performance
class TestZoteroPerformanceIntegration:
    """Performance integration tests for Zotero features."""
    
    def test_search_performance_with_large_dataset(self, test_client_zotero):
        """Test search performance with large number of items."""
        
        # Create large test dataset
        large_dataset = []
        for i in range(5000):
            large_dataset.append({
                'key': f'PERF{i:05d}',
                'title': f'Performance Test Paper {i}',
                'creators': [{'firstName': f'Author{i}', 'lastName': f'Test{i}'}],
                'abstractNote': f'Abstract content for performance testing {i}',
                'tags': [{'tag': f'performance{i % 100}'}, {'tag': f'test{i % 50}'}]
            })
        
        with patch('services.zotero.zotero_search_service.ZoteroSearchService') as mock_search:
            mock_search_instance = AsyncMock()
            mock_search.return_value = mock_search_instance
            
            # Mock search results
            mock_search_instance.search_items.return_value = {
                'items': large_dataset[:100],  # Return first 100 results
                'total_count': 5000,
                'facets': {
                    'authors': [{'name': 'Author1', 'count': 50}],
                    'tags': [{'name': 'performance1', 'count': 25}]
                }
            }
            
            # Test search performance
            search_queries = [
                "machine learning",
                "artificial intelligence", 
                "neural networks",
                "deep learning",
                "natural language processing"
            ]
            
            for query in search_queries:
                start_time = time.time()
                
                search_response = test_client_zotero.post(
                    "/api/zotero/search",
                    json={
                        "query": query,
                        "library_id": "perf-lib-123",
                        "limit": 100,
                        "include_facets": True
                    }
                )
                
                search_time = time.time() - start_time
                
                assert search_response.status_code == 200
                assert search_time < 2.0  # Should complete within 2 seconds
                
                search_data = search_response.json()
                assert "items" in search_data
                assert "total_count" in search_data
                assert "facets" in search_data
    
    def test_citation_generation_performance(self, test_client_zotero):
        """Test citation generation performance with many items."""
        
        # Create test items for citation
        citation_items = [f'CITE{i:04d}' for i in range(100)]
        
        with patch('services.zotero.zotero_citation_service.ZoteroCitationService') as mock_citation:
            mock_citation_instance = AsyncMock()
            mock_citation.return_value = mock_citation_instance
            
            mock_citation_instance.generate_citations.return_value = [
                {
                    'item_key': key,
                    'citation': f'Citation for {key}',
                    'style': 'apa'
                } for key in citation_items
            ]
            
            start_time = time.time()
            
            citation_response = test_client_zotero.post(
                "/api/zotero/citations/generate",
                json={
                    "item_keys": citation_items,
                    "style": "apa",
                    "format": "text"
                }
            )
            
            citation_time = time.time() - start_time
            
            assert citation_response.status_code == 200
            assert citation_time < 5.0  # Should complete within 5 seconds
            
            citation_data = citation_response.json()
            assert len(citation_data["citations"]) == 100
    
    def test_memory_usage_during_sync(self, test_client_zotero):
        """Test memory usage during large sync operations."""
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large sync dataset
        large_sync_data = []
        for i in range(2000):
            large_sync_data.append({
                'key': f'MEM{i:05d}',
                'title': f'Memory Test Item {i}',
                'abstractNote': 'A' * 1000,  # 1KB abstract
                'creators': [{'firstName': f'Author{i}', 'lastName': f'Test{i}'}]
            })
        
        with patch('services.zotero.zotero_sync_service.ZoteroSyncService') as mock_sync:
            mock_sync_instance = AsyncMock()
            mock_sync.return_value = mock_sync_instance
            
            mock_sync_instance.sync_items.return_value = {
                'success': True,
                'items_processed': len(large_sync_data),
                'items_added': len(large_sync_data),
                'items_updated': 0,
                'errors': []
            }
            
            # Perform sync
            sync_response = test_client_zotero.post(
                "/api/zotero/sync/memory-test-conn/libraries",
                json={"batch_size": 200}
            )
            
            assert sync_response.status_code == 200
            
            # Check memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (less than 500MB)
            assert memory_increase < 500


@pytest.mark.stress
class TestZoteroStressTests:
    """Stress tests for Zotero integration under high load."""
    
    def test_concurrent_user_operations(self, test_client_zotero):
        """Test system behavior with many concurrent users."""
        
        def simulate_user_activity(user_id):
            """Simulate typical user activity."""
            operations = []
            
            # Connection
            conn_response = test_client_zotero.post(
                "/api/zotero/auth/test-connection",
                json={"user_id": user_id, "access_token": f"token-{user_id}"}
            )
            operations.append(('connection', conn_response.status_code))
            
            # Sync
            sync_response = test_client_zotero.post(
                f"/api/zotero/sync/{user_id}-conn/libraries"
            )
            operations.append(('sync', sync_response.status_code))
            
            # Search
            search_response = test_client_zotero.post(
                "/api/zotero/search",
                json={"query": "test", "library_id": f"{user_id}-lib"}
            )
            operations.append(('search', search_response.status_code))
            
            # Citation
            citation_response = test_client_zotero.post(
                "/api/zotero/citations/generate",
                json={"item_keys": ["TEST123"], "style": "apa"}
            )
            operations.append(('citation', citation_response.status_code))
            
            return operations
        
        # Simulate 20 concurrent users
        num_users = 20
        user_ids = [f"stress-user-{i}" for i in range(num_users)]
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(simulate_user_activity, user_id) for user_id in user_ids]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Verify all operations completed
        assert len(results) == num_users
        
        # Check success rates
        all_operations = [op for user_ops in results for op in user_ops]
        success_rate = sum(1 for _, status in all_operations if status == 200) / len(all_operations)
        
        assert success_rate > 0.8  # At least 80% success rate
        assert total_time < 120.0  # Should complete within 2 minutes
    
    def test_high_frequency_sync_operations(self, test_client_zotero):
        """Test system behavior with high frequency sync operations."""
        
        with patch('services.zotero.zotero_sync_service.ZoteroSyncService') as mock_sync:
            mock_sync_instance = AsyncMock()
            mock_sync.return_value = mock_sync_instance
            
            mock_sync_instance.sync_items.return_value = {
                'success': True,
                'items_processed': 10,
                'items_added': 5,
                'items_updated': 5,
                'errors': []
            }
            
            connection_id = "high-freq-conn"
            
            # Perform rapid sync operations
            sync_results = []
            for i in range(50):  # 50 rapid syncs
                sync_response = test_client_zotero.post(
                    f"/api/zotero/sync/{connection_id}/incremental"
                )
                sync_results.append(sync_response.status_code)
                
                time.sleep(0.1)  # Small delay between requests
            
            # Verify most syncs succeeded
            success_count = sum(1 for status in sync_results if status == 200)
            success_rate = success_count / len(sync_results)
            
            assert success_rate > 0.9  # At least 90% success rate
    
    def test_large_batch_operations(self, test_client_zotero):
        """Test system behavior with large batch operations."""
        
        # Test large citation batch
        large_item_keys = [f'BATCH{i:05d}' for i in range(500)]
        
        with patch('services.zotero.zotero_citation_service.ZoteroCitationService') as mock_citation:
            mock_citation_instance = AsyncMock()
            mock_citation.return_value = mock_citation_instance
            
            mock_citation_instance.generate_citations.return_value = [
                {'item_key': key, 'citation': f'Citation {key}', 'style': 'apa'}
                for key in large_item_keys
            ]
            
            start_time = time.time()
            
            batch_response = test_client_zotero.post(
                "/api/zotero/citations/batch-generate",
                json={
                    "item_keys": large_item_keys,
                    "style": "apa",
                    "format": "text"
                }
            )
            
            batch_time = time.time() - start_time
            
            assert batch_response.status_code == 200
            assert batch_time < 30.0  # Should complete within 30 seconds
            
            batch_data = batch_response.json()
            assert len(batch_data["citations"]) == 500


@pytest.mark.integration
class TestZoteroErrorRecoveryIntegration:
    """Integration tests for error recovery scenarios."""
    
    def test_api_failure_recovery(self, test_client_zotero):
        """Test recovery from Zotero API failures."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Simulate API failure then recovery
            call_count = 0
            def failing_then_success(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:  # Fail first 2 calls
                    raise Exception("API temporarily unavailable")
                return [{'key': 'SUCCESS123', 'title': 'Recovery Test'}]
            
            mock_client_instance.get_items.side_effect = failing_then_success
            
            # Attempt sync with retry
            sync_response = test_client_zotero.post(
                "/api/zotero/sync/recovery-test-conn/libraries",
                json={"retry_on_failure": True, "max_retries": 3}
            )
            
            # Should eventually succeed
            assert sync_response.status_code == 200
            sync_data = sync_response.json()
            assert sync_data["success"] is True
            assert call_count == 3  # Should have retried
    
    def test_partial_sync_failure_handling(self, test_client_zotero):
        """Test handling of partial sync failures."""
        
        with patch('services.zotero.zotero_sync_service.ZoteroSyncService') as mock_sync:
            mock_sync_instance = AsyncMock()
            mock_sync.return_value = mock_sync_instance
            
            # Simulate partial failure
            mock_sync_instance.sync_items.return_value = {
                'success': True,
                'items_processed': 100,
                'items_added': 80,
                'items_updated': 15,
                'items_failed': 5,
                'errors': [
                    {'item_key': 'FAIL1', 'error': 'Invalid data format'},
                    {'item_key': 'FAIL2', 'error': 'Missing required field'}
                ]
            }
            
            sync_response = test_client_zotero.post(
                "/api/zotero/sync/partial-fail-conn/libraries"
            )
            
            assert sync_response.status_code == 200
            sync_data = sync_response.json()
            assert sync_data["success"] is True
            assert "errors" in sync_data
            assert len(sync_data["errors"]) == 2
    
    def test_network_timeout_handling(self, test_client_zotero):
        """Test handling of network timeouts."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Simulate timeout
            import asyncio
            mock_client_instance.get_items.side_effect = asyncio.TimeoutError("Request timeout")
            
            sync_response = test_client_zotero.post(
                "/api/zotero/sync/timeout-test-conn/libraries",
                json={"timeout": 5}
            )
            
            # Should handle timeout gracefully
            assert sync_response.status_code in [200, 408, 500]
            
            if sync_response.status_code == 200:
                sync_data = sync_response.json()
                assert "error" in sync_data or "timeout" in sync_data.get("message", "").lower()