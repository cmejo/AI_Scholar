#!/usr/bin/env python3
"""
Test script for Docker and Deployment Configuration Validator

This script tests the functionality of the docker_deployment_validator.py
to ensure it correctly identifies issues in Docker configurations, docker-compose files,
deployment scripts, and environment configurations.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add the scripts directory to the path so we can import our validator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docker_deployment_validator import (
    DockerDeploymentValidator,
    DockerfileAnalyzer,
    DockerComposeAnalyzer,
    DeploymentScriptAnalyzer,
    EnvironmentConfigAnalyzer,
    IssueSeverity,
    IssueType
)


class TestDockerfileAnalyzer(unittest.TestCase):
    """Test cases for Dockerfile analysis"""
    
    def setUp(self):
        self.analyzer = DockerfileAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_temp_dockerfile(self, content: str) -> str:
        """Create a temporary Dockerfile with given content"""
        dockerfile_path = os.path.join(self.temp_dir, "Dockerfile")
        with open(dockerfile_path, 'w') as f:
            f.write(content)
        return dockerfile_path
    
    def test_ubuntu_compatible_base_image(self):
        """Test that Ubuntu-compatible base images don't trigger warnings"""
        content = """
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y python3
"""
        dockerfile_path = self.create_temp_dockerfile(content)
        issues = self.analyzer.analyze_dockerfile(dockerfile_path)
        
        # Should not have base image compatibility issues
        base_image_issues = [i for i in issues if i.rule_id == "DOCKERFILE_BASE_COMPATIBILITY"]
        self.assertEqual(len(base_image_issues), 0)
    
    def test_incompatible_base_image(self):
        """Test that incompatible base images trigger warnings"""
        content = """
FROM centos:7
RUN yum install -y python3
"""
        dockerfile_path = self.create_temp_dockerfile(content)
        issues = self.analyzer.analyze_dockerfile(dockerfile_path)
        
        # Should have base image compatibility issue
        base_image_issues = [i for i in issues if i.rule_id == "DOCKERFILE_BASE_COMPATIBILITY"]
        self.assertGreater(len(base_image_issues), 0)
        self.assertTrue(base_image_issues[0].ubuntu_specific)
    
    def test_deprecated_maintainer(self):
        """Test detection of deprecated MAINTAINER instruction"""
        content = """
FROM ubuntu:24.04
MAINTAINER test@example.com
"""
        dockerfile_path = self.create_temp_dockerfile(content)
        issues = self.analyzer.analyze_dockerfile(dockerfile_path)
        
        # Should detect deprecated command
        deprecated_issues = [i for i in issues if i.rule_id == "DOCKERFILE_DEPRECATED_CMD"]
        self.assertGreater(len(deprecated_issues), 0)
    
    def test_apt_without_update(self):
        """Test detection of apt-get install without update"""
        content = """
FROM ubuntu:24.04
RUN apt-get install -y python3
"""
        dockerfile_path = self.create_temp_dockerfile(content)
        issues = self.analyzer.analyze_dockerfile(dockerfile_path)
        
        # Should detect apt without update
        apt_issues = [i for i in issues if i.rule_id == "DOCKERFILE_APT_UPDATE"]
        self.assertGreater(len(apt_issues), 0)
        self.assertTrue(apt_issues[0].ubuntu_specific)
    
    def test_missing_healthcheck(self):
        """Test detection of missing HEALTHCHECK"""
        content = """
FROM ubuntu:24.04
EXPOSE 8000
"""
        dockerfile_path = self.create_temp_dockerfile(content)
        issues = self.analyzer.analyze_dockerfile(dockerfile_path)
        
        # Should detect missing healthcheck
        healthcheck_issues = [i for i in issues if i.rule_id == "DOCKERFILE_MISSING_HEALTHCHECK"]
        self.assertGreater(len(healthcheck_issues), 0)


