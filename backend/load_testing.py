#!/usr/bin/env python3
"""
Comprehensive load testing script for the AI Scholar RAG system.
"""
import asyncio
import argparse
import json
import logging
from datetime import datetime
from typing import Dict, Any

from services.performance_testing import get_performance_tester, LoadTestConfig
from services.monitoring_service import get_performance_monitor, get_performance_benchmark
from core.database_optimization import initialize_database_optimizations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_light_load_test():
    """Run a light load test for basic performance validation."""
    logger.info("Starting light load test...")
    
    config = LoadTestConfig(
        concurrent_users=5,
        test_duration_seconds=30,
        ramp_up_seconds=5,
        think_time_seconds=0.5
    )
    
    performance_tester = get_performance_tester()
    result = await performance_tester.run_load_test(config)
    
    print("\n" + "="*60)
    print("LIGHT LOAD TEST RESULTS")
    print("="*60)
    print(f"Total Requests: {result.total_requests}")
    print(f"Successful Requests: {result.successful_requests}")
    print(f"Failed Requests: {result.failed_requests}")
    print(f"Requests/Second: {result.requests_per_second:.2f}")
    print(f"Average Response Time: {result.average_response_time*1000:.2f}ms")
    print(f"95th Percentile: {result.p95_response_time*1000:.2f}ms")
    print(f"Error Rate: {result.error_rate:.2%}")
    print("="*60)
    
    return result

async def run_moderate_load_test():
    """Run a moderate load test for normal usage simulation."""
    logger.info("Starting moderate load test...")
    
    config = LoadTestConfig(
        concurrent_users=20,
        test_duration_seconds=120,
        ramp_up_seconds=20,
        think_time_seconds=1.0,
        endpoint_weights={
            '/api/chat/enhanced': 0.5,
            '/api/search/semantic': 0.3,
            '/api/analytics/dashboard': 0.1,
            '/api/knowledge-graph': 0.1
        }
    )
    
    performance_tester = get_performance_tester()
    result = await performance_tester.run_load_test(config)
    
    print("\n" + "="*60)
    print("MODERATE LOAD TEST RESULTS")
    print("="*60)
    print(f"Total Requests: {result.total_requests}")
    print(f"Successful Requests: {result.successful_requests}")
    print(f"Failed Requests: {result.failed_requests}")
    print(f"Requests/Second: {result.requests_per_second:.2f}")
    print(f"Average Response Time: {result.average_response_time*1000:.2f}ms")
    print(f"95th Percentile: {result.p95_response_time*1000:.2f}ms")
    print(f"99th Percentile: {result.p99_response_time*1000:.2f}ms")
    print(f"Error Rate: {result.error_rate:.2%}")
    
    print("\nEndpoint Statistics:")
    for endpoint, stats in result.endpoint_stats.items():
        print(f"  {endpoint}:")
        print(f"    Requests: {stats['request_count']}")
        print(f"    Avg Response Time: {stats['average_response_time']*1000:.2f}ms")
        print(f"    Success Rate: {stats['success_rate']:.2%}")
    
    print("="*60)
    
    return result

async def run_stress_test():
    """Run a stress test to find system limits."""
    logger.info("Starting stress test...")
    
    config = LoadTestConfig(
        concurrent_users=50,
        test_duration_seconds=180,
        ramp_up_seconds=30,
        think_time_seconds=0.5,
        endpoint_weights={
            '/api/chat/enhanced': 0.6,
            '/api/search/semantic': 0.4
        }
    )
    
    performance_tester = get_performance_tester()
    result = await performance_tester.run_load_test(config)
    
    print("\n" + "="*60)
    print("STRESS TEST RESULTS")
    print("="*60)
    print(f"Total Requests: {result.total_requests}")
    print(f"Successful Requests: {result.successful_requests}")
    print(f"Failed Requests: {result.failed_requests}")
    print(f"Requests/Second: {result.requests_per_second:.2f}")
    print(f"Average Response Time: {result.average_response_time*1000:.2f}ms")
    print(f"95th Percentile: {result.p95_response_time*1000:.2f}ms")
    print(f"99th Percentile: {result.p99_response_time*1000:.2f}ms")
    print(f"Error Rate: {result.error_rate:.2%}")
    
    # Analyze stress test results
    if result.error_rate > 0.05:  # 5% error rate threshold
        print("\n⚠️  HIGH ERROR RATE DETECTED - System may be under stress")
    
    if result.p95_response_time > 5.0:  # 5 second threshold
        print("\n⚠️  HIGH RESPONSE TIMES DETECTED - Performance degradation")
    
    print("="*60)
    
    return result

async def run_database_stress_test():
    """Run database-specific stress test."""
    logger.info("Starting database stress test...")
    
    performance_tester = get_performance_tester()
    db_results = await performance_tester.run_database_performance_test()
    
    print("\n" + "="*60)
    print("DATABASE PERFORMANCE TEST RESULTS")
    print("="*60)
    
    for test_name, results in db_results.items():
        avg_time = results['average_time']
        max_time = results['max_time']
        
        print(f"{test_name}:")
        print(f"  Average: {avg_time*1000:.2f}ms")
        print(f"  Maximum: {max_time*1000:.2f}ms")
        
        # Flag slow queries
        if avg_time > 1.0:
            print(f"  ⚠️  SLOW QUERY DETECTED")
    
    print("="*60)
    
    return db_results

