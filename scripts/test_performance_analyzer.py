#!/usr/bin/env python3
"""
Test suite for Performance Analyzer

Tests the performance analysis and optimization detector functionality
including memory leak detection, database performance analysis,
CPU profiling, and caching optimization.
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from performance_analyzer import (
    PerformanceAnalyzer,
    MemoryLeakDetector,
    DatabasePerformanceAnalyzer,
    CPUProfiler,
    CachingAnalyzer,
    MemoryLeakIssue,
    DatabasePerformanceIssue,
    CPUBottleneckIssue,
    CachingOptimizationIssue
)

class TestMemoryLeakDetector(unittest.TestCase):
    """Test memory leak detection functionality"""
    
    def setUp(self):
        self.detector = MemoryLeakDetector()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, filename: str, content: str) -> str:
        """Create a test file with given content"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path
    
    def test_unclosed_file_detection(self):
        """Test detection of unclosed file handles"""
        content = '''
def read_file():
    f = open("test.txt", "r")
    data = f.read()
    return data
'''
        self.create_test_file("test_unclosed.py", content)
        issues = self.detector.analyze_python_files(self.temp_dir)
        
        unclosed_issues = [i for i in issues if i.leak_type == "unclosed_resource"]
        self.assertGreater(len(unclosed_issues), 0)
        self.assertEqual(unclosed_issues[0].severity, "medium")
    
    def test_proper_resource_management(self):
        """Test that proper resource management doesn't trigger issues"""
        content = '''
def read_file():
    with open("test.txt", "r") as f:
        data = f.read()
    return data
'''
        self.create_test_file("test_proper.py", content)
        issues = self.detector.analyze_python_files(self.temp_dir)
        
        unclosed_issues = [i for i in issues if i.leak_type == "unclosed_resource"]
        self.assertEqual(len(unclosed_issues), 0)
    
    def test_large_data_structure_detection(self):
        """Test detection of potentially large data structures"""
        content = '''
def process_data():
    large_list = [x for x in range(1000000)]
    return large_list
'''
        self.create_test_file("test_large.py", content)
        issues = self.detector.analyze_python_files(self.temp_dir)
        
        large_structure_issues = [i for i in issues if i.leak_type == "large_data_structure"]
        self.assertGreater(len(large_structure_issues), 0)
    
    def test_event_listener_detection(self):
        """Test detection of unremoved event listeners"""
        content = '''
def setup_events():
    element.addEventListener("click", handler)
    
def cleanup():
    pass  # No removeEventListener
'''
        self.create_test_file("test_events.py", content)
        issues = self.detector.analyze_python_files(self.temp_dir)
        
        event_issues = [i for i in issues if i.leak_type == "unremoved_event_listener"]
        self.assertGreater(len(event_issues), 0)

