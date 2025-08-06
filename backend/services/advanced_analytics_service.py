"""
Advanced Analytics Service for Comprehensive Monitoring

This service provides advanced analytics capabilities for feature usage,
user behavior tracking, performance analysis, and business intelligence.
"""

import json
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import pandas as pd
import numpy as np
from sqlalchemy import func, and_, or_
from backend.core.database import get_db_session
from backend.services.comprehensive_monitoring_service import (
    FeatureUsageMetrics, PerformanceMetrics, IntegrationHealthMetrics, 
    BusinessMetrics, FeatureCategory
)

logger = logging.getLogger(__name__)

@dataclass
class UserBehaviorPattern:
    """User behavior pattern analysis"""
    user_id: str
    session_count: int
    total_duration_minutes: float
    favorite_features: List[str]
    usage_frequency: str  # daily, weekly, monthly
    engagement_score: float
    churn_risk: str  # low, medium, high
    last_activity: datetime

@dataclass
class FeaturePerformanceInsight:
    """Feature performance insight"""
    feature_name: str
    category: str
    usage_trend: str  # increasing, decreasing, stable
    performance_trend: str  # improving, degrading, stable
    user_satisfaction: float
    adoption_rate: float
    retention_rate: float
    key_issues: List[str]

@dataclass
class BusinessIntelligenceReport:
    """Business intelligence report"""
    report_type: str
    period: str
    key_metrics: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    trends: Dict[str, str]
    generated_at: datetime

