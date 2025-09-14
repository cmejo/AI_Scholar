"""
Service Manager for handling service initialization and health monitoring
"""
import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class MockSemanticSearchService:
    """
    Mock semantic search service for when the full service cannot be initialized
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MockSemanticSearchService")
        self.logger.info("Mock semantic search service initialized")
    
    async def health_check(self):
        """Health check for mock service"""
        return {"status": "mock", "message": "Mock semantic search service is running"}
    
    def get_status(self):
        """Get service status"""
        return {
            "type": "mock",
            "status": "healthy",
            "message": "Mock service - full functionality not available"
        }
    
    async def advanced_search(self, query):
        """Mock search method"""
        self.logger.warning("Mock semantic search called - returning empty results")
        return []
    
    async def generate_hypotheses(self, user_id, research_area, existing_knowledge=None):
        """Mock hypothesis generation"""
        self.logger.warning("Mock hypothesis generation called - returning empty results")
        return []
    
    async def discover_cross_domain_insights(self, user_id, source_domain, target_domains=None):
        """Mock cross-domain insights"""
        self.logger.warning("Mock cross-domain insights called - returning empty results")
        return []
    
    async def predict_research_trends(self, user_id, domain, time_horizon_months=12):
        """Mock research trends prediction"""
        self.logger.warning("Mock research trends prediction called - returning empty results")
        return {
            "domain": domain,
            "time_horizon_months": time_horizon_months,
            "predicted_trends": [],
            "emerging_topics": [],
            "research_opportunities": [],
            "methodology_trends": [],
            "confidence_scores": {},
            "generated_at": datetime.utcnow().isoformat()
        }


class MockResearchAutomationService:
    """
    Mock research automation service for when the full service cannot be initialized
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MockResearchAutomationService")
        self.logger.info("Mock research automation service initialized")
        self.active_workflows = {}
        self.scheduler_running = False
    
    async def health_check(self):
        """Health check for mock service"""
        return {"status": "mock", "message": "Mock research automation service is running"}
    
    def get_status(self):
        """Get service status"""
        return {
            "type": "mock",
            "status": "healthy",
            "message": "Mock service - full functionality not available",
            "active_workflows": len(self.active_workflows),
            "scheduler_running": self.scheduler_running
        }
    
    async def create_automated_workflow(self, user_id, name, workflow_type, description, configuration, schedule_config):
        """Mock workflow creation"""
        self.logger.warning("Mock research automation workflow creation called")
        return {
            "id": "mock-workflow-id",
            "user_id": user_id,
            "name": name,
            "workflow_type": workflow_type,
            "status": "mock",
            "message": "Mock workflow - not actually created"
        }
    
    async def execute_workflow(self, workflow_id, manual_trigger=False):
        """Mock workflow execution"""
        self.logger.warning("Mock research automation workflow execution called")
        return {
            "status": "mock",
            "message": "Mock workflow execution - no actual processing performed"
        }
    
    async def get_workflow_status(self, workflow_id):
        """Mock workflow status"""
        return {
            "status": "mock",
            "message": "Mock workflow status"
        }
    
    async def list_workflows(self, user_id):
        """Mock workflow listing"""
        return []
    
    async def pause_workflow(self, workflow_id):
        """Mock workflow pause"""
        return {"status": "mock", "message": "Mock workflow pause"}
    
    async def resume_workflow(self, workflow_id):
        """Mock workflow resume"""
        return {"status": "mock", "message": "Mock workflow resume"}
    
    async def delete_workflow(self, workflow_id):
        """Mock workflow deletion"""
        return {"status": "mock", "message": "Mock workflow deletion"}


class MockAdvancedAnalyticsService:
    """
    Mock advanced analytics service for when the full service cannot be initialized
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MockAdvancedAnalyticsService")
        self.logger.info("Mock advanced analytics service initialized")
    
    async def health_check(self):
        """Health check for mock service"""
        return {"status": "mock", "message": "Mock advanced analytics service is running"}
    
    def get_status(self):
        """Get service status"""
        return {
            "type": "mock",
            "status": "healthy",
            "message": "Mock service - full functionality not available"
        }
    
    def analyze_user_behavior_patterns(self, days=30, environment="production"):
        """Mock user behavior analysis"""
        self.logger.warning("Mock user behavior analysis called - returning empty results")
        return []
    
    def analyze_feature_performance_insights(self, days=30, environment="production"):
        """Mock feature performance analysis"""
        self.logger.warning("Mock feature performance analysis called - returning empty results")
        return []
    
    def generate_business_intelligence_report(self, report_type="comprehensive", days=30, environment="production"):
        """Mock business intelligence report"""
        self.logger.warning("Mock business intelligence report called - returning empty report")
        from datetime import datetime
        return {
            "report_type": report_type,
            "period": f"{days} days",
            "key_metrics": {},
            "insights": ["Mock service - no actual analytics available"],
            "recommendations": [],
            "trends": {},
            "generated_at": datetime.utcnow()
        }
    
    def get_predictive_insights(self, days=30, environment="production"):
        """Mock predictive insights"""
        self.logger.warning("Mock predictive insights called - returning empty results")
        from datetime import datetime
        return {
            "usage_trend": "unknown",
            "predicted_daily_usage": 0,
            "trending_features": [],
            "current_daily_average": 0,
            "current_user_average": 0,
            "prediction_confidence": "none",
            "generated_at": datetime.utcnow().isoformat()
        }


class MockKnowledgeGraphService:
    """
    Mock knowledge graph service for when the full service cannot be initialized
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MockKnowledgeGraphService")
        self.logger.info("Mock knowledge graph service initialized")
        self.entities_store = {}
        self.relationships_store = {}
    
    async def health_check(self):
        """Health check for mock service"""
        return {"status": "mock", "message": "Mock knowledge graph service is running"}
    
    def get_status(self):
        """Get service status"""
        return {
            "type": "mock",
            "status": "healthy",
            "message": "Mock service - full functionality not available",
            "entities_count": len(self.entities_store),
            "relationships_count": len(self.relationships_store)
        }
    
    async def create_entity(self, name, entity_type, description=None, importance_score=0.5, document_id=None, metadata=None):
        """Mock entity creation"""
        self.logger.warning("Mock knowledge graph entity creation called")
        return {
            "id": "mock-entity-id",
            "name": name,
            "type": entity_type,
            "description": description,
            "importance_score": importance_score,
            "document_id": document_id,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "status": "mock"
        }
    
    async def get_entities(self, entity_type=None, document_id=None, min_importance=0.0, limit=100):
        """Mock entity retrieval"""
        self.logger.warning("Mock knowledge graph entity retrieval called - returning empty results")
        return []
    
    async def create_relationship(self, source_entity_id, target_entity_id, relationship_type, confidence_score=0.5, context=None, metadata=None):
        """Mock relationship creation"""
        self.logger.warning("Mock knowledge graph relationship creation called")
        return {
            "id": "mock-relationship-id",
            "source_entity_id": source_entity_id,
            "target_entity_id": target_entity_id,
            "relationship_type": relationship_type,
            "confidence_score": confidence_score,
            "context": context,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "status": "mock"
        }
    
    async def query_graph(self, entity_name=None, relationship_type=None, max_depth=2, min_confidence=0.0, include_metadata=True):
        """Mock graph query"""
        self.logger.warning("Mock knowledge graph query called - returning empty results")
        return {
            "entities": [],
            "relationships": [],
            "metadata": {
                "query_entity": entity_name,
                "query_relationship_type": relationship_type,
                "max_depth": max_depth,
                "min_confidence": min_confidence,
                "total_entities": 0,
                "total_relationships": 0,
                "status": "mock"
            }
        }
    
    async def get_entity_connections(self, entity_id, depth=2, min_confidence=0.5):
        """Mock entity connections"""
        self.logger.warning("Mock knowledge graph entity connections called - returning empty results")
        return {
            "connections": [],
            "entity_id": entity_id,
            "depth": depth,
            "min_confidence": min_confidence,
            "total_connections": 0,
            "status": "mock"
        }
    
    async def build_from_documents(self, documents):
        """Mock knowledge graph building from documents"""
        self.logger.warning("Mock knowledge graph building from documents called")
        return {
            "entities_count": 0,
            "relationships_count": 0,
            "graph_analysis": {"status": "mock"},
            "build_timestamp": datetime.now().isoformat(),
            "status": "mock"
        }
    
    async def find_research_connections(self, query, max_results=10):
        """Mock research connections discovery"""
        self.logger.warning("Mock research connections discovery called - returning empty results")
        return []
    
    async def suggest_research_directions(self, user_interests):
        """Mock research direction suggestions"""
        self.logger.warning("Mock research direction suggestions called - returning empty results")
        return []