class TestDockerComposeAnalyzer(unittest.TestCase):
    """Test cases for docker-compose analysis"""
    
    def setUp(self):
        self.analyzer = DockerComposeAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_temp_compose_file(self, content: str) -> str:
        """Create a temporary docker-compose file with given content"""
        compose_path = os.path.join(self.temp_dir, "docker-compose.yml")
        with open(compose_path, 'w') as f:
            f.write(content)
        return compose_path
    
    def test_valid_compose_file(self):
        """Test that a valid compose file doesn't trigger major issues"""
        content = """
version: '3.8'
services:
  web:
    image: nginx:alpine
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost"]
      interval: 30s
      timeout: 10s
      retries: 3
"""
        compose_path = self.create_temp_compose_file(content)
        issues = self.analyzer.analyze_compose_file(compose_path)
        
        # Should not have critical issues
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        self.assertEqual(len(critical_issues), 0)
    
    def test_missing_version(self):
        """Test detection of missing version field"""
        content = """
services:
  web:
    image: nginx:alpine
"""
        compose_path = self.create_temp_compose_file(content)
        issues = self.analyzer.analyze_compose_file(compose_path)
        
        # Should detect missing version
        version_issues = [i for i in issues if "version" in i.description.lower()]
        self.assertGreater(len(version_issues), 0)
    
    def test_service_without_image_or_build(self):
        """Test detection of service without image or build"""
        content = """
version: '3.8'
services:
  web:
    restart: unless-stopped
"""
        compose_path = self.create_temp_compose_file(content)
        issues = self.analyzer.analyze_compose_file(compose_path)
        
        # Should detect missing image/build
        image_issues = [i for i in issues if i.rule_id == "COMPOSE_SERVICE_NO_IMAGE"]
        self.assertGreater(len(image_issues), 0)
    
    def test_privileged_mode_warning(self):
        """Test detection of privileged mode"""
        content = """
version: '3.8'
services:
  web:
    image: nginx:alpine
    privileged: true
"""
        compose_path = self.create_temp_compose_file(content)
        issues = self.analyzer.analyze_compose_file(compose_path)
        
        # Should detect privileged mode security issue
        privileged_issues = [i for i in issues if i.rule_id == "COMPOSE_PRIVILEGED_MODE"]
        self.assertGreater(len(privileged_issues), 0)
        self.assertEqual(privileged_issues[0].issue_type, IssueType.SECURITY_ISSUE)
    
    def test_invalid_yaml(self):
        """Test handling of invalid YAML"""
        content = """
version: '3.8'
services:
  web:
    image: nginx:alpine
    ports:
      - 80:80
    - 443:443  # Invalid YAML - missing port mapping
"""
        compose_path = self.create_temp_compose_file(content)
        issues = self.analyzer.analyze_compose_file(compose_path)
        
        # Should detect YAML error
        yaml_issues = [i for i in issues if i.rule_id == "COMPOSE_YAML_ERROR"]
        self.assertGreater(len(yaml_issues), 0)
        self.assertEqual(yaml_issues[0].severity, IssueSeverity.CRITICAL)


class TestDeploymentScriptAnalyzer(unittest.TestCase):
    """Test cases for deployment script analysis"""
    
    def setUp(self):
        self.analyzer = DeploymentScriptAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_temp_script(self, content: str) -> str:
        """Create a temporary script file with given content"""
        script_path = os.path.join(self.temp_dir, "deploy.sh")
        with open(script_path, 'w') as f:
            f.write(content)
        return script_path
    
    def test_missing_shebang(self):
        """Test detection of missing shebang"""
        content = """
echo "Deploying application..."
docker-compose up -d
"""
        script_path = self.create_temp_script(content)
        issues = self.analyzer.analyze_script(script_path)
        
        # Should detect missing shebang
        shebang_issues = [i for i in issues if i.rule_id == "SCRIPT_MISSING_SHEBANG"]
        self.assertGreater(len(shebang_issues), 0)
        self.assertTrue(shebang_issues[0].ubuntu_specific)
    
    def test_ubuntu_incompatible_commands(self):
        """Test detection of Ubuntu incompatible commands"""
        content = """#!/bin/bash
yum install -y docker
systemctl start docker
"""
        script_path = self.create_temp_script(content)
        issues = self.analyzer.analyze_script(script_path)
        
        # Should detect Ubuntu incompatible commands
        ubuntu_issues = [i for i in issues if i.rule_id == "SCRIPT_UBUNTU_INCOMPATIBLE"]
        self.assertGreater(len(ubuntu_issues), 0)
        self.assertTrue(all(issue.ubuntu_specific for issue in ubuntu_issues))
    
    def test_dangerous_rm_command(self):
        """Test detection of dangerous rm commands"""
        content = """#!/bin/bash
rm -rf /
"""
        script_path = self.create_temp_script(content)
        issues = self.analyzer.analyze_script(script_path)
        
        # Should detect dangerous rm command
        dangerous_issues = [i for i in issues if i.rule_id == "SCRIPT_DANGEROUS_RM"]
        self.assertGreater(len(dangerous_issues), 0)
        self.assertEqual(dangerous_issues[0].severity, IssueSeverity.CRITICAL)
    
    def test_valid_ubuntu_script(self):
        """Test that a valid Ubuntu script doesn't trigger major issues"""
        content = """#!/bin/bash
set -e

echo "Deploying on Ubuntu..."
apt-get update
apt-get install -y docker.io
docker --version
"""
        script_path = self.create_temp_script(content)
        issues = self.analyzer.analyze_script(script_path)
        
        # Should not have critical Ubuntu compatibility issues
        critical_ubuntu_issues = [i for i in issues 
                                if i.severity == IssueSeverity.CRITICAL and i.ubuntu_specific]
        self.assertEqual(len(critical_ubuntu_issues), 0)


