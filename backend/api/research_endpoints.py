"""
Research Assistant API Endpoints
Provides endpoints for research assistance capabilities including literature review,
research proposal generation, methodology advice, and data analysis guidance.
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
from services.research_assistant import (
    ResearchAssistant, LiteratureSearchService, ResearchProposalGenerator,
    MethodologyAdvisor, ResearchTopic, LiteratureReview, ResearchProposal,
    MethodologyRecommendation, DataAnalysisGuidance, ResearchMethodology,
    DataAnalysisMethod
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/research", tags=["research"])

# Request/Response Models
class ResearchTopicRequest(BaseModel):
    domain: Optional[str] = None
    keywords: Optional[List[str]] = None
    num_topics: int = Field(default=5, ge=1, le=10)

class LiteratureReviewRequest(BaseModel):
    topic: str
    research_questions: List[str]
    scope: str = Field(default="comprehensive", regex="^(comprehensive|focused|brief)$")
    max_sources: int = Field(default=50, ge=10, le=100)

class ResearchProposalRequest(BaseModel):
    topic: str
    research_questions: List[str]
    methodology_preference: Optional[str] = None
    include_literature_review: bool = True

class MethodologyAdviceRequest(BaseModel):
    research_questions: List[str]
    domain: str
    constraints: Dict[str, Any] = Field(default_factory=dict)

class DataAnalysisGuidanceRequest(BaseModel):
    research_question: str
    data_description: str
    sample_size: int = Field(ge=1)
    data_type: str = Field(default="mixed")

class LiteratureSearchRequest(BaseModel):
    query: str
    databases: Optional[List[str]] = None
    date_range: Optional[Dict[str, int]] = None
    max_results: int = Field(default=50, ge=10, le=100)

# Response Models
class ResearchTopicResponse(BaseModel):
    id: str
    title: str
    description: str
    keywords: List[str]
    domain: str
    research_questions: List[str]
    significance: str
    novelty_score: float
    feasibility_score: float
    impact_potential: float
    related_topics: List[str]
    suggested_methodologies: List[str]
    estimated_timeline: Dict[str, int]
    resources_needed: List[str]

class LiteratureReviewResponse(BaseModel):
    id: str
    topic: str
    research_questions: List[str]
    search_strategy: Dict[str, Any]
    sources: List[Dict[str, Any]]
    themes: List[Dict[str, Any]]
    gaps_identified: List[str]
    synthesis: str
    recommendations: List[str]
    quality_assessment: Dict[str, Any]
    created_at: str

class ResearchProposalResponse(BaseModel):
    id: str
    title: str
    abstract: str
    introduction: str
    research_questions: List[str]
    hypotheses: List[str]
    methodology: Dict[str, Any]
    timeline: Dict[str, Any]
    budget: Dict[str, Any]
    expected_outcomes: List[str]
    significance: str
    limitations: List[str]
    ethical_considerations: str
    created_at: str

class MethodologyRecommendationResponse(BaseModel):
    methodology: str
    suitability_score: float
    rationale: str
    advantages: List[str]
    disadvantages: List[str]
    requirements: List[str]
    estimated_duration: int
    complexity_level: str
    sample_size_guidance: str
    data_collection_methods: List[str]
    analysis_methods: List[str]
    tools_recommended: List[str]

class DataAnalysisGuidanceResponse(BaseModel):
    research_question: str
    data_type: str
    sample_size: int
    recommended_methods: List[str]
    statistical_tests: List[str]
    software_tools: List[str]
    assumptions: List[str]
    interpretation_guidelines: str
    visualization_suggestions: List[str]
    reporting_standards: List[str]
    confidence_level: float

# Endpoints

@router.post("/topics/generate", response_model=List[ResearchTopicResponse])
async def generate_research_topics(
    request: ResearchTopicRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate research topic suggestions based on user's documents and interests"""
    try:
        research_assistant = ResearchAssistant(db)
        
        topics = await research_assistant.generate_research_topics(
            user_id=current_user.id,
            domain=request.domain,
            keywords=request.keywords,
            num_topics=request.num_topics
        )
        
        return [
            ResearchTopicResponse(
                id=topic.id,
                title=topic.title,
                description=topic.description,
                keywords=topic.keywords,
                domain=topic.domain,
                research_questions=topic.research_questions,
                significance=topic.significance,
                novelty_score=topic.novelty_score,
                feasibility_score=topic.feasibility_score,
                impact_potential=topic.impact_potential,
                related_topics=topic.related_topics,
                suggested_methodologies=[m.value for m in topic.suggested_methodologies],
                estimated_timeline=topic.estimated_timeline,
                resources_needed=topic.resources_needed
            )
            for topic in topics
        ]
        
    except Exception as e:
        logger.error(f"Error generating research topics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/literature-review/generate", response_model=LiteratureReviewResponse)