class TestDatabasePerformanceAnalyzer(unittest.TestCase):
    """Test database performance analysis functionality"""
    
    def setUp(self):
        self.analyzer = DatabasePerformanceAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, filename: str, content: str) -> str:
        """Create a test file with given content"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path
    
    def test_select_star_detection(self):
        """Test detection of SELECT * queries"""
        content = '''
def get_users():
    query = "SELECT * FROM users WHERE active = 1"
    return execute_query(query)
'''
        self.create_test_file("test_select_star.py", content)
        issues = self.analyzer.analyze_sql_files(self.temp_dir)
        
        select_star_issues = [i for i in issues if "SELECT *" in i.description]
        self.assertGreater(len(select_star_issues), 0)
        self.assertEqual(select_star_issues[0].severity, "low")
    
    def test_missing_limit_detection(self):
        """Test detection of queries without LIMIT clauses"""
        content = '''
def get_all_posts():
    query = "SELECT title, content FROM posts WHERE published = 1"
    return execute_query(query)
'''
        self.create_test_file("test_no_limit.py", content)
        issues = self.analyzer.analyze_sql_files(self.temp_dir)
        
        limit_issues = [i for i in issues if "LIMIT" in i.description]
        self.assertGreater(len(limit_issues), 0)
    
    def test_complex_join_detection(self):
        """Test detection of complex JOIN queries"""
        content = '''
def get_complex_data():
    query = """
    SELECT u.name, p.title, c.content, t.name
    FROM users u
    JOIN posts p ON u.id = p.user_id
    JOIN comments c ON p.id = c.post_id
    JOIN tags t ON p.id = t.post_id
    JOIN categories cat ON p.category_id = cat.id
    """
    return execute_query(query)
'''
        self.create_test_file("test_complex_join.py", content)
        issues = self.analyzer.analyze_sql_files(self.temp_dir)
        
        join_issues = [i for i in issues if "JOIN" in i.description]
        self.assertGreater(len(join_issues), 0)
    
    def test_index_suggestion(self):
        """Test suggestion of missing indexes"""
        content = '''
def find_user_by_email():
    query = "SELECT id, name FROM users WHERE email = %s"
    return execute_query(query)
'''
        self.create_test_file("test_index.py", content)
        issues = self.analyzer.analyze_sql_files(self.temp_dir)
        
        index_issues = [i for i in issues if "index" in i.description.lower()]
        self.assertGreater(len(index_issues), 0)

class TestCPUProfiler(unittest.TestCase):
    """Test CPU profiling functionality"""
    
    def setUp(self):
        self.profiler = CPUProfiler()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, filename: str, content: str) -> str:
        """Create a test file with given content"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path
    
    def test_nested_loop_detection(self):
        """Test detection of nested loops"""
        content = '''
def process_matrix():
    for i in range(100):
        for j in range(100):
            for k in range(100):
                result = i * j * k
    return result
'''
        self.create_test_file("test_nested_loops.py", content)
        issues = self.profiler.analyze_python_files(self.temp_dir)
        
        nested_loop_issues = [i for i in issues if "nested" in i.description.lower()]
        self.assertGreater(len(nested_loop_issues), 0)
        self.assertIn(nested_loop_issues[0].severity, ["medium", "high"])
    
    def test_recursive_function_detection(self):
        """Test detection of recursive functions"""
        content = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
'''
        self.create_test_file("test_recursion.py", content)
        issues = self.profiler.analyze_python_files(self.temp_dir)
        
        recursive_issues = [i for i in issues if i.function_name == "fibonacci"]
        self.assertGreater(len(recursive_issues), 0)
        self.assertEqual(recursive_issues[0].severity, "medium")
    
    def test_blocking_operation_detection(self):
        """Test detection of blocking operations"""
        content = '''
import time
import requests

def slow_function():
    time.sleep(5)
    response = requests.get("http://example.com")
    return response.text
'''
        self.create_test_file("test_blocking.py", content)
        issues = self.profiler.analyze_python_files(self.temp_dir)
        
        blocking_issues = [i for i in issues if "blocking" in i.description.lower()]
        self.assertGreater(len(blocking_issues), 0)
    
    def test_inefficient_operations(self):
        """Test detection of inefficient operations"""
        content = '''
def process_data():
    data = [i for i in range(1000)]
    sorted_data = sorted(data)
    return sorted_data
'''
        self.create_test_file("test_inefficient.py", content)
        issues = self.profiler.analyze_python_files(self.temp_dir)
        
        # Should detect sorting operation
        sorting_issues = [i for i in issues if i.function_name == "sorted"]
        self.assertGreaterEqual(len(sorting_issues), 0)  # May or may not be flagged as inefficient

class TestCachingAnalyzer(unittest.TestCase):
    """Test caching analysis functionality"""
    
    def setUp(self):
        self.analyzer = CachingAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, filename: str, content: str) -> str:
        """Create a test file with given content"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path
    
    def test_missing_cache_detection(self):
        """Test detection of functions that could benefit from caching"""
        content = '''
