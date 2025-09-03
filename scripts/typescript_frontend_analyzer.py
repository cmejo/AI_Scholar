#!/usr/bin/env python3
"""
TypeScript/React Frontend Code Analysis Tool

This tool provides comprehensive analysis of TypeScript/React frontend code including:
- TypeScript compilation errors and type mismatches
- React component analysis for unused imports and component issues
- Bundle analysis for performance optimization opportunities
- Accessibility compliance checking for React components

Requirements: 2.1, 2.2, 2.3
"""

import os
import sys
import json
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import ast
import tempfile
import shutil

class IssueType(Enum):
    TYPESCRIPT_ERROR = "typescript_error"
    TYPE_MISMATCH = "type_mismatch"
    UNUSED_IMPORT = "unused_import"
    COMPONENT_ISSUE = "component_issue"
    BUNDLE_ISSUE = "bundle_issue"
    ACCESSIBILITY_ISSUE = "accessibility_issue"
    PERFORMANCE_ISSUE = "performance_issue"

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
    auto_fixable: bool
    related_issues: List[str]

@dataclass
class TypeScriptAnalysisResult:
    compilation_errors: List[AnalysisIssue]
    type_errors: List[AnalysisIssue]
    warnings: List[AnalysisIssue]
    total_files_analyzed: int
    success: bool

@dataclass
class ReactComponentAnalysisResult:
    unused_imports: List[AnalysisIssue]
    component_issues: List[AnalysisIssue]
    hook_issues: List[AnalysisIssue]
    total_components_analyzed: int
    success: bool

@dataclass
class BundleAnalysisResult:
    bundle_size_issues: List[AnalysisIssue]
    optimization_opportunities: List[AnalysisIssue]
    dependency_issues: List[AnalysisIssue]
    performance_recommendations: List[AnalysisIssue]
    bundle_stats: Dict[str, Any]
    success: bool

@dataclass
class AccessibilityAnalysisResult:
    accessibility_violations: List[AnalysisIssue]
    wcag_compliance_issues: List[AnalysisIssue]
    semantic_issues: List[AnalysisIssue]
    total_components_checked: int
    success: bool

@dataclass
class FrontendAnalysisResult:
    typescript_analysis: TypeScriptAnalysisResult
    react_analysis: ReactComponentAnalysisResult
    bundle_analysis: BundleAnalysisResult
    accessibility_analysis: AccessibilityAnalysisResult
    summary: Dict[str, Any]
    timestamp: str

