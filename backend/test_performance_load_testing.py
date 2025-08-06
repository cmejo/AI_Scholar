"""
Comprehensive Performance and Load Testing Suite

This module provides comprehensive performance and load testing for all advanced features
including mobile, voice, integration, and enterprise systems.
"""

import pytest
import asyncio
import time
import json
import statistics
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.performance_testing_service import (
    PerformanceTestingService,
    PerformanceMetrics,
    LoadTestConfig,
    MobilePerformanceConfig
)

class TestMobilePerformanceTests:
    """Test mobile performance testing capabilities"""
    
    @pytest.fixture
    def performance_service(self):
        return PerformanceTestingService()
    
    @pytest.fixture
    def mobile_config(self):
        return MobilePerformanceConfig(
            device_type='mobile',
            network_type='4g',
            battery_simulation=True,
            offline_mode_test=True,
            cache_performance_test=True
        )
    
    @pytest.mark.asyncio
    async def test_mobile_ui_performance(self, performance_service, mobile_config):
        """Test mobile UI performance measurement"""
        results = await performance_service.run_mobile_performance_tests(mobile_config)
        
        # Verify results structure
        assert len(results) >= 4  # UI, network, battery, offline, cache tests
        
        # Find UI performance result
        ui_result = next((r for r in results if 'UI Performance' in r.test_name), None)
        assert ui_result is not None
        
        # Verify UI performance metrics
        assert ui_result.duration_ms > 0
        assert ui_result.cpu_usage_percent >= 0
        assert ui_result.memory_usage_mb >= 0
        assert ui_result.throughput_ops_per_sec > 0
        assert 'avg_interaction_time_ms' in ui_result.additional_metrics
        assert 'device_type' in ui_result.additional_metrics
        assert ui_result.additional_metrics['device_type'] == 'mobile'
    
    @pytest.mark.asyncio
    async def test_mobile_network_optimization(self, performance_service, mobile_config):
        """Test mobile network performance optimization"""
        results = await performance_service.run_mobile_performance_tests(mobile_config)
        
        # Find network performance result
        network_result = next((r for r in results if 'Network Performance' in r.test_name), None)
        assert network_result is not None
        
        # Verify network optimization metrics
        assert network_result.network_latency_ms > 0
        assert network_result.success_count > 0
        assert network_result.error_count == 0
        assert 'network_type' in network_result.additional_metrics
        assert network_result.additional_metrics['network_type'] == '4g'
        assert 'success_rate_percent' in network_result.additional_metrics
        assert network_result.additional_metrics['success_rate_percent'] == 100.0
    
    @pytest.mark.asyncio
    async def test_battery_optimization(self, performance_service, mobile_config):
        """Test battery optimization performance"""
        results = await performance_service.run_mobile_performance_tests(mobile_config)
        
        # Find battery optimization result
        battery_result = next((r for r in results if 'Battery Optimization' in r.test_name), None)
        assert battery_result is not None
        
        # Verify battery optimization metrics
        assert battery_result.success_count > 0
        assert 'cpu_operations' in battery_result.additional_metrics
        assert 'background_sync_operations' in battery_result.additional_metrics
        assert 'battery_efficiency_score' in battery_result.additional_metrics
        assert battery_result.additional_metrics['battery_efficiency_score'] > 80
    
    @pytest.mark.asyncio
    async def test_offline_mode_performance(self, performance_service, mobile_config):
        """Test offline mode performance"""
        results = await performance_service.run_mobile_performance_tests(mobile_config)
        
        # Find offline performance result
        offline_result = next((r for r in results if 'Offline Mode' in r.test_name), None)
        assert offline_result is not None
        
        # Verify offline performance metrics
        assert offline_result.success_count > 0
        assert 'cache_hits' in offline_result.additional_metrics
        assert 'cache_misses' in offline_result.additional_metrics
        assert 'cache_hit_rate_percent' in offline_result.additional_metrics
        assert offline_result.additional_metrics['cache_hit_rate_percent'] > 70
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, performance_service, mobile_config):
        """Test cache performance optimization"""
        results = await performance_service.run_mobile_performance_tests(mobile_config)
        
        # Find cache performance result
        cache_result = next((r for r in results if 'Cache Performance' in r.test_name), None)
        assert cache_result is not None
        
        # Verify cache performance metrics
        assert cache_result.throughput_ops_per_sec > 0
        assert cache_result.success_count > 0
        assert 'avg_cache_operation_ms' in cache_result.additional_metrics
        assert 'cache_efficiency_score' in cache_result.additional_metrics
        assert cache_result.additional_metrics['cache_efficiency_score'] > 90

