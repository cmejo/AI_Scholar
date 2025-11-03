#!/usr/bin/env python3
"""
Multi-Instance ArXiv System Monitor

This script provides comprehensive monitoring for the multi-instance ArXiv system,
including health checks, performance monitoring, and status reporting.
"""

import sys
import os
import argparse
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

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
        logging.FileHandler('logs/multi_instance_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SystemMonitor:
    """Comprehensive system monitor for multi-instance ArXiv system."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_manager = InstanceConfigManager(config_dir)
        self.storage_monitor = StorageMonitor()
        self.performance_monitor = PerformanceMonitor()
        self.error_manager = ErrorManager()
        self.email_service = EmailNotificationService()
        
        # Load instance configurations
        self.instances = self.config_manager.get_all_instances()
        
        logger.info(f"SystemMonitor initialized with {len(self.instances)} instances")
    
    async def run_health_check(self, instance_name: Optional[str] = None) -> Dict[str, Any]:
        """Run comprehensive health check."""
        logger.info("Starting system health check")
        
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'instances': {},
            'system_metrics': {},
            'alerts': []
        }
        
        # Check specific instance or all instances
        instances_to_check = [instance_name] if instance_name else list(self.instances.keys())
        
        for instance in instances_to_check:
            if instance not in self.instances:
                logger.warning(f"Instance {instance} not found")
                continue
            
            instance_health = await self._check_instance_health(instance)
            health_report['instances'][instance] = instance_health
            
            if instance_health['status'] != 'healthy':
                health_report['overall_status'] = 'degraded'
        
        # Check system-wide metrics
        health_report['system_metrics'] = await self._check_system_metrics()
        
        # Generate alerts if needed
        health_report['alerts'] = self._generate_alerts(health_report)
        
        logger.info(f"Health check completed. Status: {health_report['overall_status']}")
        return health_report  
  
    async def _check_instance_health(self, instance_name: str) -> Dict[str, Any]:
        """Check health of a specific instance."""
        logger.info(f"Checking health for instance: {instance_name}")
        
        config = self.instances[instance_name]
        health = {
            'status': 'healthy',
            'checks': {},
            'metrics': {},
            'last_activity': None,
            'issues': []
        }
        
        try:
            # Check storage health
            storage_health = await self._check_storage_health(config)
            health['checks']['storage'] = storage_health
            
            # Check vector store health
            vector_health = await self._check_vector_store_health(instance_name)
            health['checks']['vector_store'] = vector_health
            
            # Check recent activity
            activity_health = await self._check_recent_activity(config)
            health['checks']['activity'] = activity_health
            health['last_activity'] = activity_health.get('last_update')
            
            # Check error rates
            error_health = await self._check_error_rates(instance_name)
            health['checks']['errors'] = error_health
            
            # Determine overall instance status
            failed_checks = [name for name, check in health['checks'].items() 
                           if check.get('status') != 'healthy']
            
            if failed_checks:
                health['status'] = 'degraded' if len(failed_checks) < 3 else 'unhealthy'
                health['issues'] = [f"{check} check failed" for check in failed_checks]
        
        except Exception as e:
            logger.error(f"Error checking instance {instance_name}: {e}")
            health['status'] = 'error'
            health['issues'] = [f"Health check failed: {str(e)}"]
        
        return health
    
    async def _check_storage_health(self, config) -> Dict[str, Any]:
        """Check storage health for an instance."""
        try:
            storage_stats = await self.storage_monitor.get_storage_stats(config.storage_path)
            
            # Check disk usage
            usage_percent = storage_stats.get('usage_percent', 0)
            free_space_gb = storage_stats.get('free_space_gb', 0)
            
            status = 'healthy'
            issues = []
            
            if usage_percent > 90:
                status = 'critical'
                issues.append(f"Disk usage critical: {usage_percent}%")
            elif usage_percent > 80:
                status = 'warning'
                issues.append(f"Disk usage high: {usage_percent}%")
            
            if free_space_gb < 1:
                status = 'critical'
                issues.append(f"Low free space: {free_space_gb}GB")
            
            return {
                'status': status,
                'usage_percent': usage_percent,
                'free_space_gb': free_space_gb,
                'issues': issues
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'issues': ['Storage check failed']
            }
    
    async def _check_vector_store_health(self, instance_name: str) -> Dict[str, Any]:
        """Check vector store health for an instance."""
        try:
            # This would integrate with the vector store service
            # For now, we'll do basic checks
            
            collection_name = f"{instance_name}_papers"
            
            # Check if collection exists and has documents
            # This is a placeholder - actual implementation would use ChromaDB client
            status = 'healthy'
            document_count = 0  # Would be retrieved from actual vector store
            
            return {
                'status': status,
                'collection_name': collection_name,
                'document_count': document_count,
                'issues': []
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'issues': ['Vector store check failed']
            }
    
    async def _check_recent_activity(self, config) -> Dict[str, Any]:
        """Check recent activity for an instance."""
        try:
            # Check for recent log files or update markers
            log_dir = Path(config.storage_path) / "logs"
            
            if not log_dir.exists():
                return {
                    'status': 'warning',
                    'last_update': None,
                    'issues': ['No log directory found']
                }
            
            # Find most recent log file
            log_files = list(log_dir.glob("*.log"))
            if not log_files:
                return {
                    'status': 'warning',
                    'last_update': None,
                    'issues': ['No log files found']
                }
            
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            last_modified = datetime.fromtimestamp(latest_log.stat().st_mtime)
            
            # Check if activity is recent (within last 7 days)
            days_since_activity = (datetime.now() - last_modified).days
            
            status = 'healthy'
            issues = []
            
            if days_since_activity > 30:
                status = 'warning'
                issues.append(f"No activity for {days_since_activity} days")
            
            return {
                'status': status,
                'last_update': last_modified.isoformat(),
                'days_since_activity': days_since_activity,
                'issues': issues
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'issues': ['Activity check failed']
            }
    
    async def _check_error_rates(self, instance_name: str) -> Dict[str, Any]:
        """Check error rates for an instance."""
        try:
            # Get recent errors from error manager
            recent_errors = await self.error_manager.get_recent_errors(
                instance_name, 
                hours=24
            )
            
            error_count = len(recent_errors)
            critical_errors = len([e for e in recent_errors if e.severity == 'critical'])
            
            status = 'healthy'
            issues = []
            
            if critical_errors > 0:
                status = 'critical'
                issues.append(f"{critical_errors} critical errors in last 24h")
            elif error_count > 50:
                status = 'warning'
                issues.append(f"High error rate: {error_count} errors in last 24h")
            
            return {
                'status': status,
                'error_count_24h': error_count,
                'critical_errors_24h': critical_errors,
                'issues': issues
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'issues': ['Error rate check failed']
            } 
   
    async def _check_system_metrics(self) -> Dict[str, Any]:
        """Check system-wide metrics."""
        try:
            metrics = await self.performance_monitor.get_system_metrics()
            
            return {
                'cpu_usage': metrics.get('cpu_usage', 0),
                'memory_usage': metrics.get('memory_usage', 0),
                'disk_io': metrics.get('disk_io', {}),
                'network_io': metrics.get('network_io', {}),
                'load_average': metrics.get('load_average', [])
            }
        
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {'error': str(e)}
    
    def _generate_alerts(self, health_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on health report."""
        alerts = []
        
        # Check for unhealthy instances
        for instance_name, instance_health in health_report['instances'].items():
            if instance_health['status'] in ['unhealthy', 'error']:
                alerts.append({
                    'level': 'critical',
                    'type': 'instance_health',
                    'instance': instance_name,
                    'message': f"Instance {instance_name} is {instance_health['status']}",
                    'issues': instance_health.get('issues', [])
                })
            elif instance_health['status'] == 'degraded':
                alerts.append({
                    'level': 'warning',
                    'type': 'instance_health',
                    'instance': instance_name,
                    'message': f"Instance {instance_name} is degraded",
                    'issues': instance_health.get('issues', [])
                })
        
        # Check system metrics
        system_metrics = health_report.get('system_metrics', {})
        
        if system_metrics.get('cpu_usage', 0) > 90:
            alerts.append({
                'level': 'warning',
                'type': 'system_resource',
                'message': f"High CPU usage: {system_metrics['cpu_usage']}%"
            })
        
        if system_metrics.get('memory_usage', 0) > 90:
            alerts.append({
                'level': 'warning',
                'type': 'system_resource',
                'message': f"High memory usage: {system_metrics['memory_usage']}%"
            })
        
        return alerts
    
    async def generate_status_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive status report."""
        logger.info("Generating status report")
        
        health_report = await self.run_health_check()
        
        # Add additional statistics
        report = {
            'system_status': health_report,
            'instance_statistics': {},
            'recommendations': []
        }
        
        # Get statistics for each instance
        for instance_name in self.instances.keys():
            try:
                stats = await self._get_instance_statistics(instance_name)
                report['instance_statistics'][instance_name] = stats
            except Exception as e:
                logger.error(f"Error getting statistics for {instance_name}: {e}")
                report['instance_statistics'][instance_name] = {'error': str(e)}
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(report)
        
        # Save report if output file specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Status report saved to {output_file}")
        
        return json.dumps(report, indent=2, default=str)
    
    async def _get_instance_statistics(self, instance_name: str) -> Dict[str, Any]:
        """Get statistics for a specific instance."""
        config = self.instances[instance_name]
        
        stats = {
            'storage_usage': {},
            'processing_stats': {},
            'error_summary': {}
        }
        
        try:
            # Storage statistics
            storage_stats = await self.storage_monitor.get_storage_stats(config.storage_path)
            stats['storage_usage'] = storage_stats
            
            # Processing statistics (would be retrieved from actual processing logs)
            stats['processing_stats'] = {
                'papers_processed_today': 0,  # Placeholder
                'papers_processed_this_month': 0,  # Placeholder
                'average_processing_time': 0,  # Placeholder
                'last_successful_run': None  # Placeholder
            }
            
            # Error summary
            recent_errors = await self.error_manager.get_recent_errors(instance_name, hours=24)
            stats['error_summary'] = {
                'total_errors_24h': len(recent_errors),
                'critical_errors_24h': len([e for e in recent_errors if e.severity == 'critical']),
                'most_common_error': None  # Would be calculated from actual errors
            }
        
        except Exception as e:
            stats['error'] = str(e)
        
        return stats
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on system status."""
        recommendations = []
        
        # Check for storage issues
        for instance_name, instance_health in report['system_status']['instances'].items():
            storage_check = instance_health.get('checks', {}).get('storage', {})
            
            if storage_check.get('usage_percent', 0) > 80:
                recommendations.append(
                    f"Consider cleaning up storage for {instance_name} "
                    f"(usage: {storage_check['usage_percent']}%)"
                )
            
            if storage_check.get('free_space_gb', 0) < 5:
                recommendations.append(
                    f"Urgent: Add more storage for {instance_name} "
                    f"(free space: {storage_check['free_space_gb']}GB)"
                )
        
        # Check for error patterns
        for instance_name, stats in report['instance_statistics'].items():
            error_summary = stats.get('error_summary', {})
            
            if error_summary.get('critical_errors_24h', 0) > 0:
                recommendations.append(
                    f"Investigate critical errors in {instance_name} "
                    f"({error_summary['critical_errors_24h']} in last 24h)"
                )
            
            if error_summary.get('total_errors_24h', 0) > 50:
                recommendations.append(
                    f"High error rate in {instance_name} - review error logs "
                    f"({error_summary['total_errors_24h']} errors in last 24h)"
                )
        
        # System resource recommendations
        system_metrics = report['system_status'].get('system_metrics', {})
        
        if system_metrics.get('cpu_usage', 0) > 80:
            recommendations.append(
                "Consider reducing concurrent processing or upgrading CPU resources"
            )
        
        if system_metrics.get('memory_usage', 0) > 80:
            recommendations.append(
                "Consider increasing memory allocation or optimizing memory usage"
            )
        
        return recommendations    
 
   async def send_alert_notifications(self, health_report: Dict[str, Any]) -> bool:
        """Send alert notifications if critical issues are found."""
        alerts = health_report.get('alerts', [])
        critical_alerts = [a for a in alerts if a['level'] == 'critical']
        
        if not critical_alerts:
            return True
        
        try:
            # Prepare alert email
            subject = f"CRITICAL: Multi-Instance ArXiv System Alert"
            
            alert_summary = "\n".join([
                f"- {alert['message']}" for alert in critical_alerts
            ])
            
            message = f"""
Critical issues detected in the Multi-Instance ArXiv System:

{alert_summary}

Please investigate immediately.

Full health report:
{json.dumps(health_report, indent=2, default=str)}
            """
            
            # Send notification
            success = await self.email_service.send_notification(
                subject=subject,
                message=message,
                priority='critical'
            )
            
            if success:
                logger.info(f"Alert notification sent for {len(critical_alerts)} critical issues")
            else:
                logger.error("Failed to send alert notification")
            
            return success
        
        except Exception as e:
            logger.error(f"Error sending alert notification: {e}")
            return False


async def main():
    """Main entry point for the monitor script."""
    parser = argparse.ArgumentParser(description="Multi-Instance ArXiv System Monitor")
    
    parser.add_argument(
        '--config-dir',
        default='config',
        help='Configuration directory path'
    )
    
    parser.add_argument(
        '--instance',
        help='Monitor specific instance only'
    )
    
    parser.add_argument(
        '--output',
        help='Output file for status report'
    )
    
    parser.add_argument(
        '--send-alerts',
        action='store_true',
        help='Send email alerts for critical issues'
    )
    
    parser.add_argument(
        '--continuous',
        type=int,
        metavar='MINUTES',
        help='Run continuously, checking every N minutes'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        monitor = SystemMonitor(args.config_dir)
        
        if args.continuous:
            logger.info(f"Starting continuous monitoring (every {args.continuous} minutes)")
            
            while True:
                try:
                    # Run health check
                    health_report = await monitor.run_health_check(args.instance)
                    
                    # Generate status report
                    if args.output:
                        await monitor.generate_status_report(args.output)
                    
                    # Send alerts if enabled
                    if args.send_alerts:
                        await monitor.send_alert_notifications(health_report)
                    
                    # Print summary
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                          f"System status: {health_report['overall_status']}")
                    
                    if health_report['alerts']:
                        print(f"  Alerts: {len(health_report['alerts'])}")
                        for alert in health_report['alerts']:
                            print(f"    {alert['level'].upper()}: {alert['message']}")
                    
                    # Wait for next check
                    await asyncio.sleep(args.continuous * 60)
                
                except KeyboardInterrupt:
                    logger.info("Monitoring stopped by user")
                    break
                except Exception as e:
                    logger.error(f"Error in continuous monitoring: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute before retrying
        
        else:
            # Single run
            logger.info("Running single health check")
            
            health_report = await monitor.run_health_check(args.instance)
            
            # Generate and display status report
            status_report = await monitor.generate_status_report(args.output)
            
            if not args.output:
                print(status_report)
            
            # Send alerts if enabled
            if args.send_alerts:
                await monitor.send_alert_notifications(health_report)
            
            # Exit with appropriate code
            if health_report['overall_status'] == 'healthy':
                sys.exit(0)
            elif health_report['overall_status'] == 'degraded':
                sys.exit(1)
            else:
                sys.exit(2)
    
    except Exception as e:
        logger.error(f"Monitor failed: {e}")
        sys.exit(3)


if __name__ == "__main__":
    asyncio.run(main())