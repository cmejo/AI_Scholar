#!/usr/bin/env python3
"""
Docker and Deployment Configuration Validator

This script validates Docker configurations, docker-compose files, deployment scripts,
and environment configurations for Ubuntu compatibility and best practices.

Requirements covered:
- 3.1: Ubuntu-compatible Docker configurations
- 3.2: Docker-compose service definitions and networking
- 3.3: Ubuntu shell compatibility for deployment scripts
- 3.4: Environment variable and configuration validation
"""

import os
import re
import json
import yaml
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class IssueSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueType(Enum):
    DOCKERFILE_ISSUE = "dockerfile_issue"
    DOCKER_COMPOSE_ISSUE = "docker_compose_issue"
    DEPLOYMENT_SCRIPT_ISSUE = "deployment_script_issue"
    ENVIRONMENT_CONFIG_ISSUE = "environment_config_issue"
    UBUNTU_COMPATIBILITY = "ubuntu_compatibility"
    SECURITY_ISSUE = "security_issue"
    PERFORMANCE_ISSUE = "performance_issue"


@dataclass
class ValidationIssue:
    """Represents a validation issue found during analysis"""
    file_path: str
    line_number: Optional[int]
    issue_type: IssueType
    severity: IssueSeverity
    description: str
    recommendation: str
    ubuntu_specific: bool = False
    auto_fixable: bool = False
    rule_id: str = ""


@dataclass
class ValidationResult:
    """Contains the results of validation analysis"""
    issues: List[ValidationIssue] = field(default_factory=list)
    files_analyzed: int = 0
    total_issues: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    info_issues: int = 0