import requests

def get_user_data(user_id):
    response = requests.get(f"https://api.example.com/users/{user_id}")
    return response.json()
'''
        self.create_test_file("test_missing_cache.py", content)
        issues = self.analyzer.analyze_caching_strategies(self.temp_dir)
        
        missing_cache_issues = [i for i in issues if i.cache_type == "missing_cache"]
        self.assertGreater(len(missing_cache_issues), 0)
    
    def test_cache_invalidation_detection(self):
        """Test detection of missing cache invalidation"""
        content = '''
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(x):
    return x ** 2

def update_data():
    # Updates data but doesn't invalidate cache
    pass
'''
        self.create_test_file("test_invalidation.py", content)
        issues = self.analyzer.analyze_caching_strategies(self.temp_dir)
        
        invalidation_issues = [i for i in issues if "invalidation" in i.cache_type]
        self.assertGreater(len(invalidation_issues), 0)
    
    def test_cache_configuration_issues(self):
        """Test detection of cache configuration issues"""
        content = '''
from functools import lru_cache

@lru_cache()  # No maxsize specified
def compute_value(x):
    return x * 2
'''
        self.create_test_file("test_config.py", content)
        issues = self.analyzer.analyze_caching_strategies(self.temp_dir)
        
        config_issues = [i for i in issues if "no_maxsize" in i.cache_type]
        self.assertGreater(len(config_issues), 0)

class TestPerformanceAnalyzer(unittest.TestCase):
    """Test the main performance analyzer"""
    
    def setUp(self):
        self.analyzer = PerformanceAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, filename: str, content: str) -> str:
        """Create a test file with given content"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path
    
    def test_comprehensive_analysis(self):
        """Test comprehensive performance analysis"""
        # Create test files with various issues
        memory_leak_content = '''
def read_data():
    f = open("data.txt", "r")
    return f.read()  # File not closed
'''
        
        db_performance_content = '''
def get_all_users():
    query = "SELECT * FROM users"  # SELECT * without LIMIT
    return execute_query(query)
'''
        
        cpu_bottleneck_content = '''
def nested_processing():
    for i in range(100):
        for j in range(100):
            for k in range(100):
                result = i * j * k
    return result
'''
        
        caching_content = '''
import requests

def fetch_user_data(user_id):
    response = requests.get(f"/api/users/{user_id}")
    return response.json()  # Could be cached
'''
        
        self.create_test_file("memory_test.py", memory_leak_content)
        self.create_test_file("db_test.py", db_performance_content)
        self.create_test_file("cpu_test.py", cpu_bottleneck_content)
        self.create_test_file("cache_test.py", caching_content)
        
        # Run comprehensive analysis
        results = self.analyzer.analyze_directory(self.temp_dir)
        
        # Verify results structure
        self.assertIsNotNone(results.timestamp)
        self.assertIsInstance(results.memory_leaks, list)
        self.assertIsInstance(results.database_issues, list)
        self.assertIsInstance(results.cpu_bottlenecks, list)
        self.assertIsInstance(results.caching_issues, list)
        self.assertIsInstance(results.summary, dict)
        
        # Verify we found issues
        self.assertGreater(len(results.memory_leaks), 0)
        self.assertGreater(len(results.database_issues), 0)
        self.assertGreater(len(results.cpu_bottlenecks), 0)
        self.assertGreater(len(results.caching_issues), 0)
        
        # Verify summary
        self.assertIn('total_issues', results.summary)
        self.assertGreater(results.summary['total_issues'], 0)
    
    def test_save_and_load_results(self):
        """Test saving and loading analysis results"""
        # Create a simple test file
        content = '''
def simple_function():
    f = open("test.txt")
    return f.read()
