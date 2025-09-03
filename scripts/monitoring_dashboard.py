#!/usr/bin/env python3
"""
Monitoring Dashboard for Code Quality Metrics
Provides a web-based dashboard for visualizing quality metrics and trends.
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import threading
import time

try:
    from flask import Flask, render_template_string, jsonify, request
    import plotly.graph_objs as go
    import plotly.utils
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask and Plotly not available. Install with: pip install flask plotly")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MonitoringDashboard:
    """Web-based monitoring dashboard for code quality metrics."""
    
    def __init__(self, project_root: Path, db_path: Optional[Path] = None):
        self.project_root = project_root
        self.db_path = db_path or project_root / "monitoring.db"
        self.app = Flask(__name__) if FLASK_AVAILABLE else None
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup Flask routes for the dashboard."""
        if not self.app:
            return
        
        @self.app.route('/')
        def dashboard():
            return render_template_string(self._get_dashboard_template())
        
        @self.app.route('/api/metrics')
        def api_metrics():
            days = request.args.get('days', 7, type=int)
            return jsonify(self.get_metrics_data(days))
        
        @self.app.route('/api/quality-gates')
        def api_quality_gates():
            days = request.args.get('days', 7, type=int)
            return jsonify(self.get_quality_gates_data(days))
        
        @self.app.route('/api/alerts')
        def api_alerts():
            return jsonify(self.get_active_alerts())
        
        @self.app.route('/api/trends')
        def api_trends():
            days = request.args.get('days', 30, type=int)
            return jsonify(self.get_trends_data(days))
    
    def get_metrics_data(self, days: int = 7) -> Dict[str, Any]:
        """Get quality metrics data for the specified number of days."""
        if not self.db_path.exists():
            return {"error": "No monitoring data available"}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT timestamp, total_issues, critical_issues, high_issues,
                           medium_issues, low_issues, ubuntu_issues, auto_fixable_issues,
                           test_coverage, build_success, deployment_success
                    FROM quality_metrics 
                    WHERE timestamp > datetime('now', '-{} days')
                    ORDER BY timestamp DESC
                """.format(days))
                
                rows = cursor.fetchall()
                
                if not rows:
                    return {"error": "No data available for the specified period"}
                
                # Get latest metrics
                latest = rows[0]
                
                # Prepare time series data
                timestamps = []
                total_issues = []
                critical_issues = []
                high_issues = []
                test_coverage = []
                ubuntu_issues = []
                
                for row in reversed(rows):  # Reverse to get chronological order
                    timestamps.append(row[0])
                    total_issues.append(row[1])
                    critical_issues.append(row[2])
                    high_issues.append(row[3])
                    test_coverage.append(row[8])
                    ubuntu_issues.append(row[6])
                
                return {
                    "latest_metrics": {
                        "timestamp": latest[0],
                        "total_issues": latest[1],
                        "critical_issues": latest[2],
                        "high_issues": latest[3],
                        "medium_issues": latest[4],
                        "low_issues": latest[5],
                        "ubuntu_issues": latest[6],
                        "auto_fixable_issues": latest[7],
                        "test_coverage": latest[8],
                        "build_success": latest[9],
                        "deployment_success": latest[10]
                    },
                    "time_series": {
                        "timestamps": timestamps,
                        "total_issues": total_issues,
                        "critical_issues": critical_issues,
                        "high_issues": high_issues,
                        "test_coverage": test_coverage,
                        "ubuntu_issues": ubuntu_issues
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get metrics data: {e}")
            return {"error": str(e)}
    
    def get_quality_gates_data(self, days: int = 7) -> Dict[str, Any]:
        """Get quality gates data for the specified number of days."""
        if not self.db_path.exists():
            return {"error": "No quality gates data available"}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get latest gate results
                cursor = conn.execute("""
                    SELECT gate_name, status, threshold_value, actual_value, passed, timestamp
                    FROM quality_gate_results 
                    WHERE timestamp > datetime('now', '-{} days')
                    ORDER BY timestamp DESC
                """.format(days))
                
                rows = cursor.fetchall()
                
                if not rows:
                    return {"error": "No quality gates data available"}
                
                # Group by gate name and get latest result for each
                latest_gates = {}
                for row in rows:
                    gate_name = row[0]
                    if gate_name not in latest_gates:
                        latest_gates[gate_name] = {
                            "name": gate_name,
                            "status": row[1],
                            "threshold": row[2],
                            "actual_value": row[3],
                            "passed": bool(row[4]),
                            "timestamp": row[5]
                        }
                
                # Get pass/fail trends
                cursor = conn.execute("""
                    SELECT gate_name, COUNT(*) as total, 
                           SUM(CASE WHEN passed THEN 1 ELSE 0 END) as passed_count
                    FROM quality_gate_results 
                    WHERE timestamp > datetime('now', '-{} days')
                    GROUP BY gate_name
                """.format(days))
                
                trends = {}
                for row in cursor.fetchall():
                    gate_name, total, passed_count = row
                    trends[gate_name] = {
                        "total_runs": total,
                        "passed_runs": passed_count,
                        "pass_rate": (passed_count / total * 100) if total > 0 else 0
                    }
                
                return {
                    "latest_gates": list(latest_gates.values()),
                    "trends": trends
                }
                
        except Exception as e:
            logger.error(f"Failed to get quality gates data: {e}")
            return {"error": str(e)}
    
    def get_active_alerts(self) -> Dict[str, Any]:
        """Get active monitoring alerts."""
        if not self.db_path.exists():
            return {"alerts": []}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, timestamp, severity, title, description, component,
                           ubuntu_specific, auto_fixable, resolved, resolution_notes
                    FROM monitoring_alerts 
                    WHERE resolved = FALSE
                    ORDER BY timestamp DESC
                    LIMIT 50
                """)
                
                alerts = []
                for row in cursor.fetchall():
                    alerts.append({
                        "id": row[0],
                        "timestamp": row[1],
                        "severity": row[2],
                        "title": row[3],
                        "description": row[4],
                        "component": row[5],
                        "ubuntu_specific": bool(row[6]),
                        "auto_fixable": bool(row[7]),
                        "resolved": bool(row[8]),
                        "resolution_notes": row[9]
                    })
                
                return {"alerts": alerts}
                
        except Exception as e:
            logger.error(f"Failed to get alerts data: {e}")
            return {"alerts": []}
    
    def get_trends_data(self, days: int = 30) -> Dict[str, Any]:
        """Get trend analysis data."""
        if not self.db_path.exists():
            return {"error": "No trends data available"}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get daily aggregated metrics
                cursor = conn.execute("""
                    SELECT DATE(timestamp) as date,
                           AVG(total_issues) as avg_total_issues,
                           AVG(critical_issues) as avg_critical_issues,
                           AVG(test_coverage) as avg_test_coverage,
                           AVG(ubuntu_issues) as avg_ubuntu_issues
                    FROM quality_metrics 
                    WHERE timestamp > datetime('now', '-{} days')
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """.format(days))
                
                trends = []
                for row in cursor.fetchall():
                    trends.append({
                        "date": row[0],
                        "avg_total_issues": row[1],
                        "avg_critical_issues": row[2],
                        "avg_test_coverage": row[3],
                        "avg_ubuntu_issues": row[4]
                    })
                
                return {"trends": trends}
                
        except Exception as e:
            logger.error(f"Failed to get trends data: {e}")
            return {"error": str(e)}
    
    def _get_dashboard_template(self) -> str:
        """Get the HTML template for the dashboard."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Quality Monitoring Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .metric-label {
            color: #666;
            font-size: 0.9em;
        }
        .critical { color: #dc3545; }
        .high { color: #fd7e14; }
        .medium { color: #ffc107; }
        .low { color: #28a745; }
        .ubuntu { color: #e95420; }
        .coverage { color: #007bff; }
        .charts-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .quality-gates {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .gate-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
        }
        .gate-passed {
            background-color: #d4edda;
            border-left: 4px solid #28a745;
        }
        .gate-failed {
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
        }
        .alerts-section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .alert-item {
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }
        .alert-critical { border-left-color: #dc3545; background-color: #f8d7da; }
        .alert-high { border-left-color: #fd7e14; background-color: #fff3cd; }
        .alert-medium { border-left-color: #ffc107; background-color: #fff3cd; }
        .alert-low { border-left-color: #28a745; background-color: #d4edda; }
        .refresh-btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-left: 10px;
        }
        .refresh-btn:hover {
            background: #0056b3;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Code Quality Monitoring Dashboard</h1>
            <p>Real-time monitoring of code quality metrics and Ubuntu compatibility</p>
            <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh</button>
            <span id="last-updated"></span>
        </div>
        
        <div id="metrics-section">
            <div class="loading">Loading metrics...</div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <h3>📊 Issues Trend</h3>
                <div id="issues-chart"></div>
            </div>
            <div class="chart-container">
                <h3>📈 Test Coverage Trend</h3>
                <div id="coverage-chart"></div>
            </div>
        </div>
        
        <div id="quality-gates-section">
            <div class="loading">Loading quality gates...</div>
        </div>
        
        <div id="alerts-section">
            <div class="loading">Loading alerts...</div>
        </div>
    </div>

    <script>
        let refreshInterval;
        
        function formatTimestamp(timestamp) {
            return new Date(timestamp).toLocaleString();
        }
        
        function createMetricsCards(data) {
            const metrics = data.latest_metrics;
            return `
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">${metrics.total_issues}</div>
                        <div class="metric-label">Total Issues</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value critical">${metrics.critical_issues}</div>
                        <div class="metric-label">Critical Issues</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value high">${metrics.high_issues}</div>
                        <div class="metric-label">High Issues</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value coverage">${metrics.test_coverage.toFixed(1)}%</div>
                        <div class="metric-label">Test Coverage</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value ubuntu">${metrics.ubuntu_issues}</div>
                        <div class="metric-label">Ubuntu Issues</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value low">${metrics.auto_fixable_issues}</div>
                        <div class="metric-label">Auto-fixable</div>
                    </div>
                </div>
            `;
        }
        
        function createIssuesChart(data) {
            const trace1 = {
                x: data.time_series.timestamps,
                y: data.time_series.total_issues,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Total Issues',
                line: { color: '#007bff' }
            };
            
            const trace2 = {
                x: data.time_series.timestamps,
                y: data.time_series.critical_issues,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Critical Issues',
                line: { color: '#dc3545' }
            };
            
            const trace3 = {
                x: data.time_series.timestamps,
                y: data.time_series.ubuntu_issues,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Ubuntu Issues',
                line: { color: '#e95420' }
            };
            
            const layout = {
                title: 'Issues Over Time',
                xaxis: { title: 'Time' },
                yaxis: { title: 'Number of Issues' },
                showlegend: true
            };
            
            Plotly.newPlot('issues-chart', [trace1, trace2, trace3], layout);
        }
        
        function createCoverageChart(data) {
            const trace = {
                x: data.time_series.timestamps,
                y: data.time_series.test_coverage,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Test Coverage',
                line: { color: '#28a745' }
            };
            
            const layout = {
                title: 'Test Coverage Over Time',
                xaxis: { title: 'Time' },
                yaxis: { title: 'Coverage %', range: [0, 100] },
                showlegend: false
            };
            
            Plotly.newPlot('coverage-chart', [trace], layout);
        }
        
        function createQualityGatesSection(data) {
            let html = '<div class="quality-gates"><h3>🚦 Quality Gates Status</h3>';
            
            data.latest_gates.forEach(gate => {
                const gateClass = gate.passed ? 'gate-passed' : 'gate-failed';
                const statusIcon = gate.passed ? '✅' : '❌';
                const gateName = gate.name.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase());
                
                html += `
                    <div class="gate-item ${gateClass}">
                        <div>
                            <strong>${statusIcon} ${gateName}</strong><br>
                            <small>Threshold: ${gate.threshold}, Actual: ${gate.actual_value}</small>
                        </div>
                        <div>${gate.status}</div>
                    </div>
                `;
            });
            
            html += '</div>';
            return html;
        }
        
        function createAlertsSection(data) {
            let html = '<div class="alerts-section"><h3>🚨 Active Alerts</h3>';
            
            if (data.alerts.length === 0) {
                html += '<p>No active alerts. All systems are running smoothly! 🎉</p>';
            } else {
                data.alerts.forEach(alert => {
                    const alertClass = `alert-${alert.severity}`;
                    const ubuntuFlag = alert.ubuntu_specific ? ' 🐧' : '';
                    const fixableFlag = alert.auto_fixable ? ' 🔧' : '';
                    
                    html += `
                        <div class="alert-item ${alertClass}">
                            <div>
                                <strong>${alert.title}${ubuntuFlag}${fixableFlag}</strong><br>
                                <small>${alert.description}</small><br>
                                <small>Component: ${alert.component} | ${formatTimestamp(alert.timestamp)}</small>
                            </div>
                        </div>
                    `;
                });
            }
            
            html += '</div>';
            return html;
        }
        
        async function loadMetrics() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                
                if (data.error) {
                    document.getElementById('metrics-section').innerHTML = `<div class="loading">Error: ${data.error}</div>`;
                    return;
                }
                
                document.getElementById('metrics-section').innerHTML = createMetricsCards(data);
                createIssuesChart(data);
                createCoverageChart(data);
                
            } catch (error) {
                document.getElementById('metrics-section').innerHTML = `<div class="loading">Error loading metrics: ${error.message}</div>`;
            }
        }
        
        async function loadQualityGates() {
            try {
                const response = await fetch('/api/quality-gates');
                const data = await response.json();
                
                if (data.error) {
                    document.getElementById('quality-gates-section').innerHTML = `<div class="loading">Error: ${data.error}</div>`;
                    return;
                }
                
                document.getElementById('quality-gates-section').innerHTML = createQualityGatesSection(data);
                
            } catch (error) {
                document.getElementById('quality-gates-section').innerHTML = `<div class="loading">Error loading quality gates: ${error.message}</div>`;
            }
        }
        
        async function loadAlerts() {
            try {
                const response = await fetch('/api/alerts');
                const data = await response.json();
                
                document.getElementById('alerts-section').innerHTML = createAlertsSection(data);
                
            } catch (error) {
                document.getElementById('alerts-section').innerHTML = `<div class="loading">Error loading alerts: ${error.message}</div>`;
            }
        }
        
        function refreshDashboard() {
            document.getElementById('last-updated').textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
            loadMetrics();
            loadQualityGates();
            loadAlerts();
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            refreshDashboard();
            
            // Auto-refresh every 30 seconds
            refreshInterval = setInterval(refreshDashboard, 30000);
        });
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', function() {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
        });
    </script>
</body>
</html>
        """
    
    def run(self, host: str = "localhost", port: int = 8080, debug: bool = False):
        """Run the monitoring dashboard server."""
        if not FLASK_AVAILABLE:
            logger.error("Flask is not available. Install with: pip install flask plotly")
            return
        
        if not self.app:
            logger.error("Flask app not initialized")
            return
        
        logger.info(f"Starting monitoring dashboard on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def main():
    """Main entry point for monitoring dashboard."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Code Quality Monitoring Dashboard")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root directory")
    parser.add_argument("--db-path", type=Path, help="Database file path")
    parser.add_argument("--host", default="localhost", help="Dashboard host")
    parser.add_argument("--port", type=int, default=8080, help="Dashboard port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Initialize and run dashboard
    dashboard = MonitoringDashboard(args.project_root, args.db_path)
    dashboard.run(args.host, args.port, args.debug)


if __name__ == "__main__":
    main()