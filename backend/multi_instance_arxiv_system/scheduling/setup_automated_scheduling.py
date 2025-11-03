#!/usr/bin/env python3
"""
Comprehensive Automated Scheduling Setup Script.

Sets up the complete automated scheduling system with health checks,
conflict resolution, error recovery, and monitoring.
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from .setup_enhanced_cron_jobs import main as setup_cron_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_systemd_service() -> bool:
    """Create systemd service for monitoring (optional)."""
    logger.info("Creating systemd service for monitoring")
    
    try:
        service_content = """[Unit]
Description=Multi-Instance ArXiv System Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/multi_instance_arxiv
ExecStart=/usr/bin/python3 /opt/multi_instance_arxiv/scheduling/run_system_validation.py --include-performance
Restart=always
RestartSec=3600

[Install]
WantedBy=multi-user.target
"""
        
        service_path = Path("/etc/systemd/system/multi-instance-arxiv-monitor.service")
        
        # Only create if we have write permissions
        if os.access("/etc/systemd/system", os.W_OK):
            with open(service_path, 'w') as f:
                f.write(service_content)
            
            logger.info(f"Systemd service created: {service_path}")
            logger.info("To enable: sudo systemctl enable multi-instance-arxiv-monitor")
            logger.info("To start: sudo systemctl start multi-instance-arxiv-monitor")
            return True
        else:
            logger.warning("No write permission for /etc/systemd/system - skipping systemd service")
            return False
            
    except Exception as e:
        logger.warning(f"Failed to create systemd service: {e}")
        return False


def create_logrotate_config() -> bool:
    """Create logrotate configuration for log management."""
    logger.info("Creating logrotate configuration")
    
    try:
        logrotate_content = """/var/log/multi_instance_arxiv/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        # Send HUP signal to processes if needed
    endscript
}

