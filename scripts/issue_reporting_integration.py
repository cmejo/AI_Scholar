#!/usr/bin/env python3
"""
Issue Reporting Integration System

This script integrates the comprehensive issue reporting system with existing analyzers,
collecting issues from all analysis tools and generating unified reports.

Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the scripts directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from issue_reporting_system import (
    ComprehensiveIssueReportingSystem,
    IssueType,
    IssueSeverity,
    AnalysisIssue
)

# Import existing analyzers
try:
    from python_backend_analyzer import PythonBackendAnalyzer
    HAS_PYTHON_ANALYZER = True
except ImportError:
    HAS_PYTHON_ANALYZER = False
    logging.warning("Python backend analyzer not available")

try:
    from typescript_frontend_analyzer import TypeScriptFrontendAnalyzer
    HAS_TYPESCRIPT_ANALYZER = True
except ImportError:
    HAS_TYPESCRIPT_ANALYZER = False
    logging.warning("TypeScript frontend analyzer not available")

try:
    from docker_deployment_validator import DockerDeploymentValidator
    HAS_DOCKER_VALIDATOR = True
except ImportError:
    HAS_DOCKER_VALIDATOR = False
    logging.warning("Docker deployment validator not available")

try:
    from security_vulnerability_scanner import SecurityVulnerabilityScanner
    HAS_SECURITY_SCANNER = True
except ImportError:
    HAS_SECURITY_SCANNER = False
    logging.warning("Security vulnerability scanner not available")

try:
    from ubuntu_compatibility_tester import UbuntuCompatibilityTester
    HAS_UBUNTU_TESTER = True
except ImportError:
    HAS_UBUNTU_TESTER = False
    logging.warning("Ubuntu compatibility tester not available")

try:
    from code_quality_analyzer import CodeQualityAnalyzer
    HAS_CODE_QUALITY_ANALYZER = True
except ImportError:
    HAS_CODE_QUALITY_ANALYZER = False
    logging.warning("Code quality analyzer not available")

try:
    from performance_analyzer import PerformanceAnalyzer
    HAS_PERFORMANCE_ANALYZER = True
except ImportError:
    HAS_PERFORMANCE_ANALYZER = False
    logging.warning("Performance analyzer not available")


class IssueCollector:
    """Collects issues from various analysis tools and converts them to unified format"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.reporting_system = ComprehensiveIssueReportingSystem(project_root)
        self.logger = logging.getLogger(__name__)
        
        # Issue type mappings for legacy analyzers
        self.type_mappings = {
            # Python analyzer mappings
            "syntax_error": IssueType.SYNTAX_ERROR,
            "type_error": IssueType.TYPE_ERROR,
            "import_error": IssueType.IMPORT_ERROR,
            "dependency_vulnerability": IssueType.DEPENDENCY_VULNERABILITY,
            "sql_syntax_error": IssueType.SQL_SYNTAX_ERROR,
            "sql_performance_issue": IssueType.SQL_PERFORMANCE_ISSUE,
            "service_integration_error": IssueType.SERVICE_INTEGRATION_ERROR,
            "style_issue": IssueType.STYLE_ISSUE,
            "security_vulnerability": IssueType.SECURITY_VULNERABILITY,
            
            # TypeScript analyzer mappings
            "typescript_error": IssueType.TYPESCRIPT_ERROR,
            "type_mismatch": IssueType.TYPE_ERROR,
            "unused_import": IssueType.UNUSED_IMPORT,
            "component_issue": IssueType.REACT_COMPONENT_ISSUE,
            "bundle_issue": IssueType.BUNDLE_SIZE_ISSUE,
            "accessibility_issue": IssueType.ACCESSIBILITY_ISSUE,
            "performance_issue": IssueType.PERFORMANCE_ISSUE,
            
            # Docker validator mappings
            "dockerfile_issue": IssueType.DOCKERFILE_ISSUE,
            "docker_compose_issue": IssueType.DOCKER_COMPOSE_ISSUE,
            "deployment_script_issue": IssueType.DEPLOYMENT_SCRIPT_ISSUE,
            "environment_config_issue": IssueType.ENVIRONMENT_CONFIG_ISSUE,
            "ubuntu_compatibility": IssueType.UBUNTU_COMPATIBILITY,
            
            # Security scanner mappings
            "vulnerability": IssueType.SECURITY_VULNERABILITY,
            "dependency_vuln": IssueType.DEPENDENCY_VULNERABILITY,
            "permission_issue": IssueType.PERMISSION_ISSUE,
            
            # Performance analyzer mappings
            "memory_leak": IssueType.MEMORY_LEAK,
            "cpu_issue": IssueType.PERFORMANCE_ISSUE,
            "database_performance": IssueType.SQL_PERFORMANCE_ISSUE,
            
            # Code quality mappings
            "code_smell": IssueType.CODE_SMELL,
            "technical_debt": IssueType.TECHNICAL_DEBT,
            "documentation_issue": IssueType.DOCUMENTATION_ISSUE
        }
        
        self.severity_mappings = {
            "critical": IssueSeverity.CRITICAL,
            "high": IssueSeverity.HIGH,
            "medium": IssueSeverity.MEDIUM,
            "low": IssueSeverity.LOW,
            "info": IssueSeverity.INFO
        }
    
    def collect_python_issues(self) -> List[AnalysisIssue]:
        """Collect issues from Python backend analyzer"""
        issues = []
        
        if not HAS_PYTHON_ANALYZER:
            self.logger.warning("Python analyzer not available, skipping")
            return issues
        
        try:
            self.logger.info("Running Python backend analysis...")
            analyzer = PythonBackendAnalyzer(self.project_root / "backend")
            
            # Run different analysis types
            analysis_results = [
                analyzer.analyze_syntax_and_imports(),
                analyzer.analyze_dependencies(),
                analyzer.analyze_database_queries()
            ]
            
            for result in analysis_results:
                if result.success:
                    for legacy_issue in result.issues:
                        issue = self._convert_legacy_issue(legacy_issue, "python_analyzer")
                        if issue:
                            issues.append(issue)
                else:
                    self.logger.error(f"Python analysis failed: {result.error_message}")
            
            self.logger.info(f"Collected {len(issues)} Python issues")
            
        except Exception as e:
            self.logger.error(f"Error collecting Python issues: {e}")
        
        return issues
    
    def collect_typescript_issues(self) -> List[AnalysisIssue]:
        """Collect issues from TypeScript frontend analyzer"""
        issues = []
        
        if not HAS_TYPESCRIPT_ANALYZER:
            self.logger.warning("TypeScript analyzer not available, skipping")
            return issues
        
        try:
            self.logger.info("Running TypeScript frontend analysis...")
            analyzer = TypeScriptFrontendAnalyzer(str(self.project_root))
            
            # Check dependencies first
            if not analyzer._check_dependencies():
                self.logger.warning("TypeScript analyzer dependencies not available")
                return issues
            
            # Run comprehensive analysis
            result = analyzer.analyze_comprehensive()
            
            # Convert TypeScript analysis results
            if result.typescript_analysis.success:
                for legacy_issue in (result.typescript_analysis.compilation_errors + 
                                   result.typescript_analysis.type_errors + 
                                   result.typescript_analysis.warnings):
                    issue = self._convert_legacy_issue(legacy_issue, "typescript_analyzer")
                    if issue:
                        issues.append(issue)
            
            if result.react_analysis.success:
                for legacy_issue in (result.react_analysis.unused_imports + 
                                   result.react_analysis.component_issues + 
                                   result.react_analysis.hook_issues):
                    issue = self._convert_legacy_issue(legacy_issue, "react_analyzer")
                    if issue:
                        issues.append(issue)
            
            if result.bundle_analysis.success:
                for legacy_issue in (result.bundle_analysis.bundle_size_issues + 
                                   result.bundle_analysis.optimization_opportunities + 
                                   result.bundle_analysis.dependency_issues):
                    issue = self._convert_legacy_issue(legacy_issue, "bundle_analyzer")
                    if issue:
                        issues.append(issue)
            
            if result.accessibility_analysis.success:
                for legacy_issue in result.accessibility_analysis.accessibility_violations:
                    issue = self._convert_legacy_issue(legacy_issue, "accessibility_analyzer")
                    if issue:
                        issues.append(issue)
            
            self.logger.info(f"Collected {len(issues)} TypeScript/React issues")
            
        except Exception as e:
            self.logger.error(f"Error collecting TypeScript issues: {e}")
        
        return issues
    
    def collect_docker_issues(self) -> List[AnalysisIssue]:
        """Collect issues from Docker deployment validator"""
        issues = []
        
        if not HAS_DOCKER_VALIDATOR:
            self.logger.warning("Docker validator not available, skipping")
            return issues
        
        try:
            self.logger.info("Running Docker deployment validation...")
            validator = DockerDeploymentValidator(str(self.project_root))
            result = validator.validate_all()
            
            for legacy_issue in result.issues:
                issue = self._convert_legacy_issue(legacy_issue, "docker_validator")
                if issue:
                    issues.append(issue)
            
            self.logger.info(f"Collected {len(issues)} Docker issues")
            
        except Exception as e:
            self.logger.error(f"Error collecting Docker issues: {e}")
        
        return issues
    
    def collect_security_issues(self) -> List[AnalysisIssue]:
        """Collect issues from security vulnerability scanner"""
        issues = []
        
        if not HAS_SECURITY_SCANNER:
            self.logger.warning("Security scanner not available, skipping")
            return issues
        
        try:
            self.logger.info("Running security vulnerability scan...")
            scanner = SecurityVulnerabilityScanner(str(self.project_root))
            result = scanner.run_comprehensive_scan()
            
            # Convert security scan results
            for category, scan_issues in result.items():
                if isinstance(scan_issues, list):
                    for legacy_issue in scan_issues:
                        issue = self._convert_legacy_issue(legacy_issue, "security_scanner")
                        if issue:
                            issues.append(issue)
            
            self.logger.info(f"Collected {len(issues)} security issues")
            
        except Exception as e:
            self.logger.error(f"Error collecting security issues: {e}")
        
        return issues
    
    def collect_ubuntu_compatibility_issues(self) -> List[AnalysisIssue]:
        """Collect issues from Ubuntu compatibility tester"""
        issues = []
        
        if not HAS_UBUNTU_TESTER:
            self.logger.warning("Ubuntu compatibility tester not available, skipping")
            return issues
        
        try:
            self.logger.info("Running Ubuntu compatibility tests...")
            tester = UbuntuCompatibilityTester(str(self.project_root))
            result = tester.run_comprehensive_compatibility_test()
            
            # Convert compatibility test results
            for test_category, test_results in result.items():
                if isinstance(test_results, dict) and 'issues' in test_results:
                    for legacy_issue in test_results['issues']:
                        issue = self._convert_legacy_issue(legacy_issue, "ubuntu_tester")
                        if issue:
                            issues.append(issue)
            
            self.logger.info(f"Collected {len(issues)} Ubuntu compatibility issues")
            
        except Exception as e:
            self.logger.error(f"Error collecting Ubuntu compatibility issues: {e}")
        
        return issues
    
    def collect_code_quality_issues(self) -> List[AnalysisIssue]:
        """Collect issues from code quality analyzer"""
        issues = []
        
        if not HAS_CODE_QUALITY_ANALYZER:
            self.logger.warning("Code quality analyzer not available, skipping")
            return issues
        
        try:
            self.logger.info("Running code quality analysis...")
            analyzer = CodeQualityAnalyzer(str(self.project_root))
            result = analyzer.run_comprehensive_analysis()
            
            # Convert code quality results
            for analysis_type, analysis_results in result.items():
                if isinstance(analysis_results, dict) and 'issues' in analysis_results:
                    for legacy_issue in analysis_results['issues']:
                        issue = self._convert_legacy_issue(legacy_issue, "code_quality_analyzer")
                        if issue:
                            issues.append(issue)
            
            self.logger.info(f"Collected {len(issues)} code quality issues")
            
        except Exception as e:
            self.logger.error(f"Error collecting code quality issues: {e}")
        
        return issues
    
    def collect_performance_issues(self) -> List[AnalysisIssue]:
        """Collect issues from performance analyzer"""
        issues = []
        
        if not HAS_PERFORMANCE_ANALYZER:
            self.logger.warning("Performance analyzer not available, skipping")
            return issues
        
        try:
            self.logger.info("Running performance analysis...")
            analyzer = PerformanceAnalyzer(str(self.project_root))
            result = analyzer.run_comprehensive_analysis()
            
            # Convert performance analysis results
            for analysis_type, analysis_results in result.items():
                if isinstance(analysis_results, dict) and 'issues' in analysis_results:
                    for legacy_issue in analysis_results['issues']:
                        issue = self._convert_legacy_issue(legacy_issue, "performance_analyzer")
                        if issue:
                            issues.append(issue)
            
            self.logger.info(f"Collected {len(issues)} performance issues")
            
        except Exception as e:
            self.logger.error(f"Error collecting performance issues: {e}")
        
        return issues
    
    def _convert_legacy_issue(self, legacy_issue: Any, tool: str) -> Optional[AnalysisIssue]:
        """Convert legacy issue format to new comprehensive format"""
        try:
            # Handle different legacy issue formats
            if hasattr(legacy_issue, '__dict__'):
                # Dataclass or object with attributes
                issue_dict = legacy_issue.__dict__ if hasattr(legacy_issue, '__dict__') else {}
            elif isinstance(legacy_issue, dict):
                # Dictionary format
                issue_dict = legacy_issue
            else:
                self.logger.warning(f"Unknown legacy issue format: {type(legacy_issue)}")
                return None
            
            # Extract basic information
            issue_type_str = issue_dict.get('type', 'unknown')
            if hasattr(issue_type_str, 'value'):
                issue_type_str = issue_type_str.value
            
            severity_str = issue_dict.get('severity', 'medium')
            if hasattr(severity_str, 'value'):
                severity_str = severity_str.value
            elif hasattr(severity_str, 'label'):
                severity_str = severity_str.label
            
            # Map to new types
            issue_type = self.type_mappings.get(issue_type_str, IssueType.TECHNICAL_DEBT)
            severity = self.severity_mappings.get(severity_str, IssueSeverity.MEDIUM)
            
            # Extract location information
            file_path = issue_dict.get('file_path', 'unknown')
            line_number = issue_dict.get('line_number')
            column_number = issue_dict.get('column_number')
            
            # Extract description and title
            description = issue_dict.get('description', 'No description available')
            title = description[:100] + "..." if len(description) > 100 else description
            
            # Extract additional information
            code_snippet = issue_dict.get('code_snippet')
            function_name = issue_dict.get('function_name')
            class_name = issue_dict.get('class_name')
            
            # Create comprehensive issue
            issue = self.reporting_system.create_issue(
                issue_type=issue_type,
                severity=severity,
                title=title,
                description=description,
                file_path=file_path,
                line_number=line_number,
                column_number=column_number,
                tool=tool,
                code_snippet=code_snippet,
                function_name=function_name,
                class_name=class_name
            )
            
            # Add legacy-specific tags
            if issue_dict.get('ubuntu_specific'):
                issue.tags.add('ubuntu_specific')
            if issue_dict.get('auto_fixable'):
                issue.tags.add('auto_fixable')
            
            return issue
            
        except Exception as e:
            self.logger.error(f"Error converting legacy issue: {e}")
            return None
    
    def collect_all_issues(self) -> List[AnalysisIssue]:
        """Collect issues from all available analyzers"""
        all_issues = []
        
        # Collect from each analyzer
        collectors = [
            ("Python Backend", self.collect_python_issues),
            ("TypeScript Frontend", self.collect_typescript_issues),
            ("Docker Deployment", self.collect_docker_issues),
            ("Security Vulnerabilities", self.collect_security_issues),
            ("Ubuntu Compatibility", self.collect_ubuntu_compatibility_issues),
            ("Code Quality", self.collect_code_quality_issues),
            ("Performance", self.collect_performance_issues)
        ]
        
        for name, collector in collectors:
            try:
                self.logger.info(f"Collecting issues from {name}...")
                issues = collector()
                all_issues.extend(issues)
                self.logger.info(f"Collected {len(issues)} issues from {name}")
            except Exception as e:
                self.logger.error(f"Error collecting issues from {name}: {e}")
        
        self.logger.info(f"Total issues collected: {len(all_issues)}")
        return all_issues


