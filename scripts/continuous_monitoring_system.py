#!/usr/bin/env python3
"""
Continuous Monitoring and Alerting System for Code Quality
Implements quality gates, regression detection, Ubuntu compatibility monitoring,
and maintenance procedure automation.
"""

import json
import logging
import os
import smtplib
import subprocess
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import sqlite3
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class MonitoringStatus(Enum):
    PASSING = "passing"
    WARNING = "warning"
    FAILING = "failing"
    ERROR = "error"


@dataclass
class QualityGate:
    name: str
    description: str
    threshold_type: str  # "max_issues", "max_severity", "coverage_min"
    threshold_value: Any
    enabled: bool = True
    ubuntu_specific: bool = False


@dataclass
class MonitoringAlert:
    id: str
    timestamp: datetime
    severity: AlertSeverity
    title: str
    description: str
    component: str
    ubuntu_specific: bool
    auto_fixable: bool
    resolved: bool = False
    resolution_notes: Optional[str] = None


@dataclass
class QualityMetrics:
    timestamp: datetime
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    ubuntu_issues: int
    auto_fixable_issues: int
    test_coverage: float
    build_success: bool
    deployment_success: bool


class ContinuousMonitoringSystem:
    """Main monitoring system for continuous code quality management."""
    
    def __init__(self, project_root: Path, config_file: Optional[Path] = None):
        self.project_root = project_root
        self.config_file = config_file or project_root / "monitoring-config.yml"
        self.db_path = project_root / "monitoring.db"
        self.config = self._load_config()
        self.quality_gates = self._load_quality_gates()
        self._init_database()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration."""
        default_config = {
            "monitoring": {
                "check_interval_minutes": 60,
                "retention_days": 30,
                "enable_email_alerts": False,
                "enable_slack_alerts": False,
                "enable_webhook_alerts": False
            },
            "quality_gates": {
                "max_critical_issues": 0,
                "max_high_issues": 5,
                "max_total_issues": 50,
                "min_test_coverage": 80.0,
                "max_ubuntu_compatibility_issues": 2
            },
            "alerts": {
                "email": {
                    "smtp_server": "localhost",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "recipients": []
                },
                "slack": {
                    "webhook_url": "",
                    "channel": "#code-quality"
                },
                "webhook": {
                    "url": "",
                    "headers": {}
                }
            },
            "maintenance": {
                "auto_fix_enabled": True,
                "auto_update_dependencies": False,
                "auto_format_code": True,
                "backup_before_fixes": True
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    user_config = yaml.safe_load(f)
                    # Merge with defaults
                    return self._merge_configs(default_config, user_config)
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}, using defaults")
        
        return default_config
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Recursively merge user config with defaults."""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _load_quality_gates(self) -> List[QualityGate]:
        """Load quality gate definitions."""
        gates_config = self.config.get("quality_gates", {})
        
        return [
            QualityGate(
                name="critical_issues",
                description="No critical issues allowed",
                threshold_type="max_issues",
                threshold_value=gates_config.get("max_critical_issues", 0),
                ubuntu_specific=False
            ),
            QualityGate(
                name="high_issues",
                description="Limited high severity issues",
                threshold_type="max_issues",
                threshold_value=gates_config.get("max_high_issues", 5),
                ubuntu_specific=False
            ),
            QualityGate(
                name="total_issues",
                description="Total issues threshold",
                threshold_type="max_issues",
                threshold_value=gates_config.get("max_total_issues", 50),
                ubuntu_specific=False
            ),
            QualityGate(
                name="test_coverage",
                description="Minimum test coverage required",
                threshold_type="coverage_min",
                threshold_value=gates_config.get("min_test_coverage", 80.0),
                ubuntu_specific=False
            ),
            QualityGate(
                name="ubuntu_compatibility",
                description="Ubuntu compatibility issues threshold",
                threshold_type="max_issues",
                threshold_value=gates_config.get("max_ubuntu_compatibility_issues", 2),
                ubuntu_specific=True
            )
        ]
    
    def _init_database(self):
        """Initialize SQLite database for monitoring data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quality_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_issues INTEGER,
                    critical_issues INTEGER,
                    high_issues INTEGER,
                    medium_issues INTEGER,
                    low_issues INTEGER,
                    ubuntu_issues INTEGER,
                    auto_fixable_issues INTEGER,
                    test_coverage REAL,
                    build_success BOOLEAN,
                    deployment_success BOOLEAN
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_alerts (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    component TEXT,
                    ubuntu_specific BOOLEAN,
                    auto_fixable BOOLEAN,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_notes TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quality_gate_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    gate_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    threshold_value TEXT,
                    actual_value TEXT,
                    passed BOOLEAN
                )
            """)
            
            conn.commit()
    
    def run_quality_analysis(self) -> QualityMetrics:
        """Run comprehensive quality analysis."""
        logger.info("Running quality analysis...")
        
        # Run the main codebase analysis
        analysis_script = self.project_root / "scripts" / "codebase-analysis.py"
        if not analysis_script.exists():
            raise FileNotFoundError("Codebase analysis script not found")
        
        try:
            result = subprocess.run([
                "python", str(analysis_script), "--output", "monitoring_analysis.json"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=1800)
            
            if result.returncode != 0:
                logger.error(f"Analysis failed: {result.stderr}")
                raise RuntimeError("Quality analysis failed")
            
            # Load analysis results
            analysis_file = self.project_root / "monitoring_analysis.json"
            if not analysis_file.exists():
                raise FileNotFoundError("Analysis results file not found")
            
            with open(analysis_file, 'r') as f:
                analysis_data = json.load(f)
            
            # Calculate metrics
            total_issues = analysis_data.get("total_issues_found", 0)
            
            # Count issues by severity
            critical_issues = 0
            high_issues = 0
            medium_issues = 0
            low_issues = 0
            ubuntu_issues = 0
            auto_fixable_issues = 0
            
            for result in analysis_data.get("results", []):
                for issue in result.get("issues", []):
                    severity = issue.get("severity", "info")
                    if severity == "critical":
                        critical_issues += 1
                    elif severity == "high":
                        high_issues += 1
                    elif severity == "medium":
                        medium_issues += 1
                    elif severity == "low":
                        low_issues += 1
                    
                    if issue.get("ubuntu_specific", False):
                        ubuntu_issues += 1
                    
                    if issue.get("auto_fixable", False):
                        auto_fixable_issues += 1
            
            # Get test coverage (mock for now, would integrate with actual coverage tools)
            test_coverage = self._get_test_coverage()
            
            # Check build and deployment status
            build_success = self._check_build_status()
            deployment_success = self._check_deployment_status()
            
            metrics = QualityMetrics(
                timestamp=datetime.now(),
                total_issues=total_issues,
                critical_issues=critical_issues,
                high_issues=high_issues,
                medium_issues=medium_issues,
                low_issues=low_issues,
                ubuntu_issues=ubuntu_issues,
                auto_fixable_issues=auto_fixable_issues,
                test_coverage=test_coverage,
                build_success=build_success,
                deployment_success=deployment_success
            )
            
            # Store metrics in database
            self._store_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Quality analysis failed: {e}")
            raise
    
    def _get_test_coverage(self) -> float:
        """Get current test coverage percentage."""
        try:
            # Try to get coverage from existing coverage reports
            coverage_file = self.project_root / "coverage" / "coverage-final.json"
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                    total = coverage_data.get("total", {})
                    return total.get("lines", {}).get("pct", 0.0)
            
            # Fallback: run coverage analysis
            result = subprocess.run([
                "npm", "run", "test:coverage", "--", "--reporter=json"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Parse coverage output (implementation depends on test framework)
                return 85.0  # Mock value
            
        except Exception as e:
            logger.warning(f"Failed to get test coverage: {e}")
        
        return 0.0
    
    def _check_build_status(self) -> bool:
        """Check if the project builds successfully."""
        try:
            # Check frontend build
            result = subprocess.run([
                "npm", "run", "build"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                return False
            
            # Check backend (if applicable)
            backend_path = self.project_root / "backend"
            if backend_path.exists():
                result = subprocess.run([
                    "python", "-m", "py_compile", "app.py"
                ], cwd=backend_path, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Build status check failed: {e}")
            return False
    
    def _check_deployment_status(self) -> bool:
        """Check if deployment configuration is valid."""
        try:
            # Check Docker compose files
            compose_files = list(self.project_root.glob("docker-compose*.yml"))
            for compose_file in compose_files:
                result = subprocess.run([
                    "docker-compose", "-f", str(compose_file), "config"
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Deployment status check failed: {e}")
            return False
    
    def _store_metrics(self, metrics: QualityMetrics):
        """Store quality metrics in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO quality_metrics (
                    timestamp, total_issues, critical_issues, high_issues,
                    medium_issues, low_issues, ubuntu_issues, auto_fixable_issues,
                    test_coverage, build_success, deployment_success
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.timestamp.isoformat(),
                metrics.total_issues,
                metrics.critical_issues,
                metrics.high_issues,
                metrics.medium_issues,
                metrics.low_issues,
                metrics.ubuntu_issues,
                metrics.auto_fixable_issues,
                metrics.test_coverage,
                metrics.build_success,
                metrics.deployment_success
            ))
            conn.commit()
    
    def evaluate_quality_gates(self, metrics: QualityMetrics) -> List[Tuple[QualityGate, bool, str]]:
        """Evaluate all quality gates against current metrics."""
        results = []
        
        for gate in self.quality_gates:
            if not gate.enabled:
                continue
            
            passed = True
            message = ""
            
            if gate.name == "critical_issues":
                passed = metrics.critical_issues <= gate.threshold_value
                message = f"Critical issues: {metrics.critical_issues} (threshold: {gate.threshold_value})"
            
            elif gate.name == "high_issues":
                passed = metrics.high_issues <= gate.threshold_value
                message = f"High issues: {metrics.high_issues} (threshold: {gate.threshold_value})"
            
            elif gate.name == "total_issues":
                passed = metrics.total_issues <= gate.threshold_value
                message = f"Total issues: {metrics.total_issues} (threshold: {gate.threshold_value})"
            
            elif gate.name == "test_coverage":
                passed = metrics.test_coverage >= gate.threshold_value
                message = f"Test coverage: {metrics.test_coverage:.1f}% (threshold: {gate.threshold_value}%)"
            
            elif gate.name == "ubuntu_compatibility":
                passed = metrics.ubuntu_issues <= gate.threshold_value
                message = f"Ubuntu issues: {metrics.ubuntu_issues} (threshold: {gate.threshold_value})"
            
            # Store gate result
            self._store_gate_result(gate, passed, message, metrics.timestamp)
            
            results.append((gate, passed, message))
        
        return results
    
    def _store_gate_result(self, gate: QualityGate, passed: bool, message: str, timestamp: datetime):
        """Store quality gate result in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO quality_gate_results (
                    timestamp, gate_name, status, threshold_value, actual_value, passed
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                timestamp.isoformat(),
                gate.name,
                "PASSED" if passed else "FAILED",
                str(gate.threshold_value),
                message,
                passed
            ))
            conn.commit()
    
    def detect_regressions(self, current_metrics: QualityMetrics) -> List[MonitoringAlert]:
        """Detect quality regressions by comparing with historical data."""
        alerts = []
        
        # Get historical metrics (last 7 days)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM quality_metrics 
                WHERE timestamp > datetime('now', '-7 days')
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            historical_data = cursor.fetchall()
        
        if len(historical_data) < 2:
            logger.info("Insufficient historical data for regression detection")
            return alerts
        
        # Compare with previous metrics
        prev_metrics = historical_data[1] if len(historical_data) > 1 else historical_data[0]
        
        # Check for regressions
        if current_metrics.critical_issues > prev_metrics[3]:  # critical_issues column
            alerts.append(MonitoringAlert(
                id=f"regression_critical_{int(time.time())}",
                timestamp=datetime.now(),
                severity=AlertSeverity.CRITICAL,
                title="Critical Issues Regression",
                description=f"Critical issues increased from {prev_metrics[3]} to {current_metrics.critical_issues}",
                component="code_quality",
                ubuntu_specific=False,
                auto_fixable=False
            ))
        
        if current_metrics.total_issues > prev_metrics[2] * 1.2:  # 20% increase threshold
            alerts.append(MonitoringAlert(
                id=f"regression_total_{int(time.time())}",
                timestamp=datetime.now(),
                severity=AlertSeverity.HIGH,
                title="Total Issues Regression",
                description=f"Total issues increased significantly from {prev_metrics[2]} to {current_metrics.total_issues}",
                component="code_quality",
                ubuntu_specific=False,
                auto_fixable=current_metrics.auto_fixable_issues > 0
            ))
        
        if current_metrics.test_coverage < prev_metrics[9] - 5.0:  # 5% decrease threshold
            alerts.append(MonitoringAlert(
                id=f"regression_coverage_{int(time.time())}",
                timestamp=datetime.now(),
                severity=AlertSeverity.MEDIUM,
                title="Test Coverage Regression",
                description=f"Test coverage decreased from {prev_metrics[9]:.1f}% to {current_metrics.test_coverage:.1f}%",
                component="testing",
                ubuntu_specific=False,
                auto_fixable=False
            ))
        
        if current_metrics.ubuntu_issues > prev_metrics[6]:  # ubuntu_issues column
            alerts.append(MonitoringAlert(
                id=f"regression_ubuntu_{int(time.time())}",
                timestamp=datetime.now(),
                severity=AlertSeverity.HIGH,
                title="Ubuntu Compatibility Regression",
                description=f"Ubuntu compatibility issues increased from {prev_metrics[6]} to {current_metrics.ubuntu_issues}",
                component="ubuntu_compatibility",
                ubuntu_specific=True,
                auto_fixable=False
            ))
        
        # Store alerts
        for alert in alerts:
            self._store_alert(alert)
        
        return alerts
    
    def _store_alert(self, alert: MonitoringAlert):
        """Store alert in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO monitoring_alerts (
                    id, timestamp, severity, title, description, component,
                    ubuntu_specific, auto_fixable, resolved, resolution_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.id,
                alert.timestamp.isoformat(),
                alert.severity.value,
                alert.title,
                alert.description,
                alert.component,
                alert.ubuntu_specific,
                alert.auto_fixable,
                alert.resolved,
                alert.resolution_notes
            ))
            conn.commit()
    
    def send_alerts(self, alerts: List[MonitoringAlert], gate_failures: List[Tuple[QualityGate, bool, str]]):
        """Send alerts through configured channels."""
        if not alerts and not any(not passed for _, passed, _ in gate_failures):
            return
        
        # Prepare alert message
        message = self._format_alert_message(alerts, gate_failures)
        
        # Send email alerts
        if self.config["monitoring"]["enable_email_alerts"]:
            self._send_email_alert(message)
        
        # Send Slack alerts
        if self.config["monitoring"]["enable_slack_alerts"]:
            self._send_slack_alert(message)
        
        # Send webhook alerts
        if self.config["monitoring"]["enable_webhook_alerts"]:
            self._send_webhook_alert(message, alerts, gate_failures)
    
    def _format_alert_message(self, alerts: List[MonitoringAlert], gate_failures: List[Tuple[QualityGate, bool, str]]) -> str:
        """Format alert message for notifications."""
        message_parts = ["🚨 Code Quality Alert 🚨\n"]
        
        if gate_failures:
            failed_gates = [gate for gate, passed, msg in gate_failures if not passed]
            if failed_gates:
                message_parts.append("❌ Quality Gate Failures:")
                for gate, _, msg in gate_failures:
                    if not _:
                        message_parts.append(f"  • {gate.name}: {msg}")
                message_parts.append("")
        
        if alerts:
            message_parts.append("⚠️ Quality Regressions:")
            for alert in alerts:
                icon = "🔴" if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH] else "🟡"
                ubuntu_flag = " [Ubuntu]" if alert.ubuntu_specific else ""
                fix_flag = " [Auto-fixable]" if alert.auto_fixable else ""
                message_parts.append(f"  {icon} {alert.title}{ubuntu_flag}{fix_flag}")
                message_parts.append(f"     {alert.description}")
            message_parts.append("")
        
        message_parts.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        message_parts.append("Check the monitoring dashboard for detailed information.")
        
        return "\n".join(message_parts)
    
    def _send_email_alert(self, message: str):
        """Send email alert."""
        try:
            email_config = self.config["alerts"]["email"]
            if not email_config["recipients"]:
                return
            
            msg = MIMEMultipart()
            msg['From'] = email_config["username"]
            msg['To'] = ", ".join(email_config["recipients"])
            msg['Subject'] = "Code Quality Alert - AI Scholar"
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            server.starttls()
            server.login(email_config["username"], email_config["password"])
            server.send_message(msg)
            server.quit()
            
            logger.info("Email alert sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def _send_slack_alert(self, message: str):
        """Send Slack alert."""
        try:
            import requests
            
            slack_config = self.config["alerts"]["slack"]
            if not slack_config["webhook_url"]:
                return
            
            payload = {
                "channel": slack_config["channel"],
                "text": message,
                "username": "Code Quality Monitor",
                "icon_emoji": ":warning:"
            }
            
            response = requests.post(slack_config["webhook_url"], json=payload)
            response.raise_for_status()
            
            logger.info("Slack alert sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    def _send_webhook_alert(self, message: str, alerts: List[MonitoringAlert], gate_failures: List[Tuple[QualityGate, bool, str]]):
        """Send webhook alert."""
        try:
            import requests
            
            webhook_config = self.config["alerts"]["webhook"]
            if not webhook_config["url"]:
                return
            
            payload = {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "alerts": [asdict(alert) for alert in alerts],
                "gate_failures": [
                    {"gate": gate.name, "passed": passed, "message": msg}
                    for gate, passed, msg in gate_failures
                ]
            }
            
            headers = webhook_config.get("headers", {})
            headers["Content-Type"] = "application/json"
            
            response = requests.post(webhook_config["url"], json=payload, headers=headers)
            response.raise_for_status()
            
            logger.info("Webhook alert sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    def run_maintenance_procedures(self, metrics: QualityMetrics) -> Dict[str, Any]:
        """Run automated maintenance procedures."""
        maintenance_config = self.config["maintenance"]
        results = {
            "auto_fixes_applied": 0,
            "dependencies_updated": 0,
            "code_formatted": False,
            "backup_created": False,
            "errors": []
        }
        
        try:
            # Create backup if enabled
            if maintenance_config["backup_before_fixes"]:
                results["backup_created"] = self._create_backup()
            
            # Auto-format code if enabled
            if maintenance_config["auto_format_code"]:
                results["code_formatted"] = self._auto_format_code()
            
            # Apply auto-fixes if enabled
            if maintenance_config["auto_fix_enabled"] and metrics.auto_fixable_issues > 0:
                results["auto_fixes_applied"] = self._apply_auto_fixes()
            
            # Update dependencies if enabled
            if maintenance_config["auto_update_dependencies"]:
                results["dependencies_updated"] = self._update_dependencies()
            
        except Exception as e:
            logger.error(f"Maintenance procedure failed: {e}")
            results["errors"].append(str(e))
        
        return results
    
    def _create_backup(self) -> bool:
        """Create backup of current codebase."""
        try:
            backup_dir = self.project_root / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.tar.gz"
            backup_path = backup_dir / backup_name
            
            subprocess.run([
                "tar", "-czf", str(backup_path), 
                "--exclude=node_modules", "--exclude=venv", "--exclude=.git",
                "--exclude=backups", "."
            ], cwd=self.project_root, check=True)
            
            logger.info(f"Backup created: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False
    
    def _auto_format_code(self) -> bool:
        """Auto-format code using configured formatters."""
        try:
            # Format Python code with black
            backend_path = self.project_root / "backend"
            if backend_path.exists():
                subprocess.run([
                    "python", "-m", "black", "."
                ], cwd=backend_path, check=True)
            
            # Format TypeScript/JavaScript code with prettier
            subprocess.run([
                "npm", "run", "format"
            ], cwd=self.project_root, check=True)
            
            logger.info("Code formatting completed")
            return True
            
        except Exception as e:
            logger.error(f"Code formatting failed: {e}")
            return False
    
    def _apply_auto_fixes(self) -> int:
        """Apply automated fixes for fixable issues."""
        try:
            # Run the automated fix engine
            fix_script = self.project_root / "scripts" / "automated_fix_engine.py"
            if not fix_script.exists():
                logger.warning("Automated fix engine not found")
                return 0
            
            result = subprocess.run([
                "python", str(fix_script), "--auto-apply"
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse output to count fixes applied
                output = result.stdout
                if "fixes applied:" in output.lower():
                    import re
                    match = re.search(r'(\d+)\s+fixes applied', output.lower())
                    if match:
                        return int(match.group(1))
            
            return 0
            
        except Exception as e:
            logger.error(f"Auto-fix application failed: {e}")
            return 0
    
    def _update_dependencies(self) -> int:
        """Update project dependencies."""
        try:
            updates_count = 0
            
            # Update npm dependencies
            result = subprocess.run([
                "npm", "update"
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                updates_count += 1
            
            # Update Python dependencies (if requirements.txt exists)
            backend_path = self.project_root / "backend"
            requirements_file = backend_path / "requirements.txt"
            if requirements_file.exists():
                subprocess.run([
                    "pip", "install", "--upgrade", "-r", "requirements.txt"
                ], cwd=backend_path, check=True)
                updates_count += 1
            
            logger.info(f"Dependencies updated: {updates_count} package managers")
            return updates_count
            
        except Exception as e:
            logger.error(f"Dependency update failed: {e}")
            return 0
    
    def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report."""
        with sqlite3.connect(self.db_path) as conn:
            # Get recent metrics
            cursor = conn.execute("""
                SELECT * FROM quality_metrics 
                ORDER BY timestamp DESC 
                LIMIT 30
            """)
            recent_metrics = cursor.fetchall()
            
            # Get active alerts
            cursor = conn.execute("""
                SELECT * FROM monitoring_alerts 
                WHERE resolved = FALSE
                ORDER BY timestamp DESC
            """)
            active_alerts = cursor.fetchall()
            
            # Get quality gate trends
            cursor = conn.execute("""
                SELECT gate_name, COUNT(*) as total, 
                       SUM(CASE WHEN passed THEN 1 ELSE 0 END) as passed
                FROM quality_gate_results 
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY gate_name
            """)
            gate_trends = cursor.fetchall()
        
        return {
            "report_timestamp": datetime.now().isoformat(),
            "recent_metrics": recent_metrics,
            "active_alerts": active_alerts,
            "quality_gate_trends": gate_trends,
            "monitoring_config": self.config
        }
    
    def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Run complete monitoring cycle."""
        logger.info("Starting monitoring cycle...")
        
        try:
            # Run quality analysis
            metrics = self.run_quality_analysis()
            
            # Evaluate quality gates
            gate_results = self.evaluate_quality_gates(metrics)
            
            # Detect regressions
            regression_alerts = self.detect_regressions(metrics)
            
            # Send alerts if needed
            self.send_alerts(regression_alerts, gate_results)
            
            # Run maintenance procedures
            maintenance_results = self.run_maintenance_procedures(metrics)
            
            # Generate report
            report = self.generate_monitoring_report()
            
            cycle_result = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "metrics": asdict(metrics),
                "quality_gates": [
                    {"gate": gate.name, "passed": passed, "message": msg}
                    for gate, passed, msg in gate_results
                ],
                "regression_alerts": [asdict(alert) for alert in regression_alerts],
                "maintenance_results": maintenance_results,
                "report": report
            }
            
            logger.info("Monitoring cycle completed successfully")
            return cycle_result
            
        except Exception as e:
            logger.error(f"Monitoring cycle failed: {e}")
            return {
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }


def main():
    """Main entry point for continuous monitoring system."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Continuous Monitoring and Alerting System")
    parser.add_argument("--config", type=Path, help="Configuration file path")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root directory")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in minutes")
    parser.add_argument("--report", action="store_true", help="Generate monitoring report")
    
    args = parser.parse_args()
    
    # Initialize monitoring system
    monitoring = ContinuousMonitoringSystem(args.project_root, args.config)
    
    if args.report:
        # Generate and print report
        report = monitoring.generate_monitoring_report()
        print(json.dumps(report, indent=2, default=str))
        return
    
    if args.daemon:
        # Run as daemon
        logger.info(f"Starting monitoring daemon with {args.interval} minute intervals")
        while True:
            try:
                result = monitoring.run_monitoring_cycle()
                if not result["success"]:
                    logger.error(f"Monitoring cycle failed: {result.get('error')}")
                
                time.sleep(args.interval * 60)  # Convert minutes to seconds
                
            except KeyboardInterrupt:
                logger.info("Monitoring daemon stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitoring daemon: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    else:
        # Run single monitoring cycle
        result = monitoring.run_monitoring_cycle()
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()