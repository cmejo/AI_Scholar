#!/usr/bin/env python3
"""
Demo script for comprehensive issue reporting system

This script demonstrates the issue reporting system by creating sample issues
and generating comprehensive reports in all formats.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add the scripts directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from issue_reporting_system import (
    ComprehensiveIssueReportingSystem,
    IssueType,
    IssueSeverity
)


def create_sample_issues(system):
    """Create a comprehensive set of sample issues for demonstration"""
    sample_issues = []
    
    # Critical blocking issues
    sample_issues.append(system.create_issue(
        issue_type=IssueType.SYNTAX_ERROR,
        severity=IssueSeverity.CRITICAL,
        title="Python syntax error in main application",
        description="Missing colon after if statement on line 42. This prevents the application from starting.",
        file_path="backend/app.py",
        line_number=42,
        tool="python_analyzer",
        code_snippet="if condition\n    print('hello')"
    ))
    
    sample_issues.append(system.create_issue(
        issue_type=IssueType.COMPILATION_ERROR,
        severity=IssueSeverity.CRITICAL,
        title="TypeScript compilation error",
        description="Cannot find module 'react-router-dom'. This prevents the frontend from building.",
        file_path="frontend/src/App.tsx",
        line_number=5,
        tool="typescript_analyzer"
    ))
    
    # High severity security issues
    sample_issues.append(system.create_issue(
        issue_type=IssueType.SECURITY_VULNERABILITY,
        severity=IssueSeverity.HIGH,
        title="Potential SQL injection vulnerability",
        description="User input is directly concatenated into SQL query without sanitization in authentication endpoint.",
        file_path="backend/api/auth.py",
        line_number=67,
        tool="security_scanner",
        code_snippet="query = f\"SELECT * FROM users WHERE username = '{username}'\""
    ))
    
    sample_issues.append(system.create_issue(
        issue_type=IssueType.DEPENDENCY_VULNERABILITY,
        severity=IssueSeverity.HIGH,
        title="Vulnerable dependency detected",
        description="Package 'requests' version 2.25.1 has known security vulnerabilities (CVE-2023-32681).",
        file_path="backend/requirements.txt",
        line_number=15,
        tool="security_scanner"
    ))
    
    # Ubuntu compatibility issues
    sample_issues.append(system.create_issue(
        issue_type=IssueType.UBUNTU_COMPATIBILITY,
        severity=IssueSeverity.HIGH,
        title="Ubuntu incompatible package manager command",
        description="Using 'yum install' instead of 'apt-get install' in deployment script. This will fail on Ubuntu servers.",
        file_path="scripts/deploy.sh",
        line_number=15,
        tool="deployment_analyzer"
    ))
    
    sample_issues.append(system.create_issue(
        issue_type=IssueType.DOCKERFILE_ISSUE,
        severity=IssueSeverity.MEDIUM,
        title="Dockerfile uses non-Ubuntu base image",
        description="Using CentOS base image which may cause compatibility issues on Ubuntu servers.",
        file_path="Dockerfile.backend",
        line_number=1,
        tool="docker_validator"
    ))
    
    # Performance issues
    sample_issues.append(system.create_issue(
        issue_type=IssueType.BUNDLE_SIZE_ISSUE,
        severity=IssueSeverity.MEDIUM,
        title="Large JavaScript bundle size",
        description="Main JavaScript bundle size (750KB) exceeds recommended threshold of 500KB.",
        file_path="frontend/dist/main.js",
        tool="bundle_analyzer"
    ))
    
    sample_issues.append(system.create_issue(
        issue_type=IssueType.SQL_PERFORMANCE_ISSUE,
        severity=IssueSeverity.MEDIUM,
        title="Inefficient database query",
        description="SELECT * query without WHERE clause may cause performance issues with large datasets.",
        file_path="backend/services/user_service.py",
        line_number=45,
        tool="database_analyzer",
        code_snippet="SELECT * FROM users ORDER BY created_at DESC"
    ))
    
    # Code quality issues
    sample_issues.append(system.create_issue(
        issue_type=IssueType.UNUSED_IMPORT,
        severity=IssueSeverity.LOW,
        title="Unused React import",
        description="Import 'useState' from 'react' is declared but not used in component.",
        file_path="frontend/src/components/Header.tsx",
        line_number=3,
        tool="typescript_analyzer"
    ))
    
    sample_issues.append(system.create_issue(
        issue_type=IssueType.STYLE_ISSUE,
        severity=IssueSeverity.LOW,
        title="Code formatting inconsistency",
        description="Line exceeds maximum length of 88 characters (current: 95).",
        file_path="backend/models/user.py",
        line_number=23,
        tool="code_quality_analyzer"
    ))
    
    sample_issues.append(system.create_issue(
        issue_type=IssueType.TYPE_ERROR,
        severity=IssueSeverity.MEDIUM,
        title="Missing type annotation",
        description="Function 'process_data' is missing return type annotation.",
        file_path="backend/utils/data_processor.py",
        line_number=12,
        tool="type_checker"
    ))
    
    sample_issues.append(system.create_issue(
        issue_type=IssueType.ACCESSIBILITY_ISSUE,
        severity=IssueSeverity.MEDIUM,
        title="Missing alt text for image",
        description="Image element is missing alt attribute for screen readers.",
        file_path="frontend/src/components/UserProfile.tsx",
        line_number=28,
        tool="accessibility_checker"
    ))
    
    # Configuration issues
    sample_issues.append(system.create_issue(
        issue_type=IssueType.ENVIRONMENT_CONFIG_ISSUE,
        severity=IssueSeverity.MEDIUM,
        title="Hardcoded secret in environment file",
        description="Database password is hardcoded in .env file instead of using secure secret management.",
        file_path=".env",
        line_number=8,
        tool="config_analyzer"
    ))
    
    sample_issues.append(system.create_issue(
        issue_type=IssueType.DOCKER_COMPOSE_ISSUE,
        severity=IssueSeverity.LOW,
        title="Missing health check in docker-compose",
        description="Service 'backend' is missing health check configuration.",
        file_path="docker-compose.yml",
        line_number=25,
        tool="docker_validator"
    ))
    
    # Documentation issues
    sample_issues.append(system.create_issue(
        issue_type=IssueType.DOCUMENTATION_ISSUE,
        severity=IssueSeverity.LOW,
        title="Missing function docstring",
        description="Public function 'authenticate_user' is missing docstring documentation.",
        file_path="backend/services/auth_service.py",
        line_number=34,
        tool="documentation_checker"
    ))
    
    return sample_issues


def demonstrate_filtering_and_analysis(system, issues):
    """Demonstrate filtering and analysis capabilities"""
    print("\n" + "="*60)
    print("FILTERING AND ANALYSIS DEMONSTRATION")
    print("="*60)
    
    # Show different filtering options
    critical_issues = system.filter_issues(issues, severity=IssueSeverity.CRITICAL)
    print(f"Critical Issues: {len(critical_issues)}")
    for issue in critical_issues:
        print(f"  - {issue.title}")
    
    security_issues = system.filter_issues(issues, issue_type=IssueType.SECURITY_VULNERABILITY)
    print(f"\nSecurity Issues: {len(security_issues)}")
    for issue in security_issues:
        print(f"  - {issue.title}")
    
    python_issues = system.filter_issues(issues, file_pattern="backend/*.py")
    print(f"\nPython Backend Issues: {len(python_issues)}")
    for issue in python_issues[:3]:  # Show first 3
        print(f"  - {issue.title}")
    
    # Show special categories
    ubuntu_issues = system.get_ubuntu_specific_issues(issues)
    print(f"\nUbuntu Compatibility Issues: {len(ubuntu_issues)}")
    for issue in ubuntu_issues:
        print(f"  - {issue.title} (Priority: {issue.priority_score:.1f})")
    
    auto_fixable = system.get_auto_fixable_issues(issues)
    print(f"\nAuto-fixable Issues: {len(auto_fixable)}")
    for issue in auto_fixable[:5]:  # Show first 5
        print(f"  - {issue.title}")
        for fix in issue.fix_suggestions:
            if fix.auto_fixable:
                print(f"    Fix: {fix.description}")
                break
    
    blocking_issues = system.get_blocking_issues(issues)
    print(f"\nDeployment Blocking Issues: {len(blocking_issues)}")
    for issue in blocking_issues:
        print(f"  - {issue.title} (Severity: {issue.severity.label})")


def demonstrate_report_formats(system, issues, output_dir):
    """Demonstrate different report formats"""
    print("\n" + "="*60)
    print("REPORT FORMAT DEMONSTRATION")
    print("="*60)
    
    formats = ["summary", "detailed", "json", "csv", "markdown"]
    
    for format_type in formats:
        print(f"\n{format_type.upper()} REPORT SAMPLE:")
        print("-" * (len(format_type) + 15))
        
        report = system.report_generator.generate_report(issues, format_type)
        
        if format_type == "json":
            # Pretty print JSON sample
            try:
                data = json.loads(report)
                print(f"Total Issues: {data['metadata']['total_issues']}")
                print(f"Critical: {data['summary']['by_severity'].get('critical', 0)}")
                print(f"High: {data['summary']['by_severity'].get('high', 0)}")
                print(f"Ubuntu Issues: {data['summary']['ubuntu_specific_count']}")
                print(f"Auto-fixable: {data['summary']['auto_fixable_count']}")
            except:
                print("JSON format generated successfully")
        elif format_type == "csv":
            lines = report.split('\n')
            print(f"CSV Headers: {lines[0] if lines else 'N/A'}")
            print(f"Data Rows: {len(lines) - 1}")
        elif format_type in ["summary", "detailed", "markdown"]:
            # Show first few lines
            lines = report.split('\n')
            for line in lines[:10]:
                print(line)
            if len(lines) > 10:
                print(f"... ({len(lines) - 10} more lines)")


def main():
    """Main demonstration function"""
    print("COMPREHENSIVE ISSUE REPORTING SYSTEM DEMONSTRATION")
    print("=" * 60)
    
    # Create temporary directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Demo output directory: {temp_dir}")
        
        # Initialize system
        system = ComprehensiveIssueReportingSystem(temp_dir)
        
        # Create comprehensive sample issues
        print("\nCreating sample issues...")
        issues = create_sample_issues(system)
        print(f"Created {len(issues)} sample issues")
        
        # Show issue distribution
        severity_counts = {}
        category_counts = {}
        type_counts = {}
        
        for issue in issues:
            severity_counts[issue.severity.label] = severity_counts.get(issue.severity.label, 0) + 1
            category_counts[issue.category.value] = category_counts.get(issue.category.value, 0) + 1
            type_counts[issue.type.value] = type_counts.get(issue.type.value, 0) + 1
        
        print(f"\nIssue Distribution:")
        print(f"By Severity: {dict(sorted(severity_counts.items()))}")
        print(f"By Category: {dict(sorted(category_counts.items()))}")
        
        # Generate comprehensive reports
        print(f"\nGenerating comprehensive reports...")
        reports = system.generate_comprehensive_report(issues, temp_dir)
        
        print(f"Generated {len(reports)} report files:")
        for format_type, filepath in reports.items():
            file_size = os.path.getsize(filepath)
            print(f"  {format_type}: {filepath} ({file_size} bytes)")
        
        # Show top priority issues
        priority_issues = system.get_priority_issues(issues, 5)
        print(f"\nTOP 5 PRIORITY ISSUES:")
        print("-" * 25)
        for i, issue in enumerate(priority_issues, 1):
            print(f"{i}. [{issue.severity.label.upper()}] {issue.title}")
            print(f"   Priority Score: {issue.priority_score:.1f}")
            print(f"   File: {issue.location.file_path}")
            print(f"   Impact: {'Blocking' if issue.impact.deployment_blocking else 'Non-blocking'}")
            if issue.fix_suggestions:
                print(f"   Fix: {issue.fix_suggestions[0].description}")
            print()
        
        # Demonstrate filtering and analysis
        demonstrate_filtering_and_analysis(system, issues)
        
        # Demonstrate report formats
        demonstrate_report_formats(system, issues, temp_dir)
        
        # Show actionable recommendations
        print("\n" + "="*60)
        print("ACTIONABLE RECOMMENDATIONS")
        print("="*60)
        
        blocking_count = len(system.get_blocking_issues(issues))
        security_count = len([i for i in issues if i.impact.security_risk])
        ubuntu_count = len(system.get_ubuntu_specific_issues(issues))
        auto_fixable_count = len(system.get_auto_fixable_issues(issues))
        
        print(f"IMMEDIATE ACTIONS REQUIRED:")
        if blocking_count > 0:
            print(f"🚨 Fix {blocking_count} deployment-blocking issues first")
        if security_count > 0:
            print(f"🔒 Address {security_count} security vulnerabilities")
        if ubuntu_count > 0:
            print(f"🐧 Resolve {ubuntu_count} Ubuntu compatibility issues")
        if auto_fixable_count > 0:
            print(f"🔧 {auto_fixable_count} issues can be automatically fixed")
        
        print(f"\nRECOMMENDED WORKFLOW:")
        print("1. Fix critical and high severity issues first")
        print("2. Address deployment-blocking issues")
        print("3. Resolve security vulnerabilities")
        print("4. Fix Ubuntu compatibility issues")
        print("5. Apply automatic fixes for code quality issues")
        print("6. Run comprehensive tests after fixes")
        
        print(f"\nDemonstration completed successfully!")
        print(f"Check the generated reports in: {temp_dir}")


if __name__ == "__main__":
    main()