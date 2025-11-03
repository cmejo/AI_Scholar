#!/usr/bin/env python3
"""
System Cleanup Script for automated maintenance.

Performs system cleanup including old files, logs, and temporary data.
"""

import argparse
import logging
import sys
import shutil
import os
from pathlib import Path
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cleanup_old_logs(log_dir: Path, retention_days: int, dry_run: bool = False) -> int:
    """Clean up old log files."""
    logger.info(f"Cleaning up logs older than {retention_days} days in {log_dir}")
    
    if not log_dir.exists():
        logger.warning(f"Log directory does not exist: {log_dir}")
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    cleaned_count = 0
    
    try:
        for log_file in log_dir.rglob("*.log"):
            try:
                # Check file modification time
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                
                if mtime < cutoff_date:
                    if dry_run:
                        logger.info(f"Would delete old log: {log_file}")
                    else:
                        log_file.unlink()
                        logger.debug(f"Deleted old log: {log_file}")
                    cleaned_count += 1
                    
            except Exception as e:
                logger.warning(f"Could not process log file {log_file}: {e}")
        
        logger.info(f"Cleaned up {cleaned_count} old log files")
        return cleaned_count
        
    except Exception as e:
        logger.error(f"Failed to cleanup logs in {log_dir}: {e}")
        return 0


def cleanup_temporary_files(temp_dirs: list, dry_run: bool = False) -> int:
    """Clean up temporary files and directories."""
    logger.info("Cleaning up temporary files")
    
    cleaned_count = 0
    
    for temp_dir in temp_dirs:
        temp_path = Path(temp_dir)
        
        if not temp_path.exists():
            continue
        
        try:
            # Clean up files older than 1 day
            cutoff_date = datetime.now() - timedelta(days=1)
            
            for temp_file in temp_path.rglob("*"):
                if temp_file.is_file():
                    try:
                        mtime = datetime.fromtimestamp(temp_file.stat().st_mtime)
                        
                        if mtime < cutoff_date:
                            if dry_run:
                                logger.info(f"Would delete temp file: {temp_file}")
                            else:
                                temp_file.unlink()
                                logger.debug(f"Deleted temp file: {temp_file}")
                            cleaned_count += 1
                            
                    except Exception as e:
                        logger.warning(f"Could not process temp file {temp_file}: {e}")
            
            # Clean up empty directories
            for temp_dir_path in temp_path.rglob("*"):
                if temp_dir_path.is_dir() and not any(temp_dir_path.iterdir()):
                    if dry_run:
                        logger.info(f"Would delete empty dir: {temp_dir_path}")
                    else:
                        temp_dir_path.rmdir()
                        logger.debug(f"Deleted empty dir: {temp_dir_path}")
                    cleaned_count += 1
                    
        except Exception as e:
            logger.error(f"Failed to cleanup temp directory {temp_dir}: {e}")
    
    logger.info(f"Cleaned up {cleaned_count} temporary files/directories")
    return cleaned_count


def cleanup_old_reports(report_dir: Path, retention_days: int, dry_run: bool = False) -> int:
    """Clean up old report files."""
    logger.info(f"Cleaning up reports older than {retention_days} days in {report_dir}")
    
    if not report_dir.exists():
        logger.warning(f"Report directory does not exist: {report_dir}")
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    cleaned_count = 0
    
    try:
        for report_file in report_dir.glob("*"):
            if report_file.is_file():
                try:
                    mtime = datetime.fromtimestamp(report_file.stat().st_mtime)
                    
                    if mtime < cutoff_date:
                        if dry_run:
                            logger.info(f"Would delete old report: {report_file}")
                        else:
                            report_file.unlink()
                            logger.debug(f"Deleted old report: {report_file}")
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.warning(f"Could not process report file {report_file}: {e}")
        
        logger.info(f"Cleaned up {cleaned_count} old report files")
        return cleaned_count
        
    except Exception as e:
        logger.error(f"Failed to cleanup reports in {report_dir}: {e}")
        return 0


