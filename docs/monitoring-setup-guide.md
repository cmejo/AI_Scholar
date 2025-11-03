# Multi-Instance ArXiv System - Monitoring and Alerting Setup Guide

## Overview

This guide provides comprehensive instructions for setting up monitoring and alerting for the Multi-Instance ArXiv System. It covers system metrics, application performance, error tracking, and automated alerting.

## Monitoring Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   System Metrics│    │  Application    │    │   Database      │
│   (CPU, Memory, │    │   Metrics       │    │   Metrics       │
│   Disk, Network)│    │  (Processing,   │    │  (ChromaDB      │
│                 │    │   Downloads)    │    │   Performance)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Monitoring    │
                    │   Dashboard     │
                    │                 │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Alerting      │
                    │   System        │
                    │                 │
                    └─────────────────┘
```

## System Monitoring Setup

### 1. Install Monitoring Tools

```bash
# Install system monitoring tools
sudo apt update
sudo apt install -y htop iotop nethogs sysstat

# Install Python monitoring libraries
pip install psutil prometheus-client grafana-api

# Create monitoring directory
mkdir -p /opt/arxiv-system/monitoring/{scripts,config,data}
```

### 2. System Metrics Collection

Create the system metrics collector:

```bash
cat > /opt/arxiv-system/monitoring/scripts/system_metrics.py << 'EOF'
#!/usr/bin/env python3
"""
System metrics collection for Multi-Instance ArXiv System
"""

import psutil
import json
import time
import logging
from datetime import datetime
from pathlib import Path

class SystemMetricsCollector:
    def __init__(self, data_dir="/opt/arxiv-system/monitoring/data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/opt/arxiv-system/logs/monitoring.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def collect_cpu_metrics(self):
        """Collect CPU usage metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'cpu_count': psutil.cpu_count(),
            'load_average': psutil.getloadavg(),
            'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
    
    def collect_memory_metrics(self):
        """Collect memory usage metrics"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used,
                'free': memory.free
            },
            'swap': {
                'total': swap.total,
                'used': swap.used,
                'free': swap.free,
                'percent': swap.percent
            }
        }
    
    def collect_disk_metrics(self):
        """Collect disk usage metrics"""
        disk_usage = {}
        
        # Main system disk
        usage = psutil.disk_usage('/opt/arxiv-system')
        disk_usage['/opt/arxiv-system'] = {
            'total': usage.total,
            'used': usage.used,
            'free': usage.free,
            'percent': (usage.used / usage.total) * 100
        }
        
        # Individual instance directories
        for instance in ['ai_scholar', 'quant_scholar']:
            instance_path = f'/opt/arxiv-system/data/{instance}'
            if Path(instance_path).exists():
                usage = psutil.disk_usage(instance_path)
                disk_usage[instance_path] = {
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': (usage.used / usage.total) * 100
                }
        
        return disk_usage
    
    def collect_network_metrics(self):
        """Collect network usage metrics"""
        net_io = psutil.net_io_counters()
        
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'errin': net_io.errin,
            'errout': net_io.errout,
            'dropin': net_io.dropin,
            'dropout': net_io.dropout
        }
    
    def collect_process_metrics(self):
        """Collect process-specific metrics"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if 'python' in proc.info['name'].lower() or 'chromadb' in proc.info['name'].lower():
                    processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return processes
    
    def collect_all_metrics(self):
        """Collect all system metrics"""
        timestamp = datetime.now().isoformat()
        
        metrics = {
            'timestamp': timestamp,
            'cpu': self.collect_cpu_metrics(),
            'memory': self.collect_memory_metrics(),
            'disk': self.collect_disk_metrics(),
            'network': self.collect_network_metrics(),
            'processes': self.collect_process_metrics()
        }
        
        return metrics
    
    def save_metrics(self, metrics):
        """Save metrics to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.data_dir / f'system_metrics_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        self.logger.info(f"Metrics saved to {filename}")
        return filename
    
    def run_collection(self):
        """Run metrics collection"""
        try:
            metrics = self.collect_all_metrics()
            self.save_metrics(metrics)
            
            # Log key metrics
            cpu_percent = metrics['cpu']['cpu_percent']
            memory_percent = metrics['memory']['memory']['percent']
            disk_percent = metrics['disk']['/opt/arxiv-system']['percent']
            
            self.logger.info(f"System Status - CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%, Disk: {disk_percent:.1f}%")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return None

