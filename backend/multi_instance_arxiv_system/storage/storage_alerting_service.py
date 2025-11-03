#!/usr/bin/env python3
"""
Storage Alerting Service for multi-instance ArXiv system.

Implements immediate storage warning notifications, storage utilization reporting,
storage growth rate analysis and projections, and storage cleanup impact analysis.
"""

import asyncio
import logging
import sys
import os
import json
import sqlite3
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from .storage_monitor import StorageMonitor, StorageAlert, StorageStats, StorageAlertLevel, StorageDataType
from .data_retention_manager import DataRetentionManager, CleanupResult

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels for storage notifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportType(Enum):
    """Types of storage reports."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


@dataclass
class StorageGrowthAnalysis:
    """Storage growth analysis results."""
    current_usage_gb: float
    growth_rate_gb_per_day: float
    growth_rate_percentage_per_day: float
    projected_full_date: Optional[datetime]
    days_until_full: Optional[int]
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    confidence_score: float  # 0.0 to 1.0
    historical_data_points: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'current_usage_gb': self.current_usage_gb,
            'growth_rate_gb_per_day': self.growth_rate_gb_per_day,
            'growth_rate_percentage_per_day': self.growth_rate_percentage_per_day,
            'projected_full_date': self.projected_full_date.isoformat() if self.projected_full_date else None,
            'days_until_full': self.days_until_full,
            'trend_direction': self.trend_direction,
            'confidence_score': self.confidence_score,
            'historical_data_points': self.historical_data_points
        }


@dataclass
class CleanupImpactAnalysis:
    """Analysis of cleanup operation impact."""
    cleanup_date: datetime
    files_processed: int
    space_freed_gb: float
    space_freed_percentage: float
    actions_performed: Dict[str, int]
    before_usage_gb: float
    after_usage_gb: float
    efficiency_score: float  # 0.0 to 1.0
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'cleanup_date': self.cleanup_date.isoformat(),
            'files_processed': self.files_processed,
            'space_freed_gb': self.space_freed_gb,
            'space_freed_percentage': self.space_freed_percentage,
            'actions_performed': self.actions_performed,
            'before_usage_gb': self.before_usage_gb,
            'after_usage_gb': self.after_usage_gb,
            'efficiency_score': self.efficiency_score,
            'recommendations': self.recommendations
        }


@dataclass
class StorageUtilizationReport:
    """Comprehensive storage utilization report."""
    report_date: datetime
    report_type: ReportType
    period_start: datetime
    period_end: datetime
    
    # Current state
    total_storage_gb: float
    used_storage_gb: float
    free_storage_gb: float
    usage_percentage: float
    
    # Instance breakdown
    instance_breakdown: Dict[str, Dict[str, float]]
    data_type_breakdown: Dict[str, float]
    
    # Growth analysis
    growth_analysis: StorageGrowthAnalysis
    
    # Alerts and issues
    active_alerts: List[StorageAlert]
    resolved_alerts_count: int
    
    # Cleanup analysis
    cleanup_operations: List[CleanupImpactAnalysis]
    total_space_cleaned_gb: float
    
    # Recommendations
    recommendations: List[str]
    priority_actions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'report_date': self.report_date.isoformat(),
            'report_type': self.report_type.value,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'total_storage_gb': self.total_storage_gb,
            'used_storage_gb': self.used_storage_gb,
            'free_storage_gb': self.free_storage_gb,
            'usage_percentage': self.usage_percentage,
            'instance_breakdown': self.instance_breakdown,
            'data_type_breakdown': self.data_type_breakdown,
            'growth_analysis': self.growth_analysis.to_dict(),
            'active_alerts': [alert.to_dict() for alert in self.active_alerts],
            'resolved_alerts_count': self.resolved_alerts_count,
            'cleanup_operations': [cleanup.to_dict() for cleanup in self.cleanup_operations],
            'total_space_cleaned_gb': self.total_space_cleaned_gb,
            'recommendations': self.recommendations,
            'priority_actions': self.priority_actions
        }


class StorageAlertingService:
    """Service for storage alerting and reporting."""
    
    def __init__(self,
                 storage_monitor: StorageMonitor,
                 retention_manager: Optional[DataRetentionManager] = None,
                 database_path: str = "/tmp/storage_alerting.db",
                 alert_cooldown_minutes: int = 60):
        """
        Initialize storage alerting service.
        
        Args:
            storage_monitor: StorageMonitor instance
            retention_manager: DataRetentionManager instance (optional)
            database_path: Path to SQLite database for persistence
            alert_cooldown_minutes: Minimum time between similar alerts
        """
        self.storage_monitor = storage_monitor
        self.retention_manager = retention_manager
        self.database_path = database_path
        self.alert_cooldown_minutes = alert_cooldown_minutes
        
        # Alert tracking
        self.last_alert_times: Dict[str, datetime] = {}
        self.alert_history: List[StorageAlert] = []
        
        # Report cache
        self.report_cache: Dict[str, StorageUtilizationReport] = {}
        
        # Initialize database
        self._init_database()
        
        # Load historical data
        self._load_from_database()
        
        logger.info("StorageAlertingService initialized")
    
    def _init_database(self) -> None:
        """Initialize SQLite database for alerting data."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Create tables
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alert_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT NOT NULL,
                        level TEXT NOT NULL,
                        message TEXT NOT NULL,
                        path TEXT NOT NULL,
                        usage_percentage REAL NOT NULL,
                        threshold REAL NOT NULL,
                        instance_name TEXT,
                        data_type TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        resolved_at TIMESTAMP,
                        notification_sent BOOLEAN DEFAULT FALSE
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS utilization_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        report_type TEXT NOT NULL,
                        report_date TIMESTAMP NOT NULL,
                        period_start TIMESTAMP NOT NULL,
                        period_end TIMESTAMP NOT NULL,
                        report_json TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS growth_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        analysis_date TIMESTAMP NOT NULL,
                        current_usage_gb REAL NOT NULL,
                        growth_rate_gb_per_day REAL NOT NULL,
                        projected_full_date TIMESTAMP,
                        trend_direction TEXT NOT NULL,
                        confidence_score REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cleanup_impact (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cleanup_date TIMESTAMP NOT NULL,
                        files_processed INTEGER NOT NULL,
                        space_freed_gb REAL NOT NULL,
                        before_usage_gb REAL NOT NULL,
                        after_usage_gb REAL NOT NULL,
                        efficiency_score REAL NOT NULL,
                        impact_json TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_alert_created ON alert_history(created_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_alert_level ON alert_history(level)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_report_date ON utilization_reports(report_date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_growth_date ON growth_analysis(analysis_date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cleanup_date ON cleanup_impact(cleanup_date)')
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to initialize alerting database: {e}")
            raise
    
    def _load_from_database(self) -> None:
        """Load historical data from database."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Load recent alert history
                cursor.execute('''
                    SELECT alert_id, level, message, path, usage_percentage, threshold,
                           instance_name, data_type, created_at, resolved_at
                    FROM alert_history 
                    WHERE created_at > datetime('now', '-7 days')
                    ORDER BY created_at DESC
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
                    self.alert_history.append(alert)
                
                logger.info(f"Loaded {len(self.alert_history)} recent alerts from database")
                
        except Exception as e:
            logger.error(f"Failed to load from alerting database: {e}")
    
    async def check_and_send_alerts(self) -> List[StorageAlert]:
        """
        Check storage conditions and send alerts if necessary.
        
        Returns:
            List of alerts that were sent
        """
        alerts_sent = []
        
        try:
            # Get current storage stats
            current_stats = self.storage_monitor.get_current_stats()
            
            # Get active alerts from storage monitor
            active_alerts = self.storage_monitor.get_active_alerts()
            
            for alert in active_alerts:
                # Check if we should send this alert (cooldown period)
                if self._should_send_alert(alert):
                    # Send the alert
                    await self._send_storage_alert(alert)
                    alerts_sent.append(alert)
                    
                    # Update last alert time
                    self.last_alert_times[alert.alert_id] = datetime.now()
                    
                    # Save to database
                    self._save_alert_to_database(alert, notification_sent=True)
            
            # Check for growth-based alerts
            growth_alerts = await self._check_growth_alerts(current_stats)
            for alert in growth_alerts:
                if self._should_send_alert(alert):
                    await self._send_storage_alert(alert)
                    alerts_sent.append(alert)
                    self.last_alert_times[alert.alert_id] = datetime.now()
                    self._save_alert_to_database(alert, notification_sent=True)
            
            logger.info(f"Sent {len(alerts_sent)} storage alerts")
            return alerts_sent
            
        except Exception as e:
            logger.error(f"Failed to check and send alerts: {e}")
            return alerts_sent
    
    def _should_send_alert(self, alert: StorageAlert) -> bool:
        """Check if an alert should be sent based on cooldown period."""
        if alert.alert_id not in self.last_alert_times:
            return True
        
        last_sent = self.last_alert_times[alert.alert_id]
        cooldown_period = timedelta(minutes=self.alert_cooldown_minutes)
        
        return datetime.now() - last_sent > cooldown_period
    
    async def _send_storage_alert(self, alert: StorageAlert) -> bool:
        """
        Send a storage alert notification.
        
        Args:
            alert: StorageAlert to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # This would integrate with the email notification service
            # For now, we'll log the alert
            logger.warning(f"STORAGE ALERT [{alert.level.value.upper()}]: {alert.message}")
            logger.warning(f"  Path: {alert.path}")
            logger.warning(f"  Usage: {alert.usage_percentage:.1f}% (threshold: {alert.threshold:.1f}%)")
            
            if alert.instance_name:
                logger.warning(f"  Instance: {alert.instance_name}")
            
            # TODO: Integrate with EmailNotificationService
            # await self.email_service.send_storage_alert(alert)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send storage alert: {e}")
            return False
    
    async def _check_growth_alerts(self, current_stats: StorageStats) -> List[StorageAlert]:
        """Check for growth-based alerts."""
        alerts = []
        
        try:
            # Analyze growth trends
            growth_analysis = await self.analyze_storage_growth()
            
            # Check if growth rate is concerning
            if growth_analysis.days_until_full and growth_analysis.days_until_full < 30:
                alert = StorageAlert(
                    alert_id=f"growth_warning_{int(time.time())}",
                    level=StorageAlertLevel.WARNING,
                    message=f"Storage projected to be full in {growth_analysis.days_until_full} days at current growth rate",
                    path="system_wide",
                    usage_percentage=current_stats.overall_usage_percentage,
                    threshold=95.0,
                    data_type=None
                )
                alerts.append(alert)
            
            # Check for rapid growth
            if growth_analysis.growth_rate_percentage_per_day > 2.0:  # More than 2% per day
                alert = StorageAlert(
                    alert_id=f"rapid_growth_{int(time.time())}",
                    level=StorageAlertLevel.CRITICAL,
                    message=f"Rapid storage growth detected: {growth_analysis.growth_rate_percentage_per_day:.1f}% per day",
                    path="system_wide",
                    usage_percentage=current_stats.overall_usage_percentage,
                    threshold=80.0,
                    data_type=None
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to check growth alerts: {e}")
            return alerts
    
    def _save_alert_to_database(self, alert: StorageAlert, notification_sent: bool = False) -> None:
        """Save alert to database."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO alert_history 
                    (alert_id, level, message, path, usage_percentage, threshold,
                     instance_name, data_type, created_at, resolved_at, notification_sent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    alert.resolved_at.isoformat() if alert.resolved_at else None,
                    notification_sent
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to save alert to database: {e}")
    
    async def analyze_storage_growth(self, days_back: int = 30) -> StorageGrowthAnalysis:
        """
        Analyze storage growth trends.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            StorageGrowthAnalysis with growth trends
        """
        try:
            # Get historical usage data
            cutoff_date = datetime.now() - timedelta(days=days_back)
            usage_history = self.storage_monitor.get_usage_history(days=days_back)
            
            if len(usage_history) < 2:
                # Not enough data for analysis
                current_stats = self.storage_monitor.get_current_stats()
                return StorageGrowthAnalysis(
                    current_usage_gb=current_stats.used_storage_gb,
                    growth_rate_gb_per_day=0.0,
                    growth_rate_percentage_per_day=0.0,
                    projected_full_date=None,
                    days_until_full=None,
                    trend_direction='stable',
                    confidence_score=0.0,
                    historical_data_points=len(usage_history)
                )
            
            # Calculate growth rate
            usage_data = [(u.last_updated, u.used_gb) for u in usage_history]
            usage_data.sort(key=lambda x: x[0])  # Sort by date
            
            # Linear regression for growth rate
            x_values = [(date - usage_data[0][0]).total_seconds() / 86400 for date, _ in usage_data]  # Days
            y_values = [usage for _, usage in usage_data]
            
            if len(x_values) > 1:
                # Calculate slope (growth rate per day)
                n = len(x_values)
                sum_x = sum(x_values)
                sum_y = sum(y_values)
                sum_xy = sum(x * y for x, y in zip(x_values, y_values))
                sum_x2 = sum(x * x for x in x_values)
                
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                growth_rate_gb_per_day = slope
                
                # Calculate confidence (R-squared)
                y_mean = sum_y / n
                ss_tot = sum((y - y_mean) ** 2 for y in y_values)
                ss_res = sum((y - (slope * x + (sum_y - slope * sum_x) / n)) ** 2 
                           for x, y in zip(x_values, y_values))
                
                confidence_score = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
                confidence_score = max(0.0, min(1.0, confidence_score))
            else:
                growth_rate_gb_per_day = 0.0
                confidence_score = 0.0
            
            # Current usage
            current_usage_gb = y_values[-1] if y_values else 0.0
            current_stats = self.storage_monitor.get_current_stats()
            total_storage_gb = current_stats.total_storage_gb
            
            # Growth rate as percentage
            growth_rate_percentage_per_day = (growth_rate_gb_per_day / total_storage_gb * 100) if total_storage_gb > 0 else 0.0
            
            # Trend direction
            if abs(growth_rate_gb_per_day) < 0.1:  # Less than 100MB per day
                trend_direction = 'stable'
            elif growth_rate_gb_per_day > 0:
                trend_direction = 'increasing'
            else:
                trend_direction = 'decreasing'
            
            # Projected full date
            projected_full_date = None
            days_until_full = None
            
            if growth_rate_gb_per_day > 0:
                free_space_gb = current_stats.free_storage_gb
                days_to_full = free_space_gb / growth_rate_gb_per_day
                
                if days_to_full > 0:
                    projected_full_date = datetime.now() + timedelta(days=days_to_full)
                    days_until_full = int(days_to_full)
            
            analysis = StorageGrowthAnalysis(
                current_usage_gb=current_usage_gb,
                growth_rate_gb_per_day=growth_rate_gb_per_day,
                growth_rate_percentage_per_day=growth_rate_percentage_per_day,
                projected_full_date=projected_full_date,
                days_until_full=days_until_full,
                trend_direction=trend_direction,
                confidence_score=confidence_score,
                historical_data_points=len(usage_history)
            )
            
            # Save analysis to database
            self._save_growth_analysis(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze storage growth: {e}")
            # Return default analysis
            current_stats = self.storage_monitor.get_current_stats()
            return StorageGrowthAnalysis(
                current_usage_gb=current_stats.used_storage_gb,
                growth_rate_gb_per_day=0.0,
                growth_rate_percentage_per_day=0.0,
                projected_full_date=None,
                days_until_full=None,
                trend_direction='stable',
                confidence_score=0.0,
                historical_data_points=0
            )
    
    def _save_growth_analysis(self, analysis: StorageGrowthAnalysis) -> None:
        """Save growth analysis to database."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO growth_analysis 
                    (analysis_date, current_usage_gb, growth_rate_gb_per_day,
                     projected_full_date, trend_direction, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    analysis.current_usage_gb,
                    analysis.growth_rate_gb_per_day,
                    analysis.projected_full_date.isoformat() if analysis.projected_full_date else None,
                    analysis.trend_direction,
                    analysis.confidence_score
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to save growth analysis: {e}")
    
    async def analyze_cleanup_impact(self, cleanup_result: CleanupResult, 
                                   before_stats: StorageStats, 
                                   after_stats: StorageStats) -> CleanupImpactAnalysis:
        """
        Analyze the impact of a cleanup operation.
        
        Args:
            cleanup_result: Result of cleanup operation
            before_stats: Storage stats before cleanup
            after_stats: Storage stats after cleanup
            
        Returns:
            CleanupImpactAnalysis with impact assessment
        """
        try:
            space_freed_gb = cleanup_result.total_space_freed_mb / 1024
            space_freed_percentage = (space_freed_gb / before_stats.total_storage_gb * 100) if before_stats.total_storage_gb > 0 else 0.0
            
            # Calculate efficiency score
            expected_freed = space_freed_gb
            actual_freed = before_stats.used_storage_gb - after_stats.used_storage_gb
            efficiency_score = min(1.0, actual_freed / expected_freed) if expected_freed > 0 else 0.0
            
            # Generate recommendations
            recommendations = []
            
            if efficiency_score < 0.8:
                recommendations.append("Cleanup efficiency was lower than expected. Review retention policies.")
            
            if space_freed_percentage < 1.0:
                recommendations.append("Cleanup freed less than 1% of total storage. Consider more aggressive policies.")
            
            if cleanup_result.errors:
                recommendations.append(f"Cleanup had {len(cleanup_result.errors)} errors. Review error logs.")
            
            if space_freed_gb > 10.0:
                recommendations.append("Significant space freed. Consider scheduling more frequent cleanups.")
            
            analysis = CleanupImpactAnalysis(
                cleanup_date=datetime.now(),
                files_processed=cleanup_result.total_files_processed,
                space_freed_gb=space_freed_gb,
                space_freed_percentage=space_freed_percentage,
                actions_performed=dict(cleanup_result.actions_performed),
                before_usage_gb=before_stats.used_storage_gb,
                after_usage_gb=after_stats.used_storage_gb,
                efficiency_score=efficiency_score,
                recommendations=recommendations
            )
            
            # Save analysis to database
            self._save_cleanup_impact(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze cleanup impact: {e}")
            # Return default analysis
            return CleanupImpactAnalysis(
                cleanup_date=datetime.now(),
                files_processed=0,
                space_freed_gb=0.0,
                space_freed_percentage=0.0,
                actions_performed={},
                before_usage_gb=0.0,
                after_usage_gb=0.0,
                efficiency_score=0.0,
                recommendations=["Analysis failed - review cleanup operation manually"]
            )
    
    def _save_cleanup_impact(self, analysis: CleanupImpactAnalysis) -> None:
        """Save cleanup impact analysis to database."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO cleanup_impact 
                    (cleanup_date, files_processed, space_freed_gb, before_usage_gb,
                     after_usage_gb, efficiency_score, impact_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis.cleanup_date.isoformat(),
                    analysis.files_processed,
                    analysis.space_freed_gb,
                    analysis.before_usage_gb,
                    analysis.after_usage_gb,
                    analysis.efficiency_score,
                    json.dumps(analysis.to_dict())
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to save cleanup impact: {e}")
    
    async def generate_utilization_report(self, 
                                        report_type: ReportType = ReportType.MONTHLY) -> StorageUtilizationReport:
        """
        Generate comprehensive storage utilization report.
        
        Args:
            report_type: Type of report to generate
            
        Returns:
            StorageUtilizationReport with comprehensive analysis
        """
        try:
            # Determine report period
            now = datetime.now()
            
            if report_type == ReportType.DAILY:
                period_start = now - timedelta(days=1)
            elif report_type == ReportType.WEEKLY:
                period_start = now - timedelta(weeks=1)
            elif report_type == ReportType.MONTHLY:
                period_start = now - timedelta(days=30)
            elif report_type == ReportType.QUARTERLY:
                period_start = now - timedelta(days=90)
            else:  # ANNUAL
                period_start = now - timedelta(days=365)
            
            period_end = now
            
            # Get current storage stats
            current_stats = self.storage_monitor.get_current_stats()
            
            # Get growth analysis
            growth_analysis = await self.analyze_storage_growth()
            
            # Get active alerts
            active_alerts = self.storage_monitor.get_active_alerts()
            
            # Get resolved alerts count
            resolved_alerts_count = self._get_resolved_alerts_count(period_start, period_end)
            
            # Get cleanup operations
            cleanup_operations = self._get_cleanup_operations(period_start, period_end)
            total_space_cleaned_gb = sum(op.space_freed_gb for op in cleanup_operations)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(current_stats, growth_analysis, active_alerts)
            priority_actions = self._generate_priority_actions(current_stats, growth_analysis, active_alerts)
            
            report = StorageUtilizationReport(
                report_date=now,
                report_type=report_type,
                period_start=period_start,
                period_end=period_end,
                total_storage_gb=current_stats.total_storage_gb,
                used_storage_gb=current_stats.used_storage_gb,
                free_storage_gb=current_stats.free_storage_gb,
                usage_percentage=current_stats.overall_usage_percentage,
                instance_breakdown=current_stats.instance_breakdown,
                data_type_breakdown=current_stats.data_type_breakdown,
                growth_analysis=growth_analysis,
                active_alerts=active_alerts,
                resolved_alerts_count=resolved_alerts_count,
                cleanup_operations=cleanup_operations,
                total_space_cleaned_gb=total_space_cleaned_gb,
                recommendations=recommendations,
                priority_actions=priority_actions
            )
            
            # Save report to database
            self._save_utilization_report(report)
            
            # Cache report
            cache_key = f"{report_type.value}_{now.strftime('%Y%m%d')}"
            self.report_cache[cache_key] = report
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate utilization report: {e}")
            raise
    
    def _get_resolved_alerts_count(self, start_date: datetime, end_date: datetime) -> int:
        """Get count of resolved alerts in period."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM alert_history 
                    WHERE resolved_at IS NOT NULL 
                    AND resolved_at BETWEEN ? AND ?
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Failed to get resolved alerts count: {e}")
            return 0
    
    def _get_cleanup_operations(self, start_date: datetime, end_date: datetime) -> List[CleanupImpactAnalysis]:
        """Get cleanup operations in period."""
        operations = []
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT impact_json FROM cleanup_impact 
                    WHERE cleanup_date BETWEEN ? AND ?
                    ORDER BY cleanup_date DESC
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                for row in cursor.fetchall():
                    try:
                        impact_data = json.loads(row[0])
                        # Reconstruct CleanupImpactAnalysis from dict
                        analysis = CleanupImpactAnalysis(
                            cleanup_date=datetime.fromisoformat(impact_data['cleanup_date']),
                            files_processed=impact_data['files_processed'],
                            space_freed_gb=impact_data['space_freed_gb'],
                            space_freed_percentage=impact_data['space_freed_percentage'],
                            actions_performed=impact_data['actions_performed'],
                            before_usage_gb=impact_data['before_usage_gb'],
                            after_usage_gb=impact_data['after_usage_gb'],
                            efficiency_score=impact_data['efficiency_score'],
                            recommendations=impact_data['recommendations']
                        )
                        operations.append(analysis)
                    except Exception as e:
                        logger.error(f"Failed to parse cleanup operation: {e}")
                
        except Exception as e:
            logger.error(f"Failed to get cleanup operations: {e}")
        
        return operations
    
    def _generate_recommendations(self, 
                                current_stats: StorageStats,
                                growth_analysis: StorageGrowthAnalysis,
                                active_alerts: List[StorageAlert]) -> List[str]:
        """Generate storage recommendations."""
        recommendations = []
        
        # Usage-based recommendations
        if current_stats.overall_usage_percentage > 90:
            recommendations.append("Storage usage is critically high (>90%). Immediate cleanup required.")
        elif current_stats.overall_usage_percentage > 80:
            recommendations.append("Storage usage is high (>80%). Schedule cleanup operations.")
        elif current_stats.overall_usage_percentage > 70:
            recommendations.append("Storage usage is moderate (>70%). Monitor growth trends closely.")
        
        # Growth-based recommendations
        if growth_analysis.days_until_full and growth_analysis.days_until_full < 30:
            recommendations.append(f"Storage projected to be full in {growth_analysis.days_until_full} days. Plan capacity expansion.")
        
        if growth_analysis.growth_rate_percentage_per_day > 1.0:
            recommendations.append("High storage growth rate detected. Review data retention policies.")
        
        # Alert-based recommendations
        if len(active_alerts) > 5:
            recommendations.append("Multiple storage alerts active. Review storage configuration.")
        
        # Instance-specific recommendations
        for instance, breakdown in current_stats.instance_breakdown.items():
            if breakdown.get('total', 0) > current_stats.total_storage_gb * 0.6:
                recommendations.append(f"Instance '{instance}' using >60% of total storage. Review instance data.")
        
        return recommendations
    
    def _generate_priority_actions(self,
                                 current_stats: StorageStats,
                                 growth_analysis: StorageGrowthAnalysis,
                                 active_alerts: List[StorageAlert]) -> List[str]:
        """Generate priority actions."""
        priority_actions = []
        
        # Critical actions
        if current_stats.overall_usage_percentage > 95:
            priority_actions.append("CRITICAL: Execute emergency cleanup immediately")
        
        if growth_analysis.days_until_full and growth_analysis.days_until_full < 7:
            priority_actions.append("URGENT: Storage will be full within a week - expand capacity")
        
        # High priority actions
        critical_alerts = [a for a in active_alerts if a.level == StorageAlertLevel.CRITICAL]
        if critical_alerts:
            priority_actions.append(f"HIGH: Resolve {len(critical_alerts)} critical storage alerts")
        
        if current_stats.overall_usage_percentage > 85:
            priority_actions.append("HIGH: Schedule comprehensive cleanup operation")
        
        # Medium priority actions
        if growth_analysis.confidence_score > 0.8 and growth_analysis.growth_rate_percentage_per_day > 0.5:
            priority_actions.append("MEDIUM: Review and optimize data retention policies")
        
        return priority_actions
    
    def _save_utilization_report(self, report: StorageUtilizationReport) -> None:
        """Save utilization report to database."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO utilization_reports 
                    (report_type, report_date, period_start, period_end, report_json)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    report.report_type.value,
                    report.report_date.isoformat(),
                    report.period_start.isoformat(),
                    report.period_end.isoformat(),
                    json.dumps(report.to_dict())
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to save utilization report: {e}")
    
    def get_recent_reports(self, report_type: Optional[ReportType] = None, 
                          limit: int = 10) -> List[StorageUtilizationReport]:
        """Get recent utilization reports."""
        reports = []
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                if report_type:
                    cursor.execute('''
                        SELECT report_json FROM utilization_reports 
                        WHERE report_type = ?
                        ORDER BY report_date DESC 
                        LIMIT ?
                    ''', (report_type.value, limit))
                else:
                    cursor.execute('''
                        SELECT report_json FROM utilization_reports 
                        ORDER BY report_date DESC 
                        LIMIT ?
                    ''', (limit,))
                
                for row in cursor.fetchall():
                    try:
                        report_data = json.loads(row[0])
                        # Note: This is a simplified reconstruction
                        # In practice, you'd want a proper from_dict method
                        reports.append(report_data)
                    except Exception as e:
                        logger.error(f"Failed to parse report: {e}")
                
        except Exception as e:
            logger.error(f"Failed to get recent reports: {e}")
        
        return reports