class DockerfileAnalyzer:
    """Analyzes Dockerfile configurations for Ubuntu compatibility and best practices"""
    
    def __init__(self):
        self.ubuntu_compatible_bases = {
            'ubuntu:24.04', 'ubuntu:22.04', 'ubuntu:20.04',
            'python:3.11-slim', 'python:3.10-slim', 'python:3.9-slim',
            'node:20-alpine', 'node:18-alpine', 'node:16-alpine',
            'nginx:alpine', 'redis:alpine', 'postgres:15-alpine'
        }
        
        self.deprecated_commands = {
            'MAINTAINER': 'Use LABEL maintainer instead',
            'ADD': 'Use COPY instead unless you need ADD specific features'
        }
        
        self.security_issues = {
            'USER root': 'Avoid running containers as root user',
            'chmod 777': 'Avoid overly permissive file permissions',
            'wget': 'Consider using COPY or ADD instead of downloading in containers'
        }

    def analyze_dockerfile(self, dockerfile_path: str) -> List[ValidationIssue]:
        """Analyze a single Dockerfile for issues"""
        issues = []
        
        if not os.path.exists(dockerfile_path):
            return issues
            
        try:
            with open(dockerfile_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=dockerfile_path,
                line_number=None,
                issue_type=IssueType.DOCKERFILE_ISSUE,
                severity=IssueSeverity.HIGH,
                description=f"Failed to read Dockerfile: {str(e)}",
                recommendation="Ensure file exists and is readable",
                rule_id="DOCKERFILE_READ_ERROR"
            ))
            return issues
        
        # Analyze each line
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Check base image compatibility
            if line.upper().startswith('FROM'):
                issues.extend(self._check_base_image(dockerfile_path, line_num, line))
            
            # Check for deprecated commands
            for deprecated_cmd, suggestion in self.deprecated_commands.items():
                if line.upper().startswith(deprecated_cmd):
                    issues.append(ValidationIssue(
                        file_path=dockerfile_path,
                        line_number=line_num,
                        issue_type=IssueType.DOCKERFILE_ISSUE,
                        severity=IssueSeverity.MEDIUM,
                        description=f"Deprecated command: {deprecated_cmd}",
                        recommendation=suggestion,
                        rule_id="DOCKERFILE_DEPRECATED_CMD"
                    ))
            
            # Check for security issues
            for security_pattern, warning in self.security_issues.items():
                if security_pattern.lower() in line.lower():
                    issues.append(ValidationIssue(
                        file_path=dockerfile_path,
                        line_number=line_num,
                        issue_type=IssueType.SECURITY_ISSUE,
                        severity=IssueSeverity.HIGH,
                        description=f"Security concern: {security_pattern}",
                        recommendation=warning,
                        rule_id="DOCKERFILE_SECURITY"
                    ))
            
            # Check Ubuntu-specific package management
            if 'apt-get' in line.lower():
                issues.extend(self._check_apt_usage(dockerfile_path, line_num, line))
            
            # Check for missing health checks
            if line.upper().startswith('EXPOSE'):
                # This is a simplified check - in practice, you'd track if HEALTHCHECK follows
                pass
        
        # Check for missing essential instructions
        dockerfile_content = ''.join(lines).upper()
        if 'HEALTHCHECK' not in dockerfile_content:
            issues.append(ValidationIssue(
                file_path=dockerfile_path,
                line_number=None,
                issue_type=IssueType.DOCKERFILE_ISSUE,
                severity=IssueSeverity.MEDIUM,
                description="Missing HEALTHCHECK instruction",
                recommendation="Add HEALTHCHECK instruction for better container monitoring",
                rule_id="DOCKERFILE_MISSING_HEALTHCHECK"
            ))
        
        return issues
    
    def _check_base_image(self, file_path: str, line_num: int, line: str) -> List[ValidationIssue]:
        """Check if base image is Ubuntu compatible"""
        issues = []
        
        # Extract image name from FROM instruction
        parts = line.split()
        if len(parts) < 2:
            return issues
            
        image = parts[1].lower()
        
        # Check if it's a known Ubuntu-compatible base
        is_compatible = any(base in image for base in self.ubuntu_compatible_bases)
        
        if not is_compatible:
            # Check for potentially problematic bases
            if any(problematic in image for problematic in ['centos', 'rhel', 'fedora']):
                issues.append(ValidationIssue(
                    file_path=file_path,
                    line_number=line_num,
                    issue_type=IssueType.UBUNTU_COMPATIBILITY,
                    severity=IssueSeverity.HIGH,
                    description=f"Base image may not be Ubuntu compatible: {image}",
                    recommendation="Consider using Ubuntu-based images for better compatibility",
                    ubuntu_specific=True,
                    rule_id="DOCKERFILE_BASE_COMPATIBILITY"
                ))
        
        return issues
    
    def _check_apt_usage(self, file_path: str, line_num: int, line: str) -> List[ValidationIssue]:
        """Check apt-get usage for Ubuntu best practices"""
        issues = []
        
        # Check for missing apt-get update
        if 'apt-get install' in line.lower() and 'apt-get update' not in line.lower():
            issues.append(ValidationIssue(
                file_path=file_path,
                line_number=line_num,
                issue_type=IssueType.DOCKERFILE_ISSUE,
                severity=IssueSeverity.MEDIUM,
                description="apt-get install without update",
                recommendation="Run 'apt-get update' before 'apt-get install'",
                ubuntu_specific=True,
                rule_id="DOCKERFILE_APT_UPDATE"
            ))
        
        # Check for missing cleanup
        if 'apt-get install' in line.lower() and 'rm -rf /var/lib/apt/lists/*' not in line.lower():
            issues.append(ValidationIssue(
                file_path=file_path,
                line_number=line_num,
                issue_type=IssueType.DOCKERFILE_ISSUE,
                severity=IssueSeverity.LOW,
                description="Missing apt cache cleanup",
                recommendation="Add '&& rm -rf /var/lib/apt/lists/*' to reduce image size",
                ubuntu_specific=True,
                rule_id="DOCKERFILE_APT_CLEANUP"
            ))
        
        return issues


