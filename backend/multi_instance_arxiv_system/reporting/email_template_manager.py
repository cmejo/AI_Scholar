"""
Email Template Manager for multi-instance ArXiv system.

Manages different notification types, template loading, and responsive HTML email templates.
Provides a centralized system for managing email templates with different priorities and formats.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import jinja2
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications supported by the system."""
    UPDATE_SUCCESS = "update_success"
    UPDATE_FAILURE = "update_failure"
    STORAGE_WARNING = "storage_warning"
    STORAGE_CRITICAL = "storage_critical"
    ERROR_SUMMARY = "error_summary"
    SYSTEM_HEALTH = "system_health"
    TEST_NOTIFICATION = "test_notification"


class NotificationPriority(Enum):
    """Priority levels for notifications."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EmailTemplate:
    """Email template configuration."""
    template_name: str
    notification_type: NotificationType
    priority: NotificationPriority
    subject_template: str
    html_template_path: str
    text_template_path: Optional[str] = None
    description: str = ""
    variables: List[str] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'template_name': self.template_name,
            'notification_type': self.notification_type.value,
            'priority': self.priority.value,
            'subject_template': self.subject_template,
            'html_template_path': self.html_template_path,
            'text_template_path': self.text_template_path,
            'description': self.description,
            'variables': self.variables,
            'created_date': self.created_date.isoformat(),
            'last_modified': self.last_modified.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailTemplate':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            template_name=data['template_name'],
            notification_type=NotificationType(data['notification_type']),
            priority=NotificationPriority(data['priority']),
            subject_template=data['subject_template'],
            html_template_path=data['html_template_path'],
            text_template_path=data.get('text_template_path'),
            description=data.get('description', ''),
            variables=data.get('variables', []),
            created_date=datetime.fromisoformat(data['created_date']),
            last_modified=datetime.fromisoformat(data['last_modified'])
        )


class EmailTemplateManager:
    """Manages email templates for different notification types."""
    
    def __init__(self, templates_directory: str = None):
        """
        Initialize email template manager.
        
        Args:
            templates_directory: Directory containing email templates
        """
        self.templates_directory = Path(templates_directory or 
                                       Path(__file__).parent / "templates")
        self.templates_directory.mkdir(parents=True, exist_ok=True)
        
        # Template registry
        self.templates: Dict[str, EmailTemplate] = {}
        
        # Jinja2 environment for template rendering
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_directory)),
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.jinja_env.filters['format_datetime'] = self._format_datetime
        self.jinja_env.filters['format_filesize'] = self._format_filesize
        self.jinja_env.filters['format_percentage'] = self._format_percentage
        
        # Load existing templates
        self._load_templates()
        
        # Create default templates if none exist
        if not self.templates:
            self._create_default_templates()
        
        logger.info(f"EmailTemplateManager initialized with {len(self.templates)} templates")
    
    def _format_datetime(self, dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime for template display."""
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        return dt.strftime(format_str)
    
    def _format_filesize(self, size_bytes: float) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def _format_percentage(self, value: float, decimals: int = 1) -> str:
        """Format percentage value."""
        return f"{value:.{decimals}f}%"
    
    def _load_templates(self) -> None:
        """Load existing templates from registry file."""
        registry_file = self.templates_directory / "template_registry.json"
        if registry_file.exists():
            try:
                with open(registry_file, 'r') as f:
                    registry_data = json.load(f)
                
                for template_data in registry_data.get('templates', []):
                    template = EmailTemplate.from_dict(template_data)
                    self.templates[template.template_name] = template
                
                logger.info(f"Loaded {len(self.templates)} templates from registry")
                
            except Exception as e:
                logger.error(f"Failed to load template registry: {e}")
    
    def _save_templates(self) -> None:
        """Save templates to registry file."""
        registry_file = self.templates_directory / "template_registry.json"
        try:
            registry_data = {
                'templates': [template.to_dict() for template in self.templates.values()],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(registry_file, 'w') as f:
                json.dump(registry_data, f, indent=2)
            
            logger.info(f"Saved {len(self.templates)} templates to registry")
            
        except Exception as e:
            logger.error(f"Failed to save template registry:ss_rate", "timestamp"]
            ),
            
            # Update Failure Template
            EmailTemplate(
                template_name="update_failure_detailed",
                notification_type=NotificationType.UPDATE_FAILURE,
                priority=NotificationPriority.HIGH,
                subject_template="❌ Monthly Update Failed - {{ instance_name|title }} ({{ error_count }} errors)",
                html_template_path="update_failure_detailed.html",
                description="Detailed failure report with error analysis and recommendations",
                variables=["report", "instance_name", "error_count", "error_details", "timestamp"]
            ),
            
            # Update Warning Template
            EmailTemplate(
                template_name="update_warning_issues",
                notification_type=NotificationType.UPDATE_WARNING,
                priority=NotificationPriority.HIGH,
                subject_template="⚠️ Monthly Update Issues Detected - {{ instance_name|title }} ({{ success_rate }}% success)",
                html_template_path="update_warning_issues.html",
                description="Warning report for updates with significant issues",
                variables=["report", "instance_name", "success_rate", "warning_details", "timestamp"]
            ),
            
            # Storage Alert Template
            EmailTemplate(
                template_name="storage_alert_comprehensive",
                notification_type=NotificationType.STORAGE_ALERT,
                priority=NotificationPriority.HIGH,
                subject_template="💾 Storage Alert - {{ alert_level|title }} ({{ usage_percentage }}% used)",
                html_template_path="storage_alert_comprehensive.html",
                description="Comprehensive storage monitoring alert with recommendations",
                variables=["alert_level", "usage_percentage", "storage_stats", "recommendations", "timestamp"]
            ),
            
            # Storage Critical Template
            EmailTemplate(
                template_name="storage_critical_urgent",
                notification_type=NotificationType.STORAGE_CRITICAL,
                priority=NotificationPriority.CRITICAL,
                subject_template="🚨 CRITICAL: Storage Almost Full - {{ usage_percentage }}% used ({{ available_gb }}GB remaining)",
                html_template_path="storage_critical_urgent.html",
                description="Critical storage alert requiring immediate action",
                variables=["usage_percentage", "available_gb", "storage_stats", "urgent_actions", "timestamp"]
            ),
            
            # Error Summary Template
            EmailTemplate(
                template_name="error_summary_analysis",
                notification_type=NotificationType.ERROR_SUMMARY,
                priority=NotificationPriority.HIGH,
                subject_template="📊 Error Summary Report - {{ total_errors }} errors across {{ instance_count }} instances",
                html_template_path="error_summary_analysis.html",
                description="Comprehensive error analysis across all instances",
                variables=["total_errors", "instance_count", "error_analysis", "trends", "timestamp"]
            ),
            
            # System Health Template
            EmailTemplate(
                template_name="system_health_report",
                notification_type=NotificationType.SYSTEM_HEALTH,
                priority=NotificationPriority.NORMAL,
                subject_template="🏥 System Health Report - {{ overall_status|title }} Status",
                html_template_path="system_health_report.html",
                description="Overall system health and performance report",
                variables=["overall_status", "health_metrics", "performance_data", "recommendations", "timestamp"]
            ),
            
            # Performance Alert Template
            EmailTemplate(
                template_name="performance_alert_degradation",
                notification_type=NotificationType.PERFORMANCE_ALERT,
                priority=NotificationPriority.HIGH,
                subject_template="⚡ Performance Alert - {{ metric_name }} degraded by {{ degradation_percent }}%",
                html_template_path="performance_alert_degradation.html",
                description="Performance degradation alert with analysis",
                variables=["metric_name", "degradation_percent", "performance_metrics", "analysis", "timestamp"]
            ),
            
            # Test Notification Template
            EmailTemplate(
                template_name="test_notification_simple",
                notification_type=NotificationType.TEST_NOTIFICATION,
                priority=NotificationPriority.LOW,
                subject_template="🧪 Test Notification - Multi-Instance ArXiv System",
                html_template_path="test_notification_simple.html",
                description="Simple test notification to verify email configuration",
                variables=["system_info", "timestamp"]
            )
        ]
        
        # Register templates
        for template in default_templates:
            self.register_template(template)
        
        # Create corresponding HTML template files
        self._create_default_html_templates()
        
        logger.info(f"Created {len(default_templates)} default templates")
    
    def _create_default_html_templates(self) -> None:
        """Create default HTML template files."""
        
        # Base template with responsive design
        base_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{{ title }}</title>
    <style>
        /* Reset and base styles */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333333;
            background-color: #f8f9fa;
        }
        
        /* Container and layout */
        .email-container {
            max-width: 800px;
            margin: 0 auto;
            background-color: #ffffff;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .header .subtitle {
            font-size: 16px;
            opacity: 0.9;
        }
        
        .content {
            padding: 30px 20px;
        }
        
        .section {
            margin-bottom: 30px;
            padding: 20px;
            border-left: 4px solid #667eea;
            background-color: #f8f9fa;
            border-radius: 0 8px 8px 0;
        }
        
        .section h2 {
            color: #2c3e50;
            font-size: 22px;
            margin-bottom: 15px;
            font-weight: 600;
        }
        
        .section h3 {
            color: #34495e;
            font-size: 18px;
            margin-bottom: 10px;
            font-weight: 500;
        }
        
        /* Stats grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .stat-card .number {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
            display: block;
        }
        
        .stat-card .label {
            font-size: 14px;
            opacity: 0.9;
        }
        
        /* Status indicators */
        .status-success { color: #28a745; font-weight: bold; }
        .status-warning { color: #ffc107; font-weight: bold; }
        .status-error { color: #dc3545; font-weight: bold; }
        .status-info { color: #17a2b8; font-weight: bold; }
        
        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }
        
        tr:hover {
            background-color: #f8f9fa;
        }
        
        /* Progress bars */
        .progress-bar {
            width: 100%;
            height: 24px;
            background-color: #e9ecef;
            border-radius: 12px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s ease;
            border-radius: 12px;
        }
        
        .progress-fill.warning {
            background: linear-gradient(90deg, #ffc107, #fd7e14);
        }
        
        .progress-fill.danger {
            background: linear-gradient(90deg, #dc3545, #e83e8c);
        }
        
        /* Charts and images */
        .chart-container {
            text-align: center;
            margin: 20px 0;
        }
        
        .chart-image {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        
        /* Error and alert boxes */
        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid;
        }
        
        .alert-success {
            background-color: #d4edda;
            border-left-color: #28a745;
            color: #155724;
        }
        
        .alert-warning {
            background-color: #fff3cd;
            border-left-color: #ffc107;
            color: #856404;
        }
        
        .alert-error {
            background-color: #f8d7da;
            border-left-color: #dc3545;
            color: #721c24;
        }
        
        .alert-info {
            background-color: #d1ecf1;
            border-left-color: #17a2b8;
            color: #0c5460;
        }
        
        /* Error list */
        .error-list {
            background-color: #fff5f5;
            border: 1px solid #fed7d7;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }
        
        .error-item {
            padding: 10px;
            margin: 8px 0;
            background-color: #fee;
            border-left: 4px solid #dc3545;
            border-radius: 4px;
            font-size: 14px;
        }
        
        /* Recommendations */
        .recommendation {
            background-color: #e7f3ff;
            border: 1px solid #b8daff;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }
        
        .recommendation h4 {
            color: #004085;
            margin-bottom: 10px;
        }
        
        .recommendation ul {
            margin-left: 20px;
        }
        
        .recommendation li {
            margin: 5px 0;
        }
        
        /* Footer */
        .footer {
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            border-top: 1px solid #e9ecef;
            color: #6c757d;
            font-size: 14px;
        }
        
        .timestamp {
            font-size: 12px;
            color: #adb5bd;
            margin-top: 10px;
        }
        
        /* Responsive design */
        @media only screen and (max-width: 600px) {
            .email-container {
                margin: 0;
                box-shadow: none;
            }
            
            .header, .content, .footer {
                padding: 20px 15px;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .stat-card .number {
                font-size: 28px;
            }
            
            .section {
                padding: 15px;
            }
            
            table {
                font-size: 14px;
            }
            
            th, td {
                padding: 8px 10px;
            }
        }
        
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            body {
                background-color: #1a1a1a;
                color: #e9ecef;
            }
            
            .email-container {
                background-color: #2d3748;
            }
            
            .section {
                background-color: #4a5568;
            }
            
            th {
                background-color: #4a5568;
                color: #e9ecef;
            }
            
            .alert-success {
                background-color: #2d5a3d;
                color: #a3d9a5;
            }
            
            .alert-warning {
                background-color: #5d4e2a;
                color: #f6e05e;
            }
            
            .alert-error {
                background-color: #5d2a2a;
                color: #feb2b2;
            }
            
            .alert-info {
                background-color: #2a4a5d;
                color: #90cdf4;
            }
        }
    </style>
</head>
<body>
    <div class="email-container">
        {% block content %}{% endblock %}
        
        <div class="footer">
            <p><strong>Multi-Instance ArXiv System</strong></p>
            <p>Automated Research Paper Processing & Analysis</p>
            <div class="timestamp">
                Generated on {{ timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') if timestamp else 'N/A' }}
            </div>
        </div>
    </div>
</body>
</html>'''
        
        # Save base template
        base_template_file = self.templates_directory / "base_email.html"
        with open(base_template_file, 'w') as f:
            f.write(base_template)
        
        # Create specific templates
        templates_content = {
            'update_success_comprehensive.html': '''{% extends "base_email.html" %}

{% block content %}
<div class="header">
    <h1>✅ Monthly Update Completed Successfully</h1>
    <div class="subtitle">{{ report.instance_name|title }} - {{ report.update_date.strftime('%B %d, %Y') }}</div>
</div>

<div class="content">
    <div class="section">
        <h2>📊 Processing Summary</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <span class="number">{{ report.papers_discovered }}</span>
                <div class="label">Papers Discovered</div>
            </div>
            <div class="stat-card">
                <span class="number">{{ report.papers_processed }}</span>
                <div class="label">Successfully Processed</div>
            </div>
            <div class="stat-card">
                <span class="number">{{ report.papers_failed }}</span>
                <div class="label">Failed</div>
            </div>
            <div class="stat-card">
                <span class="number">{{ "%.1f"|format((report.papers_processed / report.papers_discovered * 100) if report.papers_discovered > 0 else 0) }}%</span>
                <div class="label">Success Rate</div>
            </div>
        </div>
        
        {% if report.papers_processed > 0 %}
        <div class="progress-bar">
            <div class="progress-fill" style="width: {{ (report.papers_processed / report.papers_discovered * 100) if report.papers_discovered > 0 else 0 }}%"></div>
        </div>
        {% endif %}
    </div>
    
    {% if report.performance_metrics %}
    <div class="section">
        <h2>⚡ Performance Metrics</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
                <th>Unit</th>
            </tr>
            <tr>
                <td>Processing Rate</td>
                <td>{{ "%.1f"|format(report.performance_metrics.processing_rate_papers_per_hour) }}</td>
                <td>Papers/hour</td>
            </tr>
            <tr>
                <td>Download Rate</td>
                <td>{{ "%.2f"|format(report.performance_metrics.download_rate_mbps) }}</td>
                <td>Mbps</td>
            </tr>
            <tr>
                <td>Processing Time</td>
                <td>{{ "%.1f"|format(report.processing_time_seconds / 3600) }}</td>
                <td>Hours</td>
            </tr>
            <tr>
                <td>Memory Usage (Peak)</td>
                <td>{{ report.performance_metrics.memory_usage_peak_mb }}</td>
                <td>MB</td>
            </tr>
        </table>
    </div>
    {% endif %}
    
    {% if report.storage_stats %}
    <div class="section">
        <h2>💾 Storage Status</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <span class="number">{{ "%.1f"|format(report.storage_stats.used_space_gb) }}</span>
                <div class="label">Used (GB)</div>
            </div>
            <div class="stat-card">
                <span class="number">{{ "%.1f"|format(report.storage_stats.available_space_gb) }}</span>
                <div class="label">Available (GB)</div>
            </div>
            <div class="stat-card">
                <span class="number">{{ "%.1f"|format(report.storage_stats.usage_percentage) }}%</span>
                <div class="label">Usage</div>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill {% if report.storage_stats.usage_percentage > 85 %}danger{% elif report.storage_stats.usage_percentage > 70 %}warning{% endif %}" 
                 style="width: {{ report.storage_stats.usage_percentage }}%"></div>
        </div>
    </div>
    {% endif %}
    
    {% if report.errors %}
    <div class="section">
        <h2>⚠️ Issues Encountered</h2>
        <div class="alert alert-warning">
            <strong>{{ report.errors|length }} errors occurred during processing</strong>
        </div>
        
        {% for error in report.errors[:5] %}
        <div class="error-item">
            <strong>{{ error.category.value if error.category.value else error.category }}</strong>: {{ error.error_message }}<br>
            <small>File: {{ error.file_path }}</small>
        </div>
        {% endfor %}
        
        {% if report.errors|length > 5 %}
        <p><em>... and {{ report.errors|length - 5 }} more errors</em></p>
        {% endif %}
    </div>
    {% else %}
    <div class="section">
        <div class="alert alert-success">
            <strong>✅ No errors occurred during processing!</strong>
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}''',

            'update_failure_detailed.html': '''{% extends "base_email.html" %}

{% block content %}
<div class="header" style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);">
    <h1>❌ Monthly Update Failed</h1>
    <div class="subtitle">{{ report.instance_name|title }} - {{ report.update_date.strftime('%B %d, %Y') }}</div>
</div>

<div class="content">
    <div class="alert alert-error">
        <h3>Update Failed</h3>
        <p>The monthly update for {{ report.instance_name|title }} encountered critical errors and could not complete successfully.</p>
    </div>
    
    <div class="section">
        <h2>📊 Failure Summary</h2>
        <div class="stats-grid">
            <div class="stat-card" style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);">
                <span class="number">{{ report.papers_discovered }}</span>
                <div class="label">Papers Discovered</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);">
                <span class="number">{{ report.papers_processed }}</span>
                <div class="label">Successfully Processed</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);">
                <span class="number">{{ report.papers_failed }}</span>
                <div class="label">Failed</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);">
                <span class="number">{{ "%.1f"|format((report.papers_processed / report.papers_discovered * 100) if report.papers_discovered > 0 else 0) }}%</span>
                <div class="label">Success Rate</div>
            </div>
        </div>
    </div>
    
    {% if report.errors %}
    <div class="section">
        <h2>🚨 Error Details</h2>
        <div class="error-list">
            {% for error in report.errors %}
            <div class="error-item">
                <strong>{{ error.category.value if error.category.value else error.category }}</strong><br>
                <strong>File:</strong> {{ error.file_path }}<br>
                <strong>Error:</strong> {{ error.error_message }}<br>
                <strong>Time:</strong> {{ error.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}
    
    <div class="section">
        <h2>🔧 Recommended Actions</h2>
        <div class="recommendation">
            <h4>Immediate Actions Required:</h4>
            <ul>
                <li>Check system logs for detailed error information</li>
                <li>Verify system resources (disk space, memory, network connectivity)</li>
                <li>Run system health check to identify underlying issues</li>
                <li>Consider manual intervention for critical failures</li>
                <li>Review and restart failed processing jobs</li>
            </ul>
        </div>
        
        <div class="recommendation">
            <h4>Investigation Steps:</h4>
            <ul>
                <li>Review error patterns to identify common causes</li>
                <li>Check external service availability (arXiv, journal sources)</li>
                <li>Validate configuration files and permissions</li>
                <li>Monitor system performance during retry attempts</li>
            </ul>
        </div>
    </div>
</div>
{% endblock %}''',

            'storage_alert_comprehensive.html': '''{% extends "base_email.html" %}

{% block content %}
<div class="header" style="background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);">
    <h1>💾 Storage Alert</h1>
    <div class="subtitle">{{ alert_level|title }} - {{ usage_percentage }}% Used</div>
</div>

<div class="content">
    <div class="alert alert-{% if alert_level == 'critical' %}error{% else %}warning{% endif %}">
        <h3>{% if alert_level == 'critical' %}🚨 Critical Storage Alert{% else %}⚠️ Storage Warning{% endif %}</h3>
        <p>Storage usage has reached {{ usage_percentage }}% of total capacity.</p>
        {% if alert_level == 'critical' %}
        <p><strong>Immediate action required to prevent system disruption!</strong></p>
        {% endif %}
    </div>
    
    <div class="section">
        <h2>📊 Storage Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <span class="number">{{ "%.1f"|format(storage_stats.total_space_gb) }}</span>
                <div class="label">Total Space (GB)</div>
            </div>
            <div class="stat-card">
                <span class="number">{{ "%.1f"|format(storage_stats.used_space_gb) }}</span>
                <div class="label">Used Space (GB)</div>
            </div>
            <div class="stat-card">
                <span class="number">{{ "%.1f"|format(storage_stats.available_space_gb) }}</span>
                <div class="label">Available (GB)</div>
            </div>
            <div class="stat-card">
                <span class="number">{{ "%.1f"|format(storage_stats.usage_percentage) }}%</span>
                <div class="label">Usage Percentage</div>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill {% if storage_stats.usage_percentage > 95 %}danger{% elif storage_stats.usage_percentage > 85 %}warning{% endif %}" 
                 style="width: {{ storage_stats.usage_percentage }}%"></div>
        </div>
    </div>
    
    {% if storage_stats.instance_breakdown %}
    <div class="section">
        <h2>📂 Storage Breakdown by Instance</h2>
        <table>
            <tr>
                <th>Instance</th>
                <th>Storage Used (GB)</th>
                <th>Percentage of Total</th>
            </tr>
            {% for instance, usage_gb in storage_stats.instance_breakdown.items() %}
            <tr>
                <td>{{ instance|title }}</td>
                <td>{{ "%.1f"|format(usage_gb) }}</td>
                <td>{{ "%.1f"|format(usage_gb / storage_stats.total_space_gb * 100) }}%</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endif %}
    
    {% if recommendations %}
    <div class="section">
        <h2>🔧 Cleanup Recommendations</h2>
        {% for recommendation in recommendations %}
        <div class="recommendation">
            <h4>{{ recommendation.recommendation_type|title }} - {{ recommendation.priority|title }} Priority</h4>
            <p>{{ recommendation.description }}</p>
            {% if recommendation.estimated_space_savings_gb > 0 %}
            <p><strong>Estimated Savings:</strong> {{ "%.1f"|format(recommendation.estimated_space_savings_gb) }} GB</p>
            {% endif %}
            {% if recommendation.commands %}
            <p><strong>Commands to execute:</strong></p>
            <ul>
            {% for command in recommendation.commands %}
                <li><code>{{ command }}</code></li>
            {% endfor %}
            </ul>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    {% if storage_stats.projected_full_date %}
    <div class="section">
        <div class="alert alert-warning">
            <h4>📈 Storage Projection</h4>
            <p>At current growth rate ({{ "%.1f"|format(storage_stats.growth_rate_gb_per_month) }} GB/month), 
               storage will be full by <strong>{{ storage_stats.projected_full_date.strftime('%B %d, %Y') }}</strong>.</p>
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}''',

            'test_notification_simple.html': '''{% extends "base_email.html" %}

{% block content %}
<div class="header">
    <h1>🧪 Test Notification</h1>
    <div class="subtitle">Multi-Instance ArXiv System</div>
</div>

<div class="content">
    <div class="alert alert-info">
        <h3>✅ Email Configuration Test</h3>
        <p>This is a test notification to verify that email notifications are working correctly.</p>
    </div>
    
    <div class="section">
        <h2>📋 System Information</h2>
        <table>
            <tr>
                <th>Property</th>
                <th>Value</th>
            </tr>
            {% if system_info %}
            {% for key, value in system_info.items() %}
            <tr>
                <td>{{ key|title }}</td>
                <td>{{ value }}</td>
            </tr>
            {% endfor %}
            {% else %}
            <tr>
                <td>Status</td>
                <td class="status-success">Email system operational</td>
            </tr>
            <tr>
                <td>Test Time</td>
                <td>{{ timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') if timestamp else 'N/A' }}</td>
            </tr>
            {% endif %}
        </table>
    </div>
    
    <div class="section">
        <div class="alert alert-success">
            <h4>🎉 Success!</h4>
            <p>If you received this email, your notification system is configured correctly and working as expected.</p>
        </div>
    </div>
</div>
{% endblock %}'''
        }
        
        # Create template files
        for filename, content in templates_content.items():
            template_file = self.templates_directory / filename
            with open(template_file, 'w') as f:
                f.write(content)
        
        logger.info(f"Created {len(templates_content)} HTML template files")
    
    def register_template(self, template: EmailTemplate) -> bool:
        """Register a new email template."""
        try:
            # Update timestamp
            template.last_modified = datetime.now()
            
            # Add to registry
            self.templates[template.template_name] = template
            
            # Group by type
            if template.notification_type not in self.templates_by_type:
                self.templates_by_type[template.notification_type] = []
            
            # Remove existing template of same name from type group
            self.templates_by_type[template.notification_type] = [
                t for t in self.templates_by_type[template.notification_type]
                if t.template_name != template.template_name
            ]
            
            # Add new template
            self.templates_by_type[template.notification_type].append(template)
            
            # Save registry
            self._save_template_registry()
            
            logger.info(f"Registered template: {template.template_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register template {template.template_name}: {e}")
            return False
    
    def get_template(self, template_name: str) -> Optional[EmailTemplate]:
        """Get template by name."""
        return self.templates.get(template_name)
    
    def get_templates_by_type(self, notification_type: NotificationType) -> List[EmailTemplate]:
        """Get all templates for a specific notification type."""
        return self.templates_by_ty