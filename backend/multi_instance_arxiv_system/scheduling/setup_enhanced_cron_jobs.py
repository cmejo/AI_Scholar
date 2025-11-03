#!/usr/bin/env python3
"""
Enhanced Cron Job Setup Script with comprehensive scheduling features.

Sets up automated cron jobs with health checks, conflict resolution,
and error recovery for the multi-instance ArXiv system.
"""

import argparse
import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from .cron_scheduler import CronScheduler
from .automated_scheduler import AutomatedScheduler, SchedulingConfig
from .health_checker import HealthChecker
from .conflict_resolver import ConflictResolver
from .error_recovery_manager import ErrorRecoveryManager, RecoveryConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_enhanced_cron_jobs(scheduler: CronScheduler, args) -> bool:
    """Create enhanced cron jobs with validation and monitoring."""
    logger.info("Creating enhanced cron jobs")
    
    try:
        # Validate all schedules first
        schedules_to_validate = [
            ('monthly_update', args.monthly_schedule),
            ('health_check', args.health_check_schedule),
            ('cleanup', args.cleanup_schedule),
            ('conflict_cleanup', args.conflict_cleanup_schedule),
            ('error_report', args.error_report_schedule)
        ]
        
        for name, schedule in schedules_to_validate:
            if not scheduler.validate_schedule(schedule):
                logger.error(f"Invalid {name} schedule: {schedule}")
                return False
        
        script_dir = Path(args.script_dir)
        
        # 1. Enhanced Monthly Update Job
        success = scheduler.add_monthly_update_job(
            instance_names=[name.strip() for name in args.instances.split(',')],
            schedule=args.monthly_schedule,
            python_path=args.python_path,
            script_path=str(script_dir / "run_scheduled_monthly_update.py")
        )
        if not success:
            logger.error("Failed to add enhanced monthly update job")
            return False
        
        # 2. Health Check Job (every 6 hours by default)
        success = scheduler.add_health_check_job(
            schedule=args.health_check_schedule,
            python_path=args.python_path,
            script_path=str(script_dir / "run_health_check.py")
        )
        if not success:
            logger.error("Failed to add health check job")
            return False
        
        # 3. System Cleanup Job
        success = scheduler.add_cleanup_job(
            schedule=args.cleanup_schedule,
            python_path=args.python_path,
            script_path=str(script_dir / "run_system_cleanup.py")
        )
        if not success:
            logger.error("Failed to add cleanup job")
            return False
        
        # 4. Conflict Resolution Cleanup Job (daily)
        from .cron_scheduler import CronJobConfig
        conflict_cleanup_job = CronJobConfig(
            name="conflict_cleanup",
            schedule=args.conflict_cleanup_schedule,
            command=f"{args.python_path} {script_dir / 'run_conflict_cleanup.py'} >> /var/log/multi_instance_arxiv/conflict_cleanup.log 2>&1",
            description="Daily cleanup of stale locks and conflict resolution",
            enabled=True,
            environment_vars={
                'PYTHONPATH': str(Path(__file__).parent.parent.parent),
                'PATH': os.environ.get('PATH', ''),
                'HOME': os.environ.get('HOME', '/root')
            }
        )
        scheduler.jobs[conflict_cleanup_job.name] = conflict_cleanup_job
        
        # 5. Error Recovery Report Job (weekly)
        error_report_job = CronJobConfig(
            name="error_recovery_report",
            schedule=args.error_report_schedule,
            command=f"{args.python_path} {script_dir / 'run_error_report.py'} >> /var/log/multi_instance_arxiv/error_report.log 2>&1",
            description="Weekly error recovery and performance report",
            enabled=True,
            environment_vars={
                'PYTHONPATH': str(Path(__file__).parent.parent.parent),
                'PATH': os.environ.get('PATH', ''),
                'HOME': os.environ.get('HOME', '/root')
            }
        )
        scheduler.jobs[error_report_job.name] = error_report_job
        
        # 6. System Validation Job (daily)
        validation_job = CronJobConfig(
            name="system_validation",
            schedule="0 1 * * *",  # Daily at 1 AM
            command=f"{args.python_path} {script_dir / 'run_system_validation.py'} >> /var/log/multi_instance_arxiv/validation.log 2>&1",
            description="Daily system validation and readiness check",
            enabled=True,
            environment_vars={
                'PYTHONPATH': str(Path(__file__).parent.parent.parent),
                'PATH': os.environ.get('PATH', ''),
                'HOME': os.environ.get('HOME', '/root')
            }
        )
        scheduler.jobs[validation_job.name] = validation_job
        
        logger.info("Enhanced cron jobs created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create enhanced cron jobs: {e}")
        return False


