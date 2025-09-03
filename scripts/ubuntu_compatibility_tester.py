#!/usr/bin/env python3
"""
Ubuntu Compatibility Testing Framework

This module provides comprehensive testing for Ubuntu server compatibility,
including package dependencies, Docker behavior, system integration, and performance.
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
import time
import psutil
import docker
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    SKIP = "SKIP"

@dataclass
class UbuntuCompatibilityResult:
    test_name: str
    result: TestResult
    message: str
    details: Dict[str, Any]
    execution_time: float
    ubuntu_specific: bool = True

class UbuntuEnvironmentSimulator:
    """Simulates Ubuntu environment for package dependency testing"""
    
    def __init__(self, ubuntu_version: str = "24.04"):
        self.ubuntu_version = ubuntu_version
        self.docker_client = None
        self.test_results: List[UbuntuCompatibilityResult] = []
        
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Docker client initialization failed: {e}")
    
    def test_python_dependencies(self) -> UbuntuCompatibilityResult:
        """Test Python package dependencies on Ubuntu"""
        start_time = time.time()
        
        try:
            # Read requirements files
            requirements_files = [
                "backend/requirements.txt",
                "backend/requirements-dev.txt",
                "requirements.txt"
            ]
            
            all_packages = set()
            for req_file in requirements_files:
                if os.path.exists(req_file):
                    with open(req_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                # Extract package name (before ==, >=, etc.)
                                package = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0]
                                all_packages.add(package.strip())
            
            # Test package installation in Ubuntu container
            if self.docker_client:
                result = self._test_packages_in_container(list(all_packages))
            else:
                result = self._test_packages_locally(list(all_packages))
            
            execution_time = time.time() - start_time
            return UbuntuCompatibilityResult(
                test_name="python_dependencies",
                result=result["status"],
                message=result["message"],
                details=result["details"],
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return UbuntuCompatibilityResult(
                test_name="python_dependencies",
                result=TestResult.FAIL,
                message=f"Python dependency test failed: {str(e)}",
                details={"error": str(e)},
                execution_time=execution_time
            )
    
    def _test_packages_in_container(self, packages: List[str]) -> Dict[str, Any]:
        """Test package installation in Ubuntu Docker container"""
        try:
            # Create a test container with Ubuntu
            container = self.docker_client.containers.run(
                f"ubuntu:{self.ubuntu_version}",
                command="sleep 300",
                detach=True,
                remove=True
            )
            
            try:
                # Update package lists
                container.exec_run("apt-get update")
                
                # Install Python and pip
                result = container.exec_run("apt-get install -y python3 python3-pip python3-venv")
                if result.exit_code != 0:
                    return {
                        "status": TestResult.FAIL,
                        "message": "Failed to install Python in Ubuntu container",
                        "details": {"error": result.output.decode()}
                    }
                
                # Test package installations
                failed_packages = []
                successful_packages = []
                
                for package in packages[:10]:  # Test first 10 packages to avoid timeout
                    try:
                        result = container.exec_run(f"pip3 install {package}")
                        if result.exit_code == 0:
                            successful_packages.append(package)
                        else:
                            failed_packages.append({
                                "package": package,
                                "error": result.output.decode()
                            })
                    except Exception as e:
                        failed_packages.append({
                            "package": package,
                            "error": str(e)
                        })
                
                if failed_packages:
                    return {
                        "status": TestResult.WARNING,
                        "message": f"Some packages failed to install: {len(failed_packages)}/{len(packages[:10])}",
                        "details": {
                            "failed_packages": failed_packages,
                            "successful_packages": successful_packages
                        }
                    }
                else:
                    return {
                        "status": TestResult.PASS,
                        "message": f"All tested packages installed successfully: {len(successful_packages)}",
                        "details": {"successful_packages": successful_packages}
                    }
                    
            finally:
                container.stop()
                
        except Exception as e:
            return {
                "status": TestResult.FAIL,
                "message": f"Container test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_packages_locally(self, packages: List[str]) -> Dict[str, Any]:
        """Test package compatibility locally (fallback when Docker unavailable)"""
        try:
            # Create virtual environment for testing
            with tempfile.TemporaryDirectory() as temp_dir:
                venv_path = os.path.join(temp_dir, "test_venv")
                
                # Create virtual environment
                result = subprocess.run([sys.executable, "-m", "venv", venv_path], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    return {
                        "status": TestResult.FAIL,
                        "message": "Failed to create virtual environment",
                        "details": {"error": result.stderr}
                    }
                
                # Test package installations
                pip_path = os.path.join(venv_path, "bin", "pip") if os.name != 'nt' else os.path.join(venv_path, "Scripts", "pip.exe")
                
                failed_packages = []
                successful_packages = []
                
                for package in packages[:5]:  # Test fewer packages locally
                    try:
                        result = subprocess.run([pip_path, "install", package], 
                                              capture_output=True, text=True, timeout=60)
                        if result.returncode == 0:
                            successful_packages.append(package)
                        else:
                            failed_packages.append({
                                "package": package,
                                "error": result.stderr
                            })
                    except subprocess.TimeoutExpired:
                        failed_packages.append({
                            "package": package,
                            "error": "Installation timeout"
                        })
                    except Exception as e:
                        failed_packages.append({
                            "package": package,
                            "error": str(e)
                        })
                
                if failed_packages:
                    return {
                        "status": TestResult.WARNING,
                        "message": f"Some packages failed locally: {len(failed_packages)}/{len(packages[:5])}",
                        "details": {
                            "failed_packages": failed_packages,
                            "successful_packages": successful_packages,
                            "note": "Local testing - results may differ from Ubuntu server"
                        }
                    }
                else:
                    return {
                        "status": TestResult.PASS,
                        "message": f"All tested packages installed locally: {len(successful_packages)}",
                        "details": {
                            "successful_packages": successful_packages,
                            "note": "Local testing - results may differ from Ubuntu server"
                        }
                    }
                    
        except Exception as e:
            return {
                "status": TestResult.FAIL,
                "message": f"Local package test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def test_nodejs_dependencies(self) -> UbuntuCompatibilityResult:
        """Test Node.js package dependencies on Ubuntu"""
        start_time = time.time()
        
        try:
            # Check if package.json exists
            if not os.path.exists("package.json"):
                execution_time = time.time() - start_time
                return UbuntuCompatibilityResult(
                    test_name="nodejs_dependencies",
                    result=TestResult.SKIP,
                    message="No package.json found",
                    details={},
                    execution_time=execution_time
                )
            
            # Read package.json
            with open("package.json", 'r') as f:
                package_data = json.load(f)
            
            dependencies = {}
            dependencies.update(package_data.get("dependencies", {}))
            dependencies.update(package_data.get("devDependencies", {}))
            
            if self.docker_client:
                result = self._test_node_packages_in_container(dependencies)
            else:
                result = self._test_node_packages_locally(dependencies)
            
            execution_time = time.time() - start_time
            return UbuntuCompatibilityResult(
                test_name="nodejs_dependencies",
                result=result["status"],
                message=result["message"],
                details=result["details"],
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return UbuntuCompatibilityResult(
                test_name="nodejs_dependencies",
                result=TestResult.FAIL,
                message=f"Node.js dependency test failed: {str(e)}",
                details={"error": str(e)},
                execution_time=execution_time
            )
    
    def _test_node_packages_in_container(self, dependencies: Dict[str, str]) -> Dict[str, Any]:
        """Test Node.js package installation in Ubuntu container"""
        try:
            container = self.docker_client.containers.run(
                f"ubuntu:{self.ubuntu_version}",
                command="sleep 300",
                detach=True,
                remove=True
            )
            
            try:
                # Update and install Node.js
                container.exec_run("apt-get update")
                result = container.exec_run("apt-get install -y curl")
                if result.exit_code != 0:
                    return {
                        "status": TestResult.FAIL,
                        "message": "Failed to install curl in Ubuntu container",
                        "details": {"error": result.output.decode()}
                    }
                
                # Install Node.js 20 LTS
                container.exec_run("curl -fsSL https://deb.nodesource.com/setup_20.x | bash -")
                result = container.exec_run("apt-get install -y nodejs")
                if result.exit_code != 0:
                    return {
                        "status": TestResult.FAIL,
                        "message": "Failed to install Node.js in Ubuntu container",
                        "details": {"error": result.output.decode()}
                    }
                
                # Test npm installation
                failed_packages = []
                successful_packages = []
                
                # Test a few key packages
                test_packages = list(dependencies.keys())[:5]
                
                for package in test_packages:
                    try:
                        result = container.exec_run(f"npm install {package}")
                        if result.exit_code == 0:
                            successful_packages.append(package)
                        else:
                            failed_packages.append({
                                "package": package,
                                "error": result.output.decode()
                            })
                    except Exception as e:
                        failed_packages.append({
                            "package": package,
                            "error": str(e)
                        })
                
                if failed_packages:
                    return {
                        "status": TestResult.WARNING,
                        "message": f"Some Node.js packages failed: {len(failed_packages)}/{len(test_packages)}",
                        "details": {
                            "failed_packages": failed_packages,
                            "successful_packages": successful_packages
                        }
                    }
                else:
                    return {
                        "status": TestResult.PASS,
                        "message": f"All tested Node.js packages installed: {len(successful_packages)}",
                        "details": {"successful_packages": successful_packages}
                    }
                    
            finally:
                container.stop()
                
        except Exception as e:
            return {
                "status": TestResult.FAIL,
                "message": f"Node.js container test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_node_packages_locally(self, dependencies: Dict[str, str]) -> Dict[str, Any]:
        """Test Node.js packages locally (fallback)"""
        try:
            # Check if npm is available
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                return {
                    "status": TestResult.SKIP,
                    "message": "npm not available for local testing",
                    "details": {}
                }
            
            return {
                "status": TestResult.PASS,
                "message": "npm available locally - full testing requires Ubuntu container",
                "details": {
                    "npm_version": result.stdout.strip(),
                    "total_dependencies": len(dependencies),
                    "note": "Local testing limited - use Docker for full Ubuntu compatibility"
                }
            }
            
        except Exception as e:
            return {
                "status": TestResult.FAIL,
                "message": f"Local Node.js test failed: {str(e)}",
                "details": {"error": str(e)}
            }

class DockerContainerTestSuite:
    """Test suite for Ubuntu-specific Docker container behavior"""
    
    def __init__(self):
        self.docker_client = None
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Docker client initialization failed: {e}")
    
    def test_docker_build_ubuntu_compatibility(self) -> UbuntuCompatibilityResult:
        """Test Docker builds with Ubuntu base images"""
        start_time = time.time()
        
        try:
            if not self.docker_client:
                execution_time = time.time() - start_time
                return UbuntuCompatibilityResult(
                    test_name="docker_build_ubuntu",
                    result=TestResult.SKIP,
                    message="Docker not available",
                    details={},
                    execution_time=execution_time
                )
            
            # Find Dockerfiles
            dockerfiles = []
            for root, dirs, files in os.walk("."):
                for file in files:
                    if file.startswith("Dockerfile"):
                        dockerfiles.append(os.path.join(root, file))
            
            if not dockerfiles:
                execution_time = time.time() - start_time
                return UbuntuCompatibilityResult(
                    test_name="docker_build_ubuntu",
                    result=TestResult.SKIP,
                    message="No Dockerfiles found",
                    details={},
                    execution_time=execution_time
                )
            
            build_results = []
            for dockerfile in dockerfiles:
                try:
                    # Read Dockerfile content
                    with open(dockerfile, 'r') as f:
                        content = f.read()
                    
                    # Check for Ubuntu compatibility issues
                    issues = self._analyze_dockerfile_ubuntu_compatibility(content)
                    
                    build_results.append({
                        "dockerfile": dockerfile,
                        "ubuntu_compatible": len(issues) == 0,
                        "issues": issues
                    })
                    
                except Exception as e:
                    build_results.append({
                        "dockerfile": dockerfile,
                        "ubuntu_compatible": False,
                        "issues": [f"Analysis failed: {str(e)}"]
                    })
            
            # Determine overall result
            compatible_count = sum(1 for r in build_results if r["ubuntu_compatible"])
            total_count = len(build_results)
            
            if compatible_count == total_count:
                result_status = TestResult.PASS
                message = f"All Dockerfiles Ubuntu compatible: {compatible_count}/{total_count}"
            elif compatible_count > 0:
                result_status = TestResult.WARNING
                message = f"Some Dockerfiles have Ubuntu issues: {compatible_count}/{total_count} compatible"
            else:
                result_status = TestResult.FAIL
                message = f"No Dockerfiles are Ubuntu compatible: {compatible_count}/{total_count}"
            
            execution_time = time.time() - start_time
            return UbuntuCompatibilityResult(
                test_name="docker_build_ubuntu",
                result=result_status,
                message=message,
                details={"build_results": build_results},
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return UbuntuCompatibilityResult(
                test_name="docker_build_ubuntu",
                result=TestResult.FAIL,
                message=f"Docker build test failed: {str(e)}",
                details={"error": str(e)},
                execution_time=execution_time
            )
    
    def _analyze_dockerfile_ubuntu_compatibility(self, content: str) -> List[str]:
        """Analyze Dockerfile for Ubuntu compatibility issues"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Check for non-Ubuntu base images that might cause issues
            if line.startswith('FROM') and 'ubuntu' not in line.lower():
                if any(distro in line.lower() for distro in ['alpine', 'centos', 'fedora', 'debian']):
                    issues.append(f"Line {i}: Non-Ubuntu base image may have compatibility issues")
            
            # Check for package manager usage
            if 'yum' in line or 'dnf' in line:
                issues.append(f"Line {i}: yum/dnf package manager not available on Ubuntu")
            
            if 'apk' in line:
                issues.append(f"Line {i}: apk package manager not available on Ubuntu")
            
            # Check for Ubuntu-specific package names
            if 'apt-get' in line or 'apt' in line:
                if 'python-dev' in line:
                    issues.append(f"Line {i}: Use 'python3-dev' instead of 'python-dev' on Ubuntu")
                if 'nodejs-npm' in line:
                    issues.append(f"Line {i}: Use 'nodejs npm' instead of 'nodejs-npm' on Ubuntu")
        
        return issues
    
    def test_container_networking_ubuntu(self) -> UbuntuCompatibilityResult:
        """Test container networking behavior on Ubuntu"""
        start_time = time.time()
        
        try:
            if not self.docker_client:
                execution_time = time.time() - start_time
                return UbuntuCompatibilityResult(
                    test_name="container_networking_ubuntu",
                    result=TestResult.SKIP,
                    message="Docker not available",
                    details={},
                    execution_time=execution_time
                )
            
            # Test basic networking
            container = self.docker_client.containers.run(
                "ubuntu:24.04",
                command="sleep 60",
                detach=True,
                remove=True,
                ports={'8080/tcp': None}  # Let Docker assign port
            )
            
            try:
                # Test network connectivity
                result = container.exec_run("apt-get update")
                network_works = result.exit_code == 0
                
                # Test port binding
                container.reload()
                ports = container.ports
                port_binding_works = '8080/tcp' in ports and ports['8080/tcp'] is not None
                
                # Test internal networking
                result = container.exec_run("ping -c 1 8.8.8.8")
                external_connectivity = result.exit_code == 0
                
                details = {
                    "network_connectivity": network_works,
                    "port_binding": port_binding_works,
                    "external_connectivity": external_connectivity,
                    "assigned_ports": ports
                }
                
                if network_works and port_binding_works and external_connectivity:
                    result_status = TestResult.PASS
                    message = "Container networking works correctly on Ubuntu"
                elif network_works and port_binding_works:
                    result_status = TestResult.WARNING
                    message = "Basic networking works, external connectivity issues"
                else:
                    result_status = TestResult.FAIL
                    message = "Container networking has issues on Ubuntu"
                
                execution_time = time.time() - start_time
                return UbuntuCompatibilityResult(
                    test_name="container_networking_ubuntu",
                    result=result_status,
                    message=message,
                    details=details,
                    execution_time=execution_time
                )
                
            finally:
                container.stop()
                
        except Exception as e:
            execution_time = time.time() - start_time
            return UbuntuCompatibilityResult(
                test_name="container_networking_ubuntu",
                result=TestResult.FAIL,
                message=f"Container networking test failed: {str(e)}",
                details={"error": str(e)},
                execution_time=execution_time
            )

