#!/usr/bin/env python3
"""
Verification test for Task 4.2: Add research automation service

This test verifies that all requirements for task 4.2 are met:
- Implement conditional import of research_automation service
- Create service wrapper with graceful error handling
- Add research automation health check and status monitoring
"""
import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_conditional_import():
    """Verify conditional import of research_automation service"""
    logger.info("=== Verifying Conditional Import ===")
    
    try:
        # Test that the service manager can handle missing dependencies gracefully
        from core.service_manager import service_manager
        
        # The service should initialize even if dependencies are missing
        success = await service_manager.initialize_research_automation_service()
        
        if success:
            logger.info("✓ Conditional import working - service initialized despite missing dependencies")
            return True
        else:
            logger.error("✗ Conditional import failed - service could not initialize")
            return False
            
    except Exception as e:
        logger.error(f"✗ Conditional import test failed: {e}")
        return False

async def verify_service_wrapper():
    """Verify service wrapper with graceful error handling"""
    logger.info("=== Verifying Service Wrapper ===")
    
    try:
        from core.service_manager import service_manager
        
        # Get the service instance
        service = service_manager.get_service("research_automation")
        
        if not service:
            logger.error("✗ Service wrapper test failed - no service instance")
            return False
        
        # Test that the service has proper error handling
        logger.info("Testing service wrapper methods...")
        
        # Test health check method
        health_result = await service.health_check()
        if health_result and "status" in health_result:
            logger.info("✓ Service wrapper health check method working")
        else:
            logger.error("✗ Service wrapper health check method failed")
            return False
        
        # Test get_status method
        status = service.get_status()
        if status and "status" in status:
            logger.info("✓ Service wrapper get_status method working")
        else:
            logger.error("✗ Service wrapper get_status method failed")
            return False
        
        # Test workflow methods with error handling
        try:
            workflow = await service.create_automated_workflow(
                user_id="test",
                name="test",
                workflow_type="test",
                description="test",
                configuration={},
                schedule_config={}
            )
            if workflow:
                logger.info("✓ Service wrapper workflow methods working")
            else:
                logger.error("✗ Service wrapper workflow methods failed")
                return False
        except Exception as e:
            logger.error(f"✗ Service wrapper workflow methods failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Service wrapper test failed: {e}")
        return False

async def verify_health_check_monitoring():
    """Verify research automation health check and status monitoring"""
    logger.info("=== Verifying Health Check and Status Monitoring ===")
    
    try:
        from core.service_manager import service_manager
        
        # Test service manager health check
        health = await service_manager.check_service_health("research_automation")
        
        if health and health.name == "research_automation":
            logger.info(f"✓ Service manager health check working - status: {health.status.value}")
        else:
            logger.error("✗ Service manager health check failed")
            return False
        
        # Test health status tracking
        health_info = service_manager.get_service_health("research_automation")
        
        if health_info and "status" in health_info:
            logger.info(f"✓ Health status tracking working - status: {health_info['status']}")
        else:
            logger.error("✗ Health status tracking failed")
            return False
        
        # Test initialization summary includes research automation
        summary = service_manager.get_initialization_summary()
        
        if "research_automation" in summary.get("initialization_order", []):
            logger.info("✓ Service included in initialization summary")
        else:
            logger.error("✗ Service not found in initialization summary")
            return False
        
        # Test health monitoring status
        monitoring_status = service_manager.get_health_monitoring_status()
        
        if monitoring_status and "monitoring_enabled" in monitoring_status:
            logger.info("✓ Health monitoring status available")
        else:
            logger.error("✗ Health monitoring status failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Health check and monitoring test failed: {e}")
        return False

async def verify_requirements_coverage():
    """Verify that all requirements are covered"""
    logger.info("=== Verifying Requirements Coverage ===")
    
    try:
        # Requirement 1.1: Service import restoration
        logger.info("Checking Requirement 1.1: Service import restoration")
        from core.service_manager import service_manager
        service = service_manager.get_service("research_automation")
        if service:
            logger.info("✓ Requirement 1.1: Service successfully imported and available")
        else:
            logger.error("✗ Requirement 1.1: Service not available")
            return False
        
        # Requirement 1.2: Clear error messages
        logger.info("Checking Requirement 1.2: Clear error messages")
        # The service should provide clear status messages
        status = service.get_status()
        if status and "message" in status:
            logger.info(f"✓ Requirement 1.2: Clear status messages available: {status['message']}")
        else:
            logger.error("✗ Requirement 1.2: No clear status messages")
            return False
        
        # Requirement 1.4: Service availability
        logger.info("Checking Requirement 1.4: Service availability")
        health = await service_manager.check_service_health("research_automation")
        if health and health.status.value in ["healthy", "degraded"]:
            logger.info(f"✓ Requirement 1.4: Service is available with status: {health.status.value}")
        else:
            logger.error("✗ Requirement 1.4: Service not available")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Requirements coverage test failed: {e}")
        return False

async def main():
    """Main verification function"""
    logger.info("Starting Task 4.2 Verification: Add research automation service")
    logger.info("=" * 60)
    
    # Run all verification tests
    tests = [
        ("Conditional Import", verify_conditional_import),
        ("Service Wrapper", verify_service_wrapper),
        ("Health Check & Monitoring", verify_health_check_monitoring),
        ("Requirements Coverage", verify_requirements_coverage)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning {test_name} verification...")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✓ {test_name} verification PASSED")
            else:
                logger.error(f"✗ {test_name} verification FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} verification ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TASK 4.2 VERIFICATION SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✓ Task 4.2 COMPLETED SUCCESSFULLY")
        logger.info("All requirements have been implemented:")
        logger.info("- ✓ Conditional import of research_automation service")
        logger.info("- ✓ Service wrapper with graceful error handling")
        logger.info("- ✓ Research automation health check and status monitoring")
        return 0
    else:
        logger.error("✗ Task 4.2 INCOMPLETE")
        logger.error(f"{total - passed} verification tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)