class AdvancedAnalyticsService:
    """Advanced analytics service for comprehensive monitoring"""
    
    def __init__(self):
        self.engagement_thresholds = {
            "high": 80,
            "medium": 50,
            "low": 20
        }
        self.performance_thresholds = {
            "excellent": 100,
            "good": 500,
            "fair": 1000,
            "poor": 2000
        }
    
    def analyze_user_behavior_patterns(self, days: int = 30, 
                                     environment: str = "production") -> List[UserBehaviorPattern]:
        """Analyze user behavior patterns and engagement"""
        try:
            with get_db_session() as db:
                start_time = datetime.utcnow() - timedelta(days=days)
                
                # Get user activity data
                user_activities = db.query(FeatureUsageMetrics).filter(
                    FeatureUsageMetrics.timestamp >= start_time,
                    FeatureUsageMetrics.environment == environment,
                    FeatureUsageMetrics.user_id.isnot(None)
                ).all()
                
                # Group by user
                user_data = defaultdict(list)
                for activity in user_activities:
                    user_data[activity.user_id].append(activity)
                
                patterns = []
                for user_id, activities in user_data.items():
                    pattern = self._analyze_single_user_pattern(user_id, activities, days)
                    patterns.append(pattern)
                
                return sorted(patterns, key=lambda x: x.engagement_score, reverse=True)
                
        except Exception as e:
            logger.error(f"Error analyzing user behavior patterns: {str(e)}")
            return []
    
    def _analyze_single_user_pattern(self, user_id: str, activities: List[FeatureUsageMetrics], 
                                   period_days: int) -> UserBehaviorPattern:
        """Analyze behavior pattern for a single user"""
        # Calculate session metrics
        session_count = len(set(activity.session_id for activity in activities if activity.session_id))
        
        # Calculate total duration
        total_duration_ms = sum(activity.duration_ms for activity in activities if activity.duration_ms)
        total_duration_minutes = total_duration_ms / 60000 if total_duration_ms else 0
        
        # Find favorite features
        feature_counts = Counter(activity.feature_name for activity in activities)
        favorite_features = [feature for feature, _ in feature_counts.most_common(5)]
        
        # Determine usage frequency
        unique_days = len(set(activity.timestamp.date() for activity in activities))
        if unique_days >= period_days * 0.8:
            usage_frequency = "daily"
        elif unique_days >= period_days * 0.3:
            usage_frequency = "weekly"
        else:
            usage_frequency = "monthly"
        
        # Calculate engagement score (0-100)
        engagement_score = min(100, (
            (session_count / max(1, period_days)) * 20 +  # Session frequency
            (total_duration_minutes / max(1, session_count)) * 0.1 +  # Avg session duration
            len(favorite_features) * 5 +  # Feature diversity
            (unique_days / period_days) * 50  # Activity consistency
        ))
        
        # Determine churn risk
        last_activity = max(activity.timestamp for activity in activities)
        days_since_last_activity = (datetime.utcnow() - last_activity).days
        
        if days_since_last_activity > 7:
            churn_risk = "high"
        elif days_since_last_activity > 3:
            churn_risk = "medium"
        else:
            churn_risk = "low"
        
        return UserBehaviorPattern(
            user_id=user_id,
            session_count=session_count,
            total_duration_minutes=total_duration_minutes,
            favorite_features=favorite_features,
            usage_frequency=usage_frequency,
            engagement_score=engagement_score,
            churn_risk=churn_risk,
            last_activity=last_activity
        )
    
    def analyze_feature_performance_insights(self, days: int = 30, 
                                           environment: str = "production") -> List[FeaturePerformanceInsight]:
        """Analyze feature performance insights and trends"""
        try:
            with get_db_session() as db:
                start_time = datetime.utcnow() - timedelta(days=days)
                
                # Get feature usage data
                usage_data = db.query(FeatureUsageMetrics).filter(
                    FeatureUsageMetrics.timestamp >= start_time,
                    FeatureUsageMetrics.environment == environment
                ).all()
                
                # Get performance data
                performance_data = db.query(PerformanceMetrics).filter(
                    PerformanceMetrics.timestamp >= start_time,
                    PerformanceMetrics.environment == environment
                ).all()
                
                # Group by feature
                feature_insights = {}
                
                # Analyze usage data
                feature_usage = defaultdict(list)
                for usage in usage_data:
                    feature_usage[usage.feature_name].append(usage)
                
                for feature_name, usages in feature_usage.items():
                    insight = self._analyze_feature_insight(feature_name, usages, performance_data, days)
                    feature_insights[feature_name] = insight
                
                return list(feature_insights.values())
                
        except Exception as e:
            logger.error(f"Error analyzing feature performance insights: {str(e)}")
            return []
    
    def _analyze_feature_insight(self, feature_name: str, usages: List[FeatureUsageMetrics],
                               performance_data: List[PerformanceMetrics], 
                               period_days: int) -> FeaturePerformanceInsight:
        """Analyze insight for a single feature"""
        # Get feature category
        category = usages[0].feature_category if usages else "unknown"
        
        # Analyze usage trend
        mid_point = len(usages) // 2
        first_half = usages[:mid_point]
        second_half = usages[mid_point:]
        
        if len(second_half) > len(first_half) * 1.1:
            usage_trend = "increasing"
        elif len(second_half) < len(first_half) * 0.9:
            usage_trend = "decreasing"
        else:
            usage_trend = "stable"
        
        # Analyze performance trend
        feature_performance = [p for p in performance_data if feature_name.lower() in p.endpoint.lower()]
        if feature_performance:
            mid_point_perf = len(feature_performance) // 2
            first_half_perf = feature_performance[:mid_point_perf]
            second_half_perf = feature_performance[mid_point_perf:]
            
            if first_half_perf and second_half_perf:
                first_avg = statistics.mean(p.response_time_ms for p in first_half_perf)
                second_avg = statistics.mean(p.response_time_ms for p in second_half_perf)
                
                if second_avg < first_avg * 0.9:
                    performance_trend = "improving"
                elif second_avg > first_avg * 1.1:
                    performance_trend = "degrading"
                else:
                    performance_trend = "stable"
            else:
                performance_trend = "stable"
        else:
            performance_trend = "unknown"
        
        # Calculate user satisfaction (based on success rate)
        successful_usages = sum(1 for usage in usages if usage.success)
        user_satisfaction = (successful_usages / len(usages)) * 100 if usages else 0
        
        # Calculate adoption rate (unique users / total users estimate)
        unique_users = len(set(usage.user_id for usage in usages if usage.user_id))
        adoption_rate = min(100, unique_users * 2)  # Simplified calculation
        
        # Calculate retention rate (users who used feature multiple times)
        user_usage_counts = Counter(usage.user_id for usage in usages if usage.user_id)
        returning_users = sum(1 for count in user_usage_counts.values() if count > 1)
        retention_rate = (returning_users / max(1, unique_users)) * 100
        
        # Identify key issues
        key_issues = []
        error_usages = [usage for usage in usages if not usage.success]
        if error_usages:
            error_messages = [usage.error_message for usage in error_usages if usage.error_message]
            error_counts = Counter(error_messages)
            key_issues = [f"{error}: {count} occurrences" for error, count in error_counts.most_common(3)]
        
        if user_satisfaction < 90:
            key_issues.append(f"Low user satisfaction: {user_satisfaction:.1f}%")
        
        if retention_rate < 50:
            key_issues.append(f"Low retention rate: {retention_rate:.1f}%")
        
        return FeaturePerformanceInsight(
            feature_name=feature_name,
            category=category,
            usage_trend=usage_trend,
            performance_trend=performance_trend,
            user_satisfaction=user_satisfaction,
            adoption_rate=adoption_rate,
            retention_rate=retention_rate,
            key_issues=key_issues
        )
    
    def generate_business_intelligence_report(self, report_type: str = "comprehensive",
                                            days: int = 30, environment: str = "production") -> BusinessIntelligenceReport:
        """Generate business intelligence report"""
        try:
            if report_type == "comprehensive":
                return self._generate_comprehensive_report(days, environment)
            elif report_type == "performance":
                return self._generate_performance_report(days, environment)
            elif report_type == "engagement":
                return self._generate_engagement_report(days, environment)
            else:
                raise ValueError(f"Unknown report type: {report_type}")
                
        except Exception as e:
            logger.error(f"Error generating business intelligence report: {str(e)}")
            return BusinessIntelligenceReport(
                report_type=report_type,
                period=f"{days} days",
                key_metrics={},
                insights=[f"Error generating report: {str(e)}"],
                recommendations=[],
                trends={},
                generated_at=datetime.utcnow()
            )
    
    def _generate_comprehensive_report(self, days: int, environment: str) -> BusinessIntelligenceReport:
        """Generate comprehensive business intelligence report"""
        with get_db_session() as db:
            start_time = datetime.utcnow() - timedelta(days=days)
            
            # Get all metrics
            usage_metrics = db.query(FeatureUsageMetrics).filter(
                FeatureUsageMetrics.timestamp >= start_time,
                FeatureUsageMetrics.environment == environment
            ).all()
            
            performance_metrics = db.query(PerformanceMetrics).filter(
                PerformanceMetrics.timestamp >= start_time,
                PerformanceMetrics.environment == environment
            ).all()
            
            business_metrics = db.query(BusinessMetrics).filter(
                BusinessMetrics.timestamp >= start_time,
                BusinessMetrics.environment == environment
            ).all()
            
            # Calculate key metrics
            total_users = len(set(m.user_id for m in usage_metrics if m.user_id))
            total_sessions = len(set(m.session_id for m in usage_metrics if m.session_id))
            total_features_used = len(set(m.feature_name for m in usage_metrics))
            
            avg_response_time = statistics.mean(m.response_time_ms for m in performance_metrics) if performance_metrics else 0
            success_rate = (sum(1 for m in usage_metrics if m.success) / len(usage_metrics)) * 100 if usage_metrics else 0
            
            # Feature category breakdown
            category_usage = Counter(m.feature_category for m in usage_metrics)
            
            key_metrics = {
                "total_users": total_users,
                "total_sessions": total_sessions,
                "total_features_used": total_features_used,
                "average_response_time_ms": avg_response_time,
                "success_rate_percentage": success_rate,
                "category_usage": dict(category_usage)
            }
            
            # Generate insights
            insights = []
            if total_users > 0:
                insights.append(f"Platform has {total_users} active users over {days} days")
            
            if success_rate < 95:
                insights.append(f"Success rate of {success_rate:.1f}% indicates room for improvement")
            
            if avg_response_time > 1000:
                insights.append(f"Average response time of {avg_response_time:.0f}ms may impact user experience")
            
            # Most popular category
            if category_usage:
                top_category = max(category_usage.items(), key=lambda x: x[1])
                insights.append(f"Most popular feature category is {top_category[0]} with {top_category[1]} uses")
            
            # Generate recommendations
            recommendations = []
            if success_rate < 95:
                recommendations.append("Focus on improving error handling and system reliability")
            
            if avg_response_time > 1000:
                recommendations.append("Optimize performance to reduce response times")
            
            if total_users < 100:
                recommendations.append("Implement user acquisition strategies to grow user base")
            
            # Analyze trends
            trends = {}
            if len(usage_metrics) > 10:
                mid_point = len(usage_metrics) // 2
                first_half_users = len(set(m.user_id for m in usage_metrics[:mid_point] if m.user_id))
                second_half_users = len(set(m.user_id for m in usage_metrics[mid_point:] if m.user_id))
                
                if second_half_users > first_half_users * 1.1:
                    trends["user_growth"] = "increasing"
                elif second_half_users < first_half_users * 0.9:
                    trends["user_growth"] = "decreasing"
                else:
                    trends["user_growth"] = "stable"
            
            return BusinessIntelligenceReport(
                report_type="comprehensive",
                period=f"{days} days",
                key_metrics=key_metrics,
                insights=insights,
                recommendations=recommendations,
                trends=trends,
                generated_at=datetime.utcnow()
            )
    
    def _generate_performance_report(self, days: int, environment: str) -> BusinessIntelligenceReport:
        """Generate performance-focused business intelligence report"""
        with get_db_session() as db:
            start_time = datetime.utcnow() - timedelta(days=days)
            
            performance_metrics = db.query(PerformanceMetrics).filter(
                PerformanceMetrics.timestamp >= start_time,
                PerformanceMetrics.environment == environment
            ).all()
            
            if not performance_metrics:
                return BusinessIntelligenceReport(
                    report_type="performance",
                    period=f"{days} days",
                    key_metrics={},
                    insights=["No performance data available for the specified period"],
                    recommendations=[],
                    trends={},
                    generated_at=datetime.utcnow()
                )
            
            # Calculate performance metrics
            response_times = [m.response_time_ms for m in performance_metrics]
            response_times.sort()
            
            avg_response_time = statistics.mean(response_times)
            p50_response_time = response_times[len(response_times) // 2]
            p95_response_time = response_times[int(len(response_times) * 0.95)]
            p99_response_time = response_times[int(len(response_times) * 0.99)]
            
            error_count = sum(1 for m in performance_metrics if m.status_code >= 400)
            error_rate = (error_count / len(performance_metrics)) * 100
            
            # Endpoint performance
            endpoint_performance = defaultdict(list)
            for m in performance_metrics:
                endpoint_performance[m.endpoint].append(m.response_time_ms)
            
            slowest_endpoints = sorted(
                [(endpoint, statistics.mean(times)) for endpoint, times in endpoint_performance.items()],
                key=lambda x: x[1], reverse=True
            )[:5]
            
            key_metrics = {
                "total_requests": len(performance_metrics),
                "average_response_time_ms": avg_response_time,
                "p50_response_time_ms": p50_response_time,
                "p95_response_time_ms": p95_response_time,
                "p99_response_time_ms": p99_response_time,
                "error_rate_percentage": error_rate,
                "slowest_endpoints": slowest_endpoints
            }
            
            # Generate insights
            insights = []
            insights.append(f"Processed {len(performance_metrics)} requests with {avg_response_time:.0f}ms average response time")
            
            if error_rate > 5:
                insights.append(f"High error rate of {error_rate:.1f}% requires attention")
            
            if p95_response_time > 2000:
                insights.append(f"95th percentile response time of {p95_response_time:.0f}ms may impact user experience")
            
            if slowest_endpoints:
                insights.append(f"Slowest endpoint is {slowest_endpoints[0][0]} with {slowest_endpoints[0][1]:.0f}ms average")
            
            # Generate recommendations
            recommendations = []
            if error_rate > 5:
                recommendations.append("Investigate and fix high error rate issues")
            
            if p95_response_time > 2000:
                recommendations.append("Optimize slow endpoints to improve user experience")
            
            if avg_response_time > 500:
                recommendations.append("Consider caching strategies and database optimization")
            
            return BusinessIntelligenceReport(
                report_type="performance",
                period=f"{days} days",
                key_metrics=key_metrics,
                insights=insights,
                recommendations=recommendations,
                trends={},
                generated_at=datetime.utcnow()
            )
    
    def _generate_engagement_report(self, days: int, environment: str) -> BusinessIntelligenceReport:
        """Generate user engagement-focused business intelligence report"""
        user_patterns = self.analyze_user_behavior_patterns(days, environment)
        
        if not user_patterns:
            return BusinessIntelligenceReport(
                report_type="engagement",
                period=f"{days} days",
                key_metrics={},
                insights=["No user engagement data available for the specified period"],
                recommendations=[],
                trends={},
                generated_at=datetime.utcnow()
            )
        
        # Calculate engagement metrics
        total_users = len(user_patterns)
        high_engagement_users = sum(1 for p in user_patterns if p.engagement_score >= 80)
        medium_engagement_users = sum(1 for p in user_patterns if 50 <= p.engagement_score < 80)
        low_engagement_users = sum(1 for p in user_patterns if p.engagement_score < 50)
        
        avg_engagement_score = statistics.mean(p.engagement_score for p in user_patterns)
        avg_session_duration = statistics.mean(p.total_duration_minutes / max(1, p.session_count) for p in user_patterns)
        
        # Churn risk analysis
        high_churn_risk = sum(1 for p in user_patterns if p.churn_risk == "high")
        medium_churn_risk = sum(1 for p in user_patterns if p.churn_risk == "medium")
        low_churn_risk = sum(1 for p in user_patterns if p.churn_risk == "low")
        
        # Usage frequency distribution
        daily_users = sum(1 for p in user_patterns if p.usage_frequency == "daily")
        weekly_users = sum(1 for p in user_patterns if p.usage_frequency == "weekly")
        monthly_users = sum(1 for p in user_patterns if p.usage_frequency == "monthly")
        
        key_metrics = {
            "total_users": total_users,
            "average_engagement_score": avg_engagement_score,
            "average_session_duration_minutes": avg_session_duration,
            "engagement_distribution": {
                "high": high_engagement_users,
                "medium": medium_engagement_users,
                "low": low_engagement_users
            },
            "churn_risk_distribution": {
                "high": high_churn_risk,
                "medium": medium_churn_risk,
                "low": low_churn_risk
            },
            "usage_frequency_distribution": {
                "daily": daily_users,
                "weekly": weekly_users,
                "monthly": monthly_users
            }
        }
        
        # Generate insights
        insights = []
        insights.append(f"Average user engagement score is {avg_engagement_score:.1f}/100")
        
        if high_engagement_users / total_users > 0.3:
            insights.append(f"{high_engagement_users} users ({high_engagement_users/total_users*100:.1f}%) are highly engaged")
        
        if high_churn_risk / total_users > 0.2:
            insights.append(f"{high_churn_risk} users ({high_churn_risk/total_users*100:.1f}%) are at high churn risk")
        
        if daily_users / total_users > 0.5:
            insights.append(f"{daily_users} users ({daily_users/total_users*100:.1f}%) use the platform daily")
        
        # Generate recommendations
        recommendations = []
        if avg_engagement_score < 60:
            recommendations.append("Focus on improving user engagement through better onboarding and feature discovery")
        
        if high_churn_risk / total_users > 0.2:
            recommendations.append("Implement retention campaigns for users at high churn risk")
        
        if low_engagement_users / total_users > 0.4:
            recommendations.append("Create targeted campaigns to re-engage low-activity users")
        
        if avg_session_duration < 5:
            recommendations.append("Improve user experience to increase session duration")
        
        return BusinessIntelligenceReport(
            report_type="engagement",
            period=f"{days} days",
            key_metrics=key_metrics,
            insights=insights,
            recommendations=recommendations,
            trends={},
            generated_at=datetime.utcnow()
        )
    
    def get_predictive_insights(self, days: int = 30, environment: str = "production") -> Dict[str, Any]:
        """Generate predictive insights based on historical data"""
        try:
            with get_db_session() as db:
                start_time = datetime.utcnow() - timedelta(days=days)
                
                # Get historical data
                usage_data = db.query(FeatureUsageMetrics).filter(
                    FeatureUsageMetrics.timestamp >= start_time,
                    FeatureUsageMetrics.environment == environment
                ).all()
                
                if not usage_data:
                    return {"error": "Insufficient data for predictions"}
                
                # Group data by day
                daily_usage = defaultdict(int)
                daily_users = defaultdict(set)
                
                for usage in usage_data:
                    day = usage.timestamp.date()
                    daily_usage[day] += 1
                    if usage.user_id:
                        daily_users[day].add(usage.user_id)
                
                # Convert to lists for analysis
                days_list = sorted(daily_usage.keys())
                usage_counts = [daily_usage[day] for day in days_list]
                user_counts = [len(daily_users[day]) for day in days_list]
                
                # Simple trend analysis
                if len(usage_counts) >= 7:
                    recent_avg = statistics.mean(usage_counts[-7:])
                    older_avg = statistics.mean(usage_counts[:7])
                    
                    usage_trend = "increasing" if recent_avg > older_avg * 1.1 else "decreasing" if recent_avg < older_avg * 0.9 else "stable"
                    
                    # Predict next week's usage (simple linear projection)
                    if len(usage_counts) >= 14:
                        growth_rate = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
                        predicted_usage = recent_avg * (1 + growth_rate)
                    else:
                        predicted_usage = recent_avg
                else:
                    usage_trend = "insufficient_data"
                    predicted_usage = statistics.mean(usage_counts) if usage_counts else 0
                
                # Feature popularity predictions
                feature_usage = Counter(usage.feature_name for usage in usage_data)
                trending_features = feature_usage.most_common(5)
                
                return {
                    "usage_trend": usage_trend,
                    "predicted_daily_usage": predicted_usage,
                    "trending_features": trending_features,
                    "current_daily_average": statistics.mean(usage_counts) if usage_counts else 0,
                    "current_user_average": statistics.mean(user_counts) if user_counts else 0,
                    "prediction_confidence": "medium" if len(usage_counts) >= 14 else "low",
                    "generated_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error generating predictive insights: {str(e)}")
            return {"error": str(e)}

# Global service instance
advanced_analytics_service = AdvancedAnalyticsService()