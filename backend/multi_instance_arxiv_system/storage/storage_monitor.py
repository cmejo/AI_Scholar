#!/usr/bin/env python3
"""
Storage Monitor for multi-instance ArXiv system.

Implements StorageMonitor for real-time disk usage tracking, storage threshold monitoring
and alerting, storage usage prediction and trend analysis, and storage breakdown by
instance and data type.
"""

import asyncio
import logging
import sys
import os
import shutil
import threading
import time
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import psutil

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class StorageAlertLevel(Enum):
    """Storage alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class StorageDataType(Enum):
    """Types of data stored in the system."""
    PDF_FILES = "pdf_files"
    PROCESSED_DATA = "processed_data"
    STATE_FILES = "state_files"
    LOG_FILES = "log_files"
    ARCHIVE_DATA = "archive_data"
    VECTOR_STORE = "vector_store"
    DATABASE = "database"
    TEMP_FILES = "temp_files"


@dataclass
class StorageUsage:
    """Storage usage information for a specific path."""
    path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percentage: float
    data_type: StorageDataType
    instance_name: Optional[str] = None
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def total_gb(self) -> float:
        """Total space in GB."""
        return self.total_bytes / (1024**3)
    
    @property
    def used_gb(self) -> float:
        """Used space in GB."""
        return self.used_bytes / (1024**3)
    
    @property
    def free_gb(self) -> float:
        """Free space in GB."""
        return self.free_bytes / (1024**3)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'path': self.path,
            'total_bytes': self.total_bytes,
            'used_bytes': self.used_bytes,
            'free_bytes': self.free_bytes,
            'usage_percentage': self.usage_percentage,
            'total_gb': self.total_gb,
            'used_gb': self.used_gb,
            'free_gb': self.free_gb,
            'data_type': self.data_type.value,
            'instance_name': self.instance_name,
            'last_updated': self.last_updated.isoformat()
        }


@dataclass
class StorageAlert:
    """Storage alert information."""
    alert_id: str
    level: StorageAlertLevel
    message: str
    path: str
    usage_percentage: float
    threshold: float
    instance_name: Optional[str] = None
    data_type: Optional[StorageDataType] = None
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'alert_id': self.alert_id,
            'level': self.level.value,
            'message': self.message,
            'path': self.path,
            'usage_percentage': self.usage_percentage,
            'threshold': self.threshold,
            'instance_name': self.instance_name,
            'data_type': self.data_type.value if self.data_type else None,
            'created_at': self.created_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


@dataclass
class StorageStats:
    """Comprehensive storage statistics."""
    total_storage_gb: float
    used_storage_gb: float
    free_storage_gb: float
    overall_usage_percentage: float
    instance_breakdown: Dict[str, Dict[str, float]]
    data_type_breakdown: Dict[str, float]
    growth_rate_gb_per_day: float
    projected_full_date: Optional[datetime]
    alerts_count: Dict[str, int]
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'total_storage_gb': self.total_storage_gb,
            'used_storage_gb': self.used_storage_gb,
            'free_storage_gb': self.free_storage_gb,
            'overall_usage_percentage': self.overall_usage_percentage,
            'instance_breakdown': self.instance_breakdown,
            'data_type_breakdown': self.data_type_breakdown,
            'growth_rate_gb_per_day': self.growth_rate_gb_per_day,
            'projected_full_date': self.projected_full_date.isoformat() if self.projected_full_date else None,
            'alerts_count': self.alerts_count,
            'last_updated': self.last_updated.isoformat()
        }


class StorageMonitor:
    """Monitors storage usage across all instances and data types."""
    
    def __init__(self, 
                 database_path: str = "/tmp/storage_monitor.db",
                 monitoring_interval: int = 300,  # 5 minutes
                 alert_thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize storage monitor.
        
        Args:
            database_path: Path to SQLite database for persistence
            monitoring_interval: Monitoring interval in seconds
            alert_thresholds: Custom alert thresholds by level
        """
        self.database_path = database_path
        self.monitoring_interval = monitoring_interval
        
        # Default alert thresholds (percentage)
        self.alert_thresholds = alert_thresholds or {
            'warning': 80.0,
            'critical': 90.0,
            'emergency': 95.0
        }
        
        # Monitoring state
        self.monitored_paths: Dict[str, Tuple[StorageDataType, Optional[str]]] = {}
        self.current_usage: Dict[str, StorageUsage] = {}
        self.active_alerts: Dict[str, StorageAlert] = {}
        self.usage_history: deque = deque(maxlen=1000)  # Keep last 1000 measurements
        
        # Monitoring thread
        self.monitoring_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        self.running = False
        
        # Initialize database
        self._init_database()
        
        # Load historical data
        self._load_from_database()
        
        logger.info("StorageMonitor initialized")
    
    def _init_database(self) -> None:
        """Initialize SQLite database for storage monitoring data."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Create tables
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS storage_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        path TEXT NOT NULL,
                        total_bytes INTEGER NOT NULL,
                        used_bytes INTEGER NOT NULL,
                        free_bytes INTEGER NOT NULL,
                        usage_percentage REAL NOT NULL,
                        data_type TEXT NOT NULL,
                        instance_name TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS storage_alerts (
                        alert_id TEXT PRIMARY KEY,
                        level TEXT NOT NULL,
                        message TEXT NOT NULL,
                        path TEXT NOT NULL,
                        usage_percentage REAL NOT NULL,
                        threshold REAL NOT NULL,
                        instance_name TEXT,
                        data_type TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        resolved_at TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS monitored_paths (
                        path TEXT PRIMARY KEY,
                        data_type TEXT NOT NULL,
                        instance_name TEXT,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON storage_usage(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_usage_path ON storage_usage(path)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_level ON storage_alerts(level)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_created ON storage_alerts(created_at)')
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to initialize storage monitor database: {e}")
            raise
    
    def _load_from_database(self) -> None:
        """Load monitored paths and recent data from database."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Load monitored paths
                cursor.execute('SELECT path, data_type, instance_name FROM monitored_paths')
                for path, data_type, instance_name in cursor.fetchall():
                    self.monitored_paths[path] = (StorageDataType(data_type), instance_name)
                
                # Load active alerts
                cursor.execute('''
                    SELECT alert_id, level, message, path, usage_percentage, threshold,
                           instance_name, data_type, created_at, resolved_at
                    FROM storage_alerts WHERE resolved_at IS NULL
                ''')
                
                for row in cursor.fetchall():
                    alert = StorageAlert(
                        alert_id=row[0],
                        level=StorageAlertLevel(row[1]),
                        message=row[2],
                        path=row[3],
                        usage_percentage=row[4],
                        threshold=row[5],
                        instance_name=row[6],
                        data_type=StorageDataType(row[7]) if row[7] else None,
                        created_at=datetime.fromisoformat(row[8]),
                        resolved_at=datetime.fromisoformat(row[9]) if row[9] else None
                    )
                    self.active_alerts[alert.alert_id] = alert
                
                logger.info(f"Loaded {len(self.monitored_paths)} monitored paths and {len(self.active_alerts)} active alerts")
                
        except Exception as e:
            logger.error(f"Failed to load from storage monitor database: {e}")
    
    def add_monitored_path(self, 
                          path: str,
                          data_type: StorageDataType,
                          instance_name: Optional[str] = None) -> bool:
        """
        Add a path to be monitored.
        
        Args:
            path: Path to monitor
            data_type: Type of data stored at this path
            instance_name: Instance name if path is instance-specific
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            path = os.path.abspath(path)
            
            if not os.path.exists(path):
                logger.warning(f"Path does not exist: {path}")
                return False
            
            self.monitored_paths[path] = (data_type, instance_name)
            
            # Save to database
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO monitored_paths (path, data_type, instance_name)
                    VALUES (?, ?, ?)
                ''', (path, data_type.value, instance_name))
                conn.commit()
            
            logger.info(f"Added monitored path: {path} ({data_type.value})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add monitored path {path}: {e}")
            return False
    
    def remove_monitored_path(self, path: str) -> bool:
        """
        Remove a path from monitoring.
        
        Args:
            path: Path to stop monitoring
            
        Returns:
            True if removed successfully, False otherwise
        """
        try:
            path = os.path.abspath(path)
            
            if path in self.monitored_paths:
                del self.monitored_paths[path]
                
                # Remove from database
                with sqlite3.connect(self.database_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM monitored_paths WHERE path = ?', (path,))
                    conn.commit()
                
                logger.info(f"Removed monitored path: {path}")
                return True
            else:
                logger.warning(f"Path not being monitored: {path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove monitored path {path}: {e}")
            return False
    
    def start_monitoring(self) -> None:
        """Start the storage monitoring thread."""
        if self.running:
            logger.warning("Storage monitoring is already running")
            return
        
        self.running = True
        self.shutdown_event.clear()
        
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            name="StorageMonitor",
            daemon=True
        )
        self.monitoring_thread.start()
        
        logger.info("Storage monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop the storage monitoring thread."""
        if not self.running:
            return
        
        logger.info("Stopping storage monitoring...")
        self.running = False
        self.shutdown_event.set()
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10.0)
        
        logger.info("Storage monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.running and not self.shutdown_event.is_set():
            try:
                # Collect storage usage data
                self._collect_storage_usage()
                
                # Check for alerts
                self._check_storage_alerts()
                
                # Clean up old data
                self._cleanup_old_data()
                
                # Wait for next monitoring cycle
                self.shutdown_event.wait(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in storage monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _collect_storage_usage(self) -> None:
        """Collect storage usage data for all monitored paths."""
        try:
            for path, (data_type, instance_name) in self.monitored_paths.items():
                try:
                    if not os.path.exists(path):
                        logger.warning(f"Monitored path no longer exists: {path}")
                        continue
                    
                    # Get disk usage
                    total, used, free = shutil.disk_usage(path)
                    usage_percentage = (used / total) * 100 if total > 0 else 0
                    
                    # Create usage record
                    usage = StorageUsage(
                        path=path,
                        total_bytes=total,
                        used_bytes=used,
                        free_bytes=free,
                        usage_percentage=usage_percentage,
                        data_type=data_type,
                        instance_name=instance_name
                    )
                    
                    self.current_usage[path] = usage
                    self.usage_history.append(usage)
                    
                    # Save to database
                    self._save_usage_to_database(usage)
                    
                except Exception as e:
                    logger.error(f"Failed to collect usage for {path}: {e}")
            
            logger.debug(f"Collected storage usage for {len(self.current_usage)} paths")
            
        except Exception as e:
            logger.error(f"Failed to collect storage usage: {e}")
    
    def _save_usage_to_database(self, usage: StorageUsage) -> None:
        """Save storage usage to database."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO storage_usage 
                    (path, total_bytes, used_bytes, free_bytes, usage_percentage, 
                     data_type, instance_name, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    usage.path,
                    usage.total_bytes,
                    usage.used_bytes,
                    usage.free_bytes,
                    usage.usage_percentage,
                    usage.data_type.value,
                    usage.instance_name,
                    usage.last_updated.isoformat()
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to save usage to database: {e}")
    
    def _check_storage_alerts(self) -> None:
        """Check for storage alerts based on thresholds."""
        try:
            for path, usage in self.current_usage.items():
                # Check each threshold level
                alert_level = None
                threshold = 0.0
                
                if usage.usage_percentage >= self.alert_thresholds['emergency']:
                    alert_level = StorageAlertLevel.EMERGENCY
                    threshold = self.alert_thresholds['emergency']
                elif usage.usage_percentage >= self.alert_thresholds['critical']:
                    alert_level = StorageAlertLevel.CRITICAL
                    threshold = self.alert_thresholds['critical']
                elif usage.usage_percentage >= self.alert_thresholds['warning']:
                    alert_level = StorageAlertLevel.WARNING
                    threshold = self.alert_thresholds['warning']
                
                if alert_level:
                    # Create alert ID
                    alert_id = f"storage_{alert_level.value}_{hash(path) % 10000}"
                    
                    # Check if alert already exists
                    if alert_id not in self.active_alerts:
                        alert = StorageAlert(
                            alert_id=alert_id,
                            level=alert_level,
                            message=f"Storage usage {usage.usage_percentage:.1f}% exceeds {threshold}% threshold",
                            path=path,
                            usage_percentage=usage.usage_percentage,
                            threshold=threshold,
                            instance_name=usage.instance_name,
                            data_type=usage.data_type
                        )
                        
                        self.active_alerts[alert_id] = alert
                        self._save_alert_to_database(alert)
                        
                        logger.warning(f"Storage alert created: {alert.message} for {path}")
                
                # Resolve alerts if usage drops below threshold
                alerts_to_resolve = []
                for alert_id, alert in self.active_alerts.items():
                    if (alert.path == path and 
                        usage.usage_percentage < alert.threshold - 5.0):  # 5% hysteresis
                        alerts_to_resolve.append(alert_id)
                
                for alert_id in alerts_to_resolve:
                    self._resolve_alert(alert_id)
            
        except Exception as e:
            logger.error(f"Failed to check storage alerts: {e}")
    
    def _save_alert_to_database(self, alert: StorageAlert) -> None:
        """Save storage alert to database."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO storage_alerts 
                    (alert_id, level, message, path, usage_percentage, threshold,
                     instance_name, data_type, created_at, resolved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert.alert_id,
                    alert.level.value,
                    alert.message,
                    alert.path,
                    alert.usage_percentage,
                    alert.threshold,
                    alert.instance_name,
                    alert.data_type.value if alert.data_type else None,
                    alert.created_at.isoformat(),
                    alert.resolved_at.isoformat() if alert.resolved_at else None
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to save alert to database: {e}")
    
    def _resolve_alert(self, alert_id: str) -> None:
        """Resolve a storage alert."""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.resolved_at = datetime.now()
                
                # Update database
                self._save_alert_to_database(alert)
                
                # Remove from active alerts
                del self.active_alerts[alert_id]
                
                logger.info(f"Resolved storage alert: {alert_id}")
                
        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {e}")
    
    def _cleanup_old_data(self) -> None:
        """Clean up old storage monitoring data."""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Clean old usage data
                cursor.execute(
                    'DELETE FROM storage_usage WHERE timestamp < ?',
                    (cutoff_date.isoformat(),)
                )
                
                # Clean old resolved alerts
                cursor.execute(
                    'DELETE FROM storage_alerts WHERE resolved_at IS NOT NULL AND resolved_at < ?',
                    (cutoff_date.isoformat(),)
                )
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to cleanup old storage data: {e}")
    
    def get_current_stats(self) -> StorageStats:
        """Get current comprehensive storage statistics."""
        try:
            total_storage = 0.0
            used_storage = 0.0
            free_storage = 0.0
            
            instance_breakdown = defaultdict(lambda: defaultdict(float))
            data_type_breakdown = defaultdict(float)
            
            # Calculate totals and breakdowns
            for usage in self.current_usage.values():
                total_storage += usage.total_gb
                used_storage += usage.used_gb
                free_storage += usage.free_gb
                
                # Instance breakdown
                if usage.instance_name:
                    instance_breakdown[usage.instance_name][usage.data_type.value] += usage.used_gb
                    instance_breakdown[usage.instance_name]['total'] += usage.used_gb
                
                # Data type breakdown
                data_type_breakdown[usage.data_type.value] += usage.used_gb
            
            # Calculate overall usage percentage
            overall_usage = (used_storage / total_storage * 100) if total_storage > 0 else 0
            
            # Calculate growth rate and projection
            try:
                growth_rate, projected_full = self._calculate_growth_projection()
            except RecursionError:
                growth_rate, projected_full = 0.0, None
            
            # Count alerts by level
            alerts_count = defaultdict(int)
            for alert in self.active_alerts.values():
                alerts_count[alert.level.value] += 1
            
            return StorageStats(
                total_storage_gb=total_storage,
                used_storage_gb=used_storage,
                free_storage_gb=free_storage,
                overall_usage_percentage=overall_usage,
                instance_breakdown=dict(instance_breakdown),
                data_type_breakdown=dict(data_type_breakdown),
                growth_rate_gb_per_day=growth_rate,
                projected_full_date=projected_full,
                alerts_count=dict(alerts_count)
            )
            
        except Exception as e:
            logger.error(f"Failed to get current storage stats: {e}")
            return StorageStats(
                total_storage_gb=0.0,
                used_storage_gb=0.0,
                free_storage_gb=0.0,
                overall_usage_percentage=0.0,
                instance_breakdown={},
                data_type_breakdown={},
                growth_rate_gb_per_day=0.0,
                projected_full_date=None,
                alerts_count={}
            )
    
    def _calculate_growth_projection(self) -> Tuple[float, Optional[datetime]]:
        """Calculate storage growth rate and projected full date."""
        try:
            if len(self.usage_history) < 2:
                return 0.0, None
            
            # Get usage data from last 7 days
            recent_cutoff = datetime.now() - timedelta(days=7)
            recent_usage = [u for u in self.usage_history if u.last_updated > recent_cutoff]
            
            if len(recent_usage) < 2:
                return 0.0, None
            
            # Calculate growth rate (GB per day)
            oldest = min(recent_usage, key=lambda x: x.last_updated)
            newest = max(recent_usage, key=lambda x: x.last_updated)
            
            time_diff_days = (newest.last_updated - oldest.last_updated).total_seconds() / 86400
            if time_diff_days <= 0:
                return 0.0, None
            
            # Sum up used storage for comparison
            oldest_total = sum(u.used_gb for u in recent_usage if u.last_updated == oldest.last_updated)
            newest_total = sum(u.used_gb for u in recent_usage if u.last_updated == newest.last_updated)
            
            growth_rate = (newest_total - oldest_total) / time_diff_days
            
            # Project when storage will be full (calculate directly to avoid recursion)
            current_free = sum(u.free_gb for u in self.current_usage.values())
            if growth_rate > 0 and current_free > 0:
                days_to_full = current_free / growth_rate
                projected_full = datetime.now() + timedelta(days=days_to_full)
                return growth_rate, projected_full
            
            return growth_rate, None
            
        except Exception as e:
            logger.error(f"Failed to calculate growth projection: {e}")
            return 0.0, None
    
    def get_usage_history(self, 
                         path: Optional[str] = None,
                         days: int = 7) -> List[StorageUsage]:
        """
        Get storage usage history.
        
        Args:
            path: Specific path to get history for (None for all)
            days: Number of days of history to retrieve
            
        Returns:
            List of StorageUsage records
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                if path:
                    cursor.execute('''
                        SELECT path, total_bytes, used_bytes, free_bytes, usage_percentage,
                               data_type, instance_name, timestamp
                        FROM storage_usage 
                        WHERE path = ? AND timestamp > ?
                        ORDER BY timestamp
                    ''', (path, cutoff_date.isoformat()))
                else:
                    cursor.execute('''
                        SELECT path, total_bytes, used_bytes, free_bytes, usage_percentage,
                               data_type, instance_name, timestamp
                        FROM storage_usage 
                        WHERE timestamp > ?
                        ORDER BY timestamp
                    ''', (cutoff_date.isoformat(),))
                
                history = []
                for row in cursor.fetchall():
                    usage = StorageUsage(
                        path=row[0],
                        total_bytes=row[1],
                        used_bytes=row[2],
                        free_bytes=row[3],
                        usage_percentage=row[4],
                        data_type=StorageDataType(row[5]),
                        instance_name=row[6],
                        last_updated=datetime.fromisoformat(row[7])
                    )
                    history.append(usage)
                
                return history
                
        except Exception as e:
            logger.error(f"Failed to get usage history: {e}")
            return []
    
    def get_active_alerts(self, 
                         level: Optional[StorageAlertLevel] = None) -> List[StorageAlert]:
        """
        Get active storage alerts.
        
        Args:
            level: Filter by alert level (None for all)
            
        Returns:
            List of active StorageAlert objects
        """
        alerts = list(self.active_alerts.values())
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return sorted(alerts, key=lambda x: x.created_at, reverse=True)
    
    def force_check(self) -> Dict[str, Any]:
        """
        Force an immediate storage check.
        
        Returns:
            Dictionary with check results
        """
        try:
            logger.info("Forcing immediate storage check")
            
            # Collect current usage
            self._collect_storage_usage()
            
            # Check for alerts
            self._check_storage_alerts()
            
            # Get current stats
            stats = self.get_current_stats()
            
            return {
                'success': True,
                'message': 'Storage check completed',
                'stats': stats.to_dict(),
                'monitored_paths': len(self.monitored_paths),
                'active_alerts': len(self.active_alerts),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to force storage check: {e}")
            return {
                'success': False,
                'message': f'Storage check failed: {e}',
                'timestamp': datetime.now().isoformat()
            }
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            'running': self.running,
            'monitored_paths': len(self.monitored_paths),
            'active_alerts': len(self.active_alerts),
            'monitoring_interval': self.monitoring_interval,
            'alert_thresholds': self.alert_thresholds,
            'database_path': self.database_path,
            'last_check': max([u.last_updated for u in self.current_usage.values()]).isoformat() if self.current_usage else None
        }
    
    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.stop_monitoring()
        except:
            pass