class IntegratedIssueReporter:
    """Main class for integrated issue reporting"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.collector = IssueCollector(project_root)
        self.reporting_system = ComprehensiveIssueReportingSystem(project_root)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def run_comprehensive_analysis(self, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Run comprehensive analysis and generate reports"""
        start_time = time.time()
        
        self.logger.info("Starting comprehensive issue analysis...")
        
        # Collect all issues
        all_issues = self.collector.collect_all_issues()
        
        if not all_issues:
            self.logger.warning("No issues found")
            return {
                "total_issues": 0,
                "execution_time": time.time() - start_time,
                "reports": {}
            }
        
        # Generate comprehensive reports
        reports = self.reporting_system.generate_comprehensive_report(all_issues, output_dir)
        
        # Generate analysis summary
        summary = self._generate_analysis_summary(all_issues)
        
        execution_time = time.time() - start_time
        
        result = {
            "total_issues": len(all_issues),
            "execution_time": execution_time,
            "summary": summary,
            "reports": reports,
            "priority_issues": [
                {
                    "id": issue.id,
                    "title": issue.title,
                    "severity": issue.severity.label,
                    "priority_score": issue.priority_score,
                    "file_path": issue.location.file_path
                }
                for issue in self.reporting_system.get_priority_issues(all_issues, 10)
            ],
            "ubuntu_issues": len(self.reporting_system.get_ubuntu_specific_issues(all_issues)),
            "auto_fixable_issues": len(self.reporting_system.get_auto_fixable_issues(all_issues)),
            "blocking_issues": len(self.reporting_system.get_blocking_issues(all_issues))
        }
        
        self.logger.info(f"Analysis completed in {execution_time:.2f} seconds")
        self.logger.info(f"Generated {len(reports)} report files")
        
        return result
    
    def _generate_analysis_summary(self, issues: List[AnalysisIssue]) -> Dict[str, Any]:
        """Generate analysis summary statistics"""
        summary = {
            "by_severity": {},
            "by_category": {},
            "by_type": {},
            "by_tool": {},
            "by_file_extension": {},
            "impact_analysis": {
                "deployment_blocking": 0,
                "security_risk": 0,
                "performance_impact": 0,
                "ubuntu_specific": 0,
                "user_facing": 0,
                "core_functionality": 0
            }
        }
        
        for issue in issues:
            # Count by severity
            severity = issue.severity.label
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            
            # Count by category
            category = issue.category.value
            summary["by_category"][category] = summary["by_category"].get(category, 0) + 1
            
            # Count by type
            issue_type = issue.type.value
            summary["by_type"][issue_type] = summary["by_type"].get(issue_type, 0) + 1
            
            # Count by tool
            tool = issue.tool
            summary["by_tool"][tool] = summary["by_tool"].get(tool, 0) + 1
            
            # Count by file extension
            file_path = issue.location.file_path
            if '.' in file_path:
                ext = file_path.split('.')[-1].lower()
                summary["by_file_extension"][ext] = summary["by_file_extension"].get(ext, 0) + 1
            
            # Impact analysis
            if issue.impact.deployment_blocking:
                summary["impact_analysis"]["deployment_blocking"] += 1
            if issue.impact.security_risk:
                summary["impact_analysis"]["security_risk"] += 1
            if issue.impact.performance_impact:
                summary["impact_analysis"]["performance_impact"] += 1
            if issue.impact.ubuntu_specific:
                summary["impact_analysis"]["ubuntu_specific"] += 1
            if issue.impact.user_facing:
                summary["impact_analysis"]["user_facing"] += 1
            if issue.impact.affects_core_functionality:
                summary["impact_analysis"]["core_functionality"] += 1
        
        return summary
    
    def generate_fix_script(self, issues: List[AnalysisIssue], 
                           output_file: str = "auto_fix_script.sh") -> str:
        """Generate a script to automatically fix issues where possible"""
        auto_fixable_issues = self.reporting_system.get_auto_fixable_issues(issues)
        
        if not auto_fixable_issues:
            return "No auto-fixable issues found."
        
        script_lines = [
            "#!/bin/bash",
            "# Auto-generated fix script",
            f"# Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Fixes {len(auto_fixable_issues)} auto-fixable issues",
            "",
            "set -e  # Exit on any error",
            "",
            "echo 'Starting automatic fixes...'",
            ""
        ]
        
        for issue in auto_fixable_issues:
            script_lines.append(f"# Fix for: {issue.title}")
            script_lines.append(f"# File: {issue.location.file_path}")
            
            for fix in issue.fix_suggestions:
                if fix.auto_fixable and fix.fix_command:
                    script_lines.append(f"echo 'Applying fix: {fix.description}'")
                    script_lines.append(fix.fix_command)
                    script_lines.append("")
        
        script_lines.extend([
            "echo 'All automatic fixes applied successfully!'",
            "echo 'Please review the changes and run tests to verify everything works correctly.'"
        ])
        
        script_content = "\n".join(script_lines)
        
        output_path = self.project_root / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(output_path, 0o755)
        
        self.logger.info(f"Generated auto-fix script: {output_path}")
        return str(output_path)