class TestVoiceProcessingPerformanceTests:
    """Test voice processing performance testing capabilities"""
    
    @pytest.fixture
    def performance_service(self):
        return PerformanceTestingService()
    
    @pytest.mark.asyncio
    async def test_speech_to_text_latency(self, performance_service):
        """Test speech-to-text processing latency"""
        results = await performance_service.run_voice_processing_performance_tests()
        
        # Find speech-to-text result
        stt_result = next((r for r in results if 'Speech-to-Text' in r.test_name), None)
        assert stt_result is not None
        
        # Verify latency metrics
        assert stt_result.network_latency_ms > 0
        assert stt_result.success_count > 0
        assert 'avg_processing_time_ms' in stt_result.additional_metrics
        assert 'transcription_accuracy' in stt_result.additional_metrics
        assert stt_result.additional_metrics['transcription_accuracy'] > 90
        assert 'real_time_factor' in stt_result.additional_metrics
    
    @pytest.mark.asyncio
    async def test_text_to_speech_latency(self, performance_service):
        """Test text-to-speech processing latency"""
        results = await performance_service.run_voice_processing_performance_tests()
        
        # Find text-to-speech result
        tts_result = next((r for r in results if 'Text-to-Speech' in r.test_name), None)
        assert tts_result is not None
        
        # Verify synthesis metrics
        assert tts_result.network_latency_ms > 0
        assert tts_result.success_count > 0
        assert 'avg_synthesis_time_ms' in tts_result.additional_metrics
        assert 'voice_quality_score' in tts_result.additional_metrics
        assert tts_result.additional_metrics['voice_quality_score'] > 80
        assert 'naturalness_score' in tts_result.additional_metrics
    
    @pytest.mark.asyncio
    async def test_voice_command_processing(self, performance_service):
        """Test voice command processing performance"""
        results = await performance_service.run_voice_processing_performance_tests()
        
        # Find voice command result
        command_result = next((r for r in results if 'Voice Command' in r.test_name), None)
        assert command_result is not None
        
        # Verify command processing metrics
        assert command_result.success_count > 0
        assert command_result.error_rate_percent < 10  # Less than 10% error rate
        assert 'avg_command_processing_ms' in command_result.additional_metrics
        assert 'command_accuracy' in command_result.additional_metrics
        assert command_result.additional_metrics['command_accuracy'] > 90
        assert 'intent_recognition_accuracy' in command_result.additional_metrics
    
    @pytest.mark.asyncio
    async def test_realtime_voice_processing(self, performance_service):
        """Test real-time voice processing performance"""
        results = await performance_service.run_voice_processing_performance_tests()
        
        # Find real-time processing result
        realtime_result = next((r for r in results if 'Real-time Voice' in r.test_name), None)
        assert realtime_result is not None
        
        # Verify real-time performance
        assert realtime_result.throughput_ops_per_sec > 0
        assert 'buffer_underrun_rate' in realtime_result.additional_metrics
        assert realtime_result.additional_metrics['buffer_underrun_rate'] < 5  # Less than 5% underruns
        assert 'real_time_performance' in realtime_result.additional_metrics
        assert realtime_result.additional_metrics['real_time_performance'] > 95
    
    @pytest.mark.asyncio
    async def test_multilingual_voice_performance(self, performance_service):
        """Test multilingual voice processing performance"""
        results = await performance_service.run_voice_processing_performance_tests()
        
        # Find multilingual result
        multilingual_result = next((r for r in results if 'Multilingual Voice' in r.test_name), None)
        assert multilingual_result is not None
        
        # Verify multilingual support
        assert multilingual_result.success_count > 0
        assert 'language_performance' in multilingual_result.additional_metrics
        assert 'supported_languages' in multilingual_result.additional_metrics
        assert multilingual_result.additional_metrics['supported_languages'] >= 7
        
        # Check individual language performance
        lang_performance = multilingual_result.additional_metrics['language_performance']
        assert 'en' in lang_performance
        assert 'es' in lang_performance
        assert 'zh' in lang_performance

