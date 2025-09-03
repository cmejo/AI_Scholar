#!/usr/bin/env python3
"""
Test script for the comprehensive issue reporting system

This script tests all components of the issue reporting and prioritization system
to ensure they work correctly with various types of issues.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add the scripts directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from issue_reporting_system import (
    ComprehensiveIssueReportingSystem,
    IssueType,
    IssueSeverity,
    IssueCategory,
    IssueClassifier,
    FixSuggestionGenerator,
    IssueReportGenerator,
    AnalysisIssue,
    IssueLocation,
    IssueImpact,
    FixSuggestion
)

from issue_reporting_integration import (
    IssueCollector,
    IntegratedIssueReporter
)


class TestIssueReportingSystem(unittest.TestCase):
    """Test cases for the issue reporting system"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.system = ComprehensiveIssueReportingSystem(self.temp_dir)
        self.classifier = IssueClassifier()
        self.fix_generator = FixSuggestionGenerator()
        self.report_generator = IssueReportGenerator()
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_issue_creation(self):
        """Test creating comprehensive issues"""
        issue = self.system.create_issue(
            issue_type=IssueType.SYNTAX_ERROR,
            severity=IssueSeverity.CRITICAL,
            title="Test syntax error",
            description="Missing colon in if statement",
            file_path="test.py",
            line_number=42,
            tool="test_analyzer"
        )
        
        self.assertIsInstance(issue, AnalysisIssue)
        self.assertEqual(issue.type, IssueType.SYNTAX_ERROR)
        self.assertEqual(issue.severity, IssueSeverity.CRITICAL)
        self.assertEqual(issue.title, "Test syntax error")
        self.assertEqual(issue.location.file_path, "test.py")
        self.assertEqual(issue.location.line_number, 42)
        self.assertEqual(issue.tool, "test_analyzer")
        self.assertGreater(issue.priority_score, 0)
        self.assertIsInstance(issue.fix_suggestions, list)
    
    def test_issue_classification(self):
        """Test issue classification and impact assessment"""
        # Test blocking issue
        category, impact = self.classifier.classify_issue(
            IssueType.SYNTAX_ERROR,
            "Cannot compile due to syntax error",
            "main.py"
        )
        
        self.assertEqual(category, IssueCategory.BLOCKING)
        self.assertTrue(impact.deployment_blocking)
        self.assertTrue(impact.affects_core_functionality)
        
        # Test security issue
        category, impact = self.classifier.classify_issue(
            IssueType.SECURITY_VULNERABILITY,
            "SQL injection vulnerability detected",
            "api/auth.py"
        )
        
        self.assertEqual(category, IssueCategory.SECURITY)
        self.assertTrue(impact.security_risk)
        
        # Test Ubuntu compatibility issue
        category, impact = self.classifier.classify_issue(
            IssueType.UBUNTU_COMPATIBILITY,
            "Using yum instead of apt-get",
            "deploy.sh"
        )
        
        self.assertEqual(category, IssueCategory.COMPATIBILITY)
        self.assertTrue(impact.ubuntu_specific)
    
    def test_priority_scoring(self):
        """Test priority scoring algorithm"""
        # Create issues with different characteristics
        critical_blocking = self.system.create_issue(
            IssueType.SYNTAX_ERROR,
            IssueSeverity.CRITICAL,
            "Critical syntax error",
            "Cannot compile",
            "main.py"
        )
        
        medium_style = self.system.create_issue(
            IssueType.STYLE_ISSUE,
            IssueSeverity.MEDIUM,
            "Style issue",
            "Missing docstring",
            "utils.py"
        )
        
        high_security = self.system.create_issue(
            IssueType.SECURITY_VULNERABILITY,
            IssueSeverity.HIGH,
            "Security vulnerability",
            "Potential XSS",
            "frontend/component.tsx"
        )
        
        # Critical blocking should have highest priority
        self.assertGreater(critical_blocking.priority_score, high_security.priority_score)
        self.assertGreater(high_security.priority_score, medium_style.priority_score)
    
    def test_fix_suggestion_generation(self):
        """Test fix suggestion generation"""
        # Test auto-fixable issue
        unused_import_issue = self.system.create_issue(
            IssueType.UNUSED_IMPORT,
            IssueSeverity.LOW,
            "Unused import",
            "Import 'os' is not used",
            "test.py",
            line_number=1
        )
        
        self.assertTrue(len(unused_import_issue.fix_suggestions) > 0)
        self.assertTrue(any(fix.auto_fixable for fix in unused_import_issue.fix_suggestions))
        
        # Test security issue
        security_issue = self.system.create_issue(
            IssueType.SECURITY_VULNERABILITY,
            IssueSeverity.HIGH,
            "SQL injection",
            "Potential SQL injection",
            "api.py"
        )
        
        self.assertTrue(len(security_issue.fix_suggestions) > 0)
        self.assertFalse(all(fix.auto_fixable for fix in security_issue.fix_suggestions))
    
    def test_report_generation(self):
        """Test report generation in different formats"""
        # Create sample issues
        issues = [
            self.system.create_issue(
                IssueType.SYNTAX_ERROR,
                IssueSeverity.CRITICAL,
                "Syntax error",
                "Missing colon",
                "main.py",
                line_number=10
            ),
            self.system.create_issue(
                IssueType.UNUSED_IMPORT,
                IssueSeverity.LOW,
                "Unused import",
                "Import not used",
                "utils.py",
                line_number=1
            ),
            self.system.create_issue(
                IssueType.UBUNTU_COMPATIBILITY,
                IssueSeverity.HIGH,
                "Ubuntu incompatibility",
                "Using yum command",
                "deploy.sh",
                line_number=5
            )
        ]
        
        # Test different report formats
        formats = ["summary", "detailed", "json", "csv", "markdown"]
        
        for format_type in formats:
            report = self.report_generator.generate_report(issues, format_type)
            self.assertIsInstance(report, str)
            self.assertGreater(len(report), 0)
            
            if format_type == "json":
                # Validate JSON format
                try:
                    json.loads(report)
                except json.JSONDecodeError:
                    self.fail(f"Invalid JSON in {format_type} report")
    
    def test_issue_filtering(self):
        """Test issue filtering functionality"""
        issues = [
            self.system.create_issue(
                IssueType.SYNTAX_ERROR,
                IssueSeverity.CRITICAL,
                "Critical syntax error",
                "Cannot compile",
                "main.py"
            ),
            self.system.create_issue(
                IssueType.STYLE_ISSUE,
                IssueSeverity.LOW,
                "Style issue",
                "Missing docstring",
                "utils.py"
            ),
            self.system.create_issue(
                IssueType.UBUNTU_COMPATIBILITY,
                IssueSeverity.HIGH,
                "Ubuntu issue",
                "Incompatible command",
                "deploy.sh"
            )
        ]
        
        # Test severity filtering
        critical_issues = self.system.filter_issues(issues, severity=IssueSeverity.CRITICAL)
        self.assertEqual(len(critical_issues), 1)
        self.assertEqual(critical_issues[0].severity, IssueSeverity.CRITICAL)
        
        # Test type filtering
        style_issues = self.system.filter_issues(issues, issue_type=IssueType.STYLE_ISSUE)
        self.assertEqual(len(style_issues), 1)
        self.assertEqual(style_issues[0].type, IssueType.STYLE_ISSUE)
        
        # Test file pattern filtering
        python_issues = self.system.filter_issues(issues, file_pattern="*.py")
        self.assertEqual(len(python_issues), 2)
    
    def test_priority_issue_selection(self):
        """Test priority issue selection"""
        issues = [
            self.system.create_issue(
                IssueType.SYNTAX_ERROR,
                IssueSeverity.CRITICAL,
                "Critical error",
                "Cannot compile",
                "main.py"
            ),
            self.system.create_issue(
                IssueType.STYLE_ISSUE,
                IssueSeverity.LOW,
                "Style issue",
                "Minor formatting",
                "utils.py"
            ),
            self.system.create_issue(
                IssueType.SECURITY_VULNERABILITY,
                IssueSeverity.HIGH,
                "Security issue",
                "Potential vulnerability",
                "api.py"
            )
        ]
        
        # Get top priority issues
        top_issues = self.system.get_priority_issues(issues, limit=2)
        self.assertEqual(len(top_issues), 2)
        
        # Should be sorted by priority score (highest first)
        self.assertGreaterEqual(top_issues[0].priority_score, top_issues[1].priority_score)
        
        # Critical issue should be first
        self.assertEqual(top_issues[0].severity, IssueSeverity.CRITICAL)
    
    def test_ubuntu_specific_issues(self):
        """Test Ubuntu-specific issue identification"""
        issues = [
            self.system.create_issue(
                IssueType.UBUNTU_COMPATIBILITY,
                IssueSeverity.HIGH,
                "Ubuntu compatibility",
                "Using yum command",
                "deploy.sh"
            ),
            self.system.create_issue(
                IssueType.SYNTAX_ERROR,
                IssueSeverity.CRITICAL,
                "Syntax error",
                "Missing colon",
                "main.py"
            )
        ]
        
        ubuntu_issues = self.system.get_ubuntu_specific_issues(issues)
        self.assertEqual(len(ubuntu_issues), 1)
        self.assertTrue(ubuntu_issues[0].impact.ubuntu_specific)
    
    def test_auto_fixable_issues(self):
        """Test auto-fixable issue identification"""
        issues = [
            self.system.create_issue(
                IssueType.UNUSED_IMPORT,
                IssueSeverity.LOW,
                "Unused import",
                "Import not used",
                "test.py"
            ),
            self.system.create_issue(
                IssueType.SECURITY_VULNERABILITY,
                IssueSeverity.HIGH,
                "Security issue",
                "Manual fix required",
                "api.py"
            )
        ]
        
        auto_fixable = self.system.get_auto_fixable_issues(issues)
        self.assertEqual(len(auto_fixable), 1)
        self.assertTrue(any(fix.auto_fixable for fix in auto_fixable[0].fix_suggestions))
    
    def test_blocking_issues(self):
        """Test blocking issue identification"""
        issues = [
            self.system.create_issue(
                IssueType.SYNTAX_ERROR,
                IssueSeverity.CRITICAL,
                "Syntax error",
                "Cannot compile",
                "main.py"
            ),
            self.system.create_issue(
                IssueType.STYLE_ISSUE,
                IssueSeverity.LOW,
                "Style issue",
                "Minor formatting",
                "utils.py"
            )
        ]
        
        blocking_issues = self.system.get_blocking_issues(issues)
        self.assertEqual(len(blocking_issues), 1)
        self.assertTrue(blocking_issues[0].impact.deployment_blocking)