def main():
    """Main function for running integrated issue reporting"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Issue Reporting System")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--output-dir", help="Output directory for reports")
    parser.add_argument("--generate-fix-script", action="store_true", 
                       help="Generate automatic fix script")
    parser.add_argument("--format", choices=["summary", "detailed", "json", "csv", "markdown"],
                       default="summary", help="Report format to display")
    
    args = parser.parse_args()
    
    # Run comprehensive analysis
    reporter = IntegratedIssueReporter(args.project_root)
    result = reporter.run_comprehensive_analysis(args.output_dir)
    
    # Display results
    print(f"\nCOMPREHENSIVE ISSUE ANALYSIS RESULTS")
    print("=" * 40)
    print(f"Total Issues Found: {result['total_issues']}")
    print(f"Analysis Time: {result['execution_time']:.2f} seconds")
    print(f"Ubuntu-specific Issues: {result['ubuntu_issues']}")
    print(f"Auto-fixable Issues: {result['auto_fixable_issues']}")
    print(f"Deployment Blocking Issues: {result['blocking_issues']}")
    
    if result['priority_issues']:
        print(f"\nTOP PRIORITY ISSUES:")
        for i, issue in enumerate(result['priority_issues'][:5], 1):
            print(f"{i}. [{issue['severity'].upper()}] {issue['title']}")
            print(f"   File: {issue['file_path']}")
            print(f"   Priority Score: {issue['priority_score']:.1f}")
    
    print(f"\nGenerated Reports:")
    for format_type, filepath in result['reports'].items():
        print(f"  {format_type}: {filepath}")
    
    # Generate fix script if requested
    if args.generate_fix_script and result['auto_fixable_issues'] > 0:
        # We need to collect issues again for the fix script
        all_issues = reporter.collector.collect_all_issues()
        fix_script = reporter.generate_fix_script(all_issues)
        print(f"\nGenerated auto-fix script: {fix_script}")
    
    return 0 if result['total_issues'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())