class TestIntegrationLoadTests:
    """Test integration load testing capabilities"""
    
    @pytest.fixture
    def performance_service(self):
        return PerformanceTestingService()
    
    @pytest.fixture
    def load_configs(self):
        return [
            LoadTestConfig(
                concurrent_users=10,
                test_duration_seconds=5,
                ramp_up_seconds=2,
                target_endpoint='/api/test',
                request_payload={'test': 'data'},
                expected_response_time_ms=200,
                max_error_rate_percent=5.0
            )
        ]
    
    @pytest.mark.asyncio
    async def test_integration_load_testing(self, performance_service, load_configs):
        """Test integration load testing"""
        results = await performance_service.run_integration_load_tests(load_configs)
        
        # Should have multiple test types for each config
        assert len(results) >= 4  # Normal load, rate limiting, failover, burst
        
        # Find normal load test result
        load_result = next((r for r in results if 'Integration Load Test' in r.test_name), None)
        assert load_result is not None
        
        # Verify load test metrics
        assert load_result.throughput_ops_per_sec > 0
        assert load_result.success_count > 0
        assert 'concurrent_users' in load_result.additional_metrics
        assert load_result.additional_metrics['concurrent_users'] == 10
        assert 'avg_response_time_ms' in load_result.additional_metrics
        assert 'p95_response_time_ms' in load_result.additional_metrics
    
    @pytest.mark.asyncio
    async def test_rate_limiting_behavior(self, performance_service, load_configs):
        """Test rate limiting behavior"""
        results = await performance_service.run_integration_load_tests(load_configs)
        
        # Find rate limiting result
        rate_limit_result = next((r for r in results if 'Rate Limiting Test' in r.test_name), None)
        assert rate_limit_result is not None
        
        # Verify rate limiting metrics
        assert 'rate_limit_hits' in rate_limit_result.additional_metrics
        assert 'rate_limiting_effective' in rate_limit_result.additional_metrics
        assert rate_limit_result.additional_metrics['rate_limiting_effective'] is True
        assert rate_limit_result.error_count > 0  # Should have some rate limited requests
    
    @pytest.mark.asyncio
    async def test_failover_behavior(self, performance_service, load_configs):
        """Test failover behavior during service disruptions"""
        results = await performance_service.run_integration_load_tests(load_configs)
        
        # Find failover result
        failover_result = next((r for r in results if 'Failover Test' in r.test_name), None)
        assert failover_result is not None
        
        # Verify failover metrics
        assert 'primary_requests' in failover_result.additional_metrics
        assert 'failover_requests' in failover_result.additional_metrics
        assert 'failover_triggered' in failover_result.additional_metrics
        assert failover_result.additional_metrics['failover_triggered'] is True
        assert failover_result.success_count > 0  # Should have successful failover requests
    
    @pytest.mark.asyncio
    async def test_burst_load_handling(self, performance_service, load_configs):
        """Test burst load handling"""
        results = await performance_service.run_integration_load_tests(load_configs)
        
        # Find burst load result
        burst_result = next((r for r in results if 'Burst Load Test' in r.test_name), None)
        assert burst_result is not None
        
        # Verify burst load metrics
        assert 'phase_analysis' in burst_result.additional_metrics
        assert 'burst_multiplier' in burst_result.additional_metrics
        assert 'burst_handling_effective' in burst_result.additional_metrics
        
        phase_analysis = burst_result.additional_metrics['phase_analysis']
        assert 'normal' in phase_analysis
        assert 'burst' in phase_analysis
        assert 'recovery' in phase_analysis