def setup_monitoring_and_alerting(args) -> bool:
    """Set up monitoring and alerting infrastructure."""
    logger.info("Setting up monitoring and alerting")
    
    try:
        # Create log directories
        log_dirs = [
            "/var/log/multi_instance_arxiv",
            "/var/log/multi_instance_arxiv/health_checks",
            "/var/log/multi_instance_arxiv/conflicts",
            "/var/log/multi_instance_arxiv/errors",
            "/var/log/multi_instance_arxiv/reports"
        ]
        
        for log_dir in log_dirs:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created log directory: {log_dir}")
        
        # Create configuration directory
        config_dir = Path("/etc/multi_instance_arxiv")
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create monitoring configuration
        monitoring_config = {
            "monitoring": {
                "enabled": True,
                "health_check_interval_hours": 6,
                "conflict_cleanup_interval_hours": 24,
                "error_report_interval_days": 7,
                "log_retention_days": 30
            },
            "alerting": {
                "enabled": args.enable_alerting,
                "email_recipients": args.alert_recipients.split(',') if args.alert_recipients else [],
                "critical_failure_immediate_alert": True,
                "health_check_failure_alert": True,
                "conflict_resolution_failure_alert": True
            },
            "thresholds": {
                "memory_warning_percent": 80,
                "memory_critical_percent": 90,
                "disk_warning_percent": 85,
                "disk_critical_percent": 95,
                "error_rate_warning_percent": 10,
                "error_rate_critical_percent": 25
            }
        }
        
        config_file = config_dir / "monitoring_config.json"
        with open(config_file, 'w') as f:
            json.dump(monitoring_config, f, indent=2)
        
        logger.info(f"Monitoring configuration saved to: {config_file}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup monitoring and alerting: {e}")
        return False


