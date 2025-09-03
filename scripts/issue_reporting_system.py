#!/usr/bin/env python3
"""
Comprehensive Issue Reporting and Prioritization System

This system provides:
- Issue classification with severity and type categorization
- Priority scoring algorithm based on impact and Ubuntu compatibility
- Detailed reporting with actionable recommendations
- Fix suggestion generator for auto-fixable issues

Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple, Union
import hashlib


class IssueType(Enum):
    """Comprehensive issue type classification"""
    # Code Issues
    SYNTAX_ERROR = "syntax_error"
    TYPE_ERROR = "type_error"
    IMPORT_ERROR = "import_error"
    COMPILATION_ERROR = "compilation_error"
    
    # Security Issues
    SECURITY_VULNERABILITY = "security_vulnerability"
    DEPENDENCY_VULNERABILITY = "dependency_vulnerability"
    AUTHENTICATION_ISSUE = "authentication_issue"
    PERMISSION_ISSUE = "permission_issue"
    
    # Performance Issues
    PERFORMANCE_ISSUE = "performance_issue"
    MEMORY_LEAK = "memory_leak"
    SQL_PERFORMANCE_ISSUE = "sql_performance_issue"
    BUNDLE_SIZE_ISSUE = "bundle_size_issue"
    
    # Configuration Issues
    CONFIGURATION_ERROR = "configuration_error"
    ENVIRONMENT_CONFIG_ISSUE = "environment_config_issue"
    DOCKER_ISSUE = "docker_issue"
    DEPLOYMENT_SCRIPT_ISSUE = "deployment_script_issue"
    
    # Database Issues
    SQL_SYNTAX_ERROR = "sql_syntax_error"
    DATABASE_CONNECTION_ERROR = "database_connection_error"
    
    # Frontend Issues
    TYPESCRIPT_ERROR = "typescript_error"
    REACT_COMPONENT_ISSUE = "react_component_issue"
    ACCESSIBILITY_ISSUE = "accessibility_issue"
    UNUSED_IMPORT = "unused_import"
    
    # Infrastructure Issues
    UBUNTU_COMPATIBILITY = "ubuntu_compatibility"
    DOCKERFILE_ISSUE = "dockerfile_issue"
    DOCKER_COMPOSE_ISSUE = "docker_compose_issue"
    
    # Code Quality Issues
    STYLE_ISSUE = "style_issue"
    CODE_SMELL = "code_smell"
    TECHNICAL_DEBT = "technical_debt"
    DOCUMENTATION_ISSUE = "documentation_issue"
    
    # Service Integration Issues
    SERVICE_INTEGRATION_ERROR = "service_integration_error"
    API_COMPATIBILITY_ISSUE = "api_compatibility_issue"


class IssueSeverity(Enum):
    """Issue severity levels with numeric values for sorting"""
    CRITICAL = ("critical", 100)
    HIGH = ("high", 75)
    MEDIUM = ("medium", 50)
    LOW = ("low", 25)
    INFO = ("info", 10)
    
    def __init__(self, label: str, score: int):
        self.label = label
        self.score = score


class IssueCategory(Enum):
    """High-level issue categories for grouping"""
    BLOCKING = "blocking"          # Prevents deployment/compilation
    SECURITY = "security"          # Security vulnerabilities
    PERFORMANCE = "performance"    # Performance impacts
    COMPATIBILITY = "compatibility" # Ubuntu/system compatibility
    MAINTAINABILITY = "maintainability" # Code quality and maintenance
    FUNCTIONALITY = "functionality" # Feature/behavior issues


@dataclass
class IssueLocation:
    """Represents the location of an issue"""
    file_path: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    code_snippet: Optional[str] = None


@dataclass
class FixSuggestion:
    """Represents a suggested fix for an issue"""
    description: str
    confidence: float  # 0.0 to 1.0
    auto_fixable: bool
    fix_command: Optional[str] = None
    fix_code: Optional[str] = None
    estimated_effort: str = "unknown"  # "low", "medium", "high"


@dataclass
class IssueImpact:
    """Represents the impact assessment of an issue"""
    deployment_blocking: bool = False
    security_risk: bool = False
    performance_impact: bool = False
    user_facing: bool = False
    ubuntu_specific: bool = False
    affects_core_functionality: bool = False
    estimated_fix_time: str = "unknown"  # "minutes", "hours", "days"


@dataclass
class AnalysisIssue:
    """Comprehensive issue representation"""
    id: str
    type: IssueType
    severity: IssueSeverity
    category: IssueCategory
    title: str
    description: str
    location: IssueLocation
    impact: IssueImpact
    fix_suggestions: List[FixSuggestion] = field(default_factory=list)
    related_issues: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    tool: str = "unknown"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    priority_score: float = 0.0
    
    def __post_init__(self):
        """Calculate priority score after initialization"""
        self.priority_score = self._calculate_priority_score()
    
    def _calculate_priority_score(self) -> float:
        """Calculate priority score based on multiple factors"""
        base_score = self.severity.score
        
        # Impact multipliers
        multipliers = 1.0
        
        if self.impact.deployment_blocking:
            multipliers *= 1.5
        
        if self.impact.security_risk:
            multipliers *= 1.4
        
        if self.impact.ubuntu_specific:
            multipliers *= 1.3
        
        if self.impact.affects_core_functionality:
            multipliers *= 1.2
        
        if self.impact.user_facing:
            multipliers *= 1.1
        
        # Type-specific adjustments
        type_multipliers = {
            IssueType.SYNTAX_ERROR: 1.5,
            IssueType.COMPILATION_ERROR: 1.5,
            IssueType.SECURITY_VULNERABILITY: 1.4,
            IssueType.DEPENDENCY_VULNERABILITY: 1.3,
            IssueType.UBUNTU_COMPATIBILITY: 1.3,
            IssueType.DOCKER_ISSUE: 1.2,
            IssueType.PERFORMANCE_ISSUE: 1.1,
            IssueType.STYLE_ISSUE: 0.8,
            IssueType.DOCUMENTATION_ISSUE: 0.7,
        }
        
        multipliers *= type_multipliers.get(self.type, 1.0)
        
        # Auto-fixable issues get slightly lower priority
        if any(fix.auto_fixable for fix in self.fix_suggestions):
            multipliers *= 0.9
        
        return base_score * multipliers


class IssueClassifier:
    """Classifies issues into categories and determines impact"""
    
    def __init__(self):
        self.blocking_types = {
            IssueType.SYNTAX_ERROR,
            IssueType.COMPILATION_ERROR,
            IssueType.IMPORT_ERROR,
            IssueType.DOCKER_ISSUE,
        }
        
        self.security_types = {
            IssueType.SECURITY_VULNERABILITY,
            IssueType.DEPENDENCY_VULNERABILITY,
            IssueType.AUTHENTICATION_ISSUE,
            IssueType.PERMISSION_ISSUE,
        }
        
        self.performance_types = {
            IssueType.PERFORMANCE_ISSUE,
            IssueType.MEMORY_LEAK,
            IssueType.SQL_PERFORMANCE_ISSUE,
            IssueType.BUNDLE_SIZE_ISSUE,
        }
        
        self.compatibility_types = {
            IssueType.UBUNTU_COMPATIBILITY,
            IssueType.DOCKERFILE_ISSUE,
            IssueType.DOCKER_COMPOSE_ISSUE,
            IssueType.DEPLOYMENT_SCRIPT_ISSUE,
        }
    
    def classify_issue(self, issue_type: IssueType, description: str, 
                      file_path: str) -> Tuple[IssueCategory, IssueImpact]:
        """Classify an issue and assess its impact"""
        
        # Determine category
        if issue_type in self.blocking_types:
            category = IssueCategory.BLOCKING
        elif issue_type in self.security_types:
            category = IssueCategory.SECURITY
        elif issue_type in self.performance_types:
            category = IssueCategory.PERFORMANCE
        elif issue_type in self.compatibility_types:
            category = IssueCategory.COMPATIBILITY
        else:
            category = IssueCategory.MAINTAINABILITY
        
        # Assess impact
        impact = IssueImpact()
        
        # Deployment blocking assessment
        impact.deployment_blocking = (
            issue_type in self.blocking_types or
            "cannot compile" in description.lower() or
            "build failed" in description.lower() or
            "docker" in description.lower() and "failed" in description.lower()
        )
        
        # Security risk assessment
        impact.security_risk = (
            issue_type in self.security_types or
            any(keyword in description.lower() for keyword in [
                "vulnerability", "security", "injection", "xss", "csrf",
                "authentication", "authorization", "privilege"
            ])
        )
        
        # Performance impact assessment
        impact.performance_impact = (
            issue_type in self.performance_types or
            any(keyword in description.lower() for keyword in [
                "slow", "performance", "memory", "cpu", "timeout",
                "large bundle", "inefficient"
            ])
        )
        
        # Ubuntu specific assessment
        impact.ubuntu_specific = (
            issue_type == IssueType.UBUNTU_COMPATIBILITY or
            any(keyword in description.lower() for keyword in [
                "ubuntu", "apt-get", "systemd", "linux", "posix"
            ])
        )
        
        # User facing assessment
        impact.user_facing = (
            "frontend" in file_path.lower() or
            "ui" in file_path.lower() or
            "component" in file_path.lower() or
            issue_type in {IssueType.ACCESSIBILITY_ISSUE, IssueType.REACT_COMPONENT_ISSUE}
        )
        
        # Core functionality assessment
        impact.affects_core_functionality = (
            "core" in file_path.lower() or
            "main" in file_path.lower() or
            "app.py" in file_path.lower() or
            "index" in file_path.lower() or
            impact.deployment_blocking
        )
        
        # Estimate fix time
        if issue_type in {IssueType.STYLE_ISSUE, IssueType.UNUSED_IMPORT}:
            impact.estimated_fix_time = "minutes"
        elif issue_type in {IssueType.TYPE_ERROR, IssueType.CONFIGURATION_ERROR}:
            impact.estimated_fix_time = "hours"
        elif issue_type in {IssueType.SECURITY_VULNERABILITY, IssueType.TECHNICAL_DEBT}:
            impact.estimated_fix_time = "days"
        else:
            impact.estimated_fix_time = "hours"
        
        return category, impact


class FixSuggestionGenerator:
    """Generates fix suggestions for different types of issues"""
    
    def __init__(self):
        self.fix_templates = self._load_fix_templates()
    
    def _load_fix_templates(self) -> Dict[IssueType, List[Dict[str, Any]]]:
        """Load fix suggestion templates for different issue types"""
        return {
            IssueType.UNUSED_IMPORT: [
                {
                    "description": "Remove unused import statement",
                    "confidence": 0.9,
                    "auto_fixable": True,
                    "fix_command": "Remove the import line",
                    "estimated_effort": "low"
                }
            ],
            IssueType.STYLE_ISSUE: [
                {
                    "description": "Apply automatic code formatting",
                    "confidence": 0.95,
                    "auto_fixable": True,
                    "fix_command": "Run code formatter (black, prettier, etc.)",
                    "estimated_effort": "low"
                }
            ],
            IssueType.DEPENDENCY_VULNERABILITY: [
                {
                    "description": "Update vulnerable dependency to latest secure version",
                    "confidence": 0.8,
                    "auto_fixable": True,
                    "fix_command": "Update package version in requirements.txt or package.json",
                    "estimated_effort": "low"
                }
            ],
            IssueType.TYPE_ERROR: [
                {
                    "description": "Add proper type annotations",
                    "confidence": 0.7,
                    "auto_fixable": False,
                    "fix_command": "Add type hints to function parameters and return values",
                    "estimated_effort": "medium"
                }
            ],
            IssueType.SQL_PERFORMANCE_ISSUE: [
                {
                    "description": "Add database index for better query performance",
                    "confidence": 0.6,
                    "auto_fixable": False,
                    "fix_command": "CREATE INDEX ON table_name (column_name)",
                    "estimated_effort": "medium"
                },
                {
                    "description": "Optimize query by specifying exact columns instead of SELECT *",
                    "confidence": 0.8,
                    "auto_fixable": False,
                    "fix_command": "Replace SELECT * with specific column names",
                    "estimated_effort": "low"
                }
            ],
            IssueType.UBUNTU_COMPATIBILITY: [
                {
                    "description": "Replace incompatible command with Ubuntu equivalent",
                    "confidence": 0.7,
                    "auto_fixable": False,
                    "fix_command": "Use apt-get instead of yum/dnf, or update-rc.d instead of chkconfig",
                    "estimated_effort": "medium"
                }
            ],
            IssueType.DOCKER_ISSUE: [
                {
                    "description": "Update Dockerfile to use Ubuntu-compatible base image",
                    "confidence": 0.8,
                    "auto_fixable": False,
                    "fix_command": "Change FROM instruction to use ubuntu:24.04 or python:3.11-slim",
                    "estimated_effort": "low"
                }
            ],
            IssueType.SECURITY_VULNERABILITY: [
                {
                    "description": "Implement proper input validation and sanitization",
                    "confidence": 0.6,
                    "auto_fixable": False,
                    "fix_command": "Add input validation, use parameterized queries, sanitize user input",
                    "estimated_effort": "high"
                }
            ]
        }
    
    def generate_suggestions(self, issue: AnalysisIssue) -> List[FixSuggestion]:
        """Generate fix suggestions for an issue"""
        suggestions = []
        
        # Get template suggestions
        templates = self.fix_templates.get(issue.type, [])
        for template in templates:
            suggestion = FixSuggestion(
                description=template["description"],
                confidence=template["confidence"],
                auto_fixable=template["auto_fixable"],
                fix_command=template.get("fix_command"),
                estimated_effort=template.get("estimated_effort", "unknown")
            )
            suggestions.append(suggestion)
        
        # Generate context-specific suggestions
        context_suggestions = self._generate_context_specific_suggestions(issue)
        suggestions.extend(context_suggestions)
        
        return suggestions
    
    def _generate_context_specific_suggestions(self, issue: AnalysisIssue) -> List[FixSuggestion]:
        """Generate suggestions based on issue context"""
        suggestions = []
        
        # File-specific suggestions
        file_path = issue.location.file_path.lower()
        
        if "dockerfile" in file_path:
            suggestions.append(FixSuggestion(
                description="Run hadolint to check Dockerfile best practices",
                confidence=0.8,
                auto_fixable=False,
                fix_command="hadolint Dockerfile",
                estimated_effort="low"
            ))
        
        elif file_path.endswith(('.py', '.pyi')):
            suggestions.append(FixSuggestion(
                description="Run Python linters for detailed analysis",
                confidence=0.9,
                auto_fixable=True,
                fix_command="black . && flake8 . && mypy .",
                estimated_effort="low"
            ))
        
        elif file_path.endswith(('.ts', '.tsx', '.js', '.jsx')):
            suggestions.append(FixSuggestion(
                description="Run TypeScript compiler and ESLint",
                confidence=0.9,
                auto_fixable=True,
                fix_command="npx tsc --noEmit && npx eslint --fix .",
                estimated_effort="low"
            ))
        
        elif "docker-compose" in file_path:
            suggestions.append(FixSuggestion(
                description="Validate docker-compose configuration",
                confidence=0.8,
                auto_fixable=False,
                fix_command="docker-compose config",
                estimated_effort="low"
            ))
        
        # Description-based suggestions
        description_lower = issue.description.lower()
        
        if "import" in description_lower and "not found" in description_lower:
            suggestions.append(FixSuggestion(
                description="Install missing dependency or check import path",
                confidence=0.7,
                auto_fixable=False,
                fix_command="pip install <package> or npm install <package>",
                estimated_effort="low"
            ))
        
        if "permission" in description_lower:
            suggestions.append(FixSuggestion(
                description="Fix file permissions",
                confidence=0.8,
                auto_fixable=True,
                fix_command="chmod +x <file> or chown <user>:<group> <file>",
                estimated_effort="low"
            ))
        
        return suggestions


class IssueReportGenerator:
    """Generates comprehensive issue reports in various formats"""
    
    def __init__(self):
        self.report_templates = {
            "summary": self._generate_summary_report,
            "detailed": self._generate_detailed_report,
            "json": self._generate_json_report,
            "csv": self._generate_csv_report,
            "markdown": self._generate_markdown_report
        }
    
    def generate_report(self, issues: List[AnalysisIssue], 
                       format_type: str = "detailed",
                       output_file: Optional[str] = None) -> str:
        """Generate a report in the specified format"""
        
        if format_type not in self.report_templates:
            raise ValueError(f"Unsupported report format: {format_type}")
        
        report_content = self.report_templates[format_type](issues)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
        
        return report_content
    
    def _generate_summary_report(self, issues: List[AnalysisIssue]) -> str:
        """Generate a summary report"""
        if not issues:
            return "No issues found."
        
        # Sort issues by priority
        sorted_issues = sorted(issues, key=lambda x: x.priority_score, reverse=True)
        
        # Count by severity
        severity_counts = {}
        for issue in issues:
            severity_counts[issue.severity.label] = severity_counts.get(issue.severity.label, 0) + 1
        
        # Count by category
        category_counts = {}
        for issue in issues:
            category_counts[issue.category.value] = category_counts.get(issue.category.value, 0) + 1
        
        # Count by type
        type_counts = {}
        for issue in issues:
            type_counts[issue.type.value] = type_counts.get(issue.type.value, 0) + 1
        
        report = f"""