class TestEnterpriseScalabilityTests:
    """Test enterprise scalability testing capabilities"""
    
    @pytest.fixture
    def performance_service(self):
        return PerformanceTestingService()
    
    @pytest.mark.asyncio
    async def test_compliance_monitoring_scalability(self, performance_service):
        """Test compliance monitoring system scalability"""
        results = await performance_service.run_enterprise_scalability_tests()
        
        # Find compliance monitoring result
        compliance_result = next((r for r in results if 'Compliance Monitoring' in r.test_name), None)
        assert compliance_result is not None
        
        # Verify scalability metrics
        assert compliance_result.throughput_ops_per_sec > 0
        assert compliance_result.success_count > 0
        assert 'scalability_results' in compliance_result.additional_metrics
        assert 'max_user_capacity' in compliance_result.additional_metrics
        assert 'scalability_factor' in compliance_result.additional_metrics
        
        scalability_results = compliance_result.additional_metrics['scalability_results']
        assert len(scalability_results) > 0
        assert all('user_count' in result for result in scalability_results)
    
    @pytest.mark.asyncio
    async def test_user_management_scalability(self, performance_service):
        """Test institutional user management scalability"""
        results = await performance_service.run_enterprise_scalability_tests()
        
        # Find user management result
        user_mgmt_result = next((r for r in results if 'User Management' in r.test_name), None)
        assert user_mgmt_result is not None
        
        # Verify user management scalability
        assert user_mgmt_result.throughput_ops_per_sec > 0
        assert user_mgmt_result.success_count > 0
        assert 'operation_results' in user_mgmt_result.additional_metrics
        assert 'supported_operations' in user_mgmt_result.additional_metrics
        
        operation_results = user_mgmt_result.additional_metrics['operation_results']
        assert 'bulk_import' in operation_results
        assert 'create_user' in operation_results
        assert 'update_permissions' in operation_results
    
    @pytest.mark.asyncio
    async def test_resource_optimization_scalability(self, performance_service):
        """Test resource optimization system scalability"""
        results = await performance_service.run_enterprise_scalability_tests()
        
        # Find resource optimization result
        resource_result = next((r for r in results if 'Resource Optimization' in r.test_name), None)
        assert resource_result is not None
        
        # Verify resource optimization scalability
        assert resource_result.throughput_ops_per_sec > 0
        assert 'optimization_results' in resource_result.additional_metrics
        assert 'resource_types_supported' in resource_result.additional_metrics
        assert resource_result.additional_metrics['resource_types_supported'] >= 4
        
        optimization_results = resource_result.additional_metrics['optimization_results']
        assert 'cpu' in optimization_results
        assert 'memory' in optimization_results
        assert 'storage' in optimization_results
        assert 'network' in optimization_results
    
    @pytest.mark.asyncio
    async def test_reporting_scalability(self, performance_service):
        """Test reporting system scalability"""
        results = await performance_service.run_enterprise_scalability_tests()
        
        # Find reporting result
        reporting_result = next((r for r in results if 'Reporting System' in r.test_name), None)
        assert reporting_result is not None
        
        # Verify reporting scalability
        assert reporting_result.throughput_ops_per_sec > 0
        assert reporting_result.success_count > 0
        assert 'reporting_results' in reporting_result.additional_metrics
        assert 'max_data_volume' in reporting_result.additional_metrics
        assert 'report_types_supported' in reporting_result.additional_metrics
        
        reporting_results = reporting_result.additional_metrics['reporting_results']
        assert 'user_activity' in reporting_results
        assert 'compliance_summary' in reporting_results
        assert 'resource_usage' in reporting_results
    
    @pytest.mark.asyncio
    async def test_concurrent_enterprise_operations(self, performance_service):
        """Test concurrent enterprise operations"""
        results = await performance_service.run_enterprise_scalability_tests()
        
        # Find concurrent operations result
        concurrent_result = next((r for r in results if 'Concurrent Enterprise' in r.test_name), None)
        assert concurrent_result is not None
        
        # Verify concurrent operations
        assert concurrent_result.throughput_ops_per_sec > 0
        assert concurrent_result.success_count > 0
        assert 'operation_stats' in concurrent_result.additional_metrics
        assert 'concurrent_operations' in concurrent_result.additional_metrics
        assert 'concurrency_efficiency' in concurrent_result.additional_metrics
        
        operation_stats = concurrent_result.additional_metrics['operation_stats']
        assert len(operation_stats) > 0
        assert all('count' in stats for stats in operation_stats.values())

