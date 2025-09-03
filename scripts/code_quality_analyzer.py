#!/usr/bin/env python3
"""
Code Quality and Technical Debt Analyzer

This module provides comprehensive analysis of code quality issues and technical debt
across the AI Scholar codebase, including:
- Code structure analysis for coding standards violations
- Dependency analysis for outdated and unnecessary packages
- Error handling completeness checking
- Documentation coverage analysis and gap identification

Requirements: 6.1, 6.2, 6.3, 6.4
"""

import os
import json
import ast
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class QualityIssue:
    """Represents a code quality or technical debt issue"""
    type: str
    severity: str
    file_path: str
    line_number: Optional[int]
    description: str
    recommendation: str
    category: str
    auto_fixable: bool = False

@dataclass
class DependencyIssue:
    """Represents a dependency-related issue"""
    package_name: str
    current_version: str
    latest_version: str
    issue_type: str  # 'outdated', 'unnecessary', 'vulnerable'
    file_path: str
    recommendation: str

@dataclass
class DocumentationGap:
    """Represents missing or inadequate documentation"""
    file_path: str
    function_name: Optional[str]
    class_name: Optional[str]
    gap_type: str  # 'missing_docstring', 'incomplete_docstring', 'missing_type_hints'
    description: str
    recommendation: str

