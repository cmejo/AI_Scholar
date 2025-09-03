#!/usr/bin/env python3
"""
Zotero Integration User Acceptance Testing Framework

This framework provides tools for conducting comprehensive user acceptance testing
of the Zotero integration features, including automated test scenarios,
performance validation, and accessibility testing.
"""

import os
import json
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path

import pytest
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestScenario:
    """Represents a user acceptance test scenario."""
    id: str
    name: str
    description: str
    category: str
    priority: str  # high, medium, low
    estimated_duration: int  # minutes
    prerequisites: List[str]
    steps: List[Dict[str, Any]]
    expected_outcomes: List[str]
    acceptance_criteria: List[str]

@dataclass
class TestResult:
    """Represents the result of a test scenario execution."""
    scenario_id: str
    status: str  # passed, failed, skipped
    start_time: datetime
    end_time: datetime
    duration: float
    errors: List[str]
    warnings: List[str]
    screenshots: List[str]
    performance_metrics: Dict[str, float]
    user_feedback: Optional[str] = None

class ZoteroUATFramework:
    """Main framework for Zotero integration user acceptance testing."""
    
    def __init__(self, config_path: str = "config/uat_config.json"):
        self.config = self._load_config(config_path)
        self.base_url = self.config.get('base_url', 'http://localhost:3000')
        self.api_url = self.config.get('api_url', 'http://localhost:8000')
        self.test_data_path = Path(self.config.get('test_data_path', 'tests/data'))
        self.results_path = Path(self.config.get('results_path', 'tests/results'))
        self.screenshots_path = self.results_path / 'screenshots'
        
        # Create directories
        self.results_path.mkdir(parents=True, exist_ok=True)
        self.screenshots_path.mkdir(parents=True, exist_ok=True)
        
        self.driver = None
        self.test_results: List[TestResult] = []
        
    def _load_config(self, config_path: str) -> Dict:
        """Load UAT configuration."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return {}
    
    def setup_driver(self, headless: bool = False):
        """Setup Selenium WebDriver."""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        
    def teardown_driver(self):
        """Cleanup WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def take_screenshot(self, name: str) -> str:
        """Take screenshot and return path."""
        if not self.driver:
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = self.screenshots_path / filename
        
        self.driver.save_screenshot(str(filepath))
        return str(filepath)
    
    def wait_for_element(self, by: By, value: str, timeout: int = 10):
        """Wait for element to be present and visible."""
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.visibility_of_element_located((by, value)))
    
    def measure_performance(self, action: Callable, *args, **kwargs) -> Dict[str, float]:
        """Measure performance metrics for an action."""
        start_time = time.time()
        
        # Execute action
        result = action(*args, **kwargs)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Get browser performance metrics if available
        metrics = {'duration': duration}
        
        if self.driver:
            try:
                # Get navigation timing
                nav_timing = self.driver.execute_script(
                    "return window.performance.timing"
                )
                if nav_timing:
                    load_time = nav_timing['loadEventEnd'] - nav_timing['navigationStart']
                    metrics['page_load_time'] = load_time / 1000.0  # Convert to seconds
                
                # Get memory usage if available
                memory = self.driver.execute_script(
                    "return window.performance.memory"
                )
                if memory:
                    metrics['memory_used'] = memory['usedJSHeapSize']
                    metrics['memory_total'] = memory['totalJSHeapSize']
            except Exception as e:
                logger.warning(f"Could not collect performance metrics: {e}")
        
        return metrics
    
    def check_accessibility(self) -> List[str]:
        """Check basic accessibility compliance."""
        issues = []
        
        if not self.driver:
            return issues
        
        try:
            # Check for alt text on images
            images = self.driver.find_elements(By.TAG_NAME, "img")
            for img in images:
                if not img.get_attribute("alt"):
                    issues.append(f"Image missing alt text: {img.get_attribute('src')}")
            
            # Check for form labels
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            for input_elem in inputs:
                input_type = input_elem.get_attribute("type")
                if input_type not in ["hidden", "submit", "button"]:
                    label_id = input_elem.get_attribute("id")
                    if label_id:
                        labels = self.driver.find_elements(By.CSS_SELECTOR, f"label[for='{label_id}']")
                        if not labels:
                            issues.append(f"Input missing label: {input_elem.get_attribute('name')}")
            
            # Check for heading hierarchy
            headings = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
            prev_level = 0
            for heading in headings:
                level = int(heading.tag_name[1])
                if level > prev_level + 1:
                    issues.append(f"Heading hierarchy skip: {heading.text}")
                prev_level = level
            
        except Exception as e:
            logger.warning(f"Accessibility check failed: {e}")
        
        return issues
    
    def load_test_scenarios(self) -> List[TestScenario]:
        """Load test scenarios from configuration."""
        scenarios = []
        
        # Connection and Authentication Scenarios
        scenarios.extend([
            TestScenario(
                id="zotero_001",
                name="Connect Zotero Account",
                description="User successfully connects their Zotero account via OAuth",
                category="authentication",
                priority="high",
                estimated_duration=5,
                prerequisites=["Valid Zotero account", "AI Scholar account"],
                steps=[
                    {"action": "navigate", "target": "/settings/integrations"},
                    {"action": "click", "target": "[data-testid='connect-zotero']"},
                    {"action": "wait", "target": "oauth_redirect"},
                    {"action": "authenticate", "target": "zotero_oauth"},
                    {"action": "verify", "target": "connection_success"}
                ],
                expected_outcomes=[
                    "OAuth flow completes successfully",
                    "Connection status shows as connected",
                    "User can access Zotero features"
                ],
                acceptance_criteria=[
                    "Connection completes within 30 seconds",
                    "No error messages displayed",
                    "Connection persists after page refresh"
                ]
            ),
            
            TestScenario(
                id="zotero_002",
                name="Import Personal Library",
                description="User imports their personal Zotero library",
                category="import",
                priority="high",
                estimated_duration=10,
                prerequisites=["Connected Zotero account", "Library with references"],
                steps=[
                    {"action": "navigate", "target": "/zotero/import"},
                    {"action": "select", "target": "personal_library"},
                    {"action": "click", "target": "start_import"},
                    {"action": "monitor", "target": "import_progress"},
                    {"action": "verify", "target": "import_completion"}
                ],
                expected_outcomes=[
                    "Import process starts successfully",
                    "Progress is displayed to user",
                    "All references are imported correctly"
                ],
                acceptance_criteria=[
                    "Import completes without errors",
                    "Reference count matches Zotero library",
                    "Collections are preserved"
                ]
            )
        ])
        
        # Search and Browse Scenarios
        scenarios.extend([
            TestScenario(
                id="zotero_003",
                name="Search References",
                description="User searches for references using various criteria",
                category="search",
                priority="high",
                estimated_duration=8,
                prerequisites=["Imported library"],
                steps=[
                    {"action": "navigate", "target": "/zotero/library"},
                    {"action": "type", "target": "search_input", "value": "machine learning"},
                    {"action": "wait", "target": "search_results"},
                    {"action": "verify", "target": "results_relevance"},
                    {"action": "filter", "target": "author_filter"},
                    {"action": "verify", "target": "filtered_results"}
                ],
                expected_outcomes=[
                    "Search returns relevant results",
                    "Filters work correctly",
                    "Results are properly formatted"
                ],
                acceptance_criteria=[
                    "Search completes within 3 seconds",
                    "Results are ranked by relevance",
                    "Filters reduce result set appropriately"
                ]
            )
        ])
        
        # Citation Generation Scenarios
        scenarios.extend([
            TestScenario(
                id="zotero_004",
                name="Generate Citations",
                description="User generates citations in different formats",
                category="citations",
                priority="high",
                estimated_duration=6,
                prerequisites=["Imported references"],
                steps=[
                    {"action": "navigate", "target": "/zotero/library"},
                    {"action": "select", "target": "reference_item"},
                    {"action": "click", "target": "cite_button"},
                    {"action": "select", "target": "apa_style"},
                    {"action": "verify", "target": "citation_format"},
                    {"action": "copy", "target": "citation_text"}
                ],
                expected_outcomes=[
                    "Citation is properly formatted",
                    "Multiple styles are available",
                    "Citation can be copied to clipboard"
                ],
                acceptance_criteria=[
                    "Citation follows style guidelines",
                    "All required fields are included",
                    "Copy function works correctly"
                ]
            )
        ])
        
        # AI Features Scenarios
        scenarios.extend([
            TestScenario(
                id="zotero_005",
                name="AI Research Insights",
                description="User views AI-generated research insights",
                category="ai_features",
                priority="medium",
                estimated_duration=12,
                prerequisites=["Imported library with abstracts"],
                steps=[
                    {"action": "navigate", "target": "/zotero/insights"},
                    {"action": "wait", "target": "ai_analysis_complete"},
                    {"action": "verify", "target": "topic_clusters"},
                    {"action": "click", "target": "similarity_network"},
                    {"action": "verify", "target": "network_visualization"}
                ],
                expected_outcomes=[
                    "AI analysis completes successfully",
                    "Insights are meaningful and accurate",
                    "Visualizations are interactive"
                ],
                acceptance_criteria=[
                    "Analysis completes within 2 minutes",
                    "Topics are relevant to library content",
                    "Similarity connections make sense"
                ]
            )
        ])
        
        return scenarios
    
    async def execute_scenario(self, scenario: TestScenario) -> TestResult:
        """Execute a single test scenario."""
        logger.info(f"Executing scenario: {scenario.name}")
        
        start_time = datetime.now()
        errors = []
        warnings = []
        screenshots = []
        performance_metrics = {}
        
        try:
            # Take initial screenshot
            screenshots.append(self.take_screenshot(f"{scenario.id}_start"))
            
            # Execute each step
            for i, step in enumerate(scenario.steps):
                step_name = f"{scenario.id}_step_{i+1}"
                logger.info(f"Executing step {i+1}: {step['action']}")
                
                try:
                    # Measure performance for each step
                    metrics = self.measure_performance(
                        self._execute_step, step
                    )
                    performance_metrics[step_name] = metrics
                    
                    # Take screenshot after important steps
                    if step['action'] in ['click', 'verify', 'authenticate']:
                        screenshots.append(self.take_screenshot(step_name))
                    
                except Exception as e:
                    error_msg = f"Step {i+1} failed: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    screenshots.append(self.take_screenshot(f"{step_name}_error"))
                    break
            
            # Check accessibility
            accessibility_issues = self.check_accessibility()
            if accessibility_issues:
                warnings.extend([f"Accessibility: {issue}" for issue in accessibility_issues])
            
            # Determine status
            status = "failed" if errors else "passed"
            
        except Exception as e:
            errors.append(f"Scenario execution failed: {str(e)}")
            status = "failed"
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return TestResult(
            scenario_id=scenario.id,
            status=status,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            errors=errors,
            warnings=warnings,
            screenshots=screenshots,
            performance_metrics=performance_metrics
        )
    
    def _execute_step(self, step: Dict[str, Any]):
        """Execute a single test step."""
        action = step['action']
        target = step.get('target', '')
        value = step.get('value', '')
        
        if action == 'navigate':
            self.driver.get(f"{self.base_url}{target}")
        
        elif action == 'click':
            element = self.wait_for_element(By.CSS_SELECTOR, target)
            element.click()
        
        elif action == 'type':
            element = self.wait_for_element(By.CSS_SELECTOR, target)
            element.clear()
            element.send_keys(value)
        
        elif action == 'wait':
            if target == 'oauth_redirect':
                # Wait for OAuth redirect
                WebDriverWait(self.driver, 30).until(
                    lambda d: 'zotero.org' in d.current_url or 'callback' in d.current_url
                )
            else:
                time.sleep(2)  # Generic wait
        
        elif action == 'verify':
            if target == 'connection_success':
                self.wait_for_element(By.CSS_SELECTOR, "[data-testid='zotero-connected']")
            elif target == 'search_results':
                self.wait_for_element(By.CSS_SELECTOR, "[data-testid='search-results']")
            # Add more verification logic as needed
        
        elif action == 'select':
            element = self.wait_for_element(By.CSS_SELECTOR, target)
            element.click()
        
        elif action == 'monitor':
            if target == 'import_progress':
                # Monitor import progress
                progress_bar = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='import-progress']")
                # Wait for completion (simplified)
                WebDriverWait(self.driver, 300).until(
                    lambda d: 'completed' in progress_bar.get_attribute('class')
                )
    
    async def run_test_suite(self, categories: Optional[List[str]] = None, 
                           priorities: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run the complete test suite."""
        logger.info("Starting Zotero UAT test suite")
        
        scenarios = self.load_test_scenarios()
        
        # Filter scenarios
        if categories:
            scenarios = [s for s in scenarios if s.category in categories]
        if priorities:
            scenarios = [s for s in scenarios if s.priority in priorities]
        
        # Setup
        self.setup_driver(headless=self.config.get('headless', False))
        
        try:
            # Execute scenarios
            for scenario in scenarios:
                result = await self.execute_scenario(scenario)
                self.test_results.append(result)
        
        finally:
            self.teardown_driver()
        
        # Generate report
        report = self.generate_report()
        
        # Save results
        self.save_results()
        
        return report
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate test execution report."""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == 'passed'])
        failed_tests = len([r for r in self.test_results if r.status == 'failed'])
        
        total_duration = sum(r.duration for r in self.test_results)
        avg_duration = total_duration / total_tests if total_tests > 0 else 0
        
        # Performance summary
        all_metrics = {}
        for result in self.test_results:
            for step, metrics in result.performance_metrics.items():
                for metric, value in metrics.items():
                    if metric not in all_metrics:
                        all_metrics[metric] = []
                    all_metrics[metric].append(value)
        
        performance_summary = {}
        for metric, values in all_metrics.items():
            performance_summary[metric] = {
                'avg': sum(values) / len(values),
                'min': min(values),
                'max': max(values)
            }
        
        # Collect all errors and warnings
        all_errors = []
        all_warnings = []
        for result in self.test_results:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'total_duration': total_duration,
                'average_duration': avg_duration
            },
            'performance': performance_summary,
            'errors': all_errors,
            'warnings': all_warnings,
            'detailed_results': [asdict(r) for r in self.test_results],
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def save_results(self):
        """Save test results to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        results_file = self.results_path / f"uat_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump([asdict(r) for r in self.test_results], f, indent=2, default=str)
        
        # Save summary report
        report = self.generate_report()
        report_file = self.results_path / f"uat_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Generate HTML report
        self.generate_html_report(report, timestamp)
        
        logger.info(f"Results saved to {self.results_path}")
    
    def generate_html_report(self, report: Dict[str, Any], timestamp: str):
        """Generate HTML report."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Zotero Integration UAT Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                .warning {{ color: orange; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .error-list {{ background: #ffe6e6; padding: 10px; border-radius: 5px; }}
                .warning-list {{ background: #fff3cd; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>Zotero Integration User Acceptance Test Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="summary">
                <h2>Summary</h2>
                <p>Total Tests: {report['summary']['total_tests']}</p>
                <p class="passed">Passed: {report['summary']['passed']}</p>
                <p class="failed">Failed: {report['summary']['failed']}</p>
                <p>Success Rate: {report['summary']['success_rate']:.1f}%</p>
                <p>Total Duration: {report['summary']['total_duration']:.1f} seconds</p>
            </div>
            
            <h2>Test Results</h2>
            <table>
                <tr>
                    <th>Scenario ID</th>
                    <th>Status</th>
                    <th>Duration (s)</th>
                    <th>Errors</th>
                    <th>Warnings</th>
                </tr>
        """
        
        for result in report['detailed_results']:
            status_class = 'passed' if result['status'] == 'passed' else 'failed'
            html_content += f"""
                <tr>
                    <td>{result['scenario_id']}</td>
                    <td class="{status_class}">{result['status']}</td>
                    <td>{result['duration']:.1f}</td>
                    <td>{len(result['errors'])}</td>
                    <td>{len(result['warnings'])}</td>
                </tr>
            """
        
        html_content += """
            </table>
        """
        
        if report['errors']:
            html_content += """
            <div class="error-list">
                <h2>Errors</h2>
                <ul>
            """
            for error in report['errors']:
                html_content += f"<li>{error}</li>"
            html_content += "</ul></div>"
        
        if report['warnings']:
            html_content += """
            <div class="warning-list">
                <h2>Warnings</h2>
                <ul>
            """
            for warning in report['warnings']:
                html_content += f"<li>{warning}</li>"
            html_content += "</ul></div>"
        
        html_content += """
        </body>
        </html>
        """
        
        html_file = self.results_path / f"uat_report_{timestamp}.html"
        with open(html_file, 'w') as f:
            f.write(html_content)

# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Zotero Integration UAT Framework')
    parser.add_argument('--config', default='config/uat_config.json',
                       help='Configuration file path')
    parser.add_argument('--categories', nargs='+',
                       help='Test categories to run')
    parser.add_argument('--priorities', nargs='+', 
                       choices=['high', 'medium', 'low'],
                       help='Test priorities to run')
    parser.add_argument('--headless', action='store_true',
                       help='Run tests in headless mode')
    
    args = parser.parse_args()
    
    # Create framework instance
    framework = ZoteroUATFramework(args.config)
    if args.headless:
        framework.config['headless'] = True
    
    # Run tests
    async def main():
        report = await framework.run_test_suite(
            categories=args.categories,
            priorities=args.priorities
        )
        
        print(f"\nTest Suite Completed!")
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        
        if report['summary']['failed'] > 0:
            print("\nFailed tests require attention before release.")
            exit(1)
        else:
            print("\nAll tests passed! Ready for release.")
    
    asyncio.run(main())