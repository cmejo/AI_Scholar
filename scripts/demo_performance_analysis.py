#!/usr/bin/env python3
"""
Performance Analysis Demo

This script demonstrates the performance analysis capabilities by creating
sample code with various performance issues and running the analyzer on them.

Requirements: 5.1, 5.2, 5.3, 5.4
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from performance_analyzer import PerformanceAnalyzer

def create_demo_files(demo_dir: str) -> None:
    """Create demo files with various performance issues"""
    
    # Memory leak examples
    memory_leak_content = '''
import sqlite3
import requests
import json

class DataProcessor:
    def __init__(self):
        self.connections = []
        self.file_handles = []
    
    def process_file(self, filename):
        # Memory leak: file not closed
        f = open(filename, 'r')
        data = f.read()
        self.file_handles.append(f)  # Keeping reference
        return data
    
    def connect_database(self):
        # Memory leak: connection not closed
        conn = sqlite3.connect('database.db')
        self.connections.append(conn)
        return conn
    
    def large_data_processing(self):
        # Potential memory issue: large data structure
        large_list = [x for x in range(1000000)]
        large_dict = {i: [j for j in range(100)] for i in range(10000)}
        return large_list, large_dict
    
    def event_handler_setup(self):
        # Event listener without removal
        element.addEventListener("click", self.handle_click)
        element.addEventListener("scroll", self.handle_scroll)
        # No corresponding removeEventListener calls
    
    def handle_click(self, event):
        pass
    
    def handle_scroll(self, event):
        pass
    
    def circular_reference_example(self):
        # Potential circular reference
        self.parent = self
        self.child = self
        self.reference = self
'''
    
    # Database performance issues
    database_issues_content = '''
import sqlite3
import psycopg2

class UserRepository:
    def __init__(self):
        self.conn = sqlite3.connect('users.db')
    
    def get_all_users(self):
        # Issue: SELECT * without LIMIT
        query = "SELECT * FROM users WHERE active = 1"
        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()
    
    def find_user_by_email(self, email):
        # Issue: Missing index suggestion
        query = "SELECT id, name, email FROM users WHERE email = ?"
        cursor = self.conn.cursor()
        cursor.execute(query, (email,))
        return cursor.fetchone()
    
    def get_user_posts(self, user_id):
        # Issue: Complex JOIN query
        query = """
        SELECT u.name, p.title, c.content, t.name, cat.name, l.count
        FROM users u
        JOIN posts p ON u.id = p.user_id
        JOIN comments c ON p.id = c.post_id
        JOIN tags t ON p.id = t.post_id
        JOIN categories cat ON p.category_id = cat.id
        JOIN likes l ON p.id = l.post_id
        WHERE u.id = ?
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (user_id,))
        return cursor.fetchall()
    
    def search_posts(self, keyword):
        # Issue: No LIMIT clause for search
        query = "SELECT title, content FROM posts WHERE title LIKE ? OR content LIKE ?"
        cursor = self.conn.cursor()
        cursor.execute(query, (f'%{keyword}%', f'%{keyword}%'))
        return cursor.fetchall()
    
    def get_user_analytics(self):
        # Potential N+1 query pattern
        users = self.get_all_users()
        for user in users:
            # This creates N+1 queries
            posts_query = "SELECT COUNT(*) FROM posts WHERE user_id = ?"
            cursor = self.conn.cursor()
            cursor.execute(posts_query, (user[0],))
            user_posts = cursor.fetchone()
'''
    
    # CPU bottleneck examples
    cpu_bottleneck_content = '''
import time
import requests
import json

