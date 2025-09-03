#!/usr/bin/env python3
"""
TypeScript/React Frontend Analysis Runner

This script runs comprehensive analysis of the TypeScript/React frontend code
including compilation errors, component issues, bundle optimization, and
accessibility compliance checking.

Requirements: 2.1, 2.2, 2.3
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typescript_frontend_analyzer import TypeScriptFrontendAnalyzer, IssueType, IssueSeverity

def print_analysis_header():
    """Print analysis header"""
    print("=" * 80)
    print("TypeScript/React Frontend Code Analysis")
    print("=" * 80)
    print(f"Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def print_section_header(title: str):
    """Print section header"""
    print(f"\n{'-' * 60}")
    print(f"{title}")
    print(f"{'-' * 60}")

def print_issues(issues, title: str):
    """Print issues in a formatted way"""
    if not issues:
        print(f"✓ No {title.lower()} found")
        return
    
    print(f"Found {len(issues)} {title.lower()}:")
    
    # Group issues by severity
    by_severity = {}
    for issue in issues:
        severity = issue.severity.value
        if severity not in by_severity:
            by_severity[severity] = []
        by_severity[severity].append(issue)
    
    # Print by severity (critical first)
    severity_order = ['critical', 'high', 'medium', 'low', 'info']
    
    for severity in severity_order:
        if severity in by_severity:
            severity_issues = by_severity[severity]
            print(f"\n  {severity.upper()} ({len(severity_issues)} issues):")
            
            for issue in severity_issues[:10]:  # Limit to first 10 per severity
                location = ""
                if issue.line_number:
                    location = f":{issue.line_number}"
                    if issue.column_number:
                        location += f":{issue.column_number}"
                
                print(f"    • {issue.file_path}{location}")
                print(f"      {issue.description}")
                print(f"      → {issue.recommendation}")
                if issue.auto_fixable:
                    print(f"      🔧 Auto-fixable")
                print()
            
            if len(severity_issues) > 10:
                print(f"    ... and {len(severity_issues) - 10} more {severity} issues")

def print_typescript_analysis(result):
    """Print TypeScript analysis results"""
    print_section_header("TypeScript Compilation Analysis")
    
    print(f"Files analyzed: {result.total_files_analyzed}")
    print(f"Analysis success: {'✓' if result.success else '✗'}")
    
    if result.compilation_errors:
        print_issues(result.compilation_errors, "Compilation Errors")
    
    if result.type_errors:
        print_issues(result.type_errors, "Type Errors")
    
    if result.warnings:
        print_issues(result.warnings, "Warnings")

def print_react_analysis(result):
    """Print React component analysis results"""
    print_section_header("React Component Analysis")
    
    print(f"Components analyzed: {result.total_components_analyzed}")
    print(f"Analysis success: {'✓' if result.success else '✗'}")
    
    if result.unused_imports:
        print_issues(result.unused_imports, "Unused Imports")
    
    if result.component_issues:
        print_issues(result.component_issues, "Component Issues")
    
    if result.hook_issues:
        print_issues(result.hook_issues, "React Hooks Issues")

def print_bundle_analysis(result):
    """Print bundle analysis results"""
    print_section_header("Bundle Performance Analysis")
    
    print(f"Analysis success: {'✓' if result.success else '✗'}")
    
    if result.bundle_stats:
        stats = result.bundle_stats
        print(f"Total bundle size: {stats.get('total_size', 0) / 1024:.1f} KB")
        print(f"JavaScript size: {stats.get('js_size', 0) / 1024:.1f} KB")
        print(f"CSS size: {stats.get('css_size', 0) / 1024:.1f} KB")
        print(f"Asset size: {stats.get('asset_size', 0) / 1024:.1f} KB")
        print(f"Total files: {len(stats.get('files', []))}")
    
    if result.bundle_size_issues:
        print_issues(result.bundle_size_issues, "Bundle Size Issues")
    
    if result.optimization_opportunities:
        print_issues(result.optimization_opportunities, "Optimization Opportunities")
    
    if result.dependency_issues:
        print_issues(result.dependency_issues, "Dependency Issues")
    
    if result.performance_recommendations:
        print_issues(result.performance_recommendations, "Performance Recommendations")

def print_accessibility_analysis(result):
    """Print accessibility analysis results"""
    print_section_header("Accessibility Compliance Analysis")
    
    print(f"Components checked: {result.total_components_checked}")
    print(f"Analysis success: {'✓' if result.success else '✗'}")
    
    if result.accessibility_violations:
        print_issues(result.accessibility_violations, "Accessibility Violations")
    
    if result.wcag_compliance_issues:
        print_issues(result.wcag_compliance_issues, "WCAG Compliance Issues")
    
    if result.semantic_issues:
        print_issues(result.semantic_issues, "Semantic HTML Issues")

def print_summary(result):
    """Print analysis summary"""
    print_section_header("Analysis Summary")
    
    summary = result.summary
    
    print(f"Total issues found: {summary['total_issues']}")
    print(f"Critical issues: {summary['critical_issues']}")
    print(f"High priority issues: {summary['high_issues']}")
    print(f"TypeScript files analyzed: {summary['typescript_files_analyzed']}")
    print(f"React components analyzed: {summary['react_components_analyzed']}")
    print(f"Accessibility components checked: {summary['accessibility_components_checked']}")
    print(f"Bundle analysis success: {'✓' if summary['bundle_analysis_success'] else '✗'}")
    print(f"Overall analysis success: {'✓' if summary['overall_success'] else '✗'}")
    
    if summary.get('recommendations'):
        print("\nRecommendations:")
        for i, rec in enumerate(summary['recommendations'], 1):
            print(f"  {i}. {rec}")

def generate_report(result, output_file: str):
    """Generate detailed report"""
    print_section_header("Generating Detailed Report")
    
    try:
        # Convert result to dict for JSON serialization
        from dataclasses import asdict
        from enum import Enum
        
        def convert_enums(obj):
            if isinstance(obj, dict):
                return {k: convert_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enums(item) for item in obj]
            elif isinstance(obj, Enum):
                return obj.value
            else:
                return obj
        
        result_dict = convert_enums(asdict(result))
        
        # Add metadata
        result_dict['metadata'] = {
            'analysis_tool': 'TypeScript Frontend Analyzer',
            'version': '1.0.0',
            'generated_at': datetime.now().isoformat(),
            'requirements_covered': ['2.1', '2.2', '2.3']
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Detailed report saved to: {output_file}")
        
        # Generate summary report
        summary_file = output_file.replace('.json', '_summary.txt')
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("TypeScript/React Frontend Analysis Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Issues: {result.summary['total_issues']}\n")
            f.write(f"Critical Issues: {result.summary['critical_issues']}\n")
            f.write(f"High Priority Issues: {result.summary['high_issues']}\n")
            f.write(f"Overall Success: {result.summary['overall_success']}\n\n")
            
            # Issue breakdown
            f.write("Issue Breakdown:\n")
            f.write(f"- TypeScript compilation errors: {len(result.typescript_analysis.compilation_errors)}\n")
            f.write(f"- TypeScript type errors: {len(result.typescript_analysis.type_errors)}\n")
            f.write(f"- React unused imports: {len(result.react_analysis.unused_imports)}\n")
            f.write(f"- React component issues: {len(result.react_analysis.component_issues)}\n")
            f.write(f"- React hooks issues: {len(result.react_analysis.hook_issues)}\n")
            f.write(f"- Bundle size issues: {len(result.bundle_analysis.bundle_size_issues)}\n")
            f.write(f"- Accessibility violations: {len(result.accessibility_analysis.accessibility_violations)}\n")
            f.write(f"- WCAG compliance issues: {len(result.accessibility_analysis.wcag_compliance_issues)}\n\n")
            
            # Recommendations
            if result.summary.get('recommendations'):
                f.write("Recommendations:\n")
                for i, rec in enumerate(result.summary['recommendations'], 1):
                    f.write(f"{i}. {rec}\n")
        
        print(f"✓ Summary report saved to: {summary_file}")
        
    except Exception as e:
        print(f"✗ Error generating report: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Run comprehensive TypeScript/React frontend analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_typescript_frontend_analysis.py
  python run_typescript_frontend_analysis.py --output frontend_analysis.json
  python run_typescript_frontend_analysis.py --typescript-only
  python run_typescript_frontend_analysis.py --react-only
  python run_typescript_frontend_analysis.py --bundle-only
  python run_typescript_frontend_analysis.py --accessibility-only
        """
    )
    
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root directory (default: current directory)"
    )
    
    parser.add_argument(
        "--output",
        default="frontend_analysis_results.json",
        help="Output file for detailed results (default: frontend_analysis_results.json)"
    )
    
    parser.add_argument(
        "--typescript-only",
        action="store_true",
        help="Run only TypeScript compilation analysis"
    )
    
    parser.add_argument(
        "--react-only",
        action="store_true",
        help="Run only React component analysis"
    )
    
    parser.add_argument(
        "--bundle-only",
        action="store_true",
        help="Run only bundle performance analysis"
    )
    
    parser.add_argument(
        "--accessibility-only",
        action="store_true",
        help="Run only accessibility compliance analysis"
    )
    
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip generating detailed report files"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress detailed output, show only summary"
    )
    
    args = parser.parse_args()
    
    # Validate project root
    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        print(f"Error: Project root directory does not exist: {project_root}")
        return 1
    
    # Initialize analyzer
    analyzer = TypeScriptFrontendAnalyzer(str(project_root))
    
    if not args.quiet:
        print_analysis_header()
    
    try:
        # Run specific analysis or comprehensive analysis
        if args.typescript_only:
            result = analyzer.analyze_typescript_compilation()
            if not args.quiet:
                print_typescript_analysis(result)
        elif args.react_only:
            result = analyzer.analyze_react_components()
            if not args.quiet:
                print_react_analysis(result)
        elif args.bundle_only:
            result = analyzer.analyze_bundle_performance()
            if not args.quiet:
                print_bundle_analysis(result)
        elif args.accessibility_only:
            result = analyzer.analyze_accessibility_compliance()
            if not args.quiet:
                print_accessibility_analysis(result)
        else:
            # Run comprehensive analysis
            result = analyzer.run_comprehensive_analysis()
            
            if not args.quiet:
                print_typescript_analysis(result.typescript_analysis)
                print_react_analysis(result.react_analysis)
                print_bundle_analysis(result.bundle_analysis)
                print_accessibility_analysis(result.accessibility_analysis)
                print_summary(result)
            
            # Generate report
            if not args.no_report:
                generate_report(result, args.output)
        
        # Print final status
        if hasattr(result, 'summary'):
            success = result.summary.get('overall_success', False)
            total_issues = result.summary.get('total_issues', 0)
            critical_issues = result.summary.get('critical_issues', 0)
        else:
            success = getattr(result, 'success', False)
            total_issues = 1 if not success else 0
            critical_issues = 1 if not success else 0
        
        print(f"\n{'=' * 80}")
        print(f"Analysis completed: {'✓ SUCCESS' if success else '✗ ISSUES FOUND'}")
        print(f"Total issues: {total_issues}")
        if critical_issues > 0:
            print(f"Critical issues: {critical_issues} (requires immediate attention)")
        print(f"{'=' * 80}")
        
        # Return appropriate exit code
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user")
        return 130
    except Exception as e:
        print(f"\nError during analysis: {e}")
        if not args.quiet:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())