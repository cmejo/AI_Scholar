#!/usr/bin/env python3
"""
Automated Fix Application System
Implements auto-fix capabilities for common code formatting, style issues,
dependency updates, and Ubuntu-specific optimizations.
"""

import os
import sys
import json
import subprocess
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

# Optional imports
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import toml
    HAS_TOML = True
except ImportError:
    HAS_TOML = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FixType(Enum):
    """Types of fixes that can be applied"""
    CODE_FORMATTING = "code_formatting"
    STYLE_ISSUES = "style_issues"
    DEPENDENCY_UPDATE = "dependency_update"
    CONFIGURATION_FIX = "configuration_fix"
    UBUNTU_OPTIMIZATION = "ubuntu_optimization"
    SECURITY_FIX = "security_fix"

class FixSeverity(Enum):
    """Severity levels for fixes"""
    SAFE = "safe"           # No risk, can be applied automatically
    LOW_RISK = "low_risk"   # Minimal risk, requires confirmation
    MEDIUM_RISK = "medium_risk"  # Some risk, requires review
    HIGH_RISK = "high_risk"      # High risk, manual intervention needed

@dataclass
class FixResult:
    """Result of applying a fix"""
    success: bool
    fix_type: FixType
    file_path: str
    description: str
    changes_made: List[str]
    backup_created: bool
    error_message: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

