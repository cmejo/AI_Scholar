"""
HTML Report Generator for multi-instance ArXiv system.

Generates rich HTML email reports with charts and visualizations for:
- Processing statistics and summaries
- Error analysis and recommendations
- Storage monitoring and trends
- Performance metrics and comparisons
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import base64
from io import BytesIO

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    logging.warning("Matplotlib/Seaborn not available. Charts will be disabled.")

from ..shared.multi_instance_data_models import (
    UpdateReport, StorageStats, PerformanceMetrics, ProcessingError
)

logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    """Generates rich HTML reports with embedded charts and visualizations."""
    
    def __init__(self):
        """Initialize HTML report generator."""
        self.template_dir = Path(__file__).parent / "templates"
        self.template_dir.mkdir(exist_ok=True)
        
        # Set up plotting style if available
        if PLOTTING_AVAILABLE:
            plt.style.use('seaborn-v0_8')
            sns.set_palette("husl")
    
    def create_processing_summary(self, report: UpdateReport) -> str:
        """
        Create HTML summary of processing statistics.
        
        Args:
            report: Update report with processing statistics
            
        Returns:
            HTML string with processing summary
        """
        try:
            # Calculate derived metrics
            success_rate = (report.papers_processed / max(report.papers_discovered, 1)) * 100
            error_rate = (report.papers_failed / max(report.papers_discovered, 1)) * 100
            processing_rate = report.papers_processed / max(report.processing_time_seconds / 3600, 0.01)  # papers per hour
            
            html = f"""
            <div class="processing-summary">
                <h2>📊 Processing Summary - {report.instance_name.title()}</h2>
                <div class="summary-grid">
                    <div class="metric-card success">
                        <h3>Papers Processed</h3>
                        <div class="metric-value">{report.papers_processed:,}</div>
                        <div class="metric-subtitle">Success Rate: {success_rate:.1f}%</div>
                    </div>
                    <div class="metric-card info">
                        <h3>Papers Discovered</h3>
                        <div class="metric-value">{report.papers_discovered:,}</div>
                        <div class="metric-subtitle">Downloaded: {report.papers_downloaded:,}</div>
                    </div>
                    <div class="metric-card warning">
                        <h3>Processing Time</h3>
                        <div class="metric-value">{self._format_duration(report.processing_time_seconds)}</div>
                        <div class="metric-subtitle">Rate: {processing_rate:.1f} papers/hour</div>
                    </div>
                    <div class="metric-card {'error' if report.papers_failed > 0 else 'success'}">
                        <h3>Failed Papers</h3>
                        <div class="metric-value">{report.papers_failed:,}</div>
                        <div class="metric-subtitle">Error Rate: {error_rate:.1f}%</div>
                    </div>
                </div>
                
                <div class="progress-bar-container">
                    <div class="progress-label">Processing Progress</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {success_rate:.1f}%"></div>
                    </div>
                    <div class="progress-text">{report.papers_processed:,} of {report.papers_discovered:,} papers processed</div>
                </div>
            </div>
            """
            
            # Add processing chart if plotting is available
            if PLOTTING_AVAILABLE and report.papers_discovered > 0:
                chart_html = self._create_processing_chart(report)
                html += chart_html
            
            return html
            
        except Exception as e:
            logger.error(f"Error creating processing summary: {e}")
            return f"<div class='error'>Error generating processing summary: {e}</div>"
    
    def create_error_analysis(self, errors: List[ProcessingError]) -> str:
        """
        Create HTML analysis of processing errors.
        
        Args:
            errors: List of processing errors
            
        Returns:
            HTML string with error analysis
        """
        try:
            if not errors:
                return """
                <div class="error-analysis">
                    <h2>✅ Error Analysis</h2>
                    <div class="success-message">No errors occurred during processing!</div>
                </div>
                """
            
            # Categorize errors
            error_categories = {}
            for error in errors:
                category = error.category.value if hasattr(error.category, 'value') else str(error.category)
                if category not in error_categories:
                    error_categories[category] = []
                error_categories[category].append(error)
            
            html = f"""
            <div class="error-analysis">
                <h2>⚠️ Error Analysis ({len(errors)} total errors)</h2>
                <div class="error-summary">
            """
            
            # Error category breakdown
            for category, category_errors in error_categories.items():
                severity_counts = {}
                for error in category_errors:
                    severity = error.severity.value if hasattr(error.severity, 'value') else str(error.severity)
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                html += f"""
                <div class="error-category">
                    <h3>{category.replace('_', ' ').title()} ({len(category_errors)} errors)</h3>
                    <div class="severity-breakdown">
                """
                
                for severity, count in severity_counts.items():
                    html += f"""
                    <span class="severity-badge {severity.lower()}">{severity}: {count}</span>
                    """
                
                html += """
                    </div>
                    <div class="error-details">
                """
                
                # Show first few errors as examples
                for error in category_errors[:3]:
                    html += f"""
                    <div class="error-item">
                        <div class="error-message">{error.message}</div>
                        <div class="error-context">File: {error.file_path or 'Unknown'}</div>
                        <div class="error-timestamp">{error.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</div>
                    </div>
                    """
                
                if len(category_errors) > 3:
                    html += f"<div class='more-errors'>... and {len(category_errors) - 3} more errors</div>"
                
                html += """
                    </div>
                </div>
                """
            
            html += """
                </div>
            </div>
            """
            
            # Add error chart if plotting is available
            if PLOTTING_AVAILABLE:
                chart_html = self._create_error_chart(error_categories)
                html += chart_html
            
            return html
            
        except Exception as e:
            logger.error(f"Error creating error analysis: {e}")
            return f"<div class='error'>Error generating error analysis: {e}</div>"
    
    def create_storage_charts(self, storage_stats: StorageStats) -> str:
        """
        Create HTML charts for storage monitoring.
        
        Args:
            storage_stats: Storage statistics
            
        Returns:
            HTML string with storage charts
        """
        try:
            usage_percent = storage_stats.usage_percentage
            available_gb = storage_stats.available_space_gb
            
            # Determine status color
            if usage_percent >= 90:
                status_class = "critical"
                status_icon = "🔴"
            elif usage_percent >= 75:
                status_class = "warning"
                status_icon = "🟡"
            else:
                status_class = "good"
                status_icon = "🟢"
            
            html = f"""
            <div class="storage-analysis">
                <h2>{status_icon} Storage Analysis</h2>
                <div class="storage-overview">
                    <div class="storage-gauge">
                        <div class="gauge-container">
                            <div class="gauge-fill {status_class}" style="width: {usage_percent:.1f}%"></div>
                        </div>
                        <div class="gauge-label">{usage_percent:.1f}% Used</div>
                    </div>
                    <div class="storage-details">
                        <div class="storage-metric">
                            <span class="label">Total Space:</span>
                            <span class="value">{storage_stats.total_space_gb:.1f} GB</span>
                        </div>
                        <div class="storage-metric">
                            <span class="label">Used Space:</span>
                            <span class="value">{storage_stats.used_space_gb:.1f} GB</span>
                        </div>
                        <div class="storage-metric">
                            <span class="label">Available:</span>
                            <span class="value">{available_gb:.1f} GB</span>
                        </div>
                        <div class="storage-metric">
                            <span class="label">Growth Rate:</span>
                            <span class="value">{storage_stats.growth_rate_gb_per_month:.1f} GB/month</span>
                        </div>
                    </div>
                </div>
            """
            
            # Instance breakdown
            if storage_stats.instance_breakdown:
                html += """
                <div class="instance-breakdown">
                    <h3>Storage by Instance</h3>
                    <div class="breakdown-chart">
                """
                
                for instance, size_gb in storage_stats.instance_breakdown.items():
                    percentage = (size_gb / storage_stats.used_space_gb) * 100 if storage_stats.used_space_gb > 0 else 0
                    html += f"""
                    <div class="breakdown-item">
                        <div class="breakdown-label">{instance.replace('_', ' ').title()}</div>
                        <div class="breakdown-bar">
                            <div class="breakdown-fill" style="width: {percentage:.1f}%"></div>
                        </div>
                        <div class="breakdown-value">{size_gb:.1f} GB ({percentage:.1f}%)</div>
                    </div>
                    """
                
                html += """
                    </div>
                </div>
                """
            
            # Storage projection
            if storage_stats.projected_full_date:
                days_until_full = (storage_stats.projected_full_date - datetime.now()).days
                html += f"""
                <div class="storage-projection">
                    <h3>Storage Projection</h3>
                    <div class="projection-warning">
                        ⚠️ Storage projected to be full in <strong>{days_until_full} days</strong>
                        ({storage_stats.projected_full_date.strftime('%Y-%m-%d')})
                    </div>
                </div>
                """
            
            html += """
            </div>
            """
            
            # Add storage chart if plotting is available
            if PLOTTING_AVAILABLE:
                chart_html = self._create_storage_chart(storage_stats)
                html += chart_html
            
            return html
            
        except Exception as e:
            logger.error(f"Error creating storage charts: {e}")
            return f"<div class='error'>Error generating storage charts: {e}</div>"
    
    def create_trend_analysis(self, historical_reports: List[UpdateReport]) -> str:
        """
        Create HTML trend analysis from historical data.
        
        Args:
            historical_reports: List of historical update reports
            
        Returns:
            HTML string with trend analysis
        """
        try:
            if len(historical_reports) < 2:
                return """
                <div class="trend-analysis">
                    <h2>📈 Trend Analysis</h2>
                    <div class="info-message">Insufficient historical data for trend analysis.</div>
                </div>
                """
            
            # Sort reports by date
            sorted_reports = sorted(historical_reports, key=lambda r: r.update_date)
            latest = sorted_reports[-1]
            previous = sorted_reports[-2]
            
            # Calculate trends
            papers_trend = latest.papers_processed - previous.papers_processed
            storage_trend = latest.storage_used_mb - previous.storage_used_mb
            time_trend = latest.processing_time_seconds - previous.processing_time_seconds
            
            html = f"""
            <div class="trend-analysis">
                <h2>📈 Trend Analysis</h2>
                <div class="trend-grid">
                    <div class="trend-card">
                        <h3>Papers Processed</h3>
                        <div class="trend-value">{latest.papers_processed:,}</div>
                        <div class="trend-change {'positive' if papers_trend >= 0 else 'negative'}">
                            {'↗️' if papers_trend >= 0 else '↘️'} {papers_trend:+,} from last update
                        </div>
                    </div>
                    <div class="trend-card">
                        <h3>Storage Usage</h3>
                        <div class="trend-value">{latest.storage_used_mb / 1024:.1f} GB</div>
                        <div class="trend-change {'negative' if storage_trend >= 0 else 'positive'}">
                            {'↗️' if storage_trend >= 0 else '↘️'} {storage_trend / 1024:+.1f} GB from last update
                        </div>
                    </div>
                    <div class="trend-card">
                        <h3>Processing Time</h3>
                        <div class="trend-value">{self._format_duration(latest.processing_time_seconds)}</div>
                        <div class="trend-change {'negative' if time_trend >= 0 else 'positive'}">
                            {'↗️' if time_trend >= 0 else '↘️'} {self._format_duration(abs(time_trend))} from last update
                        </div>
                    </div>
                </div>
            """
            
            # Performance trends
            if len(sorted_reports) >= 3:
                avg_processing_rate = sum(r.papers_processed / max(r.processing_time_seconds / 3600, 0.01) 
                                        for r in sorted_reports[-3:]) / 3
                html += f"""
                <div class="performance-trends">
                    <h3>Performance Trends (Last 3 Updates)</h3>
                    <div class="performance-metric">
                        <span class="label">Average Processing Rate:</span>
                        <span class="value">{avg_processing_rate:.1f} papers/hour</span>
                    </div>
                </div>
                """
            
            html += """
            </div>
            """
            
            # Add trend chart if plotting is available
            if PLOTTING_AVAILABLE and len(sorted_reports) >= 3:
                chart_html = self._create_trend_chart(sorted_reports)
                html += chart_html
            
            return html
            
        except Exception as e:
            logger.error(f"Error creating trend analysis: {e}")
            return f"<div class='error'>Error generating trend analysis: {e}</div>"
    
    def _create_processing_chart(self, report: UpdateReport) -> str:
        """Create processing statistics chart."""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # Processing breakdown pie chart
            labels = ['Processed', 'Failed', 'Skipped']
            sizes = [
                report.papers_processed,
                report.papers_failed,
                max(0, report.papers_discovered - report.papers_processed - report.papers_failed)
            ]
            colors = ['#2ecc71', '#e74c3c', '#95a5a6']
            
            ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax1.set_title('Processing Breakdown')
            
            # Processing rate over time (simulated)
            hours = list(range(1, int(report.processing_time_seconds / 3600) + 2))
            cumulative_papers = [min(report.papers_processed, 
                                   int(report.papers_processed * h / max(len(hours) - 1, 1))) 
                                for h in hours]
            
            ax2.plot(hours, cumulative_papers, marker='o', linewidth=2, markersize=4)
            ax2.set_xlabel('Hours')
            ax2.set_ylabel('Papers Processed')
            ax2.set_title('Processing Progress')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f"""
            <div class="chart-container">
                <img src="data:image/png;base64,{chart_data}" alt="Processing Chart" class="chart-image">
            </div>
            """
            
        except Exception as e:
            logger.error(f"Error creating processing chart: {e}")
            return ""
    
    def _create_error_chart(self, error_categories: Dict[str, List]) -> str:
        """Create error analysis chart."""
        try:
            if not error_categories:
                return ""
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            categories = list(error_categories.keys())
            counts = [len(errors) for errors in error_categories.values()]
            
            bars = ax.bar(categories, counts, color='#e74c3c', alpha=0.7)
            ax.set_xlabel('Error Categories')
            ax.set_ylabel('Number of Errors')
            ax.set_title('Error Distribution by Category')
            
            # Add value labels on bars
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{count}', ha='center', va='bottom')
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f"""
            <div class="chart-container">
                <img src="data:image/png;base64,{chart_data}" alt="Error Chart" class="chart-image">
            </div>
            """
            
        except Exception as e:
            logger.error(f"Error creating error chart: {e}")
            return ""
    
    def _create_storage_chart(self, storage_stats: StorageStats) -> str:
        """Create storage usage chart."""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # Storage usage pie chart
            used = storage_stats.used_space_gb
            available = storage_stats.available_space_gb
            
            ax1.pie([used, available], labels=['Used', 'Available'], 
                   colors=['#e74c3c', '#2ecc71'], autopct='%1.1f%%', startangle=90)
            ax1.set_title(f'Storage Usage ({storage_stats.usage_percentage:.1f}%)')
            
            # Instance breakdown bar chart
            if storage_stats.instance_breakdown:
                instances = list(storage_stats.instance_breakdown.keys())
                sizes = list(storage_stats.instance_breakdown.values())
                
                bars = ax2.bar(instances, sizes, color='#3498db', alpha=0.7)
                ax2.set_xlabel('Instances')
                ax2.set_ylabel('Storage (GB)')
                ax2.set_title('Storage by Instance')
                
                # Add value labels
                for bar, size in zip(bars, sizes):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                           f'{size:.1f}GB', ha='center', va='bottom')
                
                plt.xticks(rotation=45, ha='right')
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f"""
            <div class="chart-container">
                <img src="data:image/png;base64,{chart_data}" alt="Storage Chart" class="chart-image">
            </div>
            """
            
        except Exception as e:
            logger.error(f"Error creating storage chart: {e}")
            return ""
    
    def _create_trend_chart(self, reports: List[UpdateReport]) -> str:
        """Create trend analysis chart."""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            dates = [r.update_date for r in reports]
            papers_processed = [r.papers_processed for r in reports]
            storage_used = [r.storage_used_mb / 1024 for r in reports]  # Convert to GB
            
            # Papers processed trend
            ax1.plot(dates, papers_processed, marker='o', linewidth=2, markersize=6, color='#2ecc71')
            ax1.set_ylabel('Papers Processed')
            ax1.set_title('Papers Processed Over Time')
            ax1.grid(True, alpha=0.3)
            
            # Storage usage trend
            ax2.plot(dates, storage_used, marker='s', linewidth=2, markersize=6, color='#e74c3c')
            ax2.set_xlabel('Date')
            ax2.set_ylabel('Storage Used (GB)')
            ax2.set_title('Storage Usage Over Time')
            ax2.grid(True, alpha=0.3)
            
            # Format x-axis dates
            for ax in [ax1, ax2]:
                ax.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f"""
            <div class="chart-container">
                <img src="data:image/png;base64,{chart_data}" alt="Trend Chart" class="chart-image">
            </div>
            """
            
        except Exception as e:
            logger.error(f"Error creating trend chart: {e}")
            return ""
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human-readable string."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def get_base_css(self) -> str:
        """Get base CSS styles for HTML reports."""
        return """
        <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }
        
        .processing-summary, .error-analysis, .storage-analysis, .trend-analysis {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        h2 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        
        .summary-grid, .trend-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .metric-card, .trend-card {
            background: #f8f9fa;
            border-radius: 6px;
            padding: 15px;
            text-align: center;
            border-left: 4px solid #3498db;
        }
        
        .metric-card.success, .trend-card.success { border-left-color: #2ecc71; }
        .metric-card.warning, .trend-card.warning { border-left-color: #f39c12; }
        .metric-card.error, .trend-card.error { border-left-color: #e74c3c; }
        .metric-card.info, .trend-card.info { border-left-color: #3498db; }
        
        .metric-value, .trend-value {
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
            margin: 10px 0;
        }
        
        .metric-subtitle {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        
        .progress-bar-container {
            margin: 20px 0;
        }
        
        .progress-bar {
            background: #ecf0f1;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            background: linear-gradient(90deg, #2ecc71, #27ae60);
            height: 100%;
            transition: width 0.3s ease;
        }
        
        .progress-text {
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }
        
        .error-category {
            background: #fff5f5;
            border: 1px solid #fed7d7;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 15px;
        }
        
        .severity-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            margin-right: 8px;
            margin-bottom: 5px;
        }
        
        .severity-badge.critical { background: #e74c3c; color: white; }
        .severity-badge.high { background: #f39c12; color: white; }
        .severity-badge.medium { background: #f1c40f; color: #333; }
        .severity-badge.low { background: #95a5a6; color: white; }
        
        .error-item {
            background: white;
            border-radius: 4px;
            padding: 10px;
            margin: 8px 0;
            border-left: 3px solid #e74c3c;
        }
        
        .error-message {
            font-weight: bold;
            color: #e74c3c;
            margin-bottom: 5px;
        }
        
        .error-context, .error-timestamp {
            font-size: 0.85em;
            color: #7f8c8d;
        }
        
        .storage-overview {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .gauge-container {
            background: #ecf0f1;
            border-radius: 10px;
            height: 30px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .gauge-fill {
            height: 100%;
            transition: width 0.3s ease;
        }
        
        .gauge-fill.good { background: linear-gradient(90deg, #2ecc71, #27ae60); }
        .gauge-fill.warning { background: linear-gradient(90deg, #f39c12, #e67e22); }
        .gauge-fill.critical { background: linear-gradient(90deg, #e74c3c, #c0392b); }
        
        .storage-metric {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #ecf0f1;
        }
        
        .storage-metric:last-child {
            border-bottom: none;
        }
        
        .breakdown-item {
            display: grid;
            grid-template-columns: 1fr 2fr 1fr;
            gap: 10px;
            align-items: center;
            padding: 8px 0;
        }
        
        .breakdown-bar {
            background: #ecf0f1;
            border-radius: 4px;
            height: 20px;
            overflow: hidden;
        }
        
        .breakdown-fill {
            background: #3498db;
            height: 100%;
            transition: width 0.3s ease;
        }
        
        .trend-change.positive { color: #2ecc71; }
        .trend-change.negative { color: #e74c3c; }
        
        .chart-container {
            text-align: center;
            margin: 20px 0;
        }
        
        .chart-image {
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .success-message, .info-message {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }
        
        .info-message {
            background: #d1ecf1;
            border-color: #bee5eb;
            color: #0c5460;
        }
        
        .projection-warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }
        
        .error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }
        </style>
        """