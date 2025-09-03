#!/usr/bin/env python3
"""
Comprehensive Codebase Analysis Tool for Ubuntu Compatibility
Orchestrates all static analysis tools for the AI Scholar project.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class IssueType(Enum):
    SYNTAX_ERROR = "syntax_error"
    TYPE_ERROR = "type_error"
    IMPORT_ERROR = "import_error"
    CONFIGURATION_ERROR = "configuration_error"
    SECURITY_VULNERABILITY = "security_vulnerability"
    PERFORMANCE_ISSUE = "performance_issue"
    UBUNTU_COMPATIBILITY = "ubuntu_compatibility"
    DOCKER_ISSUE = "docker_issue"
    DEPENDENCY_ISSUE = "dependency_issue"
    STYLE_ISSUE = "style_issue"


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
    error_message: Optional[str] = None


class CodebaseAnalyzer:
    """Main analyzer class that orchestrates all analysis tools."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: List[AnalysisResult] = []
        self.issue_counter = 0
        
    def generate_issue_id(self) -> str:
        """Generate unique issue ID."""
        self.issue_counter += 1
        return f"ISSUE_{self.issue_counter:04d}"
    
    def run_command(self, command: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {' '.join(command)}")
            raise
        except Exception as e:
            logger.error(f"Command failed: {' '.join(command)}, Error: {e}")
            raise
    
    def analyze_python_backend(self) -> List[AnalysisResult]:
        """Run all Python analysis tools on the backend."""
        backend_path = self.project_root / "backend"
        if not backend_path.exists():
            logger.warning("Backend directory not found, skipping Python analysis")
            return []
        
        python_results = []
        
        # Flake8 analysis
        python_results.append(self._run_flake8(backend_path))
        
        # Black formatting check
        python_results.append(self._run_black_check(backend_path))
        
        # MyPy type checking
        python_results.append(self._run_mypy(backend_path))
        
        # Bandit security analysis
        python_results.append(self._run_bandit(backend_path))
        
        # Pylint analysis
        python_results.append(self._run_pylint(backend_path))
        
        return python_results
    
    def _run_flake8(self, backend_path: Path) -> AnalysisResult:
        """Run flake8 analysis."""
        start_time = time.time()
        issues = []
        
        try:
            result = self.run_command([
                "python", "-m", "flake8", ".", 
                "--config", "setup.cfg",
                "--format", "json"
            ], cwd=backend_path)
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                return AnalysisResult("flake8", True, [], execution_time)
            
            # Parse flake8 output (it doesn't have native JSON output, so we'll parse text)
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split(':', 4)
                    if len(parts) >= 4:
                        file_path = parts[0]
                        line_num = int(parts[1]) if parts[1].isdigit() else None
                        col_num = int(parts[2]) if parts[2].isdigit() else None
                        message = parts[3].strip() if len(parts) > 3 else "Unknown error"
                        
                        issue = AnalysisIssue(
                            id=self.generate_issue_id(),
                            type=IssueType.STYLE_ISSUE,
                            severity=IssueSeverity.LOW,
                            file_path=file_path,
                            line_number=line_num,
                            column_number=col_num,
                            description=f"Flake8: {message}",
                            recommendation="Fix code style issue according to PEP 8",
                            ubuntu_specific=False,
                            auto_fixable=True,
                            tool="flake8"
                        )
                        issues.append(issue)
            
            return AnalysisResult("flake8", True, issues, execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Flake8 analysis failed: {e}")
            return AnalysisResult("flake8", False, [], execution_time, str(e))
    
    def _run_black_check(self, backend_path: Path) -> AnalysisResult:
        """Run black formatting check."""
        start_time = time.time()
        issues = []
        
        try:
            result = self.run_command([
                "python", "-m", "black", "--check", "--diff", "."
            ], cwd=backend_path)
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                return AnalysisResult("black", True, [], execution_time)
            
            # Parse black output for formatting issues
            if result.stdout:
                issue = AnalysisIssue(
                    id=self.generate_issue_id(),
                    type=IssueType.STYLE_ISSUE,
                    severity=IssueSeverity.LOW,
                    file_path="multiple files",
                    line_number=None,
                    column_number=None,
                    description="Black: Code formatting issues detected",
                    recommendation="Run 'python -m black .' to auto-format code",
                    ubuntu_specific=False,
                    auto_fixable=True,
                    tool="black"
                )
                issues.append(issue)
            
            return AnalysisResult("black", True, issues, execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Black analysis failed: {e}")
            return AnalysisResult("black", False, [], execution_time, str(e))
    
    def _run_mypy(self, backend_path: Path) -> AnalysisResult:
        """Run MyPy type checking."""
        start_time = time.time()
        issues = []
        
        try:
            result = self.run_command([
                "python", "-m", "mypy", ".", "--json-report", "/tmp/mypy-report"
            ], cwd=backend_path)
            
            execution_time = time.time() - start_time
            
            # Parse MyPy output
            for line in result.stdout.strip().split('\n'):
                if line.strip() and ':' in line:
                    parts = line.split(':', 3)
                    if len(parts) >= 3:
                        file_path = parts[0]
                        line_num = int(parts[1]) if parts[1].isdigit() else None
                        message = parts[2].strip() if len(parts) > 2 else "Type error"
                        
                        issue = AnalysisIssue(
                            id=self.generate_issue_id(),
                            type=IssueType.TYPE_ERROR,
                            severity=IssueSeverity.MEDIUM,
                            file_path=file_path,
                            line_number=line_num,
                            column_number=None,
                            description=f"MyPy: {message}",
                            recommendation="Fix type annotations and type errors",
                            ubuntu_specific=False,
                            auto_fixable=False,
                            tool="mypy"
                        )
                        issues.append(issue)
            
            return AnalysisResult("mypy", True, issues, execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"MyPy analysis failed: {e}")
            return AnalysisResult("mypy", False, [], execution_time, str(e))
    
    def _run_bandit(self, backend_path: Path) -> AnalysisResult:
        """Run Bandit security analysis."""
        start_time = time.time()
        issues = []
        
        try:
            result = self.run_command([
                "python", "-m", "bandit", "-r", ".", "-f", "json"
            ], cwd=backend_path)
            
            execution_time = time.time() - start_time
            
            if result.stdout:
                try:
                    bandit_data = json.loads(result.stdout)
                    for result_item in bandit_data.get('results', []):
                        severity_map = {
                            'HIGH': IssueSeverity.HIGH,
                            'MEDIUM': IssueSeverity.MEDIUM,
                            'LOW': IssueSeverity.LOW
                        }
                        
                        issue = AnalysisIssue(
                            id=self.generate_issue_id(),
                            type=IssueType.SECURITY_VULNERABILITY,
                            severity=severity_map.get(result_item.get('issue_severity', 'LOW'), IssueSeverity.LOW),
                            file_path=result_item.get('filename', ''),
                            line_number=result_item.get('line_number'),
                            column_number=None,
                            description=f"Bandit: {result_item.get('issue_text', '')}",
                            recommendation=f"Security issue: {result_item.get('issue_text', '')}",
                            ubuntu_specific=False,
                            auto_fixable=False,
                            tool="bandit"
                        )
                        issues.append(issue)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Bandit JSON output")
            
            return AnalysisResult("bandit", True, issues, execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Bandit analysis failed: {e}")
            return AnalysisResult("bandit", False, [], execution_time, str(e))
    
    def _run_pylint(self, backend_path: Path) -> AnalysisResult:
        """Run Pylint analysis."""
        start_time = time.time()
        issues = []
        
        try:
            result = self.run_command([
                "python", "-m", "pylint", ".", "--output-format=json"
            ], cwd=backend_path)
            
            execution_time = time.time() - start_time
            
            if result.stdout:
                try:
                    pylint_data = json.loads(result.stdout)
                    for item in pylint_data:
                        severity_map = {
                            'error': IssueSeverity.HIGH,
                            'warning': IssueSeverity.MEDIUM,
                            'refactor': IssueSeverity.LOW,
                            'convention': IssueSeverity.LOW,
                            'info': IssueSeverity.INFO
                        }
                        
                        issue = AnalysisIssue(
                            id=self.generate_issue_id(),
                            type=IssueType.STYLE_ISSUE,
                            severity=severity_map.get(item.get('type', 'info'), IssueSeverity.INFO),
                            file_path=item.get('path', ''),
                            line_number=item.get('line'),
                            column_number=item.get('column'),
                            description=f"Pylint: {item.get('message', '')}",
                            recommendation=f"Code quality issue: {item.get('message', '')}",
                            ubuntu_specific=False,
                            auto_fixable=False,
                            tool="pylint"
                        )
                        issues.append(issue)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Pylint JSON output")
            
            return AnalysisResult("pylint", True, issues, execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Pylint analysis failed: {e}")
            return AnalysisResult("pylint", False, [], execution_time, str(e))
    
    def analyze_typescript_frontend(self) -> List[AnalysisResult]:
        """Run all TypeScript/React analysis tools on the frontend."""
        frontend_results = []
        
        # ESLint analysis
        frontend_results.append(self._run_eslint())
        
        # Prettier check
        frontend_results.append(self._run_prettier_check())
        
        # TypeScript compiler check
        frontend_results.append(self._run_typescript_check())
        
        return frontend_results
    
    def _run_eslint(self) -> AnalysisResult:
        """Run ESLint analysis."""
        start_time = time.time()
        issues = []
        
        try:
            result = self.run_command([
                "npm", "run", "lint", "--", "--format", "json"
            ])
            
            execution_time = time.time() - start_time
            
            if result.stdout:
                try:
                    eslint_data = json.loads(result.stdout)
                    for file_result in eslint_data:
                        for message in file_result.get('messages', []):
                            severity_map = {
                                2: IssueSeverity.HIGH,  # error
                                1: IssueSeverity.MEDIUM,  # warning
                                0: IssueSeverity.INFO  # info
                            }
                            
                            issue = AnalysisIssue(
                                id=self.generate_issue_id(),
                                type=IssueType.STYLE_ISSUE,
                                severity=severity_map.get(message.get('severity', 0), IssueSeverity.INFO),
                                file_path=file_result.get('filePath', ''),
                                line_number=message.get('line'),
                                column_number=message.get('column'),
                                description=f"ESLint: {message.get('message', '')}",
                                recommendation=f"Fix ESLint rule: {message.get('ruleId', '')}",
                                ubuntu_specific=False,
                                auto_fixable=message.get('fix') is not None,
                                tool="eslint"
                            )
                            issues.append(issue)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse ESLint JSON output")
            
            return AnalysisResult("eslint", True, issues, execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"ESLint analysis failed: {e}")
            return AnalysisResult("eslint", False, [], execution_time, str(e))
    
    def _run_prettier_check(self) -> AnalysisResult:
        """Run Prettier formatting check."""
        start_time = time.time()
        issues = []
        
        try:
            result = self.run_command([
                "npm", "run", "format:check"
            ])
            
            execution_time = time.time() - start_time
            
            if result.returncode != 0:
                issue = AnalysisIssue(
                    id=self.generate_issue_id(),
                    type=IssueType.STYLE_ISSUE,
                    severity=IssueSeverity.LOW,
                    file_path="multiple files",
                    line_number=None,
                    column_number=None,
                    description="Prettier: Code formatting issues detected",
                    recommendation="Run 'npm run format' to auto-format code",
                    ubuntu_specific=False,
                    auto_fixable=True,
                    tool="prettier"
                )
                issues.append(issue)
            
            return AnalysisResult("prettier", True, issues, execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Prettier analysis failed: {e}")
            return AnalysisResult("prettier", False, [], execution_time, str(e))
    
    def _run_typescript_check(self) -> AnalysisResult:
        """Run TypeScript compiler check."""
        start_time = time.time()
        issues = []
        
        try:
            result = self.run_command([
                "npm", "run", "type-check"
            ])
            
            execution_time = time.time() - start_time
            
            # Parse TypeScript compiler output
            for line in result.stderr.strip().split('\n'):
                if line.strip() and '(' in line and ')' in line:
                    # Parse TypeScript error format: file.ts(line,col): error TS####: message
                    parts = line.split(':', 2)
                    if len(parts) >= 2:
                        file_info = parts[0]
                        message = parts[1].strip() if len(parts) > 1 else "TypeScript error"
                        
                        # Extract file path and line/column
                        if '(' in file_info and ')' in file_info:
                            file_path = file_info.split('(')[0]
                            coords = file_info.split('(')[1].split(')')[0]
                            line_num = int(coords.split(',')[0]) if ',' in coords else None
                            col_num = int(coords.split(',')[1]) if ',' in coords and len(coords.split(',')) > 1 else None
                        else:
                            file_path = file_info
                            line_num = None
                            col_num = None
                        
                        issue = AnalysisIssue(
                            id=self.generate_issue_id(),
                            type=IssueType.TYPE_ERROR,
                            severity=IssueSeverity.HIGH,
                            file_path=file_path,
                            line_number=line_num,
                            column_number=col_num,
                            description=f"TypeScript: {message}",
                            recommendation="Fix TypeScript compilation error",
                            ubuntu_specific=False,
                            auto_fixable=False,
                            tool="typescript"
                        )
                        issues.append(issue)
            
            return AnalysisResult("typescript", True, issues, execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"TypeScript analysis failed: {e}")
            return AnalysisResult("typescript", False, [], execution_time, str(e))
    
    def analyze_docker_configs(self) -> List[AnalysisResult]:
        """Run Docker and configuration analysis tools."""
        docker_results = []
        
        # Hadolint for Dockerfiles
        docker_results.append(self._run_hadolint())
        
        # YAML lint for docker-compose files
        docker_results.append(self._run_yamllint())
        
        # Shellcheck for shell scripts
        docker_results.append(self._run_shellcheck())
        
        return docker_results
    
    def _run_hadolint(self) -> AnalysisResult:
        """Run Hadolint on Dockerfiles."""
        start_time = time.time()
        issues = []
        
        try:
            # Find all Dockerfiles
            dockerfiles = list(self.project_root.glob("**/Dockerfile*"))
            
            for dockerfile in dockerfiles:
                result = self.run_command([
                    "hadolint", "--format", "json", str(dockerfile)
                ])
                
                if result.stdout:
                    try:
                        hadolint_data = json.loads(result.stdout)
                        for item in hadolint_data:
                            severity_map = {
                                'error': IssueSeverity.HIGH,
                                'warning': IssueSeverity.MEDIUM,
                                'info': IssueSeverity.LOW,
                                'style': IssueSeverity.LOW
                            }
                            
                            issue = AnalysisIssue(
                                id=self.generate_issue_id(),
                                type=IssueType.DOCKER_ISSUE,
                                severity=severity_map.get(item.get('level', 'info'), IssueSeverity.INFO),
                                file_path=str(dockerfile),
                                line_number=item.get('line'),
                                column_number=item.get('column'),
                                description=f"Hadolint: {item.get('message', '')}",
                                recommendation=f"Docker best practice: {item.get('message', '')}",
                                ubuntu_specific=True,
                                auto_fixable=False,
                                tool="hadolint"
                            )
                            issues.append(issue)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse Hadolint JSON output for {dockerfile}")
            
            execution_time = time.time() - start_time
            return AnalysisResult("hadolint", True, issues, execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Hadolint analysis failed: {e}")
            return AnalysisResult("hadolint", False, [], execution_time, str(e))
    
    def _run_yamllint(self) -> AnalysisResult:
        """Run YAML lint on configuration files."""
        start_time = time.time()
        issues = []
        
        try:
            # Find all YAML files
            yaml_files = list(self.project_root.glob("**/*.yml")) + list(self.project_root.glob("**/*.yaml"))
            
            for yaml_file in yaml_files:
                result = self.run_command([
                    "yamllint", "-f", "parsable", str(yaml_file)
                ])
                
                # Parse yamllint output
                for line in result.stdout.strip().split('\n'):
                    if line.strip() and ':' in line:
                        parts = line.split(':', 4)
                        if len(parts) >= 4:
                            file_path = parts[0]
                            line_num = int(parts[1]) if parts[1].isdigit() else None
                            col_num = int(parts[2]) if parts[2].isdigit() else None
                            message = parts[3].strip() if len(parts) > 3 else "YAML error"
                            
                            issue = AnalysisIssue(
                                id=self.generate_issue_id(),
                                type=IssueType.CONFIGURATION_ERROR,
                                severity=IssueSeverity.MEDIUM,
                                file_path=file_path,
                                line_number=line_num,
                                column_number=col_num,
                                description=f"YAML Lint: {message}",
                                recommendation="Fix YAML syntax and formatting",
                                ubuntu_specific=False,
                                auto_fixable=True,
                                tool="yamllint"
                            )
                            issues.append(issue)
            
            execution_time = time.time() - start_time
            return AnalysisResult("yamllint", True, issues, execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"YAML lint analysis failed: {e}")
            return AnalysisResult("yamllint", False, [], execution_time, str(e))
    
    def _run_shellcheck(self) -> AnalysisResult:
        """Run Shellcheck on shell scripts."""
        start_time = time.time()
        issues = []
        
        try:
            # Find all shell scripts
            shell_files = list(self.project_root.glob("**/*.sh"))
            
            for shell_file in shell_files:
                result = self.run_command([
                    "shellcheck", "--format", "json", str(shell_file)
                ])
                
                if result.stdout:
                    try:
                        shellcheck_data = json.loads(result.stdout)
                        for item in shellcheck_data:
                            severity_map = {
                                'error': IssueSeverity.HIGH,
                                'warning': IssueSeverity.MEDIUM,
                                'info': IssueSeverity.LOW,
                                'style': IssueSeverity.LOW
                            }
                            
                            issue = AnalysisIssue(
                                id=self.generate_issue_id(),
                                type=IssueType.UBUNTU_COMPATIBILITY,
                                severity=severity_map.get(item.get('level', 'info'), IssueSeverity.INFO),
                                file_path=str(shell_file),
                                line_number=item.get('line'),
                                column_number=item.get('column'),
                                description=f"Shellcheck: {item.get('message', '')}",
                                recommendation=f"Shell script issue: {item.get('message', '')}",
                                ubuntu_specific=True,
                                auto_fixable=False,
                                tool="shellcheck"
                            )
                            issues.append(issue)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse Shellcheck JSON output for {shell_file}")
            
            execution_time = time.time() - start_time
            return AnalysisResult("shellcheck", True, issues, execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Shellcheck analysis failed: {e}")
            return AnalysisResult("shellcheck", False, [], execution_time, str(e))
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete analysis and return results."""
        logger.info("Starting comprehensive codebase analysis...")
        
        all_results = []
        
        # Python backend analysis
        logger.info("Analyzing Python backend...")
        all_results.extend(self.analyze_python_backend())
        
        # TypeScript frontend analysis
        logger.info("Analyzing TypeScript frontend...")
        all_results.extend(self.analyze_typescript_frontend())
        
        # Docker and configuration analysis
        logger.info("Analyzing Docker and configuration files...")
        all_results.extend(self.analyze_docker_configs())
        
        self.results = all_results
        
        # Generate summary
        total_issues = sum(len(result.issues) for result in all_results)
        successful_tools = sum(1 for result in all_results if result.success)
        total_tools = len(all_results)
        
        summary = {
            "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tools_run": total_tools,
            "successful_tools": successful_tools,
            "failed_tools": total_tools - successful_tools,
            "total_issues_found": total_issues,
            "results": [asdict(result) for result in all_results]
        }
        
        logger.info(f"Analysis complete. Found {total_issues} issues across {successful_tools}/{total_tools} tools.")
        
        return summary
    
    def save_results(self, output_file: Path):
        """Save analysis results to JSON file."""
        summary = self.run_full_analysis()
        
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Results saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Comprehensive Codebase Analysis Tool")
    parser.add_argument("--output", "-o", type=Path, default="analysis-results.json",
                       help="Output file for analysis results")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="Project root directory")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    analyzer = CodebaseAnalyzer(args.project_root)
    analyzer.save_results(args.output)


if __name__ == "__main__":
    main()