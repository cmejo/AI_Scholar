#!/usr/bin/env python3
"""
Test script to verify Task 2 implementation: Enhanced data models and configuration system.

This script tests the enhanced paper data models, instance configuration management,
and reporting/monitoring data models.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def test_enhanced_paper_data_models():
    """Test enhanced paper data models (Task 2.1)."""
    print("Testing enhanced paper data models...")
    
    from multi_instance_arxiv_system.shared.multi_instance_data_models import (
        BasePaper, ArxivPaper, JournalPaper
    )
    
    # Test ArxivPaper
    arxiv_paper = ArxivPaper(
        paper_id="2301.00001",
        title="Test AI Paper",
        authors=["John Doe", "Jane Smith"],
        abstract="This is a test abstract for an AI paper.",
        published_date=datetime.now(),
        source_type="arxiv",
        instance_name="ai_scholar",
        arxiv_id="2301.00001",
        categories=["cs.AI", "cs.LG"],
        pdf_url="https://arxiv.org/pdf/2301.00001.pdf"
    )
    
    # Test document ID generation
    doc_id = arxiv_paper.get_document_id()
    print(f"ArXiv paper document ID: {doc_id}")
    assert "ai_scholar_arxiv" in doc_id
    
    # Test filename generation
    filename = arxiv_paper.get_filename()
    print(f"ArXiv paper filename: {filename}")
    assert filename.endswith(".pdf")
    
    # Test serialization
    paper_dict = arxiv_paper.to_dict()
    assert paper_dict['instance_name'] == 'ai_scholar'
    
    # Test JournalPaper
    journal_paper = JournalPaper(
        paper_id="jss_v50_i01",
        title="Test Statistics Paper",
        authors=["Alice Johnson"],
        abstract="This is a test abstract for a statistics paper.",
        published_date=datetime.now(),
        source_type="journal",
        instance_name="quant_scholar",
        journal_name="Journal of Statistical Software",
        volume="50",
        issue="1",
        pdf_url="https://www.jstatsoft.org/article/view/v050i01/v50i01.pdf"
    )
    
    # Test document ID generation
    doc_id = journal_paper.get_document_id()
    print(f"Journal paper document ID: {doc_id}")
    assert "quant_scholar_journal" in doc_id
    
    print("✓ Enhanced paper data models test passed")


def test_instance_configuration_management():
    """Test instance configuration management (Task 2.2)."""
    print("\nTesting instance configuration management...")
    
    from multi_instance_arxiv_system.config.instance_config_manager import (
        InstanceConfigManager, MultiInstanceConfigManager
    )
    
    # Test InstanceConfigManager for AI Scholar
    ai_config_manager = InstanceConfigManager(
        instance_name="ai_scholar",
        config_dir="backend/multi_instance_arxiv_system/configs"
    )
    
    # Get instance configuration
    ai_config = ai_config_manager.get_instance_config()
    print(f"AI Scholar config loaded: {ai_config.instance_name}")
    assert ai_config.instance_name == "ai_scholar"
    assert ai_config.display_name == "AI Scholar"
    assert len(ai_config.arxiv_categories) > 0
    
    # Validate configuration
    validation_errors = ai_config_manager.validate_instance_config()
    print(f"AI Scholar validation errors: {len(validation_errors)}")
    
    # Test InstanceConfigManager for Quant Scholar
    quant_config_manager = InstanceConfigManager(
        instance_name="quant_scholar",
        config_dir="backend/multi_instance_arxiv_system/configs"
    )
    
    # Get instance configuration
    quant_config = quant_config_manager.get_instance_config()
    print(f"Quant Scholar config loaded: {quant_config.instance_name}")
    assert quant_config.instance_name == "quant_scholar"
    assert quant_config.display_name == "Quant Scholar"
    assert len(quant_config.journal_sources) > 0
    
    # Test MultiInstanceConfigManager
    multi_config_manager = MultiInstanceConfigManager(
        config_dir=Path("backend/multi_instance_arxiv_system/configs")
    )
    
    # List configured instances
    instances = multi_config_manager.list_configured_instances()
    print(f"Configured instances: {instances}")
    assert "ai_scholar" in instances
    assert "quant_scholar" in instances
    
    # Validate all configurations
    validation_results = multi_config_manager.validate_all_configs()
    print(f"Validation results: {validation_results}")
    
    print("✓ Instance configuration management test passed")


def test_reporting_monitoring_data_models():
    """Test reporting and monitoring data models (Task 2.3)."""
    print("\nTesting reporting and monitoring data models...")
    
    from multi_instance_arxiv_system.shared.multi_instance_data_models import (
        UpdateReport, StorageStats, PerformanceMetrics, EmailReport,
        CleanupRecommendation, SystemHealthReport, InstanceHealthReport
    )
    from arxiv_rag_enhancement.shared.data_models import ProcessingError
    
    # Test StorageStats
    storage_stats = StorageStats(
        total_space_gb=1000.0,
        used_space_gb=250.0,
        available_space_gb=750.0,
        usage_percentage=25.0,
        instance_breakdown={"ai_scholar": 150.0, "quant_scholar": 100.0},
        growth_rate_gb_per_month=10.0
    )
    
    # Test serialization
    storage_dict = storage_stats.to_dict()
    assert storage_dict['usage_percentage'] == 25.0
    
    # Test PerformanceMetrics
    performance_metrics = PerformanceMetrics(
        download_rate_mbps=50.0,
        processing_rate_papers_per_hour=120.0,
        embedding_generation_rate=80.0,
        memory_usage_peak_mb=2048,
        cpu_usage_average_percent=65.0,
        error_rate_percentage=2.5
    )
    
    # Test UpdateReport
    update_report = UpdateReport(
        instance_name="ai_scholar",
        update_date=datetime.now(),
        papers_discovered=500,
        papers_downloaded=480,
        papers_processed=475,
        papers_failed=5,
        storage_used_mb=1024,
        processing_time_seconds=3600.0,
        errors=[],
        storage_stats=storage_stats,
        performance_metrics=performance_metrics,
        categories_processed=["cs.AI", "cs.LG"],
        duplicate_papers_skipped=20
    )
    
    # Test serialization
    report_dict = update_report.to_dict()
    assert report_dict['instance_name'] == 'ai_scholar'
    assert report_dict['papers_discovered'] == 500
    
    # Test EmailReport
    email_report = EmailReport(
        report_id="email_001",
        instance_name="ai_scholar",
        report_type="monthly_update",
        subject="AI Scholar Monthly Update",
        html_content="<html><body>Test content</body></html>",
        text_content="Test content",
        recipients=["admin@example.com"],
        priority="normal"
    )
    
    # Test email operations
    email_report.mark_as_sent()
    assert email_report.delivery_status == "sent"
    assert email_report.sent_at is not None
    
    # Test CleanupRecommendation
    cleanup_rec = CleanupRecommendation(
        recommendation_id="cleanup_001",
        instance_name="ai_scholar",
        cleanup_type="old_files",
        description="Remove files older than 90 days",
        files_to_remove=["/path/to/old/file1.pdf", "/path/to/old/file2.pdf"],
        space_to_free_mb=500,
        risk_level="low",
        auto_executable=True
    )
    
    # Test InstanceHealthReport
    instance_health = InstanceHealthReport(
        instance_name="ai_scholar",
        status="healthy",
        last_update=datetime.now(),
        papers_count=1000,
        processing_rate=120.0,
        error_rate=2.5,
        storage_usage_mb=2048,
        vector_store_status="connected",
        configuration_valid=True,
        active_issues=[]
    )
    
    # Test SystemHealthReport
    system_health = SystemHealthReport(
        report_id="health_001",
        generated_at=datetime.now(),
        overall_status="healthy",
        instance_reports={"ai_scholar": instance_health},
        storage_health=storage_stats,
        system_metrics=performance_metrics,
        active_alerts=[],
        recommendations=[cleanup_rec]
    )
    
    # Test serialization
    health_dict = system_health.to_dict()
    assert health_dict['overall_status'] == 'healthy'
    assert 'ai_scholar' in health_dict['instance_reports']
    
    print("✓ Reporting and monitoring data models test passed")


def main():
    """Run all tests for Task 2 implementation."""
    print("Testing Task 2: Enhanced data models and configuration system")
    print("=" * 70)
    
    try:
        # Test subtask 2.1
        test_enhanced_paper_data_models()
        
        # Test subtask 2.2
        test_instance_configuration_management()
        
        # Test subtask 2.3
        test_reporting_monitoring_data_models()
        
        print("\n" + "=" * 70)
        print("✓ All Task 2 tests passed successfully!")
        print("Enhanced data models and configuration system implementation is complete.")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)