"""
Secure Code Execution API Endpoints

Provides REST API endpoints for secure code execution with containerized sandboxing.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from services.secure_code_execution import (
    SecureCodeExecutionService,
    CodeExecutionRequest,
    ExecutionResult,
    ExecutionLanguage,
    ExecutionStatus,
    ResourceLimits,
    SecurityPolicy,
    secure_code_execution_service
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/secure-execution", tags=["secure-execution"])

# Pydantic models for API
class ResourceLimitsModel(BaseModel):
    max_memory_mb: int = Field(default=512, ge=64, le=2048, description="Maximum memory in MB")
    max_cpu_percent: float = Field(default=50.0, ge=10.0, le=100.0, description="Maximum CPU percentage")
    max_execution_time_seconds: int = Field(default=30, ge=1, le=300, description="Maximum execution time in seconds")
    max_disk_usage_mb: int = Field(default=100, ge=10, le=1024, description="Maximum disk usage in MB")
    max_network_requests: int = Field(default=10, ge=0, le=100, description="Maximum network requests")
    max_processes: int = Field(default=1, ge=1, le=10, description="Maximum number of processes")
    max_open_files: int = Field(default=100, ge=10, le=1000, description="Maximum number of open files")
    max_output_size_mb: int = Field(default=10, ge=1, le=100, description="Maximum output size in MB")

class SecurityPolicyModel(BaseModel):
    allow_network_access: bool = Field(default=False, description="Allow network access")
    allow_file_system_access: bool = Field(default=False, description="Allow file system access")
    allow_subprocess_execution: bool = Field(default=False, description="Allow subprocess execution")
    blocked_imports: Optional[List[str]] = Field(default=None, description="List of blocked imports")
    blocked_functions: Optional[List[str]] = Field(default=None, description="List of blocked functions")
    allowed_domains: Optional[List[str]] = Field(default=None, description="List of allowed domains for network access")
    scan_for_malware: bool = Field(default=True, description="Enable malware signature scanning")
    enable_code_signing: bool = Field(default=False, description="Enable code signing verification")
    max_recursion_depth: int = Field(default=100, ge=1, le=1000, description="Maximum recursion depth")

class CodeExecutionRequestModel(BaseModel):
    code: str = Field(..., description="Code to execute")
    language: ExecutionLanguage = Field(..., description="Programming language")
    dependencies: Optional[List[str]] = Field(default=[], description="List of dependencies to install")
    resource_limits: Optional[ResourceLimitsModel] = Field(default=None, description="Resource limits")
    security_policy: Optional[SecurityPolicyModel] = Field(default=None, description="Security policy")
    environment_variables: Optional[Dict[str, str]] = Field(default={}, description="Environment variables")

class ExecutionResultModel(BaseModel):
    execution_id: str
    status: ExecutionStatus
    output: str
    error: Optional[str] = None
    execution_time: float
    memory_used_mb: float
    cpu_used_percent: float
    security_violations: List[str]
    dependencies_installed: List[str]
    created_at: datetime
    container_id: Optional[str] = None
    resource_usage: Optional[Dict[str, Any]] = None
    security_scan_results: Optional[Dict[str, Any]] = None
    warnings: Optional[List[str]] = None

    class Config:
        from_attributes = True

@router.post("/execute", response_model=ExecutionResultModel)
async def execute_code(request: CodeExecutionRequestModel, background_tasks: BackgroundTasks):
    """
    Execute code securely in a containerized environment
    
    This endpoint provides secure code execution with:
    - Containerized sandboxing
    - Resource limits and timeouts
    - Security scanning and policy enforcement
    - Dependency management
    - Multiple language support
    """
    try:
        # Convert Pydantic models to service models
        resource_limits = None
        if request.resource_limits:
            resource_limits = ResourceLimits(
                max_memory_mb=request.resource_limits.max_memory_mb,
                max_cpu_percent=request.resource_limits.max_cpu_percent,
                max_execution_time_seconds=request.resource_limits.max_execution_time_seconds,
                max_disk_usage_mb=request.resource_limits.max_disk_usage_mb,
                max_network_requests=request.resource_limits.max_network_requests,
                max_processes=request.resource_limits.max_processes,
                max_open_files=request.resource_limits.max_open_files,
                max_output_size_mb=request.resource_limits.max_output_size_mb
            )
        
        security_policy = None
        if request.security_policy:
            security_policy = SecurityPolicy(
                allow_network_access=request.security_policy.allow_network_access,
                allow_file_system_access=request.security_policy.allow_file_system_access,
                allow_subprocess_execution=request.security_policy.allow_subprocess_execution,
                blocked_imports=request.security_policy.blocked_imports,
                blocked_functions=request.security_policy.blocked_functions,
                allowed_domains=request.security_policy.allowed_domains,
                scan_for_malware=request.security_policy.scan_for_malware,
                enable_code_signing=request.security_policy.enable_code_signing,
                max_recursion_depth=request.security_policy.max_recursion_depth
            )
        
        execution_request = CodeExecutionRequest(
            code=request.code,
            language=request.language,
            dependencies=request.dependencies or [],
            resource_limits=resource_limits,
            security_policy=security_policy,
            environment_variables=request.environment_variables or {}
        )
        
        # Execute code
        result = await secure_code_execution_service.execute_code(execution_request)
        
        # Schedule cleanup of old executions in background
        background_tasks.add_task(secure_code_execution_service.cleanup_old_executions)
        
        return ExecutionResultModel(
            execution_id=result.execution_id,
            status=result.status,
            output=result.output,
            error=result.error,
            execution_time=result.execution_time,
            memory_used_mb=result.memory_used_mb,
            cpu_used_percent=result.cpu_used_percent,
            security_violations=result.security_violations,
            dependencies_installed=result.dependencies_installed,
            created_at=result.created_at,
            container_id=result.container_id,
            resource_usage=result.resource_usage,
            security_scan_results=result.security_scan_results,
            warnings=result.warnings
        )
    
    except Exception as e:
        logger.error(f"Code execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Code execution failed: {str(e)}")

@router.get("/result/{execution_id}", response_model=ExecutionResultModel)
async def get_execution_result(execution_id: str):
    """
    Get execution result by ID
    """
    try:
        result = await secure_code_execution_service.get_execution_result(execution_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Execution result not found")
        
        return ExecutionResultModel(
            execution_id=result.execution_id,
            status=result.status,
            output=result.output,
            error=result.error,
            execution_time=result.execution_time,
            memory_used_mb=result.memory_used_mb,
            cpu_used_percent=result.cpu_used_percent,
            security_violations=result.security_violations,
            dependencies_installed=result.dependencies_installed,
            created_at=result.created_at,
            container_id=result.container_id,
            resource_usage=result.resource_usage,
            security_scan_results=result.security_scan_results,
            warnings=result.warnings
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving execution result: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve execution result: {str(e)}")

@router.get("/executions", response_model=List[ExecutionResultModel])
async def list_active_executions():
    """
    List all active executions
    """
    try:
        results = await secure_code_execution_service.list_active_executions()
        
        return [
            ExecutionResultModel(
                execution_id=result.execution_id,
                status=result.status,
                output=result.output,
                error=result.error,
                execution_time=result.execution_time,
                memory_used_mb=result.memory_used_mb,
                cpu_used_percent=result.cpu_used_percent,
                security_violations=result.security_violations,
                dependencies_installed=result.dependencies_installed,
                created_at=result.created_at,
                container_id=result.container_id,
                resource_usage=result.resource_usage,
                security_scan_results=result.security_scan_results,
                warnings=result.warnings
            )
            for result in results
        ]
    
    except Exception as e:
        logger.error(f"Error listing executions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list executions: {str(e)}")

@router.post("/cancel/{execution_id}")
async def cancel_execution(execution_id: str):
    """
    Cancel an active execution
    """
    try:
        success = await secure_code_execution_service.cancel_execution(execution_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Execution not found or cannot be cancelled")
        
        return {"message": "Execution cancelled successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel execution: {str(e)}")

@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported programming languages
    """
    return {
        "languages": [
            {
                "name": "Python",
                "value": "python",
                "description": "Python 3.9 with common scientific libraries"
            },
            {
                "name": "R",
                "value": "r",
                "description": "R statistical computing language"
            },
            {
                "name": "JavaScript",
                "value": "javascript",
                "description": "Node.js JavaScript runtime"
            },
            {
                "name": "Bash",
                "value": "bash",
                "description": "Bash shell scripting"
            },
            {
                "name": "SQL",
                "value": "sql",
                "description": "SQL queries (limited support)"
            }
        ]
    }

