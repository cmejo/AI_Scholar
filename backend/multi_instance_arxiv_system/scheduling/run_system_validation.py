#!/usr/bin/env python3
"""
System Validation Script for automated scheduling.

Performs daily system validation and readiness checks.
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

from .automated_scheduler import AutomatedScheduler
from .health_checker import HealthChecker
from .conflict_resolver import ConflictResolver

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for system validation."""
    parser = argparse.ArgumentParser(description="Validate system readiness and health")
    
    parser.add_argument(
        '--output-file',
        type=str,
        help='Output file for validation results (JSON format)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--exit-on-failure',
        action='store_true',
        help='Exit with non-zero code if validation fails'
    )
    
    parser.add_argument(
        '--include-performance',
        action='store_true',
        help='Include performance metrics in validation'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting system validation")
    
    try:
        validation_results = {
            'validation_type': 'daily_system_validation',
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {},
            'recommendations': []
        }
        
        # Initialize components
        scheduler = AutomatedScheduler()
        health_checker = HealthChecker()
        conflict_resolver = ConflictResolver()
        
        # 1. Validate scheduling setup
        logger.info("Validating scheduling setup...")
        is_valid, issues = await scheduler.validate_scheduling_setup()
        validation_results['checks']['scheduling_setup'] = {
            'status': 'healthy' if is_valid else 'critical',
            'issues': issues
        }
        
        if not is_valid:
            validation_results['overall_status'] = 'critical'
            validation_results['recommendations'].extend([
                f"Fix scheduling issue: {issue}" for issue in issues
            ])
        
        # 2. Run health check
        logger.info("Running comprehensive health check...")
        health_status = await health_checker.run_comprehensive_health_check()
        
        validation_results['checks']['system_health'] = {
            'status': health_status.overall_status,
            'check_results': [result.to_dict() for result in health_status.check_results]
        }
        
        if health_status.overall_status == 'critical':
            validation_results['overall_status'] = 'critical'
        elif health_status.overall_status == 'warning' and validation_results['overall_status'] != 'critical':
            validation_results['overall_status'] = 'warning'
        
        # Check if system is ready for updates
        is_ready, blocking_issues = health_checker.is_system_ready_for_update(health_status)
        validation_results['checks']['update_readiness'] = {
            'status': 'healthy' if is_ready else 'critical',
            'ready': is_ready,
            'blocking_issues': blocking_issues
        }
        
        if not is_ready:
            validation_results['overall_status'] = 'critical'
            validation_results['recommendations'].extend([
                f"Resolve blocking issue: {issue}" for issue in blocking_issues
            ])
        
        # 3. Check for conflicts
        logger.info("Checking for scheduling conflicts...")
        conflicts = await conflict_resolver.detect_conflicts("validation_check")
        
        critical_conflicts = [c for c in conflicts if c.severity.value == 'critical']
        validation_results['checks']['conflicts'] = {
            'status': 'critical' if critical_conflicts else 'healthy' if not conflicts else 'warning',
            'total_conflicts': len(conflicts),
            'critical_conflicts': len(critical_conflicts),
            'conflicts': [c.to_dict() for c in conflicts]
        }
        
        if critical_conflicts:
            validation_results['overall_status'] = 'critical'
            validation_results['recommendations'].append(
                f"Resolve {len(critical_conflicts)} critical scheduling conflicts"
            )
        
        # 4. Performance metrics (if requested)
        if args.include_performance:
            logger.info("Collecting performance metrics...")
            
            # Get execution statistics
            execution_stats = scheduler.get_execution_statistics()
            validation_results['checks']['performance'] = {
                'status': 'healthy' if execution_stats.get('success_rate', 100) >= 90 else 'warning',
                'statistics': execution_stats
            }
            
            if execution_stats.get('success_rate', 100) < 80:
                validation_results['overall_status'] = 'warning'
                validation_results['recommendations'].append(
                    "Low success rate detected - investigate execution failures"
                )
            
            # Get conflict resolution statistics
            conflict_stats = conflict_resolver.get_conflict_statistics()
            validation_results['checks']['conflict_resolution_performance'] = {
                'status': 'healthy' if conflict_stats.get('success_rate', 100) >= 90 else 'warning',
                'statistics': conflict_stats
            }
        
        # 5. Storage validation
        logger.info("Validating storage...")
        storage_issues = []
        
        # Check critical directories
        critical_dirs = [
            "/datapool/aischolar",
            "/var/log/multi_instance_arxiv",
            "/tmp/multi_instance_locks"
        ]
        
        for dir_path in critical_dirs:
            path = Path(dir_path)
            if not path.exists():
                storage_issues.append(f"Critical directory missing: {dir_path}")
            elif not os.access(path, os.W_OK):
                storage_issues.append(f"No write permission for: {dir_path}")
        
        # Check disk space
        import shutil
        try:
            usage = shutil.disk_usage("/")
            percent_used = (usage.used / usage.total) * 100
            
            if percent_used > 95:
                storage_issues.append(f"Critical disk space: {percent_used:.1f}% used")
            elif percent_used > 85:
                storage_issues.append(f"High disk usage: {percent_used:.1f}% used")
                
        except Exception as e:
            storage_issues.append(f"Cannot check disk usage: {e}")
        
        validation_results['checks']['storage'] = {
            'status': 'critical' if any('Critical' in issue for issue in storage_issues) else 
                     'warning' if storage_issues else 'healthy',
            'issues': storage_issues
        }
        
        if storage_issues:
            if any('Critical' in issue for issue in storage_issues):
                validation_results['overall_status'] = 'critical'
            elif validation_results['overall_status'] == 'healthy':
                validation_results['overall_status'] = 'warning'
            
            validation_results['recommendations'].extend([
                f"Fix storage issue: {issue}" for issue in storage_issues
            ])
        
        # Generate final recommendations
        if validation_results['overall_status'] == 'healthy':
            validation_results['recommendations'].append("System is healthy and ready for operations")
        elif validation_results['overall_status'] == 'warning':
            validation_results['recommendations'].insert(0, "System has warnings - monitor closely")
        else:
            validation_results['recommendations'].insert(0, "System has critical issues - immediate attention required")
        
        # Print summary
        print_validation_summary(validation_results)
        
        # Save results to file if requested
        if args.output_file:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(validation_results, f, indent=2, default=str)
            
            logger.info(f"Validation results saved to {output_path}")
        
        # Exit with appropriate code
        if args.exit_on_failure and validation_results['overall_status'] == 'critical':
            logger.error("System validation failed - exiting with error code")
            return 1
        
        logger.info(f"System validation completed - status: {validation_results['overall_status']}")
        return 0
        
    except Exception as e:
        logger.error(f"System validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def print_validation_summary(results: dict) -> None:
    """Print a summary of validation results."""
    print("\n" + "=" * 60)
    print("SYSTEM VALIDATION SUMMARY")
    print("=" * 60)
    
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Validation Time: {results['timestamp']}")
    
    print("\nCheck Results:")
    for check_name, check_result in results['checks'].items():
        status = check_result['status'].upper()
        symbol = "✓" if status == "HEALTHY" else "⚠" if status == "WARNING" else "✗"
        print(f"  {symbol} {check_name.replace('_', ' ').title()}: {status}")
    
    print("\nRecommendations:")
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"  {i}. {rec}")
    
    print("=" * 60 + "\n")


if __name__ == "__main__":
    import os
    exit_code = asyncio.run(main())
    sys.exit(exit_code)