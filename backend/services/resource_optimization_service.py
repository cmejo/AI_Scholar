"""
Resource Optimization Service for Enterprise Features
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import json
import statistics
from collections import defaultdict

from core.database import (
    get_db, Institution, ResourceUsage, User, UserRole, 
    Document, Message, Conversation, AnalyticsEvent
)

class ResourceOptimizationService:
    """Service for analyzing and optimizing resource usage patterns"""
    
    def __init__(self):
        self.resource_types = {
            'database_query': {'unit': 'queries', 'cost_per_unit': 0.001},
            'document_upload': {'unit': 'mb', 'cost_per_unit': 0.01},
            'ai_request': {'unit': 'requests', 'cost_per_unit': 0.05},
            'storage': {'unit': 'gb', 'cost_per_unit': 0.02},
            'bandwidth': {'unit': 'gb', 'cost_per_unit': 0.05}
        }
    
    async def analyze_usage_patterns(self, institution_id: str, 
                                   time_range: Optional[Dict[str, datetime]] = None) -> Dict[str, Any]:
        """Analyze usage patterns for library and database resources"""
        db = next(get_db())
        try:
            # Default to last 30 days if no time range specified
            if not time_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                time_range = {'start': start_date, 'end': end_date}
            
            # Get resource usage data
            usage_query = db.query(ResourceUsage).filter(
                and_(
                    ResourceUsage.institution_id == institution_id,
                    ResourceUsage.timestamp >= time_range['start'],
                    ResourceUsage.timestamp <= time_range['end']
                )
            )
            
            usage_records = usage_query.all()
            
            # Analyze patterns by resource type
            patterns_by_type = defaultdict(list)
            patterns_by_user = defaultdict(list)
            patterns_by_time = defaultdict(list)
            
            for record in usage_records:
                patterns_by_type[record.resource_type].append({
                    'amount': record.usage_amount,
                    'cost': record.cost or 0,
                    'timestamp': record.timestamp,
                    'user_id': record.user_id
                })
                
                patterns_by_user[record.user_id].append({
                    'resource_type': record.resource_type,
                    'amount': record.usage_amount,
                    'cost': record.cost or 0,
                    'timestamp': record.timestamp
                })
                
                # Group by hour of day for temporal patterns
                hour = record.timestamp.hour
                patterns_by_time[hour].append({
                    'resource_type': record.resource_type,
                    'amount': record.usage_amount,
                    'cost': record.cost or 0
                })
            
            # Calculate statistics
            usage_statistics = {}
            for resource_type, records in patterns_by_type.items():
                amounts = [r['amount'] for r in records]
                costs = [r['cost'] for r in records]
                
                usage_statistics[resource_type] = {
                    'total_usage': sum(amounts),
                    'total_cost': sum(costs),
                    'average_usage': statistics.mean(amounts) if amounts else 0,
                    'peak_usage': max(amounts) if amounts else 0,
                    'usage_count': len(amounts),
                    'cost_per_usage': sum(costs) / len(amounts) if amounts else 0
                }
            
            # Identify peak usage times
            peak_hours = {}
            for hour, records in patterns_by_time.items():
                total_usage = sum(r['amount'] for r in records)
                peak_hours[hour] = total_usage
            
            # Sort hours by usage
            sorted_peak_hours = sorted(peak_hours.items(), key=lambda x: x[1], reverse=True)
            
            # Identify heavy users
            user_usage = {}
            for user_id, records in patterns_by_user.items():
                total_cost = sum(r['cost'] for r in records)
                total_usage = sum(r['amount'] for r in records)
                user_usage[user_id] = {
                    'total_cost': total_cost,
                    'total_usage': total_usage,
                    'usage_count': len(records)
                }
            
            # Sort users by cost
            heavy_users = sorted(user_usage.items(), key=lambda x: x[1]['total_cost'], reverse=True)[:10]
            
            return {
                'analysis_period': {
                    'start': time_range['start'],
                    'end': time_range['end']
                },
                'usage_statistics': usage_statistics,
                'peak_usage_hours': sorted_peak_hours[:5],  # Top 5 peak hours
                'heavy_users': heavy_users,
                'total_records_analyzed': len(usage_records),
                'patterns_identified': {
                    'resource_types': len(patterns_by_type),
                    'active_users': len(patterns_by_user),
                    'time_periods': len(patterns_by_time)
                }
            }
            
        finally:
            db.close()
    
    async def optimize_resource_allocation(self, institution_id: str, 
                                         optimization_goals: Dict[str, Any]) -> Dict[str, Any]:
        """Build resource allocation optimization with cost-benefit analysis"""
        db = next(get_db())
        try:
            # Get current usage patterns
            usage_analysis = await self.analyze_usage_patterns(institution_id)
            
            # Get institution settings
            institution = db.query(Institution).filter(
                Institution.id == institution_id
            ).first()
            
            if not institution:
                raise ValueError("Institution not found")
            
            current_settings = institution.settings or {}
            budget_limit = optimization_goals.get('budget_limit', current_settings.get('budget_limit', 1000))
            performance_target = optimization_goals.get('performance_target', 'balanced')  # 'cost', 'performance', 'balanced'
            
            # Calculate current costs
            current_total_cost = sum(
                stats['total_cost'] for stats in usage_analysis['usage_statistics'].values()
            )
            
            # Generate optimization recommendations
            recommendations = []
            potential_savings = 0
            
            # Analyze each resource type for optimization opportunities
            for resource_type, stats in usage_analysis['usage_statistics'].items():
                resource_config = self.resource_types.get(resource_type, {})
                
                # Check for over-provisioning
                if stats['peak_usage'] < stats['average_usage'] * 0.5:
                    savings = stats['total_cost'] * 0.2  # Potential 20% savings
                    recommendations.append({
                        'type': 'reduce_allocation',
                        'resource': resource_type,
                        'current_cost': stats['total_cost'],
                        'recommended_reduction': '20%',
                        'potential_savings': savings,
                        'reason': 'Low peak usage indicates over-provisioning'
                    })
                    potential_savings += savings
                
                # Check for high cost per usage
                avg_cost_per_unit = resource_config.get('cost_per_unit', 0)
                if stats['cost_per_usage'] > avg_cost_per_unit * 1.5:
                    savings = stats['total_cost'] * 0.15  # Potential 15% savings
                    recommendations.append({
                        'type': 'optimize_usage',
                        'resource': resource_type,
                        'current_cost': stats['total_cost'],
                        'recommended_action': 'Implement usage optimization',
                        'potential_savings': savings,
                        'reason': 'High cost per usage suggests inefficient usage patterns'
                    })
                    potential_savings += savings
            
            # Check for temporal optimization opportunities
            peak_hours = usage_analysis['peak_usage_hours']
            if len(peak_hours) > 0:
                # Suggest load balancing
                peak_hour, peak_usage = peak_hours[0]
                if peak_usage > sum(hour_usage for _, hour_usage in peak_hours[1:5]) / 4 * 2:
                    recommendations.append({
                        'type': 'load_balancing',
                        'resource': 'all_resources',
                        'current_peak_hour': peak_hour,
                        'recommended_action': 'Implement load balancing to distribute usage',
                        'potential_savings': current_total_cost * 0.1,
                        'reason': f'High concentration of usage at hour {peak_hour}'
                    })
                    potential_savings += current_total_cost * 0.1
            
            # User-based optimizations
            heavy_users = usage_analysis['heavy_users']
            if len(heavy_users) > 0:
                top_user_id, top_user_stats = heavy_users[0]
                if top_user_stats['total_cost'] > current_total_cost * 0.3:
                    recommendations.append({
                        'type': 'user_optimization',
                        'resource': 'user_behavior',
                        'user_id': top_user_id,
                        'current_cost': top_user_stats['total_cost'],
                        'recommended_action': 'Provide usage optimization training',
                        'potential_savings': top_user_stats['total_cost'] * 0.2,
                        'reason': 'Single user accounts for >30% of total costs'
                    })
                    potential_savings += top_user_stats['total_cost'] * 0.2
            
            # Calculate ROI for each recommendation
            for rec in recommendations:
                if rec['potential_savings'] > 0:
                    implementation_cost = rec['potential_savings'] * 0.1  # Assume 10% implementation cost
                    rec['roi'] = (rec['potential_savings'] - implementation_cost) / implementation_cost * 100
                    rec['implementation_cost'] = implementation_cost
            
            # Sort recommendations by ROI
            recommendations.sort(key=lambda x: x.get('roi', 0), reverse=True)
            
            # Generate optimized allocation plan
            optimized_allocation = await self._generate_allocation_plan(
                institution_id, recommendations, budget_limit, performance_target, db
            )
            
            return {
                'current_cost': current_total_cost,
                'budget_limit': budget_limit,
                'potential_savings': potential_savings,
                'optimization_recommendations': recommendations,
                'optimized_allocation': optimized_allocation,
                'cost_benefit_analysis': {
                    'total_implementation_cost': sum(r.get('implementation_cost', 0) for r in recommendations),
                    'total_potential_savings': potential_savings,
                    'net_benefit': potential_savings - sum(r.get('implementation_cost', 0) for r in recommendations),
                    'payback_period_months': 1 if potential_savings > 0 else float('inf')
                }
            }
            
        finally:
            db.close()
    
    async def forecast_usage(self, institution_id: str, forecast_period_days: int = 30) -> Dict[str, Any]:
        """Create usage forecasting and capacity planning tools"""
        db = next(get_db())
        try:
            # Get historical data for forecasting (last 90 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            usage_records = db.query(ResourceUsage).filter(
                and_(
                    ResourceUsage.institution_id == institution_id,
                    ResourceUsage.timestamp >= start_date,
                    ResourceUsage.timestamp <= end_date
                )
            ).order_by(ResourceUsage.timestamp).all()
            
            if not usage_records:
                return {
                    'forecast_period_days': forecast_period_days,
                    'forecasts': {},
                    'capacity_recommendations': [],
                    'confidence': 0,
                    'message': 'Insufficient historical data for forecasting'
                }
            
            # Group data by resource type and day
            daily_usage = defaultdict(lambda: defaultdict(float))
            
            for record in usage_records:
                day = record.timestamp.date()
                daily_usage[record.resource_type][day] += record.usage_amount
            
            # Generate forecasts for each resource type
            forecasts = {}
            capacity_recommendations = []
            
            for resource_type, daily_data in daily_usage.items():
                # Simple linear trend forecasting
                days = sorted(daily_data.keys())
                usage_values = [daily_data[day] for day in days]
                
                if len(usage_values) < 7:  # Need at least a week of data
                    continue
                
                # Calculate trend
                x_values = list(range(len(usage_values)))
                trend = self._calculate_linear_trend(x_values, usage_values)
                
                # Forecast future usage
                forecast_days = []
                forecast_values = []
                
                for i in range(forecast_period_days):
                    future_day = end_date.date() + timedelta(days=i+1)
                    future_x = len(usage_values) + i
                    forecast_value = max(0, trend['slope'] * future_x + trend['intercept'])
                    
                    forecast_days.append(future_day)
                    forecast_values.append(forecast_value)
                
                # Calculate confidence based on trend consistency
                recent_values = usage_values[-14:]  # Last 2 weeks
                variance = statistics.variance(recent_values) if len(recent_values) > 1 else 0
                mean_usage = statistics.mean(recent_values)
                confidence = max(0, min(100, 100 - (variance / mean_usage * 100) if mean_usage > 0 else 0))
                
                forecasts[resource_type] = {
                    'historical_average': mean_usage,
                    'trend_slope': trend['slope'],
                    'forecast_values': forecast_values,
                    'forecast_days': [day.isoformat() for day in forecast_days],
                    'confidence_score': confidence,
                    'peak_forecast': max(forecast_values) if forecast_values else 0,
                    'total_forecast': sum(forecast_values)
                }
                
                # Generate capacity recommendations
                peak_forecast = max(forecast_values) if forecast_values else 0
                current_peak = max(usage_values[-7:]) if len(usage_values) >= 7 else mean_usage
                
                if peak_forecast > current_peak * 1.2:
                    capacity_recommendations.append({
                        'resource_type': resource_type,
                        'recommendation': 'increase_capacity',
                        'current_peak': current_peak,
                        'forecast_peak': peak_forecast,
                        'recommended_increase': f"{((peak_forecast / current_peak - 1) * 100):.1f}%",
                        'urgency': 'high' if peak_forecast > current_peak * 1.5 else 'medium'
                    })
                elif peak_forecast < current_peak * 0.8:
                    capacity_recommendations.append({
                        'resource_type': resource_type,
                        'recommendation': 'reduce_capacity',
                        'current_peak': current_peak,
                        'forecast_peak': peak_forecast,
                        'recommended_reduction': f"{((1 - peak_forecast / current_peak) * 100):.1f}%",
                        'urgency': 'low'
                    })
            
            # Calculate overall confidence
            overall_confidence = statistics.mean([
                f['confidence_score'] for f in forecasts.values()
            ]) if forecasts else 0
            
            return {
                'forecast_period_days': forecast_period_days,
                'forecasts': forecasts,
                'capacity_recommendations': capacity_recommendations,
                'overall_confidence': overall_confidence,
                'data_points_analyzed': len(usage_records),
                'forecast_generated_at': datetime.now()
            }
            
        finally:
            db.close()
    
    async def recommend_resources(self, institution_id: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Add resource recommendation system for efficient utilization"""
        db = next(get_db())
        try:
            user_id = user_context.get('user_id')
            user_role = user_context.get('role', 'student')
            department = user_context.get('department')
            current_usage = user_context.get('current_usage', {})
            
            # Get user's historical usage patterns
            user_usage = db.query(ResourceUsage).filter(
                and_(
                    ResourceUsage.user_id == user_id,
                    ResourceUsage.institution_id == institution_id,
                    ResourceUsage.timestamp >= datetime.now() - timedelta(days=30)
                )
            ).all()
            
            # Get similar users' usage patterns (same role and department)
            similar_users_query = db.query(UserRole).filter(
                and_(
                    UserRole.institution_id == institution_id,
                    UserRole.role_name == user_role,
                    UserRole.department == department,
                    UserRole.user_id != user_id
                )
            )
            
            similar_user_ids = [ur.user_id for ur in similar_users_query.all()]
            
            similar_usage = db.query(ResourceUsage).filter(
                and_(
                    ResourceUsage.user_id.in_(similar_user_ids),
                    ResourceUsage.institution_id == institution_id,
                    ResourceUsage.timestamp >= datetime.now() - timedelta(days=30)
                )
            ).all() if similar_user_ids else []
            
            # Analyze user's usage patterns
            user_patterns = defaultdict(list)
            for usage in user_usage:
                user_patterns[usage.resource_type].append(usage.usage_amount)
            
            # Analyze similar users' patterns
            similar_patterns = defaultdict(list)
            for usage in similar_usage:
                similar_patterns[usage.resource_type].append(usage.usage_amount)
            
            # Generate recommendations
            recommendations = []
            
            for resource_type in self.resource_types.keys():
                user_avg = statistics.mean(user_patterns[resource_type]) if user_patterns[resource_type] else 0
                similar_avg = statistics.mean(similar_patterns[resource_type]) if similar_patterns[resource_type] else 0
                
                # Compare usage patterns
                if similar_avg > 0:
                    usage_ratio = user_avg / similar_avg
                    
                    if usage_ratio < 0.5:  # User is using much less than peers
                        recommendations.append({
                            'type': 'underutilization',
                            'resource': resource_type,
                            'current_usage': user_avg,
                            'peer_average': similar_avg,
                            'recommendation': f'Consider increasing {resource_type} usage to match peer levels',
                            'potential_benefit': 'Improved productivity and research outcomes',
                            'priority': 'medium'
                        })
                    elif usage_ratio > 2.0:  # User is using much more than peers
                        recommendations.append({
                            'type': 'overutilization',
                            'resource': resource_type,
                            'current_usage': user_avg,
                            'peer_average': similar_avg,
                            'recommendation': f'Consider optimizing {resource_type} usage patterns',
                            'potential_benefit': 'Cost savings and improved efficiency',
                            'priority': 'high'
                        })
                
                # Check for missing resource usage
                if user_avg == 0 and similar_avg > 0:
                    recommendations.append({
                        'type': 'missing_resource',
                        'resource': resource_type,
                        'current_usage': 0,
                        'peer_average': similar_avg,
                        'recommendation': f'Consider utilizing {resource_type} resources',
                        'potential_benefit': 'Access to additional research capabilities',
                        'priority': 'low'
                    })
            
            # Add role-specific recommendations
            role_recommendations = await self._get_role_specific_recommendations(
                user_role, department, user_patterns, db
            )
            recommendations.extend(role_recommendations)
            
            # Sort by priority
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
            
            return {
                'user_id': user_id,
                'user_role': user_role,
                'department': department,
                'recommendations': recommendations,
                'peer_comparison': {
                    'similar_users_count': len(similar_user_ids),
                    'comparison_period_days': 30
                },
                'generated_at': datetime.now()
            }
            
        finally:
            db.close()
    
    async def _generate_allocation_plan(self, institution_id: str, recommendations: List[Dict], 
                                      budget_limit: float, performance_target: str, db: Session) -> Dict[str, Any]:
        """Generate optimized resource allocation plan"""
        
        # Get current allocation
        current_usage = db.query(ResourceUsage).filter(
            and_(
                ResourceUsage.institution_id == institution_id,
                ResourceUsage.timestamp >= datetime.now() - timedelta(days=30)
            )
        ).all()
        
        current_allocation = defaultdict(float)
        for usage in current_usage:
            current_allocation[usage.resource_type] += usage.cost or 0
        
        # Apply recommendations based on performance target
        optimized_allocation = dict(current_allocation)
        
        for rec in recommendations:
            if rec['type'] == 'reduce_allocation':
                resource = rec['resource']
                reduction = optimized_allocation[resource] * 0.2
                optimized_allocation[resource] -= reduction
            elif rec['type'] == 'optimize_usage':
                resource = rec['resource']
                optimization = optimized_allocation[resource] * 0.15
                optimized_allocation[resource] -= optimization
        
        # Ensure budget compliance
        total_optimized = sum(optimized_allocation.values())
        if total_optimized > budget_limit:
            # Scale down proportionally
            scale_factor = budget_limit / total_optimized
            for resource in optimized_allocation:
                optimized_allocation[resource] *= scale_factor
        
        return {
            'current_allocation': dict(current_allocation),
            'optimized_allocation': dict(optimized_allocation),
            'total_current_cost': sum(current_allocation.values()),
            'total_optimized_cost': sum(optimized_allocation.values()),
            'budget_limit': budget_limit,
            'budget_utilization': sum(optimized_allocation.values()) / budget_limit * 100
        }
    
    def _calculate_linear_trend(self, x_values: List[int], y_values: List[float]) -> Dict[str, float]:
        """Calculate linear trend using least squares method"""
        n = len(x_values)
        if n < 2:
            return {'slope': 0, 'intercept': statistics.mean(y_values) if y_values else 0}
        
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        
        return {'slope': slope, 'intercept': intercept}
    
    async def _get_role_specific_recommendations(self, role: str, department: str, 
                                               user_patterns: Dict, db: Session) -> List[Dict[str, Any]]:
        """Get role-specific resource recommendations"""
        recommendations = []
        
        if role == 'student':
            # Students should focus on learning resources
            if not user_patterns.get('ai_request'):
                recommendations.append({
                    'type': 'role_specific',
                    'resource': 'ai_request',
                    'recommendation': 'Consider using AI assistance for research and learning',
                    'potential_benefit': 'Enhanced learning and research productivity',
                    'priority': 'medium'
                })
        
        elif role == 'faculty':
            # Faculty should have balanced resource usage
            if not user_patterns.get('database_query'):
                recommendations.append({
                    'type': 'role_specific',
                    'resource': 'database_query',
                    'recommendation': 'Utilize database resources for research',
                    'potential_benefit': 'Access to comprehensive research data',
                    'priority': 'high'
                })
        
        elif role == 'admin':
            # Admins should monitor all resource types
            recommendations.append({
                'type': 'role_specific',
                'resource': 'monitoring',
                'recommendation': 'Regular monitoring of institutional resource usage',
                'potential_benefit': 'Better resource management and cost control',
                'priority': 'high'
            })
        
        return recommendations