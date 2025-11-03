"""
Cron Scheduler for automated monthly updates.

Provides utilities for setting up and managing cron jobs for the multi-instance
ArXiv system monthly updates.
"""

import logging
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import os
from datetime import datetime
from dataclasses import dataclass

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


@dataclass
class CronJobConfig:
    """Configuration for a cron job."""
    name: str
    schedule: str  # Cron expression (e.g., "0 2 1 * *" for 2 AM on 1st of each month)
    command: str
    description: str
    enabled: bool = True
    user: str = "root"
    environment_vars: Dict[str, str] = None
    
    def __post_init__(self):
        if self.environment_vars is None:
            self.environment_vars = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'schedule': self.schedule,
            'command': self.command,
            'description': self.description,
            'enabled': self.enabled,
            'user': self.user,
            'environment_vars': self.environment_vars
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CronJobConfig':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            name=data['name'],
            schedule=data['schedule'],
            command=data['command'],
            description=data['description'],
            enabled=data.get('enabled', True),
            user=data.get('user', 'root'),
            environment_vars=data.get('environment_vars', {})
        )


class CronScheduler:
    """Manages cron jobs for automated monthly updates."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize cron scheduler.
        
        Args:
            config_file: Path to cron configuration file
        """
        self.config_file = config_file or "/etc/multi_instance_arxiv/cron_config.json"
        self.jobs: Dict[str, CronJobConfig] = {}
        
        # Load existing configuration
        self._load_config()
        
        logger.info("CronScheduler initialized")
    
    def _load_config(self) -> None:
        """Load cron configuration from file."""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                
                for job_data in config_data.get('jobs', []):
                    job = CronJobConfig.from_dict(job_data)
                    self.jobs[job.name] = job
                
                logger.info(f"Loaded {len(self.jobs)} cron job configurations")
            else:
                logger.info("No existing cron configuration found")
                
        except Exception as e:
            logger.error(f"Failed to load cron configuration: {e}")
    
    def _save_config(self) -> None:
        """Save cron configuration to file."""
        try:
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = {
                'jobs': [job.to_dict() for job in self.jobs.values()],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Saved cron configuration to {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save cron configuration: {e}")
    
    def add_monthly_update_job(self, 
                             instance_names: List[str],
                             schedule: str = "0 2 1 * *",
                             python_path: Optional[str] = None,
                             script_path: Optional[str] = None) -> bool:
        """
        Add monthly update cron job.
        
        Args:
            instance_names: List of instance names to update
            schedule: Cron schedule expression (default: 2 AM on 1st of each month)
            python_path: Path to Python executable
            script_path: Path to monthly update script
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Default paths
            if python_path is None:
                python_path = sys.executable
            
            if script_path is None:
                script_path = str(Path(__file__).parent / "run_monthly_updates.py")
            
            # Create command
            instances_arg = ",".join(instance_names)
            command = f"{python_path} {script_path} --instances {instances_arg}"
            
            # Add logging
            log_dir = "/var/log/multi_instance_arxiv"
            log_file = f"{log_dir}/monthly_update.log"
            command += f" >> {log_file} 2>&1"
            
            # Create job configuration
            job = CronJobConfig(
                name="monthly_update_all_instances",
                schedule=schedule,
                command=command,
                description=f"Monthly update for instances: {', '.join(instance_names)}",
                enabled=True,
                environment_vars={
                    'PYTHONPATH': str(Path(__file__).parent.parent.parent),
                    'PATH': os.environ.get('PATH', ''),
                    'HOME': os.environ.get('HOME', '/root')
                }
            )
            
            self.jobs[job.name] = job
            self._save_config()
            
            logger.info(f"Added monthly update cron job: {job.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add monthly update job: {e}")
            return False
    
    def add_health_check_job(self, 
                           schedule: str = "0 */6 * * *",
                           python_path: Optional[str] = None,
                           script_path: Optional[str] = None) -> bool:
        """
        Add health check cron job.
        
        Args:
            schedule: Cron schedule expression (default: every 6 hours)
            python_path: Path to Python executable
            script_path: Path to health check script
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Default paths
            if python_path is None:
                python_path = sys.executable
            
            if script_path is None:
                script_path = str(Path(__file__).parent / "run_health_check.py")
            
            # Create command
            command = f"{python_path} {script_path}"
            
            # Add logging
            log_dir = "/var/log/multi_instance_arxiv"
            log_file = f"{log_dir}/health_check.log"
            command += f" >> {log_file} 2>&1"
            
            # Create job configuration
            job = CronJobConfig(
                name="health_check_all_instances",
                schedule=schedule,
                command=command,
                description="Health check for all instances",
                enabled=True,
                environment_vars={
                    'PYTHONPATH': str(Path(__file__).parent.parent.parent),
                    'PATH': os.environ.get('PATH', ''),
                    'HOME': os.environ.get('HOME', '/root')
                }
            )
            
            self.jobs[job.name] = job
            self._save_config()
            
            logger.info(f"Added health check cron job: {job.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add health check job: {e}")
            return False
    
    def add_cleanup_job(self, 
                       schedule: str = "0 3 1 * *",
                       python_path: Optional[str] = None,
                       script_path: Optional[str] = None) -> bool:
        """
        Add cleanup cron job.
        
        Args:
            schedule: Cron schedule expression (default: 3 AM on 1st of each month)
            python_path: Path to Python executable
            script_path: Path to cleanup script
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Default paths
            if python_path is None:
                python_path = sys.executable
            
            if script_path is None:
                script_path = str(Path(__file__).parent / "run_cleanup.py")
            
            # Create command
            command = f"{python_path} {script_path}"
            
            # Add logging
            log_dir = "/var/log/multi_instance_arxiv"
            log_file = f"{log_dir}/cleanup.log"
            command += f" >> {log_file} 2>&1"
            
            # Create job configuration
            job = CronJobConfig(
                name="cleanup_all_instances",
                schedule=schedule,
                command=command,
                description="Cleanup old files for all instances",
                enabled=True,
                environment_vars={
                    'PYTHONPATH': str(Path(__file__).parent.parent.parent),
                    'PATH': os.environ.get('PATH', ''),
                    'HOME': os.environ.get('HOME', '/root')
                }
            )
            
            self.jobs[job.name] = job
            self._save_config()
            
            logger.info(f"Added cleanup cron job: {job.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add cleanup job: {e}")
            return False
    
    def install_cron_jobs(self) -> bool:
        """
        Install all configured cron jobs to the system crontab.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create log directory
            log_dir = Path("/var/log/multi_instance_arxiv")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Get current crontab
            try:
                result = subprocess.run(['crontab', '-l'], 
                                      capture_output=True, text=True, check=False)
                current_crontab = result.stdout if result.returncode == 0 else ""
            except Exception:
                current_crontab = ""
            
            # Remove existing multi-instance jobs
            lines = current_crontab.split('\n')
            filtered_lines = [
                line for line in lines 
                if not line.strip().startswith('#') or 
                'multi_instance_arxiv' not in line
            ]
            
            # Add header comment
            filtered_lines.append("# Multi-Instance ArXiv System Cron Jobs")
            filtered_lines.append(f"# Generated on {datetime.now().isoformat()}")
            
            # Add configured jobs
            for job in self.jobs.values():
                if job.enabled:
                    # Add environment variables as comments
                    if job.environment_vars:
                        for key, value in job.environment_vars.items():
                            filtered_lines.append(f"# {key}={value}")
                    
                    # Add job description
                    filtered_lines.append(f"# {job.description}")
                    
                    # Add cron job line
                    filtered_lines.append(f"{job.schedule} {job.command}")
                    filtered_lines.append("")  # Empty line for readability
            
            # Write new crontab
            new_crontab = '\n'.join(filtered_lines)
            
            process = subprocess.Popen(['crontab', '-'], 
                                     stdin=subprocess.PIPE, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            
            stdout, stderr = process.communicate(input=new_crontab)
            
            if process.returncode == 0:
                logger.info(f"Successfully installed {len([j for j in self.jobs.values() if j.enabled])} cron jobs")
                return True
            else:
                logger.error(f"Failed to install cron jobs: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to install cron jobs: {e}")
            return False
    
    def remove_cron_jobs(self) -> bool:
        """
        Remove all multi-instance cron jobs from the system crontab.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current crontab
            try:
                result = subprocess.run(['crontab', '-l'], 
                                      capture_output=True, text=True, check=False)
                current_crontab = result.stdout if result.returncode == 0 else ""
            except Exception:
                current_crontab = ""
            
            # Remove multi-instance jobs
            lines = current_crontab.split('\n')
            filtered_lines = []
            skip_next = False
            
            for line in lines:
                # Skip multi-instance related lines
                if ('multi_instance_arxiv' in line or 
                    'monthly_update' in line or
                    'health_check' in line or
                    skip_next):
                    skip_next = False
                    continue
                
                # Check if next line should be skipped (for comments before jobs)
                if line.strip().startswith('#') and 'Multi-Instance ArXiv' in line:
                    skip_next = True
                    continue
                
                filtered_lines.append(line)
            
            # Write new crontab
            new_crontab = '\n'.join(filtered_lines)
            
            process = subprocess.Popen(['crontab', '-'], 
                                     stdin=subprocess.PIPE, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            
            stdout, stderr = process.communicate(input=new_crontab)
            
            if process.returncode == 0:
                logger.info("Successfully removed multi-instance cron jobs")
                return True
            else:
                logger.error(f"Failed to remove cron jobs: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove cron jobs: {e}")
            return False
    
    def list_cron_jobs(self) -> List[Dict[str, Any]]:
        """
        List all configured cron jobs.
        
        Returns:
            List of job configurations
        """
        return [job.to_dict() for job in self.jobs.values()]
    
    def enable_job(self, job_name: str) -> bool:
        """
        Enable a specific cron job.
        
        Args:
            job_name: Name of the job to enable
            
        Returns:
            True if successful, False otherwise
        """
        if job_name in self.jobs:
            self.jobs[job_name].enabled = True
            self._save_config()
            logger.info(f"Enabled cron job: {job_name}")
            return True
        else:
            logger.error(f"Cron job not found: {job_name}")
            return False
    
    def disable_job(self, job_name: str) -> bool:
        """
        Disable a specific cron job.
        
        Args:
            job_name: Name of the job to disable
            
        Returns:
            True if successful, False otherwise
        """
        if job_name in self.jobs:
            self.jobs[job_name].enabled = False
            self._save_config()
            logger.info(f"Disabled cron job: {job_name}")
            return True
        else:
            logger.error(f"Cron job not found: {job_name}")
            return False
    
    def remove_job(self, job_name: str) -> bool:
        """
        Remove a specific cron job.
        
        Args:
            job_name: Name of the job to remove
            
        Returns:
            True if successful, False otherwise
        """
        if job_name in self.jobs:
            del self.jobs[job_name]
            self._save_config()
            logger.info(f"Removed cron job: {job_name}")
            return True
        else:
            logger.error(f"Cron job not found: {job_name}")
            return False
    
    def validate_schedule(self, schedule: str) -> bool:
        """
        Validate a cron schedule expression.
        
        Args:
            schedule: Cron schedule expression
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic validation - should have 5 parts
            parts = schedule.strip().split()
            if len(parts) != 5:
                return False
            
            # Validate each part (basic check)
            ranges = [
                (0, 59),    # minute
                (0, 23),    # hour
                (1, 31),    # day of month
                (1, 12),    # month
                (0, 7)      # day of week (0 and 7 are Sunday)
            ]
            
            for i, part in enumerate(parts):
                if part == '*':
                    continue
                
                # Handle ranges and lists
                if ',' in part:
                    values = part.split(',')
                else:
                    values = [part]
                
                for value in values:
                    if '-' in value:
                        # Range
                        start, end = value.split('-')
                        start, end = int(start), int(end)
                        if not (ranges[i][0] <= start <= ranges[i][1] and 
                               ranges[i][0] <= end <= ranges[i][1]):
                            return False
                    elif '/' in value:
                        # Step
                        base, step = value.split('/')
                        if base != '*':
                            base_val = int(base)
                            if not (ranges[i][0] <= base_val <= ranges[i][1]):
                                return False
                        step_val = int(step)
                        if step_val <= 0:
                            return False
                    else:
                        # Single value
                        val = int(value)
                        if not (ranges[i][0] <= val <= ranges[i][1]):
                            return False
            
            return True
            
        except Exception:
            return False
    
    def get_next_run_time(self, job_name: str) -> Optional[str]:
        """
        Get the next scheduled run time for a job.
        
        Args:
            job_name: Name of the job
            
        Returns:
            Next run time as ISO string, or None if not available
        """
        # This would require a more sophisticated cron parser
        # For now, return a placeholder
        if job_name in self.jobs:
            return "Next run time calculation not implemented"
        return None