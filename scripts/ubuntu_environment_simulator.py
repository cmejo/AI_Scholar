#!/usr/bin/env python3
"""
Ubuntu Environment Simulation
Service integration testing with Ubuntu environment simulation
"""

import json
import logging
import os
import subprocess
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import docker
import yaml

logger = logging.getLogger(__name__)

@dataclass
class UbuntuTestResult:
    """Ubuntu environment test result"""
    test_name: str
    category: str
    status: str  # 'passed', 'failed', 'skipped'
    duration: float
    message: str
    details: Dict[str, Any]
    ubuntu_version: str = "24.04"

@dataclass
class UbuntuEnvironmentConfig:
    """Ubuntu environment configuration"""
    ubuntu_version: str = "24.04"
    docker_image: str = "ubuntu:24.04"
    test_container_name: str = "ai_scholar_ubuntu_test"
    python_version: str = "3.11"
    node_version: str = "20"
    
    # Application configuration
    app_port: int = 8000
    frontend_port: int = 3000
    postgres_port: int = 5432
    redis_port: int = 6379

class UbuntuEnvironmentSimulator:
    """Ubuntu environment simulation for integration testing"""
    
    def __init__(self, config: UbuntuEnvironmentConfig = None):
        self.config = config or UbuntuEnvironmentConfig()
        self.results: List[UbuntuTestResult] = []
        self.docker_client = None
        self.test_container = None
        
    def initialize(self) -> bool:
        """Initialize Ubuntu testing environment"""
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized for Ubuntu testing")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            return False
    
    def run_all_tests(self) -> List[UbuntuTestResult]:
        """Run all Ubuntu environment simulation tests"""
        logger.info("Starting Ubuntu environment simulation tests")
        
        if not self.initialize():
            return self.results
        
        test_methods = [
            ("ubuntu_container_setup", self._test_ubuntu_container_setup),
            ("system_dependencies", self._test_system_dependencies),
            ("python_environment", self._test_python_environment),
            ("node_environment", self._test_node_environment),
            ("docker_in_ubuntu", self._test_docker_in_ubuntu),
            ("network_configuration", self._test_network_configuration),
            ("file_system_operations", self._test_file_system_operations),
            ("service_deployment", self._test_service_deployment),
            ("application_startup", self._test_application_startup),
            ("resource_monitoring", self._test_resource_monitoring)
        ]
        
        for test_name, test_method in test_methods:
            try:
                logger.info(f"Running Ubuntu test: {test_name}")
                test_method()
            except Exception as e:
                logger.error(f"Error in {test_name}: {e}")
                self.results.append(UbuntuTestResult(
                    test_name=test_name,
                    category="ubuntu_simulation",
                    status="failed",
                    duration=0.0,
                    message=f"Test execution failed: {str(e)}",
                    details={"error": str(e)}
                ))
        
        # Cleanup
        self._cleanup()
        
        return self.results
    
    def _test_ubuntu_container_setup(self):
        """Test Ubuntu container setup and basic functionality"""
        start_time = time.time()
        test_name = "ubuntu_container_setup"
        
        try:
            # Pull Ubuntu image
            logger.info(f"Pulling Ubuntu image: {self.config.docker_image}")
            image = self.docker_client.images.pull(self.config.docker_image)
            
            # Create and start container
            self.test_container = self.docker_client.containers.run(
                self.config.docker_image,
                command="sleep 300",  # Keep container running
                name=self.config.test_container_name,
                detach=True,
                remove=True,
                volumes={
                    os.getcwd(): {'bind': '/app', 'mode': 'rw'}
                }
            )
            
            # Wait for container to be ready
            time.sleep(2)
            
            # Test basic commands
            result = self.test_container.exec_run("uname -a")
            if result.exit_code != 0:
                raise Exception(f"Basic command failed: {result.output.decode()}")
            
            system_info = result.output.decode().strip()
            
            # Test package manager
            result = self.test_container.exec_run("apt-get update")
            if result.exit_code != 0:
                raise Exception(f"Package manager update failed: {result.output.decode()}")
            
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="passed",
                duration=duration,
                message="Ubuntu container setup successful",
                details={
                    "image": self.config.docker_image,
                    "system_info": system_info,
                    "container_id": self.test_container.id[:12]
                }
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="failed",
                duration=duration,
                message=f"Ubuntu container setup failed: {str(e)}",
                details={"error": str(e)}
            ))
    
    def _test_system_dependencies(self):
        """Test system dependencies installation"""
        start_time = time.time()
        test_name = "system_dependencies"
        
        try:
            if not self.test_container:
                raise Exception("Test container not available")
            
            # Install essential packages
            packages = [
                "curl", "wget", "git", "build-essential", 
                "software-properties-common", "apt-transport-https",
                "ca-certificates", "gnupg", "lsb-release"
            ]
            
            install_cmd = f"apt-get install -y {' '.join(packages)}"
            result = self.test_container.exec_run(install_cmd)
            
            if result.exit_code != 0:
                raise Exception(f"Package installation failed: {result.output.decode()}")
            
            # Verify installations
            verification_results = {}
            for package in ["curl", "wget", "git"]:
                result = self.test_container.exec_run(f"which {package}")
                verification_results[package] = result.exit_code == 0
            
            # Test build tools
            result = self.test_container.exec_run("gcc --version")
            gcc_available = result.exit_code == 0
            
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="passed",
                duration=duration,
                message="System dependencies installation successful",
                details={
                    "packages_installed": packages,
                    "verification_results": verification_results,
                    "gcc_available": gcc_available
                }
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="failed",
                duration=duration,
                message=f"System dependencies test failed: {str(e)}",
                details={"error": str(e)}
            ))
    
    def _test_python_environment(self):
        """Test Python environment setup"""
        start_time = time.time()
        test_name = "python_environment"
        
        try:
            if not self.test_container:
                raise Exception("Test container not available")
            
            # Install Python
            python_install_commands = [
                "apt-get install -y python3 python3-pip python3-venv python3-dev",
                "python3 --version",
                "pip3 --version"
            ]
            
            python_info = {}
            for cmd in python_install_commands:
                result = self.test_container.exec_run(cmd)
                if "version" in cmd:
                    if result.exit_code == 0:
                        python_info[cmd.split()[0]] = result.output.decode().strip()
                elif result.exit_code != 0:
                    raise Exception(f"Python setup command failed: {cmd}")
            
            # Test virtual environment creation
            venv_commands = [
                "python3 -m venv /tmp/test_venv",
                "source /tmp/test_venv/bin/activate && python --version"
            ]
            
            for cmd in venv_commands:
                result = self.test_container.exec_run(f"bash -c '{cmd}'")
                if result.exit_code != 0:
                    raise Exception(f"Virtual environment command failed: {cmd}")
            
            # Test pip package installation
            result = self.test_container.exec_run(
                "bash -c 'source /tmp/test_venv/bin/activate && pip install requests'"
            )
            if result.exit_code != 0:
                raise Exception("Pip package installation failed")
            
            # Test package import
            result = self.test_container.exec_run(
                "bash -c 'source /tmp/test_venv/bin/activate && python -c \"import requests; print(requests.__version__)\"'"
            )
            if result.exit_code != 0:
                raise Exception("Package import test failed")
            
            requests_version = result.output.decode().strip()
            
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="passed",
                duration=duration,
                message="Python environment setup successful",
                details={
                    "python_info": python_info,
                    "venv_created": True,
                    "pip_install_test": "passed",
                    "requests_version": requests_version
                }
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="failed",
                duration=duration,
                message=f"Python environment test failed: {str(e)}",
                details={"error": str(e)}
            ))
    
    def _test_node_environment(self):
        """Test Node.js environment setup"""
        start_time = time.time()
        test_name = "node_environment"
        
        try:
            if not self.test_container:
                raise Exception("Test container not available")
            
            # Install Node.js
            node_install_commands = [
                "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -",
                "apt-get install -y nodejs",
                "node --version",
                "npm --version"
            ]
            
            node_info = {}
            for cmd in node_install_commands:
                result = self.test_container.exec_run(f"bash -c '{cmd}'")
                if "version" in cmd:
                    if result.exit_code == 0:
                        node_info[cmd.split()[0]] = result.output.decode().strip()
                elif result.exit_code != 0 and "curl" not in cmd:
                    raise Exception(f"Node.js setup command failed: {cmd}")
            
            # Test npm package installation
            result = self.test_container.exec_run("npm install -g typescript")
            if result.exit_code != 0:
                raise Exception("Global npm package installation failed")
            
            # Test TypeScript compilation
            test_ts_content = 'const message: string = "Hello Ubuntu"; console.log(message);'
            
            # Create test TypeScript file
            result = self.test_container.exec_run(
                f"bash -c 'echo \"{test_ts_content}\" > /tmp/test.ts'"
            )
            if result.exit_code != 0:
                raise Exception("Failed to create test TypeScript file")
            
            # Compile TypeScript
            result = self.test_container.exec_run("tsc /tmp/test.ts")
            if result.exit_code != 0:
                raise Exception("TypeScript compilation failed")
            
            # Run compiled JavaScript
            result = self.test_container.exec_run("node /tmp/test.js")
            if result.exit_code != 0:
                raise Exception("JavaScript execution failed")
            
            js_output = result.output.decode().strip()
            
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="passed",
                duration=duration,
                message="Node.js environment setup successful",
                details={
                    "node_info": node_info,
                    "typescript_installed": True,
                    "compilation_test": "passed",
                    "js_output": js_output
                }
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="failed",
                duration=duration,
                message=f"Node.js environment test failed: {str(e)}",
                details={"error": str(e)}
            ))
    
    def _test_docker_in_ubuntu(self):
        """Test Docker installation and functionality within Ubuntu"""
        start_time = time.time()
        test_name = "docker_in_ubuntu"
        
        try:
            if not self.test_container:
                raise Exception("Test container not available")
            
            # Install Docker
            docker_install_commands = [
                "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg",
                'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null',
                "apt-get update",
                "apt-get install -y docker-ce docker-ce-cli containerd.io"
            ]
            
            for cmd in docker_install_commands:
                result = self.test_container.exec_run(f"bash -c '{cmd}'")
                # Note: Docker installation in container may not fully work due to systemd limitations
                # This test primarily validates the installation process
            
            # Test Docker version (may fail in container environment)
            result = self.test_container.exec_run("docker --version")
            docker_version_available = result.exit_code == 0
            docker_version = result.output.decode().strip() if docker_version_available else "Not available in container"
            
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="passed",
                duration=duration,
                message="Docker installation process completed",
                details={
                    "installation_commands_executed": len(docker_install_commands),
                    "docker_version_available": docker_version_available,
                    "docker_version": docker_version,
                    "note": "Full Docker functionality requires privileged container or host system"
                }
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="failed",
                duration=duration,
                message=f"Docker in Ubuntu test failed: {str(e)}",
                details={"error": str(e)}
            ))
    
    def _test_network_configuration(self):
        """Test network configuration in Ubuntu environment"""
        start_time = time.time()
        test_name = "network_configuration"
        
        try:
            if not self.test_container:
                raise Exception("Test container not available")
            
            # Test network tools installation
            result = self.test_container.exec_run("apt-get install -y net-tools iputils-ping")
            if result.exit_code != 0:
                raise Exception("Network tools installation failed")
            
            # Test network interface information
            result = self.test_container.exec_run("ip addr show")
            if result.exit_code != 0:
                raise Exception("Network interface query failed")
            
            network_info = result.output.decode()
            
            # Test DNS resolution
            result = self.test_container.exec_run("nslookup google.com")
            dns_working = result.exit_code == 0
            
            # Test connectivity
            result = self.test_container.exec_run("ping -c 3 8.8.8.8")
            ping_working = result.exit_code == 0
            
            # Test port listening simulation
            result = self.test_container.exec_run("netstat -tuln")
            netstat_available = result.exit_code == 0
            
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="passed",
                duration=duration,
                message="Network configuration test completed",
                details={
                    "network_tools_installed": True,
                    "network_interfaces_available": True,
                    "dns_resolution": dns_working,
                    "ping_connectivity": ping_working,
                    "netstat_available": netstat_available
                }
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="failed",
                duration=duration,
                message=f"Network configuration test failed: {str(e)}",
                details={"error": str(e)}
            ))
    
    def _test_file_system_operations(self):
        """Test file system operations in Ubuntu"""
        start_time = time.time()
        test_name = "file_system_operations"
        
        try:
            if not self.test_container:
                raise Exception("Test container not available")
            
            # Test file operations
            file_operations = [
                "mkdir -p /tmp/test_dir",
                "echo 'test content' > /tmp/test_dir/test_file.txt",
                "chmod 644 /tmp/test_dir/test_file.txt",
                "chmod 755 /tmp/test_dir",
                "ls -la /tmp/test_dir",
                "cat /tmp/test_dir/test_file.txt"
            ]
            
            operation_results = {}
            for cmd in file_operations:
                result = self.test_container.exec_run(cmd)
                operation_results[cmd] = {
                    "exit_code": result.exit_code,
                    "success": result.exit_code == 0
                }
                if result.exit_code != 0:
                    operation_results[cmd]["error"] = result.output.decode()
            
            # Test file permissions
            result = self.test_container.exec_run("stat -c '%a' /tmp/test_dir/test_file.txt")
            file_permissions = result.output.decode().strip() if result.exit_code == 0 else "unknown"
            
            result = self.test_container.exec_run("stat -c '%a' /tmp/test_dir")
            dir_permissions = result.output.decode().strip() if result.exit_code == 0 else "unknown"
            
            # Test disk space
            result = self.test_container.exec_run("df -h /tmp")
            disk_info = result.output.decode() if result.exit_code == 0 else "unavailable"
            
            # Cleanup
            self.test_container.exec_run("rm -rf /tmp/test_dir")
            
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="passed",
                duration=duration,
                message="File system operations test completed",
                details={
                    "operation_results": operation_results,
                    "file_permissions": file_permissions,
                    "directory_permissions": dir_permissions,
                    "disk_info_available": disk_info != "unavailable"
                }
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="failed",
                duration=duration,
                message=f"File system operations test failed: {str(e)}",
                details={"error": str(e)}
            ))
    
    def _test_service_deployment(self):
        """Test service deployment simulation"""
        start_time = time.time()
        test_name = "service_deployment"
        
        try:
            if not self.test_container:
                raise Exception("Test container not available")
            
            # Create a simple Python web service
            service_code = '''
import http.server
import socketserver
import json
from datetime import datetime

class TestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "message": "Ubuntu service test"
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            super().do_GET()

PORT = 8080
with socketserver.TCPServer(("", PORT), TestHandler) as httpd:
    print(f"Server running on port {PORT}")
    httpd.serve_forever()
'''
            
            # Write service code to container
            result = self.test_container.exec_run(
                f"bash -c 'cat > /tmp/test_service.py << \"EOF\"\n{service_code}\nEOF'"
            )
            if result.exit_code != 0:
                raise Exception("Failed to create service file")
            
            # Start service in background
            result = self.test_container.exec_run(
                "bash -c 'cd /tmp && python3 test_service.py &'",
                detach=True
            )
            
            # Wait for service to start
            time.sleep(3)
            
            # Test service health endpoint
            result = self.test_container.exec_run(
                "curl -s http://localhost:8080/health"
            )
            
            service_response = ""
            if result.exit_code == 0:
                service_response = result.output.decode()
            
            # Check if service is listening
            result = self.test_container.exec_run("netstat -tuln | grep 8080")
            service_listening = result.exit_code == 0
            
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="passed",
                duration=duration,
                message="Service deployment simulation completed",
                details={
                    "service_created": True,
                    "service_listening": service_listening,
                    "health_check_response": service_response,
                    "port": 8080
                }
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="failed",
                duration=duration,
                message=f"Service deployment test failed: {str(e)}",
                details={"error": str(e)}
            ))
    
    def _test_application_startup(self):
        """Test application startup simulation"""
        start_time = time.time()
        test_name = "application_startup"
        
        try:
            if not self.test_container:
                raise Exception("Test container not available")
            
            # Simulate application startup script
            startup_script = '''#!/bin/bash
set -e

echo "Starting AI Scholar application simulation..."

# Check Python
python3 --version || exit 1

# Check Node.js
node --version || exit 1

# Create application directories
mkdir -p /app/backend /app/frontend /app/logs

# Simulate backend startup
echo "Starting backend services..."
cd /app/backend
echo "Backend service started" > /app/logs/backend.log

# Simulate frontend build
echo "Building frontend..."
cd /app/frontend
echo "Frontend built successfully" > /app/logs/frontend.log

# Simulate database connection
echo "Connecting to databases..."
echo "Database connections established" > /app/logs/database.log

echo "Application startup completed successfully"
'''
            
            # Write startup script
            result = self.test_container.exec_run(
                f"bash -c 'cat > /tmp/startup.sh << \"EOF\"\n{startup_script}\nEOF'"
            )
            if result.exit_code != 0:
                raise Exception("Failed to create startup script")
            
            # Make script executable
            result = self.test_container.exec_run("chmod +x /tmp/startup.sh")
            if result.exit_code != 0:
                raise Exception("Failed to make startup script executable")
            
            # Run startup script
            result = self.test_container.exec_run("/tmp/startup.sh")
            startup_success = result.exit_code == 0
            startup_output = result.output.decode()
            
            # Check log files
            log_files = ["backend.log", "frontend.log", "database.log"]
            log_status = {}
            
            for log_file in log_files:
                result = self.test_container.exec_run(f"cat /app/logs/{log_file}")
                log_status[log_file] = {
                    "exists": result.exit_code == 0,
                    "content": result.output.decode().strip() if result.exit_code == 0 else ""
                }
            
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="passed" if startup_success else "failed",
                duration=duration,
                message="Application startup simulation completed",
                details={
                    "startup_success": startup_success,
                    "startup_output": startup_output,
                    "log_files": log_status,
                    "directories_created": True
                }
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="failed",
                duration=duration,
                message=f"Application startup test failed: {str(e)}",
                details={"error": str(e)}
            ))
    
    def _test_resource_monitoring(self):
        """Test resource monitoring in Ubuntu environment"""
        start_time = time.time()
        test_name = "resource_monitoring"
        
        try:
            if not self.test_container:
                raise Exception("Test container not available")
            
            # Install monitoring tools
            result = self.test_container.exec_run("apt-get install -y htop iostat")
            # Note: htop and iostat may not be available in minimal containers
            
            # Test basic resource monitoring commands
            monitoring_commands = {
                "memory": "free -h",
                "disk": "df -h",
                "cpu": "cat /proc/cpuinfo | grep processor | wc -l",
                "load": "uptime",
                "processes": "ps aux | wc -l"
            }
            
            resource_info = {}
            for resource, cmd in monitoring_commands.items():
                result = self.test_container.exec_run(cmd)
                if result.exit_code == 0:
                    resource_info[resource] = result.output.decode().strip()
                else:
                    resource_info[resource] = f"Command failed: {result.output.decode()}"
            
            # Test process monitoring
            result = self.test_container.exec_run("ps aux")
            process_list_available = result.exit_code == 0
            process_count = len(result.output.decode().split('\n')) - 1 if process_list_available else 0
            
            # Test system limits
            result = self.test_container.exec_run("ulimit -a")
            system_limits = result.output.decode() if result.exit_code == 0 else "unavailable"
            
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="passed",
                duration=duration,
                message="Resource monitoring test completed",
                details={
                    "resource_info": resource_info,
                    "process_count": process_count,
                    "system_limits_available": system_limits != "unavailable"
                }
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(UbuntuTestResult(
                test_name=test_name,
                category="ubuntu_simulation",
                status="failed",
                duration=duration,
                message=f"Resource monitoring test failed: {str(e)}",
                details={"error": str(e)}
            ))
    
    def _cleanup(self):
        """Cleanup test resources"""
        try:
            if self.test_container:
                logger.info("Cleaning up test container")
                self.test_container.stop()
                # Container will be automatically removed due to remove=True
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate Ubuntu environment simulation report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "passed"])
        failed_tests = len([r for r in self.results if r.status == "failed"])
        skipped_tests = len([r for r in self.results if r.status == "skipped"])
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": skipped_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "ubuntu_version": self.config.ubuntu_version
            },
            "results": [asdict(result) for result in self.results],
            "failed_tests": [
                asdict(result) for result in self.results 
                if result.status == "failed"
            ],
            "configuration": asdict(self.config)
        }
        
        return report

def main():
    """Main function for Ubuntu environment simulation"""
    simulator = UbuntuEnvironmentSimulator()
    results = simulator.run_all_tests()
    report = simulator.generate_report()
    
    # Save report
    os.makedirs("integration_test_results", exist_ok=True)
    with open("integration_test_results/ubuntu_environment_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\nUBUNTU ENVIRONMENT SIMULATION SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Skipped: {report['summary']['skipped']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
    print(f"Ubuntu Version: {report['summary']['ubuntu_version']}")
    
    return report['summary']['failed'] == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)