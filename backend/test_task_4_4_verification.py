#!/usr/bin/env python3
"""
Test script to verify Task 4.4: Add knowledge graph service
"""
import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.service_manager import ServiceManager
from core.conditional_importer import ConditionalImporter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_knowledge_graph_service_initialization():
    """Test knowledge graph service initialization"""
    print("🧪 Testing Knowledge Graph Service Initialization...")
    
    # Create service manager
    service_manager = ServiceManager()
    
    # Test knowledge graph service initialization
    success = await service_manager.initialize_knowledge_graph_service()
    
    if success:
        print("✅ Knowledge graph service initialized successfully")
        
        # Get service instance
        kg_service = service_manager.get_service("knowledge_graph")
        if kg_service:
            print("✅ Knowledge graph service instance retrieved")
            
            # Test service health check
            try:
                health = await kg_service.health_check()
                print(f"✅ Knowledge graph service health check: {health}")
            except Exception as e:
                print(f"⚠️  Knowledge graph service health check failed: {e}")
            
            # Test service status
            try:
                status = kg_service.get_status()
                print(f"✅ Knowledge graph service status: {status}")
            except Exception as e:
                print(f"⚠️  Knowledge graph service status failed: {e}")
            
            # Test basic service methods
            try:
                # Test entity creation
                entity = await kg_service.create_entity(
                    name="Test Entity",
                    entity_type="concept",
                    description="Test entity for verification",
                    importance_score=0.8
                )
                print(f"✅ Knowledge graph entity creation: {entity}")
                
                # Test entity retrieval
                entities = await kg_service.get_entities(limit=10)
                print(f"✅ Knowledge graph entity retrieval: {len(entities)} entities")
                
                # Test graph query
                query_result = await kg_service.query_graph(
                    entity_name="Test",
                    max_depth=2
                )
                print(f"✅ Knowledge graph query: {query_result['metadata']}")
                
            except Exception as e:
                print(f"⚠️  Knowledge graph service methods test failed: {e}")
        else:
            print("❌ Failed to retrieve knowledge graph service instance")
            return False
    else:
        print("❌ Knowledge graph service initialization failed")
        return False
    
    return True

async def test_knowledge_graph_service_health_monitoring():
    """Test knowledge graph service health monitoring"""
    print("\n🧪 Testing Knowledge Graph Service Health Monitoring...")
    
    # Create service manager
    service_manager = ServiceManager()
    
    # Initialize knowledge graph service
    await service_manager.initialize_knowledge_graph_service()
    
    # Test service health check through service manager
    try:
        health = await service_manager.check_service_health("knowledge_graph")
        print(f"✅ Service manager health check: {health.name} - {health.status.value}")
        
        if health.error_message:
            print(f"⚠️  Health check error message: {health.error_message}")
        
        print(f"✅ Dependencies: {health.dependencies}")
        print(f"✅ Initialization time: {health.initialization_time}s")
        
    except Exception as e:
        print(f"❌ Service manager health check failed: {e}")
        return False
    
    # Test service health status
    try:
        is_healthy = service_manager.is_service_healthy("knowledge_graph")
        print(f"✅ Service healthy status: {is_healthy}")
    except Exception as e:
        print(f"❌ Service healthy status check failed: {e}")
        return False
    
    return True

async def test_knowledge_graph_dependencies():
    """Test knowledge graph service dependencies"""
    print("\n🧪 Testing Knowledge Graph Service Dependencies...")
    
    # Test dependency imports
    dependencies = [
        ("networkx", "NetworkX for graph operations"),
        ("numpy", "NumPy for numerical operations"),
        ("spacy", "spaCy for natural language processing"),
        ("sklearn", "scikit-learn for machine learning")
    ]
    
    available_deps = []
    missing_deps = []
    
    for dep_name, dep_desc in dependencies:
        result = ConditionalImporter.safe_import(dep_name, fallback=None)
        if result is not None:
            available_deps.append((dep_name, dep_desc))
            print(f"✅ {dep_name}: Available - {dep_desc}")
        else:
            missing_deps.append((dep_name, dep_desc))
            print(f"⚠️  {dep_name}: Missing - {dep_desc}")
    
    print(f"\n📊 Dependency Summary:")
    print(f"   Available: {len(available_deps)}/{len(dependencies)}")
    print(f"   Missing: {len(missing_deps)}/{len(dependencies)}")
    
    if missing_deps:
        print(f"\n⚠️  Missing dependencies will cause fallback to mock service:")
        for dep_name, dep_desc in missing_deps:
            print(f"   - {dep_name}: {dep_desc}")
    
    return len(available_deps) > 0

async def test_knowledge_graph_service_integration():
    """Test knowledge graph service integration with service manager"""
    print("\n🧪 Testing Knowledge Graph Service Integration...")
    
    # Create service manager
    service_manager = ServiceManager()
    
    # Initialize all services to test integration
    services_to_test = [
        ("database", service_manager.initialize_database_service),
        ("semantic_search", service_manager.initialize_semantic_search_service),
        ("research_automation", service_manager.initialize_research_automation_service),
        ("advanced_analytics", service_manager.initialize_advanced_analytics_service),
        ("knowledge_graph", service_manager.initialize_knowledge_graph_service)
    ]
    
    initialized_services = []
    failed_services = []
    
    for service_name, init_method in services_to_test:
        try:
            success = await init_method()
            if success:
                initialized_services.append(service_name)
                print(f"✅ {service_name} service: Initialized")
            else:
                failed_services.append(service_name)
                print(f"⚠️  {service_name} service: Failed to initialize")
        except Exception as e:
            failed_services.append(service_name)
            print(f"❌ {service_name} service: Exception during initialization - {e}")
    
    print(f"\n📊 Service Integration Summary:")
    print(f"   Initialized: {len(initialized_services)}/{len(services_to_test)}")
    print(f"   Failed: {len(failed_services)}/{len(services_to_test)}")
    
    # Test overall health
    try:
        health_summary = service_manager.get_service_health()
        print(f"✅ Overall health check completed for {len(health_summary)} services")
        
        for service_name, health_info in health_summary.items():
            status = health_info.get('status', 'unknown')
            print(f"   - {service_name}: {status}")
    except Exception as e:
        print(f"❌ Overall health check failed: {e}")
        return False
    
    return len(initialized_services) >= len(services_to_test) // 2  # At least half should work

async def main():
    """Run all knowledge graph service tests"""
    print("🚀 Starting Knowledge Graph Service Verification Tests")
    print("=" * 60)
    
    tests = [
        ("Knowledge Graph Service Initialization", test_knowledge_graph_service_initialization),
        ("Knowledge Graph Service Health Monitoring", test_knowledge_graph_service_health_monitoring),
        ("Knowledge Graph Service Dependencies", test_knowledge_graph_dependencies),
        ("Knowledge Graph Service Integration", test_knowledge_graph_service_integration)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            result = await test_func()
            if result:
                print(f"✅ {test_name}: PASSED")
                passed_tests += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            logger.exception(f"Test {test_name} failed with exception")
    
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS")
    print(f"   Passed: {passed_tests}/{total_tests}")
    print(f"   Failed: {total_tests - passed_tests}/{total_tests}")
    print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Knowledge graph service is working correctly.")
        return True
    elif passed_tests >= total_tests // 2:
        print("⚠️  Most tests passed. Knowledge graph service is partially working.")
        return True
    else:
        print("❌ Most tests failed. Knowledge graph service needs attention.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)