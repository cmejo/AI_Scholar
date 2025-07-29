"""
Advanced Analytics API Endpoints
Provides endpoints for comprehensive analytics, insights, visualizations,
and knowledge pattern discovery.
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
from services.advanced_analytics import (
    AdvancedAnalyticsService, AnalyticsMetric, VisualizationData,
    InsightReport, DocumentRelationship, KnowledgePattern,
    AnalyticsTimeframe, VisualizationType, MetricType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Request/Response Models
class AnalyticsReportRequest(BaseModel):
    timeframe: AnalyticsTimeframe = AnalyticsTimeframe.MONTH
    include_predictions: bool = True

class DocumentRelationshipRequest(BaseModel):
    min_similarity: float = Field(default=0.3, ge=0.0, le=1.0)
    max_relationships: int = Field(default=100, ge=10, le=500)

class KnowledgePatternRequest(BaseModel):
    min_frequency: int = Field(default=3, ge=1, le=20)
    confidence_threshold: float = Field(default=0.7, ge=0.1, le=1.0)

class UsageInsightsRequest(BaseModel):
    timeframe: AnalyticsTimeframe = AnalyticsTimeframe.MONTH

class KnowledgeMapRequest(BaseModel):
    layout_algorithm: str = Field(default="spring", regex="^(spring|circular|kamada_kawai)$")
    max_nodes: int = Field(default=100, ge=10, le=500)

class ContentAnalyticsRequest(BaseModel):
    timeframe: AnalyticsTimeframe = AnalyticsTimeframe.MONTH

# Response Models
class AnalyticsMetricResponse(BaseModel):
    name: str
    value: Any
    metric_type: str
    description: str
    unit: Optional[str] = None
    trend: Optional[float] = None
    benchmark: Optional[float] = None
    timestamp: Optional[str] = None

class VisualizationDataResponse(BaseModel):
    chart_type: str
    title: str
    data: Dict[str, Any]
    config: Dict[str, Any]
    description: str
    insights: List[str]

class InsightReportResponse(BaseModel):
    id: str
    title: str
    summary: str
    metrics: List[AnalyticsMetricResponse]
    visualizations: List[VisualizationDataResponse]
    recommendations: List[str]
    timeframe: str
    generated_at: str
    confidence_score: float

class DocumentRelationshipResponse(BaseModel):
    source_doc_id: str
    target_doc_id: str
    relationship_type: str
    strength: float
    shared_concepts: List[str]
    similarity_score: float

class KnowledgePatternResponse(BaseModel):
    pattern_id: str
    pattern_type: str
    entities: List[str]
    relationships: List[str]
    frequency: int
    confidence: float
    examples: List[str]

# Endpoints

@router.post("/report/comprehensive", response_model=InsightReportResponse)
async def generate_comprehensive_report(
    request: AnalyticsReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate comprehensive analytics report"""
    try:
        analytics_service = AdvancedAnalyticsService(db)
        
        report = await analytics_service.generate_comprehensive_report(
            user_id=current_user.id,
            timeframe=request.timeframe,
            include_predictions=request.include_predictions
        )
        
        # Convert metrics to response format
        metrics_response = []
        for metric in report.metrics:
            metrics_response.append(AnalyticsMetricResponse(
                name=metric.name,
                value=metric.value,
                metric_type=metric.metric_type.value,
                description=metric.description,
                unit=metric.unit,
                trend=metric.trend,
                benchmark=metric.benchmark,
                timestamp=metric.timestamp.isoformat() if metric.timestamp else None
            ))
        
        # Convert visualizations to response format
        viz_response = []
        for viz in report.visualizations:
            viz_response.append(VisualizationDataResponse(
                chart_type=viz.chart_type.value,
                title=viz.title,
                data=viz.data,
                config=viz.config,
                description=viz.description,
                insights=viz.insights
            ))
        
        return InsightReportResponse(
            id=report.id,
            title=report.title,
            summary=report.summary,
            metrics=metrics_response,
            visualizations=viz_response,
            recommendations=report.recommendations,
            timeframe=report.timeframe.value,
            generated_at=report.generated_at.isoformat(),
            confidence_score=report.confidence_score
        )
        
    except Exception as e:
        logger.error(f"Error generating comprehensive report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/relationships", response_model=List[DocumentRelationshipResponse])
