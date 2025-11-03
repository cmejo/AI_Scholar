#!/usr/bin/env python3
"""
Demo script for Task 2.3: Reporting and monitoring data models.

This script demonstrates how the new reporting and monitoring data models
can be used together to create comprehensive system reports and monitoring.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from multi_instance_arxiv_system.shared.multi_instance_data_models import (
    UpdateReport, StorageStats, PerformanceMetrics, EmailReport,
    MonitoringAlert, ProcessingMetrics, StorageBreakdown, ErrorAnalysis,
    ComparisonReport, NotificationHistory, TrendAnalysis, ResourceUtilization,
    QualityMetrics, SystemHealthReport, InstanceHealthReport
)
from arxiv_rag_enhancement.shared.data_models import ProcessingError


def create_sample_update_report(instance_name: str) -> UpdateReport:
    """Create a sample update report for demonstration."""
    
    # Create storage stats
    storage_stats = StorageStats(
        total_space_gb=1000.0,
        used_space_gb=300.0 if instance_name == "ai_scholar" else 200.0,
        available_space_gb=700.0 if instance_name == "ai_scholar" else 800.0,
        usage_percentage=30.0 if instance_name == "ai_scholar" else 20.0,
        instance_breakdown={instance_name: 300.0 if instance_name == "ai_scholar" else 200.0},
        growth_rate_gb_per_month=15.0,
        projected_full_date=datetime.now() + timedelta(days=365)
    )
    
    # Create performance metrics
    performance_metrics = PerformanceMetrics(
        download_rate_mbps=45.0 if instance_name == "ai_scholar" else 35.0,
        processing_rate_papers_per_hour=120.0 if instance_name == "ai_scholar" else 80.0,
        embedding_generation_rate=90.0,
        memory_usage_peak_mb=2048,
        cpu_usage_average_percent=65.0,
        error_rate_percentage=2.1
    )
    
    # Create some sample errors
    errors = [
        ProcessingError(
            file_path=f"/datapool/{instance_name}/pdf/sample_paper_1.pdf",
            error_message="PDF parsing failed - corrupted file",
            error_type="pdf_error",
            timestamp=datetime.now() - timedelta(hours=2)
        ),
        ProcessingError(
            file_path=f"/datapool/{instance_name}/pdf/sample_paper_2.pdf",
            error_message="Network timeout during download",
            error_type="network_error",
            timestamp=datetime.now() - timedelta(hours=1)
        )
    ]
    
    return UpdateReport(
        instance_name=instance_name,
        update_date=datetime.now(),
        papers_discovered=500 if instance_name == "ai_scholar" else 300,
        papers_downloaded=485 if instance_name == "ai_scholar" else 290,
        papers_processed=475 if instance_name == "ai_scholar" else 285,
        papers_failed=10 if instance_name == "ai_scholar" else 5,
        storage_used_mb=300000 if instance_name == "ai_scholar" else 200000,
        processing_time_seconds=3600.0,
        errors=errors,
        storage_stats=storage_stats,
        performance_metrics=performance_metrics,
        categories_processed=["cs.AI", "cs.LG", "stat.ML"] if instance_name == "ai_scholar" 
                           else ["q-fin.CP", "econ.EM", "stat.AP"],
        duplicate_papers_skipped=15 if instance_name == "ai_scholar" else 10
    )


def create_monitoring_alerts() -> list[MonitoringAlert]:
    """Create sample monitoring alerts."""
    
    alerts = []
    
    # Storage warning alert
    alerts.append(MonitoringAlert(
        alert_id="alert_001",
        instance_name="ai_scholar",
        alert_type="storage_warning",
        severity="warning",
        title="Storage Usage Approaching Limit",
        message="AI Scholar storage usage has reached 85% of allocated space",
        created_at=datetime.now() - timedelta(hours=2),
        metadata={"threshold": 80, "current_usage": 85, "projected_full": "30 days"}
    ))
    
    # Processing error alert
    alerts.append(MonitoringAlert(
        alert_id="alert_002",
        instance_name="quant_scholar",
        alert_type="processing_error",
        severity="error",
        title="High Error Rate Detected",
        message="Quant Scholar processing error rate exceeded 5% threshold",
        created_at=datetime.now() - timedelta(minutes=30),
        metadata={"threshold": 5.0, "current_rate": 7.2, "error_count": 25}
    ))
    
    # Performance degradation alert
    alerts.append(MonitoringAlert(
        alert_id="alert_003",
        instance_name="ai_scholar",
        alert_type="performance_degradation",
        severity="warning",
        title="Processing Rate Decline",
        message="AI Scholar processing rate has decreased by 20% compared to last week",
        created_at=datetime.now() - timedelta(hours=1),
        metadata={"previous_rate": 150.0, "current_rate": 120.0, "decline_percent": 20.0}
    ))
    
    return alerts


def create_error_analysis(instance_name: str) -> ErrorAnalysis:
    """Create sample error analysis."""
    
    start_time = datetime.now() - timedelta(days=7)
    end_time = datetime.now()
    
    return ErrorAnalysis(
        instance_name=instance_name,
        analysis_period_start=start_time,
        analysis_period_end=end_time,
        total_errors=42,
        error_categories={
            "pdf_error": 18,
            "network_error": 12,
            "processing_error": 8,
            "storage_error": 4
        },
        error_trends={
            "pdf_error": 15.2,  # 15.2% increase
            "network_error": -8.5,  # 8.5% decrease
            "processing_error": 3.1,  # 3.1% increase
            "storage_error": 0.0  # No change
        },
        most_common_errors=[
            "PDF parsing failed - corrupted file",
            "Network timeout during download",
            "Memory allocation error during processing"
        ],
        error_rate_by_hour={i: max(0, 6 - abs(i - 12)) for i in range(24)},  # Peak at noon
        resolution_suggestions=[
            "Implement more robust PDF validation before processing",
            "Increase network timeout values and add retry logic",
            "Monitor memory usage and implement garbage collection",
            "Add disk space monitoring and cleanup automation"
        ]
    )


def create_quality_metrics(instance_name: str) -> QualityMetrics:
    """Create sample quality metrics."""
    
    return QualityMetrics(
        instance_name=instance_name,
        measurement_date=datetime.now(),
        papers_with_complete_metadata=450 if instance_name == "ai_scholar" else 270,
        papers_with_missing_metadata=25 if instance_name == "ai_scholar" else 15,
        embedding_quality_score=0.87 if instance_name == "ai_scholar" else 0.82,
        text_extraction_success_rate=94.2 if instance_name == "ai_scholar" else 91.8,
        duplicate_detection_accuracy=89.5,
        processing_consistency_score=0.91,
        data_validation_errors=3 if instance_name == "ai_scholar" else 2
    )


def create_trend_analysis(instance_name: str) -> TrendAnalysis:
    """Create sample trend analysis."""
    
    # Generate sample data points for the last 30 days
    data_points = []
    base_time = datetime.now() - timedelta(days=30)
    base_value = 100.0
    
    for i in range(30):
        # Simulate an increasing trend with some noise
        value = base_value + (i * 2.5) + (i % 7 - 3) * 5  # Weekly pattern with growth
        data_points.append({
            "timestamp": (base_time + timedelta(days=i)).isoformat(),
            "value": round(value, 2)
        })
    
    return TrendAnalysis(
        instance_name=instance_name,
        analysis_type="processing_rate",
        time_period_days=30,
        data_points=data_points,
        trend_direction="increasing",
        trend_strength=0.78,
        predicted_values={
            "next_week": 185.0,
            "next_month": 210.0,
            "next_quarter": 250.0
        },
        confidence_interval={
            "next_week": (175.0, 195.0),
            "next_month": (195.0, 225.0),
            "next_quarter": (230.0, 270.0)
        }
    )


def create_system_health_report() -> SystemHealthReport:
    """Create a comprehensive system health report."""
    
    # Create instance health reports
    ai_scholar_health = InstanceHealthReport(
        instance_name="ai_scholar",
        status="healthy",
        last_update=datetime.now() - timedelta(hours=1),
        papers_count=12500,
        processing_rate=120.0,
        error_rate=2.1,
        storage_usage_mb=300000,
        vector_store_status="connected",
        configuration_valid=True,
        active_issues=[]
    )
    
    quant_scholar_health = InstanceHealthReport(
        instance_name="quant_scholar",
        status="warning",
        last_update=datetime.now() - timedelta(hours=2),
        papers_count=8200,
        processing_rate=75.0,
        error_rate=5.8,
        storage_usage_mb=200000,
        vector_store_status="connected",
        configuration_valid=True,
        active_issues=["High error rate detected", "Processing rate below target"]
    )
    
    # Create system-wide storage stats
    system_storage = StorageStats(
        total_space_gb=1000.0,
        used_space_gb=500.0,
        available_space_gb=500.0,
        usage_percentage=50.0,
        instance_breakdown={"ai_scholar": 300.0, "quant_scholar": 200.0},
        growth_rate_gb_per_month=25.0,
        projected_full_date=datetime.now() + timedelta(days=600)
    )
    
    # Create system performance metrics
    system_metrics = PerformanceMetrics(
        download_rate_mbps=40.0,
        processing_rate_papers_per_hour=97.5,
        embedding_generation_rate=85.0,
        memory_usage_peak_mb=4096,
        cpu_usage_average_percent=68.0,
        error_rate_percentage=3.2
    )
    
    return SystemHealthReport(
        report_id=f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        generated_at=datetime.now(),
        overall_status="warning",
        instance_reports={
            "ai_scholar": ai_scholar_health,
            "quant_scholar": quant_scholar_health
        },
        storage_health=system_storage,
        system_metrics=system_metrics,
        active_alerts=[
            "Quant Scholar error rate above threshold",
            "System storage usage at 50%"
        ],
        recommendations=[]
    )


def demonstrate_reporting_workflow():
    """Demonstrate a complete reporting workflow."""
    
    print("🔄 Demonstrating Multi-Instance Reporting Workflow")
    print("=" * 60)
    
    # 1. Create update reports for both instances
    print("\n1. Creating monthly update reports...")
    ai_report = create_sample_update_report("ai_scholar")
    quant_report = create_sample_update_report("quant_scholar")
    
    print(f"   ✓ AI Scholar: {ai_report.papers_processed} papers processed")
    print(f"   ✓ Quant Scholar: {quant_report.papers_processed} papers processed")
    
    # 2. Generate monitoring alerts
    print("\n2. Generating monitoring alerts...")
    alerts = create_monitoring_alerts()
    
    for alert in alerts:
        print(f"   🚨 {alert.severity.upper()}: {alert.title} ({alert.instance_name})")
    
    # 3. Create error analysis
    print("\n3. Performing error analysis...")
    ai_errors = create_error_analysis("ai_scholar")
    quant_errors = create_error_analysis("quant_scholar")
    
    print(f"   📊 AI Scholar: {ai_errors.total_errors} errors over {ai_errors.analysis_duration_hours:.1f} hours")
    print(f"   📊 Quant Scholar: {quant_errors.total_errors} errors over {quant_errors.analysis_duration_hours:.1f} hours")
    
    # 4. Generate quality metrics
    print("\n4. Assessing data quality...")
    ai_quality = create_quality_metrics("ai_scholar")
    quant_quality = create_quality_metrics("quant_scholar")
    
    print(f"   📈 AI Scholar quality score: {ai_quality.overall_quality_score:.2f}")
    print(f"   📈 Quant Scholar quality score: {quant_quality.overall_quality_score:.2f}")
    
    # 5. Create trend analysis
    print("\n5. Analyzing trends...")
    ai_trends = create_trend_analysis("ai_scholar")
    quant_trends = create_trend_analysis("quant_scholar")
    
    print(f"   📈 AI Scholar: {ai_trends.get_trend_summary()}")
    print(f"   📈 Quant Scholar: {quant_trends.get_trend_summary()}")
    
    # 6. Generate system health report
    print("\n6. Creating system health report...")
    health_report = create_system_health_report()
    
    print(f"   🏥 Overall system status: {health_report.overall_status.upper()}")
    print(f"   🏥 Active alerts: {len(health_report.active_alerts)}")
    
    # 7. Create comparison report
    print("\n7. Generating comparison report...")
    # Create a mock previous report for comparison
    previous_ai_report = create_sample_update_report("ai_scholar")
    previous_ai_report.papers_processed = 420  # Lower than current
    previous_ai_report.processing_time_seconds = 4200.0  # Slower than current
    
    comparison = ComparisonReport(
        instance_name="ai_scholar",
        current_period=ai_report,
        previous_period=previous_ai_report,
        comparison_date=datetime.now()
    )
    
    print(f"   📊 Papers change: {comparison.papers_change:+d}")
    print(f"   📊 Performance change: {comparison.performance_change_percent:+.1f}%")
    
    # 8. Save reports to files (demonstration)
    print("\n8. Saving reports...")
    
    reports_dir = Path("reports") / datetime.now().strftime("%Y-%m-%d")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Save update reports
    ai_report.save_to_file(reports_dir / "ai_scholar_update.json")
    quant_report.save_to_file(reports_dir / "quant_scholar_update.json")
    
    # Save health report
    with open(reports_dir / "system_health.json", 'w') as f:
        json.dump(health_report.to_dict(), f, indent=2)
    
    print(f"   💾 Reports saved to: {reports_dir}")
    
    print("\n" + "=" * 60)
    print("✅ Reporting workflow demonstration complete!")
    print("\nKey capabilities demonstrated:")
    print("- Comprehensive update reporting with metrics")
    print("- Real-time monitoring alerts and notifications")
    print("- Error analysis and trend identification")
    print("- Data quality assessment and tracking")
    print("- System health monitoring and reporting")
    print("- Period-over-period comparison analysis")
    print("- Structured data serialization and storage")


def main():
    """Run the reporting and monitoring demo."""
    
    print("Demo: Task 2.3 - Reporting and Monitoring Data Models")
    print("This demo shows how the new data models work together")
    print("to provide comprehensive monitoring and reporting capabilities.")
    
    try:
        demonstrate_reporting_workflow()
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)