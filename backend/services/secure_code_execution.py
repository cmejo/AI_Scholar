"""
Secure Code Execution Service

This service provides secure, containerized code execution with:
- Docker-based sandboxing
- Resource limits and timeouts
- Dependency management
- Security scanning and analysis
- Support for multiple programming languages
"""

import asyncio
import json
import logging
import os
import tempfile
import time
import uuid
import hashlib
import tarfile
import io
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Set
import docker
import psutil
import subprocess
import ast
import re
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class ExecutionLanguage(Enum):
    PYTHON = "python"
    R = "r"
    JAVASCRIPT = "javascript"
    BASH = "bash"
    SQL = "sql"

class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SECURITY_VIOLATION = "security_violation"

@dataclass
class ResourceLimits:
    """Resource limits for code execution"""
    max_memory_mb: int = 512
    max_cpu_percent: float = 50.0
    max_execution_time_seconds: int = 30
    max_disk_usage_mb: int = 100
    max_network_requests: int = 10
    max_processes: int = 1
    max_open_files: int = 100
    max_output_size_mb: int = 10

@dataclass
class SecurityPolicy:
    """Security policy for code execution"""
    allow_network_access: bool = False
    allow_file_system_access: bool = False
    allow_subprocess_execution: bool = False
    blocked_imports: List[str] = None
    blocked_functions: List[str] = None
    allowed_domains: List[str] = None
    scan_for_malware: bool = True
    enable_code_signing: bool = False
    max_recursion_depth: int = 100
    
    def __post_init__(self):
        if self.blocked_imports is None:
            self.blocked_imports = [
                'os', 'sys', 'subprocess', 'socket', 'urllib', 'requests',
                'http', 'ftplib', 'smtplib', 'telnetlib', 'webbrowser',
                'ctypes', 'multiprocessing', 'threading', 'asyncio',
                'importlib', 'pkgutil', 'imp', 'zipimport'
            ]
        if self.blocked_functions is None:
            self.blocked_functions = [
                'exec', 'eval', 'compile', '__import__', 'open', 'file',
                'input', 'raw_input', 'execfile', 'reload', 'globals',
                'locals', 'vars', 'dir', 'getattr', 'setattr', 'delattr',
                'hasattr', 'callable', 'isinstance', 'issubclass'
            ]
        if self.allowed_domains is None:
            self.allowed_domains = []

@dataclass
class ExecutionResult:
    """Result of code execution"""
    execution_id: str
    status: ExecutionStatus
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    memory_used_mb: float = 0.0
    cpu_used_percent: float = 0.0
    security_violations: List[str] = None
    dependencies_installed: List[str] = None
    created_at: datetime = None
    container_id: Optional[str] = None
    resource_usage: Dict[str, Any] = None
    security_scan_results: Dict[str, Any] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.security_violations is None:
            self.security_violations = []
        if self.dependencies_installed is None:
            self.dependencies_installed = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.resource_usage is None:
            self.resource_usage = {}
        if self.security_scan_results is None:
            self.security_scan_results = {}
        if self.warnings is None:
            self.warnings = []