ISSUE ANALYSIS SUMMARY
======================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW
--------
Total Issues: {len(issues)}
Critical: {severity_counts.get('critical', 0)}
High: {severity_counts.get('high', 0)}
Medium: {severity_counts.get('medium', 0)}
Low: {severity_counts.get('low', 0)}
Info: {severity_counts.get('info', 0)}

ISSUES BY CATEGORY
------------------
"""
        for category, count in sorted(category_counts.items()):
            report += f"{category.title()}: {count}\n"
        
        report += "\nTOP 10 PRIORITY ISSUES\n"
        report += "----------------------\n"
        
        for i, issue in enumerate(sorted_issues[:10], 1):
            report += f"{i:2d}. [{issue.severity.label.upper()}] {issue.title}\n"
            report += f"    File: {issue.location.file_path}\n"
            if issue.location.line_number:
                report += f"    Line: {issue.location.line_number}\n"
            report += f"    Priority Score: {issue.priority_score:.1f}\n"
            report += "\n"
        
        # Ubuntu-specific issues
        ubuntu_issues = [issue for issue in issues if issue.impact.ubuntu_specific]
        if ubuntu_issues:
            report += f"\nUBUNTU COMPATIBILITY ISSUES: {len(ubuntu_issues)}\n"
            report += "=" * 35 + "\n"
            for issue in ubuntu_issues[:5]:
                report += f"- {issue.title} ({issue.location.file_path})\n"
        
        # Auto-fixable issues
        auto_fixable = [issue for issue in issues if any(fix.auto_fixable for fix in issue.fix_suggestions)]
        if auto_fixable:
            report += f"\nAUTO-FIXABLE ISSUES: {len(auto_fixable)}\n"
            report += "=" * 20 + "\n"
            for issue in auto_fixable[:5]:
                report += f"- {issue.title} ({issue.location.file_path})\n"
        
        return report
    
    def _generate_detailed_report(self, issues: List[AnalysisIssue]) -> str:
        """Generate a detailed report with full issue information"""
        if not issues:
            return "No issues found."
        
        sorted_issues = sorted(issues, key=lambda x: x.priority_score, reverse=True)
        
        report = f"""
