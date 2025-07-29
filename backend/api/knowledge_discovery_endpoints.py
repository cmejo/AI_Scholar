"""
Advanced Knowledge Discovery API Endpoints
Provides endpoints for semantic search v2, hypothesis generation, cross-domain insights,
and predictive research trend analysis.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from core.auth import get_current_user
from models.schemas import User
from services.semantic_search_v2 import (
    SemanticSearchV2Service, SearchQuery, SearchResult, HypothesisGeneration,
    CrossDomainInsight, SearchMode, ReasoningType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge-discovery", tags=["knowledge-discovery"])

# Request/Response Models
class AdvancedSearchRequest(BaseModel):
    query_text: str
    mode: SearchMode = SearchMode.HYBRID
    reasoning_types: List[ReasoningType] = [ReasoningType.SEMANTIC, ReasoningType.ASSOCIATIVE]
    temporal_constraints: Optional[Dict[str, Any]] = None
    domain_filters: Optional[List[str]] = None
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    max_results: int = Field(default=20, ge=1, le=100)
    include_explanations: bool = True

class HypothesisGenerationRequest(BaseModel):
    research_area: str
    existing_knowledge: Optional[List[str]] = None

class CrossDomainInsightRequest(BaseModel):
    source_domain: str
    target_domains: Optional[List[str]] = None

class TrendPredictionRequest(BaseModel):
    domain: str
    time_horizon_months: int = Field(default=12, ge=1, le=60)

class SearchResultResponse(BaseModel):
    id: str
    document_id: str
    chunk_id: str
    content: str
    title: str
    relevance_score: float
    confidence_score: float
    reasoning_path: List[str]
    knowledge_connections: List[Dict[str, Any]]
    temporal_context: Optional[Dict[str, Any]]
    cross_domain_insights: List[str]
    explanation: str
    metadata: Dict[str, Any]

class HypothesisResponse(BaseModel):
    id: str
    hypothesis: str
    confidence: float
    supporting_evidence: List[str]
    contradicting_evidence: List[str]
    research_gaps: List[str]
    methodology_suggestions: List[str]
    predicted_outcomes: List[str]

class CrossDomainInsightResponse(BaseModel):
    id: str
    source_domain: str
    target_domain: str
    insight: str
    confidence: float
    analogical_reasoning: str
    potential_applications: List[str]
    supporting_documents: List[str]

# Endpoints

@router.post("/search/advanced", response_model=List[SearchResultResponse])
async def advanced_semantic_search(
    request: AdvancedSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform advanced semantic search with reasoning capabilities"""
    try:
        search_service = SemanticSearchV2Service(db)
        
        # Create search query
        query = SearchQuery(
            query_text=request.query_text,
            user_id=current_user.id,
            mode=request.mode,
            reasoning_types=request.reasoning_types,
            temporal_constraints=request.temporal_constraints,
            domain_filters=request.domain_filters,
            confidence_threshold=request.confidence_threshold,
            max_results=request.max_results,
            include_explanations=request.include_explanations
        )
        
        # Perform search
        results = await search_service.advanced_search(query)
        
        # Convert to response format
        response_results = []
        for result in results:
            response_results.append(SearchResultResponse(
                id=result.id,
                document_id=result.document_id,
                chunk_id=result.chunk_id,
                content=result.content,
                title=result.title,
                relevance_score=result.relevance_score,
                confidence_score=result.confidence_score,
                reasoning_path=result.reasoning_path,
                knowledge_connections=result.knowledge_connections,
                temporal_context=result.temporal_context,
                cross_domain_insights=result.cross_domain_insights,
                explanation=result.explanation,
                metadata=result.metadata
            ))
        
        return response_results
        
    except Exception as e:
        logger.error(f"Error in advanced search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hypotheses/generate", response_model=List[HypothesisResponse])
