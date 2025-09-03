#!/usr/bin/env python3
"""
Test Suite for Automated Fix Engine
Tests all components of the automated fix application system.
"""

import os
import sys
import json
import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from automated_fix_engine import (
    AutoFixEngine, CodeFormattingFixer, DependencyUpdater,
    ConfigurationFixer, UbuntuOptimizer, FixType, FixSeverity, FixResult
)

class TestAutoFixEngine:
    """Test cases for the main AutoFixEngine class"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.fix_engine = AutoFixEngine(str(self.project_root))
        
        # Create test directory structure
        (self.project_root / "backend").mkdir()
        (self.project_root / "frontend").mkdir()
        (self.project_root / "scripts").mkdir()
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test AutoFixEngine initialization"""
        assert self.fix_engine.project_root == self.project_root
        assert self.fix_engine.backup_dir.exists()
        assert isinstance(self.fix_engine.code_formatter, CodeFormattingFixer)
        assert isinstance(self.fix_engine.dependency_updater, DependencyUpdater)
        assert isinstance(self.fix_engine.config_fixer, ConfigurationFixer)
        assert isinstance(self.fix_engine.ubuntu_optimizer, UbuntuOptimizer)
    
    def test_create_backup(self):
        """Test backup creation functionality"""
        # Create test file
        test_file = self.project_root / "test.py"
        test_content = "print('hello world')"
        test_file.write_text(test_content)
        
        # Create backup
        result = self.fix_engine.create_backup(test_file)
        
        assert result is True
        backup_files = list(self.fix_engine.backup_dir.glob("test.py_*.backup"))
        assert len(backup_files) == 1
        assert backup_files[0].read_text() == test_content
    
    def test_should_skip_file(self):
        """Test file skipping logic"""
        # Files that should be skipped
        skip_files = [
            self.project_root / "node_modules" / "test.js",
            self.project_root / ".git" / "config",
            self.project_root / "__pycache__" / "test.pyc",
            self.project_root / "venv" / "lib" / "test.py"
        ]
        
        for file_path in skip_files:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()
            assert self.fix_engine._should_skip_file(file_path) is True
        
        # Files that should not be skipped
        normal_files = [
            self.project_root / "src" / "test.py",
            self.project_root / "components" / "test.tsx"
        ]
        
        for file_path in normal_files:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()
            assert self.fix_engine._should_skip_file(file_path) is False
    
    def test_generate_fix_report(self):
        """Test fix report generation"""
        # Add some mock fixes
        self.fix_engine.applied_fixes = [
            FixResult(
                success=True,
                fix_type=FixType.CODE_FORMATTING,
                file_path="test.py",
                description="Test fix",
                changes_made=["Applied formatting"],
                backup_created=True
            ),
            FixResult(
                success=False,
                fix_type=FixType.DEPENDENCY_UPDATE,
                file_path="requirements.txt",
                description="Failed update",
                changes_made=[],
                backup_created=False,
                error_message="Test error"
            )
        ]
        
        report = self.fix_engine.generate_fix_report()
        
        assert report["total_fixes_applied"] == 2
        assert report["successful_fixes"] == 1
        assert report["failed_fixes"] == 1
        assert "code_formatting" in report["fixes_by_type"]
        assert "dependency_update" in report["fixes_by_type"]
        assert len(report["fixes_details"]) == 2