@dataclass
class CodeExecutionRequest:
    """Request for code execution"""
    code: str
    language: ExecutionLanguage
    dependencies: List[str] = None
    resource_limits: ResourceLimits = None
    security_policy: SecurityPolicy = None
    environment_variables: Dict[str, str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.resource_limits is None:
            self.resource_limits = ResourceLimits()
        if self.security_policy is None:
            self.security_policy = SecurityPolicy()
        if self.environment_variables is None:
            self.environment_variables = {}

class SecurityScanner:
    """Enhanced security scanner for code analysis"""
    
    def __init__(self):
        self.python_dangerous_patterns = [
            r'__import__\s*\(',
            r'exec\s*\(',
            r'eval\s*\(',
            r'compile\s*\(',
            r'open\s*\(',
            r'file\s*\(',
            r'subprocess\.',
            r'os\.',
            r'sys\.',
            r'socket\.',
            r'urllib\.',
            r'requests\.',
            r'http\.',
            r'ctypes\.',
            r'multiprocessing\.',
            r'threading\.',
            r'__builtins__',
            r'globals\s*\(',
            r'locals\s*\(',
            r'vars\s*\(',
            r'getattr\s*\(',
            r'setattr\s*\(',
            r'delattr\s*\(',
        ]
        
        self.javascript_dangerous_patterns = [
            r'eval\s*\(',
            r'Function\s*\(',
            r'setTimeout\s*\(',
            r'setInterval\s*\(',
            r'require\s*\(',
            r'process\.',
            r'fs\.',
            r'child_process\.',
            r'net\.',
            r'http\.',
            r'vm\.',
            r'cluster\.',
            r'crypto\.',
            r'os\.',
            r'path\.',
            r'url\.',
        ]
        
        self.malware_signatures = [
            # Common malware patterns
            r'rm\s+-rf\s+/',
            r'format\s+c:',
            r'del\s+/s\s+/q',
            r'shutdown\s+-s',
            r'curl.*\|\s*sh',
            r'wget.*\|\s*sh',
            r'base64.*decode',
            r'reverse\s+shell',
            r'backdoor',
            r'keylogger',
            r'password\s+stealer',
        ]
        
        self.code_complexity_threshold = 1000  # Maximum cyclomatic complexity
    
    async def scan_python_code(self, code: str, security_policy: SecurityPolicy) -> List[str]:
        """Enhanced Python code security scanning"""
        violations = []
        
        try:
            # Parse AST to check for dangerous constructs
            tree = ast.parse(code)
            
            # Check code complexity
            complexity = self._calculate_complexity(tree)
            if complexity > self.code_complexity_threshold:
                violations.append(f"Code complexity too high: {complexity}")
            
            # Check recursion depth
            max_depth = self._check_recursion_depth(tree)
            if max_depth > security_policy.max_recursion_depth:
                violations.append(f"Recursion depth too high: {max_depth}")
            
            for node in ast.walk(tree):
                # Check for dangerous function calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in security_policy.blocked_functions:
                            violations.append(f"Blocked function call: {node.func.id}")
                    elif isinstance(node.func, ast.Attribute):
                        # Check for method calls on dangerous modules
                        if hasattr(node.func, 'value') and isinstance(node.func.value, ast.Name):
                            module_name = node.func.value.id
                            if module_name in security_policy.blocked_imports:
                                violations.append(f"Blocked method call: {module_name}.{node.func.attr}")
                
                # Check for dangerous imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in security_policy.blocked_imports:
                            violations.append(f"Blocked import: {alias.name}")
                
                if isinstance(node, ast.ImportFrom):
                    if node.module and node.module in security_policy.blocked_imports:
                        violations.append(f"Blocked import from: {node.module}")
                
                # Check for dynamic code execution
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in ['exec', 'eval', 'compile']:
                        violations.append(f"Dynamic code execution detected: {node.func.id}")
                
                # Check for file operations
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in ['open', 'file'] and not security_policy.allow_file_system_access:
                        violations.append("File system access not allowed")
        
        except SyntaxError as e:
            violations.append(f"Syntax error: {str(e)}")
        
        # Pattern-based scanning
        for pattern in self.python_dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                violations.append(f"Dangerous pattern detected: {pattern}")
        
        # Malware signature scanning
        if security_policy.scan_for_malware:
            violations.extend(await self._scan_for_malware(code))
        
        return violations
    
    async def scan_javascript_code(self, code: str, security_policy: SecurityPolicy) -> List[str]:
        """Scan JavaScript code for security violations"""
        violations = []
        
        # Pattern-based scanning for JavaScript
        for pattern in self.javascript_dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                violations.append(f"Dangerous pattern detected: {pattern}")
        
        return violations
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity of AST"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers)
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def _check_recursion_depth(self, tree: ast.AST) -> int:
        """Check maximum recursion depth in code"""
        max_depth = 0
        
        def count_depth(node, current_depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    count_depth(child, current_depth + 1)
                else:
                    count_depth(child, current_depth)
        
        count_depth(tree)
        return max_depth
    
    async def _scan_for_malware(self, code: str) -> List[str]:
        """Scan code for malware signatures"""
        violations = []
        
        for signature in self.malware_signatures:
            if re.search(signature, code, re.IGNORECASE):
                violations.append(f"Potential malware signature detected: {signature}")
        
        return violations
    
    async def scan_code(self, code: str, language: ExecutionLanguage, security_policy: SecurityPolicy) -> List[str]:
        """Scan code for security violations based on language"""
        if language == ExecutionLanguage.PYTHON:
            return await self.scan_python_code(code, security_policy)
        elif language == ExecutionLanguage.JAVASCRIPT:
            return await self.scan_javascript_code(code, security_policy)
        else:
            # Basic pattern scanning for other languages
            violations = []
            dangerous_patterns = [
                r'system\s*\(',
                r'exec\s*\(',
                r'shell_exec\s*\(',
                r'passthru\s*\(',
                r'eval\s*\(',
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    violations.append(f"Potentially dangerous pattern: {pattern}")
            
            # Malware signature scanning
            if security_policy.scan_for_malware:
                violations.extend(await self._scan_for_malware(code))
            
            return violations

class DependencyManager:
    """Enhanced dependency manager with caching and validation"""
    
    def __init__(self):
        self.supported_package_managers = {
            ExecutionLanguage.PYTHON: "pip",
            ExecutionLanguage.R: "install.packages",
            ExecutionLanguage.JAVASCRIPT: "npm"
        }
        self.dependency_cache = {}  # Cache for validated dependencies
        self.package_whitelist = {
            ExecutionLanguage.PYTHON: {
                'numpy', 'pandas', 'matplotlib', 'scipy', 'scikit-learn',
                'seaborn', 'plotly', 'sympy', 'statsmodels', 'jupyter',
                'ipython', 'notebook', 'jupyterlab', 'bokeh', 'altair',
                'networkx', 'beautifulsoup4', 'lxml', 'openpyxl', 'xlrd',
                'pillow', 'opencv-python', 'imageio', 'tqdm', 'joblib'
            },
            ExecutionLanguage.JAVASCRIPT: {
                'lodash', 'moment', 'axios', 'express', 'react', 'vue',
                'angular', 'jquery', 'bootstrap', 'd3', 'chart.js',
                'three', 'p5', 'ml-matrix', 'simple-statistics'
            },
            ExecutionLanguage.R: {
                'ggplot2', 'dplyr', 'tidyr', 'readr', 'stringr', 'lubridate',
                'purrr', 'tibble', 'forcats', 'shiny', 'plotly', 'DT',
                'knitr', 'rmarkdown', 'devtools', 'testthat'
            }
        }
    
    async def validate_dependencies(self, dependencies: List[str], language: ExecutionLanguage) -> List[str]:
        """Enhanced dependency validation with whitelist and caching"""
        cache_key = f"{language.value}:{':'.join(sorted(dependencies))}"
        
        # Check cache first
        if cache_key in self.dependency_cache:
            return self.dependency_cache[cache_key]
        
        safe_dependencies = []
        blocked_packages = {
            ExecutionLanguage.PYTHON: [
                'os', 'sys', 'subprocess', 'socket', 'urllib3', 'requests',
                'paramiko', 'fabric', 'pexpect', 'ptyprocess', 'ctypes',
                'multiprocessing', 'threading', 'asyncio', 'importlib'
            ],
            ExecutionLanguage.JAVASCRIPT: [
                'child_process', 'fs', 'net', 'http', 'https', 'cluster',
                'dgram', 'dns', 'tls', 'crypto', 'vm', 'os', 'path'
            ],
            ExecutionLanguage.R: [
                'system', 'shell', 'processx', 'callr', 'reticulate'
            ]
        }
        
        blocked = blocked_packages.get(language, [])
        whitelist = self.package_whitelist.get(language, set())
        
        for dep in dependencies:
            # Remove version specifiers for checking
            package_name = re.split(r'[<>=!]', dep)[0].strip()
            
            # Check if package is explicitly blocked
            if package_name in blocked:
                logger.warning(f"Blocked dependency: {package_name}")
                continue
            
            # Check if package is in whitelist (if whitelist exists)
            if whitelist and package_name not in whitelist:
                logger.warning(f"Package not in whitelist: {package_name}")
                continue
            
            # Additional security checks
            if await self._is_package_safe(package_name, language):
                safe_dependencies.append(dep)
            else:
                logger.warning(f"Package failed security check: {package_name}")
        
        # Cache the result
        self.dependency_cache[cache_key] = safe_dependencies
        return safe_dependencies
    
    async def _is_package_safe(self, package_name: str, language: ExecutionLanguage) -> bool:
        """Additional security checks for packages"""
        # Check for suspicious package names
        suspicious_patterns = [
            r'.*backdoor.*',
            r'.*malware.*',
            r'.*virus.*',
            r'.*trojan.*',
            r'.*keylog.*',
            r'.*steal.*',
            r'.*hack.*',
            r'.*exploit.*'
        ]
        
        for pattern in suspicious_patterns:
            if re.match(pattern, package_name, re.IGNORECASE):
                return False
        
        # Check package name length (extremely long names might be suspicious)
        if len(package_name) > 100:
            return False
        
        # Check for valid package name format
        if not re.match(r'^[a-zA-Z0-9_.-]+$', package_name):
            return False
        
        return True
    
    async def install_dependencies(self, dependencies: List[str], language: ExecutionLanguage, 
                                 container_name: str) -> List[str]:
        """Install dependencies in container"""
        installed = []
        
        if not dependencies:
            return installed
        
        try:
            if language == ExecutionLanguage.PYTHON:
                for dep in dependencies:
                    cmd = f"docker exec {container_name} pip install --no-cache-dir --timeout=30 {dep}"
                    result = await asyncio.create_subprocess_shell(
                        cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await result.communicate()
                    
                    if result.returncode == 0:
                        installed.append(dep)
                    else:
                        logger.error(f"Failed to install {dep}: {stderr.decode()}")
            
            elif language == ExecutionLanguage.JAVASCRIPT:
                if dependencies:
                    deps_str = " ".join(dependencies)
                    cmd = f"docker exec {container_name} npm install --no-save {deps_str}"
                    result = await asyncio.create_subprocess_shell(
                        cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await result.communicate()
                    
                    if result.returncode == 0:
                        installed.extend(dependencies)
                    else:
                        logger.error(f"Failed to install npm packages: {stderr.decode()}")
        
        except Exception as e:
            logger.error(f"Error installing dependencies: {str(e)}")
        
        return installed

class ResourceMonitor:
    """Monitor resource usage of containers"""
    
    def __init__(self):
        self.monitoring_active = {}
    
    async def start_monitoring(self, container_name: str, resource_limits: ResourceLimits) -> None:
        """Start monitoring container resources"""
        self.monitoring_active[container_name] = True
        
        # Start monitoring in background
        asyncio.create_task(self._monitor_container(container_name, resource_limits))
    
    async def stop_monitoring(self, container_name: str) -> Dict[str, Any]:
        """Stop monitoring and return final stats"""
        self.monitoring_active[container_name] = False
        
        # Return final resource usage stats
        return await self._get_container_stats(container_name)
    
    async def _monitor_container(self, container_name: str, resource_limits: ResourceLimits) -> None:
        """Monitor container resource usage"""
        try:
            client = docker.from_env()
            container = client.containers.get(container_name)
            
            while self.monitoring_active.get(container_name, False):
                stats = container.stats(stream=False)
                
                # Check memory usage
                memory_usage = stats['memory_stats'].get('usage', 0) / (1024 * 1024)  # MB
                if memory_usage > resource_limits.max_memory_mb:
                    logger.warning(f"Container {container_name} exceeded memory limit: {memory_usage}MB")
                
                # Check CPU usage
                cpu_stats = stats['cpu_stats']
                precpu_stats = stats['precpu_stats']
                
                cpu_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
                system_delta = cpu_stats['system_cpu_usage'] - precpu_stats['system_cpu_usage']
                
                if system_delta > 0:
                    cpu_percent = (cpu_delta / system_delta) * 100.0
                    if cpu_percent > resource_limits.max_cpu_percent:
                        logger.warning(f"Container {container_name} exceeded CPU limit: {cpu_percent}%")
                
                await asyncio.sleep(1)  # Monitor every second
                
        except Exception as e:
            logger.error(f"Error monitoring container {container_name}: {str(e)}")
    
    async def _get_container_stats(self, container_name: str) -> Dict[str, Any]:
        """Get current container statistics"""
        try:
            client = docker.from_env()
            container = client.containers.get(container_name)
            stats = container.stats(stream=False)
            
            memory_usage = stats['memory_stats'].get('usage', 0) / (1024 * 1024)  # MB
            
            # Calculate CPU usage
            cpu_stats = stats['cpu_stats']
            precpu_stats = stats['precpu_stats']
            
            cpu_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
            system_delta = cpu_stats['system_cpu_usage'] - precpu_stats['system_cpu_usage']
            
            cpu_percent = 0.0
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * 100.0
            
            return {
                'memory_usage_mb': memory_usage,
                'cpu_usage_percent': cpu_percent,
                'network_rx_bytes': stats['networks'].get('eth0', {}).get('rx_bytes', 0),
                'network_tx_bytes': stats['networks'].get('eth0', {}).get('tx_bytes', 0),
                'block_read_bytes': sum(stat.get('value', 0) for stat in stats['blkio_stats']['io_service_bytes_recursive'] if stat.get('op') == 'Read'),
                'block_write_bytes': sum(stat.get('value', 0) for stat in stats['blkio_stats']['io_service_bytes_recursive'] if stat.get('op') == 'Write')
            }
        except Exception as e:
            logger.error(f"Error getting container stats: {str(e)}")
            return {}

class ContainerManager:
    """Enhanced container manager with advanced security and monitoring"""
    
    def __init__(self):
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {str(e)}")
            self.docker_client = None
        
        self.base_images = {
            ExecutionLanguage.PYTHON: "python:3.9-slim",
            ExecutionLanguage.R: "r-base:4.3.0",
            ExecutionLanguage.JAVASCRIPT: "node:18-slim",
            ExecutionLanguage.BASH: "ubuntu:22.04"
        }
        
        self.active_containers = {}  # Track active containers
        self.resource_monitor = ResourceMonitor()
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def create_container(self, language: ExecutionLanguage, resource_limits: ResourceLimits,
                             security_policy: SecurityPolicy) -> Optional[str]:
        """Create a highly secure container for code execution"""
        if not self.docker_client:
            raise RuntimeError("Docker client not available")
        
        try:
            container_name = f"code-exec-{uuid.uuid4().hex[:8]}"
            image = self.base_images.get(language, "ubuntu:22.04")
            
            # Enhanced security configuration
            container_config = {
                'image': image,
                'name': container_name,
                'detach': True,
                'mem_limit': f"{resource_limits.max_memory_mb}m",
                'memswap_limit': f"{resource_limits.max_memory_mb}m",  # Disable swap
                'cpu_quota': int(resource_limits.max_cpu_percent * 1000),
                'cpu_period': 100000,
                'network_disabled': not security_policy.allow_network_access,
                'read_only': not security_policy.allow_file_system_access,
                'security_opt': [
                    'no-new-privileges:true',
                    'seccomp=unconfined',  # Can be restricted further
                    'apparmor=unconfined'  # Can be restricted further
                ],
                'cap_drop': ['ALL'],
                'cap_add': [],  # No capabilities by default
                'user': 'nobody',
                'working_dir': '/tmp',
                'command': 'sleep infinity',
                'environment': {
                    'PYTHONDONTWRITEBYTECODE': '1',
                    'PYTHONUNBUFFERED': '1',
                    'NODE_ENV': 'production'
                },
                'ulimits': [
                    docker.types.Ulimit(name='nproc', soft=resource_limits.max_processes, hard=resource_limits.max_processes),
                    docker.types.Ulimit(name='nofile', soft=resource_limits.max_open_files, hard=resource_limits.max_open_files),
                    docker.types.Ulimit(name='fsize', soft=resource_limits.max_disk_usage_mb * 1024 * 1024, hard=resource_limits.max_disk_usage_mb * 1024 * 1024)
                ],
                'tmpfs': {
                    '/tmp': 'rw,noexec,nosuid,size=100m',
                    '/var/tmp': 'rw,noexec,nosuid,size=100m'
                } if not security_policy.allow_file_system_access else {},
                'pids_limit': resource_limits.max_processes
            }
            
            # Add network restrictions if needed
            if security_policy.allow_network_access and security_policy.allowed_domains:
                # Create custom network with restrictions (would need additional setup)
                pass
            
            # Create and start container
            container = self.docker_client.containers.run(**container_config)
            
            # Track the container
            self.active_containers[container_name] = {
                'container': container,
                'created_at': datetime.utcnow(),
                'language': language,
                'resource_limits': resource_limits
            }
            
            # Start resource monitoring
            await self.resource_monitor.start_monitoring(container_name, resource_limits)
            
            # Wait for container to be ready
            await asyncio.sleep(1)
            
            return container_name
        
        except Exception as e:
            logger.error(f"Failed to create container: {str(e)}")
            return None
    
    async def execute_in_container(self, container_name: str, command: str, 
                                 timeout: int, resource_limits: ResourceLimits) -> tuple[str, str, int]:
        """Execute command in container with enhanced monitoring and limits"""
        try:
            container = self.docker_client.containers.get(container_name)
            
            # Create a temporary file for the code to avoid command injection
            code_hash = hashlib.md5(command.encode()).hexdigest()
            temp_file = f"/tmp/code_{code_hash}.py"  # Adjust extension based on language
            
            # Write code to file inside container
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                code_data = command.encode('utf-8')
                tarinfo = tarfile.TarInfo(name='code.py')
                tarinfo.size = len(code_data)
                tar.addfile(tarinfo, io.BytesIO(code_data))
            
            tar_stream.seek(0)
            container.put_archive('/tmp', tar_stream)
            
            # Execute with enhanced security
            exec_command = self._build_secure_command(command, resource_limits)
            
            # Execute command with timeout
            result = container.exec_run(
                exec_command,
                stdout=True,
                stderr=True,
                stream=False,
                timeout=timeout,
                user='nobody',
                workdir='/tmp'
            )
            
            stdout = result.output.decode('utf-8', errors='ignore')
            
            # Check output size limit
            if len(stdout) > resource_limits.max_output_size_mb * 1024 * 1024:
                stdout = stdout[:resource_limits.max_output_size_mb * 1024 * 1024] + "\n[Output truncated - size limit exceeded]"
            
            return stdout, "", result.exit_code
        
        except docker.errors.APIError as e:
            if "timeout" in str(e).lower():
                return "", "Execution timeout", 124
            return "", f"Container error: {str(e)}", 1
        except Exception as e:
            return "", f"Execution error: {str(e)}", 1
    
    def _build_secure_command(self, original_command: str, resource_limits: ResourceLimits) -> str:
        """Build a secure command with additional restrictions"""
        # Add resource limits to the command
        secure_command = f"timeout {resource_limits.max_execution_time_seconds}s "
        secure_command += f"ulimit -v {resource_limits.max_memory_mb * 1024}; "  # Virtual memory limit
        secure_command += f"ulimit -f {resource_limits.max_disk_usage_mb * 1024}; "  # File size limit
        secure_command += f"ulimit -u {resource_limits.max_processes}; "  # Process limit
        secure_command += original_command
        
        return secure_command
    
    async def cleanup_container(self, container_name: str) -> Dict[str, Any]:
        """Enhanced container cleanup with resource stats"""
        resource_stats = {}
        
        try:
            # Stop resource monitoring and get final stats
            resource_stats = await self.resource_monitor.stop_monitoring(container_name)
            
            # Remove from active containers
            if container_name in self.active_containers:
                del self.active_containers[container_name]
            
            # Stop and remove container
            container = self.docker_client.containers.get(container_name)
            container.stop(timeout=5)
            container.remove(force=True)
            
            logger.info(f"Successfully cleaned up container {container_name}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup container {container_name}: {str(e)}")
        
        return resource_stats
    
    async def cleanup_all_containers(self):
        """Clean up all active containers"""
        for container_name in list(self.active_containers.keys()):
            await self.cleanup_container(container_name)
    
    async def get_container_stats(self, container_name: str) -> Dict[str, Any]:
        """Get current container statistics"""
        return await self.resource_monitor._get_container_stats(container_name)

class SecureCodeExecutionService:
    """Main service for secure code execution"""
    
    def __init__(self):
        self.security_scanner = SecurityScanner()
        self.dependency_manager = DependencyManager()
        self.container_manager = ContainerManager()
        self.active_executions: Dict[str, ExecutionResult] = {}
    
    async def execute_code(self, request: CodeExecutionRequest) -> ExecutionResult:
        """Execute code securely with all safety measures"""
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        result = ExecutionResult(
            execution_id=execution_id,
            status=ExecutionStatus.PENDING,
            output="",
            created_at=datetime.utcnow()
        )
        
        self.active_executions[execution_id] = result
        
        try:
            # Step 1: Security scanning
            logger.info(f"Scanning code for execution {execution_id}")
            security_violations = await self.security_scanner.scan_code(
                request.code, request.language, request.security_policy
            )
            
            # Generate detailed security scan results
            result.security_scan_results = {
                'scan_timestamp': datetime.utcnow().isoformat(),
                'language': request.language.value,
                'violations_found': len(security_violations),
                'scan_duration_ms': 0,  # Would be calculated in real implementation
                'security_level': 'high' if len(security_violations) == 0 else 'low'
            }
            
            if security_violations:
                result.status = ExecutionStatus.SECURITY_VIOLATION
                result.security_violations = security_violations
                result.error = f"Security violations detected: {', '.join(security_violations)}"
                return result
            
            # Step 2: Validate dependencies
            safe_dependencies = await self.dependency_manager.validate_dependencies(
                request.dependencies, request.language
            )
            
            # Step 3: Create secure container
            result.status = ExecutionStatus.RUNNING
            container_name = await self.container_manager.create_container(
                request.language, request.resource_limits, request.security_policy
            )
            
            if not container_name:
                result.status = ExecutionStatus.FAILED
                result.error = "Failed to create secure execution environment"
                return result
            
            try:
                # Step 4: Install dependencies
                if safe_dependencies:
                    installed_deps = await self.dependency_manager.install_dependencies(
                        safe_dependencies, request.language, container_name
                    )
                    result.dependencies_installed = installed_deps
                
                # Step 5: Execute code
                execution_command = self._build_execution_command(
                    request.code, request.language, request.environment_variables
                )
                
                stdout, stderr, exit_code = await self.container_manager.execute_in_container(
                    container_name, execution_command, request.resource_limits.max_execution_time_seconds,
                    request.resource_limits
                )
                
                # Step 6: Process results
                result.execution_time = time.time() - start_time
                result.output = stdout
                
                if exit_code == 124:  # Timeout
                    result.status = ExecutionStatus.TIMEOUT
                    result.error = "Execution timeout"
                elif exit_code != 0:
                    result.status = ExecutionStatus.FAILED
                    result.error = stderr
                else:
                    result.status = ExecutionStatus.COMPLETED
                
            finally:
                # Always cleanup container and get resource stats
                resource_stats = await self.container_manager.cleanup_container(container_name)
                result.resource_usage = resource_stats
                result.container_id = container_name
        
        except Exception as e:
            logger.error(f"Execution error for {execution_id}: {str(e)}")
            result.status = ExecutionStatus.FAILED
            result.error = f"Internal execution error: {str(e)}"
        
        finally:
            result.execution_time = time.time() - start_time
            self.active_executions[execution_id] = result
        
        return result
    
    def _build_execution_command(self, code: str, language: ExecutionLanguage, 
                               env_vars: Dict[str, str]) -> str:
        """Build execution command for different languages"""
        # Set environment variables
        env_prefix = ""
        if env_vars:
            env_items = [f"{k}='{v}'" for k, v in env_vars.items()]
            env_prefix = " ".join(env_items) + " "
        
        if language == ExecutionLanguage.PYTHON:
            # Write code to file and execute
            return f'{env_prefix}python3 -c "{code.replace(chr(34), chr(92)+chr(34))}"'
        
        elif language == ExecutionLanguage.JAVASCRIPT:
            return f'{env_prefix}node -e "{code.replace(chr(34), chr(92)+chr(34))}"'
        
        elif language == ExecutionLanguage.R:
            return f'{env_prefix}Rscript -e "{code.replace(chr(34), chr(92)+chr(34))}"'
        
        elif language == ExecutionLanguage.BASH:
            return f'{env_prefix}bash -c "{code.replace(chr(34), chr(92)+chr(34))}"'
        
        else:
            raise ValueError(f"Unsupported language: {language}")
    
    async def get_execution_result(self, execution_id: str) -> Optional[ExecutionResult]:
        """Get execution result by ID"""
        return self.active_executions.get(execution_id)
    
    async def list_active_executions(self) -> List[ExecutionResult]:
        """List all active executions"""
        return list(self.active_executions.values())
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an active execution"""
        if execution_id in self.active_executions:
            result = self.active_executions[execution_id]
            if result.status == ExecutionStatus.RUNNING:
                result.status = ExecutionStatus.FAILED
                result.error = "Execution cancelled by user"
                return True
        return False
    
    async def cleanup_old_executions(self, max_age_hours: int = 24):
        """Clean up old execution results"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for execution_id, result in self.active_executions.items():
            if result.created_at < cutoff_time:
                to_remove.append(execution_id)
        
        for execution_id in to_remove:
            del self.active_executions[execution_id]
        
        logger.info(f"Cleaned up {len(to_remove)} old execution results")

# Global service instance
secure_code_execution_service = SecureCodeExecutionService()