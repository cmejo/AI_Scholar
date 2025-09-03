#!/usr/bin/env python3
"""
Performance Analysis Runner

This script runs comprehensive performance analysis on the AI Scholar codebase
to identify memory leaks, database performance issues, CPU bottlenecks,
and caching optimization opportunities.

Requirements: 5.1, 5.2, 5.3, 5.4
"""

import os
import sys
import argparse
import json
from datetime import datetime
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from performance_analyzer import PerformanceAnalyzer

def main():
    """Main function to run performance analysis"""
    parser = argparse.ArgumentParser(
        description="Performance Analysis and Optimization Detector for AI Scholar",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_performance_analysis.py ../backend
  python run_performance_analysis.py ../backend --output performance_results.json
  python run_performance_analysis.py . --verbose
  python run_performance_analysis.py ../backend --focus memory,database
        """
    )
    
    parser.add_argument(
        "directory",
        help="Directory to analyze (e.g., ../backend, ../frontend, .)"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="performance_analysis_results.json",
        help="Output file for detailed results (default: performance_analysis_results.json)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output with detailed issue descriptions"
    )
    
    parser.add_argument(
        "--focus",
        choices=["memory", "database", "cpu", "caching", "all"],
        default="all",
        help="Focus analysis on specific areas (default: all)"
    )
    
    parser.add_argument(
        "--severity",
        choices=["critical", "high", "medium", "low", "all"],
        default="all",
        help="Filter results by minimum severity level (default: all)"
    )
    
    parser.add_argument(
        "--format",
        choices=["json", "text", "both"],
        default="both",
        help="Output format (default: both)"
    )
    
    args = parser.parse_args()
    
    # Validate directory
    if not os.path.exists(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist")
        sys.exit(1)
    
    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a directory")
        sys.exit(1)
    
    print("AI Scholar Performance Analysis")
    print("=" * 50)
    print(f"Analyzing directory: {os.path.abspath(args.directory)}")
    print(f"Focus areas: {args.focus}")
    print(f"Minimum severity: {args.severity}")
    print(f"Output format: {args.format}")
    print()
    
    # Run analysis
    analyzer = PerformanceAnalyzer()
    
    try:
        results = analyzer.analyze_directory(args.directory)
        
        # Filter results by focus area
        if args.focus != "all":
            results = filter_by_focus(results, args.focus)
        
        # Filter results by severity
        if args.severity != "all":
            results = filter_by_severity(results, args.severity)
        
        # Save results
        if args.format in ["json", "both"]:
            analyzer.save_results(results, args.output)
            print(f"Detailed results saved to: {args.output}")
        
        # Print summary
        if args.format in ["text", "both"]:
            analyzer.print_summary(results)
            
            if args.verbose:
                print_detailed_results(results)
        
        # Generate recommendations
        print_recommendations(results)
        
        # Exit with appropriate code
        total_critical = sum(
            1 for issue_list in [results.memory_leaks, results.database_issues, 
                               results.cpu_bottlenecks, results.caching_issues]
            for issue in issue_list
            if getattr(issue, 'severity', 'low') == 'critical'
        )
        
        if total_critical > 0:
            print(f"\nWARNING: Found {total_critical} critical performance issues!")
            sys.exit(1)
        else:
            print("\nPerformance analysis completed successfully.")
            sys.exit(0)
            
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def filter_by_focus(results, focus_area):
    """Filter results by focus area"""
    from performance_analyzer import PerformanceAnalysisResult
    
    if focus_area == "memory":
        return PerformanceAnalysisResult(
            timestamp=results.timestamp,
            memory_leaks=results.memory_leaks,
            database_issues=[],
            cpu_bottlenecks=[],
            caching_issues=[],
            summary=results.summary
        )
    elif focus_area == "database":
        return PerformanceAnalysisResult(
            timestamp=results.timestamp,
            memory_leaks=[],
            database_issues=results.database_issues,
            cpu_bottlenecks=[],
            caching_issues=[],
            summary=results.summary
        )
    elif focus_area == "cpu":
        return PerformanceAnalysisResult(
            timestamp=results.timestamp,
            memory_leaks=[],
            database_issues=[],
            cpu_bottlenecks=results.cpu_bottlenecks,
            caching_issues=[],
            summary=results.summary
        )
    elif focus_area == "caching":
        return PerformanceAnalysisResult(
            timestamp=results.timestamp,
            memory_leaks=[],
            database_issues=[],
            cpu_bottlenecks=[],
            caching_issues=results.caching_issues,
            summary=results.summary
        )
    
    return results

def filter_by_severity(results, min_severity):
    """Filter results by minimum severity level"""
    from performance_analyzer import PerformanceAnalysisResult
    
    severity_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    min_level = severity_levels.get(min_severity, 0)
    
    def filter_issues(issues):
        return [
            issue for issue in issues
            if severity_levels.get(getattr(issue, 'severity', 'low'), 0) >= min_level
        ]
    
    return PerformanceAnalysisResult(
        timestamp=results.timestamp,
        memory_leaks=filter_issues(results.memory_leaks),
        database_issues=filter_issues(results.database_issues),
        cpu_bottlenecks=filter_issues(results.cpu_bottlenecks),
        caching_issues=filter_issues(results.caching_issues),
        summary=results.summary
    )

def print_detailed_results(results):
    """Print detailed results for verbose output"""
    print("\n" + "="*80)
    print("DETAILED PERFORMANCE ISSUES")
    print("="*80)
    
    # Memory Leaks
    if results.memory_leaks:
        print("\nMEMORY LEAK ISSUES:")
        print("-" * 40)
        for i, issue in enumerate(results.memory_leaks, 1):
            print(f"{i}. {issue.description}")
            print(f"   File: {issue.file_path}")
            if issue.line_number:
                print(f"   Line: {issue.line_number}")
            print(f"   Severity: {issue.severity.upper()}")
            print(f"   Type: {issue.leak_type}")
            print(f"   Memory Growth Rate: {issue.memory_growth_rate}")
            print("   Recommendations:")
            for rec in issue.recommendations:
                print(f"     - {rec}")
            print()
    
    # Database Issues
    if results.database_issues:
        print("\nDATABASE PERFORMANCE ISSUES:")
        print("-" * 40)
        for i, issue in enumerate(results.database_issues, 1):
            print(f"{i}. {issue.description}")
            print(f"   File: {issue.file_path}")
            if issue.line_number:
                print(f"   Line: {issue.line_number}")
            print(f"   Severity: {issue.severity.upper()}")
            print(f"   Query Type: {issue.query_type}")
            if issue.execution_time > 0:
                print(f"   Execution Time: {issue.execution_time}s")
            print("   Optimization Suggestions:")
            for suggestion in issue.optimization_suggestions:
                print(f"     - {suggestion}")
            print()
    
    # CPU Bottlenecks
    if results.cpu_bottlenecks:
        print("\nCPU BOTTLENECK ISSUES:")
        print("-" * 40)
        for i, issue in enumerate(results.cpu_bottlenecks, 1):
            print(f"{i}. {issue.description}")
            print(f"   File: {issue.file_path}")
            if issue.line_number:
                print(f"   Line: {issue.line_number}")
            print(f"   Severity: {issue.severity.upper()}")
            print(f"   Function: {issue.function_name}")
            if issue.cpu_usage_percent > 0:
                print(f"   CPU Usage: {issue.cpu_usage_percent}%")
            if issue.execution_time > 0:
                print(f"   Execution Time: {issue.execution_time}s")
            print("   Optimization Suggestions:")
            for suggestion in issue.optimization_suggestions:
                print(f"     - {suggestion}")
            print()
    
    # Caching Issues
    if results.caching_issues:
        print("\nCACHING OPTIMIZATION ISSUES:")
        print("-" * 40)
        for i, issue in enumerate(results.caching_issues, 1):
            print(f"{i}. {issue.description}")
            print(f"   File: {issue.file_path}")
            print(f"   Severity: {issue.severity.upper()}")
            print(f"   Cache Type: {issue.cache_type}")
            print(f"   Hit Rate: {issue.hit_rate}%")
            print(f"   Miss Rate: {issue.miss_rate}%")
            print("   Optimization Suggestions:")
            for suggestion in issue.optimization_suggestions:
                print(f"     - {suggestion}")
            print()

def print_recommendations(results):
    """Print prioritized recommendations"""
    print("\n" + "="*80)
    print("PRIORITIZED RECOMMENDATIONS")
    print("="*80)
    
    # Collect all issues with priorities
    all_issues = []
    
    for issue in results.memory_leaks:
        priority = calculate_priority(issue.severity, "memory")
        all_issues.append((priority, "Memory Leak", issue.description, issue.recommendations))
    
    for issue in results.database_issues:
        priority = calculate_priority(issue.severity, "database")
        all_issues.append((priority, "Database", issue.description, issue.optimization_suggestions))
    
    for issue in results.cpu_bottlenecks:
        priority = calculate_priority(issue.severity, "cpu")
        all_issues.append((priority, "CPU", issue.description, issue.optimization_suggestions))
    
    for issue in results.caching_issues:
        priority = calculate_priority(issue.severity, "caching")
        all_issues.append((priority, "Caching", issue.description, issue.optimization_suggestions))
    
    # Sort by priority (higher first)
    all_issues.sort(key=lambda x: x[0], reverse=True)
    
    # Print top 10 recommendations
    print("\nTop 10 Priority Issues:")
    for i, (priority, category, description, recommendations) in enumerate(all_issues[:10], 1):
        print(f"\n{i}. [{category}] {description}")
        print(f"   Priority Score: {priority}")
        if recommendations:
            print(f"   Key Recommendation: {recommendations[0]}")
    
    # Print category-specific recommendations
    print("\n\nCategory-Specific Recommendations:")
    
    if results.memory_leaks:
        print("\nMemory Management:")
        print("- Use context managers (with statements) for all resource management")
        print("- Implement proper cleanup in __del__ methods")
        print("- Monitor memory usage in production")
        print("- Use memory profiling tools during development")
    
    if results.database_issues:
        print("\nDatabase Optimization:")
        print("- Add indexes for frequently queried columns")
        print("- Implement query result caching")
        print("- Use connection pooling")
        print("- Monitor slow query logs")
    
    if results.cpu_bottlenecks:
        print("\nCPU Performance:")
        print("- Use async/await for I/O-bound operations")
        print("- Implement algorithmic optimizations")
        print("- Consider multiprocessing for CPU-intensive tasks")
        print("- Profile code to identify actual bottlenecks")
    
    if results.caching_issues:
        print("\nCaching Strategy:")
        print("- Implement multi-level caching (memory + Redis)")
        print("- Use appropriate cache TTL values")
        print("- Implement cache warming strategies")
        print("- Monitor cache hit rates")

def calculate_priority(severity, category):
    """Calculate priority score for an issue"""
    severity_scores = {"critical": 100, "high": 75, "medium": 50, "low": 25}
    category_multipliers = {"memory": 1.2, "database": 1.1, "cpu": 1.0, "caching": 0.9}
    
    base_score = severity_scores.get(severity, 25)
    multiplier = category_multipliers.get(category, 1.0)
    
    return base_score * multiplier

if __name__ == "__main__":
    main()