class TestCodeFormattingFixer:
    """Test cases for CodeFormattingFixer"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.formatter = CodeFormattingFixer(self.project_root)
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    @patch('subprocess.run')
    def test_fix_python_file_success(self, mock_run):
        """Test successful Python file formatting"""
        # Mock successful subprocess calls
        mock_run.return_value = Mock(returncode=0)
        
        # Create test Python file
        test_file = self.project_root / "test.py"
        test_file.write_text("import os\nimport sys\nprint('hello')")
        
        result = self.formatter._fix_python_file(test_file)
        
        assert result is not None
        assert result.success is True
        assert result.fix_type == FixType.CODE_FORMATTING
        assert "Applied black formatting" in result.changes_made
        assert "Sorted imports with isort" in result.changes_made
    
    @patch('subprocess.run')
    def test_fix_python_file_failure(self, mock_run):
        """Test Python file formatting failure"""
        # Mock failed subprocess call
        mock_run.side_effect = Exception("Command failed")
        
        test_file = self.project_root / "test.py"
        test_file.write_text("invalid python code")
        
        result = self.formatter._fix_python_file(test_file)
        
        assert result is not None
        assert result.success is False
        assert result.error_message == "Command failed"
    
    @patch('subprocess.run')
    def test_fix_typescript_file_success(self, mock_run):
        """Test successful TypeScript file formatting"""
        # Mock successful subprocess calls
        mock_run.return_value = Mock(returncode=0)
        
        test_file = self.project_root / "test.ts"
        test_file.write_text("const x=1;console.log(x);")
        
        result = self.formatter._fix_typescript_file(test_file)
        
        assert result is not None
        assert result.success is True
        assert result.fix_type == FixType.CODE_FORMATTING
        assert "Applied prettier formatting" in result.changes_made
        assert "Applied ESLint auto-fixes" in result.changes_made


class TestDependencyUpdater:
    """Test cases for DependencyUpdater"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.updater = DependencyUpdater(self.project_root)
        
        # Create backend directory
        (self.project_root / "backend").mkdir()
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_update_python_dependencies(self):
        """Test Python dependency updates"""
        # Create requirements.txt with outdated versions
        requirements_file = self.project_root / "backend" / "requirements.txt"
        requirements_content = """fastapi==0.100.0
uvicorn==0.20.0
pydantic==1.10.0
# This is a comment
requests==2.28.0
"""
        requirements_file.write_text(requirements_content)
        
        result = self.updater.update_python_dependencies(check_compatibility=True)
        
        assert result is not None
        assert result.success is True
        assert result.fix_type == FixType.DEPENDENCY_UPDATE
        assert len(result.changes_made) > 0
        
        # Check that file was updated
        updated_content = requirements_file.read_text()
        assert "fastapi>=0.104.0,<1.0.0" in updated_content
        assert "uvicorn>=0.24.0,<1.0.0" in updated_content
        assert "pydantic>=2.0.0,<3.0.0" in updated_content
    
    def test_update_node_dependencies(self):
        """Test Node.js dependency updates"""
        # Create package.json with outdated versions
        package_json = self.project_root / "package.json"
        package_data = {
            "name": "test-project",
            "dependencies": {
                "react": "^17.0.0",
                "typescript": "^4.0.0"
            },
            "devDependencies": {
                "vite": "^4.0.0",
                "@types/node": "^18.0.0"
            }
        }
        
        with open(package_json, 'w') as f:
            json.dump(package_data, f, indent=2)
        
        result = self.updater.update_node_dependencies(check_compatibility=True)
        
        assert result is not None
        assert result.success is True
        assert result.fix_type == FixType.DEPENDENCY_UPDATE
        assert len(result.changes_made) > 0
        
        # Check that file was updated
        with open(package_json, 'r') as f:
            updated_data = json.load(f)
        
        assert updated_data["dependencies"]["react"] == "^18.0.0"
        assert updated_data["dependencies"]["typescript"] == "^5.0.0"
        assert updated_data["devDependencies"]["vite"] == "^5.0.0"
        assert updated_data["devDependencies"]["@types/node"] == "^20.0.0"


class TestConfigurationFixer:
    """Test cases for ConfigurationFixer"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.config_fixer = ConfigurationFixer(self.project_root)
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_fix_docker_compose(self):
        """Test Docker Compose configuration fixes"""
        # Create docker-compose.yml with issues
        docker_compose = self.project_root / "docker-compose.yml"
        compose_content = """version: '3.8'
services:
  backend:
    image: python:3.11-slim
    volumes:
      - .:/app
  frontend:
    image: node:20-alpine
    volumes:
      - .:/app
"""
        docker_compose.write_text(compose_content)
        
        result = self.config_fixer._fix_docker_compose(docker_compose)
        
        assert result is not None
        assert result.success is True
        assert result.fix_type == FixType.CONFIGURATION_FIX
        
        # Check that fixes were applied
        updated_content = docker_compose.read_text()
        assert "python:3.11-slim-bookworm" in updated_content
        assert "node:20-bookworm-slim" in updated_content
        assert ".:/app:delegated" in updated_content
    
    def test_fix_dockerfile(self):
        """Test Dockerfile configuration fixes"""
        # Create Dockerfile with issues
        dockerfile = self.project_root / "Dockerfile"
        dockerfile_content = """FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN apt-get update
