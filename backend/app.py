"""
Main FastAPI application for AI Scholar RAG Backend
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    JSONResponse,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from api.advanced_endpoints import router as advanced_router
from api.compliance_endpoints import router as compliance_router
from api.developer_portal_endpoints import router as developer_portal_router
from api.funding_matcher_endpoints import router as funding_matcher_router
from api.gamification_endpoints import router as gamification_router
from api.grant_application_endpoints import router as grant_application_router
from api.graphql_schema import graphql_router
from api.institutional_role_management_endpoints import (
    router as institutional_role_management_router,
)
from api.integration_auth_endpoints import router as integration_auth_router
from api.learning_progress_endpoints import router as learning_progress_router
from api.monitoring_endpoints import router as monitoring_router
from api.multimodal_endpoints import router as multimodal_router
from api.publication_venue_endpoints import router as publication_venue_router
from api.quiz_endpoints import router as quiz_router
from api.research_endpoints import router as research_router
from api.resource_optimization_endpoints import router as resource_optimization_router
from api.secure_code_execution_endpoints import router as secure_execution_router
from api.spaced_repetition_endpoints import router as spaced_repetition_router
from api.student_progress_endpoints import router as student_progress_router
from api.unified_api_endpoints import router as unified_api_router
from api.voice_endpoints import router as voice_router
from api.webhook_notification_endpoints import router as webhook_notification_router
from api.zotero_endpoints import router as zotero_router
from core.config import ALLOWED_FILE_TYPES, MAX_BATCH_FILES, MAX_FILE_SIZE_MB, settings
from core.database import init_db
from core.exceptions import (
    AuthenticationError,
    BaseAPIException,
    DocumentNotFoundError,
    DocumentProcessingError,
    FileValidationError,
    ValidationError,
)
from core.redis_client import redis_client
from middleware.performance_middleware import (
    CacheOptimizationMiddleware,
    DatabaseOptimizationMiddleware,
    PerformanceMiddleware,
)
from models.schemas import (
    ChatRequest,
    ChatResponse,
    ChunkingStrategy,
    DocumentComparisonRequest,
    DocumentComparisonResponse,
    DocumentResponse,
    EnhancedChatRequest,
    EnhancedChatResponse,
    UserCreate,
    UserResponse,
)
from services.auth_service import AuthService
from services.document_processor import DocumentProcessor
from services.enhanced_rag_service import EnhancedRAGService
from services.hierarchical_chunking import HierarchicalChunkingService
from services.knowledge_graph import KnowledgeGraphService
from services.memory_service import MemoryService
from services.rag_service import RAGService
from services.reasoning_engine import ReasoningEngine
from services.user_profile_service import UserProfileService
from services.vector_store import VectorStoreService
from utils.file_validation import FileValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
document_processor = DocumentProcessor()
rag_service = RAGService()
enhanced_rag_service = EnhancedRAGService()
vector_store = VectorStoreService()
auth_service = AuthService()
knowledge_graph = KnowledgeGraphService()
memory_service = MemoryService()
reasoning_engine = ReasoningEngine()
user_profile_service = UserProfileService()
hierarchical_chunking_service = HierarchicalChunkingService()
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting AI Scholar RAG Backend...")
    await init_db()
    await redis_client.connect()
    await vector_store.initialize()
    await knowledge_graph.initialize()
    logger.info("Backend initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down AI Scholar RAG Backend...")


# Create FastAPI app with enhanced configuration
app = FastAPI(
    title="AI Scholar API",
    description="""
    ## 🎓 AI Scholar Research Platform API
    
    A comprehensive API for AI-powered research assistance and document management.
    
    ### Features
    - **Document Processing**: Upload and process research documents with AI
    - **RAG System**: Retrieval-Augmented Generation for intelligent Q&A
    - **Knowledge Graphs**: Entity extraction and relationship mapping
    - **Research Tools**: Advanced research workflow management
    - **Real-time Collaboration**: Live document collaboration and updates
    
    ### Authentication
    Use Bearer token authentication for all protected endpoints.
    
    ### Rate Limits
    - 60 requests per minute per IP
    - 1000 requests per hour per IP
    - Burst limit: 10 requests per 10 seconds
    
    ### Quick Start
    ```python
    import requests
    
    # Upload a document
    with open('research_paper.pdf', 'rb') as f:
        response = requests.post(
            'http://localhost:8000/api/documents/upload',
            files={'file': f},
            headers={'Authorization': 'Bearer YOUR_TOKEN'}
        )
    
    # Ask a question about the document
    response = requests.post(
        'http://localhost:8000/api/chat/query',
        json={
            'query': 'What are the main findings?',
            'document_ids': ['doc_id_from_upload']
        },
        headers={'Authorization': 'Bearer YOUR_TOKEN'}
    )
    ```
    """,
    version="2.0.0",
    contact={
        "name": "AI Scholar Team",
        "url": "https://github.com/cmejo/AI_Scholar",
        "email": "support@aischolar.com",
    },
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    lifespan=lifespan,
)


def custom_openapi():
    """Custom OpenAPI schema with enhanced documentation"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add custom extensions
    openapi_schema["info"]["x-logo"] = {
        "url": "/static/logo.png",
        "altText": "AI Scholar Logo",
    }

    # Add examples for common operations
    openapi_schema["info"]["x-examples"] = {
        "document_upload": {
            "summary": "Upload Research Paper",
            "description": "Upload a PDF research paper for processing",
            "value": {
                "file": "research_paper.pdf",
                "chunking_strategy": "hierarchical",
                "metadata": {
                    "title": "Research Paper Title",
                    "authors": ["Author 1", "Author 2"],
                    "year": 2024,
                },
            },
        },
        "ai_query": {
            "summary": "Ask AI Question",
            "description": "Query the AI system about uploaded documents",
            "value": {
                "query": "What are the main contributions of this research?",
                "context_limit": 5,
                "include_sources": True,
            },
        },
    }

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }

    # Add global security requirement
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Shutdown handler
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down AI Scholar RAG Backend...")
    await redis_client.disconnect()


