#!/usr/bin/env python3
"""
Multi-Instance ArXiv System - Comprehensive Health Check Automation

This script provides automated health checking for all system components including:
- System resources (CPU, memory, disk)
- ChromaDB database health
- Service status monitoring
- Application component validation
- Network connectivity checks
- Data integrity verification
"""

import sys
import os
import json
import time
import subprocess
import requests
import psutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add the backend directory to Python path
script_dir = Path(__file__).parent
project_root = script_dir.parent
backend_dir = project_root / 'backend'
sys.path.insert(0, str(backend_dir))


class SystemHealthChecker:
    """Comprehensive system health checker"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or '/opt/arxiv-system/config'
        self.results = {}
        self.start_time = datetime.now()
        
        # Setup logging
        log_dir = Path('/opt/arxiv-system/logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'health_check.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Health check thresholds
        self.thresholds = {
            'cpu_warning': 80.0,
            'cpu_critical': 90.0,
            'memory_warning': 80.0,
            'memory_critical': 90.0,
            'disk_warning': 80.0,
            'disk_critical': 90.0,
            'response_time_warning': 2000,  # ms
            'response_time_critical': 5000,  # ms
        }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource utilization"""
        self.logger.info("Checking system resources...")
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk_usage = psutil.disk_usage('/opt/arxiv-system')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Determine status levels
            cpu_status = self._get_status_level(cpu_percent, 'cpu')
            memory_status = self._get_status_level(memory.percent, 'memory')
            disk_status = self._get_status_level((disk_usage.used / disk_usage.total) * 100, 'disk')
            
            results = {
                'status': 'healthy',
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'load_average': load_avg,
                    'status': cpu_status
                },
                'memory': {
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'percent': memory.percent,
                    'status': memory_status,
                    'swap': {
                        'total_gb': swap.total / (1024**3),
                        'used_gb': swap.used / (1024**3),
                        'percent': swap.percent
                    }
                },
                'disk': {
                    'total_gb': disk_usage.total / (1024**3),
                    'used_gb': disk_usage.used / (1024**3),
                    'free_gb': disk_usage.free / (1024**3),
                    'percent': (disk_usage.used / disk_usage.total) * 100,
                    'status': disk_status
                },
                'network': {
                    'bytes_sent_mb': network.bytes_sent / (1024**2),
                    'bytes_recv_mb': network.bytes_recv / (1024**2),
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            }
            
            # Overall status
            if any(status == 'critical' for status in [cpu_status, memory_status, disk_status]):
                results['status'] = 'critical'
            elif any(status == 'warning' for status in [cpu_status, memory_status, disk_status]):
                results['status'] = 'warning'
            
            self.logger.info(f"System resources check completed - Status: {results['status']}")
            return results
            
        except Exception as e:
            self.logger.error(f"System resources check failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_chromadb_health(self) -> Dict[str, Any]:
        """Check ChromaDB database health"""
        self.logger.info("Checking ChromaDB health...")
        
        try:
            # Basic connectivity test
            start_time = time.time()
            response = requests.get('http://localhost:8000/api/v1/heartbeat', timeout=10)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if response.status_code != 200:
                return {
                    'status': 'critical',
                    'error': f'ChromaDB returned status code: {response.status_code}'
                }
            
            # Get collections information
            collections_response = requests.get('http://localhost:8000/api/v1/collections', timeout=10)
            collections = collections_response.json() if collections_response.status_code == 200 else []
            
            # Check collection health
            collection_stats = {}
            for collection in collections:
                collection_name = collection.get('name', 'unknown')
                try:
                    count_response = requests.get(
                        f'http://localhost:8000/api/v1/collections/{collection_name}/count',
                        timeout=10
                    )
                    count = count_response.json() if count_response.status_code == 200 else 0
                    collection_stats[collection_name] = {
                        'document_count': count,
                        'metadata': collection.get('metadata', {})
                    }
                except Exception as e:
                    collection_stats[collection_name] = {'error': str(e)}
            
            # Determine response time status
            response_status = self._get_status_level(response_time, 'response_time')
            
            results = {
                'status': 'healthy' if response_status == 'healthy' else response_status,
                'response_time_ms': response_time,
                'response_status': response_status,
                'collections': collection_stats,
                'total_collections': len(collections),
                'total_documents': sum(
                    stats.get('document_count', 0) 
                    for stats in collection_stats.values() 
                    if isinstance(stats.get('document_count'), int)
                )
            }
            
            self.logger.info(f"ChromaDB health check completed - Status: {results['status']}")
            return results
            
        except requests.exceptions.ConnectionError:
            self.logger.error("ChromaDB connection failed")
            return {
                'status': 'critical',
                'error': 'ChromaDB is not responding'
            }
        except Exception as e:
            self.logger.error(f"ChromaDB health check failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_service_status(self) -> Dict[str, Any]:
        """Check systemd service status"""
        self.logger.info("Checking service status...")
        
        services = [
            'chromadb.service',
            'arxiv-system-monitor.service'
        ]
        
        service_results = {}
        overall_status = 'healthy'
        
        for service in services:
            try:
                # Check if service is active
                result = subprocess.run(
                    ['systemctl', 'is-active', service],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                is_active = result.returncode == 0
                status = result.stdout.strip()
                
                # Get service details
                status_result = subprocess.run(
                    ['systemctl', 'status', service, '--no-pager', '-l'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                service_results[service] = {
                    'active': is_active,
                    'status': status,
                    'details': status_result.stdout if status_result.returncode == 0 else 'Status unavailable'
                }
                
                if not is_active:
                    overall_status = 'critical'
                    
            except subprocess.TimeoutExpired:
                service_results[service] = {
                    'active': False,
                    'status': 'timeout',
                    'error': 'Service check timed out'
                }
                overall_status = 'critical'
            except Exception as e:
                service_results[service] = {
                    'active': False,
                    'status': 'error',
                    'error': str(e)
                }
                overall_status = 'critical'
        
        results = {
            'status': overall_status,
            'services': service_results,
            'active_services': sum(1 for s in service_results.values() if s.get('active', False)),
            'total_services': len(services)
        }
        
        self.logger.info(f"Service status check completed - Status: {results['status']}")
        return results
    
    def check_docker_containers(self) -> Dict[str, Any]:
        """Check Docker container status"""
        self.logger.info("Checking Docker container status...")
        
        try:
            # Check if Docker is running
            docker_result = subprocess.run(
                ['docker', 'ps', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if docker_result.returncode != 0:
                return {
                    'status': 'critical',
                    'error': 'Docker is not running or accessible'
                }
            
            # Parse container information
            containers = []
            if docker_result.stdout.strip():
                for line in docker_result.stdout.strip().split('\n'):
                    try:
                        container = json.loads(line)
                        containers.append(container)
                    except json.JSONDecodeError:
                        continue
            
            # Check specific containers
            chromadb_container = None
            for container in containers:
                if 'chromadb' in container.get('Names', '').lower():
                    chromadb_container = container
                    break
            
            results = {
                'status': 'healthy',
                'docker_running': True,
                'total_containers': len(containers),
                'containers': containers,
                'chromadb_container': chromadb_container
            }
            
            if not chromadb_container:
                results['status'] = 'warning'
                results['warning'] = 'ChromaDB container not found'
            elif chromadb_container.get('State') != 'running':
                results['status'] = 'critical'
                results['error'] = f"ChromaDB container state: {chromadb_container.get('State')}"
            
            self.logger.info(f"Docker container check completed - Status: {results['status']}")
            return results
            
        except subprocess.TimeoutExpired:
            return {
                'status': 'critical',
                'error': 'Docker command timed out'
            }
        except Exception as e:
            self.logger.error(f"Docker container check failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_file_system_health(self) -> Dict[str, Any]:
        """Check file system health and permissions"""
        self.logger.info("Checking file system health...")
        
        try:
            critical_paths = [
                '/opt/arxiv-system',
                '/opt/arxiv-system/config',
                '/opt/arxiv-system/data',
                '/opt/arxiv-system/logs',
                '/opt/arxiv-system/.env'
            ]
            
            path_results = {}
            overall_status = 'healthy'
            
            for path in critical_paths:
                path_obj = Path(path)
                
                if not path_obj.exists():
                    path_results[path] = {
                        'exists': False,
                        'status': 'critical'
                    }
                    overall_status = 'critical'
                    continue
                
                # Check permissions
                stat_info = path_obj.stat()
                permissions = oct(stat_info.st_mode)[-3:]
                
                # Check ownership
                import pwd
                import grp
                try:
                    owner = pwd.getpwuid(stat_info.st_uid).pw_name
                    group = grp.getgrgid(stat_info.st_gid).gr_name
                except (KeyError, OSError):
                    owner = str(stat_info.st_uid)
                    group = str(stat_info.st_gid)
                
                path_results[path] = {
                    'exists': True,
                    'permissions': permissions,
                    'owner': owner,
                    'group': group,
                    'size_bytes': stat_info.st_size if path_obj.is_file() else None,
                    'status': 'healthy'
                }
                
                # Check for specific permission issues
                if path == '/opt/arxiv-system/.env' and permissions != '600':
                    path_results[path]['status'] = 'warning'
                    path_results[path]['warning'] = f'Insecure permissions: {permissions}'
                    if overall_status == 'healthy':
                        overall_status = 'warning'
            
            # Check disk space for each instance
            instance_stats = {}
            for instance in ['ai_scholar', 'quant_scholar']:
                instance_path = Path(f'/opt/arxiv-system/data/{instance}')
                if instance_path.exists():
                    # Count files and calculate sizes
                    papers_count = len(list((instance_path / 'papers').glob('*.pdf'))) if (instance_path / 'papers').exists() else 0
                    
                    # Calculate directory size
                    total_size = 0
                    try:
                        for file_path in instance_path.rglob('*'):
                            if file_path.is_file():
                                total_size += file_path.stat().st_size
                    except (OSError, PermissionError):
                        total_size = -1  # Indicate error
                    
                    instance_stats[instance] = {
                        'papers_count': papers_count,
                        'total_size_mb': total_size / (1024**2) if total_size >= 0 else None,
                        'status': 'healthy' if total_size >= 0 else 'warning'
                    }
            
            results = {
                'status': overall_status,
                'paths': path_results,
                'instances': instance_stats
            }
            
            self.logger.info(f"File system health check completed - Status: {results['status']}")
            return results
            
        except Exception as e:
            self.logger.error(f"File system health check failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity"""
        self.logger.info("Checking network connectivity...")
        
        try:
            test_urls = [
                ('arxiv.org', 'https://arxiv.org'),
                ('google.com', 'https://www.google.com'),
                ('github.com', 'https://github.com')
            ]
            
            connectivity_results = {}
            successful_connections = 0
            
            for name, url in test_urls:
                try:
                    start_time = time.time()
                    response = requests.get(url, timeout=10)
                    response_time = (time.time() - start_time) * 1000
                    
                    connectivity_results[name] = {
                        'reachable': True,
                        'status_code': response.status_code,
                        'response_time_ms': response_time,
                        'status': 'healthy' if response.status_code == 200 else 'warning'
                    }
                    
                    if response.status_code == 200:
                        successful_connections += 1
                        
                except requests.exceptions.RequestException as e:
                    connectivity_results[name] = {
                        'reachable': False,
                        'error': str(e),
                        'status': 'critical'
                    }
            
            # Overall connectivity status
            if successful_connections == len(test_urls):
                overall_status = 'healthy'
            elif successful_connections > 0:
                overall_status = 'warning'
            else:
                overall_status = 'critical'
            
            results = {
                'status': overall_status,
                'connectivity': connectivity_results,
                'successful_connections': successful_connections,
                'total_tests': len(test_urls)
            }
            
            self.logger.info(f"Network connectivity check completed - Status: {results['status']}")
            return results
            
        except Exception as e:
            self.logger.error(f"Network connectivity check failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_log_health(self) -> Dict[str, Any]:
        """Check log files for errors and warnings"""
        self.logger.info("Checking log health...")
        
        try:
            log_dirs = [
                Path('/opt/arxiv-system/logs'),
                Path('/opt/arxiv-system/data/ai_scholar/logs'),
                Path('/opt/arxiv-system/data/quant_scholar/logs')
            ]
            
            log_analysis = {}
            overall_status = 'healthy'
            
            for log_dir in log_dirs:
                if not log_dir.exists():
                    continue
                
                dir_name = str(log_dir.relative_to(Path('/opt/arxiv-system')))
                
                # Analyze recent log files (last 24 hours)
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                error_count = 0
                warning_count = 0
                total_lines = 0
                
                for log_file in log_dir.glob('*.log'):
                    try:
                        # Check if file was modified recently
                        if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_time:
                            continue
                        
                        with open(log_file, 'r') as f:
                            for line in f:
                                total_lines += 1
                                line_lower = line.lower()
                                if 'error' in line_lower or 'critical' in line_lower:
                                    error_count += 1
                                elif 'warning' in line_lower or 'warn' in line_lower:
                                    warning_count += 1
                                    
                    except (OSError, PermissionError, UnicodeDecodeError):
                        continue
                
                # Determine status for this log directory
                if error_count > 10:  # More than 10 errors in 24h
                    dir_status = 'critical'
                    overall_status = 'critical'
                elif error_count > 0 or warning_count > 20:  # Any errors or many warnings
                    dir_status = 'warning'
                    if overall_status == 'healthy':
                        overall_status = 'warning'
                else:
                    dir_status = 'healthy'
                
                log_analysis[dir_name] = {
                    'error_count': error_count,
                    'warning_count': warning_count,
                    'total_lines': total_lines,
                    'status': dir_status
                }
            
            results = {
                'status': overall_status,
                'log_analysis': log_analysis,
                'total_errors': sum(analysis.get('error_count', 0) for analysis in log_analysis.values()),
                'total_warnings': sum(analysis.get('warning_count', 0) for analysis in log_analysis.values())
            }
            
            self.logger.info(f"Log health check completed - Status: {results['status']}")
            return results
            
        except Exception as e:
            self.logger.error(f"Log health check failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_status_level(self, value: float, metric_type: str) -> str:
        """Get status level based on thresholds"""
        warning_threshold = self.thresholds.get(f'{metric_type}_warning', 80)
        critical_threshold = self.thresholds.get(f'{metric_type}_critical', 90)
        
        if value >= critical_threshold:
            return 'critical'
        elif value >= warning_threshold:
            return 'warning'
        else:
            return 'healthy'
    
    def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check of all system components"""
        self.logger.info("Starting comprehensive health check...")
        
        # Run all health checks
        health_checks = {
            'system_resources': self.check_system_resources(),
            'chromadb': self.check_chromadb_health(),
            'services': self.check_service_status(),
            'docker': self.check_docker_containers(),
            'filesystem': self.check_file_system_health(),
            'network': self.check_network_connectivity(),
            'logs': self.check_log_health()
        }
        
        # Determine overall system health
        status_priority = {'critical': 3, 'error': 2, 'warning': 1, 'healthy': 0}
        overall_status = 'healthy'
        
        for check_name, check_result in health_checks.items():
            check_status = check_result.get('status', 'error')
            if status_priority.get(check_status, 2) > status_priority.get(overall_status, 0):
                overall_status = check_status
        
        # Calculate health score
        healthy_checks = sum(1 for result in health_checks.values() if result.get('status') == 'healthy')
        health_score = (healthy_checks / len(health_checks)) * 100
        
        # Generate summary
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        summary = {
            'overall_status': overall_status,
            'health_score': health_score,
            'timestamp': end_time.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'checks_performed': len(health_checks),
            'healthy_checks': healthy_checks,
            'detailed_results': health_checks
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(health_checks)
        summary['recommendations'] = recommendations
        
        self.logger.info(f"Comprehensive health check completed - Overall status: {overall_status}")
        return summary
    
    def _generate_recommendations(self, health_checks: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on health check results"""
        recommendations = []
        
        for check_name, result in health_checks.items():
            status = result.get('status', 'unknown')
            
            if status == 'critical':
                if check_name == 'system_resources':
                    if result.get('cpu', {}).get('status') == 'critical':
                        recommendations.append("CRITICAL: High CPU usage detected - investigate running processes")
                    if result.get('memory', {}).get('status') == 'critical':
                        recommendations.append("CRITICAL: High memory usage detected - restart services or add more RAM")
                    if result.get('disk', {}).get('status') == 'critical':
                        recommendations.append("CRITICAL: Low disk space - clean up old files or add storage")
                
                elif check_name == 'chromadb':
                    recommendations.append("CRITICAL: ChromaDB is not responding - restart ChromaDB service")
                
                elif check_name == 'services':
                    recommendations.append("CRITICAL: System services are not running - restart failed services")
                
                elif check_name == 'docker':
                    recommendations.append("CRITICAL: Docker containers have issues - check Docker service")
                
                elif check_name == 'network':
                    recommendations.append("CRITICAL: Network connectivity issues - check internet connection")
            
            elif status == 'warning':
                if check_name == 'logs':
                    recommendations.append("WARNING: High error/warning count in logs - investigate recent issues")
                elif check_name == 'filesystem':
                    recommendations.append("WARNING: File system issues detected - check permissions and disk space")
        
        if not recommendations:
            recommendations.append("System is healthy - no immediate action required")
        
        # Add general maintenance recommendations
        recommendations.extend([
            "Regular maintenance: Review and rotate log files",
            "Regular maintenance: Update system packages and dependencies",
            "Regular maintenance: Verify backup procedures are working",
            "Regular maintenance: Monitor system performance trends"
        ])
        
        return recommendations
    
    def save_health_report(self, results: Dict[str, Any]) -> str:
        """Save health check results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'/opt/arxiv-system/logs/health_report_{timestamp}.json'
        
        try:
            with open(report_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            self.logger.info(f"Health report saved to: {report_file}")
            return report_file
            
        except Exception as e:
            self.logger.error(f"Failed to save health report: {e}")
            return ""
    
    def print_health_summary(self, results: Dict[str, Any]):
        """Print health check summary to console"""
        print("\n" + "=" * 60)
        print("MULTI-INSTANCE ARXIV SYSTEM - HEALTH CHECK SUMMARY")
        print("=" * 60)
        print(f"Overall Status: {results['overall_status'].upper()}")
        print(f"Health Score: {results['health_score']:.1f}%")
        print(f"Timestamp: {results['timestamp']}")
        print(f"Duration: {results['duration_seconds']:.1f} seconds")
        
        print(f"\nComponent Status:")
        for check_name, check_result in results['detailed_results'].items():
            status = check_result.get('status', 'unknown')
            status_symbol = {
                'healthy': '✓',
                'warning': '⚠',
                'critical': '✗',
                'error': '✗'
            }.get(status, '?')
            
            print(f"  {status_symbol} {check_name.replace('_', ' ').title()}: {status.upper()}")
        
        print(f"\nTop Recommendations:")
        for i, recommendation in enumerate(results['recommendations'][:5], 1):
            print(f"{i}. {recommendation}")
        
        print("\n" + "=" * 60)


def main():
    """Main health check function"""
    health_checker = SystemHealthChecker()
    
    try:
        # Run comprehensive health check
        results = health_checker.run_comprehensive_health_check()
        
        # Save results
        report_file = health_checker.save_health_report(results)
        
        # Print summary
        health_checker.print_health_summary(results)
        
        # Exit with appropriate code
        if results['overall_status'] in ['critical', 'error']:
            print(f"\n❌ System health check failed! Check {report_file} for details.")
            sys.exit(1)
        elif results['overall_status'] == 'warning':
            print(f"\n⚠️  System has warnings. Check {report_file} for details.")
            sys.exit(0)
        else:
            print(f"\n✅ System is healthy! Report saved to {report_file}")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n💥 Health check failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()