class TestEnvironmentConfigAnalyzer(unittest.TestCase):
    """Test cases for environment configuration analysis"""
    
    def setUp(self):
        self.analyzer = EnvironmentConfigAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_temp_env_file(self, content: str) -> str:
        """Create a temporary .env file with given content"""
        env_path = os.path.join(self.temp_dir, ".env")
        with open(env_path, 'w') as f:
            f.write(content)
        return env_path
    
    def test_valid_env_file(self):
        """Test that a valid env file doesn't trigger major issues"""
        content = """
# Database configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp

# Application settings
DEBUG=false
LOG_LEVEL=info
"""
        env_path = self.create_temp_env_file(content)
        issues = self.analyzer.analyze_env_file(env_path)
        
        # Should not have critical issues
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        self.assertEqual(len(critical_issues), 0)
    
    def test_sensitive_data_exposure(self):
        """Test detection of sensitive data in env files"""
        content = """
DB_PASSWORD=secret123
API_KEY=abc123def456
SECRET_TOKEN=mysecrettoken
"""
        env_path = self.create_temp_env_file(content)
        issues = self.analyzer.analyze_env_file(env_path)
        
        # Should detect sensitive data exposure
        sensitive_issues = [i for i in issues if i.rule_id == "ENV_SENSITIVE_DATA"]
        self.assertGreater(len(sensitive_issues), 0)
        self.assertTrue(all(issue.issue_type == IssueType.SECURITY_ISSUE for issue in sensitive_issues))
    
    def test_duplicate_variables(self):
        """Test detection of duplicate environment variables"""
        content = """
DB_HOST=localhost
DB_PORT=5432
DB_HOST=127.0.0.1
"""
        env_path = self.create_temp_env_file(content)
        issues = self.analyzer.analyze_env_file(env_path)
        
        # Should detect duplicate variables
        duplicate_issues = [i for i in issues if i.rule_id == "ENV_DUPLICATE_VAR"]
        self.assertGreater(len(duplicate_issues), 0)
    
    def test_invalid_format(self):
        """Test detection of invalid environment variable format"""
        content = """
DB_HOST=localhost
INVALID_LINE_WITHOUT_EQUALS
DB_PORT=5432
"""
        env_path = self.create_temp_env_file(content)
        issues = self.analyzer.analyze_env_file(env_path)
        
        # Should detect invalid format
        format_issues = [i for i in issues if i.rule_id == "ENV_INVALID_FORMAT"]
        self.assertGreater(len(format_issues), 0)
    
    def test_empty_values(self):
        """Test detection of empty environment variable values"""
        content = """
DB_HOST=localhost
DB_PASSWORD=
API_KEY=
"""
        env_path = self.create_temp_env_file(content)
        issues = self.analyzer.analyze_env_file(env_path)
        
        # Should detect empty values
        empty_issues = [i for i in issues if i.rule_id == "ENV_EMPTY_VALUE"]
        self.assertGreater(len(empty_issues), 0)