def validate_system_readiness() -> bool:
    """Validate that the system is ready for automated scheduling."""
    logger.info("Validating system readiness")
    
    try:
        # Check required directories
        required_dirs = [
            "/datapool/aischolar",
            "/tmp/multi_instance_locks",
            "/var/log/multi_instance_arxiv"
        ]
        
        for dir_path in required_dirs:
            path = Path(dir_path)
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created required directory: {dir_path}")
                except Exception as e:
                    logger.error(f"Cannot create required directory {dir_path}: {e}")
                    return False
        
        # Check Python dependencies
        required_packages = [
            'asyncio', 'aiohttp', 'aiofiles', 'psutil', 
            'requests', 'yaml', 'chromadb'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing required packages: {', '.join(missing_packages)}")
            return False
        
        # Test basic system health
        import asyncio
        
        async def test_health():
            health_checker = HealthChecker()
            health_status = await health_checker.run_comprehensive_health_check()
            return health_status.overall_status != 'critical'
        
        health_ok = asyncio.run(test_health())
        if not health_ok:
            logger.warning("System health check indicates critical issues")
            return False
        
        logger.info("System readiness validation passed")
        return True
        
    except Exception as e:
        logger.error(f"System readiness validation failed: {e}")
        return False


def main():
    """Main entry point for enhanced cron job setup."""
    parser = argparse.ArgumentParser(description="Setup enhanced cron jobs for multi-instance ArXiv system")
    
    parser.add_argument(
        '--action',
        choices=['install', 'remove', 'list', 'validate', 'test'],
        default='install',
        help='Action to perform'
    )
    
    parser.add_argument(
        '--instances',
        type=str,
        default='ai_scholar,quant_scholar',
        help='Comma-separated list of instance names'
    )
    
    parser.add_argument(
        '--monthly-schedule',
        type=str,
        default='0 2 1 * *',
        help='Cron schedule for monthly updates (default: 2 AM on 1st of each month)'
    )
    
    parser.add_argument(
        '--health-check-schedule',
        type=str,
        default='0 */6 * * *',
        help='Cron schedule for health checks (default: every 6 hours)'
    )
    
    parser.add_argument(
        '--cleanup-schedule',
        type=str,
        default='0 3 1 * *',
        help='Cron schedule for cleanup (default: 3 AM on 1st of each month)'
    )
    
    parser.add_argument(
        '--conflict-cleanup-schedule',
        type=str,
        default='0 4 * * *',
        help='Cron schedule for conflict cleanup (default: 4 AM daily)'
    )
    
    parser.add_argument(
        '--error-report-schedule',
        type=str,
        default='0 5 * * 0',
        help='Cron schedule for error reports (default: 5 AM on Sundays)'
    )
    
    parser.add_argument(
        '--python-path',
        type=str,
        default=sys.executable,
        help='Path to Python executable'
    )
    
    parser.add_argument(
        '--script-dir',
        type=str,
        default=str(Path(__file__).parent),
        help='Directory containing scheduling scripts'
    )
    
    parser.add_argument(
        '--config-file',
        type=str,
        help='Custom cron configuration file path'
    )
    
    parser.add_argument(
        '--enable-alerting',
        action='store_true',
        help='Enable email alerting for failures'
    )
    
    parser.add_argument(
        '--alert-recipients',
        type=str,
        help='Comma-separated list of email addresses for alerts'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force installation even if validation fails'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Enhanced cron job setup - Action: {args.action}")
    
    try:
        # Initialize cron scheduler
        scheduler = CronScheduler(args.config_file)
        
        if args.action == 'install':
            return install_enhanced_cron_jobs(scheduler, args)
        elif args.action == 'remove':
            return remove_cron_jobs(scheduler, args)
        elif args.action == 'list':
            return list_cron_jobs(scheduler, args)
        elif args.action == 'validate':
            return validate_cron_setup(scheduler, args)
        elif args.action == 'test':
            return test_cron_setup(scheduler, args)
        else:
            logger.error(f"Unknown action: {args.action}")
            return 1
            
    except Exception as e:
        logger.error(f"Enhanced cron job setup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def install_enhanced_cron_jobs(scheduler: CronScheduler, args) -> int:
    """Install enhanced cron jobs with validation."""
    logger.info("Installing enhanced cron jobs")
    
    try:
        # Validate system readiness unless forced
        if not args.force:
            if not validate_system_readiness():
                logger.error("System readiness validation failed. Use --force to override.")
                return 1
        
        if args.dry_run:
            logger.info("DRY RUN - Would install the following enhanced cron jobs:")
            logger.info(f"  Monthly updates: {args.monthly_schedule}")
            logger.info(f"  Health checks: {args.health_check_schedule}")
            logger.info(f"  System cleanup: {args.cleanup_schedule}")
            logger.info(f"  Conflict cleanup: {args.conflict_cleanup_schedule}")
            logger.info(f"  Error reports: {args.error_report_schedule}")
            logger.info(f"  System validation: 0 1 * * * (daily)")
            return 0
        
        # Setup monitoring and alerting infrastructure
        if not setup_monitoring_and_alerting(args):
            logger.error("Failed to setup monitoring and alerting")
            return 1
        
        # Create enhanced cron jobs
        if not create_enhanced_cron_jobs(scheduler, args):
            logger.error("Failed to create enhanced cron jobs")
            return 1
        
        # Install jobs to system crontab
        success = scheduler.install_cron_jobs()
        
        if success:
            logger.info("Enhanced cron jobs installed successfully")
            
            # List installed jobs
            jobs = scheduler.list_cron_jobs()
            logger.info(f"Installed {len(jobs)} enhanced cron jobs:")
            for job in jobs:
                if job['enabled']:
                    logger.info(f"  - {job['name']}: {job['schedule']}")
            
            # Create helper scripts
            create_helper_scripts(args)
            
            logger.info("\n=== Installation Complete ===")
            logger.info("Enhanced scheduling features installed:")
            logger.info("  ✓ Automated monthly updates with health checks")
            logger.info("  ✓ Conflict detection and resolution")
            logger.info("  ✓ Error recovery and retry mechanisms")
            logger.info("  ✓ System monitoring and alerting")
            logger.info("  ✓ Automated cleanup and maintenance")
            logger.info("\nMonitor logs at: /var/log/multi_instance_arxiv/")
            
            return 0
        else:
            logger.error("Failed to install enhanced cron jobs to system")
            return 1
            
    except Exception as e:
        logger.error(f"Failed to install enhanced cron jobs: {e}")
        return 1


def create_helper_scripts(args) -> None:
    """Create helper scripts for manual operations."""
    script_dir = Path(args.script_dir)
    
    # Create manual health check script
    health_check_script = script_dir / "manual_health_check.sh"
    with open(health_check_script, 'w') as f:
        f.write(f"""#!/bin/bash
# Manual health check script
echo "Running comprehensive health check..."
{args.python_path} {script_dir / 'run_health_check.py'} --verbose --check-instances --output-file /tmp/health_check_result.json
echo "Health check complete. Results saved to /tmp/health_check_result.json"
""")
    health_check_script.chmod(0o755)
    
    # Create manual conflict resolution script
    conflict_script = script_dir / "manual_conflict_check.sh"
    with open(conflict_script, 'w') as f:
        f.write(f"""#!/bin/bash
# Manual conflict resolution script
echo "Checking for scheduling conflicts..."
{args.python_path} {script_dir / 'run_conflict_cleanup.py'} --verbose
echo "Conflict check complete."
""")
    conflict_script.chmod(0o755)
    
    logger.info("Helper scripts created:")
    logger.info(f"  - {health_check_script}")
    logger.info(f"  - {conflict_script}")


def remove_cron_jobs(scheduler: CronScheduler, args) -> int:
    """Remove enhanced cron jobs."""
    logger.info("Removing enhanced cron jobs")
    
    try:
        if args.dry_run:
            logger.info("DRY RUN - Would remove all multi-instance cron jobs")
            return 0
        
        success = scheduler.remove_cron_jobs()
        
        if success:
            logger.info("Enhanced cron jobs removed successfully")
            return 0
        else:
            logger.error("Failed to remove cron jobs")
            return 1
            
    except Exception as e:
        logger.error(f"Failed to remove cron jobs: {e}")
        return 1


def list_cron_jobs(scheduler: CronScheduler, args) -> int:
    """List configured cron jobs with enhanced information."""
    logger.info("Listing enhanced cron jobs")
    
    try:
        jobs = scheduler.list_cron_jobs()
        
        if not jobs:
            print("No enhanced cron jobs configured")
            return 0
        
        print(f"\nEnhanced Cron Jobs ({len(jobs)} total):")
        print("=" * 80)
        
        for job in jobs:
            status = "ENABLED" if job['enabled'] else "DISABLED"
            print(f"Name: {job['name']}")
            print(f"Schedule: {job['schedule']}")
            print(f"Status: {status}")
            print(f"Description: {job['description']}")
            print(f"Command: {job['command'][:60]}{'...' if len(job['command']) > 60 else ''}")
            
            # Show next run time if possible
            next_run = scheduler.get_next_run_time(job['name'])
            if next_run:
                print(f"Next run: {next_run}")
            
            print("-" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to list cron jobs: {e}")
        return 1


def validate_cron_setup(scheduler: CronScheduler, args) -> int:
    """Validate enhanced cron job setup."""
    logger.info("Validating enhanced cron job setup")
    
    try:
        # Validate system readiness
        if not validate_system_readiness():
            logger.error("System readiness validation failed")
            return 1
        
        # Validate cron jobs
        jobs = scheduler.list_cron_jobs()
        
        if not jobs:
            logger.warning("No cron jobs to validate")
            return 0
        
        validation_errors = []
        
        for job in jobs:
            # Validate schedule
            if not scheduler.validate_schedule(job['schedule']):
                validation_errors.append(f"Invalid schedule for job '{job['name']}': {job['schedule']}")
            
            # Validate command paths
            command_parts = job['command'].split()
            if command_parts:
                python_path = command_parts[0]
                if not Path(python_path).exists():
                    validation_errors.append(f"Python executable not found for job '{job['name']}': {python_path}")
                
                if len(command_parts) > 1:
                    script_path = command_parts[1]
                    if not Path(script_path).exists():
                        validation_errors.append(f"Script not found for job '{job['name']}': {script_path}")
        
        # Test automated scheduler
        try:
            import asyncio
            
            async def test_scheduler():
                auto_scheduler = AutomatedScheduler()
                is_valid, issues = await auto_scheduler.validate_scheduling_setup()
                return is_valid, issues
            
            is_valid, scheduler_issues = asyncio.run(test_scheduler())
            if not is_valid:
                validation_errors.extend(scheduler_issues)
                
        except Exception as e:
            validation_errors.append(f"Automated scheduler validation failed: {e}")
        
        if validation_errors:
            logger.error("Validation errors found:")
            for error in validation_errors:
                logger.error(f"  - {error}")
            return 1
        else:
            logger.info("All enhanced cron jobs and systems are valid")
            return 0
            
    except Exception as e:
        logger.error(f"Failed to validate cron setup: {e}")
        return 1


def test_cron_setup(scheduler: CronScheduler, args) -> int:
    """Test enhanced cron job setup."""
    logger.info("Testing enhanced cron job setup")
    
    try:
        # Test health checker
        import asyncio
        
        async def test_components():
            logger.info("Testing health checker...")
            health_checker = HealthChecker()
            health_status = await health_checker.run_comprehensive_health_check()
            logger.info(f"Health check result: {health_status.overall_status}")
            
            logger.info("Testing conflict resolver...")
            conflict_resolver = ConflictResolver()
            conflicts = await conflict_resolver.detect_conflicts("test_operation")
            logger.info(f"Detected {len(conflicts)} conflicts")
            
            logger.info("Testing error recovery manager...")
            error_recovery = ErrorRecoveryManager()
            stats = error_recovery.get_error_statistics()
            logger.info(f"Error recovery stats: {stats['total_errors']} total errors")
            
            return True
        
        success = asyncio.run(test_components())
        
        if success:
            logger.info("Enhanced cron job setup test completed successfully")
            return 0
        else:
            logger.error("Enhanced cron job setup test failed")
            return 1
            
    except Exception as e:
        logger.error(f"Failed to test cron setup: {e}")
        return 1


if __name__ == "__main__":
    import os
    exit_code = main()
    sys.exit(exit_code)