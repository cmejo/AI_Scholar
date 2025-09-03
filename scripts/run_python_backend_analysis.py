#!/usr/bin/env python3
"""
Comprehensive Python Backend Analysis Runner
Integrates the Python backend analyzer with the main codebase analysis system.
"""

import json
import logging
import sys
import time
from pathlib import Path
from python_backend_analyzer import PythonBackendAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('python_backend_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def generate_analysis_report(results: dict, output_path: Path):
    """Generate a comprehensive analysis report."""
    
    report_lines = [
        "# Python Backend Code Analysis Report",
        f"Generated on: {results['analysis_timestamp']}",
        "",
        "## Summary",
        f"- **Backend Path**: {results['backend_path']}",
        f"- **Python Files Discovered**: {results['total_python_files']}",
        f"- **Total Files Analyzed**: {results['total_files_analyzed']}",
        f"- **Total Issues Found**: {results['total_issues_found']}",
        "",
        "## Issue Breakdown",
        ""
    ]
    
    # Add issue breakdown
    breakdown = results['issue_breakdown']
    
    report_lines.extend([
        "### By Issue Type",
        ""
    ])
    
    for issue_type, count in breakdown['by_type'].items():
        report_lines.append(f"- **{issue_type.replace('_', ' ').title()}**: {count}")
    
    report_lines.extend([
        "",
        "### By Severity",
        ""
    ])
    
    for severity, count in breakdown['by_severity'].items():
        report_lines.append(f"- **{severity.title()}**: {count}")
    
    report_lines.extend([
        "",
        "### By Analysis Tool",
        ""
    ])
    
    for tool, count in breakdown['by_tool'].items():
        report_lines.append(f"- **{tool.replace('_', ' ').title()}**: {count}")
    
    # Add critical issues section
    critical_issues = []
    high_issues = []
    
    for result in results['results']:
        for issue in result['issues']:
            if issue['severity'] == 'IssueSeverity.CRITICAL':
                critical_issues.append(issue)
            elif issue['severity'] == 'IssueSeverity.HIGH':
                high_issues.append(issue)
    
    if critical_issues:
        report_lines.extend([
            "",
            "## Critical Issues (Immediate Attention Required)",
            ""
        ])
        
        for i, issue in enumerate(critical_issues[:10], 1):  # Show first 10
            report_lines.extend([
                f"### {i}. {issue['description']}",
                f"- **File**: {issue['file_path']}",
                f"- **Line**: {issue['line_number'] or 'N/A'}",
                f"- **Tool**: {issue['tool']}",
                f"- **Recommendation**: {issue['recommendation']}",
                ""
            ])
        
        if len(critical_issues) > 10:
            report_lines.append(f"... and {len(critical_issues) - 10} more critical issues")
    
    if high_issues:
        report_lines.extend([
            "",
            "## High Priority Issues",
            ""
        ])
        
        for i, issue in enumerate(high_issues[:5], 1):  # Show first 5
            report_lines.extend([
                f"### {i}. {issue['description']}",
                f"- **File**: {issue['file_path']}",
                f"- **Line**: {issue['line_number'] or 'N/A'}",
                f"- **Tool**: {issue['tool']}",
                f"- **Recommendation**: {issue['recommendation']}",
                ""
            ])
        
        if len(high_issues) > 5:
            report_lines.append(f"... and {len(high_issues) - 5} more high priority issues")
    
    # Add recommendations section
    report_lines.extend([
        "",
        "## Recommendations",
        "",
        "### Immediate Actions",
        "1. **Fix Critical Issues**: Address all critical syntax errors and security vulnerabilities",
        "2. **Resolve Import Errors**: Fix missing imports and dependency issues",
        "3. **Security Review**: Review and fix SQL injection vulnerabilities",
        "",
        "### Medium-term Improvements",
        "1. **Type Annotations**: Add missing type annotations for better code quality",
        "2. **Error Handling**: Improve error handling in service integration points",
        "3. **SQL Optimization**: Review and optimize SQL queries for performance",
        "",
        "### Long-term Maintenance",
        "1. **Code Quality**: Establish coding standards and automated quality checks",
        "2. **Dependency Management**: Regular dependency updates and vulnerability scanning",
        "3. **Documentation**: Improve code documentation and type hints",
        "",
        "## Ubuntu Compatibility Notes",
        "",
        f"- **Ubuntu-specific Issues**: {sum(1 for result in results['results'] for issue in result['issues'] if issue.get('ubuntu_specific', False))}",
        "- Most issues are platform-independent but should be tested on Ubuntu",
        "- Pay special attention to file path handling and dependency versions",
        "",
        "---",
        "",
        f"*Report generated by Python Backend Analyzer v1.0*"
    ])
    
    # Write report
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Analysis report saved to {output_path}")


def main():
    """Main function to run Python backend analysis."""
    logger.info("Starting comprehensive Python backend analysis...")
    
    # Check if backend directory exists
    backend_path = Path("backend")
    if not backend_path.exists():
        logger.error("Backend directory not found!")
        sys.exit(1)
    
    try:
        # Initialize analyzer
        analyzer = PythonBackendAnalyzer(backend_path)
        
        # Run full analysis
        results = analyzer.run_full_analysis()
        
        # Save detailed results
        results_file = Path("python_backend_analysis_detailed.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Detailed results saved to {results_file}")
        
        # Generate human-readable report
        report_file = Path("python_backend_analysis_report.md")
        generate_analysis_report(results, report_file)
        
        # Print summary
        print("\n" + "="*60)
        print("PYTHON BACKEND ANALYSIS SUMMARY")
        print("="*60)
        print(f"Files analyzed: {results['total_files_analyzed']}")
        print(f"Issues found: {results['total_issues_found']}")
        print("\nIssue breakdown by severity:")
        
        for severity, count in results['issue_breakdown']['by_severity'].items():
            print(f"  {severity.title()}: {count}")
        
        print(f"\nDetailed results: {results_file}")
        print(f"Human-readable report: {report_file}")
        
        # Return appropriate exit code
        critical_count = results['issue_breakdown']['by_severity'].get('critical', 0)
        high_count = results['issue_breakdown']['by_severity'].get('high', 0)
        
        if critical_count > 0:
            logger.warning(f"Found {critical_count} critical issues that need immediate attention!")
            return 2
        elif high_count > 0:
            logger.warning(f"Found {high_count} high priority issues that should be addressed soon.")
            return 1
        else:
            logger.info("No critical or high priority issues found.")
            return 0
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)