async def generate_research_hypotheses(
    request: HypothesisGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate research hypotheses based on knowledge gaps"""
    try:
        search_service = SemanticSearchV2Service(db)
        
        hypotheses = await search_service.generate_hypotheses(
            user_id=current_user.id,
            research_area=request.research_area,
            existing_knowledge=request.existing_knowledge
        )
        
        # Convert to response format
        response_hypotheses = []
        for hypothesis in hypotheses:
            response_hypotheses.append(HypothesisResponse(
                id=hypothesis.id,
                hypothesis=hypothesis.hypothesis,
                confidence=hypothesis.confidence,
                supporting_evidence=hypothesis.supporting_evidence,
                contradicting_evidence=hypothesis.contradicting_evidence,
                research_gaps=hypothesis.research_gaps,
                methodology_suggestions=hypothesis.methodology_suggestions,
                predicted_outcomes=hypothesis.predicted_outcomes
            ))
        
        return response_hypotheses
        
    except Exception as e:
        logger.error(f"Error generating hypotheses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/insights/cross-domain", response_model=List[CrossDomainInsightResponse])
async def discover_cross_domain_insights(
    request: CrossDomainInsightRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Discover insights by connecting different research domains"""
    try:
        search_service = SemanticSearchV2Service(db)
        
        insights = await search_service.discover_cross_domain_insights(
            user_id=current_user.id,
            source_domain=request.source_domain,
            target_domains=request.target_domains
        )
        
        # Convert to response format
        response_insights = []
        for insight in insights:
            response_insights.append(CrossDomainInsightResponse(
                id=insight.id,
                source_domain=insight.source_domain,
                target_domain=insight.target_domain,
                insight=insight.insight,
                confidence=insight.confidence,
                analogical_reasoning=insight.analogical_reasoning,
                potential_applications=insight.potential_applications,
                supporting_documents=insight.supporting_documents
            ))
        
        return response_insights
        
    except Exception as e:
        logger.error(f"Error discovering cross-domain insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trends/predict", response_model=Dict[str, Any])
async def predict_research_trends(
    request: TrendPredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Predict future research trends and directions"""
    try:
        search_service = SemanticSearchV2Service(db)
        
        predictions = await search_service.predict_research_trends(
            user_id=current_user.id,
            domain=request.domain,
            time_horizon_months=request.time_horizon_months
        )
        
        return predictions
        
    except Exception as e:
        logger.error(f"Error predicting research trends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/modes", response_model=List[Dict[str, str]])
async def get_search_modes():
    """Get available search modes"""
    try:
        modes = []
        
        mode_descriptions = {
            SearchMode.SEMANTIC: "Pure semantic similarity search",
            SearchMode.HYBRID: "Combines semantic and keyword search",
            SearchMode.KNOWLEDGE_GRAPH: "Knowledge graph-based search",
            SearchMode.TEMPORAL: "Time-aware search with temporal reasoning",
            SearchMode.CROSS_DOMAIN: "Cross-domain analogical search",
            SearchMode.PREDICTIVE: "Predictive search for future trends"
        }
        
        for mode in SearchMode:
            modes.append({
                "value": mode.value,
                "name": mode.value.replace("_", " ").title(),
                "description": mode_descriptions.get(mode, "Search mode")
            })
        
        return modes
        
    except Exception as e:
        logger.error(f"Error getting search modes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reasoning/types", response_model=List[Dict[str, str]])
async def get_reasoning_types():
    """Get available reasoning types"""
    try:
        types = []
        
        type_descriptions = {
            ReasoningType.CAUSAL: "Identifies cause-and-effect relationships",
            ReasoningType.ANALOGICAL: "Finds analogies and similar patterns",
            ReasoningType.TEMPORAL: "Considers temporal relationships and sequences",
            ReasoningType.HIERARCHICAL: "Understands hierarchical structures and classifications",
            ReasoningType.ASSOCIATIVE: "Discovers associative connections between concepts"
        }
        
        for reasoning_type in ReasoningType:
            types.append({
                "value": reasoning_type.value,
                "name": reasoning_type.value.replace("_", " ").title(),
                "description": type_descriptions.get(reasoning_type, "Reasoning type")
            })
        
        return types
        
    except Exception as e:
        logger.error(f"Error getting reasoning types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/domains", response_model=List[str])
async def get_research_domains():
    """Get available research domains for cross-domain analysis"""
    try:
        domains = [
            "computer_science",
            "medicine",
            "psychology",
            "business",
            "education",
            "engineering",
            "social_sciences",
            "natural_sciences",
            "humanities",
            "interdisciplinary"
        ]
        
        return domains
        
    except Exception as e:
        logger.error(f"Error getting research domains: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-gaps/{research_area}", response_model=List[str])
async def identify_knowledge_gaps(
    research_area: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Identify knowledge gaps in a research area"""
    try:
        search_service = SemanticSearchV2Service(db)
        
        # Analyze existing knowledge to identify gaps
        knowledge_analysis = await search_service._analyze_existing_knowledge(
            current_user.id, research_area
        )
        
        gaps = await search_service._identify_knowledge_gaps(
            current_user.id, research_area, knowledge_analysis
        )
        
        return gaps
        
    except Exception as e:
        logger.error(f"Error identifying knowledge gaps: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/explain", response_model=Dict[str, Any])
async def explain_search_results(
    search_results: List[SearchResultResponse] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Provide detailed explanations for search results"""
    try:
        explanations = {
            "overall_explanation": "Search results ranked by relevance and enhanced through reasoning",
            "result_explanations": [],
            "reasoning_summary": {},
            "confidence_analysis": {}
        }
        
        # Analyze reasoning types used
        reasoning_counts = {}
        confidence_scores = []
        
        for result in search_results:
            confidence_scores.append(result.confidence_score)
            
            # Count reasoning types
            for reasoning in result.reasoning_path:
                reasoning_counts[reasoning] = reasoning_counts.get(reasoning, 0) + 1
            
            # Individual result explanation
            explanations["result_explanations"].append({
                "result_id": result.id,
                "explanation": result.explanation,
                "key_factors": {
                    "relevance": result.relevance_score,
                    "confidence": result.confidence_score,
                    "reasoning_applied": result.reasoning_path,
                    "knowledge_connections": len(result.knowledge_connections)
                }
            })
        
        # Summary statistics
        explanations["reasoning_summary"] = reasoning_counts
        explanations["confidence_analysis"] = {
            "average_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
            "confidence_range": {
                "min": min(confidence_scores) if confidence_scores else 0,
                "max": max(confidence_scores) if confidence_scores else 0
            },
            "high_confidence_results": len([s for s in confidence_scores if s > 0.8])
        }
        
        return explanations
        
    except Exception as e:
        logger.error(f"Error explaining search results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/discovery", response_model=Dict[str, Any])
async def get_discovery_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365)
):
    """Get knowledge discovery analytics for user"""
    try:
        from core.database import AnalyticsEvent
        from datetime import timedelta
        
        # Get discovery events
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        events = db.query(AnalyticsEvent).filter(
            AnalyticsEvent.user_id == current_user.id,
            AnalyticsEvent.event_type == "semantic_search_v2",
            AnalyticsEvent.created_at >= start_date
        ).all()
        
        # Analyze discovery patterns
        analytics = {
            "total_searches": len(events),
            "search_modes_used": {},
            "reasoning_types_used": {},
            "average_results_per_search": 0,
            "confidence_trends": [],
            "domain_exploration": {},
            "discovery_insights": []
        }
        
        if events:
            total_results = 0
            confidence_scores = []
            
            for event in events:
                event_data = event.event_data
                
                # Search modes
                mode = event_data.get("search_mode", "unknown")
                analytics["search_modes_used"][mode] = analytics["search_modes_used"].get(mode, 0) + 1
                
                # Reasoning types
                reasoning_types = event_data.get("reasoning_types", [])
                for rt in reasoning_types:
                    analytics["reasoning_types_used"][rt] = analytics["reasoning_types_used"].get(rt, 0) + 1
                
                # Results and confidence
                result_count = event_data.get("result_count", 0)
                total_results += result_count
                
                confidence = event_data.get("confidence_threshold", 0.5)
                confidence_scores.append(confidence)
            
            analytics["average_results_per_search"] = total_results / len(events)
            
            # Generate insights
            most_used_mode = max(analytics["search_modes_used"].items(), key=lambda x: x[1])[0] if analytics["search_modes_used"] else "none"
            most_used_reasoning = max(analytics["reasoning_types_used"].items(), key=lambda x: x[1])[0] if analytics["reasoning_types_used"] else "none"
            
            analytics["discovery_insights"] = [
                f"Most frequently used search mode: {most_used_mode}",
                f"Most applied reasoning type: {most_used_reasoning}",
                f"Average search confidence threshold: {sum(confidence_scores) / len(confidence_scores):.2f}",
                f"Discovery activity: {len(events)} searches in {days} days"
            ]
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting discovery analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for knowledge discovery service"""
    try:
        return {
            "status": "healthy",
            "service": "knowledge_discovery",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "advanced_semantic_search",
                "hypothesis_generation",
                "cross_domain_insights",
                "trend_prediction",
                "reasoning_enhancement"
            ]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Service unhealthy")