class TestDockerDeploymentValidator(unittest.TestCase):
    """Integration tests for the main validator"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.validator = DockerDeploymentValidator(self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_project_structure(self):
        """Create a test project structure with various files"""
        # Create Dockerfile
        dockerfile_content = """
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y python3
EXPOSE 8000
"""
        with open(os.path.join(self.temp_dir, "Dockerfile"), 'w') as f:
            f.write(dockerfile_content)
        
        # Create docker-compose.yml
        compose_content = """
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    restart: unless-stopped
"""
        with open(os.path.join(self.temp_dir, "docker-compose.yml"), 'w') as f:
            f.write(compose_content)
        
        # Create deployment script
        script_content = """#!/bin/bash
echo "Deploying application..."
docker-compose up -d
"""
        script_path = os.path.join(self.temp_dir, "deploy.sh")
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        
        # Create .env file
        env_content = """
DB_HOST=localhost
DB_PORT=5432
DEBUG=true
"""
        with open(os.path.join(self.temp_dir, ".env"), 'w') as f:
            f.write(env_content)
    
    def test_comprehensive_validation(self):
        """Test comprehensive validation of a project"""
        self.create_test_project_structure()
        
        result = self.validator.validate_all()
        
        # Should analyze all files
        self.assertGreater(result.files_analyzed, 0)
        
        # Should find some issues (missing healthcheck, etc.)
        self.assertGreater(result.total_issues, 0)
        
        # Verify issue counts add up
        total_calculated = (result.critical_issues + result.high_issues + 
                          result.medium_issues + result.low_issues + result.info_issues)
        self.assertEqual(total_calculated, result.total_issues)
    
    def test_report_generation(self):
        """Test report generation functionality"""
        self.create_test_project_structure()
        
        result = self.validator.validate_all()
        report = self.validator.generate_report(result)
        
        # Report should contain expected sections
        self.assertIn("# Docker and Deployment Configuration Validation Report", report)
        self.assertIn("## Summary", report)
        self.assertIn(f"Files analyzed: {result.files_analyzed}", report)
        self.assertIn(f"Total issues: {result.total_issues}", report)


def run_validation_demo():
    """Run a demonstration of the validator on the actual project"""
    print("=" * 60)
    print("Docker and Deployment Configuration Validator Demo")
    print("=" * 60)
    
    # Run validator on the current project
    validator = DockerDeploymentValidator(".")
    result = validator.validate_all()
    
    print(f"\nValidation Results:")
    print(f"- Files analyzed: {result.files_analyzed}")
    print(f"- Total issues found: {result.total_issues}")
    print(f"- Critical: {result.critical_issues}")
    print(f"- High: {result.high_issues}")
    print(f"- Medium: {result.medium_issues}")
    print(f"- Low: {result.low_issues}")
    print(f"- Info: {result.info_issues}")
    
    # Show some example issues
    if result.issues:
        print(f"\nExample Issues (showing first 5):")
        for i, issue in enumerate(result.issues[:5]):
            print(f"\n{i+1}. {issue.file_path}")
            print(f"   Type: {issue.issue_type.value}")
            print(f"   Severity: {issue.severity.value}")
            print(f"   Description: {issue.description}")
            if issue.ubuntu_specific:
                print(f"   Ubuntu Specific: Yes")
    
    # Generate report
    report_file = "docker_deployment_validation_report.md"
    validator.generate_report(result, report_file)
    print(f"\nDetailed report saved to: {report_file}")
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Docker Deployment Validator")
    parser.add_argument("--demo", action="store_true", help="Run validation demo on current project")
    parser.add_argument("--test", action="store_true", help="Run unit tests")
    
    args = parser.parse_args()
    
    if args.demo:
        run_validation_demo()
    elif args.test:
        # Run unit tests
        unittest.main(argv=[''], exit=False, verbosity=2)
    else:
        # Run both by default
        print("Running unit tests...")
        unittest.main(argv=[''], exit=False, verbosity=2)
        print("\n" + "="*60)
        run_validation_demo()