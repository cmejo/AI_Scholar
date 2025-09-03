# Continuous Monitoring and Alerting System

A comprehensive system for continuous code quality monitoring, quality gate enforcement, regression detection, Ubuntu compatibility monitoring, and automated maintenance procedures.

## Overview

The Continuous Monitoring and Alerting System provides:

- **Quality Gate Enforcement**: Automated quality standards enforcement for CI/CD pipelines
- **Regression Detection**: Identifies quality regressions by comparing historical metrics
- **Ubuntu Compatibility Monitoring**: Specialized monitoring for Ubuntu server compatibility
- **Automated Maintenance**: Routine maintenance tasks and code quality improvements
- **Real-time Dashboard**: Web-based monitoring dashboard with visualizations
- **Multi-channel Alerts**: Email, Slack, and webhook notifications

## Components

### 1. Continuous Monitoring System (`continuous_monitoring_system.py`)

The core monitoring engine that orchestrates quality analysis, evaluates quality gates, detects regressions, and manages alerts.

**Key Features:**
- Comprehensive quality analysis integration
- Configurable quality gates with thresholds
- Historical trend analysis and regression detection
- Multi-channel alert system (email, Slack, webhooks)
- Automated maintenance procedure execution
- SQLite database for metrics storage

**Usage:**
```bash
# Run single monitoring cycle
python scripts/continuous_monitoring_system.py

# Run as daemon with scheduled checks
python scripts/continuous_monitoring_system.py --daemon --interval 60

# Generate monitoring report
python scripts/continuous_monitoring_system.py --report
```

### 2. CI/CD Quality Gates (`cicd_quality_gates.py`)

Integrates with CI/CD pipelines to enforce quality standards and generate reports.

**Key Features:**
- Quality gate evaluation for CI/CD pipelines
- Multiple report formats (JSON, HTML, JUnit XML)
- Configurable failure thresholds
- Actionable recommendations generation
- CI/CD environment integration

**Usage:**
```bash
# Run quality check for CI/CD
python scripts/cicd_quality_gates.py

# Generate reports in specific directory
python scripts/cicd_quality_gates.py --output-dir ./reports

# Fail pipeline on quality gate failures
python scripts/cicd_quality_gates.py --fail-on-gate-failure
```

### 3. Monitoring Dashboard (`monitoring_dashboard.py`)

Web-based dashboard for visualizing quality metrics and monitoring system status.

**Key Features:**
- Real-time quality metrics visualization
- Interactive charts and graphs
- Quality gate status monitoring
- Active alerts display
- Historical trend analysis
- Auto-refresh functionality

**Usage:**
```bash
# Start dashboard server
python scripts/monitoring_dashboard.py --host 0.0.0.0 --port 8080

# Start with custom database
python scripts/monitoring_dashboard.py --db-path ./custom_monitoring.db
```

### 4. Maintenance Automation (`maintenance_automation.py`)

Automated maintenance system for routine code quality management tasks.

**Key Features:**
- Scheduled maintenance tasks
- Automated code formatting
- Auto-fix application for common issues
- Dependency updates with safety checks
- Backup creation and management
- Temporary file cleanup

**Usage:**
```bash
# Run daily maintenance
python scripts/maintenance_automation.py --daily

# Run as scheduled daemon
python scripts/maintenance_automation.py --daemon

# Run specific maintenance tasks
python scripts/maintenance_automation.py --format
python scripts/maintenance_automation.py --cleanup
python scripts/maintenance_automation.py --backup
```

## Configuration

The system uses a YAML configuration file (`monitoring-config.yml`) for customization:

```yaml
monitoring:
  check_interval_minutes: 60
  enable_email_alerts: false
  enable_slack_alerts: false

quality_gates:
  max_critical_issues: 0
  max_high_issues: 5
  max_total_issues: 50
  min_test_coverage: 80.0
  max_ubuntu_compatibility_issues: 2

alerts:
  email:
    smtp_server: "localhost"
    recipients: ["admin@example.com"]
  slack:
    webhook_url: "https://hooks.slack.com/..."
    channel: "#code-quality"

maintenance:
  auto_fix_enabled: true
  auto_format_code: true
  backup_before_fixes: true
```

