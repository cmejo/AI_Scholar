"""
Analytics models and schemas
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class DailyActivity(BaseModel):
    date: str
    users: int
    messages: int

class ContentItem(BaseModel):
    title: str
    views: int
    engagement: int

class PerformanceMetrics(BaseModel):
    uptime: float
    error_rate: float
    avg_load_time: int

class AnalyticsData(BaseModel):
    total_users: int
    active_users: int
    total_messages: int
    avg_response_time: int
    user_growth: float
    message_growth: float
    daily_activity: List[DailyActivity]
    top_content: List[ContentItem]
    performance_metrics: PerformanceMetrics

class UserMetrics(BaseModel):
    user_id: str
    total_sessions: int
    total_messages: int
    avg_session_duration: float
    last_active: datetime
    favorite_features: List[str]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class SystemMetrics(BaseModel):
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_connections: int
    response_time_avg: float
    error_count: int
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class EventData(BaseModel):
    event: str
    properties: Dict[str, Any]
    timestamp: Optional[datetime] = None