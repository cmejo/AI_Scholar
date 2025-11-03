#!/usr/bin/env python3
"""
Error Recovery Report Script for automated scheduling.

Generates comprehensive error recovery and performance reports.
"""

import asyncio
import argparse
import logging
import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from .error_recovery_manager import ErrorRecoveryManager
from .automated_scheduler import AutomatedScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for error recovery report."""
    parser = argparse.ArgumentParser(description="Generate error recovery and performance report")
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='/var/log/multi_instance_arxiv/reports',
        help='Output directory for reports'
    )
    
    parser.add_argument(
        '--format',
        choices=['json', 'text', 'both'],
        default='both',
        help='Report format'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting error recovery report generation")
    
    try:
        # Create output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        error_recovery = ErrorRecoveryManager()
        scheduler = AutomatedScheduler()
        
        # Generate timestamp for report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Collect error recovery statistics
        error_stats = error_recovery.get_error_statistics()
        
        # Collect execution statistics
        execution_stats = scheduler.get_execution_statistics()
        
        # Create comprehensive report
        report = {
            'report_type': 'weekly_error_recovery_report',
            'generated_at': datetime.now().isoformat(),
            'period': 'last_7_days',
            'error_recovery': error_stats,
            'execution_performance': execution_stats,
            'summary': {
                'total_errors': error_stats.get('total_errors', 0),
                'recent_errors': error_stats.get('recent_errors_last_hour', 0),
                'total_executions': execution_stats.get('total_executions', 0),
                'success_rate': execution_stats.get('success_rate', 0),
                'recent_success_rate': execution_stats.get('recent_success_rate_24h', 0)
            },
            'recommendations': generate_recommendations(error_stats, execution_stats)
        }
        
        # Save JSON report
        if args.format in ['json', 'both']:
            json_file = output_dir / f"error_recovery_report_{timestamp}.json"
            with open(json_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"JSON report saved to: {json_file}")
        
        # Save text report
        if args.format in ['text', 'both']:
            text_file = output_dir / f"error_recovery_report_{timestamp}.txt"
            with open(text_file, 'w') as f:
                write_text_report(f, report)
            logger.info(f"Text report saved to: {text_file}")
        
        # Export detailed error recovery report
        detailed_report_file = output_dir / f"detailed_error_recovery_{timestamp}.json"
        success = error_recovery.export_error_report(detailed_report_file)
        if success:
            logger.info(f"Detailed error recovery report saved to: {detailed_report_file}")
        
        # Export execution report
        execution_report_file = output_dir / f"execution_report_{timestamp}.json"
        success = scheduler.export_execution_report(execution_report_file)
        if success:
            logger.info(f"Execution report saved to: {execution_report_file}")
        
        # Print summary to console
        print_report_summary(report)
        
        logger.info("Error recovery report generation completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error recovery report generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def generate_recommendations(error_stats: dict, execution_stats: dict) -> list:
    """Generate recommendations based on error and execution statistics."""
    recommendations = []
    
    # Error rate recommendations
    total_errors = error_stats.get('total_errors', 0)
    recent_errors = error_stats.get('recent_errors_last_hour', 0)
    
    if recent_errors > 10:
        recommendations.append("High recent error rate detected - investigate immediate causes")
    
    if total_errors > 100:
        recommendations.append("High total error count - review error patterns and implement preventive measures")
    
    # Success rate recommendations
    success_rate = execution_stats.get('success_rate', 100)
    recent_success_rate = execution_stats.get('recent_success_rate_24h', 100)
    
    if success_rate < 90:
        recommendations.append("Overall success rate below 90% - review and improve error handling")
    
    if recent_success_rate < 80:
        recommendations.append("Recent success rate critically low - immediate attention required")
    
    # Circuit breaker recommendations
    circuit_breakers = error_stats.get('circuit_breakers', {})
    open_breakers = [name for name, info in circuit_breakers.items() if info.get('is_open', False)]
    
    if open_breakers:
        recommendations.append(f"Circuit breakers open for: {', '.join(open_breakers)} - investigate root causes")
    
    # Error type recommendations
    error_types = error_stats.get('error_types', {})
    if error_types:
        most_common_error = max(error_types.items(), key=lambda x: x[1])
        if most_common_error[1] > 10:
            recommendations.append(f"Most common error '{most_common_error[0]}' occurs frequently - implement specific handling")
    
    if not recommendations:
        recommendations.append("System performance is healthy - continue monitoring")
    
    return recommendations


def write_text_report(file, report: dict) -> None:
    """Write a human-readable text report."""
    file.write("Multi-Instance ArXiv System - Weekly Error Recovery Report\n")
    file.write("=" * 60 + "\n\n")
    
    file.write(f"Generated: {report['generated_at']}\n")
    file.write(f"Period: {report['period']}\n\n")
    
    # Summary section
    summary = report['summary']
    file.write("SUMMARY\n")
    file.write("-" * 20 + "\n")
    file.write(f"Total Errors: {summary['total_errors']}\n")
    file.write(f"Recent Errors (1h): {summary['recent_errors']}\n")
    file.write(f"Total Executions: {summary['total_executions']}\n")
    file.write(f"Success Rate: {summary['success_rate']:.1f}%\n")
    file.write(f"Recent Success Rate (24h): {summary['recent_success_rate']:.1f}%\n\n")
    
    # Error recovery section
    error_recovery = report['error_recovery']
    file.write("ERROR RECOVERY STATISTICS\n")
    file.write("-" * 30 + "\n")
    
    error_types = error_recovery.get('error_types', {})
    if error_types:
        file.write("Most Common Errors:\n")
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]:
            file.write(f"  - {error_type}: {count}\n")
        file.write("\n")
    
    # Circuit breakers
    circuit_breakers = error_recovery.get('circuit_breakers', {})
    if circuit_breakers:
        file.write("Circuit Breaker Status:\n")
        for name, info in circuit_breakers.items():
            status = "OPEN" if info.get('is_open', False) else "CLOSED"
            file.write(f"  - {name}: {status} (failures: {info.get('failure_count', 0)})\n")
        file.write("\n")
    
    # Recommendations
    recommendations = report['recommendations']
    file.write("RECOMMENDATIONS\n")
    file.write("-" * 20 + "\n")
    for i, rec in enumerate(recommendations, 1):
        file.write(f"{i}. {rec}\n")
    file.write("\n")
    
    # Execution performance
    execution = report['execution_performance']
    file.write("EXECUTION PERFORMANCE\n")
    file.write("-" * 25 + "\n")
    file.write(f"Average Duration: {execution.get('average_duration_seconds', 0):.1f} seconds\n")
    file.write(f"Recent Executions (24h): {execution.get('recent_executions_24h', 0)}\n")
    
    operation_stats = execution.get('operation_statistics', {})
    if operation_stats:
        file.write("\nOperation Statistics:\n")
        for op_name, stats in operation_stats.items():
            file.write(f"  - {op_name}: {stats['successful']}/{stats['total']} ({stats['success_rate']:.1f}%)\n")


def print_report_summary(report: dict) -> None:
    """Print a summary of the report to console."""
    print("\n" + "=" * 60)
    print("ERROR RECOVERY REPORT SUMMARY")
    print("=" * 60)
    
    summary = report['summary']
    print(f"Total Errors: {summary['total_errors']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Recent Success Rate (24h): {summary['recent_success_rate']:.1f}%")
    
    print("\nTop Recommendations:")
    for i, rec in enumerate(report['recommendations'][:3], 1):
        print(f"{i}. {rec}")
    
    print("=" * 60 + "\n")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)