## Quality Gates

The system enforces the following quality gates:

### Critical Quality Gates (Blocking)
- **Critical Issues**: No critical issues allowed (threshold: 0)
- **High Issues**: Limited high severity issues (threshold: 5)
- **Test Coverage**: Minimum test coverage required (threshold: 80%)
- **Ubuntu Compatibility**: Maximum Ubuntu-specific issues (threshold: 2)
- **Build Success**: Build must succeed
- **Deployment Success**: Deployment validation must pass

### Non-blocking Quality Gates
- **Total Issues**: Overall issue count threshold (threshold: 50)

## Regression Detection

The system automatically detects quality regressions by comparing current metrics with historical data:

- **Critical Issues Increase**: Any increase in critical issues
- **Total Issues Spike**: 20% or more increase in total issues
- **Coverage Decrease**: 5% or more decrease in test coverage
- **Ubuntu Issues**: Any increase in Ubuntu compatibility issues

## Alert System

### Alert Channels

1. **Email Alerts**
   - SMTP configuration required
   - Supports multiple recipients
   - Rich HTML formatting

2. **Slack Alerts**
   - Webhook integration
   - Customizable channel and formatting
   - Real-time notifications

3. **Webhook Alerts**
   - Generic webhook support
   - JSON payload with full alert data
   - Custom headers support

### Alert Severity Levels

- **CRITICAL**: System-breaking issues requiring immediate attention
- **HIGH**: Significant issues that should be addressed quickly
- **MEDIUM**: Moderate issues that should be fixed
- **LOW**: Minor issues or improvements
- **INFO**: Informational messages

## Maintenance Automation

### Scheduled Tasks

- **Daily Maintenance** (02:00): Code formatting, auto-fixes, cleanup
- **Weekly Deep Clean** (Sunday 03:00): Full maintenance + dependency updates
- **Dependency Check** (Monday 04:00): Security and dependency updates

### Maintenance Operations

1. **Code Formatting**
   - Python: Black formatter
   - JavaScript/TypeScript: Prettier

2. **Auto-fixes**
   - Applies fixes for auto-fixable issues
   - Configurable maximum fixes per cycle

3. **Cleanup**
   - Removes temporary files and caches
   - Cleans up build artifacts

4. **Backup Management**
   - Creates compressed backups before changes
   - Automatic cleanup of old backups

## Database Schema

The system uses SQLite for data storage with the following tables:

### quality_metrics
Stores historical quality metrics for trend analysis.

### monitoring_alerts
Tracks all monitoring alerts and their resolution status.

### quality_gate_results
Records quality gate evaluation results over time.

### maintenance_log
Logs all maintenance activities and their results.

## Usage

### Basic Usage

1. **Initialize the monitoring system:**
```bash
# Create configuration file
cp monitoring-config.yml.example monitoring-config.yml
# Edit configuration as needed

# Run initial setup
python scripts/continuous_monitoring_system.py --setup
```

2. **Run quality analysis:**
```bash
# Single analysis run
python scripts/continuous_monitoring_system.py

# Continuous monitoring
python scripts/continuous_monitoring_system.py --daemon
```

3. **Start monitoring dashboard:**
```bash
python scripts/monitoring_dashboard.py --host 0.0.0.0 --port 8080
```

4. **Run maintenance tasks:**
```bash
# Daily maintenance
python scripts/maintenance_automation.py --daily

# Automated scheduling
python scripts/maintenance_automation.py --daemon
```

### Command Line Options

#### Continuous Monitoring System
- `--daemon`: Run as background daemon
- `--interval N`: Check interval in minutes (default: 60)
- `--report`: Generate monitoring report only
- `--config FILE`: Custom configuration file

#### CI/CD Quality Gates
- `--output-dir DIR`: Output directory for reports
- `--fail-on-gate-failure`: Exit with error code on failures
- `--config FILE`: Custom configuration file

#### Monitoring Dashboard
- `--host HOST`: Dashboard host (default: localhost)
- `--port PORT`: Dashboard port (default: 8080)
- `--debug`: Enable debug mode