class CodeStructureAnalyzer:
    """Analyzes code structure for violations of coding standards"""
    
    def __init__(self):
        self.issues: List[QualityIssue] = []
        self.coding_standards = {
            'max_function_length': 50,
            'max_class_length': 500,
            'max_complexity': 10,
            'max_parameters': 5,
            'max_nesting_depth': 4
        }
    
    def analyze_python_files(self, directory: str) -> List[QualityIssue]:
        """Analyze Python files for code structure violations"""
        issues = []
        
        for root, dirs, files in os.walk(directory):
            # Skip virtual environments and cache directories
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.pytest_cache', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        issues.extend(self._analyze_python_file(file_path))
                    except Exception as e:
                        logger.warning(f"Error analyzing {file_path}: {e}")
        
        return issues
    
    def _analyze_python_file(self, file_path: str) -> List[QualityIssue]:
        """Analyze a single Python file for structure violations"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
            
            # Analyze functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    issues.extend(self._analyze_function(node, file_path, content))
                elif isinstance(node, ast.ClassDef):
                    issues.extend(self._analyze_class(node, file_path, content))
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    issues.extend(self._analyze_import(node, file_path))
            
            # Check for long files
            lines = content.split('\n')
            if len(lines) > 1000:
                issues.append(QualityIssue(
                    type="file_too_long",
                    severity="medium",
                    file_path=file_path,
                    line_number=None,
                    description=f"File has {len(lines)} lines, exceeding recommended 1000 lines",
                    recommendation="Consider splitting this file into smaller, more focused modules",
                    category="code_structure"
                ))
            
        except SyntaxError as e:
            issues.append(QualityIssue(
                type="syntax_error",
                severity="critical",
                file_path=file_path,
                line_number=e.lineno,
                description=f"Syntax error: {e.msg}",
                recommendation="Fix syntax error to enable proper code analysis",
                category="syntax"
            ))
        
        return issues
    
    def _analyze_function(self, node: ast.FunctionDef, file_path: str, content: str) -> List[QualityIssue]:
        """Analyze function for structure violations"""
        issues = []
        lines = content.split('\n')
        
        # Calculate function length
        func_lines = node.end_lineno - node.lineno + 1 if node.end_lineno else 0
        if func_lines > self.coding_standards['max_function_length']:
            issues.append(QualityIssue(
                type="function_too_long",
                severity="medium",
                file_path=file_path,
                line_number=node.lineno,
                description=f"Function '{node.name}' has {func_lines} lines, exceeding recommended {self.coding_standards['max_function_length']}",
                recommendation="Consider breaking this function into smaller, more focused functions",
                category="code_structure"
            ))
        
        # Check parameter count
        param_count = len(node.args.args)
        if param_count > self.coding_standards['max_parameters']:
            issues.append(QualityIssue(
                type="too_many_parameters",
                severity="medium",
                file_path=file_path,
                line_number=node.lineno,
                description=f"Function '{node.name}' has {param_count} parameters, exceeding recommended {self.coding_standards['max_parameters']}",
                recommendation="Consider using a configuration object or breaking the function into smaller parts",
                category="code_structure"
            ))
        
        # Check for missing docstring
        if not ast.get_docstring(node):
            issues.append(QualityIssue(
                type="missing_docstring",
                severity="low",
                file_path=file_path,
                line_number=node.lineno,
                description=f"Function '{node.name}' is missing a docstring",
                recommendation="Add a docstring describing the function's purpose, parameters, and return value",
                category="documentation",
                auto_fixable=True
            ))
        
        return issues
    
    def _analyze_class(self, node: ast.ClassDef, file_path: str, content: str) -> List[QualityIssue]:
        """Analyze class for structure violations"""
        issues = []
        
        # Calculate class length
        class_lines = node.end_lineno - node.lineno + 1 if node.end_lineno else 0
        if class_lines > self.coding_standards['max_class_length']:
            issues.append(QualityIssue(
                type="class_too_long",
                severity="medium",
                file_path=file_path,
                line_number=node.lineno,
                description=f"Class '{node.name}' has {class_lines} lines, exceeding recommended {self.coding_standards['max_class_length']}",
                recommendation="Consider breaking this class into smaller, more focused classes",
                category="code_structure"
            ))
        
        # Check for missing docstring
        if not ast.get_docstring(node):
            issues.append(QualityIssue(
                type="missing_docstring",
                severity="low",
                file_path=file_path,
                line_number=node.lineno,
                description=f"Class '{node.name}' is missing a docstring",
                recommendation="Add a docstring describing the class's purpose and usage",
                category="documentation",
                auto_fixable=True
            ))
        
        return issues
    
    def _analyze_import(self, node: ast.Import | ast.ImportFrom, file_path: str) -> List[QualityIssue]:
        """Analyze imports for potential issues"""
        issues = []
        
        # Check for unused imports (basic check)
        # This is a simplified check - a more sophisticated version would track usage
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith('_'):
                    issues.append(QualityIssue(
                        type="private_import",
                        severity="low",
                        file_path=file_path,
                        line_number=node.lineno,
                        description=f"Importing private module '{alias.name}'",
                        recommendation="Avoid importing private modules; use public APIs instead",
                        category="code_structure"
                    ))
        
        return issues

class DependencyAnalyzer:
    """Analyzes dependencies for outdated and unnecessary packages"""
    
    def __init__(self):
        self.issues: List[DependencyIssue] = []
    
    def analyze_python_dependencies(self, requirements_files: List[str]) -> List[DependencyIssue]:
        """Analyze Python dependencies for issues"""
        issues = []
        
        for req_file in requirements_files:
            if os.path.exists(req_file):
                try:
                    issues.extend(self._analyze_requirements_file(req_file))
                except Exception as e:
                    logger.warning(f"Error analyzing {req_file}: {e}")
        
        return issues
    
    def _analyze_requirements_file(self, file_path: str) -> List[DependencyIssue]:
        """Analyze a requirements file for dependency issues"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    issues.extend(self._analyze_dependency_line(line, file_path, line_num))
        
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
        
        return issues
    
    def _analyze_dependency_line(self, line: str, file_path: str, line_num: int) -> List[DependencyIssue]:
        """Analyze a single dependency line"""
        issues = []
        
        # Parse package name and version
        if '==' in line:
            package_name, version = line.split('==', 1)
            package_name = package_name.strip()
            version = version.strip()
            
            # Check for outdated packages (simplified check)
            if self._is_potentially_outdated(package_name, version):
                issues.append(DependencyIssue(
                    package_name=package_name,
                    current_version=version,
                    latest_version="unknown",
                    issue_type="potentially_outdated",
                    file_path=file_path,
                    recommendation=f"Check if {package_name} has newer versions available"
                ))
        
        return issues
    
    def _is_potentially_outdated(self, package_name: str, version: str) -> bool:
        """Simple heuristic to identify potentially outdated packages"""
        # This is a simplified check - in practice, you'd query PyPI API
        outdated_patterns = [
            r'^\d+\.\d+$',  # Major.minor only (missing patch)
            r'^0\.\d+',     # Pre-1.0 versions
        ]
        
        for pattern in outdated_patterns:
            if re.match(pattern, version):
                return True
        
        return False
    
    def analyze_node_dependencies(self, package_json_files: List[str]) -> List[DependencyIssue]:
        """Analyze Node.js dependencies for issues"""
        issues = []
        
        for package_file in package_json_files:
            if os.path.exists(package_file):
                try:
                    issues.extend(self._analyze_package_json(package_file))
                except Exception as e:
                    logger.warning(f"Error analyzing {package_file}: {e}")
        
        return issues
    
    def _analyze_package_json(self, file_path: str) -> List[DependencyIssue]:
        """Analyze package.json for dependency issues"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            # Analyze dependencies
            for dep_type in ['dependencies', 'devDependencies']:
                if dep_type in package_data:
                    for package_name, version in package_data[dep_type].items():
                        if self._is_node_package_outdated(package_name, version):
                            issues.append(DependencyIssue(
                                package_name=package_name,
                                current_version=version,
                                latest_version="unknown",
                                issue_type="potentially_outdated",
                                file_path=file_path,
                                recommendation=f"Check if {package_name} has newer versions available"
                            ))
        
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
        
        return issues
    
    def _is_node_package_outdated(self, package_name: str, version: str) -> bool:
        """Simple heuristic to identify potentially outdated Node packages"""
        # Check for very old version patterns
        if version.startswith('^0.') or version.startswith('~0.'):
            return True
        
        # Check for exact old versions
        old_patterns = [
            r'^\d+\.\d+\.\d+$',  # Exact versions without range
        ]
        
        for pattern in old_patterns:
            if re.match(pattern, version.lstrip('^~')):
                return True
        
        return False

class ErrorHandlingAnalyzer:
    """Analyzes error handling completeness"""
    
    def __init__(self):
        self.issues: List[QualityIssue] = []
    
    def analyze_error_handling(self, directory: str) -> List[QualityIssue]:
        """Analyze error handling patterns in Python files"""
        issues = []
        
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.pytest_cache', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        issues.extend(self._analyze_file_error_handling(file_path))
                    except Exception as e:
                        logger.warning(f"Error analyzing error handling in {file_path}: {e}")
        
        return issues
    
    def _analyze_file_error_handling(self, file_path: str) -> List[QualityIssue]:
        """Analyze error handling in a single file"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
            
            # Find functions that might need error handling
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    issues.extend(self._analyze_function_error_handling(node, file_path, content))
        
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
        
        return issues
    
    def _analyze_function_error_handling(self, node: ast.FunctionDef, file_path: str, content: str) -> List[QualityIssue]:
        """Analyze error handling in a function"""
        issues = []
        
        # Check for risky operations without try-catch
        risky_operations = self._find_risky_operations(node)
        has_try_except = self._has_try_except_blocks(node)
        
        if risky_operations and not has_try_except:
            issues.append(QualityIssue(
                type="missing_error_handling",
                severity="medium",
                file_path=file_path,
                line_number=node.lineno,
                description=f"Function '{node.name}' contains risky operations but lacks error handling",
                recommendation="Add try-except blocks to handle potential exceptions",
                category="error_handling"
            ))
        
        # Check for bare except clauses
        for child in ast.walk(node):
            if isinstance(child, ast.ExceptHandler) and child.type is None:
                issues.append(QualityIssue(
                    type="bare_except",
                    severity="medium",
                    file_path=file_path,
                    line_number=child.lineno,
                    description="Bare except clause catches all exceptions",
                    recommendation="Specify specific exception types to catch",
                    category="error_handling",
                    auto_fixable=True
                ))
        
        return issues
    
    def _find_risky_operations(self, node: ast.FunctionDef) -> List[str]:
        """Find operations that commonly raise exceptions"""
        risky_ops = []
        
        for child in ast.walk(node):
            # File operations
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                if child.func.id in ['open', 'read', 'write']:
                    risky_ops.append('file_operation')
            
            # Network operations
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                if child.func.attr in ['get', 'post', 'put', 'delete', 'request']:
                    risky_ops.append('network_operation')
            
            # Database operations
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                if child.func.attr in ['execute', 'query', 'commit', 'rollback']:
                    risky_ops.append('database_operation')
        
        return risky_ops
    
    def _has_try_except_blocks(self, node: ast.FunctionDef) -> bool:
        """Check if function has try-except blocks"""
        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                return True
        return False