class DockerComposeAnalyzer:
    """Analyzes docker-compose configurations for service definitions and networking"""
    
    def __init__(self):
        self.required_fields = ['version', 'services']
        self.service_required_fields = ['image', 'build']  # At least one required
        
    def analyze_compose_file(self, compose_path: str) -> List[ValidationIssue]:
        """Analyze a docker-compose file for issues"""
        issues = []
        
        if not os.path.exists(compose_path):
            return issues
        
        try:
            with open(compose_path, 'r', encoding='utf-8') as f:
                compose_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            issues.append(ValidationIssue(
                file_path=compose_path,
                line_number=None,
                issue_type=IssueType.DOCKER_COMPOSE_ISSUE,
                severity=IssueSeverity.CRITICAL,
                description=f"Invalid YAML syntax: {str(e)}",
                recommendation="Fix YAML syntax errors",
                rule_id="COMPOSE_YAML_ERROR"
            ))
            return issues
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=compose_path,
                line_number=None,
                issue_type=IssueType.DOCKER_COMPOSE_ISSUE,
                severity=IssueSeverity.HIGH,
                description=f"Failed to read compose file: {str(e)}",
                recommendation="Ensure file exists and is readable",
                rule_id="COMPOSE_READ_ERROR"
            ))
            return issues
        
        if not isinstance(compose_data, dict):
            issues.append(ValidationIssue(
                file_path=compose_path,
                line_number=None,
                issue_type=IssueType.DOCKER_COMPOSE_ISSUE,
                severity=IssueSeverity.CRITICAL,
                description="Invalid compose file structure",
                recommendation="Ensure compose file has proper YAML structure",
                rule_id="COMPOSE_STRUCTURE_ERROR"
            ))
            return issues
        
        # Check required top-level fields
        for field in self.required_fields:
            if field not in compose_data:
                issues.append(ValidationIssue(
                    file_path=compose_path,
                    line_number=None,
                    issue_type=IssueType.DOCKER_COMPOSE_ISSUE,
                    severity=IssueSeverity.HIGH,
                    description=f"Missing required field: {field}",
                    recommendation=f"Add {field} field to compose file",
                    rule_id="COMPOSE_MISSING_FIELD"
                ))
        
        # Check version compatibility
        if 'version' in compose_data:
            issues.extend(self._check_version_compatibility(compose_path, compose_data['version']))
        
        # Analyze services
        if 'services' in compose_data:
            issues.extend(self._analyze_services(compose_path, compose_data['services']))
        
        # Check networks configuration
        if 'networks' in compose_data:
            issues.extend(self._analyze_networks(compose_path, compose_data['networks']))
        
        # Check volumes configuration
        if 'volumes' in compose_data:
            issues.extend(self._analyze_volumes(compose_path, compose_data['volumes']))
        
        return issues
    
    def _check_version_compatibility(self, file_path: str, version: str) -> List[ValidationIssue]:
        """Check docker-compose version compatibility"""
        issues = []
        
        try:
            version_num = float(version)
            if version_num < 3.0:
                issues.append(ValidationIssue(
                    file_path=file_path,
                    line_number=None,
                    issue_type=IssueType.DOCKER_COMPOSE_ISSUE,
                    severity=IssueSeverity.MEDIUM,
                    description=f"Old compose version: {version}",
                    recommendation="Consider upgrading to version 3.x for better features",
                    rule_id="COMPOSE_OLD_VERSION"
                ))
        except ValueError:
            issues.append(ValidationIssue(
                file_path=file_path,
                line_number=None,
                issue_type=IssueType.DOCKER_COMPOSE_ISSUE,
                severity=IssueSeverity.HIGH,
                description=f"Invalid version format: {version}",
                recommendation="Use valid version format (e.g., '3.8')",
                rule_id="COMPOSE_INVALID_VERSION"
            ))
        
        return issues
    
    def _analyze_services(self, file_path: str, services: Dict) -> List[ValidationIssue]:
        """Analyze services configuration"""
        issues = []
        
        if not isinstance(services, dict):
            issues.append(ValidationIssue(
                file_path=file_path,
                line_number=None,
                issue_type=IssueType.DOCKER_COMPOSE_ISSUE,
                severity=IssueSeverity.HIGH,
                description="Services must be a dictionary",
                recommendation="Fix services structure",
                rule_id="COMPOSE_SERVICES_STRUCTURE"
            ))
            return issues
        
        for service_name, service_config in services.items():
            if not isinstance(service_config, dict):
                continue
            
            # Check if service has image or build
            if 'image' not in service_config and 'build' not in service_config:
                issues.append(ValidationIssue(
                    file_path=file_path,
                    line_number=None,
                    issue_type=IssueType.DOCKER_COMPOSE_ISSUE,
                    severity=IssueSeverity.HIGH,
                    description=f"Service '{service_name}' missing image or build",
                    recommendation="Add either 'image' or 'build' configuration",
                    rule_id="COMPOSE_SERVICE_NO_IMAGE"
                ))
            
            # Check for security issues
            if 'privileged' in service_config and service_config['privileged']:
                issues.append(ValidationIssue(
                    file_path=file_path,
                    line_number=None,
                    issue_type=IssueType.SECURITY_ISSUE,
                    severity=IssueSeverity.HIGH,
                    description=f"Service '{service_name}' runs in privileged mode",
                    recommendation="Avoid privileged mode unless absolutely necessary",
                    rule_id="COMPOSE_PRIVILEGED_MODE"
                ))
            
            # Check restart policy
            if 'restart' not in service_config:
                issues.append(ValidationIssue(
                    file_path=file_path,
                    line_number=None,
                    issue_type=IssueType.DOCKER_COMPOSE_ISSUE,
                    severity=IssueSeverity.LOW,
                    description=f"Service '{service_name}' missing restart policy",
                    recommendation="Add restart policy (e.g., 'unless-stopped')",
                    rule_id="COMPOSE_NO_RESTART_POLICY"
                ))
            
            # Check health checks
            if 'healthcheck' not in service_config:
                issues.append(ValidationIssue(
                    file_path=file_path,
                    line_number=None,
                    issue_type=IssueType.DOCKER_COMPOSE_ISSUE,
                    severity=IssueSeverity.MEDIUM,
                    description=f"Service '{service_name}' missing health check",
                    recommendation="Add healthcheck configuration for better monitoring",
                    rule_id="COMPOSE_NO_HEALTHCHECK"
                ))
            
            # Check environment variables
            if 'environment' in service_config:
                issues.extend(self._check_environment_vars(file_path, service_name, service_config['environment']))
        
        return issues
    
    def _analyze_networks(self, file_path: str, networks: Dict) -> List[ValidationIssue]:
        """Analyze networks configuration"""
        issues = []
        
        for network_name, network_config in networks.items():
            if isinstance(network_config, dict):
                # Check for external networks without proper configuration
                if network_config.get('external') and not network_config.get('name'):
                    issues.append(ValidationIssue(
                        file_path=file_path,
                        line_number=None,
                        issue_type=IssueType.DOCKER_COMPOSE_ISSUE,
                        severity=IssueSeverity.MEDIUM,
                        description=f"External network '{network_name}' missing name",
                        recommendation="Specify network name for external networks",
                        rule_id="COMPOSE_EXTERNAL_NETWORK_NAME"
                    ))
        
        return issues
    
    def _analyze_volumes(self, file_path: str, volumes: Dict) -> List[ValidationIssue]:
        """Analyze volumes configuration"""
        issues = []
        
        for volume_name, volume_config in volumes.items():
            if isinstance(volume_config, dict):
                # Check for external volumes
                if volume_config.get('external') and not volume_config.get('name'):
                    issues.append(ValidationIssue(
                        file_path=file_path,
                        line_number=None,
                        issue_type=IssueType.DOCKER_COMPOSE_ISSUE,
                        severity=IssueSeverity.MEDIUM,
                        description=f"External volume '{volume_name}' missing name",
                        recommendation="Specify volume name for external volumes",
                        rule_id="COMPOSE_EXTERNAL_VOLUME_NAME"
                    ))
        
        return issues
    
    def _check_environment_vars(self, file_path: str, service_name: str, env_vars) -> List[ValidationIssue]:
        """Check environment variables configuration"""
        issues = []
        
        if isinstance(env_vars, list):
            for env_var in env_vars:
                if isinstance(env_var, str) and '=' in env_var:
                    key, value = env_var.split('=', 1)
                    if not value or value.strip() == '':
                        issues.append(ValidationIssue(
                            file_path=file_path,
                            line_number=None,
                            issue_type=IssueType.ENVIRONMENT_CONFIG_ISSUE,
                            severity=IssueSeverity.MEDIUM,
                            description=f"Empty environment variable '{key}' in service '{service_name}'",
                            recommendation="Provide value or use env_file for sensitive data",
                            rule_id="COMPOSE_EMPTY_ENV_VAR"
                        ))
        
        return issues


