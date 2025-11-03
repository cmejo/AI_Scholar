#!/usr/bin/env python3
"""
Storage Manager for Multi-Instance ArXiv System

This script provides comprehensive storage management including cleanup,
optimization, archival, and monitoring capabilities.
"""

import sys
import os
import argparse
import asyncio
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.core.instance_config import InstanceConfigManager
    from multi_instance_arxiv_system.monitoring.storage_monitor import StorageMonitor
    from multi_instance_arxiv_system.storage.data_retention_manager import DataRetentionManager
    from multi_instance_arxiv_system.reporting.email_notification_service import EmailNotificationService
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure the multi-instance ArXiv system is properly installed.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/storage_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StorageManager:
    """Comprehensive storage management for multi-instance ArXiv system."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_manager = InstanceConfigManager(config_dir)
        self.storage_monitor = StorageMonitor()
        self.retention_manager = DataRetentionManager()
        self.email_service = EmailNotificationService()
        
        # Load instance configurations
        self.instances = self.config_manager.get_all_instances()
        
        logger.info(f"StorageManager initialized with {len(self.instances)} instances")
    
    async def analyze_storage_usage(self, instance_name: Optional[str] = None) -> Dict[str, Any]:
        """Analyze storage usage across instances."""
        logger.info("Analyzing storage usage")
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'instances': {},
            'total_usage': {
                'total_size_gb': 0,
                'total_files': 0,
                'breakdown': {}
            },
            'recommendations': []
        }
        
        # Analyze specific instance or all instances
        instances_to_analyze = [instance_name] if instance_name else list(self.instances.keys())
        
        for instance in instances_to_analyze:
            if instance not in self.instances:
                logger.warning(f"Instance {instance} not found")
                continue
            
            instance_analysis = await self._analyze_instance_storage(instance)
            analysis['instances'][instance] = instance_analysis
            
            # Add to totals
            analysis['total_usage']['total_size_gb'] += instance_analysis.get('total_size_gb', 0)
            analysis['total_usage']['total_files'] += instance_analysis.get('total_files', 0)
        
        # Generate storage breakdown
        analysis['total_usage']['breakdown'] = self._calculate_storage_breakdown(analysis['instances'])
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_storage_recommendations(analysis)
        
        logger.info(f"Storage analysis completed. Total usage: {analysis['total_usage']['total_size_gb']:.2f} GB")
        return analysis    

    async def _analyze_instance_storage(self, instance_name: str) -> Dict[str, Any]:
        """Analyze storage usage for a specific instance."""
        logger.info(f"Analyzing storage for instance: {instance_name}")
        
        config = self.instances[instance_name]
        storage_path = Path(config.storage_path)
        
        analysis = {
            'instance_name': instance_name,
            'storage_path': str(storage_path),
            'total_size_gb': 0,
            'total_files': 0,
            'directories': {},
            'file_types': {},
            'age_distribution': {},
            'large_files': [],
            'issues': []
        }
        
        if not storage_path.exists():
            analysis['issues'].append(f"Storage path does not exist: {storage_path}")
            return analysis
        
        try:
            # Analyze directory structure
            for item in storage_path.rglob('*'):
                if item.is_file():
                    file_size = item.stat().st_size
                    file_size_gb = file_size / (1024**3)
                    
                    analysis['total_size_gb'] += file_size_gb
                    analysis['total_files'] += 1
                    
                    # Directory breakdown
                    relative_path = item.relative_to(storage_path)
                    dir_name = str(relative_path.parts[0]) if relative_path.parts else 'root'
                    
                    if dir_name not in analysis['directories']:
                        analysis['directories'][dir_name] = {'size_gb': 0, 'files': 0}
                    
                    analysis['directories'][dir_name]['size_gb'] += file_size_gb
                    analysis['directories'][dir_name]['files'] += 1
                    
                    # File type breakdown
                    file_ext = item.suffix.lower() or 'no_extension'
                    if file_ext not in analysis['file_types']:
                        analysis['file_types'][file_ext] = {'size_gb': 0, 'files': 0}
                    
                    analysis['file_types'][file_ext]['size_gb'] += file_size_gb
                    analysis['file_types'][file_ext]['files'] += 1
                    
                    # Age distribution
                    file_age_days = (datetime.now() - datetime.fromtimestamp(item.stat().st_mtime)).days
                    age_bucket = self._get_age_bucket(file_age_days)
                    
                    if age_bucket not in analysis['age_distribution']:
                        analysis['age_distribution'][age_bucket] = {'size_gb': 0, 'files': 0}
                    
                    analysis['age_distribution'][age_bucket]['size_gb'] += file_size_gb
                    analysis['age_distribution'][age_bucket]['files'] += 1
                    
                    # Track large files (>100MB)
                    if file_size_gb > 0.1:
                        analysis['large_files'].append({
                            'path': str(relative_path),
                            'size_gb': file_size_gb,
                            'age_days': file_age_days
                        })
            
            # Sort large files by size
            analysis['large_files'].sort(key=lambda x: x['size_gb'], reverse=True)
            analysis['large_files'] = analysis['large_files'][:20]  # Keep top 20
        
        except Exception as e:
            logger.error(f"Error analyzing storage for {instance_name}: {e}")
            analysis['issues'].append(f"Analysis error: {str(e)}")
        
        return analysis
    
    def _get_age_bucket(self, age_days: int) -> str:
        """Get age bucket for file age distribution."""
        if age_days < 7:
            return "< 1 week"
        elif age_days < 30:
            return "1-4 weeks"
        elif age_days < 90:
            return "1-3 months"
        elif age_days < 365:
            return "3-12 months"
        else:
            return "> 1 year"
    
    def _calculate_storage_breakdown(self, instances: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall storage breakdown across instances."""
        breakdown = {
            'by_instance': {},
            'by_file_type': {},
            'by_age': {}
        }
        
        for instance_name, instance_data in instances.items():
            # By instance
            breakdown['by_instance'][instance_name] = {
                'size_gb': instance_data.get('total_size_gb', 0),
                'files': instance_data.get('total_files', 0)
            }
            
            # By file type
            for file_type, type_data in instance_data.get('file_types', {}).items():
                if file_type not in breakdown['by_file_type']:
                    breakdown['by_file_type'][file_type] = {'size_gb': 0, 'files': 0}
                
                breakdown['by_file_type'][file_type]['size_gb'] += type_data['size_gb']
                breakdown['by_file_type'][file_type]['files'] += type_data['files']
            
            # By age
            for age_bucket, age_data in instance_data.get('age_distribution', {}).items():
                if age_bucket not in breakdown['by_age']:
                    breakdown['by_age'][age_bucket] = {'size_gb': 0, 'files': 0}
                
                breakdown['by_age'][age_bucket]['size_gb'] += age_data['size_gb']
                breakdown['by_age'][age_bucket]['files'] += age_data['files']
        
        return breakdown
    
    def _generate_storage_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate storage optimization recommendations."""
        recommendations = []
        
        total_size = analysis['total_usage']['total_size_gb']
        breakdown = analysis['total_usage']['breakdown']
        
        # Check overall usage
        if total_size > 100:  # More than 100GB
            recommendations.append(f"Large storage usage detected: {total_size:.2f} GB")
        
        # Check for old files
        old_files_size = breakdown.get('by_age', {}).get('> 1 year', {}).get('size_gb', 0)
        if old_files_size > 10:  # More than 10GB of old files
            recommendations.append(
                f"Consider archiving old files: {old_files_size:.2f} GB older than 1 year"
            )
        
        # Check for large file types
        for file_type, type_data in breakdown.get('by_file_type', {}).items():
            if type_data['size_gb'] > 20:  # More than 20GB of one file type
                recommendations.append(
                    f"Large {file_type} files: {type_data['size_gb']:.2f} GB "
                    f"({type_data['files']} files)"
                )
        
        # Instance-specific recommendations
        for instance_name, instance_data in analysis['instances'].items():
            instance_size = instance_data.get('total_size_gb', 0)
            
            if instance_size > 50:  # More than 50GB per instance
                recommendations.append(
                    f"Instance {instance_name} using {instance_size:.2f} GB - "
                    "consider cleanup or archival"
                )
            
            # Check for large files in instance
            large_files = instance_data.get('large_files', [])
            if large_files and large_files[0]['size_gb'] > 1:  # Files larger than 1GB
                recommendations.append(
                    f"Large files in {instance_name}: "
                    f"{large_files[0]['path']} ({large_files[0]['size_gb']:.2f} GB)"
                )
        
        return recommendations 
   
    async def cleanup_storage(
        self, 
        instance_name: Optional[str] = None,
        dry_run: bool = True,
        max_age_days: int = 365,
        min_free_space_gb: float = 10.0
    ) -> Dict[str, Any]:
        """Clean up storage by removing old or unnecessary files."""
        logger.info(f"Starting storage cleanup (dry_run={dry_run})")
        
        cleanup_report = {
            'timestamp': datetime.now().isoformat(),
            'dry_run': dry_run,
            'instances': {},
            'total_cleaned': {
                'files_removed': 0,
                'space_freed_gb': 0
            },
            'errors': []
        }
        
        # Clean specific instance or all instances
        instances_to_clean = [instance_name] if instance_name else list(self.instances.keys())
        
        for instance in instances_to_clean:
            if instance not in self.instances:
                logger.warning(f"Instance {instance} not found")
                continue
            
            try:
                instance_cleanup = await self._cleanup_instance_storage(
                    instance, dry_run, max_age_days, min_free_space_gb
                )
                cleanup_report['instances'][instance] = instance_cleanup
                
                # Add to totals
                cleanup_report['total_cleaned']['files_removed'] += instance_cleanup.get('files_removed', 0)
                cleanup_report['total_cleaned']['space_freed_gb'] += instance_cleanup.get('space_freed_gb', 0)
            
            except Exception as e:
                error_msg = f"Error cleaning {instance}: {str(e)}"
                logger.error(error_msg)
                cleanup_report['errors'].append(error_msg)
        
        logger.info(f"Storage cleanup completed. "
                   f"Files removed: {cleanup_report['total_cleaned']['files_removed']}, "
                   f"Space freed: {cleanup_report['total_cleaned']['space_freed_gb']:.2f} GB")
        
        return cleanup_report
    
    async def _cleanup_instance_storage(
        self,
        instance_name: str,
        dry_run: bool,
        max_age_days: int,
        min_free_space_gb: float
    ) -> Dict[str, Any]:
        """Clean up storage for a specific instance."""
        logger.info(f"Cleaning storage for instance: {instance_name}")
        
        config = self.instances[instance_name]
        storage_path = Path(config.storage_path)
        
        cleanup_result = {
            'instance_name': instance_name,
            'files_removed': 0,
            'space_freed_gb': 0,
            'cleanup_actions': [],
            'skipped_files': [],
            'errors': []
        }
        
        if not storage_path.exists():
            cleanup_result['errors'].append(f"Storage path does not exist: {storage_path}")
            return cleanup_result
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        try:
            # Clean temporary files
            temp_patterns = ['*.tmp', '*.temp', '*.lock', '.DS_Store', 'Thumbs.db']
            for pattern in temp_patterns:
                for temp_file in storage_path.rglob(pattern):
                    if temp_file.is_file():
                        file_size_gb = temp_file.stat().st_size / (1024**3)
                        
                        if not dry_run:
                            temp_file.unlink()
                        
                        cleanup_result['files_removed'] += 1
                        cleanup_result['space_freed_gb'] += file_size_gb
                        cleanup_result['cleanup_actions'].append(f"Removed temp file: {temp_file.name}")
            
            # Clean old log files
            log_dir = storage_path / "logs"
            if log_dir.exists():
                for log_file in log_dir.glob("*.log"):
                    if log_file.is_file():
                        file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                        
                        if file_mtime < cutoff_date:
                            file_size_gb = log_file.stat().st_size / (1024**3)
                            
                            if not dry_run:
                                log_file.unlink()
                            
                            cleanup_result['files_removed'] += 1
                            cleanup_result['space_freed_gb'] += file_size_gb
                            cleanup_result['cleanup_actions'].append(f"Removed old log: {log_file.name}")
            
            # Clean old cache files
            cache_dir = storage_path / "cache"
            if cache_dir.exists():
                for cache_file in cache_dir.rglob("*"):
                    if cache_file.is_file():
                        file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                        
                        if file_mtime < cutoff_date:
                            file_size_gb = cache_file.stat().st_size / (1024**3)
                            
                            if not dry_run:
                                cache_file.unlink()
                            
                            cleanup_result['files_removed'] += 1
                            cleanup_result['space_freed_gb'] += file_size_gb
                            cleanup_result['cleanup_actions'].append(f"Removed old cache: {cache_file.name}")
            
            # Clean duplicate files (basic implementation)
            await self._clean_duplicate_files(storage_path, cleanup_result, dry_run)
            
            # Clean empty directories
            if not dry_run:
                self._remove_empty_directories(storage_path)
        
        except Exception as e:
            error_msg = f"Error during cleanup: {str(e)}"
            logger.error(error_msg)
            cleanup_result['errors'].append(error_msg)
        
        return cleanup_result
    
    async def _clean_duplicate_files(
        self, 
        storage_path: Path, 
        cleanup_result: Dict[str, Any], 
        dry_run: bool
    ) -> None:
        """Clean duplicate files based on size and name similarity."""
        # Simple duplicate detection based on file size and name
        size_groups = {}
        
        for file_path in storage_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.pdf', '.txt', '.json']:
                file_size = file_path.stat().st_size
                
                if file_size not in size_groups:
                    size_groups[file_size] = []
                
                size_groups[file_size].append(file_path)
        
        # Check groups with multiple files of same size
        for size, files in size_groups.items():
            if len(files) > 1:
                # Sort by modification time, keep newest
                files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                
                # Check if files have similar names (potential duplicates)
                for i in range(1, len(files)):
                    if self._are_likely_duplicates(files[0], files[i]):
                        file_size_gb = files[i].stat().st_size / (1024**3)
                        
                        if not dry_run:
                            files[i].unlink()
                        
                        cleanup_result['files_removed'] += 1
                        cleanup_result['space_freed_gb'] += file_size_gb
                        cleanup_result['cleanup_actions'].append(
                            f"Removed duplicate: {files[i].name}"
                        )
    
    def _are_likely_duplicates(self, file1: Path, file2: Path) -> bool:
        """Check if two files are likely duplicates based on name similarity."""
        name1 = file1.stem.lower()
        name2 = file2.stem.lower()
        
        # Simple similarity check
        if name1 == name2:
            return True
        
        # Check for common duplicate patterns
        duplicate_patterns = ['_copy', '_duplicate', ' (1)', ' (2)', '_backup']
        
        for pattern in duplicate_patterns:
            if pattern in name1 or pattern in name2:
                base1 = name1.replace(pattern, '')
                base2 = name2.replace(pattern, '')
                if base1 == base2:
                    return True
        
        return False
    
    def _remove_empty_directories(self, storage_path: Path) -> None:
        """Remove empty directories recursively."""
        for dir_path in storage_path.rglob("*"):
            if dir_path.is_dir():
                try:
                    if not any(dir_path.iterdir()):  # Directory is empty
                        dir_path.rmdir()
                        logger.debug(f"Removed empty directory: {dir_path}")
                except OSError:
                    # Directory not empty or permission error
                    pass    
 
   async def optimize_storage(self, instance_name: Optional[str] = None) -> Dict[str, Any]:
        """Optimize storage by compressing and reorganizing files."""
        logger.info("Starting storage optimization")
        
        optimization_report = {
            'timestamp': datetime.now().isoformat(),
            'instances': {},
            'total_optimized': {
                'files_compressed': 0,
                'space_saved_gb': 0,
                'files_reorganized': 0
            },
            'errors': []
        }
        
        # Optimize specific instance or all instances
        instances_to_optimize = [instance_name] if instance_name else list(self.instances.keys())
        
        for instance in instances_to_optimize:
            if instance not in self.instances:
                logger.warning(f"Instance {instance} not found")
                continue
            
            try:
                instance_optimization = await self._optimize_instance_storage(instance)
                optimization_report['instances'][instance] = instance_optimization
                
                # Add to totals
                optimization_report['total_optimized']['files_compressed'] += instance_optimization.get('files_compressed', 0)
                optimization_report['total_optimized']['space_saved_gb'] += instance_optimization.get('space_saved_gb', 0)
                optimization_report['total_optimized']['files_reorganized'] += instance_optimization.get('files_reorganized', 0)
            
            except Exception as e:
                error_msg = f"Error optimizing {instance}: {str(e)}"
                logger.error(error_msg)
                optimization_report['errors'].append(error_msg)
        
        logger.info(f"Storage optimization completed. "
                   f"Files compressed: {optimization_report['total_optimized']['files_compressed']}, "
                   f"Space saved: {optimization_report['total_optimized']['space_saved_gb']:.2f} GB")
        
        return optimization_report
    
    async def _optimize_instance_storage(self, instance_name: str) -> Dict[str, Any]:
        """Optimize storage for a specific instance."""
        logger.info(f"Optimizing storage for instance: {instance_name}")
        
        config = self.instances[instance_name]
        storage_path = Path(config.storage_path)
        
        optimization_result = {
            'instance_name': instance_name,
            'files_compressed': 0,
            'space_saved_gb': 0,
            'files_reorganized': 0,
            'optimization_actions': [],
            'errors': []
        }
        
        if not storage_path.exists():
            optimization_result['errors'].append(f"Storage path does not exist: {storage_path}")
            return optimization_result
        
        try:
            # Compress old log files
            await self._compress_old_logs(storage_path, optimization_result)
            
            # Reorganize files by date
            await self._reorganize_files_by_date(storage_path, optimization_result)
            
            # Create directory structure if needed
            await self._ensure_directory_structure(storage_path, optimization_result)
        
        except Exception as e:
            error_msg = f"Error during optimization: {str(e)}"
            logger.error(error_msg)
            optimization_result['errors'].append(error_msg)
        
        return optimization_result
    
    async def _compress_old_logs(self, storage_path: Path, result: Dict[str, Any]) -> None:
        """Compress old log files to save space."""
        import gzip
        
        log_dir = storage_path / "logs"
        if not log_dir.exists():
            return
        
        cutoff_date = datetime.now() - timedelta(days=7)  # Compress logs older than 7 days
        
        for log_file in log_dir.glob("*.log"):
            if log_file.is_file():
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                
                if file_mtime < cutoff_date:
                    original_size = log_file.stat().st_size
                    compressed_path = log_file.with_suffix('.log.gz')
                    
                    if not compressed_path.exists():
                        try:
                            with open(log_file, 'rb') as f_in:
                                with gzip.open(compressed_path, 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                            
                            compressed_size = compressed_path.stat().st_size
                            space_saved = (original_size - compressed_size) / (1024**3)
                            
                            log_file.unlink()  # Remove original
                            
                            result['files_compressed'] += 1
                            result['space_saved_gb'] += space_saved
                            result['optimization_actions'].append(
                                f"Compressed log: {log_file.name} "
                                f"(saved {space_saved:.2f} GB)"
                            )
                        
                        except Exception as e:
                            result['errors'].append(f"Failed to compress {log_file.name}: {str(e)}")
    
    async def _reorganize_files_by_date(self, storage_path: Path, result: Dict[str, Any]) -> None:
        """Reorganize files into date-based directory structure."""
        papers_dir = storage_path / "papers"
        if not papers_dir.exists():
            return
        
        # Look for PDF files that aren't already organized
        for pdf_file in papers_dir.glob("*.pdf"):
            if pdf_file.is_file():
                file_mtime = datetime.fromtimestamp(pdf_file.stat().st_mtime)
                year_month = file_mtime.strftime("%Y-%m")
                
                # Create year-month directory
                target_dir = papers_dir / year_month
                target_dir.mkdir(exist_ok=True)
                
                target_path = target_dir / pdf_file.name
                
                if not target_path.exists():
                    try:
                        shutil.move(str(pdf_file), str(target_path))
                        
                        result['files_reorganized'] += 1
                        result['optimization_actions'].append(
                            f"Moved {pdf_file.name} to {year_month}/"
                        )
                    
                    except Exception as e:
                        result['errors'].append(f"Failed to move {pdf_file.name}: {str(e)}")
    
    async def _ensure_directory_structure(self, storage_path: Path, result: Dict[str, Any]) -> None:
        """Ensure proper directory structure exists."""
        required_dirs = [
            "papers",
            "logs",
            "cache",
            "reports",
            "backups"
        ]
        
        for dir_name in required_dirs:
            dir_path = storage_path / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                result['optimization_actions'].append(f"Created directory: {dir_name}")
    
    async def generate_storage_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive storage report."""
        logger.info("Generating storage report")
        
        # Analyze storage usage
        analysis = await self.analyze_storage_usage()
        
        # Add additional information
        report = {
            'storage_analysis': analysis,
            'system_info': await self._get_system_storage_info(),
            'cleanup_recommendations': self._generate_cleanup_recommendations(analysis),
            'optimization_suggestions': self._generate_optimization_suggestions(analysis)
        }
        
        # Save report if output file specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Storage report saved to {output_file}")
        
        return json.dumps(report, indent=2, default=str)
    
    async def _get_system_storage_info(self) -> Dict[str, Any]:
        """Get system-wide storage information."""
        try:
            # Get disk usage for the system
            total, used, free = shutil.disk_usage("/")
            
            return {
                'total_disk_gb': total / (1024**3),
                'used_disk_gb': used / (1024**3),
                'free_disk_gb': free / (1024**3),
                'usage_percent': (used / total) * 100
            }
        
        except Exception as e:
            logger.error(f"Error getting system storage info: {e}")
            return {'error': str(e)}
    
    def _generate_cleanup_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate cleanup recommendations based on analysis."""
        recommendations = []
        
        # Check for old files
        breakdown = analysis['total_usage']['breakdown']
        old_files = breakdown.get('by_age', {}).get('> 1 year', {})
        
        if old_files.get('size_gb', 0) > 5:
            recommendations.append(
                f"Archive or delete files older than 1 year: {old_files['size_gb']:.2f} GB"
            )
        
        # Check for large file types
        for file_type, type_data in breakdown.get('by_file_type', {}).items():
            if file_type in ['.log', '.tmp', '.cache'] and type_data['size_gb'] > 1:
                recommendations.append(
                    f"Clean up {file_type} files: {type_data['size_gb']:.2f} GB"
                )
        
        # Instance-specific recommendations
        for instance_name, instance_data in analysis['instances'].items():
            large_files = instance_data.get('large_files', [])
            
            if large_files:
                top_file = large_files[0]
                if top_file['size_gb'] > 1 and top_file['age_days'] > 30:
                    recommendations.append(
                        f"Review large file in {instance_name}: "
                        f"{top_file['path']} ({top_file['size_gb']:.2f} GB, "
                        f"{top_file['age_days']} days old)"
                    )
        
        return recommendations
    
    def _generate_optimization_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate optimization suggestions based on analysis."""
        suggestions = []
        
        total_size = analysis['total_usage']['total_size_gb']
        
        if total_size > 50:
            suggestions.append("Consider implementing automated compression for old files")
        
        if total_size > 100:
            suggestions.append("Consider implementing data archival to external storage")
        
        # Check for unorganized files
        for instance_name, instance_data in analysis['instances'].items():
            directories = instance_data.get('directories', {})
            
            if 'root' in directories and directories['root']['size_gb'] > 5:
                suggestions.append(
                    f"Organize files in {instance_name} root directory into subdirectories"
                )
        
        suggestions.append("Set up automated storage monitoring and alerting")
        suggestions.append("Implement regular cleanup schedules")
        
        return suggestions

