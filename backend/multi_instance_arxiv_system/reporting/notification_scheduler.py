#!/usr/bin/env python3
"""
Notification Scheduler for multi-instance ArXiv system.

Implements NotificationScheduler for different notification types, notification throttling
to prevent spam, notification preferences and filtering, and notification history tracking.
"""

import asyncio
import logging
import sys
import json
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import sqlite3
from contextlib import contextmanager

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from .email_notification_service import EmailNotificationService, NotificationPriority
from ..shared.multi_instance_data_models import NotificationConfig

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications that can be scheduled."""
    MONTHLY_UPDATE_SUCCESS = "monthly_update_success"
    MONTHLY_UPDATE_FAILURE = "monthly_update_failure"
    STORAGE_WARNING = "storage_warning"
    STORAGE_CRITICAL = "storage_critical"
    ERROR_SUMMARY = "error_summary"
    SYSTEM_HEALTH = "system_health"
    MAINTENANCE_REMINDER = "maintenance_reminder"
    PERFORMANCE_ALERT = "performance_alert"
    SECURITY_ALERT = "security_alert"
    CUSTOM = "custom"


class ThrottleRule(Enum):
    """Throttling rules for notifications."""
    NO_THROTTLE = "no_throttle"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class NotificationPreferences:
    """User notification preferences."""
    user_id: str
    email: str
    enabled_types: Set[NotificationType] = field(default_factory=set)
    disabled_types: Set[NotificationType] = field(default_factory=set)
    priority_threshold: NotificationPriority = NotificationPriority.NORMAL
    throttle_rules: Dict[NotificationType, ThrottleRule] = field(default_factory=dict)
    quiet_hours_start: Optional[int] = None  # Hour (0-23)
    quiet_hours_end: Optional[int] = None    # Hour (0-23)
    timezone: str = "UTC"
    enabled: bool = True
    
    def should_receive(self, 
                      notification_type: NotificationType,
                      priority: NotificationPriority) -> bool:
        """Check if user should receive this notification."""
        if not self.enabled:
            return False
        
        # Check priority threshold
        if priority.value < self.priority_threshold.value:
            return False
        
        # Check if type is explicitly disabled
        if notification_type in self.disabled_types:
            return False
        
        # Check if type is explicitly enabled or if no specific rules
        if self.enabled_types:
            return notification_type in self.enabled_types
        
        return True
    
    def is_in_quiet_hours(self) -> bool:
        """Check if current time is in quiet hours."""
        if self.quiet_hours_start is None or self.quiet_hours_end is None:
            return False
        
        current_hour = datetime.now().hour
        
        if self.quiet_hours_start <= self.quiet_hours_end:
            # Normal range (e.g., 22:00 to 06:00 next day)
            return self.quiet_hours_start <= current_hour <= self.quiet_hours_end
        else:
            # Overnight range (e.g., 22:00 to 06:00 next day)
            return current_hour >= self.quiet_hours_start or current_hour <= self.quiet_hours_end
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'user_id': self.user_id,
            'email': self.email,
            'enabled_types': [t.value for t in self.enabled_types],
            'disabled_types': [t.value for t in self.disabled_types],
            'priority_threshold': self.priority_threshold.name,
            'throttle_rules': {k.value: v.value for k, v in self.throttle_rules.items()},
            'quiet_hours_start': self.quiet_hours_start,
            'quiet_hours_end': self.quiet_hours_end,
            'timezone': self.timezone,
            'enabled': self.enabled
        }


@dataclass
class ScheduledNotification:
    """A scheduled notification with timing and conditions."""
    notification_id: str
    notification_type: NotificationType
    subject: str
    template_name: str
    context: Dict[str, Any]
    priority: NotificationPriority
    scheduled_at: datetime
    created_at: datetime = field(default_factory=datetime.now)
    recurring: bool = False
    recurrence_pattern: Optional[str] = None  # cron-like pattern
    conditions: Dict[str, Any] = field(default_factory=dict)
    max_attempts: int = 3
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    status: str = "pending"  # pending, sent, failed, cancelled
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'notification_id': self.notification_id,
            'notification_type': self.notification_type.value,
            'subject': self.subject,
            'template_name': self.template_name,
            'context': self.context,
            'priority': self.priority.name,
            'scheduled_at': self.scheduled_at.isoformat(),
            'created_at': self.created_at.isoformat(),
            'recurring': self.recurring,
            'recurrence_pattern': self.recurrence_pattern,
            'conditions': self.conditions,
            'max_attempts': self.max_attempts,
            'attempts': self.attempts,
            'last_attempt': self.last_attempt.isoformat() if self.last_attempt else None,
            'status': self.status
        }


@dataclass
class NotificationHistory:
    """Historical record of sent notifications."""
    notification_id: str
    notification_type: NotificationType
    subject: str
    recipients: List[str]
    priority: NotificationPriority
    sent_at: datetime
    delivery_status: Dict[str, bool]  # recipient -> success
    template_used: str
    context_hash: str  # Hash of context for deduplication
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'notification_id': self.notification_id,
            'notification_type': self.notification_type.value,
            'subject': self.subject,
            'recipients': self.recipients,
            'priority': self.priority.name,
            'sent_at': self.sent_at.isoformat(),
            'delivery_status': self.delivery_status,
            'template_used': self.template_used,
            'context_hash': self.context_hash
        }


class NotificationThrottler:
    """Handles notification throttling to prevent spam."""
    
    def __init__(self):
        """Initialize throttler with tracking structures."""
        self.sent_notifications: Dict[str, deque] = defaultdict(deque)  # user_id -> timestamps
        self.type_limits = {
            ThrottleRule.HOURLY: timedelta(hours=1),
            ThrottleRule.DAILY: timedelta(days=1),
            ThrottleRule.WEEKLY: timedelta(weeks=1),
            ThrottleRule.MONTHLY: timedelta(days=30)
        }
        self.max_notifications = {
            ThrottleRule.HOURLY: 10,
            ThrottleRule.DAILY: 50,
            ThrottleRule.WEEKLY: 200,
            ThrottleRule.MONTHLY: 500
        }
    
    def can_send_notification(self, 
                            user_id: str,
                            notification_type: NotificationType,
                            throttle_rule: ThrottleRule,
                            priority: NotificationPriority) -> bool:
        """Check if notification can be sent based on throttling rules."""
        if throttle_rule == ThrottleRule.NO_THROTTLE:
            return True
        
        # Critical notifications bypass throttling
        if priority == NotificationPriority.CRITICAL:
            return True
        
        # Get time window and limit
        time_window = self.type_limits.get(throttle_rule)
        max_count = self.max_notifications.get(throttle_rule)
        
        if not time_window or not max_count:
            return True
        
        # Clean old notifications
        cutoff_time = datetime.now() - time_window
        user_notifications = self.sent_notifications[user_id]
        
        while user_notifications and user_notifications[0] < cutoff_time:
            user_notifications.popleft()
        
        # Check if under limit
        return len(user_notifications) < max_count
    
    def record_notification(self, user_id: str) -> None:
        """Record that a notification was sent to a user."""
        self.sent_notifications[user_id].append(datetime.now())
    
    def get_throttle_status(self, user_id: str) -> Dict[str, Any]:
        """Get current throttle status for a user."""
        status = {}
        
        for rule, time_window in self.type_limits.items():
            cutoff_time = datetime.now() - time_window
            user_notifications = self.sent_notifications[user_id]
            
            # Count recent notifications
            recent_count = sum(1 for ts in user_notifications if ts > cutoff_time)
            max_count = self.max_notifications[rule]
            
            status[rule.value] = {
                'recent_count': recent_count,
                'max_count': max_count,
                'remaining': max_count - recent_count,
                'time_window': str(time_window)
            }
        
        return status


class NotificationScheduler:
    """Manages scheduling and delivery of notifications with throttling and preferences."""
    
    def __init__(self, 
                 email_service: EmailNotificationService,
                 database_path: str = None):
        """
        Initialize notification scheduler.
        
        Args:
            email_service: Email notification service
            database_path: Path to SQLite database for persistence
        """
        self.email_service = email_service
        self.database_path = database_path or "/tmp/notification_scheduler.db"
        
        # Initialize components
        self.throttler = NotificationThrottler()
        self.preferences: Dict[str, NotificationPreferences] = {}
        self.scheduled_notifications: Dict[str, ScheduledNotification] = {}
        self.notification_history: List[NotificationHistory] = []
        
        # Scheduler state
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        
        # Notification filters and hooks
        self.pre_send_filters: List[Callable] = []
        self.post_send_hooks: List[Callable] = []
        
        # Initialize database
        self._init_database()
        
        # Load preferences and scheduled notifications
        self._load_from_database()
        
        logger.info("NotificationScheduler initialized")
    
    def _init_database(self) -> None:
        """Initialize SQLite database for persistence."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Create tables
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notification_preferences (
                        user_id TEXT PRIMARY KEY,
                        email TEXT NOT NULL,
                        preferences_json TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scheduled_notifications (
                        notification_id TEXT PRIMARY KEY,
                        notification_json TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notification_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        notification_id TEXT NOT NULL,
                        history_json TEXT NOT NULL,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_history_sent_at 
                    ON notification_history(sent_at)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_history_type 
                    ON notification_history(notification_id)
                ''')
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _load_from_database(self) -> None:
        """Load preferences and scheduled notifications from database."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Load preferences
                cursor.execute('SELECT user_id, preferences_json FROM notification_preferences')
                for user_id, prefs_json in cursor.fetchall():
                    try:
                        prefs_data = json.loads(prefs_json)
                        prefs = NotificationPreferences(
                            user_id=prefs_data['user_id'],
                            email=prefs_data['email'],
                            enabled_types={NotificationType(t) for t in prefs_data.get('enabled_types', [])},
                            disabled_types={NotificationType(t) for t in prefs_data.get('disabled_types', [])},
                            priority_threshold=NotificationPriority[prefs_data.get('priority_threshold', 'NORMAL')],
                            throttle_rules={
                                NotificationType(k): ThrottleRule(v) 
                                for k, v in prefs_data.get('throttle_rules', {}).items()
                            },
                            quiet_hours_start=prefs_data.get('quiet_hours_start'),
                            quiet_hours_end=prefs_data.get('quiet_hours_end'),
                            timezone=prefs_data.get('timezone', 'UTC'),
                            enabled=prefs_data.get('enabled', True)
                        )
                        self.preferences[user_id] = prefs
                    except Exception as e:
                        logger.error(f"Failed to load preferences for {user_id}: {e}")
                
                # Load scheduled notifications
                cursor.execute('SELECT notification_id, notification_json FROM scheduled_notifications')
                for notif_id, notif_json in cursor.fetchall():
                    try:
                        notif_data = json.loads(notif_json)
                        notification = ScheduledNotification(
                            notification_id=notif_data['notification_id'],
                            notification_type=NotificationType(notif_data['notification_type']),
                            subject=notif_data['subject'],
                            template_name=notif_data['template_name'],
                            context=notif_data['context'],
                            priority=NotificationPriority[notif_data['priority']],
                            scheduled_at=datetime.fromisoformat(notif_data['scheduled_at']),
                            created_at=datetime.fromisoformat(notif_data['created_at']),
                            recurring=notif_data.get('recurring', False),
                            recurrence_pattern=notif_data.get('recurrence_pattern'),
                            conditions=notif_data.get('conditions', {}),
                            max_attempts=notif_data.get('max_attempts', 3),
                            attempts=notif_data.get('attempts', 0),
                            last_attempt=datetime.fromisoformat(notif_data['last_attempt']) if notif_data.get('last_attempt') else None,
                            status=notif_data.get('status', 'pending')
                        )
                        self.scheduled_notifications[notif_id] = notification
                    except Exception as e:
                        logger.error(f"Failed to load scheduled notification {notif_id}: {e}")
                
                logger.info(f"Loaded {len(self.preferences)} preferences and {len(self.scheduled_notifications)} scheduled notifications")
                
        except Exception as e:
            logger.error(f"Failed to load from database: {e}")
    
    def add_user_preferences(self, 
                           user_id: str,
                           email: str,
                           enabled_types: Optional[Set[NotificationType]] = None,
                           disabled_types: Optional[Set[NotificationType]] = None,
                           priority_threshold: NotificationPriority = NotificationPriority.NORMAL,
                           throttle_rules: Optional[Dict[NotificationType, ThrottleRule]] = None,
                           quiet_hours_start: Optional[int] = None,
                           quiet_hours_end: Optional[int] = None) -> bool:
        """
        Add or update user notification preferences.
        
        Args:
            user_id: Unique user identifier
            email: User email address
            enabled_types: Set of enabled notification types
            disabled_types: Set of disabled notification types
            priority_threshold: Minimum priority level
            throttle_rules: Throttling rules per notification type
            quiet_hours_start: Start of quiet hours (0-23)
            quiet_hours_end: End of quiet hours (0-23)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            preferences = NotificationPreferences(
                user_id=user_id,
                email=email,
                enabled_types=enabled_types or set(),
                disabled_types=disabled_types or set(),
                priority_threshold=priority_threshold,
                throttle_rules=throttle_rules or {},
                quiet_hours_start=quiet_hours_start,
                quiet_hours_end=quiet_hours_end
            )
            
            self.preferences[user_id] = preferences
            
            # Save to database
            self._save_preferences_to_database(preferences)
            
            logger.info(f"Added/updated preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add user preferences: {e}")
            return False
    
    def schedule_notification(self,
                            notification_type: NotificationType,
                            subject: str,
                            template_name: str,
                            context: Dict[str, Any],
                            scheduled_at: datetime,
                            priority: NotificationPriority = NotificationPriority.NORMAL,
                            recurring: bool = False,
                            recurrence_pattern: Optional[str] = None,
                            conditions: Optional[Dict[str, Any]] = None) -> str:
        """
        Schedule a notification for future delivery.
        
        Args:
            notification_type: Type of notification
            subject: Email subject
            template_name: Template file name
            context: Template context variables
            scheduled_at: When to send the notification
            priority: Notification priority
            recurring: Whether notification should repeat
            recurrence_pattern: Cron-like pattern for recurring notifications
            conditions: Conditions that must be met to send
            
        Returns:
            Notification ID for tracking
        """
        try:
            notification_id = f"sched_{int(time.time())}_{notification_type.value}"
            
            notification = ScheduledNotification(
                notification_id=notification_id,
                notification_type=notification_type,
                subject=subject,
                template_name=template_name,
                context=context,
                priority=priority,
                scheduled_at=scheduled_at,
                recurring=recurring,
                recurrence_pattern=recurrence_pattern,
                conditions=conditions or {}
            )
            
            self.scheduled_notifications[notification_id] = notification
            
            # Save to database
            self._save_scheduled_notification_to_database(notification)
            
            logger.info(f"Scheduled notification {notification_id} for {scheduled_at}")
            return notification_id
            
        except Exception as e:
            logger.error(f"Failed to schedule notification: {e}")
            raise
    
    def cancel_scheduled_notification(self, notification_id: str) -> bool:
        """
        Cancel a scheduled notification.
        
        Args:
            notification_id: ID of notification to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        try:
            if notification_id in self.scheduled_notifications:
                self.scheduled_notifications[notification_id].status = "cancelled"
                
                # Update in database
                self._save_scheduled_notification_to_database(
                    self.scheduled_notifications[notification_id]
                )
                
                logger.info(f"Cancelled scheduled notification {notification_id}")
                return True
            else:
                logger.warning(f"Scheduled notification {notification_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to cancel notification {notification_id}: {e}")
            return False
    
    async def send_immediate_notification(self,
                                        notification_type: NotificationType,
                                        subject: str,
                                        template_name: str,
                                        context: Dict[str, Any],
                                        priority: NotificationPriority = NotificationPriority.NORMAL,
                                        target_users: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Send immediate notification with preference filtering and throttling.
        
        Args:
            notification_type: Type of notification
            subject: Email subject
            template_name: Template file name
            context: Template context variables
            priority: Notification priority
            target_users: Specific users to target (None for all)
            
        Returns:
            Dictionary with sending results
        """
        try:
            # Apply pre-send filters
            for filter_func in self.pre_send_filters:
                if not filter_func(notification_type, subject, context, priority):
                    return {
                        'success': False,
                        'message': 'Notification filtered out by pre-send filter',
                        'sent_count': 0,
                        'filtered_count': 0
                    }
            
            # Get eligible recipients
            eligible_recipients = []
            filtered_count = 0
            
            target_preferences = (
                [self.preferences[uid] for uid in target_users if uid in self.preferences]
                if target_users else list(self.preferences.values())
            )
            
            for prefs in target_preferences:
                # Check if user should receive this notification
                if not prefs.should_receive(notification_type, priority):
                    filtered_count += 1
                    continue
                
                # Check quiet hours (except for critical notifications)
                if priority != NotificationPriority.CRITICAL and prefs.is_in_quiet_hours():
                    filtered_count += 1
                    continue
                
                # Check throttling
                throttle_rule = prefs.throttle_rules.get(notification_type, ThrottleRule.DAILY)
                if not self.throttler.can_send_notification(
                    prefs.user_id, notification_type, throttle_rule, priority
                ):
                    filtered_count += 1
                    continue
                
                eligible_recipients.append(prefs)
            
            if not eligible_recipients:
                return {
                    'success': False,
                    'message': 'No eligible recipients after filtering',
                    'sent_count': 0,
                    'filtered_count': filtered_count
                }
            
            # Send notification
            notification_id = await self.email_service.send_template_notification(
                template_name=template_name,
                subject=subject,
                context=context,
                priority=priority,
                notification_type=notification_type.value
            )
            
            # Record throttling for successful sends
            for prefs in eligible_recipients:
                self.throttler.record_notification(prefs.user_id)
            
            # Record in history
            history = NotificationHistory(
                notification_id=notification_id,
                notification_type=notification_type,
                subject=subject,
                recipients=[prefs.email for prefs in eligible_recipients],
                priority=priority,
                sent_at=datetime.now(),
                delivery_status={},  # Will be updated by post-send hooks
                template_used=template_name,
                context_hash=self._hash_context(context)
            )
            
            self.notification_history.append(history)
            self._save_history_to_database(history)
            
            # Apply post-send hooks
            for hook_func in self.post_send_hooks:
                try:
                    hook_func(notification_id, notification_type, eligible_recipients)
                except Exception as e:
                    logger.error(f"Post-send hook failed: {e}")
            
            return {
                'success': True,
                'message': f'Notification sent to {len(eligible_recipients)} recipients',
                'notification_id': notification_id,
                'sent_count': len(eligible_recipients),
                'filtered_count': filtered_count,
                'recipients': [prefs.email for prefs in eligible_recipients]
            }
            
        except Exception as e:
            logger.error(f"Failed to send immediate notification: {e}")
            return {
                'success': False,
                'message': f'Failed to send notification: {e}',
                'sent_count': 0,
                'filtered_count': 0
            }
    
    def start_scheduler(self) -> None:
        """Start the notification scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.shutdown_event.clear()
        
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="NotificationScheduler",
            daemon=True
        )
        self.scheduler_thread.start()
        
        logger.info("Notification scheduler started")
    
    def stop_scheduler(self) -> None:
        """Stop the notification scheduler."""
        if not self.running:
            return
        
        logger.info("Stopping notification scheduler...")
        self.running = False
        self.shutdown_event.set()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5.0)
        
        logger.info("Notification scheduler stopped")
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop for processing scheduled notifications."""
        while self.running and not self.shutdown_event.is_set():
            try:
                current_time = datetime.now()
                
                # Process scheduled notifications
                for notification_id, notification in list(self.scheduled_notifications.items()):
                    if notification.status != "pending":
                        continue
                    
                    if notification.scheduled_at <= current_time:
                        asyncio.create_task(self._process_scheduled_notification(notification))
                
                # Sleep for a short interval
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                time.sleep(30)  # Wait longer on error
    
    async def _process_scheduled_notification(self, notification: ScheduledNotification) -> None:
        """Process a scheduled notification."""
        try:
            notification.attempts += 1
            notification.last_attempt = datetime.now()
            
            # Check conditions if any
            if notification.conditions and not self._check_conditions(notification.conditions):
                logger.info(f"Conditions not met for notification {notification.notification_id}")
                
                # Reschedule if recurring
                if notification.recurring:
                    self._reschedule_notification(notification)
                else:
                    notification.status = "cancelled"
                
                self._save_scheduled_notification_to_database(notification)
                return
            
            # Send notification
            result = await self.send_immediate_notification(
                notification_type=notification.notification_type,
                subject=notification.subject,
                template_name=notification.template_name,
                context=notification.context,
                priority=notification.priority
            )
            
            if result['success']:
                notification.status = "sent"
                logger.info(f"Sent scheduled notification {notification.notification_id}")
                
                # Reschedule if recurring
                if notification.recurring:
                    self._reschedule_notification(notification)
            else:
                if notification.attempts >= notification.max_attempts:
                    notification.status = "failed"
                    logger.error(f"Scheduled notification {notification.notification_id} failed after {notification.attempts} attempts")
                else:
                    # Retry later
                    notification.scheduled_at = datetime.now() + timedelta(minutes=5 * notification.attempts)
                    logger.info(f"Rescheduling failed notification {notification.notification_id} for retry")
            
            self._save_scheduled_notification_to_database(notification)
            
        except Exception as e:
            logger.error(f"Failed to process scheduled notification {notification.notification_id}: {e}")
            notification.status = "failed"
            self._save_scheduled_notification_to_database(notification)
    
    def _check_conditions(self, conditions: Dict[str, Any]) -> bool:
        """Check if conditions are met for sending notification."""
        # Implement condition checking logic
        # This could check system status, storage levels, etc.
        return True  # Placeholder implementation
    
    def _reschedule_notification(self, notification: ScheduledNotification) -> None:
        """Reschedule a recurring notification."""
        if not notification.recurrence_pattern:
            return
        
        # Simple recurrence patterns (could be extended with cron-like syntax)
        if notification.recurrence_pattern == "daily":
            notification.scheduled_at += timedelta(days=1)
        elif notification.recurrence_pattern == "weekly":
            notification.scheduled_at += timedelta(weeks=1)
        elif notification.recurrence_pattern == "monthly":
            notification.scheduled_at += timedelta(days=30)
        
        notification.status = "pending"
        notification.attempts = 0
        notification.last_attempt = None
    
    def _hash_context(self, context: Dict[str, Any]) -> str:
        """Generate hash of context for deduplication."""
        import hashlib
        context_str = json.dumps(context, sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()
    
    def _save_preferences_to_database(self, preferences: NotificationPreferences) -> None:
        """Save preferences to database."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO notification_preferences 
                    (user_id, email, preferences_json, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    preferences.user_id,
                    preferences.email,
                    json.dumps(preferences.to_dict())
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save preferences to database: {e}")
    
    def _save_scheduled_notification_to_database(self, notification: ScheduledNotification) -> None:
        """Save scheduled notification to database."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO scheduled_notifications 
                    (notification_id, notification_json, created_at)
                    VALUES (?, ?, ?)
                ''', (
                    notification.notification_id,
                    json.dumps(notification.to_dict()),
                    notification.created_at.isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save scheduled notification to database: {e}")
    
    def _save_history_to_database(self, history: NotificationHistory) -> None:
        """Save notification history to database."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO notification_history 
                    (notification_id, history_json, sent_at)
                    VALUES (?, ?, ?)
                ''', (
                    history.notification_id,
                    json.dumps(history.to_dict()),
                    history.sent_at.isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save history to database: {e}")
    
    def add_pre_send_filter(self, filter_func: Callable) -> None:
        """Add a pre-send filter function."""
        self.pre_send_filters.append(filter_func)
    
    def add_post_send_hook(self, hook_func: Callable) -> None:
        """Add a post-send hook function."""
        self.post_send_hooks.append(hook_func)
    
    def get_user_preferences(self, user_id: str) -> Optional[NotificationPreferences]:
        """Get preferences for a specific user."""
        return self.preferences.get(user_id)
    
    def get_scheduled_notifications(self, 
                                  notification_type: Optional[NotificationType] = None,
                                  status: Optional[str] = None) -> List[ScheduledNotification]:
        """Get scheduled notifications with optional filtering."""
        notifications = list(self.scheduled_notifications.values())
        
        if notification_type:
            notifications = [n for n in notifications if n.notification_type == notification_type]
        
        if status:
            notifications = [n for n in notifications if n.status == status]
        
        return notifications
    
    def get_notification_history(self, 
                               days: int = 30,
                               notification_type: Optional[NotificationType] = None) -> List[NotificationHistory]:
        """Get notification history with optional filtering."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        history = [h for h in self.notification_history if h.sent_at > cutoff_date]
        
        if notification_type:
            history = [h for h in history if h.notification_type == notification_type]
        
        return history
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get notification scheduler statistics."""
        total_scheduled = len(self.scheduled_notifications)
        pending_scheduled = len([n for n in self.scheduled_notifications.values() if n.status == "pending"])
        
        # Recent history stats
        recent_history = self.get_notification_history(days=7)
        
        return {
            'total_users': len(self.preferences),
            'active_users': len([p for p in self.preferences.values() if p.enabled]),
            'total_scheduled': total_scheduled,
            'pending_scheduled': pending_scheduled,
            'recent_notifications_7d': len(recent_history),
            'scheduler_running': self.running,
            'throttler_status': {
                user_id: self.throttler.get_throttle_status(user_id)
                for user_id in list(self.preferences.keys())[:5]  # Sample of users
            }
        }
    
    def cleanup_old_data(self, days: int = 90) -> Dict[str, int]:
        """Clean up old notification history and completed scheduled notifications."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Clean history
        old_history_count = len([h for h in self.notification_history if h.sent_at < cutoff_date])
        self.notification_history = [h for h in self.notification_history if h.sent_at >= cutoff_date]
        
        # Clean completed scheduled notifications
        old_scheduled_count = 0
        for notif_id, notification in list(self.scheduled_notifications.items()):
            if (notification.status in ["sent", "failed", "cancelled"] and 
                notification.created_at < cutoff_date):
                del self.scheduled_notifications[notif_id]
                old_scheduled_count += 1
        
        # Clean database
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Clean old history
                cursor.execute(
                    'DELETE FROM notification_history WHERE sent_at < ?',
                    (cutoff_date.isoformat(),)
                )
                
                # Clean old scheduled notifications
                cursor.execute('''
                    DELETE FROM scheduled_notifications 
                    WHERE created_at < ? AND notification_json LIKE '%"status": "sent"%'
                       OR notification_json LIKE '%"status": "failed"%'
                       OR notification_json LIKE '%"status": "cancelled"%'
                ''', (cutoff_date.isoformat(),))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to cleanup database: {e}")
        
        logger.info(f"Cleaned up {old_history_count} old history records and {old_scheduled_count} old scheduled notifications")
        
        return {
            'history_cleaned': old_history_count,
            'scheduled_cleaned': old_scheduled_count
        }
    
    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.stop_scheduler()
        except:
            pass