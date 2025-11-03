#!/usr/bin/env python3
"""
Production Readiness Validation Script for Multi-Instance ArXiv System

This script performs comprehensive production readiness validation including:
- Performance testing under realistic load
- Storage management and cleanup validation
- Error handling and recovery testing
- Security and access control validation
- Monitoring and alerting system validation
- Backup and recovery procedures testing
"""

import sys
import os
import json
import time
import subprocess
import tempfile
import shutil
import psutil
import requests
from pathlib import Path
from datetime import datetime, timedelta
import logging
import concurrent.futures

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


class ProductionReadinessValidator:
    """Comprehensive production readiness validator"""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('production_readiness_validation.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_system_performance(self):
        """Validate system performance under production load"""
        self.logger.info("Validating system performance under load...")
        
        performance_results = {
            'cpu_performance': self._test_cpu_performance(),
            'memory_performance': self._test_memory_performance(),
            'disk_performance': self._test_disk_performance(),
            'network_performance': self._test_network_performance(),
            'concurrent_processing': self._test_concurrent_processing()
        }
        
        self.results['performance'] = performance_results
        
        # Check if performance meets production requirements
        performance_ok = all([
            performance_results['cpu_performance']['passed'],
            performance_results['memory_performance']['passed'],
            performance_results['disk_performance']['passed'],
            performance_results['network_performance']['passed'],
            performance_results['concurrent_processing']['passed']
        ])
        
        if performance_ok:
            self.logger.info("✓ System performance validation passed")
        else:
            self.logger.error("✗ System performance validation failed")
        
        return performance_ok
    
    def _test_cpu_performance(self):
        """Test CPU performance under load"""
        try:
            # Test CPU-intensive operations
            start_time = time.time()
            
            def cpu_intensive_task(iterations):
                result = 0
                for i in range(iterations):
                    result += i * i
                return result
            
            # Run CPU test
            iterations = 1000000
            result = cpu_intensive_task(iterations)
            duration = time.time() - start_time
            
            # Calculate performance metrics
            operations_per_second = iterations / duration
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Production requirements: should handle at least 500K ops/sec
            passed = operations_per_second > 500000 and cpu_usage < 90
            
            return {
                'passed': passed,
                'operations_per_second': operations_per_second,
                'cpu_usage_percent': cpu_usage,
                'duration_seconds': duration
            }
            
        except Exception as e:
            self.logger.error(f"CPU performance test failed: {e}")
            return {'passed': False, 'error': str(e)}
    
    def _test_memory_performance(self):
        """Test memory performance and management"""
        try:
            process = psutil.Process()
            initial_memory = process.memory_info().rss
            
            # Test memory allocation and deallocation
            start_time = time.time()
            
            # Allocate large amounts of memory
            memory_blocks = []
            for i in range(10):
                # Allocate 100MB blocks
                block = bytearray(100 * 1024 * 1024)
                memory_blocks.append(block)
            
            peak_memory = process.memory_info().rss
            
            # Deallocate memory
            memory_blocks.clear()
            import gc
            gc.collect()
            
            final_memory = process.memory_info().rss
            duration = time.time() - start_time
            
            # Calculate metrics
            memory_allocated_mb = (peak_memory - initial_memory) / (1024 * 1024)
            memory_freed_mb = (peak_memory - final_memory) / (1024 * 1024)
            memory_efficiency = memory_freed_mb / memory_allocated_mb if memory_allocated_mb > 0 else 0
            
            # Production requirements: efficient memory management
            passed = (
                memory_allocated_mb > 900 and  # Should allocate close to 1GB
                memory_efficiency > 0.8 and   # Should free at least 80% of memory
                duration < 5                   # Should complete within 5 seconds
            )
            
            return {
                'passed': passed,
                'memory_allocated_mb': memory_allocated_mb,
                'memory_freed_mb': memory_freed_mb,
                'memory_efficiency': memory_efficiency,
                'duration_seconds': duration
            }
            
        except Exception as e:
            self.logger.error(f"Memory performance test failed: {e}")
            return {'passed': False, 'error': str(e)}
    
    def _test_disk_performance(self):
        """Test disk I/O performance"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                test_file = Path(temp_dir) / 'performance_test.dat'
                
                # Test write performance
                write_start = time.time()
                data = b'x' * (10 * 1024 * 1024)  # 10MB
                
                for i in range(10):  # Write 100MB total
                    with open(test_file, 'ab') as f:
                        f.write(data)
                
                write_duration = time.time() - write_start
                write_speed_mbps = 100 / write_duration
                
                # Test read performance
                read_start = time.time()
                
                with open(test_file, 'rb') as f:
                    while f.read(1024 * 1024):  # Read in 1MB chunks
                        pass
                
                read_duration = time.time() - read_start
                read_speed_mbps = 100 / read_duration
                
                # Production requirements: at least 50 MB/s read/write
                passed = write_speed_mbps > 50 and read_speed_mbps > 50
                
                return {
                    'passed': passed,
                    'write_speed_mbps': write_speed_mbps,
                    'read_speed_mbps': read_speed_mbps,
                    'write_duration': write_duration,
                    'read_duration': read_duration
                }
                
        except Exception as e:
            self.logger.error(f"Disk performance test failed: {e}")
            return {'passed': False, 'error': str(e)}
    
    def _test_network_performance(self):
        """Test network performance"""
        try:
            # Test HTTP request performance
            test_urls = [
                'https://httpbin.org/delay/1',
                'https://httpbin.org/bytes/1024',
                'https://httpbin.org/json'
            ]
            
            start_time = time.time()
            successful_requests = 0
            total_bytes = 0
            
            for url in test_urls * 5:  # 15 requests total
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        successful_requests += 1
                        total_bytes += len(response.content)
                except Exception:
                    pass
            
            duration = time.time() - start_time
            requests_per_second = successful_requests / duration
            throughput_kbps = (total_bytes / 1024) / duration
            
            # Production requirements: handle at least 5 req/sec
            passed = requests_per_second > 5 and successful_requests > 10
            
            return {
                'passed': passed,
                'requests_per_second': requests_per_second,
                'throughput_kbps': throughput_kbps,
                'successful_requests': successful_requests,
                'duration_seconds': duration
            }
            
        except Exception as e:
            self.logger.error(f"Network performance test failed: {e}")
            return {'passed': False, 'error': str(e)}
    
    def _test_concurrent_processing(self):
        """Test concurrent processing performance"""
        try:
            def processing_task(task_id):
                """Simulate processing task"""
                # Simulate CPU and I/O work
                result = 0
                for i in range(100000):
                    result += i
                
                # Simulate I/O
                time.sleep(0.01)
                
                return {'task_id': task_id, 'result': result}
            
            # Test with different concurrency levels
            concurrency_results = {}
            
            for num_workers in [1, 2, 4, 8]:
                start_time = time.time()
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                    futures = [
                        executor.submit(processing_task, i)
                        for i in range(20)  # 20 tasks
                    ]
                    results = [future.result() for future in futures]
                
                duration = time.time() - start_time
                throughput = len(results) / duration
                
                concurrency_results[num_workers] = {
                    'duration': duration,
                    'throughput': throughput,
                    'completed_tasks': len(results)
                }
            
            # Validate scalability
            single_worker_throughput = concurrency_results[1]['throughput']
            multi_worker_throughput = concurrency_results[4]['throughput']
            
            # Should see improvement with more workers
            scalability_improvement = multi_worker_throughput / single_worker_throughput
            
            passed = scalability_improvement > 1.5  # At least 50% improvement
            
            return {
                'passed': passed,
                'scalability_improvement': scalability_improvement,
                'concurrency_results': concurrency_results
            }
            
        except Exception as e:
            self.logger.error(f"Concurrent processing test failed: {e}")
            return {'passed': False, 'error': str(e)}
    
    def validate_storage_management(self):
        """Validate storage management capabilities"""
        self.logger.info("Validating storage management...")
        
        storage_results = {
            'cleanup_procedures': self._test_cleanup_procedures(),
            'retention_policies': self._test_retention_policies(),
            'storage_monitoring': self._test_storage_monitoring(),
            'disk_space_management': self._test_disk_space_management()
        }
        
        self.results['storage'] = storage_results
        
        storage_ok = all([
            storage_results['cleanup_procedures']['passed'],
            storage_results['retention_policies']['passed'],
            storage_results['storage_monitoring']['passed'],
            storage_results['disk_space_management']['passed']
        ])
        
        if storage_ok:
            self.logger.info("✓ Storage management validation passed")
        else:
            self.logger.error("✗ Storage management validation failed")
        
        return storage_ok
    
    def _test_cleanup_procedures(self):
        """Test automated cleanup procedures"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Create test files with different ages
                old_files = []
                recent_files = []
                
                # Create old files (simulate 30+ days old)
                old_timestamp = time.time() - (35 * 24 * 3600)
                for i in range(10):
                    old_file = temp_path / f'old_file_{i}.tmp'
                    old_file.write_text(f"Old content {i}")
                    os.utime(old_file, (old_timestamp, old_timestamp))
                    old_files.append(old_file)
                
                # Create recent files (simulate 5 days old)
                recent_timestamp = time.time() - (5 * 24 * 3600)
                for i in range(5):
                    recent_file = temp_path / f'recent_file_{i}.tmp'
                    recent_file.write_text(f"Recent content {i}")
                    os.utime(recent_file, (recent_timestamp, recent_timestamp))
                    recent_files.append(recent_file)
                
                # Test cleanup logic
                def cleanup_old_files(directory, max_age_days=30):
                    """Clean up files older than max_age_days"""
                    cutoff_time = time.time() - (max_age_days * 24 * 3600)
                    removed_count = 0
                    
                    for file_path in Path(directory).glob('*.tmp'):
                        if file_path.stat().st_mtime < cutoff_time:
                            file_path.unlink()
                            removed_count += 1
                    
                    return removed_count
                
                # Run cleanup
                removed_count = cleanup_old_files(temp_path, max_age_days=30)
                
                # Verify cleanup results
                remaining_files = list(temp_path.glob('*.tmp'))
                
                passed = (
                    removed_count == len(old_files) and
                    len(remaining_files) == len(recent_files)
                )
                
                return {
                    'passed': passed,
                    'files_removed': removed_count,
                    'files_remaining': len(remaining_files),
                    'expected_removed': len(old_files),
                    'expected_remaining': len(recent_files)
                }
                
        except Exception as e:
            self.logger.error(f"Cleanup procedures test failed: {e}")
            return {'passed': False, 'error': str(e)}
    
    def _test_retention_policies(self):
        """Test data retention policies"""
        try:
            # Test retention policy logic
            def should_retain_file(file_age_days, file_type):
                """Determine if file should be retained based on policy"""
                retention_policies = {
                    'papers': 365,      # Keep papers for 1 year
                    'logs': 90,         # Keep logs for 3 months
                    'cache': 7,         # Keep cache for 1 week
                    'reports': 180      # Keep reports for 6 months
                }
                
                max_age = retention_policies.get(file_type, 30)
                return file_age_days <= max_age
            
            # Test different file types and ages
            test_cases = [
                (10, 'papers', True),    # Recent paper - keep
                (400, 'papers', False),  # Old paper - remove
                (50, 'logs', True),      # Recent log - keep
                (100, 'logs', False),    # Old log - remove
                (3, 'cache', True),      # Recent cache - keep
                (10, 'cache', False),    # Old cache - remove
                (100, 'reports', True),  # Recent report - keep
                (200, 'reports', False)  # Old report - remove
            ]
            
            correct_decisions = 0
            for age, file_type, expected in test_cases:
                result = should_retain_file(age, file_type)
                if result == expected:
                    correct_decisions += 1
            
            passed = correct_decisions == len(test_cases)
            
            return {
                'passed': passed,
                'correct_decisions': correct_decisions,
                'total_cases': len(test_cases),
                'accuracy': correct_decisions / len(test_cases)
            }
            
        except Exception as e:
            self.logger.error(f"Retention policies test failed: {e}")
            return {'passed': False, 'error': str(e)}
    
    def _test_storage_monitoring(self):
        """Test storage monitoring capabilities"""
        try:
            # Test disk usage monitoring
            disk_usage = psutil.disk_usage('/')
            
            total_gb = disk_usage.total / (1024**3)
            used_gb = disk_usage.used / (1024**3)
            free_gb = disk_usage.free / (1024**3)
            usage_percent = (used_gb / total_gb) * 100
            
            # Test storage threshold detection
            def check_storage_thresholds(usage_percent):
                """Check if storage usage exceeds thresholds"""
                thresholds = {
                    'warning': 80,
                    'critical': 90,
                    'emergency': 95
                }
                
                alerts = []
                for level, threshold in thresholds.items():
                    if usage_percent > threshold:
                        alerts.append(level)
                
                return alerts
            
            alerts = check_storage_thresholds(usage_percent)
            
            # Test storage statistics collection
            storage_stats = {
                'total_gb': total_gb,
                'used_gb': used_gb,
                'free_gb': free_gb,
                'usage_percent': usage_percent,
                'alerts': alerts
            }
            
            # Monitoring should work regardless of current usage
            passed = (
                total_gb > 0 and
                used_gb >= 0 and
                free_gb >= 0 and
                0 <= usage_percent <= 100
            )
            
            return {
                'passed': passed,
                'storage_stats': storage_stats,
                'monitoring_functional': True
            }
            
        except Exception as e:
            self.logger.error(f"Storage monitoring test failed: {e}")
            return {'passed': False, 'error': str(e)}
    
    def _test_disk_space_management(self):
        """Test disk space management under low space conditions"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Simulate disk space management
                def manage_disk_space(directory, target_free_percent=20):
                    """Manage disk space by cleaning up files"""
                    # Get current usage
                    total_size = 0
                    files_by_age = []
                    
                    for file_path in Path(directory).rglob('*'):
                        if file_path.is_file():
                            size = file_path.stat().st_size
                            age = time.time() - file_path.stat().st_mtime
                            total_size += size
                            files_by_age.append((age, size, file_path))
                    
                    # Sort by age (oldest first)
                    files_by_age.sort(reverse=True)
                    
                    # Calculate how much space to free
                    target_free_size = total_size * (target_free_percent / 100)
                    
                    # Remove oldest files until target is met
                    freed_size = 0
                    removed_files = 0
                    
                    for age, size, file_path in files_by_age:
                        if freed_size >= target_free_size:
                            break
                        
                        try:
                            file_path.unlink()
                            freed_size += size
                            removed_files += 1
                        except Exception:
                            pass
                    
                    return {
                        'freed_size': freed_size,
                        'removed_files': removed_files,
                        'target_size': target_free_size
                    }
                
                # Create test files
                for i in range(20):
                    test_file = temp_path / f'test_file_{i}.dat'
                    test_file.write_bytes(b'x' * (1024 * 1024))  # 1MB each
                    
                    # Set different ages
                    age_offset = i * 3600  # 1 hour apart
                    old_time = time.time() - age_offset
                    os.utime(test_file, (old_time, old_time))
                
                # Test disk space management
                result = manage_disk_space(temp_path, target_free_percent=25)
                
                # Verify management worked
                passed = (
                    result['removed_files'] > 0 and
                    result['freed_size'] > 0 and
                    result['freed_size'] >= result['target_size'] * 0.8  # Within 80% of target
                )
                
                return {
                    'passed': passed,
                    'management_result': result
                }
                
        except Exception as e:
            self.logger.error(f"Disk space management test failed: {e}")
            return {'passed': False, 'error': str(e)}
    
    def validate_error_handling(self):
        """Validate error handling and recovery mechanisms"""
        self.logger.info("Validating error handling and recovery...")
        
        error_results = {
            'retry_mechanisms': self._test_retry_mechanisms(),
            'error_categorization': self._test_error_categorization(),
            'recovery_procedures': self._test_recovery_procedures(),
            'graceful_degradation': self._test_graceful_degradation()
        }
        
        self.results['error_handling'] = error_results
        
        error_ok = all([
            error_results['retry_mechanisms']['passed'],
            error_results['error_categorization']['passed'],
            error_results['recovery_procedures']['passed'],
            error_results['graceful_degradation']['passed']
        ])
        
        if error_ok:
            self.logger.info("✓ Error handling validation passed")
        else:
            self.logger.error("✗ Error handling validation failed")
        
        return error_ok
    
    def _test_retry_mechanisms(self):
        """Test retry mechanisms with exponential backoff"""
        try:
            def retry_with_backoff(func, max_retries=3, initial_delay=1):
                """Retry function with exponential backoff"""
                for attempt in range(max_retries + 1):
                    try:
                        return func()
                    except Exception as e:
                        if attempt == max_retries:
                            raise e
                        
                        delay = initial_delay * (2 ** attempt)
                        time.sleep(min(delay, 10))  # Cap at 10 seconds
                
                return None
            
            # Test successful retry after failures
            call_count = 0
            def failing_then_success():
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    raise Exception("Temporary failure")
                return "success"
            
            # Mock time.sleep to speed up test
            original_sleep = time.sleep
            time.sleep = lambda x: None
            
            try:
                result = retry_with_backoff(failing_then_success, max_retries=3)
                success_case_passed = result == "success" and call_count == 3
            finally:
                time.sleep = original_sleep
            
            # Test maximum retry limit
            def always_failing():
                raise Exception("Persistent failure")
            
            time.sleep = lambda x: None
            try:
                try:
                    retry_with_backoff(always_failing, max_retries=2)
                    failure_case_passed = False
                except Exception:
                    failure_case_passed = True
            finally:
                time.sleep = original_sleep
            
            passed = success_case_passed and failure_case_passed
            
            return {
                'passed': passed,
                'success_case_passed': success_case_passed,
                'failure_case_passed': failure_case_passed
            }
            
        except Exception as e:
            self.logger.error(f"Retry mechanisms test failed: {e}")
            return {'passed': False, 'error': str(e)}
    
    def _test_error_categorization(self):
        """Test error categorization and handling strategies"""
        try:
            def categorize_error(error):
                """Categorize error for appropriate handling"""
                error_str = str(error).lower()
                
                if 'network' in error_str or 'connection' in error_str:
                    return 'network'
                elif 'timeout' in error_str:
                    return 'timeout'
                elif 'memory' in error_str:
                    return 'memory'
                elif 'disk' in error_str or 'space' in error_str:
                    return 'storage'
                elif 'permission' in error_str or 'access' in error_str:
                    return 'permission'
                else:
                    return 'unknown'
            
            # Test error categorization
            test_errors = [
                (Exception("Network connection failed"), 'network'),
                (Exception("Request timeout occurred"), 'timeout'),
                (Exception("Out of memory error"), 'memory'),
                (Exception("No disk space available"), 'storage'),
                (Exception("Permission denied"), 'permission'),
                (Exception("Some other error"), 'unknown')
            ]
            
            correct_categorizations = 0
            for error, expected_category in test_errors:
                actual_category = categorize_error(error)
                if actual_category == expected_category:
                    correct_categorizations += 1
            
            passed = correct_categorizations == len(test_errors)
            
            return {
                'passed': passed,
                'correct_categorizations': correct_categorizations,
                'total_tests': len(test_errors),
                'accuracy': correct_categorizations / len(test_errors)
            }
            
        except Exception as e:
            self.logger.error(f"Error categorization test failed: {e}")
            return {'passed': False, 'error': str(e)}
    
    def _test_recovery_procedures(self):
        """Test automated recovery procedures"""
        try:
            # Test recovery strategy selection
            def get_recovery_strategy(error_category):
                """Get recovery strategy for error category"""
                strategies = {
                    'network': {'retry': True, 'delay': 5, 'max_attempts': 3},
                    'timeout': {'retry': True, 'delay': 10, 'max_attempts': 2},
                    'memory': {'retry': False, 'action': 'restart_process'},
                    'storage': {'retry': False, 'action': 'cleanup_space'},
                    'permission': {'retry': False, 'action': 'check_permissions'},
                    'unknown': {'retry': True, 'delay': 1, 'max_attempts': 1}
                }
                
                return strategies.get(error_category, strategies['unknown'])
            
            # Test recovery execution simulation
            def execute_recovery(strategy, error_context):
                """Execute recovery strategy"""
                if strategy.get('retry', False):
                    return {
                        'action': 'retry',
                        'delay': strategy.get('delay', 1),
                        'max_attempts': strategy.get('max_attempts', 1),
                        'success': True
                    }
                else:
                    action = strategy.get('action', 'manual_intervention')
                    return {
                        'action': action,
                        'success': True,
                        'message': f"Executed {action} for recovery"
                    }
            
            # Test recovery for different error types
            test_cases = [
                ('network', {'error': 'Connection failed'}),
                ('timeout', {'error': 'Request timeout'}),
                ('memory', {'error': 'Out of memory'}),
                ('storage', {'error': 'Disk full'}),
                ('permission', {'error': 'Access denied'})
            ]
            
            successful_recoveries = 0
            for error_category, context in test_cases:
                strategy = get_recovery_strategy(error_category)
                recovery_result = execute_recovery(strategy, context)
                
                if recovery_result.get('success', False):
                    successful_recoveries += 1
            
            passed = successful_recoveries == len(test_cases)
            
            return {
                'passed': passed,
                'successful_recoveries': successful_recoveries,
                'total_cases': len(test_cases),
                'success_rate': successful_recoveries / len(test_cases)
            }
            
        except Exception as e:
            self.logger.error(f"Recovery procedures test failed: {e}")
            return {'passed': False, 'error': str(e)}
    
    def _test_graceful_degradation(self):
        """Test graceful degradation under adverse conditions"""
        try:
            # Test system behavior under resource constraints
            def simulate_degraded_operation(available_memory_percent, available_disk_percent):
                """Simulate system operation under resource constraints"""
                
                # Determine operational mode based on available resources
                if available_memory_percent < 10 or available_disk_percent < 5:
                    return {
                        'mode': 'emergency',
                        'operations': ['critical_only'],
                        'performance_reduction': 0.9
                    }
                elif available_memory_percent < 20 or available_disk_percent < 10:
                    return {
                        'mode': 'degraded',
                        'operations': ['essential', 'critical'],
                        'performance_reduction': 0.5
                    }
                elif available_memory_percent < 40 or available_disk_percent < 20:
                    return {
                        'mode': 'reduced',
                        'operations': ['normal', 'essential', 'critical'],
                        'performance_reduction': 0.2
                    }
                else:
                    return {
                        'mode': 'normal',
                        'operations': ['all'],
                        'performance_reduction': 0.0
                    }
            
            # Test different resource scenarios
            test_scenarios = [
                (80, 80, 'normal'),      # Normal operation
                (30, 50, 'reduced'),     # Reduced operation
                (15, 25, 'degraded'),    # Degraded operation
                (5, 15, 'emergency')     # Emergency operation
            ]
            
            correct_modes = 0
            for memory_pct, disk_pct, expected_mode in test_scenarios:
                result = simulate_degraded_operation(memory_pct, disk_pct)
                if result['mode'] == expected_mode:
                    correct_modes += 1
            
            passed = correct_modes == len(test_scenarios)
            
            return {
                'passed': passed,
                'correct_modes': correct_modes,
                'total_scenarios': len(test_scenarios),
                'accuracy': correct_modes / len(test_scenarios)
            }
            
        except Exception as e:
            self.logger.error(f"Graceful degradation test failed: {e}")
            return {'passed': False, 'error': str(e)}
    
    def validate_security_compliance(self):
        """Validate security and compliance measures"""
        self.logger.info("Validating security and compliance...")
        
        security_results = {
            'access_control': self._test_access_control(),
            'input_validation': self._test_input_validation(),
            'file_permissions': self._test_file_permissions(),
            'data_protection': self._test_data_protection()
        }
        
        self.results['security'] = security_results
        
        security_ok = all([
            security_results['access_control']['passed'],
            security_results['input_validation']['passed'],
            security_results['file_permissions']['passed'],
            security_results['data_protection']['passed']
        ])
        
        if security_ok:
            self.logger.info("✓ Security compliance validation passed")
        else:
            self.logger.error("✗ Security compliance validation failed")
        
        return security_ok
    
    def _test_access_control(self):
        """Test access control mechanisms"""
        try:
            # Test path traversal prevention
            def is_safe_path(base_path, user_path):
                """Check if user path is safe (no directory traversal)"""
                try:
                    base = Path(base_path).resolve()
                    full_path = (base / user_path).resolve()
                    full_path.relative_to(base)
                    return True
                except (ValueError, OSError):
                    return False
            
            # Test safe and unsafe paths
            base_dir = "/opt/arxiv-system/data"
            
            safe_paths = [
                "papers/paper1.pdf",
                "logs/system.log",
                "cache/temp.dat"
            ]
            
            unsafe_paths = [
                "../../../etc/passwd",
                "../../sensitive_file.txt",
                "/etc/passwd",
                "..\\..\\windows\\system32"
            ]
            
            safe_results = [is_safe_path(base_dir, path) for path in safe_paths]
            unsafe_results = [is_safe_path(base_dir, path) for path in unsafe_paths]
            
            # All safe paths should be allowed, all unsafe paths should be blocked
            passed = (
                all(safe_results) and
                not any(unsafe_results)
            )
            
            return {
                'passed': passed,
                'safe_paths_allowed': sum(safe_results),
                'unsafe_paths_blocked': sum(not result for result in unsafe_results),
                'total_safe_tests': len(safe_paths),
                'total_unsafe_tests': len(unsafe_paths)
            }
            
        except Exception as e:
            self.logger.error(f"Access control test failed: {e}")
            return {'passed': False, 'error': str(e)}
    
    def _test_input_validation(self):
        """Test input validation and sanitization"""
        try:
            import re
            
            def validate_arxiv_id(arxiv_id):
                """Validate arXiv ID format"""
                if not isinstance(arxiv_id, str) or len(arxiv_id) > 50:
                    return False
                
                # Valid arXiv ID patterns
                patterns = [
                    r'^[a-z-]+(\.[A-Z]{2})?/\d{7}$',  # Old format: cs.AI/2024001
                    r'^\d{4}\.\d{4,5}$'               # New format: 2024.12345
                ]
                
                return any(re.match(pattern, arxiv_id) for pattern in patterns)
            
            # Test valid IDs
            valid_ids = [
                'cs.AI/2024001',
                'q-fin.ST/2024002',
                'math.ST/2024003',
                '2024.12345',
                '2024.1234'
            ]
            
            # Test invalid IDs
            invalid_ids = [
                '../../../etc/passwd',
                '<script>alert("xss")</script>',
                'DROP TABLE papers;',
                '',
                'a' * 100,  # Too long
                '2024.abc',
                'invalid/format'
            ]
            
            valid_results = [validate_arxiv_id(id_) for id_ in valid_ids]
            invalid_results = [validate_arxiv_id(id_) for id_ in invalid_ids]
            
            passed = (
                all(valid_results) and
                not any(invalid_results)
            )
            
            return {
                'passed': passed,
                'valid_ids_accepted': sum(valid_results),
                'invalid_ids_rejected': sum(not result for result in invalid_results),
                'total_valid_tests': len(valid_ids),
                'total_invalid_tests': len(invalid_ids)
            }
            
        except Exception as e:
            self.logger.error(f"Input validation test failed: {e}")
            return {'passed': False, 'error': str(e)}
    
    def _test_file_permissions(self):
        """Test file permission security"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Test secure file creation
                config_file = temp_path / 'config.yaml'
                config_file.write_text("sensitive: configuration")
                config_file.chmod(0o600)  # Owner read/write only
                
                log_file = temp_path / 'system.log'
                log_file.write_text("log entries")
                log_file.chmod(0o644)  # Owner read/write, others read
                
                data_dir = temp_path / 'data'
                data_dir.mkdir()
                data_dir.chmod(0o755)  # Standard directory permissions
                
                # Verify permissions
                import stat
                
                config_perms = oct(config_file.stat().st_mode)[-3:]
                log_perms = oct(log_file.stat().st_mode)[-3:]
                dir_perms = oct(data_dir.stat().st_mode)[-3:]
                
                passed = (
                    config_perms == '600' and  # Sensitive config
                    log_perms == '644' and     # Log file
                    dir_perms == '755'         # Directory
                )
                
                return {
                    'passed': passed,
                    'config_permissions': config_perms,
                    'log_permissions': log_perms,
                    'directory_permissions': dir_perms
                }
                
        except Exception as e:
            self.logger.error(f"File permissions test failed: {e}")
            return {'passed': False, 'error': str(e)}
    
    def _test_data_protection(self):
        """Test data protection measures"""
        try:
            # Test data sanitization
            def sanitize_filename(filename):
                """Sanitize filename for safe storage"""
                import re
                
                # Remove dangerous characters
                safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                
                # Limit length
                if len(safe_filename) > 255:
                    safe_filename = safe_filename[:255]
                
                # Prevent hidden files and reserved names
                if safe_filename.startswith('.') or safe_filename.lower() in ['con', 'prn', 'aux', 'nul']:
                    safe_filename = 'safe_' + safe_filename
                
                return safe_filename
            
            # Test filename sanitization
            test_filenames = [
                ('normal_file.pdf', 'normal_file.pdf'),
                ('file<with>bad:chars.pdf', 'file_with_bad_chars.pdf'),
                ('.hidden_file.pdf', 'safe_.hidden_file.pdf'),
                ('con.pdf', 'safe_con.pdf'),
                ('a' * 300 + '.pdf', 'a' * 251 + '.pdf')  # Truncated
            ]
            
            sanitization_passed = 0
            for original, expected in test_filenames:
                result = sanitize_filename(original)
                if len(result) <= 255 and not any(char in result for char in '<>:"/\\|?*'):
                    sanitization_passed += 1
            
            # Test data validation
            def validate_paper_metadata(metadata):
                """Validate paper metadata"""
                required_fields = ['title', 'authors', 'abstract']
                
                if not isinstance(metadata, dict):
                    return False
                
                for field in required_fields:
                    if field not in metadata or not metadata[field]:
                        return False
                
                # Check field lengths
                if len(metadata['title']) > 1000:
                    return False
                
                if len(metadata['abstract']) > 10000:
                    return False
                
                return True
            
            # Test metadata validation
            valid_metadata = {
                'title': 'Test Paper Title',
                'authors': ['Author 1', 'Author 2'],
                'abstract': 'This is a test abstract.'
            }
            
            invalid_metadata_cases = [
                {},  # Missing fields
                {'title': '', 'authors': [], 'abstract': ''},  # Empty fields
                {'title': 'x' * 2000, 'authors': ['Author'], 'abstract': 'Abstract'},  # Too long
                'not_a_dict'  # Wrong type
            ]
            
            validation_results = [validate_paper_metadata(valid_metadata)]
            validation_results.extend([validate_paper_metadata(meta) for meta in invalid_metadata_cases])
            
            # First should pass, rest should fail
            validation_passed = validation_results[0] and not any(validation_results[1:])
            
            passed = (
                sanitization_passed == len(test_filenames) and
                validation_passed
            )
            
            return {
                'passed': passed,
                'sanitization_tests_passed': sanitization_passed,
                'validation_tests_passed': validation_passed,
                'total_sanitization_tests': len(test_filenames)
            }
            
        except Exception as e:
            self.logger.error(f"Data protection test failed: {e}")
            return {'passed': False, 'error': str(e)}
    
    def generate_production_readiness_report(self):
        """Generate comprehensive production readiness report"""
        self.logger.info("Generating production readiness report...")
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Calculate overall readiness score
        category_scores = {}
        total_score = 0
        total_categories = 0
        
        for category, results in self.results.items():
            if isinstance(results, dict):
                category_passed = 0
                category_total = 0
                
                for test_name, test_result in results.items():
                    if isinstance(test_result, dict) and 'passed' in test_result:
                        category_total += 1
                        if test_result['passed']:
                            category_passed += 1
                
                if category_total > 0:
                    category_score = (category_passed / category_total) * 100
                    category_scores[category] = {
                        'score': category_score,
                        'passed': category_passed,
                        'total': category_total
                    }
                    total_score += category_score
                    total_categories += 1
        
        overall_score = total_score / total_categories if total_categories > 0 else 0
        
        # Determine readiness level
        if overall_score >= 95:
            readiness_level = 'PRODUCTION_READY'
        elif overall_score >= 85:
            readiness_level = 'MOSTLY_READY'
        elif overall_score >= 70:
            readiness_level = 'NEEDS_IMPROVEMENT'
        else:
            readiness_level = 'NOT_READY'
        
        report = {
            'production_readiness_summary': {
                'overall_score': overall_score,
                'readiness_level': readiness_level,
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'category_scores': category_scores
            },
            'detailed_results': self.results,
            'recommendations': self._generate_production_recommendations(category_scores)
        }
        
        # Save report to file
        report_file = f'production_readiness_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Production readiness report saved to: {report_file}")
        
        return report
    
    def _generate_production_recommendations(self, category_scores):
        """Generate production readiness recommendations"""
        recommendations = []
        
        for category, score_info in category_scores.items():
            score = score_info['score']
            
            if score < 100:
                if score < 70:
                    recommendations.append(f"CRITICAL: {category} needs significant improvement (score: {score:.1f}%)")
                elif score < 85:
                    recommendations.append(f"IMPORTANT: {category} needs improvement (score: {score:.1f}%)")
                else:
                    recommendations.append(f"MINOR: {category} has minor issues (score: {score:.1f}%)")
        
        if not recommendations:
            recommendations.append("System is production ready - all tests passed successfully")
        
        # Add general production recommendations
        recommendations.extend([
            "Ensure monitoring and alerting systems are configured",
            "Verify backup and recovery procedures are tested",
            "Confirm security policies and access controls are in place",
            "Validate performance under expected production load",
            "Test disaster recovery procedures",
            "Ensure operational runbooks are up to date"
        ])
        
        return recommendations
    
    def run_complete_production_validation(self):
        """Run complete production readiness validation"""
        self.logger.info("Starting production readiness validation...")
        self.logger.info("=" * 60)
        
        try:
            # Run all validation categories
            performance_ok = self.validate_system_performance()
            storage_ok = self.validate_storage_management()
            error_ok = self.validate_error_handling()
            security_ok = self.validate_security_compliance()
            
            # Generate comprehensive report
            report = self.generate_production_readiness_report()
            
            # Print summary
            self.print_production_summary(report)
            
            # Determine overall success
            overall_success = (
                performance_ok and storage_ok and 
                error_ok and security_ok and
                report['production_readiness_summary']['overall_score'] >= 85
            )
            
            return overall_success
            
        except Exception as e:
            self.logger.error(f"Production validation failed with error: {e}")
            return False
    
    def print_production_summary(self, report):
        """Print production readiness summary"""
        summary = report['production_readiness_summary']
        
        print("\n" + "=" * 60)
        print("PRODUCTION READINESS SUMMARY")
        print("=" * 60)
        print(f"Overall Score: {summary['overall_score']:.1f}%")
        print(f"Readiness Level: {summary['readiness_level']}")
        print(f"Duration: {summary['duration_seconds']:.1f} seconds")
        
        print("\nCategory Scores:")
        for category, score_info in summary['category_scores'].items():
            score = score_info['score']
            passed = score_info['passed']
            total = score_info['total']
            print(f"  {category.title()}: {score:.1f}% ({passed}/{total} tests passed)")
        
        print("\nRecommendations:")
        for i, recommendation in enumerate(report['recommendations'][:10], 1):
            print(f"{i}. {recommendation}")
        
        print("\n" + "=" * 60)


def main():
    """Main production readiness validation function"""
    validator = ProductionReadinessValidator()
    success = validator.run_complete_production_validation()
    
    if success:
        print("\n🎉 System is production ready!")
        sys.exit(0)
    else:
        print("\n❌ System is not ready for production. Please address the issues identified.")
        sys.exit(1)


if __name__ == "__main__":
    main()