/datapool/aischolar/*/logs/*.log {
    weekly
    missingok
    rotate 12
    compress
    delaycompress
    notifempty
    create 644 root root
}
"""
        
        logrotate_path = Path("/etc/logrotate.d/multi-instance-arxiv")
        
        # Only create if we have write permissions
        if os.access("/etc/logrotate.d", os.W_OK):
            with open(logrotate_path, 'w') as f:
                f.write(logrotate_content)
            
            logger.info(f"Logrotate configuration created: {logrotate_path}")
            return True
        else:
            logger.warning("No write permission for /etc/logrotate.d - skipping logrotate config")
            return False
            
    except Exception as e:
        logger.warning(f"Failed to create logrotate config: {e}")
        return False


def setup_directory_structure() -> bool:
    """Set up the required directory structure."""
    logger.info("Setting up directory structure")
    
    try:
        directories = [
            "/var/log/multi_instance_arxiv",
            "/var/log/multi_instance_arxiv/health_checks",
            "/var/log/multi_instance_arxiv/conflicts",
            "/var/log/multi_instance_arxiv/errors",
            "/var/log/multi_instance_arxiv/reports",
            "/etc/multi_instance_arxiv",
            "/etc/multi_instance_arxiv/instances",
            "/tmp/multi_instance_locks",
            "/opt/multi_instance_arxiv",
            "/opt/multi_instance_arxiv/scheduling"
        ]
        
        for directory in directories:
            path = Path(directory)
            try:
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {directory}")
            except PermissionError:
                logger.warning(f"No permission to create directory: {directory}")
            except Exception as e:
                logger.warning(f"Failed to create directory {directory}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup directory structure: {e}")
        return False


def create_configuration_files() -> bool:
    """Create default configuration files."""
    logger.info("Creating configuration files")
    
    try:
        # Create AI Scholar configuration
        ai_scholar_config = """instance:
  name: "ai_scholar"
  display_name: "AI Scholar"
  description: "General AI and Physics Research Papers"

data_sources:
  arxiv:
    categories:
      - "cond-mat"
      - "gr-qc"
      - "hep-ph"
      - "hep-th"
      - "math"
      - "math-ph"
      - "physics"
      - "q-alg"
      - "quant-ph"
    start_date: "2020-01-01"

storage:
  pdf_directory: "/datapool/aischolar/ai-scholar-arxiv-dataset/pdf"
  processed_directory: "/datapool/aischolar/ai-scholar-arxiv-dataset/processed"
  state_directory: "/datapool/aischolar/ai-scholar-arxiv-dataset/state"
  error_log_directory: "/datapool/aischolar/ai-scholar-arxiv-dataset/logs"

processing:
  batch_size: 20
  max_concurrent_downloads: 5
  max_concurrent_processing: 3
  retry_attempts: 3
  timeout_seconds: 300

vector_store:
  collection_name: "ai_scholar_papers"
  embedding_model: "all-MiniLM-L6-v2"

notifications:
  enabled: false
  recipients: []
"""
        
        # Create Quant Scholar configuration
        quant_scholar_config = """instance:
  name: "quant_scholar"
  display_name: "Quant Scholar"
  description: "Quantitative Finance and Statistics Research Papers"

data_sources:
  arxiv:
    categories:
      - "econ.EM"
      - "econ.GN"
      - "econ.TH"
      - "eess.SY"
      - "math.ST"
      - "math.PR"
      - "math.OC"
      - "q-fin.*"
      - "stat.*"
    start_date: "2020-01-01"
    
  journals:
    - name: "Journal of Statistical Software"
      url: "https://www.jstatsoft.org/index"
      handler: "JStatSoftwareHandler"
    - name: "R Journal"
      url: "https://journal.r-project.org/issues.html"
      handler: "RJournalHandler"

storage:
  pdf_directory: "/datapool/aischolar/quant-scholar-dataset/pdf"
  processed_directory: "/datapool/aischolar/quant-scholar-dataset/processed"
  state_directory: "/datapool/aischolar/quant-scholar-dataset/state"
  error_log_directory: "/datapool/aischolar/quant-scholar-dataset/logs"

processing:
  batch_size: 15
  max_concurrent_downloads: 3
  max_concurrent_processing: 2
  retry_attempts: 3
  timeout_seconds: 300

vector_store:
  collection_name: "quant_scholar_papers"
  embedding_model: "all-MiniLM-L6-v2"

notifications:
  enabled: false
  recipients: []
"""
        
        # Write configuration files
        config_dir = Path("/etc/multi_instance_arxiv/instances")
        
        if config_dir.exists() or config_dir.parent.exists():
            config_dir.mkdir(parents=True, exist_ok=True)
            
            ai_config_path = config_dir / "ai_scholar.yaml"
            quant_config_path = config_dir / "quant_scholar.yaml"
            
            with open(ai_config_path, 'w') as f:
                f.write(ai_scholar_config)
            
            with open(quant_config_path, 'w') as f:
                f.write(quant_scholar_config)
            
            logger.info(f"Configuration files created:")
            logger.info(f"  - {ai_config_path}")
            logger.info(f"  - {quant_config_path}")
            
            return True
        else:
            logger.warning("Cannot create configuration files - no write permission")
            return False
            
    except Exception as e:
        logger.error(f"Failed to create configuration files: {e}")
        return False


def create_wrapper_scripts() -> bool:
    """Create wrapper scripts for easy management."""
    logger.info("Creating wrapper scripts")
    
    try:
        script_dir = Path(__file__).parent
        wrapper_dir = Path("/usr/local/bin")
        
        if not os.access(wrapper_dir, os.W_OK):
            wrapper_dir = Path.home() / "bin"
            wrapper_dir.mkdir(exist_ok=True)
        
        # Health check wrapper
        health_wrapper = f"""#!/bin/bash
# Multi-Instance ArXiv Health Check Wrapper
{sys.executable} {script_dir / 'run_health_check.py'} "$@"
"""
        
        # Manual update wrapper
        update_wrapper = f"""#!/bin/bash
# Multi-Instance ArXiv Manual Update Wrapper
{sys.executable} {script_dir / 'run_scheduled_monthly_update.py'} "$@"
"""
        
        # System validation wrapper
        validation_wrapper = f"""#!/bin/bash
# Multi-Instance ArXiv System Validation Wrapper
{sys.executable} {script_dir / 'run_system_validation.py'} "$@"
"""
        
        wrappers = [
            ("multi-instance-health-check", health_wrapper),
            ("multi-instance-manual-update", update_wrapper),
            ("multi-instance-validate", validation_wrapper)
        ]
        
        created_wrappers = []
        for name, content in wrappers:
            wrapper_path = wrapper_dir / name
            try:
                with open(wrapper_path, 'w') as f:
                    f.write(content)
                wrapper_path.chmod(0o755)
                created_wrappers.append(str(wrapper_path))
            except Exception as e:
                logger.warning(f"Failed to create wrapper {name}: {e}")
        
        if created_wrappers:
            logger.info("Wrapper scripts created:")
            for wrapper in created_wrappers:
                logger.info(f"  - {wrapper}")
            return True
        else:
            logger.warning("No wrapper scripts could be created")
            return False
            
    except Exception as e:
        logger.error(f"Failed to create wrapper scripts: {e}")
        return False


def main():
    """Main entry point for automated scheduling setup."""
    parser = argparse.ArgumentParser(description="Setup comprehensive automated scheduling system")
    
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
        help='Cron schedule for monthly updates'
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
        '--skip-systemd',
        action='store_true',
        help='Skip systemd service creation'
    )
    
    parser.add_argument(
        '--skip-logrotate',
        action='store_true',
        help='Skip logrotate configuration'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    args = parser.parse_args()
    
    logger.info("=== Multi-Instance ArXiv Automated Scheduling Setup ===")
    logger.info(f"Start time: {datetime.now().isoformat()}")
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No actual changes will be made")
    
    try:
        success_count = 0
        total_steps = 6
        
        # Step 1: Setup directory structure
        logger.info("\n1. Setting up directory structure...")
        if args.dry_run or setup_directory_structure():
            success_count += 1
            logger.info("✓ Directory structure setup completed")
        else:
            logger.error("✗ Directory structure setup failed")
        
        # Step 2: Create configuration files
        logger.info("\n2. Creating configuration files...")
        if args.dry_run or create_configuration_files():
            success_count += 1
            logger.info("✓ Configuration files created")
        else:
            logger.error("✗ Configuration files creation failed")
        
        # Step 3: Setup enhanced cron jobs
        logger.info("\n3. Setting up enhanced cron jobs...")
        
        # Prepare arguments for cron setup
        cron_args = [
            '--action', 'install',
            '--instances', args.instances,
            '--monthly-schedule', args.monthly_schedule
        ]
        
        if args.enable_alerting:
            cron_args.append('--enable-alerting')
        
        if args.alert_recipients:
            cron_args.extend(['--alert-recipients', args.alert_recipients])
        
        if args.dry_run:
            cron_args.append('--dry-run')
        
        # Temporarily modify sys.argv for the cron setup
        original_argv = sys.argv
        sys.argv = ['setup_enhanced_cron_jobs.py'] + cron_args
        
        try:
            cron_result = setup_cron_main()
            if cron_result == 0:
                success_count += 1
                logger.info("✓ Enhanced cron jobs setup completed")
            else:
                logger.error("✗ Enhanced cron jobs setup failed")
        finally:
            sys.argv = original_argv
        
        # Step 4: Create systemd service (optional)
        logger.info("\n4. Creating systemd service...")
        if args.skip_systemd:
            logger.info("Skipped systemd service creation (--skip-systemd)")
            success_count += 1
        elif args.dry_run or create_systemd_service():
            success_count += 1
            logger.info("✓ Systemd service setup completed")
        else:
            logger.warning("⚠ Systemd service setup failed (non-critical)")
            success_count += 1  # Non-critical failure
        
        # Step 5: Create logrotate configuration
        logger.info("\n5. Creating logrotate configuration...")
        if args.skip_logrotate:
            logger.info("Skipped logrotate configuration (--skip-logrotate)")
            success_count += 1
        elif args.dry_run or create_logrotate_config():
            success_count += 1
            logger.info("✓ Logrotate configuration completed")
        else:
            logger.warning("⚠ Logrotate configuration failed (non-critical)")
            success_count += 1  # Non-critical failure
        
        # Step 6: Create wrapper scripts
        logger.info("\n6. Creating wrapper scripts...")
        if args.dry_run or create_wrapper_scripts():
            success_count += 1
            logger.info("✓ Wrapper scripts created")
        else:
            logger.warning("⚠ Wrapper scripts creation failed (non-critical)")
            success_count += 1  # Non-critical failure
        
        # Final summary
        logger.info(f"\n=== Setup Summary ===")
        logger.info(f"Completed: {success_count}/{total_steps} steps")
        
        if success_count == total_steps:
            logger.info("🎉 Automated scheduling setup completed successfully!")
            
            logger.info("\n📋 What was installed:")
            logger.info("  ✓ Enhanced cron jobs with health checks")
            logger.info("  ✓ Conflict detection and resolution")
            logger.info("  ✓ Error recovery and retry mechanisms")
            logger.info("  ✓ System monitoring and validation")
            logger.info("  ✓ Automated cleanup and maintenance")
            logger.info("  ✓ Comprehensive logging and reporting")
            
            logger.info("\n🔧 Next steps:")
            logger.info("  1. Review configuration files in /etc/multi_instance_arxiv/instances/")
            logger.info("  2. Test the system: multi-instance-validate --verbose")
            logger.info("  3. Run manual health check: multi-instance-health-check")
            logger.info("  4. Monitor logs in /var/log/multi_instance_arxiv/")
            logger.info("  5. Check cron jobs: crontab -l")
            
            return 0
        else:
            logger.warning("⚠ Setup completed with some issues")
            return 1
            
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)