async def generate_literature_review(
    request: LiteratureReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a comprehensive literature review"""
    try:
        research_assistant = ResearchAssistant(db)
        
        review = await research_assistant.generate_literature_review(
            user_id=current_user.id,
            topic=request.topic,
            research_questions=request.research_questions,
            scope=request.scope,
            max_sources=request.max_sources
        )
        
        return LiteratureReviewResponse(
            id=review.id,
            topic=review.topic,
            research_questions=review.research_questions,
            search_strategy=review.search_strategy,
            sources=review.sources,
            themes=review.themes,
            gaps_identified=review.gaps_identified,
            synthesis=review.synthesis,
            recommendations=review.recommendations,
            quality_assessment=review.quality_assessment,
            created_at=review.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error generating literature review: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/proposal/generate", response_model=ResearchProposalResponse)
async def generate_research_proposal(
    request: ResearchProposalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a comprehensive research proposal"""
    try:
        proposal_generator = ResearchProposalGenerator(db)
        
        result = await proposal_generator.generate_proposal_outline(
            user_id=current_user.id,
            topic=request.topic,
            research_questions=request.research_questions,
            methodology_preference=request.methodology_preference
        )
        
        proposal = result["proposal"]
        
        return ResearchProposalResponse(
            id=proposal.id,
            title=proposal.title,
            abstract=proposal.abstract,
            introduction=proposal.introduction,
            research_questions=proposal.research_questions,
            hypotheses=proposal.hypotheses,
            methodology=proposal.methodology,
            timeline=proposal.timeline,
            budget=proposal.budget,
            expected_outcomes=proposal.expected_outcomes,
            significance=proposal.significance,
            limitations=proposal.limitations,
            ethical_considerations=proposal.ethical_considerations,
            created_at=proposal.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error generating research proposal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/methodology/advice", response_model=Dict[str, Any])
async def get_methodology_advice(
    request: MethodologyAdviceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get methodology advice for research questions"""
    try:
        methodology_advisor = MethodologyAdvisor(db)
        
        advice = await methodology_advisor.get_methodology_advice(
            research_questions=request.research_questions,
            domain=request.domain,
            constraints=request.constraints
        )
        
        # Convert recommendations to response format
        recommendations = []
        for rec in advice["recommendations"]:
            recommendations.append(MethodologyRecommendationResponse(
                methodology=rec.methodology.value,
                suitability_score=rec.suitability_score,
                rationale=rec.rationale,
                advantages=rec.advantages,
                disadvantages=rec.disadvantages,
                requirements=rec.requirements,
                estimated_duration=rec.estimated_duration,
                complexity_level=rec.complexity_level,
                sample_size_guidance=rec.sample_size_guidance,
                data_collection_methods=rec.data_collection_methods,
                analysis_methods=[method.value for method in rec.analysis_methods],
                tools_recommended=rec.tools_recommended
            ))
        
        return {
            "question_analysis": advice["question_analysis"],
            "recommendations": [rec.dict() for rec in recommendations],
            "detailed_advice": advice["detailed_advice"],
            "constraints_considered": advice["constraints_considered"]
        }
        
    except Exception as e:
        logger.error(f"Error getting methodology advice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data-analysis/guidance", response_model=DataAnalysisGuidanceResponse)
async def get_data_analysis_guidance(
    request: DataAnalysisGuidanceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get data analysis guidance for research"""
    try:
        research_assistant = ResearchAssistant(db)
        
        guidance = await research_assistant.provide_data_analysis_guidance(
            research_question=request.research_question,
            data_description=request.data_description,
            sample_size=request.sample_size,
            data_type=request.data_type
        )
        
        return DataAnalysisGuidanceResponse(
            research_question=guidance.research_question,
            data_type=guidance.data_type,
            sample_size=guidance.sample_size,
            recommended_methods=[method.value for method in guidance.recommended_methods],
            statistical_tests=guidance.statistical_tests,
            software_tools=guidance.software_tools,
            assumptions=guidance.assumptions,
            interpretation_guidelines=guidance.interpretation_guidelines,
            visualization_suggestions=guidance.visualization_suggestions,
            reporting_standards=guidance.reporting_standards,
            confidence_level=guidance.confidence_level
        )
        
    except Exception as e:
        logger.error(f"Error getting data analysis guidance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/literature/search", response_model=Dict[str, Any])
async def search_literature(
    request: LiteratureSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search literature in user's document collection"""
    try:
        literature_service = LiteratureSearchService(db)
        
        results = await literature_service.search_literature(
            user_id=current_user.id,
            query=request.query,
            databases=request.databases,
            date_range=request.date_range,
            max_results=request.max_results
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching literature: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/methodologies", response_model=List[Dict[str, str]])
async def get_available_methodologies():
    """Get list of available research methodologies"""
    try:
        methodologies = []
        for methodology in ResearchMethodology:
            methodologies.append({
                "value": methodology.value,
                "name": methodology.value.replace("_", " ").title(),
                "description": f"{methodology.value.replace('_', ' ').title()} research methodology"
            })
        
        return methodologies
        
    except Exception as e:
        logger.error(f"Error getting methodologies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis-methods", response_model=List[Dict[str, str]])
async def get_available_analysis_methods():
    """Get list of available data analysis methods"""
    try:
        methods = []
        for method in DataAnalysisMethod:
            methods.append({
                "value": method.value,
                "name": method.value.replace("_", " ").title(),
                "description": f"{method.value.replace('_', ' ').title()} analysis method"
            })
        
        return methods
        
    except Exception as e:
        logger.error(f"Error getting analysis methods: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/domains", response_model=List[str])
async def get_research_domains():
    """Get list of available research domains"""
    try:
        domains = [
            "Computer Science",
            "Medicine",
            "Psychology", 
            "Education",
            "Business",
            "Engineering",
            "Social Sciences",
            "Natural Sciences",
            "Humanities",
            "Interdisciplinary"
        ]
        
        return domains
        
    except Exception as e:
        logger.error(f"Error getting research domains: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# User research history endpoints
@router.get("/history/topics", response_model=List[Dict[str, Any]])
async def get_user_research_topics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=50)
):
    """Get user's research topic history"""
    try:
        # Query user's research topics from document chunks with special metadata
        from core.database import DocumentChunk
        import json
        
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id.like(f"%{current_user.id}%"),
            DocumentChunk.chunk_index == -1,  # Special index for research topics
            DocumentChunk.chunk_metadata.contains("research_topic")
        ).order_by(DocumentChunk.created_at.desc()).limit(limit).all()
        
        topics = []
        for chunk in chunks:
            try:
                metadata = json.loads(chunk.chunk_metadata)
                if metadata.get("is_research_topic"):
                    topics.append({
                        "id": chunk.id,
                        "title": metadata.get("title", "Untitled"),
                        "domain": metadata.get("domain", "Unknown"),
                        "keywords": metadata.get("keywords", []),
                        "created_at": metadata.get("created_at"),
                        "novelty_score": metadata.get("novelty_score", 0.0),
                        "feasibility_score": metadata.get("feasibility_score", 0.0)
                    })
            except json.JSONDecodeError:
                continue
        
        return topics
        
    except Exception as e:
        logger.error(f"Error getting user research topics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/reviews", response_model=List[Dict[str, Any]])
async def get_user_literature_reviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=50)
):
    """Get user's literature review history"""
    try:
        from core.database import DocumentChunk
        import json
        
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id.like(f"literature_review_{current_user.id}%"),
            DocumentChunk.chunk_index == -2,  # Special index for literature reviews
            DocumentChunk.chunk_metadata.contains("literature_review")
        ).order_by(DocumentChunk.created_at.desc()).limit(limit).all()
        
        reviews = []
        for chunk in chunks:
            try:
                metadata = json.loads(chunk.chunk_metadata)
                if metadata.get("is_literature_review"):
                    reviews.append({
                        "id": chunk.id,
                        "topic": metadata.get("topic", "Untitled"),
                        "research_questions": metadata.get("research_questions", []),
                        "num_sources": metadata.get("num_sources", 0),
                        "num_themes": metadata.get("num_themes", 0),
                        "created_at": metadata.get("created_at"),
                        "quality_assessment": metadata.get("quality_assessment", {})
                    })
            except json.JSONDecodeError:
                continue
        
        return reviews
        
    except Exception as e:
        logger.error(f"Error getting user literature reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/proposals", response_model=List[Dict[str, Any]])
async def get_user_research_proposals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=50)
):
    """Get user's research proposal history"""
    try:
        from core.database import DocumentChunk
        import json
        
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id.like(f"research_proposal_{current_user.id}%"),
            DocumentChunk.chunk_index == -3,  # Special index for research proposals
            DocumentChunk.chunk_metadata.contains("research_proposal")
        ).order_by(DocumentChunk.created_at.desc()).limit(limit).all()
        
        proposals = []
        for chunk in chunks:
            try:
                metadata = json.loads(chunk.chunk_metadata)
                if metadata.get("is_research_proposal"):
                    proposals.append({
                        "id": chunk.id,
                        "title": metadata.get("title", "Untitled"),
                        "research_questions": metadata.get("research_questions", []),
                        "methodology": metadata.get("methodology", {}),
                        "timeline": metadata.get("timeline", {}),
                        "created_at": metadata.get("created_at")
                    })
            except json.JSONDecodeError:
                continue
        
        return proposals
        
    except Exception as e:
        logger.error(f"Error getting user research proposals: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))