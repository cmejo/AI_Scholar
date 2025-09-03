#!/usr/bin/env python3
"""
CI/CD Quality Gate Enforcement System
Integrates with continuous integration pipelines to enforce quality standards.
"""

import json
import logging
import os
import sys
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class QualityGateResult:
    name: str
    passed: bool
    threshold: Any
    actual_value: Any
    message: str
    blocking: bool = True


@dataclass
class CICDReport:
    timestamp: datetime
    pipeline_id: str
    branch: str
    commit_hash: str
    quality_gates: List[QualityGateResult]
    overall_status: str
    metrics: Dict[str, Any]
    recommendations: List[str]


class CICDQualityGates:
    """CI/CD Quality Gate enforcement system."""
    
    def __init__(self, project_root: Path, config_file: Optional[Path] = None):
        self.project_root = project_root
        self.config_file = config_file or project_root / "monitoring-config.yml"
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            import yaml
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
        
        # Default configuration
        return {
            "quality_gates": {
                "max_critical_issues": 0,
                "max_high_issues": 5,
                "max_total_issues": 50,
                "min_test_coverage": 80.0,
                "max_ubuntu_compatibility_issues": 2,
                "require_build_success": True,
                "require_deployment_success": True
            },
            "cicd_integration": {
                "enable_quality_gates": True,
                "fail_on_gate_failure": True,
                "generate_reports": True,
                "report_formats": ["json", "html", "junit"]
            }
        }
    
    def run_quality_analysis(self) -> Dict[str, Any]:
        """Run quality analysis and return results."""
        logger.info("Running quality analysis for CI/CD...")
        
        # Run the continuous monitoring system
        monitoring_script = self.project_root / "scripts" / "continuous_monitoring_system.py"
        if not monitoring_script.exists():
            raise FileNotFoundError("Continuous monitoring system not found")
        
        try:
            result = subprocess.run([
                "python", str(monitoring_script), "--project-root", str(self.project_root)
            ], capture_output=True, text=True, timeout=1800)
            
            if result.returncode != 0:
                logger.error(f"Quality analysis failed: {result.stderr}")
                raise RuntimeError("Quality analysis failed")
            
            # Parse the monitoring result
            monitoring_result = json.loads(result.stdout)
            return monitoring_result
            
        except Exception as e:
            logger.error(f"Failed to run quality analysis: {e}")
            raise
    
    def evaluate_quality_gates(self, analysis_result: Dict[str, Any]) -> List[QualityGateResult]:
        """Evaluate quality gates against analysis results."""
        gates_config = self.config["quality_gates"]
        metrics = analysis_result.get("metrics", {})
        
        gate_results = []
        
        # Critical issues gate
        critical_issues = metrics.get("critical_issues", 0)
        max_critical = gates_config.get("max_critical_issues", 0)
        gate_results.append(QualityGateResult(
            name="critical_issues",
            passed=critical_issues <= max_critical,
            threshold=max_critical,
            actual_value=critical_issues,
            message=f"Critical issues: {critical_issues} (max: {max_critical})",
            blocking=True
        ))
        
        # High issues gate
        high_issues = metrics.get("high_issues", 0)
        max_high = gates_config.get("max_high_issues", 5)
        gate_results.append(QualityGateResult(
            name="high_issues",
            passed=high_issues <= max_high,
            threshold=max_high,
            actual_value=high_issues,
            message=f"High severity issues: {high_issues} (max: {max_high})",
            blocking=True
        ))
        
        # Total issues gate
        total_issues = metrics.get("total_issues", 0)
        max_total = gates_config.get("max_total_issues", 50)
        gate_results.append(QualityGateResult(
            name="total_issues",
            passed=total_issues <= max_total,
            threshold=max_total,
            actual_value=total_issues,
            message=f"Total issues: {total_issues} (max: {max_total})",
            blocking=False
        ))
        
        # Test coverage gate
        test_coverage = metrics.get("test_coverage", 0.0)
        min_coverage = gates_config.get("min_test_coverage", 80.0)
        gate_results.append(QualityGateResult(
            name="test_coverage",
            passed=test_coverage >= min_coverage,
            threshold=min_coverage,
            actual_value=test_coverage,
            message=f"Test coverage: {test_coverage:.1f}% (min: {min_coverage}%)",
            blocking=True
        ))
        
        # Ubuntu compatibility gate
        ubuntu_issues = metrics.get("ubuntu_issues", 0)
        max_ubuntu = gates_config.get("max_ubuntu_compatibility_issues", 2)
        gate_results.append(QualityGateResult(
            name="ubuntu_compatibility",
            passed=ubuntu_issues <= max_ubuntu,
            threshold=max_ubuntu,
            actual_value=ubuntu_issues,
            message=f"Ubuntu compatibility issues: {ubuntu_issues} (max: {max_ubuntu})",
            blocking=True
        ))
        
        # Build success gate
        if gates_config.get("require_build_success", True):
            build_success = metrics.get("build_success", False)
            gate_results.append(QualityGateResult(
                name="build_success",
                passed=build_success,
                threshold=True,
                actual_value=build_success,
                message=f"Build success: {build_success}",
                blocking=True
            ))
        
        # Deployment validation gate
        if gates_config.get("require_deployment_success", True):
            deployment_success = metrics.get("deployment_success", False)
            gate_results.append(QualityGateResult(
                name="deployment_success",
                passed=deployment_success,
                threshold=True,
                actual_value=deployment_success,
                message=f"Deployment validation: {deployment_success}",
                blocking=True
            ))
        
        return gate_results
    
    def generate_recommendations(self, gate_results: List[QualityGateResult], metrics: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on gate results."""
        recommendations = []
        
        for gate in gate_results:
            if not gate.passed:
                if gate.name == "critical_issues":
                    recommendations.append(
                        "🔴 Fix all critical issues before proceeding. "
                        "Critical issues indicate serious problems that must be resolved."
                    )
                
                elif gate.name == "high_issues":
                    recommendations.append(
                        "🟠 Reduce high severity issues. Consider fixing the most impactful ones first."
                    )
                
                elif gate.name == "test_coverage":
                    recommendations.append(
                        "📊 Increase test coverage by adding unit tests for uncovered code paths."
                    )
                
                elif gate.name == "ubuntu_compatibility":
                    recommendations.append(
                        "🐧 Fix Ubuntu compatibility issues to ensure proper deployment on Ubuntu servers."
                    )
                
                elif gate.name == "build_success":
                    recommendations.append(
                        "🔨 Fix build errors. The application must build successfully before deployment."
                    )
                
                elif gate.name == "deployment_success":
                    recommendations.append(
                        "🚀 Fix deployment configuration issues. Validate Docker and deployment scripts."
                    )
        
        # Add general recommendations based on metrics
        auto_fixable = metrics.get("auto_fixable_issues", 0)
        if auto_fixable > 0:
            recommendations.append(
                f"🔧 {auto_fixable} issues can be automatically fixed. "
                "Run the automated fix system to resolve them quickly."
            )
        
        return recommendations
    
    def create_cicd_report(self, analysis_result: Dict[str, Any], gate_results: List[QualityGateResult]) -> CICDReport:
        """Create comprehensive CI/CD report."""
        # Get CI/CD environment information
        pipeline_id = os.getenv("CI_PIPELINE_ID", os.getenv("GITHUB_RUN_ID", "unknown"))
        branch = os.getenv("CI_COMMIT_REF_NAME", os.getenv("GITHUB_REF_NAME", "unknown"))
        commit_hash = os.getenv("CI_COMMIT_SHA", os.getenv("GITHUB_SHA", "unknown"))
        
        # Determine overall status
        blocking_failures = [gate for gate in gate_results if not gate.passed and gate.blocking]
        overall_status = "FAILED" if blocking_failures else "PASSED"
        
        # Generate recommendations
        recommendations = self.generate_recommendations(gate_results, analysis_result.get("metrics", {}))
        
        return CICDReport(
            timestamp=datetime.now(),
            pipeline_id=pipeline_id,
            branch=branch,
            commit_hash=commit_hash,
            quality_gates=gate_results,
            overall_status=overall_status,
            metrics=analysis_result.get("metrics", {}),
            recommendations=recommendations
        )
    
    def generate_json_report(self, report: CICDReport, output_path: Path):
        """Generate JSON report for CI/CD systems."""
        report_data = asdict(report)
        
        # Convert datetime to string for JSON serialization
        report_data["timestamp"] = report.timestamp.isoformat()
        
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"JSON report generated: {output_path}")
    
    def generate_html_report(self, report: CICDReport, output_path: Path):
        """Generate HTML report for human consumption."""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Quality Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 20px; }
        .status-passed { color: #28a745; font-weight: bold; }
        .status-failed { color: #dc3545; font-weight: bold; }
        .gate-passed { background-color: #d4edda; border-left: 4px solid #28a745; padding: 10px; margin: 5px 0; }
        .gate-failed { background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 10px; margin: 5px 0; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .metric-card { background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }
        .metric-value { font-size: 2em; font-weight: bold; color: #007bff; }
        .recommendations { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .recommendation { margin: 10px 0; padding: 5px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Code Quality Report</h1>
            <p><strong>Pipeline:</strong> {pipeline_id}</p>
            <p><strong>Branch:</strong> {branch}</p>
            <p><strong>Commit:</strong> {commit_hash}</p>
            <p><strong>Timestamp:</strong> {timestamp}</p>
            <p><strong>Overall Status:</strong> <span class="status-{status_class}">{overall_status}</span></p>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value">{total_issues}</div>
                <div>Total Issues</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{critical_issues}</div>
                <div>Critical Issues</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{high_issues}</div>
                <div>High Issues</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{test_coverage:.1f}%</div>
                <div>Test Coverage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{ubuntu_issues}</div>
                <div>Ubuntu Issues</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{auto_fixable_issues}</div>
                <div>Auto-fixable</div>
            </div>
        </div>
        
        <h2>Quality Gates</h2>
        {quality_gates_html}
        
        {recommendations_html}
    </div>
</body>
</html>
        """
        
        # Generate quality gates HTML
        gates_html = ""
        for gate in report.quality_gates:
            gate_class = "gate-passed" if gate.passed else "gate-failed"
            status_icon = "✅" if gate.passed else "❌"
            blocking_text = " (Blocking)" if gate.blocking else " (Non-blocking)"
            
            gates_html += f"""
            <div class="{gate_class}">
                <strong>{status_icon} {gate.name.replace('_', ' ').title()}{blocking_text}</strong><br>
                {gate.message}
            </div>
            """
        
        # Generate recommendations HTML
        recommendations_html = ""
        if report.recommendations:
            recommendations_html = """
            <div class="recommendations">
                <h3>Recommendations</h3>
            """
            for rec in report.recommendations:
                recommendations_html += f'<div class="recommendation">{rec}</div>'
            recommendations_html += "</div>"
        
        # Fill template
        html_content = html_template.format(
            pipeline_id=report.pipeline_id,
            branch=report.branch,
            commit_hash=report.commit_hash[:8],
            timestamp=report.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            overall_status=report.overall_status,
            status_class=report.overall_status.lower(),
            total_issues=report.metrics.get("total_issues", 0),
            critical_issues=report.metrics.get("critical_issues", 0),
            high_issues=report.metrics.get("high_issues", 0),
            test_coverage=report.metrics.get("test_coverage", 0.0),
            ubuntu_issues=report.metrics.get("ubuntu_issues", 0),
            auto_fixable_issues=report.metrics.get("auto_fixable_issues", 0),
            quality_gates_html=gates_html,
            recommendations_html=recommendations_html
        )
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {output_path}")
    
    def generate_junit_report(self, report: CICDReport, output_path: Path):
        """Generate JUnit XML report for CI/CD integration."""
        # Create root element
        testsuites = ET.Element("testsuites")
        testsuites.set("name", "Quality Gates")
        testsuites.set("tests", str(len(report.quality_gates)))
        testsuites.set("failures", str(sum(1 for gate in report.quality_gates if not gate.passed)))
        testsuites.set("time", "0")
        testsuites.set("timestamp", report.timestamp.isoformat())
        
        # Create testsuite
        testsuite = ET.SubElement(testsuites, "testsuite")
        testsuite.set("name", "Quality Gates")
        testsuite.set("tests", str(len(report.quality_gates)))
        testsuite.set("failures", str(sum(1 for gate in report.quality_gates if not gate.passed)))
        testsuite.set("time", "0")
        
        # Add test cases for each quality gate
        for gate in report.quality_gates:
            testcase = ET.SubElement(testsuite, "testcase")
            testcase.set("name", gate.name)
            testcase.set("classname", "QualityGates")
            testcase.set("time", "0")
            
            if not gate.passed:
                failure = ET.SubElement(testcase, "failure")
                failure.set("message", gate.message)
                failure.set("type", "QualityGateFailure")
                failure.text = f"Quality gate '{gate.name}' failed: {gate.message}"
        
        # Write XML file
        tree = ET.ElementTree(testsuites)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        
        logger.info(f"JUnit report generated: {output_path}")
    
    def run_cicd_quality_check(self, output_dir: Optional[Path] = None) -> int:
        """Run complete CI/CD quality check and return exit code."""
        if output_dir is None:
            output_dir = self.project_root / "quality-reports"
        
        output_dir.mkdir(exist_ok=True)
        
        try:
            # Run quality analysis
            analysis_result = self.run_quality_analysis()
            
            # Evaluate quality gates
            gate_results = self.evaluate_quality_gates(analysis_result)
            
            # Create report
            report = self.create_cicd_report(analysis_result, gate_results)
            
            # Generate reports in configured formats
            report_formats = self.config["cicd_integration"].get("report_formats", ["json"])
            
            if "json" in report_formats:
                self.generate_json_report(report, output_dir / "quality-report.json")
            
            if "html" in report_formats:
                self.generate_html_report(report, output_dir / "quality-report.html")
            
            if "junit" in report_formats:
                self.generate_junit_report(report, output_dir / "quality-report.xml")
            
            # Log results
            logger.info(f"Quality check completed. Overall status: {report.overall_status}")
            
            for gate in gate_results:
                status_icon = "✅" if gate.passed else "❌"
                logger.info(f"{status_icon} {gate.name}: {gate.message}")
            
            if report.recommendations:
                logger.info("Recommendations:")
                for rec in report.recommendations:
                    logger.info(f"  {rec}")
            
            # Determine exit code
            if self.config["cicd_integration"].get("fail_on_gate_failure", True):
                blocking_failures = [gate for gate in gate_results if not gate.passed and gate.blocking]
                return 1 if blocking_failures else 0
            else:
                return 0
            
        except Exception as e:
            logger.error(f"CI/CD quality check failed: {e}")
            return 1


def main():
    """Main entry point for CI/CD quality gates."""
    import argparse
    
    parser = argparse.ArgumentParser(description="CI/CD Quality Gate Enforcement")
    parser.add_argument("--config", type=Path, help="Configuration file path")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root directory")
    parser.add_argument("--output-dir", type=Path, help="Output directory for reports")
    parser.add_argument("--fail-on-gate-failure", action="store_true", help="Fail with non-zero exit code on gate failures")
    
    args = parser.parse_args()
    
    # Initialize CI/CD quality gates
    cicd_gates = CICDQualityGates(args.project_root, args.config)
    
    # Override config if command line argument provided
    if args.fail_on_gate_failure:
        cicd_gates.config["cicd_integration"]["fail_on_gate_failure"] = True
    
    # Run quality check
    exit_code = cicd_gates.run_cicd_quality_check(args.output_dir)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()