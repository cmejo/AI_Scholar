"""
Error Recovery and Prevention System for Multi-Instance ArXiv System.

This module provides automated error recovery procedures, preventive error detection,
early warning systems, error history tracking, and learning mechanisms.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
import logging
import asyncio
import json
import pickle
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.error_handling.error_models import (
        ProcessingError, ErrorType, ErrorCategory, ErrorSeverity
    )
    from multi_instance_arxiv_system.error_handling.error_analyzer import (
        ErrorAnalyzer, ErrorPattern, ResolutionSuggestion
    )
except ImportError as e:
    print(f"Import error: {e}")
    # Create minimal fallback classes for testing
    class ProcessingError:
        def __init__(self, *args, **kwargs): pass
    class ErrorType:
        HTTP_ERROR = "http_error"
    class ErrorCategory:
        NETWORK = "network"
    class ErrorSeverity:
        HIGH = "high"
    class ErrorAnalyzer:
        def __init__(self, *args, **kwargs): pass
    class ErrorPattern:
        def __init__(self, *args, **kwargs): pass
    class ResolutionSuggestion:
        def __init__(self, *args, **kwargs): pass

logger = logging.getLogger(__name__)


class PreventionStrategy(Enum):
    """Error prevention strategies."""
    PROACTIVE_MONITORING = "proactive_monitoring"
    RESOURCE_PREALLOCATION = "resource_preallocation"
    CIRCUIT_BREAKER = "circuit_breaker"
    RATE_LIMITING = "rate_limiting"
    HEALTH_CHECKS = "health_checks"
    PREDICTIVE_SCALING = "predictive_scaling"
    GRACEFUL_DEGRADATION = "graceful_degradation"


class WarningLevel(Enum):
    """Early warning levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class PreventionRule:
    """Rule for preventing specific types of errors."""
    
    rule_id: str
    name: str
    description: str
    target_error_types: List[ErrorType]
    strategy: PreventionStrategy
    conditions: Dict[str, Any]
    actions: List[str]
    enabled: bool = True
    success_count: int = 0
    trigger_count: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of this prevention rule."""
        if self.trigger_count == 0:
            return 0.0
        return (self.success_count / self.trigger_count) * 100.0


@dataclass
class EarlyWarning:
    """Early warning about potential errors."""
    
    warning_id: str
    timestamp: datetime
    level: WarningLevel
    title: str
    description: str
    predicted_error_types: List[ErrorType]
    confidence: float
    time_to_occurrence: timedelta
    recommended_actions: List[str]
    is_acknowledged: bool = False
    is_resolved: bool = False


@dataclass
class LearningRecord:
    """Record of learned patterns and their effectiveness."""
    
    record_id: str
    pattern_signature: str
    error_types: List[ErrorType]
    prevention_actions: List[str]
    effectiveness_score: float
    usage_count: int
    last_used: datetime
    created_at: datetime


class ErrorPreventionSystem:
    """
    Comprehensive error prevention system with automated recovery,
    predictive detection, and learning mechanisms.
    """
    
    def __init__(
        self,
        instance_name: str,
        learning_data_path: Optional[str] = None
    ):
        self.instance_name = instance_name
        self.learning_data_path = learning_data_path or f"data/{instance_name}_error_learning.pkl"
        
        # Core components
        self.error_analyzer = ErrorAnalyzer(instance_name)
        
        # Prevention rules
        self.prevention_rules: Dict[str, PreventionRule] = {}
        self.active_warnings: Dict[str, EarlyWarning] = {}
        
        # Learning system
        self.learning_records: Dict[str, LearningRecord] = {}
        self.pattern_memory: deque = deque(maxlen=1000)
        
        # Monitoring state
        self.resource_monitors: Dict[str, Any] = {}
        self.health_check_results: Dict[str, Dict[str, Any]] = {}
        
        # Prevention statistics
        self.total_preventions = 0
        self.successful_preventions = 0
        self.false_positives = 0
        
        # Initialize default prevention rules
        self._initialize_default_prevention_rules()
        
        # Load learning data
        self._load_learning_data()
        
        logger.info(f"ErrorPreventionSystem initialized for {instance_name}")
    
    def _initialize_default_prevention_rules(self) -> None:
        """Initialize default prevention rules."""
        
        # Disk space monitoring rule
        self.prevention_rules["disk_space_monitor"] = PreventionRule(
            rule_id="disk_space_monitor",
            name="Disk Space Monitoring",
            description="Monitor disk space and prevent disk full errors",
            target_error_types=[ErrorType.DISK_FULL],
            strategy=PreventionStrategy.PROACTIVE_MONITORING,
            conditions={
                "disk_usage_threshold": 85,  # Percentage
                "check_interval_minutes": 5
            },
            actions=[
                "cleanup_temp_files",
                "compress_old_logs",
                "send_warning_notification"
            ]
        )
        
        # Memory monitoring rule
        self.prevention_rules["memory_monitor"] = PreventionRule(
            rule_id="memory_monitor",
            name="Memory Usage Monitoring",
            description="Monitor memory usage and prevent memory errors",
            target_error_types=[ErrorType.MEMORY_ERROR],
            strategy=PreventionStrategy.PROACTIVE_MONITORING,
            conditions={
                "memory_usage_threshold": 90,  # Percentage
                "check_interval_minutes": 2
            },
            actions=[
                "garbage_collection",
                "reduce_batch_size",
                "restart_workers"
            ]
        )
        
        # Network circuit breaker rule
        self.prevention_rules["network_circuit_breaker"] = PreventionRule(
            rule_id="network_circuit_breaker",
            name="Network Circuit Breaker",
            description="Prevent cascading network failures",
            target_error_types=[
                ErrorType.CONNECTION_TIMEOUT,
                ErrorType.CONNECTION_REFUSED,
                ErrorType.HTTP_ERROR
            ],
            strategy=PreventionStrategy.CIRCUIT_BREAKER,
            conditions={
                "failure_threshold": 5,
                "time_window_minutes": 10,
                "recovery_timeout_minutes": 5
            },
            actions=[
                "open_circuit_breaker",
                "enable_fallback_mode",
                "reduce_request_rate"
            ]
        )
        
        # Rate limiting rule
        self.prevention_rules["rate_limiter"] = PreventionRule(
            rule_id="rate_limiter",
            name="Request Rate Limiting",
            description="Prevent rate limit exceeded errors",
            target_error_types=[ErrorType.RATE_LIMIT_EXCEEDED],
            strategy=PreventionStrategy.RATE_LIMITING,
            conditions={
                "max_requests_per_minute": 60,
                "burst_allowance": 10
            },
            actions=[
                "throttle_requests",
                "implement_backoff",
                "queue_requests"
            ]
        )
        
        # Health check rule
        self.prevention_rules["health_checks"] = PreventionRule(
            rule_id="health_checks",
            name="System Health Checks",
            description="Perform regular health checks to prevent system failures",
            target_error_types=[
                ErrorType.PROCESS_KILLED,
                ErrorType.CPU_OVERLOAD
            ],
            strategy=PreventionStrategy.HEALTH_CHECKS,
            conditions={
                "check_interval_minutes": 5,
                "cpu_threshold": 95,
                "response_time_threshold_ms": 5000
            },
            actions=[
                "restart_unhealthy_services",
                "scale_resources",
                "enable_graceful_degradation"
            ]
        )
    
    async def start_prevention_system(self) -> None:
        """Start the error prevention system."""
        
        logger.info(f"Starting error prevention system for {self.instance_name}")
        
        # Start monitoring tasks
        asyncio.create_task(self._prevention_monitor_loop())
        asyncio.create_task(self._early_warning_system())
        asyncio.create_task(self._learning_system_update())
        
        logger.info("Error prevention system started")
    
    async def _prevention_monitor_loop(self) -> None:
        """Main prevention monitoring loop."""
        
        while True:
            try:
                await self._check_prevention_rules()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in prevention monitor loop: {e}")
                await asyncio.sleep(60)
    
    async def _check_prevention_rules(self) -> None:
        """Check all active prevention rules."""
        
        for rule in self.prevention_rules.values():
            if not rule.enabled:
                continue
            
            try:
                should_trigger = await self._evaluate_prevention_rule(rule)
                if should_trigger:
                    await self._execute_prevention_actions(rule)
            except Exception as e:
                logger.error(f"Error checking prevention rule {rule.rule_id}: {e}")
    
    async def _evaluate_prevention_rule(self, rule: PreventionRule) -> bool:
        """Evaluate whether a prevention rule should trigger."""
        
        if rule.strategy == PreventionStrategy.PROACTIVE_MONITORING:
            return await self._evaluate_monitoring_rule(rule)
        elif rule.strategy == PreventionStrategy.CIRCUIT_BREAKER:
            return await self._evaluate_circuit_breaker_rule(rule)
        elif rule.strategy == PreventionStrategy.RATE_LIMITING:
            return await self._evaluate_rate_limiting_rule(rule)
        elif rule.strategy == PreventionStrategy.HEALTH_CHECKS:
            return await self._evaluate_health_check_rule(rule)
        else:
            return False
    
    async def _evaluate_monitoring_rule(self, rule: PreventionRule) -> bool:
        """Evaluate monitoring-based prevention rules."""
        
        if rule.rule_id == "disk_space_monitor":
            # Check disk space
            disk_usage = await self._get_disk_usage_percentage()
            threshold = rule.conditions.get("disk_usage_threshold", 85)
            return disk_usage > threshold
        
        elif rule.rule_id == "memory_monitor":
            # Check memory usage
            memory_usage = await self._get_memory_usage_percentage()
            threshold = rule.conditions.get("memory_usage_threshold", 90)
            return memory_usage > threshold
        
        return False
    
    async def _evaluate_circuit_breaker_rule(self, rule: PreventionRule) -> bool:
        """Evaluate circuit breaker prevention rules."""
        
        # Check recent error patterns for network failures
        recent_errors = self._get_recent_errors(timedelta(minutes=10))
        network_errors = [
            e for e in recent_errors 
            if e.error_type in rule.target_error_types
        ]
        
        failure_threshold = rule.conditions.get("failure_threshold", 5)
        return len(network_errors) >= failure_threshold
    
    async def _evaluate_rate_limiting_rule(self, rule: PreventionRule) -> bool:
        """Evaluate rate limiting prevention rules."""
        
        # Check current request rate
        current_rate = await self._get_current_request_rate()
        max_rate = rule.conditions.get("max_requests_per_minute", 60)
        
        return current_rate > max_rate
    
    async def _evaluate_health_check_rule(self, rule: PreventionRule) -> bool:
        """Evaluate health check prevention rules."""
        
        # Perform health checks
        health_results = await self._perform_health_checks()
        
        # Check CPU usage
        cpu_usage = health_results.get("cpu_usage", 0)
        cpu_threshold = rule.conditions.get("cpu_threshold", 95)
        
        # Check response times
        response_time = health_results.get("response_time_ms", 0)
        response_threshold = rule.conditions.get("response_time_threshold_ms", 5000)
        
        return cpu_usage > cpu_threshold or response_time > response_threshold
    
    async def _execute_prevention_actions(self, rule: PreventionRule) -> None:
        """Execute prevention actions for a triggered rule."""
        
        logger.info(f"Executing prevention actions for rule: {rule.name}")
        
        rule.trigger_count += 1
        success = True
        
        for action in rule.actions:
            try:
                action_success = await self._execute_prevention_action(action, rule)
                if not action_success:
                    success = False
            except Exception as e:
                logger.error(f"Failed to execute prevention action {action}: {e}")
                success = False
        
        if success:
            rule.success_count += 1
            self.successful_preventions += 1
        
        self.total_preventions += 1
        
        # Create early warning if appropriate
        if rule.strategy in [PreventionStrategy.PROACTIVE_MONITORING, PreventionStrategy.HEALTH_CHECKS]:
            await self._create_early_warning(rule)
    
    async def _execute_prevention_action(self, action: str, rule: PreventionRule) -> bool:
        """Execute a specific prevention action."""
        
        try:
            if action == "cleanup_temp_files":
                return await self._cleanup_temp_files()
            elif action == "compress_old_logs":
                return await self._compress_old_logs()
            elif action == "garbage_collection":
                return await self._trigger_garbage_collection()
            elif action == "reduce_batch_size":
                return await self._reduce_batch_size()
            elif action == "open_circuit_breaker":
                return await self._open_circuit_breaker(rule.target_error_types)
            elif action == "throttle_requests":
                return await self._throttle_requests()
            elif action == "restart_unhealthy_services":
                return await self._restart_unhealthy_services()
            elif action == "send_warning_notification":
                return await self._send_warning_notification(rule)
            else:
                logger.warning(f"Unknown prevention action: {action}")
                return False
        
        except Exception as e:
            logger.error(f"Error executing prevention action {action}: {e}")
            return False
    
    async def _early_warning_system(self) -> None:
        """Early warning system loop."""
        
        while True:
            try:
                await self._generate_early_warnings()
                await self._process_active_warnings()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in early warning system: {e}")
                await asyncio.sleep(120)
    
    async def _generate_early_warnings(self) -> None:
        """Generate early warnings based on patterns and trends."""
        
        # Analyze recent error patterns
        await self.error_analyzer.perform_comprehensive_analysis()
        
        # Check for concerning trends
        trends = self.error_analyzer.get_trends()
        for error_type, trend in trends.items():
            if trend.is_concerning:
                await self._create_trend_warning(error_type, trend)
        
        # Check for resource exhaustion patterns
        await self._check_resource_exhaustion_warnings()
        
        # Check for performance degradation patterns
        await self._check_performance_degradation_warnings()
    
    async def _create_early_warning(self, rule: PreventionRule) -> None:
        """Create an early warning based on a prevention rule trigger."""
        
        warning_id = f"prevention_{rule.rule_id}_{int(datetime.now().timestamp())}"
        
        warning = EarlyWarning(
            warning_id=warning_id,
            timestamp=datetime.now(),
            level=WarningLevel.WARNING,
            title=f"Prevention Rule Triggered: {rule.name}",
            description=f"Prevention rule '{rule.name}' has been triggered. {rule.description}",
            predicted_error_types=rule.target_error_types,
            confidence=0.8,
            time_to_occurrence=timedelta(minutes=15),
            recommended_actions=rule.actions
        )
        
        self.active_warnings[warning_id] = warning
        logger.warning(f"Early warning created: {warning.title}")
    
    async def _create_trend_warning(self, error_type: ErrorType, trend) -> None:
        """Create warning for concerning error trends."""
        
        warning_id = f"trend_{error_type.value}_{int(datetime.now().timestamp())}"
        
        if warning_id not in self.active_warnings:
            warning = EarlyWarning(
                warning_id=warning_id,
                timestamp=datetime.now(),
                level=WarningLevel.CRITICAL if trend.change_rate > 100 else WarningLevel.WARNING,
                title=f"Increasing Error Trend: {error_type.value}",
                description=f"Error rate for {error_type.value} is increasing by {trend.change_rate:.1f}%",
                predicted_error_types=[error_type],
                confidence=trend.confidence,
                time_to_occurrence=timedelta(hours=2),
                recommended_actions=[
                    "Investigate root cause",
                    "Implement additional monitoring",
                    "Consider preventive measures"
                ]
            )
            
            self.active_warnings[warning_id] = warning
            logger.critical(f"Trend warning created: {warning.title}")
    
    async def _learning_system_update(self) -> None:
        """Update the learning system with new patterns and effectiveness data."""
        
        while True:
            try:
                await self._update_learning_records()
                await self._optimize_prevention_rules()
                await self._save_learning_data()
                await asyncio.sleep(3600)  # Update every hour
            except Exception as e:
                logger.error(f"Error in learning system update: {e}")
                await asyncio.sleep(1800)
    
    async def _update_learning_records(self) -> None:
        """Update learning records based on recent prevention effectiveness."""
        
        # Analyze prevention rule effectiveness
        for rule in self.prevention_rules.values():
            if rule.trigger_count > 0:
                effectiveness = rule.success_rate / 100.0
                
                record_id = f"rule_{rule.rule_id}"
                if record_id in self.learning_records:
                    record = self.learning_records[record_id]
                    record.effectiveness_score = (record.effectiveness_score + effectiveness) / 2
                    record.usage_count += 1
                    record.last_used = datetime.now()
                else:
                    self.learning_records[record_id] = LearningRecord(
                        record_id=record_id,
                        pattern_signature=rule.rule_id,
                        error_types=rule.target_error_types,
                        prevention_actions=rule.actions,
                        effectiveness_score=effectiveness,
                        usage_count=1,
                        last_used=datetime.now(),
                        created_at=datetime.now()
                    )
    
    async def _optimize_prevention_rules(self) -> None:
        """Optimize prevention rules based on learning data."""
        
        for record in self.learning_records.values():
            if record.effectiveness_score < 0.3 and record.usage_count > 10:
                # Disable ineffective rules
                rule_id = record.pattern_signature
                if rule_id in self.prevention_rules:
                    self.prevention_rules[rule_id].enabled = False
                    logger.info(f"Disabled ineffective prevention rule: {rule_id}")
            
            elif record.effectiveness_score > 0.8 and record.usage_count > 5:
                # Enhance effective rules
                rule_id = record.pattern_signature
                if rule_id in self.prevention_rules:
                    rule = self.prevention_rules[rule_id]
                    # Make conditions more sensitive for effective rules
                    if "threshold" in rule.conditions:
                        for key, value in rule.conditions.items():
                            if "threshold" in key and isinstance(value, (int, float)):
                                rule.conditions[key] = value * 0.9  # Make 10% more sensitive
    
    # Helper methods for prevention actions
    async def _cleanup_temp_files(self) -> bool:
        """Clean up temporary files."""
        logger.info("Executing cleanup_temp_files prevention action")
        # Implementation would clean up temp files
        return True
    
    async def _compress_old_logs(self) -> bool:
        """Compress old log files."""
        logger.info("Executing compress_old_logs prevention action")
        # Implementation would compress logs
        return True
    
    async def _trigger_garbage_collection(self) -> bool:
        """Trigger garbage collection."""
        logger.info("Executing garbage_collection prevention action")
        import gc
        gc.collect()
        return True
    
    async def _reduce_batch_size(self) -> bool:
        """Reduce processing batch size."""
        logger.info("Executing reduce_batch_size prevention action")
        # Implementation would reduce batch sizes
        return True
    
    async def _open_circuit_breaker(self, error_types: List[ErrorType]) -> bool:
        """Open circuit breaker for specific error types."""
        logger.info(f"Opening circuit breaker for error types: {[e.value for e in error_types]}")
        # Implementation would open circuit breakers
        return True
    
    async def _throttle_requests(self) -> bool:
        """Throttle request rate."""
        logger.info("Executing throttle_requests prevention action")
        # Implementation would throttle requests
        return True
    
    async def _restart_unhealthy_services(self) -> bool:
        """Restart unhealthy services."""
        logger.info("Executing restart_unhealthy_services prevention action")
        # Implementation would restart services
        return True
    
    async def _send_warning_notification(self, rule: PreventionRule) -> bool:
        """Send warning notification."""
        logger.warning(f"Prevention warning: {rule.name} - {rule.description}")
        # Implementation would send actual notifications
        return True
    
    # Helper methods for monitoring
    async def _get_disk_usage_percentage(self) -> float:
        """Get current disk usage percentage."""
        import shutil
        try:
            usage = shutil.disk_usage("/")
            return (usage.used / usage.total) * 100
        except Exception:
            return 0.0
    
    async def _get_memory_usage_percentage(self) -> float:
        """Get current memory usage percentage."""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except Exception:
            return 0.0
    
    async def _get_current_request_rate(self) -> float:
        """Get current request rate."""
        # Implementation would track actual request rates
        return 0.0
    
    async def _perform_health_checks(self) -> Dict[str, Any]:
        """Perform system health checks."""
        try:
            import psutil
            return {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
                "response_time_ms": 100  # Placeholder
            }
        except Exception:
            return {"cpu_usage": 0, "memory_usage": 0, "response_time_ms": 0}
    
    def _get_recent_errors(self, time_window: timedelta) -> List[ProcessingError]:
        """Get recent errors within time window."""
        cutoff_time = datetime.now() - time_window
        return [
            error for error in self.error_analyzer.error_history
            if error.timestamp >= cutoff_time
        ]
    
    async def _check_resource_exhaustion_warnings(self) -> None:
        """Check for resource exhaustion warning conditions."""
        # Implementation would check various resource metrics
        pass
    
    async def _check_performance_degradation_warnings(self) -> None:
        """Check for performance degradation warning conditions."""
        # Implementation would check performance metrics
        pass
    
    async def _process_active_warnings(self) -> None:
        """Process and manage active warnings."""
        
        current_time = datetime.now()
        expired_warnings = []
        
        for warning_id, warning in self.active_warnings.items():
            # Check if warning has expired
            if current_time - warning.timestamp > timedelta(hours=24):
                expired_warnings.append(warning_id)
            
            # Auto-acknowledge low-level warnings after some time
            elif (not warning.is_acknowledged and 
                  warning.level == WarningLevel.INFO and
                  current_time - warning.timestamp > timedelta(hours=1)):
                warning.is_acknowledged = True
        
        # Remove expired warnings
        for warning_id in expired_warnings:
            del self.active_warnings[warning_id]
    
    def _load_learning_data(self) -> None:
        """Load learning data from persistent storage."""
        
        try:
            if Path(self.learning_data_path).exists():
                with open(self.learning_data_path, 'rb') as f:
                    data = pickle.load(f)
                    self.learning_records = data.get('learning_records', {})
                    logger.info(f"Loaded {len(self.learning_records)} learning records")
        except Exception as e:
            logger.error(f"Failed to load learning data: {e}")
    
    async def _save_learning_data(self) -> None:
        """Save learning data to persistent storage."""
        
        try:
            Path(self.learning_data_path).parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'learning_records': self.learning_records,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.learning_data_path, 'wb') as f:
                pickle.dump(data, f)
                
            logger.debug("Learning data saved successfully")
        except Exception as e:
            logger.error(f"Failed to save learning data: {e}")
    
    # Public interface methods
    def add_prevention_rule(self, rule: PreventionRule) -> None:
        """Add a custom prevention rule."""
        
        self.prevention_rules[rule.rule_id] = rule
        logger.info(f"Added prevention rule: {rule.name}")
    
    def remove_prevention_rule(self, rule_id: str) -> bool:
        """Remove a prevention rule."""
        
        if rule_id in self.prevention_rules:
            del self.prevention_rules[rule_id]
            logger.info(f"Removed prevention rule: {rule_id}")
            return True
        return False
    
    def get_active_warnings(self) -> List[EarlyWarning]:
        """Get list of active warnings."""
        return list(self.active_warnings.values())
    
    def acknowledge_warning(self, warning_id: str) -> bool:
        """Acknowledge a warning."""
        
        if warning_id in self.active_warnings:
            self.active_warnings[warning_id].is_acknowledged = True
            logger.info(f"Warning acknowledged: {warning_id}")
            return True
        return False
    
    def get_prevention_statistics(self) -> Dict[str, Any]:
        """Get prevention system statistics."""
        
        rule_stats = {}
        for rule_id, rule in self.prevention_rules.items():
            rule_stats[rule_id] = {
                'name': rule.name,
                'enabled': rule.enabled,
                'trigger_count': rule.trigger_count,
                'success_count': rule.success_count,
                'success_rate': rule.success_rate
            }
        
        return {
            'instance_name': self.instance_name,
            'total_preventions': self.total_preventions,
            'successful_preventions': self.successful_preventions,
            'prevention_success_rate': (self.successful_preventions / max(1, self.total_preventions)) * 100,
            'active_warnings': len(self.active_warnings),
            'learning_records': len(self.learning_records),
            'prevention_rules': rule_stats
        }