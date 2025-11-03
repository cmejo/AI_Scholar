"""
FastAPI application with comprehensive error handling and service management infrastructure
"""
import logging
import json
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder

# Import service management infrastructure
from core import setup_default_logging, service_manager, get_service_logger

# Import error handling utilities
from core.error_handler import EndpointErrorHandler

# Import middleware
from middleware.error_monitoring import ErrorMonitoringMiddleware, RequestMetricsMiddleware

# Import the advanced endpoints (using simple version for now)
from api.advanced_endpoints_simple import router as advanced_router, error_router

# Import authentication and analytics
from auth.routes import router as auth_router
from analytics.routes import router as analytics_router
from auth.database import init_auth_db, create_admin_user

# Import RAG routes
from api.scientific_rag_routes import router as rag_router

# Import Models routes
from api.models_routes import router as models_router

# Import Papers routes
from api.papers_routes import router as papers_router

# Set up basic logging (simplified for now)
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Create FastAPI app
app = FastAPI(
    title="AI Scholar API",
    description="AI Scholar Research Platform with Service Management",
    version="1.0.0"
)

# Add error monitoring middleware
app.add_middleware(ErrorMonitoringMiddleware, enable_request_logging=True)
app.add_middleware(RequestMetricsMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent error format"""
    request_id = request.headers.get('x-request-id')
    
    # Log the HTTP exception
    logger.warning(
        f"HTTP exception in {request.url.path}: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": str(request.url.path),
            "method": request.method,
            "request_id": request_id
        }
    )
    
    # Return consistent error format
    if isinstance(exc.detail, dict):
        # Detail is already formatted (from our error handler)
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    else:
        # Format simple string details
        error_response = EndpointErrorHandler.create_error_response(
            error_type="http_error",
            message=str(exc.detail),
            request_id=request_id
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict()
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    request_id = request.headers.get('x-request-id')
    
    # Extract validation error details
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    # Log the validation error
    logger.warning(
        f"Validation error in {request.url.path}: {error_details}",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "request_id": request_id,
            "validation_errors": error_details
        }
    )
    
    error_response = EndpointErrorHandler.create_error_response(
        error_type="validation_error",
        message="Request validation failed",
        details={"validation_errors": error_details},
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    request_id = request.headers.get('x-request-id')
    
    # Log the unexpected exception
    logger.error(
        f"Unexpected exception in {request.url.path}: {str(exc)}",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "request_id": request_id,
            "exception_type": type(exc).__name__
        },
        exc_info=True
    )
    
    error_response = EndpointErrorHandler.create_error_response(
        error_type="internal_error",
        message="An unexpected error occurred",
        details={
            "exception_type": type(exc).__name__,
            "path": str(request.url.path),
            "method": request.method
        },
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )


# Include the routers
try:
    app.include_router(advanced_router)
    app.include_router(error_router)
    app.include_router(auth_router)
    app.include_router(analytics_router)
    app.include_router(rag_router)
    app.include_router(models_router)
    app.include_router(papers_router)
    logger.info("Successfully included all routers")
except Exception as e:
    logger.error(f"Failed to include routers: {e}")
    raise

# Add basic chat endpoints
@app.post("/chat/message")
async def chat_message_endpoint(request: Request):
    """Chat message endpoint that matches frontend API calls"""
    try:
        data = await request.json()
        message = data.get("message", "")
        context = data.get("context", {})
        dataset = context.get("dataset", "ai_scholar")  # Default to AI Scholar
        
        # Import services
        from services.ollama_service import ollama_service
        from services.vector_store_service import vector_store_service
        
        # Determine which dataset/collection to use
        collection_name = "ai_scholar_papers" if dataset == "ai_scholar" else "quant_finance_papers"
        
        # Try to get relevant context from vector store
        relevant_chunks = []
        try:
            if hasattr(vector_store_service, 'search_similar'):
                search_results = await vector_store_service.search_similar(
                    query=message,
                    collection_name=collection_name,
                    limit=5
                )
                relevant_chunks = [result.get('content', '') for result in search_results]
        except Exception as search_error:
            logger.warning(f"Vector search failed: {search_error}")
        
        # Use Ollama to generate response
        try:
            if relevant_chunks:
                # Use scientific response with context
                result = await ollama_service.generate_scientific_response(
                    query=message,
                    context_chunks=relevant_chunks,
                    model="llama3.1:8b"  # Use latest model
                )
                
                response = {
                    "response": result['response'],
                    "sources": result.get('citations', []),
                    "reasoning": f"Generated using {result['model']} with {result['context_chunks_used']} relevant sources from {dataset} dataset",
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "success",
                    "dataset": dataset,
                    "confidence": result.get('confidence_score', 0.8)
                }
            else:
                # Generate basic response without context
                ai_response = await ollama_service.generate_response(
                    prompt=f"As an AI research assistant for {dataset.replace('_', ' ').title()}, please answer: {message}",
                    model="llama3.1:8b"
                )
                
                response = {
                    "response": ai_response,
                    "sources": [],
                    "reasoning": f"Generated using Ollama AI model for {dataset} dataset",
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "success",
                    "dataset": dataset,
                    "confidence": 0.7
                }
        except Exception as ollama_error:
            logger.error(f"Ollama error: {ollama_error}")
            # Fallback to a helpful response
            response = {
                "response": f"I understand you're asking: '{message}'. I'm having trouble connecting to the AI model right now. Please ensure Ollama is running on localhost:11435 with models like 'llama3.1:8b' available. You can check available models with 'ollama list'.",
                "sources": [],
                "reasoning": "Fallback response due to AI model unavailability",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "partial_success",
                "dataset": dataset,
                "error_details": str(ollama_error)
            }
        
        return JSONResponse(content=jsonable_encoder(response))
    except Exception as e:
        logger.error(f"Chat message endpoint error: {e}")
        error_response = {
            "response": "I'm sorry, there was an error processing your message. Please try again.",
            "sources": [],
            "reasoning": "Error occurred during processing",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e)
        }
        return JSONResponse(content=jsonable_encoder(error_response))

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """Basic chat endpoint for the chatbot"""
    try:
        data = await request.json()
        message = data.get("message", "")
        
        # Import Ollama service
        from services.ollama_service import ollama_service
        
        # Check if Ollama service is available
        if not hasattr(ollama_service, 'generate_response'):
            # Fallback response if Ollama is not available
            response = {
                "response": "🤖 **AI Scholar Assistant**\n\nI'm your comprehensive research and automation assistant powered by advanced RAG technology. I can help with:\n\n**Core Capabilities:**\n• Document analysis and processing\n• Research assistance and literature review\n• Workflow automation and integration\n• Data analytics and visualization\n• Knowledge graph construction\n\n**Advanced Features:**\n• RAG (Retrieval-Augmented Generation)\n• Semantic search across processed papers\n• Multi-modal AI integration\n• Citation and source tracking\n\nAsk me anything about your research topics!",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success"
            }
        else:
            # Use Ollama to generate response
            try:
                ai_response = await ollama_service.generate_response(
                    prompt=message,
                    model="llama2"  # or whatever model you prefer
                )
                
                response = {
                    "response": ai_response,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "success"
                }
            except Exception as ollama_error:
                logger.error(f"Ollama error: {ollama_error}")
                # Fallback to a helpful response
                response = {
                    "response": f"I understand you're asking about: '{message}'. I'm having trouble connecting to the AI model right now, but I'm here to help with your research. Could you try rephrasing your question or check if the Ollama service is running?",
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "partial_success",
                    "note": "AI model temporarily unavailable"
                }
        
        return JSONResponse(content=jsonable_encoder(response))
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        error_response = {
            "response": "I'm sorry, there was an error processing your message. Please try again.",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e)
        }
        return JSONResponse(content=jsonable_encoder(error_response))

@app.get("/api/chat/health")
async def chat_health():
    """Chat service health check"""
    from services.ollama_service import ollama_service
    
    # Check Ollama health
    ollama_health = await ollama_service.health_check()
    
    response = {
        "status": "ok" if ollama_health.get('status') == 'healthy' else "degraded",
        "message": "Chat service is running",
        "timestamp": datetime.utcnow().isoformat(),
        "features": ["basic_chat", "research_assistance", "dataset_switching", "rag_integration"],
        "ollama_status": ollama_health,
        "available_datasets": ["ai_scholar", "quant_finance"]
    }
    return JSONResponse(content=jsonable_encoder(response))

@app.get("/api/chat/datasets")
async def get_available_datasets():
    """Get available datasets for chat"""
    datasets = {
        "ai_scholar": {
            "name": "AI Scholar",
            "description": "Scientific research papers and academic literature",
            "collection": "ai_scholar_papers",
            "features": ["arxiv_papers", "research_analysis", "citation_tracking"]
        },
        "quant_finance": {
            "name": "Quant Scholar", 
            "description": "Quantitative finance and trading research",
            "collection": "quant_finance_papers",
            "features": ["financial_modeling", "trading_strategies", "risk_analysis"]
        }
    }
    return JSONResponse(content=jsonable_encoder(datasets))

@app.post("/api/chat/switch-dataset")
async def switch_dataset(request: Request):
    """Switch between AI Scholar and Quant Scholar datasets"""
    try:
        data = await request.json()
        dataset = data.get("dataset", "ai_scholar")
        
        if dataset not in ["ai_scholar", "quant_finance"]:
            raise HTTPException(status_code=400, detail="Invalid dataset. Choose 'ai_scholar' or 'quant_finance'")
        
        # You could store user preferences here
        response = {
            "message": f"Switched to {dataset.replace('_', ' ').title()} dataset",
            "dataset": dataset,
            "description": "AI Scholar - Scientific research papers" if dataset == "ai_scholar" else "Quant Scholar - Quantitative finance research",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=jsonable_encoder(response))
    except Exception as e:
        logger.error(f"Dataset switch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Scholar RAG Backend is running", "version": "1.0.0"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}

@app.get("/debug/ollama")
async def debug_ollama():
    """Debug Ollama connectivity"""
    try:
        from services.ollama_service import ollama_service
        
        # Test basic connectivity
        health_status = await ollama_service.health_check()
        
        # Try to list models
        models = await ollama_service.list_models()
        
        # Test a simple generation
        test_response = None
        try:
            test_response = await ollama_service.generate_response(
                prompt="Hello, this is a test. Please respond with 'Ollama is working!'",
                model="llama3.1:8b"
            )
        except Exception as gen_error:
            test_response = f"Generation failed: {str(gen_error)}"
        
        return {
            "ollama_health": health_status,
            "available_models": models,
            "test_generation": test_response,
            "base_url": ollama_service.base_url,
            "current_model": ollama_service.current_model
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to connect to Ollama service"
        }

@app.get("/metrics")
async def get_metrics():
    """Get application metrics"""
    # Find the metrics middleware
    metrics_middleware = None
    for middleware in app.user_middleware:
        if isinstance(middleware.cls, type) and issubclass(middleware.cls, RequestMetricsMiddleware):
            # This is a bit tricky to access the instance, so we'll create a simple response
            break
    
    return {
        "status": "ok",
        "message": "Metrics endpoint available",
        "timestamp": "2024-01-01T00:00:00Z"  # Placeholder
    }

@app.post("/error-tracking/errors/report")
async def report_error(request: Request):
    """Handle frontend error reporting"""
    try:
        error_data = await request.json()
        logger.error(f"Frontend error reported: {error_data}")
        return {"status": "ok", "message": "Error reported successfully"}
    except Exception as e:
        logger.error(f"Failed to process error report: {e}")
        return {"status": "error", "message": "Failed to process error report"}

@app.post("/api/error-tracking/errors/report")
async def report_error_api(request: Request):
    """Handle frontend error reporting via API route"""
    try:
        error_data = await request.json()
        logger.error(f"Frontend error reported via API: {error_data}")
        return {"status": "ok", "message": "Error reported successfully"}
    except Exception as e:
        logger.error(f"Failed to process error report: {e}")
        return {"status": "error", "message": "Failed to process error report"}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting service initialization")
    
    # Initialize authentication database
    try:
        logger.info("Initializing authentication database...")
        init_auth_db()
        logger.info("Authentication database initialized successfully")
        
        # Create admin user
        logger.info("Creating admin user...")
        create_admin_user()
    except Exception as e:
        logger.error(f"Error during authentication database initialization: {e}", exc_info=True)
    
    # Initialize database service
    try:
        logger.info("Initializing database service...")
        db_success = await service_manager.initialize_database_service()
        if db_success:
            logger.info("Database service initialized successfully")
        else:
            logger.warning("Database service initialization failed, continuing with limited functionality")
    except Exception as e:
        logger.error(f"Error during database service initialization: {e}", exc_info=True)
    
    # Initialize semantic search service
    try:
        logger.info("Initializing semantic search service...")
        semantic_success = await service_manager.initialize_semantic_search_service()
        if semantic_success:
            logger.info("Semantic search service initialized successfully")
        else:
            logger.warning("Semantic search service initialization failed, continuing with limited functionality")
    except Exception as e:
        logger.error(f"Error during semantic search service initialization: {e}", exc_info=True)
    
    # Initialize research automation service
    try:
        logger.info("Initializing research automation service...")
        automation_success = await service_manager.initialize_research_automation_service()
        if automation_success:
            logger.info("Research automation service initialized successfully")
        else:
            logger.warning("Research automation service initialization failed, continuing with limited functionality")
    except Exception as e:
        logger.error(f"Error during research automation service initialization: {e}", exc_info=True)
    
    # Initialize advanced analytics service
    try:
        logger.info("Initializing advanced analytics service...")
        analytics_success = await service_manager.initialize_advanced_analytics_service()
        if analytics_success:
            logger.info("Advanced analytics service initialized successfully")
        else:
            logger.warning("Advanced analytics service initialization failed, continuing with limited functionality")
    except Exception as e:
        logger.error(f"Error during advanced analytics service initialization: {e}", exc_info=True)
    
    # Initialize knowledge graph service
    try:
        logger.info("Initializing knowledge graph service...")
        kg_success = await service_manager.initialize_knowledge_graph_service()
        if kg_success:
            logger.info("Knowledge graph service initialized successfully")
        else:
            logger.warning("Knowledge graph service initialization failed, continuing with limited functionality")
    except Exception as e:
        logger.error(f"Error during knowledge graph service initialization: {e}", exc_info=True)
    
    # Initialize RAG services
    try:
        logger.info("Initializing RAG services...")
        from services.vector_store_service import VectorStoreService
        from services.ollama_service import OllamaService
        
        # Create instances with correct configuration
        vector_store_service = VectorStoreService(chroma_host="localhost", chroma_port=8082)
        ollama_service = OllamaService(base_url="http://localhost:11435")
        
        # Initialize vector store
        await vector_store_service.initialize()
        logger.info("Vector store service initialized successfully")
        
        # Initialize Ollama service
        await ollama_service.initialize()
        logger.info("Ollama service initialized successfully")
        
        # Store instances globally for routes to use
        import services.vector_store_service as vs_module
        import services.ollama_service as ollama_module
        vs_module.vector_store_service = vector_store_service
        ollama_module.ollama_service = ollama_service
        
    except Exception as e:
        logger.error(f"Error during RAG services initialization: {e}", exc_info=True)
    
    # Start health monitoring
    await service_manager.start_health_monitoring()
    
    # Log initialization summary
    summary = service_manager.get_initialization_summary()
    logger.info(f"Service initialization summary: {summary}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Application shutting down")
    
    # Stop health monitoring
    await service_manager.stop_health_monitoring()
    
    logger.info("Application shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)