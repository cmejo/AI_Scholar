#!/usr/bin/env python3
"""
Test script for Task 2.3: Create reporting and monitoring data models.

This script tests the new reporting and monitoring data models to ensure they work correctly
with serialization, deserialization, and provide the required functionality.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.shared.multi_instance_data_models import (
        UpdateReport, StorageStats, PerformanceMetrics, EmailReport,
        MonitoringAlert, ProcessingMetrics, StorageBreakdown, ErrorAnalysis,
        ComparisonReport, NotificationHistory, TrendAnalysis, ResourceUtilization,
        QualityMetrics, CleanupRecommendation, SystemHealthReport, InstanceHealthReport
    )
    from arxiv_rag_enhancement.shared.data_models import ProcessingError
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)


def test_update_report():
    """Test UpdateReport model functionality."""
    print("Testing UpdateReport model...")
    
    # Create sample data
    storage_stats = StorageStats(
        total_space_gb=1000.0,
        used_space_gb=250.0,
        available_space_gb=750.0,
        usage_percentage=25.0,
        instance_breakdown={"ai_scholar": 150.0, "quant_scholar": 100.0},
        growth_rate_gb_per_month=10.0
    )
    
    performance_metrics = PerformanceMetrics(
        download_rate_mbps=50.0,
        processing_rate_papers_per_hour=120.0,
        embedding_generation_rate=80.0,
        memory_usage_peak_mb=2048,
        cpu_usage_average_percent=65.0,
        error_rate_percentage=2.5
    )
    
    errors = [
        ProcessingError(
            file_path="/test/paper1.pdf",
            error_message="PDF parsing failed",
            error_type="pdf_error",
            timestamp=datetime.now()
        )
    ]
    
    report = UpdateReport(
        instance_name="ai_scholar",
        update_date=datetime.now(),
        papers_discovered=500,
        papers_downloaded=480,
        papers_processed=470,
        papers_failed=10,
        storage_used_mb=150000,
        processing_time_seconds=3600.0,
        errors=errors,
        storage_stats=storage_stats,
        performance_metrics=performance_metrics,
        categories_processed=["cs.AI", "cs.LG", "stat.ML"],
        duplicate_papers_skipped=20
    )
    
    # Test serialization
    report_dict = report.to_dict()
    assert isinstance(report_dict, dict)
    assert report_dict['instance_name'] == "ai_scholar"
    assert report_dict['papers_discovered'] == 500
    
    # Test deserialization
    restored_report = UpdateReport.from_dict(report_dict)
    assert restored_report.instance_name == report.instance_name
    assert restored_report.papers_discovered == report.papers_discovered
    assert len(restored_report.errors) == len(report.errors)
    
    print("✓ UpdateReport model test passed")


def test_monitoring_alert():
    """Test MonitoringAlert model functionality."""
    print("Testing MonitoringAlert model...")
    
    alert = MonitoringAlert(
        alert_id="alert_001",
        instance_name="quant_scholar",
        alert_type="storage_warning",
        severity="warning",
        title="Storage Usage High",
        message="Storage usage has exceeded 80% threshold",
        created_at=datetime.now(),
        metadata={"threshold": 80, "current_usage": 85}
    )
    
    # Test initial state
    assert alert.status == "active"
    assert alert.resolved_at is None
    
    # Test acknowledgment
    alert.acknowledge()
    assert alert.status == "acknowledged"
    
    # Test resolution
    alert.resolve()
    assert alert.status == "resolved"
    assert alert.resolved_at is not None
    
    # Test serialization
    alert_dict = alert.to_dict()
    restored_alert = MonitoringAlert.from_dict(alert_dict)
    assert restored_alert.alert_id == alert.alert_id
    assert restored_alert.status == alert.status
    
    print("✓ MonitoringAlert model test passed")


def test_processing_metrics():
    """Test ProcessingMetrics model functionality."""
    print("Testing ProcessingMetrics model...")
    
    metrics = ProcessingMetrics(
        instance_name="ai_scholar",
        measurement_time=datetime.now(),
        papers_processed_per_hour=150.0,
        download_speed_mbps=25.0,
        embedding_generation_rate=100.0,
        memory_usage_mb=1024,
        cpu_usage_percent=70.0,
        disk_io_rate_mbps=15.0,
        network_io_rate_mbps=20.0,
        active_threads=8,
        queue_size=50,
        error_count_last_hour=2
    )
    
    # Test serialization
    metrics_dict = metrics.to_dict()
    restored_metrics = ProcessingMetrics.from_dict(metrics_dict)
    assert restored_metrics.instance_name == metrics.instance_name
    assert restored_metrics.papers_processed_per_hour == metrics.papers_processed_per_hour
    
    print("✓ ProcessingMetrics model test passed")


def test_storage_breakdown():
    """Test StorageBreakdown model functionality."""
    print("Testing StorageBreakdown model...")
    
    breakdown = StorageBreakdown(
        instance_name="quant_scholar",
        measurement_time=datetime.now(),
        pdf_files_mb=50000,
        processed_data_mb=30000,
        vector_store_mb=20000,
        logs_mb=1000,
        temp_files_mb=500,
        archive_mb=10000,
        total_files_count=25000,
        oldest_file_date=datetime.now() - timedelta(days=365),
        newest_file_date=datetime.now()
    )
    
    # Test calculated property
    expected_total = 50000 + 30000 + 20000 + 1000 + 500 + 10000
    assert breakdown.total_mb == expected_total
    
    # Test serialization
    breakdown_dict = breakdown.to_dict()
    restored_breakdown = StorageBreakdown.from_dict(breakdown_dict)
    assert restored_breakdown.total_mb == breakdown.total_mb
    
    print("✓ StorageBreakdown model test passed")


def test_error_analysis():
    """Test ErrorAnalysis model functionality."""
    print("Testing ErrorAnalysis model...")
    
    start_time = datetime.now() - timedelta(hours=24)
    end_time = datetime.now()
    
    analysis = ErrorAnalysis(
        instance_name="ai_scholar",
        analysis_period_start=start_time,
        analysis_period_end=end_time,
        total_errors=48,
        error_categories={"pdf_error": 20, "network_error": 15, "processing_error": 13},
        error_trends={"pdf_error": 5.2, "network_error": -2.1, "processing_error": 1.8},
        most_common_errors=["PDF parsing failed", "Network timeout", "Memory allocation error"],
        error_rate_by_hour={i: i % 5 for i in range(24)},
        resolution_suggestions=["Increase timeout values", "Add retry logic", "Monitor memory usage"]
    )
    
    # Test calculated properties
    assert abs(analysis.analysis_duration_hours - 24.0) < 0.1  # Allow small floating point differences
    assert abs(analysis.average_errors_per_hour - 2.0) < 0.1
    
    # Test serialization
    analysis_dict = analysis.to_dict()
    restored_analysis = ErrorAnalysis.from_dict(analysis_dict)
    assert restored_analysis.total_errors == analysis.total_errors
    assert restored_analysis.average_errors_per_hour == analysis.average_errors_per_hour
    
    print("✓ ErrorAnalysis model test passed")


def test_comparison_report():
    """Test ComparisonReport model functionality."""
    print("Testing ComparisonReport model...")
    
    # Create current and previous reports
    current_storage = StorageStats(
        total_space_gb=1000.0, used_space_gb=300.0, available_space_gb=700.0,
        usage_percentage=30.0, instance_breakdown={"ai_scholar": 300.0}
    )
    
    previous_storage = StorageStats(
        total_space_gb=1000.0, used_space_gb=250.0, available_space_gb=750.0,
        usage_percentage=25.0, instance_breakdown={"ai_scholar": 250.0}
    )
    
    current_metrics = PerformanceMetrics(
        download_rate_mbps=50.0, processing_rate_papers_per_hour=120.0
    )
    
    previous_metrics = PerformanceMetrics(
        download_rate_mbps=45.0, processing_rate_papers_per_hour=100.0
    )
    
    current_report = UpdateReport(
        instance_name="ai_scholar", update_date=datetime.now(),
        papers_discovered=500, papers_downloaded=480, papers_processed=470,
        papers_failed=10, storage_used_mb=300000, processing_time_seconds=3600.0,
        errors=[], storage_stats=current_storage, performance_metrics=current_metrics
    )
    
    previous_report = UpdateReport(
        instance_name="ai_scholar", update_date=datetime.now() - timedelta(days=30),
        papers_discovered=450, papers_downloaded=430, papers_processed=420,
        papers_failed=10, storage_used_mb=250000, processing_time_seconds=4200.0,
        errors=[], storage_stats=previous_storage, performance_metrics=previous_metrics
    )
    
    comparison = ComparisonReport(
        instance_name="ai_scholar",
        current_period=current_report,
        previous_period=previous_report,
        comparison_date=datetime.now()
    )
    
    # Test calculated changes
    assert comparison.papers_change == 50  # 470 - 420
    assert comparison.storage_change_mb == 50000  # 300000 - 250000
    assert comparison.performance_change_percent > 0  # Should be positive improvement
    
    # Test serialization
    comparison_dict = comparison.to_dict()
    restored_comparison = ComparisonReport.from_dict(comparison_dict)
    assert restored_comparison.papers_change == comparison.papers_change
    
    print("✓ ComparisonReport model test passed")


def test_quality_metrics():
    """Test QualityMetrics model functionality."""
    print("Testing QualityMetrics model...")
    
    metrics = QualityMetrics(
        instance_name="quant_scholar",
        measurement_date=datetime.now(),
        papers_with_complete_metadata=450,
        papers_with_missing_metadata=50,
        embedding_quality_score=0.85,
        text_extraction_success_rate=92.5,
        duplicate_detection_accuracy=88.0,
        processing_consistency_score=0.90,
        data_validation_errors=5
    )
    
    # Test calculated properties
    assert metrics.total_papers == 500
    assert metrics.metadata_completeness_rate == 90.0
    assert 0.0 <= metrics.overall_quality_score <= 1.0
    
    # Test serialization
    metrics_dict = metrics.to_dict()
    restored_metrics = QualityMetrics.from_dict(metrics_dict)
    assert restored_metrics.total_papers == metrics.total_papers
    assert restored_metrics.overall_quality_score == metrics.overall_quality_score
    
    print("✓ QualityMetrics model test passed")


def test_resource_utilization():
    """Test ResourceUtilization model functionality."""
    print("Testing ResourceUtilization model...")
    
    utilization = ResourceUtilization(
        instance_name="ai_scholar",
        measurement_time=datetime.now(),
        cpu_usage_percent=75.0,
        memory_usage_mb=6144,
        memory_total_mb=8192,
        disk_usage_percent=65.0,
        disk_io_read_mbps=25.0,
        disk_io_write_mbps=15.0,
        network_in_mbps=10.0,
        network_out_mbps=8.0,
        active_processes=12,
        load_average=2.5
    )
    
    # Test calculated properties
    assert utilization.memory_usage_percent == 75.0
    assert not utilization.is_resource_constrained  # Should be False with these values
    
    # Test resource constrained detection
    high_utilization = ResourceUtilization(
        instance_name="test", measurement_time=datetime.now(),
        cpu_usage_percent=85.0, memory_usage_mb=7000, memory_total_mb=8192,
        disk_usage_percent=95.0, disk_io_read_mbps=0, disk_io_write_mbps=0,
        network_in_mbps=0, network_out_mbps=0, active_processes=0, load_average=0
    )
    assert high_utilization.is_resource_constrained  # Should be True
    
    print("✓ ResourceUtilization model test passed")


def test_trend_analysis():
    """Test TrendAnalysis model functionality."""
    print("Testing TrendAnalysis model...")
    
    # Create sample data points
    data_points = []
    base_time = datetime.now() - timedelta(days=30)
    for i in range(30):
        data_points.append({
            "timestamp": (base_time + timedelta(days=i)).isoformat(),
            "value": 100 + i * 2  # Increasing trend
        })
    
    analysis = TrendAnalysis(
        instance_name="ai_scholar",
        analysis_type="processing_rate",
        time_period_days=30,
        data_points=data_points,
        trend_direction="increasing",
        trend_strength=0.85,
        predicted_values={"2024-01-01": 180.0, "2024-01-15": 190.0},
        confidence_interval={"2024-01-01": (175.0, 185.0), "2024-01-15": (185.0, 195.0)}
    )
    
    # Test trend summary
    summary = analysis.get_trend_summary()
    assert "strong increasing trend" in summary
    assert "30 days" in summary
    
    # Test serialization
    analysis_dict = analysis.to_dict()
    restored_analysis = TrendAnalysis.from_dict(analysis_dict)
    assert restored_analysis.trend_direction == analysis.trend_direction
    assert restored_analysis.trend_strength == analysis.trend_strength
    
    print("✓ TrendAnalysis model test passed")


def main():
    """Run all tests for the reporting and monitoring data models."""
    print("Testing Task 2.3: Reporting and Monitoring Data Models")
    print("=" * 60)
    
    try:
        test_update_report()
        test_monitoring_alert()
        test_processing_metrics()
        test_storage_breakdown()
        test_error_analysis()
        test_comparison_report()
        test_quality_metrics()
        test_resource_utilization()
        test_trend_analysis()
        
        print("\n" + "=" * 60)
        print("✅ All reporting and monitoring data model tests passed!")
        print("\nNew models implemented:")
        print("- MonitoringAlert: System alerts and notifications")
        print("- ProcessingMetrics: Detailed processing performance metrics")
        print("- StorageBreakdown: Detailed storage usage analysis")
        print("- ErrorAnalysis: Error trend analysis and reporting")
        print("- ComparisonReport: Period-over-period comparison")
        print("- NotificationHistory: Notification tracking")
        print("- TrendAnalysis: Long-term trend analysis")
        print("- ResourceUtilization: System resource monitoring")
        print("- QualityMetrics: Data quality assessment")
        print("\nThese models provide comprehensive reporting and monitoring")
        print("capabilities for the multi-instance ArXiv system.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)