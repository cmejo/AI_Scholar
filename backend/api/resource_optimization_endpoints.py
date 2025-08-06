"""
Resource Optimization API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from services.resource_optimization_service import ResourceOptimizationService
from core.database import get_current_user, User

router = APIRouter(prefix="/api/resource-optimization", tags=["resource-optimization"])

# Request/Response Models
class TimeRangeRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class OptimizationGoalsRequest(BaseModel):
    budget_limit: Optional[float] = Field(None, description="Budget limit for optimization")
    performance_target: str = Field("balanced", description="Performance target: cost, performance, or balanced")

class UserContextRequest(BaseModel):
    user_id: str
    role: str = Field(..., description="User role (student, faculty, admin)")
    department: Optional[str] = None
    current_usage: Optional[Dict[str, Any]] = None

class UsageAnalysisResponse(BaseModel):
    analysis_period: Dict[str, datetime]
    usage_statistics: Dict[str, Any]
    peak_usage_hours: List[tuple]
    heavy_users: List[tuple]
    total_records_analyzed: int
    patterns_identified: Dict[str, int]

class OptimizationResponse(BaseModel):
    current_cost: float
    budget_limit: float
    potential_savings: float
    optimization_recommendations: List[Dict[str, Any]]
    optimized_allocation: Dict[str, Any]
    cost_benefit_analysis: Dict[str, Any]

class ForecastResponse(BaseModel):
    forecast_period_days: int
    forecasts: Dict[str, Any]
    capacity_recommendations: List[Dict[str, Any]]
    overall_confidence: float
    data_points_analyzed: int
    forecast_generated_at: datetime

class RecommendationResponse(BaseModel):
    user_id: str
    user_role: str
    department: Optional[str]
    recommendations: List[Dict[str, Any]]
    peer_comparison: Dict[str, Any]
    generated_at: datetime

@router.post("/analyze-usage/{institution_id}", response_model=UsageAnalysisResponse)
async def analyze_usage_patterns(
    institution_id: str,
    time_range: Optional[TimeRangeRequest] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze usage patterns for library and database resources
    
    This endpoint provides comprehensive analysis of resource usage patterns
    including statistics, peak usage times, and heavy users identification.
    """
    try:
        service = ResourceOptimizationService()
        
        # Convert time range if provided
        time_range_dict = None
        if time_range and (time_range.start_date or time_range.end_date):
            time_range_dict = {}
            if time_range.start_date:
                time_range_dict['start'] = time_range.start_date
            if time_range.end_date:
                time_range_dict['end'] = time_range.end_date
        
        result = await service.analyze_usage_patterns(institution_id, time_range_dict)
        
        return UsageAnalysisResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze usage patterns: {str(e)}")

@router.post("/optimize-allocation/{institution_id}", response_model=OptimizationResponse)
async def optimize_resource_allocation(
    institution_id: str,
    optimization_goals: OptimizationGoalsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Build resource allocation optimization with cost-benefit analysis
    
    This endpoint provides optimization recommendations based on usage patterns
    and generates cost-benefit analysis for resource allocation decisions.
    """
    try:
        service = ResourceOptimizationService()
        
        goals_dict = optimization_goals.dict(exclude_none=True)
        result = await service.optimize_resource_allocation(institution_id, goals_dict)
        
        return OptimizationResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to optimize resource allocation: {str(e)}")

@router.get("/forecast-usage/{institution_id}", response_model=ForecastResponse)
async def forecast_usage(
    institution_id: str,
    forecast_period_days: int = Query(30, description="Number of days to forecast"),
    current_user: User = Depends(get_current_user)
):
    """
    Create usage forecasting and capacity planning tools
    
    This endpoint provides usage forecasting based on historical data
    and generates capacity planning recommendations.
    """
    try:
        service = ResourceOptimizationService()
        
        result = await service.forecast_usage(institution_id, forecast_period_days)
        
        return ForecastResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to forecast usage: {str(e)}")

@router.post("/recommend-resources/{institution_id}", response_model=RecommendationResponse)
async def recommend_resources(
    institution_id: str,
    user_context: UserContextRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Add resource recommendation system for efficient utilization
    
    This endpoint provides personalized resource recommendations based on
    user context and peer comparison analysis.
    """
    try:
        service = ResourceOptimizationService()
        
        context_dict = user_context.dict(exclude_none=True)
        result = await service.recommend_resources(institution_id, context_dict)
        
        return RecommendationResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate resource recommendations: {str(e)}")

@router.get("/usage-summary/{institution_id}")
async def get_usage_summary(
    institution_id: str,
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user)
):
    """
    Get a quick summary of resource usage for the institution
    """
    try:
        service = ResourceOptimizationService()
        
        # Get usage analysis for the specified period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        time_range = {'start': start_date, 'end': end_date}
        
        analysis = await service.analyze_usage_patterns(institution_id, time_range)
        
        # Calculate summary metrics
        total_cost = sum(stats['total_cost'] for stats in analysis['usage_statistics'].values())
        total_usage = sum(stats['total_usage'] for stats in analysis['usage_statistics'].values())
        
        summary = {
            'period_days': days,
            'total_cost': total_cost,
            'total_usage': total_usage,
            'resource_types': len(analysis['usage_statistics']),
            'active_users': len(analysis['heavy_users']),
            'records_analyzed': analysis['total_records_analyzed'],
            'top_resource_by_cost': max(
                analysis['usage_statistics'].items(),
                key=lambda x: x[1]['total_cost']
            )[0] if analysis['usage_statistics'] else None,
            'peak_usage_hour': analysis['peak_usage_hours'][0][0] if analysis['peak_usage_hours'] else None
        }
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage summary: {str(e)}")

@router.get("/optimization-dashboard/{institution_id}")
async def get_optimization_dashboard(
    institution_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive optimization dashboard data
    """
    try:
        service = ResourceOptimizationService()
        
        # Get usage analysis
        usage_analysis = await service.analyze_usage_patterns(institution_id)
        
        # Get optimization recommendations
        optimization_goals = {"budget_limit": 1000, "performance_target": "balanced"}
        optimization = await service.optimize_resource_allocation(institution_id, optimization_goals)
        
        # Get usage forecast
        forecast = await service.forecast_usage(institution_id, 30)
        
        dashboard = {
            'current_usage': {
                'total_cost': sum(stats['total_cost'] for stats in usage_analysis['usage_statistics'].values()),
                'resource_breakdown': usage_analysis['usage_statistics'],
                'peak_hours': usage_analysis['peak_usage_hours'][:3],
                'heavy_users': usage_analysis['heavy_users'][:5]
            },
            'optimization': {
                'potential_savings': optimization['potential_savings'],
                'top_recommendations': optimization['optimization_recommendations'][:3],
                'cost_benefit': optimization['cost_benefit_analysis']
            },
            'forecast': {
                'confidence': forecast['overall_confidence'],
                'capacity_alerts': [
                    rec for rec in forecast['capacity_recommendations'] 
                    if rec.get('urgency') == 'high'
                ][:3],
                'trending_resources': list(forecast['forecasts'].keys())[:5]
            },
            'generated_at': datetime.now()
        }
        
        return dashboard
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get optimization dashboard: {str(e)}")