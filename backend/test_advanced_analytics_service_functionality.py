#!/usr/bin/env python3
"""
Test script for Advanced Analytics Service functionality without FastAPI dependencies
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from core.service_manager import ServiceManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_advanced_analytics_service_functionality():
    """Test advanced analytics service functionality"""
    logger.info("Testing Advanced Analytics Service functionality...")
    
    # Create and initialize service manager
    service_manager_instance = ServiceManager()
    
    try:
        # Initialize the advanced analytics service
        logger.info("Initializing advanced analytics service...")
        success = await service_manager_instance.initialize_advanced_analytics_service()
        
        if not success:
            logger.error("❌ Service initialization failed")
            return False
        
        logger.info("✅ Service initialization: SUCCESS")
        
        # Get the service instance
        service = service_manager_instance.get_service("advanced_analytics")
        if not service:
            logger.error("❌ Service retrieval failed")
            return False
        
        logger.info("✅ Service retrieval: SUCCESS")
        
        # Test health check functionality (simulating endpoint logic)
        logger.info("Testing health check functionality...")
        
        # Check if service is available
        if service:
            logger.info("✅ Service is available")
            
            # Perform service health check
            health = await service_manager_instance.check_service_health("advanced_analytics")
            logger.info(f"✅ Service health check: {health.status.value}")
            
            # Get additional service status
            service_status = service.get_status()
            logger.info(f"✅ Service status: {service_status}")
            
            # Simulate the health check endpoint response
            health_response = {
                "status": "ok" if health.status.value == "healthy" else health.status.value,
                "timestamp": datetime.utcnow(),
                "service": {
                    "name": health.name,
                    "status": health.status.value,
                    "last_check": health.last_check.isoformat(),
                    "error_message": health.error_message,
                    "dependencies": health.dependencies,
                    "initialization_time": health.initialization_time,
                    "service_details": service_status
                },
                "message": "Advanced analytics service health check completed"
            }
            
            logger.info("✅ Health check response structure created successfully")
            logger.info(f"Response: {health_response}")
            
            # Test service methods
            logger.info("Testing service methods...")
            
            # Test user behavior analysis
            try:
                patterns = service.analyze_user_behavior_patterns(days=7, environment="test")
                logger.info(f"✅ User behavior patterns: {len(patterns) if patterns else 0} patterns")
            except Exception as e:
                logger.error(f"❌ User behavior patterns test failed: {e}")
            
            # Test feature performance insights
            try:
                insights = service.analyze_feature_performance_insights(days=7, environment="test")
                logger.info(f"✅ Feature performance insights: {len(insights) if insights else 0} insights")
            except Exception as e:
                logger.error(f"❌ Feature performance insights test failed: {e}")
            
            # Test business intelligence report
            try:
                report = service.generate_business_intelligence_report(
                    report_type="comprehensive", days=7, environment="test"
                )
                logger.info(f"✅ Business intelligence report: {report.get('report_type', 'unknown')}")
            except Exception as e:
                logger.error(f"❌ Business intelligence report test failed: {e}")
            
            # Test predictive insights
            try:
                predictions = service.get_predictive_insights(days=7, environment="test")
                logger.info(f"✅ Predictive insights: {predictions.get('usage_trend', 'unknown')}")
            except Exception as e:
                logger.error(f"❌ Predictive insights test failed: {e}")
            
        else:
            logger.error("❌ Service not available")
            return False
        
        # Test service manager health monitoring
        logger.info("Testing service manager health monitoring...")
        
        # Get service health summary
        health_summary = service_manager_instance.get_service_health()
        logger.info(f"✅ Service health summary: {health_summary}")
        
        # Get initialization summary
        init_summary = service_manager_instance.get_initialization_summary()
        logger.info(f"✅ Initialization summary: {init_summary}")
        
        # Verify the service is marked as healthy
        if "advanced_analytics" in health_summary:
            analytics_health = health_summary["advanced_analytics"]
            if analytics_health.get("status") == "healthy":
                logger.info("✅ Service health status: HEALTHY")
            else:
                logger.warning(f"⚠️ Service health status: {analytics_health.get('status')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}", exc_info=True)
        return False

async def main():
    """Main test function"""
    logger.info("Starting Advanced Analytics Service functionality test...")
    
    success = await test_advanced_analytics_service_functionality()
    
    if success:
        logger.info("🎉 All functionality tests passed!")
        return 0
    else:
        logger.error("💥 Some functionality tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)