app = FastAPI(
    title="AI Scholar RAG Backend",
    description="Advanced RAG system with knowledge graphs and multi-modal processing",
    version="1.0.0",
    lifespan=lifespan,
)

# Performance monitoring middleware
app.add_middleware(PerformanceMiddleware, enable_detailed_logging=False)

# Cache optimization middleware
app.add_middleware(CacheOptimizationMiddleware)

# Database optimization middleware
app.add_middleware(DatabaseOptimizationMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom exception handlers
@app.exception_handler(BaseAPIException)
async def base_api_exception_handler(request, exc: BaseAPIException):
    """Handle custom API exceptions"""
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


@app.exception_handler(FileValidationError)
async def file_validation_exception_handler(request, exc: FileValidationError):
    """Handle file validation errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.extra_data,
            }
        },
    )


# Include advanced endpoints router
app.include_router(advanced_router)
app.include_router(monitoring_router)
app.include_router(multimodal_router)
app.include_router(research_router)
app.include_router(voice_router)
app.include_router(quiz_router)
app.include_router(spaced_repetition_router)
app.include_router(learning_progress_router)
app.include_router(gamification_router)
app.include_router(secure_execution_router)
app.include_router(student_progress_router)
app.include_router(institutional_role_management_router)
app.include_router(compliance_router)
app.include_router(resource_optimization_router)
app.include_router(funding_matcher_router)
app.include_router(publication_venue_router)
app.include_router(grant_application_router)

# Include unified API and GraphQL routers
app.include_router(unified_api_router)
app.include_router(graphql_router)
app.include_router(integration_auth_router)
app.include_router(webhook_notification_router)
app.include_router(developer_portal_router)
app.include_router(zotero_router)


# Dependency for authentication
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Get current authenticated user"""
    try:
        user = await auth_service.verify_token(credentials.credentials)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Scholar RAG Backend is running", "version": "1.0.0"}


@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        user = await auth_service.create_user(user_data)
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/login")
async def login(email: str = Form(...), password: str = Form(...)):
    """Login user and return access token"""
    try:
        token_data = await auth_service.authenticate_user(email, password)
        return token_data
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/api/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.HIERARCHICAL,
    user=Depends(get_current_user),
):
    """Upload and process a document with enhanced hierarchical chunking"""
    try:
        # Enhanced file validation with security checks
        file_content = await file.read()
        await file.seek(0)  # Reset file pointer

        validation_result = FileValidator.validate_upload_file(
            filename=file.filename or "unknown",
            file_content=file_content,
            declared_mime_type=file.content_type or "",
        )

        if not validation_result["is_valid"]:
            raise FileValidationError(
                message="; ".join(validation_result["errors"]),
                filename=file.filename,
                validation_errors=validation_result["errors"],
            )

        # Process document with enhanced processing
        result = await document_processor.process_document(file, user.id)

        # Apply hierarchical chunking if requested
        if chunking_strategy == ChunkingStrategy.HIERARCHICAL:
            chunks = await hierarchical_chunking_service.chunk_document(
                document=result, strategy=chunking_strategy.value
            )
            result.chunks_count = len(chunks)
            logger.info(f"Applied hierarchical chunking: {len(chunks)} chunks created")

        # Add to vector store with enhanced embeddings
        await vector_store.add_document(result)

        # Update knowledge graph with entity extraction
        await knowledge_graph.add_document(result)

        # Track document upload analytics
        try:
            from services.analytics_service import AnalyticsService

            analytics_service = AnalyticsService()
            await analytics_service.track_event(
                user_id=user.id,
                event_type="document_uploaded",
                event_data={
                    "document_id": result.id,
                    "file_size": result.size,
                    "chunking_strategy": chunking_strategy.value,
                    "chunks_count": result.chunks_count,
                },
            )
        except Exception as analytics_error:
            logger.warning(f"Analytics tracking failed: {analytics_error}")

        return result

    except FileValidationError:
        raise  # Re-raise validation errors as-is
    except DocumentProcessingError:
        raise  # Re-raise processing errors as-is
    except Exception as e:
        logger.error(f"Unexpected document processing error: {str(e)}")
        raise DocumentProcessingError(
            message="An unexpected error occurred during document processing",
            processing_stage="upload",
        )


