#!/usr/bin/env python3
"""
AI Scholar RAG Chatbot - Backend Quality Metrics Collection

This script collects comprehensive backend-specific quality metrics including:
- Code complexity analysis using radon
- Maintainability index calculation
- Technical debt estimation
- Code duplication detection
- Performance metrics
"""

import json
import os
import sys
import subprocess
import ast
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class ComplexityMetrics:
    """Code complexity metrics"""
    cyclomatic_complexity: float
    cognitive_complexity: float
    maintainability_index: float
    lines_of_code: int
    logical_lines: int
    comment_lines: int
    blank_lines: int


@dataclass
class QualityMetrics:
    """Overall quality metrics"""
    timestamp: str
    complexity: ComplexityMetrics
    technical_debt: Dict[str, Any]
    duplication: Dict[str, Any]
    security: Dict[str, Any]
    dependencies: Dict[str, Any]
    test_metrics: Dict[str, Any]
    performance: Dict[str, Any]


class BackendQualityAnalyzer:
    """Backend quality metrics analyzer"""
    
    def __init__(self, backend_dir: str = "backend"):
        self.backend_dir = Path(backend_dir)
        self.output_dir = Path("quality-reports")
        self.output_dir.mkdir(exist_ok=True)
        
        # Ensure we're in the backend directory
        if not self.backend_dir.exists():
            raise FileNotFoundError(f"Backend directory {backend_dir} not found")
    
    def analyze_all_metrics(self) -> QualityMetrics:
        """Collect all quality metrics"""
        print("🔍 Starting backend quality metrics collection...")
        
        metrics = QualityMetrics(
            timestamp=datetime.now().isoformat(),
            complexity=self.analyze_complexity(),
            technical_debt=self.analyze_technical_debt(),
            duplication=self.analyze_code_duplication(),
            security=self.analyze_security_metrics(),
            dependencies=self.analyze_dependencies(),
            test_metrics=self.analyze_test_metrics(),
            performance=self.analyze_performance_metrics()
        )
        
        self.save_metrics(metrics)
        self.generate_reports(metrics)
        
        print("✅ Backend quality metrics collection completed!")
        return metrics
    
    def analyze_complexity(self) -> ComplexityMetrics:
        """Analyze code complexity using AST parsing"""
        print("📊 Analyzing code complexity...")
        
        total_complexity = 0
        total_functions = 0
        total_loc = 0
        total_logical_lines = 0
        total_comment_lines = 0
        total_blank_lines = 0
        
        for py_file in self.backend_dir.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST for complexity analysis
                tree = ast.parse(content)
                file_complexity = self._calculate_cyclomatic_complexity(tree)
                total_complexity += file_complexity
                
                # Count functions
                functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
                total_functions += len(functions)
                
                # Line counting
                lines = content.split('\n')
                total_loc += len(lines)
                
                # Count logical lines (non-empty, non-comment)
                logical_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
                total_logical_lines += len(logical_lines)
                
                # Count comment lines
                comment_lines = [line for line in lines if line.strip().startswith('#')]
                total_comment_lines += len(comment_lines)
                
                # Count blank lines
                blank_lines = [line for line in lines if not line.strip()]
                total_blank_lines += len(blank_lines)
                
            except Exception as e:
                print(f"⚠️ Error analyzing {py_file}: {e}")
                continue
        
        # Calculate averages
        avg_complexity = total_complexity / max(total_functions, 1)
        
        # Calculate maintainability index (simplified version)
        # MI = 171 - 5.2 * ln(Halstead Volume) - 0.23 * (Cyclomatic Complexity) - 16.2 * ln(Lines of Code)
        # Simplified version without Halstead metrics
        maintainability = max(0, 100 - (avg_complexity * 2) - (total_loc / 1000))
        
        return ComplexityMetrics(
            cyclomatic_complexity=round(avg_complexity, 2),
            cognitive_complexity=round(avg_complexity * 1.2, 2),  # Approximation
            maintainability_index=round(maintainability, 2),
            lines_of_code=total_loc,
            logical_lines=total_logical_lines,
            comment_lines=total_comment_lines,
            blank_lines=total_blank_lines
        )
    
    def analyze_technical_debt(self) -> Dict[str, Any]:
        """Analyze technical debt indicators"""
        print("💳 Analyzing technical debt...")
        
        debt_indicators = {
            'todo_comments': 0,
            'fixme_comments': 0,
            'hack_comments': 0,
            'deprecated_usage': 0,
            'long_functions': 0,
            'complex_functions': 0,
            'debt_ratio': 0.0,
            'estimated_hours': 0
        }
        
        for py_file in self.backend_dir.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Count debt indicators
                debt_indicators['todo_comments'] += len(re.findall(r'#.*TODO', content, re.IGNORECASE))
                debt_indicators['fixme_comments'] += len(re.findall(r'#.*FIXME', content, re.IGNORECASE))
                debt_indicators['hack_comments'] += len(re.findall(r'#.*HACK', content, re.IGNORECASE))
                debt_indicators['deprecated_usage'] += len(re.findall(r'@deprecated|warnings\.warn', content, re.IGNORECASE))
                
                # Analyze function complexity
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                        if func_lines > 50:  # Long function threshold
                            debt_indicators['long_functions'] += 1
                        
                        complexity = self._calculate_function_complexity(node)
                        if complexity > 10:  # Complex function threshold
                            debt_indicators['complex_functions'] += 1
                            
            except Exception as e:
                print(f"⚠️ Error analyzing debt in {py_file}: {e}")
                continue
        
        # Calculate debt ratio and estimated remediation time
        total_debt_items = sum([
            debt_indicators['todo_comments'],
            debt_indicators['fixme_comments'],
            debt_indicators['hack_comments'],
            debt_indicators['long_functions'],
            debt_indicators['complex_functions']
        ])
        
        debt_indicators['debt_ratio'] = round(total_debt_items / max(debt_indicators.get('total_functions', 1), 1), 3)
        debt_indicators['estimated_hours'] = total_debt_items * 2  # Rough estimate: 2 hours per debt item
        
        return debt_indicators
    
    def analyze_code_duplication(self) -> Dict[str, Any]:
        """Analyze code duplication"""
        print("🔄 Analyzing code duplication...")
        
        duplication_metrics = {
            'duplicate_blocks': 0,
            'duplicate_lines': 0,
            'duplication_ratio': 0.0,
            'files_with_duplication': []
        }
        
        # Simple duplication detection using line-based comparison
        file_contents = {}
        total_lines = 0
        
        for py_file in self.backend_dir.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith('#')]
                    file_contents[str(py_file)] = lines
                    total_lines += len(lines)
            except Exception as e:
                print(f"⚠️ Error reading {py_file}: {e}")
                continue
        
        # Find duplicate blocks (simplified approach)
        duplicate_lines = 0
        files_with_duplication = set()
        
        for file1, lines1 in file_contents.items():
            for file2, lines2 in file_contents.items():
                if file1 >= file2:  # Avoid duplicate comparisons
                    continue
                
                # Find common subsequences of at least 5 lines
                common_blocks = self._find_common_blocks(lines1, lines2, min_length=5)
                if common_blocks:
                    duplicate_lines += sum(len(block) for block in common_blocks)
                    files_with_duplication.add(file1)
                    files_with_duplication.add(file2)
        
        duplication_metrics['duplicate_blocks'] = len(files_with_duplication)
        duplication_metrics['duplicate_lines'] = duplicate_lines
        duplication_metrics['duplication_ratio'] = round(duplicate_lines / max(total_lines, 1), 3)
        duplication_metrics['files_with_duplication'] = list(files_with_duplication)
        
        return duplication_metrics
    
    def analyze_security_metrics(self) -> Dict[str, Any]:
        """Analyze security-related metrics"""
        print("🔒 Analyzing security metrics...")
        
        security_metrics = {
            'bandit_issues': {},
            'safety_vulnerabilities': 0,
            'security_score': 100,
            'hardcoded_secrets': 0,
            'sql_injection_risks': 0,
            'xss_risks': 0
        }
        
        # Run Bandit security analysis
        try:
            result = subprocess.run([
                'python', '-m', 'bandit', '-r', '.', '-f', 'json'
            ], cwd=self.backend_dir, capture_output=True, text=True)
            
            if result.returncode == 0 or result.stdout:
                bandit_data = json.loads(result.stdout)
                security_metrics['bandit_issues'] = {
                    'total': len(bandit_data.get('results', [])),
                    'high': len([r for r in bandit_data.get('results', []) if r.get('issue_severity') == 'HIGH']),
                    'medium': len([r for r in bandit_data.get('results', []) if r.get('issue_severity') == 'MEDIUM']),
                    'low': len([r for r in bandit_data.get('results', []) if r.get('issue_severity') == 'LOW'])
                }
        except Exception as e:
            print(f"⚠️ Error running Bandit: {e}")
        
        # Run Safety check for dependencies
        try:
            result = subprocess.run([
                'python', '-m', 'safety', 'check', '--json'
            ], cwd=self.backend_dir, capture_output=True, text=True)
            
            if result.stdout:
                safety_data = json.loads(result.stdout)
                security_metrics['safety_vulnerabilities'] = len(safety_data)
        except Exception as e:
            print(f"⚠️ Error running Safety: {e}")
        
        # Manual security pattern detection
        for py_file in self.backend_dir.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for potential security issues
                security_metrics['hardcoded_secrets'] += len(re.findall(
                    r'(password|secret|key|token)\s*=\s*["\'][^"\']+["\']', 
                    content, re.IGNORECASE
                ))
                
                security_metrics['sql_injection_risks'] += len(re.findall(
                    r'execute\s*\(\s*["\'].*%.*["\']', content, re.IGNORECASE
                ))
                
                security_metrics['xss_risks'] += len(re.findall(
                    r'render_template_string|Markup\(|safe\s*\|', content, re.IGNORECASE
                ))
                
            except Exception as e:
                print(f"⚠️ Error analyzing security in {py_file}: {e}")
                continue
        
        # Calculate security score
        total_issues = (
            security_metrics['bandit_issues'].get('total', 0) +
            security_metrics['safety_vulnerabilities'] +
            security_metrics['hardcoded_secrets'] +
            security_metrics['sql_injection_risks'] +
            security_metrics['xss_risks']
        )
        
        security_metrics['security_score'] = max(0, 100 - (total_issues * 5))
        
        return security_metrics
    
    def analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze dependency metrics"""
        print("📦 Analyzing dependencies...")
        
        dependency_metrics = {
            'total_dependencies': 0,
            'outdated_dependencies': 0,
            'dev_dependencies': 0,
            'dependency_tree_depth': 0,
            'license_issues': 0
        }
        
        # Count dependencies from requirements files
        req_files = ['requirements.txt', 'requirements-dev.txt']
        
        for req_file in req_files:
            req_path = self.backend_dir / req_file
            if req_path.exists():
                try:
                    with open(req_path, 'r') as f:
                        lines = [line.strip() for line in f.readlines() 
                                if line.strip() and not line.startswith('#')]
                        
                        if 'dev' in req_file:
                            dependency_metrics['dev_dependencies'] = len(lines)
                        else:
                            dependency_metrics['total_dependencies'] = len(lines)
                            
                except Exception as e:
                    print(f"⚠️ Error reading {req_file}: {e}")
        
        # Try to get more detailed dependency info using pip
        try:
            result = subprocess.run([
                'python', '-m', 'pip', 'list', '--outdated', '--format=json'
            ], cwd=self.backend_dir, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                outdated_data = json.loads(result.stdout)
                dependency_metrics['outdated_dependencies'] = len(outdated_data)
        except Exception as e:
            print(f"⚠️ Error checking outdated dependencies: {e}")
        
        return dependency_metrics
    
    def analyze_test_metrics(self) -> Dict[str, Any]:
        """Analyze test-related metrics"""
        print("🧪 Analyzing test metrics...")
        
        test_metrics = {
            'total_test_files': 0,
            'total_test_functions': 0,
            'test_coverage': 0.0,
            'test_to_code_ratio': 0.0,
            'test_complexity': 0.0
        }
        
        # Count test files and functions
        test_files = list(self.backend_dir.rglob("test_*.py")) + list(self.backend_dir.rglob("*_test.py"))
        test_metrics['total_test_files'] = len(test_files)
        
        total_test_functions = 0
        total_test_complexity = 0
        
        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                test_functions = [node for node in ast.walk(tree) 
                                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) 
                                and node.name.startswith('test_')]
                
                total_test_functions += len(test_functions)
                
                # Calculate test complexity
                for func in test_functions:
                    complexity = self._calculate_function_complexity(func)
                    total_test_complexity += complexity
                    
            except Exception as e:
                print(f"⚠️ Error analyzing test file {test_file}: {e}")
                continue
        
        test_metrics['total_test_functions'] = total_test_functions
        test_metrics['test_complexity'] = round(total_test_complexity / max(total_test_functions, 1), 2)
        
        # Get coverage from pytest if available
        try:
            result = subprocess.run([
                'python', '-m', 'pytest', '--cov=.', '--cov-report=json', '--tb=no', '-q'
            ], cwd=self.backend_dir, capture_output=True, text=True)
            
            coverage_file = self.backend_dir / 'coverage.json'
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                    test_metrics['test_coverage'] = round(coverage_data.get('totals', {}).get('percent_covered', 0), 2)
        except Exception as e:
            print(f"⚠️ Error getting test coverage: {e}")
        
        # Calculate test-to-code ratio
        total_code_files = len(list(self.backend_dir.rglob("*.py"))) - len(test_files)
        test_metrics['test_to_code_ratio'] = round(len(test_files) / max(total_code_files, 1), 2)
        
        return test_metrics
    
    def analyze_performance_metrics(self) -> Dict[str, Any]:
        """Analyze performance-related metrics"""
        print("⚡ Analyzing performance metrics...")
        
        performance_metrics = {
            'import_time': 0.0,
            'startup_time': 0.0,
            'memory_usage': 0,
            'performance_hotspots': []
        }
        
        # Measure import time for main modules
        main_modules = ['app.py', 'main.py', '__init__.py']
        
        for module in main_modules:
            module_path = self.backend_dir / module
            if module_path.exists():
                try:
                    import time
                    start_time = time.time()
                    
                    # This is a simplified approach - in practice, you'd want to
                    # run this in a separate process to avoid import side effects
                    result = subprocess.run([
                        'python', '-c', f'import time; start=time.time(); import {module_path.stem}; print(time.time()-start)'
                    ], cwd=self.backend_dir, capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        import_time = float(result.stdout.strip())
                        performance_metrics['import_time'] = round(import_time, 3)
                        break
                        
                except Exception as e:
                    print(f"⚠️ Error measuring import time for {module}: {e}")
                    continue
        
        # Look for potential performance issues in code
        performance_hotspots = []
        
        for py_file in self.backend_dir.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for performance anti-patterns
                if re.search(r'for.*in.*range\(len\(', content):
                    performance_hotspots.append(f"{py_file}: Inefficient range(len()) loop")
                
                if re.search(r'\.append\(.*\)\s*$', content, re.MULTILINE):
                    append_count = len(re.findall(r'\.append\(', content))
                    if append_count > 10:
                        performance_hotspots.append(f"{py_file}: Many append operations ({append_count})")
                
                if re.search(r'time\.sleep\(', content):
                    performance_hotspots.append(f"{py_file}: Blocking sleep operations")
                    
            except Exception as e:
                print(f"⚠️ Error analyzing performance in {py_file}: {e}")
                continue
        
        performance_metrics['performance_hotspots'] = performance_hotspots[:10]  # Limit to top 10
        
        return performance_metrics
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped in analysis"""
        skip_patterns = [
            '__pycache__',
            '.pytest_cache',
            '.mypy_cache',
            'venv',
            '.venv',
            'migrations',
            'alembic'
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity of AST"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(node, ast.comprehension):
                complexity += 1
        
        return complexity
    
    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate complexity of a single function"""
        complexity = 1
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def _find_common_blocks(self, lines1: List[str], lines2: List[str], min_length: int = 5) -> List[List[str]]:
        """Find common blocks of lines between two files"""
        common_blocks = []
        
        for i in range(len(lines1) - min_length + 1):
            for j in range(len(lines2) - min_length + 1):
                block_length = 0
                
                while (i + block_length < len(lines1) and 
                       j + block_length < len(lines2) and
                       lines1[i + block_length] == lines2[j + block_length]):
                    block_length += 1
                
                if block_length >= min_length:
                    common_blocks.append(lines1[i:i + block_length])
        
        return common_blocks
    
    def save_metrics(self, metrics: QualityMetrics) -> None:
        """Save metrics to JSON file"""
        output_file = self.output_dir / f"backend-quality-metrics-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w') as f:
            json.dump(asdict(metrics), f, indent=2, default=str)
        
        print(f"💾 Backend metrics saved to {output_file}")
    
    def generate_reports(self, metrics: QualityMetrics) -> None:
        """Generate human-readable reports"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Generate Markdown report
        md_report = self._generate_markdown_report(metrics)
        md_file = self.output_dir / f"backend-quality-report-{timestamp}.md"
        
        with open(md_file, 'w') as f:
            f.write(md_report)
        
        print(f"📄 Backend quality report generated: {md_file}")
    
    def _generate_markdown_report(self, metrics: QualityMetrics) -> str:
        """Generate Markdown quality report"""
        return f"""# Backend Quality Metrics Report

**Generated:** {datetime.fromisoformat(metrics.timestamp).strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Code Complexity Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Cyclomatic Complexity | {metrics.complexity.cyclomatic_complexity} | {'✅' if metrics.complexity.cyclomatic_complexity < 10 else '⚠️'} |
| Maintainability Index | {metrics.complexity.maintainability_index}/100 | {'✅' if metrics.complexity.maintainability_index > 70 else '❌'} |
| Lines of Code | {metrics.complexity.lines_of_code:,} | ℹ️ |
| Logical Lines | {metrics.complexity.logical_lines:,} | ℹ️ |
| Comment Lines | {metrics.complexity.comment_lines:,} | ℹ️ |

## 💳 Technical Debt Analysis

| Indicator | Count | Impact |
|-----------|-------|--------|
| TODO Comments | {metrics.technical_debt['todo_comments']} | {'⚠️' if metrics.technical_debt['todo_comments'] > 10 else '✅'} |
| FIXME Comments | {metrics.technical_debt['fixme_comments']} | {'⚠️' if metrics.technical_debt['fixme_comments'] > 5 else '✅'} |
| Long Functions | {metrics.technical_debt['long_functions']} | {'⚠️' if metrics.technical_debt['long_functions'] > 5 else '✅'} |
| Complex Functions | {metrics.technical_debt['complex_functions']} | {'⚠️' if metrics.technical_debt['complex_functions'] > 3 else '✅'} |
| **Estimated Remediation** | {metrics.technical_debt['estimated_hours']} hours | {'❌' if metrics.technical_debt['estimated_hours'] > 40 else '✅'} |

## 🔄 Code Duplication

- **Duplicate Blocks:** {metrics.duplication['duplicate_blocks']}
- **Duplicate Lines:** {metrics.duplication['duplicate_lines']}
- **Duplication Ratio:** {metrics.duplication['duplication_ratio']:.1%}
- **Files Affected:** {len(metrics.duplication['files_with_duplication'])}

## 🔒 Security Analysis

| Category | Count | Severity |
|----------|-------|----------|
| Bandit Issues (High) | {metrics.security['bandit_issues'].get('high', 0)} | {'❌' if metrics.security['bandit_issues'].get('high', 0) > 0 else '✅'} |
| Bandit Issues (Medium) | {metrics.security['bandit_issues'].get('medium', 0)} | {'⚠️' if metrics.security['bandit_issues'].get('medium', 0) > 0 else '✅'} |
| Dependency Vulnerabilities | {metrics.security['safety_vulnerabilities']} | {'❌' if metrics.security['safety_vulnerabilities'] > 0 else '✅'} |
| Hardcoded Secrets | {metrics.security['hardcoded_secrets']} | {'❌' if metrics.security['hardcoded_secrets'] > 0 else '✅'} |
| **Security Score** | {metrics.security['security_score']}/100 | {'✅' if metrics.security['security_score'] > 90 else '⚠️'} |

## 🧪 Test Metrics

- **Test Files:** {metrics.test_metrics['total_test_files']}
- **Test Functions:** {metrics.test_metrics['total_test_functions']}
- **Test Coverage:** {metrics.test_metrics['test_coverage']}%
- **Test-to-Code Ratio:** {metrics.test_metrics['test_to_code_ratio']:.2f}
- **Test Complexity:** {metrics.test_metrics['test_complexity']}

## ⚡ Performance Analysis

- **Import Time:** {metrics.performance['import_time']}s
- **Performance Hotspots:** {len(metrics.performance['performance_hotspots'])}

### Performance Issues Found:
{chr(10).join(f"- {hotspot}" for hotspot in metrics.performance['performance_hotspots'][:5])}

## 📦 Dependencies

- **Total Dependencies:** {metrics.dependencies['total_dependencies']}
- **Dev Dependencies:** {metrics.dependencies['dev_dependencies']}
- **Outdated Dependencies:** {metrics.dependencies['outdated_dependencies']}

## 🎯 Recommendations

{self._generate_recommendations(metrics)}

---
*Report generated by AI Scholar Backend Quality Analyzer*
"""
    
    def _generate_recommendations(self, metrics: QualityMetrics) -> str:
        """Generate recommendations based on metrics"""
        recommendations = []
        
        if metrics.complexity.cyclomatic_complexity > 10:
            recommendations.append("🔧 **Reduce Complexity:** Break down complex functions into smaller, more manageable pieces")
        
        if metrics.complexity.maintainability_index < 70:
            recommendations.append("📈 **Improve Maintainability:** Refactor code to improve readability and reduce complexity")
        
        if metrics.technical_debt['estimated_hours'] > 20:
            recommendations.append("💳 **Address Technical Debt:** Prioritize fixing TODO/FIXME items and refactoring complex functions")
        
        if metrics.duplication['duplication_ratio'] > 0.1:
            recommendations.append("🔄 **Reduce Duplication:** Extract common code into reusable functions or modules")
        
        if metrics.security['security_score'] < 90:
            recommendations.append("🔒 **Improve Security:** Address security issues identified by Bandit and update vulnerable dependencies")
        
        if metrics.test_metrics['test_coverage'] < 80:
            recommendations.append("🧪 **Increase Test Coverage:** Add unit tests to reach target coverage threshold")
        
        if len(metrics.performance['performance_hotspots']) > 0:
            recommendations.append("⚡ **Optimize Performance:** Address identified performance bottlenecks")
        
        if not recommendations:
            recommendations.append("🎉 **Excellent Work!** All quality metrics are within acceptable ranges")
        
        return '\n'.join(f"{i+1}. {rec}" for i, rec in enumerate(recommendations))


def main():
    """Main execution function"""
    try:
        analyzer = BackendQualityAnalyzer()
        metrics = analyzer.analyze_all_metrics()
        
        print(f"\n🎉 Backend quality analysis completed!")
        print(f"📊 Quality Score: {metrics.complexity.maintainability_index}/100")
        print(f"🔒 Security Score: {metrics.security['security_score']}/100")
        print(f"🧪 Test Coverage: {metrics.test_metrics['test_coverage']}%")
        print(f"📄 Reports saved in quality-reports/ directory")
        
        return 0
        
    except Exception as e:
        print(f"❌ Backend quality analysis failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())