"""
Test result collection and aggregation service.
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import json

from core.redis_client import RedisClient, get_redis_client
from services.test_runner_service import TestResult, TestSuite, ComprehensiveTestReport, TestStatus

logger = logging.getLogger(__name__)

class AggregationPeriod(Enum):
    """Time periods for aggregation."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

@dataclass
class TestMetrics:
    """Aggregated test metrics."""
    period: str
    start_time: datetime
    end_time: datetime
    total_executions: int
    successful_executions: int
    failed_executions: int
    error_executions: int
    success_rate: float
    average_execution_time: float
    total_tests_run: int
    total_tests_passed: int
    total_tests_failed: int
    test_pass_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **asdict(self),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat()
        }

@dataclass
class TestSuiteMetrics:
    """Metrics for individual test suites."""
    suite_name: str
    period: str
    executions: int
    average_duration: float
    pass_rate: float
    most_common_failures: List[Dict[str, Any]]
    performance_trend: List[float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

@dataclass
class TestTrend:
    """Test execution trends."""
    metric_name: str
    time_series: List[Tuple[datetime, float]]
    trend_direction: str  # "improving", "degrading", "stable"
    trend_strength: float  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'metric_name': self.metric_name,
            'time_series': [(ts.isoformat(), value) for ts, value in self.time_series],
            'trend_direction': self.trend_direction,
            'trend_strength': self.trend_strength
        }

