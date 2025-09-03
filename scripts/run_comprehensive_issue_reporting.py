#!/usr/bin/env python3
"""
Comprehensive Issue Reporting Runner

This script runs the comprehensive issue reporting system, collecting issues from all
available analyzers and generating detailed reports with prioritization and fix suggestions.

Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add the scripts directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from issue_reporting_integration import IntegratedIssueReporter


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Setup logging configuration"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def print_analysis_summary(result: Dict[str, Any]):
    """Print a formatted analysis summary"""
    print("\n" + "="*60)
    print("COMPREHENSIVE ISSUE ANALYSIS SUMMARY")
    print("="*60)
    
    print(f"Total Issues Found: {result['total_issues']}")
    print(f"Analysis Time: {result['execution_time']:.2f} seconds")
    print(f"Ubuntu-specific Issues: {result['ubuntu_issues']}")
    print(f"Auto-fixable Issues: {result['auto_fixable_issues']}")
    print(f"Deployment Blocking Issues: {result['blocking_issues']}")
    
    if 'summary' in result:
        summary = result['summary']
        
        print(f"\nISSUES BY SEVERITY:")
        print("-" * 20)
        for severity, count in sorted(summary.get('by_severity', {}).items()):
            print(f"  {severity.title()}: {count}")
        
        print(f"\nISSUES BY CATEGORY:")
        print("-" * 20)
        for category, count in sorted(summary.get('by_category', {}).items()):
            print(f"  {category.title()}: {count}")
        
        print(f"\nISSUES BY TOOL:")
        print("-" * 15)
        for tool, count in sorted(summary.get('by_tool', {}).items()):
            print(f"  {tool}: {count}")
        
        if summary.get('impact_analysis'):
            impact = summary['impact_analysis']
            print(f"\nIMPACT ANALYSIS:")
            print("-" * 16)
            print(f"  Deployment Blocking: {impact.get('deployment_blocking', 0)}")
            print(f"  Security Risk: {impact.get('security_risk', 0)}")
            print(f"  Performance Impact: {impact.get('performance_impact', 0)}")
            print(f"  Ubuntu Specific: {impact.get('ubuntu_specific', 0)}")
            print(f"  User Facing: {impact.get('user_facing', 0)}")
            print(f"  Core Functionality: {impact.get('core_functionality', 0)}")
    
    if result.get('priority_issues'):
        print(f"\nTOP PRIORITY ISSUES:")
        print("-" * 20)
        for i, issue in enumerate(result['priority_issues'][:10], 1):
            print(f"{i:2d}. [{issue['severity'].upper()}] {issue['title']}")
            print(f"     File: {issue['file_path']}")
            print(f"     Priority Score: {issue['priority_score']:.1f}")
    
    if result.get('reports'):
        print(f"\nGENERATED REPORTS:")
        print("-" * 18)
        for format_type, filepath in result['reports'].items():
            print(f"  {format_type.title()}: {filepath}")


def print_recommendations(result: Dict[str, Any]):
    """Print actionable recommendations based on analysis results"""
    print("\n" + "="*60)
    print("ACTIONABLE RECOMMENDATIONS")
    print("="*60)
    
    total_issues = result.get('total_issues', 0)
    blocking_issues = result.get('blocking_issues', 0)
    security_issues = result.get('summary', {}).get('impact_analysis', {}).get('security_risk', 0)
    ubuntu_issues = result.get('ubuntu_issues', 0)
    auto_fixable = result.get('auto_fixable_issues', 0)
    
    if total_issues == 0:
        print("🎉 No issues found! Your codebase looks good.")
        return
    
    print("IMMEDIATE ACTIONS:")
    print("-" * 18)
    
    if blocking_issues > 0:
        print(f"🚨 CRITICAL: Fix {blocking_issues} deployment-blocking issues first")
        print("   These prevent the application from running properly")
    
    if security_issues > 0:
        print(f"🔒 SECURITY: Address {security_issues} security vulnerabilities")
        print("   These pose potential security risks")
    
    if ubuntu_issues > 0:
        print(f"🐧 UBUNTU: Resolve {ubuntu_issues} Ubuntu compatibility issues")
        print("   These may cause problems when deploying on Ubuntu servers")
    
    if auto_fixable > 0:
        print(f"🔧 QUICK WINS: {auto_fixable} issues can be automatically fixed")
        print("   Run the auto-fix script to resolve these quickly")
    
    print(f"\nNEXT STEPS:")
    print("-" * 11)
    
    if blocking_issues > 0:
        print("1. Focus on CRITICAL and HIGH severity issues first")
        print("2. Fix deployment-blocking issues to ensure the app can run")
    
    if security_issues > 0:
        print("3. Review and fix security vulnerabilities")
        print("4. Update vulnerable dependencies")
    
    if ubuntu_issues > 0:
        print("5. Test deployment on Ubuntu environment")
        print("6. Update deployment scripts for Ubuntu compatibility")
    
    print("7. Run tests after fixing issues to ensure nothing breaks")
    print("8. Consider setting up automated quality gates in CI/CD")
    
    # Provide specific tool recommendations
    summary = result.get('summary', {})
    by_tool = summary.get('by_tool', {})
    
    if by_tool:
        print(f"\nTOOL-SPECIFIC RECOMMENDATIONS:")
        print("-" * 30)
        
        if 'python_analyzer' in by_tool:
            print("• Python: Run 'black .' and 'flake8 .' for code formatting")
        
        if 'typescript_analyzer' in by_tool:
            print("• TypeScript: Run 'npx tsc --noEmit' and 'npx eslint --fix .'")
        
        if 'docker_validator' in by_tool:
            print("• Docker: Use 'hadolint Dockerfile' and 'docker-compose config'")
        
        if 'security_scanner' in by_tool:
            print("• Security: Run 'safety check' and 'npm audit fix'")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Comprehensive Issue Reporting System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Run full analysis
  %(prog)s --output-dir ./reports            # Specify output directory
  %(prog)s --generate-fix-script              # Generate auto-fix script
  %(prog)s --format json --quiet             # JSON output only
  %(prog)s --log-level DEBUG --log-file analysis.log  # Debug logging
        """
    )
    
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root directory (default: current directory)"
    )
    
    parser.add_argument(
        "--output-dir",
        help="Output directory for reports (default: ./issue_reports)"
    )
    
    parser.add_argument(
        "--generate-fix-script",
        action="store_true",
        help="Generate automatic fix script for auto-fixable issues"
    )
    
    parser.add_argument(
        "--format",
        choices=["summary", "detailed", "json", "csv", "markdown"],
        default="summary",
        help="Primary report format to display (default: summary)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        help="Log file path (default: console only)"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress summary output, only show specified format"
    )
    
    parser.add_argument(
        "--no-recommendations",
        action="store_true",
        help="Skip actionable recommendations"
    )
    
    parser.add_argument(
        "--save-results",
        help="Save analysis results to JSON file"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize reporter
        logger.info(f"Initializing issue reporter for project: {args.project_root}")
        reporter = IntegratedIssueReporter(args.project_root)
        
        # Run comprehensive analysis
        logger.info("Starting comprehensive issue analysis...")
        start_time = time.time()
        
        result = reporter.run_comprehensive_analysis(args.output_dir)
        
        # Save results if requested
        if args.save_results:
            with open(args.save_results, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"Analysis results saved to: {args.save_results}")
        
        # Display results
        if not args.quiet:
            print_analysis_summary(result)
            
            if not args.no_recommendations:
                print_recommendations(result)
        
        # Display specific format if requested and different from summary
        if args.format != "summary" or args.quiet:
            if result['total_issues'] > 0:
                # We need to collect issues again for specific format display
                all_issues = reporter.collector.collect_all_issues()
                format_report = reporter.reporting_system.report_generator.generate_report(
                    all_issues, args.format
                )
                
                if args.quiet:
                    print(format_report)
                else:
                    print(f"\n{args.format.upper()} REPORT:")
                    print("=" * (len(args.format) + 8))
                    print(format_report)
        
        # Generate fix script if requested
        if args.generate_fix_script and result['auto_fixable_issues'] > 0:
            logger.info("Generating automatic fix script...")
            all_issues = reporter.collector.collect_all_issues()
            fix_script_path = reporter.generate_fix_script(all_issues)
            
            if not args.quiet:
                print(f"\n🔧 AUTO-FIX SCRIPT GENERATED:")
                print(f"   {fix_script_path}")
                print(f"   Run with: bash {fix_script_path}")
        
        # Determine exit code
        exit_code = 0
        if result['blocking_issues'] > 0:
            exit_code = 2  # Critical issues
        elif result['total_issues'] > 0:
            exit_code = 1  # Issues found
        
        if not args.quiet:
            if exit_code == 0:
                print(f"\n✅ Analysis completed successfully - no issues found!")
            elif exit_code == 1:
                print(f"\n⚠️  Analysis completed - {result['total_issues']} issues found")
            else:
                print(f"\n❌ Analysis completed - {result['blocking_issues']} critical issues found")
        
        logger.info(f"Analysis completed in {result['execution_time']:.2f} seconds")
        return exit_code
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        print("\n⏹️  Analysis interrupted")
        return 130
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        print(f"\n❌ Analysis failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())