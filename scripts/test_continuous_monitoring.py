#!/usr/bin/env python3
"""
Test Suite for Continuous Monitoring and Alerting System
Comprehensive tests for all monitoring components.
"""

import json
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from continuous_monitoring_system import (
    ContinuousMonitoringSystem, QualityGate, MonitoringAlert, QualityMetrics,
    AlertSeverity, MonitoringStatus
)
from cicd_quality_gates import CICDQualityGates, QualityGateResult
from maintenance_automation import MaintenanceAutomation


class TestContinuousMonitoringSystem(unittest.TestCase):
    """Test cases for the continuous monitoring system."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.monitoring = ContinuousMonitoringSystem(self.temp_dir)
        
        # Create test config file
        self.config_file = self.temp_dir / "monitoring-config.yml"
        with open(self.config_file, 'w') as f:
            f.write("""
monitoring:
  check_interval_minutes: 60
  enable_email_alerts: false
quality_gates:
  max_critical_issues: 0
  max_high_issues: 5
  max_total_issues: 50
  min_test_coverage: 80.0
""")
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_quality_gate_creation(self):
        """Test quality gate creation and configuration."""
        gates = self.monitoring._load_quality_gates()
        
        self.assertIsInstance(gates, list)
        self.assertTrue(len(gates) > 0)
        
        # Check that critical issues gate exists
        critical_gate = next((g for g in gates if g.name == "critical_issues"), None)
        self.assertIsNotNone(critical_gate)
        self.assertEqual(critical_gate.threshold_value, 0)
    
    def test_database_initialization(self):
        """Test database initialization."""
        self.assertTrue(self.monitoring.db_path.exists())
        
        with sqlite3.connect(self.monitoring.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ["quality_metrics", "monitoring_alerts", "quality_gate_results"]
            for table in expected_tables:
                self.assertIn(table, tables)
    
    @patch('subprocess.run')
    def test_quality_analysis_execution(self, mock_run):
        """Test quality analysis execution."""
        # Mock successful analysis
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Create mock analysis results file
        analysis_file = self.temp_dir / "monitoring_analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump({
                "total_issues_found": 10,
                "results": [
                    {
                        "issues": [
                            {
                                "severity": "high",
                                "ubuntu_specific": True,
                                "auto_fixable": False
                            },
                            {
                                "severity": "medium",
                                "ubuntu_specific": False,
                                "auto_fixable": True
                            }
                        ]
                    }
                ]
            }, f)
        
        # Create codebase analysis script
        analysis_script = self.temp_dir / "scripts" / "codebase-analysis.py"
        analysis_script.parent.mkdir(exist_ok=True)
        analysis_script.touch()
        
        metrics = self.monitoring.run_quality_analysis()
        
        self.assertIsInstance(metrics, QualityMetrics)
        self.assertEqual(metrics.total_issues, 10)
        self.assertEqual(metrics.high_issues, 1)
        self.assertEqual(metrics.ubuntu_issues, 1)
        self.assertEqual(metrics.auto_fixable_issues, 1)
    
    def test_quality_gate_evaluation(self):
        """Test quality gate evaluation."""
        metrics = QualityMetrics(
            timestamp=datetime.now(),
            total_issues=5,
            critical_issues=0,
            high_issues=2,
            medium_issues=2,
            low_issues=1,
            ubuntu_issues=1,
            auto_fixable_issues=2,
            test_coverage=85.0,
            build_success=True,
            deployment_success=True
        )
        
        gate_results = self.monitoring.evaluate_quality_gates(metrics)
        
        self.assertIsInstance(gate_results, list)
        self.assertTrue(len(gate_results) > 0)
        
        # Check critical issues gate (should pass)
        critical_result = next((r for r in gate_results if r[0].name == "critical_issues"), None)
        self.assertIsNotNone(critical_result)
        self.assertTrue(critical_result[1])  # Should pass
    
    def test_regression_detection(self):
        """Test regression detection functionality."""
        # Store some historical metrics
        historical_metrics = [
            QualityMetrics(
                timestamp=datetime.now() - timedelta(days=1),
                total_issues=5,
                critical_issues=0,
                high_issues=1,
                medium_issues=3,
                low_issues=1,
                ubuntu_issues=0,
                auto_fixable_issues=2,
                test_coverage=85.0,
                build_success=True,
                deployment_success=True
            ),
            QualityMetrics(
                timestamp=datetime.now() - timedelta(days=2),
                total_issues=3,
                critical_issues=0,
                high_issues=0,
                medium_issues=2,
                low_issues=1,
                ubuntu_issues=0,
                auto_fixable_issues=1,
                test_coverage=87.0,
                build_success=True,
                deployment_success=True
            )
        ]
        
        for metrics in historical_metrics:
            self.monitoring._store_metrics(metrics)
        
        # Current metrics with regression
        current_metrics = QualityMetrics(
            timestamp=datetime.now(),
            total_issues=15,  # Significant increase
            critical_issues=1,  # New critical issue
            high_issues=3,
            medium_issues=8,
            low_issues=3,
            ubuntu_issues=2,  # New Ubuntu issues
            auto_fixable_issues=5,
            test_coverage=75.0,  # Decreased coverage
            build_success=True,
            deployment_success=True
        )
        
        alerts = self.monitoring.detect_regressions(current_metrics)
        
        self.assertIsInstance(alerts, list)
        self.assertTrue(len(alerts) > 0)
        
        # Should detect critical issues regression
        critical_alert = next((a for a in alerts if "Critical" in a.title), None)
        self.assertIsNotNone(critical_alert)
    
    def test_alert_storage_and_retrieval(self):
        """Test alert storage and retrieval."""
        alert = MonitoringAlert(
            id="test_alert_001",
            timestamp=datetime.now(),
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="This is a test alert",
            component="test_component",
            ubuntu_specific=True,
            auto_fixable=False
        )
        
        self.monitoring._store_alert(alert)
        
        # Retrieve alerts
        with sqlite3.connect(self.monitoring.db_path) as conn:
            cursor = conn.execute("SELECT * FROM monitoring_alerts WHERE id = ?", (alert.id,))
            row = cursor.fetchone()
            
            self.assertIsNotNone(row)
            self.assertEqual(row[0], alert.id)
            self.assertEqual(row[2], alert.severity.value)
    
    @patch('smtplib.SMTP')
    def test_email_alert_sending(self, mock_smtp):
        """Test email alert sending functionality."""
        # Configure email alerts
        self.monitoring.config["monitoring"]["enable_email_alerts"] = True
        self.monitoring.config["alerts"]["email"]["recipients"] = ["test@example.com"]
        self.monitoring.config["alerts"]["email"]["username"] = "sender@example.com"
        self.monitoring.config["alerts"]["email"]["password"] = "password"
        
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        alerts = [
            MonitoringAlert(
                id="test_alert",
                timestamp=datetime.now(),
                severity=AlertSeverity.CRITICAL,
                title="Test Critical Alert",
                description="Critical issue detected",
                component="test",
                ubuntu_specific=False,
                auto_fixable=False
            )
        ]
        
        gate_failures = []
        
        self.monitoring.send_alerts(alerts, gate_failures)
        
        mock_smtp.assert_called_once()
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()
    
    def test_monitoring_cycle_execution(self):
        """Test complete monitoring cycle execution."""
        # Create necessary files and mocks
        analysis_script = self.temp_dir / "scripts" / "codebase-analysis.py"
        analysis_script.parent.mkdir(exist_ok=True)
        analysis_script.touch()
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps({
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "total_issues": 5,
                    "critical_issues": 0,
                    "high_issues": 1,
                    "medium_issues": 3,
                    "low_issues": 1,
                    "ubuntu_issues": 0,
                    "auto_fixable_issues": 2,
                    "test_coverage": 85.0,
                    "build_success": True,
                    "deployment_success": True
                }
            })
            mock_run.return_value = mock_result
            
            result = self.monitoring.run_monitoring_cycle()
            
            self.assertTrue(result["success"])
            self.assertIn("metrics", result)
            self.assertIn("quality_gates", result)


class TestCICDQualityGates(unittest.TestCase):
    """Test cases for CI/CD quality gates."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cicd_gates = CICDQualityGates(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_quality_gate_evaluation(self):
        """Test quality gate evaluation for CI/CD."""
        analysis_result = {
            "metrics": {
                "total_issues": 10,
                "critical_issues": 0,
                "high_issues": 3,
                "medium_issues": 5,
                "low_issues": 2,
                "ubuntu_issues": 1,
                "auto_fixable_issues": 4,
                "test_coverage": 85.0,
                "build_success": True,
                "deployment_success": True
            }
        }
        
        gate_results = self.cicd_gates.evaluate_quality_gates(analysis_result)
        
        self.assertIsInstance(gate_results, list)
        self.assertTrue(len(gate_results) > 0)
        
        # Check that all gates have proper structure
        for gate in gate_results:
            self.assertIsInstance(gate, QualityGateResult)
            self.assertIsInstance(gate.passed, bool)
            self.assertIsNotNone(gate.message)
    
    def test_report_generation(self):
        """Test CI/CD report generation."""
        analysis_result = {
            "metrics": {
                "total_issues": 5,
                "critical_issues": 0,
                "high_issues": 1,
                "medium_issues": 3,
                "low_issues": 1,
                "ubuntu_issues": 0,
                "auto_fixable_issues": 2,
                "test_coverage": 85.0,
                "build_success": True,
                "deployment_success": True
            }
        }
        
        gate_results = self.cicd_gates.evaluate_quality_gates(analysis_result)
        report = self.cicd_gates.create_cicd_report(analysis_result, gate_results)
        
        self.assertIsNotNone(report.timestamp)
        self.assertEqual(report.overall_status, "PASSED")
        self.assertIsInstance(report.recommendations, list)
    
    def test_json_report_generation(self):
        """Test JSON report generation."""
        analysis_result = {"metrics": {"total_issues": 0, "critical_issues": 0}}
        gate_results = []
        report = self.cicd_gates.create_cicd_report(analysis_result, gate_results)
        
        output_file = self.temp_dir / "test_report.json"
        self.cicd_gates.generate_json_report(report, output_file)
        
        self.assertTrue(output_file.exists())
        
        with open(output_file, 'r') as f:
            report_data = json.load(f)
            
        self.assertIn("timestamp", report_data)
        self.assertIn("overall_status", report_data)
    
    def test_html_report_generation(self):
        """Test HTML report generation."""
        analysis_result = {"metrics": {"total_issues": 5, "critical_issues": 1}}
        gate_results = []
        report = self.cicd_gates.create_cicd_report(analysis_result, gate_results)
        
        output_file = self.temp_dir / "test_report.html"
        self.cicd_gates.generate_html_report(report, output_file)
        
        self.assertTrue(output_file.exists())
        
        with open(output_file, 'r') as f:
            html_content = f.read()
            
        self.assertIn("<html", html_content)
        self.assertIn("Code Quality Report", html_content)


