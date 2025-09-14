"""
Advanced API endpoints with comprehensive error handling and service management integration
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any

# Import service management infrastructure
from core import service_manager, get_service_logger

# Import error handling utilities
from core.error_handler import (
    handle_endpoint_errors,
    EndpointErrorHandler,
    ServiceUnavailableError,
    ValidationError,
    validate_request_data,
    create_fallback_response
)

# Import Pydantic models
from models.schemas import (
    DetailedHealthCheckResponse,
    ServicesHealthCheckResponse,
    ServiceHealthCheckResponse,
    ServiceHealthResponse
)

logger = get_service_logger('advanced_endpoints', 'general')

router = APIRouter(prefix="/api/advanced", tags=["advanced"])

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "message": "Advanced endpoints are working"}

@router.get("/health/detailed", response_model=DetailedHealthCheckResponse)
@handle_endpoint_errors("detailed_health_check")
async def detailed_health_check():
    """
    Detailed health check endpoint that reports individual service status
    
    Returns comprehensive health information including:
    - Overall system status
    - Individual service health status
    - Service initialization summary
    - Timestamp of health check
    """
    # Get service health information
    service_health = service_manager.get_service_health()
    initialization_summary = service_manager.get_initialization_summary()
    
    # Determine overall status based on service health
    overall_status = "ok"
    if initialization_summary.get("failed_services", 0) > 0:
        overall_status = "degraded"
    
    return DetailedHealthCheckResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        services=service_health,
        summary=initialization_summary,
        message="Detailed health check completed successfully"
    )

@router.get("/health/services", response_model=ServicesHealthCheckResponse)
@handle_endpoint_errors(
    "services_health_check",
    fallback_response=create_fallback_response(
        message="Services health check temporarily unavailable",
        data={"services": {}},
        status="unavailable"
    )
)
async def services_health_check():
    """
    Check health of all services with real-time health checks
    
    Performs active health checks on all registered services and returns
    their current status, including any error messages and dependencies.
    """
    # Perform health checks on all services
    health_results = await service_manager.check_all_services_health()
    
    # Convert to Pydantic models
    service_responses = {}
    for service_name, health in health_results.items():
        service_responses[service_name] = ServiceHealthResponse(
            name=health.name,
            status=health.status,
            last_check=health.last_check,
            error_message=health.error_message,
            dependencies=health.dependencies,
            initialization_time=health.initialization_time
        )
    
    return ServicesHealthCheckResponse(
        status="ok",
        timestamp=datetime.utcnow(),
        services=service_responses
    )

@router.get("/health/service/{service_name}", response_model=ServiceHealthCheckResponse)
@handle_endpoint_errors(
    "service_health_check",
    fallback_response=create_fallback_response(
        message="Service health check temporarily unavailable",
        data={"service": {"name": "unknown", "status": "unavailable"}},
        status="unavailable"
    )
)
async def service_health_check(service_name: str):
    """
    Check health of a specific service
    
    Performs a real-time health check on the specified service and returns
    detailed status information including error messages and dependencies.
    
    Args:
        service_name: Name of the service to check
    """
    health = await service_manager.check_service_health(service_name)
    
    service_response = ServiceHealthResponse(
        name=health.name,
        status=health.status,
        last_check=health.last_check,
        error_message=health.error_message,
        dependencies=health.dependencies,
        initialization_time=health.initialization_time
    )
    
    return ServiceHealthCheckResponse(
        status="ok",
        timestamp=datetime.utcnow(),
        service=service_response
    )

@router.get("/health/monitoring")
@handle_endpoint_errors(
    "health_monitoring_status",
    fallback_response=create_fallback_response(
        message="Health monitoring status temporarily unavailable",
        data={"monitoring": {"enabled": "unknown", "status": "unavailable"}},
        status="unavailable"
    )
)
async def health_monitoring_status():
    """
    Get health monitoring configuration and status
    
    Returns information about the health monitoring system including:
    - Monitoring configuration (interval, cache TTL, enabled status)
    - Current monitoring status (active/inactive)
    - Cache statistics and status
    """
    monitoring_status = service_manager.get_health_monitoring_status()
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow(),
        "monitoring": monitoring_status
    }

@router.post("/health/monitoring/configure")
@handle_endpoint_errors(
    "configure_health_monitoring",
    fallback_response=create_fallback_response(
        message="Health monitoring configuration temporarily unavailable",
        data={"configuration": {"status": "unavailable"}},
        status="unavailable"
    )
)
async def configure_health_monitoring(
    interval: int = None,
    cache_ttl: int = None,
    enabled: bool = None
):
    """
    Configure health monitoring parameters
    
    Args:
        interval: Health check interval in seconds (optional)
        cache_ttl: Cache TTL in seconds (optional)
        enabled: Enable/disable monitoring (optional)
    """
    service_manager.configure_health_monitoring(
        interval=interval,
        cache_ttl=cache_ttl,
        enabled=enabled
    )
    
    # Restart monitoring if configuration changed and monitoring is enabled
    if enabled is not None:
        if enabled:
            await service_manager.start_health_monitoring()
        else:
            await service_manager.stop_health_monitoring()
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow(),
        "message": "Health monitoring configuration updated",
        "configuration": service_manager.get_health_monitoring_status()
    }

@router.get("/database/health")
@handle_endpoint_errors(
    "database_health_check",
    required_services=["database"],
    fallback_response=create_fallback_response(
        message="Database service unavailable",
        data={"service_registered": False, "connection": "unknown"},
        status="unavailable"
    )
)
async def database_health_check():
    """
    Check database connection and health status
    
    Returns detailed information about database connectivity,
    table status, and performance metrics.
    """
    # Get database service (guaranteed to be available due to decorator)
    database_service = service_manager.get_service("database")
    
    # Perform database health check
    health_info = await database_service.health_check()
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow(),
        "database": health_info
    }

@router.get("/database/connection")
@handle_endpoint_errors(
    "database_connection_test",
    required_services=["database"],
    fallback_response=create_fallback_response(
        message="Database connection test unavailable - service not initialized",
        data={"status": "unknown", "connection": "unavailable"},
        status="unavailable"
    )
)
async def database_connection_test():
    """
    Test database connectivity
    
    Performs a simple connection test to verify database availability.
    """
    # Get database service (guaranteed to be available due to decorator)
    database_service = service_manager.get_service("database")
    
    # Test connection
    if database_service.is_healthy():
        return {
            "status": "connected",
            "timestamp": datetime.utcnow(),
            "message": "Database connection successful",
            "service_status": database_service.get_status()
        }
    else:
        return {
            "status": "disconnected",
            "timestamp": datetime.utcnow(),
            "message": "Database connection failed",
            "service_status": database_service.get_status()
        }

@router.get("/database/models")
@handle_endpoint_errors(
    "database_models_info",
    required_services=["database"],
    fallback_response=create_fallback_response(
        message="Database models information unavailable - service not initialized",
        data={"models": [], "model_count": 0},
        status="unavailable"
    )
)
async def database_models_info():
    """
    Get information about available database models
    
    Returns list of available database models and their status.
    """
    # Get database service (guaranteed to be available due to decorator)
    database_service = service_manager.get_service("database")
    
    available_models = database_service.get_available_models()
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow(),
        "models": available_models,
        "model_count": len(available_models),
        "service_status": database_service.get_status()
    }

@router.get("/database/migration/check")
@handle_endpoint_errors(
    "database_migration_check",
    required_services=["database"],
    fallback_response=create_fallback_response(
        message="Database migration check unavailable - service not initialized",
        data={"tables": {}, "connection": "unknown"},
        status="unavailable"
    )
)
async def database_migration_check():
    """
    Check database migration status
    
    Verifies if database tables are properly created and up to date.
    """
    # Get database service (guaranteed to be available due to decorator)
    database_service = service_manager.get_service("database")
    
    # Perform health check which includes table verification
    health_info = await database_service.health_check()
    
    migration_status = {
        "status": "ok" if health_info.get("status") == "healthy" else "needs_attention",
        "timestamp": datetime.utcnow(),
        "tables": health_info.get("details", {}).get("tables", {}),
        "connection": health_info.get("details", {}).get("connection", "unknown"),
        "message": "Migration check completed"
    }
    
    return migration_status

@router.get("/semantic-search/health")
@handle_endpoint_errors(
    "semantic_search_health_check",
    fallback_response=create_fallback_response(
        message="Semantic search health check temporarily unavailable",
        data={"service": {"status": "unavailable", "initialization": "unknown"}},
        status="unavailable"
    )
)
async def semantic_search_health_check():
    """
    Check semantic search service health
    
    Returns detailed information about semantic search service status,
    including initialization status and any error messages.
    """
    # Check if semantic search service is available
    semantic_search_service = service_manager.get_service("semantic_search")
    
    if not semantic_search_service:
        return {
            "status": "unavailable",
            "timestamp": datetime.utcnow(),
            "message": "Semantic search service not initialized",
            "details": {
                "service_registered": False,
                "initialization": "not_started"
            }
        }
    
    # Perform service health check
    health = await service_manager.check_service_health("semantic_search")
    
    return {
        "status": "ok" if health.status.value == "healthy" else health.status.value,
        "timestamp": datetime.utcnow(),
        "service": {
            "name": health.name,
            "status": health.status.value,
            "last_check": health.last_check.isoformat(),
            "error_message": health.error_message,
            "dependencies": health.dependencies,
            "initialization_time": health.initialization_time
        },
        "message": "Semantic search service health check completed"
    }

@router.get("/research-automation/health")
@handle_endpoint_errors(
    "research_automation_health_check",
    fallback_response=create_fallback_response(
        message="Research automation health check temporarily unavailable",
        data={"service": {"status": "unavailable", "initialization": "unknown"}},
        status="unavailable"
    )
)
async def research_automation_health_check():
    """
    Check research automation service health
    
    Returns detailed information about research automation service status,
    including workflow status and scheduler information.
    """
    # Check if research automation service is available
    research_automation_service = service_manager.get_service("research_automation")
    
    if not research_automation_service:
        return {
            "status": "unavailable",
            "timestamp": datetime.utcnow(),
            "message": "Research automation service not initialized",
            "details": {
                "service_registered": False,
                "initialization": "not_started"
            }
        }
    
    # Perform service health check
    health = await service_manager.check_service_health("research_automation")
    
    # Get additional service status
    service_status = research_automation_service.get_status()
    
    return {
        "status": "ok" if health.status.value == "healthy" else health.status.value,
        "timestamp": datetime.utcnow(),
        "service": {
            "name": health.name,
            "status": health.status.value,
            "last_check": health.last_check.isoformat(),
            "error_message": health.error_message,
            "dependencies": health.dependencies,
            "initialization_time": health.initialization_time,
            "service_details": service_status
        },
        "message": "Research automation service health check completed"
    }

@router.get("/advanced-analytics/health")
@handle_endpoint_errors(
    "advanced_analytics_health_check",
    fallback_response=create_fallback_response(
        message="Advanced analytics health check temporarily unavailable",
        data={"service": {"status": "unavailable", "initialization": "unknown"}},
        status="unavailable"
    )
)
async def advanced_analytics_health_check():
    """
    Check advanced analytics service health
    
    Returns detailed information about advanced analytics service status,
    including initialization status and any error messages.
    """
    # Check if advanced analytics service is available
    advanced_analytics_service = service_manager.get_service("advanced_analytics")
    
    if not advanced_analytics_service:
        return {
            "status": "unavailable",
            "timestamp": datetime.utcnow(),
            "message": "Advanced analytics service not initialized",
            "details": {
                "service_registered": False,
                "initialization": "not_started"
            }
        }
    
    # Perform service health check
    health = await service_manager.check_service_health("advanced_analytics")
    
    # Get additional service status
    service_status = advanced_analytics_service.get_status()
    
    return {
        "status": "ok" if health.status.value == "healthy" else health.status.value,
        "timestamp": datetime.utcnow(),
        "service": {
            "name": health.name,
            "status": health.status.value,
            "last_check": health.last_check.isoformat(),
            "error_message": health.error_message,
            "dependencies": health.dependencies,
            "initialization_time": health.initialization_time,
            "service_details": service_status
        },
        "message": "Advanced analytics service health check completed"
    }

@router.get("/knowledge-graph/health")
@handle_endpoint_errors(
    "knowledge_graph_health_check",
    fallback_response=create_fallback_response(
        message="Knowledge graph health check temporarily unavailable",
        data={"service": {"status": "unavailable", "initialization": "unknown"}},
        status="unavailable"
    )
)
async def knowledge_graph_health_check():
    """
    Check knowledge graph service health
    
    Returns detailed information about knowledge graph service status,
    including entity and relationship counts and any error messages.
    """
    # Check if knowledge graph service is available
    knowledge_graph_service = service_manager.get_service("knowledge_graph")
    
    if not knowledge_graph_service:
        return {
            "status": "unavailable",
            "timestamp": datetime.utcnow(),
            "message": "Knowledge graph service not initialized",
            "details": {
                "service_registered": False,
                "initialization": "not_started"
            }
        }
    
    # Perform service health check
    health = await service_manager.check_service_health("knowledge_graph")
    
    # Get additional service status
    service_status = knowledge_graph_service.get_status()
    
    return {
        "status": "ok" if health.status.value == "healthy" else health.status.value,
        "timestamp": datetime.utcnow(),
        "service": {
            "name": health.name,
            "status": health.status.value,
            "last_check": health.last_check.isoformat(),
            "error_message": health.error_message,
            "dependencies": health.dependencies,
            "initialization_time": health.initialization_time,
            "service_details": service_status
        },
        "message": "Knowledge graph service health check completed"
    }

@router.get("/test")
async def test_endpoint():
    """Test endpoint"""
    logger.info("Test endpoint called")
    return {
        "message": "Test endpoint working",
        "timestamp": datetime.utcnow().isoformat(),
        "service_manager_status": "initialized"
    }

# ============================================================================
# BASIC RESEARCH ENDPOINTS
# ============================================================================

@router.get("/research/status")
@handle_endpoint_errors(
    "research_status",
    fallback_response=create_fallback_response(
        message="Research services status check temporarily unavailable",
        data={"services": {}, "overall_status": "unknown"},
        status="unavailable"
    )
)
async def research_status():
    """
    Get research services status
    
    Returns the status of all research-related services including
    semantic search, research automation, and knowledge graph services.
    """
    research_services = [
        "semantic_search",
        "research_automation", 
        "advanced_analytics",
        "knowledge_graph"
    ]
    
    service_status = {}
    overall_status = "ok"
    
    for service_name in research_services:
        try:
            service = service_manager.get_service(service_name)
            if service:
                health = await service_manager.check_service_health(service_name)
                service_status[service_name] = {
                    "status": health.status.value,
                    "last_check": health.last_check.isoformat(),
                    "error_message": health.error_message,
                    "available": True
                }
                
                if health.status.value != "healthy":
                    overall_status = "degraded"
            else:
                service_status[service_name] = {
                    "status": "unavailable",
                    "available": False,
                    "error_message": "Service not initialized"
                }
                overall_status = "degraded"
                
        except Exception as e:
            logger.error(f"Error checking {service_name} status: {str(e)}")
            service_status[service_name] = {
                "status": "error",
                "available": False,
                "error_message": str(e)
            }
            overall_status = "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow(),
        "services": service_status,
        "message": "Research services status check completed"
    }

@router.get("/research/capabilities")
@handle_endpoint_errors(
    "research_capabilities",
    fallback_response=create_fallback_response(
        message="Research capabilities check temporarily unavailable",
        data={"capabilities": {}},
        status="unavailable"
    )
)
async def research_capabilities():
    """
    Get available research capabilities
    
    Returns information about available research features and capabilities
    based on the current service status.
    """
    capabilities = {
        "semantic_search": {
            "name": "Semantic Search",
            "description": "Advanced semantic search with vector similarity and knowledge graph reasoning",
            "features": [
                "Vector-based similarity search",
                "Knowledge graph integration",
                "Cross-domain insights",
                "Temporal analysis",
                "Hypothesis generation"
            ],
            "available": False,
            "status": "checking"
        },
        "research_automation": {
            "name": "Research Automation",
            "description": "Automated research workflows and literature monitoring",
            "features": [
                "Literature monitoring",
                "Citation management",
                "Data collection automation",
                "Report generation",
                "Workflow scheduling"
            ],
            "available": False,
            "status": "checking"
        },
        "advanced_analytics": {
            "name": "Advanced Analytics",
            "description": "Research analytics and insights generation",
            "features": [
                "User behavior analysis",
                "Feature performance insights",
                "Business intelligence reports",
                "Predictive analytics",
                "Trend analysis"
            ],
            "available": False,
            "status": "checking"
        },
        "knowledge_graph": {
            "name": "Knowledge Graph",
            "description": "Knowledge graph construction and querying",
            "features": [
                "Entity extraction",
                "Relationship mapping",
                "Graph querying",
                "Research connections discovery",
                "Knowledge visualization"
            ],
            "available": False,
            "status": "checking"
        }
    }
    
    # Check service availability
    for service_name in capabilities.keys():
        try:
            service = service_manager.get_service(service_name)
            if service:
                health = await service_manager.check_service_health(service_name)
                capabilities[service_name]["available"] = health.status.value == "healthy"
                capabilities[service_name]["status"] = health.status.value
                if health.error_message:
                    capabilities[service_name]["error"] = health.error_message
            else:
                capabilities[service_name]["status"] = "unavailable"
                capabilities[service_name]["error"] = "Service not initialized"
                
        except Exception as e:
            logger.error(f"Error checking {service_name} capability: {str(e)}")
            capabilities[service_name]["status"] = "error"
            capabilities[service_name]["error"] = str(e)
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow(),
        "capabilities": capabilities,
        "message": "Research capabilities retrieved successfully"
    }

@router.post("/research/search/basic")
@handle_endpoint_errors(
    "basic_research_search",
    fallback_response=create_fallback_response(
        message="Search service temporarily unavailable - using mock results",
        data=[],
        status="degraded"
    )
)
async def basic_research_search(request: Dict[str, Any]):
    """
    Basic research search endpoint with comprehensive error handling
    
    Performs a simple research search using available services.
    Falls back to mock results if services are unavailable.
    
    Request body:
    - query: Search query string
    - max_results: Maximum number of results (default: 10)
    - user_id: User ID for personalization (optional)
    """
    # Validate request data
    validate_request_data(request, ["query"])
    
    query = request.get("query", "").strip()
    max_results = request.get("max_results", 10)
    user_id = request.get("user_id")
    
    # Validate max_results
    if not isinstance(max_results, int) or max_results < 1 or max_results > 100:
        max_results = 10
    
    # Try to use semantic search service
    semantic_search_service = service_manager.get_service("semantic_search")
    
    if semantic_search_service and service_manager.is_service_healthy("semantic_search"):
        try:
            # Use real semantic search service
            if hasattr(semantic_search_service, 'advanced_search'):
                results = await semantic_search_service.advanced_search(query)
                
                return {
                    "status": "ok",
                    "timestamp": datetime.utcnow(),
                    "query": query,
                    "results": results[:max_results],
                    "total_results": len(results),
                    "service_used": "semantic_search",
                    "message": "Search completed successfully"
                }
            else:
                logger.warning("Semantic search service missing advanced_search method")
                
        except Exception as e:
            logger.error(f"Error using semantic search service: {str(e)}")
            raise ServiceUnavailableError("semantic_search", f"Search service error: {str(e)}")
    
    # Fallback to mock results
    logger.info("Using mock search results - semantic search service unavailable")
    
    mock_results = [
        {
            "id": f"mock-result-{i}",
            "title": f"Research Paper {i}: {query}",
            "content": f"This is a mock research result for query '{query}'. "
                      f"In a real implementation, this would contain actual search results.",
            "relevance_score": max(0.1, 1.0 - (i * 0.1)),
            "source": "mock_database",
            "type": "research_paper",
            "metadata": {
                "authors": [f"Author {i}"],
                "year": 2024 - (i % 5),
                "journal": f"Mock Journal {i % 3 + 1}"
            }
        }
        for i in range(min(max_results, 5))  # Limit mock results
    ]
    
    return {
        "status": "degraded",
        "timestamp": datetime.utcnow(),
        "query": query,
        "results": mock_results,
        "total_results": len(mock_results),
        "service_used": "mock",
        "message": "Search completed with mock results - semantic search service unavailable",
        "fallback": True
    }

@router.get("/research/domains")
async def research_domains():
    """
    Get available research domains
    
    Returns a list of supported research domains and their descriptions.
    """
    try:
        domains = {
            "computer_science": {
                "name": "Computer Science",
                "description": "Software engineering, algorithms, AI, machine learning, cybersecurity",
                "subdomains": [
                    "artificial_intelligence",
                    "machine_learning", 
                    "software_engineering",
                    "cybersecurity",
                    "data_science",
                    "human_computer_interaction"
                ]
            },
            "engineering": {
                "name": "Engineering",
                "description": "Mechanical, electrical, civil, chemical, and other engineering disciplines",
                "subdomains": [
                    "mechanical_engineering",
                    "electrical_engineering",
                    "civil_engineering",
                    "chemical_engineering",
                    "biomedical_engineering"
                ]
            },
            "medicine": {
                "name": "Medicine & Health Sciences",
                "description": "Medical research, clinical studies, public health, biomedical sciences",
                "subdomains": [
                    "clinical_medicine",
                    "public_health",
                    "biomedical_research",
                    "pharmacology",
                    "epidemiology"
                ]
            },
            "natural_sciences": {
                "name": "Natural Sciences",
                "description": "Physics, chemistry, biology, earth sciences, mathematics",
                "subdomains": [
                    "physics",
                    "chemistry", 
                    "biology",
                    "mathematics",
                    "earth_sciences",
                    "environmental_science"
                ]
            },
            "social_sciences": {
                "name": "Social Sciences",
                "description": "Psychology, sociology, economics, political science, anthropology",
                "subdomains": [
                    "psychology",
                    "sociology",
                    "economics",
                    "political_science",
                    "anthropology",
                    "education"
                ]
            },
            "humanities": {
                "name": "Humanities",
                "description": "Literature, history, philosophy, linguistics, cultural studies",
                "subdomains": [
                    "literature",
                    "history",
                    "philosophy",
                    "linguistics",
                    "cultural_studies",
                    "art_history"
                ]
            }
        }
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow(),
            "domains": domains,
            "total_domains": len(domains),
            "message": "Research domains retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Research domains retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Research domains retrieval failed: {str(e)}"
        )

@router.post("/research/validate")
async def validate_research_query(request: Dict[str, Any]):
    """
    Validate research query and provide suggestions
    
    Validates a research query and provides suggestions for improvement.
    
    Request body:
    - query: Research query to validate
    - domain: Research domain (optional)
    - user_id: User ID (optional)
    """
    try:
        query = request.get("query", "").strip()
        domain = request.get("domain")
        user_id = request.get("user_id")
        
        if not query:
            raise HTTPException(
                status_code=400,
                detail="Query parameter is required"
            )
        
        # Basic query validation
        validation_results = {
            "is_valid": True,
            "issues": [],
            "suggestions": [],
            "confidence": 1.0,
            "query_type": "general"
        }
        
        # Check query length
        if len(query) < 3:
            validation_results["is_valid"] = False
            validation_results["issues"].append("Query too short")
            validation_results["suggestions"].append("Please provide a more detailed query (at least 3 characters)")
            validation_results["confidence"] = 0.1
        elif len(query) > 500:
            validation_results["issues"].append("Query very long")
            validation_results["suggestions"].append("Consider breaking down your query into smaller, more focused questions")
            validation_results["confidence"] = 0.7
        
        # Check for question words to determine query type
        question_words = ["what", "how", "why", "when", "where", "who", "which"]
        if any(word in query.lower() for word in question_words):
            validation_results["query_type"] = "question"
        elif "compare" in query.lower() or "vs" in query.lower():
            validation_results["query_type"] = "comparison"
        elif "review" in query.lower() or "survey" in query.lower():
            validation_results["query_type"] = "literature_review"
        
        # Domain-specific suggestions
        if domain:
            if domain == "computer_science":
                validation_results["suggestions"].append("Consider including specific technologies, algorithms, or methodologies")
            elif domain == "medicine":
                validation_results["suggestions"].append("Consider including population, intervention, comparison, and outcome (PICO) elements")
            elif domain == "social_sciences":
                validation_results["suggestions"].append("Consider specifying the population, context, and research methodology")
        
        # General suggestions for improvement
        if validation_results["is_valid"]:
            validation_results["suggestions"].extend([
                "Consider adding specific keywords related to your research area",
                "Include time constraints if relevant (e.g., 'recent studies', 'since 2020')",
                "Specify the type of sources you're looking for (e.g., 'peer-reviewed', 'case studies')"
            ])
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow(),
            "query": query,
            "domain": domain,
            "validation": validation_results,
            "message": "Query validation completed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Research query validation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Query validation failed: {str(e)}"
        )

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/analytics/report/{user_id}")
@handle_endpoint_errors(
    "generate_analytics_report",
    required_services=["advanced_analytics"],
    fallback_response=create_fallback_response(
        message="Analytics report generation temporarily unavailable",
        data={
            "basic_metrics": {
                "total_documents": 0,
                "total_searches": 0,
                "active_days": 0
            },
            "message": "Full analytics unavailable - service not initialized"
        },
        status="unavailable"
    )
)
async def generate_analytics_report(
    user_id: str,
    timeframe: str = "month",
    include_predictions: bool = True
):
    """
    Generate comprehensive analytics report for a user
    
    Args:
        user_id: User ID to generate report for
        timeframe: Time period for analysis (hour, day, week, month, quarter, year, all_time)
        include_predictions: Whether to include predictive analytics
    
    Returns comprehensive analytics report with metrics, visualizations, and insights
    """
    # Validate user_id
    validate_request_data({"user_id": user_id}, ["user_id"])
    
    # Validate timeframe
    valid_timeframes = ["hour", "day", "week", "month", "quarter", "year", "all_time"]
    if timeframe not in valid_timeframes:
        raise ValidationError(
            message=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}",
            details={"valid_timeframes": valid_timeframes, "provided_timeframe": timeframe}
        )
    
    try:
        # Get advanced analytics service (guaranteed to be available due to decorator)
        advanced_analytics_service = service_manager.get_service("advanced_analytics")
        
        # Generate comprehensive report
        from services.advanced_analytics import AnalyticsTimeframe
        
        # Convert string timeframe to enum
        timeframe_enum = AnalyticsTimeframe(timeframe)
        
        report = await advanced_analytics_service.generate_comprehensive_report(
            user_id=user_id,
            timeframe=timeframe_enum,
            include_predictions=include_predictions
        )
        
        return {
                "status": "ok",
                "timestamp": datetime.utcnow(),
                "user_id": user_id,
                "report": {
                    "id": report.id,
                    "title": report.title,
                    "summary": report.summary,
                    "metrics": [
                        {
                            "name": metric.name,
                            "value": metric.value,
                            "type": metric.metric_type.value,
                            "description": metric.description,
                            "unit": metric.unit,
                            "trend": metric.trend,
                            "benchmark": metric.benchmark,
                            "timestamp": metric.timestamp.isoformat() if metric.timestamp else None
                        }
                        for metric in report.metrics
                    ],
                    "visualizations": [
                        {
                            "chart_type": viz.chart_type.value,
                            "title": viz.title,
                            "data": viz.data,
                            "config": viz.config,
                            "description": viz.description,
                            "insights": viz.insights
                        }
                        for viz in report.visualizations
                    ],
                    "recommendations": report.recommendations,
                    "timeframe": report.timeframe.value,
                    "generated_at": report.generated_at.isoformat(),
                    "confidence_score": report.confidence_score
                },
                "message": "Analytics report generated successfully"
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics report generation failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "message": f"Analytics report generation failed: {str(e)}",
            "user_id": user_id,
            "error_details": {
                "error": str(e),
                "service_available": service_manager.get_service("advanced_analytics") is not None
            }
        }

@router.get("/analytics/usage/{user_id}")
async def get_usage_insights(
    user_id: str,
    timeframe: str = "month"
):
    """
    Get detailed usage insights for a user
    
    Args:
        user_id: User ID to analyze
        timeframe: Time period for analysis
    
    Returns detailed usage patterns, activity trends, and feature utilization
    """
    try:
        # Check if advanced analytics service is available
        advanced_analytics_service = service_manager.get_service("advanced_analytics")
        
        if not advanced_analytics_service:
            return {
                "status": "unavailable",
                "timestamp": datetime.utcnow(),
                "message": "Advanced analytics service not initialized",
                "user_id": user_id,
                "fallback_data": {
                    "message": "Usage insights unavailable - service not initialized"
                }
            }
        
        # Validate timeframe
        valid_timeframes = ["hour", "day", "week", "month", "quarter", "year", "all_time"]
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
            )
        
        # Check service health
        health = await service_manager.check_service_health("advanced_analytics")
        
        if health.status.value != "healthy":
            return {
                "status": "degraded",
                "timestamp": datetime.utcnow(),
                "message": f"Advanced analytics service is {health.status.value}",
                "user_id": user_id,
                "error": health.error_message
            }
        
        # Generate usage insights
        from services.advanced_analytics import AnalyticsTimeframe
        
        timeframe_enum = AnalyticsTimeframe(timeframe)
        
        insights = await advanced_analytics_service.generate_usage_insights(
            user_id=user_id,
            timeframe=timeframe_enum
        )
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "timeframe": timeframe,
            "insights": insights,
            "message": "Usage insights generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Usage insights generation failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "message": f"Usage insights generation failed: {str(e)}",
            "user_id": user_id,
            "error_details": {
                "error": str(e),
                "service_available": service_manager.get_service("advanced_analytics") is not None
            }
        }

@router.get("/analytics/content/{user_id}")
async def get_content_analytics(
    user_id: str,
    timeframe: str = "month"
):
    """
    Get comprehensive content analytics for a user
    
    Args:
        user_id: User ID to analyze
        timeframe: Time period for analysis
    
    Returns content statistics, topic analysis, quality metrics, and growth trends
    """
    try:
        # Check if advanced analytics service is available
        advanced_analytics_service = service_manager.get_service("advanced_analytics")
        
        if not advanced_analytics_service:
            return {
                "status": "unavailable",
                "timestamp": datetime.utcnow(),
                "message": "Advanced analytics service not initialized",
                "user_id": user_id,
                "fallback_data": {
                    "message": "Content analytics unavailable - service not initialized"
                }
            }
        
        # Validate timeframe
        valid_timeframes = ["hour", "day", "week", "month", "quarter", "year", "all_time"]
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
            )
        
        # Check service health
        health = await service_manager.check_service_health("advanced_analytics")
        
        if health.status.value != "healthy":
            return {
                "status": "degraded",
                "timestamp": datetime.utcnow(),
                "message": f"Advanced analytics service is {health.status.value}",
                "user_id": user_id,
                "error": health.error_message
            }
        
        # Generate content analytics
        from services.advanced_analytics import AnalyticsTimeframe
        
        timeframe_enum = AnalyticsTimeframe(timeframe)
        
        analytics = await advanced_analytics_service.generate_content_analytics(
            user_id=user_id,
            timeframe=timeframe_enum
        )
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "timeframe": timeframe,
            "analytics": analytics,
            "message": "Content analytics generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content analytics generation failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "message": f"Content analytics generation failed: {str(e)}",
            "user_id": user_id,
            "error_details": {
                "error": str(e),
                "service_available": service_manager.get_service("advanced_analytics") is not None
            }
        }

@router.get("/analytics/relationships/{user_id}")
async def analyze_document_relationships(
    user_id: str,
    min_similarity: float = 0.3,
    max_relationships: int = 100
):
    """
    Analyze relationships between user's documents
    
    Args:
        user_id: User ID to analyze
        min_similarity: Minimum similarity threshold (0.0 to 1.0)
        max_relationships: Maximum number of relationships to return
    
    Returns document relationships with similarity scores and shared concepts
    """
    try:
        # Check if advanced analytics service is available
        advanced_analytics_service = service_manager.get_service("advanced_analytics")
        
        if not advanced_analytics_service:
            return {
                "status": "unavailable",
                "timestamp": datetime.utcnow(),
                "message": "Advanced analytics service not initialized",
                "user_id": user_id,
                "fallback_data": {
                    "message": "Document relationship analysis unavailable - service not initialized"
                }
            }
        
        # Validate parameters
        if not 0.0 <= min_similarity <= 1.0:
            raise HTTPException(
                status_code=400,
                detail="min_similarity must be between 0.0 and 1.0"
            )
        
        if not 1 <= max_relationships <= 1000:
            raise HTTPException(
                status_code=400,
                detail="max_relationships must be between 1 and 1000"
            )
        
        # Check service health
        health = await service_manager.check_service_health("advanced_analytics")
        
        if health.status.value != "healthy":
            return {
                "status": "degraded",
                "timestamp": datetime.utcnow(),
                "message": f"Advanced analytics service is {health.status.value}",
                "user_id": user_id,
                "error": health.error_message
            }
        
        # Analyze document relationships
        relationships = await advanced_analytics_service.analyze_document_relationships(
            user_id=user_id,
            min_similarity=min_similarity,
            max_relationships=max_relationships
        )
        
        # Convert relationships to serializable format
        relationship_data = [
            {
                "source_doc_id": rel.source_doc_id,
                "target_doc_id": rel.target_doc_id,
                "relationship_type": rel.relationship_type,
                "strength": rel.strength,
                "shared_concepts": rel.shared_concepts,
                "similarity_score": rel.similarity_score
            }
            for rel in relationships
        ]
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "parameters": {
                "min_similarity": min_similarity,
                "max_relationships": max_relationships
            },
            "relationships": relationship_data,
            "total_relationships": len(relationship_data),
            "message": "Document relationship analysis completed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document relationship analysis failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "message": f"Document relationship analysis failed: {str(e)}",
            "user_id": user_id,
            "error_details": {
                "error": str(e),
                "service_available": service_manager.get_service("advanced_analytics") is not None
            }
        }

@router.get("/analytics/knowledge-patterns/{user_id}")
async def discover_knowledge_patterns(
    user_id: str,
    min_frequency: int = 3,
    confidence_threshold: float = 0.7
):
    """
    Discover patterns in user's knowledge graph
    
    Args:
        user_id: User ID to analyze
        min_frequency: Minimum frequency for pattern detection
        confidence_threshold: Minimum confidence score for patterns
    
    Returns discovered knowledge patterns with entities, relationships, and confidence scores
    """
    try:
        # Check if advanced analytics service is available
        advanced_analytics_service = service_manager.get_service("advanced_analytics")
        
        if not advanced_analytics_service:
            return {
                "status": "unavailable",
                "timestamp": datetime.utcnow(),
                "message": "Advanced analytics service not initialized",
                "user_id": user_id,
                "fallback_data": {
                    "message": "Knowledge pattern discovery unavailable - service not initialized"
                }
            }
        
        # Validate parameters
        if min_frequency < 1:
            raise HTTPException(
                status_code=400,
                detail="min_frequency must be at least 1"
            )
        
        if not 0.0 <= confidence_threshold <= 1.0:
            raise HTTPException(
                status_code=400,
                detail="confidence_threshold must be between 0.0 and 1.0"
            )
        
        # Check service health
        health = await service_manager.check_service_health("advanced_analytics")
        
        if health.status.value != "healthy":
            return {
                "status": "degraded",
                "timestamp": datetime.utcnow(),
                "message": f"Advanced analytics service is {health.status.value}",
                "user_id": user_id,
                "error": health.error_message
            }
        
        # Discover knowledge patterns
        patterns = await advanced_analytics_service.discover_knowledge_patterns(
            user_id=user_id,
            min_frequency=min_frequency,
            confidence_threshold=confidence_threshold
        )
        
        # Convert patterns to serializable format
        pattern_data = [
            {
                "pattern_id": pattern.pattern_id,
                "pattern_type": pattern.pattern_type,
                "entities": pattern.entities,
                "relationships": pattern.relationships,
                "frequency": pattern.frequency,
                "confidence": pattern.confidence,
                "examples": pattern.examples
            }
            for pattern in patterns
        ]
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "parameters": {
                "min_frequency": min_frequency,
                "confidence_threshold": confidence_threshold
            },
            "patterns": pattern_data,
            "total_patterns": len(pattern_data),
            "message": "Knowledge pattern discovery completed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Knowledge pattern discovery failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "message": f"Knowledge pattern discovery failed: {str(e)}",
            "user_id": user_id,
            "error_details": {
                "error": str(e),
                "service_available": service_manager.get_service("advanced_analytics") is not None
            }
        }

@router.get("/analytics/knowledge-map/{user_id}")
async def create_knowledge_map_visualization(
    user_id: str,
    layout_algorithm: str = "spring",
    max_nodes: int = 100
):
    """
    Create interactive knowledge map visualization
    
    Args:
        user_id: User ID to create map for
        layout_algorithm: Graph layout algorithm (spring, circular, kamada_kawai)
        max_nodes: Maximum number of nodes to include
    
    Returns interactive knowledge map visualization data
    """
    try:
        # Check if advanced analytics service is available
        advanced_analytics_service = service_manager.get_service("advanced_analytics")
        
        if not advanced_analytics_service:
            return {
                "status": "unavailable",
                "timestamp": datetime.utcnow(),
                "message": "Advanced analytics service not initialized",
                "user_id": user_id,
                "fallback_data": {
                    "message": "Knowledge map visualization unavailable - service not initialized"
                }
            }
        
        # Validate parameters
        valid_layouts = ["spring", "circular", "kamada_kawai"]
        if layout_algorithm not in valid_layouts:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid layout_algorithm. Must be one of: {', '.join(valid_layouts)}"
            )
        
        if not 10 <= max_nodes <= 500:
            raise HTTPException(
                status_code=400,
                detail="max_nodes must be between 10 and 500"
            )
        
        # Check service health
        health = await service_manager.check_service_health("advanced_analytics")
        
        if health.status.value != "healthy":
            return {
                "status": "degraded",
                "timestamp": datetime.utcnow(),
                "message": f"Advanced analytics service is {health.status.value}",
                "user_id": user_id,
                "error": health.error_message
            }
        
        # Create knowledge map visualization
        visualization = await advanced_analytics_service.create_knowledge_map_visualization(
            user_id=user_id,
            layout_algorithm=layout_algorithm,
            max_nodes=max_nodes
        )
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "parameters": {
                "layout_algorithm": layout_algorithm,
                "max_nodes": max_nodes
            },
            "visualization": {
                "chart_type": visualization.chart_type.value,
                "title": visualization.title,
                "data": visualization.data,
                "config": visualization.config,
                "description": visualization.description,
                "insights": visualization.insights
            },
            "message": "Knowledge map visualization created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Knowledge map visualization failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "message": f"Knowledge map visualization failed: {str(e)}",
            "user_id": user_id,
            "error_details": {
                "error": str(e),
                "service_available": service_manager.get_service("advanced_analytics") is not None
            }
        }

@router.get("/analytics/metrics/{user_id}")
async def get_analytics_metrics(
    user_id: str,
    metric_types: str = "all",
    timeframe: str = "month"
):
    """
    Get specific analytics metrics for a user
    
    Args:
        user_id: User ID to get metrics for
        metric_types: Comma-separated list of metric types (usage,performance,content,user_behavior,knowledge,all)
        timeframe: Time period for analysis
    
    Returns specific analytics metrics based on requested types
    """
    try:
        # Check if advanced analytics service is available
        advanced_analytics_service = service_manager.get_service("advanced_analytics")
        
        if not advanced_analytics_service:
            return {
                "status": "unavailable",
                "timestamp": datetime.utcnow(),
                "message": "Advanced analytics service not initialized",
                "user_id": user_id,
                "fallback_data": {
                    "message": "Analytics metrics unavailable - service not initialized"
                }
            }
        
        # Validate timeframe
        valid_timeframes = ["hour", "day", "week", "month", "quarter", "year", "all_time"]
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
            )
        
        # Parse metric types
        valid_metric_types = ["usage", "performance", "content", "user_behavior", "knowledge", "all"]
        requested_types = [t.strip() for t in metric_types.split(",")]
        
        if "all" in requested_types:
            requested_types = ["usage", "performance", "content", "user_behavior", "knowledge"]
        
        invalid_types = [t for t in requested_types if t not in valid_metric_types]
        if invalid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid metric types: {', '.join(invalid_types)}. Valid types: {', '.join(valid_metric_types)}"
            )
        
        # Check service health
        health = await service_manager.check_service_health("advanced_analytics")
        
        if health.status.value != "healthy":
            return {
                "status": "degraded",
                "timestamp": datetime.utcnow(),
                "message": f"Advanced analytics service is {health.status.value}",
                "user_id": user_id,
                "error": health.error_message
            }
        
        # Get metrics from service
        from services.advanced_analytics import AnalyticsTimeframe
        
        timeframe_enum = AnalyticsTimeframe(timeframe)
        all_metrics = []
        
        # Get requested metric types
        if "usage" in requested_types:
            usage_metrics = await advanced_analytics_service._get_usage_metrics(user_id, timeframe_enum)
            all_metrics.extend(usage_metrics)
        
        if "performance" in requested_types:
            performance_metrics = await advanced_analytics_service._get_performance_metrics(user_id, timeframe_enum)
            all_metrics.extend(performance_metrics)
        
        if "content" in requested_types:
            content_metrics = await advanced_analytics_service._get_content_metrics(user_id, timeframe_enum)
            all_metrics.extend(content_metrics)
        
        if "user_behavior" in requested_types:
            behavior_metrics = await advanced_analytics_service._get_user_behavior_metrics(user_id, timeframe_enum)
            all_metrics.extend(behavior_metrics)
        
        if "knowledge" in requested_types:
            knowledge_metrics = await advanced_analytics_service._get_knowledge_metrics(user_id, timeframe_enum)
            all_metrics.extend(knowledge_metrics)
        
        # Convert metrics to serializable format
        metrics_data = [
            {
                "name": metric.name,
                "value": metric.value,
                "type": metric.metric_type.value,
                "description": metric.description,
                "unit": metric.unit,
                "trend": metric.trend,
                "benchmark": metric.benchmark,
                "timestamp": metric.timestamp.isoformat() if metric.timestamp else None
            }
            for metric in all_metrics
        ]
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "parameters": {
                "metric_types": requested_types,
                "timeframe": timeframe
            },
            "metrics": metrics_data,
            "total_metrics": len(metrics_data),
            "message": "Analytics metrics retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics metrics retrieval failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "message": f"Analytics metrics retrieval failed: {str(e)}",
            "user_id": user_id,
            "error_details": {
                "error": str(e),
                "service_available": service_manager.get_service("advanced_analytics") is not None
            }
        }

# ============================================================================
# SEMANTIC SEARCH ENDPOINTS
# ============================================================================

@router.post("/semantic-search/search")
@handle_endpoint_errors(
    "semantic_search",
    required_services=["semantic_search"],
    fallback_response=create_fallback_response(
        message="Semantic search temporarily unavailable - using basic search",
        data={"results": [], "search_mode": "fallback"},
        status="degraded"
    )
)
async def semantic_search(request: Dict[str, Any]):
    """
    Perform semantic search with conditional service access
    
    Performs advanced semantic search using the semantic search service.
    Falls back to basic search if the service is unavailable.
    
    Request body:
    - query: Search query string (required)
    - user_id: User ID for personalized search (required)
    - mode: Search mode (semantic, hybrid, knowledge_graph, temporal, cross_domain, predictive)
    - reasoning_types: List of reasoning types to apply (causal, analogical, temporal, hierarchical, associative)
    - max_results: Maximum number of results (default: 20)
    - confidence_threshold: Minimum confidence threshold (default: 0.5)
    - include_explanations: Include explanations for results (default: true)
    - temporal_constraints: Temporal constraints for search (optional)
    - domain_filters: Domain filters for search (optional)
    """
    # Validate required parameters
    validate_request_data(request, ["query", "user_id"])
    
    query = request.get("query", "").strip()
    user_id = request.get("user_id", "").strip()
    
    # Extract optional parameters with defaults
    mode = request.get("mode", "semantic")
    reasoning_types = request.get("reasoning_types", ["associative"])
        max_results = request.get("max_results", 20)
        confidence_threshold = request.get("confidence_threshold", 0.5)
        include_explanations = request.get("include_explanations", True)
        temporal_constraints = request.get("temporal_constraints")
        domain_filters = request.get("domain_filters")
    
    # Validate parameters
        if not isinstance(max_results, int) or max_results < 1 or max_results > 100:
            max_results = 20
        
        if not isinstance(confidence_threshold, (int, float)) or confidence_threshold < 0 or confidence_threshold > 1:
            confidence_threshold = 0.5
        
        # Try to use semantic search service
        semantic_search_service = service_manager.get_service("semantic_search")
        
        if semantic_search_service:
            try:
                # Check if service is healthy
                health = await service_manager.check_service_health("semantic_search")
                
                if health.status.value == "healthy":
                    # Import SearchQuery and SearchMode from the service
                    from services.semantic_search_v2 import SearchQuery, SearchMode, ReasoningType
                    
                    # Convert string mode to enum
                    try:
                        search_mode = SearchMode(mode)
                    except ValueError:
                        search_mode = SearchMode.SEMANTIC
                    
                    # Convert reasoning types to enums
                    reasoning_enums = []
                    for rt in reasoning_types:
                        try:
                            reasoning_enums.append(ReasoningType(rt))
                        except ValueError:
                            logger.warning(f"Invalid reasoning type: {rt}")
                    
                    if not reasoning_enums:
                        reasoning_enums = [ReasoningType.ASSOCIATIVE]
                    
                    # Create search query
                    search_query = SearchQuery(
                        query_text=query,
                        user_id=user_id,
                        mode=search_mode,
                        reasoning_types=reasoning_enums,
                        temporal_constraints=temporal_constraints,
                        domain_filters=domain_filters,
                        confidence_threshold=confidence_threshold,
                        max_results=max_results,
                        include_explanations=include_explanations
                    )
                    
                    # Perform advanced search
                    results = await semantic_search_service.advanced_search(search_query)
                    
                    # Convert results to serializable format
                    serialized_results = []
                    for result in results:
                        serialized_results.append({
                            "id": result.id,
                            "document_id": result.document_id,
                            "chunk_id": result.chunk_id,
                            "content": result.content,
                            "title": result.title,
                            "relevance_score": result.relevance_score,
                            "confidence_score": result.confidence_score,
                            "reasoning_path": result.reasoning_path,
                            "knowledge_connections": result.knowledge_connections,
                            "temporal_context": result.temporal_context,
                            "cross_domain_insights": result.cross_domain_insights,
                            "explanation": result.explanation,
                            "metadata": result.metadata
                        })
                    
                    return {
                        "status": "ok",
                        "timestamp": datetime.utcnow(),
                        "query": query,
                        "user_id": user_id,
                        "search_parameters": {
                            "mode": mode,
                            "reasoning_types": reasoning_types,
                            "max_results": max_results,
                            "confidence_threshold": confidence_threshold,
                            "include_explanations": include_explanations
                        },
                        "results": serialized_results,
                        "total_results": len(serialized_results),
                        "service_used": "semantic_search_v2",
                        "message": "Semantic search completed successfully"
                    }
                    
                else:
                    logger.warning(f"Semantic search service unhealthy: {health.status.value}")
                    
            except Exception as e:
                logger.error(f"Error using semantic search service: {str(e)}", exc_info=True)
        
        # Fallback to basic search if service unavailable
        logger.info("Using fallback search - semantic search service unavailable")
        
        # Create mock search results
        mock_results = [
            {
                "id": f"fallback-result-{i}",
                "document_id": f"doc-{i}",
                "chunk_id": f"chunk-{i}",
                "content": f"This is a fallback search result for query '{query}'. "
                          f"The semantic search service is currently unavailable.",
                "title": f"Fallback Result {i}: {query}",
                "relevance_score": max(0.1, 1.0 - (i * 0.1)),
                "confidence_score": 0.5,
                "reasoning_path": ["fallback"],
                "knowledge_connections": [],
                "temporal_context": None,
                "cross_domain_insights": [],
                "explanation": "This is a fallback result generated when semantic search is unavailable.",
                "metadata": {
                    "source": "fallback",
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            for i in range(min(max_results, 3))
        ]
        
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow(),
            "query": query,
            "user_id": user_id,
            "search_parameters": {
                "mode": mode,
                "reasoning_types": reasoning_types,
                "max_results": max_results,
                "confidence_threshold": confidence_threshold,
                "include_explanations": include_explanations
            },
            "results": mock_results,
            "total_results": len(mock_results),
            "service_used": "fallback",
            "message": "Search completed with fallback results - semantic search service unavailable",
            "fallback": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Semantic search failed: {str(e)}", exc_info=True)
        raise ServiceUnavailableError("semantic_search", f"Search failed: {str(e)}")able")
        
        # Basic fallback search implementation
        fallback_results = []
        
        # Try to get some basic results from database if available
        try:
            database_service = service_manager.get_service("database")
            if database_service:
                # Import database models
                from models.schemas import Document, DocumentChunk
                
                # Get user's documents
                db_session = database_service.get_session()
                documents = db_session.query(Document).filter(
                    Document.user_id == user_id,
                    Document.status == "completed"
                ).limit(10).all()
                
                query_words = set(query.lower().split())
                
                for doc in documents:
                    # Simple text matching
                    doc_words = set(doc.name.lower().split())
                    overlap = len(query_words.intersection(doc_words))
                    relevance = overlap / len(query_words) if query_words else 0
                    
                    if relevance >= confidence_threshold:
                        fallback_results.append({
                            "id": f"fallback-{doc.id}",
                            "document_id": doc.id,
                            "chunk_id": None,
                            "content": f"Document: {doc.name}",
                            "title": doc.name,
                            "relevance_score": relevance,
                            "confidence_score": relevance,
                            "reasoning_path": ["fallback_search"],
                            "knowledge_connections": [],
                            "temporal_context": None,
                            "cross_domain_insights": [],
                            "explanation": "Fallback search result - semantic search service unavailable",
                            "metadata": {
                                "document_created": doc.created_at.isoformat() if doc.created_at else None,
                                "content_type": doc.content_type,
                                "fallback": True
                            }
                        })
                
                # Sort by relevance
                fallback_results.sort(key=lambda x: x["relevance_score"], reverse=True)
                fallback_results = fallback_results[:max_results]
                
        except Exception as e:
            logger.error(f"Error in fallback search: {str(e)}")
        
        # If no fallback results, create mock results
        if not fallback_results:
            fallback_results = [{
                "id": "mock-result-1",
                "document_id": "mock-doc-1",
                "chunk_id": None,
                "content": f"Mock search result for query: {query}",
                "title": f"Mock Result for '{query}'",
                "relevance_score": 0.5,
                "confidence_score": 0.5,
                "reasoning_path": ["mock_search"],
                "knowledge_connections": [],
                "temporal_context": None,
                "cross_domain_insights": [],
                "explanation": "Mock search result - semantic search service unavailable",
                "metadata": {
                    "mock": True,
                    "service_status": "unavailable"
                }
            }]
        
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow(),
            "query": query,
            "user_id": user_id,
            "search_parameters": {
                "mode": mode,
                "reasoning_types": reasoning_types,
                "max_results": max_results,
                "confidence_threshold": confidence_threshold,
                "include_explanations": include_explanations
            },
            "results": fallback_results,
            "total_results": len(fallback_results),
            "service_used": "fallback_search",
            "message": "Search completed with fallback - semantic search service unavailable",
            "warning": "Semantic search service unavailable, using fallback search"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Semantic search failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Semantic search failed: {str(e)}"
        )

@router.post("/semantic-search/hypotheses")
async def generate_research_hypotheses(request: Dict[str, Any]):
    """
    Generate research hypotheses using semantic search service
    
    Uses the semantic search service to generate research hypotheses
    based on knowledge gaps and existing research.
    
    Request body:
    - user_id: User ID for personalized hypothesis generation (required)
    - research_area: Research area for hypothesis generation (required)
    - existing_knowledge: List of existing knowledge points (optional)
    """
    try:
        # Validate required parameters
        user_id = request.get("user_id", "").strip()
        research_area = request.get("research_area", "").strip()
        existing_knowledge = request.get("existing_knowledge", [])
        
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail="User ID parameter is required"
            )
        
        if not research_area:
            raise HTTPException(
                status_code=400,
                detail="Research area parameter is required"
            )
        
        # Try to use semantic search service
        semantic_search_service = service_manager.get_service("semantic_search")
        
        if semantic_search_service:
            try:
                # Check if service is healthy
                health = await service_manager.check_service_health("semantic_search")
                
                if health.status.value == "healthy":
                    # Generate hypotheses using the service
                    hypotheses = await semantic_search_service.generate_hypotheses(
                        user_id=user_id,
                        research_area=research_area,
                        existing_knowledge=existing_knowledge
                    )
                    
                    # Convert hypotheses to serializable format
                    serialized_hypotheses = []
                    for hypothesis in hypotheses:
                        serialized_hypotheses.append({
                            "id": hypothesis.id,
                            "hypothesis": hypothesis.hypothesis,
                            "confidence": hypothesis.confidence,
                            "supporting_evidence": hypothesis.supporting_evidence,
                            "contradicting_evidence": hypothesis.contradicting_evidence,
                            "research_gaps": hypothesis.research_gaps,
                            "methodology_suggestions": hypothesis.methodology_suggestions,
                            "predicted_outcomes": hypothesis.predicted_outcomes
                        })
                    
                    return {
                        "status": "ok",
                        "timestamp": datetime.utcnow(),
                        "user_id": user_id,
                        "research_area": research_area,
                        "hypotheses": serialized_hypotheses,
                        "total_hypotheses": len(serialized_hypotheses),
                        "service_used": "semantic_search_v2",
                        "message": "Research hypotheses generated successfully"
                    }
                    
                else:
                    logger.warning(f"Semantic search service unhealthy: {health.status.value}")
                    
            except Exception as e:
                logger.error(f"Error generating hypotheses: {str(e)}", exc_info=True)
        
        # Fallback to mock hypotheses
        logger.info("Using mock hypotheses - semantic search service unavailable")
        
        mock_hypotheses = [
            {
                "id": "mock-hypothesis-1",
                "hypothesis": f"There are significant unexplored relationships in {research_area} that could lead to new insights",
                "confidence": 0.7,
                "supporting_evidence": [
                    f"Existing research in {research_area} shows preliminary patterns",
                    "Theoretical frameworks suggest potential relationships"
                ],
                "contradicting_evidence": [
                    "Limited empirical evidence available"
                ],
                "research_gaps": [
                    f"Limited longitudinal studies in {research_area}",
                    f"Lack of cross-cultural research in {research_area}"
                ],
                "methodology_suggestions": [
                    "Mixed-methods approach",
                    "Longitudinal cohort study"
                ],
                "predicted_outcomes": [
                    "New theoretical framework development",
                    "Practical applications identification"
                ]
            }
        ]
        
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "research_area": research_area,
            "hypotheses": mock_hypotheses,
            "total_hypotheses": len(mock_hypotheses),
            "service_used": "mock_service",
            "message": "Mock hypotheses generated - semantic search service unavailable",
            "warning": "Semantic search service unavailable, using mock hypotheses"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hypothesis generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Hypothesis generation failed: {str(e)}"
        )

@router.post("/semantic-search/cross-domain-insights")
async def discover_cross_domain_insights(request: Dict[str, Any]):
    """
    Discover cross-domain insights using semantic search service
    
    Uses the semantic search service to discover insights by connecting
    different research domains through analogical reasoning.
    
    Request body:
    - user_id: User ID for personalized insight discovery (required)
    - source_domain: Source research domain (required)
    - target_domains: List of target domains to explore (optional)
    """
    try:
        # Validate required parameters
        user_id = request.get("user_id", "").strip()
        source_domain = request.get("source_domain", "").strip()
        target_domains = request.get("target_domains", [])
        
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail="User ID parameter is required"
            )
        
        if not source_domain:
            raise HTTPException(
                status_code=400,
                detail="Source domain parameter is required"
            )
        
        # Try to use semantic search service
        semantic_search_service = service_manager.get_service("semantic_search")
        
        if semantic_search_service:
            try:
                # Check if service is healthy
                health = await service_manager.check_service_health("semantic_search")
                
                if health.status.value == "healthy":
                    # Discover cross-domain insights using the service
                    insights = await semantic_search_service.discover_cross_domain_insights(
                        user_id=user_id,
                        source_domain=source_domain,
                        target_domains=target_domains if target_domains else None
                    )
                    
                    # Convert insights to serializable format
                    serialized_insights = []
                    for insight in insights:
                        serialized_insights.append({
                            "id": insight.id,
                            "source_domain": insight.source_domain,
                            "target_domain": insight.target_domain,
                            "insight": insight.insight,
                            "confidence": insight.confidence,
                            "analogical_reasoning": insight.analogical_reasoning,
                            "potential_applications": insight.potential_applications,
                            "supporting_documents": insight.supporting_documents
                        })
                    
                    return {
                        "status": "ok",
                        "timestamp": datetime.utcnow(),
                        "user_id": user_id,
                        "source_domain": source_domain,
                        "target_domains": target_domains,
                        "insights": serialized_insights,
                        "total_insights": len(serialized_insights),
                        "service_used": "semantic_search_v2",
                        "message": "Cross-domain insights discovered successfully"
                    }
                    
                else:
                    logger.warning(f"Semantic search service unhealthy: {health.status.value}")
                    
            except Exception as e:
                logger.error(f"Error discovering cross-domain insights: {str(e)}", exc_info=True)
        
        # Fallback to mock insights
        logger.info("Using mock insights - semantic search service unavailable")
        
        mock_insights = [
            {
                "id": "mock-insight-1",
                "source_domain": source_domain,
                "target_domain": target_domains[0] if target_domains else "general",
                "insight": f"Patterns from {source_domain} could be applied to solve problems in other domains",
                "confidence": 0.6,
                "analogical_reasoning": f"Similar structural patterns exist between {source_domain} and other fields",
                "potential_applications": [
                    "Cross-disciplinary research opportunities",
                    "Novel problem-solving approaches"
                ],
                "supporting_documents": []
            }
        ]
        
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "source_domain": source_domain,
            "target_domains": target_domains,
            "insights": mock_insights,
            "total_insights": len(mock_insights),
            "service_used": "mock_service",
            "message": "Mock cross-domain insights generated - semantic search service unavailable",
            "warning": "Semantic search service unavailable, using mock insights"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cross-domain insight discovery failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Cross-domain insight discovery failed: {str(e)}"
        )

@router.post("/semantic-search/predict-trends")
async def predict_research_trends(request: Dict[str, Any]):
    """
    Predict research trends using semantic search service
    
    Uses the semantic search service to predict future research trends
    and directions based on historical patterns and emerging topics.
    
    Request body:
    - user_id: User ID for personalized trend prediction (required)
    - domain: Research domain for trend prediction (required)
    - time_horizon_months: Time horizon for predictions in months (default: 12)
    """
    try:
        # Validate required parameters
        user_id = request.get("user_id", "").strip()
        domain = request.get("domain", "").strip()
        time_horizon_months = request.get("time_horizon_months", 12)
        
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail="User ID parameter is required"
            )
        
        if not domain:
            raise HTTPException(
                status_code=400,
                detail="Domain parameter is required"
            )
        
        # Validate time horizon
        if not isinstance(time_horizon_months, int) or time_horizon_months < 1 or time_horizon_months > 60:
            time_horizon_months = 12
        
        # Try to use semantic search service
        semantic_search_service = service_manager.get_service("semantic_search")
        
        if semantic_search_service:
            try:
                # Check if service is healthy
                health = await service_manager.check_service_health("semantic_search")
                
                if health.status.value == "healthy":
                    # Predict research trends using the service
                    trends = await semantic_search_service.predict_research_trends(
                        user_id=user_id,
                        domain=domain,
                        time_horizon_months=time_horizon_months
                    )
                    
                    return {
                        "status": "ok",
                        "timestamp": datetime.utcnow(),
                        "user_id": user_id,
                        "predictions": trends,
                        "service_used": "semantic_search_v2",
                        "message": "Research trends predicted successfully"
                    }
                    
                else:
                    logger.warning(f"Semantic search service unhealthy: {health.status.value}")
                    
            except Exception as e:
                logger.error(f"Error predicting research trends: {str(e)}", exc_info=True)
        
        # Fallback to mock trends
        logger.info("Using mock trends - semantic search service unavailable")
        
        mock_trends = {
            "domain": domain,
            "time_horizon_months": time_horizon_months,
            "predicted_trends": [
                f"Increased focus on interdisciplinary approaches in {domain}",
                f"Growing emphasis on data-driven methodologies in {domain}",
                f"Rising interest in ethical considerations within {domain}"
            ],
            "emerging_topics": [
                f"AI applications in {domain}",
                f"Sustainability aspects of {domain}",
                f"Global perspectives on {domain}"
            ],
            "research_opportunities": [
                f"Cross-cultural studies in {domain}",
                f"Longitudinal research in {domain}",
                f"Mixed-methods approaches in {domain}"
            ],
            "methodology_trends": [
                "Increased use of machine learning",
                "Greater emphasis on reproducibility",
                "More collaborative research approaches"
            ],
            "confidence_scores": {
                "overall_confidence": 0.6,
                "trend_confidence": 0.5,
                "methodology_confidence": 0.7
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "predictions": mock_trends,
            "service_used": "mock_service",
            "message": "Mock research trends generated - semantic search service unavailable",
            "warning": "Semantic search service unavailable, using mock trends"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Research trend prediction failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Research trend prediction failed: {str(e)}"
        )

@router.get("/semantic-search/modes")
async def get_search_modes():
    """
    Get available semantic search modes
    
    Returns information about available search modes and reasoning types
    that can be used with the semantic search service.
    """
    try:
        search_modes = [
            {
                "mode": "semantic",
                "name": "Semantic Search",
                "description": "Basic semantic search using vector similarity",
                "features": ["Vector similarity", "Content matching", "Relevance scoring"]
            },
            {
                "mode": "hybrid",
                "name": "Hybrid Search",
                "description": "Combines semantic and keyword search",
                "features": ["Vector similarity", "Keyword matching", "Hybrid scoring"]
            },
            {
                "mode": "knowledge_graph",
                "name": "Knowledge Graph Search",
                "description": "Search enhanced with knowledge graph reasoning",
                "features": ["Entity relationships", "Graph traversal", "Contextual connections"]
            },
            {
                "mode": "temporal",
                "name": "Temporal Search",
                "description": "Search with temporal reasoning and time-based analysis",
                "features": ["Time-based filtering", "Temporal patterns", "Historical context"]
            },
            {
                "mode": "cross_domain",
                "name": "Cross-Domain Search",
                "description": "Search across different research domains",
                "features": ["Domain bridging", "Analogical reasoning", "Cross-field insights"]
            },
            {
                "mode": "predictive",
                "name": "Predictive Search",
                "description": "Search with predictive analysis and trend identification",
                "features": ["Trend analysis", "Future predictions", "Pattern recognition"]
            }
        ]
        
        reasoning_types = [
            {
                "type": "causal",
                "name": "Causal Reasoning",
                "description": "Identifies cause-and-effect relationships",
                "weight": 0.3
            },
            {
                "type": "analogical",
                "name": "Analogical Reasoning",
                "description": "Finds analogies and similar patterns",
                "weight": 0.25
            },
            {
                "type": "temporal",
                "name": "Temporal Reasoning",
                "description": "Analyzes temporal patterns and sequences",
                "weight": 0.2
            },
            {
                "type": "hierarchical",
                "name": "Hierarchical Reasoning",
                "description": "Understands hierarchical structures and relationships",
                "weight": 0.15
            },
            {
                "type": "associative",
                "name": "Associative Reasoning",
                "description": "Finds associative connections between concepts",
                "weight": 0.1
            }
        ]
        
        # Check service availability
        semantic_search_service = service_manager.get_service("semantic_search")
        service_available = False
        service_status = "unavailable"
        
        if semantic_search_service:
            try:
                health = await service_manager.check_service_health("semantic_search")
                service_available = health.status.value == "healthy"
                service_status = health.status.value
            except Exception as e:
                logger.error(f"Error checking semantic search service health: {str(e)}")
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow(),
            "search_modes": search_modes,
            "reasoning_types": reasoning_types,
            "service_status": {
                "available": service_available,
                "status": service_status,
                "message": "Semantic search service is available" if service_available else "Semantic search service unavailable - fallback modes available"
            },
            "message": "Search modes and reasoning types retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting search modes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting search modes: {str(e)}"
        )