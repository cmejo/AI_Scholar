#!/usr/bin/env python3
"""
Enhanced Python Backend Code Analysis Tool
Implements comprehensive analysis for syntax errors, import issues, type inconsistencies,
dependency vulnerabilities, database queries, and service integration patterns.
"""

import ast
import json
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
import importlib.util
import sqlite3

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Optional imports - gracefully handle missing dependencies
try:
    import sqlparse
    from sqlparse import sql, tokens
    HAS_SQLPARSE = True
except ImportError:
    HAS_SQLPARSE = False
    logger.warning("sqlparse not available - SQL analysis will be limited")

try:
    import safety
    HAS_SAFETY = True
except ImportError:
    HAS_SAFETY = False
    logger.warning("safety not available - vulnerability scanning will be limited")


class IssueType(Enum):
    SYNTAX_ERROR = "syntax_error"
    TYPE_ERROR = "type_error"
    IMPORT_ERROR = "import_error"
    DEPENDENCY_VULNERABILITY = "dependency_vulnerability"
    SQL_SYNTAX_ERROR = "sql_syntax_error"
    SQL_PERFORMANCE_ISSUE = "sql_performance_issue"
    SERVICE_INTEGRATION_ERROR = "service_integration_error"
    STYLE_ISSUE = "style_issue"
    SECURITY_VULNERABILITY = "security_vulnerability"


class IssueSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class AnalysisIssue:
    id: str
    type: IssueType
    severity: IssueSeverity
    file_path: str
    line_number: Optional[int]
    column_number: Optional[int]
    description: str
    recommendation: str
    ubuntu_specific: bool
    auto_fixable: bool
    tool: str
    code_snippet: Optional[str] = None
    related_issues: List[str] = None

    def __post_init__(self):
        if self.related_issues is None:
            self.related_issues = []


@dataclass
class AnalysisResult:
    tool_name: str
    success: bool
    issues: List[AnalysisIssue]
    execution_time: float
    files_analyzed: int
    error_message: Optional[str] = None