async 
def main():
    """Main entry point for the storage manager script."""
    parser = argparse.ArgumentParser(description="Multi-Instance ArXiv Storage Manager")
    
    parser.add_argument(
        '--config-dir',
        default='config',
        help='Configuration directory path'
    )
    
    parser.add_argument(
        '--instance',
        help='Target specific instance only'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze storage usage')
    analyze_parser.add_argument(
        '--output',
        help='Output file for analysis report'
    )
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up storage')
    cleanup_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be cleaned without actually doing it'
    )
    cleanup_parser.add_argument(
        '--max-age-days',
        type=int,
        default=365,
        help='Maximum age in days for files to keep'
    )
    cleanup_parser.add_argument(
        '--min-free-space',
        type=float,
        default=10.0,
        help='Minimum free space in GB to maintain'
    )
    
    # Optimize command
    optimize_parser = subparsers.add_parser('optimize', help='Optimize storage')
    optimize_parser.add_argument(
        '--output',
        help='Output file for optimization report'
    )
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate storage report')
    report_parser.add_argument(
        '--output',
        help='Output file for storage report'
    )
    
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
        manager = StorageManager(args.config_dir)
        
        if args.command == 'analyze':
            logger.info("Running storage analysis")
            analysis = await manager.analyze_storage_usage(args.instance)
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(analysis, f, indent=2, default=str)
                print(f"Analysis saved to {args.output}")
            else:
                print(json.dumps(analysis, indent=2, default=str))
        
        elif args.command == 'cleanup':
            logger.info("Running storage cleanup")
            cleanup_report = await manager.cleanup_storage(
                instance_name=args.instance,
                dry_run=args.dry_run,
                max_age_days=args.max_age_days,
                min_free_space_gb=args.min_free_space
            )
            
            print(json.dumps(cleanup_report, indent=2, default=str))
            
            if cleanup_report['total_cleaned']['files_removed'] > 0:
                print(f"\nSummary:")
                print(f"Files removed: {cleanup_report['total_cleaned']['files_removed']}")
                print(f"Space freed: {cleanup_report['total_cleaned']['space_freed_gb']:.2f} GB")
                
                if args.dry_run:
                    print("(This was a dry run - no files were actually removed)")
        
        elif args.command == 'optimize':
            logger.info("Running storage optimization")
            optimization_report = await manager.optimize_storage(args.instance)
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(optimization_report, f, indent=2, default=str)
                print(f"Optimization report saved to {args.output}")
            else:
                print(json.dumps(optimization_report, indent=2, default=str))
        
        elif args.command == 'report':
            logger.info("Generating storage report")
            report = await manager.generate_storage_report(args.output)
            
            if not args.output:
                print(report)
    
    except Exception as e:
        logger.error(f"Storage manager failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())