@router.get("/security-policy/default")
async def get_default_security_policy():
    """
    Get default security policy configuration
    """
    policy = SecurityPolicy()
    return {
        "allow_network_access": policy.allow_network_access,
        "allow_file_system_access": policy.allow_file_system_access,
        "allow_subprocess_execution": policy.allow_subprocess_execution,
        "blocked_imports": policy.blocked_imports,
        "blocked_functions": policy.blocked_functions,
        "allowed_domains": policy.allowed_domains,
        "scan_for_malware": policy.scan_for_malware,
        "enable_code_signing": policy.enable_code_signing,
        "max_recursion_depth": policy.max_recursion_depth
    }

@router.get("/resource-limits/default")
async def get_default_resource_limits():
    """
    Get default resource limits configuration
    """
    limits = ResourceLimits()
    return {
        "max_memory_mb": limits.max_memory_mb,
        "max_cpu_percent": limits.max_cpu_percent,
        "max_execution_time_seconds": limits.max_execution_time_seconds,
        "max_disk_usage_mb": limits.max_disk_usage_mb,
        "max_network_requests": limits.max_network_requests,
        "max_processes": limits.max_processes,
        "max_open_files": limits.max_open_files,
        "max_output_size_mb": limits.max_output_size_mb
    }

@router.post("/validate-code")
async def validate_code(code: str, language: ExecutionLanguage):
    """
    Validate code for security violations without executing
    """
    try:
        security_policy = SecurityPolicy()
        scanner = secure_code_execution_service.security_scanner
        
        violations = await scanner.scan_code(code, language, security_policy)
        
        return {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "language": language.value
        }
    
    except Exception as e:
        logger.error(f"Code validation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Code validation failed: {str(e)}")

@router.get("/container/{container_id}/stats")
async def get_container_stats(container_id: str):
    """
    Get real-time container statistics
    """
    try:
        stats = await secure_code_execution_service.container_manager.get_container_stats(container_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Container not found or not accessible")
        
        return {
            "container_id": container_id,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting container stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get container stats: {str(e)}")

@router.delete("/cleanup")
async def cleanup_old_executions(max_age_hours: int = 24):
    """
    Clean up old execution results
    """
    try:
        await secure_code_execution_service.cleanup_old_executions(max_age_hours)
        return {"message": f"Cleaned up executions older than {max_age_hours} hours"}
    
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")