DETAILED ISSUE ANALYSIS REPORT
==============================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Issues: {len(issues)}

"""
        
        for i, issue in enumerate(sorted_issues, 1):
            report += f"ISSUE #{i} - {issue.id}\n"
            report += "=" * 50 + "\n"
            report += f"Title: {issue.title}\n"
            report += f"Type: {issue.type.value}\n"
            report += f"Severity: {issue.severity.label.upper()}\n"
            report += f"Category: {issue.category.value}\n"
            report += f"Priority Score: {issue.priority_score:.1f}\n"
            report += f"Tool: {issue.tool}\n"
            report += f"Timestamp: {issue.timestamp}\n"
            report += "\n"
            
            report += "LOCATION:\n"
            report += f"  File: {issue.location.file_path}\n"
            if issue.location.line_number:
                report += f"  Line: {issue.location.line_number}\n"
            if issue.location.column_number:
                report += f"  Column: {issue.location.column_number}\n"
            if issue.location.function_name:
                report += f"  Function: {issue.location.function_name}\n"
            if issue.location.class_name:
                report += f"  Class: {issue.location.class_name}\n"
            report += "\n"
            
            report += "DESCRIPTION:\n"
            report += f"  {issue.description}\n"
            report += "\n"
            
            report += "IMPACT ASSESSMENT:\n"
            report += f"  Deployment Blocking: {'Yes' if issue.impact.deployment_blocking else 'No'}\n"
            report += f"  Security Risk: {'Yes' if issue.impact.security_risk else 'No'}\n"
            report += f"  Performance Impact: {'Yes' if issue.impact.performance_impact else 'No'}\n"
            report += f"  User Facing: {'Yes' if issue.impact.user_facing else 'No'}\n"
            report += f"  Ubuntu Specific: {'Yes' if issue.impact.ubuntu_specific else 'No'}\n"
            report += f"  Core Functionality: {'Yes' if issue.impact.affects_core_functionality else 'No'}\n"
            report += f"  Estimated Fix Time: {issue.impact.estimated_fix_time}\n"
            report += "\n"
            
            if issue.fix_suggestions:
                report += "FIX SUGGESTIONS:\n"
                for j, fix in enumerate(issue.fix_suggestions, 1):
                    report += f"  {j}. {fix.description}\n"
                    report += f"     Confidence: {fix.confidence:.1%}\n"
                    report += f"     Auto-fixable: {'Yes' if fix.auto_fixable else 'No'}\n"
                    report += f"     Effort: {fix.estimated_effort}\n"
                    if fix.fix_command:
                        report += f"     Command: {fix.fix_command}\n"
                    report += "\n"
            
            if issue.location.code_snippet:
                report += "CODE SNIPPET:\n"
                report += f"  {issue.location.code_snippet}\n"
                report += "\n"
            
            if issue.related_issues:
                report += f"RELATED ISSUES: {', '.join(issue.related_issues)}\n"
                report += "\n"
            
            if issue.tags:
                report += f"TAGS: {', '.join(sorted(issue.tags))}\n"
                report += "\n"
            
            report += "-" * 50 + "\n\n"
        
        return report
    
    def _generate_json_report(self, issues: List[AnalysisIssue]) -> str:
        """Generate a JSON report"""
        report_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_issues": len(issues),
                "report_version": "1.0"
            },
            "summary": {
                "by_severity": {},
                "by_category": {},
                "by_type": {},
                "ubuntu_specific_count": len([i for i in issues if i.impact.ubuntu_specific]),
                "auto_fixable_count": len([i for i in issues if any(f.auto_fixable for f in i.fix_suggestions)]),
                "blocking_count": len([i for i in issues if i.impact.deployment_blocking])
            },
            "issues": []
        }
        
        # Count summaries
        for issue in issues:
            # By severity
            severity = issue.severity.label
            report_data["summary"]["by_severity"][severity] = report_data["summary"]["by_severity"].get(severity, 0) + 1
            
            # By category
            category = issue.category.value
            report_data["summary"]["by_category"][category] = report_data["summary"]["by_category"].get(category, 0) + 1
            
            # By type
            issue_type = issue.type.value
            report_data["summary"]["by_type"][issue_type] = report_data["summary"]["by_type"].get(issue_type, 0) + 1
        
        # Convert issues to dict format
        for issue in sorted(issues, key=lambda x: x.priority_score, reverse=True):
            issue_dict = {
                "id": issue.id,
                "title": issue.title,
                "type": issue.type.value,
                "severity": issue.severity.label,
                "category": issue.category.value,
                "priority_score": issue.priority_score,
                "description": issue.description,
                "tool": issue.tool,
                "timestamp": issue.timestamp,
                "location": {
                    "file_path": issue.location.file_path,
                    "line_number": issue.location.line_number,
                    "column_number": issue.location.column_number,
                    "function_name": issue.location.function_name,
                    "class_name": issue.location.class_name,
                    "code_snippet": issue.location.code_snippet
                },
                "impact": {
                    "deployment_blocking": issue.impact.deployment_blocking,
                    "security_risk": issue.impact.security_risk,
                    "performance_impact": issue.impact.performance_impact,
                    "user_facing": issue.impact.user_facing,
                    "ubuntu_specific": issue.impact.ubuntu_specific,
                    "affects_core_functionality": issue.impact.affects_core_functionality,
                    "estimated_fix_time": issue.impact.estimated_fix_time
                },
                "fix_suggestions": [
                    {
                        "description": fix.description,
                        "confidence": fix.confidence,
                        "auto_fixable": fix.auto_fixable,
                        "fix_command": fix.fix_command,
                        "fix_code": fix.fix_code,
                        "estimated_effort": fix.estimated_effort
                    }
                    for fix in issue.fix_suggestions
                ],
                "related_issues": issue.related_issues,
                "tags": list(issue.tags)
            }
            report_data["issues"].append(issue_dict)
        
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    def _generate_csv_report(self, issues: List[AnalysisIssue]) -> str:
        """Generate a CSV report"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "ID", "Title", "Type", "Severity", "Category", "Priority Score",
            "File Path", "Line Number", "Description", "Tool",
            "Deployment Blocking", "Security Risk", "Ubuntu Specific",
            "Auto Fixable", "Estimated Fix Time", "Fix Suggestions"
        ])
        
        # Data rows
        for issue in sorted(issues, key=lambda x: x.priority_score, reverse=True):
            auto_fixable = any(fix.auto_fixable for fix in issue.fix_suggestions)
            fix_suggestions = "; ".join([fix.description for fix in issue.fix_suggestions])
            
            writer.writerow([
                issue.id,
                issue.title,
                issue.type.value,
                issue.severity.label,
                issue.category.value,
                f"{issue.priority_score:.1f}",
                issue.location.file_path,
                issue.location.line_number or "",
                issue.description,
                issue.tool,
                "Yes" if issue.impact.deployment_blocking else "No",
                "Yes" if issue.impact.security_risk else "No",
                "Yes" if issue.impact.ubuntu_specific else "No",
                "Yes" if auto_fixable else "No",
                issue.impact.estimated_fix_time,
                fix_suggestions
            ])
        
        return output.getvalue()
    
    def _generate_markdown_report(self, issues: List[AnalysisIssue]) -> str:
        """Generate a Markdown report"""
        if not issues:
            return "# Issue Analysis Report\n\nNo issues found."
        
        sorted_issues = sorted(issues, key=lambda x: x.priority_score, reverse=True)
        
        # Count summaries
        severity_counts = {}
        category_counts = {}
        for issue in issues:
            severity_counts[issue.severity.label] = severity_counts.get(issue.severity.label, 0) + 1
            category_counts[issue.category.value] = category_counts.get(issue.category.value, 0) + 1
        
        ubuntu_issues = [issue for issue in issues if issue.impact.ubuntu_specific]
        auto_fixable = [issue for issue in issues if any(fix.auto_fixable for fix in issue.fix_suggestions)]
        blocking_issues = [issue for issue in issues if issue.impact.deployment_blocking]
        
        report = f"""# Issue Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Total Issues:** {len(issues)}
- **Critical:** {severity_counts.get('critical', 0)}
- **High:** {severity_counts.get('high', 0)}
- **Medium:** {severity_counts.get('medium', 0)}
- **Low:** {severity_counts.get('low', 0)}
- **Info:** {severity_counts.get('info', 0)}

### Special Categories

- **Ubuntu Compatibility Issues:** {len(ubuntu_issues)}
- **Auto-fixable Issues:** {len(auto_fixable)}
- **Deployment Blocking Issues:** {len(blocking_issues)}

## Issues by Category

"""
        
        for category, count in sorted(category_counts.items()):
            report += f"- **{category.title()}:** {count}\n"
        
        report += "\n## Top Priority Issues\n\n"
        
        for i, issue in enumerate(sorted_issues[:20], 1):
            severity_badge = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢',
                'info': '🔵'
            }.get(issue.severity.label, '⚪')
            
            report += f"### {i}. {severity_badge} {issue.title}\n\n"
            report += f"- **Type:** {issue.type.value}\n"
            report += f"- **Severity:** {issue.severity.label.upper()}\n"
            report += f"- **Priority Score:** {issue.priority_score:.1f}\n"
            report += f"- **File:** `{issue.location.file_path}`\n"
            
            if issue.location.line_number:
                report += f"- **Line:** {issue.location.line_number}\n"
            
            report += f"- **Tool:** {issue.tool}\n"
            
            # Impact indicators
            impact_indicators = []
            if issue.impact.deployment_blocking:
                impact_indicators.append("🚫 Deployment Blocking")
            if issue.impact.security_risk:
                impact_indicators.append("🔒 Security Risk")
            if issue.impact.ubuntu_specific:
                impact_indicators.append("🐧 Ubuntu Specific")
            if any(fix.auto_fixable for fix in issue.fix_suggestions):
                impact_indicators.append("🔧 Auto-fixable")
            
            if impact_indicators:
                report += f"- **Impact:** {' | '.join(impact_indicators)}\n"
            
            report += f"\n**Description:** {issue.description}\n\n"
            
            if issue.fix_suggestions:
                report += "**Fix Suggestions:**\n"
                for j, fix in enumerate(issue.fix_suggestions, 1):
                    confidence_bar = "█" * int(fix.confidence * 5) + "░" * (5 - int(fix.confidence * 5))
                    report += f"{j}. {fix.description} (Confidence: {confidence_bar} {fix.confidence:.1%})\n"
                    if fix.fix_command:
                        report += f"   ```bash\n   {fix.fix_command}\n   ```\n"
                report += "\n"
            
            if issue.location.code_snippet:
                report += "**Code Snippet:**\n"
                report += f"```\n{issue.location.code_snippet}\n```\n\n"
            
            report += "---\n\n"
        
        return report