class DataAnalyzer:
    def __init__(self):
        self.data = []
    
    def nested_loop_processing(self, data):
        # CPU bottleneck: triple nested loops
        results = []
        for i in range(len(data)):
            for j in range(len(data)):
                for k in range(len(data)):
                    if i != j and j != k and i != k:
                        result = data[i] * data[j] * data[k]
                        results.append(result)
        return results
    
    def recursive_fibonacci(self, n):
        # CPU bottleneck: inefficient recursion
        if n <= 1:
            return n
        return self.recursive_fibonacci(n-1) + self.recursive_fibonacci(n-2)
    
    def inefficient_sorting(self, data):
        # CPU bottleneck: inefficient operations
        sorted_data = sorted(data)
        reversed_data = sorted_data[::-1]
        sorted_again = sorted(reversed_data)
        return sorted_again
    
    def blocking_operations(self):
        # Blocking operations
        time.sleep(2)  # Blocking sleep
        response = requests.get("https://httpbin.org/delay/3")  # Blocking HTTP
        data = response.json()
        
        # More blocking operations
        user_input = input("Enter something: ")  # Blocking input
        return data, user_input
    
    def nested_comprehensions(self, matrix):
        # Potentially inefficient nested comprehensions
        result = [[sum([x * y for y in row]) for x in col] for col in matrix for row in matrix]
        return result
    
    def quadratic_algorithm(self, items):
        # O(n²) algorithm that could be optimized
        duplicates = []
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if items[i] == items[j]:
                    duplicates.append(items[i])
        return duplicates
'''
    
    # Caching optimization examples
    caching_issues_content = '''
import requests
import json
import sqlite3
from functools import lru_cache
import redis

class APIService:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    def fetch_user_profile(self, user_id):
        # Missing caching for expensive API call
        response = requests.get(f"https://api.example.com/users/{user_id}")
        return response.json()
    
    def get_weather_data(self, city):
        # Missing caching for external API
        response = requests.get(f"https://api.weather.com/v1/current?city={city}")
        return response.json()
    
    @lru_cache()  # Issue: no maxsize specified
    def compute_expensive_calculation(self, x, y):
        return x ** y + sum(range(x * y))
    
    @lru_cache(maxsize=None)  # Issue: unlimited cache size
    def another_calculation(self, data):
        return sum(data) * len(data)
    
    def database_query_without_cache(self, query):
        # Database query that could benefit from caching
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
        return result
    
    def cache_with_invalidation_issues(self, key, value):
        # Cache usage without proper invalidation
        self.redis_client.set(key, json.dumps(value))
        # No cache invalidation strategy implemented
    
    def inefficient_cache_pattern(self, cache_key):
        # Inefficient cache check pattern
        cached_value = self.redis_client.get(cache_key)
        if cached_value is None:
            # Expensive operation
            value = self.expensive_operation()
            self.redis_client.set(cache_key, json.dumps(value))
            return value
        return json.loads(cached_value)
    
    def expensive_operation(self):
        # Simulate expensive operation
        return sum(range(10000))
    
    def file_processing_without_cache(self, filename):
        # File processing that could benefit from caching
        with open(filename, 'r') as f:
            content = f.read()
        
        # Expensive processing
        processed_data = self.process_file_content(content)
        return processed_data
    
    def process_file_content(self, content):
        # Simulate expensive file processing
        return len(content.split())
'''
    
    # Mixed performance issues
    mixed_issues_content = '''
import time
import sqlite3
import requests
from functools import lru_cache

class ComplexService:
    def __init__(self):
        self.db_connection = None
        self.cache = {}
    
    def initialize(self):
        # Memory leak: connection not properly managed
        self.db_connection = sqlite3.connect('complex.db')
    
    def process_user_data(self, user_ids):
        # Multiple performance issues in one method
        results = []
        
        # CPU bottleneck: nested loops
        for user_id in user_ids:
            for i in range(100):
                for j in range(50):
                    # Database issue: N+1 queries
                    query = "SELECT * FROM user_data WHERE user_id = ? AND category = ?"
                    cursor = self.db_connection.cursor()
                    cursor.execute(query, (user_id, i))
                    data = cursor.fetchall()
                    
                    # Missing caching for expensive operation
                    processed = self.expensive_processing(data)
                    results.append(processed)
                    
                    # Blocking operation in loop
                    time.sleep(0.01)
        
        return results
    
    def expensive_processing(self, data):
        # Could benefit from caching
        return sum(len(str(item)) for item in data)
    
    @lru_cache()  # Configuration issue: no maxsize
    def cached_calculation(self, x):
        return x ** 2
    
    def cleanup(self):
        # Proper cleanup method, but not always called
        if self.db_connection:
            self.db_connection.close()