class PythonBackendAnalyzer:
    """Enhanced Python backend code analyzer with comprehensive error detection."""
    
    def __init__(self, backend_path: Path):
        self.backend_path = backend_path
        self.issue_counter = 0
        self.python_files: List[Path] = []
        self.service_files: List[Path] = []
        self.api_files: List[Path] = []
        self.model_files: List[Path] = []
        self.sql_patterns: List[str] = []
        
        self._discover_files()
        self._load_sql_patterns()
    
    def generate_issue_id(self) -> str:
        """Generate unique issue ID."""
        self.issue_counter += 1
        return f"PY_{self.issue_counter:04d}"
    
    def _discover_files(self):
        """Discover and categorize Python files in the backend."""
        for pattern in ["**/*.py"]:
            for file_path in self.backend_path.glob(pattern):
                if file_path.is_file() and not self._should_skip_file(file_path):
                    self.python_files.append(file_path)
                    
                    # Categorize files
                    if "services" in str(file_path):
                        self.service_files.append(file_path)
                    elif "api" in str(file_path):
                        self.api_files.append(file_path)
                    elif "models" in str(file_path):
                        self.model_files.append(file_path)
        
        logger.info(f"Discovered {len(self.python_files)} Python files")
        logger.info(f"  - Services: {len(self.service_files)}")
        logger.info(f"  - API endpoints: {len(self.api_files)}")
        logger.info(f"  - Models: {len(self.model_files)}")
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during analysis."""
        skip_patterns = [
            "__pycache__",
            ".pyc",
            "venv",
            ".venv",
            "test_",
            ".pytest_cache",
            ".mypy_cache"
        ]
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _load_sql_patterns(self):
        """Load common SQL patterns for analysis."""
        self.sql_patterns = [
            r"SELECT\s+\*\s+FROM",  # SELECT * queries
            r"WHERE\s+\w+\s*=\s*['\"].*['\"]",  # Potential SQL injection
            r"ORDER\s+BY\s+\w+\s+(?:ASC|DESC)?(?:\s*,\s*\w+\s+(?:ASC|DESC)?)*\s*$",  # ORDER BY without LIMIT
            r"INSERT\s+INTO\s+\w+\s*\([^)]*\)\s*VALUES",  # INSERT statements
            r"UPDATE\s+\w+\s+SET",  # UPDATE statements
            r"DELETE\s+FROM\s+\w+",  # DELETE statements
        ]
    
    def analyze_syntax_and_imports(self) -> AnalysisResult:
        """Analyze Python files for syntax errors and import issues."""
        start_time = time.time()
        issues = []
        files_analyzed = 0
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                files_analyzed += 1
                
                # Check syntax
                syntax_issues = self._check_syntax(file_path, content)
                issues.extend(syntax_issues)
                
                # Check imports
                import_issues = self._check_imports(file_path, content)
                issues.extend(import_issues)
                
                # Check type annotations
                type_issues = self._check_type_annotations(file_path, content)
                issues.extend(type_issues)
                
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
                issue = AnalysisIssue(
                    id=self.generate_issue_id(),
                    type=IssueType.SYNTAX_ERROR,
                    severity=IssueSeverity.HIGH,
                    file_path=str(file_path),
                    line_number=None,
                    column_number=None,
                    description=f"Failed to analyze file: {e}",
                    recommendation="Check file encoding and syntax",
                    ubuntu_specific=False,
                    auto_fixable=False,
                    tool="syntax_analyzer"
                )
                issues.append(issue)
        
        execution_time = time.time() - start_time
        return AnalysisResult(
            "syntax_and_imports",
            True,
            issues,
            execution_time,
            files_analyzed
        )
    
    def _check_syntax(self, file_path: Path, content: str) -> List[AnalysisIssue]:
        """Check Python syntax errors."""
        issues = []
        
        try:
            ast.parse(content)
        except SyntaxError as e:
            issue = AnalysisIssue(
                id=self.generate_issue_id(),
                type=IssueType.SYNTAX_ERROR,
                severity=IssueSeverity.CRITICAL,
                file_path=str(file_path),
                line_number=e.lineno,
                column_number=e.offset,
                description=f"Syntax error: {e.msg}",
                recommendation="Fix Python syntax error",
                ubuntu_specific=False,
                auto_fixable=False,
                tool="ast_parser",
                code_snippet=self._get_code_snippet(content, e.lineno)
            )
            issues.append(issue)
        except Exception as e:
            issue = AnalysisIssue(
                id=self.generate_issue_id(),
                type=IssueType.SYNTAX_ERROR,
                severity=IssueSeverity.HIGH,
                file_path=str(file_path),
                line_number=None,
                column_number=None,
                description=f"Parse error: {e}",
                recommendation="Check file structure and syntax",
                ubuntu_specific=False,
                auto_fixable=False,
                tool="ast_parser"
            )
            issues.append(issue)
        
        return issues
    
    def _check_imports(self, file_path: Path, content: str) -> List[AnalysisIssue]:
        """Check for import issues."""
        issues = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        import_issues = self._validate_import(file_path, alias.name, node.lineno)
                        issues.extend(import_issues)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        import_issues = self._validate_import(file_path, node.module, node.lineno)
                        issues.extend(import_issues)
                        
                        # Check for relative imports
                        if node.level > 0:
                            issue = AnalysisIssue(
                                id=self.generate_issue_id(),
                                type=IssueType.IMPORT_ERROR,
                                severity=IssueSeverity.LOW,
                                file_path=str(file_path),
                                line_number=node.lineno,
                                column_number=None,
                                description=f"Relative import detected: {node.module}",
                                recommendation="Consider using absolute imports for better clarity",
                                ubuntu_specific=False,
                                auto_fixable=False,
                                tool="import_analyzer"
                            )
                            issues.append(issue)
        
        except Exception as e:
            logger.error(f"Error checking imports in {file_path}: {e}")
        
        return issues
    
    def _validate_import(self, file_path: Path, module_name: str, line_number: int) -> List[AnalysisIssue]:
        """Validate if an import is available."""
        issues = []
        
        # Skip standard library and common third-party modules
        skip_modules = {
            'os', 'sys', 'json', 'time', 'datetime', 'pathlib', 'typing',
            'fastapi', 'pydantic', 'sqlalchemy', 'redis', 'requests',
            'numpy', 'pandas', 'pytest', 'logging', 'asyncio', 'uuid',
            'hashlib', 'base64', 'urllib', 'http', 'email', 'collections'
        }
        
        if module_name.split('.')[0] in skip_modules:
            return issues
        
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                issue = AnalysisIssue(
                    id=self.generate_issue_id(),
                    type=IssueType.IMPORT_ERROR,
                    severity=IssueSeverity.HIGH,
                    file_path=str(file_path),
                    line_number=line_number,
                    column_number=None,
                    description=f"Module not found: {module_name}",
                    recommendation=f"Install missing module or check import path: {module_name}",
                    ubuntu_specific=True,
                    auto_fixable=False,
                    tool="import_validator"
                )
                issues.append(issue)
        except (ImportError, ModuleNotFoundError, ValueError):
            # Some modules might not be importable in the analysis environment
            pass
        except Exception as e:
            logger.debug(f"Could not validate import {module_name}: {e}")
        
        return issues
    
    def _check_type_annotations(self, file_path: Path, content: str) -> List[AnalysisIssue]:
        """Check for type annotation issues."""
        issues = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for missing return type annotation
                    if node.returns is None and not node.name.startswith('_'):
                        issue = AnalysisIssue(
                            id=self.generate_issue_id(),
                            type=IssueType.TYPE_ERROR,
                            severity=IssueSeverity.LOW,
                            file_path=str(file_path),
                            line_number=node.lineno,
                            column_number=None,
                            description=f"Function '{node.name}' missing return type annotation",
                            recommendation="Add return type annotation for better type safety",
                            ubuntu_specific=False,
                            auto_fixable=False,
                            tool="type_checker"
                        )
                        issues.append(issue)
                    
                    # Check for missing parameter type annotations
                    for arg in node.args.args:
                        if arg.annotation is None and arg.arg != 'self':
                            issue = AnalysisIssue(
                                id=self.generate_issue_id(),
                                type=IssueType.TYPE_ERROR,
                                severity=IssueSeverity.LOW,
                                file_path=str(file_path),
                                line_number=node.lineno,
                                column_number=None,
                                description=f"Parameter '{arg.arg}' in function '{node.name}' missing type annotation",
                                recommendation="Add type annotation for better type safety",
                                ubuntu_specific=False,
                                auto_fixable=False,
                                tool="type_checker"
                            )
                            issues.append(issue)
        
        except Exception as e:
            logger.error(f"Error checking type annotations in {file_path}: {e}")
        
        return issues
    
    def analyze_dependencies(self) -> AnalysisResult:
        """Analyze dependencies for vulnerabilities using safety and pip-audit."""
        start_time = time.time()
        issues = []
        
        # Run safety check
        safety_issues = self._run_safety_check()
        issues.extend(safety_issues)
        
        # Run pip-audit check
        pip_audit_issues = self._run_pip_audit()
        issues.extend(pip_audit_issues)
        
        # Check requirements files
        req_issues = self._check_requirements_files()
        issues.extend(req_issues)
        
        execution_time = time.time() - start_time
        return AnalysisResult(
            "dependency_analyzer",
            True,
            issues,
            execution_time,
            2  # requirements.txt and requirements-dev.txt
        )
    
    def _run_safety_check(self) -> List[AnalysisIssue]:
        """Run safety vulnerability scanner."""
        issues = []
        
        try:
            result = subprocess.run([
                "python", "-m", "safety", "check", "--json"
            ], cwd=self.backend_path, capture_output=True, text=True, timeout=120)
            
            if result.stdout:
                try:
                    safety_data = json.loads(result.stdout)
                    for vuln in safety_data:
                        issue = AnalysisIssue(
                            id=self.generate_issue_id(),
                            type=IssueType.DEPENDENCY_VULNERABILITY,
                            severity=self._map_safety_severity(vuln.get('vulnerability_id', '')),
                            file_path="requirements.txt",
                            line_number=None,
                            column_number=None,
                            description=f"Vulnerability in {vuln.get('package_name', 'unknown')}: {vuln.get('advisory', '')}",
                            recommendation=f"Update {vuln.get('package_name', 'package')} to version {vuln.get('analyzed_version', 'latest')} or higher",
                            ubuntu_specific=False,
                            auto_fixable=True,
                            tool="safety"
                        )
                        issues.append(issue)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse safety JSON output")
        
        except subprocess.TimeoutExpired:
            logger.warning("Safety check timed out")
        except Exception as e:
            logger.error(f"Safety check failed: {e}")
        
        return issues
    
    def _run_pip_audit(self) -> List[AnalysisIssue]:
        """Run pip-audit vulnerability scanner."""
        issues = []
        
        try:
            result = subprocess.run([
                "python", "-m", "pip_audit", "--format", "json"
            ], cwd=self.backend_path, capture_output=True, text=True, timeout=120)
            
            if result.stdout:
                try:
                    audit_data = json.loads(result.stdout)
                    for vuln in audit_data.get('vulnerabilities', []):
                        issue = AnalysisIssue(
                            id=self.generate_issue_id(),
                            type=IssueType.DEPENDENCY_VULNERABILITY,
                            severity=IssueSeverity.HIGH,
                            file_path="requirements.txt",
                            line_number=None,
                            column_number=None,
                            description=f"Vulnerability in {vuln.get('package', 'unknown')}: {vuln.get('id', '')}",
                            recommendation=f"Update package to fix vulnerability: {vuln.get('fix_versions', [])}",
                            ubuntu_specific=False,
                            auto_fixable=True,
                            tool="pip_audit"
                        )
                        issues.append(issue)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse pip-audit JSON output")
        
        except subprocess.TimeoutExpired:
            logger.warning("Pip-audit check timed out")
        except Exception as e:
            logger.error(f"Pip-audit check failed: {e}")
        
        return issues
    
    def _check_requirements_files(self) -> List[AnalysisIssue]:
        """Check requirements files for issues."""
        issues = []
        
        req_files = ["requirements.txt", "requirements-dev.txt"]
        
        for req_file in req_files:
            req_path = self.backend_path / req_file
            if req_path.exists():
                try:
                    with open(req_path, 'r') as f:
                        lines = f.readlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Check for unpinned versions
                            if '==' not in line and '>=' not in line and '~=' not in line:
                                issue = AnalysisIssue(
                                    id=self.generate_issue_id(),
                                    type=IssueType.DEPENDENCY_VULNERABILITY,
                                    severity=IssueSeverity.MEDIUM,
                                    file_path=str(req_path),
                                    line_number=line_num,
                                    column_number=None,
                                    description=f"Unpinned dependency: {line}",
                                    recommendation="Pin dependency versions for reproducible builds",
                                    ubuntu_specific=False,
                                    auto_fixable=True,
                                    tool="requirements_checker"
                                )
                                issues.append(issue)
                
                except Exception as e:
                    logger.error(f"Error checking {req_file}: {e}")
        
        return issues
    
    def analyze_database_queries(self) -> AnalysisResult:
        """Analyze SQL queries for syntax errors and performance issues."""
        start_time = time.time()
        issues = []
        files_analyzed = 0
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                files_analyzed += 1
                
                # Find SQL queries in the file
                sql_issues = self._analyze_sql_in_file(file_path, content)
                issues.extend(sql_issues)
                
            except Exception as e:
                logger.error(f"Error analyzing SQL in {file_path}: {e}")
        
        execution_time = time.time() - start_time
        return AnalysisResult(
            "database_query_analyzer",
            True,
            issues,
            execution_time,
            files_analyzed
        )
    
    def _analyze_sql_in_file(self, file_path: Path, content: str) -> List[AnalysisIssue]:
        """Analyze SQL queries found in a Python file."""
        issues = []
        
        # Find SQL queries in strings
        sql_patterns = [
            r'"""(.*?SELECT.*?)"""',
            r"'''(.*?SELECT.*?)'''",
            r'"(SELECT.*?)"',
            r"'(SELECT.*?)'",
            r'"""(.*?INSERT.*?)"""',
            r"'''(.*?INSERT.*?)'''",
            r'"(INSERT.*?)"',
            r"'(INSERT.*?)'",
            r'"""(.*?UPDATE.*?)"""',
            r"'''(.*?UPDATE.*?)'''",
            r'"(UPDATE.*?)"',
            r"'(UPDATE.*?)'",
            r'"""(.*?DELETE.*?)"""',
            r"'''(.*?DELETE.*?)'''",
            r'"(DELETE.*?)"',
            r"'(DELETE.*?)'"
        ]
        
        for pattern in sql_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                sql_query = match.group(1).strip()
                line_number = content[:match.start()].count('\n') + 1
                
                # Analyze the SQL query
                query_issues = self._analyze_sql_query(file_path, sql_query, line_number)
                issues.extend(query_issues)
        
        return issues
    
    def _analyze_sql_query(self, file_path: Path, sql_query: str, line_number: int) -> List[AnalysisIssue]:
        """Analyze a specific SQL query for issues."""
        issues = []
        
        # Basic SQL analysis without sqlparse
        if not HAS_SQLPARSE:
            # Simple regex-based analysis
            if re.search(r'SELECT\s+\*', sql_query, re.IGNORECASE):
                issue = AnalysisIssue(
                    id=self.generate_issue_id(),
                    type=IssueType.SQL_PERFORMANCE_ISSUE,
                    severity=IssueSeverity.MEDIUM,
                    file_path=str(file_path),
                    line_number=line_number,
                    column_number=None,
                    description="SELECT * query detected",
                    recommendation="Specify explicit column names instead of using SELECT *",
                    ubuntu_specific=False,
                    auto_fixable=False,
                    tool="sql_analyzer_basic",
                    code_snippet=sql_query[:100] + "..." if len(sql_query) > 100 else sql_query
                )
                issues.append(issue)
            
            # Check for unsafe UPDATE/DELETE
            if re.search(r'(UPDATE|DELETE).*(?!WHERE)', sql_query, re.IGNORECASE | re.DOTALL):
                if not re.search(r'WHERE', sql_query, re.IGNORECASE):
                    issue = AnalysisIssue(
                        id=self.generate_issue_id(),
                        type=IssueType.SQL_SYNTAX_ERROR,
                        severity=IssueSeverity.HIGH,
                        file_path=str(file_path),
                        line_number=line_number,
                        column_number=None,
                        description="UPDATE/DELETE without WHERE clause",
                        recommendation="Add WHERE clause to prevent unintended data modification",
                        ubuntu_specific=False,
                        auto_fixable=False,
                        tool="sql_analyzer_basic",
                        code_snippet=sql_query[:100] + "..." if len(sql_query) > 100 else sql_query
                    )
                    issues.append(issue)
            
            # Check for potential SQL injection
            if self._has_sql_injection_risk(sql_query):
                issue = AnalysisIssue(
                    id=self.generate_issue_id(),
                    type=IssueType.SECURITY_VULNERABILITY,
                    severity=IssueSeverity.CRITICAL,
                    file_path=str(file_path),
                    line_number=line_number,
                    column_number=None,
                    description="Potential SQL injection vulnerability",
                    recommendation="Use parameterized queries or prepared statements",
                    ubuntu_specific=False,
                    auto_fixable=False,
                    tool="sql_analyzer_basic",
                    code_snippet=sql_query[:100] + "..." if len(sql_query) > 100 else sql_query
                )
                issues.append(issue)
            
            return issues
        
        try:
            # Parse SQL query with sqlparse
            parsed = sqlparse.parse(sql_query)
            
            if not parsed:
                return issues
            
            statement = parsed[0]
            
            # Check for SELECT * queries
            if self._has_select_star(statement):
                issue = AnalysisIssue(
                    id=self.generate_issue_id(),
                    type=IssueType.SQL_PERFORMANCE_ISSUE,
                    severity=IssueSeverity.MEDIUM,
                    file_path=str(file_path),
                    line_number=line_number,
                    column_number=None,
                    description="SELECT * query detected",
                    recommendation="Specify explicit column names instead of using SELECT *",
                    ubuntu_specific=False,
                    auto_fixable=False,
                    tool="sql_analyzer",
                    code_snippet=sql_query[:100] + "..." if len(sql_query) > 100 else sql_query
                )
                issues.append(issue)
            
            # Check for missing WHERE clause in UPDATE/DELETE
            if self._is_unsafe_update_delete(statement):
                issue = AnalysisIssue(
                    id=self.generate_issue_id(),
                    type=IssueType.SQL_SYNTAX_ERROR,
                    severity=IssueSeverity.HIGH,
                    file_path=str(file_path),
                    line_number=line_number,
                    column_number=None,
                    description="UPDATE/DELETE without WHERE clause",
                    recommendation="Add WHERE clause to prevent unintended data modification",
                    ubuntu_specific=False,
                    auto_fixable=False,
                    tool="sql_analyzer",
                    code_snippet=sql_query[:100] + "..." if len(sql_query) > 100 else sql_query
                )
                issues.append(issue)
            
            # Check for potential SQL injection
            if self._has_sql_injection_risk(sql_query):
                issue = AnalysisIssue(
                    id=self.generate_issue_id(),
                    type=IssueType.SECURITY_VULNERABILITY,
                    severity=IssueSeverity.CRITICAL,
                    file_path=str(file_path),
                    line_number=line_number,
                    column_number=None,
                    description="Potential SQL injection vulnerability",
                    recommendation="Use parameterized queries or prepared statements",
                    ubuntu_specific=False,
                    auto_fixable=False,
                    tool="sql_analyzer",
                    code_snippet=sql_query[:100] + "..." if len(sql_query) > 100 else sql_query
                )
                issues.append(issue)
        
        except Exception as e:
            logger.debug(f"Error parsing SQL query: {e}")
        
        return issues
    
    def _has_select_star(self, statement) -> bool:
        """Check if statement contains SELECT *."""
        if not HAS_SQLPARSE:
            return False
        
        tokens_list = list(statement.flatten())
        for i, token in enumerate(tokens_list):
            if token.ttype is tokens.Keyword and token.value.upper() == 'SELECT':
                # Look for * in the next few tokens
                for j in range(i + 1, min(i + 5, len(tokens_list))):
                    if tokens_list[j].ttype is tokens.Wildcard:
                        return True
        return False
    
    def _is_unsafe_update_delete(self, statement) -> bool:
        """Check if UPDATE/DELETE statement lacks WHERE clause."""
        if not HAS_SQLPARSE:
            return False
        
        tokens_list = list(statement.flatten())
        has_update_delete = False
        has_where = False
        
        for token in tokens_list:
            if token.ttype is tokens.Keyword:
                if token.value.upper() in ['UPDATE', 'DELETE']:
                    has_update_delete = True
                elif token.value.upper() == 'WHERE':
                    has_where = True
        
        return has_update_delete and not has_where
    
    def _has_sql_injection_risk(self, sql_query: str) -> bool:
        """Check for potential SQL injection patterns."""
        injection_patterns = [
            r'%s',  # String formatting
            r'\+.*\+',  # String concatenation
            r'format\(',  # String format method
            r'f".*{.*}"',  # f-string with variables
            r"f'.*{.*}'"  # f-string with variables
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, sql_query):
                return True
        
        return False
    
    def analyze_service_integration(self) -> AnalysisResult:
        """Analyze service integration patterns and inter-service communication."""
        start_time = time.time()
        issues = []
        files_analyzed = 0
        
        # Analyze service files
        for file_path in self.service_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                files_analyzed += 1
                
                # Check service integration patterns
                integration_issues = self._analyze_service_integration(file_path, content)
                issues.extend(integration_issues)
                
            except Exception as e:
                logger.error(f"Error analyzing service integration in {file_path}: {e}")
        
        # Analyze API endpoint files
        for file_path in self.api_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                files_analyzed += 1
                
                # Check API integration patterns
                api_issues = self._analyze_api_integration(file_path, content)
                issues.extend(api_issues)
                
            except Exception as e:
                logger.error(f"Error analyzing API integration in {file_path}: {e}")
        
        execution_time = time.time() - start_time
        return AnalysisResult(
            "service_integration_analyzer",
            True,
            issues,
            execution_time,
            files_analyzed
        )
    
    def _analyze_service_integration(self, file_path: Path, content: str) -> List[AnalysisIssue]:
        """Analyze service integration patterns."""
        issues = []
        
        try:
            tree = ast.parse(content)
            
            # Check for proper error handling in service calls
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check for HTTP requests without error handling
                    if self._is_http_request_call(node):
                        if not self._has_error_handling(node, tree):
                            issue = AnalysisIssue(
                                id=self.generate_issue_id(),
                                type=IssueType.SERVICE_INTEGRATION_ERROR,
                                severity=IssueSeverity.MEDIUM,
                                file_path=str(file_path),
                                line_number=node.lineno,
                                column_number=None,
                                description="HTTP request without proper error handling",
                                recommendation="Add try-catch block for HTTP requests",
                                ubuntu_specific=False,
                                auto_fixable=False,
                                tool="service_integration_analyzer"
                            )
                            issues.append(issue)
                    
                    # Check for database calls without error handling
                    if self._is_database_call(node):
                        if not self._has_error_handling(node, tree):
                            issue = AnalysisIssue(
                                id=self.generate_issue_id(),
                                type=IssueType.SERVICE_INTEGRATION_ERROR,
                                severity=IssueSeverity.MEDIUM,
                                file_path=str(file_path),
                                line_number=node.lineno,
                                column_number=None,
                                description="Database call without proper error handling",
                                recommendation="Add try-catch block for database operations",
                                ubuntu_specific=False,
                                auto_fixable=False,
                                tool="service_integration_analyzer"
                            )
                            issues.append(issue)
        
        except Exception as e:
            logger.error(f"Error analyzing service integration: {e}")
        
        return issues
    
    def _analyze_api_integration(self, file_path: Path, content: str) -> List[AnalysisIssue]:
        """Analyze API integration patterns."""
        issues = []
        
        # Check for missing input validation
        if 'request' in content and 'validate' not in content:
            issue = AnalysisIssue(
                id=self.generate_issue_id(),
                type=IssueType.SERVICE_INTEGRATION_ERROR,
                severity=IssueSeverity.MEDIUM,
                file_path=str(file_path),
                line_number=None,
                column_number=None,
                description="API endpoint may lack input validation",
                recommendation="Add input validation for API endpoints",
                ubuntu_specific=False,
                auto_fixable=False,
                tool="api_integration_analyzer"
            )
            issues.append(issue)
        
        # Check for missing authentication
        if '@app.' in content and 'auth' not in content.lower():
            issue = AnalysisIssue(
                id=self.generate_issue_id(),
                type=IssueType.SERVICE_INTEGRATION_ERROR,
                severity=IssueSeverity.HIGH,
                file_path=str(file_path),
                line_number=None,
                column_number=None,
                description="API endpoint may lack authentication",
                recommendation="Add authentication middleware to API endpoints",
                ubuntu_specific=False,
                auto_fixable=False,
                tool="api_integration_analyzer"
            )
            issues.append(issue)
        
        return issues
    
    def _is_http_request_call(self, node: ast.Call) -> bool:
        """Check if node is an HTTP request call."""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return node.func.value.id in ['requests', 'httpx', 'aiohttp']
        elif isinstance(node.func, ast.Name):
            return node.func.id in ['get', 'post', 'put', 'delete', 'patch']
        return False
    
    def _is_database_call(self, node: ast.Call) -> bool:
        """Check if node is a database call."""
        if isinstance(node.func, ast.Attribute):
            return node.func.attr in ['execute', 'query', 'commit', 'rollback']
        return False
    
    def _has_error_handling(self, node: ast.Call, tree: ast.AST) -> bool:
        """Check if a call is wrapped in error handling."""
        # Simple heuristic: check if the call is within a try block
        for parent in ast.walk(tree):
            if isinstance(parent, ast.Try):
                for child in ast.walk(parent):
                    if child is node:
                        return True
        return False
    
    def _get_code_snippet(self, content: str, line_number: Optional[int], context: int = 2) -> Optional[str]:
        """Get code snippet around the specified line."""
        if line_number is None:
            return None
        
        lines = content.split('\n')
        start = max(0, line_number - context - 1)
        end = min(len(lines), line_number + context)
        
        snippet_lines = []
        for i in range(start, end):
            prefix = ">>> " if i == line_number - 1 else "    "
            snippet_lines.append(f"{prefix}{lines[i]}")
        
        return '\n'.join(snippet_lines)
    
    def _map_safety_severity(self, vuln_id: str) -> IssueSeverity:
        """Map safety vulnerability ID to severity."""
        # This is a simplified mapping - in practice, you'd use the actual severity data
        if 'critical' in vuln_id.lower():
            return IssueSeverity.CRITICAL
        elif 'high' in vuln_id.lower():
            return IssueSeverity.HIGH
        else:
            return IssueSeverity.MEDIUM
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete Python backend analysis."""
        logger.info("Starting Python backend analysis...")
        
        results = []
        
        # Syntax and import analysis
        logger.info("Analyzing syntax and imports...")
        results.append(self.analyze_syntax_and_imports())
        
        # Dependency vulnerability analysis
        logger.info("Analyzing dependencies...")
        results.append(self.analyze_dependencies())
        
        # Database query analysis
        logger.info("Analyzing database queries...")
        results.append(self.analyze_database_queries())
        
        # Service integration analysis
        logger.info("Analyzing service integration...")
        results.append(self.analyze_service_integration())
        
        # Generate summary
        total_issues = sum(len(result.issues) for result in results)
        total_files = sum(result.files_analyzed for result in results)
        
        summary = {
            "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "backend_path": str(self.backend_path),
            "total_python_files": len(self.python_files),
            "total_files_analyzed": total_files,
            "total_issues_found": total_issues,
            "results": [asdict(result) for result in results],
            "issue_breakdown": self._generate_issue_breakdown(results)
        }
        
        logger.info(f"Python backend analysis complete. Found {total_issues} issues across {total_files} files.")
        
        return summary
    
    def _generate_issue_breakdown(self, results: List[AnalysisResult]) -> Dict[str, int]:
        """Generate breakdown of issues by type and severity."""
        breakdown = {
            "by_type": {},
            "by_severity": {},
            "by_tool": {}
        }
        
        for result in results:
            for issue in result.issues:
                # By type
                issue_type = issue.type.value
                breakdown["by_type"][issue_type] = breakdown["by_type"].get(issue_type, 0) + 1
                
                # By severity
                severity = issue.severity.value
                breakdown["by_severity"][severity] = breakdown["by_severity"].get(severity, 0) + 1
                
                # By tool
                tool = issue.tool
                breakdown["by_tool"][tool] = breakdown["by_tool"].get(tool, 0) + 1
        
        return breakdown


def main():
    """Main function to run Python backend analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Python Backend Code Analyzer")
    parser.add_argument("--backend-path", type=Path, default=Path("backend"),
                       help="Path to backend directory")
    parser.add_argument("--output", type=Path, default=Path("python_backend_analysis.json"),
                       help="Output file for analysis results")
    
    args = parser.parse_args()
    
    if not args.backend_path.exists():
        logger.error(f"Backend path does not exist: {args.backend_path}")
        sys.exit(1)
    
    analyzer = PythonBackendAnalyzer(args.backend_path)
    results = analyzer.run_full_analysis()
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Analysis results saved to {args.output}")
    
    # Print summary
    print(f"\nPython Backend Analysis Summary:")
    print(f"Files analyzed: {results['total_files_analyzed']}")
    print(f"Issues found: {results['total_issues_found']}")
    print(f"\nIssue breakdown:")
    for category, breakdown in results['issue_breakdown'].items():
        print(f"  {category}:")
        for key, count in breakdown.items():
            print(f"    {key}: {count}")


if __name__ == "__main__":
    main()