class TestPerformanceReporting:
    """Test performance reporting and analysis"""
    
    @pytest.fixture
    def performance_service(self):
        return PerformanceTestingService()
    
    @pytest.fixture
    def sample_metrics(self):
        return [
            PerformanceMetrics(
                test_name="Sample Test 1",
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(seconds=1),
                duration_ms=1000,
                cpu_usage_percent=50.0,
                memory_usage_mb=100.0,
                network_latency_ms=50.0,
                throughput_ops_per_sec=100.0,
                error_rate_percent=2.0,
                success_count=98,
                error_count=2
            ),
            PerformanceMetrics(
                test_name="Sample Test 2",
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(seconds=2),
                duration_ms=2000,
                cpu_usage_percent=75.0,
                memory_usage_mb=200.0,
                network_latency_ms=100.0,
                throughput_ops_per_sec=50.0,
                error_rate_percent=1.0,
                success_count=99,
                error_count=1
            )
        ]
    
    def test_performance_report_generation(self, performance_service, sample_metrics):
        """Test performance report generation"""
        report = performance_service.generate_performance_report(sample_metrics)
        
        # Verify report structure
        assert "report_generated" in report
        assert "summary" in report
        assert "category_breakdown" in report
        assert "detailed_results" in report
        assert "recommendations" in report
        
        # Verify summary metrics
        summary = report["summary"]
        assert summary["total_tests"] == 2
        assert summary["successful_tests"] == 2  # Both have error rate < 5%
        assert summary["success_rate_percent"] == 100.0
        assert summary["avg_test_duration_ms"] == 1500.0  # (1000 + 2000) / 2
        assert summary["avg_cpu_usage_percent"] == 62.5  # (50 + 75) / 2
        assert summary["avg_throughput_ops_per_sec"] == 75.0  # (100 + 50) / 2
    
    def test_performance_recommendations(self, performance_service):
        """Test performance optimization recommendations"""
        # Create metrics with various performance issues
        high_cpu_metrics = PerformanceMetrics(
            test_name="High CPU Test",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=1),
            duration_ms=1000,
            cpu_usage_percent=90.0,  # High CPU
            memory_usage_mb=100.0,
            error_rate_percent=0.0,
            success_count=100,
            error_count=0
        )
        
        high_memory_metrics = PerformanceMetrics(
            test_name="High Memory Test",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=1),
            duration_ms=1000,
            cpu_usage_percent=50.0,
            memory_usage_mb=1500.0,  # High memory
            error_rate_percent=0.0,
            success_count=100,
            error_count=0
        )
        
        high_error_metrics = PerformanceMetrics(
            test_name="High Error Test",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=1),
            duration_ms=1000,
            cpu_usage_percent=50.0,
            memory_usage_mb=100.0,
            error_rate_percent=10.0,  # High error rate
            success_count=90,
            error_count=10
        )
        
        test_metrics = [high_cpu_metrics, high_memory_metrics, high_error_metrics]
        report = performance_service.generate_performance_report(test_metrics)
        
        recommendations = report["recommendations"]
        assert len(recommendations) >= 3
        
        # Check for specific recommendations
        cpu_recommendation = any("CPU usage" in rec for rec in recommendations)
        memory_recommendation = any("memory usage" in rec for rec in recommendations)
        error_recommendation = any("error rates" in rec for rec in recommendations)
        
        assert cpu_recommendation
        assert memory_recommendation
        assert error_recommendation
    
    def test_empty_results_handling(self, performance_service):
        """Test handling of empty test results"""
        report = performance_service.generate_performance_report([])
        
        assert "error" in report
        assert report["error"] == "No test results available"

class TestPerformanceIntegration:
    """Integration tests for performance testing system"""
    
    @pytest.mark.asyncio
    async def test_comprehensive_performance_test_suite(self):
        """Test running the complete performance test suite"""
        from services.performance_testing_service import run_comprehensive_performance_tests
        
        # Run comprehensive tests (with shorter durations for testing)
        report = await run_comprehensive_performance_tests()
        
        # Verify comprehensive report structure
        assert "report_generated" in report
        assert "summary" in report
        assert "category_breakdown" in report
        assert "detailed_results" in report
        assert "recommendations" in report
        
        # Verify we have results from all test categories
        detailed_results = report["detailed_results"]
        assert len(detailed_results) > 0
        
        # Check for different test categories
        test_names = [result["test_name"] for result in detailed_results]
        
        # Should have mobile tests
        mobile_tests = [name for name in test_names if "Mobile" in name or "UI Performance" in name or "Network Performance" in name]
        assert len(mobile_tests) > 0
        
        # Should have voice tests
        voice_tests = [name for name in test_names if "Voice" in name or "Speech" in name]
        assert len(voice_tests) > 0
        
        # Should have integration tests
        integration_tests = [name for name in test_names if "Integration" in name or "Load Test" in name]
        assert len(integration_tests) > 0
        
        # Should have enterprise tests
        enterprise_tests = [name for name in test_names if "Enterprise" in name or "Scalability" in name]
        assert len(enterprise_tests) > 0
        
        # Verify summary metrics are reasonable
        summary = report["summary"]
        assert summary["total_tests"] > 10  # Should have many tests
        assert summary["success_rate_percent"] >= 80  # Most tests should pass
        assert summary["avg_test_duration_ms"] > 0
        assert summary["avg_cpu_usage_percent"] >= 0
        assert summary["avg_memory_usage_mb"] >= 0

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])