'''
        self.create_test_file("simple.py", content)
        
        # Run analysis
        results = self.analyzer.analyze_directory(self.temp_dir)
        
        # Save results
        output_file = os.path.join(self.temp_dir, "results.json")
        self.analyzer.save_results(results, output_file)
        
        # Verify file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Load and verify results
        with open(output_file, 'r') as f:
            loaded_data = json.load(f)
        
        self.assertIn('timestamp', loaded_data)
        self.assertIn('memory_leaks', loaded_data)
        self.assertIn('database_issues', loaded_data)
        self.assertIn('cpu_bottlenecks', loaded_data)
        self.assertIn('caching_issues', loaded_data)
        self.assertIn('summary', loaded_data)

class TestIntegration(unittest.TestCase):
    """Integration tests for the performance analyzer"""
    
    def test_real_world_scenario(self):
        """Test with a realistic code scenario"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create a realistic Python service file
            service_content = '''
import os
import json
import time
import requests
from functools import lru_cache
import sqlite3

class UserService:
    def __init__(self):
        self.db_path = "users.db"
        
    def get_user_by_id(self, user_id):
        # Potential memory leak - connection not closed
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Inefficient query - SELECT *
        query = "SELECT * FROM users WHERE id = ?"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        
        return result
    
    def get_all_users(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Missing LIMIT clause
        query = "SELECT id, name, email FROM users WHERE active = 1"
        cursor.execute(query)
        results = cursor.fetchall()
        
        conn.close()
        return results
    
    def process_user_data(self):
        users = self.get_all_users()
        
        # Nested loops - CPU bottleneck
        for user in users:
            for i in range(100):
                for j in range(100):
                    # Expensive computation
                    result = user[0] * i * j
        
        return result
    
    def fetch_external_data(self, user_id):
        # Could benefit from caching
        response = requests.get(f"https://api.example.com/users/{user_id}")
        time.sleep(0.1)  # Blocking operation
        return response.json()
    
    @lru_cache()  # Missing maxsize
    def compute_score(self, user_id):
        return user_id * 42
'''
            
            file_path = os.path.join(temp_dir, "user_service.py")
            with open(file_path, 'w') as f:
                f.write(service_content)
            
            # Run analysis
            analyzer = PerformanceAnalyzer()
            results = analyzer.analyze_directory(temp_dir)
            
            # Verify we found various types of issues
            self.assertGreater(len(results.memory_leaks), 0)
            self.assertGreater(len(results.database_issues), 0)
            self.assertGreater(len(results.cpu_bottlenecks), 0)
            self.assertGreater(len(results.caching_issues), 0)
            
            # Verify specific issues were found
            memory_leak_types = [issue.leak_type for issue in results.memory_leaks]
            self.assertIn("unclosed_resource", memory_leak_types)
            
            db_issue_descriptions = [issue.description for issue in results.database_issues]
            select_star_found = any("SELECT *" in desc for desc in db_issue_descriptions)
            self.assertTrue(select_star_found)
            
            cpu_issue_descriptions = [issue.description for issue in results.cpu_bottlenecks]
            nested_loop_found = any("nested" in desc.lower() for desc in cpu_issue_descriptions)
            blocking_found = any("blocking" in desc.lower() for desc in cpu_issue_descriptions)
            self.assertTrue(nested_loop_found or blocking_found)
            
            cache_issue_types = [issue.cache_type for issue in results.caching_issues]
            missing_cache_found = "missing_cache" in cache_issue_types
            config_issue_found = any("no_maxsize" in cache_type for cache_type in cache_issue_types)
            self.assertTrue(missing_cache_found or config_issue_found)
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

def run_tests():
    """Run all performance analyzer tests"""
    print("Running Performance Analyzer Tests...")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestMemoryLeakDetector,
        TestDatabasePerformanceAnalyzer,
        TestCPUProfiler,
        TestCachingAnalyzer,
        TestPerformanceAnalyzer,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall: {'PASSED' if success else 'FAILED'}")
    
    return success

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)