class ServiceStatus(Enum):
    """Service status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    INITIALIZING = "initializing"
    FAILED = "failed"


@dataclass
class ServiceHealth:
    """Service health information"""
    name: str
    status: ServiceStatus
    last_check: datetime
    error_message: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    initialization_time: Optional[float] = None


class ServiceManager:
    """
    Centralized service manager for handling service initialization and health monitoring
    """
    
    def __init__(self):
        self.services: Dict[str, Any] = {}
        self.health_status: Dict[str, ServiceHealth] = {}
        self.initialization_order: List[str] = []
        self.logger = logging.getLogger(f"{__name__}.ServiceManager")
        
        # Health monitoring configuration
        self.health_check_interval: int = 300  # 5 minutes in seconds
        self.health_cache_ttl: int = 60  # 1 minute cache TTL in seconds
        self.monitoring_enabled: bool = True
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Health check cache
        self.health_cache: Dict[str, tuple[ServiceHealth, datetime]] = {}
        
    async def initialize_database_service(self) -> bool:
        """
        Initialize database service with comprehensive error handling and safe imports
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        service_name = "database"
        initialization_start_time = datetime.utcnow()
        
        try:
            self.logger.info(
                f"Starting database service initialization",
                extra={
                    "service_name": service_name,
                    "event_type": "database_service_initialization_start",
                    "start_time": initialization_start_time.isoformat()
                }
            )
            
            # Try to import database service with error handling
            try:
                from services.database_service import initialize_database_service
                self.logger.debug(
                    "Successfully imported database service initialization function",
                    extra={
                        "service_name": service_name,
                        "event_type": "database_service_import_success",
                        "import_type": "initialization_function"
                    }
                )
            except ImportError as e:
                error_details = {
                    "error_type": "import_error",
                    "import_target": "services.database_service.initialize_database_service",
                    "error_message": str(e)
                }
                self.logger.error(
                    f"Failed to import database service initialization function: {str(e)}",
                    extra={
                        "service_name": service_name,
                        "event_type": "database_service_import_error",
                        **error_details
                    },
                    exc_info=True
                )
                return False
            except Exception as e:
                error_details = {
                    "error_type": type(e).__name__,
                    "import_target": "services.database_service.initialize_database_service",
                    "error_message": str(e)
                }
                self.logger.error(
                    f"Unexpected error importing database service: {str(e)}",
                    extra={
                        "service_name": service_name,
                        "event_type": "database_service_import_unexpected_error",
                        **error_details
                    },
                    exc_info=True
                )
                return False
            
            # Initialize the database service with timeout and error handling
            try:
                self.logger.info("Calling database service initialization function...")
                success = await asyncio.wait_for(
                    initialize_database_service(),
                    timeout=60.0  # 60 second timeout for database initialization
                )
                
                if not success:
                    error_details = {
                        "error_type": "initialization_failure",
                        "initialization_result": success,
                        "reason": "Database service initialization function returned False"
                    }
                    self.logger.error(
                        "Database service initialization function returned False",
                        extra={
                            "service_name": service_name,
                            "event_type": "database_service_initialization_failed",
                            **error_details
                        }
                    )
                    return False
                
                self.logger.info(
                    "Database service initialization function completed successfully",
                    extra={
                        "service_name": service_name,
                        "event_type": "database_service_initialization_function_success"
                    }
                )
                
            except asyncio.TimeoutError as e:
                error_details = {
                    "error_type": "timeout_error",
                    "timeout_duration": 60.0,
                    "elapsed_time": (datetime.utcnow() - initialization_start_time).total_seconds()
                }
                self.logger.error(
                    "Database service initialization timed out",
                    extra={
                        "service_name": service_name,
                        "event_type": "database_service_initialization_timeout",
                        **error_details
                    }
                )
                return False
                
            except Exception as e:
                error_details = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "elapsed_time": (datetime.utcnow() - initialization_start_time).total_seconds()
                }
                self.logger.error(
                    f"Database service initialization function failed: {str(e)}",
                    extra={
                        "service_name": service_name,
                        "event_type": "database_service_initialization_function_error",
                        **error_details
                    },
                    exc_info=True
                )
                return False
            
            # Get the database service instance with error handling
            try:
                from services.database_service import get_database_service
                self.logger.debug(
                    "Successfully imported database service getter function",
                    extra={
                        "service_name": service_name,
                        "event_type": "database_service_getter_import_success"
                    }
                )
                
                database_service = await asyncio.wait_for(
                    get_database_service(),
                    timeout=30.0  # 30 second timeout for getting service instance
                )
                
                if database_service is None:
                    error_details = {
                        "error_type": "service_instance_null",
                        "reason": "get_database_service() returned None"
                    }
                    self.logger.error(
                        "Database service getter returned None",
                        extra={
                            "service_name": service_name,
                            "event_type": "database_service_getter_null_result",
                            **error_details
                        }
                    )
                    return False
                
                self.logger.info(
                    f"Successfully retrieved database service instance: {type(database_service).__name__}",
                    extra={
                        "service_name": service_name,
                        "event_type": "database_service_instance_retrieved",
                        "instance_type": type(database_service).__name__
                    }
                )
                
            except ImportError as e:
                error_details = {
                    "error_type": "import_error",
                    "import_target": "services.database_service.get_database_service",
                    "error_message": str(e)
                }
                self.logger.error(
                    f"Failed to import database service getter function: {str(e)}",
                    extra={
                        "service_name": service_name,
                        "event_type": "database_service_getter_import_error",
                        **error_details
                    },
                    exc_info=True
                )
                return False
                
            except asyncio.TimeoutError as e:
                error_details = {
                    "error_type": "timeout_error",
                    "timeout_duration": 30.0,
                    "operation": "get_database_service"
                }
                self.logger.error(
                    "Database service getter timed out",
                    extra={
                        "service_name": service_name,
                        "event_type": "database_service_getter_timeout",
                        **error_details
                    }
                )
                return False
                
            except Exception as e:
                error_details = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "operation": "get_database_service"
                }
                self.logger.error(
                    f"Database service getter failed: {str(e)}",
                    extra={
                        "service_name": service_name,
                        "event_type": "database_service_getter_error",
                        **error_details
                    },
                    exc_info=True
                )
                return False
            
            # Register the service with the service manager using enhanced initialization
            def database_service_factory():
                return database_service
            
            initialization_result = await self.initialize_service(
                service_name=service_name,
                service_factory=database_service_factory,
                dependencies=[],
                max_retries=2,  # Fewer retries since we already have the instance
                retry_delay=1.0,
                recovery_strategy="fail"  # No fallback for database service
            )
            
            total_time = (datetime.utcnow() - initialization_start_time).total_seconds()
            
            if initialization_result:
                self.logger.info(
                    f"Database service initialization completed successfully in {total_time:.2f}s",
                    extra={
                        "service_name": service_name,
                        "event_type": "database_service_initialization_complete_success",
                        "total_initialization_time": total_time
                    }
                )
            else:
                self.logger.error(
                    f"Database service initialization failed after {total_time:.2f}s",
                    extra={
                        "service_name": service_name,
                        "event_type": "database_service_initialization_complete_failure",
                        "total_initialization_time": total_time
                    }
                )
            
            return initialization_result
                
        except Exception as e:
            total_time = (datetime.utcnow() - initialization_start_time).total_seconds()
            error_details = {
                "error_type": "unexpected_error",
                "exception_type": type(e).__name__,
                "error_message": str(e),
                "total_time": total_time
            }
            self.logger.error(
                f"Unexpected error during database service initialization: {str(e)}",
                extra={
                    "service_name": service_name,
                    "event_type": "database_service_initialization_unexpected_error",
                    **error_details
                },
                exc_info=True
            )
            return False

    async def initialize_semantic_search_service(self) -> bool:
        """
        Initialize semantic search service with comprehensive error handling and safe imports
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        service_name = "semantic_search"
        initialization_start_time = datetime.utcnow()
        
        try:
            self.logger.info(
                "Starting semantic search service initialization",
                extra={
                    "service_name": service_name,
                    "event_type": "semantic_search_initialization_start",
                    "start_time": initialization_start_time.isoformat()
                }
            )
            
            # Import conditional importer with error handling
            try:
                from core.conditional_importer import ConditionalImporter
                self.logger.debug(
                    "Successfully imported ConditionalImporter",
                    extra={
                        "service_name": service_name,
                        "event_type": "conditional_importer_import_success"
                    }
                )
            except ImportError as e:
                error_details = {
                    "error_type": "import_error",
                    "import_target": "core.conditional_importer.ConditionalImporter",
                    "error_message": str(e)
                }
                self.logger.error(
                    f"Failed to import ConditionalImporter: {str(e)}",
                    extra={
                        "service_name": service_name,
                        "event_type": "conditional_importer_import_error",
                        **error_details
                    },
                    exc_info=True
                )
                return await self._initialize_mock_semantic_search_service_with_error_handling("ConditionalImporter import failed")
            
            # Check required dependencies with detailed logging
            dependency_check_results = {}
            
            try:
                numpy_available = ConditionalImporter.safe_import("numpy", fallback=None) is not None
                dependency_check_results["numpy"] = {
                    "available": numpy_available,
                    "required": True
                }
                
                if not numpy_available:
                    self.logger.warning(
                        "numpy not available - will use mock semantic search service",
                        extra={
                            "service_name": service_name,
                            "event_type": "dependency_check_failed",
                            "missing_dependency": "numpy"
                        }
                    )
                    return await self._initialize_mock_semantic_search_service_with_error_handling("numpy dependency not available")
                
                sqlalchemy_available = ConditionalImporter.safe_import("sqlalchemy", fallback=None) is not None
                dependency_check_results["sqlalchemy"] = {
                    "available": sqlalchemy_available,
                    "required": True
                }
                
                if not sqlalchemy_available:
                    self.logger.warning(
                        "sqlalchemy not available - will use mock semantic search service",
                        extra={
                            "service_name": service_name,
                            "event_type": "dependency_check_failed",
                            "missing_dependency": "sqlalchemy"
                        }
                    )
                    return await self._initialize_mock_semantic_search_service_with_error_handling("sqlalchemy dependency not available")
                
                self.logger.info(
                    "All required dependencies available for semantic search service",
                    extra={
                        "service_name": service_name,
                        "event_type": "dependency_check_success",
                        "dependency_results": dependency_check_results
                    }
                )
                
            except Exception as e:
                error_details = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "operation": "dependency_check"
                }
                self.logger.error(
                    f"Error during dependency check: {str(e)}",
                    extra={
                        "service_name": service_name,
                        "event_type": "dependency_check_error",
                        **error_details
                    },
                    exc_info=True
                )
                return await self._initialize_mock_semantic_search_service_with_error_handling(f"Dependency check error: {str(e)}")
            
            # Safely import the semantic search service class with detailed error handling
            try:
                SemanticSearchV2Service = ConditionalImporter.safe_import(
                    module_name="services.semantic_search_v2",
                    attribute="SemanticSearchV2Service",
                    fallback=None
                )
                
                if SemanticSearchV2Service is None:
                    self.logger.warning(
                        "SemanticSearchV2Service class not available - will use mock service",
                        extra={
                            "service_name": service_name,
                            "event_type": "service_class_import_failed",
                            "import_target": "services.semantic_search_v2.SemanticSearchV2Service"
                        }
                    )
                    return await self._initialize_mock_semantic_search_service_with_error_handling("SemanticSearchV2Service class not available")
                
                self.logger.info(
                    "Successfully imported SemanticSearchV2Service class",
                    extra={
                        "service_name": service_name,
                        "event_type": "service_class_import_success",
                        "service_class": "SemanticSearchV2Service"
                    }
                )
                
            except Exception as e:
                error_details = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "import_target": "services.semantic_search_v2.SemanticSearchV2Service"
                }
                self.logger.error(
                    f"Error importing SemanticSearchV2Service: {str(e)}",
                    extra={
                        "service_name": service_name,
                        "event_type": "service_class_import_error",
                        **error_details
                    },
                    exc_info=True
                )
                return await self._initialize_mock_semantic_search_service_with_error_handling(f"Service class import error: {str(e)}")
            
            # Check database service dependency with detailed validation
            try:
                database_service = self.get_service("database")
                if not database_service:
                    self.logger.warning(
                        "Database service not available - will use mock semantic search service",
                        extra={
                            "service_name": service_name,
                            "event_type": "dependency_service_unavailable",
                            "missing_service": "database"
                        }
                    )
                    return await self._initialize_mock_semantic_search_service_with_error_handling("Database service dependency not available")
                
                # Validate database service health
                if not self.is_service_healthy("database"):
                    database_health = self.health_status.get("database")
                    health_info = {
                        "status": database_health.status.value if database_health else "unknown",
                        "error_message": database_health.error_message if database_health else "unknown"
                    }
                    self.logger.warning(
                        "Database service is not healthy - will use mock semantic search service",
                        extra={
                            "service_name": service_name,
                            "event_type": "dependency_service_unhealthy",
                            "dependency_service": "database",
                            "dependency_health": health_info
                        }
                    )
                    return await self._initialize_mock_semantic_search_service_with_error_handling("Database service dependency is unhealthy")
                
                self.logger.info(
                    "Database service dependency validated successfully",
                    extra={
                        "service_name": service_name,
                        "event_type": "dependency_service_validated",
                        "dependency_service": "database"
                    }
                )
                
            except Exception as e:
                error_details = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "operation": "database_service_validation"
                }
                self.logger.error(
                    f"Error validating database service dependency: {str(e)}",
                    extra={
                        "service_name": service_name,
                        "event_type": "dependency_service_validation_error",
                        **error_details
                    },
                    exc_info=True
                )
                return await self._initialize_mock_semantic_search_service_with_error_handling(f"Database service validation error: {str(e)}")
            
            # Create enhanced service factory function with comprehensive error handling
            def create_semantic_search_service():
                factory_start_time = datetime.utcnow()
                try:
                    self.logger.debug(
                        "Creating semantic search service instance",
                        extra={
                            "service_name": service_name,
                            "event_type": "service_factory_start",
                            "factory_start_time": factory_start_time.isoformat()
                        }
                    )
                    
                    # Get database session with error handling
                    try:
                        db_session = database_service.get_session()
                        if db_session is None:
                            raise RuntimeError("Database service returned None session")
                        
                        self.logger.debug(
                            "Successfully obtained database session",
                            extra={
                                "service_name": service_name,
                                "event_type": "database_session_obtained"
                            }
                        )
                        
                    except Exception as e:
                        self.logger.error(
                            f"Error getting database session: {str(e)}",
                            extra={
                                "service_name": service_name,
                                "event_type": "database_session_error",
                                "error_type": type(e).__name__,
                                "error_message": str(e)
                            },
                            exc_info=True
                        )
                        # Fall back to mock service
                        return MockSemanticSearchService()
                    
                    # Create the actual service instance
                    try:
                        service_instance = SemanticSearchV2Service(db=db_session)
                        factory_time = (datetime.utcnow() - factory_start_time).total_seconds()
                        
                        self.logger.info(
                            f"Successfully created semantic search service instance in {factory_time:.2f}s",
                            extra={
                                "service_name": service_name,
                                "event_type": "service_factory_success",
                                "factory_time": factory_time,
                                "instance_type": type(service_instance).__name__
                            }
                        )
                        
                        return service_instance
                        
                    except Exception as e:
                        factory_time = (datetime.utcnow() - factory_start_time).total_seconds()
                        self.logger.error(
                            f"Error creating semantic search service instance: {str(e)}",
                            extra={
                                "service_name": service_name,
                                "event_type": "service_factory_instance_error",
                                "factory_time": factory_time,
                                "error_type": type(e).__name__,
                                "error_message": str(e)
                            },
                            exc_info=True
                        )
                        # Fall back to mock service
                        return MockSemanticSearchService()
                        
                except Exception as e:
                    factory_time = (datetime.utcnow() - factory_start_time).total_seconds()
                    self.logger.error(
                        f"Unexpected error in semantic search service factory: {str(e)}",
                        extra={
                            "service_name": service_name,
                            "event_type": "service_factory_unexpected_error",
                            "factory_time": factory_time,
                            "error_type": type(e).__name__,
                            "error_message": str(e)
                        },
                        exc_info=True
                    )
                    # Fall back to mock service
                    return MockSemanticSearchService()
            
            # Initialize the service using enhanced service manager
            initialization_result = await self.initialize_service(
                service_name=service_name,
                service_factory=create_semantic_search_service,
                dependencies=["database"],
                max_retries=3,
                retry_delay=2.0,
                recovery_strategy="fallback"
            )
            
            total_time = (datetime.utcnow() - initialization_start_time).total_seconds()
            
            if initialization_result:
                self.logger.info(
                    f"Semantic search service initialization completed successfully in {total_time:.2f}s",
                    extra={
                        "service_name": service_name,
                        "event_type": "semantic_search_initialization_complete_success",
                        "total_initialization_time": total_time
                    }
                )
            else:
                self.logger.error(
                    f"Semantic search service initialization failed after {total_time:.2f}s",
                    extra={
                        "service_name": service_name,
                        "event_type": "semantic_search_initialization_complete_failure",
                        "total_initialization_time": total_time
                    }
                )
            
            return initialization_result
            
        except Exception as e:
            total_time = (datetime.utcnow() - initialization_start_time).total_seconds()
            error_details = {
                "error_type": "unexpected_error",
                "exception_type": type(e).__name__,
                "error_message": str(e),
                "total_time": total_time
            }
            self.logger.error(
                f"Unexpected error during semantic search service initialization: {str(e)}",
                extra={
                    "service_name": service_name,
                    "event_type": "semantic_search_initialization_unexpected_error",
                    **error_details
                },
                exc_info=True
            )
            # Fall back to mock service as last resort
            return await self._initialize_mock_semantic_search_service_with_error_handling(f"Unexpected error: {str(e)}")
    
    async def _initialize_mock_semantic_search_service_with_error_handling(self, reason: str) -> bool:
        """
        Initialize mock semantic search service with enhanced error handling and logging
        
        Args:
            reason: Reason for falling back to mock service
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        service_name = "semantic_search"
        mock_start_time = datetime.utcnow()
        
        try:
            self.logger.warning(
                f"Initializing mock semantic search service due to: {reason}",
                extra={
                    "service_name": service_name,
                    "event_type": "mock_service_initialization_start",
                    "fallback_reason": reason,
                    "start_time": mock_start_time.isoformat()
                }
            )
            
            # Create service factory function for mock service with error handling
            def create_mock_service():
                try:
                    mock_instance = MockSemanticSearchService()
                    self.logger.info(
                        "Successfully created mock semantic search service instance",
                        extra={
                            "service_name": service_name,
                            "event_type": "mock_service_instance_created",
                            "instance_type": type(mock_instance).__name__
                        }
                    )
                    return mock_instance
                except Exception as e:
                    self.logger.error(
                        f"Error creating mock semantic search service: {str(e)}",
                        extra={
                            "service_name": service_name,
                            "event_type": "mock_service_creation_error",
                            "error_type": type(e).__name__,
                            "error_message": str(e)
                        },
                        exc_info=True
                    )
                    raise
            
            # Initialize the mock service
            initialization_result = await self.initialize_service(
                service_name=service_name,
                service_factory=create_mock_service,
                dependencies=[],  # Mock service has no dependencies
                max_retries=1,  # Fewer retries for mock service
                retry_delay=1.0,
                recovery_strategy="fail"  # No further fallback for mock service
            )
            
            total_time = (datetime.utcnow() - mock_start_time).total_seconds()
            
            if initialization_result:
                self.logger.warning(
                    f"Mock semantic search service initialization completed in {total_time:.2f}s",
                    extra={
                        "service_name": service_name,
                        "event_type": "mock_service_initialization_success",
                        "total_time": total_time,
                        "fallback_reason": reason
                    }
                )
            else:
                self.logger.error(
                    f"Mock semantic search service initialization failed after {total_time:.2f}s",
                    extra={
                        "service_name": service_name,
                        "event_type": "mock_service_initialization_failure",
                        "total_time": total_time,
                        "fallback_reason": reason
                    }
                )
            
            return initialization_result
            
        except Exception as e:
            total_time = (datetime.utcnow() - mock_start_time).total_seconds()
            error_details = {
                "error_type": "mock_service_error",
                "exception_type": type(e).__name__,
                "error_message": str(e),
                "total_time": total_time,
                "fallback_reason": reason
            }
            self.logger.error(
                f"Error initializing mock semantic search service: {str(e)}",
                extra={
                    "service_name": service_name,
                    "event_type": "mock_service_initialization_error",
                    **error_details
                },
                exc_info=True
            )
            return False

    async def _initialize_mock_semantic_search_service(self) -> bool:
        """
        Initialize mock semantic search service as fallback (legacy method)
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        return await self._initialize_mock_semantic_search_service_with_error_handling("Legacy fallback method called")

    async def initialize_research_automation_service(self) -> bool:
        """
        Initialize research automation service with safe imports and error handling
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            from core.conditional_importer import ConditionalImporter
            
            self.logger.info("Attempting to initialize research automation service...")
            
            # Check if required dependencies are available
            schedule_available = ConditionalImporter.safe_import("schedule", fallback=None) is not None
            sqlalchemy_available = ConditionalImporter.safe_import("sqlalchemy", fallback=None) is not None
            
            if not schedule_available:
                self.logger.warning("schedule library not available - using mock research automation service")
                return await self._initialize_mock_research_automation_service()
            
            if not sqlalchemy_available:
                self.logger.warning("sqlalchemy not available - using mock research automation service")
                return await self._initialize_mock_research_automation_service()
            
            # Safely import the research automation service class
            ResearchAutomationService = ConditionalImporter.safe_import(
                module_name="services.research_automation",
                attribute="ResearchAutomationService",
                fallback=None
            )
            
            if ResearchAutomationService is None:
                self.logger.warning("ResearchAutomationService class not available - using mock service")
                return await self._initialize_mock_research_automation_service()
            
            # Check if database service is available (dependency)
            database_service = self.get_service("database")
            if not database_service:
                self.logger.warning("Database service not available - using mock research automation service")
                return await self._initialize_mock_research_automation_service()
            
            # Create service factory function
            def create_research_automation_service():
                try:
                    # Get database session
                    db_session = database_service.get_session()
                    return ResearchAutomationService(db=db_session)
                except Exception as e:
                    self.logger.error(f"Error creating research automation service instance: {e}")
                    # Fall back to mock service
                    return MockResearchAutomationService()
            
            # Initialize the service
            return await self.initialize_service(
                service_name="research_automation",
                service_factory=create_research_automation_service,
                dependencies=["database"]
            )
            
        except Exception as e:
            self.logger.error(f"Error initializing research automation service: {e}", exc_info=True)
            # Fall back to mock service
            return await self._initialize_mock_research_automation_service()

    async def _initialize_mock_research_automation_service(self) -> bool:
        """
        Initialize mock research automation service as fallback
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing mock research automation service...")
            
            # Create service factory function for mock service
            def create_mock_service():
                return MockResearchAutomationService()
            
            # Initialize the mock service
            return await self.initialize_service(
                service_name="research_automation",
                service_factory=create_mock_service,
                dependencies=[]
            )
            
        except Exception as e:
            self.logger.error(f"Error initializing mock research automation service: {e}", exc_info=True)
            return False

    async def initialize_advanced_analytics_service(self) -> bool:
        """
        Initialize advanced analytics service with safe imports and error handling
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            from core.conditional_importer import ConditionalImporter
            
            self.logger.info("Attempting to initialize advanced analytics service...")
            
            # Check if required dependencies are available
            pandas_available = ConditionalImporter.safe_import("pandas", fallback=None) is not None
            numpy_available = ConditionalImporter.safe_import("numpy", fallback=None) is not None
            sqlalchemy_available = ConditionalImporter.safe_import("sqlalchemy", fallback=None) is not None
            
            if not pandas_available:
                self.logger.warning("pandas not available - using mock advanced analytics service")
                return await self._initialize_mock_advanced_analytics_service()
            
            if not numpy_available:
                self.logger.warning("numpy not available - using mock advanced analytics service")
                return await self._initialize_mock_advanced_analytics_service()
            
            if not sqlalchemy_available:
                self.logger.warning("sqlalchemy not available - using mock advanced analytics service")
                return await self._initialize_mock_advanced_analytics_service()
            
            # Safely import the advanced analytics service class
            AdvancedAnalyticsService = ConditionalImporter.safe_import(
                module_name="services.advanced_analytics_service",
                attribute="AdvancedAnalyticsService",
                fallback=None
            )
            
            if AdvancedAnalyticsService is None:
                self.logger.warning("AdvancedAnalyticsService class not available - using mock service")
                return await self._initialize_mock_advanced_analytics_service()
            
            # Check if database service is available (dependency)
            database_service = self.get_service("database")
            if not database_service:
                self.logger.warning("Database service not available - using mock advanced analytics service")
                return await self._initialize_mock_advanced_analytics_service()
            
            # Create service factory function
            def create_advanced_analytics_service():
                try:
                    # Create service instance
                    return AdvancedAnalyticsService()
                except Exception as e:
                    self.logger.error(f"Error creating advanced analytics service instance: {e}")
                    # Fall back to mock service
                    return MockAdvancedAnalyticsService()
            
            # Initialize the service
            return await self.initialize_service(
                service_name="advanced_analytics",
                service_factory=create_advanced_analytics_service,
                dependencies=["database"]
            )
            
        except Exception as e:
            self.logger.error(f"Error initializing advanced analytics service: {e}", exc_info=True)
            # Fall back to mock service
            return await self._initialize_mock_advanced_analytics_service()

    async def _initialize_mock_advanced_analytics_service(self) -> bool:
        """
        Initialize mock advanced analytics service as fallback
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing mock advanced analytics service...")
            
            # Create service factory function for mock service
            def create_mock_service():
                return MockAdvancedAnalyticsService()
            
            # Initialize the mock service
            return await self.initialize_service(
                service_name="advanced_analytics",
                service_factory=create_mock_service,
                dependencies=[]
            )
            
        except Exception as e:
            self.logger.error(f"Error initializing mock advanced analytics service: {e}", exc_info=True)
            return False

    async def initialize_knowledge_graph_service(self) -> bool:
        """
        Initialize knowledge graph service with safe imports and error handling
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            from core.conditional_importer import ConditionalImporter
            
            self.logger.info("Attempting to initialize knowledge graph service...")
            
            # Check if required dependencies are available
            networkx_available = ConditionalImporter.safe_import("networkx", fallback=None) is not None
            numpy_available = ConditionalImporter.safe_import("numpy", fallback=None) is not None
            spacy_available = ConditionalImporter.safe_import("spacy", fallback=None) is not None
            sklearn_available = ConditionalImporter.safe_import("sklearn", fallback=None) is not None
            
            if not networkx_available:
                self.logger.warning("networkx not available - using mock knowledge graph service")
                return await self._initialize_mock_knowledge_graph_service()
            
            if not numpy_available:
                self.logger.warning("numpy not available - using mock knowledge graph service")
                return await self._initialize_mock_knowledge_graph_service()
            
            if not spacy_available:
                self.logger.warning("spacy not available - using mock knowledge graph service")
                return await self._initialize_mock_knowledge_graph_service()
            
            if not sklearn_available:
                self.logger.warning("sklearn not available - using mock knowledge graph service")
                return await self._initialize_mock_knowledge_graph_service()
            
            # Safely import the knowledge graph service class
            KnowledgeGraphService = ConditionalImporter.safe_import(
                module_name="services.knowledge_graph_service",
                attribute="KnowledgeGraphService",
                fallback=None
            )
            
            if KnowledgeGraphService is None:
                self.logger.warning("KnowledgeGraphService class not available - using mock service")
                return await self._initialize_mock_knowledge_graph_service()
            
            # Create service factory function
            def create_knowledge_graph_service():
                try:
                    return KnowledgeGraphService()
                except Exception as e:
                    self.logger.error(f"Error creating knowledge graph service instance: {e}")
                    # Fall back to mock service
                    return MockKnowledgeGraphService()
            
            # Initialize the service
            return await self.initialize_service(
                service_name="knowledge_graph",
                service_factory=create_knowledge_graph_service,
                dependencies=[]
            )
            
        except Exception as e:
            self.logger.error(f"Error initializing knowledge graph service: {e}", exc_info=True)
            # Fall back to mock service
            return await self._initialize_mock_knowledge_graph_service()

    async def _initialize_mock_knowledge_graph_service(self) -> bool:
        """
        Initialize mock knowledge graph service as fallback
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing mock knowledge graph service...")
            
            # Create service factory function for mock service
            def create_mock_service():
                return MockKnowledgeGraphService()
            
            # Initialize the mock service
            return await self.initialize_service(
                service_name="knowledge_graph",
                service_factory=create_mock_service,
                dependencies=[]
            )
            
        except Exception as e:
            self.logger.error(f"Error initializing mock knowledge graph service: {e}", exc_info=True)
            return False

    async def initialize_service(
        self, 
        service_name: str, 
        service_factory, 
        dependencies: List[str] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        recovery_strategy: str = "fallback",
        **kwargs
    ) -> bool:
        """
        Initialize a service with comprehensive error handling and retry logic
        
        Args:
            service_name: Name of the service
            service_factory: Function or class to create the service
            dependencies: List of service names this service depends on
            max_retries: Maximum number of initialization retries
            retry_delay: Delay between retries in seconds
            recovery_strategy: Recovery strategy ("fallback", "fail", "retry")
            **kwargs: Additional arguments for service initialization
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        dependencies = dependencies or []
        start_time = datetime.utcnow()
        initialization_context = {
            "service_name": service_name,
            "dependencies": dependencies,
            "recovery_strategy": recovery_strategy,
            "max_retries": max_retries,
            "start_time": start_time.isoformat()
        }
        
        try:
            # Enhanced input validation with detailed error logging
            self._log_service_initialization_start(service_name, initialization_context)
            
            if not service_name or not isinstance(service_name, str):
                error_details = {
                    "error_type": "validation_error",
                    "invalid_service_name": service_name,
                    "service_name_type": type(service_name).__name__
                }
                self._log_service_initialization_error(service_name, "Invalid service name", error_details)
                raise ValueError(f"Invalid service name: {service_name}")
            
            # Check if service already exists with detailed logging
            if service_name in self.services:
                existing_service_info = {
                    "service_status": self.health_status.get(service_name, {}).status.value if service_name in self.health_status else "unknown",
                    "initialization_order_position": self.initialization_order.index(service_name) if service_name in self.initialization_order else -1
                }
                self._log_service_initialization_warning(service_name, "Service already initialized, skipping", existing_service_info)
                return True
            
            # Enhanced dependency validation with detailed error reporting
            dependency_validation_result = await self._validate_service_dependencies(service_name, dependencies)
            if not dependency_validation_result["valid"]:
                error_msg = f"Cannot initialize {service_name}: {dependency_validation_result['error_message']}"
                self._log_service_initialization_error(service_name, error_msg, dependency_validation_result["details"])
                
                self.health_status[service_name] = ServiceHealth(
                    name=service_name,
                    status=ServiceStatus.FAILED,
                    last_check=datetime.utcnow(),
                    error_message=error_msg,
                    dependencies=dependencies
                )
                return False
            
            # Update status to initializing with detailed logging
            self.health_status[service_name] = ServiceHealth(
                name=service_name,
                status=ServiceStatus.INITIALIZING,
                last_check=start_time,
                dependencies=dependencies
            )
            self._log_service_status_change(service_name, ServiceStatus.INITIALIZING, "Starting service initialization")
            
            # Enhanced initialization attempts with comprehensive error handling
            last_error = None
            initialization_attempts = []
            
            for attempt in range(max_retries):
                attempt_start_time = datetime.utcnow()
                attempt_context = {
                    "attempt_number": attempt + 1,
                    "max_attempts": max_retries,
                    "attempt_start_time": attempt_start_time.isoformat(),
                    "retry_delay": retry_delay
                }
                
                try:
                    self._log_service_initialization_attempt(service_name, attempt_context)
                    
                    # Enhanced service factory validation
                    factory_validation_result = self._validate_service_factory(service_name, service_factory)
                    if not factory_validation_result["valid"]:
                        raise ValueError(factory_validation_result["error_message"])
                    
                    # Create service instance with enhanced error handling and timeout
                    service_instance = await self._create_service_instance_with_error_handling(
                        service_name, service_factory, attempt + 1, **kwargs
                    )
                    
                    if service_instance is None:
                        error_details = {
                            "error_type": "factory_error",
                            "factory_type": type(service_factory).__name__,
                            "factory_callable": callable(service_factory)
                        }
                        self._log_service_initialization_error(service_name, "Service factory returned None", error_details)
                        raise RuntimeError(f"Service factory returned None for {service_name}")
                    
                    # Enhanced service instance validation
                    validation_result = await self._validate_service_instance_with_error_handling(service_name, service_instance, attempt + 1)
                    if not validation_result["valid"]:
                        raise RuntimeError(f"Service validation failed: {validation_result['error_message']}")
                    
                    # Store service with success logging
                    self.services[service_name] = service_instance
                    self.initialization_order.append(service_name)
                    
                    # Calculate initialization time and log success
                    end_time = datetime.utcnow()
                    init_time = (end_time - start_time).total_seconds()
                    attempt_time = (end_time - attempt_start_time).total_seconds()
                    
                    success_details = {
                        "total_initialization_time": init_time,
                        "final_attempt_time": attempt_time,
                        "successful_attempt": attempt + 1,
                        "service_type": type(service_instance).__name__,
                        "validation_results": validation_result.get("details", {})
                    }
                    
                    # Update health status with success
                    self.health_status[service_name] = ServiceHealth(
                        name=service_name,
                        status=ServiceStatus.HEALTHY,
                        last_check=end_time,
                        dependencies=dependencies,
                        initialization_time=init_time
                    )
                    
                    self._log_service_initialization_success(service_name, success_details)
                    self._log_service_status_change(service_name, ServiceStatus.HEALTHY, f"Service initialized successfully in {init_time:.2f}s")
                    
                    # Log service capabilities if available
                    await self._log_service_capabilities(service_name, service_instance)
                    
                    return True
                    
                except asyncio.TimeoutError as e:
                    last_error = e
                    attempt_time = (datetime.utcnow() - attempt_start_time).total_seconds()
                    timeout_details = {
                        "error_type": "timeout_error",
                        "timeout_duration": 30.0,
                        "attempt_duration": attempt_time,
                        "attempt_number": attempt + 1
                    }
                    error_msg = f"Service {service_name} initialization timed out (attempt {attempt + 1})"
                    self._log_service_initialization_error(service_name, error_msg, timeout_details)
                    initialization_attempts.append({
                        "attempt": attempt + 1,
                        "error_type": "timeout",
                        "error_message": str(e),
                        "duration": attempt_time
                    })
                    
                except Exception as e:
                    last_error = e
                    attempt_time = (datetime.utcnow() - attempt_start_time).total_seconds()
                    exception_details = {
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "attempt_duration": attempt_time,
                        "attempt_number": attempt + 1,
                        "traceback_available": True
                    }
                    error_msg = f"Failed to initialize {service_name} (attempt {attempt + 1}): {str(e)}"
                    self._log_service_initialization_error(service_name, error_msg, exception_details, include_traceback=True)
                    initialization_attempts.append({
                        "attempt": attempt + 1,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "duration": attempt_time
                    })
                
                # Enhanced recovery strategy implementation
                if attempt < max_retries - 1:
                    recovery_result = await self._apply_recovery_strategy(
                        service_name, recovery_strategy, dependencies, attempt + 1, retry_delay, last_error
                    )
                    
                    if recovery_result["success"]:
                        return True
                    
                    # Update retry delay for next attempt
                    retry_delay = recovery_result.get("next_retry_delay", retry_delay)
                else:
                    # Final attempt failed
                    self._log_service_initialization_final_attempt_failed(service_name, attempt + 1, last_error)
            
            # All attempts failed - comprehensive failure handling
            end_time = datetime.utcnow()
            init_time = (end_time - start_time).total_seconds()
            
            failure_details = {
                "total_attempts": max_retries,
                "total_initialization_time": init_time,
                "last_error_type": type(last_error).__name__ if last_error else "unknown",
                "last_error_message": str(last_error) if last_error else "unknown",
                "initialization_attempts": initialization_attempts,
                "recovery_strategy": recovery_strategy
            }
            
            final_error_msg = f"Failed to initialize {service_name} after {max_retries} attempts. Last error: {str(last_error)}"
            self._log_service_initialization_complete_failure(service_name, final_error_msg, failure_details)
            
            self.health_status[service_name] = ServiceHealth(
                name=service_name,
                status=ServiceStatus.FAILED,
                last_check=end_time,
                error_message=final_error_msg,
                dependencies=dependencies,
                initialization_time=init_time
            )
            
            self._log_service_status_change(service_name, ServiceStatus.FAILED, final_error_msg)
            
            # Try final fallback if strategy allows
            if recovery_strategy == "fallback":
                final_fallback_result = await self._try_final_fallback_initialization(service_name, dependencies, failure_details)
                if final_fallback_result["success"]:
                    self._log_service_initialization_fallback_success(service_name, final_fallback_result["details"])
                    return True
            
            return False
            
        except Exception as e:
            # Catch-all for unexpected errors with comprehensive logging
            end_time = datetime.utcnow()
            init_time = (end_time - start_time).total_seconds()
            
            unexpected_error_details = {
                "error_type": "unexpected_error",
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "total_time": init_time,
                "initialization_context": initialization_context,
                "traceback_available": True
            }
            
            error_msg = f"Unexpected error during {service_name} initialization: {str(e)}"
            self._log_service_initialization_error(service_name, error_msg, unexpected_error_details, include_traceback=True)
            
            self.health_status[service_name] = ServiceHealth(
                name=service_name,
                status=ServiceStatus.FAILED,
                last_check=end_time,
                error_message=error_msg,
                dependencies=dependencies,
                initialization_time=init_time
            )
            
            self._log_service_status_change(service_name, ServiceStatus.FAILED, error_msg)
            
            return False
    
    # ============================================================================
    # ENHANCED ERROR HANDLING AND LOGGING METHODS
    # ============================================================================
    
    def _log_service_initialization_start(self, service_name: str, context: Dict[str, Any]):
        """Log the start of service initialization with context"""
        self.logger.info(
            f"Starting initialization of service '{service_name}'",
            extra={
                "service_name": service_name,
                "event_type": "service_initialization_start",
                **context
            }
        )
    
    def _log_service_initialization_error(self, service_name: str, error_message: str, details: Dict[str, Any], include_traceback: bool = False):
        """Log service initialization errors with detailed context"""
        log_extra = {
            "service_name": service_name,
            "event_type": "service_initialization_error",
            "error_message": error_message,
            **details
        }
        
        if include_traceback:
            self.logger.error(error_message, extra=log_extra, exc_info=True)
        else:
            self.logger.error(error_message, extra=log_extra)
    
    def _log_service_initialization_warning(self, service_name: str, warning_message: str, details: Dict[str, Any]):
        """Log service initialization warnings with context"""
        self.logger.warning(
            warning_message,
            extra={
                "service_name": service_name,
                "event_type": "service_initialization_warning",
                "warning_message": warning_message,
                **details
            }
        )
    
    def _log_service_initialization_attempt(self, service_name: str, attempt_context: Dict[str, Any]):
        """Log each initialization attempt"""
        self.logger.info(
            f"Attempting to initialize service '{service_name}' (attempt {attempt_context['attempt_number']}/{attempt_context['max_attempts']})",
            extra={
                "service_name": service_name,
                "event_type": "service_initialization_attempt",
                **attempt_context
            }
        )
    
    def _log_service_initialization_success(self, service_name: str, success_details: Dict[str, Any]):
        """Log successful service initialization with detailed metrics"""
        self.logger.info(
            f"Successfully initialized service '{service_name}' in {success_details['total_initialization_time']:.2f}s",
            extra={
                "service_name": service_name,
                "event_type": "service_initialization_success",
                **success_details
            }
        )
    
    def _log_service_initialization_final_attempt_failed(self, service_name: str, attempt_number: int, last_error: Exception):
        """Log when the final initialization attempt fails"""
        self.logger.error(
            f"Final initialization attempt ({attempt_number}) failed for service '{service_name}': {str(last_error)}",
            extra={
                "service_name": service_name,
                "event_type": "service_initialization_final_attempt_failed",
                "final_attempt_number": attempt_number,
                "last_error_type": type(last_error).__name__,
                "last_error_message": str(last_error)
            }
        )
    
    def _log_service_initialization_complete_failure(self, service_name: str, error_message: str, failure_details: Dict[str, Any]):
        """Log complete service initialization failure with comprehensive details"""
        self.logger.error(
            f"Complete initialization failure for service '{service_name}': {error_message}",
            extra={
                "service_name": service_name,
                "event_type": "service_initialization_complete_failure",
                **failure_details
            }
        )
    
    def _log_service_initialization_fallback_success(self, service_name: str, fallback_details: Dict[str, Any]):
        """Log successful fallback initialization"""
        self.logger.warning(
            f"Service '{service_name}' initialized with fallback after main initialization failed",
            extra={
                "service_name": service_name,
                "event_type": "service_initialization_fallback_success",
                **fallback_details
            }
        )
    
    def _log_service_status_change(self, service_name: str, new_status: ServiceStatus, reason: str):
        """Log service status changes"""
        self.logger.info(
            f"Service '{service_name}' status changed to {new_status.value}: {reason}",
            extra={
                "service_name": service_name,
                "event_type": "service_status_change",
                "new_status": new_status.value,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def _log_service_capabilities(self, service_name: str, service_instance: Any):
        """Log service capabilities if available"""
        try:
            if hasattr(service_instance, 'get_capabilities'):
                capabilities = service_instance.get_capabilities()
                self.logger.debug(
                    f"Service '{service_name}' capabilities retrieved",
                    extra={
                        "service_name": service_name,
                        "event_type": "service_capabilities_logged",
                        "capabilities": capabilities
                    }
                )
        except Exception as e:
            self.logger.debug(
                f"Could not retrieve capabilities for service '{service_name}': {str(e)}",
                extra={
                    "service_name": service_name,
                    "event_type": "service_capabilities_error",
                    "error_message": str(e)
                }
            )
    
    async def _validate_service_dependencies(self, service_name: str, dependencies: List[str]) -> Dict[str, Any]:
        """Enhanced dependency validation with detailed error reporting"""
        validation_result = {
            "valid": True,
            "error_message": "",
            "details": {
                "total_dependencies": len(dependencies),
                "missing_dependencies": [],
                "unhealthy_dependencies": [],
                "healthy_dependencies": [],
                "dependency_status": {}
            }
        }
        
        for dep in dependencies:
            if dep not in self.services:
                validation_result["details"]["missing_dependencies"].append(dep)
                validation_result["details"]["dependency_status"][dep] = "missing"
            elif not self.is_service_healthy(dep):
                validation_result["details"]["unhealthy_dependencies"].append(dep)
                health = self.health_status.get(dep)
                validation_result["details"]["dependency_status"][dep] = {
                    "status": health.status.value if health else "unknown",
                    "error_message": health.error_message if health else "unknown"
                }
            else:
                validation_result["details"]["healthy_dependencies"].append(dep)
                validation_result["details"]["dependency_status"][dep] = "healthy"
        
        if validation_result["details"]["missing_dependencies"] or validation_result["details"]["unhealthy_dependencies"]:
            validation_result["valid"] = False
            missing_deps = validation_result["details"]["missing_dependencies"]
            unhealthy_deps = validation_result["details"]["unhealthy_dependencies"]
            
            error_parts = []
            if missing_deps:
                error_parts.append(f"missing dependencies: {missing_deps}")
            if unhealthy_deps:
                error_parts.append(f"unhealthy dependencies: {unhealthy_deps}")
            
            validation_result["error_message"] = "; ".join(error_parts)
        
        return validation_result
    
    def _validate_service_factory(self, service_name: str, service_factory) -> Dict[str, Any]:
        """Enhanced service factory validation"""
        validation_result = {
            "valid": True,
            "error_message": "",
            "details": {
                "factory_type": type(service_factory).__name__,
                "is_callable": callable(service_factory),
                "is_coroutine_function": asyncio.iscoroutinefunction(service_factory),
                "has_name": hasattr(service_factory, '__name__'),
                "factory_name": getattr(service_factory, '__name__', 'unknown')
            }
        }
        
        if not callable(service_factory):
            validation_result["valid"] = False
            validation_result["error_message"] = f"Service factory for {service_name} is not callable (type: {type(service_factory).__name__})"
        
        return validation_result
    
    async def _create_service_instance_with_error_handling(self, service_name: str, service_factory, attempt_number: int, **kwargs) -> Any:
        """Create service instance with enhanced error handling and logging"""
        creation_start_time = datetime.utcnow()
        
        try:
            self.logger.debug(
                f"Creating service instance for '{service_name}' (attempt {attempt_number})",
                extra={
                    "service_name": service_name,
                    "event_type": "service_instance_creation_start",
                    "attempt_number": attempt_number,
                    "factory_type": type(service_factory).__name__,
                    "kwargs_provided": list(kwargs.keys()) if kwargs else []
                }
            )
            
            # Create service instance with timeout and proper async handling
            service_instance = await asyncio.wait_for(
                self._create_service_instance(service_factory, **kwargs),
                timeout=30.0  # 30 second timeout
            )
            
            creation_time = (datetime.utcnow() - creation_start_time).total_seconds()
            
            self.logger.debug(
                f"Service instance created for '{service_name}' in {creation_time:.2f}s",
                extra={
                    "service_name": service_name,
                    "event_type": "service_instance_creation_success",
                    "attempt_number": attempt_number,
                    "creation_time": creation_time,
                    "instance_type": type(service_instance).__name__ if service_instance else "None"
                }
            )
            
            return service_instance
            
        except asyncio.TimeoutError as e:
            creation_time = (datetime.utcnow() - creation_start_time).total_seconds()
            self.logger.error(
                f"Service instance creation timed out for '{service_name}' after {creation_time:.2f}s",
                extra={
                    "service_name": service_name,
                    "event_type": "service_instance_creation_timeout",
                    "attempt_number": attempt_number,
                    "timeout_duration": 30.0,
                    "creation_time": creation_time
                }
            )
            raise
            
        except Exception as e:
            creation_time = (datetime.utcnow() - creation_start_time).total_seconds()
            self.logger.error(
                f"Service instance creation failed for '{service_name}': {str(e)}",
                extra={
                    "service_name": service_name,
                    "event_type": "service_instance_creation_error",
                    "attempt_number": attempt_number,
                    "creation_time": creation_time,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise
    
    async def _validate_service_instance_with_error_handling(self, service_name: str, service_instance: Any, attempt_number: int) -> Dict[str, Any]:
        """Enhanced service instance validation with detailed error reporting"""
        validation_start_time = datetime.utcnow()
        validation_result = {
            "valid": True,
            "error_message": "",
            "details": {
                "instance_type": type(service_instance).__name__,
                "has_health_check": hasattr(service_instance, 'health_check'),
                "has_get_status": hasattr(service_instance, 'get_status'),
                "validation_checks": [],
                "health_check_result": None,
                "status_check_result": None
            }
        }
        
        try:
            self.logger.debug(
                f"Validating service instance for '{service_name}' (attempt {attempt_number})",
                extra={
                    "service_name": service_name,
                    "event_type": "service_instance_validation_start",
                    "attempt_number": attempt_number,
                    "instance_type": type(service_instance).__name__
                }
            )
            
            # Basic validation
            if service_instance is None:
                validation_result["valid"] = False
                validation_result["error_message"] = "Service instance is None"
                return validation_result
            
            validation_result["details"]["validation_checks"].append("instance_not_none")
            
            # Check for required methods/attributes
            required_methods = ['get_status']
            for method in required_methods:
                if hasattr(service_instance, method):
                    validation_result["details"]["validation_checks"].append(f"has_{method}")
                else:
                    self.logger.warning(
                        f"Service '{service_name}' missing recommended method: {method}",
                        extra={
                            "service_name": service_name,
                            "event_type": "service_validation_warning",
                            "missing_method": method
                        }
                    )
            
            # Perform health check if available
            if hasattr(service_instance, 'health_check'):
                try:
                    health_result = await asyncio.wait_for(
                        service_instance.health_check(),
                        timeout=10.0  # 10 second timeout for health check
                    )
                    validation_result["details"]["health_check_result"] = health_result
                    validation_result["details"]["validation_checks"].append("health_check_passed")
                    
                    self.logger.debug(
                        f"Health check passed for service '{service_name}': {health_result}",
                        extra={
                            "service_name": service_name,
                            "event_type": "service_health_check_success",
                            "health_result": health_result
                        }
                    )
                    
                    # Validate health check response
                    if isinstance(health_result, dict):
                        status = health_result.get('status', 'unknown')
                        if status in ['error', 'failed', 'unhealthy']:
                            validation_result["valid"] = False
                            validation_result["error_message"] = f"Service health check failed: {health_result}"
                            return validation_result
                    
                except asyncio.TimeoutError:
                    self.logger.warning(
                        f"Health check timeout for service '{service_name}'",
                        extra={
                            "service_name": service_name,
                            "event_type": "service_health_check_timeout"
                        }
                    )
                    validation_result["details"]["validation_checks"].append("health_check_timeout")
                    
                except Exception as e:
                    self.logger.warning(
                        f"Health check failed for service '{service_name}': {e}",
                        extra={
                            "service_name": service_name,
                            "event_type": "service_health_check_error",
                            "error_message": str(e)
                        }
                    )
                    validation_result["details"]["validation_checks"].append("health_check_failed")
            
            # Test basic functionality if available
            if hasattr(service_instance, 'get_status'):
                try:
                    status = service_instance.get_status()
                    validation_result["details"]["status_check_result"] = status
                    validation_result["details"]["validation_checks"].append("status_check_passed")
                    
                    self.logger.debug(
                        f"Status check passed for service '{service_name}': {status}",
                        extra={
                            "service_name": service_name,
                            "event_type": "service_status_check_success",
                            "status_result": status
                        }
                    )
                    
                except Exception as e:
                    self.logger.warning(
                        f"Status check failed for service '{service_name}': {e}",
                        extra={
                            "service_name": service_name,
                            "event_type": "service_status_check_error",
                            "error_message": str(e)
                        }
                    )
                    validation_result["details"]["validation_checks"].append("status_check_failed")
            
            validation_time = (datetime.utcnow() - validation_start_time).total_seconds()
            validation_result["details"]["validation_time"] = validation_time
            
            self.logger.debug(
                f"Service instance validation completed for '{service_name}' in {validation_time:.2f}s",
                extra={
                    "service_name": service_name,
                    "event_type": "service_instance_validation_success",
                    "validation_time": validation_time,
                    "validation_checks": validation_result["details"]["validation_checks"]
                }
            )
            
            return validation_result
            
        except Exception as e:
            validation_time = (datetime.utcnow() - validation_start_time).total_seconds()
            validation_result["valid"] = False
            validation_result["error_message"] = f"Service validation failed: {str(e)}"
            validation_result["details"]["validation_time"] = validation_time
            
            self.logger.error(
                f"Service instance validation failed for '{service_name}': {str(e)}",
                extra={
                    "service_name": service_name,
                    "event_type": "service_instance_validation_error",
                    "validation_time": validation_time,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            
            return validation_result
    
    async def _apply_recovery_strategy(self, service_name: str, recovery_strategy: str, dependencies: List[str], 
                                     attempt_number: int, retry_delay: float, last_error: Exception) -> Dict[str, Any]:
        """Apply recovery strategy with detailed logging and error handling"""
        recovery_result = {
            "success": False,
            "strategy_applied": recovery_strategy,
            "next_retry_delay": retry_delay,
            "details": {}
        }
        
        try:
            self.logger.info(
                f"Applying recovery strategy '{recovery_strategy}' for service '{service_name}' after attempt {attempt_number}",
                extra={
                    "service_name": service_name,
                    "event_type": "recovery_strategy_start",
                    "recovery_strategy": recovery_strategy,
                    "attempt_number": attempt_number,
                    "last_error_type": type(last_error).__name__,
                    "retry_delay": retry_delay
                }
            )
            
            if recovery_strategy == "retry":
                self.logger.info(f"Retrying initialization of '{service_name}' in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                # Exponential backoff
                recovery_result["next_retry_delay"] = retry_delay * 1.5
                recovery_result["details"]["backoff_applied"] = True
                
            elif recovery_strategy == "fallback":
                # Try to initialize with fallback/mock service
                fallback_result = await self._try_fallback_initialization_with_error_handling(service_name, dependencies, attempt_number)
                if fallback_result["success"]:
                    recovery_result["success"] = True
                    recovery_result["details"]["fallback_success"] = True
                    recovery_result["details"]["fallback_details"] = fallback_result["details"]
                    return recovery_result
                else:
                    self.logger.info(f"Fallback failed for '{service_name}', retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    recovery_result["details"]["fallback_failed"] = True
                    recovery_result["details"]["fallback_error"] = fallback_result.get("error_message", "unknown")
                    
            else:  # "fail"
                recovery_result["details"]["fail_fast"] = True
                self.logger.info(f"Fail-fast strategy applied for service '{service_name}' - stopping retries")
            
            return recovery_result
            
        except Exception as e:
            self.logger.error(
                f"Error applying recovery strategy '{recovery_strategy}' for service '{service_name}': {str(e)}",
                extra={
                    "service_name": service_name,
                    "event_type": "recovery_strategy_error",
                    "recovery_strategy": recovery_strategy,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            recovery_result["details"]["recovery_error"] = str(e)
            return recovery_result
    
    async def _try_fallback_initialization_with_error_handling(self, service_name: str, dependencies: List[str], attempt_number: int) -> Dict[str, Any]:
        """Try fallback initialization with enhanced error handling and logging"""
        fallback_result = {
            "success": False,
            "error_message": "",
            "details": {
                "attempt_number": attempt_number,
                "fallback_type": "mock_service"
            }
        }
        
        try:
            self.logger.info(
                f"Attempting fallback initialization for service '{service_name}' (attempt {attempt_number})",
                extra={
                    "service_name": service_name,
                    "event_type": "fallback_initialization_start",
                    "attempt_number": attempt_number
                }
            )
            
            # Use the existing fallback method but with enhanced logging
            success = await self._try_fallback_initialization(service_name, dependencies)
            
            if success:
                fallback_result["success"] = True
                fallback_result["details"]["fallback_service_type"] = "mock"
                self.logger.warning(
                    f"Fallback initialization successful for service '{service_name}'",
                    extra={
                        "service_name": service_name,
                        "event_type": "fallback_initialization_success",
                        "attempt_number": attempt_number
                    }
                )
            else:
                fallback_result["error_message"] = "Fallback initialization failed"
                self.logger.error(
                    f"Fallback initialization failed for service '{service_name}'",
                    extra={
                        "service_name": service_name,
                        "event_type": "fallback_initialization_failed",
                        "attempt_number": attempt_number
                    }
                )
            
            return fallback_result
            
        except Exception as e:
            fallback_result["error_message"] = str(e)
            fallback_result["details"]["exception_type"] = type(e).__name__
            
            self.logger.error(
                f"Error during fallback initialization for service '{service_name}': {str(e)}",
                extra={
                    "service_name": service_name,
                    "event_type": "fallback_initialization_error",
                    "attempt_number": attempt_number,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            
            return fallback_result
    
    async def _try_final_fallback_initialization(self, service_name: str, dependencies: List[str], failure_details: Dict[str, Any]) -> Dict[str, Any]:
        """Try final fallback initialization after all regular attempts failed"""
        final_fallback_result = {
            "success": False,
            "details": {
                "final_fallback_attempt": True,
                "previous_failure_details": failure_details
            }
        }
        
        try:
            self.logger.warning(
                f"Attempting final fallback initialization for service '{service_name}' after complete failure",
                extra={
                    "service_name": service_name,
                    "event_type": "final_fallback_initialization_start",
                    "previous_attempts": failure_details.get("total_attempts", 0)
                }
            )
            
            success = await self._try_fallback_initialization(service_name, dependencies)
            
            if success:
                final_fallback_result["success"] = True
                final_fallback_result["details"]["fallback_service_type"] = "mock"
                
                # Update the service status to degraded since it's using fallback
                if service_name in self.health_status:
                    self.health_status[service_name].status = ServiceStatus.DEGRADED
                    self.health_status[service_name].error_message = "Using fallback/mock service after initialization failure"
                
                self.logger.warning(
                    f"Final fallback initialization successful for service '{service_name}' - service running in degraded mode",
                    extra={
                        "service_name": service_name,
                        "event_type": "final_fallback_initialization_success",
                        "service_status": "degraded"
                    }
                )
            else:
                final_fallback_result["details"]["final_fallback_failed"] = True
                self.logger.error(
                    f"Final fallback initialization failed for service '{service_name}' - service completely unavailable",
                    extra={
                        "service_name": service_name,
                        "event_type": "final_fallback_initialization_failed"
                    }
                )
            
            return final_fallback_result
            
        except Exception as e:
            final_fallback_result["details"]["final_fallback_error"] = str(e)
            
            self.logger.error(
                f"Error during final fallback initialization for service '{service_name}': {str(e)}",
                extra={
                    "service_name": service_name,
                    "event_type": "final_fallback_initialization_error",
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            
            return final_fallback_result

    async def _create_service_instance(self, service_factory, **kwargs) -> Any:
        """
        Create service instance with proper async handling
        
        Args:
            service_factory: Factory function to create the service
            **kwargs: Additional arguments for service creation
            
        Returns:
            Service instance
        """
        try:
            # Handle both sync and async factory functions
            if asyncio.iscoroutinefunction(service_factory):
                return await service_factory(**kwargs)
            else:
                # Run sync factory in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, lambda: service_factory(**kwargs))
        except Exception as e:
            self.logger.error(f"Error in service factory: {str(e)}", exc_info=True)
            raise
    
    async def _validate_service_instance(self, service_name: str, service_instance: Any) -> None:
        """
        Validate service instance after creation
        
        Args:
            service_name: Name of the service
            service_instance: Service instance to validate
        """
        try:
            # Basic validation
            if service_instance is None:
                raise ValueError("Service instance is None")
            
            # Check for required methods/attributes
            required_methods = ['get_status']  # Minimum required method
            for method in required_methods:
                if not hasattr(service_instance, method):
                    self.logger.warning(f"Service {service_name} missing recommended method: {method}")
            
            # Perform health check if available
            if hasattr(service_instance, 'health_check'):
                try:
                    health_result = await asyncio.wait_for(
                        service_instance.health_check(),
                        timeout=10.0  # 10 second timeout for health check
                    )
                    self.logger.debug(f"Health check for {service_name}: {health_result}")
                    
                    # Validate health check response
                    if isinstance(health_result, dict):
                        status = health_result.get('status', 'unknown')
                        if status in ['error', 'failed', 'unhealthy']:
                            raise RuntimeError(f"Service {service_name} health check failed: {health_result}")
                    
                except asyncio.TimeoutError:
                    self.logger.warning(f"Health check timeout for {service_name}")
                except Exception as e:
                    self.logger.warning(f"Health check failed for {service_name}: {e}")
                    # Don't fail initialization for health check failures
            
            # Test basic functionality if available
            if hasattr(service_instance, 'get_status'):
                try:
                    status = service_instance.get_status()
                    self.logger.debug(f"Status for {service_name}: {status}")
                except Exception as e:
                    self.logger.warning(f"Status check failed for {service_name}: {e}")
            
        except Exception as e:
            self.logger.error(f"Service validation failed for {service_name}: {str(e)}")
            raise
    
    async def _try_fallback_initialization(self, service_name: str, dependencies: List[str]) -> bool:
        """
        Try to initialize service with fallback/mock implementation
        
        Args:
            service_name: Name of the service
            dependencies: Service dependencies
            
        Returns:
            bool: True if fallback initialization successful
        """
        try:
            self.logger.info(f"Attempting fallback initialization for {service_name}")
            
            # Map service names to their mock classes
            mock_services = {
                "semantic_search": MockSemanticSearchService,
                "research_automation": MockResearchAutomationService,
                "advanced_analytics": MockAdvancedAnalyticsService,
                "knowledge_graph": MockKnowledgeGraphService
            }
            
            if service_name in mock_services:
                mock_class = mock_services[service_name]
                
                def create_mock_service():
                    return mock_class()
                
                # Store the mock service directly (avoid recursion)
                mock_instance = create_mock_service()
                self.services[service_name] = mock_instance
                self.initialization_order.append(service_name)
                
                # Update health status
                self.health_status[service_name] = ServiceHealth(
                    name=service_name,
                    status=ServiceStatus.DEGRADED,  # Mark as degraded since it's a mock
                    last_check=datetime.utcnow(),
                    error_message="Using mock/fallback service",
                    dependencies=[]  # Mock services have no dependencies
                )
                
                self.logger.warning(f"Initialized {service_name} with mock/fallback service")
                return True
            else:
                self.logger.warning(f"No fallback available for service {service_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Fallback initialization failed for {service_name}: {str(e)}")
            return False

    def get_service(self, service_name: str) -> Optional[Any]:
        """
        Get a service instance by name
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service instance or None if not available
        """
        return self.services.get(service_name)
    
    def is_service_healthy(self, service_name: str) -> bool:
        """
        Check if a service is healthy
        
        Args:
            service_name: Name of the service
            
        Returns:
            bool: True if service is healthy, False otherwise
        """
        health = self.health_status.get(service_name)
        return health is not None and health.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]
    
    def _create_service_health(self, service_name: str, status: ServiceStatus, error_message: str = None) -> ServiceHealth:
        """
        Create a ServiceHealth instance
        
        Args:
            service_name: Name of the service
            status: Service status
            error_message: Optional error message
            
        Returns:
            ServiceHealth instance
        """
        return ServiceHealth(
            name=service_name,
            status=status,
            last_check=datetime.utcnow(),
            error_message=error_message
        )
    
    async def check_service_health(self, service_name: str, use_cache: bool = True) -> ServiceHealth:
        """
        Perform a health check on a specific service with caching support
        
        Args:
            service_name: Name of the service
            use_cache: Whether to use cached results if available
            
        Returns:
            ServiceHealth: Current health status of the service
        """
        # Check cache first if enabled
        if use_cache:
            cached_health = self._get_cached_health(service_name)
            if cached_health:
                self.logger.debug(f"Using cached health status for {service_name}")
                return cached_health
        
        # Perform actual health check
        return await self._perform_health_check(service_name, cache_result=True)
    
    async def check_all_services_health(self, use_cache: bool = True) -> Dict[str, ServiceHealth]:
        """
        Perform health checks on all services with caching support
        
        Args:
            use_cache: Whether to use cached results if available
        
        Returns:
            Dict[str, ServiceHealth]: Health status of all services
        """
        health_results = {}
        
        for service_name in self.services.keys():
            health_results[service_name] = await self.check_service_health(service_name, use_cache=use_cache)
        
        return health_results
    
    def get_service_health(self, service_name: str = None) -> Dict[str, Any]:
        """
        Get health status of services
        
        Args:
            service_name: Optional specific service name
            
        Returns:
            Dict containing health information
        """
        if service_name:
            health = self.health_status.get(service_name)
            if health:
                return {
                    "name": health.name,
                    "status": health.status.value,
                    "last_check": health.last_check.isoformat(),
                    "error_message": health.error_message,
                    "dependencies": health.dependencies,
                    "initialization_time": health.initialization_time
                }
            return {"error": f"Service {service_name} not found"}
        
        # Return all services health
        result = {}
        for name, health in self.health_status.items():
            result[name] = {
                "status": health.status.value,
                "last_check": health.last_check.isoformat(),
                "error_message": health.error_message,
                "dependencies": health.dependencies,
                "initialization_time": health.initialization_time
            }
        
        return result
    
    async def shutdown_service(self, service_name: str) -> bool:
        """
        Shutdown a specific service
        
        Args:
            service_name: Name of the service to shutdown
            
        Returns:
            True if shutdown successful, False otherwise
        """
        try:
            if service_name not in self.services:
                self.logger.warning(f"Service {service_name} not found for shutdown")
                return False
            
            service = self.services[service_name]
            
            # Call shutdown method if available
            if hasattr(service, 'shutdown') and callable(getattr(service, 'shutdown')):
                if asyncio.iscoroutinefunction(service.shutdown):
                    await service.shutdown()
                else:
                    service.shutdown()
            
            # Remove from services and health status
            del self.services[service_name]
            if service_name in self.health_status:
                del self.health_status[service_name]
            
            self.logger.info(f"Service {service_name} shutdown successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error shutting down service {service_name}: {str(e)}")
            return False
    
    async def shutdown_all_services(self) -> bool:
        """
        Shutdown all services
        
        Returns:
            True if all services shutdown successfully, False otherwise
        """
        try:
            service_names = list(self.services.keys())
            success = True
            
            for service_name in service_names:
                result = await self.shutdown_service(service_name)
                if not result:
                    success = False
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error shutting down all services: {str(e)}")
            return False
    
    def list_services(self) -> list:
        """
        Get list of all service names
        
        Returns:
            List of service names
        """
        return list(self.services.keys())
    
    def get_initialization_order(self) -> list:
        """
        Get the order in which services were initialized
        
        Returns:
            List of service names in initialization order
        """
        return self.initialization_order.copy()
    
    def _validate_dependencies(self, dependencies: list) -> bool:
        """
        Validate that all dependencies exist
        
        Args:
            dependencies: List of dependency service names
            
        Returns:
            True if all dependencies exist, False otherwise
        """
        if not dependencies:
            return True
        
        for dep in dependencies:
            if dep not in self.services:
                return False
        
        return True
    
    def _resolve_initialization_order(self, service_definitions: dict) -> list:
        """
        Resolve service initialization order based on dependencies
        
        Args:
            service_definitions: Dict mapping service names to their dependencies
            
        Returns:
            List of service names in initialization order
            
        Raises:
            ValueError: If circular dependencies or missing dependencies are detected
        """
        # Simple topological sort implementation
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(service_name):
            if service_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {service_name}")
            
            if service_name in visited:
                return
            
            if service_name not in service_definitions:
                raise ValueError(f"Missing dependency: {service_name}")
            
            if service_name == service_definitions[service_name]:
                raise ValueError(f"Self-dependency detected: {service_name}")
            
            temp_visited.add(service_name)
            
            for dep in service_definitions[service_name]:
                visit(dep)
            
            temp_visited.remove(service_name)
            visited.add(service_name)
            order.append(service_name)
        
        for service_name in service_definitions:
            if service_name not in visited:
                visit(service_name)
        
        return order
    
    async def initialize_services_batch(self, service_definitions: dict, service_instances: dict) -> dict:
        """
        Initialize multiple services in batch with proper dependency ordering
        
        Args:
            service_definitions: Dict mapping service names to their dependencies
            service_instances: Dict mapping service names to their instances
            
        Returns:
            Dict mapping service names to initialization results
        """
        try:
            # Resolve initialization order
            order = self._resolve_initialization_order(service_definitions)
            
            results = {}
            
            for service_name in order:
                if service_name in service_instances:
                    result = await self.initialize_service(
                        service_name,
                        lambda svc=service_instances[service_name]: svc,
                        service_definitions[service_name]
                    )
                    results[service_name] = result
                else:
                    results[service_name] = False
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in batch service initialization: {str(e)}")
            return {name: False for name in service_definitions.keys()}
    
    def get_initialization_summary(self) -> Dict[str, Any]:
        """
        Get summary of service initialization
        
        Returns:
            Dict containing initialization summary
        """
        total_services = len(self.health_status)
        healthy_services = sum(1 for h in self.health_status.values() 
                             if h.status == ServiceStatus.HEALTHY)
        failed_services = sum(1 for h in self.health_status.values() 
                            if h.status == ServiceStatus.FAILED)
        
        return {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "failed_services": failed_services,
            "initialization_order": self.initialization_order,
            "overall_health": "healthy" if failed_services == 0 else "degraded",
            "monitoring_enabled": self.monitoring_enabled,
            "health_check_interval": self.health_check_interval
        }
    
    async def start_health_monitoring(self):
        """
        Start periodic health monitoring for all services
        """
        if self.monitoring_task and not self.monitoring_task.done():
            self.logger.warning("Health monitoring already running")
            return
        
        if not self.monitoring_enabled:
            self.logger.info("Health monitoring is disabled")
            return
        
        self.logger.info(f"Starting health monitoring with {self.health_check_interval}s interval")
        self.monitoring_task = asyncio.create_task(self._health_monitoring_loop())
    
    async def stop_health_monitoring(self):
        """
        Stop periodic health monitoring
        """
        if self.monitoring_task and not self.monitoring_task.done():
            self.logger.info("Stopping health monitoring")
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
    
    async def _health_monitoring_loop(self):
        """
        Internal loop for periodic health monitoring
        """
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                if not self.monitoring_enabled:
                    break
                
                self.logger.debug("Performing periodic health checks")
                
                # Perform health checks on all services
                for service_name in list(self.services.keys()):
                    try:
                        await self._perform_health_check(service_name, cache_result=True)
                    except Exception as e:
                        self.logger.error(f"Error during periodic health check for {service_name}: {e}")
                
                self.logger.debug("Completed periodic health checks")
                
            except asyncio.CancelledError:
                self.logger.info("Health monitoring loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}", exc_info=True)
                # Continue monitoring despite errors
                await asyncio.sleep(10)  # Short delay before retrying
    
    def _is_health_cache_valid(self, service_name: str) -> bool:
        """
        Check if cached health status is still valid
        
        Args:
            service_name: Name of the service
            
        Returns:
            bool: True if cache is valid, False otherwise
        """
        if service_name not in self.health_cache:
            return False
        
        _, cache_time = self.health_cache[service_name]
        return (datetime.utcnow() - cache_time).total_seconds() < self.health_cache_ttl
    
    def _get_cached_health(self, service_name: str) -> Optional[ServiceHealth]:
        """
        Get cached health status if valid
        
        Args:
            service_name: Name of the service
            
        Returns:
            ServiceHealth or None if cache is invalid
        """
        if self._is_health_cache_valid(service_name):
            health, _ = self.health_cache[service_name]
            return health
        return None
    
    def _cache_health_result(self, service_name: str, health: ServiceHealth):
        """
        Cache health check result
        
        Args:
            service_name: Name of the service
            health: Health status to cache
        """
        self.health_cache[service_name] = (health, datetime.utcnow())
    
    async def _perform_health_check(self, service_name: str, cache_result: bool = False) -> ServiceHealth:
        """
        Perform actual health check on a service
        
        Args:
            service_name: Name of the service
            cache_result: Whether to cache the result
            
        Returns:
            ServiceHealth: Current health status
        """
        if service_name not in self.services:
            health = ServiceHealth(
                name=service_name,
                status=ServiceStatus.FAILED,
                last_check=datetime.utcnow(),
                error_message="Service not found"
            )
            if cache_result:
                self._cache_health_result(service_name, health)
            return health
        
        service = self.services[service_name]
        current_time = datetime.utcnow()
        
        try:
            # Try to call a health check method if available
            if hasattr(service, 'health_check'):
                if asyncio.iscoroutinefunction(service.health_check):
                    await service.health_check()
                else:
                    service.health_check()
            
            # Update health status
            health = ServiceHealth(
                name=service_name,
                status=ServiceStatus.HEALTHY,
                last_check=current_time,
                error_message=None,
                dependencies=self.health_status.get(service_name, ServiceHealth(
                    name=service_name, status=ServiceStatus.HEALTHY, last_check=current_time
                )).dependencies,
                initialization_time=self.health_status.get(service_name, ServiceHealth(
                    name=service_name, status=ServiceStatus.HEALTHY, last_check=current_time
                )).initialization_time
            )
            
            # Update stored health status
            self.health_status[service_name] = health
            
        except Exception as e:
            error_msg = f"Health check failed for {service_name}: {str(e)}"
            self.logger.warning(error_msg)
            
            health = ServiceHealth(
                name=service_name,
                status=ServiceStatus.DEGRADED,
                last_check=current_time,
                error_message=error_msg,
                dependencies=self.health_status.get(service_name, ServiceHealth(
                    name=service_name, status=ServiceStatus.DEGRADED, last_check=current_time
                )).dependencies,
                initialization_time=self.health_status.get(service_name, ServiceHealth(
                    name=service_name, status=ServiceStatus.DEGRADED, last_check=current_time
                )).initialization_time
            )
            
            # Update stored health status
            self.health_status[service_name] = health
        
        if cache_result:
            self._cache_health_result(service_name, health)
        
        return health
    
    def configure_health_monitoring(
        self, 
        interval: int = None, 
        cache_ttl: int = None, 
        enabled: bool = None
    ):
        """
        Configure health monitoring parameters
        
        Args:
            interval: Health check interval in seconds
            cache_ttl: Cache TTL in seconds
            enabled: Whether monitoring is enabled
        """
        if interval is not None:
            self.health_check_interval = interval
            self.logger.info(f"Health check interval set to {interval}s")
        
        if cache_ttl is not None:
            self.health_cache_ttl = cache_ttl
            self.logger.info(f"Health cache TTL set to {cache_ttl}s")
        
        if enabled is not None:
            self.monitoring_enabled = enabled
            self.logger.info(f"Health monitoring {'enabled' if enabled else 'disabled'}")
    
    def get_health_monitoring_status(self) -> Dict[str, Any]:
        """
        Get current health monitoring configuration and status
        
        Returns:
            Dict containing monitoring status information
        """
        return {
            "monitoring_enabled": self.monitoring_enabled,
            "health_check_interval": self.health_check_interval,
            "cache_ttl": self.health_cache_ttl,
            "monitoring_active": self.monitoring_task is not None and not self.monitoring_task.done(),
            "cached_services": list(self.health_cache.keys()),
            "cache_stats": {
                service_name: {
                    "cached_at": cache_time.isoformat(),
                    "age_seconds": (datetime.utcnow() - cache_time).total_seconds(),
                    "valid": self._is_health_cache_valid(service_name)
                }
                for service_name, (_, cache_time) in self.health_cache.items()
            }
        }


# Global service manager instance
service_manager = ServiceManager()