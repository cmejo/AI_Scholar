#!/usr/bin/env python3
"""
Code Quality Analysis Runner

This script runs comprehensive code quality and technical debt analysis
on the AI Scholar codebase and generates detailed reports.

Usage:
    python run_code_quality_analysis.py [options]

Requirements: 6.1, 6.2, 6.3, 6.4
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from code_quality_analyzer import CodeQualityAnalyzer

def generate_html_report(results: dict, output_file: str):
    """Generate an HTML report from analysis results"""
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Quality Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .metric { background: #e9ecef; padding: 15px; border-radius: 5px; text-align: center; }
        .metric h3 { margin: 0 0 10px 0; color: #495057; }
        .metric .value { font-size: 2em; font-weight: bold; color: #007bff; }
        .section { margin-bottom: 30px; }
        .section h2 { color: #343a40; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .issue { background: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin-bottom: 10px; }
        .issue.critical { border-left-color: #dc3545; }
        .issue.high { border-left-color: #fd7e14; }
        .issue.medium { border-left-color: #ffc107; }
        .issue.low { border-left-color: #28a745; }
        .issue-header { font-weight: bold; color: #495057; }
        .issue-description { margin: 5px 0; }
        .issue-recommendation { font-style: italic; color: #6c757d; }
        .file-path { font-family: monospace; background: #e9ecef; padding: 2px 5px; border-radius: 3px; }
        .recommendations { background: #d1ecf1; border: 1px solid #bee5eb; padding: 20px; border-radius: 5px; }
        .recommendations ul { margin: 10px 0; }
        .auto-fixable { color: #28a745; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Code Quality Analysis Report</h1>
        <p><strong>Generated:</strong> {timestamp}</p>
        <p><strong>Root Directory:</strong> {root_directory}</p>
    </div>

    <div class="summary">
        <div class="metric">
            <h3>Total Issues</h3>
            <div class="value">{total_issues}</div>
        </div>
        <div class="metric">
            <h3>Critical Issues</h3>
            <div class="value">{critical_count}</div>
        </div>
        <div class="metric">
            <h3>Auto-fixable</h3>
            <div class="value">{auto_fixable}</div>
        </div>
        <div class="metric">
            <h3>Documentation Gaps</h3>
            <div class="value">{doc_gaps}</div>
        </div>
    </div>

    <div class="recommendations">
        <h2>Key Recommendations</h2>
        <ul>
            {recommendations_html}
        </ul>
    </div>

    <div class="section">
        <h2>Code Structure Issues ({structure_count})</h2>
        {structure_issues_html}
    </div>

    <div class="section">
        <h2>Dependency Issues ({dependency_count})</h2>
        {dependency_issues_html}
    </div>

    <div class="section">
        <h2>Error Handling Issues ({error_handling_count})</h2>
        {error_handling_issues_html}
    </div>

    <div class="section">
        <h2>Documentation Gaps ({documentation_count})</h2>
        {documentation_gaps_html}
    </div>
</body>
</html>
"""
    
    # Extract data from results
    summary = results.get("analysis_summary", {})
    
    # Generate HTML for issues
    def format_issues(issues, issue_type="quality"):
        if not issues:
            return "<p>No issues found.</p>"
        
        html = ""
        for issue in issues:
            if issue_type == "quality":
                severity = issue.get("severity", "low")
                auto_fix = " <span class='auto-fixable'>(Auto-fixable)</span>" if issue.get("auto_fixable") else ""
                html += f"""
                <div class="issue {severity}">
                    <div class="issue-header">{issue.get('type', 'Unknown')} - {severity.title()}{auto_fix}</div>
                    <div class="file-path">{issue.get('file_path', 'Unknown file')}</div>
                    {f"<div>Line {issue['line_number']}</div>" if issue.get('line_number') else ""}
                    <div class="issue-description">{issue.get('description', 'No description')}</div>
                    <div class="issue-recommendation">💡 {issue.get('recommendation', 'No recommendation')}</div>
                </div>
                """
            elif issue_type == "dependency":
                html += f"""
                <div class="issue medium">
                    <div class="issue-header">{issue.get('issue_type', 'Unknown')} - {issue.get('package_name', 'Unknown package')}</div>
                    <div class="file-path">{issue.get('file_path', 'Unknown file')}</div>
                    <div class="issue-description">Current: {issue.get('current_version', 'Unknown')} | Latest: {issue.get('latest_version', 'Unknown')}</div>
                    <div class="issue-recommendation">💡 {issue.get('recommendation', 'No recommendation')}</div>
                </div>
                """
            elif issue_type == "documentation":
                html += f"""
                <div class="issue low">
                    <div class="issue-header">{issue.get('gap_type', 'Unknown')} - {issue.get('function_name', issue.get('class_name', 'Module'))}</div>
                    <div class="file-path">{issue.get('file_path', 'Unknown file')}</div>
                    <div class="issue-description">{issue.get('description', 'No description')}</div>
                    <div class="issue-recommendation">💡 {issue.get('recommendation', 'No recommendation')}</div>
                </div>
                """
        return html
    
    # Format recommendations
    recommendations_html = ""
    for rec in results.get("recommendations", []):
        recommendations_html += f"<li>{rec}</li>"
    
    # Fill template
    html_content = html_template.format(
        timestamp=results.get("timestamp", "Unknown"),
        root_directory=results.get("root_directory", "Unknown"),
        total_issues=summary.get("total_issues", 0),
        critical_count=summary.get("severity_breakdown", {}).get("critical", 0),
        auto_fixable=summary.get("auto_fixable_issues", 0),
        doc_gaps=summary.get("documentation_gaps", 0),
        recommendations_html=recommendations_html,
        structure_count=summary.get("code_structure_issues", 0),
        structure_issues_html=format_issues(results.get("code_structure_issues", []), "quality"),
        dependency_count=summary.get("dependency_issues", 0),
        dependency_issues_html=format_issues(results.get("dependency_issues", []), "dependency"),
        error_handling_count=summary.get("error_handling_issues", 0),
        error_handling_issues_html=format_issues(results.get("error_handling_issues", []), "quality"),
        documentation_count=summary.get("documentation_gaps", 0),
        documentation_gaps_html=format_issues(results.get("documentation_gaps", []), "documentation")
    )
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

