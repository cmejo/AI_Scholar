#!/usr/bin/env python3
"""
Demo Script for Continuous Monitoring and Alerting System
Demonstrates all features of the monitoring system with sample data.
"""

import json
import logging
import sqlite3
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
import sys

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from continuous_monitoring_system import (
    ContinuousMonitoringSystem, QualityMetrics, MonitoringAlert, AlertSeverity
)
from cicd_quality_gates import CICDQualityGates
from maintenance_automation import MaintenanceAutomation

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MonitoringSystemDemo:
    """Demonstration of the continuous monitoring system."""
    
    def __init__(self, demo_dir: Path):
        self.demo_dir = demo_dir
        self.demo_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.monitoring = ContinuousMonitoringSystem(demo_dir)
        self.cicd_gates = CICDQualityGates(demo_dir)
        self.maintenance = MaintenanceAutomation(demo_dir)
        
        # Create demo project structure
        self._setup_demo_project()
    
    def _setup_demo_project(self):
        """Set up demo project structure and files."""
        logger.info("Setting up demo project structure...")
        
        # Create project directories
        (self.demo_dir / "backend").mkdir(exist_ok=True)
        (self.demo_dir / "frontend").mkdir(exist_ok=True)
        (self.demo_dir / "scripts").mkdir(exist_ok=True)
        
        # Create demo Python files
        backend_file = self.demo_dir / "backend" / "app.py"
        backend_file.write_text("""
# Demo Python application
import os
import sys
from typing import List, Dict

def process_data(data: List[Dict]) -> Dict:
    '''Process incoming data and return results.'''
    results = {}
    for item in data:
        if 'id' in item:
            results[item['id']] = item.get('value', 0)
    return results

def main():
    print("Demo application running")
    sample_data = [
        {'id': 1, 'value': 100},
        {'id': 2, 'value': 200}
    ]
    results = process_data(sample_data)
    print(f"Results: {results}")

if __name__ == "__main__":
    main()
""")
        
        # Create demo TypeScript file
        frontend_file = self.demo_dir / "frontend" / "app.ts"
        frontend_file.write_text("""
// Demo TypeScript application
interface DataItem {
    id: number;
    value: number;
    name?: string;
}

class DataProcessor {
    private data: DataItem[] = [];
    
    addItem(item: DataItem): void {
        this.data.push(item);
    }
    
    processData(): Record<number, number> {
        const results: Record<number, number> = {};
        this.data.forEach(item => {
            results[item.id] = item.value;
        });
        return results;
    }
}

const processor = new DataProcessor();
processor.addItem({ id: 1, value: 100 });
processor.addItem({ id: 2, value: 200 });
console.log(processor.processData());
""")
        
        # Create package.json
        package_json = self.demo_dir / "package.json"
        package_json.write_text(json.dumps({
            "name": "monitoring-demo",
            "version": "1.0.0",
            "scripts": {
                "build": "tsc",
                "test": "jest",
                "lint": "eslint .",
                "format": "prettier --write .",
                "format:check": "prettier --check ."
            },
            "devDependencies": {
                "typescript": "^4.9.0",
                "jest": "^29.0.0",
                "eslint": "^8.0.0",
                "prettier": "^2.8.0"
            }
        }, indent=2))
        
        # Create mock analysis script
        analysis_script = self.demo_dir / "scripts" / "codebase-analysis.py"
        analysis_script.write_text("""
#!/usr/bin/env python3
import json
import sys
import random
from datetime import datetime

# Simulate analysis results with some variability
base_issues = 10
critical_issues = random.randint(0, 2)
high_issues = random.randint(1, 5)
medium_issues = random.randint(3, 8)
low_issues = base_issues - critical_issues - high_issues - medium_issues
ubuntu_issues = random.randint(0, 3)
auto_fixable = random.randint(2, 6)

results = {
    "analysis_timestamp": datetime.now().isoformat(),
    "total_tools_run": 8,
    "successful_tools": 8,
    "failed_tools": 0,
    "total_issues_found": base_issues,
    "results": [
        {
            "tool_name": "flake8",
            "success": True,
            "issues": [
                {
                    "severity": "medium",
                    "ubuntu_specific": False,
                    "auto_fixable": True
                } for _ in range(medium_issues)
            ] + [
                {
                    "severity": "high",
                    "ubuntu_specific": False,
                    "auto_fixable": False
                } for _ in range(high_issues)
            ] + [
                {
                    "severity": "critical",
                    "ubuntu_specific": True,
                    "auto_fixable": False
                } for _ in range(critical_issues)
            ] + [
                {
                    "severity": "low",
                    "ubuntu_specific": random.choice([True, False]),
                    "auto_fixable": True
                } for _ in range(low_issues)
            ]
        }
    ]
}

print(json.dumps(results))
""")
        analysis_script.chmod(0o755)
        
        # Create mock fix engine
        fix_script = self.demo_dir / "scripts" / "automated_fix_engine.py"
        fix_script.write_text("""
#!/usr/bin/env python3
import random
import sys

fixes_applied = random.randint(1, 5)
fixes_attempted = fixes_applied + random.randint(0, 2)

print(f"{fixes_applied} fixes applied, {fixes_attempted} fixes attempted")
""")
        fix_script.chmod(0o755)
        
        logger.info("Demo project structure created successfully")
    
    def demonstrate_quality_analysis(self) -> Dict[str, Any]:
        """Demonstrate quality analysis functionality."""
        logger.info("🔍 Demonstrating Quality Analysis...")
        
        try:
            metrics = self.monitoring.run_quality_analysis()
            
            print(f"\n📊 Quality Metrics:")
            print(f"  Total Issues: {metrics.total_issues}")
            print(f"  Critical Issues: {metrics.critical_issues}")
            print(f"  High Issues: {metrics.high_issues}")
            print(f"  Medium Issues: {metrics.medium_issues}")
            print(f"  Low Issues: {metrics.low_issues}")
            print(f"  Ubuntu Issues: {metrics.ubuntu_issues}")
            print(f"  Auto-fixable Issues: {metrics.auto_fixable_issues}")
            print(f"  Test Coverage: {metrics.test_coverage:.1f}%")
            print(f"  Build Success: {metrics.build_success}")
            print(f"  Deployment Success: {metrics.deployment_success}")
            
            return {"success": True, "metrics": metrics}
            
        except Exception as e:
            logger.error(f"Quality analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    def demonstrate_quality_gates(self, metrics: QualityMetrics) -> Dict[str, Any]:
        """Demonstrate quality gate evaluation."""
        logger.info("🚦 Demonstrating Quality Gates...")
        
        gate_results = self.monitoring.evaluate_quality_gates(metrics)
        
        print(f"\n🚦 Quality Gate Results:")
        for gate, passed, message in gate_results:
            status_icon = "✅" if passed else "❌"
            blocking_text = " (Blocking)" if gate.name in ["critical_issues", "high_issues", "test_coverage"] else ""
            print(f"  {status_icon} {gate.name.replace('_', ' ').title()}{blocking_text}: {message}")
        
        passed_gates = sum(1 for _, passed, _ in gate_results if passed)
        total_gates = len(gate_results)
        
        return {
            "total_gates": total_gates,
            "passed_gates": passed_gates,
            "overall_status": "PASSED" if passed_gates == total_gates else "FAILED"
        }
    
    def demonstrate_regression_detection(self) -> Dict[str, Any]:
        """Demonstrate regression detection with historical data."""
        logger.info("📈 Demonstrating Regression Detection...")
        
        # Create historical metrics
        historical_metrics = [
            QualityMetrics(
                timestamp=datetime.now() - timedelta(days=3),
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
                total_issues=7,
                critical_issues=0,
                high_issues=2,
                medium_issues=4,
                low_issues=1,
                ubuntu_issues=1,
                auto_fixable_issues=3,
                test_coverage=83.0,
                build_success=True,
                deployment_success=True
            ),
            QualityMetrics(
                timestamp=datetime.now() - timedelta(days=1),
                total_issues=6,
                critical_issues=0,
                high_issues=1,
                medium_issues=4,
                low_issues=1,
                ubuntu_issues=0,
                auto_fixable_issues=2,
                test_coverage=84.0,
                build_success=True,
                deployment_success=True
            )
        ]
        
        # Store historical data
        for metrics in historical_metrics:
            self.monitoring._store_metrics(metrics)
        
        # Create current metrics with regression
        current_metrics = QualityMetrics(
            timestamp=datetime.now(),
            total_issues=15,  # Significant increase
            critical_issues=2,  # New critical issues
            high_issues=4,
            medium_issues=7,
            low_issues=2,
            ubuntu_issues=3,  # New Ubuntu issues
            auto_fixable_issues=5,
            test_coverage=75.0,  # Decreased coverage
            build_success=True,
            deployment_success=True
        )
        
        # Detect regressions
        alerts = self.monitoring.detect_regressions(current_metrics)
        
        print(f"\n📈 Regression Detection Results:")
        if alerts:
            for alert in alerts:
                severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(alert.severity.value, "ℹ️")
                ubuntu_flag = " 🐧" if alert.ubuntu_specific else ""
                fix_flag = " 🔧" if alert.auto_fixable else ""
                print(f"  {severity_icon} {alert.title}{ubuntu_flag}{fix_flag}")
                print(f"     {alert.description}")
        else:
            print("  ✅ No regressions detected")
        
        return {
            "alerts_generated": len(alerts),
            "regression_detected": len(alerts) > 0,
            "alerts": [{"title": a.title, "severity": a.severity.value} for a in alerts]
        }
    
    def demonstrate_cicd_integration(self) -> Dict[str, Any]:
        """Demonstrate CI/CD integration."""
        logger.info("🔄 Demonstrating CI/CD Integration...")
        
        # Create monitoring system mock
        monitoring_script = self.demo_dir / "scripts" / "continuous_monitoring_system.py"
        monitoring_script.write_text(f"""
import json
import sys
result = {{
    "success": True,
    "metrics": {{
        "total_issues": 8,
        "critical_issues": 1,
        "high_issues": 2,
        "medium_issues": 4,
        "low_issues": 1,
        "ubuntu_issues": 1,
        "auto_fixable_issues": 3,
        "test_coverage": 82.0,
        "build_success": True,
        "deployment_success": True
    }}
}}
print(json.dumps(result))
""")
        
        # Run CI/CD quality check
        reports_dir = self.demo_dir / "quality-reports"
        exit_code = self.cicd_gates.run_cicd_quality_check(reports_dir)
        
        print(f"\n🔄 CI/CD Integration Results:")
        print(f"  Exit Code: {exit_code}")
        print(f"  Status: {'PASSED' if exit_code == 0 else 'FAILED'}")
        
        # Check generated reports
        report_files = list(reports_dir.glob("*")) if reports_dir.exists() else []
        print(f"  Reports Generated: {len(report_files)}")
        for report_file in report_files:
            print(f"    - {report_file.name}")
        
        return {
            "exit_code": exit_code,
            "status": "PASSED" if exit_code == 0 else "FAILED",
            "reports_generated": len(report_files)
        }
    
    def demonstrate_maintenance_automation(self) -> Dict[str, Any]:
        """Demonstrate maintenance automation."""
        logger.info("🔧 Demonstrating Maintenance Automation...")
        
        # Create some files that need maintenance
        messy_file = self.demo_dir / "messy_code.py"
        messy_file.write_text("""
# Poorly formatted Python code
def   bad_function(  x,y  ):
    if x>y:
        return x+y
    else:
        return x-y

class   BadClass:
    def __init__(self,value):
        self.value=value
    def get_value(self):
        return self.value
""")
        
        # Create temporary files
        temp_files = [
            self.demo_dir / "temp.pyc",
            self.demo_dir / "__pycache__" / "module.pyc",
            self.demo_dir / "test.tmp"
        ]
        
        for temp_file in temp_files:
            temp_file.parent.mkdir(exist_ok=True)
            temp_file.write_text("temporary content")
        
        # Run maintenance tasks
        print(f"\n🔧 Maintenance Automation Results:")
        
        # 1. Create backup
        backup_success = self.maintenance.create_backup("demo_backup")
        print(f"  📦 Backup Creation: {'✅ Success' if backup_success else '❌ Failed'}")
        
        # 2. Cleanup temporary files
        cleanup_results = self.maintenance.cleanup_temporary_files()
        print(f"  🧹 Cleanup: {cleanup_results['files_removed']} files removed, {cleanup_results['space_freed_mb']} MB freed")
        
        # 3. Apply auto-fixes (simulated)
        fix_results = self.maintenance.apply_auto_fixes()
        print(f"  🔧 Auto-fixes: {fix_results['fixes_applied']} applied, {fix_results['fixes_attempted']} attempted")
        
        # 4. Cleanup old backups
        cleanup_count = self.maintenance.cleanup_old_backups()
        print(f"  🗑️ Backup Cleanup: {cleanup_count} old backups removed")
        
        return {
            "backup_created": backup_success,
            "files_cleaned": cleanup_results['files_removed'],
            "fixes_applied": fix_results['fixes_applied'],
            "old_backups_removed": cleanup_count
        }
    
    def demonstrate_monitoring_cycle(self) -> Dict[str, Any]:
        """Demonstrate complete monitoring cycle."""
        logger.info("🔄 Demonstrating Complete Monitoring Cycle...")
        
        try:
            result = self.monitoring.run_monitoring_cycle()
            
            print(f"\n🔄 Complete Monitoring Cycle Results:")
            print(f"  Success: {'✅' if result['success'] else '❌'}")
            print(f"  Timestamp: {result['timestamp']}")
            
            if result['success']:
                metrics = result['metrics']
                print(f"  Total Issues: {metrics['total_issues']}")
                print(f"  Critical Issues: {metrics['critical_issues']}")
                
                quality_gates = result['quality_gates']
                passed_gates = sum(1 for gate in quality_gates if gate['passed'])
                print(f"  Quality Gates: {passed_gates}/{len(quality_gates)} passed")
                
                alerts = result.get('regression_alerts', [])
                print(f"  Regression Alerts: {len(alerts)}")
                
                maintenance = result.get('maintenance_results', {})
                print(f"  Maintenance Tasks: {len(maintenance)} completed")
            
            return result
            
        except Exception as e:
            logger.error(f"Monitoring cycle failed: {e}")
            return {"success": False, "error": str(e)}
    
    def demonstrate_database_operations(self) -> Dict[str, Any]:
        """Demonstrate database operations and data persistence."""
        logger.info("💾 Demonstrating Database Operations...")
        
        db_path = self.monitoring.db_path
        
        print(f"\n💾 Database Operations:")
        print(f"  Database Path: {db_path}")
        print(f"  Database Exists: {'✅' if db_path.exists() else '❌'}")
        
        if db_path.exists():
            with sqlite3.connect(db_path) as conn:
                # Check tables
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                print(f"  Tables: {', '.join(tables)}")
                
                # Count records
                record_counts = {}
                for table in tables:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    record_counts[table] = count
                    print(f"    {table}: {count} records")
                
                return {
                    "database_exists": True,
                    "tables": tables,
                    "record_counts": record_counts
                }
        
        return {"database_exists": False}
    
    def run_complete_demo(self) -> Dict[str, Any]:
        """Run complete demonstration of all features."""
        print("🚀 Starting Continuous Monitoring System Demo")
        print("=" * 60)
        
        demo_results = {}
        
        try:
            # 1. Quality Analysis
            analysis_result = self.demonstrate_quality_analysis()
            demo_results["quality_analysis"] = analysis_result
            
            if analysis_result["success"]:
                metrics = analysis_result["metrics"]
                
                # 2. Quality Gates
                gates_result = self.demonstrate_quality_gates(metrics)
                demo_results["quality_gates"] = gates_result
                
                # 3. Regression Detection
                regression_result = self.demonstrate_regression_detection()
                demo_results["regression_detection"] = regression_result
            
            # 4. CI/CD Integration
            cicd_result = self.demonstrate_cicd_integration()
            demo_results["cicd_integration"] = cicd_result
            
            # 5. Maintenance Automation
            maintenance_result = self.demonstrate_maintenance_automation()
            demo_results["maintenance_automation"] = maintenance_result
            
            # 6. Complete Monitoring Cycle
            cycle_result = self.demonstrate_monitoring_cycle()
            demo_results["monitoring_cycle"] = cycle_result
            
            # 7. Database Operations
            db_result = self.demonstrate_database_operations()
            demo_results["database_operations"] = db_result
            
            print("\n" + "=" * 60)
            print("✅ Demo completed successfully!")
            print("\nDemo Summary:")
            print(f"  Quality Analysis: {'✅' if demo_results.get('quality_analysis', {}).get('success') else '❌'}")
            print(f"  Quality Gates: {'✅' if demo_results.get('quality_gates', {}).get('overall_status') == 'PASSED' else '❌'}")
            print(f"  Regression Detection: {'✅' if 'regression_detection' in demo_results else '❌'}")
            print(f"  CI/CD Integration: {'✅' if demo_results.get('cicd_integration', {}).get('exit_code') == 0 else '❌'}")
            print(f"  Maintenance Automation: {'✅' if demo_results.get('maintenance_automation', {}).get('backup_created') else '❌'}")
            print(f"  Monitoring Cycle: {'✅' if demo_results.get('monitoring_cycle', {}).get('success') else '❌'}")
            print(f"  Database Operations: {'✅' if demo_results.get('database_operations', {}).get('database_exists') else '❌'}")
            
            return demo_results
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            return {"success": False, "error": str(e)}


def main():
    """Main entry point for the demo."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Continuous Monitoring System Demo")
    parser.add_argument("--demo-dir", type=Path, help="Demo directory path")
    parser.add_argument("--keep-files", action="store_true", help="Keep demo files after completion")
    parser.add_argument("--component", choices=[
        "analysis", "gates", "regression", "cicd", "maintenance", "cycle", "database", "all"
    ], default="all", help="Specific component to demo")
    
    args = parser.parse_args()
    
    # Create demo directory
    if args.demo_dir:
        demo_dir = args.demo_dir
    else:
        demo_dir = Path(tempfile.mkdtemp(prefix="monitoring_demo_"))
    
    demo_dir.mkdir(exist_ok=True)
    
    try:
        demo = MonitoringSystemDemo(demo_dir)
        
        if args.component == "all":
            results = demo.run_complete_demo()
        elif args.component == "analysis":
            results = demo.demonstrate_quality_analysis()
        elif args.component == "gates":
            # Need metrics first
            analysis_result = demo.demonstrate_quality_analysis()
            if analysis_result["success"]:
                results = demo.demonstrate_quality_gates(analysis_result["metrics"])
            else:
                results = {"error": "Quality analysis failed"}
        elif args.component == "regression":
            results = demo.demonstrate_regression_detection()
        elif args.component == "cicd":
            results = demo.demonstrate_cicd_integration()
        elif args.component == "maintenance":
            results = demo.demonstrate_maintenance_automation()
        elif args.component == "cycle":
            results = demo.demonstrate_monitoring_cycle()
        elif args.component == "database":
            results = demo.demonstrate_database_operations()
        
        # Save results
        results_file = demo_dir / "demo_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Demo results saved to: {results_file}")
        
        if not args.keep_files and not args.demo_dir:
            print(f"\n🗑️ Cleaning up demo directory: {demo_dir}")
            import shutil
            shutil.rmtree(demo_dir)
        else:
            print(f"\n📁 Demo files preserved in: {demo_dir}")
        
    except Exception as e:
        logger.error(f"Demo execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()