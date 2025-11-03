#!/usr/bin/env python3
"""
Cron Job Setup Script for multi-instance ArXiv system.

Sets up automated cron jobs for monthly updates, health checks, and maintenance.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from cron_scheduler import CronScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for cron job setup."""
    parser = argparse.ArgumentParser(description="Setup cron jobs for multi-instance ArXiv system")
    
    parser.add_argument(
        '--action',
        choices=['install', 'remove', 'list', 'validate'],
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
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Cron job setup - Action: {args.action}")
    
    try:
        # Initialize cron scheduler
        scheduler = CronScheduler(args.config_file)
        
        if args.action == 'install':
            return install_cron_jobs(scheduler, args)
        elif args.action == 'remove':
            return remove_cron_jobs(scheduler, args)
        elif args.action == 'list':
            return list_cron_jobs(scheduler, args)
        elif args.action == 'validate':
            return validate_cron_jobs(scheduler, args)
        else:
            logger.error(f"Unknown action: {args.action}")
            return 1
            
    except Exception as e:
        logger.error(f"Cron job setup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def install_cron_jobs(scheduler: CronScheduler, args) -> int:
    """Install cron jobs."""
    logger.info("Installing cron jobs")
    
    try:
        instance_names = [name.strip() for name in args.instances.split(',')]
        
        # Validate schedules
        if not scheduler.validate_schedule(args.monthly_schedule):
            logger.error(f"Invalid monthly schedule: {args.monthly_schedule}")
            return 1
        
        if not scheduler.validate_schedule(args.health_check_schedule):
            logger.error(f"Invalid health check schedule: {args.health_check_schedule}")
            return 1
        
        if not scheduler.validate_schedule(args.cleanup_schedule):
            logger.error(f"Invalid cleanup schedule: {args.cleanup_schedule}")
            return 1
        
        if args.dry_run:
            logger.info("DRY RUN - Would install the following cron jobs:")
            logger.info(f"  Monthly updates: {args.monthly_schedule} for instances {instance_names}")
            logger.info(f"  Health checks: {args.health_check_schedule}")
            logger.info(f"  Cleanup: {args.cleanup_schedule}")
            return 0
        
        # Add monthly update job
        success = scheduler.add_monthly_update_job(
            instance_names=instance_names,
            schedule=args.monthly_schedule,
            python_path=args.python_path,
            script_path=str(Path(args.script_dir) / "run_monthly_updates.py")
        )
        
        if not success:
            logger.error("Failed to add monthly update job")
            return 1
        
        # Add health check job
        success = scheduler.add_health_check_job(
            schedule=args.health_check_schedule,
            python_path=args.python_path,
            script_path=str(Path(args.script_dir) / "run_health_check.py")
        )
        
        if not success:
            logger.error("Failed to add health check job")
            return 1
        
        # Add cleanup job
        success = scheduler.add_cleanup_job(
            schedule=args.cleanup_schedule,
            python_path=args.python_path,
            script_path=str(Path(args.script_dir) / "run_cleanup.py")
        )
        
        if not success:
            logger.error("Failed to add cleanup job")
            return 1
        
        # Install jobs to system crontab
        success = scheduler.install_cron_jobs()
        
        if success:
            logger.info("Cron jobs installed successfully")
            
            # List installed jobs
            jobs = scheduler.list_cron_jobs()
            logger.info(f"Installed {len(jobs)} cron jobs:")
            for job in jobs:
                if job['enabled']:
                    logger.info(f"  - {job['name']}: {job['schedule']}")
            
            return 0
        else:
            logger.error("Failed to install cron jobs to system")
            return 1
            
    except Exception as e:
        logger.error(f"Failed to install cron jobs: {e}")
        return 1


def remove_cron_jobs(scheduler: CronScheduler, args) -> int:
    """Remove cron jobs."""
    logger.info("Removing cron jobs")
    
    try:
        if args.dry_run:
            logger.info("DRY RUN - Would remove all multi-instance cron jobs")
            return 0
        
        success = scheduler.remove_cron_jobs()
        
        if success:
            logger.info("Cron jobs removed successfully")
            return 0
        else:
            logger.error("Failed to remove cron jobs")
            return 1
            
    except Exception as e:
        logger.error(f"Failed to remove cron jobs: {e}")
        return 1


def list_cron_jobs(scheduler: CronScheduler, args) -> int:
    """List configured cron jobs."""
    logger.info("Listing cron jobs")
    
    try:
        jobs = scheduler.list_cron_jobs()
        
        if not jobs:
            print("No cron jobs configured")
            return 0
        
        print(f"\nConfigured Cron Jobs ({len(jobs)} total):")
        print("-" * 60)
        
        for job in jobs:
            status = "ENABLED" if job['enabled'] else "DISABLED"
            print(f"Name: {job['name']}")
            print(f"Schedule: {job['schedule']}")
            print(f"Status: {status}")
            print(f"Description: {job['description']}")
            print(f"Command: {job['command'][:80]}{'...' if len(job['command']) > 80 else ''}")
            print("-" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to list cron jobs: {e}")
        return 1


def validate_cron_jobs(scheduler: CronScheduler, args) -> int:
    """Validate cron job configurations."""
    logger.info("Validating cron jobs")
    
    try:
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
        
        if validation_errors:
            logger.error("Validation errors found:")
            for error in validation_errors:
                logger.error(f"  - {error}")
            return 1
        else:
            logger.info("All cron jobs are valid")
            return 0
            
    except Exception as e:
        logger.error(f"Failed to validate cron jobs: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)