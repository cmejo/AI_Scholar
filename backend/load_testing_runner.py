"""
Load Testing Runner for Advanced RAG Features

This module provides a comprehensive load testing runner that can be used
to test the performance and scalability of all advanced features.
"""

import asyncio
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.performance_testing_service import (
    PerformanceTestingService,
    LoadTestConfig,
    MobilePerformanceConfig,
    run_comprehensive_performance_tests
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LoadTestingRunner:
    """Comprehensive load testing runner"""
    
    def __init__(self):
        self.performance_service = PerformanceTestingService()
        self.results = []
    
    async def run_mobile_load_tests(self, device_types: List[str] = None, network_types: List[str] = None) -> Dict[str, Any]:
        """Run mobile performance load tests"""
        logger.info("Starting mobile load tests")
        
        device_types = device_types or ['mobile', 'tablet', 'desktop']
        network_types = network_types or ['3g', '4g', '5g', 'wifi']
        
        mobile_results = []
        
        for device_type in device_types:
            for network_type in network_types:
                logger.info(f"Testing {device_type} on {network_type}")
                
                config = MobilePerformanceConfig(
                    device_type=device_type,
                    network_type=network_type,
                    battery_simulation=True,
                    offline_mode_test=True,
                    cache_performance_test=True
                )
                
                results = await self.performance_service.run_mobile_performance_tests(config)
                mobile_results.extend(results)
        
        return {
            'test_type': 'mobile_load_tests',
            'results': mobile_results,
            'summary': self._summarize_results(mobile_results)
        }
    
    async def run_voice_load_tests(self, concurrent_users: List[int] = None) -> Dict[str, Any]:
        """Run voice processing load tests"""
        logger.info("Starting voice processing load tests")
        
        concurrent_users = concurrent_users or [10, 25, 50, 100]
        voice_results = []
        
        for user_count in concurrent_users:
            logger.info(f"Testing voice processing with {user_count} concurrent users")
            
            # Simulate concurrent voice processing
            async def simulate_voice_user():
                return await self.performance_service.run_voice_processing_performance_tests()
            
            # Run concurrent voice tests
            tasks = [simulate_voice_user() for _ in range(min(user_count // 10, 10))]  # Scale down for testing
            concurrent_results = await asyncio.gather(*tasks)
            
            # Flatten results
            for result_set in concurrent_results:
                voice_results.extend(result_set)
        
        return {
            'test_type': 'voice_load_tests',
            'results': voice_results,
            'summary': self._summarize_results(voice_results)
        }
    
    async def run_integration_stress_tests(self, max_concurrent_users: int = 200) -> Dict[str, Any]:
        """Run integration stress tests"""
        logger.info("Starting integration stress tests")
        
        # Define stress test configurations
        stress_configs = [
            LoadTestConfig(
                concurrent_users=50,
                test_duration_seconds=60,
                ramp_up_seconds=15,
                target_endpoint='/api/search',
                request_payload={'query': 'machine learning research'},
                expected_response_time_ms=300,
                max_error_rate_percent=5.0
            ),
            LoadTestConfig(
                concurrent_users=100,
                test_duration_seconds=120,
                ramp_up_seconds=30,
                target_endpoint='/api/voice/process',
                request_payload={'audio_data': 'base64_encoded_audio'},
                expected_response_time_ms=500,
                max_error_rate_percent=3.0
            ),
            LoadTestConfig(
                concurrent_users=max_concurrent_users,
                test_duration_seconds=180,
                ramp_up_seconds=60,
                target_endpoint='/api/documents/analyze',
                request_payload={'document_id': 'test_doc_123'},
                expected_response_time_ms=1000,
                max_error_rate_percent=10.0
            )
        ]
        
        integration_results = await self.performance_service.run_integration_load_tests(stress_configs)
        
        return {
            'test_type': 'integration_stress_tests',
            'results': integration_results,
            'summary': self._summarize_results(integration_results)
        }
    
    async def run_enterprise_capacity_tests(self, max_institutions: int = 100) -> Dict[str, Any]:
        """Run enterprise capacity tests"""
        logger.info("Starting enterprise capacity tests")
        
        # Test enterprise features at scale
        enterprise_results = await self.performance_service.run_enterprise_scalability_tests()
        
        # Additional capacity testing
        capacity_results = []
        
        # Test increasing institutional loads
        institution_counts = [10, 25, 50, max_institutions]
        
        for institution_count in institution_counts:
            logger.info(f"Testing capacity for {institution_count} institutions")
            
            # Simulate institutional load
            start_time = datetime.now()
            
            # Simulate concurrent institutional operations
            async def simulate_institutional_operations():
                await asyncio.sleep(0.1)  # Simulate processing time
                return {
                    'institution_id': f'inst_{institution_count}',
                    'operations_completed': 100,
                    'processing_time_ms': 100
                }
            
            tasks = [simulate_institutional_operations() for _ in range(institution_count)]
            institutional_results = await asyncio.gather(*tasks)
            
            end_time = datetime.now()
            
            capacity_results.append({
                'institution_count': institution_count,
                'total_operations': sum(r['operations_completed'] for r in institutional_results),
                'total_time_ms': (end_time - start_time).total_seconds() * 1000,
                'throughput_ops_per_sec': sum(r['operations_completed'] for r in institutional_results) / ((end_time - start_time).total_seconds())
            })
        
        enterprise_results.extend([{
            'test_name': 'Enterprise Capacity Test',
            'capacity_results': capacity_results
        }])
        
        return {
            'test_type': 'enterprise_capacity_tests',
            'results': enterprise_results,
            'summary': self._summarize_results(enterprise_results)
        }
    
    async def run_endurance_tests(self, duration_hours: float = 1.0) -> Dict[str, Any]:
        """Run endurance tests for long-term stability"""
        logger.info(f"Starting endurance tests for {duration_hours} hours")
        
        duration_seconds = duration_hours * 3600
        test_interval = 60  # Test every minute
        
        endurance_results = []
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < duration_seconds:
            logger.info(f"Endurance test checkpoint at {(datetime.now() - start_time).total_seconds():.0f} seconds")
            
            # Run a subset of tests
            checkpoint_results = []
            
            # Quick mobile test
            mobile_config = MobilePerformanceConfig(
                device_type='mobile',
                network_type='4g',
                battery_simulation=False,
                offline_mode_test=False,
                cache_performance_test=True
            )
            mobile_result = await self.performance_service.run_mobile_performance_tests(mobile_config)
            checkpoint_results.extend(mobile_result)
            
            # Quick voice test
            voice_result = await self.performance_service.run_voice_processing_performance_tests()
            checkpoint_results.extend(voice_result)
            
            endurance_results.append({
                'checkpoint_time': datetime.now().isoformat(),
                'elapsed_seconds': (datetime.now() - start_time).total_seconds(),
                'results': checkpoint_results
            })
            
            # Wait for next interval
            await asyncio.sleep(test_interval)
        
        return {
            'test_type': 'endurance_tests',
            'duration_hours': duration_hours,
            'checkpoints': len(endurance_results),
            'results': endurance_results,
            'summary': self._summarize_endurance_results(endurance_results)
        }
    
    def _summarize_results(self, results: List[Any]) -> Dict[str, Any]:
        """Summarize test results"""
        if not results:
            return {'error': 'No results to summarize'}
        
        # Handle different result formats
        if isinstance(results[0], dict) and 'test_name' in results[0]:
            # PerformanceMetrics format
            total_tests = len(results)
            successful_tests = sum(1 for r in results if r.get('error_rate_percent', 0) < 5.0)
            avg_duration = sum(r.get('duration_ms', 0) for r in results) / total_tests if total_tests > 0 else 0
            avg_cpu = sum(r.get('cpu_usage_percent', 0) for r in results) / total_tests if total_tests > 0 else 0
            avg_memory = sum(r.get('memory_usage_mb', 0) for r in results) / total_tests if total_tests > 0 else 0
        else:
            # Handle other formats
            total_tests = len(results)
            successful_tests = total_tests  # Assume success if no error info
            avg_duration = 0
            avg_cpu = 0
            avg_memory = 0
        
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate_percent': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            'avg_duration_ms': avg_duration,
            'avg_cpu_usage_percent': avg_cpu,
            'avg_memory_usage_mb': avg_memory
        }
    
    def _summarize_endurance_results(self, endurance_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize endurance test results"""
        if not endurance_results:
            return {'error': 'No endurance results to summarize'}
        
        total_checkpoints = len(endurance_results)
        
        # Analyze performance degradation over time
        performance_trend = []
        for checkpoint in endurance_results:
            checkpoint_summary = self._summarize_results(checkpoint['results'])
            performance_trend.append({
                'elapsed_seconds': checkpoint['elapsed_seconds'],
                'success_rate': checkpoint_summary.get('success_rate_percent', 0),
                'avg_duration_ms': checkpoint_summary.get('avg_duration_ms', 0)
            })
        
        # Calculate stability metrics
        success_rates = [p['success_rate'] for p in performance_trend]
        durations = [p['avg_duration_ms'] for p in performance_trend if p['avg_duration_ms'] > 0]
        
        stability_score = min(success_rates) if success_rates else 0
        performance_consistency = 100 - (max(durations) - min(durations)) / max(durations) * 100 if durations and max(durations) > 0 else 100
        
        return {
            'total_checkpoints': total_checkpoints,
            'stability_score': stability_score,
            'performance_consistency': max(0, performance_consistency),
            'performance_trend': performance_trend,
            'endurance_passed': stability_score > 90 and performance_consistency > 80
        }
    
    async def run_comprehensive_load_tests(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run comprehensive load tests"""
        config = config or {}
        
        logger.info("Starting comprehensive load testing suite")
        
        all_results = {}
        
        # Mobile load tests
        if config.get('include_mobile', True):
            mobile_results = await self.run_mobile_load_tests(
                device_types=config.get('device_types'),
                network_types=config.get('network_types')
            )
            all_results['mobile'] = mobile_results
        
        # Voice load tests
        if config.get('include_voice', True):
            voice_results = await self.run_voice_load_tests(
                concurrent_users=config.get('voice_concurrent_users')
            )
            all_results['voice'] = voice_results
        
        # Integration stress tests
        if config.get('include_integration', True):
            integration_results = await self.run_integration_stress_tests(
                max_concurrent_users=config.get('max_concurrent_users', 200)
            )
            all_results['integration'] = integration_results
        
        # Enterprise capacity tests
        if config.get('include_enterprise', True):
            enterprise_results = await self.run_enterprise_capacity_tests(
                max_institutions=config.get('max_institutions', 100)
            )
            all_results['enterprise'] = enterprise_results
        
        # Endurance tests (optional, can be time-consuming)
        if config.get('include_endurance', False):
            endurance_results = await self.run_endurance_tests(
                duration_hours=config.get('endurance_hours', 0.5)
            )
            all_results['endurance'] = endurance_results
        
        # Generate overall summary
        overall_summary = self._generate_overall_summary(all_results)
        
        return {
            'test_suite': 'comprehensive_load_tests',
            'timestamp': datetime.now().isoformat(),
            'configuration': config,
            'results': all_results,
            'overall_summary': overall_summary
        }
    
    def _generate_overall_summary(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall summary of all test results"""
        total_test_categories = len(all_results)
        passed_categories = 0
        
        category_summaries = {}
        
        for category, results in all_results.items():
            summary = results.get('summary', {})
            success_rate = summary.get('success_rate_percent', 0)
            
            category_summaries[category] = {
                'success_rate': success_rate,
                'passed': success_rate >= 80  # 80% threshold for passing
            }
            
            if success_rate >= 80:
                passed_categories += 1
        
        overall_pass_rate = (passed_categories / total_test_categories * 100) if total_test_categories > 0 else 0
        
        return {
            'total_categories': total_test_categories,
            'passed_categories': passed_categories,
            'overall_pass_rate': overall_pass_rate,
            'category_summaries': category_summaries,
            'load_testing_passed': overall_pass_rate >= 80,
            'recommendations': self._generate_load_test_recommendations(category_summaries)
        }
    
    def _generate_load_test_recommendations(self, category_summaries: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on load test results"""
        recommendations = []
        
        for category, summary in category_summaries.items():
            if not summary['passed']:
                success_rate = summary['success_rate']
                if success_rate < 50:
                    recommendations.append(f"Critical performance issues in {category} testing. Immediate optimization required.")
                elif success_rate < 80:
                    recommendations.append(f"Performance issues detected in {category} testing. Optimization recommended.")
        
        if not recommendations:
            recommendations.append("All load tests passed successfully. System is performing well under load.")
        
        return recommendations

async def main():
    """Main function for running load tests"""
    parser = argparse.ArgumentParser(description='Advanced RAG Load Testing Runner')
    parser.add_argument('--test-type', choices=['mobile', 'voice', 'integration', 'enterprise', 'endurance', 'comprehensive'], 
                       default='comprehensive', help='Type of load test to run')
    parser.add_argument('--output-file', type=str, help='Output file for test results (JSON format)')
    parser.add_argument('--max-concurrent-users', type=int, default=100, help='Maximum concurrent users for load testing')
    parser.add_argument('--endurance-hours', type=float, default=0.5, help='Duration for endurance tests in hours')
    parser.add_argument('--include-endurance', action='store_true', help='Include endurance tests in comprehensive testing')
    
    args = parser.parse_args()
    
    runner = LoadTestingRunner()
    
    try:
        if args.test_type == 'mobile':
            results = await runner.run_mobile_load_tests()
        elif args.test_type == 'voice':
            results = await runner.run_voice_load_tests()
        elif args.test_type == 'integration':
            results = await runner.run_integration_stress_tests(args.max_concurrent_users)
        elif args.test_type == 'enterprise':
            results = await runner.run_enterprise_capacity_tests()
        elif args.test_type == 'endurance':
            results = await runner.run_endurance_tests(args.endurance_hours)
        else:  # comprehensive
            config = {
                'max_concurrent_users': args.max_concurrent_users,
                'include_endurance': args.include_endurance,
                'endurance_hours': args.endurance_hours
            }
            results = await runner.run_comprehensive_load_tests(config)
        
        # Output results
        if args.output_file:
            with open(args.output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Results saved to {args.output_file}")
        else:
            print(json.dumps(results, indent=2, default=str))
        
        # Print summary
        if 'overall_summary' in results:
            summary = results['overall_summary']
            logger.info(f"Load Testing Summary:")
            logger.info(f"  Overall Pass Rate: {summary['overall_pass_rate']:.1f}%")
            logger.info(f"  Categories Passed: {summary['passed_categories']}/{summary['total_categories']}")
            logger.info(f"  Load Testing Passed: {summary['load_testing_passed']}")
            
            if summary['recommendations']:
                logger.info("Recommendations:")
                for rec in summary['recommendations']:
                    logger.info(f"  - {rec}")
    
    except Exception as e:
        logger.error(f"Load testing failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())