class TestMaintenanceAutomation(unittest.TestCase):
    """Test cases for maintenance automation."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.maintenance = MaintenanceAutomation(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_backup_creation(self):
        """Test backup creation functionality."""
        # Create some test files
        test_file = self.temp_dir / "test_file.py"
        test_file.write_text("print('Hello, World!')")
        
        success = self.maintenance.create_backup("test_backup")
        
        self.assertTrue(success)
        
        backup_dir = self.temp_dir / "backups"
        self.assertTrue(backup_dir.exists())
        
        backup_files = list(backup_dir.glob("test_backup.tar.gz"))
        self.assertEqual(len(backup_files), 1)
    
    def test_backup_cleanup(self):
        """Test old backup cleanup."""
        backup_dir = self.temp_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        # Create old backup files
        old_backup = backup_dir / "old_backup.tar.gz"
        old_backup.touch()
        
        # Set modification time to 10 days ago
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(old_backup, (old_time, old_time))
        
        # Create recent backup
        recent_backup = backup_dir / "recent_backup.tar.gz"
        recent_backup.touch()
        
        removed_count = self.maintenance.cleanup_old_backups()
        
        self.assertEqual(removed_count, 1)
        self.assertFalse(old_backup.exists())
        self.assertTrue(recent_backup.exists())
    
    @patch('subprocess.run')
    def test_code_formatting(self, mock_run):
        """Test code formatting functionality."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Create backend directory
        backend_dir = self.temp_dir / "backend"
        backend_dir.mkdir()
        
        # Create package.json
        package_json = self.temp_dir / "package.json"
        package_json.write_text('{"scripts": {"format": "prettier --write ."}}')
        
        results = self.maintenance.auto_format_code()
        
        self.assertTrue(results["python_formatted"])
        self.assertTrue(results["javascript_formatted"])
        self.assertEqual(len(results["errors"]), 0)
    
    def test_temporary_file_cleanup(self):
        """Test temporary file cleanup."""
        # Create temporary files and directories
        temp_files = [
            self.temp_dir / "test.pyc",
            self.temp_dir / "__pycache__" / "module.pyc",
            self.temp_dir / "test.tmp"
        ]
        
        for temp_file in temp_files:
            temp_file.parent.mkdir(exist_ok=True)
            temp_file.write_text("temporary content")
        
        results = self.maintenance.cleanup_temporary_files()
        
        self.assertGreater(results["files_removed"], 0)
        self.assertGreater(results["space_freed_mb"], 0)
        
        # Check that files were actually removed
        for temp_file in temp_files:
            if temp_file.exists():
                self.assertFalse(temp_file.exists())
    
    def test_maintenance_logging(self):
        """Test maintenance activity logging."""
        # Initialize database
        self.maintenance.db_path = self.temp_dir / "test_monitoring.db"
        
        results = {"success": True, "files_processed": 5}
        self.maintenance.log_maintenance_activity("test_activity", results)
        
        # Check that log was created
        with sqlite3.connect(self.maintenance.db_path) as conn:
            cursor = conn.execute("SELECT * FROM maintenance_log WHERE activity_type = ?", ("test_activity",))
            row = cursor.fetchone()
            
            self.assertIsNotNone(row)
            self.assertEqual(row[2], "test_activity")  # activity_type column


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete monitoring system."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create project structure
        self.scripts_dir = self.temp_dir / "scripts"
        self.scripts_dir.mkdir()
        
        # Create mock analysis script
        analysis_script = self.scripts_dir / "codebase-analysis.py"
        analysis_script.write_text("""
import json
import sys
result = {
    "total_issues_found": 5,
    "results": [{"issues": [{"severity": "medium", "ubuntu_specific": False, "auto_fixable": True}]}]
}
print(json.dumps(result))
""")
        
        # Create mock fix engine
        fix_script = self.scripts_dir / "automated_fix_engine.py"
        fix_script.write_text("""
print("3 fixes applied, 3 fixes attempted")
""")
    
    def tearDown(self):
        """Clean up integration test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_end_to_end_monitoring_cycle(self):
        """Test complete end-to-end monitoring cycle."""
        monitoring = ContinuousMonitoringSystem(self.temp_dir)
        
        # Run monitoring cycle
        result = monitoring.run_monitoring_cycle()
        
        self.assertTrue(result["success"])
        self.assertIn("metrics", result)
        self.assertIn("quality_gates", result)
        
        # Check that database was updated
        with sqlite3.connect(monitoring.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM quality_metrics")
            count = cursor.fetchone()[0]
            self.assertGreater(count, 0)
    
    def test_cicd_integration_workflow(self):
        """Test CI/CD integration workflow."""
        # Create monitoring system
        monitoring_script = self.scripts_dir / "continuous_monitoring_system.py"
        monitoring_script.write_text("""