if __name__ == "__main__":
    collector = SystemMetricsCollector()
    collector.run_collection()
EOF

chmod +x /opt/arxiv-system/monitoring/scripts/system_metrics.py
```

### 3. Application Metrics Collection

Create the application metrics collector:

```bash
cat > /opt/arxiv-system/monitoring/scripts/app_metrics.py << 'EOF'
#!/usr/bin/env python3
"""
Application metrics collection for Multi-Instance ArXiv System
"""

import json
import requests
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path

class ApplicationMetricsCollector:
    def __init__(self, data_dir="/opt/arxiv-system/monitoring/data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/opt/arxiv-system/logs/monitoring.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def check_chromadb_health(self):
        """Check ChromaDB health and performance"""
        try:
            # Health check
            response = requests.get('http://localhost:8000/api/v1/heartbeat', timeout=5)
            health_status = response.status_code == 200
            
            # Get collections info
            collections_response = requests.get('http://localhost:8000/api/v1/collections', timeout=10)
            collections = collections_response.json() if collections_response.status_code == 200 else []
            
            collection_stats = {}
            for collection in collections:
                collection_name = collection.get('name', 'unknown')
                try:
                    # Get collection count
                    count_response = requests.get(
                        f'http://localhost:8000/api/v1/collections/{collection_name}/count',
                        timeout=10
                    )
                    count = count_response.json() if count_response.status_code == 200 else 0
                    collection_stats[collection_name] = {
                        'document_count': count,
                        'metadata': collection.get('metadata', {})
                    }
                except Exception as e:
                    self.logger.warning(f"Error getting stats for collection {collection_name}: {e}")
                    collection_stats[collection_name] = {'error': str(e)}
            
            return {
                'health_status': health_status,
                'response_time_ms': response.elapsed.total_seconds() * 1000 if health_status else None,
                'collections': collection_stats,
                'total_collections': len(collections)
            }
            
        except Exception as e:
            self.logger.error(f"Error checking ChromaDB health: {e}")
            return {
                'health_status': False,
                'error': str(e),
                'collections': {},
                'total_collections': 0
            }
    
    def collect_processing_stats(self):
        """Collect processing statistics from log files"""
        stats = {
            'ai_scholar': {'downloads': 0, 'processed': 0, 'errors': 0},
            'quant_scholar': {'downloads': 0, 'processed': 0, 'errors': 0}
        }
        
        # Check log files for recent activity (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for instance in ['ai_scholar', 'quant_scholar']:
            log_path = Path(f'/opt/arxiv-system/data/{instance}/logs')
            if log_path.exists():
                for log_file in log_path.glob('*.log'):
                    try:
                        with open(log_file, 'r') as f:
                            for line in f:
                                if 'downloaded' in line.lower():
                                    stats[instance]['downloads'] += 1
                                elif 'processed' in line.lower():
                                    stats[instance]['processed'] += 1
                                elif 'error' in line.lower():
                                    stats[instance]['errors'] += 1
                    except Exception as e:
                        self.logger.warning(f"Error reading log file {log_file}: {e}")
        
        return stats
    
    def collect_storage_stats(self):
        """Collect storage statistics"""
        storage_stats = {}
        
        for instance in ['ai_scholar', 'quant_scholar']:
            instance_path = Path(f'/opt/arxiv-system/data/{instance}')
            if instance_path.exists():
                # Count files and calculate sizes
                papers_path = instance_path / 'papers'
                cache_path = instance_path / 'cache'
                logs_path = instance_path / 'logs'
                
                stats = {
                    'papers': self._get_directory_stats(papers_path),
                    'cache': self._get_directory_stats(cache_path),
                    'logs': self._get_directory_stats(logs_path),
                    'total_size_mb': 0
                }
                
                # Calculate total size
                for category in ['papers', 'cache', 'logs']:
                    stats['total_size_mb'] += stats[category]['size_mb']
                
                storage_stats[instance] = stats
        
        return storage_stats
    
    def _get_directory_stats(self, path):
        """Get statistics for a directory"""
        if not path.exists():
            return {'file_count': 0, 'size_mb': 0}
        
        file_count = 0
        total_size = 0
        
        try:
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    file_count += 1
                    total_size += file_path.stat().st_size
        except Exception as e:
            self.logger.warning(f"Error calculating directory stats for {path}: {e}")
        
        return {
            'file_count': file_count,
            'size_mb': total_size / (1024 * 1024)
        }
    
    def collect_all_metrics(self):
        """Collect all application metrics"""
        timestamp = datetime.now().isoformat()
        
        metrics = {
            'timestamp': timestamp,
            'chromadb': self.check_chromadb_health(),
            'processing': self.collect_processing_stats(),
            'storage': self.collect_storage_stats()
        }
        
        return metrics
    
    def save_metrics(self, metrics):
        """Save metrics to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.data_dir / f'app_metrics_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        self.logger.info(f"Application metrics saved to {filename}")
        return filename
    
    def run_collection(self):
        """Run application metrics collection"""
        try:
            metrics = self.collect_all_metrics()
            self.save_metrics(metrics)
            
            # Log key metrics
            chromadb_status = "UP" if metrics['chromadb']['health_status'] else "DOWN"
            total_collections = metrics['chromadb']['total_collections']
            
            self.logger.info(f"Application Status - ChromaDB: {chromadb_status}, Collections: {total_collections}")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting application metrics: {e}")
            return None

if __name__ == "__main__":
    collector = ApplicationMetricsCollector()
    collector.run_collection()
EOF

chmod +x /opt/arxiv-system/monitoring/scripts/app_metrics.py
```

## Alerting System Setup

### 1. Alert Configuration

Create the alert configuration file:

```bash
cat > /opt/arxiv-system/monitoring/config/alerts.yaml << 'EOF'
# Alert configuration for Multi-Instance ArXiv System

alerts:
  system:
    cpu_threshold: 85.0  # CPU usage percentage
    memory_threshold: 90.0  # Memory usage percentage
    disk_threshold: 85.0  # Disk usage percentage
    load_threshold: 8.0  # Load average threshold
    
  application:
    chromadb_down: true  # Alert if ChromaDB is down
    processing_errors_threshold: 10  # Max errors per hour
    response_time_threshold: 5000  # Max response time in ms
    
  storage:
    low_space_threshold: 5.0  # GB of free space
    growth_rate_threshold: 10.0  # GB per day growth rate
    
notification:
  email:
    enabled: true
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    username: "your-email@gmail.com"
    recipients:
      - "admin@yourorg.com"
      - "ops@yourorg.com"
    
  slack:
    enabled: false
    webhook_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    channel: "#alerts"
    
  severity_levels:
    critical: ["chromadb_down", "disk_threshold", "memory_threshold"]
    warning: ["cpu_threshold", "processing_errors_threshold"]
    info: ["storage_growth"]
EOF
```

### 2. Alert Manager

Create the alert manager script:

```bash
cat > /opt/arxiv-system/monitoring/scripts/alert_manager.py << 'EOF'
#!/usr/bin/env python3
"""
Alert manager for Multi-Instance ArXiv System
"""

import json
import yaml
import smtplib
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AlertManager:
    def __init__(self, config_path="/opt/arxiv-system/monitoring/config/alerts.yaml"):
        self.config_path = Path(config_path)
        self.load_config()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/opt/arxiv-system/logs/alerts.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Alert state tracking
        self.alert_state_file = Path('/opt/arxiv-system/monitoring/data/alert_state.json')
        self.load_alert_state()
    
    def load_config(self):
        """Load alert configuration"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Error loading alert config: {e}")
            self.config = {}
    
    def load_alert_state(self):
        """Load previous alert state"""
        try:
            if self.alert_state_file.exists():
                with open(self.alert_state_file, 'r') as f:
                    self.alert_state = json.load(f)
            else:
                self.alert_state = {}
        except Exception as e:
            self.logger.error(f"Error loading alert state: {e}")
            self.alert_state = {}
    
    def save_alert_state(self):
        """Save current alert state"""
        try:
            with open(self.alert_state_file, 'w') as f:
                json.dump(self.alert_state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving alert state: {e}")
    
    def check_system_alerts(self, metrics):
        """Check system metrics for alert conditions"""
        alerts = []
        system_config = self.config.get('alerts', {}).get('system', {})
        
        # CPU usage alert
        cpu_percent = metrics.get('cpu', {}).get('cpu_percent', 0)
        if cpu_percent > system_config.get('cpu_threshold', 85):
            alerts.append({
                'type': 'cpu_threshold',
                'severity': 'warning',
                'message': f'High CPU usage: {cpu_percent:.1f}%',
                'value': cpu_percent,
                'threshold': system_config.get('cpu_threshold', 85)
            })
        
        # Memory usage alert
        memory_percent = metrics.get('memory', {}).get('memory', {}).get('percent', 0)
        if memory_percent > system_config.get('memory_threshold', 90):
            alerts.append({
                'type': 'memory_threshold',
                'severity': 'critical',
                'message': f'High memory usage: {memory_percent:.1f}%',
                'value': memory_percent,
                'threshold': system_config.get('memory_threshold', 90)
            })
        
        # Disk usage alert
        disk_metrics = metrics.get('disk', {})
        for path, disk_info in disk_metrics.items():
            disk_percent = disk_info.get('percent', 0)
            if disk_percent > system_config.get('disk_threshold', 85):
                alerts.append({
                    'type': 'disk_threshold',
                    'severity': 'critical',
                    'message': f'High disk usage on {path}: {disk_percent:.1f}%',
                    'value': disk_percent,
                    'threshold': system_config.get('disk_threshold', 85),
                    'path': path
                })
        
        return alerts
    
    def check_application_alerts(self, metrics):
        """Check application metrics for alert conditions"""
        alerts = []
        app_config = self.config.get('alerts', {}).get('application', {})
        
        # ChromaDB health alert
        chromadb_health = metrics.get('chromadb', {}).get('health_status', False)
        if not chromadb_health and app_config.get('chromadb_down', True):
            alerts.append({
                'type': 'chromadb_down',
                'severity': 'critical',
                'message': 'ChromaDB is not responding',
                'value': False,
                'threshold': True
            })
        
        # Response time alert
        response_time = metrics.get('chromadb', {}).get('response_time_ms', 0)
        if response_time > app_config.get('response_time_threshold', 5000):
            alerts.append({
                'type': 'response_time_threshold',
                'severity': 'warning',
                'message': f'High ChromaDB response time: {response_time:.0f}ms',
                'value': response_time,
                'threshold': app_config.get('response_time_threshold', 5000)
            })
        
        return alerts
    
    def should_send_alert(self, alert):
        """Determine if alert should be sent (avoid spam)"""
        alert_key = f"{alert['type']}_{alert.get('path', '')}"
        current_time = datetime.now()
        
        # Check if we've sent this alert recently
        if alert_key in self.alert_state:
            last_sent = datetime.fromisoformat(self.alert_state[alert_key]['last_sent'])
            cooldown_hours = 1 if alert['severity'] == 'critical' else 4
            
            if current_time - last_sent < timedelta(hours=cooldown_hours):
                return False
        
        # Update alert state
        self.alert_state[alert_key] = {
            'last_sent': current_time.isoformat(),
            'count': self.alert_state.get(alert_key, {}).get('count', 0) + 1
        }
        
        return True
    
    def send_email_alert(self, alerts):
        """Send email alert"""
        try:
            email_config = self.config.get('notification', {}).get('email', {})
            if not email_config.get('enabled', False):
                return
            
            # Create email content
            subject = f"ArXiv System Alert - {len(alerts)} issue(s) detected"
            
            body = "Multi-Instance ArXiv System Alert\n"
            body += "=" * 40 + "\n\n"
            body += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            critical_alerts = [a for a in alerts if a['severity'] == 'critical']
            warning_alerts = [a for a in alerts if a['severity'] == 'warning']
            
            if critical_alerts:
                body += "CRITICAL ALERTS:\n"
                body += "-" * 20 + "\n"
                for alert in critical_alerts:
                    body += f"• {alert['message']}\n"
                body += "\n"
            
            if warning_alerts:
                body += "WARNING ALERTS:\n"
                body += "-" * 20 + "\n"
                for alert in warning_alerts:
                    body += f"• {alert['message']}\n"
                body += "\n"
            
            body += "Please check the system and take appropriate action.\n"
            body += "\nSystem Dashboard: http://your-monitoring-dashboard.com\n"
            
            # Send email
            msg = MIMEMultipart()
            msg['From'] = email_config['username']
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_host'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['username'], email_config.get('password', ''))
            
            for recipient in email_config.get('recipients', []):
                msg['To'] = recipient
                server.send_message(msg)
                del msg['To']
            
            server.quit()
            self.logger.info(f"Alert email sent to {len(email_config.get('recipients', []))} recipients")
            
        except Exception as e:
            self.logger.error(f"Error sending email alert: {e}")
    
    def process_alerts(self, system_metrics, app_metrics):
        """Process all alerts"""
        all_alerts = []
        
        # Check system alerts
        if system_metrics:
            all_alerts.extend(self.check_system_alerts(system_metrics))
        
        # Check application alerts
        if app_metrics:
            all_alerts.extend(self.check_application_alerts(app_metrics))
        
        # Filter alerts that should be sent
        alerts_to_send = [alert for alert in all_alerts if self.should_send_alert(alert)]
        
        if alerts_to_send:
            self.logger.warning(f"Sending {len(alerts_to_send)} alerts")
            self.send_email_alert(alerts_to_send)
            self.save_alert_state()
        else:
            self.logger.info("No alerts to send")
        
        return alerts_to_send

if __name__ == "__main__":
    # Load latest metrics and check for alerts
    alert_manager = AlertManager()
    
    # Load latest system metrics
    system_metrics = None
    app_metrics = None
    
    data_dir = Path('/opt/arxiv-system/monitoring/data')
    
    # Find latest system metrics file
    system_files = sorted(data_dir.glob('system_metrics_*.json'))
    if system_files:
        with open(system_files[-1], 'r') as f:
            system_metrics = json.load(f)
    
    # Find latest app metrics file
    app_files = sorted(data_dir.glob('app_metrics_*.json'))
    if app_files:
        with open(app_files[-1], 'r') as f:
            app_metrics = json.load(f)
    
    # Process alerts
    alert_manager.process_alerts(system_metrics, app_metrics)
EOF

chmod +x /opt/arxiv-system/monitoring/scripts/alert_manager.py
```

## Performance Monitoring

### 1. Performance Dashboard

Create a simple web dashboard for monitoring:

```bash
cat > /opt/arxiv-system/monitoring/scripts/dashboard.py << 'EOF'
#!/usr/bin/env python3
"""
Simple web dashboard for Multi-Instance ArXiv System monitoring
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>ArXiv System Monitoring Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; margin-bottom: 20px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .metric-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
        .metric-title { font-weight: bold; margin-bottom: 10px; color: #2c3e50; }
        .metric-value { font-size: 24px; margin: 5px 0; }
        .status-ok { color: #27ae60; }
        .status-warning { color: #f39c12; }
        .status-critical { color: #e74c3c; }
        .timestamp { color: #7f8c8d; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Multi-Instance ArXiv System - Monitoring Dashboard</h1>
        <p>Last Updated: {{ timestamp }}</p>
    </div>
    
    <div class="metrics-grid">
        <!-- System Metrics -->
        <div class="metric-card">
            <div class="metric-title">System Resources</div>
            <div class="metric-value status-{{ cpu_status }}">CPU: {{ cpu_percent }}%</div>
            <div class="metric-value status-{{ memory_status }}">Memory: {{ memory_percent }}%</div>
            <div class="metric-value status-{{ disk_status }}">Disk: {{ disk_percent }}%</div>
        </div>
        
        <!-- ChromaDB Status -->
        <div class="metric-card">
            <div class="metric-title">ChromaDB Status</div>
            <div class="metric-value status-{{ chromadb_status }}">{{ chromadb_health }}</div>
            <div>Collections: {{ total_collections }}</div>
            <div>Response Time: {{ response_time }}ms</div>
        </div>
        
        <!-- AI Scholar Instance -->
        <div class="metric-card">
            <div class="metric-title">AI Scholar Instance</div>
            <div>Papers: {{ ai_papers }} files</div>
            <div>Storage: {{ ai_storage_mb }} MB</div>
            <div>Recent Downloads: {{ ai_downloads }}</div>
            <div>Recent Errors: {{ ai_errors }}</div>
        </div>
        
        <!-- Quant Scholar Instance -->
        <div class="metric-card">
            <div class="metric-title">Quant Scholar Instance</div>
            <div>Papers: {{ quant_papers }} files</div>
            <div>Storage: {{ quant_storage_mb }} MB</div>
            <div>Recent Downloads: {{ quant_downloads }}</div>
            <div>Recent Errors: {{ quant_errors }}</div>
        </div>
        
        <!-- Recent Alerts -->
        <div class="metric-card">
            <div class="metric-title">Recent Alerts</div>
            {% if recent_alerts %}
                {% for alert in recent_alerts %}
                <div class="status-{{ alert.severity }}">{{ alert.message }}</div>
                {% endfor %}
            {% else %}
                <div class="status-ok">No recent alerts</div>
            {% endif %}
        </div>
        
        <!-- Storage Breakdown -->
        <div class="metric-card">
            <div class="metric-title">Storage Breakdown</div>
            <div>Total Used: {{ total_storage_gb }} GB</div>
            <div>AI Scholar: {{ ai_storage_gb }} GB</div>
            <div>Quant Scholar: {{ quant_storage_gb }} GB</div>
            <div>Free Space: {{ free_space_gb }} GB</div>
        </div>
    </div>
</body>
</html>
'''

class DashboardData:
    def __init__(self):
        self.data_dir = Path('/opt/arxiv-system/monitoring/data')
    
    def get_latest_metrics(self):
        """Get latest system and application metrics"""
        system_metrics = None
        app_metrics = None
        
        # Get latest system metrics
        system_files = sorted(self.data_dir.glob('system_metrics_*.json'))
        if system_files:
            with open(system_files[-1], 'r') as f:
                system_metrics = json.load(f)
        
        # Get latest app metrics
        app_files = sorted(self.data_dir.glob('app_metrics_*.json'))
        if app_files:
            with open(app_files[-1], 'r') as f:
                app_metrics = json.load(f)
        
        return system_metrics, app_metrics
    
    def get_status_class(self, value, warning_threshold, critical_threshold):
        """Get CSS class based on value and thresholds"""
        if value >= critical_threshold:
            return 'critical'
        elif value >= warning_threshold:
            return 'warning'
        else:
            return 'ok'
    
    def prepare_dashboard_data(self):
        """Prepare data for dashboard template"""
        system_metrics, app_metrics = self.get_latest_metrics()
        
        if not system_metrics or not app_metrics:
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error': 'No metrics data available'
            }
        
        # System metrics
        cpu_percent = system_metrics.get('cpu', {}).get('cpu_percent', 0)
        memory_percent = system_metrics.get('memory', {}).get('memory', {}).get('percent', 0)
        
        # Disk metrics (main system)
        disk_info = system_metrics.get('disk', {}).get('/opt/arxiv-system', {})
        disk_percent = disk_info.get('percent', 0)
        free_space_gb = disk_info.get('free', 0) / (1024**3)
        
        # ChromaDB metrics
        chromadb = app_metrics.get('chromadb', {})
        chromadb_health = "UP" if chromadb.get('health_status', False) else "DOWN"
        total_collections = chromadb.get('total_collections', 0)
        response_time = chromadb.get('response_time_ms', 0)
        
        # Instance metrics
        storage = app_metrics.get('storage', {})
        processing = app_metrics.get('processing', {})
        
        ai_scholar = storage.get('ai_scholar', {})
        quant_scholar = storage.get('quant_scholar', {})
        
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'cpu_percent': f"{cpu_percent:.1f}",
            'cpu_status': self.get_status_class(cpu_percent, 70, 85),
            'memory_percent': f"{memory_percent:.1f}",
            'memory_status': self.get_status_class(memory_percent, 80, 90),
            'disk_percent': f"{disk_percent:.1f}",
            'disk_status': self.get_status_class(disk_percent, 80, 90),
            'chromadb_health': chromadb_health,
            'chromadb_status': 'ok' if chromadb_health == 'UP' else 'critical',
            'total_collections': total_collections,
            'response_time': f"{response_time:.0f}",
            'ai_papers': ai_scholar.get('papers', {}).get('file_count', 0),
            'ai_storage_mb': f"{ai_scholar.get('total_size_mb', 0):.1f}",
            'ai_storage_gb': f"{ai_scholar.get('total_size_mb', 0) / 1024:.2f}",
            'ai_downloads': processing.get('ai_scholar', {}).get('downloads', 0),
            'ai_errors': processing.get('ai_scholar', {}).get('errors', 0),
            'quant_papers': quant_scholar.get('papers', {}).get('file_count', 0),
            'quant_storage_mb': f"{quant_scholar.get('total_size_mb', 0):.1f}",
            'quant_storage_gb': f"{quant_scholar.get('total_size_mb', 0) / 1024:.2f}",
            'quant_downloads': processing.get('quant_scholar', {}).get('downloads', 0),
            'quant_errors': processing.get('quant_scholar', {}).get('errors', 0),
            'total_storage_gb': f"{(ai_scholar.get('total_size_mb', 0) + quant_scholar.get('total_size_mb', 0)) / 1024:.2f}",
            'free_space_gb': f"{free_space_gb:.2f}",
            'recent_alerts': []  # TODO: Load from alert history
        }

dashboard_data = DashboardData()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    data = dashboard_data.prepare_dashboard_data()
    return render_template_string(DASHBOARD_TEMPLATE, **data)

@app.route('/api/metrics')
def api_metrics():
    """API endpoint for metrics data"""
    system_metrics, app_metrics = dashboard_data.get_latest_metrics()
    return jsonify({
        'system': system_metrics,
        'application': app_metrics
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF

chmod +x /opt/arxiv-system/monitoring/scripts/dashboard.py
```

## Automated Monitoring Setup

### 1. Create Monitoring Cron Jobs

```bash
# Create comprehensive monitoring script
cat > /opt/arxiv-system/monitoring/scripts/run_monitoring.sh << 'EOF'
#!/bin/bash

cd /opt/arxiv-system
source venv/bin/activate

# Collect system metrics
python monitoring/scripts/system_metrics.py

# Collect application metrics
python monitoring/scripts/app_metrics.py

# Check for alerts
python monitoring/scripts/alert_manager.py

# Cleanup old metric files (keep last 7 days)
find /opt/arxiv-system/monitoring/data -name "*.json" -mtime +7 -delete
EOF

chmod +x /opt/arxiv-system/monitoring/scripts/run_monitoring.sh

# Add to crontab (run every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/arxiv-system/monitoring/scripts/run_monitoring.sh") | crontab -
```

### 2. Create Health Check Script

```bash
cat > /opt/arxiv-system/monitoring/scripts/health_check.sh << 'EOF'
#!/bin/bash

echo "=== Multi-Instance ArXiv System Health Check ==="
echo "Timestamp: $(date)"
echo

# Check ChromaDB
echo "ChromaDB Status:"
if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; then
    echo "  ✓ ChromaDB is running"
else
    echo "  ✗ ChromaDB is not responding"
fi

# Check disk space
echo
echo "Disk Usage:"
df -h /opt/arxiv-system | tail -1 | awk '{print "  " $1 ": " $5 " used (" $4 " free)"}'

# Check system resources
echo
echo "System Resources:"
echo "  CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)% used"
echo "  Memory: $(free | grep Mem | awk '{printf "%.1f%% used", $3/$2 * 100.0}')"

# Check recent errors
echo
echo "Recent Errors (last hour):"
error_count=$(find /opt/arxiv-system/logs -name "*.log" -mmin -60 -exec grep -i error {} \; | wc -l)
if [ $error_count -eq 0 ]; then
    echo "  ✓ No errors found"
else
    echo "  ⚠ $error_count errors found in logs"
fi

# Check instance data
echo
echo "Instance Status:"
for instance in ai_scholar quant_scholar; do
    if [ -d "/opt/arxiv-system/data/$instance" ]; then
        paper_count=$(find /opt/arxiv-system/data/$instance/papers -name "*.pdf" 2>/dev/null | wc -l)
        echo "  $instance: $paper_count papers"
    else
        echo "  $instance: directory not found"
    fi
done

echo
echo "Health check completed."
EOF

chmod +x /opt/arxiv-system/monitoring/scripts/health_check.sh
```

This completes the monitoring and alerting setup guide. Now let me mark this task as complete and move to the next task.

<function_calls>
<invoke name="taskStatus">
<parameter name="taskFilePath">.kiro/specs/multi-instance-arxiv-system/tasks.md