class TestResultAggregator:
    """Service for collecting and aggregating test results."""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self.aggregation_cache = {}
        
    async def collect_test_results(self, test_report: ComprehensiveTestReport):
        """Collect and store test results for aggregation."""
        try:
            # Store the complete test report
            report_key = f"test_report:{test_report.timestamp.strftime('%Y-%m-%d-%H-%M-%S')}"
            await self.redis_client.set(
                report_key, 
                test_report.to_dict(), 
                ex=90 * 24 * 3600  # Keep for 90 days
            )
            
            # Extract and store key metrics for quick aggregation
            metrics = self._extract_key_metrics(test_report)
            metrics_key = f"test_metrics:{test_report.timestamp.strftime('%Y-%m-%d-%H')}"
            
            # Append to hourly metrics list
            await self.redis_client.lpush(metrics_key, metrics)
            await self.redis_client.expire(metrics_key, 90 * 24 * 3600)
            
            # Update real-time counters
            await self._update_counters(test_report)
            
            logger.info(f"Collected test results: {report_key}")
        
        except Exception as e:
            logger.error(f"Failed to collect test results: {e}")
    
    def _extract_key_metrics(self, test_report: ComprehensiveTestReport) -> Dict[str, Any]:
        """Extract key metrics from test report."""
        total_tests = sum(suite.total_tests for suite in test_report.test_suites)
        total_passed = sum(suite.passed_tests for suite in test_report.test_suites)
        total_failed = sum(suite.failed_tests for suite in test_report.test_suites)
        total_errors = sum(suite.error_tests for suite in test_report.test_suites)
        
        return {
            'timestamp': test_report.timestamp.isoformat(),
            'overall_status': test_report.overall_status.value,
            'execution_time': test_report.total_execution_time,
            'system_health_score': test_report.system_health_score,
            'total_tests': total_tests,
            'passed_tests': total_passed,
            'failed_tests': total_failed,
            'error_tests': total_errors,
            'pass_rate': total_passed / total_tests if total_tests > 0 else 0,
            'suite_metrics': [
                {
                    'name': suite.suite_name,
                    'duration': suite.execution_time,
                    'total_tests': suite.total_tests,
                    'passed_tests': suite.passed_tests,
                    'failed_tests': suite.failed_tests,
                    'pass_rate': suite.passed_tests / suite.total_tests if suite.total_tests > 0 else 0
                }
                for suite in test_report.test_suites
            ]
        }
    
    async def _update_counters(self, test_report: ComprehensiveTestReport):
        """Update real-time counters."""
        try:
            # Daily counters
            date_key = test_report.timestamp.strftime('%Y-%m-%d')
            
            await self.redis_client.incr(f"test_counter:executions:{date_key}")
            
            if test_report.overall_status == TestStatus.PASSED:
                await self.redis_client.incr(f"test_counter:successes:{date_key}")
            elif test_report.overall_status == TestStatus.FAILED:
                await self.redis_client.incr(f"test_counter:failures:{date_key}")
            else:
                await self.redis_client.incr(f"test_counter:errors:{date_key}")
            
            # Set expiration for counters
            for counter_type in ['executions', 'successes', 'failures', 'errors']:
                await self.redis_client.expire(f"test_counter:{counter_type}:{date_key}", 90 * 24 * 3600)
        
        except Exception as e:
            logger.error(f"Failed to update counters: {e}")
    
    async def get_aggregated_metrics(self, period: AggregationPeriod, 
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> TestMetrics:
        """Get aggregated test metrics for a specific period."""
        if end_date is None:
            end_date = datetime.now()
        
        if start_date is None:
            if period == AggregationPeriod.HOURLY:
                start_date = end_date - timedelta(hours=24)
            elif period == AggregationPeriod.DAILY:
                start_date = end_date - timedelta(days=30)
            elif period == AggregationPeriod.WEEKLY:
                start_date = end_date - timedelta(weeks=12)
            else:  # MONTHLY
                start_date = end_date - timedelta(days=365)
        
        try:
            # Get metrics data for the period
            metrics_data = await self._get_metrics_data(start_date, end_date, period)
            
            if not metrics_data:
                return TestMetrics(
                    period=period.value,
                    start_time=start_date,
                    end_time=end_date,
                    total_executions=0,
                    successful_executions=0,
                    failed_executions=0,
                    error_executions=0,
                    success_rate=0.0,
                    average_execution_time=0.0,
                    total_tests_run=0,
                    total_tests_passed=0,
                    total_tests_failed=0,
                    test_pass_rate=0.0
                )
            
            # Aggregate the data
            total_executions = len(metrics_data)
            successful_executions = sum(1 for m in metrics_data if m['overall_status'] == 'passed')
            failed_executions = sum(1 for m in metrics_data if m['overall_status'] == 'failed')
            error_executions = sum(1 for m in metrics_data if m['overall_status'] == 'error')
            
            success_rate = successful_executions / total_executions if total_executions > 0 else 0
            
            execution_times = [m['execution_time'] for m in metrics_data if m.get('execution_time')]
            average_execution_time = statistics.mean(execution_times) if execution_times else 0
            
            total_tests_run = sum(m.get('total_tests', 0) for m in metrics_data)
            total_tests_passed = sum(m.get('passed_tests', 0) for m in metrics_data)
            total_tests_failed = sum(m.get('failed_tests', 0) for m in metrics_data)
            
            test_pass_rate = total_tests_passed / total_tests_run if total_tests_run > 0 else 0
            
            return TestMetrics(
                period=period.value,
                start_time=start_date,
                end_time=end_date,
                total_executions=total_executions,
                successful_executions=successful_executions,
                failed_executions=failed_executions,
                error_executions=error_executions,
                success_rate=success_rate,
                average_execution_time=average_execution_time,
                total_tests_run=total_tests_run,
                total_tests_passed=total_tests_passed,
                total_tests_failed=total_tests_failed,
                test_pass_rate=test_pass_rate
            )
        
        except Exception as e:
            logger.error(f"Failed to get aggregated metrics: {e}")
            raise
    
    async def get_suite_metrics(self, suite_name: str, 
                              period: AggregationPeriod,
                              days: int = 30) -> TestSuiteMetrics:
        """Get metrics for a specific test suite."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            metrics_data = await self._get_metrics_data(start_date, end_date, period)
            
            # Filter for specific suite
            suite_data = []
            for metrics in metrics_data:
                for suite_metric in metrics.get('suite_metrics', []):
                    if suite_metric['name'] == suite_name:
                        suite_data.append({
                            **suite_metric,
                            'timestamp': metrics['timestamp']
                        })
            
            if not suite_data:
                return TestSuiteMetrics(
                    suite_name=suite_name,
                    period=period.value,
                    executions=0,
                    average_duration=0.0,
                    pass_rate=0.0,
                    most_common_failures=[],
                    performance_trend=[]
                )
            
            # Calculate metrics
            executions = len(suite_data)
            durations = [s['duration'] for s in suite_data if s.get('duration')]
            average_duration = statistics.mean(durations) if durations else 0
            
            pass_rates = [s['pass_rate'] for s in suite_data if s.get('pass_rate') is not None]
            pass_rate = statistics.mean(pass_rates) if pass_rates else 0
            
            # Performance trend (last 10 executions)
            recent_data = sorted(suite_data, key=lambda x: x['timestamp'])[-10:]
            performance_trend = [s['duration'] for s in recent_data if s.get('duration')]
            
            return TestSuiteMetrics(
                suite_name=suite_name,
                period=period.value,
                executions=executions,
                average_duration=average_duration,
                pass_rate=pass_rate,
                most_common_failures=[],  # Would be implemented with failure analysis
                performance_trend=performance_trend
            )
        
        except Exception as e:
            logger.error(f"Failed to get suite metrics: {e}")
            raise
    
    async def get_test_trends(self, metrics: List[str], days: int = 30) -> List[TestTrend]:
        """Get test execution trends."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            metrics_data = await self._get_metrics_data(start_date, end_date, AggregationPeriod.DAILY)
            
            trends = []
            
            for metric_name in metrics:
                time_series = []
                
                for data in metrics_data:
                    timestamp = datetime.fromisoformat(data['timestamp'])
                    value = data.get(metric_name, 0)
                    time_series.append((timestamp, value))
                
                # Sort by timestamp
                time_series.sort(key=lambda x: x[0])
                
                # Calculate trend
                if len(time_series) >= 2:
                    values = [v for _, v in time_series]
                    trend_direction, trend_strength = self._calculate_trend(values)
                else:
                    trend_direction = "stable"
                    trend_strength = 0.0
                
                trends.append(TestTrend(
                    metric_name=metric_name,
                    time_series=time_series,
                    trend_direction=trend_direction,
                    trend_strength=trend_strength
                ))
            
            return trends
        
        except Exception as e:
            logger.error(f"Failed to get test trends: {e}")
            return []
    
    def _calculate_trend(self, values: List[float]) -> Tuple[str, float]:
        """Calculate trend direction and strength."""
        if len(values) < 2:
            return "stable", 0.0
        
        # Simple linear regression to determine trend
        n = len(values)
        x = list(range(n))
        
        # Calculate slope
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable", 0.0
        
        slope = numerator / denominator
        
        # Calculate correlation coefficient for strength
        try:
            correlation = statistics.correlation(x, values)
            strength = abs(correlation)
        except:
            strength = 0.0
        
        # Determine direction
        if abs(slope) < 0.01:  # Very small slope
            direction = "stable"
        elif slope > 0:
            direction = "improving"
        else:
            direction = "degrading"
        
        return direction, strength
    
    async def _get_metrics_data(self, start_date: datetime, end_date: datetime, 
                              period: AggregationPeriod) -> List[Dict[str, Any]]:
        """Get metrics data for a date range."""
        metrics_data = []
        
        try:
            if period == AggregationPeriod.HOURLY:
                # Get hourly data
                current = start_date.replace(minute=0, second=0, microsecond=0)
                while current <= end_date:
                    hour_key = f"test_metrics:{current.strftime('%Y-%m-%d-%H')}"
                    hour_data = await self.redis_client.lrange(hour_key, 0, -1)
                    
                    for data in hour_data:
                        if isinstance(data, dict):
                            metrics_data.append(data)
                    
                    current += timedelta(hours=1)
            
            else:
                # For daily, weekly, monthly - aggregate from hourly data
                current = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                while current <= end_date:
                    day_start = current
                    day_end = current + timedelta(days=1)
                    
                    # Get all hourly data for the day
                    day_metrics = []
                    hour = day_start
                    while hour < day_end:
                        hour_key = f"test_metrics:{hour.strftime('%Y-%m-%d-%H')}"
                        hour_data = await self.redis_client.lrange(hour_key, 0, -1)
                        
                        for data in hour_data:
                            if isinstance(data, dict):
                                day_metrics.append(data)
                        
                        hour += timedelta(hours=1)
                    
                    # Aggregate day metrics if we have data
                    if day_metrics:
                        if period == AggregationPeriod.DAILY:
                            # Add each execution for daily view
                            metrics_data.extend(day_metrics)
                        else:
                            # Aggregate for weekly/monthly
                            aggregated = self._aggregate_day_metrics(day_metrics, current)
                            if aggregated:
                                metrics_data.append(aggregated)
                    
                    current += timedelta(days=1)
        
        except Exception as e:
            logger.error(f"Failed to get metrics data: {e}")
        
        return metrics_data
    
    def _aggregate_day_metrics(self, day_metrics: List[Dict[str, Any]], 
                             date: datetime) -> Optional[Dict[str, Any]]:
        """Aggregate metrics for a single day."""
        if not day_metrics:
            return None
        
        total_executions = len(day_metrics)
        successful = sum(1 for m in day_metrics if m.get('overall_status') == 'passed')
        failed = sum(1 for m in day_metrics if m.get('overall_status') == 'failed')
        errors = sum(1 for m in day_metrics if m.get('overall_status') == 'error')
        
        execution_times = [m.get('execution_time', 0) for m in day_metrics]
        avg_execution_time = statistics.mean(execution_times) if execution_times else 0
        
        total_tests = sum(m.get('total_tests', 0) for m in day_metrics)
        passed_tests = sum(m.get('passed_tests', 0) for m in day_metrics)
        failed_tests = sum(m.get('failed_tests', 0) for m in day_metrics)
        
        health_scores = [m.get('system_health_score', 0) for m in day_metrics if m.get('system_health_score')]
        avg_health_score = statistics.mean(health_scores) if health_scores else 0
        
        return {
            'timestamp': date.isoformat(),
            'overall_status': 'passed' if successful == total_executions else 'mixed',
            'execution_time': avg_execution_time,
            'system_health_score': avg_health_score,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'pass_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'executions': total_executions,
            'successful_executions': successful,
            'failed_executions': failed,
            'error_executions': errors
        }
    
    async def get_failure_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Get analysis of test failures."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            # Get all test reports for the period
            failure_data = {
                'total_failures': 0,
                'failure_by_suite': {},
                'common_error_patterns': [],
                'failure_trend': [],
                'most_failing_tests': []
            }
            
            # This would analyze actual test reports for detailed failure information
            # For now, return basic structure
            
            return failure_data
        
        except Exception as e:
            logger.error(f"Failed to get failure analysis: {e}")
            return {}
    
    async def generate_test_summary(self, days: int = 7) -> Dict[str, Any]:
        """Generate a comprehensive test summary."""
        try:
            # Get aggregated metrics
            daily_metrics = await self.get_aggregated_metrics(
                AggregationPeriod.DAILY, 
                datetime.now() - timedelta(days=days)
            )
            
            # Get trends
            trends = await self.get_test_trends(['pass_rate', 'execution_time'], days)
            
            # Get failure analysis
            failure_analysis = await self.get_failure_analysis(days)
            
            return {
                'period_days': days,
                'metrics': daily_metrics.to_dict(),
                'trends': [trend.to_dict() for trend in trends],
                'failure_analysis': failure_analysis,
                'generated_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to generate test summary: {e}")
            return {}

# Global aggregator instance
test_result_aggregator = TestResultAggregator()

def get_test_result_aggregator() -> TestResultAggregator:
    """Get the global test result aggregator instance."""
    return test_result_aggregator