class DocumentationAnalyzer:
    """Analyzes documentation coverage and identifies gaps"""
    
    def __init__(self):
        self.gaps: List[DocumentationGap] = []
    
    def analyze_documentation(self, directory: str) -> List[DocumentationGap]:
        """Analyze documentation coverage in Python files"""
        gaps = []
        
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.pytest_cache', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        gaps.extend(self._analyze_file_documentation(file_path))
                    except Exception as e:
                        logger.warning(f"Error analyzing documentation in {file_path}: {e}")
        
        return gaps
    
    def _analyze_file_documentation(self, file_path: str) -> List[DocumentationGap]:
        """Analyze documentation in a single file"""
        gaps = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
            
            # Check module docstring
            if not ast.get_docstring(tree):
                gaps.append(DocumentationGap(
                    file_path=file_path,
                    function_name=None,
                    class_name=None,
                    gap_type="missing_module_docstring",
                    description="Module is missing a docstring",
                    recommendation="Add a module-level docstring describing the module's purpose"
                ))
            
            # Analyze functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    gaps.extend(self._analyze_function_documentation(node, file_path))
                elif isinstance(node, ast.ClassDef):
                    gaps.extend(self._analyze_class_documentation(node, file_path))
        
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
        
        return gaps
    
    def _analyze_function_documentation(self, node: ast.FunctionDef, file_path: str) -> List[DocumentationGap]:
        """Analyze function documentation"""
        gaps = []
        
        # Skip private functions and test functions for docstring requirements
        if node.name.startswith('_') or node.name.startswith('test_'):
            return gaps
        
        docstring = ast.get_docstring(node)
        
        if not docstring:
            gaps.append(DocumentationGap(
                file_path=file_path,
                function_name=node.name,
                class_name=None,
                gap_type="missing_docstring",
                description=f"Function '{node.name}' is missing a docstring",
                recommendation="Add a docstring describing the function's purpose, parameters, and return value"
            ))
        else:
            # Check docstring quality
            if len(docstring.split()) < 5:
                gaps.append(DocumentationGap(
                    file_path=file_path,
                    function_name=node.name,
                    class_name=None,
                    gap_type="incomplete_docstring",
                    description=f"Function '{node.name}' has a very brief docstring",
                    recommendation="Expand the docstring to include parameter descriptions and return value"
                ))
        
        # Check for type hints
        if not self._has_type_hints(node):
            gaps.append(DocumentationGap(
                file_path=file_path,
                function_name=node.name,
                class_name=None,
                gap_type="missing_type_hints",
                description=f"Function '{node.name}' is missing type hints",
                recommendation="Add type hints for parameters and return value"
            ))
        
        return gaps
    
    def _analyze_class_documentation(self, node: ast.ClassDef, file_path: str) -> List[DocumentationGap]:
        """Analyze class documentation"""
        gaps = []
        
        docstring = ast.get_docstring(node)
        
        if not docstring:
            gaps.append(DocumentationGap(
                file_path=file_path,
                function_name=None,
                class_name=node.name,
                gap_type="missing_docstring",
                description=f"Class '{node.name}' is missing a docstring",
                recommendation="Add a docstring describing the class's purpose and usage"
            ))
        
        return gaps
    
    def _has_type_hints(self, node: ast.FunctionDef) -> bool:
        """Check if function has type hints"""
        # Check return annotation
        if node.returns:
            return True
        
        # Check parameter annotations
        for arg in node.args.args:
            if arg.annotation:
                return True
        
        return False

