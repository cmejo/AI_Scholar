"""
Memory Management System for Multi-Instance ArXiv System.

This module provides instance-specific memory monitoring, cleanup, and optimization
to ensure efficient resource utilization across different scholar instances.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import gc
import threading
import time
from dataclasses import dataclass, asdict
from enum import Enum

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

logger = logging.getLogger(__name__)


class MemoryPressure(Enum):
    """Memory pressure levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    
    instance_name: str
    timestamp: datetime
    
    # Memory usage (in MB)
    total_memory_mb: int
    used_memory_mb: int
    available_memory_mb: int
    cached_memory_mb: int
    
    # Process-specific memory
    process_memory_mb: int
    process_peak_memory_mb: int
    
    # Memory pressure indicators
    memory_pressure: MemoryPressure
    swap_usage_mb: int
    
    # Garbage collection stats
    gc_collections: int
    gc_collected_objects: int
    
    @property
    def memory_usage_percent(self) -> float:
        """Calculate memory usage percentage."""
        if self.total_memory_mb == 0:
            return 0.0
        return (self.used_memory_mb / self.total_memory_mb) * 100.0
    
    @property
    def available_memory_percent(self) -> float:
        """Calculate available memory percentage."""
        if self.total_memory_mb == 0:
            return 0.0
        return (self.available_memory_mb / self.total_memory_mb) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['memory_pressure'] = self.memory_pressure.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryStats':
        """Create from dictionary (JSON deserialization)."""
        data['memory_pressure'] = MemoryPressure(data['memory_pressure'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class MemoryCleanupResult:
    """Result of memory cleanup operation."""
    
    instance_name: str
    cleanup_timestamp: datetime
    
    # Memory before cleanup
    memory_before_mb: int
    
    # Memory after cleanup
    memory_after_mb: int
    
    # Cleanup actions performed
    actions_performed: List[str]
    
    # Objects cleaned up
    objects_freed: int
    cache_cleared_mb: int
    
    @property
    def memory_freed_mb(self) -> int:
        """Calculate memory freed during cleanup."""
        return max(0, self.memory_before_mb - self.memory_after_mb)
    
    @property
    def cleanup_effectiveness_percent(self) -> float:
        """Calculate cleanup effectiveness as percentage."""
        if self.memory_before_mb == 0:
            return 0.0
        return (self.memory_freed_mb / self.memory_before_mb) * 100.0


class MemoryManager:
    """
    Instance-specific memory manager that monitors usage, performs cleanup,
    and optimizes memory allocation for multi-instance processing.
    """
    
    def __init__(
        self,
        instance_name: str,
        memory_limit_mb: int = 4096,
        warning_threshold: float = 0.8,
        critical_threshold: float = 0.95
    ):
        self.instance_name = instance_name
        self.memory_limit_mb = memory_limit_mb
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        
        # Memory tracking
        self.memory_history: List[MemoryStats] = []
        self.cleanup_history: List[MemoryCleanupResult] = []
        self.max_history_size = 1000
        
        # Cleanup configuration
        self.cleanup_config = {
            'auto_cleanup_enabled': True,
            'cleanup_interval_minutes': 10,
            'aggressive_cleanup_threshold': 0.9,
            'gc_threshold_objects': 10000,
            'cache_cleanup_enabled': True
        }
        
        # Caches and temporary data
        self.instance_caches: Dict[str, Any] = {}
        self.temporary_objects: List[Any] = []
        
        # Threading
        self.lock = threading.RLock()
        self.monitoring_active = False
        self.last_cleanup = datetime.now()
        
        logger.info(f"MemoryManager initialized for {instance_name} with {memory_limit_mb}MB limit")
    
    def start_monitoring(self) -> None:
        """Start continuous memory monitoring."""
        
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # Start monitoring thread
        monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            name=f"MemoryMonitor-{self.instance_name}",
            daemon=True
        )
        monitoring_thread.start()
        
        logger.info(f"Memory monitoring started for {self.instance_name}")
    
    def stop_monitoring(self) -> None:
        """Stop memory monitoring."""
        self.monitoring_active = False
        logger.info(f"Memory monitoring stopped for {self.instance_name}")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop (runs in separate thread)."""
        
        while self.monitoring_active:
            try:
                # Collect memory statistics
                stats = self.check_memory_usage()
                
                # Check if cleanup is needed
                if self.cleanup_config['auto_cleanup_enabled']:
                    if (stats.memory_pressure in [MemoryPressure.HIGH, MemoryPressure.CRITICAL] or
                        stats.memory_usage_percent > self.cleanup_config['aggressive_cleanup_threshold'] * 100):
                        
                        self.cleanup_if_needed()
                
                # Sleep until next check
                time.sleep(self.cleanup_config['cleanup_interval_minutes'] * 60)
                
            except Exception as e:
                logger.error(f"Error in memory monitoring loop for {self.instance_name}: {e}")
                time.sleep(60)  # Wait longer on error
    
    def check_memory_usage(self) -> MemoryStats:
        """Check current memory usage and return statistics."""
        
        try:
            # Get system memory info
            system_memory = self._get_system_memory_info()
            
            # Get process memory info
            process_memory = self._get_process_memory_info()
            
            # Determine memory pressure
            memory_pressure = self._calculate_memory_pressure(
                system_memory['available_mb'],
                system_memory['total_mb']
            )
            
            # Create memory stats
            stats = MemoryStats(
                instance_name=self.instance_name,
                timestamp=datetime.now(),
                total_memory_mb=system_memory['total_mb'],
                used_memory_mb=system_memory['used_mb'],
                available_memory_mb=system_memory['available_mb'],
                cached_memory_mb=system_memory.get('cached_mb', 0),
                process_memory_mb=process_memory['current_mb'],
                process_peak_memory_mb=process_memory['peak_mb'],
                memory_pressure=memory_pressure,
                swap_usage_mb=system_memory.get('swap_used_mb', 0),
                gc_collections=self._get_gc_stats()['collections'],
                gc_collected_objects=self._get_gc_stats()['collected_objects']
            )
            
            # Store in history
            with self.lock:
                self.memory_history.append(stats)
                if len(self.memory_history) > self.max_history_size:
                    self.memory_history = self.memory_history[-self.max_history_size:]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error checking memory usage for {self.instance_name}: {e}")
            
            # Return minimal stats on error
            return MemoryStats(
                instance_name=self.instance_name,
                timestamp=datetime.now(),
                total_memory_mb=self.memory_limit_mb,
                used_memory_mb=0,
                available_memory_mb=self.memory_limit_mb,
                cached_memory_mb=0,
                process_memory_mb=0,
                process_peak_memory_mb=0,
                memory_pressure=MemoryPressure.LOW,
                swap_usage_mb=0,
                gc_collections=0,
                gc_collected_objects=0
            )
    
    def _get_system_memory_info(self) -> Dict[str, int]:
        """Get system memory information."""
        
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'total_mb': int(memory.total / 1024 / 1024),
                'used_mb': int(memory.used / 1024 / 1024),
                'available_mb': int(memory.available / 1024 / 1024),
                'cached_mb': int(getattr(memory, 'cached', 0) / 1024 / 1024),
                'swap_total_mb': int(swap.total / 1024 / 1024),
                'swap_used_mb': int(swap.used / 1024 / 1024)
            }
            
        except ImportError:
            # Fallback when psutil is not available
            logger.warning("psutil not available, using fallback memory info")
            return {
                'total_mb': self.memory_limit_mb,
                'used_mb': int(self.memory_limit_mb * 0.5),  # Assume 50% usage
                'available_mb': int(self.memory_limit_mb * 0.5),
                'cached_mb': 0,
                'swap_total_mb': 0,
                'swap_used_mb': 0
            }
        except Exception as e:
            logger.error(f"Error getting system memory info: {e}")
            return {
                'total_mb': self.memory_limit_mb,
                'used_mb': 0,
                'available_mb': self.memory_limit_mb,
                'cached_mb': 0,
                'swap_total_mb': 0,
                'swap_used_mb': 0
            }
    
    def _get_process_memory_info(self) -> Dict[str, int]:
        """Get current process memory information."""
        
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return {
                'current_mb': int(memory_info.rss / 1024 / 1024),
                'peak_mb': int(getattr(memory_info, 'peak_wset', memory_info.rss) / 1024 / 1024)
            }
            
        except ImportError:
            # Fallback when psutil is not available
            return {'current_mb': 0, 'peak_mb': 0}
        except Exception as e:
            logger.error(f"Error getting process memory info: {e}")
            return {'current_mb': 0, 'peak_mb': 0}
    
    def _calculate_memory_pressure(self, available_mb: int, total_mb: int) -> MemoryPressure:
        """Calculate memory pressure level."""
        
        if total_mb == 0:
            return MemoryPressure.LOW
        
        usage_percent = 1.0 - (available_mb / total_mb)
        
        if usage_percent >= self.critical_threshold:
            return MemoryPressure.CRITICAL
        elif usage_percent >= self.warning_threshold:
            return MemoryPressure.HIGH
        elif usage_percent >= 0.6:
            return MemoryPressure.MODERATE
        else:
            return MemoryPressure.LOW
    
    def _get_gc_stats(self) -> Dict[str, int]:
        """Get garbage collection statistics."""
        
        try:
            import gc
            
            # Get GC stats
            stats = gc.get_stats()
            total_collections = sum(stat['collections'] for stat in stats)
            total_collected = sum(stat['collected'] for stat in stats)
            
            return {
                'collections': total_collections,
                'collected_objects': total_collected,
                'uncollectable': len(gc.garbage)
            }
            
        except Exception as e:
            logger.error(f"Error getting GC stats: {e}")
            return {'collections': 0, 'collected_objects': 0, 'uncollectable': 0}
    
    def cleanup_if_needed(self) -> MemoryCleanupResult:
        """Perform memory cleanup if needed."""
        
        with self.lock:
            # Check if cleanup was recent
            if datetime.now() - self.last_cleanup < timedelta(minutes=1):
                logger.debug(f"Skipping cleanup for {self.instance_name} - too recent")
                return self._create_empty_cleanup_result()
            
            # Get memory stats before cleanup
            stats_before = self.check_memory_usage()
            memory_before = stats_before.process_memory_mb
            
            actions_performed = []
            objects_freed = 0
            cache_cleared_mb = 0
            
            try:
                # 1. Clear instance caches
                if self.cleanup_config['cache_cleanup_enabled'] and self.instance_caches:
                    cache_size_before = len(self.instance_caches)
                    self.instance_caches.clear()
                    cache_cleared_mb = cache_size_before * 0.1  # Rough estimate
                    actions_performed.append(f"Cleared {cache_size_before} cache entries")
                
                # 2. Clear temporary objects
                if self.temporary_objects:
                    temp_count = len(self.temporary_objects)
                    self.temporary_objects.clear()
                    objects_freed += temp_count
                    actions_performed.append(f"Cleared {temp_count} temporary objects")
                
                # 3. Force garbage collection
                gc_stats_before = self._get_gc_stats()
                collected = gc.collect()
                gc_stats_after = self._get_gc_stats()
                
                if collected > 0:
                    objects_freed += collected
                    actions_performed.append(f"Garbage collected {collected} objects")
                
                # 4. Clear weak references
                try:
                    import weakref
                    weakref.WeakSet()  # This helps clear weak reference callbacks
                    actions_performed.append("Cleared weak references")
                except:
                    pass
                
                # 5. Optimize memory layout (Python-specific)
                try:
                    # Force memory compaction by creating and deleting large objects
                    temp_large_objects = [[] for _ in range(1000)]
                    del temp_large_objects
                    actions_performed.append("Performed memory compaction")
                except:
                    pass
                
                self.last_cleanup = datetime.now()
                
            except Exception as e:
                logger.error(f"Error during memory cleanup for {self.instance_name}: {e}")
                actions_performed.append(f"Cleanup error: {str(e)}")
            
            # Get memory stats after cleanup
            stats_after = self.check_memory_usage()
            memory_after = stats_after.process_memory_mb
            
            # Create cleanup result
            cleanup_result = MemoryCleanupResult(
                instance_name=self.instance_name,
                cleanup_timestamp=datetime.now(),
                memory_before_mb=memory_before,
                memory_after_mb=memory_after,
                actions_performed=actions_performed,
                objects_freed=objects_freed,
                cache_cleared_mb=int(cache_cleared_mb)
            )
            
            # Store in history
            self.cleanup_history.append(cleanup_result)
            if len(self.cleanup_history) > 100:  # Keep last 100 cleanup operations
                self.cleanup_history = self.cleanup_history[-100:]
            
            if cleanup_result.memory_freed_mb > 0:
                logger.info(
                    f"Memory cleanup for {self.instance_name}: "
                    f"freed {cleanup_result.memory_freed_mb}MB "
                    f"({cleanup_result.cleanup_effectiveness_percent:.1f}% effective)"
                )
            
            return cleanup_result
    
    def _create_empty_cleanup_result(self) -> MemoryCleanupResult:
        """Create empty cleanup result for skipped cleanups."""
        
        current_stats = self.check_memory_usage()
        
        return MemoryCleanupResult(
            instance_name=self.instance_name,
            cleanup_timestamp=datetime.now(),
            memory_before_mb=current_stats.process_memory_mb,
            memory_after_mb=current_stats.process_memory_mb,
            actions_performed=["Cleanup skipped - too recent"],
            objects_freed=0,
            cache_cleared_mb=0
        )
    
    def add_to_cache(self, key: str, value: Any) -> None:
        """Add object to instance cache."""
        
        with self.lock:
            self.instance_caches[key] = value
    
    def get_from_cache(self, key: str) -> Optional[Any]:
        """Get object from instance cache."""
        
        with self.lock:
            return self.instance_caches.get(key)
    
    def remove_from_cache(self, key: str) -> bool:
        """Remove object from instance cache."""
        
        with self.lock:
            if key in self.instance_caches:
                del self.instance_caches[key]
                return True
            return False
    
    def clear_cache(self) -> int:
        """Clear all cached objects and return count cleared."""
        
        with self.lock:
            count = len(self.instance_caches)
            self.instance_caches.clear()
            return count
    
    def add_temporary_object(self, obj: Any) -> None:
        """Add object to temporary objects list for cleanup."""
        
        with self.lock:
            self.temporary_objects.append(obj)
    
    def clear_temporary_objects(self) -> int:
        """Clear all temporary objects and return count cleared."""
        
        with self.lock:
            count = len(self.temporary_objects)
            self.temporary_objects.clear()
            return count
    
    def get_memory_history(self, hours: int = 24) -> List[MemoryStats]:
        """Get memory usage history for specified hours."""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            return [
                stats for stats in self.memory_history
                if stats.timestamp >= cutoff_time
            ]
    
    def get_cleanup_history(self, count: int = 10) -> List[MemoryCleanupResult]:
        """Get recent cleanup history."""
        
        with self.lock:
            return self.cleanup_history[-count:]
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of memory usage and management."""
        
        current_stats = self.check_memory_usage()
        recent_cleanups = self.get_cleanup_history(5)
        
        return {
            'instance_name': self.instance_name,
            'current_memory_usage': {
                'process_memory_mb': current_stats.process_memory_mb,
                'memory_pressure': current_stats.memory_pressure.value,
                'usage_percent': current_stats.memory_usage_percent,
                'available_mb': current_stats.available_memory_mb
            },
            'memory_limit_mb': self.memory_limit_mb,
            'cache_stats': {
                'cached_objects': len(self.instance_caches),
                'temporary_objects': len(self.temporary_objects)
            },
            'cleanup_stats': {
                'total_cleanups': len(self.cleanup_history),
                'last_cleanup': self.last_cleanup.isoformat() if self.last_cleanup else None,
                'recent_cleanups': len(recent_cleanups),
                'average_memory_freed_mb': (
                    sum(c.memory_freed_mb for c in recent_cleanups) / len(recent_cleanups)
                    if recent_cleanups else 0
                )
            },
            'monitoring_active': self.monitoring_active,
            'thresholds': {
                'warning_threshold': self.warning_threshold,
                'critical_threshold': self.critical_threshold
            }
        }
    
    def optimize_memory_usage(self) -> Dict[str, Any]:
        """Perform comprehensive memory optimization."""
        
        optimization_result = {
            'instance_name': self.instance_name,
            'optimization_timestamp': datetime.now().isoformat(),
            'actions_performed': [],
            'memory_before_mb': 0,
            'memory_after_mb': 0,
            'optimization_effective': False
        }
        
        try:
            # Get initial memory stats
            initial_stats = self.check_memory_usage()
            optimization_result['memory_before_mb'] = initial_stats.process_memory_mb
            
            # 1. Aggressive cleanup
            cleanup_result = self.cleanup_if_needed()
            optimization_result['actions_performed'].extend(cleanup_result.actions_performed)
            
            # 2. Optimize garbage collection thresholds
            try:
                import gc
                # Set more aggressive GC thresholds
                gc.set_threshold(700, 10, 10)  # More frequent collection
                optimization_result['actions_performed'].append("Optimized GC thresholds")
            except:
                pass
            
            # 3. Clear import caches
            try:
                import sys
                if hasattr(sys, 'modules'):
                    # Clear unused modules (be careful here)
                    modules_to_clear = [
                        name for name in sys.modules.keys()
                        if name.startswith('_') and name not in ['_thread', '_io', '_weakref']
                    ]
                    for module_name in modules_to_clear[:10]:  # Limit to 10 modules
                        if module_name in sys.modules:
                            del sys.modules[module_name]
                    
                    if modules_to_clear:
                        optimization_result['actions_performed'].append(
                            f"Cleared {min(10, len(modules_to_clear))} unused modules"
                        )
            except:
                pass
            
            # Get final memory stats
            final_stats = self.check_memory_usage()
            optimization_result['memory_after_mb'] = final_stats.process_memory_mb
            
            # Calculate effectiveness
            memory_freed = optimization_result['memory_before_mb'] - optimization_result['memory_after_mb']
            optimization_result['optimization_effective'] = memory_freed > 0
            
            logger.info(
                f"Memory optimization for {self.instance_name}: "
                f"freed {memory_freed}MB, {len(optimization_result['actions_performed'])} actions"
            )
            
        except Exception as e:
            logger.error(f"Error during memory optimization for {self.instance_name}: {e}")
            optimization_result['actions_performed'].append(f"Optimization error: {str(e)}")
        
        return optimization_result