'''
    
    # Write demo files
    demo_files = {
        'memory_leaks.py': memory_leak_content,
        'database_issues.py': database_issues_content,
        'cpu_bottlenecks.py': cpu_bottleneck_content,
        'caching_issues.py': caching_issues_content,
        'mixed_issues.py': mixed_issues_content
    }
    
    for filename, content in demo_files.items():
        file_path = os.path.join(demo_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
    
    print(f"Created {len(demo_files)} demo files in {demo_dir}")

def run_demo():
    """Run the performance analysis demo"""
    print("Performance Analysis Demo")
    print("=" * 50)
    
    # Create temporary directory for demo files
    demo_dir = tempfile.mkdtemp(prefix="performance_demo_")
    
    try:
        print(f"Creating demo files in: {demo_dir}")
        create_demo_files(demo_dir)
        
        print("\nRunning performance analysis...")
        analyzer = PerformanceAnalyzer()
        results = analyzer.analyze_directory(demo_dir)
        
        print("\nAnalysis completed! Here are the results:")
        analyzer.print_summary(results)
        
        # Save detailed results
        output_file = "performance_demo_results.json"
        analyzer.save_results(results, output_file)
        
        print(f"\nDetailed results saved to: {output_file}")
        
        # Print some specific examples
        print("\n" + "="*60)
        print("EXAMPLE ISSUES FOUND")
        print("="*60)
        
        if results.memory_leaks:
            print(f"\nMemory Leak Example:")
            issue = results.memory_leaks[0]
            print(f"  File: {os.path.basename(issue.file_path)}")
            print(f"  Issue: {issue.description}")
            print(f"  Recommendation: {issue.recommendations[0]}")
        
        if results.database_issues:
            print(f"\nDatabase Performance Example:")
            issue = results.database_issues[0]
            print(f"  File: {os.path.basename(issue.file_path)}")
            print(f"  Issue: {issue.description}")
            print(f"  Suggestion: {issue.optimization_suggestions[0]}")
        
        if results.cpu_bottlenecks:
            print(f"\nCPU Bottleneck Example:")
            issue = results.cpu_bottlenecks[0]
            print(f"  File: {os.path.basename(issue.file_path)}")
            print(f"  Issue: {issue.description}")
            print(f"  Suggestion: {issue.optimization_suggestions[0]}")
        
        if results.caching_issues:
            print(f"\nCaching Optimization Example:")
            issue = results.caching_issues[0]
            print(f"  File: {os.path.basename(issue.file_path)}")
            print(f"  Issue: {issue.description}")
            print(f"  Suggestion: {issue.optimization_suggestions[0]}")
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Demo files location: {demo_dir}")
        print(f"Results file: {output_file}")
        print("\nThe performance analyzer successfully identified various")
        print("performance issues including memory leaks, database problems,")
        print("CPU bottlenecks, and caching optimization opportunities.")
        
    except Exception as e:
        print(f"Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up demo files
        try:
            shutil.rmtree(demo_dir)
            print(f"\nCleaned up demo files from: {demo_dir}")
        except Exception as e:
            print(f"Warning: Could not clean up demo files: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance Analysis Demo")
    parser.add_argument("--keep-files", action="store_true",
                       help="Keep demo files after analysis")
    
    args = parser.parse_args()
    
    if args.keep_files:
        # Modify the demo to keep files
        global cleanup_files
        cleanup_files = False
    
    run_demo()

if __name__ == "__main__":
    main()