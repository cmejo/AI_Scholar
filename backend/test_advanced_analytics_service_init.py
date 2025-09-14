#!/usr/bin/env python3
"""
Test script for Advanced Analytics Service initialization
"""
import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.service_manager import ServiceManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_advanced_analytics_service_initialization():
    """Test advanced analytics service initialization"""
    logger.info("Testing Advanced Analytics Service initialization...")
    
    # Create service manager
    service_manager = ServiceManager()
    
    try:
        # Test database service initialization first (dependency)
        logger.info("Initializing database service (dependency)...")
        db_success = await service_manager.initialize_database_service()
        logger.info(f"Database service initialization: {'SUCCESS' if db_success else 'FAILED'}")
        
        # Test advanced analytics service initialization
        logger.info("Initializing advanced analytics service...")
        success = await service_manager.initialize_advanced_analytics_service()
        
        if success:
            logger.info("✅ Advanced analytics service initialization: SUCCESS")
            
            # Test service retrieval
            service = service_manager.get_service("advanced_analytics")
            if service:
                logger.info("✅ Service retrieval: SUCCESS")
                
                # Test service health check
                try:
                    health = await service_manager.check_service_health("advanced_analytics")
                    logger.info(f"✅ Service health check: {health.status.value}")
                    
                    # Test service methods
                    if hasattr(service, 'get_status'):
                        status = service.get_status()
                        logger.info(f"✅ Service status: {status}")
                    
                    if hasattr(service, 'health_check'):
                        health_result = await service.health_check()
                        logger.info(f"✅ Service health check result: {health_result}")
                    
                    # Test analytics methods (should work for both real and mock service)
                    if hasattr(service, 'analyze_user_behavior_patterns'):
                        patterns = service.analyze_user_behavior_patterns(days=7)
                        logger.info(f"✅ User behavior patterns test: {len(patterns) if patterns else 0} patterns")
                    
                    if hasattr(service, 'generate_business_intelligence_report'):
                        report = service.generate_business_intelligence_report(report_type="performance", days=7)
                        logger.info(f"✅ Business intelligence report test: {report.get('report_type', 'unknown')}")
                    
                    if hasattr(service, 'get_predictive_insights'):
                        insights = service.get_predictive_insights(days=7)
                        logger.info(f"✅ Predictive insights test: {insights.get('usage_trend', 'unknown')}")
                    
                except Exception as e:
                    logger.error(f"❌ Service method testing failed: {e}")
                
            else:
                logger.error("❌ Service retrieval: FAILED")
        else:
            logger.error("❌ Advanced analytics service initialization: FAILED")
        
        # Get service health summary
        health_summary = service_manager.get_service_health()
        logger.info(f"Service health summary: {health_summary}")
        
        # Get initialization summary
        init_summary = service_manager.get_initialization_summary()
        logger.info(f"Initialization summary: {init_summary}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}", exc_info=True)
        return False

async def main():
    """Main test function"""
    logger.info("Starting Advanced Analytics Service initialization test...")
    
    success = await test_advanced_analytics_service_initialization()
    
    if success:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error("💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)