import json
import sys
result = {
    "success": True,
    "metrics": {
        "total_issues": 3,
        "critical_issues": 0,
        "high_issues": 1,
        "medium_issues": 2,
        "low_issues": 0,
        "ubuntu_issues": 0,
        "auto_fixable_issues": 1,
        "test_coverage": 85.0,
        "build_success": True,
        "deployment_success": True
    }
}
print(json.dumps(result))
""")
        
        cicd_gates = CICDQualityGates(self.temp_dir)
        
        # Run quality check
        with patch.dict(os.environ, {"CI_PIPELINE_ID": "123", "CI_COMMIT_SHA": "abc123"}):
            exit_code = cicd_gates.run_cicd_quality_check()
        
        self.assertEqual(exit_code, 0)  # Should pass
        
        # Check that reports were generated
        reports_dir = self.temp_dir / "quality-reports"
        self.assertTrue(reports_dir.exists())
    
    def test_maintenance_integration(self):
        """Test maintenance automation integration."""
        maintenance = MaintenanceAutomation(self.temp_dir)
        
        # Create some files to maintain
        test_file = self.temp_dir / "test.py"
        test_file.write_text("print( 'hello' )")  # Poorly formatted
        
        # Run daily maintenance
        results = maintenance.run_daily_maintenance()
        
        self.assertIn("tasks", results)
        self.assertIn("cleanup", results["tasks"])


def run_comprehensive_tests():
    """Run all test suites."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestContinuousMonitoringSystem,
        TestCICDQualityGates,
        TestMaintenanceAutomation,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)