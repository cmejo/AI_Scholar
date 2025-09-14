"""
Advanced API endpoints for enhanced RAG features
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timedelta

from models.schemas import (
    UserProfileCreate, UserProfileResponse, UserPreferences,
    ConversationMemoryCreate, ConversationMemoryResponse,
    KnowledgeGraphEntityCreate, KnowledgeGraphEntityResponse,
    KnowledgeGraphRelationshipCreate, KnowledgeGraphRelationshipResponse,
    UserFeedbackCreate, UserFeedbackResponse,
    AnalyticsEventCreate, AnalyticsEventResponse,
    AnalyticsQuery, AnalyticsResponse,
    KnowledgeGraphQuery,
    PersonalizationSettings
)

# Import services
from services.memory_service import ConversationMemoryManager
from services.knowledge_graph_service import KnowledgeGraphService
from services.analytics_service import EnhancedAnalyticsService
from services.user_profile_service import UserProfileManager
from services.feedback_processor import FeedbackProcessor
from services.adaptive_retrieval import AdaptiveRetriever
from services.domain_adapter import DomainAdapter
# from services.topic_modeling_service import TopicModelingService
from core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/advanced", tags=["advanced"])

# Initialize services that don't require database dependencies
memory_service = ConversationMemoryManager()
knowledge_graph_service = KnowledgeGraphService()

# Services that require database sessions will be initialized in endpoints
def get_analytics_service(db: Session = Depends(get_db)) -> EnhancedAnalyticsService:
    return EnhancedAnalyticsService(db)

def get_user_profile_service(db: Session = Depends(get_db)) -> UserProfileManager:
    return UserProfileManager(db)

def get_feedback_processor() -> FeedbackProcessor:
    return FeedbackProcessor()

def get_adaptive_retriever() -> AdaptiveRetriever:
    return AdaptiveRetriever()

def get_domain_adapter() -> DomainAdapter:
    return DomainAdapter()

# Placeholder auth dependency - replace with actual auth service
async def get_current_user():
    return {"id": "test-user", "email": "test@example.com"}

# Memory Management Endpoints
@router.post("/memory/conversation", response_model=ConversationMemoryResponse)
async def create_conversation_memory(
    memory_data: ConversationMemoryCreate,
    user = Depends(get_current_user)
):
    """Create a new conversation memory entry"""
    try:
        memory_item = await memory_service.store_conversation_memory(
            conversation_id=memory_data.conversation_id,
            memory_type=memory_data.memory_type.value,
            content=memory_data.content,
            importance_score=memory_data.importance_score,
            expires_at=memory_data.expires_at,
            metadata=memory_data.metadata
        )
        
        return ConversationMemoryResponse(
            id=memory_item["id"],
            conversation_id=memory_item["conversation_id"],
            memory_type=memory_item["memory_type"],
            content=memory_item["content"],
            importance_score=memory_item["importance_score"],
            timestamp=memory_item["timestamp"],
            expires_at=memory_item.get("expires_at"),
            memory_metadata=memory_item.get("metadata", {})
        )
    except Exception as e:
        logger.error(f"Error creating conversation memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/conversation/{conversation_id}", response_model=List[ConversationMemoryResponse])
async def get_conversation_memory(
    conversation_id: str,
    memory_type: Optional[str] = None,
    user = Depends(get_current_user)
):
    """Get conversation memory for a specific conversation"""
    try:
        memories = await memory_service.get_conversation_memory(
            conversation_id=conversation_id,
            memory_type=memory_type
        )
        
        return [
            ConversationMemoryResponse(
                id=memory["id"],
                conversation_id=memory["conversation_id"],
                memory_type=memory["memory_type"],
                content=memory["content"],
                importance_score=memory["importance_score"],
                timestamp=memory["timestamp"],
                expires_at=memory.get("expires_at"),
                memory_metadata=memory.get("metadata", {})
            )
            for memory in memories
        ]
    except Exception as e:
        logger.error(f"Error retrieving conversation memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/user/{user_id}/context")
async def get_user_context(
    user_id: str,
    query: str,
    max_tokens: int = 2000,
    user = Depends(get_current_user)
):
    """Get relevant context for a user query"""
    try:
        context = await memory_service.retrieve_relevant_context(
            user_id=user_id,
            query=query,
            max_tokens=max_tokens
        )
        
        return {
            "user_id": user_id,
            "query": query,
            "context": context.get("context", ""),
            "relevance_score": context.get("relevance_score", 0.0),
            "token_count": context.get("token_count", 0),
            "memory_items": context.get("memory_items", []),
            "context_summary": context.get("summary", "")
        }
    except Exception as e:
        logger.error(f"Error retrieving user context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory/conversation/{conversation_id}/compress")
async def compress_conversation(
    conversation_id: str,
    user = Depends(get_current_user)
):
    """Compress a long conversation into a summary"""
    try:
        compression_result = await memory_service.compress_conversation(
            conversation_id=conversation_id
        )
        
        return {
            "conversation_id": conversation_id,
            "summary": compression_result.get("summary", ""),
            "compression_ratio": compression_result.get("compression_ratio", 0.0),
            "compressed_items": compression_result.get("compressed_items", 0),
            "original_items": compression_result.get("original_items", 0),
            "tokens_saved": compression_result.get("tokens_saved", 0)
        }
    except Exception as e:
        logger.error(f"Error compressing conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Knowledge Graph Endpoints
@router.post("/knowledge-graph/entities", response_model=KnowledgeGraphEntityResponse)
async def create_entity(
    entity_data: KnowledgeGraphEntityCreate,
    user = Depends(get_current_user)
):
    """Create a new knowledge graph entity"""
    try:
        entity = await knowledge_graph_service.create_entity(
            name=entity_data.name,
            entity_type=entity_data.type.value,
            description=entity_data.description,
            importance_score=entity_data.importance_score,
            document_id=entity_data.document_id,
            metadata=entity_data.metadata
        )
        
        return KnowledgeGraphEntityResponse(
            id=entity["id"],
            name=entity["name"],
            type=entity["type"],
            description=entity.get("description"),
            importance_score=entity["importance_score"],
            document_id=entity.get("document_id"),
            entity_metadata=entity.get("metadata", {}),
            created_at=entity["created_at"]
        )
    except Exception as e:
        logger.error(f"Error creating entity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-graph/entities", response_model=List[KnowledgeGraphEntityResponse])
async def get_entities(
    entity_type: Optional[str] = None,
    document_id: Optional[str] = None,
    min_importance: float = 0.0,
    limit: int = 100,
    user = Depends(get_current_user)
):
    """Get knowledge graph entities with optional filtering"""
    try:
        entities = await knowledge_graph_service.get_entities(
            entity_type=entity_type,
            document_id=document_id,
            min_importance=min_importance,
            limit=limit
        )
        
        return [
            KnowledgeGraphEntityResponse(
                id=entity["id"],
                name=entity["name"],
                type=entity["type"],
                description=entity.get("description"),
                importance_score=entity["importance_score"],
                document_id=entity.get("document_id"),
                entity_metadata=entity.get("metadata", {}),
                created_at=entity["created_at"]
            )
            for entity in entities
        ]
    except Exception as e:
        logger.error(f"Error retrieving entities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge-graph/relationships", response_model=KnowledgeGraphRelationshipResponse)
async def create_relationship(
    relationship_data: KnowledgeGraphRelationshipCreate,
    user = Depends(get_current_user)
):
    """Create a new knowledge graph relationship"""
    try:
        relationship = await knowledge_graph_service.create_relationship(
            source_entity_id=relationship_data.source_entity_id,
            target_entity_id=relationship_data.target_entity_id,
            relationship_type=relationship_data.relationship_type.value,
            confidence_score=relationship_data.confidence_score,
            context=relationship_data.context,
            metadata=relationship_data.metadata
        )
        
        return KnowledgeGraphRelationshipResponse(
            id=relationship["id"],
            source_entity_id=relationship["source_entity_id"],
            target_entity_id=relationship["target_entity_id"],
            relationship_type=relationship["relationship_type"],
            confidence_score=relationship["confidence_score"],
            context=relationship.get("context"),
            relationship_metadata=relationship.get("metadata", {}),
            created_at=relationship["created_at"]
        )
    except Exception as e:
        logger.error(f"Error creating relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge-graph/query")
async def query_knowledge_graph(
    query_data: KnowledgeGraphQuery,
    user = Depends(get_current_user)
):
    """Query the knowledge graph with advanced filtering"""
    try:
        results = await knowledge_graph_service.query_graph(
            entity_name=query_data.entity_name,
            relationship_type=query_data.relationship_type,
            max_depth=query_data.max_depth,
            min_confidence=query_data.min_confidence,
            include_metadata=query_data.include_metadata
        )
        
        return {
            "entities": results.get("entities", []),
            "relationships": results.get("relationships", []),
            "query": query_data.entity_name or "general",
            "results_count": len(results.get("entities", [])) + len(results.get("relationships", [])),
            "query_metadata": results.get("metadata", {})
        }
    except Exception as e:
        logger.error(f"Error querying knowledge graph: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-graph/entities/{entity_id}/connections")
async def get_entity_connections(
    entity_id: str,
    depth: int = 2,
    min_confidence: float = 0.5,
    user = Depends(get_current_user)
):
    """Get connections for a specific entity"""
    try:
        connections = await knowledge_graph_service.get_entity_connections(
            entity_id=entity_id,
            depth=depth,
            min_confidence=min_confidence
        )
        
        return {
            "entity_id": entity_id,
            "connections": connections.get("connections", []),
            "depth": depth,
            "total_connections": len(connections.get("connections", [])),
            "connection_types": connections.get("connection_types", [])
        }
    except Exception as e:
        logger.error(f"Error retrieving entity connections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics and Insights Endpoints
@router.post("/analytics/events", response_model=AnalyticsEventResponse)
async def create_analytics_event(
    event_data: AnalyticsEventCreate,
    user = Depends(get_current_user),
    analytics_service: EnhancedAnalyticsService = Depends(get_analytics_service)
):
    """Create a new analytics event"""
    try:
        event = await analytics_service.track_event(
            user_id=event_data.user_id or user["id"],
            event_type=event_data.event_type,
            event_data=event_data.event_data,
            session_id=event_data.session_id
        )
        
        return AnalyticsEventResponse(
            id=event["id"],
            user_id=event["user_id"],
            event_type=event["event_type"],
            event_data=event["event_data"],
            timestamp=event["timestamp"],
            session_id=event.get("session_id")
        )
    except Exception as e:
        logger.error(f"Error creating analytics event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analytics/query", response_model=AnalyticsResponse)
async def query_analytics(
    query_data: AnalyticsQuery,
    user = Depends(get_current_user),
    analytics_service: EnhancedAnalyticsService = Depends(get_analytics_service)
):
    """Query analytics data with filtering and aggregation"""
    try:
        analytics_data = await analytics_service.query_analytics(
            user_id=query_data.user_id,
            start_date=query_data.start_date,
            end_date=query_data.end_date,
            event_types=query_data.event_types,
            aggregation=query_data.aggregation
        )
        
        return AnalyticsResponse(
            total_events=analytics_data.get("total_events", 0),
            unique_users=analytics_data.get("unique_users", 0),
            time_series=analytics_data.get("time_series", []),
            top_queries=analytics_data.get("top_queries", []),
            performance_metrics=analytics_data.get("performance_metrics", {}),
            user_engagement=analytics_data.get("user_engagement", {})
        )
    except Exception as e:
        logger.error(f"Error querying analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/dashboard/{user_id}")
async def get_analytics_dashboard(
    user_id: str,
    time_range: str = "7d",
    user = Depends(get_current_user),
    analytics_service: EnhancedAnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive analytics dashboard data"""
    try:
        dashboard_data = await analytics_service.get_dashboard_data(
            user_id=user_id,
            time_range=time_range
        )
        
        return {
            "user_stats": dashboard_data.get("user_stats", {}),
            "query_stats": dashboard_data.get("query_stats", {}),
            "performance_stats": dashboard_data.get("performance_stats", {}),
            "document_stats": dashboard_data.get("document_stats", {}),
            "engagement_metrics": dashboard_data.get("engagement_metrics", {}),
            "time_range": time_range
        }
    except Exception as e:
        logger.error(f"Error retrieving dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/insights/{user_id}")
