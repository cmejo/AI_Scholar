"""
Safety monitoring system for the RL framework.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import deque, defaultdict
import numpy as np
from dataclasses import dataclass
from enum import Enum

from ..core.config import SafetyConfig
from ..models.conversation_models import ConversationState, Action
from ..models.reward_models import MultiObjectiveReward

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert levels for safety monitoring."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SafetyAlert:
    """Represents a safety alert."""
    alert_id: str
    alert_type: str
    level: AlertLevel
    message: str
    timestamp: datetime
    context: Dict[str, Any]
    resolved: bool = False


class AnomalyDetector:
    """Detects anomalies in RL system behavior."""
    
    def __init__(self, config: SafetyConfig):
        self.config = config
        self.reward_history = deque(maxlen=1000)
        self.response_length_history = deque(maxlen=1000)
        self.safety_score_history = deque(maxlen=1000)
        self.anomaly_threshold = config.anomaly_detection_sensitivity
    
    async def detect_reward_anomalies(self, reward: MultiObjectiveReward) -> List[SafetyAlert]:
        """Detect anomalies in reward signals."""
        
        alerts = []
        
        # Add current reward to history
        self.reward_history.append(reward.total_reward)
        
        if len(self.reward_history) < 50:  # Need sufficient history
            return alerts
        
        # Calculate statistics
        recent_rewards = list(self.reward_history)[-20:]
        historical_rewards = list(self.reward_history)[:-20]
        
        recent_mean = np.mean(recent_rewards)
        historical_mean = np.mean(historical_rewards)
        historical_std = np.std(historical_rewards)
        
        # Detect sudden drops in reward
        if recent_mean < historical_mean - 2 * historical_std:
            alerts.append(SafetyAlert(
                alert_id=f"reward_drop_{datetime.now().timestamp()}",
                alert_type="reward_anomaly",
                level=AlertLevel.HIGH,
                message=f"Sudden drop in reward detected: {recent_mean:.3f} vs {historical_mean:.3f}",
                timestamp=datetime.now(),
                context={
                    "recent_mean": recent_mean,
                    "historical_mean": historical_mean,
                    "deviation": (recent_mean - historical_mean) / historical_std
                }
            ))
        
        # Detect extremely high rewards (possible gaming)
        if reward.total_reward > historical_mean + 3 * historical_std:
            alerts.append(SafetyAlert(
                alert_id=f"reward_spike_{datetime.now().timestamp()}",
                alert_type="reward_anomaly",
                level=AlertLevel.MEDIUM,
                message=f"Unusually high reward detected: {reward.total_reward:.3f}",
                timestamp=datetime.now(),
                context={
                    "reward_value": reward.total_reward,
                    "historical_mean": historical_mean,
                    "z_score": (reward.total_reward - historical_mean) / historical_std
                }
            ))
        
        # Detect safety score anomalies
        self.safety_score_history.append(reward.safety)
        
        if len(self.safety_score_history) >= 20:
            recent_safety = np.mean(list(self.safety_score_history)[-10:])
            
            if recent_safety < 0.5:  # Low safety scores
                alerts.append(SafetyAlert(
                    alert_id=f"safety_decline_{datetime.now().timestamp()}",
                    alert_type="safety_anomaly",
                    level=AlertLevel.CRITICAL,
                    message=f"Safety scores declining: {recent_safety:.3f}",
                    timestamp=datetime.now(),
                    context={
                        "recent_safety_score": recent_safety,
                        "safety_threshold": 0.5
                    }
                ))
        
        return alerts
    
    async def detect_response_anomalies(self, response_text: str, action: Action) -> List[SafetyAlert]:
        """Detect anomalies in response generation."""
        
        alerts = []
        response_length = len(response_text)
        
        # Add to history
        self.response_length_history.append(response_length)
        
        if len(self.response_length_history) < 30:
            return alerts
        
        # Calculate statistics
        lengths = list(self.response_length_history)
        mean_length = np.mean(lengths)
        std_length = np.std(lengths)
        
        # Detect extremely long responses
        if response_length > mean_length + 3 * std_length and response_length > 2000:
            alerts.append(SafetyAlert(
                alert_id=f"long_response_{datetime.now().timestamp()}",
                alert_type="response_anomaly",
                level=AlertLevel.MEDIUM,
                message=f"Unusually long response: {response_length} characters",
                timestamp=datetime.now(),
                context={
                    "response_length": response_length,
                    "mean_length": mean_length,
                    "z_score": (response_length - mean_length) / std_length
                }
            ))
        
        # Detect extremely short responses
        if response_length < mean_length - 2 * std_length and response_length < 20:
            alerts.append(SafetyAlert(
                alert_id=f"short_response_{datetime.now().timestamp()}",
                alert_type="response_anomaly",
                level=AlertLevel.LOW,
                message=f"Unusually short response: {response_length} characters",
                timestamp=datetime.now(),
                context={
                    "response_length": response_length,
                    "mean_length": mean_length
                }
            ))
        
        # Detect repetitive responses
        if self._is_repetitive_response(response_text):
            alerts.append(SafetyAlert(
                alert_id=f"repetitive_response_{datetime.now().timestamp()}",
                alert_type="response_anomaly",
                level=AlertLevel.MEDIUM,
                message="Repetitive response pattern detected",
                timestamp=datetime.now(),
                context={
                    "response_preview": response_text[:100]
                }
            ))
        
        return alerts
    
    def _is_repetitive_response(self, response_text: str) -> bool:
        """Check if response is repetitive."""
        
        # Simple repetition detection
        words = response_text.lower().split()
        
        if len(words) < 10:
            return False
        
        # Check for repeated phrases
        word_counts = defaultdict(int)
        for word in words:
            word_counts[word] += 1
        
        # If any word appears more than 30% of the time, it's repetitive
        max_count = max(word_counts.values())
        repetition_ratio = max_count / len(words)
        
        return repetition_ratio > 0.3


class BiasDetector:
    """Detects potential bias in responses."""
    
    def __init__(self, config: SafetyConfig):
        self.config = config
        self.bias_patterns = self._initialize_bias_patterns()
        self.bias_history = deque(maxlen=500)
    
    def _initialize_bias_patterns(self) -> Dict[str, List[str]]:
        """Initialize bias detection patterns."""
        
        return {
            "gender_bias": [
                r"\b(men|women|male|female) are (better|worse|more|less)\b",
                r"\b(he|she) (always|never|typically)\b",
                r"\btypical (man|woman|male|female)\b"
            ],
            "racial_bias": [
                r"\b(people from|those from) .* are\b",
                r"\ball .* people are\b",
                r"\btypical .* person\b"
            ],
            "age_bias": [
                r"\b(young|old) people (always|never|can't|cannot)\b",
                r"\btypical (teenager|elderly|senior)\b"
            ],
            "cultural_bias": [
                r"\b(culture|country|religion) .* (always|never|typically)\b",
                r"\ball (christians|muslims|jews|buddhists|hindus) are\b"
            ]
        }
    
    async def detect_bias(self, response_text: str, context: Dict[str, Any]) -> List[SafetyAlert]:
        """Detect potential bias in response."""
        
        alerts = []
        response_lower = response_text.lower()
        
        for bias_type, patterns in self.bias_patterns.items():
            for pattern in patterns:
                import re
                if re.search(pattern, response_lower):
                    alerts.append(SafetyAlert(
                        alert_id=f"bias_{bias_type}_{datetime.now().timestamp()}",
                        alert_type="bias_detection",
                        level=AlertLevel.MEDIUM,
                        message=f"Potential {bias_type} detected in response",
                        timestamp=datetime.now(),
                        context={
                            "bias_type": bias_type,
                            "pattern_matched": pattern,
                            "response_preview": response_text[:200]
                        }
                    ))
        
        # Record bias detection for trend analysis
        bias_score = len(alerts) / max(1, len(self.bias_patterns))
        self.bias_history.append({
            "timestamp": datetime.now(),
            "bias_score": bias_score,
            "bias_types": [alert.context["bias_type"] for alert in alerts]
        })
        
        return alerts
    
    def get_bias_trends(self) -> Dict[str, Any]:
        """Get bias detection trends."""
        
        if not self.bias_history:
            return {"no_data": True}
        
        recent_history = [entry for entry in self.bias_history 
                         if (datetime.now() - entry["timestamp"]).days <= 7]
        
        if not recent_history:
            return {"no_recent_data": True}
        
        # Calculate trends
        bias_scores = [entry["bias_score"] for entry in recent_history]
        avg_bias_score = np.mean(bias_scores)
        
        # Count bias types
        bias_type_counts = defaultdict(int)
        for entry in recent_history:
            for bias_type in entry["bias_types"]:
                bias_type_counts[bias_type] += 1
        
        return {
            "average_bias_score": avg_bias_score,
            "total_detections": len(recent_history),
            "bias_type_counts": dict(bias_type_counts),
            "trend": "increasing" if len(bias_scores) > 5 and bias_scores[-3:] > bias_scores[:3] else "stable"
        }


class HarmfulContentDetector:
    """Detects harmful content in responses."""
    
    def __init__(self, config: SafetyConfig):
        self.config = config
        self.harmful_patterns = self._initialize_harmful_patterns()
        self.detection_history = deque(maxlen=1000)
    
    def _initialize_harmful_patterns(self) -> Dict[str, List[str]]:
        """Initialize harmful content patterns."""
        
        return {
            "violence": [
                r"\b(kill|murder|violence|attack|harm|hurt|destroy)\b",
                r"\b(weapon|gun|knife|bomb|explosive)\b",
                r"\b(fight|battle|war|combat)\b"
            ],
            "self_harm": [
                r"\b(suicide|self.harm|cut yourself|hurt yourself)\b",
                r"\b(end it all|kill myself|harm myself)\b"
            ],
            "illegal_activity": [
                r"\b(steal|rob|fraud|scam|hack|piracy)\b",
                r"\b(illegal|criminal|break the law)\b",
                r"\b(drugs|cocaine|heroin|marijuana)\b"
            ],
            "hate_speech": [
                r"\b(hate|racist|sexist|homophobic|transphobic)\b",
                r"\b(discrimination|prejudice|bigotry)\b"
            ],
            "misinformation": [
                r"\b(fake news|conspiracy|hoax|lie)\b",
                r"\b(definitely false|completely wrong|total lie)\b"
            ]
        }
    
    async def detect_harmful_content(self, response_text: str, context: Dict[str, Any]) -> List[SafetyAlert]:
        """Detect harmful content in response."""
        
        alerts = []
        response_lower = response_text.lower()
        
        for harm_type, patterns in self.harmful_patterns.items():
            for pattern in patterns:
                import re
                matches = re.findall(pattern, response_lower)
                
                if matches:
                    severity = self._assess_severity(harm_type, matches, response_text)
                    
                    alerts.append(SafetyAlert(
                        alert_id=f"harmful_{harm_type}_{datetime.now().timestamp()}",
                        alert_type="harmful_content",
                        level=severity,
                        message=f"Potential {harm_type} content detected",
                        timestamp=datetime.now(),
                        context={
                            "harm_type": harm_type,
                            "matches": matches,
                            "pattern": pattern,
                            "response_preview": response_text[:200]
                        }
                    ))
        
        # Record detection
        self.detection_history.append({
            "timestamp": datetime.now(),
            "harm_types": [alert.context["harm_type"] for alert in alerts],
            "severity_levels": [alert.level.value for alert in alerts]
        })
        
        return alerts
    
    def _assess_severity(self, harm_type: str, matches: List[str], full_text: str) -> AlertLevel:
        """Assess severity of harmful content."""
        
        # High severity harm types
        if harm_type in ["violence", "self_harm"]:
            return AlertLevel.CRITICAL
        
        # Medium severity
        if harm_type in ["illegal_activity", "hate_speech"]:
            return AlertLevel.HIGH
        
        # Check context for severity
        if "how to" in full_text.lower() or "instructions" in full_text.lower():
            return AlertLevel.HIGH
        
        return AlertLevel.MEDIUM


class SafetyMonitor:
    """Main safety monitoring system."""
    
    def __init__(self, config: SafetyConfig):
        self.config = config
        self.anomaly_detector = AnomalyDetector(config)
        self.bias_detector = BiasDetector(config)
        self.harmful_content_detector = HarmfulContentDetector(config)
        
        self.active_alerts: List[SafetyAlert] = []
        self.alert_history: List[SafetyAlert] = []
        self.enabled = config.enable_safety_monitoring
    
    async def monitor_interaction(
        self,
        conversation_state: ConversationState,
        action: Action,
        response_text: str,
        reward: MultiObjectiveReward
    ) -> List[SafetyAlert]:
        """Monitor a complete interaction for safety issues."""
        
        if not self.enabled:
            return []
        
        all_alerts = []
        
        # Detect anomalies
        reward_anomalies = await self.anomaly_detector.detect_reward_anomalies(reward)
        response_anomalies = await self.anomaly_detector.detect_response_anomalies(response_text, action)
        all_alerts.extend(reward_anomalies + response_anomalies)
        
        # Detect bias
        context = {
            "conversation_length": len(conversation_state.conversation_history),
            "domain": conversation_state.domain_context,
            "user_input": conversation_state.current_user_input
        }
        bias_alerts = await self.bias_detector.detect_bias(response_text, context)
        all_alerts.extend(bias_alerts)
        
        # Detect harmful content
        harmful_alerts = await self.harmful_content_detector.detect_harmful_content(response_text, context)
        all_alerts.extend(harmful_alerts)
        
        # Process alerts
        for alert in all_alerts:
            await self._process_alert(alert)
        
        return all_alerts
    
    async def _process_alert(self, alert: SafetyAlert) -> None:
        """Process a safety alert."""
        
        # Add to active alerts
        self.active_alerts.append(alert)
        
        # Add to history
        self.alert_history.append(alert)
        
        # Log based on severity
        if alert.level == AlertLevel.CRITICAL:
            logger.critical(f"CRITICAL SAFETY ALERT: {alert.message}")
        elif alert.level == AlertLevel.HIGH:
            logger.error(f"HIGH SAFETY ALERT: {alert.message}")
        elif alert.level == AlertLevel.MEDIUM:
            logger.warning(f"MEDIUM SAFETY ALERT: {alert.message}")
        else:
            logger.info(f"LOW SAFETY ALERT: {alert.message}")
        
        # Auto-resolve low-level alerts after some time
        if alert.level == AlertLevel.LOW:
            # In a real system, this would be handled by a background task
            pass
    
    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[SafetyAlert]:
        """Get currently active alerts."""
        
        if level:
            return [alert for alert in self.active_alerts if alert.level == level and not alert.resolved]
        
        return [alert for alert in self.active_alerts if not alert.resolved]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert."""
        
        for alert in self.active_alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                logger.info(f"Resolved safety alert: {alert_id}")
                return True
        
        return False
    
    def get_safety_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive safety dashboard data."""
        
        # Count active alerts by level
        active_by_level = defaultdict(int)
        for alert in self.get_active_alerts():
            active_by_level[alert.level.value] += 1
        
        # Recent alert trends
        recent_alerts = [alert for alert in self.alert_history 
                        if (datetime.now() - alert.timestamp).days <= 7]
        
        # Bias trends
        bias_trends = self.bias_detector.get_bias_trends()
        
        return {
            "monitoring_enabled": self.enabled,
            "active_alerts": {
                "total": len(self.get_active_alerts()),
                "by_level": dict(active_by_level)
            },
            "recent_activity": {
                "total_alerts_7_days": len(recent_alerts),
                "alert_types": list(set(alert.alert_type for alert in recent_alerts))
            },
            "bias_analysis": bias_trends,
            "system_health": {
                "anomaly_detection": "active",
                "bias_detection": "active", 
                "harmful_content_detection": "active"
            }
        }
    
    async def cleanup_old_alerts(self, retention_days: int = 30) -> None:
        """Clean up old resolved alerts."""
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # Remove old resolved alerts from active list
        self.active_alerts = [
            alert for alert in self.active_alerts
            if not alert.resolved or alert.timestamp > cutoff_date
        ]
        
        # Keep only recent history
        self.alert_history = [
            alert for alert in self.alert_history
            if alert.timestamp > cutoff_date
        ]
        
        logger.info(f"Cleaned up safety alerts older than {retention_days} days")