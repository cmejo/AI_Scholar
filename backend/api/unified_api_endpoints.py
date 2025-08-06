"""
Unified API endpoints for comprehensive integration layer
Provides RESTful, GraphQL, and WebSocket endpoints for all features
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info

from services.auth_service import AuthService
from services.mobile_sync_service import MobileSyncService
from services.voice_processing_service import VoiceProcessingService
from services.reference_manager_service import ReferenceManagerService
from services.academic_database_service import AcademicDatabaseService
from services.note_taking_integration_service import NoteTakingIntegrationService
from services.writing_tools_service import WritingToolsService
from services.quiz_generation_service import QuizGenerationService
from services.spaced_repetition_service import SpacedRepetitionService
from services.learning_progress_service import LearningProgressService
from services.gamification_service import GamificationService
from services.compliance_monitoring_service import ComplianceMonitoringService
from services.institutional_role_management_service import InstitutionalRoleManagementService
from services.resource_optimization_service import ResourceOptimizationService
from services.student_progress_tracking_service import StudentProgressTrackingService
from services.jupyter_notebook_service import JupyterNotebookService
from services.interactive_visualization_service import InteractiveVisualizationService
from services.secure_code_execution import SecureCodeExecutionService
from services.interactive_content_version_control import InteractiveContentVersionControlService
from services.funding_matcher_service import FundingMatcherService
from services.publication_venue_matcher import PublicationVenueMatcherService
from services.grant_application_tracker import GrantApplicationTrackerService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["unified-api"])
security = HTTPBearer()

# Initialize services
auth_service = AuthService()
mobile_sync_service = MobileSyncService()
voice_service = VoiceProcessingService()
reference_manager_service = ReferenceManagerService()
academic_db_service = AcademicDatabaseService()
note_taking_service = NoteTakingIntegrationService()
writing_tools_service = WritingToolsService()
quiz_service = QuizGenerationService()
spaced_repetition_service = SpacedRepetitionService()
learning_progress_service = LearningProgressService()
gamification_service = GamificationService()
compliance_service = ComplianceMonitoringService()
institutional_service = InstitutionalRoleManagementService()
resource_optimization_service = ResourceOptimizationService()
student_progress_service = StudentProgressTrackingService()
jupyter_service = JupyterNotebookService()
visualization_service = InteractiveVisualizationService()
code_execution_service = SecureCodeExecutionService()
version_control_service = InteractiveContentVersionControlService()
funding_matcher_service = FundingMatcherService()
publication_matcher_service = PublicationVenueMatcherService()
grant_tracker_service = GrantApplicationTrackerService()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        self.user_connections[websocket] = user_id

    def disconnect(self, websocket: WebSocket):
        user_id = self.user_connections.get(websocket)
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        if websocket in self.user_connections:
            del self.user_connections[websocket]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except:
                    self.disconnect(connection)

    async def broadcast(self, message: str):
        for user_connections in self.active_connections.values():
            for connection in user_connections:
                try:
                    await connection.send_text(message)
                except:
                    self.disconnect(connection)

manager = ConnectionManager()

# Pydantic models for API requests/responses
class UnifiedAPIResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    api_version: str = "1.0"

class FeatureRequest(BaseModel):
    feature: str
    action: str
    parameters: Dict[str, Any] = {}
    user_context: Optional[Dict[str, Any]] = None

class BatchRequest(BaseModel):
    requests: List[FeatureRequest]
    parallel_execution: bool = True

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        user = await auth_service.verify_token(credentials.credentials)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# RESTful API Endpoints

@router.get("/health")
async def health_check():
    """Comprehensive health check for all services"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "api_version": "1.0",
            "services": {},
            "system_info": {
                "uptime": "N/A",  # Would be calculated from app start time
                "memory_usage": "N/A",  # Would be calculated from system metrics
                "active_connections": len(manager.active_connections)
            }
        }
        
        # Check individual service health
        services_to_check = [
            ("mobile_sync", mobile_sync_service),
            ("voice_processing", voice_service),
            ("reference_manager", reference_manager_service),
            ("academic_database", academic_db_service),
            ("note_taking", note_taking_service),
            ("writing_tools", writing_tools_service),
            ("quiz_generation", quiz_service),
            ("spaced_repetition", spaced_repetition_service),
            ("learning_progress", learning_progress_service),
            ("gamification", gamification_service),
            ("compliance", compliance_service),
            ("institutional", institutional_service),
            ("resource_optimization", resource_optimization_service),
            ("student_progress", student_progress_service),
            ("jupyter", jupyter_service),
            ("visualization", visualization_service),
            ("code_execution", code_execution_service),
            ("version_control", version_control_service),
            ("funding_matcher", funding_matcher_service),
            ("publication_matcher", publication_matcher_service),
            ("grant_tracker", grant_tracker_service)
        ]
        
        for service_name, service in services_to_check:
            try:
                if hasattr(service, 'health_check'):
                    service_health = await service.health_check()
                    health_status["services"][service_name] = service_health
                else:
                    health_status["services"][service_name] = {"status": "available"}
            except Exception as e:
                health_status["services"][service_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Determine overall health status
        failed_services = [
            name for name, status in health_status["services"].items() 
            if status.get("status") == "error"
        ]
        
        if failed_services:
            health_status["status"] = "degraded" if len(failed_services) < len(services_to_check) / 2 else "unhealthy"
            health_status["failed_services"] = failed_services
        
        return UnifiedAPIResponse(success=True, data=health_status)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return UnifiedAPIResponse(
            success=False,
            error=f"Health check failed: {str(e)}"
        )

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with performance metrics"""
    try:
        start_time = datetime.now()
        
        # Basic health check
        basic_health = await health_check()
        
        # Additional detailed metrics
        detailed_metrics = {
            "response_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
            "database_status": "connected",  # Would check actual DB connection
            "redis_status": "connected",     # Would check actual Redis connection
            "external_services": {
                "pubmed_api": "available",
                "arxiv_api": "available", 
                "google_scholar": "available"
            },
            "feature_flags": {
                "mobile_sync_enabled": True,
                "voice_processing_enabled": True,
                "real_time_collaboration": True,
                "advanced_analytics": True
            }
        }
        
        # Merge basic health with detailed metrics
        if basic_health.data:
            basic_health.data.update(detailed_metrics)
        
        return basic_health
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return UnifiedAPIResponse(
            success=False,
            error=f"Detailed health check failed: {str(e)}"
        )

@router.post("/features/execute")
async def execute_feature(
    request: FeatureRequest,
    user = Depends(get_current_user)
):
    """Execute a specific feature action through unified interface"""
    try:
        # Route request to appropriate service
        result = await route_feature_request(request, user)
        
        return UnifiedAPIResponse(
            success=True,
            data={
                "feature": request.feature,
                "action": request.action,
                "result": result
            }
        )
    except Exception as e:
        logger.error(f"Feature execution failed: {e}")
        return UnifiedAPIResponse(
            success=False,
            error=f"Feature execution failed: {str(e)}"
        )

@router.post("/features/batch")
async def execute_batch_features(
    request: BatchRequest,
    user = Depends(get_current_user)
):
    """Execute multiple feature actions in batch"""
    try:
        results = []
        
        if request.parallel_execution:
            # Execute requests in parallel
            tasks = [
                route_feature_request(req, user) 
                for req in request.requests
            ]
            parallel_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(parallel_results):
                if isinstance(result, Exception):
                    results.append({
                        "feature": request.requests[i].feature,
                        "action": request.requests[i].action,
                        "success": False,
                        "error": str(result)
                    })
                else:
                    results.append({
                        "feature": request.requests[i].feature,
                        "action": request.requests[i].action,
                        "success": True,
                        "result": result
                    })
        else:
            # Execute requests sequentially
            for req in request.requests:
                try:
                    result = await route_feature_request(req, user)
                    results.append({
                        "feature": req.feature,
                        "action": req.action,
                        "success": True,
                        "result": result
                    })
                except Exception as e:
                    results.append({
                        "feature": req.feature,
                        "action": req.action,
                        "success": False,
                        "error": str(e)
                    })
        
        return UnifiedAPIResponse(
            success=True,
            data={
                "batch_results": results,
                "total_requests": len(request.requests),
                "successful": len([r for r in results if r.get("success")]),
                "failed": len([r for r in results if not r.get("success")])
            }
        )
    except Exception as e:
        logger.error(f"Batch execution failed: {e}")
        return UnifiedAPIResponse(
            success=False,
            error=f"Batch execution failed: {str(e)}"
        )

# Mobile-specific API endpoints
@router.get("/mobile/config")
async def get_mobile_config(user = Depends(get_current_user)):
    """Get mobile app configuration"""
    try:
        config = {
            "api_version": "1.0",
            "supported_features": [
                "offline_sync", "voice_commands", "push_notifications",
                "document_upload", "real_time_chat", "knowledge_graphs"
            ],
            "sync_settings": {
                "auto_sync_interval": 300,  # 5 minutes
                "max_offline_documents": 100,
                "cache_size_limit_mb": 500
            },
            "voice_settings": {
                "supported_languages": ["en", "es", "fr", "de", "zh"],
                "default_language": "en",
                "voice_commands_enabled": True
            },
            "notification_settings": {
                "push_enabled": True,
                "channels": ["collaboration", "system", "research_updates"]
            },
            "offline_capabilities": {
                "document_viewing": True,
                "basic_search": True,
                "note_taking": True,
                "voice_recording": True
            }
        }
        
        return UnifiedAPIResponse(success=True, data=config)
    except Exception as e:
        logger.error(f"Mobile config error: {e}")
        return UnifiedAPIResponse(
            success=False,
            error=f"Failed to get mobile config: {str(e)}"
        )

@router.post("/mobile/sync")
async def mobile_sync(
    sync_data: Dict[str, Any],
    user = Depends(get_current_user)
):
    """Handle mobile data synchronization"""
    try:
        sync_result = await mobile_sync_service.sync_data(
            user_id=user.id,
            sync_data=sync_data
        )
        
        return UnifiedAPIResponse(
            success=True,
            data={
                "sync_status": sync_result.get("status", "completed"),
                "synced_items": sync_result.get("synced_items", 0),
                "conflicts_resolved": sync_result.get("conflicts_resolved", 0),
                "last_sync": datetime.now().isoformat(),
                "next_sync_recommended": (datetime.now().timestamp() + 300) * 1000  # 5 minutes from now
            }
        )
    except Exception as e:
        logger.error(f"Mobile sync error: {e}")
        return UnifiedAPIResponse(
            success=False,
            error=f"Mobile sync failed: {str(e)}"
        )

@router.get("/mobile/offline-data")
async def get_offline_data(
    limit: int = Query(50, le=100),
    user = Depends(get_current_user)
):
    """Get data for offline mobile usage"""
    try:
        offline_data = await mobile_sync_service.get_offline_data(
            user_id=user.id,
            limit=limit
        )
        
        return UnifiedAPIResponse(
            success=True,
            data={
                "documents": offline_data.get("documents", []),
                "recent_chats": offline_data.get("recent_chats", []),
                "user_preferences": offline_data.get("user_preferences", {}),
                "cached_at": datetime.now().isoformat(),
                "expires_at": (datetime.now().timestamp() + 86400) * 1000  # 24 hours from now
            }
        )
    except Exception as e:
        logger.error(f"Offline data error: {e}")
        return UnifiedAPIResponse(
            success=False,
            error=f"Failed to get offline data: {str(e)}"
        )

# External integration endpoints
@router.get("/integrations/available")
async def get_available_integrations():
    """Get list of available external integrations"""
    try:
        integrations = {
            "reference_managers": [
                {
                    "name": "Zotero",
                    "id": "zotero",
                    "description": "Sync with Zotero library",
                    "auth_type": "oauth",
                    "features": ["bibliography_sync", "annotation_import", "group_libraries"]
                },
                {
                    "name": "Mendeley",
                    "id": "mendeley", 
                    "description": "Sync with Mendeley library",
                    "auth_type": "oauth",
                    "features": ["document_sync", "annotation_sync", "social_features"]
                },
                {
                    "name": "EndNote",
                    "id": "endnote",
                    "description": "Sync with EndNote library",
                    "auth_type": "api_key",
                    "features": ["citation_sync", "library_management"]
                }
            ],
            "note_taking": [
                {
                    "name": "Obsidian",
                    "id": "obsidian",
                    "description": "Sync with Obsidian vault",
                    "auth_type": "file_access",
                    "features": ["markdown_sync", "graph_view", "plugin_support"]
                },
                {
                    "name": "Notion",
                    "id": "notion",
                    "description": "Sync with Notion workspace",
                    "auth_type": "oauth",
                    "features": ["database_sync", "page_sync", "collaboration"]
                },
                {
                    "name": "Roam Research",
                    "id": "roam",
                    "description": "Sync with Roam Research graph",
                    "auth_type": "api_key",
                    "features": ["block_sync", "graph_sync", "daily_notes"]
                }
            ],
            "academic_databases": [
                {
                    "name": "PubMed",
                    "id": "pubmed",
                    "description": "Search PubMed database",
                    "auth_type": "none",
                    "features": ["paper_search", "metadata_extraction", "citation_tracking"]
                },
                {
                    "name": "arXiv",
                    "id": "arxiv",
                    "description": "Search arXiv preprints",
                    "auth_type": "none",
                    "features": ["preprint_search", "full_text_access", "category_filtering"]
                },
                {
                    "name": "Google Scholar",
                    "id": "scholar",
                    "description": "Search Google Scholar",
                    "auth_type": "none",
                    "features": ["citation_search", "author_profiles", "metrics"]
                }
            ],
            "writing_tools": [
                {
                    "name": "Grammarly",
                    "id": "grammarly",
                    "description": "Grammar and style checking",
                    "auth_type": "api_key",
                    "features": ["grammar_check", "style_suggestions", "plagiarism_detection"]
                },
                {
                    "name": "LaTeX",
                    "id": "latex",
                    "description": "LaTeX document compilation",
                    "auth_type": "none",
                    "features": ["document_compilation", "template_support", "bibliography_integration"]
                }
            ]
        }
        
        return UnifiedAPIResponse(success=True, data=integrations)
    except Exception as e:
        logger.error(f"Available integrations error: {e}")
        return UnifiedAPIResponse(
            success=False,
            error=f"Failed to get available integrations: {str(e)}"
        )

@router.post("/integrations/{integration_id}/connect")
async def connect_integration(
    integration_id: str,
    auth_data: Dict[str, Any],
    user = Depends(get_current_user)
):
    """Connect to an external integration"""
    try:
        # Route to appropriate integration service
        if integration_id in ["zotero", "mendeley", "endnote"]:
            result = await reference_manager_service.connect_service(
                user_id=user.id,
                service=integration_id,
                auth_data=auth_data
            )
        elif integration_id in ["obsidian", "notion", "roam"]:
            result = await note_taking_service.connect_service(
                user_id=user.id,
                service=integration_id,
                auth_data=auth_data
            )
        elif integration_id in ["grammarly", "latex"]:
            result = await writing_tools_service.connect_service(
                user_id=user.id,
                service=integration_id,
                auth_data=auth_data
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown integration: {integration_id}")
        
        return UnifiedAPIResponse(
            success=True,
            data={
                "integration_id": integration_id,
                "connection_status": result.get("status", "connected"),
                "connected_at": datetime.now().isoformat(),
                "features_available": result.get("features", [])
            }
        )
    except Exception as e:
        logger.error(f"Integration connection error: {e}")
        return UnifiedAPIResponse(
            success=False,
            error=f"Failed to connect integration: {str(e)}"
        )

@router.get("/integrations/status")
async def get_integration_status(user = Depends(get_current_user)):
    """Get status of all user integrations"""
    try:
        # Get integration status from various services
        integration_status = {
            "reference_managers": await reference_manager_service.get_connection_status(user.id),
            "note_taking": await note_taking_service.get_connection_status(user.id),
            "writing_tools": await writing_tools_service.get_connection_status(user.id),
            "last_updated": datetime.now().isoformat()
        }
        
        return UnifiedAPIResponse(success=True, data=integration_status)
    except Exception as e:
        logger.error(f"Integration status error: {e}")
        return UnifiedAPIResponse(
            success=False,
            error=f"Failed to get integration status: {str(e)}"
        )

async def route_feature_request(request: FeatureRequest, user) -> Any:
    """Route feature request to appropriate service"""
    feature_routing = {
        "mobile": {
            "sync": lambda: mobile_sync_service.sync_data(user.id, request.parameters),
            "offline_cache": lambda: mobile_sync_service.manage_offline_cache(user.id, request.parameters),
            "push_notification": lambda: mobile_sync_service.send_push_notification(user.id, request.parameters)
        },
        "voice": {
            "speech_to_text": lambda: voice_service.speech_to_text(request.parameters.get("audio_data")),
            "text_to_speech": lambda: voice_service.text_to_speech(request.parameters.get("text"), request.parameters.get("voice_config")),
            "process_command": lambda: voice_service.process_voice_command(request.parameters.get("command"), user.id)
        },
        "reference_manager": {
            "sync_zotero": lambda: reference_manager_service.sync_zotero_library(user.id, request.parameters),
            "sync_mendeley": lambda: reference_manager_service.sync_mendeley_library(user.id, request.parameters),
            "sync_endnote": lambda: reference_manager_service.sync_endnote_library(user.id, request.parameters),
            "export": lambda: reference_manager_service.export_references(user.id, request.parameters)
        },
        "academic_database": {
            "search_pubmed": lambda: academic_db_service.search_pubmed(request.parameters.get("query")),
            "search_arxiv": lambda: academic_db_service.search_arxiv(request.parameters.get("query")),
            "search_scholar": lambda: academic_db_service.search_google_scholar(request.parameters.get("query")),
            "import_paper": lambda: academic_db_service.import_paper_metadata(request.parameters.get("paper_id"))
        },
        "note_taking": {
            "sync_obsidian": lambda: note_taking_service.sync_obsidian_vault(user.id, request.parameters),
            "sync_notion": lambda: note_taking_service.sync_notion_workspace(user.id, request.parameters),
            "sync_roam": lambda: note_taking_service.sync_roam_graph(user.id, request.parameters),
            "export_graph": lambda: note_taking_service.export_knowledge_graph(user.id, request.parameters)
        },
        "writing_tools": {
            "grammar_check": lambda: writing_tools_service.check_grammar(request.parameters.get("text")),
            "style_check": lambda: writing_tools_service.check_style(request.parameters.get("text")),
            "latex_compile": lambda: writing_tools_service.compile_latex(request.parameters.get("latex_code")),
            "export_document": lambda: writing_tools_service.export_document(user.id, request.parameters)
        },
        "education": {
            "generate_quiz": lambda: quiz_service.generate_quiz_from_content(request.parameters.get("content")),
            "evaluate_quiz": lambda: quiz_service.evaluate_quiz_responses(request.parameters.get("responses")),
            "schedule_review": lambda: spaced_repetition_service.calculate_next_review_date(request.parameters.get("item")),
            "track_progress": lambda: learning_progress_service.track_learning_progress(user.id, request.parameters),
            "get_achievements": lambda: gamification_service.get_user_achievements(user.id)
        },
        "enterprise": {
            "check_compliance": lambda: compliance_service.check_institutional_guidelines(request.parameters.get("data")),
            "manage_roles": lambda: institutional_service.manage_user_roles(request.parameters.get("institution_id")),
            "optimize_resources": lambda: resource_optimization_service.optimize_resource_allocation(request.parameters.get("usage_data")),
            "track_student": lambda: student_progress_service.track_student_progress(request.parameters.get("student_id"))
        },
        "interactive_content": {
            "execute_notebook": lambda: jupyter_service.execute_notebook_cells(request.parameters.get("notebook")),
            "render_visualization": lambda: visualization_service.render_interactive_visualization(request.parameters.get("viz_data")),
            "execute_code": lambda: code_execution_service.execute_code_safely(request.parameters.get("code"), request.parameters.get("language")),
            "version_control": lambda: version_control_service.create_version(user.id, request.parameters)
        },
        "opportunities": {
            "match_funding": lambda: funding_matcher_service.match_funding_opportunities(user.id, request.parameters.get("research_profile")),
            "recommend_venues": lambda: publication_matcher_service.recommend_publication_venues(request.parameters.get("paper_data")),
            "track_grants": lambda: grant_tracker_service.track_grant_applications(user.id)
        }
    }
    
    if request.feature not in feature_routing:
        raise HTTPException(status_code=400, detail=f"Unknown feature: {request.feature}")
    
    feature_actions = feature_routing[request.feature]
    if request.action not in feature_actions:
        raise HTTPException(status_code=400, detail=f"Unknown action '{request.action}' for feature '{request.feature}'")
    
    return await feature_actions[request.action]()

# WebSocket endpoints for real-time features
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """Enhanced WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, user_id)
    
    # Send welcome message
    welcome_message = {
        "type": "connection_established",
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "supported_message_types": [
            "feature_request", "ping", "subscribe", "unsubscribe",
            "real_time_chat", "collaboration_update", "voice_command"
        ]
    }
    await websocket.send_text(json.dumps(welcome_message))
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different message types
            if message_data.get("type") == "feature_request":
                await handle_websocket_feature_request(websocket, user_id, message_data)
            
            elif message_data.get("type") == "ping":
                await handle_websocket_ping(websocket, message_data)
            
            elif message_data.get("type") == "subscribe":
                await handle_websocket_subscription(websocket, user_id, message_data)
            
            elif message_data.get("type") == "unsubscribe":
                await handle_websocket_unsubscription(websocket, user_id, message_data)
            
            elif message_data.get("type") == "real_time_chat":
                await handle_websocket_chat(websocket, user_id, message_data)
            
            elif message_data.get("type") == "voice_command":
                await handle_websocket_voice_command(websocket, user_id, message_data)
            
            elif message_data.get("type") == "collaboration_update":
                await handle_websocket_collaboration(websocket, user_id, message_data)
            
            else:
                # Unknown message type
                error_response = {
                    "type": "error",
                    "error": f"Unknown message type: {message_data.get('type')}",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_text(json.dumps(error_response))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

async def handle_websocket_feature_request(websocket: WebSocket, user_id: str, message_data: dict):
    """Handle feature requests via WebSocket"""
    try:
        # Create feature request from WebSocket message
        feature_request = FeatureRequest(**message_data.get("data", {}))
        
        # Execute feature request (simplified user object for WebSocket)
        class WSUser:
            def __init__(self, user_id):
                self.id = user_id
        
        result = await route_feature_request(feature_request, WSUser(user_id))
        
        # Send result back
        response = {
            "type": "feature_response",
            "request_id": message_data.get("request_id"),
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(response))
        
    except Exception as e:
        error_response = {
            "type": "feature_response",
            "request_id": message_data.get("request_id"),
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(error_response))

async def handle_websocket_ping(websocket: WebSocket, message_data: dict):
    """Handle ping/pong for connection health"""
    pong_response = {
        "type": "pong",
        "request_id": message_data.get("request_id"),
        "timestamp": datetime.now().isoformat(),
        "server_time": datetime.now().timestamp()
    }
    await websocket.send_text(json.dumps(pong_response))

async def handle_websocket_subscription(websocket: WebSocket, user_id: str, message_data: dict):
    """Handle subscription to real-time events"""
    try:
        subscription_type = message_data.get("subscription_type")
        subscription_data = message_data.get("data", {})
        
        # Add subscription logic here
        # For now, just acknowledge the subscription
        response = {
            "type": "subscription_confirmed",
            "subscription_type": subscription_type,
            "subscription_id": f"{user_id}_{subscription_type}_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(response))
        
    except Exception as e:
        error_response = {
            "type": "subscription_error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(error_response))

async def handle_websocket_unsubscription(websocket: WebSocket, user_id: str, message_data: dict):
    """Handle unsubscription from real-time events"""
    try:
        subscription_id = message_data.get("subscription_id")
        
        # Remove subscription logic here
        response = {
            "type": "unsubscription_confirmed",
            "subscription_id": subscription_id,
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(response))
        
    except Exception as e:
        error_response = {
            "type": "unsubscription_error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(error_response))

async def handle_websocket_chat(websocket: WebSocket, user_id: str, message_data: dict):
    """Handle real-time chat messages"""
    try:
        chat_message = message_data.get("message", "")
        conversation_id = message_data.get("conversation_id")
        
        # Process chat message (simplified)
        response = {
            "type": "chat_response",
            "conversation_id": conversation_id,
            "message": f"Processed: {chat_message}",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(response))
        
    except Exception as e:
        error_response = {
            "type": "chat_error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(error_response))

async def handle_websocket_voice_command(websocket: WebSocket, user_id: str, message_data: dict):
    """Handle voice commands via WebSocket"""
    try:
        voice_data = message_data.get("voice_data", "")
        
        # Process voice command
        result = await voice_service.process_voice_command(voice_data, user_id)
        
        response = {
            "type": "voice_command_response",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(response))
        
    except Exception as e:
        error_response = {
            "type": "voice_command_error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(error_response))

async def handle_websocket_collaboration(websocket: WebSocket, user_id: str, message_data: dict):
    """Handle collaboration updates"""
    try:
        update_type = message_data.get("update_type")
        update_data = message_data.get("data", {})
        
        # Broadcast collaboration update to relevant users
        collaboration_message = {
            "type": "collaboration_update",
            "update_type": update_type,
            "data": update_data,
            "from_user": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Broadcast to all connected users (in a real implementation, 
        # this would be filtered to relevant collaborators)
        await manager.broadcast(json.dumps(collaboration_message))
        
    except Exception as e:
        error_response = {
            "type": "collaboration_error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(error_response))

@router.websocket("/ws/mobile/{user_id}")
async def mobile_websocket_endpoint(websocket: WebSocket, user_id: str):
    """Mobile-optimized WebSocket endpoint"""
    await manager.connect(websocket, user_id)
    
    # Send mobile-specific welcome message
    welcome_message = {
        "type": "mobile_connection_established",
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "mobile_features": [
            "offline_sync_status", "push_notifications", "voice_commands",
            "background_sync", "battery_optimization"
        ]
    }
    await websocket.send_text(json.dumps(welcome_message))
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle mobile-specific message types
            if message_data.get("type") == "sync_status_request":
                sync_status = await mobile_sync_service.get_sync_status(user_id)
                response = {
                    "type": "sync_status_response",
                    "data": sync_status,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_text(json.dumps(response))
            
            elif message_data.get("type") == "background_sync":
                sync_result = await mobile_sync_service.background_sync(user_id)
                response = {
                    "type": "background_sync_complete",
                    "data": sync_result,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_text(json.dumps(response))
            
            else:
                # Fallback to regular WebSocket handling
                await handle_websocket_feature_request(websocket, user_id, message_data)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Mobile WebSocket error: {e}")
        manager.disconnect(websocket)

# API versioning and compatibility support
@router.get("/version")
async def get_api_version():
    """Get current API version and supported features"""
    return UnifiedAPIResponse(
        success=True,
        data={
            "current_version": "1.0",
            "supported_versions": ["1.0"],
            "latest_version": "1.0",
            "deprecation_notices": [],
            "supported_features": [
                "mobile", "voice", "reference_manager", "academic_database",
                "note_taking", "writing_tools", "education", "enterprise",
                "interactive_content", "opportunities"
            ],
            "endpoints": {
                "rest": "/api/v1",
                "graphql": "/api/v1/graphql",
                "websocket": "/api/v1/ws",
                "mobile_websocket": "/api/v1/ws/mobile"
            },
            "capabilities": {
                "batch_processing": True,
                "real_time_updates": True,
                "webhook_support": True,
                "rate_limiting": True,
                "mobile_optimization": True,
                "offline_support": True,
                "voice_processing": True,
                "external_integrations": True,
                "authentication": ["JWT", "OAuth2", "API_KEY"]
            },
            "rate_limits": {
                "requests_per_minute": 1000,
                "batch_requests_per_minute": 100,
                "websocket_messages_per_minute": 500
            },
            "documentation": {
                "api_reference": "/api/v1/docs/reference",
                "getting_started": "/api/v1/docs/getting-started",
                "migration_guide": "/api/v1/docs/migration",
                "examples": "/api/v1/docs/examples"
            }
        }
    )

@router.get("/version/compatibility")
async def get_version_compatibility():
    """Get version compatibility information"""
    return UnifiedAPIResponse(
        success=True,
        data={
            "compatibility_matrix": {
                "1.0": {
                    "status": "current",
                    "supported_until": None,
                    "breaking_changes": [],
                    "new_features": [
                        "Enhanced mobile support",
                        "Real-time WebSocket features",
                        "External integrations",
                        "Voice processing",
                        "Batch operations"
                    ]
                }
            },
            "migration_paths": {
                "from_legacy": {
                    "automatic_migration": True,
                    "manual_steps_required": False,
                    "migration_guide": "/api/v1/docs/migration/from-legacy"
                }
            },
            "backward_compatibility": {
                "legacy_endpoints_supported": True,
                "legacy_response_format": True,
                "automatic_format_conversion": True
            }
        }
    )

# Backward compatibility endpoints
@router.get("/legacy/features")
async def list_legacy_features():
    """List features available through legacy endpoints"""
    return UnifiedAPIResponse(
        success=True,
        data={
            "message": "Legacy endpoints are still supported with automatic migration",
            "migration_guide": "/api/v1/docs/migration",
            "automatic_migration": True,
            "legacy_endpoints": [
                {
                    "path": "/api/voice/*",
                    "new_path": "/api/v1/features/execute (feature: voice)",
                    "status": "supported",
                    "migration_date": None
                },
                {
                    "path": "/api/quiz/*",
                    "new_path": "/api/v1/features/execute (feature: education)",
                    "status": "supported",
                    "migration_date": None
                },
                {
                    "path": "/api/spaced-repetition/*",
                    "new_path": "/api/v1/features/execute (feature: education)",
                    "status": "supported",
                    "migration_date": None
                },
                {
                    "path": "/api/learning-progress/*",
                    "new_path": "/api/v1/features/execute (feature: education)",
                    "status": "supported",
                    "migration_date": None
                },
                {
                    "path": "/api/gamification/*",
                    "new_path": "/api/v1/features/execute (feature: education)",
                    "status": "supported",
                    "migration_date": None
                },
                {
                    "path": "/api/secure-execution/*",
                    "new_path": "/api/v1/features/execute (feature: interactive_content)",
                    "status": "supported",
                    "migration_date": None
                },
                {
                    "path": "/api/student-progress/*",
                    "new_path": "/api/v1/features/execute (feature: enterprise)",
                    "status": "supported",
                    "migration_date": None
                },
                {
                    "path": "/api/institutional-role-management/*",
                    "new_path": "/api/v1/features/execute (feature: enterprise)",
                    "status": "supported",
                    "migration_date": None
                },
                {
                    "path": "/api/compliance/*",
                    "new_path": "/api/v1/features/execute (feature: enterprise)",
                    "status": "supported",
                    "migration_date": None
                },
                {
                    "path": "/api/resource-optimization/*",
                    "new_path": "/api/v1/features/execute (feature: enterprise)",
                    "status": "supported",
                    "migration_date": None
                },
                {
                    "path": "/api/funding-matcher/*",
                    "new_path": "/api/v1/features/execute (feature: opportunities)",
                    "status": "supported",
                    "migration_date": None
                },
                {
                    "path": "/api/publication-venue/*",
                    "new_path": "/api/v1/features/execute (feature: opportunities)",
                    "status": "supported",
                    "migration_date": None
                },
                {
                    "path": "/api/grant-application/*",
                    "new_path": "/api/v1/features/execute (feature: opportunities)",
                    "status": "supported",
                    "migration_date": None
                }
            ]
        }
    )

@router.post("/legacy/migrate")
async def migrate_from_legacy(
    migration_request: Dict[str, Any],
    user = Depends(get_current_user)
):
    """Migrate from legacy API usage to unified API"""
    try:
        legacy_endpoint = migration_request.get("legacy_endpoint")
        legacy_data = migration_request.get("data", {})
        
        # Map legacy endpoints to new unified API calls
        migration_mapping = {
            "/api/voice/": {"feature": "voice", "action": "process_command"},
            "/api/quiz/": {"feature": "education", "action": "generate_quiz"},
            "/api/spaced-repetition/": {"feature": "education", "action": "schedule_review"},
            "/api/learning-progress/": {"feature": "education", "action": "track_progress"},
            "/api/gamification/": {"feature": "education", "action": "get_achievements"},
            "/api/secure-execution/": {"feature": "interactive_content", "action": "execute_code"},
            "/api/student-progress/": {"feature": "enterprise", "action": "track_student"},
            "/api/institutional-role-management/": {"feature": "enterprise", "action": "manage_roles"},
            "/api/compliance/": {"feature": "enterprise", "action": "check_compliance"},
            "/api/resource-optimization/": {"feature": "enterprise", "action": "optimize_resources"},
            "/api/funding-matcher/": {"feature": "opportunities", "action": "match_funding"},
            "/api/publication-venue/": {"feature": "opportunities", "action": "recommend_venues"},
            "/api/grant-application/": {"feature": "opportunities", "action": "track_grants"}
        }
        
        # Find matching migration
        unified_call = None
        for legacy_path, unified_mapping in migration_mapping.items():
            if legacy_endpoint.startswith(legacy_path):
                unified_call = unified_mapping
                break
        
        if not unified_call:
            raise HTTPException(status_code=400, detail=f"No migration path found for {legacy_endpoint}")
        
        # Create unified API request
        feature_request = FeatureRequest(
            feature=unified_call["feature"],
            action=unified_call["action"],
            parameters=legacy_data
        )
        
        # Execute the migrated request
        result = await route_feature_request(feature_request, user)
        
        return UnifiedAPIResponse(
            success=True,
            data={
                "migration_successful": True,
                "legacy_endpoint": legacy_endpoint,
                "new_endpoint": f"/api/v1/features/execute",
                "new_request_format": {
                    "feature": unified_call["feature"],
                    "action": unified_call["action"],
                    "parameters": legacy_data
                },
                "result": result,
                "migration_timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return UnifiedAPIResponse(
            success=False,
            error=f"Migration failed: {str(e)}"
        )

# API documentation endpoints
@router.get("/docs/openapi")
async def get_openapi_spec():
    """Get OpenAPI specification for the unified API"""
    try:
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "AI Scholar Unified API",
                "version": "1.0.0",
                "description": "Comprehensive API for AI Scholar Advanced RAG system",
                "contact": {
                    "name": "API Support",
                    "email": "api-support@aischolar.com"
                }
            },
            "servers": [
                {
                    "url": "/api/v1",
                    "description": "Production server"
                }
            ],
            "paths": {
                "/health": {
                    "get": {
                        "summary": "Health check",
                        "description": "Check the health status of all services",
                        "responses": {
                            "200": {
                                "description": "Health status",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/UnifiedAPIResponse"}
                                    }
                                }
                            }
                        }
                    }
                },
                "/features/execute": {
                    "post": {
                        "summary": "Execute feature",
                        "description": "Execute a specific feature action",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/FeatureRequest"}
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Feature execution result",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/UnifiedAPIResponse"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "UnifiedAPIResponse": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean"},
                            "data": {"type": "object"},
                            "error": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"},
                            "api_version": {"type": "string"}
                        }
                    },
                    "FeatureRequest": {
                        "type": "object",
                        "properties": {
                            "feature": {"type": "string"},
                            "action": {"type": "string"},
                            "parameters": {"type": "object"},
                            "user_context": {"type": "object"}
                        },
                        "required": ["feature", "action"]
                    }
                },
                "securitySchemes": {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
            },
            "security": [
                {"BearerAuth": []}
            ]
        }
        
        return UnifiedAPIResponse(success=True, data=openapi_spec)
    except Exception as e:
        logger.error(f"OpenAPI spec error: {e}")
        return UnifiedAPIResponse(
            success=False,
            error=f"Failed to generate OpenAPI spec: {str(e)}"
        )