@app.get("/api/documents", response_model=List[DocumentResponse])
async def get_documents(user=Depends(get_current_user)):
    """Get all documents for the current user"""
    try:
        documents = await document_processor.get_user_documents(user.id)
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str, user=Depends(get_current_user)):
    """Delete a document"""
    try:
        await document_processor.delete_document(document_id, user.id)
        await vector_store.delete_document(document_id)
        await knowledge_graph.remove_document(document_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest, user=Depends(get_current_user)):
    """Process chat message with basic RAG (legacy endpoint)"""
    try:
        response = await rag_service.generate_response(
            query=request.message,
            user_id=user.id,
            conversation_id=request.conversation_id,
            use_chain_of_thought=request.use_chain_of_thought,
            citation_mode=request.citation_mode,
        )
        return response
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/enhanced", response_model=EnhancedChatResponse)
async def enhanced_chat_message(
    request: EnhancedChatRequest, user=Depends(get_current_user)
):
    """Process chat message with enhanced RAG including reasoning, memory, and personalization"""
    try:
        # Get user profile for personalization
        user_profile = None
        if request.personalization_level > 0:
            try:
                user_profile = await user_profile_service.get_profile(user.id)
            except Exception as profile_error:
                logger.warning(f"Could not load user profile: {profile_error}")

        # Retrieve conversation memory if enabled
        conversation_context = None
        if request.enable_memory and request.conversation_id:
            try:
                conversation_context = await memory_service.retrieve_relevant_context(
                    user_id=user.id, query=request.message, max_tokens=2000
                )
            except Exception as memory_error:
                logger.warning(f"Could not retrieve memory context: {memory_error}")

        # Generate enhanced response
        response = await enhanced_rag_service.generate_enhanced_response(
            query=request.message,
            user_id=user.id,
            conversation_id=request.conversation_id,
            use_chain_of_thought=request.use_chain_of_thought,
            citation_mode=request.citation_mode,
            enable_reasoning=request.enable_reasoning,
            enable_memory=request.enable_memory,
            personalization_level=request.personalization_level,
            max_sources=request.max_sources,
            user_profile=user_profile,
            conversation_context=conversation_context,
        )

        # Store conversation memory if enabled
        if request.enable_memory and request.conversation_id:
            try:
                await memory_service.store_conversation_memory(
                    conversation_id=request.conversation_id,
                    memory_type="short_term",
                    content=f"Q: {request.message}\nA: {response.response}",
                    importance_score=0.7,
                    metadata={
                        "query_length": len(request.message),
                        "response_length": len(response.response),
                        "sources_count": len(response.sources),
                    },
                )
            except Exception as memory_error:
                logger.warning(f"Could not store conversation memory: {memory_error}")

        # Track analytics
        try:
            from services.analytics_service import AnalyticsService

            analytics_service = AnalyticsService()
            await analytics_service.track_event(
                user_id=user.id,
                event_type="enhanced_query_executed",
                event_data={
                    "query_length": len(request.message),
                    "response_time": response.processing_time,
                    "sources_count": len(response.sources),
                    "reasoning_enabled": request.enable_reasoning,
                    "memory_enabled": request.enable_memory,
                    "personalization_level": request.personalization_level,
                    "knowledge_graph_used": response.knowledge_graph_used,
                },
            )
        except Exception as analytics_error:
            logger.warning(f"Analytics tracking failed: {analytics_error}")

        return response

    except Exception as e:
        logger.error(f"Enhanced chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/compare", response_model=DocumentComparisonResponse)