class SystemIntegrationTester:
    """Test system integration for Ubuntu networking and file system compatibility"""
    
    def test_file_system_permissions(self) -> UbuntuCompatibilityResult:
        """Test file system permissions and access patterns"""
        start_time = time.time()
        
        try:
            # Test file creation and permissions
            test_files = []
            permission_issues = []
            
            # Test script files
            script_dirs = ["scripts", "backend/scripts", "."]
            for script_dir in script_dirs:
                if os.path.exists(script_dir):
                    for file in os.listdir(script_dir):
                        if file.endswith(('.sh', '.py')):
                            file_path = os.path.join(script_dir, file)
                            if os.path.isfile(file_path):
                                # Check if executable
                                if not os.access(file_path, os.X_OK):
                                    permission_issues.append({
                                        "file": file_path,
                                        "issue": "Script file not executable",
                                        "recommendation": f"chmod +x {file_path}"
                                    })
                                test_files.append(file_path)
            
            # Test directory permissions
            important_dirs = ["backend", "frontend", "scripts", "config", "logs"]
            for dir_name in important_dirs:
                if os.path.exists(dir_name):
                    if not os.access(dir_name, os.R_OK | os.W_OK):
                        permission_issues.append({
                            "file": dir_name,
                            "issue": "Directory not readable/writable",
                            "recommendation": f"chmod 755 {dir_name}"
                        })
            
            # Test temporary file creation
            try:
                with tempfile.NamedTemporaryFile(delete=True) as tmp:
                    tmp.write(b"test")
                    tmp.flush()
                temp_file_works = True
            except Exception as e:
                temp_file_works = False
                permission_issues.append({
                    "file": "/tmp",
                    "issue": f"Cannot create temporary files: {str(e)}",
                    "recommendation": "Check /tmp directory permissions"
                })
            
            details = {
                "tested_files": len(test_files),
                "permission_issues": permission_issues,
                "temp_file_creation": temp_file_works
            }
            
            if not permission_issues and temp_file_works:
                result_status = TestResult.PASS
                message = f"File system permissions OK: {len(test_files)} files tested"
            elif len(permission_issues) <= 2:
                result_status = TestResult.WARNING
                message = f"Minor permission issues: {len(permission_issues)} issues found"
            else:
                result_status = TestResult.FAIL
                message = f"Significant permission issues: {len(permission_issues)} issues found"
            
            execution_time = time.time() - start_time
            return UbuntuCompatibilityResult(
                test_name="file_system_permissions",
                result=result_status,
                message=message,
                details=details,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return UbuntuCompatibilityResult(
                test_name="file_system_permissions",
                result=TestResult.FAIL,
                message=f"File system test failed: {str(e)}",
                details={"error": str(e)},
                execution_time=execution_time
            )
    
    def test_network_configuration(self) -> UbuntuCompatibilityResult:
        """Test network configuration and connectivity"""
        start_time = time.time()
        
        try:
            network_tests = []
            
            # Test localhost connectivity
            try:
                response = requests.get("http://localhost:8000", timeout=5)
                localhost_test = {"test": "localhost:8000", "status": "reachable", "code": response.status_code}
            except requests.exceptions.ConnectionError:
                localhost_test = {"test": "localhost:8000", "status": "connection_refused", "code": None}
            except requests.exceptions.Timeout:
                localhost_test = {"test": "localhost:8000", "status": "timeout", "code": None}
            except Exception as e:
                localhost_test = {"test": "localhost:8000", "status": "error", "error": str(e)}
            
            network_tests.append(localhost_test)
            
            # Test external connectivity
            try:
                response = requests.get("https://httpbin.org/get", timeout=10)
                external_test = {"test": "external_https", "status": "reachable", "code": response.status_code}
            except Exception as e:
                external_test = {"test": "external_https", "status": "error", "error": str(e)}
            
            network_tests.append(external_test)
            
            # Test DNS resolution
            try:
                import socket
                socket.gethostbyname("google.com")
                dns_test = {"test": "dns_resolution", "status": "working"}
            except Exception as e:
                dns_test = {"test": "dns_resolution", "status": "error", "error": str(e)}
            
            network_tests.append(dns_test)
            
            # Analyze results
            working_tests = sum(1 for test in network_tests if test["status"] in ["reachable", "working"])
            total_tests = len(network_tests)
            
            details = {"network_tests": network_tests}
            
            if working_tests == total_tests:
                result_status = TestResult.PASS
                message = f"All network tests passed: {working_tests}/{total_tests}"
            elif working_tests > 0:
                result_status = TestResult.WARNING
                message = f"Some network issues: {working_tests}/{total_tests} tests passed"
            else:
                result_status = TestResult.FAIL
                message = f"Network connectivity issues: {working_tests}/{total_tests} tests passed"
            
            execution_time = time.time() - start_time
            return UbuntuCompatibilityResult(
                test_name="network_configuration",
                result=result_status,
                message=message,
                details=details,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return UbuntuCompatibilityResult(
                test_name="network_configuration",
                result=TestResult.FAIL,
                message=f"Network configuration test failed: {str(e)}",
                details={"error": str(e)},
                execution_time=execution_time
            )

class UbuntuPerformanceBenchmark:
    """Performance benchmarking tool for Ubuntu-specific metrics"""
    
    def benchmark_system_performance(self) -> UbuntuCompatibilityResult:
        """Benchmark system performance metrics"""
        start_time = time.time()
        
        try:
            # CPU benchmark
            cpu_start = time.time()
            # Simple CPU intensive task
            result = sum(i * i for i in range(100000))
            cpu_time = time.time() - cpu_start
            
            # Memory benchmark
            memory_info = psutil.virtual_memory()
            
            # Disk I/O benchmark
            disk_start = time.time()
            with tempfile.NamedTemporaryFile(delete=True) as tmp:
                # Write 10MB of data
                data = b"x" * 1024 * 1024  # 1MB
                for _ in range(10):
                    tmp.write(data)
                tmp.flush()
                os.fsync(tmp.fileno())
            disk_time = time.time() - disk_start
            
            # Network benchmark (if possible)
            network_start = time.time()
            try:
                response = requests.get("https://httpbin.org/bytes/1024", timeout=10)
                network_time = time.time() - network_start
                network_success = response.status_code == 200
            except Exception:
                network_time = None
                network_success = False
            
            # Calculate performance scores
            performance_metrics = {
                "cpu_computation_time": cpu_time,
                "memory_total_gb": round(memory_info.total / (1024**3), 2),
                "memory_available_gb": round(memory_info.available / (1024**3), 2),
                "memory_usage_percent": memory_info.percent,
                "disk_io_time_10mb": disk_time,
                "network_download_time": network_time,
                "network_connectivity": network_success
            }
            
            # Determine performance rating
            issues = []
            if cpu_time > 0.1:  # Should be very fast for simple computation
                issues.append("CPU performance slower than expected")
            
            if memory_info.percent > 90:
                issues.append("High memory usage detected")
            
            if disk_time > 2.0:  # 10MB should write quickly
                issues.append("Disk I/O performance slower than expected")
            
            if not network_success:
                issues.append("Network connectivity issues")
            
            if not issues:
                result_status = TestResult.PASS
                message = "System performance within expected ranges"
            elif len(issues) <= 1:
                result_status = TestResult.WARNING
                message = f"Minor performance issues: {', '.join(issues)}"
            else:
                result_status = TestResult.FAIL
                message = f"Performance issues detected: {', '.join(issues)}"
            
            execution_time = time.time() - start_time
            return UbuntuCompatibilityResult(
                test_name="system_performance_benchmark",
                result=result_status,
                message=message,
                details={
                    "performance_metrics": performance_metrics,
                    "issues": issues
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return UbuntuCompatibilityResult(
                test_name="system_performance_benchmark",
                result=TestResult.FAIL,
                message=f"Performance benchmark failed: {str(e)}",
                details={"error": str(e)},
                execution_time=execution_time
            )
    
    def benchmark_docker_performance(self) -> UbuntuCompatibilityResult:
        """Benchmark Docker performance on Ubuntu"""
        start_time = time.time()
        
        try:
            docker_client = docker.from_env()
            
            # Test container startup time
            container_start = time.time()
            container = docker_client.containers.run(
                "ubuntu:24.04",
                command="echo 'performance test'",
                detach=True,
                remove=True
            )
            
            # Wait for container to complete
            container.wait()
            container_startup_time = time.time() - container_start
            
            # Test image pull time (if not cached)
            pull_start = time.time()
            try:
                docker_client.images.pull("hello-world:latest")
                pull_time = time.time() - pull_start
            except Exception:
                pull_time = None
            
            # Test container resource usage
            stats_container = docker_client.containers.run(
                "ubuntu:24.04",
                command="sleep 30",
                detach=True,
                remove=True
            )
            
            try:
                # Get container stats
                stats = stats_container.stats(stream=False)
                memory_usage = stats['memory_stats'].get('usage', 0)
                memory_limit = stats['memory_stats'].get('limit', 0)
                
                stats_container.stop()
                
                performance_metrics = {
                    "container_startup_time": container_startup_time,
                    "image_pull_time": pull_time,
                    "container_memory_usage_mb": round(memory_usage / (1024*1024), 2) if memory_usage else 0,
                    "container_memory_limit_mb": round(memory_limit / (1024*1024), 2) if memory_limit else 0
                }
                
                # Evaluate performance
                issues = []
                if container_startup_time > 10:
                    issues.append("Container startup time slower than expected")
                
                if pull_time and pull_time > 30:
                    issues.append("Image pull time slower than expected")
                
                if not issues:
                    result_status = TestResult.PASS
                    message = "Docker performance within expected ranges"
                elif len(issues) == 1:
                    result_status = TestResult.WARNING
                    message = f"Minor Docker performance issue: {issues[0]}"
                else:
                    result_status = TestResult.FAIL
                    message = f"Docker performance issues: {', '.join(issues)}"
                
                execution_time = time.time() - start_time
                return UbuntuCompatibilityResult(
                    test_name="docker_performance_benchmark",
                    result=result_status,
                    message=message,
                    details={
                        "performance_metrics": performance_metrics,
                        "issues": issues
                    },
                    execution_time=execution_time
                )
                
            except Exception as e:
                stats_container.stop()
                raise e
                
        except docker.errors.DockerException as e:
            execution_time = time.time() - start_time
            return UbuntuCompatibilityResult(
                test_name="docker_performance_benchmark",
                result=TestResult.SKIP,
                message=f"Docker not available: {str(e)}",
                details={"error": str(e)},
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return UbuntuCompatibilityResult(
                test_name="docker_performance_benchmark",
                result=TestResult.FAIL,
                message=f"Docker performance benchmark failed: {str(e)}",
                details={"error": str(e)},
                execution_time=execution_time
            )

class UbuntuCompatibilityTestFramework:
    """Main framework orchestrating all Ubuntu compatibility tests"""
    
    def __init__(self, ubuntu_version: str = "24.04"):
        self.ubuntu_version = ubuntu_version
        self.env_simulator = UbuntuEnvironmentSimulator(ubuntu_version)
        self.docker_tester = DockerContainerTestSuite()
        self.system_tester = SystemIntegrationTester()
        self.performance_benchmark = UbuntuPerformanceBenchmark()
        self.results: List[UbuntuCompatibilityResult] = []
    
    def run_all_tests(self) -> List[UbuntuCompatibilityResult]:
        """Run all Ubuntu compatibility tests"""
        logger.info("Starting Ubuntu compatibility test suite...")
        
        # Environment simulation tests
        logger.info("Testing package dependencies...")
        self.results.append(self.env_simulator.test_python_dependencies())
        self.results.append(self.env_simulator.test_nodejs_dependencies())
        
        # Docker container tests
        logger.info("Testing Docker container compatibility...")
        self.results.append(self.docker_tester.test_docker_build_ubuntu_compatibility())
        self.results.append(self.docker_tester.test_container_networking_ubuntu())
        
        # System integration tests
        logger.info("Testing system integration...")
        self.results.append(self.system_tester.test_file_system_permissions())
        self.results.append(self.system_tester.test_network_configuration())
        
        # Performance benchmarks
        logger.info("Running performance benchmarks...")
        self.results.append(self.performance_benchmark.benchmark_system_performance())
        self.results.append(self.performance_benchmark.benchmark_docker_performance())
        
        logger.info("Ubuntu compatibility test suite completed.")
        return self.results
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        if not self.results:
            self.run_all_tests()
        
        # Categorize results
        passed = [r for r in self.results if r.result == TestResult.PASS]
        warnings = [r for r in self.results if r.result == TestResult.WARNING]
        failed = [r for r in self.results if r.result == TestResult.FAIL]
        skipped = [r for r in self.results if r.result == TestResult.SKIP]
        
        # Calculate overall score
        total_tests = len(self.results)
        score = (len(passed) * 100 + len(warnings) * 50) / (total_tests * 100) if total_tests > 0 else 0
        
        # Determine overall status
        if len(failed) == 0 and len(warnings) <= 1:
            overall_status = "EXCELLENT"
        elif len(failed) == 0:
            overall_status = "GOOD"
        elif len(failed) <= 2:
            overall_status = "NEEDS_ATTENTION"
        else:
            overall_status = "CRITICAL"
        
        report = {
            "ubuntu_version": self.ubuntu_version,
            "test_summary": {
                "total_tests": total_tests,
                "passed": len(passed),
                "warnings": len(warnings),
                "failed": len(failed),
                "skipped": len(skipped),
                "score": round(score * 100, 1),
                "overall_status": overall_status
            },
            "test_results": [asdict(result) for result in self.results],
            "recommendations": self._generate_recommendations(),
            "ubuntu_specific_issues": [
                asdict(result) for result in self.results 
                if result.ubuntu_specific and result.result in [TestResult.FAIL, TestResult.WARNING]
            ]
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        failed_tests = [r for r in self.results if r.result == TestResult.FAIL]
        warning_tests = [r for r in self.results if r.result == TestResult.WARNING]
        
        if any("python_dependencies" in r.test_name for r in failed_tests):
            recommendations.append("Review Python package dependencies for Ubuntu compatibility")
        
        if any("nodejs_dependencies" in r.test_name for r in failed_tests):
            recommendations.append("Review Node.js package dependencies for Ubuntu compatibility")
        
        if any("docker" in r.test_name for r in failed_tests):
            recommendations.append("Update Docker configurations for Ubuntu server deployment")
        
        if any("file_system" in r.test_name for r in failed_tests):
            recommendations.append("Fix file system permissions for Ubuntu server environment")
        
        if any("network" in r.test_name for r in failed_tests):
            recommendations.append("Review network configuration for Ubuntu server deployment")
        
        if any("performance" in r.test_name for r in failed_tests + warning_tests):
            recommendations.append("Optimize application performance for Ubuntu server hardware")
        
        if not recommendations:
            recommendations.append("Ubuntu compatibility looks good - consider regular monitoring")
        
        return recommendations

def main():
    """Main function to run Ubuntu compatibility tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ubuntu Compatibility Testing Framework")
    parser.add_argument("--ubuntu-version", default="24.04", help="Ubuntu version to test against")
    parser.add_argument("--output", "-o", help="Output file for test results (JSON)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run tests
    framework = UbuntuCompatibilityTestFramework(args.ubuntu_version)
    results = framework.run_all_tests()
    report = framework.generate_report()
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Test results saved to {args.output}")
    else:
        print(json.dumps(report, indent=2))
    
    # Print summary
    summary = report["test_summary"]
    print(f"\nUbuntu Compatibility Test Summary:")
    print(f"Overall Status: {summary['overall_status']}")
    print(f"Score: {summary['score']}%")
    print(f"Tests: {summary['passed']} passed, {summary['warnings']} warnings, {summary['failed']} failed, {summary['skipped']} skipped")
    
    if report["recommendations"]:
        print(f"\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"- {rec}")
    
    # Exit with appropriate code
    if summary["failed"] > 0:
        sys.exit(1)
    elif summary["warnings"] > 0:
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()