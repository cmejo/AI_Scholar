"""
Test reporting and notification service.
"""
import asyncio
import logging
import json
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp

from services.test_runner_service import ComprehensiveTestReport, TestResult, TestStatus, TestSeverity
from core.redis_client import get_redis_client
from core.test_config import get_test_config_manager

logger = logging.getLogger(__name__)

class TestReportGenerator:
    """Generates comprehensive test reports in various formats."""
    
    def __init__(self):
        self.config_manager = get_test_config_manager()
        self.execution_config = self.config_manager.execution_config
        
    def generate_html_report(self, test_report: ComprehensiveTestReport) -> str:
        """Generate HTML test report."""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Execution Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
                .summary { margin: 20px 0; }
                .test-suite { margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; }
                .suite-header { background-color: #e9e9e9; padding: 10px; font-weight: bold; }
                .test-result { padding: 10px; border-bottom: 1px solid #eee; }
                .passed { color: green; }
                .failed { color: red; }
                .error { color: orange; }
                .metadata { font-size: 0.9em; color: #666; margin-top: 5px; }
                .recommendations { background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Test Execution Report</h1>
                <p><strong>Execution Time:</strong> {timestamp}</p>
                <p><strong>Total Duration:</strong> {total_duration:.2f} seconds</p>
                <p><strong>Overall Status:</strong> <span class="{overall_status_class}">{overall_status}</span></p>
                <p><strong>System Health Score:</strong> {health_score:.1f}/100</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <table border="1" cellpadding="5" cellspacing="0">
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Total Test Suites</td><td>{total_suites}</td></tr>
                    <tr><td>Total Tests</td><td>{total_tests}</td></tr>
                    <tr><td>Passed Tests</td><td class="passed">{passed_tests}</td></tr>
                    <tr><td>Failed Tests</td><td class="failed">{failed_tests}</td></tr>
                    <tr><td>Error Tests</td><td class="error">{error_tests}</td></tr>
                    <tr><td>Success Rate</td><td>{success_rate:.1%}</td></tr>
                </table>
            </div>
            
            {test_suites_html}
            
            {recommendations_html}
            
            <div class="footer">
                <p><em>Generated on {generation_time}</em></p>
            </div>
        </body>
        </html>
        """
        
        # Calculate summary statistics
        total_tests = sum(suite.total_tests for suite in test_report.test_suites)
        passed_tests = sum(suite.passed_tests for suite in test_report.test_suites)
        failed_tests = sum(suite.failed_tests for suite in test_report.test_suites)
        error_tests = sum(suite.error_tests for suite in test_report.test_suites)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        # Generate test suites HTML
        test_suites_html = ""
        for suite in test_report.test_suites:
            suite_html = f"""
            <div class="test-suite">
                <div class="suite-header">
                    {suite.suite_name} ({suite.passed_tests}/{suite.total_tests} passed, {suite.execution_time:.2f}s)
                </div>
            """
            
            for test in suite.tests:
                status_class = test.status.value.lower()
                metadata_html = ""
                if test.metadata:
                    metadata_items = [f"{k}: {v}" for k, v in test.metadata.items()]
                    metadata_html = f'<div class="metadata">{", ".join(metadata_items)}</div>'
                
                error_html = ""
                if test.error_message:
                    error_html = f'<div class="metadata"><strong>Error:</strong> {test.error_message}</div>'
                
                test_html = f"""
                <div class="test-result">
                    <span class="{status_class}"><strong>{test.test_name}</strong></span>
                    <span style="float: right;">{test.duration:.3f}s</span>
                    {error_html}
                    {metadata_html}
                </div>
                """
                suite_html += test_html
            
            suite_html += "</div>"
            test_suites_html += suite_html
        
        # Generate recommendations HTML
        recommendations_html = ""
        if test_report.recommendations:
            recommendations_html = """
            <div class="recommendations">
                <h2>Recommendations</h2>
                <ul>
            """
            for rec in test_report.recommendations:
                recommendations_html += f"<li>{rec}</li>"
            recommendations_html += "</ul></div>"
        
        # Fill template
        html_report = html_template.format(
            timestamp=test_report.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            total_duration=test_report.total_execution_time,
            overall_status=test_report.overall_status.value.title(),
            overall_status_class=test_report.overall_status.value.lower(),
            health_score=test_report.system_health_score,
            total_suites=len(test_report.test_suites),
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            error_tests=error_tests,
            success_rate=success_rate,
            test_suites_html=test_suites_html,
            recommendations_html=recommendations_html,
            generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return html_report    

    def generate_json_report(self, test_report: ComprehensiveTestReport) -> str:
        """Generate JSON test report."""
        return json.dumps(test_report.to_dict(), indent=2, default=str)
    
    def generate_csv_report(self, test_report: ComprehensiveTestReport) -> str:
        """Generate CSV test report."""
        csv_lines = [
            "Suite,Test Name,Status,Duration,Error Message,Severity"
        ]
        
        for suite in test_report.test_suites:
            for test in suite.tests:
                csv_lines.append(
                    f'"{suite.suite_name}","{test.test_name}","{test.status.value}",'
                    f'{test.duration},"{test.error_message or ""}","{test.severity.value}"'
                )
        
        return "\n".join(csv_lines)
    
    def save_report(self, test_report: ComprehensiveTestReport, format: str = "html") -> str:
        """Save test report to file."""
        if not self.execution_config.generate_html_report and format == "html":
            return ""
        
        # Create reports directory
        reports_dir = Path(self.execution_config.report_output_dir)
        reports_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = test_report.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"test_report_{timestamp}.{format}"
        filepath = reports_dir / filename
        
        # Generate report content
        if format == "html":
            content = self.generate_html_report(test_report)
        elif format == "json":
            content = self.generate_json_report(test_report)
        elif format == "csv":
            content = self.generate_csv_report(test_report)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Test report saved: {filepath}")
        return str(filepath)

class TestNotificationService:
    """Handles test result notifications."""
    
    def __init__(self):
        self.config_manager = get_test_config_manager()
        self.notification_config = self.config_manager.notification_config
        self.redis_client = get_redis_client()
        
    async def send_notifications(self, test_report: ComprehensiveTestReport):
        """Send test result notifications."""
        if not self.notification_config.enabled:
            return
        
        # Check if we should notify (failure only or always)
        should_notify = True
        if self.notification_config.notify_on_failure_only:
            should_notify = test_report.overall_status in [TestStatus.FAILED, TestStatus.ERROR]
        
        if not should_notify:
            return
        
        # Send email notifications
        if self.notification_config.email_recipients:
            await self._send_email_notification(test_report)
        
        # Send Slack notifications
        if self.notification_config.slack_webhook_url:
            await self._send_slack_notification(test_report)
    
    async def _send_email_notification(self, test_report: ComprehensiveTestReport):
        """Send email notification."""
        try:
            # Create email content
            subject = f"Test Execution Report - {test_report.overall_status.value.title()}"
            
            # Generate summary
            total_tests = sum(suite.total_tests for suite in test_report.test_suites)
            passed_tests = sum(suite.passed_tests for suite in test_report.test_suites)
            failed_tests = sum(suite.failed_tests for suite in test_report.test_suites)
            
            body = f"""
Test Execution Summary
=====================

Execution Time: {test_report.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
Overall Status: {test_report.overall_status.value.title()}
Total Duration: {test_report.total_execution_time:.2f} seconds
System Health Score: {test_report.system_health_score:.1f}/100

Test Results:
- Total Tests: {total_tests}
- Passed: {passed_tests}
- Failed: {failed_tests}
- Success Rate: {passed_tests/total_tests*100:.1f}%

Test Suites:
"""
            
            for suite in test_report.test_suites:
                body += f"\n{suite.suite_name}: {suite.passed_tests}/{suite.total_tests} passed ({suite.execution_time:.2f}s)"
            
            if test_report.recommendations:
                body += "\n\nRecommendations:\n"
                for rec in test_report.recommendations:
                    body += f"- {rec}\n"
            
            # Create email message
            msg = MimeMultipart()
            msg['From'] = "test-system@yourcompany.com"
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MimeText(body, 'plain'))
            
            # Send to all recipients
            for recipient in self.notification_config.email_recipients:
                msg['To'] = recipient
                
                # This would use actual SMTP configuration
                logger.info(f"Would send email notification to {recipient}")
                # smtp_server.send_message(msg)
        
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    async def _send_slack_notification(self, test_report: ComprehensiveTestReport):
        """Send Slack notification."""
        try:
            # Determine color based on status
            color_map = {
                TestStatus.PASSED: "good",
                TestStatus.FAILED: "danger",
                TestStatus.ERROR: "warning"
            }
            color = color_map.get(test_report.overall_status, "warning")
            
            # Calculate summary stats
            total_tests = sum(suite.total_tests for suite in test_report.test_suites)
            passed_tests = sum(suite.passed_tests for suite in test_report.test_suites)
            failed_tests = sum(suite.failed_tests for suite in test_report.test_suites)
            
            # Create Slack message
            slack_message = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"Test Execution Report - {test_report.overall_status.value.title()}",
                        "fields": [
                            {
                                "title": "Execution Time",
                                "value": test_report.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                "short": True
                            },
                            {
                                "title": "Duration",
                                "value": f"{test_report.total_execution_time:.2f}s",
                                "short": True
                            },
                            {
                                "title": "Total Tests",
                                "value": str(total_tests),
                                "short": True
                            },
                            {
                                "title": "Success Rate",
                                "value": f"{passed_tests/total_tests*100:.1f}%" if total_tests > 0 else "0%",
                                "short": True
                            },
                            {
                                "title": "System Health",
                                "value": f"{test_report.system_health_score:.1f}/100",
                                "short": True
                            }
                        ]
                    }
                ]
            }
            
            # Add failed tests details if any
            if failed_tests > 0:
                failed_details = []
                for suite in test_report.test_suites:
                    for test in suite.tests:
                        if test.status in [TestStatus.FAILED, TestStatus.ERROR]:
                            failed_details.append(f"• {suite.suite_name}: {test.test_name}")
                
                if failed_details:
                    slack_message["attachments"][0]["fields"].append({
                        "title": "Failed Tests",
                        "value": "\n".join(failed_details[:10]),  # Limit to first 10
                        "short": False
                    })
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.notification_config.slack_webhook_url,
                    json=slack_message
                ) as response:
                    if response.status == 200:
                        logger.info("Slack notification sent successfully")
                    else:
                        logger.error(f"Failed to send Slack notification: {response.status}")
        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
class Tes
tHistoryTracker:
    """Tracks test execution history and trends."""
    
    def __init__(self):
        self.redis_client = get_redis_client()
    
    async def store_test_execution(self, test_report: ComprehensiveTestReport):
        """Store test execution in history."""
        try:
            # Create execution summary
            total_tests = sum(suite.total_tests for suite in test_report.test_suites)
            passed_tests = sum(suite.passed_tests for suite in test_report.test_suites)
            failed_tests = sum(suite.failed_tests for suite in test_report.test_suites)
            
            execution_summary = {
                'timestamp': test_report.timestamp.isoformat(),
                'overall_status': test_report.overall_status.value,
                'total_execution_time': test_report.total_execution_time,
                'system_health_score': test_report.system_health_score,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'test_suites': [
                    {
                        'name': suite.suite_name,
                        'total_tests': suite.total_tests,
                        'passed_tests': suite.passed_tests,
                        'failed_tests': suite.failed_tests,
                        'execution_time': suite.execution_time
                    }
                    for suite in test_report.test_suites
                ]
            }
            
            # Store in Redis with timestamp-based key
            history_key = f"test_history:{test_report.timestamp.strftime('%Y-%m-%d')}"
            await self.redis_client.lpush(history_key, execution_summary)
            
            # Keep only last 100 executions per day
            await self.redis_client.ltrim(history_key, 0, 99)
            
            # Set expiration for 90 days
            await self.redis_client.expire(history_key, 90 * 24 * 3600)
            
            # Update daily summary
            await self._update_daily_summary(test_report.timestamp.date(), execution_summary)
            
            logger.info(f"Test execution stored in history: {history_key}")
        
        except Exception as e:
            logger.error(f"Failed to store test execution: {e}")
    
    async def _update_daily_summary(self, date, execution_summary):
        """Update daily test summary."""
        try:
            summary_key = f"test_summary:{date.strftime('%Y-%m-%d')}"
            
            # Get existing summary
            existing_summary = await self.redis_client.get(summary_key)
            if existing_summary:
                daily_summary = existing_summary
            else:
                daily_summary = {
                    'date': date.isoformat(),
                    'total_executions': 0,
                    'successful_executions': 0,
                    'failed_executions': 0,
                    'total_tests_run': 0,
                    'total_tests_passed': 0,
                    'average_execution_time': 0,
                    'average_health_score': 0
                }
            
            # Update summary
            daily_summary['total_executions'] += 1
            if execution_summary['overall_status'] == 'passed':
                daily_summary['successful_executions'] += 1
            else:
                daily_summary['failed_executions'] += 1
            
            daily_summary['total_tests_run'] += execution_summary['total_tests']
            daily_summary['total_tests_passed'] += execution_summary['passed_tests']
            
            # Update averages
            total_execs = daily_summary['total_executions']
            daily_summary['average_execution_time'] = (
                (daily_summary['average_execution_time'] * (total_execs - 1) + 
                 execution_summary['total_execution_time']) / total_execs
            )
            daily_summary['average_health_score'] = (
                (daily_summary['average_health_score'] * (total_execs - 1) + 
                 execution_summary['system_health_score']) / total_execs
            )
            
            # Store updated summary
            await self.redis_client.set(summary_key, daily_summary, ex=90 * 24 * 3600)
        
        except Exception as e:
            logger.error(f"Failed to update daily summary: {e}")
    
    async def get_test_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get test execution history."""
        try:
            history = []
            end_date = datetime.now().date()
            
            for i in range(days):
                date = end_date - timedelta(days=i)
                history_key = f"test_history:{date.strftime('%Y-%m-%d')}"
                
                day_executions = await self.redis_client.lrange(history_key, 0, -1)
                for execution in day_executions:
                    if isinstance(execution, dict):
                        history.append(execution)
            
            # Sort by timestamp descending
            history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return history
        
        except Exception as e:
            logger.error(f"Failed to get test history: {e}")
            return []
    
    async def get_test_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get test execution trends."""
        try:
            trends = {
                'success_rate_trend': [],
                'execution_time_trend': [],
                'health_score_trend': [],
                'test_count_trend': []
            }
            
            end_date = datetime.now().date()
            
            for i in range(days):
                date = end_date - timedelta(days=i)
                summary_key = f"test_summary:{date.strftime('%Y-%m-%d')}"
                
                daily_summary = await self.redis_client.get(summary_key)
                if daily_summary:
                    trends['success_rate_trend'].append({
                        'date': date.isoformat(),
                        'value': daily_summary['successful_executions'] / daily_summary['total_executions']
                        if daily_summary['total_executions'] > 0 else 0
                    })
                    trends['execution_time_trend'].append({
                        'date': date.isoformat(),
                        'value': daily_summary['average_execution_time']
                    })
                    trends['health_score_trend'].append({
                        'date': date.isoformat(),
                        'value': daily_summary['average_health_score']
                    })
                    trends['test_count_trend'].append({
                        'date': date.isoformat(),
                        'value': daily_summary['total_tests_run']
                    })
            
            # Reverse to get chronological order
            for trend_name in trends:
                trends[trend_name].reverse()
            
            return trends
        
        except Exception as e:
            logger.error(f"Failed to get test trends: {e}")
            return {}

class TestReportingService:
    """Main service for test reporting and notifications."""
    
    def __init__(self):
        self.report_generator = TestReportGenerator()
        self.notification_service = TestNotificationService()
        self.history_tracker = TestHistoryTracker()
    
    async def process_test_report(self, test_report: ComprehensiveTestReport) -> Dict[str, str]:
        """Process test report - generate reports, send notifications, store history."""
        results = {}
        
        try:
            # Generate and save reports
            if self.report_generator.execution_config.generate_html_report:
                html_path = self.report_generator.save_report(test_report, "html")
                results['html_report'] = html_path
            
            # Always generate JSON for API access
            json_path = self.report_generator.save_report(test_report, "json")
            results['json_report'] = json_path
            
            # Send notifications
            await self.notification_service.send_notifications(test_report)
            results['notifications_sent'] = True
            
            # Store in history
            await self.history_tracker.store_test_execution(test_report)
            results['stored_in_history'] = True
            
            logger.info("Test report processing completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to process test report: {e}")
            results['error'] = str(e)
        
        return results
    
    async def get_test_dashboard_data(self, days: int = 7) -> Dict[str, Any]:
        """Get data for test dashboard."""
        try:
            # Get recent history
            history = await self.history_tracker.get_test_history(days)
            
            # Get trends
            trends = await self.history_tracker.get_test_trends(days)
            
            # Calculate summary statistics
            if history:
                total_executions = len(history)
                successful_executions = sum(1 for h in history if h.get('overall_status') == 'passed')
                avg_success_rate = successful_executions / total_executions if total_executions > 0 else 0
                avg_execution_time = sum(h.get('total_execution_time', 0) for h in history) / total_executions if total_executions > 0 else 0
                avg_health_score = sum(h.get('system_health_score', 0) for h in history) / total_executions if total_executions > 0 else 0
            else:
                total_executions = 0
                successful_executions = 0
                avg_success_rate = 0
                avg_execution_time = 0
                avg_health_score = 0
            
            return {
                'summary': {
                    'total_executions': total_executions,
                    'successful_executions': successful_executions,
                    'success_rate': avg_success_rate,
                    'average_execution_time': avg_execution_time,
                    'average_health_score': avg_health_score
                },
                'recent_history': history[:10],  # Last 10 executions
                'trends': trends,
                'generated_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {'error': str(e)}

# Global instances
test_reporting_service = TestReportingService()

def get_test_reporting_service() -> TestReportingService:
    """Get the global test reporting service instance."""
    return test_reporting_service