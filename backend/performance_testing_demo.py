"""
Performance Testing Demo

This script demonstrates the comprehensive performance and load testing capabilities
implemented for the Advanced RAG system.
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.performance_testing_core import (
    CorePerformanceTestingService,
    MobilePerformanceConfig,
    LoadTestConfig,
    run_comprehensive_performance_tests
)

async def demo_mobile_performance_testing():
    """Demonstrate mobile performance testing"""
    print("🔧 Running Mobile Performance Tests...")
    print("-" * 50)
    
    service = CorePerformanceTestingService()
    
    # Test different mobile configurations
    configs = [
        MobilePerformanceConfig(
            device_type='mobile',
            network_type='4g',
            battery_simulation=True,
            offline_mode_test=True,
            cache_performance_test=True
        ),
        MobilePerformanceConfig(
            device_type='tablet',
            network_type='wifi',
            battery_simulation=False,
            offline_mode_test=True,
            cache_performance_test=True
        )
    ]
    
    for i, config in enumerate(configs, 1):
        print(f"Testing Configuration {i}: {config.device_type} on {config.network_type}")
        results = await service.run_mobile_performance_tests(config)
        
        for result in results:
            print(f"  ✓ {result.test_name}")
            print(f"    Duration: {result.duration_ms:.1f}ms")
            print(f"    CPU Usage: {result.cpu_usage_percent:.1f}%")
            print(f"    Memory Usage: {result.memory_usage_mb:.1f}MB")
            if result.additional_metrics:
                for key, value in result.additional_metrics.items():
                    if isinstance(value, (int, float)):
                        print(f"    {key.replace('_', ' ').title()}: {value:.2f}")
            print()
    
    print("✅ Mobile Performance Testing Complete\n")

async def demo_voice_processing_testing():
    """Demonstrate voice processing performance testing"""
    print("🎤 Running Voice Processing Performance Tests...")
    print("-" * 50)
    
    service = CorePerformanceTestingService()
    results = await service.run_voice_processing_performance_tests()
    
    for result in results:
        print(f"✓ {result.test_name}")
        print(f"  Duration: {result.duration_ms:.1f}ms")
        print(f"  Success Rate: {((result.success_count / (result.success_count + result.error_count)) * 100):.1f}%")
        if result.network_latency_ms:
            print(f"  Average Latency: {result.network_latency_ms:.1f}ms")
        if result.additional_metrics:
            for key, value in result.additional_metrics.items():
                if isinstance(value, (int, float)) and 'accuracy' in key.lower():
                    print(f"  {key.replace('_', ' ').title()}: {value:.1f}%")
        print()
    
    print("✅ Voice Processing Performance Testing Complete\n")

async def demo_integration_load_testing():
    """Demonstrate integration load testing"""
    print("⚡ Running Integration Load Tests...")
    print("-" * 50)
    
    service = CorePerformanceTestingService()
    
    # Configure load tests
    configs = [
        LoadTestConfig(
            concurrent_users=25,
            test_duration_seconds=10,
            ramp_up_seconds=3,
            target_endpoint='/api/search',
            request_payload={'query': 'machine learning'},
            expected_response_time_ms=200,
            max_error_rate_percent=5.0
        ),
        LoadTestConfig(
            concurrent_users=50,
            test_duration_seconds=15,
            ramp_up_seconds=5,
            target_endpoint='/api/voice/process',
            request_payload={'audio_data': 'sample_audio'},
            expected_response_time_ms=500,
            max_error_rate_percent=3.0
        )
    ]
    
    results = await service.run_integration_load_tests(configs)
    
    for result in results:
        print(f"✓ {result.test_name}")
        print(f"  Duration: {result.duration_ms:.1f}ms")
        print(f"  Success Count: {result.success_count}")
        print(f"  Error Rate: {result.error_rate_percent:.1f}%")
        if result.throughput_ops_per_sec:
            print(f"  Throughput: {result.throughput_ops_per_sec:.1f} ops/sec")
        if result.network_latency_ms:
            print(f"  Average Response Time: {result.network_latency_ms:.1f}ms")
        print()
    
    print("✅ Integration Load Testing Complete\n")

async def demo_enterprise_scalability_testing():
    """Demonstrate enterprise scalability testing"""
    print("🏢 Running Enterprise Scalability Tests...")
    print("-" * 50)
    
    service = CorePerformanceTestingService()
    results = await service.run_enterprise_scalability_tests()
    
    for result in results:
        print(f"✓ {result.test_name}")
        print(f"  Duration: {result.duration_ms:.1f}ms")
        print(f"  Operations Processed: {result.success_count}")
        if result.throughput_ops_per_sec:
            print(f"  Throughput: {result.throughput_ops_per_sec:.1f} ops/sec")
        if result.additional_metrics:
            if 'scalability_factor' in result.additional_metrics:
                print(f"  Scalability Factor: {result.additional_metrics['scalability_factor']:.2f}x")
            if 'max_user_capacity' in result.additional_metrics:
                print(f"  Max User Capacity: {result.additional_metrics['max_user_capacity']:,}")
        print()
    
    print("✅ Enterprise Scalability Testing Complete\n")

async def demo_comprehensive_performance_report():
    """Demonstrate comprehensive performance reporting"""
    print("📊 Generating Comprehensive Performance Report...")
    print("-" * 50)
    
    # Run comprehensive tests
    report = await run_comprehensive_performance_tests()
    
    # Display summary
    summary = report['summary']
    print("Performance Test Summary:")
    print(f"  Total Tests: {summary['total_tests']}")
    print(f"  Successful Tests: {summary['successful_tests']}")
    print(f"  Success Rate: {summary['success_rate_percent']:.1f}%")
    print(f"  Average Duration: {summary['avg_test_duration_ms']:.1f}ms")
    print(f"  Average CPU Usage: {summary['avg_cpu_usage_percent']:.1f}%")
    print(f"  Average Memory Usage: {summary['avg_memory_usage_mb']:.1f}MB")
    if summary['avg_throughput_ops_per_sec'] > 0:
        print(f"  Average Throughput: {summary['avg_throughput_ops_per_sec']:.1f} ops/sec")
    if summary['avg_latency_ms'] > 0:
        print(f"  Average Latency: {summary['avg_latency_ms']:.1f}ms")
    print()
    
    # Display category breakdown
    print("Performance by Category:")
    for category, stats in report['category_breakdown'].items():
        print(f"  {category}:")
        print(f"    Tests: {stats['test_count']}")
        print(f"    Success Rate: {stats['avg_success_rate']:.1f}%")
        print(f"    Avg Duration: {stats['avg_duration_ms']:.1f}ms")
        if stats['avg_throughput'] > 0:
            print(f"    Avg Throughput: {stats['avg_throughput']:.1f} ops/sec")
    print()
    
    # Display recommendations
    print("Performance Recommendations:")
    for i, recommendation in enumerate(report['recommendations'], 1):
        print(f"  {i}. {recommendation}")
    print()
    
    print("✅ Comprehensive Performance Report Complete\n")

async def main():
    """Main demo function"""
    print("🚀 Advanced RAG Performance Testing Demo")
    print("=" * 60)
    print("This demo showcases the comprehensive performance and load testing")
    print("capabilities implemented for Task 9.2")
    print("=" * 60)
    print()
    
    # Run all demo sections
    await demo_mobile_performance_testing()
    await demo_voice_processing_testing()
    await demo_integration_load_testing()
    await demo_enterprise_scalability_testing()
    await demo_comprehensive_performance_report()
    
    print("🎉 Performance Testing Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("✓ Mobile performance testing with battery and network optimization")
    print("✓ Voice processing performance testing with latency measurement")
    print("✓ Integration load testing with rate limiting and failover")
    print("✓ Enterprise scalability testing for compliance monitoring")
    print("✓ Comprehensive performance reporting and analytics")
    print("✓ Real-time performance metrics collection")
    print("✓ Performance optimization recommendations")
    
    print("\nThe performance testing system is ready for production use!")

if __name__ == "__main__":
    asyncio.run(main())