class TypeScriptFrontendAnalyzer:
    """Comprehensive TypeScript/React frontend code analyzer"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.frontend_dir = self.project_root / "frontend"
        self.src_dir = self.frontend_dir / "src"
        self.node_modules = self.project_root / "node_modules"
        self.package_json = self.project_root / "package.json"
        
        # Analysis configuration
        self.config = {
            "typescript": {
                "strict_mode": True,
                "check_unused_locals": True,
                "check_unused_parameters": True,
                "no_implicit_any": True
            },
            "react": {
                "check_hooks_rules": True,
                "check_unused_imports": True,
                "check_component_patterns": True
            },
            "bundle": {
                "size_threshold_kb": 500,
                "chunk_threshold_kb": 250,
                "analyze_dependencies": True
            },
            "accessibility": {
                "wcag_level": "AA",
                "check_semantic_html": True,
                "check_aria_attributes": True
            }
        }
        
        self.issues = []
        self.issue_counter = 0
    
    def _generate_issue_id(self) -> str:
        """Generate unique issue ID"""
        self.issue_counter += 1
        return f"frontend_{self.issue_counter:04d}"
    
    def _create_issue(self, issue_type: IssueType, severity: IssueSeverity, 
                     file_path: str, description: str, recommendation: str,
                     line_number: Optional[int] = None, column_number: Optional[int] = None,
                     auto_fixable: bool = False, related_issues: List[str] = None) -> AnalysisIssue:
        """Create a new analysis issue"""
        return AnalysisIssue(
            id=self._generate_issue_id(),
            type=issue_type,
            severity=severity,
            file_path=str(file_path),
            line_number=line_number,
            column_number=column_number,
            description=description,
            recommendation=recommendation,
            auto_fixable=auto_fixable,
            related_issues=related_issues or []
        )
    
    def _run_command(self, command: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str, str]:
        """Run a shell command and return success, stdout, stderr"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are available"""
        required_commands = ["npm", "npx", "tsc"]
        missing = []
        
        for cmd in required_commands:
            success, _, _ = self._run_command(["which", cmd])
            if not success:
                missing.append(cmd)
        
        if missing:
            print(f"Missing required commands: {', '.join(missing)}")
            return False
        
        # Check if node_modules exists
        if not self.node_modules.exists():
            print("node_modules not found. Run 'npm install' first.")
            return False
        
        return True
    
    def analyze_typescript_compilation(self) -> TypeScriptAnalysisResult:
        """Analyze TypeScript compilation errors and type mismatches"""
        print("Analyzing TypeScript compilation...")
        
        compilation_errors = []
        type_errors = []
        warnings = []
        total_files = 0
        
        try:
            # Run TypeScript compiler with noEmit flag
            success, stdout, stderr = self._run_command([
                "npx", "tsc", "--noEmit", "--pretty", "false"
            ])
            
            # Count TypeScript files
            if self.src_dir.exists():
                ts_files = list(self.src_dir.rglob("*.ts")) + list(self.src_dir.rglob("*.tsx"))
                total_files = len(ts_files)
            
            if not success and stderr:
                # Parse TypeScript compiler output
                error_lines = stderr.strip().split('\n')
                
                for line in error_lines:
                    if not line.strip():
                        continue
                    
                    # Parse TypeScript error format: file(line,col): error TS####: message
                    match = re.match(r'^(.+?)\((\d+),(\d+)\):\s+(error|warning)\s+TS(\d+):\s+(.+)$', line)
                    if match:
                        file_path, line_num, col_num, level, error_code, message = match.groups()
                        
                        # Determine issue type and severity
                        issue_type = IssueType.TYPESCRIPT_ERROR
                        severity = IssueSeverity.HIGH if level == "error" else IssueSeverity.MEDIUM
                        
                        # Categorize specific TypeScript errors
                        if error_code in ["2304", "2307", "2339"]:  # Cannot find name/module, property does not exist
                            issue_type = IssueType.TYPE_MISMATCH
                            severity = IssueSeverity.HIGH
                        elif error_code in ["2322", "2345"]:  # Type assignment errors
                            issue_type = IssueType.TYPE_MISMATCH
                            severity = IssueSeverity.MEDIUM
                        elif error_code in ["6133", "6196"]:  # Unused variables/imports
                            issue_type = IssueType.UNUSED_IMPORT
                            severity = IssueSeverity.LOW
                        
                        # Generate recommendation
                        recommendation = self._get_typescript_recommendation(error_code, message)
                        
                        issue = self._create_issue(
                            issue_type=issue_type,
                            severity=severity,
                            file_path=file_path,
                            line_number=int(line_num),
                            column_number=int(col_num),
                            description=f"TS{error_code}: {message}",
                            recommendation=recommendation,
                            auto_fixable=error_code in ["6133", "6196", "2304"]  # Some errors are auto-fixable
                        )
                        
                        if level == "error":
                            if issue_type == IssueType.TYPE_MISMATCH:
                                type_errors.append(issue)
                            else:
                                compilation_errors.append(issue)
                        else:
                            warnings.append(issue)
            
            # Additional type checking with strict mode
            if self.config["typescript"]["strict_mode"]:
                strict_issues = self._analyze_strict_type_issues()
                type_errors.extend(strict_issues)
            
            return TypeScriptAnalysisResult(
                compilation_errors=compilation_errors,
                type_errors=type_errors,
                warnings=warnings,
                total_files_analyzed=total_files,
                success=len(compilation_errors) == 0
            )
            
        except Exception as e:
            print(f"Error analyzing TypeScript compilation: {e}")
            return TypeScriptAnalysisResult(
                compilation_errors=[],
                type_errors=[],
                warnings=[],
                total_files_analyzed=0,
                success=False
            )
    
    def _get_typescript_recommendation(self, error_code: str, message: str) -> str:
        """Get recommendation for TypeScript error"""
        recommendations = {
            "2304": "Add proper import statement or check if the identifier is correctly spelled",
            "2307": "Verify the module path is correct and the module is installed",
            "2322": "Check type compatibility and add proper type annotations",
            "2339": "Verify the property exists on the type or add proper type guards",
            "2345": "Check function parameter types and provide correct arguments",
            "6133": "Remove unused variable or prefix with underscore if intentionally unused",
            "6196": "Remove unused import statement"
        }
        return recommendations.get(error_code, "Review TypeScript documentation for this error")
    
    def _analyze_strict_type_issues(self) -> List[AnalysisIssue]:
        """Analyze strict TypeScript type issues"""
        issues = []
        
        if not self.src_dir.exists():
            return issues
        
        # Find files with potential strict mode issues
        ts_files = list(self.src_dir.rglob("*.ts")) + list(self.src_dir.rglob("*.tsx"))
        
        for file_path in ts_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    # Check for any type usage
                    if re.search(r'\bany\b', line) and not line.strip().startswith('//'):
                        issue = self._create_issue(
                            issue_type=IssueType.TYPE_MISMATCH,
                            severity=IssueSeverity.MEDIUM,
                            file_path=str(file_path),
                            line_number=line_num,
                            description="Usage of 'any' type detected",
                            recommendation="Replace 'any' with specific type annotations",
                            auto_fixable=False
                        )
                        issues.append(issue)
                    
                    # Check for non-null assertions
                    if '!' in line and not line.strip().startswith('//'):
                        if re.search(r'\w+!\.', line):
                            issue = self._create_issue(
                                issue_type=IssueType.TYPE_MISMATCH,
                                severity=IssueSeverity.HIGH,
                                file_path=str(file_path),
                                line_number=line_num,
                                description="Non-null assertion operator (!) usage detected",
                                recommendation="Add proper null checks instead of using non-null assertion",
                                auto_fixable=False
                            )
                            issues.append(issue)
                            
            except Exception as e:
                print(f"Error analyzing file {file_path}: {e}")
                continue
        
        return issues
    
    def analyze_react_components(self) -> ReactComponentAnalysisResult:
        """Analyze React components for unused imports and component issues"""
        print("Analyzing React components...")
        
        unused_imports = []
        component_issues = []
        hook_issues = []
        total_components = 0
        
        try:
            if not self.src_dir.exists():
                return ReactComponentAnalysisResult(
                    unused_imports=[],
                    component_issues=[],
                    hook_issues=[],
                    total_components_analyzed=0,
                    success=False
                )
            
            # Find React component files
            react_files = list(self.src_dir.rglob("*.tsx")) + list(self.src_dir.rglob("*.jsx"))
            total_components = len(react_files)
            
            for file_path in react_files:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    
                    # Analyze unused imports
                    unused_import_issues = self._analyze_unused_imports(file_path, content)
                    unused_imports.extend(unused_import_issues)
                    
                    # Analyze component patterns
                    component_pattern_issues = self._analyze_component_patterns(file_path, content)
                    component_issues.extend(component_pattern_issues)
                    
                    # Analyze React hooks usage
                    hook_usage_issues = self._analyze_hook_usage(file_path, content)
                    hook_issues.extend(hook_usage_issues)
                    
                except Exception as e:
                    print(f"Error analyzing React file {file_path}: {e}")
                    continue
            
            return ReactComponentAnalysisResult(
                unused_imports=unused_imports,
                component_issues=component_issues,
                hook_issues=hook_issues,
                total_components_analyzed=total_components,
                success=True
            )
            
        except Exception as e:
            print(f"Error analyzing React components: {e}")
            return ReactComponentAnalysisResult(
                unused_imports=[],
                component_issues=[],
                hook_issues=[],
                total_components_analyzed=0,
                success=False
            )
    
    def _analyze_unused_imports(self, file_path: Path, content: str) -> List[AnalysisIssue]:
        """Analyze unused imports in React files"""
        issues = []
        lines = content.split('\n')
        
        # Extract imports
        imports = {}
        for line_num, line in enumerate(lines, 1):
            # Match import statements
            import_match = re.match(r'^import\s+(.+?)\s+from\s+[\'"](.+?)[\'"];?', line.strip())
            if import_match:
                import_clause, module = import_match.groups()
                
                # Parse different import patterns
                if import_clause.startswith('{') and import_clause.endswith('}'):
                    # Named imports: { Component, useState }
                    named_imports = re.findall(r'(\w+)(?:\s+as\s+(\w+))?', import_clause[1:-1])
                    for import_name, alias in named_imports:
                        actual_name = alias if alias else import_name
                        imports[actual_name] = {
                            'line': line_num,
                            'module': module,
                            'type': 'named',
                            'original': import_name
                        }
                elif ',' in import_clause:
                    # Mixed imports: React, { useState }
                    parts = import_clause.split(',')
                    for part in parts:
                        part = part.strip()
                        if part.startswith('{') and part.endswith('}'):
                            named_imports = re.findall(r'(\w+)(?:\s+as\s+(\w+))?', part[1:-1])
                            for import_name, alias in named_imports:
                                actual_name = alias if alias else import_name
                                imports[actual_name] = {
                                    'line': line_num,
                                    'module': module,
                                    'type': 'named',
                                    'original': import_name
                                }
                        else:
                            imports[part.strip()] = {
                                'line': line_num,
                                'module': module,
                                'type': 'default'
                            }
                else:
                    # Default import: React or Component
                    import_name = import_clause.strip()
                    imports[import_name] = {
                        'line': line_num,
                        'module': module,
                        'type': 'default'
                    }
        
        # Check usage of imports
        for import_name, import_info in imports.items():
            # Skip React import as it might be used implicitly in JSX
            if import_name == 'React':
                continue
            
            # Check if import is used in the file
            usage_pattern = rf'\b{re.escape(import_name)}\b'
            usage_found = False
            
            for line_num, line in enumerate(lines, 1):
                if line_num == import_info['line']:
                    continue  # Skip the import line itself
                
                if re.search(usage_pattern, line):
                    usage_found = True
                    break
            
            if not usage_found:
                issue = self._create_issue(
                    issue_type=IssueType.UNUSED_IMPORT,
                    severity=IssueSeverity.LOW,
                    file_path=str(file_path),
                    line_number=import_info['line'],
                    description=f"Unused import '{import_name}' from '{import_info['module']}'",
                    recommendation=f"Remove unused import '{import_name}' or use it in the component",
                    auto_fixable=True
                )
                issues.append(issue)
        
        return issues
    
    def _analyze_component_patterns(self, file_path: Path, content: str) -> List[AnalysisIssue]:
        """Analyze React component patterns and best practices"""
        issues = []
        lines = content.split('\n')
        
        # Check for component naming conventions
        file_name = file_path.stem
        if file_name[0].islower() and file_name != 'index':
            issue = self._create_issue(
                issue_type=IssueType.COMPONENT_ISSUE,
                severity=IssueSeverity.LOW,
                file_path=str(file_path),
                description=f"Component file '{file_name}' should start with uppercase letter",
                recommendation="Rename component file to start with uppercase letter (PascalCase)",
                auto_fixable=False
            )
            issues.append(issue)
        
        # Check for proper component export
        has_default_export = False
        has_named_export = False
        
        for line_num, line in enumerate(lines, 1):
            if re.search(r'export\s+default\s+', line):
                has_default_export = True
            elif re.search(r'export\s+(?:const|function|class)\s+\w+', line):
                has_named_export = True
            
            # Check for inline styles (performance issue)
            if re.search(r'style\s*=\s*\{\{', line):
                issue = self._create_issue(
                    issue_type=IssueType.PERFORMANCE_ISSUE,
                    severity=IssueSeverity.MEDIUM,
                    file_path=str(file_path),
                    line_number=line_num,
                    description="Inline styles detected - can cause performance issues",
                    recommendation="Move styles to CSS modules, styled-components, or define outside component",
                    auto_fixable=False
                )
                issues.append(issue)
            
            # Check for console.log statements
            if re.search(r'console\.(log|warn|error|debug)', line) and not line.strip().startswith('//'):
                issue = self._create_issue(
                    issue_type=IssueType.COMPONENT_ISSUE,
                    severity=IssueSeverity.LOW,
                    file_path=str(file_path),
                    line_number=line_num,
                    description="Console statement found in component",
                    recommendation="Remove console statements before production or use proper logging",
                    auto_fixable=True
                )
                issues.append(issue)
        
        # Check export pattern
        if not has_default_export and not has_named_export:
            issue = self._create_issue(
                issue_type=IssueType.COMPONENT_ISSUE,
                severity=IssueSeverity.MEDIUM,
                file_path=str(file_path),
                description="No component export found",
                recommendation="Add proper component export (default or named)",
                auto_fixable=False
            )
            issues.append(issue)
        
        return issues
    
    def _analyze_hook_usage(self, file_path: Path, content: str) -> List[AnalysisIssue]:
        """Analyze React hooks usage patterns"""
        issues = []
        lines = content.split('\n')
        
        # Track hook usage
        hooks_used = []
        in_component = False
        component_name = None
        
        for line_num, line in enumerate(lines, 1):
            # Detect component function
            component_match = re.search(r'(?:const|function)\s+(\w+).*?(?:React\.FC|FunctionComponent|\(\s*\)\s*=>|\(\s*props)', line)
            if component_match:
                in_component = True
                component_name = component_match.group(1)
            
            # Detect hooks usage
            hook_match = re.search(r'(use\w+)\s*\(', line)
            if hook_match and in_component:
                hook_name = hook_match.group(1)
                hooks_used.append({
                    'name': hook_name,
                    'line': line_num
                })
                
                # Check for hooks rules violations
                # Rule: Hooks should not be called inside loops, conditions, or nested functions
                if re.search(r'^\s*(if|for|while|switch)\s*\(', line.strip()):
                    issue = self._create_issue(
                        issue_type=IssueType.COMPONENT_ISSUE,
                        severity=IssueSeverity.HIGH,
                        file_path=str(file_path),
                        line_number=line_num,
                        description=f"Hook '{hook_name}' called inside conditional/loop",
                        recommendation="Move hook call to top level of component function",
                        auto_fixable=False
                    )
                    issues.append(issue)
            
            # Check for useEffect without dependency array
            if 'useEffect' in line and not re.search(r'useEffect\s*\([^,]+,\s*\[', line):
                if 'useEffect' in line and ')' in line:  # Single line useEffect
                    issue = self._create_issue(
                        issue_type=IssueType.COMPONENT_ISSUE,
                        severity=IssueSeverity.MEDIUM,
                        file_path=str(file_path),
                        line_number=line_num,
                        description="useEffect without dependency array",
                        recommendation="Add dependency array to useEffect to control when it runs",
                        auto_fixable=False
                    )
                    issues.append(issue)
        
        return issues
    
    def analyze_bundle_performance(self) -> BundleAnalysisResult:
        """Analyze bundle size and performance optimization opportunities"""
        print("Analyzing bundle performance...")
        
        bundle_size_issues = []
        optimization_opportunities = []
        dependency_issues = []
        performance_recommendations = []
        bundle_stats = {}
        
        try:
            # Build the project to analyze bundle
            print("Building project for bundle analysis...")
            success, stdout, stderr = self._run_command(["npm", "run", "build"])
            
            if not success:
                print(f"Build failed: {stderr}")
                return BundleAnalysisResult(
                    bundle_size_issues=[],
                    optimization_opportunities=[],
                    dependency_issues=[],
                    performance_recommendations=[],
                    bundle_stats={},
                    success=False
                )
            
            # Analyze dist directory
            dist_dir = self.project_root / "dist"
            if dist_dir.exists():
                bundle_stats = self._analyze_bundle_files(dist_dir)
                
                # Check bundle sizes
                for file_info in bundle_stats.get('files', []):
                    size_kb = file_info['size'] / 1024
                    
                    if file_info['name'].endswith('.js'):
                        if size_kb > self.config['bundle']['size_threshold_kb']:
                            issue = self._create_issue(
                                issue_type=IssueType.BUNDLE_ISSUE,
                                severity=IssueSeverity.HIGH,
                                file_path=file_info['path'],
                                description=f"Large JavaScript bundle: {size_kb:.1f}KB",
                                recommendation="Consider code splitting, tree shaking, or removing unused dependencies",
                                auto_fixable=False
                            )
                            bundle_size_issues.append(issue)
                        elif size_kb > self.config['bundle']['chunk_threshold_kb']:
                            issue = self._create_issue(
                                issue_type=IssueType.PERFORMANCE_ISSUE,
                                severity=IssueSeverity.MEDIUM,
                                file_path=file_info['path'],
                                description=f"Large JavaScript chunk: {size_kb:.1f}KB",
                                recommendation="Consider splitting this chunk further or lazy loading",
                                auto_fixable=False
                            )
                            optimization_opportunities.append(issue)
            
            # Analyze package.json for dependency issues
            if self.package_json.exists():
                dependency_analysis = self._analyze_dependencies()
                dependency_issues.extend(dependency_analysis)
            
            # Generate performance recommendations
            perf_recommendations = self._generate_performance_recommendations()
            performance_recommendations.extend(perf_recommendations)
            
            return BundleAnalysisResult(
                bundle_size_issues=bundle_size_issues,
                optimization_opportunities=optimization_opportunities,
                dependency_issues=dependency_issues,
                performance_recommendations=performance_recommendations,
                bundle_stats=bundle_stats,
                success=True
            )
            
        except Exception as e:
            print(f"Error analyzing bundle performance: {e}")
            return BundleAnalysisResult(
                bundle_size_issues=[],
                optimization_opportunities=[],
                dependency_issues=[],
                performance_recommendations=[],
                bundle_stats={},
                success=False
            )
    
    def _analyze_bundle_files(self, dist_dir: Path) -> Dict[str, Any]:
        """Analyze files in the dist directory"""
        stats = {
            'total_size': 0,
            'files': [],
            'js_size': 0,
            'css_size': 0,
            'asset_size': 0
        }
        
        for file_path in dist_dir.rglob('*'):
            if file_path.is_file():
                size = file_path.stat().st_size
                stats['total_size'] += size
                
                file_info = {
                    'name': file_path.name,
                    'path': str(file_path.relative_to(self.project_root)),
                    'size': size
                }
                stats['files'].append(file_info)
                
                if file_path.suffix == '.js':
                    stats['js_size'] += size
                elif file_path.suffix == '.css':
                    stats['css_size'] += size
                else:
                    stats['asset_size'] += size
        
        return stats
    
    def _analyze_dependencies(self) -> List[AnalysisIssue]:
        """Analyze package.json dependencies for issues"""
        issues = []
        
        try:
            package_data = json.loads(self.package_json.read_text())
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            
            # Check for outdated dependencies
            success, stdout, stderr = self._run_command(["npm", "outdated", "--json"])
            if stdout:
                try:
                    outdated = json.loads(stdout)
                    for package, info in outdated.items():
                        issue = self._create_issue(
                            issue_type=IssueType.BUNDLE_ISSUE,
                            severity=IssueSeverity.MEDIUM,
                            file_path="package.json",
                            description=f"Outdated dependency: {package} ({info.get('current')} -> {info.get('latest')})",
                            recommendation=f"Update {package} to latest version",
                            auto_fixable=True
                        )
                        issues.append(issue)
                except json.JSONDecodeError:
                    pass
            
            # Check for large dependencies
            large_deps = [
                'lodash', 'moment', 'jquery', 'bootstrap'  # Known large dependencies
            ]
            
            for dep in large_deps:
                if dep in dependencies:
                    issue = self._create_issue(
                        issue_type=IssueType.PERFORMANCE_ISSUE,
                        severity=IssueSeverity.MEDIUM,
                        file_path="package.json",
                        description=f"Large dependency detected: {dep}",
                        recommendation=f"Consider lighter alternatives to {dep} or use tree shaking",
                        auto_fixable=False
                    )
                    issues.append(issue)
            
        except Exception as e:
            print(f"Error analyzing dependencies: {e}")
        
        return issues
    
    def _generate_performance_recommendations(self) -> List[AnalysisIssue]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # Check for code splitting opportunities
        if self.src_dir.exists():
            large_components = []
            for file_path in self.src_dir.rglob("*.tsx"):
                try:
                    size = file_path.stat().st_size
                    if size > 10000:  # Files larger than 10KB
                        large_components.append((file_path, size))
                except:
                    continue
            
            if large_components:
                issue = self._create_issue(
                    issue_type=IssueType.PERFORMANCE_ISSUE,
                    severity=IssueSeverity.MEDIUM,
                    file_path="src/",
                    description=f"Found {len(large_components)} large component files",
                    recommendation="Consider splitting large components or implementing lazy loading",
                    auto_fixable=False
                )
                recommendations.append(issue)
        
        # Check vite.config.ts for optimization settings
        vite_config = self.project_root / "vite.config.ts"
        if vite_config.exists():
            try:
                content = vite_config.read_text()
                if "manualChunks" not in content:
                    issue = self._create_issue(
                        issue_type=IssueType.PERFORMANCE_ISSUE,
                        severity=IssueSeverity.LOW,
                        file_path="vite.config.ts",
                        description="Manual chunk splitting not configured",
                        recommendation="Configure manual chunk splitting in vite.config.ts for better caching",
                        auto_fixable=False
                    )
                    recommendations.append(issue)
                
                if "terser" not in content and "esbuild" not in content:
                    issue = self._create_issue(
                        issue_type=IssueType.PERFORMANCE_ISSUE,
                        severity=IssueSeverity.LOW,
                        file_path="vite.config.ts",
                        description="Minification not explicitly configured",
                        recommendation="Ensure proper minification is configured for production builds",
                        auto_fixable=False
                    )
                    recommendations.append(issue)
                    
            except Exception as e:
                print(f"Error analyzing vite.config.ts: {e}")
        
        return recommendations
    
    def analyze_accessibility_compliance(self) -> AccessibilityAnalysisResult:
        """Analyze React components for accessibility compliance"""
        print("Analyzing accessibility compliance...")
        
        accessibility_violations = []
        wcag_compliance_issues = []
        semantic_issues = []
        total_components = 0
        
        try:
            if not self.src_dir.exists():
                return AccessibilityAnalysisResult(
                    accessibility_violations=[],
                    wcag_compliance_issues=[],
                    semantic_issues=[],
                    total_components_checked=0,
                    success=False
                )
            
            # Find React component files
            react_files = list(self.src_dir.rglob("*.tsx")) + list(self.src_dir.rglob("*.jsx"))
            total_components = len(react_files)
            
            for file_path in react_files:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    
                    # Analyze accessibility issues
                    a11y_issues = self._analyze_accessibility_patterns(file_path, content)
                    accessibility_violations.extend(a11y_issues)
                    
                    # Analyze WCAG compliance
                    wcag_issues = self._analyze_wcag_compliance(file_path, content)
                    wcag_compliance_issues.extend(wcag_issues)
                    
                    # Analyze semantic HTML usage
                    semantic_html_issues = self._analyze_semantic_html(file_path, content)
                    semantic_issues.extend(semantic_html_issues)
                    
                except Exception as e:
                    print(f"Error analyzing accessibility in {file_path}: {e}")
                    continue
            
            return AccessibilityAnalysisResult(
                accessibility_violations=accessibility_violations,
                wcag_compliance_issues=wcag_compliance_issues,
                semantic_issues=semantic_issues,
                total_components_checked=total_components,
                success=True
            )
            
        except Exception as e:
            print(f"Error analyzing accessibility compliance: {e}")
            return AccessibilityAnalysisResult(
                accessibility_violations=[],
                wcag_compliance_issues=[],
                semantic_issues=[],
                total_components_checked=0,
                success=False
            )
    
    def _analyze_accessibility_patterns(self, file_path: Path, content: str) -> List[AnalysisIssue]:
        """Analyze accessibility patterns in React components"""
        issues = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Check for images without alt text
            if re.search(r'<img\s+[^>]*src=', line) and not re.search(r'alt\s*=', line):
                issue = self._create_issue(
                    issue_type=IssueType.ACCESSIBILITY_ISSUE,
                    severity=IssueSeverity.HIGH,
                    file_path=str(file_path),
                    line_number=line_num,
                    description="Image without alt attribute",
                    recommendation="Add alt attribute to image for screen readers",
                    auto_fixable=True
                )
                issues.append(issue)
            
            # Check for buttons without accessible text
            if re.search(r'<button[^>]*>', line):
                # Check if button has text content or aria-label
                if not re.search(r'aria-label\s*=', line) and not re.search(r'>\s*\w+', line):
                    issue = self._create_issue(
                        issue_type=IssueType.ACCESSIBILITY_ISSUE,
                        severity=IssueSeverity.HIGH,
                        file_path=str(file_path),
                        line_number=line_num,
                        description="Button without accessible text",
                        recommendation="Add aria-label or text content to button",
                        auto_fixable=False
                    )
                    issues.append(issue)
            
            # Check for form inputs without labels
            if re.search(r'<input\s+[^>]*type=', line):
                if not re.search(r'aria-label\s*=', line) and not re.search(r'id\s*=', line):
                    issue = self._create_issue(
                        issue_type=IssueType.ACCESSIBILITY_ISSUE,
                        severity=IssueSeverity.HIGH,
                        file_path=str(file_path),
                        line_number=line_num,
                        description="Form input without label association",
                        recommendation="Add id attribute and associate with label, or add aria-label",
                        auto_fixable=False
                    )
                    issues.append(issue)
            
            # Check for click handlers on non-interactive elements
            if re.search(r'onClick\s*=', line):
                if re.search(r'<div[^>]*onClick', line) or re.search(r'<span[^>]*onClick', line):
                    if not re.search(r'role\s*=\s*["\']button["\']', line):
                        issue = self._create_issue(
                            issue_type=IssueType.ACCESSIBILITY_ISSUE,
                            severity=IssueSeverity.MEDIUM,
                            file_path=str(file_path),
                            line_number=line_num,
                            description="Click handler on non-interactive element",
                            recommendation="Add role='button' and keyboard event handlers, or use button element",
                            auto_fixable=False
                        )
                        issues.append(issue)
        
        return issues
    
    def _analyze_wcag_compliance(self, file_path: Path, content: str) -> List[AnalysisIssue]:
        """Analyze WCAG compliance issues"""
        issues = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Check for color-only information conveyance
            if re.search(r'color\s*:\s*["\']?(red|green|blue)', line, re.IGNORECASE):
                issue = self._create_issue(
                    issue_type=IssueType.ACCESSIBILITY_ISSUE,
                    severity=IssueSeverity.MEDIUM,
                    file_path=str(file_path),
                    line_number=line_num,
                    description="Potential color-only information conveyance",
                    recommendation="Ensure information is not conveyed by color alone (WCAG 1.4.1)",
                    auto_fixable=False
                )
                issues.append(issue)
            
            # Check for missing focus indicators
            if re.search(r'outline\s*:\s*none', line) or re.search(r'outline\s*:\s*0', line):
                issue = self._create_issue(
                    issue_type=IssueType.ACCESSIBILITY_ISSUE,
                    severity=IssueSeverity.HIGH,
                    file_path=str(file_path),
                    line_number=line_num,
                    description="Focus outline removed without alternative",
                    recommendation="Provide alternative focus indicator when removing outline (WCAG 2.4.7)",
                    auto_fixable=False
                )
                issues.append(issue)
            
            # Check for autoplay media
            if re.search(r'autoplay', line, re.IGNORECASE):
                issue = self._create_issue(
                    issue_type=IssueType.ACCESSIBILITY_ISSUE,
                    severity=IssueSeverity.HIGH,
                    file_path=str(file_path),
                    line_number=line_num,
                    description="Autoplay media detected",
                    recommendation="Avoid autoplay or provide controls to pause/stop (WCAG 1.4.2)",
                    auto_fixable=False
                )
                issues.append(issue)
        
        return issues
    
    def _analyze_semantic_html(self, file_path: Path, content: str) -> List[AnalysisIssue]:
        """Analyze semantic HTML usage"""
        issues = []
        lines = content.split('\n')
        
        # Track heading hierarchy
        headings = []
        
        for line_num, line in enumerate(lines, 1):
            # Check heading hierarchy
            heading_match = re.search(r'<h([1-6])', line)
            if heading_match:
                level = int(heading_match.group(1))
                headings.append((line_num, level))
                
                # Check for skipped heading levels
                if len(headings) > 1:
                    prev_level = headings[-2][1]
                    if level > prev_level + 1:
                        issue = self._create_issue(
                            issue_type=IssueType.ACCESSIBILITY_ISSUE,
                            severity=IssueSeverity.MEDIUM,
                            file_path=str(file_path),
                            line_number=line_num,
                            description=f"Heading level skipped (h{prev_level} to h{level})",
                            recommendation="Use sequential heading levels for proper document structure",
                            auto_fixable=False
                        )
                        issues.append(issue)
            
            # Check for generic div/span usage where semantic elements would be better
            if re.search(r'<div[^>]*className=["\'][^"\']*(?:header|nav|main|footer|article|section)', line):
                issue = self._create_issue(
                    issue_type=IssueType.ACCESSIBILITY_ISSUE,
                    severity=IssueSeverity.LOW,
                    file_path=str(file_path),
                    line_number=line_num,
                    description="Generic div used where semantic element would be appropriate",
                    recommendation="Consider using semantic HTML elements (header, nav, main, footer, article, section)",
                    auto_fixable=False
                )
                issues.append(issue)
            
            # Check for missing lang attribute on html elements
            if re.search(r'<html[^>]*>', line) and not re.search(r'lang\s*=', line):
                issue = self._create_issue(
                    issue_type=IssueType.ACCESSIBILITY_ISSUE,
                    severity=IssueSeverity.HIGH,
                    file_path=str(file_path),
                    line_number=line_num,
                    description="HTML element missing lang attribute",
                    recommendation="Add lang attribute to html element for screen readers",
                    auto_fixable=True
                )
                issues.append(issue)
        
        return issues
    
    def run_comprehensive_analysis(self) -> FrontendAnalysisResult:
        """Run comprehensive frontend analysis"""
        print("Starting comprehensive TypeScript/React frontend analysis...")
        
        # Check dependencies
        if not self._check_dependencies():
            print("Dependency check failed. Please install required tools.")
            return self._create_failed_result()
        
        # Run all analyses
        typescript_result = self.analyze_typescript_compilation()
        react_result = self.analyze_react_components()
        bundle_result = self.analyze_bundle_performance()
        accessibility_result = self.analyze_accessibility_compliance()
        
        # Generate summary
        summary = self._generate_summary(
            typescript_result, react_result, bundle_result, accessibility_result
        )
        
        from datetime import datetime
        
        return FrontendAnalysisResult(
            typescript_analysis=typescript_result,
            react_analysis=react_result,
            bundle_analysis=bundle_result,
            accessibility_analysis=accessibility_result,
            summary=summary,
            timestamp=datetime.now().isoformat()
        )
    
    def _create_failed_result(self) -> FrontendAnalysisResult:
        """Create a failed analysis result"""
        from datetime import datetime
        
        return FrontendAnalysisResult(
            typescript_analysis=TypeScriptAnalysisResult([], [], [], 0, False),
            react_analysis=ReactComponentAnalysisResult([], [], [], 0, False),
            bundle_analysis=BundleAnalysisResult([], [], [], [], {}, False),
            accessibility_analysis=AccessibilityAnalysisResult([], [], [], 0, False),
            summary={"status": "failed", "reason": "Dependency check failed"},
            timestamp=datetime.now().isoformat()
        )
    
    def _generate_summary(self, typescript_result: TypeScriptAnalysisResult,
                         react_result: ReactComponentAnalysisResult,
                         bundle_result: BundleAnalysisResult,
                         accessibility_result: AccessibilityAnalysisResult) -> Dict[str, Any]:
        """Generate analysis summary"""
        
        total_issues = (
            len(typescript_result.compilation_errors) +
            len(typescript_result.type_errors) +
            len(typescript_result.warnings) +
            len(react_result.unused_imports) +
            len(react_result.component_issues) +
            len(react_result.hook_issues) +
            len(bundle_result.bundle_size_issues) +
            len(bundle_result.optimization_opportunities) +
            len(bundle_result.dependency_issues) +
            len(bundle_result.performance_recommendations) +
            len(accessibility_result.accessibility_violations) +
            len(accessibility_result.wcag_compliance_issues) +
            len(accessibility_result.semantic_issues)
        )
        
        critical_issues = sum(1 for result in [typescript_result, react_result, bundle_result, accessibility_result]
                            for issue_list in [getattr(result, attr) for attr in dir(result) 
                                             if isinstance(getattr(result, attr), list)]
                            for issue in issue_list
                            if hasattr(issue, 'severity') and issue.severity == IssueSeverity.CRITICAL)
        
        high_issues = sum(1 for result in [typescript_result, react_result, bundle_result, accessibility_result]
                         for issue_list in [getattr(result, attr) for attr in dir(result) 
                                          if isinstance(getattr(result, attr), list)]
                         for issue in issue_list
                         if hasattr(issue, 'severity') and issue.severity == IssueSeverity.HIGH)
        
        return {
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "high_issues": high_issues,
            "typescript_files_analyzed": typescript_result.total_files_analyzed,
            "react_components_analyzed": react_result.total_components_analyzed,
            "accessibility_components_checked": accessibility_result.total_components_checked,
            "bundle_analysis_success": bundle_result.success,
            "overall_success": all([
                typescript_result.success,
                react_result.success,
                bundle_result.success,
                accessibility_result.success
            ]),
            "recommendations": [
                "Fix critical TypeScript compilation errors first",
                "Remove unused imports to reduce bundle size",
                "Address accessibility violations for better user experience",
                "Optimize bundle size for better performance"
            ]
        }
    
    def save_results(self, result: FrontendAnalysisResult, output_file: str = "frontend_analysis_results.json"):
        """Save analysis results to JSON file"""
        try:
            output_path = self.project_root / output_file
            
            # Convert dataclasses to dict
            result_dict = asdict(result)
            
            # Convert enums to strings
            def convert_enums(obj):
                if isinstance(obj, dict):
                    return {k: convert_enums(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_enums(item) for item in obj]
                elif isinstance(obj, Enum):
                    return obj.value
                else:
                    return obj
            
            result_dict = convert_enums(result_dict)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2, ensure_ascii=False)
            
            print(f"Analysis results saved to {output_path}")
            
        except Exception as e:
            print(f"Error saving results: {e}")