class TestIssueIntegration(unittest.TestCase):
    """Test cases for issue integration system"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.collector = IssueCollector(self.temp_dir)
        self.reporter = IntegratedIssueReporter(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_legacy_issue_conversion(self):
        """Test conversion of legacy issue formats"""
        # Mock legacy issue (dictionary format)
        legacy_issue = {
            'type': 'syntax_error',
            'severity': 'critical',
            'file_path': 'test.py',
            'line_number': 42,
            'description': 'Missing colon in if statement',
            'ubuntu_specific': True,
            'auto_fixable': False
        }
        
        converted = self.collector._convert_legacy_issue(legacy_issue, "test_tool")
        
        self.assertIsInstance(converted, AnalysisIssue)
        self.assertEqual(converted.type, IssueType.SYNTAX_ERROR)
        self.assertEqual(converted.severity, IssueSeverity.CRITICAL)
        self.assertEqual(converted.location.file_path, 'test.py')
        self.assertEqual(converted.location.line_number, 42)
        self.assertEqual(converted.tool, "test_tool")
        self.assertIn('ubuntu_specific', converted.tags)
    
    @patch('issue_reporting_integration.HAS_PYTHON_ANALYZER', True)
    def test_issue_collection_mock(self):
        """Test issue collection with mocked analyzers"""
        # This test would require mocking the actual analyzers
        # For now, we'll test the structure
        
        # Test that collector methods exist and return lists
        methods = [
            'collect_python_issues',
            'collect_typescript_issues',
            'collect_docker_issues',
            'collect_security_issues',
            'collect_ubuntu_compatibility_issues',
            'collect_code_quality_issues',
            'collect_performance_issues'
        ]
        
        for method_name in methods:
            self.assertTrue(hasattr(self.collector, method_name))
            method = getattr(self.collector, method_name)
            self.assertTrue(callable(method))
    
    def test_comprehensive_report_generation(self):
        """Test comprehensive report generation"""
        # Create sample issues
        sample_issues = [
            self.collector.reporting_system.create_issue(
                IssueType.SYNTAX_ERROR,
                IssueSeverity.CRITICAL,
                "Test syntax error",
                "Missing colon",
                "test.py",
                line_number=1,
                tool="test"
            ),
            self.collector.reporting_system.create_issue(
                IssueType.UBUNTU_COMPATIBILITY,
                IssueSeverity.HIGH,
                "Ubuntu compatibility issue",
                "Using yum command",
                "deploy.sh",
                line_number=5,
                tool="test"
            )
        ]
        
        # Generate reports
        reports = self.collector.reporting_system.generate_comprehensive_report(
            sample_issues, self.temp_dir
        )
        
        # Verify reports were generated
        self.assertIsInstance(reports, dict)
        self.assertGreater(len(reports), 0)
        
        # Verify files exist
        for format_type, filepath in reports.items():
            self.assertTrue(os.path.exists(filepath))
            
            # Verify file has content
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertGreater(len(content), 0)


def run_comprehensive_test():
    """Run comprehensive test of the issue reporting system"""
    print("Running comprehensive issue reporting system tests...")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIssueReportingSystem))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIssueIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    return result.wasSuccessful()


def demo_issue_reporting_system():
    """Demonstrate the issue reporting system with sample data"""
    print("Demonstrating Issue Reporting System...")
    print("=" * 50)
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize system
        system = ComprehensiveIssueReportingSystem(temp_dir)
        
        # Create sample issues
        sample_issues = [
            system.create_issue(
                IssueType.SYNTAX_ERROR,
                IssueSeverity.CRITICAL,
                "Python syntax error in main application",
                "Missing colon after if statement on line 42",
                "backend/app.py",
                line_number=42,
                tool="python_analyzer",
                code_snippet="if condition\n    print('hello')"
            ),
            system.create_issue(
                IssueType.UBUNTU_COMPATIBILITY,
                IssueSeverity.HIGH,
                "Ubuntu incompatible package manager command",
                "Using 'yum install' instead of 'apt-get install' in deployment script",
                "scripts/deploy.sh",
                line_number=15,
                tool="deployment_analyzer"
            ),
            system.create_issue(
                IssueType.UNUSED_IMPORT,
                IssueSeverity.LOW,
                "Unused React import in component",
                "Import 'useState' from 'react' is declared but not used",
                "frontend/src/components/Header.tsx",
                line_number=3,
                tool="typescript_analyzer"
            ),
            system.create_issue(
                IssueType.SECURITY_VULNERABILITY,
                IssueSeverity.HIGH,
                "Potential SQL injection vulnerability",
                "User input is directly concatenated into SQL query without sanitization",
                "backend/api/auth.py",
                line_number=67,
                tool="security_scanner",
                code_snippet="query = f\"SELECT * FROM users WHERE username = '{username}'\""
            ),
            system.create_issue(
                IssueType.PERFORMANCE_ISSUE,
                IssueSeverity.MEDIUM,
                "Large bundle size detected",
                "JavaScript bundle size exceeds 500KB threshold",
                "frontend/dist/main.js",
                tool="bundle_analyzer"
            )
        ]
        
        print(f"Created {len(sample_issues)} sample issues")
        
        # Generate reports
        reports = system.generate_comprehensive_report(sample_issues, temp_dir)
        
        print(f"\nGenerated {len(reports)} report files:")
        for format_type, filepath in reports.items():
            print(f"  {format_type}: {filepath}")
        
        # Display summary report
        summary_report = system.report_generator.generate_report(sample_issues, "summary")
        print("\n" + "="*60)
        print("SUMMARY REPORT")
        print("="*60)
        print(summary_report)
        
        # Show priority issues
        priority_issues = system.get_priority_issues(sample_issues, 3)
        print("\nTOP 3 PRIORITY ISSUES:")
        print("-" * 30)
        for i, issue in enumerate(priority_issues, 1):
            print(f"{i}. [{issue.severity.label.upper()}] {issue.title}")
            print(f"   Priority Score: {issue.priority_score:.1f}")
            print(f"   File: {issue.location.file_path}")
            if issue.fix_suggestions:
                print(f"   Fix: {issue.fix_suggestions[0].description}")
            print()
        
        # Show Ubuntu-specific issues
        ubuntu_issues = system.get_ubuntu_specific_issues(sample_issues)
        if ubuntu_issues:
            print(f"UBUNTU COMPATIBILITY ISSUES ({len(ubuntu_issues)}):")
            print("-" * 35)
            for issue in ubuntu_issues:
                print(f"- {issue.title}")
                print(f"  File: {issue.location.file_path}")
                print()
        
        # Show auto-fixable issues
        auto_fixable = system.get_auto_fixable_issues(sample_issues)
        if auto_fixable:
            print(f"AUTO-FIXABLE ISSUES ({len(auto_fixable)}):")
            print("-" * 25)
            for issue in auto_fixable:
                print(f"- {issue.title}")
                for fix in issue.fix_suggestions:
                    if fix.auto_fixable:
                        print(f"  Fix: {fix.description}")
                        if fix.fix_command:
                            print(f"  Command: {fix.fix_command}")
                print()
        
        print("Demo completed successfully!")
        
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Issue Reporting System")
    parser.add_argument("--demo", action="store_true", help="Run demonstration")
    parser.add_argument("--test", action="store_true", help="Run unit tests")
    
    args = parser.parse_args()
    
    if args.demo:
        demo_issue_reporting_system()
    elif args.test:
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)
    else:
        # Run both by default
        print("Running unit tests...")
        success = run_comprehensive_test()
        
        if success:
            print("\nRunning demonstration...")
            demo_issue_reporting_system()
        
        sys.exit(0 if success else 1)