#### Maintenance Automation
- `--daily`: Run daily maintenance tasks
- `--weekly`: Run weekly maintenance tasks
- `--daemon`: Run scheduled maintenance daemon
- `--backup`: Create backup only
- `--format`: Format code only
- `--fix`: Apply auto-fixes only
- `--cleanup`: Clean temporary files only

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Quality Gates
on: [push, pull_request]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run Quality Gates
        run: python scripts/cicd_quality_gates.py --fail-on-gate-failure
      - name: Upload Reports
        uses: actions/upload-artifact@v2
        with:
          name: quality-reports
          path: quality-reports/
```

### GitLab CI Example

```yaml
quality_gates:
  stage: test
  script:
    - python scripts/cicd_quality_gates.py --fail-on-gate-failure
  artifacts:
    reports:
      junit: quality-reports/quality-report.xml
    paths:
      - quality-reports/
  only:
    - merge_requests
    - main
```

## Monitoring Dashboard

The web dashboard provides:

- **Real-time Metrics**: Current quality status and trends
- **Quality Gates Status**: Visual status of all quality gates
- **Active Alerts**: List of unresolved alerts
- **Historical Charts**: Trend analysis with interactive graphs
- **Auto-refresh**: Automatic updates every 30 seconds

Access the dashboard at `http://localhost:8080` after starting the server.

## Ubuntu Compatibility Features

Special monitoring for Ubuntu server environments:

- **Package Compatibility**: Monitors Ubuntu package dependencies
- **Docker Integration**: Ubuntu-specific Docker configuration validation
- **Shell Script Compatibility**: Bash script Ubuntu compatibility checks
- **File System Permissions**: Ubuntu permission and access validation
- **Network Configuration**: Ubuntu networking setup validation

## Testing

Run the comprehensive test suite:

```bash
python scripts/test_continuous_monitoring.py
```

The test suite includes:
- Unit tests for all components
- Integration tests for complete workflows
- Mock testing for external dependencies
- End-to-end testing scenarios

## Troubleshooting

### Common Issues

1. **Database Lock Errors**
   - Ensure only one monitoring process is running
   - Check file permissions on the database file

2. **Analysis Script Not Found**
   - Verify `scripts/codebase-analysis.py` exists
   - Check file permissions and execution rights

3. **Alert Delivery Failures**
   - Verify SMTP/Slack/webhook configurations
   - Check network connectivity and firewall settings

4. **Dashboard Not Loading**
   - Install Flask and Plotly: `pip install flask plotly`
   - Check port availability and firewall settings

### Logging

All components log to both console and log files:
- `monitoring.log`: Main monitoring system logs
- `maintenance.log`: Maintenance automation logs

Set log level in configuration:
```yaml
logging:
  level: "DEBUG"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## Performance Considerations

- **Database Size**: Regular cleanup of old metrics (configurable retention)
- **Analysis Frequency**: Balance between freshness and resource usage
- **Alert Throttling**: Prevents alert spam with intelligent grouping
- **Resource Monitoring**: Built-in performance tracking and optimization

## Security

- **Database Security**: SQLite file permissions and access control
- **Alert Security**: Secure credential storage for SMTP/webhooks
- **Backup Security**: Encrypted backup storage options
- **Network Security**: HTTPS support for dashboard and webhooks

## Extending the System

### Adding Custom Quality Gates

```python
def custom_gate_evaluator(metrics: QualityMetrics) -> bool:
    # Custom logic here
    return metrics.custom_metric <= threshold

# Register in quality gates configuration
```

### Custom Alert Channels

```python
def custom_alert_sender(message: str, alerts: List[MonitoringAlert]):
    # Custom alert delivery logic
    pass

# Add to alert system configuration
```

### Custom Maintenance Tasks

```python
def custom_maintenance_task() -> Dict[str, Any]:
    # Custom maintenance logic
    return {"success": True, "details": "Task completed"}

# Schedule in maintenance automation
```

## Support and Contributing

For issues, feature requests, or contributions:

1. Check existing issues and documentation
2. Create detailed bug reports with logs
3. Submit feature requests with use cases
4. Follow coding standards for contributions

## License

This monitoring system is part of the AI Scholar project and follows the same licensing terms.