class DeploymentScriptAnalyzer:
    """Analyzes deployment scripts for Ubuntu shell compatibility"""
    
    def __init__(self):
        self.ubuntu_incompatible_commands = {
            'yum': 'Use apt-get for Ubuntu systems',
            'dnf': 'Use apt-get for Ubuntu systems',
            'systemctl': 'May not be available in containers, use service or direct commands',
            'chkconfig': 'Use update-rc.d for Ubuntu systems'
        }
        
        self.shell_compatibility_issues = {
            '#!/bin/sh': 'Consider using #!/bin/bash for better compatibility',
            'source ': 'Use . instead of source for POSIX compatibility',
            'function ': 'Use func() syntax instead of function keyword'
        }
    
    def analyze_script(self, script_path: str) -> List[ValidationIssue]:
        """Analyze a deployment script for Ubuntu compatibility"""
        issues = []
        
        if not os.path.exists(script_path):
            return issues
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=script_path,
                line_number=None,
                issue_type=IssueType.DEPLOYMENT_SCRIPT_ISSUE,
                severity=IssueSeverity.HIGH,
                description=f"Failed to read script: {str(e)}",
                recommendation="Ensure file exists and is readable",
                rule_id="SCRIPT_READ_ERROR"
            ))
            return issues
        
        # Check shebang
        if lines and not lines[0].startswith('#!'):
            issues.append(ValidationIssue(
                file_path=script_path,
                line_number=1,
                issue_type=IssueType.DEPLOYMENT_SCRIPT_ISSUE,
                severity=IssueSeverity.MEDIUM,
                description="Missing shebang line",
                recommendation="Add shebang line (e.g., #!/bin/bash)",
                ubuntu_specific=True,
                rule_id="SCRIPT_MISSING_SHEBANG"
            ))
        
        # Analyze each line
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith('#'):
                continue
            
            # Check for Ubuntu incompatible commands
            for cmd, suggestion in self.ubuntu_incompatible_commands.items():
                if cmd in line_stripped:
                    issues.append(ValidationIssue(
                        file_path=script_path,
                        line_number=line_num,
                        issue_type=IssueType.UBUNTU_COMPATIBILITY,
                        severity=IssueSeverity.HIGH,
                        description=f"Ubuntu incompatible command: {cmd}",
                        recommendation=suggestion,
                        ubuntu_specific=True,
                        rule_id="SCRIPT_UBUNTU_INCOMPATIBLE"
                    ))
            
            # Check shell compatibility
            for pattern, suggestion in self.shell_compatibility_issues.items():
                if pattern in line:
                    issues.append(ValidationIssue(
                        file_path=script_path,
                        line_number=line_num,
                        issue_type=IssueType.DEPLOYMENT_SCRIPT_ISSUE,
                        severity=IssueSeverity.LOW,
                        description=f"Shell compatibility issue: {pattern}",
                        recommendation=suggestion,
                        rule_id="SCRIPT_SHELL_COMPATIBILITY"
                    ))
            
            # Check for unsafe practices
            if 'rm -rf /' in line or 'rm -rf /*' in line:
                issues.append(ValidationIssue(
                    file_path=script_path,
                    line_number=line_num,
                    issue_type=IssueType.SECURITY_ISSUE,
                    severity=IssueSeverity.CRITICAL,
                    description="Dangerous rm command detected",
                    recommendation="Review and secure file deletion commands",
                    rule_id="SCRIPT_DANGEROUS_RM"
                ))
            
            # Check for hardcoded paths that might not exist on Ubuntu
            ubuntu_specific_paths = ['/usr/local/bin', '/opt', '/etc']
            for path in ubuntu_specific_paths:
                if path in line and 'test -' not in line and '[ -' not in line:
                    issues.append(ValidationIssue(
                        file_path=script_path,
                        line_number=line_num,
                        issue_type=IssueType.UBUNTU_COMPATIBILITY,
                        severity=IssueSeverity.LOW,
                        description=f"Hardcoded path may not exist: {path}",
                        recommendation="Check path existence before using",
                        ubuntu_specific=True,
                        rule_id="SCRIPT_HARDCODED_PATH"
                    ))
        
        return issues


