#!/usr/bin/env python3
"""
Performance benchmarking and SLA target configuration.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from services.monitoring_service import get_performance_benchmark, MetricType
from services.performance_testing import get_performance_tester

logger = logging.getLogger(__name__)

# SLA Targets and Benchmarks Configuration
SLA_TARGETS = {
    # Response Time Targets (in seconds)
    'query_response_time': {
        'target': 2.0,      # 2 seconds for query responses
        'sla': 0.95,        # 95% of queries should meet target
        'critical': 5.0     # Critical threshold
    },
    'document_processing_time': {
        'target': 30.0,     # 30 seconds per document
        'sla': 0.90,        # 90% should meet target
        'critical': 60.0    # Critical threshold
    },
    'search_response_time': {
        'target': 1.5,      # 1.5 seconds for search
        'sla': 0.95,        # 95% should meet target
        'critical': 3.0     # Critical threshold
    },
    'analytics_response_time': {
        'target': 3.0,      # 3 seconds for analytics
        'sla': 0.90,        # 90% should meet target
        'critical': 10.0    # Critical threshold
    },
    
    # System Performance Targets
    'system_availability': {
        'target': 0.999,    # 99.9% uptime
        'sla': 0.999,       # Same as target
        'critical': 0.95    # Critical threshold
    },
    'cache_hit_rate': {
        'target': 0.80,     # 80% cache hit rate
        'sla': 0.75,        # Minimum 75%
        'critical': 0.50    # Critical threshold
    },
    'error_rate': {
        'target': 0.01,     # 1% error rate maximum
        'sla': 0.95,        # 95% of time should be below target
        'critical': 0.05    # Critical threshold
    },
    
    # Database Performance Targets
    'db_query_user_lookup': {
        'target': 0.1,      # 100ms for user lookups
        'sla': 0.95,        # 95% should meet target
        'critical': 0.5     # Critical threshold
    },
    'db_query_document_search': {
        'target': 0.5,      # 500ms for document searches
        'sla': 0.90,        # 90% should meet target
        'critical': 2.0     # Critical threshold
    },
    'db_query_analytics': {
        'target': 1.0,      # 1 second for analytics queries
        'sla': 0.85,        # 85% should meet target
        'critical': 5.0     # Critical threshold
    },
    
    # Load Test Targets
    'load_test_avg_response_time': {
        'target': 2.5,      # 2.5 seconds average under load
        'sla': 0.90,        # 90% of load tests should meet target
        'critical': 5.0     # Critical threshold
    },
    'load_test_requests_per_second': {
        'target': 10.0,     # 10 RPS minimum
        'sla': 0.90,        # 90% of load tests should meet target
        'critical': 5.0     # Critical threshold
    },
    
    # Cache Performance Targets
    'cache_set_operation': {
        'target': 0.01,     # 10ms for cache set
        'sla': 0.95,        # 95% should meet target
        'critical': 0.1     # Critical threshold
    },
    'cache_get_operation': {
        'target': 0.005,    # 5ms for cache get
        'sla': 0.95,        # 95% should meet target
        'critical': 0.05    # Critical threshold
    }
}

# Performance Alert Thresholds
ALERT_THRESHOLDS = {
    MetricType.RESPONSE_TIME: 3.0,      # 3 seconds
    MetricType.ERROR_RATE: 0.05,        # 5%
    MetricType.THROUGHPUT: 5.0,         # 5 RPS minimum
    MetricType.MEMORY_USAGE: 0.85,      # 85%
    MetricType.CPU_USAGE: 0.80,         # 80%
    MetricType.DISK_USAGE: 0.90,        # 90%
    MetricType.CACHE_HIT_RATE: 0.70,    # 70% minimum
    MetricType.DATABASE_CONNECTIONS: 50, # 50 connections
    MetricType.ACTIVE_USERS: 100        # 100 concurrent users
}

async def initialize_performance_benchmarks():
    """Initialize performance benchmarks with SLA targets."""
    logger.info("Initializing performance benchmarks...")
    
    performance_benchmark = get_performance_benchmark()
    
    # Set all benchmark targets
    for benchmark_name, config in SLA_TARGETS.items():
        performance_benchmark.set_benchmark(
            name=benchmark_name,
            target=config['target'],
            sla=config['sla']
        )
        logger.info(f"Set benchmark {benchmark_name}: target={config['target']}, sla={config['sla']}")
    
    logger.info("Performance benchmarks initialized successfully")

async def run_baseline_performance_test():
    """Run baseline performance test to establish initial benchmarks."""
    logger.info("Running baseline performance test...")
    
    performance_tester = get_performance_tester()
    
    # Run comprehensive benchmark
    results = await performance_tester.run_comprehensive_benchmark()
    
    # Extract key metrics for baseline
    baseline_metrics = {}
    
    # Database performance
    db_performance = results.get('database_performance', {})
    for test_name, metrics in db_performance.items():
        baseline_metrics[f'db_query_{test_name}'] = metrics.get('average_time', 0)
    
    # Cache performance
    cache_performance = results.get('cache_performance', {})
    for operation, metrics in cache_performance.items():
        if operation != 'cache_stats':
            baseline_metrics[f'cache_{operation}'] = metrics.get('average_time', 0)
    
    # System health
    system_health = results.get('system_health', {})
    baseline_metrics['system_health_score'] = system_health.get('health_score', 0)
    
    # Load test results (if available)
    load_test = results.get('load_test', {})
    if 'error' not in load_test:
        baseline_metrics['load_test_avg_response_time'] = load_test.get('average_response_time', 0)
        baseline_metrics['load_test_requests_per_second'] = load_test.get('requests_per_second', 0)
        baseline_metrics['load_test_error_rate'] = load_test.get('error_rate', 0)
    
    # Save baseline metrics
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    baseline_file = f"baseline_metrics_{timestamp}.json"
    
    import json
    with open(baseline_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'baseline_metrics': baseline_metrics,
            'full_results': results
        }, f, indent=2, default=str)
    
    logger.info(f"Baseline metrics saved to {baseline_file}")
    
    # Print baseline summary
    print("\n" + "="*60)
    print("BASELINE PERFORMANCE METRICS")
    print("="*60)
    
    for metric_name, value in baseline_metrics.items():
        if 'time' in metric_name and isinstance(value, (int, float)):
            print(f"{metric_name}: {value*1000:.2f}ms")
        elif 'rate' in metric_name and isinstance(value, (int, float)):
            print(f"{metric_name}: {value:.2%}")
        elif isinstance(value, (int, float)):
            print(f"{metric_name}: {value:.2f}")
        else:
            print(f"{metric_name}: {value}")
    
    print("="*60)
    
    return baseline_metrics

async def validate_performance_regression(baseline_file: str = None):
    """Validate performance against baseline to detect regressions."""
    logger.info("Validating performance regression...")
    
    if not baseline_file:
        logger.error("No baseline file provided for regression testing")
        return False
    
    try:
        import json
        with open(baseline_file, 'r') as f:
            baseline_data = json.load(f)
        
        baseline_metrics = baseline_data.get('baseline_metrics', {})
    except Exception as e:
        logger.error(f"Failed to load baseline file {baseline_file}: {e}")
        return False
    
    # Run current performance test
    performance_tester = get_performance_tester()
    current_results = await performance_tester.run_comprehensive_benchmark()
    
    # Extract current metrics
    current_metrics = {}
    
    # Database performance
    db_performance = current_results.get('database_performance', {})
    for test_name, metrics in db_performance.items():
        current_metrics[f'db_query_{test_name}'] = metrics.get('average_time', 0)
    
    # Cache performance
    cache_performance = current_results.get('cache_performance', {})
    for operation, metrics in cache_performance.items():
        if operation != 'cache_stats':
            current_metrics[f'cache_{operation}'] = metrics.get('average_time', 0)
    
    # Compare metrics
    regressions = []
    improvements = []
    
    print("\n" + "="*60)
    print("PERFORMANCE REGRESSION ANALYSIS")
    print("="*60)
    
    for metric_name in baseline_metrics.keys():
        if metric_name not in current_metrics:
            continue
        
        baseline_value = baseline_metrics[metric_name]
        current_value = current_metrics[metric_name]
        
        if baseline_value == 0:
            continue
        
        change_percent = ((current_value - baseline_value) / baseline_value) * 100
        
        status = "📈" if change_percent > 10 else "📉" if change_percent < -10 else "➡️"
        
        print(f"{status} {metric_name}:")
        print(f"    Baseline: {baseline_value:.3f}")
        print(f"    Current:  {current_value:.3f}")
        print(f"    Change:   {change_percent:+.1f}%")
        
        if change_percent > 20:  # 20% regression threshold
            regressions.append({
                'metric': metric_name,
                'baseline': baseline_value,
                'current': current_value,
                'change_percent': change_percent
            })
        elif change_percent < -20:  # 20% improvement
            improvements.append({
                'metric': metric_name,
                'baseline': baseline_value,
                'current': current_value,
                'change_percent': change_percent
            })
    
    print("\n" + "="*60)
    
    if regressions:
        print("⚠️  PERFORMANCE REGRESSIONS DETECTED:")
        for regression in regressions:
            print(f"  - {regression['metric']}: {regression['change_percent']:+.1f}% slower")
        print("="*60)
        return False
    
    if improvements:
        print("✅ PERFORMANCE IMPROVEMENTS DETECTED:")
        for improvement in improvements:
            print(f"  - {improvement['metric']}: {improvement['change_percent']:+.1f}% faster")
    
    print("✅ No significant performance regressions detected")
    print("="*60)
    
    return True

async def generate_performance_report():
    """Generate comprehensive performance report."""
    logger.info("Generating performance report...")
    
    performance_tester = get_performance_tester()
    performance_benchmark = get_performance_benchmark()
    
    # Run comprehensive benchmark
    benchmark_results = await performance_tester.run_comprehensive_benchmark()
    
    # Get SLA compliance
    sla_compliance = performance_benchmark.get_all_sla_compliance(24)
    
    # Generate report
    report = performance_tester.generate_performance_report(benchmark_results)
    
    # Add SLA compliance section
    report += "\n\nSLA COMPLIANCE DETAILS:\n"
    report += "="*60 + "\n"
    
    for benchmark_name, compliance in sla_compliance.items():
        if 'error' in compliance:
            report += f"{benchmark_name}: ERROR - {compliance['error']}\n"
            continue
        
        meets_sla = compliance.get('meets_sla', False)
        compliance_rate = compliance.get('compliance_rate', 0)
        target = compliance.get('target', 'N/A')
        
        status = "PASS" if meets_sla else "FAIL"
        report += f"{benchmark_name}: {status}\n"
        report += f"  Compliance Rate: {compliance_rate:.2%}\n"
        report += f"  Target: {target}\n"
        report += f"  P95: {compliance.get('p95_value', 0):.3f}\n"
        report += f"  P99: {compliance.get('p99_value', 0):.3f}\n\n"
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"performance_report_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(report)
    print(f"\nReport saved to: {report_file}")
    
    return report_file

async def main():
    """Main benchmarking function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance Benchmarking")
    parser.add_argument(
        '--action',
        choices=['init', 'baseline', 'regression', 'report'],
        default='init',
        help='Action to perform'
    )
    parser.add_argument(
        '--baseline-file',
        help='Baseline file for regression testing'
    )
    
    args = parser.parse_args()
    
    if args.action == 'init':
        await initialize_performance_benchmarks()
    
    elif args.action == 'baseline':
        await run_baseline_performance_test()
    
    elif args.action == 'regression':
        if not args.baseline_file:
            print("Error: --baseline-file required for regression testing")
            return 1
        
        success = await validate_performance_regression(args.baseline_file)
        return 0 if success else 1
    
    elif args.action == 'report':
        await generate_performance_report()
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))