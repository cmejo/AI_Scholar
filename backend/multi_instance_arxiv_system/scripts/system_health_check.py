#!/usr/bin/env python3
"""
System Health Check for Multi-Instance ArXiv System

This script provides comprehensive health validation including system resources,
service availability, configuration validation, and dependency checks.
"""

import sys
import os
import argparse
import asyncio
import json
import psutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import importlib.util

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.core.instance_config import InstanceConfigManager
    from multi_instance_arxiv_system.monitoring.storage_monitor import StorageMonitor
    from multi_instance_arxiv_system.monitoring.performance_monitor import PerformanceMonitor
    from multi_instance_arxiv_system.error_handling.error_manager import ErrorManager
    from multi_instance_arxiv_system.reporting.email_notification_service import EmailNotificationService
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure the multi-instance ArXiv system is properly installed.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system_health_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HealthCheckStatus:
    """Health check status constants."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    ERROR = "error"


class SystemHealthChecker:
    """Comprehensive system health checker for multi-instance ArXiv system."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_manager = InstanceConfigManager(config_dir)
        self.storage_monitor = StorageMonitor()
        self.performance_monitor = PerformanceMonitor()
        self.error_manager = ErrorManager()
        self.email_service = EmailNotificationService()
        
        # Load instance configurations
        self.instances = self.config_manager.get_all_instances()
        
        logger.info(f"SystemHealthChecker initialized with {len(self.instances)} instances")
    
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check across all system components."""
        logger.info("Starting comprehensive system health check")
        
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': HealthCheckStatus.HEALTHY,
            'checks': {
                'system_resources': {},
                'dependencies': {},
                'configurations': {},
                'services': {},
                'instances': {},
                'storage': {},
                'network': {},
                'security': {}
            },
            'summary': {
                'total_checks': 0,
                'passed_checks': 0,
                'warning_checks': 0,
                'failed_checks': 0
            },
            'recommendations': [],
            'critical_issues': []
        }
        
        # Run all health checks
        await self._check_system_resources(health_report)
        await self._check_dependencies(health_report)
        await self._check_configurations(health_report)
        await self._check_services(health_report)
        await self._check_instances(health_report)
        await self._check_storage_health(health_report)
        await self._check_network_connectivity(health_report)
        await self._check_security_settings(health_report)
        
        # Calculate summary and overall status
        self._calculate_health_summary(health_report)
        
        logger.info(f"Health check completed. Overall status: {health_report['overall_status']}")
        return health_report