def main():
    """Main function to run the frontend analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TypeScript/React Frontend Code Analyzer")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--output", default="frontend_analysis_results.json", help="Output file name")
    parser.add_argument("--typescript-only", action="store_true", help="Run only TypeScript analysis")
    parser.add_argument("--react-only", action="store_true", help="Run only React component analysis")
    parser.add_argument("--bundle-only", action="store_true", help="Run only bundle analysis")
    parser.add_argument("--accessibility-only", action="store_true", help="Run only accessibility analysis")
    
    args = parser.parse_args()
    
    analyzer = TypeScriptFrontendAnalyzer(args.project_root)
    
    if args.typescript_only:
        result = analyzer.analyze_typescript_compilation()
        print(f"TypeScript Analysis: {len(result.compilation_errors)} errors, {len(result.type_errors)} type errors")
    elif args.react_only:
        result = analyzer.analyze_react_components()
        print(f"React Analysis: {len(result.unused_imports)} unused imports, {len(result.component_issues)} component issues")
    elif args.bundle_only:
        result = analyzer.analyze_bundle_performance()
        print(f"Bundle Analysis: {len(result.bundle_size_issues)} size issues, {len(result.optimization_opportunities)} optimizations")
    elif args.accessibility_only:
        result = analyzer.analyze_accessibility_compliance()
        print(f"Accessibility Analysis: {len(result.accessibility_violations)} violations, {len(result.wcag_compliance_issues)} WCAG issues")
    else:
        result = analyzer.run_comprehensive_analysis()
        analyzer.save_results(result, args.output)
        
        print("\n=== Frontend Analysis Summary ===")
        print(f"Total Issues: {result.summary['total_issues']}")
        print(f"Critical Issues: {result.summary['critical_issues']}")
        print(f"High Priority Issues: {result.summary['high_issues']}")
        print(f"TypeScript Files Analyzed: {result.summary['typescript_files_analyzed']}")
        print(f"React Components Analyzed: {result.summary['react_components_analyzed']}")
        print(f"Overall Success: {result.summary['overall_success']}")

if __name__ == "__main__":
    main()