async def run_cache_performance_test():
    """Run cache performance test."""
    logger.info("Starting cache performance test...")
    
    performance_tester = get_performance_tester()
    cache_results = await performance_tester.run_cache_performance_test()
    
    print("\n" + "="*60)
    print("CACHE PERFORMANCE TEST RESULTS")
    print("="*60)
    
    for operation, results in cache_results.items():
        if operation != 'cache_stats':
            avg_time = results['average_time']
            print(f"{operation}: {avg_time*1000:.2f}ms avg")
    
    cache_stats = cache_results.get('cache_stats', {})
    if cache_stats:
        hit_rate = cache_stats.get('overall_cache_hit_rate', 0)
        print(f"\nOverall Cache Hit Rate: {hit_rate:.2%}")
        
        if hit_rate < 0.7:  # 70% threshold
            print("⚠️  LOW CACHE HIT RATE - Consider cache optimization")
    
    print("="*60)
    
    return cache_results

async def run_comprehensive_benchmark():
    """Run comprehensive performance benchmark."""
    logger.info("Starting comprehensive benchmark...")
    
    performance_tester = get_performance_tester()
    benchmark_results = await performance_tester.run_comprehensive_benchmark()
    
    # Generate and display report
    report = performance_tester.generate_performance_report(benchmark_results)
    print("\n" + report)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"benchmark_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(benchmark_results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: {filename}")
    
    return benchmark_results

async def run_sla_validation():
    """Validate SLA compliance."""
    logger.info("Validating SLA compliance...")
    
    performance_benchmark = get_performance_benchmark()
    sla_compliance = performance_benchmark.get_all_sla_compliance(24)
    
    print("\n" + "="*60)
    print("SLA COMPLIANCE REPORT")
    print("="*60)
    
    total_benchmarks = 0
    compliant_benchmarks = 0
    
    for benchmark_name, compliance in sla_compliance.items():
        if 'error' in compliance:
            print(f"{benchmark_name}: ERROR - {compliance['error']}")
            continue
        
        total_benchmarks += 1
        meets_sla = compliance.get('meets_sla', False)
        compliance_rate = compliance.get('compliance_rate', 0)
        target = compliance.get('target', 'N/A')
        
        status = "✅ PASS" if meets_sla else "❌ FAIL"
        print(f"{benchmark_name}: {status}")
        print(f"  Compliance Rate: {compliance_rate:.2%}")
        print(f"  Target: {target}")
        print(f"  Average Value: {compliance.get('average_value', 0):.3f}")
        
        if meets_sla:
            compliant_benchmarks += 1
    
    overall_compliance = compliant_benchmarks / total_benchmarks if total_benchmarks > 0 else 0
    print(f"\nOverall SLA Compliance: {overall_compliance:.2%} ({compliant_benchmarks}/{total_benchmarks})")
    
    if overall_compliance < 0.9:  # 90% threshold
        print("⚠️  SLA COMPLIANCE BELOW THRESHOLD - Review system performance")
    
    print("="*60)
    
    return sla_compliance

async def optimize_system():
    """Run system optimizations."""
    logger.info("Running system optimizations...")
    
    try:
        # Initialize database optimizations
        await initialize_database_optimizations()
        print("✅ Database optimizations applied")
        
        # Start monitoring
        performance_monitor = get_performance_monitor()
        await performance_monitor.start_monitoring(interval_seconds=30)
        print("✅ Performance monitoring started")
        
        print("\nSystem optimization completed successfully!")
        
    except Exception as e:
        logger.error(f"System optimization failed: {e}")
        print(f"❌ System optimization failed: {e}")

async def main():
    """Main load testing function."""
    parser = argparse.ArgumentParser(description="AI Scholar RAG Load Testing")
    parser.add_argument(
        '--test-type',
        choices=['light', 'moderate', 'stress', 'database', 'cache', 'benchmark', 'sla', 'optimize', 'all'],
        default='light',
        help='Type of test to run'
    )
    parser.add_argument(
        '--output-file',
        help='File to save detailed results (JSON format)'
    )
    
    args = parser.parse_args()
    
    print("AI Scholar RAG System Load Testing")
    print("="*60)
    print(f"Test Type: {args.test_type}")
    print(f"Start Time: {datetime.now().isoformat()}")
    print("="*60)
    
    results = {}
    
    try:
        if args.test_type == 'light':
            results['light_load'] = await run_light_load_test()
        
        elif args.test_type == 'moderate':
            results['moderate_load'] = await run_moderate_load_test()
        
        elif args.test_type == 'stress':
            results['stress_test'] = await run_stress_test()
        
        elif args.test_type == 'database':
            results['database_test'] = await run_database_stress_test()
        
        elif args.test_type == 'cache':
            results['cache_test'] = await run_cache_performance_test()
        
        elif args.test_type == 'benchmark':
            results['benchmark'] = await run_comprehensive_benchmark()
        
        elif args.test_type == 'sla':
            results['sla_validation'] = await run_sla_validation()
        
        elif args.test_type == 'optimize':
            await optimize_system()
        
        elif args.test_type == 'all':
            print("Running comprehensive test suite...")
            
            # Optimize system first
            await optimize_system()
            
            # Run all tests
            results['light_load'] = await run_light_load_test()
            results['moderate_load'] = await run_moderate_load_test()
            results['database_test'] = await run_database_stress_test()
            results['cache_test'] = await run_cache_performance_test()
            results['sla_validation'] = await run_sla_validation()
            results['benchmark'] = await run_comprehensive_benchmark()
            
            print("\n🎉 Comprehensive test suite completed!")
        
        # Save results if output file specified
        if args.output_file and results:
            with open(args.output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\nResults saved to: {args.output_file}")
    
    except Exception as e:
        logger.error(f"Load testing failed: {e}")
        print(f"\n❌ Load testing failed: {e}")
        return 1
    
    print(f"\nTest completed at: {datetime.now().isoformat()}")
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))