async def get_usage_insights(
    user_id: str,
    user = Depends(get_current_user),
    analytics_service: EnhancedAnalyticsService = Depends(get_analytics_service)
):
    """Get usage insights and patterns for a user"""
    try:
        insights = await analytics_service.generate_usage_insights(user_id=user_id)
        
        return {
            "patterns": insights.get("patterns", []),
            "recommendations": insights.get("recommendations", []),
            "usage_score": insights.get("usage_score", 0.0),
            "knowledge_gaps": insights.get("knowledge_gaps", []),
            "improvement_areas": insights.get("improvement_areas", [])
        }
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Personalization and Feedback Endpoints
@router.post("/personalization/profile", response_model=UserProfileResponse)
async def create_user_profile(
    profile_data: UserProfileCreate,
    user = Depends(get_current_user),
    user_profile_service: UserProfileManager = Depends(get_user_profile_service)
):
    """Create or update a user profile"""
    try:
        profile = await user_profile_service.create_or_update_profile(
            user_id=profile_data.user_id,
            preferences=profile_data.preferences.dict(),
            learning_style=profile_data.learning_style,
            domain_expertise=profile_data.domain_expertise
        )
        
        return UserProfileResponse(
            id=profile["id"],
            user_id=profile["user_id"],
            preferences=UserPreferences(**profile["preferences"]),
            interaction_history=profile.get("interaction_history", {}),
            domain_expertise=profile.get("domain_expertise", {}),
            learning_style=profile["learning_style"],
            created_at=profile["created_at"],
            updated_at=profile["updated_at"]
        )
    except Exception as e:
        logger.error(f"Error creating user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/personalization/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    user = Depends(get_current_user),
    user_profile_service: UserProfileManager = Depends(get_user_profile_service)
):
    """Get user profile"""
    try:
        profile = await user_profile_service.get_profile(user_id=user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        return UserProfileResponse(
            id=profile["id"],
            user_id=profile["user_id"],
            preferences=UserPreferences(**profile.get("preferences", {})),
            interaction_history=profile.get("interaction_history", {}),
            domain_expertise=profile.get("domain_expertise", {}),
            learning_style=profile.get("learning_style", "visual"),
            created_at=profile["created_at"],
            updated_at=profile["updated_at"]
        )
    except Exception as e:
        logger.error(f"Error retrieving user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/personalization/profile/{user_id}/preferences")
async def update_user_preferences(
    user_id: str,
    preferences: UserPreferences,
    user = Depends(get_current_user),
    user_profile_service: UserProfileManager = Depends(get_user_profile_service)
):
    """Update user preferences"""
    try:
        updated_profile = await user_profile_service.update_preferences(
            user_id=user_id,
            preferences=preferences.dict()
        )
        
        return {
            "user_id": user_id,
            "preferences": preferences.dict(),
            "updated": True,
            "updated_at": updated_profile.get("updated_at")
        }
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/personalization/feedback", response_model=UserFeedbackResponse)
async def submit_feedback(
    feedback_data: UserFeedbackCreate,
    user = Depends(get_current_user)
):
    """Submit user feedback"""
    try:
        feedback = await feedback_processor.process_feedback(
            user_id=feedback_data.user_id,
            message_id=feedback_data.message_id,
            feedback_type=feedback_data.feedback_type.value,
            feedback_value=feedback_data.feedback_value
        )
        
        return UserFeedbackResponse(
            id=feedback["id"],
            user_id=feedback["user_id"],
            message_id=feedback.get("message_id"),
            feedback_type=feedback["feedback_type"],
            feedback_value=feedback["feedback_value"],
            processed=feedback.get("processed", False),
            created_at=feedback["created_at"]
        )
    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/personalization/feedback/{user_id}", response_model=List[UserFeedbackResponse])
async def get_user_feedback(
    user_id: str,
    feedback_type: Optional[str] = None,
    limit: int = 100,
    user = Depends(get_current_user)
):
    """Get user feedback history"""
    try:
        feedback_list = await feedback_processor.get_user_feedback(
            user_id=user_id,
            feedback_type=feedback_type,
            limit=limit
        )
        
        return [
            UserFeedbackResponse(
                id=feedback["id"],
                user_id=feedback["user_id"],
                message_id=feedback.get("message_id"),
                feedback_type=feedback["feedback_type"],
                feedback_value=feedback["feedback_value"],
                processed=feedback.get("processed", False),
                created_at=feedback["created_at"]
            )
            for feedback in feedback_list
        ]
    except Exception as e:
        logger.error(f"Error retrieving feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/personalization/adaptive-strategy/{user_id}")
async def get_adaptive_strategy(
    user_id: str,
    query: str,
    user = Depends(get_current_user)
):
    """Get adaptive retrieval strategy for a user"""
    try:
        strategy = await adaptive_retriever.get_retrieval_strategy(
            user_id=user_id,
            query=query
        )
        
        return {
            "user_id": user_id,
            "query": query,
            "strategy": strategy.get("strategy_name", "default"),
            "parameters": strategy.get("parameters", {}),
            "confidence": strategy.get("confidence", 0.0),
            "reasoning": strategy.get("reasoning", "")
        }
    except Exception as e:
        logger.error(f"Error getting adaptive strategy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/personalization/domain-adaptation/{user_id}")
async def get_domain_adaptation(
    user_id: str,
    user = Depends(get_current_user)
):
    """Get domain adaptation settings for a user"""
    try:
        adaptation_data = await domain_adapter.get_user_adaptation(user_id=user_id)
        
        return {
            "user_id": user_id,
            "detected_domains": adaptation_data.get("detected_domains", {}),
            "adaptation_stats": adaptation_data.get("adaptation_stats", {}),
            "domain_preferences": adaptation_data.get("domain_preferences", {}),
            "adaptation_history": adaptation_data.get("adaptation_history", [])
        }
    except Exception as e:
        logger.error(f"Error getting domain adaptation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/personalization/settings/{user_id}")
async def update_personalization_settings(
    user_id: str,
    settings: PersonalizationSettings,
    user = Depends(get_current_user)
):
    """Update personalization settings"""
    try:
        updated_settings = await user_profile_service.update_personalization_settings(
            user_id=user_id,
            settings=settings.dict()
        )
        
        return {
            "user_id": user_id,
            "settings": settings.dict(),
            "updated": True,
            "effective_date": updated_settings.get("updated_at"),
            "previous_settings": updated_settings.get("previous_settings", {})
        }
    except Exception as e:
        logger.error(f"Error updating personalization settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Topic Modeling and Clustering Endpoints - TEMPORARILY DISABLED DUE TO NLTK ISSUES
# All topic modeling endpoints have been commented out due to NLTK dependency issues
# Uncomment and fix imports when NLTK issues are resolved