async def analyze_document_relationships(
    request: DocumentRelationshipRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze relationships between user's documents"""
    try:
        analytics_service = AdvancedAnalyticsService(db)
        
        relationships = await analytics_service.analyze_document_relationships(
            user_id=current_user.id,
            min_similarity=request.min_similarity,
            max_relationships=request.max_relationships
        )
        
        return [
            DocumentRelationshipResponse(
                source_doc_id=rel.source_doc_id,
                target_doc_id=rel.target_doc_id,
                relationship_type=rel.relationship_type,
                strength=rel.strength,
                shared_concepts=rel.shared_concepts,
                similarity_score=rel.similarity_score
            )
            for rel in relationships
        ]
        
    except Exception as e:
        logger.error(f"Error analyzing document relationships: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge/patterns", response_model=List[KnowledgePatternResponse])
async def discover_knowledge_patterns(
    request: KnowledgePatternRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Discover patterns in user's knowledge graph"""
    try:
        analytics_service = AdvancedAnalyticsService(db)
        
        patterns = await analytics_service.discover_knowledge_patterns(
            user_id=current_user.id,
            min_frequency=request.min_frequency,
            confidence_threshold=request.confidence_threshold
        )
        
        return [
            KnowledgePatternResponse(
                pattern_id=pattern.pattern_id,
                pattern_type=pattern.pattern_type,
                entities=pattern.entities,
                relationships=pattern.relationships,
                frequency=pattern.frequency,
                confidence=pattern.confidence,
                examples=pattern.examples
            )
            for pattern in patterns
        ]
        
    except Exception as e:
        logger.error(f"Error discovering knowledge patterns: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/usage/insights", response_model=Dict[str, Any])
async def generate_usage_insights(
    request: UsageInsightsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate detailed usage insights"""
    try:
        analytics_service = AdvancedAnalyticsService(db)
        
        insights = await analytics_service.generate_usage_insights(
            user_id=current_user.id,
            timeframe=request.timeframe
        )
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating usage insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge/map", response_model=VisualizationDataResponse)
async def create_knowledge_map(
    request: KnowledgeMapRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create interactive knowledge map visualization"""
    try:
        analytics_service = AdvancedAnalyticsService(db)
        
        visualization = await analytics_service.create_knowledge_map_visualization(
            user_id=current_user.id,
            layout_algorithm=request.layout_algorithm,
            max_nodes=request.max_nodes
        )
        
        return VisualizationDataResponse(
            chart_type=visualization.chart_type.value,
            title=visualization.title,
            data=visualization.data,
            config=visualization.config,
            description=visualization.description,
            insights=visualization.insights
        )
        
    except Exception as e:
        logger.error(f"Error creating knowledge map: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/content/analytics", response_model=Dict[str, Any])
async def generate_content_analytics(
    request: ContentAnalyticsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate comprehensive content analytics"""
    try:
        analytics_service = AdvancedAnalyticsService(db)
        
        analytics = await analytics_service.generate_content_analytics(
            user_id=current_user.id,
            timeframe=request.timeframe
        )
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error generating content analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/summary", response_model=Dict[str, Any])
async def get_metrics_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    timeframe: AnalyticsTimeframe = Query(default=AnalyticsTimeframe.WEEK)
):
    """Get summary of key metrics"""
    try:
        analytics_service = AdvancedAnalyticsService(db)
        
        # Get basic metrics
        usage_metrics = await analytics_service._get_usage_metrics(current_user.id, timeframe)
        performance_metrics = await analytics_service._get_performance_metrics(current_user.id, timeframe)
        content_metrics = await analytics_service._get_content_metrics(current_user.id, timeframe)
        knowledge_metrics = await analytics_service._get_knowledge_metrics(current_user.id, timeframe)
        
        # Organize by category
        summary = {
            "usage": [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "description": metric.description
                }
                for metric in usage_metrics
            ],
            "performance": [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "description": metric.description
                }
                for metric in performance_metrics
            ],
            "content": [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "description": metric.description
                }
                for metric in content_metrics
            ],
            "knowledge": [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "description": metric.description
                }
                for metric in knowledge_metrics
            ],
            "timeframe": timeframe.value,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting metrics summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualizations/available", response_model=List[Dict[str, str]])
async def get_available_visualizations():
    """Get list of available visualization types"""
    try:
        visualizations = []
        
        viz_descriptions = {
            VisualizationType.LINE_CHART: "Line chart for time series data",
            VisualizationType.BAR_CHART: "Bar chart for categorical comparisons",
            VisualizationType.PIE_CHART: "Pie chart for proportional data",
            VisualizationType.SCATTER_PLOT: "Scatter plot for correlation analysis",
            VisualizationType.HEATMAP: "Heatmap for matrix data visualization",
            VisualizationType.NETWORK_GRAPH: "Network graph for relationship visualization",
            VisualizationType.TREEMAP: "Treemap for hierarchical data",
            VisualizationType.SANKEY_DIAGRAM: "Sankey diagram for flow visualization",
            VisualizationType.WORD_CLOUD: "Word cloud for text frequency",
            VisualizationType.TIMELINE: "Timeline for temporal data"
        }
        
        for viz_type in VisualizationType:
            visualizations.append({
                "type": viz_type.value,
                "name": viz_type.value.replace("_", " ").title(),
                "description": viz_descriptions.get(viz_type, "Visualization type")
            })
        
        return visualizations
        
    except Exception as e:
        logger.error(f"Error getting available visualizations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timeframes", response_model=List[Dict[str, str]])
async def get_available_timeframes():
    """Get list of available analytics timeframes"""
    try:
        timeframes = []
        
        timeframe_descriptions = {
            AnalyticsTimeframe.HOUR: "Last hour",
            AnalyticsTimeframe.DAY: "Last 24 hours",
            AnalyticsTimeframe.WEEK: "Last 7 days",
            AnalyticsTimeframe.MONTH: "Last 30 days",
            AnalyticsTimeframe.QUARTER: "Last 90 days",
            AnalyticsTimeframe.YEAR: "Last 365 days",
            AnalyticsTimeframe.ALL_TIME: "All available data"
        }
        
        for timeframe in AnalyticsTimeframe:
            timeframes.append({
                "value": timeframe.value,
                "name": timeframe.value.replace("_", " ").title(),
                "description": timeframe_descriptions.get(timeframe, "Time period")
            })
        
        return timeframes
        
    except Exception as e:
        logger.error(f"Error getting available timeframes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metric-types", response_model=List[Dict[str, str]])
async def get_metric_types():
    """Get list of available metric types"""
    try:
        metric_types = []
        
        type_descriptions = {
            MetricType.USAGE: "User activity and engagement metrics",
            MetricType.PERFORMANCE: "System performance and efficiency metrics",
            MetricType.CONTENT: "Content volume and diversity metrics",
            MetricType.USER_BEHAVIOR: "User behavior pattern metrics",
            MetricType.KNOWLEDGE: "Knowledge graph and relationship metrics",
            MetricType.QUALITY: "Content and processing quality metrics"
        }
        
        for metric_type in MetricType:
            metric_types.append({
                "type": metric_type.value,
                "name": metric_type.value.replace("_", " ").title(),
                "description": type_descriptions.get(metric_type, "Metric category")
            })
        
        return metric_types
        
    except Exception as e:
        logger.error(f"Error getting metric types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/data", response_model=Dict[str, Any])
async def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    timeframe: AnalyticsTimeframe = Query(default=AnalyticsTimeframe.WEEK)
):
    """Get comprehensive dashboard data"""
    try:
        analytics_service = AdvancedAnalyticsService(db)
        
        # Get various analytics components
        usage_insights = await analytics_service.generate_usage_insights(current_user.id, timeframe)
        content_analytics = await analytics_service.generate_content_analytics(current_user.id, timeframe)
        
        # Get recent document relationships (limited)
        relationships = await analytics_service.analyze_document_relationships(
            current_user.id, min_similarity=0.5, max_relationships=20
        )
        
        # Get knowledge patterns (limited)
        patterns = await analytics_service.discover_knowledge_patterns(
            current_user.id, min_frequency=2, confidence_threshold=0.6
        )
        
        # Create knowledge map
        knowledge_map = await analytics_service.create_knowledge_map_visualization(
            current_user.id, max_nodes=50
        )
        
        dashboard_data = {
            "usage_insights": usage_insights,
            "content_analytics": content_analytics,
            "document_relationships": [
                {
                    "source_doc_id": rel.source_doc_id,
                    "target_doc_id": rel.target_doc_id,
                    "relationship_type": rel.relationship_type,
                    "strength": rel.strength,
                    "shared_concepts": rel.shared_concepts[:5]  # Limit concepts
                }
                for rel in relationships[:10]  # Limit relationships
            ],
            "knowledge_patterns": [
                {
                    "pattern_type": pattern.pattern_type,
                    "entities": pattern.entities[:5],  # Limit entities
                    "frequency": pattern.frequency,
                    "confidence": pattern.confidence
                }
                for pattern in patterns[:5]  # Limit patterns
            ],
            "knowledge_map": {
                "chart_type": knowledge_map.chart_type.value,
                "title": knowledge_map.title,
                "data": knowledge_map.data,
                "insights": knowledge_map.insights[:3]  # Limit insights
            },
            "timeframe": timeframe.value,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/report/{report_id}")
async def export_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    format: str = Query(default="json", regex="^(json|csv|pdf)$")
):
    """Export analytics report in various formats"""
    try:
        # This would typically retrieve a stored report and export it
        # For now, return a placeholder response
        
        from core.database import AnalyticsEvent
        
        # Find the report generation event
        report_event = db.query(AnalyticsEvent).filter(
            AnalyticsEvent.user_id == current_user.id,
            AnalyticsEvent.event_type == "analytics_report_generated",
            AnalyticsEvent.event_data.contains(f'"report_id": "{report_id}"')
        ).first()
        
        if not report_event:
            raise HTTPException(status_code=404, detail="Report not found")
        
        if format == "json":
            return {
                "report_id": report_id,
                "format": format,
                "export_url": f"/api/analytics/reports/{report_id}/download",
                "generated_at": datetime.utcnow().isoformat()
            }
        else:
            # For CSV and PDF formats, you would generate the appropriate file
            return {
                "message": f"Export in {format} format not yet implemented",
                "report_id": report_id,
                "format": format
            }
        
    except Exception as e:
        logger.error(f"Error exporting report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for analytics service"""
    try:
        return {
            "status": "healthy",
            "service": "advanced_analytics",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "comprehensive_reports",
                "document_relationships",
                "knowledge_patterns",
                "usage_insights",
                "content_analytics",
                "knowledge_mapping"
            ]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Service unhealthy")