class CodeQualityAnalyzer:
    """Main analyzer that coordinates all quality analysis components"""
    
    def __init__(self):
        self.structure_analyzer = CodeStructureAnalyzer()
        self.dependency_analyzer = DependencyAnalyzer()
        self.error_handling_analyzer = ErrorHandlingAnalyzer()
        self.documentation_analyzer = DocumentationAnalyzer()
    
    def analyze_codebase(self, root_directory: str = ".") -> Dict[str, Any]:
        """Perform comprehensive code quality analysis"""
        logger.info("Starting comprehensive code quality analysis...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "root_directory": os.path.abspath(root_directory),
            "analysis_summary": {},
            "code_structure_issues": [],
            "dependency_issues": [],
            "error_handling_issues": [],
            "documentation_gaps": [],
            "recommendations": []
        }
        
        try:
            # Analyze code structure
            logger.info("Analyzing code structure...")
            structure_issues = self.structure_analyzer.analyze_python_files(root_directory)
            results["code_structure_issues"] = [asdict(issue) for issue in structure_issues]
            
            # Analyze dependencies
            logger.info("Analyzing dependencies...")
            req_files = self._find_requirements_files(root_directory)
            package_files = self._find_package_json_files(root_directory)
            
            dependency_issues = []
            dependency_issues.extend(self.dependency_analyzer.analyze_python_dependencies(req_files))
            dependency_issues.extend(self.dependency_analyzer.analyze_node_dependencies(package_files))
            results["dependency_issues"] = [asdict(issue) for issue in dependency_issues]
            
            # Analyze error handling
            logger.info("Analyzing error handling...")
            error_handling_issues = self.error_handling_analyzer.analyze_error_handling(root_directory)
            results["error_handling_issues"] = [asdict(issue) for issue in error_handling_issues]
            
            # Analyze documentation
            logger.info("Analyzing documentation...")
            documentation_gaps = self.documentation_analyzer.analyze_documentation(root_directory)
            results["documentation_gaps"] = [asdict(gap) for gap in documentation_gaps]
            
            # Generate summary
            results["analysis_summary"] = self._generate_summary(
                structure_issues, dependency_issues, error_handling_issues, documentation_gaps
            )
            
            # Generate recommendations
            results["recommendations"] = self._generate_recommendations(
                structure_issues, dependency_issues, error_handling_issues, documentation_gaps
            )
            
            logger.info("Code quality analysis completed successfully")
            
        except Exception as e:
            logger.error(f"Error during code quality analysis: {e}")
            results["error"] = str(e)
        
        return results
    
    def _find_requirements_files(self, root_directory: str) -> List[str]:
        """Find all requirements files in the project"""
        req_files = []
        common_names = ['requirements.txt', 'requirements-dev.txt', 'dev-requirements.txt']
        
        for root, dirs, files in os.walk(root_directory):
            dirs[:] = [d for d in dirs if d not in ['venv', 'node_modules', '.git']]
            for file in files:
                if file in common_names or file.startswith('requirements'):
                    req_files.append(os.path.join(root, file))
        
        return req_files
    
    def _find_package_json_files(self, root_directory: str) -> List[str]:
        """Find all package.json files in the project"""
        package_files = []
        
        for root, dirs, files in os.walk(root_directory):
            dirs[:] = [d for d in dirs if d not in ['venv', 'node_modules', '.git']]
            if 'package.json' in files:
                package_files.append(os.path.join(root, 'package.json'))
        
        return package_files
    
    def _generate_summary(self, structure_issues: List[QualityIssue], 
                         dependency_issues: List[DependencyIssue],
                         error_handling_issues: List[QualityIssue],
                         documentation_gaps: List[DocumentationGap]) -> Dict[str, Any]:
        """Generate analysis summary"""
        total_issues = len(structure_issues) + len(dependency_issues) + len(error_handling_issues) + len(documentation_gaps)
        
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for issue in structure_issues + error_handling_issues:
            severity_counts[issue.severity] += 1
        
        return {
            "total_issues": total_issues,
            "code_structure_issues": len(structure_issues),
            "dependency_issues": len(dependency_issues),
            "error_handling_issues": len(error_handling_issues),
            "documentation_gaps": len(documentation_gaps),
            "severity_breakdown": severity_counts,
            "auto_fixable_issues": sum(1 for issue in structure_issues + error_handling_issues if issue.auto_fixable)
        }
    
    def _generate_recommendations(self, structure_issues: List[QualityIssue],
                                dependency_issues: List[DependencyIssue],
                                error_handling_issues: List[QualityIssue],
                                documentation_gaps: List[DocumentationGap]) -> List[str]:
        """Generate high-level recommendations"""
        recommendations = []
        
        # Critical issues first
        critical_issues = [issue for issue in structure_issues + error_handling_issues if issue.severity == "critical"]
        if critical_issues:
            recommendations.append(f"Address {len(critical_issues)} critical issues immediately to ensure code functionality")
        
        # Documentation gaps
        if len(documentation_gaps) > 10:
            recommendations.append("Implement a documentation standard and gradually improve documentation coverage")
        
        # Dependency issues
        if len(dependency_issues) > 5:
            recommendations.append("Review and update dependencies regularly to maintain security and compatibility")
        
        # Error handling
        error_handling_count = len(error_handling_issues)
        if error_handling_count > 5:
            recommendations.append("Implement comprehensive error handling patterns across the codebase")
        
        # Code structure
        structure_count = len(structure_issues)
        if structure_count > 10:
            recommendations.append("Refactor large functions and classes to improve maintainability")
        
        return recommendations

def main():
    """Main function to run code quality analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze code quality and technical debt")
    parser.add_argument("--directory", "-d", default=".", help="Directory to analyze")
    parser.add_argument("--output", "-o", help="Output file for results (JSON)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    analyzer = CodeQualityAnalyzer()
    results = analyzer.analyze_codebase(args.directory)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()