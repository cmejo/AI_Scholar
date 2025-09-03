#!/usr/bin/env python3
"""
Maintenance Automation System
Automates routine maintenance tasks for code quality management.
"""

import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import sqlite3
import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('maintenance.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MaintenanceAutomation:
    """Automated maintenance system for ongoing code quality management."""
    
    def __init__(self, project_root: Path, config_file: Optional[Path] = None):
        self.project_root = project_root
        self.config_file = config_file or project_root / "monitoring-config.yml"
        self.config = self._load_config()
        self.db_path = project_root / "monitoring.db"
        
    def _load_config(self) -> Dict[str, Any]:
        """Load maintenance configuration."""
        try:
            import yaml
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
        
        # Default configuration
        return {
            "maintenance": {
                "auto_fix_enabled": True,
                "auto_update_dependencies": False,
                "auto_format_code": True,
                "backup_before_fixes": True,
                "max_auto_fixes_per_cycle": 10,
                "backup_retention_days": 7
            },
            "scheduling": {
                "daily_maintenance": "02:00",
                "weekly_deep_clean": "Sunday 03:00",
                "dependency_check": "Monday 04:00"
            }
        }
    
    def create_backup(self, backup_name: Optional[str] = None) -> bool:
        """Create a backup of the current codebase."""
        try:
            backup_dir = self.project_root / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"maintenance_backup_{timestamp}"
            
            backup_path = backup_dir / f"{backup_name}.tar.gz"
            
            # Create compressed backup excluding unnecessary files
            exclude_patterns = [
                "--exclude=node_modules",
                "--exclude=venv",
                "--exclude=.git",
                "--exclude=backups",
                "--exclude=*.pyc",
                "--exclude=__pycache__",
                "--exclude=.pytest_cache",
                "--exclude=coverage",
                "--exclude=dist",
                "--exclude=build"
            ]
            
            cmd = ["tar", "-czf", str(backup_path)] + exclude_patterns + ["."]
            
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Backup created successfully: {backup_path}")
                return True
            else:
                logger.error(f"Backup creation failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False
    
    def cleanup_old_backups(self) -> int:
        """Clean up old backup files based on retention policy."""
        try:
            backup_dir = self.project_root / "backups"
            if not backup_dir.exists():
                return 0
            
            retention_days = self.config["maintenance"].get("backup_retention_days", 7)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            removed_count = 0
            for backup_file in backup_dir.glob("*.tar.gz"):
                # Get file modification time
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                
                if file_time < cutoff_date:
                    backup_file.unlink()
                    logger.info(f"Removed old backup: {backup_file.name}")
                    removed_count += 1
            
            logger.info(f"Cleaned up {removed_count} old backup files")
            return removed_count
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            return 0
    
    def auto_format_code(self) -> Dict[str, Any]:
        """Automatically format code using configured formatters."""
        results = {
            "python_formatted": False,
            "javascript_formatted": False,
            "errors": []
        }
        
        try:
            # Format Python code with black
            backend_path = self.project_root / "backend"
            if backend_path.exists():
                result = subprocess.run([
                    "python", "-m", "black", "."
                ], cwd=backend_path, capture_output=True, text=True)
                
                if result.returncode == 0:
                    results["python_formatted"] = True
                    logger.info("Python code formatted successfully")
                else:
                    results["errors"].append(f"Python formatting failed: {result.stderr}")
            
            # Format JavaScript/TypeScript code with prettier
            if (self.project_root / "package.json").exists():
                result = subprocess.run([
                    "npm", "run", "format"
                ], cwd=self.project_root, capture_output=True, text=True)
                
                if result.returncode == 0:
                    results["javascript_formatted"] = True
                    logger.info("JavaScript/TypeScript code formatted successfully")
                else:
                    results["errors"].append(f"JavaScript formatting failed: {result.stderr}")
            
        except Exception as e:
            results["errors"].append(str(e))
            logger.error(f"Code formatting failed: {e}")
        
        return results
    
    def apply_auto_fixes(self) -> Dict[str, Any]:
        """Apply automated fixes for common issues."""
        results = {
            "fixes_applied": 0,
            "fixes_attempted": 0,
            "errors": []
        }
        
        try:
            max_fixes = self.config["maintenance"].get("max_auto_fixes_per_cycle", 10)
            
            # Run the automated fix engine
            fix_script = self.project_root / "scripts" / "automated_fix_engine.py"
            if not fix_script.exists():
                results["errors"].append("Automated fix engine not found")
                return results
            
            result = subprocess.run([
                "python", str(fix_script), 
                "--auto-apply", 
                "--max-fixes", str(max_fixes)
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse output to count fixes
                output = result.stdout
                if "fixes applied:" in output.lower():
                    import re
                    match = re.search(r'(\d+)\s+fixes applied', output.lower())
                    if match:
                        results["fixes_applied"] = int(match.group(1))
                
                if "fixes attempted:" in output.lower():
                    match = re.search(r'(\d+)\s+fixes attempted', output.lower())
                    if match:
                        results["fixes_attempted"] = int(match.group(1))
                
                logger.info(f"Auto-fixes completed: {results['fixes_applied']} applied, {results['fixes_attempted']} attempted")
            else:
                results["errors"].append(f"Auto-fix execution failed: {result.stderr}")
            
        except Exception as e:
            results["errors"].append(str(e))
            logger.error(f"Auto-fix application failed: {e}")
        
        return results
    
    def update_dependencies(self) -> Dict[str, Any]:
        """Update project dependencies safely."""
        results = {
            "npm_updated": False,
            "python_updated": False,
            "security_updates": 0,
            "errors": []
        }
        
        try:
            # Update npm dependencies
            if (self.project_root / "package.json").exists():
                # First, audit for security vulnerabilities
                audit_result = subprocess.run([
                    "npm", "audit", "--json"
                ], cwd=self.project_root, capture_output=True, text=True)
                
                if audit_result.returncode == 0:
                    try:
                        audit_data = json.loads(audit_result.stdout)
                        vulnerabilities = audit_data.get("metadata", {}).get("vulnerabilities", {})
                        total_vulns = sum(vulnerabilities.values()) if isinstance(vulnerabilities, dict) else 0
                        
                        if total_vulns > 0:
                            # Apply security fixes
                            fix_result = subprocess.run([
                                "npm", "audit", "fix"
                            ], cwd=self.project_root, capture_output=True, text=True)
                            
                            if fix_result.returncode == 0:
                                results["security_updates"] = total_vulns
                                logger.info(f"Applied {total_vulns} npm security fixes")
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse npm audit output")
                
                # Update dependencies
                update_result = subprocess.run([
                    "npm", "update"
                ], cwd=self.project_root, capture_output=True, text=True)
                
                if update_result.returncode == 0:
                    results["npm_updated"] = True
                    logger.info("npm dependencies updated successfully")
                else:
                    results["errors"].append(f"npm update failed: {update_result.stderr}")
            
            # Update Python dependencies
            backend_path = self.project_root / "backend"
            requirements_file = backend_path / "requirements.txt"
            
            if requirements_file.exists():
                # Check for outdated packages
                outdated_result = subprocess.run([
                    "pip", "list", "--outdated", "--format=json"
                ], cwd=backend_path, capture_output=True, text=True)
                
                if outdated_result.returncode == 0:
                    try:
                        outdated_packages = json.loads(outdated_result.stdout)
                        if outdated_packages:
                            logger.info(f"Found {len(outdated_packages)} outdated Python packages")
                            
                            # Update packages (conservative approach - only security updates)
                            for package in outdated_packages:
                                package_name = package["name"]
                                # Only update if it's a security-related package or explicitly allowed
                                if any(sec_pkg in package_name.lower() for sec_pkg in ["security", "crypto", "ssl", "auth"]):
                                    update_result = subprocess.run([
                                        "pip", "install", "--upgrade", package_name
                                    ], cwd=backend_path, capture_output=True, text=True)
                                    
                                    if update_result.returncode == 0:
                                        logger.info(f"Updated Python package: {package_name}")
                            
                            results["python_updated"] = True
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse pip outdated output")
            
        except Exception as e:
            results["errors"].append(str(e))
            logger.error(f"Dependency update failed: {e}")
        
        return results
    
    def cleanup_temporary_files(self) -> Dict[str, Any]:
        """Clean up temporary files and caches."""
        results = {
            "files_removed": 0,
            "space_freed_mb": 0,
            "errors": []
        }
        
        try:
            # Patterns for temporary files to remove
            cleanup_patterns = [
                "**/*.pyc",
                "**/__pycache__",
                "**/.pytest_cache",
                "**/node_modules/.cache",
                "**/.mypy_cache",
                "**/coverage/.nyc_output",
                "**/*.log.old",
                "**/*.tmp",
                "**/dist",
                "**/build"
            ]
            
            total_size = 0
            files_removed = 0
            
            for pattern in cleanup_patterns:
                for path in self.project_root.glob(pattern):
                    if path.is_file():
                        size = path.stat().st_size
                        path.unlink()
                        total_size += size
                        files_removed += 1
                    elif path.is_dir():
                        size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                        shutil.rmtree(path)
                        total_size += size
                        files_removed += 1
            
            results["files_removed"] = files_removed
            results["space_freed_mb"] = round(total_size / (1024 * 1024), 2)
            
            logger.info(f"Cleanup completed: {files_removed} items removed, {results['space_freed_mb']} MB freed")
            
        except Exception as e:
            results["errors"].append(str(e))
            logger.error(f"Temporary file cleanup failed: {e}")
        
        return results
    
    def run_quality_analysis(self) -> Dict[str, Any]:
        """Run quality analysis to check current state."""
        try:
            monitoring_script = self.project_root / "scripts" / "continuous_monitoring_system.py"
            if not monitoring_script.exists():
                return {"error": "Monitoring system not found"}
            
            result = subprocess.run([
                "python", str(monitoring_script), "--project-root", str(self.project_root)
            ], capture_output=True, text=True, timeout=1800)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {"error": f"Quality analysis failed: {result.stderr}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def log_maintenance_activity(self, activity_type: str, results: Dict[str, Any]):
        """Log maintenance activity to database."""
        try:
            if not self.db_path.exists():
                return
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS maintenance_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        activity_type TEXT NOT NULL,
                        results TEXT NOT NULL,
                        success BOOLEAN NOT NULL
                    )
                """)
                
                success = len(results.get("errors", [])) == 0
                
                conn.execute("""
                    INSERT INTO maintenance_log (timestamp, activity_type, results, success)
                    VALUES (?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    activity_type,
                    json.dumps(results),
                    success
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to log maintenance activity: {e}")
    
    def run_daily_maintenance(self) -> Dict[str, Any]:
        """Run daily maintenance tasks."""
        logger.info("Starting daily maintenance...")
        
        maintenance_results = {
            "timestamp": datetime.now().isoformat(),
            "tasks": {}
        }
        
        # Create backup if enabled
        if self.config["maintenance"].get("backup_before_fixes", True):
            backup_success = self.create_backup()
            maintenance_results["tasks"]["backup"] = {"success": backup_success}
        
        # Auto-format code
        if self.config["maintenance"].get("auto_format_code", True):
            format_results = self.auto_format_code()
            maintenance_results["tasks"]["formatting"] = format_results
            self.log_maintenance_activity("formatting", format_results)
        
        # Apply auto-fixes
        if self.config["maintenance"].get("auto_fix_enabled", True):
            fix_results = self.apply_auto_fixes()
            maintenance_results["tasks"]["auto_fixes"] = fix_results
            self.log_maintenance_activity("auto_fixes", fix_results)
        
        # Clean up temporary files
        cleanup_results = self.cleanup_temporary_files()
        maintenance_results["tasks"]["cleanup"] = cleanup_results
        self.log_maintenance_activity("cleanup", cleanup_results)
        
        # Clean up old backups
        backup_cleanup_count = self.cleanup_old_backups()
        maintenance_results["tasks"]["backup_cleanup"] = {"files_removed": backup_cleanup_count}
        
        # Run quality analysis to check current state
        quality_results = self.run_quality_analysis()
        maintenance_results["tasks"]["quality_check"] = quality_results
        
        logger.info("Daily maintenance completed")
        return maintenance_results
    
    def run_weekly_maintenance(self) -> Dict[str, Any]:
        """Run weekly deep maintenance tasks."""
        logger.info("Starting weekly maintenance...")
        
        # Run daily maintenance first
        maintenance_results = self.run_daily_maintenance()
        
        # Update dependencies if enabled
        if self.config["maintenance"].get("auto_update_dependencies", False):
            dependency_results = self.update_dependencies()
            maintenance_results["tasks"]["dependency_updates"] = dependency_results
            self.log_maintenance_activity("dependency_updates", dependency_results)
        
        logger.info("Weekly maintenance completed")
        return maintenance_results
    
    def setup_scheduled_maintenance(self):
        """Set up scheduled maintenance tasks."""
        config = self.config.get("scheduling", {})
        
        # Daily maintenance
        daily_time = config.get("daily_maintenance", "02:00")
        schedule.every().day.at(daily_time).do(self.run_daily_maintenance)
        logger.info(f"Scheduled daily maintenance at {daily_time}")
        
        # Weekly maintenance
        weekly_schedule = config.get("weekly_deep_clean", "Sunday 03:00")
        if " " in weekly_schedule:
            day, time = weekly_schedule.split(" ", 1)
            getattr(schedule.every(), day.lower()).at(time).do(self.run_weekly_maintenance)
            logger.info(f"Scheduled weekly maintenance on {weekly_schedule}")
        
        # Dependency check
        dependency_schedule = config.get("dependency_check", "Monday 04:00")
        if " " in dependency_schedule:
            day, time = dependency_schedule.split(" ", 1)
            getattr(schedule.every(), day.lower()).at(time).do(self.update_dependencies)
            logger.info(f"Scheduled dependency check on {dependency_schedule}")
    
    def run_daemon(self):
        """Run maintenance daemon with scheduled tasks."""
        logger.info("Starting maintenance automation daemon...")
        
        self.setup_scheduled_maintenance()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Maintenance daemon stopped by user")
        except Exception as e:
            logger.error(f"Maintenance daemon error: {e}")


def main():
    """Main entry point for maintenance automation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Maintenance Automation System")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root directory")
    parser.add_argument("--config", type=Path, help="Configuration file path")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon with scheduled tasks")
    parser.add_argument("--daily", action="store_true", help="Run daily maintenance tasks")
    parser.add_argument("--weekly", action="store_true", help="Run weekly maintenance tasks")
    parser.add_argument("--backup", action="store_true", help="Create backup only")
    parser.add_argument("--format", action="store_true", help="Format code only")
    parser.add_argument("--fix", action="store_true", help="Apply auto-fixes only")
    parser.add_argument("--cleanup", action="store_true", help="Clean up temporary files only")
    parser.add_argument("--update-deps", action="store_true", help="Update dependencies only")
    
    args = parser.parse_args()
    
    # Initialize maintenance system
    maintenance = MaintenanceAutomation(args.project_root, args.config)
    
    if args.daemon:
        maintenance.run_daemon()
    elif args.daily:
        result = maintenance.run_daily_maintenance()
        print(json.dumps(result, indent=2))
    elif args.weekly:
        result = maintenance.run_weekly_maintenance()
        print(json.dumps(result, indent=2))
    elif args.backup:
        success = maintenance.create_backup()
        print(f"Backup {'successful' if success else 'failed'}")
    elif args.format:
        result = maintenance.auto_format_code()
        print(json.dumps(result, indent=2))
    elif args.fix:
        result = maintenance.apply_auto_fixes()
        print(json.dumps(result, indent=2))
    elif args.cleanup:
        result = maintenance.cleanup_temporary_files()
        print(json.dumps(result, indent=2))
    elif args.update_deps:
        result = maintenance.update_dependencies()
        print(json.dumps(result, indent=2))
    else:
        # Run daily maintenance by default
        result = maintenance.run_daily_maintenance()
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()