RUN pip install -r requirements.txt
"""
        dockerfile.write_text(dockerfile_content)
        
        result = self.config_fixer._fix_dockerfile(dockerfile)
        
        assert result is not None
        assert result.success is True
        assert result.fix_type == FixType.CONFIGURATION_FIX
        
        # Check that fixes were applied
        updated_content = dockerfile.read_text()
        assert "python:3.11-slim-bookworm" in updated_content
    
    def test_fix_json_file(self):
        """Test JSON file formatting"""
        # Create malformed JSON file
        json_file = self.project_root / "config.json"
        json_content = '{"name":"test","version":"1.0.0","dependencies":{"react":"^18.0.0"}}'
        json_file.write_text(json_content)
        
        result = self.config_fixer._fix_json_file(json_file)
        
        assert result is not None
        assert result.success is True
        assert result.fix_type == FixType.CONFIGURATION_FIX
        
        # Check that file was properly formatted
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        assert data["name"] == "test"
        assert data["version"] == "1.0.0"
    
    def test_fix_invalid_json_file(self):
        """Test handling of invalid JSON files"""
        # Create invalid JSON file
        json_file = self.project_root / "invalid.json"
        json_file.write_text('{"name": "test", "invalid": }')
        
        result = self.config_fixer._fix_json_file(json_file)
        
        assert result is not None
        assert result.success is False
        assert "invalid JSON" in result.description


class TestUbuntuOptimizer:
    """Test cases for UbuntuOptimizer"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.optimizer = UbuntuOptimizer(self.project_root)
        
        # Create scripts directory
        (self.project_root / "scripts").mkdir()
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_optimize_shell_script(self):
        """Test shell script optimization"""
        # Create shell script with issues
        script_file = self.project_root / "deploy.sh"
        script_content = """#!/bin/sh
apt-get update && apt-get install -y docker
docker-compose up -d
"""
        script_file.write_text(script_content)
        
        result = self.optimizer._optimize_shell_script(script_file)
        
        assert result is True
        
        # Check that optimizations were applied
        updated_content = script_file.read_text()
        assert "#!/bin/bash" in updated_content
        assert "set -e" in updated_content
        assert "apt update && apt install" in updated_content
        assert "docker compose" in updated_content
    
    def test_optimize_docker_compose_file(self):
        """Test Docker Compose optimization"""
        # Create docker-compose.yml
        compose_file = self.project_root / "docker-compose.yml"
        compose_content = """version: '3.8'
services:
  app:
    image: nginx
    restart: always
    volumes:
      - .:/app
"""
        compose_file.write_text(compose_content)
        
        result = self.optimizer._optimize_docker_file(compose_file)
        
        assert result is True
        
        # Check that optimizations were applied
        updated_content = compose_file.read_text()
        assert "restart: unless-stopped" in updated_content
        assert ".:/app:delegated" in updated_content
    
    def test_optimize_deployment_scripts(self):
        """Test deployment script optimization"""
        # Create multiple shell scripts
        scripts = ["deploy.sh", "setup.sh", "start.sh"]
        
        for script_name in scripts:
            script_file = self.project_root / script_name
            script_content = f"""#!/bin/sh
echo "Running {script_name}"
docker-compose up -d
"""
            script_file.write_text(script_content)
        
        result = self.optimizer.optimize_deployment_scripts()
        
        assert result is not None
        assert result.success is True
        assert result.fix_type == FixType.UBUNTU_OPTIMIZATION
        assert len(result.changes_made) == len(scripts)


class TestFixResult:
    """Test cases for FixResult data class"""
    
    def test_fix_result_creation(self):
        """Test FixResult creation and properties"""
        result = FixResult(
            success=True,
            fix_type=FixType.CODE_FORMATTING,
            file_path="test.py",
            description="Test fix",
            changes_made=["Applied formatting"],
            backup_created=True
        )
        
        assert result.success is True
        assert result.fix_type == FixType.CODE_FORMATTING
        assert result.file_path == "test.py"
        assert result.description == "Test fix"
        assert result.changes_made == ["Applied formatting"]
        assert result.backup_created is True
        assert result.error_message is None
        assert result.warnings == []
    
    def test_fix_result_with_error(self):
        """Test FixResult with error information"""
        result = FixResult(
            success=False,
            fix_type=FixType.DEPENDENCY_UPDATE,
            file_path="requirements.txt",
            description="Failed to update",
            changes_made=[],
            backup_created=False,
            error_message="Network error",
            warnings=["Deprecated package found"]
        )
        
        assert result.success is False
        assert result.error_message == "Network error"
        assert result.warnings == ["Deprecated package found"]


def run_tests():
    """Run all tests"""
    print("Running Automated Fix Engine Tests...")
    
    # Run pytest
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])
    
    return exit_code == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)