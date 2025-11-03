#!/usr/bin/env python3
"""
Cron Setup Script for Multi-Instance ArXiv System

This script configures automated scheduling for the multi-instance ArXiv system,
including monthly updates, health checks, storage cleanup, and monitoring.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.core.instance_config import InstanceConfigManager
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure the multi-instance ArXiv system is properly installed.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/cron_setup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CronJobManager:
    """Manages cron job configuration for the multi-instance ArXiv system."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_manager = InstanceConfigManager(config_dir)
        self.instances = self.config_manager.get_all_instances()
        
        # Get script paths
        self.scripts_dir = Path(__file__).parent
        self.python_path = sys.executable
        
        logger.info(f"CronJobManager initialized with {len(self.instances)} instances")
    
    def generate_cron_jobs(self) -> Dict[str, List[str]]:
        """Generate cron job configurations for all system components."""
        logger.info("Generating cron job configurations")
        
        cron_jobs = {
            'monthly_updates': [],
            'daily_health_checks': [],
            'weekly_storage_cleanup': [],
            'hourly_monitoring': [],
            'system_maintenance': []
        }
        
        # Monthly update jobs for each instance
        for instance_name in self.instances.keys():
            if instance_name == 'ai_scholar':
                # AI Scholar monthly update - 1st of each month at 2 AM
                cron_jobs['monthly_updates'].append(
                    f"0 2 1 * * {self.python_path} {self.scripts_dir}/ai_scholar_monthly_update.py "
                    f"--config-dir config --send-notifications"
                )
            elif instance_name == 'quant_scholar':
                # Quant Scholar monthly update - 1st of each month at 3 AM
                cron_jobs['monthly_updates'].append(
                    f"0 3 1 * * {self.python_path} {self.scripts_dir}/quant_scholar_monthly_update.py "
                    f"--config-dir config --send-notifications"
                )
        
        # Daily health checks - every day at 6 AM
        cron_jobs['daily_health_checks'].append(
            f"0 6 * * * {self.python_path} {self.scripts_dir}/system_health_check.py "
            f"--config-dir config --send-alerts --output /var/log/arxiv_system/daily_health.json"
        )
        
        # Daily system monitoring - every day at 7 AM
        cron_jobs['daily_health_checks'].append(
            f"0 7 * * * {self.python_path} {self.scripts_dir}/multi_instance_monitor.py "
            f"--config-dir config --send-alerts --output /var/log/arxiv_system/daily_status.json"
        )
        
        # Weekly storage cleanup - every Sunday at 1 AM
        cron_jobs['weekly_storage_cleanup'].append(
            f"0 1 * * 0 {self.python_path} {self.scripts_dir}/storage_manager.py "
            f"cleanup --config-dir config --max-age-days 90"
        )
        
        # Weekly storage analysis - every Sunday at 2 AM
        cron_jobs['weekly_storage_cleanup'].append(
            f"0 2 * * 0 {self.python_path} {self.scripts_dir}/storage_manager.py "
            f"analyze --config-dir config --output /var/log/arxiv_system/weekly_storage.json"
        )
        
        # Hourly monitoring - every hour
        cron_jobs['hourly_monitoring'].append(
            f"0 * * * * {self.python_path} {self.scripts_dir}/multi_instance_monitor.py "
            f"--config-dir config --continuous 60 > /dev/null 2>&1 &"
        )
        
        # System maintenance jobs
        # Log rotation - daily at midnight
        cron_jobs['system_maintenance'].append(
            "0 0 * * * /usr/sbin/logrotate /etc/logrotate.d/arxiv_system"
        )
        
        # Backup configuration - weekly on Saturday at 11 PM
        cron_jobs['system_maintenance'].append(
            f"0 23 * * 6 tar -czf /backup/arxiv_config_$(date +\\%Y\\%m\\%d).tar.gz config/"
        )
        
        logger.info(f"Generated {sum(len(jobs) for jobs in cron_jobs.values())} cron jobs")
        return cron_jobs   
 
    def install_cron_jobs(self, job_categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Install cron jobs to the system crontab."""
        logger.info("Installing cron jobs")
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'installed_jobs': [],
            'failed_jobs': [],
            'warnings': []
        }
        
        # Generate all cron jobs
        all_cron_jobs = self.generate_cron_jobs()
        
        # Filter by categories if specified
        if job_categories:
            filtered_jobs = {}
            for category in job_categories:
                if category in all_cron_jobs:
                    filtered_jobs[category] = all_cron_jobs[category]
            all_cron_jobs = filtered_jobs
        
        try:
            # Get current crontab
            try:
                current_crontab = subprocess.check_output(['crontab', '-l'], 
                                                        stderr=subprocess.DEVNULL).decode('utf-8')
            except subprocess.CalledProcessError:
                current_crontab = ""
            
            # Prepare new crontab content
            new_crontab_lines = []
            
            # Keep existing non-ArXiv cron jobs
            arxiv_marker = "# ArXiv Multi-Instance System Jobs"
            in_arxiv_section = False
            
            for line in current_crontab.split('\n'):
                if line.strip() == arxiv_marker:
                    in_arxiv_section = True
                    continue
                elif line.strip().startswith("# End ArXiv Jobs"):
                    in_arxiv_section = False
                    continue
                elif not in_arxiv_section and line.strip():
                    new_crontab_lines.append(line)
            
            # Add ArXiv system cron jobs
            new_crontab_lines.append("")
            new_crontab_lines.append(arxiv_marker)
            new_crontab_lines.append(f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            new_crontab_lines.append("")
            
            for category, jobs in all_cron_jobs.items():
                new_crontab_lines.append(f"# {category.replace('_', ' ').title()}")
                for job in jobs:
                    new_crontab_lines.append(job)
                    result['installed_jobs'].append(f"{category}: {job}")
                new_crontab_lines.append("")
            
            new_crontab_lines.append("# End ArXiv Jobs")
            
            # Write new crontab
            new_crontab_content = '\n'.join(new_crontab_lines)
            
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(new_crontab_content.encode('utf-8'))
            
            if process.returncode == 0:
                logger.info(f"Successfully installed {len(result['installed_jobs'])} cron jobs")
            else:
                error_msg = f"Failed to install crontab: {stderr.decode('utf-8')}"
                logger.error(error_msg)
                result['failed_jobs'].append(error_msg)
        
        except Exception as e:
            error_msg = f"Error installing cron jobs: {str(e)}"
            logger.error(error_msg)
            result['failed_jobs'].append(error_msg)
        
        return result
    
    def remove_cron_jobs(self) -> Dict[str, Any]:
        """Remove ArXiv system cron jobs from crontab."""
        logger.info("Removing ArXiv system cron jobs")
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'removed_jobs': [],
            'errors': []
        }
        
        try:
            # Get current crontab
            try:
                current_crontab = subprocess.check_output(['crontab', '-l'], 
                                                        stderr=subprocess.DEVNULL).decode('utf-8')
            except subprocess.CalledProcessError:
                logger.info("No existing crontab found")
                return result
            
            # Remove ArXiv system jobs
            new_crontab_lines = []
            arxiv_marker = "# ArXiv Multi-Instance System Jobs"
            in_arxiv_section = False
            removed_count = 0
            
            for line in current_crontab.split('\n'):
                if line.strip() == arxiv_marker:
                    in_arxiv_section = True
                    continue
                elif line.strip().startswith("# End ArXiv Jobs"):
                    in_arxiv_section = False
                    continue
                elif in_arxiv_section:
                    if line.strip() and not line.strip().startswith('#'):
                        result['removed_jobs'].append(line.strip())
                        removed_count += 1
                    continue
                else:
                    new_crontab_lines.append(line)
            
            # Write updated crontab
            new_crontab_content = '\n'.join(new_crontab_lines)
            
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(new_crontab_content.encode('utf-8'))
            
            if process.returncode == 0:
                logger.info(f"Successfully removed {removed_count} cron jobs")
            else:
                error_msg = f"Failed to update crontab: {stderr.decode('utf-8')}"
                logger.error(error_msg)
                result['errors'].append(error_msg)
        
        except Exception as e:
            error_msg = f"Error removing cron jobs: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
        
        return result
    
    def list_cron_jobs(self) -> Dict[str, Any]:
        """List current ArXiv system cron jobs."""
        logger.info("Listing ArXiv system cron jobs")
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'active_jobs': [],
            'system_cron_status': 'unknown'
        }
        
        try:
            # Check if cron service is running
            try:
                subprocess.check_output(['systemctl', 'is-active', 'cron'], 
                                      stderr=subprocess.DEVNULL)
                result['system_cron_status'] = 'active'
            except subprocess.CalledProcessError:
                try:
                    subprocess.check_output(['systemctl', 'is-active', 'crond'], 
                                          stderr=subprocess.DEVNULL)
                    result['system_cron_status'] = 'active'
                except subprocess.CalledProcessError:
                    result['system_cron_status'] = 'inactive'
            
            # Get current crontab
            try:
                current_crontab = subprocess.check_output(['crontab', '-l'], 
                                                        stderr=subprocess.DEVNULL).decode('utf-8')
            except subprocess.CalledProcessError:
                logger.info("No crontab found for current user")
                return result
            
            # Extract ArXiv system jobs
            arxiv_marker = "# ArXiv Multi-Instance System Jobs"
            in_arxiv_section = False
            
            for line in current_crontab.split('\n'):
                if line.strip() == arxiv_marker:
                    in_arxiv_section = True
                    continue
                elif line.strip().startswith("# End ArXiv Jobs"):
                    in_arxiv_section = False
                    continue
                elif in_arxiv_section and line.strip() and not line.strip().startswith('#'):
                    result['active_jobs'].append(line.strip())
        
        except Exception as e:
            logger.error(f"Error listing cron jobs: {e}")
            result['error'] = str(e)
        
        return result
    
    def validate_cron_setup(self) -> Dict[str, Any]:
        """Validate cron job setup and system requirements."""
        logger.info("Validating cron setup")
        
        validation = {
            'timestamp': datetime.now().isoformat(),
            'system_checks': {},
            'script_checks': {},
            'permission_checks': {},
            'overall_status': 'healthy',
            'issues': [],
            'recommendations': []
        }
        
        # Check system requirements
        validation['system_checks'] = self._check_system_requirements()
        
        # Check script availability and permissions
        validation['script_checks'] = self._check_script_availability()
        
        # Check permissions
        validation['permission_checks'] = self._check_permissions()
        
        # Determine overall status
        issues = []
        for check_category in ['system_checks', 'script_checks', 'permission_checks']:
            for check_name, check_result in validation[check_category].items():
                if check_result.get('status') == 'error':
                    issues.append(f"{check_category}.{check_name}: {check_result.get('message', 'Failed')}")
                elif check_result.get('status') == 'warning':
                    validation['recommendations'].append(
                        f"Address warning in {check_category}.{check_name}: {check_result.get('message', 'Warning')}"
                    )
        
        validation['issues'] = issues
        
        if issues:
            validation['overall_status'] = 'error' if len(issues) > 2 else 'warning'
        
        logger.info(f"Cron validation completed. Status: {validation['overall_status']}")
        return validation
    
    def _check_system_requirements(self) -> Dict[str, Any]:
        """Check system requirements for cron jobs."""
        checks = {}
        
        # Check if cron is installed and running
        try:
            subprocess.check_output(['which', 'crontab'], stderr=subprocess.DEVNULL)
            checks['crontab_available'] = {'status': 'healthy', 'message': 'crontab command available'}
        except subprocess.CalledProcessError:
            checks['crontab_available'] = {'status': 'error', 'message': 'crontab command not found'}
        
        # Check cron service status
        cron_services = ['cron', 'crond']
        cron_running = False
        
        for service in cron_services:
            try:
                subprocess.check_output(['systemctl', 'is-active', service], 
                                      stderr=subprocess.DEVNULL)
                checks['cron_service'] = {'status': 'healthy', 'message': f'{service} service is active'}
                cron_running = True
                break
            except subprocess.CalledProcessError:
                continue
        
        if not cron_running:
            checks['cron_service'] = {'status': 'error', 'message': 'No cron service is running'}
        
        # Check log directory
        log_dir = Path('/var/log/arxiv_system')
        if log_dir.exists() and log_dir.is_dir():
            checks['log_directory'] = {'status': 'healthy', 'message': 'Log directory exists'}
        else:
            checks['log_directory'] = {'status': 'warning', 'message': 'Log directory does not exist'}
        
        return checks
    
    def _check_script_availability(self) -> Dict[str, Any]:
        """Check availability of required scripts."""
        checks = {}
        
        required_scripts = [
            'ai_scholar_monthly_update.py',
            'quant_scholar_monthly_update.py',
            'system_health_check.py',
            'multi_instance_monitor.py',
            'storage_manager.py'
        ]
        
        for script_name in required_scripts:
            script_path = self.scripts_dir / script_name
            
            if script_path.exists():
                if os.access(script_path, os.X_OK):
                    checks[script_name] = {'status': 'healthy', 'message': 'Script exists and is executable'}
                else:
                    checks[script_name] = {'status': 'warning', 'message': 'Script exists but is not executable'}
            else:
                checks[script_name] = {'status': 'error', 'message': 'Script does not exist'}
        
        return checks
    
    def _check_permissions(self) -> Dict[str, Any]:
        """Check permissions for cron job operations."""
        checks = {}
        
        # Check if user can modify crontab
        try:
            subprocess.check_output(['crontab', '-l'], stderr=subprocess.DEVNULL)
            checks['crontab_access'] = {'status': 'healthy', 'message': 'User can access crontab'}
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:  # No crontab exists (normal)
                checks['crontab_access'] = {'status': 'healthy', 'message': 'User can access crontab (no existing crontab)'}
            else:
                checks['crontab_access'] = {'status': 'error', 'message': 'User cannot access crontab'}
        
        # Check write permissions for log directory
        log_dir = Path('/var/log/arxiv_system')
        if log_dir.exists():
            if os.access(log_dir, os.W_OK):
                checks['log_write_access'] = {'status': 'healthy', 'message': 'Can write to log directory'}
            else:
                checks['log_write_access'] = {'status': 'warning', 'message': 'Cannot write to log directory'}
        else:
            checks['log_write_access'] = {'status': 'warning', 'message': 'Log directory does not exist'}
        
        return checks
    
    def create_log_directories(self) -> Dict[str, Any]:
        """Create necessary log directories for cron jobs."""
        logger.info("Creating log directories")
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'created_directories': [],
            'errors': []
        }
        
        directories_to_create = [
            '/var/log/arxiv_system',
            '/backup',
            'logs'
        ]
        
        for dir_path in directories_to_create:
            try:
                path = Path(dir_path)
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                    result['created_directories'].append(str(path))
                    logger.info(f"Created directory: {path}")
            except Exception as e:
                error_msg = f"Failed to create directory {dir_path}: {str(e)}"
                logger.error(error_msg)
                result['errors'].append(error_msg)
        
        return result

async def main():
    """Main entry point for the cron setup script."""
    parser = argparse.ArgumentParser(description="Cron Setup for Multi-Instance ArXiv System")
    
    parser.add_argument(
        '--config-dir',
        default='config',
        help='Configuration directory path'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install cron jobs')
    install_parser.add_argument(
        '--categories',
        nargs='+',
        choices=['monthly_updates', 'daily_health_checks', 'weekly_storage_cleanup', 
                'hourly_monitoring', 'system_maintenance'],
        help='Install only specific job categories'
    )
    install_parser.add_argument(
        '--force',
        action='store_true',
        help='Force installation even if validation fails'
    )
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove cron jobs')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List current cron jobs')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate cron setup')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate cron job configurations')
    generate_parser.add_argument(
        '--output',
        help='Output file for generated cron jobs'
    )
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Complete setup including directories and validation')
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        manager = CronJobManager(args.config_dir)
        
        if args.command == 'install':
            # Validate setup first unless forced
            if not args.force:
                validation = manager.validate_cron_setup()
                if validation['overall_status'] == 'error':
                    print("Validation failed. Issues found:")
                    for issue in validation['issues']:
                        print(f"  - {issue}")
                    print("\nUse --force to install anyway, or fix the issues first.")
                    return
                elif validation['overall_status'] == 'warning':
                    print("Validation warnings found:")
                    for rec in validation['recommendations']:
                        print(f"  - {rec}")
                    print("Proceeding with installation...")
            
            # Install cron jobs
            result = manager.install_cron_jobs(args.categories)
            
            print(f"Cron job installation completed at {result['timestamp']}")
            print(f"Installed {len(result['installed_jobs'])} jobs:")
            for job in result['installed_jobs']:
                print(f"  - {job}")
            
            if result['failed_jobs']:
                print(f"\nFailed to install {len(result['failed_jobs'])} jobs:")
                for failure in result['failed_jobs']:
                    print(f"  - {failure}")
        
        elif args.command == 'remove':
            result = manager.remove_cron_jobs()
            
            print(f"Cron job removal completed at {result['timestamp']}")
            print(f"Removed {len(result['removed_jobs'])} jobs:")
            for job in result['removed_jobs']:
                print(f"  - {job}")
            
            if result['errors']:
                print(f"\nErrors during removal:")
                for error in result['errors']:
                    print(f"  - {error}")
        
        elif args.command == 'list':
            result = manager.list_cron_jobs()
            
            print(f"Cron job status as of {result['timestamp']}")
            print(f"System cron service: {result['system_cron_status']}")
            print(f"Active ArXiv system jobs: {len(result['active_jobs'])}")
            
            if result['active_jobs']:
                print("\nActive jobs:")
                for job in result['active_jobs']:
                    print(f"  {job}")
            else:
                print("No ArXiv system cron jobs found.")
        
        elif args.command == 'validate':
            validation = manager.validate_cron_setup()
            
            print(f"Cron setup validation completed at {validation['timestamp']}")
            print(f"Overall status: {validation['overall_status']}")
            
            # Print system checks
            print("\nSystem Requirements:")
            for check_name, check_result in validation['system_checks'].items():
                status_icon = "✓" if check_result['status'] == 'healthy' else "⚠" if check_result['status'] == 'warning' else "✗"
                print(f"  {status_icon} {check_name}: {check_result['message']}")
            
            # Print script checks
            print("\nScript Availability:")
            for check_name, check_result in validation['script_checks'].items():
                status_icon = "✓" if check_result['status'] == 'healthy' else "⚠" if check_result['status'] == 'warning' else "✗"
                print(f"  {status_icon} {check_name}: {check_result['message']}")
            
            # Print permission checks
            print("\nPermissions:")
            for check_name, check_result in validation['permission_checks'].items():
                status_icon = "✓" if check_result['status'] == 'healthy' else "⚠" if check_result['status'] == 'warning' else "✗"
                print(f"  {status_icon} {check_name}: {check_result['message']}")
            
            if validation['issues']:
                print(f"\nIssues found ({len(validation['issues'])}):")
                for issue in validation['issues']:
                    print(f"  - {issue}")
            
            if validation['recommendations']:
                print(f"\nRecommendations ({len(validation['recommendations'])}):")
                for rec in validation['recommendations']:
                    print(f"  - {rec}")
        
        elif args.command == 'generate':
            cron_jobs = manager.generate_cron_jobs()
            
            output_content = []
            output_content.append("# ArXiv Multi-Instance System Cron Jobs")
            output_content.append(f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            output_content.append("")
            
            for category, jobs in cron_jobs.items():
                output_content.append(f"# {category.replace('_', ' ').title()}")
                for job in jobs:
                    output_content.append(job)
                output_content.append("")
            
            output_text = '\n'.join(output_content)
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output_text)
                print(f"Cron job configurations saved to {args.output}")
            else:
                print(output_text)
        
        elif args.command == 'setup':
            print("Running complete cron setup...")
            
            # Create directories
            print("\n1. Creating log directories...")
            dir_result = manager.create_log_directories()
            if dir_result['created_directories']:
                print(f"Created directories: {', '.join(dir_result['created_directories'])}")
            if dir_result['errors']:
                print(f"Directory creation errors: {', '.join(dir_result['errors'])}")
            
            # Validate setup
            print("\n2. Validating system requirements...")
            validation = manager.validate_cron_setup()
            print(f"Validation status: {validation['overall_status']}")
            
            if validation['overall_status'] == 'error':
                print("Critical issues found. Please fix before proceeding:")
                for issue in validation['issues']:
                    print(f"  - {issue}")
                return
            
            # Install cron jobs
            print("\n3. Installing cron jobs...")
            install_result = manager.install_cron_jobs()
            print(f"Installed {len(install_result['installed_jobs'])} cron jobs")
            
            if install_result['failed_jobs']:
                print(f"Failed to install {len(install_result['failed_jobs'])} jobs:")
                for failure in install_result['failed_jobs']:
                    print(f"  - {failure}")
            
            print("\nCron setup completed successfully!")
            print("The system will now run automated tasks according to the schedule.")
    
    except Exception as e:
        logger.error(f"Cron setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())