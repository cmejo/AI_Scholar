"""
Update Reporter for multi-instance ArXiv system.

Generates comprehensive update reports with statistics comparison,
error summaries, and storage monitoring recommendations.
"""

import logging
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import statistics

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from ..shared.multi_instance_data_models import (
    UpdateReport, StorageStats, PerformanceMetrics, InstanceStats
)

logger = logging.getLogger(__name__)


@dataclass
class ComparisonMetrics:
    """Metrics comparing current update with historical data."""
    papers_processed_change: float = 0.0  # Percentage change
    processing_time_change: float = 0.0
    error_rate_change: float = 0.0
    storage_growth_mb: float = 0.0
    performance_trend: str = "stable"  # "improving", "declining", "stable"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'papers_processed_change': self.papers_processed_change,
            'processing_time_change': self.processing_time_change,
            'error_rate_change': self.error_rate_change,
            'storage_growth_mb': self.storage_growth_mb,
            'performance_trend': self.performance_trend
        }


@dataclass
class SystemSummary:
    """Overall system summary across all instances."""
    total_instances: int = 0
    successful_instances: int = 0
    failed_instances: int = 0
    total_papers_processed: int = 0
    total_errors: int = 0
    total_processing_time_hours: float = 0.0
    total_storage_used_gb: float = 0.0
    overall_health_status: str = "unknown"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_instances == 0:
            return 0.0
        return (self.successful_instances / self.total_instances) * 100.0
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage."""
        if self.total_papers_processed == 0:
            return 0.0
        return (self.total_errors / self.total_papers_processed) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'total_instances': self.total_instances,
            'successful_instances': self.successful_instances,
            'failed_instances': self.failed_instances,
            'success_rate': self.success_rate,
            'total_papers_processed': self.total_papers_processed,
            'total_errors': self.total_errors,
            'error_rate': self.error_rate,
            'total_processing_time_hours': self.total_processing_time_hours,
            'total_storage_used_gb': self.total_storage_used_gb,
            'overall_health_status': self.overall_health_status
        }


@dataclass
class StorageRecommendation:
    """Storage cleanup and optimization recommendation."""
    recommendation_type: str  # "cleanup", "archive", "optimize", "alert"
    priority: str  # "low", "medium", "high", "critical"
    description: str
    estimated_space_savings_gb: float = 0.0
    action_required: bool = False
    commands: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'recommendation_type': self.recommendation_type,
            'priority': self.priority,
            'description': self.description,
            'estimated_space_savings_gb': self.estimated_space_savings_gb,
            'action_required': self.action_required,
            'commands': self.commands
        }


@dataclass
class ComprehensiveUpdateReport:
    """Comprehensive update report with analysis and recommendations."""
    report_id: str
    generated_at: datetime
    system_summary: SystemSummary
    instance_reports: Dict[str, UpdateReport] = field(default_factory=dict)
    comparison_metrics: Dict[str, ComparisonMetrics] = field(default_factory=dict)
    storage_recommendations: List[StorageRecommendation] = field(default_factory=list)
    error_analysis: Dict[str, Any] = field(default_factory=dict)
    performance_insights: Dict[str, Any] = field(default_factory=dict)
    next_update_predictions: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'report_id': self.report_id,
            'generated_at': self.generated_at.isoformat(),
            'system_summary': self.system_summary.to_dict(),
            'instance_reports': {k: v.to_dict() for k, v in self.instance_reports.items()},
            'comparison_metrics': {k: v.to_dict() for k, v in self.comparison_metrics.items()},
            'storage_recommendations': [r.to_dict() for r in self.storage_recommendations],
            'error_analysis': self.error_analysis,
            'performance_insights': self.performance_insights,
            'next_update_predictions': self.next_update_predictions
        }


class UpdateReporter:
    """Generates comprehensive update reports with analysis and recommendations."""
    
    def __init__(self, reports_directory: str = "/var/log/multi_instance_arxiv/reports"):
        """
        Initialize update reporter.
        
        Args:
            reports_directory: Directory to store generated reports
        """
        self.reports_directory = Path(reports_directory)
        self.reports_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"UpdateReporter initialized with directory: {reports_directory}")
    
    async def generate_comprehensive_report(self, 
                                          instance_reports: Dict[str, UpdateReport],
                                          orchestration_id: str) -> ComprehensiveUpdateReport:
        """
        Generate comprehensive update report with analysis.
        
        Args:
            instance_reports: Dictionary of instance reports
            orchestration_id: ID of the orchestration run
            
        Returns:
            ComprehensiveUpdateReport with detailed analysis
        """
        report_id = f"comprehensive_report_{orchestration_id}"
        
        logger.info(f"Generating comprehensive report: {report_id}")
        
        # Create system summary
        system_summary = self._create_system_summary(instance_reports)
        
        # Create comprehensive report
        comprehensive_report = ComprehensiveUpdateReport(
            report_id=report_id,
            generated_at=datetime.now(),
            system_summary=system_summary,
            instance_reports=instance_reports
        )
        
        # Add comparison metrics
        comprehensive_report.comparison_metrics = await self._generate_comparison_metrics(instance_reports)
        
        # Add storage recommendations
        comprehensive_report.storage_recommendations = await self._generate_storage_recommendations(instance_reports)
        
        # Add error analysis
        comprehensive_report.error_analysis = await self._analyze_errors(instance_reports)
        
        # Add performance insights
        comprehensive_report.performance_insights = await self._analyze_performance(instance_reports)
        
        # Add predictions for next update
        comprehensive_report.next_update_predictions = await self._predict_next_update(instance_reports)
        
        # Save report
        await self._save_report(comprehensive_report)
        
        logger.info(f"Comprehensive report generated successfully: {report_id}")
        return comprehensive_report
    
    def _create_system_summary(self, instance_reports: Dict[str, UpdateReport]) -> SystemSummary:
        """Create system-wide summary from instance reports."""
        summary = SystemSummary()
        
        summary.total_instances = len(instance_reports)
        
        for instance_name, report in instance_reports.items():
            # Count successful vs failed instances
            if len(report.errors) == 0 and report.papers_processed > 0:
                summary.successful_instances += 1
            else:
                summary.failed_instances += 1
            
            # Aggregate metrics
            summary.total_papers_processed += report.papers_processed
            summary.total_errors += len(report.errors)
            summary.total_processing_time_hours += report.processing_time_seconds / 3600.0
            summary.total_storage_used_gb += report.storage_used_mb / 1024.0
        
        # Determine overall health status
        if summary.success_rate >= 90:
            summary.overall_health_status = "excellent"
        elif summary.success_rate >= 75:
            summary.overall_health_status = "good"
        elif summary.success_rate >= 50:
            summary.overall_health_status = "fair"
        else:
            summary.overall_health_status = "poor"
        
        return summary
    
    async def _generate_comparison_metrics(self, 
                                         instance_reports: Dict[str, UpdateReport]) -> Dict[str, ComparisonMetrics]:
        """Generate comparison metrics against historical data."""
        comparison_metrics = {}
        
        for instance_name, current_report in instance_reports.items():
            try:
                # Load historical reports for comparison
                historical_reports = await self._load_historical_reports(instance_name, days=30)
                
                if not historical_reports:
                    # No historical data available
                    comparison_metrics[instance_name] = ComparisonMetrics()
                    continue
                
                # Calculate comparison metrics
                metrics = ComparisonMetrics()
                
                # Papers processed change
                avg_historical_papers = statistics.mean([r.papers_processed for r in historical_reports])
                if avg_historical_papers > 0:
                    metrics.papers_processed_change = (
                        (current_report.papers_processed - avg_historical_papers) / avg_historical_papers * 100
                    )
                
                # Processing time change
                avg_historical_time = statistics.mean([r.processing_time_seconds for r in historical_reports])
                if avg_historical_time > 0:
                    metrics.processing_time_change = (
                        (current_report.processing_time_seconds - avg_historical_time) / avg_historical_time * 100
                    )
                
                # Error rate change
                current_error_rate = len(current_report.errors) / max(current_report.papers_processed, 1) * 100
                historical_error_rates = [
                    len(r.errors) / max(r.papers_processed, 1) * 100 for r in historical_reports
                ]
                avg_historical_error_rate = statistics.mean(historical_error_rates)
                
                if avg_historical_error_rate > 0:
                    metrics.error_rate_change = (
                        (current_error_rate - avg_historical_error_rate) / avg_historical_error_rate * 100
                    )
                
                # Storage growth
                if historical_reports:
                    latest_historical = max(historical_reports, key=lambda r: r.update_date)
                    metrics.storage_growth_mb = current_report.storage_used_mb - latest_historical.storage_used_mb
                
                # Performance trend
                if (metrics.papers_processed_change > 5 and 
                    metrics.processing_time_change < -5 and 
                    metrics.error_rate_change < -10):
                    metrics.performance_trend = "improving"
                elif (metrics.papers_processed_change < -5 or 
                      metrics.processing_time_change > 20 or 
                      metrics.error_rate_change > 20):
                    metrics.performance_trend = "declining"
                else:
                    metrics.performance_trend = "stable"
                
                comparison_metrics[instance_name] = metrics
                
            except Exception as e:
                logger.error(f"Failed to generate comparison metrics for {instance_name}: {e}")
                comparison_metrics[instance_name] = ComparisonMetrics()
        
        return comparison_metrics
    
    async def _generate_storage_recommendations(self, 
                                              instance_reports: Dict[str, UpdateReport]) -> List[StorageRecommendation]:
        """Generate storage cleanup and optimization recommendations."""
        recommendations = []
        
        try:
            total_storage_gb = sum(report.storage_used_mb / 1024.0 for report in instance_reports.values())
            
            # Check overall storage usage
            for instance_name, report in instance_reports.items():
                storage_gb = report.storage_used_mb / 1024.0
                
                # High storage usage recommendation
                if storage_gb > 50:  # More than 50GB
                    recommendations.append(StorageRecommendation(
                        recommendation_type="cleanup",
                        priority="high",
                        description=f"Instance '{instance_name}' is using {storage_gb:.1f}GB of storage. Consider cleaning up old files.",
                        estimated_space_savings_gb=storage_gb * 0.3,  # Estimate 30% savings
                        action_required=True,
                        commands=[
                            f"find /datapool/aischolar/{instance_name}-dataset/pdf -type f -mtime +90 -delete",
                            f"find /datapool/aischolar/{instance_name}-dataset/logs -type f -mtime +30 -delete"
                        ]
                    ))
                
                # Archive old processed data
                if storage_gb > 20:
                    recommendations.append(StorageRecommendation(
                        recommendation_type="archive",
                        priority="medium",
                        description=f"Archive old processed data for '{instance_name}' to free up space.",
                        estimated_space_savings_gb=storage_gb * 0.2,
                        action_required=False,
                        commands=[
                            f"tar -czf /datapool/aischolar/{instance_name}-archive-$(date +%Y%m%d).tar.gz /datapool/aischolar/{instance_name}-dataset/processed/",
                            f"find /datapool/aischolar/{instance_name}-dataset/processed -type f -mtime +60 -delete"
                        ]
                    ))
            
            # System-wide recommendations
            if total_storage_gb > 100:
                recommendations.append(StorageRecommendation(
                    recommendation_type="alert",
                    priority="critical",
                    description=f"Total system storage usage is {total_storage_gb:.1f}GB. Immediate cleanup required.",
                    estimated_space_savings_gb=total_storage_gb * 0.4,
                    action_required=True,
                    commands=[
                        "df -h /datapool",
                        "du -sh /datapool/aischolar/*/",
                        "find /datapool -type f -name '*.log' -mtime +7 -delete"
                    ]
                ))
            
            # Optimization recommendations
            recommendations.append(StorageRecommendation(
                recommendation_type="optimize",
                priority="low",
                description="Regular maintenance to optimize storage performance.",
                estimated_space_savings_gb=5.0,
                action_required=False,
                commands=[
                    "find /tmp -type f -name '*arxiv*' -mtime +1 -delete",
                    "find /var/log/multi_instance_arxiv -type f -name '*.log' -mtime +30 -delete",
                    "docker system prune -f"
                ]
            ))
            
        except Exception as e:
            logger.error(f"Failed to generate storage recommendations: {e}")
        
        return recommendations
    
    async def _analyze_errors(self, instance_reports: Dict[str, UpdateReport]) -> Dict[str, Any]:
        """Analyze errors across all instances."""
        error_analysis = {
            'total_errors': 0,
            'error_by_instance': {},
            'common_error_patterns': {},
            'error_trends': {},
            'critical_errors': []
        }
        
        try:
            all_errors = []
            
            for instance_name, report in instance_reports.items():
                instance_errors = len(report.errors)
                error_analysis['total_errors'] += instance_errors
                error_analysis['error_by_instance'][instance_name] = instance_errors
                
                # Collect all error messages for pattern analysis
                for error in report.errors:
                    error_msg = error.get('error_message', '') if isinstance(error, dict) else str(error)
                    all_errors.append({
                        'instance': instance_name,
                        'message': error_msg,
                        'timestamp': error.get('timestamp', '') if isinstance(error, dict) else ''
                    })
                    
                    # Identify critical errors
                    if any(keyword in error_msg.lower() for keyword in ['critical', 'fatal', 'memory', 'disk']):
                        error_analysis['critical_errors'].append({
                            'instance': instance_name,
                            'error': error_msg,
                            'severity': 'critical'
                        })
            
            # Analyze error patterns
            error_keywords = {}
            for error in all_errors:
                words = error['message'].lower().split()
                for word in words:
                    if len(word) > 3:  # Skip short words
                        error_keywords[word] = error_keywords.get(word, 0) + 1
            
            # Get most common error patterns
            sorted_keywords = sorted(error_keywords.items(), key=lambda x: x[1], reverse=True)
            error_analysis['common_error_patterns'] = dict(sorted_keywords[:10])
            
            # Error trends (simplified)
            error_analysis['error_trends'] = {
                'instances_with_errors': len([name for name, count in error_analysis['error_by_instance'].items() if count > 0]),
                'average_errors_per_instance': error_analysis['total_errors'] / len(instance_reports) if instance_reports else 0,
                'error_distribution': 'even' if len(set(error_analysis['error_by_instance'].values())) <= 2 else 'uneven'
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze errors: {e}")
        
        return error_analysis
    
    async def _analyze_performance(self, instance_reports: Dict[str, UpdateReport]) -> Dict[str, Any]:
        """Analyze performance metrics across instances."""
        performance_insights = {
            'processing_rates': {},
            'efficiency_metrics': {},
            'resource_utilization': {},
            'bottlenecks': [],
            'recommendations': []
        }
        
        try:
            processing_times = []
            papers_processed = []
            
            for instance_name, report in instance_reports.items():
                # Processing rate (papers per hour)
                if report.processing_time_seconds > 0:
                    rate = (report.papers_processed / report.processing_time_seconds) * 3600
                    performance_insights['processing_rates'][instance_name] = rate
                    processing_times.append(report.processing_time_seconds)
                    papers_processed.append(report.papers_processed)
                
                # Efficiency (papers per MB of storage)
                if report.storage_used_mb > 0:
                    efficiency = report.papers_processed / report.storage_used_mb
                    performance_insights['efficiency_metrics'][instance_name] = efficiency
            
            # Overall performance metrics
            if processing_times:
                avg_processing_time = statistics.mean(processing_times)
                avg_papers = statistics.mean(papers_processed)
                
                performance_insights['resource_utilization'] = {
                    'average_processing_time_hours': avg_processing_time / 3600,
                    'average_papers_processed': avg_papers,
                    'total_processing_time_hours': sum(processing_times) / 3600
                }
                
                # Identify bottlenecks
                for instance_name, report in instance_reports.items():
                    if report.processing_time_seconds > avg_processing_time * 1.5:
                        performance_insights['bottlenecks'].append({
                            'instance': instance_name,
                            'issue': 'slow_processing',
                            'processing_time_hours': report.processing_time_seconds / 3600,
                            'papers_processed': report.papers_processed
                        })
                    
                    if len(report.errors) > 5:
                        performance_insights['bottlenecks'].append({
                            'instance': instance_name,
                            'issue': 'high_error_rate',
                            'error_count': len(report.errors),
                            'papers_processed': report.papers_processed
                        })
                
                # Performance recommendations
                if avg_processing_time > 7200:  # More than 2 hours
                    performance_insights['recommendations'].append(
                        "Consider increasing batch size or concurrent processing to improve performance"
                    )
                
                if any(len(report.errors) > 10 for report in instance_reports.values()):
                    performance_insights['recommendations'].append(
                        "High error rates detected. Review error logs and improve error handling"
                    )
            
        except Exception as e:
            logger.error(f"Failed to analyze performance: {e}")
        
        return performance_insights
    
    async def _predict_next_update(self, instance_reports: Dict[str, UpdateReport]) -> Dict[str, Any]:
        """Generate predictions for next update based on current trends."""
        predictions = {
            'estimated_papers': {},
            'estimated_processing_time': {},
            'storage_growth_projection': {},
            'potential_issues': []
        }
        
        try:
            for instance_name, report in instance_reports.items():
                # Simple prediction based on current performance
                predictions['estimated_papers'][instance_name] = int(report.papers_processed * 1.1)  # 10% growth
                predictions['estimated_processing_time'][instance_name] = report.processing_time_seconds * 1.05  # 5% increase
                predictions['storage_growth_projection'][instance_name] = report.storage_used_mb * 0.1  # 10% growth
                
                # Predict potential issues
                if len(report.errors) > 5:
                    predictions['potential_issues'].append({
                        'instance': instance_name,
                        'issue': 'error_rate_concern',
                        'description': f"Instance has {len(report.errors)} errors, monitor closely"
                    })
                
                if report.storage_used_mb > 30000:  # More than 30GB
                    predictions['potential_issues'].append({
                        'instance': instance_name,
                        'issue': 'storage_concern',
                        'description': f"Storage usage is {report.storage_used_mb/1024:.1f}GB, cleanup recommended"
                    })
            
        except Exception as e:
            logger.error(f"Failed to generate predictions: {e}")
        
        return predictions
    
    async def _load_historical_reports(self, instance_name: str, days: int = 30) -> List[UpdateReport]:
        """Load historical reports for comparison."""
        historical_reports = []
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Look for historical report files
            for report_file in self.reports_directory.glob(f"*{instance_name}*.json"):
                try:
                    with open(report_file, 'r') as f:
                        report_data = json.load(f)
                    
                    # Check if it's a recent report
                    if 'update_date' in report_data:
                        update_date = datetime.fromisoformat(report_data['update_date'])
                        if update_date > cutoff_date:
                            # Convert to UpdateReport object (simplified)
                            historical_reports.append(type('UpdateReport', (), report_data)())
                            
                except Exception as e:
                    logger.warning(f"Could not load historical report {report_file}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to load historical reports for {instance_name}: {e}")
        
        return historical_reports
    
    async def _save_report(self, report: ComprehensiveUpdateReport) -> None:
        """Save comprehensive report to file."""
        try:
            report_file = self.reports_directory / f"{report.report_id}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report.to_dict(), f, indent=2, default=str)
            
            logger.info(f"Comprehensive report saved: {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save comprehensive report: {e}")
    
    def get_latest_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the latest comprehensive reports."""
        reports = []
        
        try:
            report_files = sorted(
                self.reports_directory.glob("comprehensive_report_*.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            
            for report_file in report_files[:limit]:
                try:
                    with open(report_file, 'r') as f:
                        report_data = json.load(f)
                    reports.append(report_data)
                except Exception as e:
                    logger.warning(f"Could not load report {report_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to get latest reports: {e}")
        
        return reports
    
    def cleanup_old_reports(self, days_to_keep: int = 90) -> int:
        """Clean up old report files."""
        cleaned_count = 0
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            for report_file in self.reports_directory.glob("*.json"):
                try:
                    stat = report_file.stat()
                    if datetime.fromtimestamp(stat.st_mtime) < cutoff_date:
                        report_file.unlink()
                        cleaned_count += 1
                except Exception as e:
                    logger.warning(f"Could not clean up report file {report_file}: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} old report files")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old reports: {e}")
        
        return cleaned_count