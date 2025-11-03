"""
Health Check System for multi-instance ArXiv system.

Provides comprehensive health checks and validation before automated runs,
including system resources, dependencies, and instance-specific validations.
"""

import asyncio
import logging
import sys
import psutil
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import requests
import subprocess
from dataclasses import dataclass, field

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from ..shared.multi_instance_data_models import (
    InstanceConfig, SystemHealthReport, InstanceHealthReport
)

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""
    check_name: str
    status: str  # 'healthy', 'warning', 'critical', 'unknown'
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'check_name': self.check_name,
            'status': self.status,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class SystemHealthStatus:
    """Overall system health status."""
    overall_status: str  # 'healthy', 'warning', 'critical'
    check_results: List[HealthCheckResult] = field(default_factory=list)
    system_info: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'overall_status': self.overall_status,
            'check_results': [result.to_dict() for result in self.check_results],
            'system_info': self.system_info,
            'timestamp': self.timestamp.isoformat()
        }


class HealthChecker:
    """Comprehensive health checker for the multi-instance system."""
    
    def __init__(self):
        """Initialize health checker."""
        self.checks = {
            'system_resources': self._check_system_resources,
            'disk_space': self._check_disk_space,
            'network_connectivity': self._check_network_connectivity,
            'dependencies': self._check_dependencies,
            'vector_store': self._check_vector_store,
            'file_permissions': self._check_file_permissions,
            'process_conflicts': self._check_process_conflicts
        }
        
        # Health check thresholds
        self.thresholds = {
            'memory_warning': 80.0,  # %
            'memory_critical': 90.0,  # %
            'disk_warning': 85.0,  # %
            'disk_critical': 95.0,  # %
            'cpu_warning': 80.0,  # %
            'cpu_critical': 90.0,  # %
            'load_warning': 2.0,  # load average
            'load_critical': 4.0   # load average
        }
        
        logger.info("HealthChecker initialized")
    
    async def run_comprehensive_health_check(self, 
                                           instance_configs: Optional[List[InstanceConfig]] = None) -> SystemHealthStatus:
        """
        Run comprehensive health check for the entire system.
        
        Args:
            instance_configs: Optional list of instance configurations to check
            
        Returns:
            SystemHealthStatus with overall health assessment
        """
        logger.info("Starting comprehensive health check")
        
        health_status = SystemHealthStatus(overall_status='healthy')
        
        # Collect system information
        health_status.system_info = await self._collect_system_info()
        
        # Run all health checks
        for check_name, check_func in self.checks.items():
            try:
                logger.debug(f"Running health check: {check_name}")
                result = await check_func()
                health_status.check_results.append(result)
                
                # Update overall status based on individual check results
                if result.status == 'critical':
                    health_status.overall_status = 'critical'
                elif result.status == 'warning' and health_status.overall_status != 'critical':
                    health_status.overall_status = 'warning'
                    
            except Exception as e:
                logger.error(f"Health check '{check_name}' failed: {e}")
                error_result = HealthCheckResult(
                    check_name=check_name,
                    status='unknown',
                    message=f"Health check failed: {e}",
                    details={'error': str(e)}
                )
                health_status.check_results.append(error_result)
        
        # Run instance-specific health checks if configurations provided
        if instance_configs:
            for config in instance_configs:
                try:
                    instance_result = await self._check_instance_health(config)
                    health_status.check_results.append(instance_result)
                    
                    if instance_result.status == 'critical':
                        health_status.overall_status = 'critical'
                    elif instance_result.status == 'warning' and health_status.overall_status != 'critical':
                        health_status.overall_status = 'warning'
                        
                except Exception as e:
                    logger.error(f"Instance health check failed for {config.instance_name}: {e}")
        
        logger.info(f"Health check completed with overall status: {health_status.overall_status}")
        return health_status
    
    async def _collect_system_info(self) -> Dict[str, Any]:
        """Collect basic system information."""
        try:
            return {
                'hostname': subprocess.check_output(['hostname'], text=True).strip(),
                'uptime': datetime.now() - datetime.fromtimestamp(psutil.boot_time()),
                'python_version': sys.version,
                'platform': sys.platform,
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                'disk_total_gb': shutil.disk_usage('/').total / (1024**3)
            }
        except Exception as e:
            logger.error(f"Failed to collect system info: {e}")
            return {'error': str(e)}
    
    async def _check_system_resources(self) -> HealthCheckResult:
        """Check system resource utilization."""
        try:
            # Memory check
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # CPU check
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Load average check (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            except:
                load_avg = 0
            
            # Determine status
            status = 'healthy'
            messages = []
            
            if (memory_percent >= self.thresholds['memory_critical'] or 
                cpu_percent >= self.thresholds['cpu_critical'] or
                load_avg >= self.thresholds['load_critical']):
                status = 'critical'
                messages.append("Critical resource utilization detected")
            elif (memory_percent >= self.thresholds['memory_warning'] or 
                  cpu_percent >= self.thresholds['cpu_warning'] or
                  load_avg >= self.thresholds['load_warning']):
                status = 'warning'
                messages.append("High resource utilization detected")
            else:
                messages.append("System resources are healthy")
            
            return HealthCheckResult(
                check_name='system_resources',
                status=status,
                message='; '.join(messages),
                details={
                    'memory_percent': memory_percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'cpu_percent': cpu_percent,
                    'load_average': load_avg,
                    'thresholds': self.thresholds
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_name='system_resources',
                status='unknown',
                message=f"Failed to check system resources: {e}",
                details={'error': str(e)}
            )
    
    async def _check_disk_space(self) -> HealthCheckResult:
        """Check disk space availability."""
        try:
            # Check root filesystem
            root_usage = shutil.disk_usage('/')
            root_percent = (root_usage.used / root_usage.total) * 100
            
            # Check common data directories
            data_dirs = [
                '/datapool',
                '/tmp',
                '/var/log'
            ]
            
            disk_info = {
                'root': {
                    'total_gb': root_usage.total / (1024**3),
                    'used_gb': root_usage.used / (1024**3),
                    'free_gb': root_usage.free / (1024**3),
                    'percent_used': root_percent
                }
            }
            
            # Check additional directories if they exist
            for data_dir in data_dirs:
                if Path(data_dir).exists():
                    try:
                        usage = shutil.disk_usage(data_dir)
                        percent = (usage.used / usage.total) * 100
                        disk_info[data_dir] = {
                            'total_gb': usage.total / (1024**3),
                            'used_gb': usage.used / (1024**3),
                            'free_gb': usage.free / (1024**3),
                            'percent_used': percent
                        }
                    except Exception:
                        pass
            
            # Determine overall status
            max_usage = max(info['percent_used'] for info in disk_info.values())
            
            if max_usage >= self.thresholds['disk_critical']:
                status = 'critical'
                message = f"Critical disk usage: {max_usage:.1f}%"
            elif max_usage >= self.thresholds['disk_warning']:
                status = 'warning'
                message = f"High disk usage: {max_usage:.1f}%"
            else:
                status = 'healthy'
                message = f"Disk usage is healthy: {max_usage:.1f}%"
            
            return HealthCheckResult(
                check_name='disk_space',
                status=status,
                message=message,
                details=disk_info
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_name='disk_space',
                status='unknown',
                message=f"Failed to check disk space: {e}",
                details={'error': str(e)}
            )
    
    async def _check_network_connectivity(self) -> HealthCheckResult:
        """Check network connectivity to essential services."""
        try:
            connectivity_tests = [
                ('arxiv.org', 'https://arxiv.org/'),
                ('google.com', 'https://www.google.com/'),
                ('jstatsoft.org', 'https://www.jstatsoft.org/'),
                ('r-project.org', 'https://journal.r-project.org/')
            ]
            
            results = {}
            failed_tests = []
            
            for name, url in connectivity_tests:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        results[name] = 'success'
                    else:
                        results[name] = f'http_{response.status_code}'
                        failed_tests.append(name)
                except requests.exceptions.Timeout:
                    results[name] = 'timeout'
                    failed_tests.append(name)
                except Exception as e:
                    results[name] = f'error: {str(e)[:50]}'
                    failed_tests.append(name)
            
            # Determine status
            if len(failed_tests) == 0:
                status = 'healthy'
                message = "All network connectivity tests passed"
            elif len(failed_tests) <= 1:
                status = 'warning'
                message = f"Some network connectivity issues: {', '.join(failed_tests)}"
            else:
                status = 'critical'
                message = f"Multiple network connectivity failures: {', '.join(failed_tests)}"
            
            return HealthCheckResult(
                check_name='network_connectivity',
                status=status,
                message=message,
                details={'test_results': results}
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_name='network_connectivity',
                status='unknown',
                message=f"Failed to check network connectivity: {e}",
                details={'error': str(e)}
            )
    
    async def _check_dependencies(self) -> HealthCheckResult:
        """Check required dependencies and services."""
        try:
            dependencies = {
                'python_packages': [
                    'requests', 'aiohttp', 'aiofiles', 'psutil', 
                    'chromadb', 'sentence-transformers', 'PyPDF2'
                ],
                'system_commands': [
                    'python3', 'pip', 'curl', 'wget'
                ]
            }
            
            results = {}
            missing_deps = []
            
            # Check Python packages
            for package in dependencies['python_packages']:
                try:
                    __import__(package)
                    results[f'package_{package}'] = 'available'
                except ImportError:
                    results[f'package_{package}'] = 'missing'
                    missing_deps.append(f'python package: {package}')
            
            # Check system commands
            for command in dependencies['system_commands']:
                try:
                    subprocess.run([command, '--version'], 
                                 capture_output=True, check=True, timeout=5)
                    results[f'command_{command}'] = 'available'
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    results[f'command_{command}'] = 'missing'
                    missing_deps.append(f'system command: {command}')
            
            # Determine status
            if len(missing_deps) == 0:
                status = 'healthy'
                message = "All dependencies are available"
            elif len(missing_deps) <= 2:
                status = 'warning'
                message = f"Some dependencies missing: {', '.join(missing_deps)}"
            else:
                status = 'critical'
                message = f"Multiple dependencies missing: {', '.join(missing_deps)}"
            
            return HealthCheckResult(
                check_name='dependencies',
                status=status,
                message=message,
                details={'dependency_results': results}
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_name='dependencies',
                status='unknown',
                message=f"Failed to check dependencies: {e}",
                details={'error': str(e)}
            )
    
    async def _check_vector_store(self) -> HealthCheckResult:
        """Check ChromaDB vector store availability."""
        try:
            # Try to import and initialize ChromaDB
            try:
                import chromadb
                client = chromadb.Client()
                
                # Test basic operations
                test_collection = client.get_or_create_collection("health_check_test")
                test_collection.add(
                    documents=["test document"],
                    ids=["test_id"],
                    metadatas=[{"test": "true"}]
                )
                
                # Query to verify it works
                results = test_collection.query(
                    query_texts=["test"],
                    n_results=1
                )
                
                # Clean up test collection
                client.delete_collection("health_check_test")
                
                return HealthCheckResult(
                    check_name='vector_store',
                    status='healthy',
                    message="ChromaDB vector store is operational",
                    details={'chromadb_version': chromadb.__version__}
                )
                
            except ImportError:
                return HealthCheckResult(
                    check_name='vector_store',
                    status='critical',
                    message="ChromaDB not available - package not installed",
                    details={'error': 'ImportError'}
                )
                
        except Exception as e:
            return HealthCheckResult(
                check_name='vector_store',
                status='critical',
                message=f"ChromaDB vector store check failed: {e}",
                details={'error': str(e)}
            )
    
    async def _check_file_permissions(self) -> HealthCheckResult:
        """Check file permissions for critical directories."""
        try:
            critical_dirs = [
                '/datapool',
                '/tmp',
                '/var/log/multi_instance_arxiv'
            ]
            
            permission_results = {}
            permission_issues = []
            
            for dir_path in critical_dirs:
                path = Path(dir_path)
                
                if not path.exists():
                    # Try to create the directory
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                        permission_results[dir_path] = 'created'
                    except PermissionError:
                        permission_results[dir_path] = 'cannot_create'
                        permission_issues.append(f"Cannot create {dir_path}")
                        continue
                
                # Check read/write permissions
                readable = os.access(path, os.R_OK)
                writable = os.access(path, os.W_OK)
                
                if readable and writable:
                    permission_results[dir_path] = 'read_write_ok'
                elif readable:
                    permission_results[dir_path] = 'read_only'
                    permission_issues.append(f"No write permission for {dir_path}")
                else:
                    permission_results[dir_path] = 'no_access'
                    permission_issues.append(f"No access to {dir_path}")
            
            # Determine status
            if len(permission_issues) == 0:
                status = 'healthy'
                message = "File permissions are correct"
            elif len(permission_issues) <= 1:
                status = 'warning'
                message = f"Some permission issues: {', '.join(permission_issues)}"
            else:
                status = 'critical'
                message = f"Multiple permission issues: {', '.join(permission_issues)}"
            
            return HealthCheckResult(
                check_name='file_permissions',
                status=status,
                message=message,
                details={'permission_results': permission_results}
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_name='file_permissions',
                status='unknown',
                message=f"Failed to check file permissions: {e}",
                details={'error': str(e)}
            )
    
    async def _check_process_conflicts(self) -> HealthCheckResult:
        """Check for conflicting processes that might interfere with operations."""
        try:
            # Look for existing multi-instance processes
            current_processes = []
            conflicting_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    
                    # Check for multi-instance related processes
                    if ('multi_instance' in cmdline.lower() or 
                        'monthly_update' in cmdline.lower() or
                        'arxiv_system' in cmdline.lower()):
                        
                        current_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': cmdline[:100]  # Truncate long command lines
                        })
                        
                        # Check if it's a potentially conflicting process
                        if ('orchestrator' in cmdline.lower() or 
                            'downloader' in cmdline.lower()):
                            conflicting_processes.append(proc.info['pid'])
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Determine status
            if len(conflicting_processes) == 0:
                status = 'healthy'
                message = "No conflicting processes detected"
            elif len(conflicting_processes) == 1:
                status = 'warning'
                message = f"Potentially conflicting process detected (PID: {conflicting_processes[0]})"
            else:
                status = 'critical'
                message = f"Multiple conflicting processes detected (PIDs: {', '.join(map(str, conflicting_processes))})"
            
            return HealthCheckResult(
                check_name='process_conflicts',
                status=status,
                message=message,
                details={
                    'current_processes': current_processes,
                    'conflicting_pids': conflicting_processes
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_name='process_conflicts',
                status='unknown',
                message=f"Failed to check process conflicts: {e}",
                details={'error': str(e)}
            )
    
    async def _check_instance_health(self, config: InstanceConfig) -> HealthCheckResult:
        """Check health of a specific instance configuration."""
        try:
            instance_issues = []
            instance_details = {}
            
            # Check storage directories
            storage_paths = [
                config.storage_paths.pdf_directory,
                config.storage_paths.processed_directory,
                config.storage_paths.state_directory,
                config.storage_paths.error_log_directory
            ]
            
            for path_str in storage_paths:
                path = Path(path_str)
                if not path.exists():
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                        instance_details[f'created_{path.name}'] = True
                    except Exception as e:
                        instance_issues.append(f"Cannot create {path}: {e}")
                        instance_details[f'error_{path.name}'] = str(e)
                elif not os.access(path, os.W_OK):
                    instance_issues.append(f"No write permission for {path}")
            
            # Check configuration validity
            try:
                if not config.arxiv_categories and not config.journal_sources:
                    instance_issues.append("No data sources configured")
                
                if config.processing_config.batch_size <= 0:
                    instance_issues.append("Invalid batch size configuration")
                    
            except Exception as e:
                instance_issues.append(f"Configuration validation error: {e}")
            
            # Determine status
            if len(instance_issues) == 0:
                status = 'healthy'
                message = f"Instance '{config.instance_name}' is healthy"
            elif len(instance_issues) <= 2:
                status = 'warning'
                message = f"Instance '{config.instance_name}' has minor issues: {', '.join(instance_issues)}"
            else:
                status = 'critical'
                message = f"Instance '{config.instance_name}' has critical issues: {', '.join(instance_issues)}"
            
            return HealthCheckResult(
                check_name=f'instance_{config.instance_name}',
                status=status,
                message=message,
                details={
                    'instance_name': config.instance_name,
                    'issues': instance_issues,
                    'details': instance_details
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_name=f'instance_{config.instance_name}',
                status='unknown',
                message=f"Failed to check instance health: {e}",
                details={'error': str(e)}
            )
    
    def is_system_ready_for_update(self, health_status: SystemHealthStatus) -> Tuple[bool, List[str]]:
        """
        Determine if the system is ready for automated updates.
        
        Args:
            health_status: System health status from comprehensive check
            
        Returns:
            Tuple of (is_ready, list_of_blocking_issues)
        """
        blocking_issues = []
        
        # Check overall status
        if health_status.overall_status == 'critical':
            blocking_issues.append("System has critical health issues")
        
        # Check specific critical conditions
        for result in health_status.check_results:
            if result.status == 'critical':
                if result.check_name == 'disk_space':
                    blocking_issues.append("Critical disk space shortage")
                elif result.check_name == 'system_resources':
                    blocking_issues.append("Critical system resource shortage")
                elif result.check_name == 'dependencies':
                    blocking_issues.append("Critical dependencies missing")
                elif result.check_name == 'vector_store':
                    blocking_issues.append("Vector store not operational")
                elif result.check_name == 'process_conflicts':
                    blocking_issues.append("Conflicting processes detected")
                elif result.check_name.startswith('instance_'):
                    blocking_issues.append(f"Instance health check failed: {result.check_name}")
        
        is_ready = len(blocking_issues) == 0
        return is_ready, blocking_issues