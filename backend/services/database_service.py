"""
Database Service with safe imports and health monitoring
"""
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from core.conditional_importer import ConditionalImporter

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Database service with safe imports and health monitoring
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.DatabaseService")
        self.is_initialized = False
        self.connection_pool = None
        self.engine = None
        self.SessionLocal = None
        self.Base = None
        self.models = {}
        self.last_health_check = None
        self.health_status = "unknown"
        self.error_message = None
        
        # Import database components safely
        self._import_database_components()
    
    def _import_database_components(self):
        """
        Safely import database components with fallbacks
        """
        try:
            # Import core database components
            self.logger.info("Importing database components...")
            
            # First check if SQLAlchemy is available
            sqlalchemy_module = ConditionalImporter.safe_import("sqlalchemy", fallback=None)
            if not sqlalchemy_module:
                self.logger.warning("SQLAlchemy not available, database service will be limited")
                self.error_message = "SQLAlchemy not installed"
                return
            
            # Import database engine and session
            database_module = ConditionalImporter.safe_import(
                "core.database",
                fallback=None
            )
            
            if database_module:
                self.engine = getattr(database_module, 'engine', None)
                self.SessionLocal = getattr(database_module, 'SessionLocal', None)
                self.Base = getattr(database_module, 'Base', None)
                
                if self.engine and self.SessionLocal and self.Base:
                    self.logger.info("Successfully imported database components")
                else:
                    self.logger.warning("Some database components are missing")
            else:
                self.logger.warning("Failed to import core.database module")
            
            # Import database models
            self._import_database_models()
            
        except Exception as e:
            self.logger.error(f"Error importing database components: {e}", exc_info=True)
            self.error_message = f"Database import error: {str(e)}"
    
    def _import_database_models(self):
        """
        Safely import database models from core.database and Pydantic schemas from models.schemas
        """
        try:
            # Import SQLAlchemy model classes from core.database
            sqlalchemy_model_names = [
                'User', 'Document', 'Conversation', 'Message', 'DocumentChunk',
                'UserProfile', 'DocumentChunkEnhanced', 'KnowledgeGraphEntity',
                'KnowledgeGraphRelationship', 'ConversationMemory', 'UserFeedback',
                'AnalyticsEvent', 'DocumentTag', 'Quiz', 'QuizQuestion',
                'QuizAttempt', 'QuizResponse', 'StudySession', 'LearningProgress',
                'SpacedRepetitionItem', 'Achievement', 'Institution',
                'InstitutionalPolicy', 'ComplianceViolation', 'UserRole',
                'ResourceUsage', 'StudentProgress', 'AdvisorFeedback', 'AuditLog'
            ]
            
            for model_name in sqlalchemy_model_names:
                model_class = ConditionalImporter.safe_import(
                    "core.database",
                    attribute=model_name,
                    fallback=None
                )
                
                if model_class:
                    self.models[f"db_{model_name}"] = model_class
                    self.logger.debug(f"Successfully imported SQLAlchemy model: {model_name}")
                else:
                    self.logger.debug(f"Failed to import SQLAlchemy model: {model_name}")
            
            # Import Pydantic schema classes from models.schemas
            pydantic_schema_names = [
                'UserProfileCreate', 'UserProfileResponse', 'UserPreferences',
                'ConversationMemoryCreate', 'ConversationMemoryResponse',
                'KnowledgeGraphEntityCreate', 'KnowledgeGraphEntityResponse',
                'KnowledgeGraphRelationshipCreate', 'KnowledgeGraphRelationshipResponse',
                'UserFeedbackCreate', 'UserFeedbackResponse',
                'AnalyticsEventCreate', 'AnalyticsEventResponse',
                'DocumentProcessingRequest', 'DocumentProcessingResponse',
                'SearchRequest', 'SearchResponse',
                'CitationRequest', 'CitationResponse',
                'ExportRequest', 'ExportResponse',
                'User', 'UserCreate', 'UserResponse',
                'PersonalizationSettings', 'DocumentResponse', 'Source',
                'ChatResponse', 'ChatRequest', 'EnhancedChatRequest', 'EnhancedChatResponse',
                'ReasoningResult', 'UncertaintyScore',
                'DocumentTagCreate', 'DocumentTagResponse',
                'AnalyticsQuery', 'AnalyticsResponse',
                'KnowledgeGraphQuery', 'DocumentComparisonRequest', 'DocumentComparisonResponse',
                'ServiceHealthResponse', 'DetailedHealthCheckResponse',
                'ServicesHealthCheckResponse', 'ServiceHealthCheckResponse'
            ]
            
            for schema_name in pydantic_schema_names:
                schema_class = ConditionalImporter.safe_import(
                    "models.schemas",
                    attribute=schema_name,
                    fallback=None
                )
                
                if schema_class:
                    self.models[f"schema_{schema_name}"] = schema_class
                    self.logger.debug(f"Successfully imported Pydantic schema: {schema_name}")
                else:
                    self.logger.debug(f"Failed to import Pydantic schema: {schema_name}")
            
            # Import enums from models.schemas
            enum_names = [
                'EntityType', 'RelationshipType', 'MemoryType', 'FeedbackType',
                'TagType', 'ReasoningType', 'ChunkingStrategy', 'CitationMode',
                'ServiceStatus'
            ]
            
            for enum_name in enum_names:
                enum_class = ConditionalImporter.safe_import(
                    "models.schemas",
                    attribute=enum_name,
                    fallback=None
                )
                
                if enum_class:
                    self.models[f"enum_{enum_name}"] = enum_class
                    self.logger.debug(f"Successfully imported enum: {enum_name}")
                else:
                    self.logger.debug(f"Failed to import enum: {enum_name}")
            
            self.logger.info(f"Successfully imported {len(self.models)} database models and schemas")
            
        except Exception as e:
            self.logger.error(f"Error importing database models and schemas: {e}", exc_info=True)
    
    async def initialize(self) -> bool:
        """
        Initialize the database service with comprehensive error handling
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing database service...")
            
            # Check if database components are available
            if not self.engine or not self.SessionLocal:
                self.error_message = "Database components not available - check SQLAlchemy installation and database configuration"
                self.logger.error(self.error_message)
                self.health_status = "failed"
                return False
            
            # Test database connection with retry logic
            connection_attempts = 3
            connection_test = False
            
            for attempt in range(connection_attempts):
                self.logger.info(f"Database connection attempt {attempt + 1}/{connection_attempts}")
                connection_test = await self._test_connection()
                
                if connection_test:
                    break
                elif attempt < connection_attempts - 1:
                    self.logger.warning(f"Connection attempt {attempt + 1} failed, retrying in 2 seconds...")
                    await asyncio.sleep(2)
            
            if not connection_test:
                self.error_message = f"Database connection failed after {connection_attempts} attempts"
                self.logger.error(self.error_message)
                self.health_status = "failed"
                return False
            
            # Initialize database tables if needed
            try:
                await self._initialize_tables()
                self.logger.info("Database tables initialized successfully")
            except Exception as table_error:
                self.error_message = f"Database table initialization failed: {str(table_error)}"
                self.logger.error(self.error_message, exc_info=True)
                self.health_status = "degraded"
                # Continue with degraded status rather than failing completely
            
            # Verify model imports
            sqlalchemy_models = len(self.get_available_sqlalchemy_models())
            pydantic_schemas = len(self.get_available_pydantic_schemas())
            enums = len(self.get_available_enums())
            
            self.logger.info(f"Database service initialized with {sqlalchemy_models} SQLAlchemy models, "
                           f"{pydantic_schemas} Pydantic schemas, and {enums} enums")
            
            self.is_initialized = True
            if self.health_status != "degraded":
                self.health_status = "healthy"
            self.logger.info("Database service initialization completed")
            return True
            
        except Exception as e:
            self.error_message = f"Database initialization failed: {str(e)}"
            self.logger.error(self.error_message, exc_info=True)
            self.health_status = "failed"
            return False
    
    async def _test_connection(self) -> bool:
        """
        Test database connection with comprehensive error handling
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.logger.debug("Testing database connection...")
            
            if not self.engine:
                self.error_message = "No database engine available"
                self.logger.error(self.error_message)
                return False
            
            # Import SQLAlchemy text function safely
            text_func = ConditionalImporter.safe_import("sqlalchemy", attribute="text", fallback=None)
            if not text_func:
                self.error_message = "SQLAlchemy text function not available"
                self.logger.error(self.error_message)
                return False
            
            # Use asyncio to run the synchronous database operation with timeout
            def test_sync_connection():
                try:
                    with self.engine.connect() as connection:
                        result = connection.execute(text_func("SELECT 1"))
                        return result.fetchone() is not None
                except Exception as e:
                    self.logger.error(f"Database connection error in sync operation: {e}")
                    raise
            
            # Run in thread pool to avoid blocking with timeout
            loop = asyncio.get_event_loop()
            try:
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, test_sync_connection),
                    timeout=10.0  # 10 second timeout
                )
                
                if result:
                    self.logger.debug("Database connection test successful")
                    self.error_message = None
                    return True
                else:
                    self.error_message = "Database connection test returned no result"
                    self.logger.error(self.error_message)
                    return False
                    
            except asyncio.TimeoutError:
                self.error_message = "Database connection test timed out"
                self.logger.error(self.error_message)
                return False
                
        except Exception as e:
            self.error_message = f"Database connection test error: {str(e)}"
            self.logger.error(self.error_message, exc_info=True)
            return False
    
    async def _initialize_tables(self):
        """
        Initialize database tables if they don't exist
        """
        try:
            if self.Base:
                self.logger.debug("Creating database tables if they don't exist...")
                
                def create_tables():
                    self.Base.metadata.create_all(bind=self.engine)
                
                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, create_tables)
                
                self.logger.info("Database tables initialized")
            else:
                self.logger.warning("Base class not available, skipping table creation")
                
        except Exception as e:
            self.logger.error(f"Error initializing database tables: {e}", exc_info=True)
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """
        Get database session with proper cleanup
        
        Yields:
            Database session
        """
        if not self.is_initialized or not self.SessionLocal:
            raise RuntimeError("Database service not initialized")
        
        session = None
        try:
            def create_session():
                return self.SessionLocal()
            
            # Create session in thread pool
            loop = asyncio.get_event_loop()
            session = await loop.run_in_executor(None, create_session)
            
            yield session
            
        except Exception as e:
            if session:
                def rollback_session():
                    session.rollback()
                
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, rollback_session)
            raise e
        finally:
            if session:
                def close_session():
                    session.close()
                
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, close_session)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check including model and schema validation
        
        Returns:
            Dict containing health check results
        """
        self.last_health_check = datetime.utcnow()
        
        health_info = {
            "service": "database",
            "status": "unknown",
            "timestamp": self.last_health_check.isoformat(),
            "details": {}
        }
        
        try:
            # Check if service is initialized
            if not self.is_initialized:
                health_info["status"] = "unhealthy"
                health_info["details"]["error"] = "Service not initialized"
                health_info["details"]["error_message"] = self.error_message
                return health_info
            
            # Test database connection
            connection_test = await self._test_connection()
            health_info["details"]["connection"] = "healthy" if connection_test else "failed"
            
            if not connection_test:
                health_info["status"] = "unhealthy"
                health_info["details"]["error"] = "Database connection failed"
                health_info["details"]["error_message"] = self.error_message
                self.health_status = "unhealthy"
                return health_info
            
            # Check database tables
            tables_info = await self._check_database_tables()
            health_info["details"]["tables"] = tables_info
            
            # Check database performance
            performance_info = await self._check_database_performance()
            health_info["details"]["performance"] = performance_info
            
            # Check model and schema imports
            models_info = self._check_models_and_schemas()
            health_info["details"]["models"] = models_info
            
            # Check database configuration
            config_info = self._check_database_configuration()
            health_info["details"]["configuration"] = config_info
            
            # Overall health status
            connection_healthy = connection_test
            tables_healthy = tables_info.get("status") == "healthy"
            models_healthy = models_info.get("status") == "healthy"
            
            if connection_healthy and tables_healthy and models_healthy:
                health_info["status"] = "healthy"
                self.health_status = "healthy"
                self.error_message = None
            elif connection_healthy and (tables_healthy or models_healthy):
                health_info["status"] = "degraded"
                self.health_status = "degraded"
            else:
                health_info["status"] = "unhealthy"
                self.health_status = "unhealthy"
            
        except Exception as e:
            health_info["status"] = "unhealthy"
            health_info["details"]["error"] = str(e)
            self.health_status = "unhealthy"
            self.error_message = str(e)
            self.logger.error(f"Database health check failed: {e}", exc_info=True)
        
        return health_info
    
    async def _check_database_tables(self) -> Dict[str, Any]:
        """
        Check database tables status
        
        Returns:
            Dict containing table status information
        """
        try:
            if not self.engine:
                return {"status": "failed", "error": "No database engine"}
            
            def check_tables():
                inspect_func = ConditionalImporter.safe_import("sqlalchemy", attribute="inspect", fallback=None)
                if not inspect_func:
                    raise Exception("SQLAlchemy inspect function not available")
                inspector = inspect_func(self.engine)
                table_names = inspector.get_table_names()
                return table_names
            
            loop = asyncio.get_event_loop()
            table_names = await loop.run_in_executor(None, check_tables)
            
            return {
                "status": "healthy",
                "table_count": len(table_names),
                "tables": table_names[:10]  # Limit to first 10 for brevity
            }
            
        except Exception as e:
            self.logger.error(f"Error checking database tables: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _check_database_performance(self) -> Dict[str, Any]:
        """
        Check basic database performance metrics
        
        Returns:
            Dict containing performance information
        """
        try:
            start_time = datetime.utcnow()
            
            # Simple performance test
            def performance_test():
                text_func = ConditionalImporter.safe_import("sqlalchemy", attribute="text", fallback=None)
                if not text_func:
                    raise Exception("SQLAlchemy text function not available")
                with self.engine.connect() as connection:
                    result = connection.execute(text_func("SELECT 1"))
                    return result.fetchone()
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, performance_test)
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000  # ms
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "connection_pool_size": getattr(self.engine.pool, 'size', 'unknown') if self.engine else 'unknown'
            }
            
        except Exception as e:
            self.logger.error(f"Error checking database performance: {e}")
            return {"status": "failed", "error": str(e)}
    
    def get_model(self, model_name: str):
        """
        Get a database model by name
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model class or None if not available
        """
        return self.models.get(model_name)
    
    def get_sqlalchemy_model(self, model_name: str):
        """
        Get a SQLAlchemy database model by name
        
        Args:
            model_name: Name of the model (without db_ prefix)
            
        Returns:
            SQLAlchemy model class or None if not available
        """
        return self.models.get(f"db_{model_name}")
    
    def get_pydantic_schema(self, schema_name: str):
        """
        Get a Pydantic schema by name
        
        Args:
            schema_name: Name of the schema (without schema_ prefix)
            
        Returns:
            Pydantic schema class or None if not available
        """
        return self.models.get(f"schema_{schema_name}")
    
    def get_enum(self, enum_name: str):
        """
        Get an enum by name
        
        Args:
            enum_name: Name of the enum (without enum_ prefix)
            
        Returns:
            Enum class or None if not available
        """
        return self.models.get(f"enum_{enum_name}")
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available database models
        
        Returns:
            List of model names
        """
        return list(self.models.keys())
    
    def get_available_sqlalchemy_models(self) -> List[str]:
        """
        Get list of available SQLAlchemy models
        
        Returns:
            List of SQLAlchemy model names
        """
        return [key[3:] for key in self.models.keys() if key.startswith("db_")]
    
    def get_available_pydantic_schemas(self) -> List[str]:
        """
        Get list of available Pydantic schemas
        
        Returns:
            List of Pydantic schema names
        """
        return [key[7:] for key in self.models.keys() if key.startswith("schema_")]
    
    def get_available_enums(self) -> List[str]:
        """
        Get list of available enums
        
        Returns:
            List of enum names
        """
        return [key[5:] for key in self.models.keys() if key.startswith("enum_")]
    
    def is_healthy(self) -> bool:
        """
        Check if database service is healthy
        
        Returns:
            bool: True if healthy, False otherwise
        """
        return self.health_status == "healthy" and self.is_initialized
    
    def _check_models_and_schemas(self) -> Dict[str, Any]:
        """
        Check the status of imported models and schemas
        
        Returns:
            Dict containing model and schema status information
        """
        try:
            sqlalchemy_models = self.get_available_sqlalchemy_models()
            pydantic_schemas = self.get_available_pydantic_schemas()
            enums = self.get_available_enums()
            
            # Expected minimum counts for healthy status
            min_sqlalchemy_models = 10
            min_pydantic_schemas = 5
            min_enums = 3
            
            status = "healthy"
            issues = []
            
            if len(sqlalchemy_models) < min_sqlalchemy_models:
                status = "degraded"
                issues.append(f"Only {len(sqlalchemy_models)} SQLAlchemy models imported (expected at least {min_sqlalchemy_models})")
            
            if len(pydantic_schemas) < min_pydantic_schemas:
                status = "degraded"
                issues.append(f"Only {len(pydantic_schemas)} Pydantic schemas imported (expected at least {min_pydantic_schemas})")
            
            if len(enums) < min_enums:
                status = "degraded"
                issues.append(f"Only {len(enums)} enums imported (expected at least {min_enums})")
            
            return {
                "status": status,
                "sqlalchemy_models_count": len(sqlalchemy_models),
                "pydantic_schemas_count": len(pydantic_schemas),
                "enums_count": len(enums),
                "total_imports": len(self.models),
                "issues": issues,
                "sample_models": sqlalchemy_models[:5],
                "sample_schemas": pydantic_schemas[:5],
                "sample_enums": enums[:3]
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "total_imports": len(self.models)
            }
    
    def _check_database_configuration(self) -> Dict[str, Any]:
        """
        Check database configuration status
        
        Returns:
            Dict containing configuration status information
        """
        try:
            config_info = {
                "status": "healthy",
                "engine_available": self.engine is not None,
                "session_factory_available": self.SessionLocal is not None,
                "base_available": self.Base is not None,
                "issues": []
            }
            
            if not self.engine:
                config_info["status"] = "failed"
                config_info["issues"].append("Database engine not available")
            
            if not self.SessionLocal:
                config_info["status"] = "failed"
                config_info["issues"].append("Session factory not available")
            
            if not self.Base:
                config_info["status"] = "degraded"
                config_info["issues"].append("Base class not available")
            
            # Add database URL info (without sensitive details)
            try:
                from core.config import settings
                db_url = settings.DATABASE_URL
                if db_url:
                    # Extract database type without exposing credentials
                    db_type = db_url.split("://")[0] if "://" in db_url else "unknown"
                    config_info["database_type"] = db_type
                    config_info["database_url_configured"] = True
                else:
                    config_info["database_url_configured"] = False
                    config_info["issues"].append("Database URL not configured")
            except Exception as config_error:
                config_info["issues"].append(f"Error reading database configuration: {str(config_error)}")
            
            return config_info
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current service status with detailed information
        
        Returns:
            Dict containing service status information
        """
        return {
            "initialized": self.is_initialized,
            "health_status": self.health_status,
            "error_message": self.error_message,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "total_models": len(self.models),
            "sqlalchemy_models": len(self.get_available_sqlalchemy_models()),
            "pydantic_schemas": len(self.get_available_pydantic_schemas()),
            "enums": len(self.get_available_enums()),
            "sample_model_names": list(self.models.keys())[:10]  # Limit for brevity
        }


# Global database service instance
database_service = DatabaseService()


async def get_database_service() -> DatabaseService:
    """
    Get the global database service instance
    
    Returns:
        DatabaseService instance
    """
    return database_service


async def initialize_database_service() -> bool:
    """
    Initialize the global database service
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    return await database_service.initialize()