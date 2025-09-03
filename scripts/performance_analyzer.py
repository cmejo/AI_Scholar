#!/usr/bin/env python3
"""
Performance Analysis and Optimization Detector

This module provides comprehensive performance analysis capabilities including:
- Memory leak detection for Python services
- Database query performance analysis with optimization suggestions
- CPU usage profiling for identifying performance bottlenecks
- Caching strategy analysis and optimization recommendations

Requirements: 5.1, 5.2, 5.3, 5.4
"""

import os
import sys
import json
import time
import psutil
import sqlite3
import threading
import tracemalloc
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import re
import ast
import subprocess
from collections import defaultdict, Counter

@dataclass
class MemoryLeakIssue:
    """Memory leak detection result"""
    service_name: str
    leak_type: str
    severity: str
    description: str
    memory_growth_rate: float
    recommendations: List[str]
    file_path: Optional[str] = None
    line_number: Optional[int] = None

@dataclass
class DatabasePerformanceIssue:
    """Database query performance issue"""
    query_type: str
    query_text: str
    execution_time: float
    severity: str
    description: str
    optimization_suggestions: List[str]
    file_path: Optional[str] = None
    line_number: Optional[int] = None

@dataclass
class CPUBottleneckIssue:
    """CPU usage bottleneck issue"""
    function_name: str
    cpu_usage_percent: float
    execution_time: float
    severity: str
    description: str
    optimization_suggestions: List[str]
    file_path: Optional[str] = None
    line_number: Optional[int] = None

@dataclass
class CachingOptimizationIssue:
    """Caching strategy optimization issue"""
    cache_type: str
    hit_rate: float
    miss_rate: float
    severity: str
    description: str
    optimization_suggestions: List[str]
    file_path: Optional[str] = None

@dataclass
class PerformanceAnalysisResult:
    """Complete performance analysis result"""
    timestamp: str
    memory_leaks: List[MemoryLeakIssue]
    database_issues: List[DatabasePerformanceIssue]
    cpu_bottlenecks: List[CPUBottleneckIssue]
    caching_issues: List[CachingOptimizationIssue]
    summary: Dict[str, Any]