class EnvironmentConfigAnalyzer:
    """Analyzes environment configuration files"""
    
    def __init__(self):
        self.sensitive_patterns = [
            'password', 'secret', 'key', 'token', 'api_key',
            'private_key', 'auth', 'credential'
        ]
    
    def analyze_env_file(self, env_path: str) -> List[ValidationIssue]:
        """Analyze environment configuration file"""
        issues = []
        
        if not os.path.exists(env_path):
            return issues
        
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=env_path,
                line_number=None,
                issue_type=IssueType.ENVIRONMENT_CONFIG_ISSUE,
                severity=IssueSeverity.HIGH,
                description=f"Failed to read env file: {str(e)}",
                recommendation="Ensure file exists and is readable",
                rule_id="ENV_READ_ERROR"
            ))
            return issues
        
        defined_vars = set()
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith('#'):
                continue
            
            if '=' not in line_stripped:
                issues.append(ValidationIssue(
                    file_path=env_path,
                    line_number=line_num,
                    issue_type=IssueType.ENVIRONMENT_CONFIG_ISSUE,
                    severity=IssueSeverity.MEDIUM,
                    description="Invalid environment variable format",
                    recommendation="Use KEY=value format",
                    rule_id="ENV_INVALID_FORMAT"
                ))
                continue
            
            key, value = line_stripped.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Check for duplicate variables
            if key in defined_vars:
                issues.append(ValidationIssue(
                    file_path=env_path,
                    line_number=line_num,
                    issue_type=IssueType.ENVIRONMENT_CONFIG_ISSUE,
                    severity=IssueSeverity.MEDIUM,
                    description=f"Duplicate environment variable: {key}",
                    recommendation="Remove duplicate variable definitions",
                    rule_id="ENV_DUPLICATE_VAR"
                ))
            
            defined_vars.add(key)
            
            # Check for sensitive data exposure
            if any(pattern in key.lower() for pattern in self.sensitive_patterns):
                if value and not value.startswith('${'):  # Not a reference
                    issues.append(ValidationIssue(
                        file_path=env_path,
                        line_number=line_num,
                        issue_type=IssueType.SECURITY_ISSUE,
                        severity=IssueSeverity.HIGH,
                        description=f"Sensitive data in environment file: {key}",
                        recommendation="Use environment variable references or external secrets",
                        rule_id="ENV_SENSITIVE_DATA"
                    ))
            
            # Check for empty values
            if not value:
                issues.append(ValidationIssue(
                    file_path=env_path,
                    line_number=line_num,
                    issue_type=IssueType.ENVIRONMENT_CONFIG_ISSUE,
                    severity=IssueSeverity.LOW,
                    description=f"Empty environment variable: {key}",
                    recommendation="Provide default value or remove unused variable",
                    rule_id="ENV_EMPTY_VALUE"
                ))
        
        return issues


