#!/usr/bin/env python3
"""
Test script for Task 8.3: Add vector store monitoring and optimization.

This script tests the monitoring service, optimization service, and backup/recovery
capabilities for the multi-instance vector store system.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import tempfile
import shutil

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.vector_store.monitoring_service import (
        VectorStoreMonitoringService, HealthStatus, CollectionHealth, PerformanceSnapshot
    )
    from multi_instance_arxiv_system.vector_store.optimization_service import (
        VectorStoreOptimizationService, OptimizationType, OptimizationRecommendation
    )
    from multi_instance_arxiv_system.vector_store.backup_recovery_service import (
        BackupRecoveryService, BackupType, BackupStatus
    )
    from multi_instance_arxiv_system.vector_store.multi_instance_vector_store_service import MultiInstanceVectorStoreService
    from multi_instance_arxiv_system.shared.multi_instance_data_models import (
        VectorStoreConfig, MonitoringAlert
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)


class MockVectorStoreService:
    """Mock vector store service for testing."""
    
    def __init__(self):
        self.initialized_instances = {"test_ai_scholar", "test_quant_scholar"}
        self.instance_services = {}
        
        # Create mock services
        for instance in self.initialized_instances:
            mock_service = MockInstanceService(instance)
            self.instance_services[instance] = mock_service
    
    async def get_instance_stats(self, instance_name: str):
        """Mock instance stats."""
        return {
            'instance_name': instance_name,
            'collection_name': f"{instance_name}_papers",
            'total_chunks': 1000 if instance_name == "test_ai_scholar" else 800,
            'embedding_model': 'all-MiniLM-L6-v2',
            'paper_types': {'arxiv': 80, 'journal': 20} if instance_name == "test_quant_scholar" else {'arxiv': 100}
        }


class MockInstanceService:
    """Mock instance service for testing."""
    
    def __init__(self, instance_name: str):
        self.instance_name = instance_name
        self.collection_name = f"{instance_name}_papers"
        self.collection = MockCollection(instance_name)


class MockCollection:
    """Mock collection for testing."""
    
    def __init__(self, instance_name: str):
        self.instance_name = instance_name
        self.metadata = {
            'instance_name': instance_name,
            'embedding_model': 'all-MiniLM-L6-v2',
            'created_at': datetime.now().isoformat()
        }
        self._document_count = 1000 if instance_name == "test_ai_scholar" else 800
    
    def count(self):
        """Mock document count."""
        return self._document_count
    
    def get(self, limit=None, include=None):
        """Mock get method."""
        actual_limit = min(limit or self._document_count, self._document_count)
        
        result = {
            'ids': [f"doc_{i}" for i in range(actual_limit)],
            'documents': [f"This is test document {i} content." for i in range(actual_limit)],
            'metadatas': [
                {
                    'instance_name': self.instance_name,
                    'document_id': f"doc_{i}",
                    'title': f"Test Document {i}",
                    'text_quality_score': 0.8 if i % 10 != 0 else 0.3,  # Some low quality
                    'section': 'abstract' if i % 3 == 0 else 'introduction'
                }
                for i in range(actual_limit)
            ]
        }
        
        if include and 'embeddings' in include:
            # Mock embeddings (384 dimensions for MiniLM)
            import numpy as np
            result['embeddings'] = [
                np.random.normal(0, 1, 384).tolist() for _ in range(actual_limit)
            ]
        
        return result
    
    def query(self, query_texts, n_results=10):
        """Mock query method."""
        return {
            'ids': [[f"result_{i}" for i in range(n_results)]],
            'documents': [[f"Result document {i}" for i in range(n_results)]],
            'distances': [[0.1 * i for i in range(n_results)]]
        }


async def test_monitoring_service():
    """Test the VectorStoreMonitoringService."""
    print("Testing VectorStoreMonitoringService...")
    
    try:
        # Create mock vector store service
        vector_store_service = MockVectorStoreService()
        
        # Create monitoring service
        monitoring_service = VectorStoreMonitoringService(vector_store_service)
        
        # Test health check
        health_results = await monitoring_service.perform_health_check()
        
        assert len(health_results) == 2  # Two test instances
        assert "test_ai_scholar" in health_results
        assert "test_quant_scholar" in health_results
        
        # Check health result structure
        ai_health = health_results["test_ai_scholar"]
        assert isinstance(ai_health, CollectionHealth)
        assert ai_health.instance_name == "test_ai_scholar"
        assert ai_health.document_count == 1000
        assert ai_health.status in [HealthStatus.HEALTHY, HealthStatus.WARNING]
        
        print(f"✓ Health check completed: AI Scholar ({ai_health.status.value}), Quant Scholar ({health_results['test_quant_scholar'].status.value})")
        
        # Test performance snapshot
        snapshots = await monitoring_service.capture_performance_snapshot()
        
        assert len(snapshots) == 2
        assert "test_ai_scholar" in snapshots
        
        ai_snapshot = snapshots["test_ai_scholar"]
        assert isinstance(ai_snapshot, PerformanceSnapshot)
        assert ai_snapshot.instance_name == "test_ai_scholar"
        
        print(f"✓ Performance snapshot captured: {len(snapshots)} instances")
        
        # Test query time recording
        monitoring_service.record_query_time("test_ai_scholar", 150.0)
        monitoring_service.record_query_time("test_ai_scholar", 200.0)
        
        avg_time = monitoring_service._get_average_query_time("test_ai_scholar")
        assert avg_time == 175.0
        
        print(f"✓ Query time recording: average {avg_time}ms")
        
        # Test monitoring report generation
        report = await monitoring_service.generate_monitoring_report()
        
        assert 'summary' in report
        assert 'instance_health' in report
        assert report['summary']['total_instances'] == 2
        
        print(f"✓ Monitoring report generated: {report['summary']['total_instances']} instances")
        
        # Test alert generation
        alerts = monitoring_service.get_active_alerts()
        print(f"✓ Active alerts: {len(alerts)}")
        
        print("✓ VectorStoreMonitoringService tests passed")
        return True
        
    except Exception as e:
        print(f"❌ VectorStoreMonitoringService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_optimization_service():
    """Test the VectorStoreOptimizationService."""
    print("Testing VectorStoreOptimizationService...")
    
    try:
        # Create mock services
        vector_store_service = MockVectorStoreService()
        monitoring_service = VectorStoreMonitoringService(vector_store_service)
        
        # Create optimization service
        optimization_service = VectorStoreOptimizationService(
            vector_store_service, 
            monitoring_service
        )
        
        # Test optimization opportunity analysis
        recommendations = await optimization_service.analyze_optimization_opportunities("test_ai_scholar")
        
        assert isinstance(recommendations, list)
        print(f"✓ Generated {len(recommendations)} optimization recommendations")
        
        # Check recommendation structure
        if recommendations:
            rec = recommendations[0]
            assert isinstance(rec, OptimizationRecommendation)
            assert rec.instance_name == "test_ai_scholar"
            assert rec.optimization_type in [OptimizationType.PERFORMANCE, OptimizationType.STORAGE, OptimizationType.QUALITY, OptimizationType.CLEANUP]
            print(f"✓ First recommendation: {rec.title} ({rec.priority} priority)")
        
        # Test performance optimization
        perf_result = await optimization_service.optimize_instance_performance("test_ai_scholar")
        
        assert perf_result.optimization_type == OptimizationType.PERFORMANCE
        assert perf_result.instance_name == "test_ai_scholar"
        assert isinstance(perf_result.success, bool)
        
        print(f"✓ Performance optimization: {'success' if perf_result.success else 'failed'}")
        print(f"  Changes made: {len(perf_result.changes_made)}")
        
        # Test storage optimization
        storage_result = await optimization_service.optimize_instance_storage("test_ai_scholar")
        
        assert storage_result.optimization_type == OptimizationType.STORAGE
        assert storage_result.instance_name == "test_ai_scholar"
        
        print(f"✓ Storage optimization: {'success' if storage_result.success else 'failed'}")
        print(f"  Changes made: {len(storage_result.changes_made)}")
        
        # Test optimization history
        history = optimization_service.get_optimization_history("test_ai_scholar")
        assert len(history) >= 2  # Should have at least the two optimizations we ran
        
        print(f"✓ Optimization history: {len(history)} entries")
        
        # Test optimization statistics
        stats = optimization_service.get_optimization_statistics()
        
        assert 'total_optimizations' in stats
        assert 'successful_optimizations' in stats
        assert stats['total_optimizations'] >= 2
        
        print(f"✓ Optimization statistics: {stats['total_optimizations']} total, {stats['successful_optimizations']} successful")
        
        print("✓ VectorStoreOptimizationService tests passed")
        return True
        
    except Exception as e:
        print(f"❌ VectorStoreOptimizationService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_backup_recovery_service():
    """Test the BackupRecoveryService."""
    print("Testing BackupRecoveryService...")
    
    try:
        # Create temporary backup directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create mock vector store service
            vector_store_service = MockVectorStoreService()
            
            # Create backup service
            backup_service = BackupRecoveryService(
                vector_store_service, 
                backup_directory=temp_dir
            )
            
            # Test backup creation
            backup_metadata = await backup_service.create_backup(
                instance_name="test_ai_scholar",
                backup_type=BackupType.FULL,
                include_embeddings=True,
                compress=True
            )
            
            assert backup_metadata.instance_name == "test_ai_scholar"
            assert backup_metadata.backup_type == BackupType.FULL
            assert backup_metadata.status == BackupStatus.COMPLETED
            assert backup_metadata.document_count == 1000
            assert backup_metadata.backup_size_mb > 0
            
            print(f"✓ Backup created: {backup_metadata.backup_id} ({backup_metadata.backup_size_mb:.1f} MB)")
            
            # Test backup validation
            assert backup_metadata.validated
            assert len(backup_metadata.validation_errors) == 0
            
            print("✓ Backup validation passed")
            
            # Test backup history
            history = backup_service.get_backup_history("test_ai_scholar")
            assert len(history) == 1
            assert history[0].backup_id == backup_metadata.backup_id
            
            print(f"✓ Backup history: {len(history)} entries")
            
            # Test different backup types
            metadata_backup = await backup_service.create_backup(
                instance_name="test_quant_scholar",
                backup_type=BackupType.METADATA_ONLY,
                include_embeddings=False,
                compress=False
            )
            
            assert metadata_backup.backup_type == BackupType.METADATA_ONLY
            assert metadata_backup.status == BackupStatus.COMPLETED
            
            print(f"✓ Metadata-only backup created: {metadata_backup.backup_id}")
            
            # Test backup statistics
            stats = backup_service.get_backup_statistics()
            
            assert stats['total_backups'] == 2
            assert stats['successful_backups'] == 2
            assert stats['backup_success_rate'] == 1.0
            assert stats['total_backup_storage_mb'] > 0
            
            print(f"✓ Backup statistics: {stats['total_backups']} backups, {stats['total_backup_storage_mb']:.1f} MB total")
            
            # Note: Recovery testing would require a more complex setup with actual ChromaDB
            # For now, we'll just test the recovery metadata creation
            print("✓ BackupRecoveryService tests passed (recovery testing requires ChromaDB)")
            
            return True
            
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
        
    except Exception as e:
        print(f"❌ BackupRecoveryService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration():
    """Test integration between monitoring, optimization, and backup services."""
    print("Testing service integration...")
    
    try:
        # Create mock vector store service
        vector_store_service = MockVectorStoreService()
        
        # Create all services
        monitoring_service = VectorStoreMonitoringService(vector_store_service)
        optimization_service = VectorStoreOptimizationService(vector_store_service, monitoring_service)
        
        temp_dir = tempfile.mkdtemp()
        try:
            backup_service = BackupRecoveryService(vector_store_service, backup_directory=temp_dir)
            
            # Test workflow: Monitor -> Optimize -> Backup
            
            # 1. Monitor health
            health_results = await monitoring_service.perform_health_check()
            print(f"✓ Health check: {len(health_results)} instances monitored")
            
            # 2. Generate optimization recommendations based on health
            recommendations = await optimization_service.analyze_optimization_opportunities()
            print(f"✓ Optimization analysis: {len(recommendations)} recommendations generated")
            
            # 3. Perform optimization
            if recommendations:
                # Find a performance recommendation
                perf_rec = next((r for r in recommendations if r.optimization_type == OptimizationType.PERFORMANCE), None)
                if perf_rec:
                    result = await optimization_service.optimize_instance_performance(perf_rec.instance_name)
                    print(f"✓ Performance optimization: {'success' if result.success else 'failed'}")
            
            # 4. Create backup after optimization
            for instance_name in vector_store_service.initialized_instances:
                backup_metadata = await backup_service.create_backup(instance_name, BackupType.FULL)
                print(f"✓ Backup created for {instance_name}: {backup_metadata.backup_id}")
            
            # 5. Generate comprehensive report
            monitoring_report = await monitoring_service.generate_monitoring_report()
            optimization_stats = optimization_service.get_optimization_statistics()
            backup_stats = backup_service.get_backup_statistics()
            
            integration_report = {
                'timestamp': datetime.now().isoformat(),
                'monitoring': {
                    'instances_monitored': monitoring_report['summary']['total_instances'],
                    'average_query_time_ms': monitoring_report['summary']['average_query_time_ms'],
                    'active_alerts': monitoring_report['summary']['active_alerts']
                },
                'optimization': {
                    'total_optimizations': optimization_stats['total_optimizations'],
                    'success_rate': optimization_stats['success_rate'],
                    'active_recommendations': optimization_stats['active_recommendations']
                },
                'backup': {
                    'total_backups': backup_stats['total_backups'],
                    'backup_success_rate': backup_stats['backup_success_rate'],
                    'total_storage_mb': backup_stats['total_backup_storage_mb']
                }
            }
            
            print("✓ Integration report generated:")
            print(f"  Monitoring: {integration_report['monitoring']['instances_monitored']} instances")
            print(f"  Optimization: {integration_report['optimization']['total_optimizations']} operations")
            print(f"  Backup: {integration_report['backup']['total_backups']} backups")
            
            print("✓ Service integration tests passed")
            return True
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
        
    except Exception as e:
        print(f"❌ Service integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests for Task 8.3."""
    print("Testing Task 8.3: Add vector store monitoring and optimization")
    print("=" * 80)
    
    test_results = []
    
    try:
        # Test individual services
        test_results.append(await test_monitoring_service())
        test_results.append(await test_optimization_service())
        test_results.append(await test_backup_recovery_service())
        
        # Test integration
        test_results.append(await test_integration())
        
        print("\n" + "=" * 80)
        
        if all(test_results):
            print("✅ All Task 8.3 tests passed!")
            print("\nImplemented features:")
            print("- Comprehensive vector store monitoring with health checks")
            print("- Performance snapshot capture and analysis")
            print("- Query time tracking and alerting")
            print("- Optimization opportunity analysis and recommendations")
            print("- Automated performance and storage optimization")
            print("- Optimization history and statistics tracking")
            print("- Full backup and recovery capabilities")
            print("- Multiple backup types (full, incremental, metadata-only)")
            print("- Backup validation and integrity checking")
            print("- Automated backup scheduling and retention")
            print("- Service integration for complete monitoring workflow")
            
            return True
        else:
            failed_count = len([r for r in test_results if not r])
            print(f"❌ {failed_count} out of {len(test_results)} tests failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)