class MemoryLeakDetector:
    """Memory leak detection tool for Python services"""
    
    def __init__(self):
        self.baseline_memory = {}
        self.memory_snapshots = []
        self.monitoring_active = False
        
    def start_monitoring(self, service_name: str) -> None:
        """Start memory monitoring for a service"""
        self.monitoring_active = True
        self.baseline_memory[service_name] = psutil.virtual_memory().used
        tracemalloc.start()
        
    def stop_monitoring(self) -> None:
        """Stop memory monitoring"""
        self.monitoring_active = False
        if tracemalloc.is_tracing():
            tracemalloc.stop()
    
    def take_snapshot(self, service_name: str) -> None:
        """Take a memory snapshot"""
        if tracemalloc.is_tracing():
            snapshot = tracemalloc.take_snapshot()
            self.memory_snapshots.append({
                'service': service_name,
                'timestamp': time.time(),
                'snapshot': snapshot,
                'memory_usage': psutil.virtual_memory().used
            })
    
    def analyze_python_files(self, directory: str) -> List[MemoryLeakIssue]:
        """Analyze Python files for potential memory leak patterns"""
        issues = []
        
        for root, dirs, files in os.walk(directory):
            # Skip virtual environments and cache directories
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    issues.extend(self._analyze_file_for_leaks(file_path))
        
        return issues
    
    def _analyze_file_for_leaks(self, file_path: str) -> List[MemoryLeakIssue]:
        """Analyze a single Python file for memory leak patterns"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse the AST
            tree = ast.parse(content)
            
            # Check for common memory leak patterns
            issues.extend(self._check_unclosed_resources(tree, file_path, content))
            issues.extend(self._check_circular_references(tree, file_path, content))
            issues.extend(self._check_large_data_structures(tree, file_path, content))
            issues.extend(self._check_event_listeners(tree, file_path, content))
            
        except Exception as e:
            issues.append(MemoryLeakIssue(
                service_name="unknown",
                leak_type="analysis_error",
                severity="low",
                description=f"Could not analyze file for memory leaks: {str(e)}",
                memory_growth_rate=0.0,
                recommendations=["Review file manually for memory leak patterns"],
                file_path=file_path
            ))
        
        return issues
    
    def _check_unclosed_resources(self, tree: ast.AST, file_path: str, content: str) -> List[MemoryLeakIssue]:
        """Check for unclosed file handles, database connections, etc."""
        issues = []
        lines = content.split('\n')
        
        class ResourceVisitor(ast.NodeVisitor):
            def __init__(self):
                self.open_calls = []
                self.with_statements = set()
                self.current_with_lines = set()
                
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and node.func.id == 'open':
                    self.open_calls.append(node.lineno)
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['connect', 'cursor', 'session']:
                        self.open_calls.append(node.lineno)
                self.generic_visit(node)
                
            def visit_With(self, node):
                # Track the range of lines covered by with statement
                start_line = node.lineno
                end_line = start_line
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    end_line = node.end_lineno
                else:
                    # Estimate end line by looking at the body
                    if node.body:
                        end_line = max(getattr(stmt, 'lineno', start_line) for stmt in node.body)
                
                for line in range(start_line, end_line + 1):
                    self.with_statements.add(line)
                
                # Also check the context expression itself
                for item in node.items:
                    if hasattr(item.context_expr, 'lineno'):
                        self.with_statements.add(item.context_expr.lineno)
                
                self.generic_visit(node)
        
        visitor = ResourceVisitor()
        visitor.visit(tree)
        
        # Check for open() calls not in with statements
        for line_no in visitor.open_calls:
            # Check if this line is within any with statement
            in_with_statement = any(
                abs(line_no - with_line) <= 5  # Allow some tolerance
                for with_line in visitor.with_statements
            )
            
            if not in_with_statement:
                issues.append(MemoryLeakIssue(
                    service_name=os.path.basename(file_path),
                    leak_type="unclosed_resource",
                    severity="medium",
                    description=f"Potential unclosed resource at line {line_no}",
                    memory_growth_rate=0.5,
                    recommendations=[
                        "Use context managers (with statements) for resource management",
                        "Ensure all opened resources are properly closed",
                        "Consider using try-finally blocks for cleanup"
                    ],
                    file_path=file_path,
                    line_number=line_no
                ))
        
        return issues
    
    def _check_circular_references(self, tree: ast.AST, file_path: str, content: str) -> List[MemoryLeakIssue]:
        """Check for potential circular reference patterns"""
        issues = []
        
        class CircularRefVisitor(ast.NodeVisitor):
            def __init__(self):
                self.class_refs = defaultdict(list)
                self.current_class = None
                
            def visit_ClassDef(self, node):
                old_class = self.current_class
                self.current_class = node.name
                self.generic_visit(node)
                self.current_class = old_class
                
            def visit_Assign(self, node):
                if self.current_class and isinstance(node.value, ast.Name):
                    for target in node.targets:
                        if isinstance(target, ast.Attribute):
                            self.class_refs[self.current_class].append({
                                'line': node.lineno,
                                'ref': node.value.id
                            })
                self.generic_visit(node)
        
        visitor = CircularRefVisitor()
        visitor.visit(tree)
        
        # Simple heuristic for circular references
        for class_name, refs in visitor.class_refs.items():
            ref_counts = Counter(ref['ref'] for ref in refs)
            for ref_name, count in ref_counts.items():
                if count > 2:  # Multiple references might indicate circular dependency
                    issues.append(MemoryLeakIssue(
                        service_name=os.path.basename(file_path),
                        leak_type="potential_circular_reference",
                        severity="low",
                        description=f"Class {class_name} has multiple references to {ref_name}",
                        memory_growth_rate=0.2,
                        recommendations=[
                            "Review object relationships for circular references",
                            "Use weak references where appropriate",
                            "Implement proper cleanup methods"
                        ],
                        file_path=file_path,
                        line_number=refs[0]['line']
                    ))
        
        return issues
    
    def _check_large_data_structures(self, tree: ast.AST, file_path: str, content: str) -> List[MemoryLeakIssue]:
        """Check for potentially large data structures that might cause memory issues"""
        issues = []
        
        class DataStructureVisitor(ast.NodeVisitor):
            def __init__(self):
                self.large_structures = []
                
            def visit_ListComp(self, node):
                # Check for potentially large list comprehensions
                if self._is_potentially_large(node):
                    self.large_structures.append({
                        'type': 'list_comprehension',
                        'line': node.lineno
                    })
                self.generic_visit(node)
                
            def visit_DictComp(self, node):
                if self._is_potentially_large(node):
                    self.large_structures.append({
                        'type': 'dict_comprehension',
                        'line': node.lineno
                    })
                self.generic_visit(node)
                
            def _is_potentially_large(self, node):
                # Simple heuristic: check for range() calls or file operations
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name) and child.func.id in ['range', 'open']:
                            return True
                return False
        
        visitor = DataStructureVisitor()
        visitor.visit(tree)
        
        for structure in visitor.large_structures:
            issues.append(MemoryLeakIssue(
                service_name=os.path.basename(file_path),
                leak_type="large_data_structure",
                severity="medium",
                description=f"Potentially large {structure['type']} at line {structure['line']}",
                memory_growth_rate=0.7,
                recommendations=[
                    "Consider using generators instead of list comprehensions for large datasets",
                    "Implement pagination or chunking for large data processing",
                    "Use memory-efficient data structures when possible"
                ],
                file_path=file_path,
                line_number=structure['line']
            ))
        
        return issues
    
    def _check_event_listeners(self, tree: ast.AST, file_path: str, content: str) -> List[MemoryLeakIssue]:
        """Check for event listeners that might not be properly removed"""
        issues = []
        
        # Look for event listener patterns
        event_patterns = [
            r'\.addEventListener\(',
            r'\.on\(',
            r'\.bind\(',
            r'signal\.connect\(',
            r'\.subscribe\('
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern in event_patterns:
                if re.search(pattern, line):
                    # Check if there's a corresponding removal
                    removal_patterns = [
                        r'\.removeEventListener\(',
                        r'\.off\(',
                        r'\.unbind\(',
                        r'\.disconnect\(',
                        r'\.unsubscribe\('
                    ]
                    
                    has_removal = any(re.search(rp, content) for rp in removal_patterns)
                    
                    if not has_removal:
                        issues.append(MemoryLeakIssue(
                            service_name=os.path.basename(file_path),
                            leak_type="unremoved_event_listener",
                            severity="medium",
                            description=f"Event listener added at line {i} without corresponding removal",
                            memory_growth_rate=0.3,
                            recommendations=[
                                "Ensure event listeners are properly removed when no longer needed",
                                "Use context managers or cleanup methods",
                                "Consider using weak references for event handlers"
                            ],
                            file_path=file_path,
                            line_number=i
                        ))
                    break
        
        return issues

class DatabasePerformanceAnalyzer:
    """Database query performance analyzer with optimization suggestions"""
    
    def __init__(self):
        self.slow_query_threshold = 1.0  # seconds
        self.query_patterns = {}
        
    def analyze_sql_files(self, directory: str) -> List[DatabasePerformanceIssue]:
        """Analyze SQL files and Python files with database queries"""
        issues = []
        
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
            
            for file in files:
                if file.endswith(('.py', '.sql')):
                    file_path = os.path.join(root, file)
                    issues.extend(self._analyze_file_for_db_issues(file_path))
        
        return issues
    
    def _analyze_file_for_db_issues(self, file_path: str) -> List[DatabasePerformanceIssue]:
        """Analyze a file for database performance issues"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find SQL queries in the file
            queries = self._extract_sql_queries(content)
            
            for query_info in queries:
                issues.extend(self._analyze_query_performance(query_info, file_path))
                
        except Exception as e:
            issues.append(DatabasePerformanceIssue(
                query_type="analysis_error",
                query_text="",
                execution_time=0.0,
                severity="low",
                description=f"Could not analyze file for database issues: {str(e)}",
                optimization_suggestions=["Review file manually for database performance issues"],
                file_path=file_path
            ))
        
        return issues
    
    def _extract_sql_queries(self, content: str) -> List[Dict[str, Any]]:
        """Extract SQL queries from file content"""
        queries = []
        lines = content.split('\n')
        
        # Patterns for SQL queries in Python code
        sql_patterns = [
            r'"""(SELECT.*?)"""',
            r"'''(SELECT.*?)'''",
            r'"(SELECT.*?)"',
            r"'(SELECT.*?)'",
            r'"""(INSERT.*?)"""',
            r"'''(INSERT.*?)'''",
            r'"(INSERT.*?)"',
            r"'(INSERT.*?)'",
            r'"""(UPDATE.*?)"""',
            r"'''(UPDATE.*?)'''",
            r'"(UPDATE.*?)"',
            r"'(UPDATE.*?)'",
            r'"""(DELETE.*?)"""',
            r"'''(DELETE.*?)'''",
            r'"(DELETE.*?)"',
            r"'(DELETE.*?)'"
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in sql_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    query_text = match.group(1).strip()
                    if len(query_text) > 10:  # Filter out very short matches
                        queries.append({
                            'text': query_text,
                            'line_number': i,
                            'type': self._determine_query_type(query_text)
                        })
        
        return queries
    
    def _determine_query_type(self, query: str) -> str:
        """Determine the type of SQL query"""
        query_upper = query.upper().strip()
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        else:
            return 'OTHER'
    
    def _analyze_query_performance(self, query_info: Dict[str, Any], file_path: str) -> List[DatabasePerformanceIssue]:
        """Analyze a specific query for performance issues"""
        issues = []
        query_text = query_info['text']
        query_type = query_info['type']
        line_number = query_info['line_number']
        
        # Check for common performance issues
        issues.extend(self._check_missing_indexes(query_text, query_type, file_path, line_number))
        issues.extend(self._check_n_plus_one_queries(query_text, query_type, file_path, line_number))
        issues.extend(self._check_inefficient_joins(query_text, query_type, file_path, line_number))
        issues.extend(self._check_select_star(query_text, query_type, file_path, line_number))
        issues.extend(self._check_missing_limits(query_text, query_type, file_path, line_number))
        
        return issues
    
    def _check_missing_indexes(self, query: str, query_type: str, file_path: str, line_number: int) -> List[DatabasePerformanceIssue]:
        """Check for queries that might benefit from indexes"""
        issues = []
        
        if query_type == 'SELECT':
            # Look for WHERE clauses without obvious indexes
            where_patterns = [
                r'WHERE\s+(\w+)\s*=',
                r'WHERE\s+(\w+)\s*IN',
                r'WHERE\s+(\w+)\s*LIKE'
            ]
            
            for pattern in where_patterns:
                matches = re.finditer(pattern, query, re.IGNORECASE)
                for match in matches:
                    column = match.group(1)
                    issues.append(DatabasePerformanceIssue(
                        query_type=query_type,
                        query_text=query[:100] + "..." if len(query) > 100 else query,
                        execution_time=0.0,
                        severity="medium",
                        description=f"Query filtering on column '{column}' may benefit from an index",
                        optimization_suggestions=[
                            f"Consider adding an index on column '{column}'",
                            "Analyze query execution plan",
                            "Monitor query performance in production"
                        ],
                        file_path=file_path,
                        line_number=line_number
                    ))
        
        return issues
    
    def _check_n_plus_one_queries(self, query: str, query_type: str, file_path: str, line_number: int) -> List[DatabasePerformanceIssue]:
        """Check for potential N+1 query patterns"""
        issues = []
        
        # Look for queries in loops (simplified heuristic)
        if query_type == 'SELECT' and ('for ' in query.lower() or 'while ' in query.lower()):
            issues.append(DatabasePerformanceIssue(
                query_type=query_type,
                query_text=query[:100] + "..." if len(query) > 100 else query,
                execution_time=0.0,
                severity="high",
                description="Potential N+1 query pattern detected",
                optimization_suggestions=[
                    "Use JOIN queries instead of multiple SELECT queries",
                    "Implement eager loading for related data",
                    "Consider using batch queries",
                    "Use ORM query optimization techniques"
                ],
                file_path=file_path,
                line_number=line_number
            ))
        
        return issues
    
    def _check_inefficient_joins(self, query: str, query_type: str, file_path: str, line_number: int) -> List[DatabasePerformanceIssue]:
        """Check for inefficient JOIN patterns"""
        issues = []
        
        if query_type == 'SELECT' and 'JOIN' in query.upper():
            # Count the number of JOINs (including different types)
            join_patterns = [r'\bJOIN\b', r'\bINNER\s+JOIN\b', r'\bLEFT\s+JOIN\b', r'\bRIGHT\s+JOIN\b', r'\bFULL\s+JOIN\b']
            join_count = 0
            for pattern in join_patterns:
                join_count += len(re.findall(pattern, query, re.IGNORECASE))
            
            if join_count > 2:  # Lowered threshold to catch more cases
                issues.append(DatabasePerformanceIssue(
                    query_type=query_type,
                    query_text=query[:100] + "..." if len(query) > 100 else query,
                    execution_time=0.0,
                    severity="medium",
                    description=f"Query has {join_count} JOINs which may impact performance",
                    optimization_suggestions=[
                        "Consider breaking complex queries into simpler ones",
                        "Ensure all JOIN conditions use indexed columns",
                        "Review if all JOINs are necessary",
                        "Consider denormalization for frequently accessed data"
                    ],
                    file_path=file_path,
                    line_number=line_number
                ))
        
        return issues
    
    def _check_select_star(self, query: str, query_type: str, file_path: str, line_number: int) -> List[DatabasePerformanceIssue]:
        """Check for SELECT * queries"""
        issues = []
        
        if query_type == 'SELECT' and re.search(r'SELECT\s+\*', query, re.IGNORECASE):
            issues.append(DatabasePerformanceIssue(
                query_type=query_type,
                query_text=query[:100] + "..." if len(query) > 100 else query,
                execution_time=0.0,
                severity="low",
                description="Query uses SELECT * which may be inefficient",
                optimization_suggestions=[
                    "Select only the columns you need",
                    "Reduce network traffic by limiting data transfer",
                    "Improve query cache efficiency",
                    "Make queries more maintainable"
                ],
                file_path=file_path,
                line_number=line_number
            ))
        
        return issues
    
    def _check_missing_limits(self, query: str, query_type: str, file_path: str, line_number: int) -> List[DatabasePerformanceIssue]:
        """Check for SELECT queries without LIMIT clauses"""
        issues = []
        
        if (query_type == 'SELECT' and 
            'LIMIT' not in query.upper() and 
            'COUNT(' not in query.upper() and
            len(query) > 50):  # Only check substantial queries
            
            issues.append(DatabasePerformanceIssue(
                query_type=query_type,
                query_text=query[:100] + "..." if len(query) > 100 else query,
                execution_time=0.0,
                severity="medium",
                description="Query lacks LIMIT clause and may return excessive data",
                optimization_suggestions=[
                    "Add LIMIT clause to prevent excessive data retrieval",
                    "Implement pagination for large result sets",
                    "Consider if all results are actually needed",
                    "Add appropriate WHERE conditions to filter results"
                ],
                file_path=file_path,
                line_number=line_number
            ))
        
        return issues

class CPUProfiler:
    """CPU usage profiler for identifying performance bottlenecks"""
    
    def __init__(self):
        self.cpu_threshold = 80.0  # CPU usage percentage threshold
        self.profiling_data = {}
        
    def analyze_python_files(self, directory: str) -> List[CPUBottleneckIssue]:
        """Analyze Python files for potential CPU bottlenecks"""
        issues = []
        
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    issues.extend(self._analyze_file_for_cpu_issues(file_path))
        
        return issues
    
    def _analyze_file_for_cpu_issues(self, file_path: str) -> List[CPUBottleneckIssue]:
        """Analyze a Python file for CPU bottleneck patterns"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Check for CPU-intensive patterns
            issues.extend(self._check_nested_loops(tree, file_path, content))
            issues.extend(self._check_recursive_functions(tree, file_path, content))
            issues.extend(self._check_inefficient_operations(tree, file_path, content))
            issues.extend(self._check_blocking_operations(tree, file_path, content))
            
        except Exception as e:
            issues.append(CPUBottleneckIssue(
                function_name="unknown",
                cpu_usage_percent=0.0,
                execution_time=0.0,
                severity="low",
                description=f"Could not analyze file for CPU issues: {str(e)}",
                optimization_suggestions=["Review file manually for CPU bottlenecks"],
                file_path=file_path
            ))
        
        return issues
    
    def _check_nested_loops(self, tree: ast.AST, file_path: str, content: str) -> List[CPUBottleneckIssue]:
        """Check for nested loops that might cause CPU bottlenecks"""
        issues = []
        
        class LoopVisitor(ast.NodeVisitor):
            def __init__(self):
                self.loop_depth = 0
                self.nested_loops = []
                
            def visit_For(self, node):
                self.loop_depth += 1
                if self.loop_depth >= 3:  # Triple nested or more
                    self.nested_loops.append({
                        'line': node.lineno,
                        'depth': self.loop_depth,
                        'type': 'for'
                    })
                self.generic_visit(node)
                self.loop_depth -= 1
                
            def visit_While(self, node):
                self.loop_depth += 1
                if self.loop_depth >= 3:
                    self.nested_loops.append({
                        'line': node.lineno,
                        'depth': self.loop_depth,
                        'type': 'while'
                    })
                self.generic_visit(node)
                self.loop_depth -= 1
        
        visitor = LoopVisitor()
        visitor.visit(tree)
        
        for loop in visitor.nested_loops:
            severity = "high" if loop['depth'] >= 4 else "medium"
            issues.append(CPUBottleneckIssue(
                function_name="nested_loop",
                cpu_usage_percent=85.0,
                execution_time=0.0,
                severity=severity,
                description=f"Nested {loop['type']} loop with depth {loop['depth']} at line {loop['line']}",
                optimization_suggestions=[
                    "Consider algorithmic improvements to reduce time complexity",
                    "Use vectorized operations where possible",
                    "Implement early exit conditions",
                    "Consider caching intermediate results",
                    "Break down complex operations into smaller chunks"
                ],
                file_path=file_path,
                line_number=loop['line']
            ))
        
        return issues
    
    def _check_recursive_functions(self, tree: ast.AST, file_path: str, content: str) -> List[CPUBottleneckIssue]:
        """Check for recursive functions that might cause performance issues"""
        issues = []
        
        class RecursionVisitor(ast.NodeVisitor):
            def __init__(self):
                self.functions = {}
                self.current_function = None
                
            def visit_FunctionDef(self, node):
                old_function = self.current_function
                self.current_function = node.name
                self.functions[node.name] = {
                    'line': node.lineno,
                    'calls_self': False
                }
                self.generic_visit(node)
                self.current_function = old_function
                
            def visit_Call(self, node):
                if (self.current_function and 
                    isinstance(node.func, ast.Name) and 
                    node.func.id == self.current_function):
                    self.functions[self.current_function]['calls_self'] = True
                self.generic_visit(node)
        
        visitor = RecursionVisitor()
        visitor.visit(tree)
        
        for func_name, info in visitor.functions.items():
            if info['calls_self']:
                issues.append(CPUBottleneckIssue(
                    function_name=func_name,
                    cpu_usage_percent=70.0,
                    execution_time=0.0,
                    severity="medium",
                    description=f"Recursive function '{func_name}' at line {info['line']}",
                    optimization_suggestions=[
                        "Consider iterative implementation instead of recursion",
                        "Implement memoization to cache results",
                        "Add recursion depth limits",
                        "Use tail recursion optimization if available",
                        "Consider using dynamic programming approaches"
                    ],
                    file_path=file_path,
                    line_number=info['line']
                ))
        
        return issues
    
    def _check_inefficient_operations(self, tree: ast.AST, file_path: str, content: str) -> List[CPUBottleneckIssue]:
        """Check for inefficient operations that might cause CPU bottlenecks"""
        issues = []
        
        class OperationVisitor(ast.NodeVisitor):
            def __init__(self):
                self.inefficient_ops = []
                
            def visit_Call(self, node):
                # Check for potentially inefficient operations
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['sorted', 'sort'] and len(node.args) > 0:
                        self.inefficient_ops.append({
                            'line': node.lineno,
                            'operation': 'sorting',
                            'function': node.func.id
                        })
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['sort', 'reverse']:
                        self.inefficient_ops.append({
                            'line': node.lineno,
                            'operation': 'list_operation',
                            'function': node.func.attr
                        })
                
                self.generic_visit(node)
                
            def visit_ListComp(self, node):
                # Check for nested list comprehensions
                for generator in node.generators:
                    if isinstance(generator.iter, ast.ListComp):
                        self.inefficient_ops.append({
                            'line': node.lineno,
                            'operation': 'nested_comprehension',
                            'function': 'list_comprehension'
                        })
                self.generic_visit(node)
        
        visitor = OperationVisitor()
        visitor.visit(tree)
        
        for op in visitor.inefficient_ops:
            severity = "medium" if op['operation'] == 'nested_comprehension' else "low"
            issues.append(CPUBottleneckIssue(
                function_name=op['function'],
                cpu_usage_percent=60.0,
                execution_time=0.0,
                severity=severity,
                description=f"Potentially inefficient {op['operation']} at line {op['line']}",
                optimization_suggestions=[
                    "Consider using more efficient algorithms",
                    "Use built-in functions optimized for performance",
                    "Implement lazy evaluation where possible",
                    "Consider using NumPy for numerical operations",
                    "Profile the code to identify actual bottlenecks"
                ],
                file_path=file_path,
                line_number=op['line']
            ))
        
        return issues
    
    def _check_blocking_operations(self, tree: ast.AST, file_path: str, content: str) -> List[CPUBottleneckIssue]:
        """Check for blocking operations that might cause performance issues"""
        issues = []
        
        # Look for blocking operations in the code
        blocking_patterns = [
            (r'time\.sleep\(', 'sleep'),
            (r'requests\.get\(', 'http_request'),
            (r'requests\.post\(', 'http_request'),
            (r'urllib\.request\.urlopen\(', 'http_request'),
            (r'input\(', 'user_input'),
            (r'raw_input\(', 'user_input')
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, op_type in blocking_patterns:
                if re.search(pattern, line):
                    issues.append(CPUBottleneckIssue(
                        function_name=op_type,
                        cpu_usage_percent=0.0,  # Blocking, not CPU intensive
                        execution_time=5.0,  # Estimated blocking time
                        severity="medium",
                        description=f"Blocking {op_type} operation at line {i}",
                        optimization_suggestions=[
                            "Consider using async/await for non-blocking operations",
                            "Implement timeouts for external requests",
                            "Use threading or multiprocessing for concurrent operations",
                            "Consider using connection pooling for HTTP requests",
                            "Implement proper error handling for blocking operations"
                        ],
                        file_path=file_path,
                        line_number=i
                    ))
        
        return issues

class CachingAnalyzer:
    """Caching strategy analyzer and optimization recommender"""
    
    def __init__(self):
        self.cache_patterns = {}
        self.redis_patterns = []
        self.memory_cache_patterns = []
        
    def analyze_caching_strategies(self, directory: str) -> List[CachingOptimizationIssue]:
        """Analyze caching strategies in the codebase"""
        issues = []
        
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    issues.extend(self._analyze_file_for_caching(file_path))
        
        return issues
    
    def _analyze_file_for_caching(self, file_path: str) -> List[CachingOptimizationIssue]:
        """Analyze a file for caching optimization opportunities"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for various caching patterns and opportunities
            issues.extend(self._check_missing_caching(content, file_path))
            issues.extend(self._check_cache_invalidation(content, file_path))
            issues.extend(self._check_cache_configuration(content, file_path))
            issues.extend(self._check_cache_efficiency(content, file_path))
            
        except Exception as e:
            issues.append(CachingOptimizationIssue(
                cache_type="analysis_error",
                hit_rate=0.0,
                miss_rate=0.0,
                severity="low",
                description=f"Could not analyze file for caching issues: {str(e)}",
                optimization_suggestions=["Review file manually for caching opportunities"],
                file_path=file_path
            ))
        
        return issues
    
    def _check_missing_caching(self, content: str, file_path: str) -> List[CachingOptimizationIssue]:
        """Check for functions that could benefit from caching"""
        issues = []
        
        # Look for expensive operations that could be cached
        expensive_patterns = [
            (r'requests\.get\(', 'http_requests'),
            (r'requests\.post\(', 'http_requests'),
            (r'\.query\(', 'database_queries'),
            (r'SELECT.*FROM', 'sql_queries'),
            (r'open\(.*\)\.read\(\)', 'file_operations'),
            (r'json\.loads\(', 'json_parsing'),
            (r'pickle\.loads\(', 'serialization')
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, operation_type in expensive_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Check if caching is already implemented in the surrounding context
                    function_content = self._extract_function_content(content, i)
                    if not self._has_caching(function_content):
                        issues.append(CachingOptimizationIssue(
                            cache_type="missing_cache",
                            hit_rate=0.0,
                            miss_rate=100.0,
                            severity="medium",
                            description=f"Function with {operation_type} at line {i} could benefit from caching",
                            optimization_suggestions=[
                                "Implement caching for expensive operations",
                                "Use @lru_cache decorator for pure functions",
                                "Consider Redis caching for shared data",
                                "Implement cache invalidation strategy",
                                "Monitor cache hit rates"
                            ],
                            file_path=file_path
                        ))
        
        return issues
    
    def _extract_function_content(self, content: str, start_line: int) -> str:
        """Extract function content starting from a given line"""
        lines = content.split('\n')
        if start_line > len(lines):
            return ""
        
        # Simple heuristic to extract function content
        function_lines = []
        indent_level = None
        
        for i in range(start_line - 1, len(lines)):
            line = lines[i]
            if line.strip() == "":
                continue
                
            current_indent = len(line) - len(line.lstrip())
            
            if indent_level is None:
                indent_level = current_indent
                function_lines.append(line)
            elif current_indent > indent_level or line.strip().startswith(('"""', "'''")):
                function_lines.append(line)
            else:
                break
        
        return '\n'.join(function_lines)
    
    def _has_caching(self, function_content: str) -> bool:
        """Check if function already has caching implemented"""
        cache_indicators = [
            '@lru_cache',
            '@cache',
            'redis.get',
            'cache.get',
            'cached_result',
            'from_cache',
            'cache_key'
        ]
        
        return any(indicator in function_content for indicator in cache_indicators)
    
    def _check_cache_invalidation(self, content: str, file_path: str) -> List[CachingOptimizationIssue]:
        """Check for proper cache invalidation strategies"""
        issues = []
        
        # Look for cache usage without proper invalidation
        cache_usage_patterns = [
            r'@lru_cache',
            r'redis\.set\(',
            r'cache\.set\(',
            r'\.cache\['
        ]
        
        invalidation_patterns = [
            r'cache\.delete\(',
            r'cache\.clear\(',
            r'redis\.delete\(',
            r'cache_clear\(',
            r'invalidate_cache\('
        ]
        
        has_cache_usage = any(re.search(pattern, content) for pattern in cache_usage_patterns)
        has_invalidation = any(re.search(pattern, content) for pattern in invalidation_patterns)
        
        if has_cache_usage and not has_invalidation:
            issues.append(CachingOptimizationIssue(
                cache_type="invalidation_missing",
                hit_rate=70.0,
                miss_rate=30.0,
                severity="medium",
                description="Cache usage detected without proper invalidation strategy",
                optimization_suggestions=[
                    "Implement cache invalidation for data updates",
                    "Use TTL (Time To Live) for automatic expiration",
                    "Implement cache versioning for data consistency",
                    "Consider event-driven cache invalidation",
                    "Monitor cache staleness"
                ],
                file_path=file_path
            ))
        
        return issues
    
    def _check_cache_configuration(self, content: str, file_path: str) -> List[CachingOptimizationIssue]:
        """Check cache configuration for optimization opportunities"""
        issues = []
        
        # Look for cache configuration issues
        config_patterns = [
            (r'@lru_cache\(\)', 'lru_cache_no_maxsize'),
            (r'@lru_cache\(maxsize=None\)', 'lru_cache_unlimited'),
            (r'redis\.Redis\(.*decode_responses=False', 'redis_no_decode'),
            (r'cache\.set\(.*timeout=None', 'cache_no_timeout')
        ]
        
        for pattern, issue_type in config_patterns:
            if re.search(pattern, content):
                severity = "medium" if "unlimited" in issue_type else "low"
                issues.append(CachingOptimizationIssue(
                    cache_type=issue_type,
                    hit_rate=60.0,
                    miss_rate=40.0,
                    severity=severity,
                    description=f"Cache configuration issue: {issue_type}",
                    optimization_suggestions=[
                        "Set appropriate cache size limits",
                        "Configure cache timeouts",
                        "Enable response decoding for Redis",
                        "Monitor cache memory usage",
                        "Implement cache size monitoring"
                    ],
                    file_path=file_path
                ))
        
        return issues
    
    def _check_cache_efficiency(self, content: str, file_path: str) -> List[CachingOptimizationIssue]:
        """Check for cache efficiency issues"""
        issues = []
        
        # Look for patterns that might indicate inefficient caching
        inefficient_patterns = [
            (r'cache\.get\(.*\)\s*is None.*cache\.set\(', 'cache_check_pattern'),
            (r'if.*not.*in.*cache.*cache\[', 'manual_cache_check'),
            (r'cache\.get\(.*json\.dumps', 'json_cache_key'),
            (r'cache\.set\(.*pickle\.dumps', 'pickle_cache_value')
        ]
        
        for pattern, issue_type in inefficient_patterns:
            if re.search(pattern, content, re.DOTALL):
                issues.append(CachingOptimizationIssue(
                    cache_type=issue_type,
                    hit_rate=50.0,
                    miss_rate=50.0,
                    severity="low",
                    description=f"Potentially inefficient caching pattern: {issue_type}",
                    optimization_suggestions=[
                        "Use cache.get_or_set() for atomic operations",
                        "Implement consistent cache key generation",
                        "Consider using cache decorators",
                        "Optimize cache value serialization",
                        "Use cache warming strategies"
                    ],
                    file_path=file_path
                ))
        
        return issues

class PerformanceAnalyzer:
    """Main performance analysis and optimization detector"""
    
    def __init__(self):
        self.memory_detector = MemoryLeakDetector()
        self.db_analyzer = DatabasePerformanceAnalyzer()
        self.cpu_profiler = CPUProfiler()
        self.cache_analyzer = CachingAnalyzer()
        
    def analyze_directory(self, directory: str) -> PerformanceAnalysisResult:
        """Perform comprehensive performance analysis on a directory"""
        print(f"Starting performance analysis of directory: {directory}")
        
        # Perform all analyses
        memory_leaks = self.memory_detector.analyze_python_files(directory)
        database_issues = self.db_analyzer.analyze_sql_files(directory)
        cpu_bottlenecks = self.cpu_profiler.analyze_python_files(directory)
        caching_issues = self.cache_analyzer.analyze_caching_strategies(directory)
        
        # Generate summary
        summary = self._generate_summary(memory_leaks, database_issues, cpu_bottlenecks, caching_issues)
        
        return PerformanceAnalysisResult(
            timestamp=datetime.now().isoformat(),
            memory_leaks=memory_leaks,
            database_issues=database_issues,
            cpu_bottlenecks=cpu_bottlenecks,
            caching_issues=caching_issues,
            summary=summary
        )
    
    def _generate_summary(self, memory_leaks: List[MemoryLeakIssue], 
                         database_issues: List[DatabasePerformanceIssue],
                         cpu_bottlenecks: List[CPUBottleneckIssue],
                         caching_issues: List[CachingOptimizationIssue]) -> Dict[str, Any]:
        """Generate analysis summary"""
        
        def count_by_severity(issues):
            counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for issue in issues:
                severity = getattr(issue, 'severity', 'low')
                counts[severity] = counts.get(severity, 0) + 1
            return counts
        
        return {
            "total_issues": len(memory_leaks) + len(database_issues) + len(cpu_bottlenecks) + len(caching_issues),
            "memory_leaks": {
                "count": len(memory_leaks),
                "severity_breakdown": count_by_severity(memory_leaks)
            },
            "database_issues": {
                "count": len(database_issues),
                "severity_breakdown": count_by_severity(database_issues)
            },
            "cpu_bottlenecks": {
                "count": len(cpu_bottlenecks),
                "severity_breakdown": count_by_severity(cpu_bottlenecks)
            },
            "caching_issues": {
                "count": len(caching_issues),
                "severity_breakdown": count_by_severity(caching_issues)
            },
            "recommendations": [
                "Implement proper resource management with context managers",
                "Add database query optimization and indexing",
                "Use async/await for non-blocking operations",
                "Implement comprehensive caching strategies",
                "Monitor performance metrics in production"
            ]
        }
    
    def save_results(self, results: PerformanceAnalysisResult, output_file: str) -> None:
        """Save analysis results to a JSON file"""
        with open(output_file, 'w') as f:
            json.dump(asdict(results), f, indent=2, default=str)
        print(f"Performance analysis results saved to: {output_file}")
    
    def print_summary(self, results: PerformanceAnalysisResult) -> None:
        """Print a summary of the analysis results"""
        print("\n" + "="*80)
        print("PERFORMANCE ANALYSIS SUMMARY")
        print("="*80)
        
        summary = results.summary
        print(f"Total Issues Found: {summary['total_issues']}")
        print()
        
        categories = [
            ("Memory Leaks", results.memory_leaks, summary['memory_leaks']),
            ("Database Issues", results.database_issues, summary['database_issues']),
            ("CPU Bottlenecks", results.cpu_bottlenecks, summary['cpu_bottlenecks']),
            ("Caching Issues", results.caching_issues, summary['caching_issues'])
        ]
        
        for category_name, issues, category_summary in categories:
            print(f"{category_name}: {category_summary['count']} issues")
            if category_summary['count'] > 0:
                severity_counts = category_summary['severity_breakdown']
                print(f"  Critical: {severity_counts.get('critical', 0)}")
                print(f"  High: {severity_counts.get('high', 0)}")
                print(f"  Medium: {severity_counts.get('medium', 0)}")
                print(f"  Low: {severity_counts.get('low', 0)}")
                
                # Show top 3 issues
                print("  Top Issues:")
                for i, issue in enumerate(issues[:3], 1):
                    description = getattr(issue, 'description', 'No description')
                    file_path = getattr(issue, 'file_path', 'Unknown file')
                    print(f"    {i}. {description} ({os.path.basename(file_path)})")
            print()
        
        print("Top Recommendations:")
        for i, rec in enumerate(summary['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print("="*80)

def main():
    """Main function to run performance analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance Analysis and Optimization Detector")
    parser.add_argument("directory", help="Directory to analyze")
    parser.add_argument("--output", "-o", default="performance_analysis_results.json",
                       help="Output file for results")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist")
        sys.exit(1)
    
    analyzer = PerformanceAnalyzer()
    results = analyzer.analyze_directory(args.directory)
    
    analyzer.save_results(results, args.output)
    analyzer.print_summary(results)
    
    if args.verbose:
        print(f"\nDetailed results saved to: {args.output}")

if __name__ == "__main__":
    main()