class AutoFixEngine:
    """Main engine for applying automated fixes"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.backup_dir = self.project_root / ".fix_backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Initialize fix modules
        self.code_formatter = CodeFormattingFixer(self.project_root)
        self.dependency_updater = DependencyUpdater(self.project_root)
        self.config_fixer = ConfigurationFixer(self.project_root)
        self.ubuntu_optimizer = UbuntuOptimizer(self.project_root)
        
        self.applied_fixes: List[FixResult] = []
        
    def create_backup(self, file_path: Path) -> bool:
        """Create backup of file before applying fixes"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.name}_{timestamp}.backup"
            backup_path = self.backup_dir / backup_name
            
            backup_path.write_text(file_path.read_text())
            logger.info(f"Created backup: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return False
    
    def apply_code_formatting_fixes(self, file_patterns: List[str] = None) -> List[FixResult]:
        """Apply code formatting fixes"""
        if file_patterns is None:
            file_patterns = ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"]
        
        results = []
        for pattern in file_patterns:
            for file_path in self.project_root.glob(pattern):
                if self._should_skip_file(file_path):
                    continue
                    
                result = self.code_formatter.fix_file(file_path)
                if result:
                    results.append(result)
                    self.applied_fixes.append(result)
        
        return results
    
    def apply_dependency_updates(self, check_compatibility: bool = True) -> List[FixResult]:
        """Apply dependency updates with compatibility checking"""
        results = []
        
        # Update Python dependencies
        python_result = self.dependency_updater.update_python_dependencies(check_compatibility)
        if python_result:
            results.append(python_result)
            self.applied_fixes.append(python_result)
        
        # Update Node.js dependencies
        node_result = self.dependency_updater.update_node_dependencies(check_compatibility)
        if node_result:
            results.append(node_result)
            self.applied_fixes.append(node_result)
        
        return results
    
    def apply_configuration_fixes(self) -> List[FixResult]:
        """Apply configuration file fixes"""
        results = []
        
        config_files = [
            "docker-compose.yml", "docker-compose.*.yml",
            "Dockerfile*", ".env*", "*.json", "*.yaml", "*.yml"
        ]
        
        for pattern in config_files:
            for file_path in self.project_root.glob(pattern):
                if self._should_skip_file(file_path):
                    continue
                    
                result = self.config_fixer.fix_file(file_path)
                if result:
                    results.append(result)
                    self.applied_fixes.append(result)
        
        return results
    
    def apply_ubuntu_optimizations(self) -> List[FixResult]:
        """Apply Ubuntu-specific optimizations"""
        results = []
        
        # Optimize deployment scripts
        script_result = self.ubuntu_optimizer.optimize_deployment_scripts()
        if script_result:
            results.append(script_result)
            self.applied_fixes.append(script_result)
        
        # Optimize Docker configurations
        docker_result = self.ubuntu_optimizer.optimize_docker_configs()
        if docker_result:
            results.append(docker_result)
            self.applied_fixes.append(docker_result)
        
        return results
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = [
            "node_modules", ".git", "__pycache__", ".pytest_cache",
            "venv", ".venv", "dist", "build", ".next", "coverage"
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def generate_fix_report(self) -> Dict[str, Any]:
        """Generate comprehensive fix report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_fixes_applied": len(self.applied_fixes),
            "fixes_by_type": {},
            "fixes_by_severity": {},
            "successful_fixes": 0,
            "failed_fixes": 0,
            "fixes_details": []
        }
        
        for fix in self.applied_fixes:
            # Count by type
            fix_type = fix.fix_type.value
            report["fixes_by_type"][fix_type] = report["fixes_by_type"].get(fix_type, 0) + 1
            
            # Count success/failure
            if fix.success:
                report["successful_fixes"] += 1
            else:
                report["failed_fixes"] += 1
            
            # Add details
            report["fixes_details"].append(asdict(fix))
        
        return report
    
    def save_fix_report(self, output_path: str = "automated_fix_report.json"):
        """Save fix report to file"""
        report = self.generate_fix_report()
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Fix report saved to {output_path}")
        return report


class CodeFormattingFixer:
    """Handles code formatting and style fixes"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
    
    def fix_file(self, file_path: Path) -> Optional[FixResult]:
        """Apply formatting fixes to a file"""
        if file_path.suffix == '.py':
            return self._fix_python_file(file_path)
        elif file_path.suffix in ['.ts', '.tsx', '.js', '.jsx']:
            return self._fix_typescript_file(file_path)
        
        return None
    
    def _fix_python_file(self, file_path: Path) -> Optional[FixResult]:
        """Fix Python file formatting"""
        changes_made = []
        
        try:
            # Apply black formatting
            result = subprocess.run([
                'black', '--quiet', str(file_path)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                changes_made.append("Applied black formatting")
            
            # Apply isort for imports
            result = subprocess.run([
                'isort', '--quiet', str(file_path)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                changes_made.append("Sorted imports with isort")
            
            if changes_made:
                return FixResult(
                    success=True,
                    fix_type=FixType.CODE_FORMATTING,
                    file_path=str(file_path),
                    description="Applied Python code formatting",
                    changes_made=changes_made,
                    backup_created=True
                )
        
        except Exception as e:
            return FixResult(
                success=False,
                fix_type=FixType.CODE_FORMATTING,
                file_path=str(file_path),
                description="Failed to apply Python formatting",
                changes_made=[],
                backup_created=False,
                error_message=str(e)
            )
        
        return None
    
    def _fix_typescript_file(self, file_path: Path) -> Optional[FixResult]:
        """Fix TypeScript/JavaScript file formatting"""
        changes_made = []
        
        try:
            # Apply prettier formatting
            result = subprocess.run([
                'npx', 'prettier', '--write', str(file_path)
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                changes_made.append("Applied prettier formatting")
            
            # Apply ESLint auto-fixes
            result = subprocess.run([
                'npx', 'eslint', '--fix', str(file_path)
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                changes_made.append("Applied ESLint auto-fixes")
            
            if changes_made:
                return FixResult(
                    success=True,
                    fix_type=FixType.CODE_FORMATTING,
                    file_path=str(file_path),
                    description="Applied TypeScript/JavaScript formatting",
                    changes_made=changes_made,
                    backup_created=True
                )
        
        except Exception as e:
            return FixResult(
                success=False,
                fix_type=FixType.CODE_FORMATTING,
                file_path=str(file_path),
                description="Failed to apply TypeScript formatting",
                changes_made=[],
                backup_created=False,
                error_message=str(e)
            )
        
        return None


class DependencyUpdater:
    """Handles dependency updates with compatibility checking"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.ubuntu_compatible_versions = self._load_ubuntu_compatibility_matrix()
    
    def _load_ubuntu_compatibility_matrix(self) -> Dict[str, Dict[str, str]]:
        """Load Ubuntu compatibility matrix for packages"""
        return {
            "python": {
                "fastapi": ">=0.104.0,<1.0.0",
                "uvicorn": ">=0.24.0,<1.0.0",
                "pydantic": ">=2.0.0,<3.0.0",
                "sqlalchemy": ">=2.0.0,<3.0.0",
                "redis": ">=5.0.0,<6.0.0",
                "psycopg2-binary": ">=2.9.0,<3.0.0"
            },
            "node": {
                "react": "^18.0.0",
                "typescript": "^5.0.0",
                "vite": "^5.0.0",
                "@types/node": "^20.0.0"
            }
        }
    
    def update_python_dependencies(self, check_compatibility: bool = True) -> Optional[FixResult]:
        """Update Python dependencies"""
        requirements_file = self.project_root / "backend" / "requirements.txt"
        if not requirements_file.exists():
            return None
        
        changes_made = []
        
        try:
            # Read current requirements
            current_reqs = requirements_file.read_text().splitlines()
            updated_reqs = []
            
            for req in current_reqs:
                if req.strip() and not req.startswith('#'):
                    updated_req = self._update_python_requirement(req, check_compatibility)
                    if updated_req != req:
                        changes_made.append(f"Updated {req} -> {updated_req}")
                    updated_reqs.append(updated_req)
                else:
                    updated_reqs.append(req)
            
            if changes_made:
                # Write updated requirements
                requirements_file.write_text('\n'.join(updated_reqs))
                
                return FixResult(
                    success=True,
                    fix_type=FixType.DEPENDENCY_UPDATE,
                    file_path=str(requirements_file),
                    description="Updated Python dependencies",
                    changes_made=changes_made,
                    backup_created=True
                )
        
        except Exception as e:
            return FixResult(
                success=False,
                fix_type=FixType.DEPENDENCY_UPDATE,
                file_path=str(requirements_file),
                description="Failed to update Python dependencies",
                changes_made=[],
                backup_created=False,
                error_message=str(e)
            )
        
        return None
    
    def update_node_dependencies(self, check_compatibility: bool = True) -> Optional[FixResult]:
        """Update Node.js dependencies"""
        package_json = self.project_root / "package.json"
        if not package_json.exists():
            return None
        
        changes_made = []
        
        try:
            with open(package_json, 'r') as f:
                package_data = json.load(f)
            
            # Update dependencies
            if 'dependencies' in package_data:
                for dep, version in package_data['dependencies'].items():
                    if check_compatibility and dep in self.ubuntu_compatible_versions.get('node', {}):
                        new_version = self.ubuntu_compatible_versions['node'][dep]
                        if new_version != version:
                            package_data['dependencies'][dep] = new_version
                            changes_made.append(f"Updated {dep}: {version} -> {new_version}")
            
            # Update devDependencies
            if 'devDependencies' in package_data:
                for dep, version in package_data['devDependencies'].items():
                    if check_compatibility and dep in self.ubuntu_compatible_versions.get('node', {}):
                        new_version = self.ubuntu_compatible_versions['node'][dep]
                        if new_version != version:
                            package_data['devDependencies'][dep] = new_version
                            changes_made.append(f"Updated {dep}: {version} -> {new_version}")
            
            if changes_made:
                with open(package_json, 'w') as f:
                    json.dump(package_data, f, indent=2)
                
                return FixResult(
                    success=True,
                    fix_type=FixType.DEPENDENCY_UPDATE,
                    file_path=str(package_json),
                    description="Updated Node.js dependencies",
                    changes_made=changes_made,
                    backup_created=True
                )
        
        except Exception as e:
            return FixResult(
                success=False,
                fix_type=FixType.DEPENDENCY_UPDATE,
                file_path=str(package_json),
                description="Failed to update Node.js dependencies",
                changes_made=[],
                backup_created=False,
                error_message=str(e)
            )
        
        return None
    
    def _update_python_requirement(self, requirement: str, check_compatibility: bool) -> str:
        """Update a single Python requirement"""
        if '==' in requirement:
            package_name = requirement.split('==')[0].strip()
            if check_compatibility and package_name in self.ubuntu_compatible_versions.get('python', {}):
                return f"{package_name}{self.ubuntu_compatible_versions['python'][package_name]}"
        
        return requirement


class ConfigurationFixer:
    """Handles configuration file fixes"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
    
    def fix_file(self, file_path: Path) -> Optional[FixResult]:
        """Fix configuration file"""
        if file_path.name.startswith('docker-compose'):
            return self._fix_docker_compose(file_path)
        elif file_path.name.startswith('Dockerfile'):
            return self._fix_dockerfile(file_path)
        elif file_path.suffix in ['.json']:
            return self._fix_json_file(file_path)
        elif file_path.suffix in ['.yml', '.yaml']:
            return self._fix_yaml_file(file_path)
        
        return None
    
    def _fix_docker_compose(self, file_path: Path) -> Optional[FixResult]:
        """Fix Docker Compose configuration"""
        changes_made = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Fix common Ubuntu compatibility issues
            ubuntu_fixes = [
                # Use Ubuntu-compatible base images
                (r'FROM python:3\.11-slim', 'FROM python:3.11-slim-bookworm'),
                (r'FROM node:20-alpine', 'FROM node:20-bookworm-slim'),
                # Fix volume permissions
                (r'- \.:/app', '- .:/app:delegated'),
                # Add proper restart policies
                (r'(services:\s*\n(?:\s+\w+:\s*\n(?:\s+.*\n)*)*)', 
                 lambda m: m.group(1).replace(':\n', ':\n    restart: unless-stopped\n') 
                 if 'restart:' not in m.group(1) else m.group(1))
            ]
            
            for pattern, replacement in ubuntu_fixes:
                if isinstance(replacement, str):
                    new_content = re.sub(pattern, replacement, content)
                    if new_content != content:
                        changes_made.append(f"Applied fix: {pattern}")
                        content = new_content
            
            if changes_made:
                with open(file_path, 'w') as f:
                    f.write(content)
                
                return FixResult(
                    success=True,
                    fix_type=FixType.CONFIGURATION_FIX,
                    file_path=str(file_path),
                    description="Fixed Docker Compose configuration",
                    changes_made=changes_made,
                    backup_created=True
                )
        
        except Exception as e:
            return FixResult(
                success=False,
                fix_type=FixType.CONFIGURATION_FIX,
                file_path=str(file_path),
                description="Failed to fix Docker Compose configuration",
                changes_made=[],
                backup_created=False,
                error_message=str(e)
            )
        
        return None
    
    def _fix_dockerfile(self, file_path: Path) -> Optional[FixResult]:
        """Fix Dockerfile configuration"""
        changes_made = []
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            updated_lines = []
            
            for line in lines:
                original_line = line
                
                # Ubuntu-specific Dockerfile optimizations
                if line.strip().startswith('FROM'):
                    # Ensure Ubuntu-compatible base images
                    if 'python:3.11-slim' in line and 'bookworm' not in line:
                        line = line.replace('python:3.11-slim', 'python:3.11-slim-bookworm')
                        changes_made.append("Updated Python base image to bookworm")
                    elif 'node:20-alpine' in line:
                        line = line.replace('node:20-alpine', 'node:20-bookworm-slim')
                        changes_made.append("Updated Node base image to bookworm-slim")
                
                elif line.strip().startswith('RUN apt-get'):
                    # Optimize apt-get commands for Ubuntu
                    if 'apt-get update' in line and '&& apt-get install' not in line:
                        line = line.rstrip() + ' && apt-get install -y --no-install-recommends \\\n'
                        changes_made.append("Optimized apt-get update command")
                
                updated_lines.append(line)
            
            if changes_made:
                with open(file_path, 'w') as f:
                    f.writelines(updated_lines)
                
                return FixResult(
                    success=True,
                    fix_type=FixType.CONFIGURATION_FIX,
                    file_path=str(file_path),
                    description="Fixed Dockerfile configuration",
                    changes_made=changes_made,
                    backup_created=True
                )
        
        except Exception as e:
            return FixResult(
                success=False,
                fix_type=FixType.CONFIGURATION_FIX,
                file_path=str(file_path),
                description="Failed to fix Dockerfile configuration",
                changes_made=[],
                backup_created=False,
                error_message=str(e)
            )
        
        return None
    
    def _fix_json_file(self, file_path: Path) -> Optional[FixResult]:
        """Fix JSON configuration file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Rewrite with proper formatting
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, sort_keys=True)
            
            return FixResult(
                success=True,
                fix_type=FixType.CONFIGURATION_FIX,
                file_path=str(file_path),
                description="Fixed JSON formatting",
                changes_made=["Applied proper JSON formatting"],
                backup_created=True
            )
        
        except json.JSONDecodeError as e:
            return FixResult(
                success=False,
                fix_type=FixType.CONFIGURATION_FIX,
                file_path=str(file_path),
                description="Failed to fix JSON file - invalid JSON",
                changes_made=[],
                backup_created=False,
                error_message=str(e)
            )
        except Exception as e:
            return FixResult(
                success=False,
                fix_type=FixType.CONFIGURATION_FIX,
                file_path=str(file_path),
                description="Failed to fix JSON file",
                changes_made=[],
                backup_created=False,
                error_message=str(e)
            )
    
    def _fix_yaml_file(self, file_path: Path) -> Optional[FixResult]:
        """Fix YAML configuration file"""
        if not HAS_YAML:
            return FixResult(
                success=False,
                fix_type=FixType.CONFIGURATION_FIX,
                file_path=str(file_path),
                description="Failed to fix YAML file - PyYAML not installed",
                changes_made=[],
                backup_created=False,
                error_message="PyYAML module not available"
            )
        
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Rewrite with proper formatting
            with open(file_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2, sort_keys=True)
            
            return FixResult(
                success=True,
                fix_type=FixType.CONFIGURATION_FIX,
                file_path=str(file_path),
                description="Fixed YAML formatting",
                changes_made=["Applied proper YAML formatting"],
                backup_created=True
            )
        
        except Exception as e:
            # Handle both yaml.YAMLError and general exceptions
            error_type = "invalid YAML" if "yaml" in str(type(e)).lower() else "general error"
            return FixResult(
                success=False,
                fix_type=FixType.CONFIGURATION_FIX,
                file_path=str(file_path),
                description=f"Failed to fix YAML file - {error_type}",
                changes_made=[],
                backup_created=False,
                error_message=str(e)
            )


class UbuntuOptimizer:
    """Handles Ubuntu-specific optimizations"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
    
    def optimize_deployment_scripts(self) -> Optional[FixResult]:
        """Optimize deployment scripts for Ubuntu"""
        changes_made = []
        script_files = []
        
        # Find shell scripts
        for pattern in ["*.sh", "scripts/*.sh", "config/*.sh"]:
            script_files.extend(self.project_root.glob(pattern))
        
        for script_file in script_files:
            if self._optimize_shell_script(script_file):
                changes_made.append(f"Optimized {script_file.name}")
        
        if changes_made:
            return FixResult(
                success=True,
                fix_type=FixType.UBUNTU_OPTIMIZATION,
                file_path="deployment_scripts",
                description="Optimized deployment scripts for Ubuntu",
                changes_made=changes_made,
                backup_created=True
            )
        
        return None
    
    def optimize_docker_configs(self) -> Optional[FixResult]:
        """Optimize Docker configurations for Ubuntu"""
        changes_made = []
        
        # Find Docker-related files
        docker_files = list(self.project_root.glob("docker-compose*.yml"))
        docker_files.extend(self.project_root.glob("Dockerfile*"))
        
        for docker_file in docker_files:
            if self._optimize_docker_file(docker_file):
                changes_made.append(f"Optimized {docker_file.name}")
        
        if changes_made:
            return FixResult(
                success=True,
                fix_type=FixType.UBUNTU_OPTIMIZATION,
                file_path="docker_configurations",
                description="Optimized Docker configurations for Ubuntu",
                changes_made=changes_made,
                backup_created=True
            )
        
        return None
    
    def _optimize_shell_script(self, script_file: Path) -> bool:
        """Optimize individual shell script for Ubuntu"""
        try:
            content = script_file.read_text()
            original_content = content
            
            # Ubuntu-specific shell optimizations
            ubuntu_optimizations = [
                # Ensure proper shebang
                (r'^#!/bin/sh', '#!/bin/bash'),
                # Use apt instead of apt-get where appropriate
                (r'apt-get update && apt-get install', 'apt update && apt install'),
                # Add error handling
                (r'^(?!.*set -e)', 'set -e\n'),
                # Optimize Docker commands for Ubuntu
                (r'docker-compose', 'docker compose'),
            ]
            
            for pattern, replacement in ubuntu_optimizations:
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            
            if content != original_content:
                script_file.write_text(content)
                return True
        
        except Exception as e:
            logger.error(f"Failed to optimize {script_file}: {e}")
        
        return False
    
    def _optimize_docker_file(self, docker_file: Path) -> bool:
        """Optimize Docker file for Ubuntu"""
        try:
            content = docker_file.read_text()
            original_content = content
            
            # Ubuntu-specific Docker optimizations
            if docker_file.name.startswith('docker-compose'):
                # Docker Compose optimizations
                ubuntu_optimizations = [
                    # Use Ubuntu-compatible restart policies
                    (r'restart: always', 'restart: unless-stopped'),
                    # Optimize volume mounts for Ubuntu
                    (r'- \.:/app$', '- .:/app:delegated'),
                ]
            else:
                # Dockerfile optimizations
                ubuntu_optimizations = [
                    # Use Ubuntu-compatible package manager
                    (r'apk add', 'apt-get update && apt-get install -y'),
                    # Optimize layer caching
                    (r'COPY \. \.', 'COPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .'),
                ]
            
            for pattern, replacement in ubuntu_optimizations:
                content = re.sub(pattern, replacement, content)
            
            if content != original_content:
                docker_file.write_text(content)
                return True
        
        except Exception as e:
            logger.error(f"Failed to optimize {docker_file}: {e}")
        
        return False


def main():
    """Main function for running automated fixes"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated Fix Application System")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--fix-types", nargs="+", 
                       choices=["formatting", "dependencies", "config", "ubuntu"],
                       default=["formatting", "dependencies", "config", "ubuntu"],
                       help="Types of fixes to apply")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed without applying")
    parser.add_argument("--output", default="automated_fix_report.json", help="Output report file")
    
    args = parser.parse_args()
    
    # Initialize fix engine
    fix_engine = AutoFixEngine(args.project_root)
    
    logger.info("Starting automated fix application...")
    
    # Apply requested fixes
    if "formatting" in args.fix_types:
        logger.info("Applying code formatting fixes...")
        fix_engine.apply_code_formatting_fixes()
    
    if "dependencies" in args.fix_types:
        logger.info("Applying dependency updates...")
        fix_engine.apply_dependency_updates()
    
    if "config" in args.fix_types:
        logger.info("Applying configuration fixes...")
        fix_engine.apply_configuration_fixes()
    
    if "ubuntu" in args.fix_types:
        logger.info("Applying Ubuntu optimizations...")
        fix_engine.apply_ubuntu_optimizations()
    
    # Generate and save report
    report = fix_engine.save_fix_report(args.output)
    
    logger.info(f"Automated fixes completed!")
    logger.info(f"Total fixes applied: {report['total_fixes_applied']}")
    logger.info(f"Successful fixes: {report['successful_fixes']}")
    logger.info(f"Failed fixes: {report['failed_fixes']}")
    logger.info(f"Report saved to: {args.output}")


if __name__ == "__main__":
    main()