class DockerDeploymentValidator:
    """Main validator class that orchestrates all analysis"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.dockerfile_analyzer = DockerfileAnalyzer()
        self.compose_analyzer = DockerComposeAnalyzer()
        self.script_analyzer = DeploymentScriptAnalyzer()
        self.env_analyzer = EnvironmentConfigAnalyzer()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_all(self) -> ValidationResult:
        """Run comprehensive validation on all Docker and deployment configurations"""
        result = ValidationResult()
        
        self.logger.info("Starting Docker and deployment configuration validation...")
        
        # Find and analyze Dockerfiles
        dockerfile_patterns = ['**/Dockerfile*', 'Dockerfile*']
        dockerfiles = []
        for pattern in dockerfile_patterns:
            dockerfiles.extend(self.project_root.glob(pattern))
        
        self.logger.info(f"Found {len(dockerfiles)} Dockerfile(s)")
        for dockerfile in dockerfiles:
            if dockerfile.is_file():
                issues = self.dockerfile_analyzer.analyze_dockerfile(str(dockerfile))
                result.issues.extend(issues)
                result.files_analyzed += 1
        
        # Find and analyze docker-compose files
        compose_patterns = ['**/docker-compose*.yml', '**/docker-compose*.yaml']
        compose_files = []
        for pattern in compose_patterns:
            compose_files.extend(self.project_root.glob(pattern))
        
        self.logger.info(f"Found {len(compose_files)} docker-compose file(s)")
        for compose_file in compose_files:
            if compose_file.is_file():
                issues = self.compose_analyzer.analyze_compose_file(str(compose_file))
                result.issues.extend(issues)
                result.files_analyzed += 1
        
        # Find and analyze deployment scripts
        script_patterns = ['**/*deploy*.sh', '**/deploy*.sh', '**/*setup*.sh']
        script_files = []
        for pattern in script_patterns:
            script_files.extend(self.project_root.glob(pattern))
        
        self.logger.info(f"Found {len(script_files)} deployment script(s)")
        for script_file in script_files:
            if script_file.is_file():
                issues = self.script_analyzer.analyze_script(str(script_file))
                result.issues.extend(issues)
                result.files_analyzed += 1
        
        # Find and analyze environment files
        env_patterns = ['**/.env*', '**/env*', '**/*.env']
        env_files = []
        for pattern in env_patterns:
            env_files.extend(self.project_root.glob(pattern))
        
        # Filter out directories and common non-env files
        env_files = [f for f in env_files if f.is_file() and 
                    not any(exclude in f.name for exclude in ['.git', 'node_modules', '__pycache__'])]
        
        self.logger.info(f"Found {len(env_files)} environment file(s)")
        for env_file in env_files:
            issues = self.env_analyzer.analyze_env_file(str(env_file))
            result.issues.extend(issues)
            result.files_analyzed += 1
        
        # Calculate statistics
        result.total_issues = len(result.issues)
        for issue in result.issues:
            if issue.severity == IssueSeverity.CRITICAL:
                result.critical_issues += 1
            elif issue.severity == IssueSeverity.HIGH:
                result.high_issues += 1
            elif issue.severity == IssueSeverity.MEDIUM:
                result.medium_issues += 1
            elif issue.severity == IssueSeverity.LOW:
                result.low_issues += 1
            elif issue.severity == IssueSeverity.INFO:
                result.info_issues += 1
        
        self.logger.info(f"Validation complete. Found {result.total_issues} issues across {result.files_analyzed} files")
        
        return result
    
    def generate_report(self, result: ValidationResult, output_file: str = None) -> str:
        """Generate a detailed validation report"""
        report_lines = []
        
        # Header
        report_lines.append("# Docker and Deployment Configuration Validation Report")
        report_lines.append(f"Generated on: {os.popen('date').read().strip()}")
        report_lines.append("")
        
        # Summary
        report_lines.append("## Summary")
        report_lines.append(f"- Files analyzed: {result.files_analyzed}")
        report_lines.append(f"- Total issues: {result.total_issues}")
        report_lines.append(f"- Critical issues: {result.critical_issues}")
        report_lines.append(f"- High severity issues: {result.high_issues}")
        report_lines.append(f"- Medium severity issues: {result.medium_issues}")
        report_lines.append(f"- Low severity issues: {result.low_issues}")
        report_lines.append(f"- Info issues: {result.info_issues}")
        report_lines.append("")
        
        # Issues by severity
        for severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH, IssueSeverity.MEDIUM, IssueSeverity.LOW, IssueSeverity.INFO]:
            severity_issues = [issue for issue in result.issues if issue.severity == severity]
            if severity_issues:
                report_lines.append(f"## {severity.value.title()} Issues ({len(severity_issues)})")
                report_lines.append("")
                
                for issue in severity_issues:
                    report_lines.append(f"### {issue.file_path}")
                    if issue.line_number:
                        report_lines.append(f"**Line:** {issue.line_number}")
                    report_lines.append(f"**Type:** {issue.issue_type.value}")
                    report_lines.append(f"**Description:** {issue.description}")
                    report_lines.append(f"**Recommendation:** {issue.recommendation}")
                    if issue.ubuntu_specific:
                        report_lines.append("**Ubuntu Specific:** Yes")
                    if issue.auto_fixable:
                        report_lines.append("**Auto-fixable:** Yes")
                    if issue.rule_id:
                        report_lines.append(f"**Rule ID:** {issue.rule_id}")
                    report_lines.append("")
        
        # Ubuntu compatibility summary
        ubuntu_issues = [issue for issue in result.issues if issue.ubuntu_specific]
        if ubuntu_issues:
            report_lines.append(f"## Ubuntu Compatibility Issues ({len(ubuntu_issues)})")
            report_lines.append("")
            report_lines.append("The following issues are specific to Ubuntu compatibility:")
            report_lines.append("")
            
            for issue in ubuntu_issues:
                report_lines.append(f"- **{issue.file_path}**: {issue.description}")
        
        report_content = "\n".join(report_lines)
        
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                self.logger.info(f"Report saved to {output_file}")
            except Exception as e:
                self.logger.error(f"Failed to save report: {str(e)}")
        
        return report_content


def main():
    """Main function to run the validator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Docker and Deployment Configuration Validator")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--output", help="Output file for the report")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    validator = DockerDeploymentValidator(args.project_root)
    result = validator.validate_all()
    
    if args.json:
        # Convert result to JSON
        json_result = {
            "summary": {
                "files_analyzed": result.files_analyzed,
                "total_issues": result.total_issues,
                "critical_issues": result.critical_issues,
                "high_issues": result.high_issues,
                "medium_issues": result.medium_issues,
                "low_issues": result.low_issues,
                "info_issues": result.info_issues
            },
            "issues": [
                {
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "issue_type": issue.issue_type.value,
                    "severity": issue.severity.value,
                    "description": issue.description,
                    "recommendation": issue.recommendation,
                    "ubuntu_specific": issue.ubuntu_specific,
                    "auto_fixable": issue.auto_fixable,
                    "rule_id": issue.rule_id
                }
                for issue in result.issues
            ]
        }
        
        output_content = json.dumps(json_result, indent=2)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output_content)
        else:
            print(output_content)
    else:
        report = validator.generate_report(result, args.output)
        if not args.output:
            print(report)
    
    # Exit with error code if critical issues found
    if result.critical_issues > 0:
        exit(1)


if __name__ == "__main__":
    main()