class ComprehensiveIssueReportingSystem:
    """Main system that orchestrates issue reporting and prioritization"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.classifier = IssueClassifier()
        self.fix_generator = FixSuggestionGenerator()
        self.report_generator = IssueReportGenerator()
        self.issue_counter = 0
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def generate_issue_id(self, tool: str = "system") -> str:
        """Generate unique issue ID"""
        self.issue_counter += 1
        timestamp = int(time.time())
        return f"{tool}_{timestamp}_{self.issue_counter:04d}"
    
    def create_issue(self, 
                    issue_type: IssueType,
                    severity: IssueSeverity,
                    title: str,
                    description: str,
                    file_path: str,
                    line_number: Optional[int] = None,
                    column_number: Optional[int] = None,
                    tool: str = "unknown",
                    code_snippet: Optional[str] = None,
                    function_name: Optional[str] = None,
                    class_name: Optional[str] = None,
                    tags: Optional[Set[str]] = None) -> AnalysisIssue:
        """Create a new analysis issue with full classification and suggestions"""
        
        # Create location
        location = IssueLocation(
            file_path=file_path,
            line_number=line_number,
            column_number=column_number,
            function_name=function_name,
            class_name=class_name,
            code_snippet=code_snippet
        )
        
        # Classify issue and assess impact
        category, impact = self.classifier.classify_issue(issue_type, description, file_path)
        
        # Create issue
        issue = AnalysisIssue(
            id=self.generate_issue_id(tool),
            type=issue_type,
            severity=severity,
            category=category,
            title=title,
            description=description,
            location=location,
            impact=impact,
            tool=tool,
            tags=tags or set()
        )
        
        # Generate fix suggestions
        issue.fix_suggestions = self.fix_generator.generate_suggestions(issue)
        
        return issue
    
    def process_legacy_issues(self, legacy_issues: List[Dict[str, Any]]) -> List[AnalysisIssue]:
        """Convert legacy issue formats to new comprehensive format"""
        processed_issues = []
        
        for legacy_issue in legacy_issues:
            try:
                # Map legacy fields to new format
                issue_type = IssueType(legacy_issue.get('type', 'unknown'))
                severity = IssueSeverity(legacy_issue.get('severity', 'medium'))
                
                # Create comprehensive issue
                issue = self.create_issue(
                    issue_type=issue_type,
                    severity=severity,
                    title=legacy_issue.get('description', 'Unknown issue'),
                    description=legacy_issue.get('description', ''),
                    file_path=legacy_issue.get('file_path', 'unknown'),
                    line_number=legacy_issue.get('line_number'),
                    column_number=legacy_issue.get('column_number'),
                    tool=legacy_issue.get('tool', 'legacy'),
                    code_snippet=legacy_issue.get('code_snippet')
                )
                
                processed_issues.append(issue)
                
            except Exception as e:
                self.logger.error(f"Error processing legacy issue: {e}")
                continue
        
        return processed_issues
    
    def generate_comprehensive_report(self, 
                                    issues: List[AnalysisIssue],
                                    output_dir: Optional[str] = None) -> Dict[str, str]:
        """Generate comprehensive reports in multiple formats"""
        
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = self.project_root / "issue_reports"
            output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reports = {}
        
        # Generate different report formats
        formats = ["summary", "detailed", "json", "csv", "markdown"]
        
        for format_type in formats:
            try:
                report_content = self.report_generator.generate_report(issues, format_type)
                
                # Determine file extension
                extensions = {
                    "summary": "txt",
                    "detailed": "txt", 
                    "json": "json",
                    "csv": "csv",
                    "markdown": "md"
                }
                
                filename = f"issue_report_{format_type}_{timestamp}.{extensions[format_type]}"
                filepath = output_path / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                reports[format_type] = str(filepath)
                self.logger.info(f"Generated {format_type} report: {filepath}")
                
            except Exception as e:
                self.logger.error(f"Error generating {format_type} report: {e}")
        
        return reports
    
    def get_priority_issues(self, issues: List[AnalysisIssue], 
                           limit: int = 10) -> List[AnalysisIssue]:
        """Get top priority issues"""
        return sorted(issues, key=lambda x: x.priority_score, reverse=True)[:limit]
    
    def get_ubuntu_specific_issues(self, issues: List[AnalysisIssue]) -> List[AnalysisIssue]:
        """Get Ubuntu-specific compatibility issues"""
        return [issue for issue in issues if issue.impact.ubuntu_specific]
    
    def get_auto_fixable_issues(self, issues: List[AnalysisIssue]) -> List[AnalysisIssue]:
        """Get issues that can be automatically fixed"""
        return [issue for issue in issues if any(fix.auto_fixable for fix in issue.fix_suggestions)]
    
    def get_blocking_issues(self, issues: List[AnalysisIssue]) -> List[AnalysisIssue]:
        """Get deployment-blocking issues"""
        return [issue for issue in issues if issue.impact.deployment_blocking]
    
    def filter_issues(self, issues: List[AnalysisIssue], 
                     severity: Optional[IssueSeverity] = None,
                     category: Optional[IssueCategory] = None,
                     issue_type: Optional[IssueType] = None,
                     file_pattern: Optional[str] = None) -> List[AnalysisIssue]:
        """Filter issues based on various criteria"""
        filtered = issues
        
        if severity:
            filtered = [issue for issue in filtered if issue.severity == severity]
        
        if category:
            filtered = [issue for issue in filtered if issue.category == category]
        
        if issue_type:
            filtered = [issue for issue in filtered if issue.type == issue_type]
        
        if file_pattern:
            import fnmatch
            filtered = [issue for issue in filtered 
                       if fnmatch.fnmatch(issue.location.file_path, file_pattern)]
        
        return filtered


def main():
    """Main function for testing the issue reporting system"""
    system = ComprehensiveIssueReportingSystem()
    
    # Create sample issues for testing
    sample_issues = [
        system.create_issue(
            issue_type=IssueType.SYNTAX_ERROR,
            severity=IssueSeverity.CRITICAL,
            title="Python syntax error in main module",
            description="Invalid syntax: missing colon after if statement",
            file_path="backend/app.py",
            line_number=42,
            tool="python_analyzer",
            code_snippet="if condition\n    print('hello')"
        ),
        system.create_issue(
            issue_type=IssueType.UBUNTU_COMPATIBILITY,
            severity=IssueSeverity.HIGH,
            title="Ubuntu incompatible package manager command",
            description="Using yum instead of apt-get in deployment script",
            file_path="scripts/deploy.sh",
            line_number=15,
            tool="deployment_analyzer"
        ),
        system.create_issue(
            issue_type=IssueType.UNUSED_IMPORT,
            severity=IssueSeverity.LOW,
            title="Unused React import",
            description="Import 'useState' is not used in component",
            file_path="frontend/src/components/Header.tsx",
            line_number=3,
            tool="typescript_analyzer"
        )
    ]
    
    # Generate comprehensive reports
    reports = system.generate_comprehensive_report(sample_issues)
    
    print("Generated reports:")
    for format_type, filepath in reports.items():
        print(f"  {format_type}: {filepath}")
    
    # Print summary to console
    summary = system.report_generator.generate_report(sample_issues, "summary")
    print("\n" + summary)


if __name__ == "__main__":
    main()