def print_summary(results: dict):
    """Print a summary of the analysis results"""
    print("\n" + "="*60)
    print("CODE QUALITY ANALYSIS SUMMARY")
    print("="*60)
    
    summary = results.get("analysis_summary", {})
    
    print(f"📊 Total Issues Found: {summary.get('total_issues', 0)}")
    print(f"🏗️  Code Structure Issues: {summary.get('code_structure_issues', 0)}")
    print(f"📦 Dependency Issues: {summary.get('dependency_issues', 0)}")
    print(f"⚠️  Error Handling Issues: {summary.get('error_handling_issues', 0)}")
    print(f"📝 Documentation Gaps: {summary.get('documentation_gaps', 0)}")
    
    severity_breakdown = summary.get("severity_breakdown", {})
    print(f"\n🚨 Severity Breakdown:")
    print(f"   Critical: {severity_breakdown.get('critical', 0)}")
    print(f"   High: {severity_breakdown.get('high', 0)}")
    print(f"   Medium: {severity_breakdown.get('medium', 0)}")
    print(f"   Low: {severity_breakdown.get('low', 0)}")
    
    print(f"\n🔧 Auto-fixable Issues: {summary.get('auto_fixable_issues', 0)}")
    
    recommendations = results.get("recommendations", [])
    if recommendations:
        print(f"\n💡 Key Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    
    print("\n" + "="*60)

def main():
    """Main function to run code quality analysis"""
    parser = argparse.ArgumentParser(
        description="Run comprehensive code quality and technical debt analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Analyze current directory
    python run_code_quality_analysis.py
    
    # Analyze specific directory with JSON output
    python run_code_quality_analysis.py -d /path/to/project -o results.json
    
    # Generate HTML report
    python run_code_quality_analysis.py --html-report report.html
    
    # Verbose output with all formats
    python run_code_quality_analysis.py -v --json results.json --html-report report.html
        """
    )
    
    parser.add_argument(
        "--directory", "-d", 
        default=".", 
        help="Directory to analyze (default: current directory)"
    )
    parser.add_argument(
        "--json", "-j", 
        help="Output JSON results to file"
    )
    parser.add_argument(
        "--html-report", 
        help="Generate HTML report file"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Verbose output"
    )
    parser.add_argument(
        "--quiet", "-q", 
        action="store_true", 
        help="Quiet mode - minimal output"
    )
    
    args = parser.parse_args()
    
    # Validate directory
    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist")
        sys.exit(1)
    
    # Run analysis
    print(f"🔍 Starting code quality analysis of: {os.path.abspath(args.directory)}")
    print("This may take a few minutes...")
    
    try:
        analyzer = CodeQualityAnalyzer()
        results = analyzer.analyze_codebase(args.directory)
        
        # Check for analysis errors
        if "error" in results:
            print(f"❌ Analysis failed: {results['error']}")
            sys.exit(1)
        
        # Print summary unless quiet mode
        if not args.quiet:
            print_summary(results)
        
        # Save JSON results
        if args.json:
            with open(args.json, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"📄 JSON results saved to: {args.json}")
        
        # Generate HTML report
        if args.html_report:
            generate_html_report(results, args.html_report)
            print(f"📊 HTML report generated: {args.html_report}")
        
        # Print detailed results if verbose and no output files
        if args.verbose and not args.json and not args.html_report:
            print("\n" + "="*60)
            print("DETAILED RESULTS")
            print("="*60)
            print(json.dumps(results, indent=2))
        
        # Determine exit code based on critical issues
        critical_issues = results.get("analysis_summary", {}).get("severity_breakdown", {}).get("critical", 0)
        if critical_issues > 0:
            print(f"\n⚠️  Found {critical_issues} critical issues that should be addressed immediately")
            sys.exit(1)
        else:
            print("\n✅ Analysis completed successfully")
            sys.exit(0)
    
    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error during analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()