async def compare_documents(
    request: DocumentComparisonRequest, user=Depends(get_current_user)
):
    """Compare multiple documents"""
    try:
        comparison = await rag_service.compare_documents(
            document_ids=request.document_ids,
            query=request.query,
            comparison_type=request.comparison_type,
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge-graph/{document_id}")
async def get_knowledge_graph(
    document_id: str,
    include_relationships: bool = True,
    max_depth: int = 2,
    min_confidence: float = 0.5,
    user=Depends(get_current_user),
):
    """Get enhanced knowledge graph for a document with filtering options"""
    try:
        graph_data = await knowledge_graph.get_document_graph(
            document_id=document_id,
            include_relationships=include_relationships,
            max_depth=max_depth,
            min_confidence=min_confidence,
        )

        # Add visualization data
        try:
            from services.knowledge_graph_visualizer import KnowledgeGraphVisualizer

            visualizer = KnowledgeGraphVisualizer()
            visualization_data = await visualizer.generate_visualization(graph_data)
            graph_data["visualization"] = visualization_data
        except Exception as viz_error:
            logger.warning(f"Visualization generation failed: {viz_error}")

        # Track knowledge graph access
        try:
            from services.analytics_service import AnalyticsService

            analytics_service = AnalyticsService()
            await analytics_service.track_event(
                user_id=user.id,
                event_type="knowledge_graph_accessed",
                event_data={
                    "document_id": document_id,
                    "entities_count": len(graph_data.get("nodes", [])),
                    "relationships_count": len(graph_data.get("edges", [])),
                    "max_depth": max_depth,
                    "min_confidence": min_confidence,
                },
            )
        except Exception as analytics_error:
            logger.warning(f"Analytics tracking failed: {analytics_error}")

        return graph_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/batch-upload")
async def batch_upload_documents(
    files: List[UploadFile] = File(...),
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.HIERARCHICAL,
    user=Depends(get_current_user),
):
    """Upload and process multiple documents in batch"""
    try:
        if len(files) > 10:  # Limit batch size
            raise HTTPException(
                status_code=400, detail="Maximum 10 files allowed per batch"
            )

        results = []
        failed_uploads = []

        for file in files:
            try:
                # Enhanced batch file validation
                try:
                    file_content = await file.read()
                    await file.seek(0)

                    validation_result = FileValidator.validate_upload_file(
                        filename=file.filename or "unknown",
                        file_content=file_content,
                        declared_mime_type=file.content_type or "",
                    )

                    if not validation_result["is_valid"]:
                        failed_uploads.append(
                            {
                                "filename": file.filename,
                                "error": "; ".join(validation_result["errors"]),
                                "validation_details": validation_result["errors"],
                            }
                        )
                        continue

                except Exception as validation_error:
                    failed_uploads.append(
                        {
                            "filename": file.filename,
                            "error": f"Validation failed: {str(validation_error)}",
                        }
                    )
                    continue

                # Process document
                result = await document_processor.process_document(file, user.id)

                # Apply hierarchical chunking
                if chunking_strategy == ChunkingStrategy.HIERARCHICAL:
                    chunks = await hierarchical_chunking_service.chunk_document(
                        document=result, strategy=chunking_strategy.value
                    )
                    result.chunks_count = len(chunks)

                # Add to vector store and knowledge graph
                await vector_store.add_document(result)
                await knowledge_graph.add_document(result)

                results.append(result)

            except Exception as file_error:
                logger.error(f"Failed to process {file.filename}: {file_error}")
                failed_uploads.append(
                    {"filename": file.filename, "error": str(file_error)}
                )

        # Track batch upload analytics
        try:
            from services.analytics_service import AnalyticsService

            analytics_service = AnalyticsService()
            await analytics_service.track_event(
                user_id=user.id,
                event_type="batch_documents_uploaded",
                event_data={
                    "total_files": len(files),
                    "successful_uploads": len(results),
                    "failed_uploads": len(failed_uploads),
                    "chunking_strategy": chunking_strategy.value,
                },
            )
        except Exception as analytics_error:
            logger.warning(f"Analytics tracking failed: {analytics_error}")

        return {
            "successful_uploads": results,
            "failed_uploads": failed_uploads,
            "summary": {
                "total_files": len(files),
                "successful": len(results),
                "failed": len(failed_uploads),
            },
        }

    except Exception as e:
        logger.error(f"Batch upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search/semantic")
async def semantic_search(
    query: str,
    limit: int = 10,
    enable_personalization: bool = True,
    user=Depends(get_current_user),
):
    """Perform semantic search across documents with optional personalization"""
    try:
        # Get personalized search strategy if enabled
        search_strategy = None
        if enable_personalization:
            try:
                from services.adaptive_retrieval import AdaptiveRetriever

                adaptive_retriever = AdaptiveRetriever()
                search_strategy = await adaptive_retriever.get_retrieval_strategy(
                    user_id=user.id, query=query
                )
            except Exception as personalization_error:
                logger.warning(
                    f"Personalization failed, using default search: {personalization_error}"
                )

        # Perform search with or without personalization
        if search_strategy:
            results = await vector_store.personalized_semantic_search(
                query=query, user_id=user.id, limit=limit, strategy=search_strategy
            )
        else:
            results = await vector_store.semantic_search(query, user.id, limit)

        # Add uncertainty scores to results
        enhanced_results = []
        for result in results:
            try:
                uncertainty_score = await reasoning_engine.quantify_uncertainty(
                    response=result.get("content", ""), sources=[result]
                )
                result["uncertainty_score"] = uncertainty_score
            except Exception as uncertainty_error:
                logger.warning(
                    f"Uncertainty quantification failed: {uncertainty_error}"
                )
                result["uncertainty_score"] = None

            enhanced_results.append(result)

        # Track search analytics
        try:
            from services.analytics_service import AnalyticsService

            analytics_service = AnalyticsService()
            await analytics_service.track_event(
                user_id=user.id,
                event_type="semantic_search",
                event_data={
                    "query": query,
                    "results_count": len(enhanced_results),
                    "personalization_enabled": enable_personalization,
                    "strategy_used": (
                        search_strategy.get("strategy_name")
                        if search_strategy
                        else "default"
                    ),
                },
            )
        except Exception as analytics_error:
            logger.warning(f"Analytics tracking failed: {analytics_error}")

        return {
            "results": enhanced_results,
            "personalization_applied": enable_personalization
            and search_strategy is not None,
            "search_strategy": (
                search_strategy.get("strategy_name") if search_strategy else "default"
            ),
            "total_results": len(enhanced_results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/dashboard")
async def get_analytics_dashboard(
    time_range: str = "7d",
    include_insights: bool = True,
    user=Depends(get_current_user),
):
    """Get enhanced analytics dashboard data with insights"""
    try:
        # Get basic analytics data
        analytics = await rag_service.get_analytics_data(user.id)

        # Get enhanced analytics from analytics service
        try:
            from services.analytics_service import AnalyticsService

            analytics_service = AnalyticsService()

            enhanced_analytics = await analytics_service.get_dashboard_data(
                user_id=user.id, time_range=time_range
            )

            # Merge basic and enhanced analytics
            analytics.update(enhanced_analytics)

            # Add usage insights if requested
            if include_insights:
                insights = await analytics_service.generate_usage_insights(
                    user_id=user.id
                )
                analytics["insights"] = insights

        except Exception as enhanced_error:
            logger.warning(f"Enhanced analytics failed: {enhanced_error}")

        # Add knowledge graph statistics
        try:
            kg_stats = await knowledge_graph.get_user_statistics(user.id)
            analytics["knowledge_graph_stats"] = kg_stats
        except Exception as kg_error:
            logger.warning(f"Knowledge graph stats failed: {kg_error}")

        # Add memory usage statistics
        try:
            memory_stats = await memory_service.get_user_memory_stats(user.id)
            analytics["memory_stats"] = memory_stats
        except Exception as memory_error:
            logger.warning(f"Memory stats failed: {memory_error}")

        analytics["time_range"] = time_range
        analytics["generated_at"] = datetime.now().isoformat()

        return analytics
    except Exception as e:
        logger.error(f"Analytics dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