def cleanup_old_state_files(state_dirs: list, retention_days: int, dry_run: bool = False) -> int:
    """Clean up old state files while preserving recent ones."""
    logger.info(f"Cleaning up state files older than {retention_days} days")
    
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    cleaned_count = 0
    
    for state_dir in state_dirs:
        state_path = Path(state_dir)
        
        if not state_path.exists():
            continue
        
        try:
            # Look for state files (but preserve the most recent ones)
            state_files = list(state_path.glob("*.json"))
            state_files.extend(state_path.glob("*.state"))
            
            # Sort by modification time (newest first)
            state_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Keep the 5 most recent state files, clean up older ones
            for state_file in state_files[5:]:
                try:
                    mtime = datetime.fromtimestamp(state_file.stat().st_mtime)
                    
                    if mtime < cutoff_date:
                        if dry_run:
                            logger.info(f"Would delete old state file: {state_file}")
                        else:
                            state_file.unlink()
                            logger.debug(f"Deleted old state file: {state_file}")
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.warning(f"Could not process state file {state_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup state files in {state_dir}: {e}")
    
    logger.info(f"Cleaned up {cleaned_count} old state files")
    return cleaned_count


def get_disk_usage(path: Path) -> dict:
    """Get disk usage statistics for a path."""
    try:
        usage = shutil.disk_usage(path)
        return {
            'total_gb': usage.total / (1024**3),
            'used_gb': usage.used / (1024**3),
            'free_gb': usage.free / (1024**3),
            'percent_used': (usage.used / usage.total) * 100
        }
    except Exception as e:
        logger.error(f"Failed to get disk usage for {path}: {e}")
        return {}


def main():
    """Main entry point for system cleanup."""
    parser = argparse.ArgumentParser(description="Perform system cleanup and maintenance")
    
    parser.add_argument(
        '--log-retention-days',
        type=int,
        default=30,
        help='Number of days to retain log files'
    )
    
    parser.add_argument(
        '--report-retention-days',
        type=int,
        default=90,
        help='Number of days to retain report files'
    )
    
    parser.add_argument(
        '--state-retention-days',
        type=int,
        default=7,
        help='Number of days to retain old state files'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be cleaned up without making changes'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting system cleanup")
    
    if args.dry_run:
        logger.info("DRY RUN - No actual cleanup will be performed")
    
    try:
        total_cleaned = 0
        
        # Define directories to clean
        log_dirs = [
            Path("/var/log/multi_instance_arxiv"),
            Path("/datapool/aischolar/ai-scholar-arxiv-dataset/logs"),
            Path("/datapool/aischolar/quant-scholar-dataset/logs")
        ]
        
        temp_dirs = [
            "/tmp/multi_instance_locks",
            "/tmp/arxiv_downloads",
            "/tmp/pdf_processing"
        ]
        
        state_dirs = [
            "/datapool/aischolar/ai-scholar-arxiv-dataset/state",
            "/datapool/aischolar/quant-scholar-dataset/state"
        ]
        
        report_dirs = [
            Path("/var/log/multi_instance_arxiv/reports")
        ]
        
        # Show disk usage before cleanup
        logger.info("Disk usage before cleanup:")
        for path in [Path("/"), Path("/datapool")] if Path("/datapool").exists() else [Path("/")]:
            usage = get_disk_usage(path)
            if usage:
                logger.info(f"  {path}: {usage['used_gb']:.1f}GB used ({usage['percent_used']:.1f}%)")
        
        # Clean up logs
        for log_dir in log_dirs:
            cleaned = cleanup_old_logs(log_dir, args.log_retention_days, args.dry_run)
            total_cleaned += cleaned
        
        # Clean up temporary files
        cleaned = cleanup_temporary_files(temp_dirs, args.dry_run)
        total_cleaned += cleaned
        
        # Clean up old reports
        for report_dir in report_dirs:
            cleaned = cleanup_old_reports(report_dir, args.report_retention_days, args.dry_run)
            total_cleaned += cleaned
        
        # Clean up old state files
        cleaned = cleanup_old_state_files(state_dirs, args.state_retention_days, args.dry_run)
        total_cleaned += cleaned
        
        # Show disk usage after cleanup
        if not args.dry_run:
            logger.info("Disk usage after cleanup:")
            for path in [Path("/"), Path("/datapool")] if Path("/datapool").exists() else [Path("/")]:
                usage = get_disk_usage(path)
                if usage:
                    logger.info(f"  {path}: {usage['used_gb']:.1f}GB used ({usage['percent_used']:.1f}%)")
        
        logger.info(f"System cleanup completed successfully - {total_cleaned} items cleaned")
        return 0
        
    except Exception as e:
        logger.error(f"System cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)