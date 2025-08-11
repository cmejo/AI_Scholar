#!/usr/bin/env python3
"""
AI Scholar RAG Chatbot - Quality Alerts System

This script monitors quality metrics and sends alerts when thresholds are breached.
Supports multiple notification channels: email, Slack, webhook, and file-based alerts.
"""

import json
import os
import sys
import smtplib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass


@dataclass
class AlertConfig:
    """Alert configuration"""
    enabled: bool = True
    email_enabled: bool = False
    slack_enabled: bool = False
    webhook_enabled: bool = False
    file_enabled: bool = True
    
    # Email configuration
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_recipients: List[str] = None
    
    # Slack configuration
    slack_webhook_url: str = ""
    slack_channel: str = "#quality-alerts"
    
    # Webhook configuration
    webhook_url: str = ""
    webhook_headers: Dict[str, str] = None
    
    # Thresholds
    quality_score_threshold: float = 80.0
    coverage_threshold: float = 80.0
    error_threshold: int = 0
    security_score_threshold: float = 90.0
    
    def __post_init__(self):
        if self.email_recipients is None:
            self.email_recipients = []
        if self.webhook_headers is None:
            self.webhook_headers = {"Content-Type": "application/json"}


class QualityAlertsSystem:
    """Quality alerts monitoring and notification system"""
    
    def __init__(self, config_file: str = "quality-alerts-config.json"):
        self.config_file = Path(config_file)
        self.reports_dir = Path("quality-reports")
        self.alerts_dir = self.reports_dir / "alerts"
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = self._load_config()
        self.alerts_history = self._load_alerts_history()
    
    def monitor_and_alert(self) -> None:
        """Monitor quality metrics and send alerts if needed"""
        print("🚨 Starting quality alerts monitoring...")
        
        # Load latest metrics
        metrics = self._load_latest_metrics()
        if not metrics:
            print("⚠️ No metrics data found - skipping alert monitoring")
            return
        
        # Check for alert conditions
        alerts = self._check_alert_conditions(metrics)
        
        if not alerts:
            print("✅ No quality alerts triggered - all metrics within thresholds")
            return
        
        print(f"🚨 {len(alerts)} quality alerts triggered!")
        
        # Send alerts through configured channels
        self._send_alerts(alerts, metrics)
        
        # Save alerts to history
        self._save_alerts_to_history(alerts)
        
        print("✅ Quality alerts processing completed")
    
    def _load_config(self) -> AlertConfig:
        """Load alert configuration"""
        if not self.config_file.exists():
            print("⚠️ Alert config file not found, creating default configuration...")
            config = AlertConfig()
            self._save_config(config)
            return config
        
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            return AlertConfig(**config_data)
        except Exception as e:
            print(f"⚠️ Error loading alert config: {e}")
            return AlertConfig()
    
    def _save_config(self, config: AlertConfig) -> None:
        """Save alert configuration"""
        config_dict = {
            'enabled': config.enabled,
            'email_enabled': config.email_enabled,
            'slack_enabled': config.slack_enabled,
            'webhook_enabled': config.webhook_enabled,
            'file_enabled': config.file_enabled,
            'smtp_server': config.smtp_server,
            'smtp_port': config.smtp_port,
            'smtp_username': config.smtp_username,
            'smtp_password': config.smtp_password,
            'email_recipients': config.email_recipients,
            'slack_webhook_url': config.slack_webhook_url,
            'slack_channel': config.slack_channel,
            'webhook_url': config.webhook_url,
            'webhook_headers': config.webhook_headers,
            'quality_score_threshold': config.quality_score_threshold,
            'coverage_threshold': config.coverage_threshold,
            'error_threshold': config.error_threshold,
            'security_score_threshold': config.security_score_threshold
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    def _load_alerts_history(self) -> List[Dict[str, Any]]:
        """Load alerts history"""
        history_file = self.alerts_dir / "alerts-history.json"
        
        if not history_file.exists():
            return []
        
        try:
            with open(history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading alerts history: {e}")
            return []
    
    def _save_alerts_to_history(self, alerts: List[Dict[str, Any]]) -> None:
        """Save alerts to history"""
        history_file = self.alerts_dir / "alerts-history.json"
        
        # Add timestamp to alerts
        timestamped_alerts = []
        for alert in alerts:
            alert_with_timestamp = alert.copy()
            alert_with_timestamp['timestamp'] = datetime.now().isoformat()
            timestamped_alerts.append(alert_with_timestamp)
        
        # Add to history
        self.alerts_history.extend(timestamped_alerts)
        
        # Keep only last 100 alerts
        if len(self.alerts_history) > 100:
            self.alerts_history = self.alerts_history[-100:]
        
        # Save to file
        with open(history_file, 'w') as f:
            json.dump(self.alerts_history, f, indent=2)
    
    def _load_latest_metrics(self) -> Optional[Dict[str, Any]]:
        """Load the latest quality metrics"""
        metrics_files = list(self.reports_dir.glob("quality-metrics-*.json"))
        
        if not metrics_files:
            return None
        
        # Get the most recent metrics file
        latest_file = max(metrics_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading metrics from {latest_file}: {e}")
            return None
    
    def _check_alert_conditions(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for alert conditions based on metrics"""
        alerts = []
        overall = metrics.get('overall', {})
        
        # Quality score alert
        quality_score = overall.get('qualityScore', 0)
        if quality_score < self.config.quality_score_threshold:
            alerts.append({
                'type': 'quality_score',
                'severity': 'warning' if quality_score > 60 else 'critical',
                'title': 'Quality Score Below Threshold',
                'message': f"Quality score ({quality_score}) is below threshold ({self.config.quality_score_threshold})",
                'current_value': quality_score,
                'threshold': self.config.quality_score_threshold,
                'recommendation': 'Review and fix code quality issues, improve test coverage, and address security concerns'
            })
        
        # Coverage alert
        coverage = overall.get('coverage', 0)
        if coverage < self.config.coverage_threshold:
            alerts.append({
                'type': 'coverage',
                'severity': 'warning',
                'title': 'Test Coverage Below Threshold',
                'message': f"Test coverage ({coverage:.1f}%) is below threshold ({self.config.coverage_threshold}%)",
                'current_value': coverage,
                'threshold': self.config.coverage_threshold,
                'recommendation': 'Add unit tests and integration tests to improve coverage'
            })
        
        # Error count alert
        total_errors = overall.get('totalErrors', 0)
        if total_errors > self.config.error_threshold:
            alerts.append({
                'type': 'errors',
                'severity': 'critical',
                'title': 'Quality Errors Detected',
                'message': f"{total_errors} quality errors found (linting, type checking, compilation)",
                'current_value': total_errors,
                'threshold': self.config.error_threshold,
                'recommendation': 'Fix all linting errors, type checking errors, and compilation issues'
            })
        
        # Security score alert
        security_score = overall.get('securityScore', 100)
        if security_score < self.config.security_score_threshold:
            alerts.append({
                'type': 'security',
                'severity': 'critical' if security_score < 70 else 'warning',
                'title': 'Security Score Below Threshold',
                'message': f"Security score ({security_score}) indicates potential vulnerabilities",
                'current_value': security_score,
                'threshold': self.config.security_score_threshold,
                'recommendation': 'Review and fix security issues identified by Bandit and update vulnerable dependencies'
            })
        
        # Check for trend-based alerts
        trend_alerts = self._check_trend_alerts(metrics)
        alerts.extend(trend_alerts)
        
        return alerts
    
    def _check_trend_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for trend-based alerts"""
        alerts = []
        trends = metrics.get('trends', [])
        
        if len(trends) < 3:
            return alerts  # Not enough data for trend analysis
        
        # Check for declining quality trend
        recent_scores = [t.get('qualityScore', 0) for t in trends[-3:]]
        if len(recent_scores) == 3 and recent_scores[0] > recent_scores[1] > recent_scores[2]:
            decline = recent_scores[0] - recent_scores[2]
            if decline > 10:
                alerts.append({
                    'type': 'quality_trend',
                    'severity': 'warning',
                    'title': 'Declining Quality Trend',
                    'message': f"Quality score has declined by {decline:.1f} points over the last 3 measurements",
                    'current_value': recent_scores[2],
                    'threshold': recent_scores[0],
                    'recommendation': 'Investigate recent changes that may have impacted code quality'
                })
        
        # Check for increasing error trend
        recent_errors = [t.get('errors', 0) for t in trends[-3:]]
        if len(recent_errors) == 3 and recent_errors[0] < recent_errors[1] < recent_errors[2]:
            increase = recent_errors[2] - recent_errors[0]
            if increase > 5:
                alerts.append({
                    'type': 'error_trend',
                    'severity': 'warning',
                    'title': 'Increasing Error Trend',
                    'message': f"Error count has increased by {increase} over the last 3 measurements",
                    'current_value': recent_errors[2],
                    'threshold': recent_errors[0],
                    'recommendation': 'Address the root cause of increasing errors before they accumulate'
                })
        
        return alerts
    
    def _send_alerts(self, alerts: List[Dict[str, Any]], metrics: Dict[str, Any]) -> None:
        """Send alerts through configured channels"""
        if not self.config.enabled:
            print("⚠️ Alerts are disabled in configuration")
            return
        
        # Send file-based alerts
        if self.config.file_enabled:
            self._send_file_alerts(alerts, metrics)
        
        # Send email alerts
        if self.config.email_enabled and self.config.email_recipients:
            self._send_email_alerts(alerts, metrics)
        
        # Send Slack alerts
        if self.config.slack_enabled and self.config.slack_webhook_url:
            self._send_slack_alerts(alerts, metrics)
        
        # Send webhook alerts
        if self.config.webhook_enabled and self.config.webhook_url:
            self._send_webhook_alerts(alerts, metrics)
    
    def _send_file_alerts(self, alerts: List[Dict[str, Any]], metrics: Dict[str, Any]) -> None:
        """Send file-based alerts"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            alert_file = self.alerts_dir / f"quality-alert-{timestamp}.json"
            
            alert_data = {
                'timestamp': datetime.now().isoformat(),
                'alerts': alerts,
                'metrics_summary': {
                    'quality_score': metrics.get('overall', {}).get('qualityScore', 0),
                    'coverage': metrics.get('overall', {}).get('coverage', 0),
                    'total_errors': metrics.get('overall', {}).get('totalErrors', 0),
                    'security_score': metrics.get('overall', {}).get('securityScore', 100)
                }
            }
            
            with open(alert_file, 'w') as f:
                json.dump(alert_data, f, indent=2)
            
            print(f"📁 File alert saved: {alert_file}")
            
        except Exception as e:
            print(f"❌ Error sending file alert: {e}")
    
    def _send_email_alerts(self, alerts: List[Dict[str, Any]], metrics: Dict[str, Any]) -> None:
        """Send email alerts"""
        try:
            # Create email content
            subject = f"🚨 AI Scholar Quality Alert - {len(alerts)} issues detected"
            body = self._generate_email_body(alerts, metrics)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.smtp_username
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            
            # Send to all recipients
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                
                for recipient in self.config.email_recipients:
                    msg['To'] = recipient
                    server.send_message(msg)
                    del msg['To']
            
            print(f"📧 Email alerts sent to {len(self.config.email_recipients)} recipients")
            
        except Exception as e:
            print(f"❌ Error sending email alerts: {e}")
    
    def _send_slack_alerts(self, alerts: List[Dict[str, Any]], metrics: Dict[str, Any]) -> None:
        """Send Slack alerts"""
        try:
            # Create Slack message
            message = self._generate_slack_message(alerts, metrics)
            
            payload = {
                'channel': self.config.slack_channel,
                'username': 'Quality Bot',
                'icon_emoji': ':warning:',
                'attachments': [message]
            }
            
            response = requests.post(self.config.slack_webhook_url, json=payload)
            response.raise_for_status()
            
            print("💬 Slack alert sent successfully")
            
        except Exception as e:
            print(f"❌ Error sending Slack alert: {e}")
    
    def _send_webhook_alerts(self, alerts: List[Dict[str, Any]], metrics: Dict[str, Any]) -> None:
        """Send webhook alerts"""
        try:
            payload = {
                'timestamp': datetime.now().isoformat(),
                'project': 'AI Scholar RAG Chatbot',
                'alert_count': len(alerts),
                'alerts': alerts,
                'metrics_summary': {
                    'quality_score': metrics.get('overall', {}).get('qualityScore', 0),
                    'coverage': metrics.get('overall', {}).get('coverage', 0),
                    'total_errors': metrics.get('overall', {}).get('totalErrors', 0),
                    'security_score': metrics.get('overall', {}).get('securityScore', 100)
                }
            }
            
            response = requests.post(
                self.config.webhook_url,
                json=payload,
                headers=self.config.webhook_headers
            )
            response.raise_for_status()
            
            print("🔗 Webhook alert sent successfully")
            
        except Exception as e:
            print(f"❌ Error sending webhook alert: {e}")
    
    def _generate_email_body(self, alerts: List[Dict[str, Any]], metrics: Dict[str, Any]) -> str:
        """Generate HTML email body"""
        overall = metrics.get('overall', {})
        
        alerts_html = ""
        for alert in alerts:
            severity_color = "#dc2626" if alert['severity'] == 'critical' else "#f59e0b"
            alerts_html += f"""
            <div style="border-left: 4px solid {severity_color}; padding: 15px; margin: 10px 0; background: #f9f9f9;">
                <h3 style="color: {severity_color}; margin: 0 0 10px 0;">{alert['title']}</h3>
                <p style="margin: 5px 0;"><strong>Message:</strong> {alert['message']}</p>
                <p style="margin: 5px 0;"><strong>Recommendation:</strong> {alert['recommendation']}</p>
            </div>
            """
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #dc2626;">🚨 AI Scholar Quality Alert</h1>
                
                <p>Quality monitoring has detected {len(alerts)} issue(s) that require attention.</p>
                
                <h2>📊 Current Metrics Summary</h2>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background: #f3f4f6;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Quality Score</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{overall.get('qualityScore', 0)}/100</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Test Coverage</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{overall.get('coverage', 0):.1f}%</td>
                    </tr>
                    <tr style="background: #f3f4f6;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Total Errors</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{overall.get('totalErrors', 0)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Security Score</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{overall.get('securityScore', 100)}/100</td>
                    </tr>
                </table>
                
                <h2>🚨 Alerts</h2>
                {alerts_html}
                
                <p style="margin-top: 30px; color: #666;">
                    <em>This alert was generated automatically by the AI Scholar Quality Monitoring System.</em>
                </p>
            </div>
        </body>
        </html>
        """
    
    def _generate_slack_message(self, alerts: List[Dict[str, Any]], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Slack message attachment"""
        overall = metrics.get('overall', {})
        
        fields = [
            {
                'title': 'Quality Score',
                'value': f"{overall.get('qualityScore', 0)}/100",
                'short': True
            },
            {
                'title': 'Test Coverage',
                'value': f"{overall.get('coverage', 0):.1f}%",
                'short': True
            },
            {
                'title': 'Total Errors',
                'value': str(overall.get('totalErrors', 0)),
                'short': True
            },
            {
                'title': 'Security Score',
                'value': f"{overall.get('securityScore', 100)}/100",
                'short': True
            }
        ]
        
        # Add alert details
        alert_text = ""
        for alert in alerts:
            emoji = "🔴" if alert['severity'] == 'critical' else "🟡"
            alert_text += f"{emoji} *{alert['title']}*: {alert['message']}\n"
        
        color = "danger" if any(a['severity'] == 'critical' for a in alerts) else "warning"
        
        return {
            'color': color,
            'title': f"🚨 AI Scholar Quality Alert - {len(alerts)} issues detected",
            'text': alert_text,
            'fields': fields,
            'footer': 'AI Scholar Quality Monitoring',
            'ts': int(datetime.now().timestamp())
        }


def main():
    """Main execution function"""
    try:
        alerts_system = QualityAlertsSystem()
        alerts_system.monitor_and_alert()
        return 0
    except Exception as e:
        print(f"❌ Quality alerts system failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())