"""
Analytics service for collecting and providing analytics data
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from core.database import SessionLocal
from analytics.models import AnalyticsData, DailyActivity, ContentItem, PerformanceMetrics, UserMetrics, SystemMetrics

class AnalyticsService:
    """Service for analytics data collection and retrieval"""
    
    def __init__(self):
        pass
    
    def get_db(self) -> Session:
        """Get database session"""
        return SessionLocal()
    
    def get_dashboard_analytics(self, time_range: str = "30d") -> AnalyticsData:
        """Get analytics data for dashboard"""
        db = self.get_db()
        try:
            # Parse time range
            days = self._parse_time_range(time_range)
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get user statistics
            try:
                from core.database import User
                total_users = db.query(User).count()
                
                # Check if User has last_login attribute
                if hasattr(User, 'last_login'):
                    active_users = db.query(User).filter(
                        User.last_login >= start_date
                    ).count()
                else:
                    active_users = int(total_users * 0.7)
            except Exception as e:
                print(f"Database query error: {e}")
                total_users = 150  # Mock value
                active_users = 105  # Mock value
            
            # Get message statistics
            try:
                from core.database import Message
                total_messages = db.query(Message).count()
            except Exception as e:
                print(f"Message query error: {e}")
                total_messages = 2500  # Mock value
            
            # Calculate growth rates (mock for now)
            user_growth = self._calculate_growth_rate(total_users, days)
            message_growth = self._calculate_growth_rate(total_messages, days)
            
            # Get daily activity data
            daily_activity = self._get_daily_activity(db, days)
            
            # Get top content
            top_content = self._get_top_content(db)
            
            # Get performance metrics
            performance_metrics = self._get_performance_metrics()
            
            return AnalyticsData(
                total_users=total_users,
                active_users=active_users,
                total_messages=total_messages,
                avg_response_time=150,  # Mock value
                user_growth=user_growth,
                message_growth=message_growth,
                daily_activity=daily_activity,
                top_content=top_content,
                performance_metrics=performance_metrics
            )
        finally:
            db.close()
    
    def track_event(self, user_id: Optional[str], event: str, properties: Dict[str, Any]):
        """Track an analytics event"""
        db = self.get_db()
        try:
            from core.database import AnalyticsEvent
            
            # Create analytics event record
            event_record = AnalyticsEvent(
                user_id=user_id,
                event_type=event,
                event_data=properties,
                timestamp=datetime.utcnow()
            )
            db.add(event_record)
            db.commit()
        except Exception as e:
            print(f"Error tracking event: {e}")
            db.rollback()
        finally:
            db.close()
    
    def get_user_metrics(self, user_id: str) -> UserMetrics:
        """Get metrics for a specific user"""
        db = self.get_db()
        try:
            from core.database import User, Message, Conversation, AnalyticsEvent
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Get user's conversations and messages
            user_conversations = db.query(Conversation).filter(
                Conversation.user_id == user_id
            ).count() if hasattr(Conversation, 'user_id') else 0
            
            user_messages = db.query(Message).join(Conversation).filter(
                Conversation.user_id == user_id
            ).count() if hasattr(Conversation, 'user_id') else 0
            
            # Get last active time, ensuring it's a datetime object
            last_active = user.last_login if hasattr(user, 'last_login') and user.last_login else user.created_at
            if not last_active:
                last_active = datetime.utcnow()
            
            # Mock additional metrics
            return UserMetrics(
                user_id=user_id,
                total_sessions=user_conversations,
                total_messages=user_messages,
                avg_session_duration=15.5,  # minutes
                last_active=last_active,
                favorite_features=["chat", "documents", "analytics"]
            )
        finally:
            db.close()
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        try:
            import psutil
            
            return SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_usage=psutil.cpu_percent(),
                memory_usage=psutil.virtual_memory().percent,
                disk_usage=psutil.disk_usage('/').percent,
                active_connections=len(psutil.net_connections()),
                response_time_avg=150.0,  # Mock value
                error_count=0  # Mock value
            )
        except Exception:
            # Fallback if psutil is not available
            return SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_usage=45.0,
                memory_usage=68.0,
                disk_usage=23.0,
                active_connections=12,
                response_time_avg=150.0,
                error_count=0
            )
    
    def export_analytics_data(self, time_range: str = "30d", format: str = "csv") -> str:
        """Export analytics data in specified format"""
        analytics_data = self.get_dashboard_analytics(time_range)
        
        if format.lower() == "csv":
            return self._export_to_csv(analytics_data)
        elif format.lower() == "json":
            return analytics_data.json(indent=2)
        else:
            raise ValueError("Unsupported export format")
    
    def _parse_time_range(self, time_range: str) -> int:
        """Parse time range string to days"""
        if time_range == "7d":
            return 7
        elif time_range == "30d":
            return 30
        elif time_range == "90d":
            return 90
        else:
            return 30
    
    def _calculate_growth_rate(self, current_value: int, days: int) -> float:
        """Calculate mock growth rate"""
        # Mock calculation - in real implementation, compare with previous period
        base_rate = 5.0  # Base growth rate
        variation = (days / 30) * 2  # Vary based on time range
        return base_rate + variation
    
    def _get_daily_activity(self, db: Session, days: int) -> List[DailyActivity]:
        """Get daily activity data"""
        daily_data = []
        
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=days - 1 - i)
            
            # Mock data generation - in real implementation, query actual data
            base_users = 50 + (i * 2)
            base_messages = 100 + (i * 5)
            
            # Add some randomness
            import random
            users = base_users + random.randint(-10, 20)
            messages = base_messages + random.randint(-20, 50)
            
            daily_data.append(DailyActivity(
                date=date.strftime("%Y-%m-%d"),
                users=max(0, users),
                messages=max(0, messages)
            ))
        
        return daily_data
    
    def _get_top_content(self, db: Session) -> List[ContentItem]:
        """Get top content items"""
        # Mock data - in real implementation, query actual content metrics
        content_items = [
            ContentItem(title="AI Research Paper Analysis", views=1250, engagement=85),
            ContentItem(title="Machine Learning Discussion", views=980, engagement=72),
            ContentItem(title="Data Science Workflow", views=856, engagement=68),
            ContentItem(title="Natural Language Processing", views=743, engagement=91),
            ContentItem(title="Computer Vision Tutorial", views=692, engagement=64),
            ContentItem(title="Deep Learning Concepts", views=587, engagement=78),
            ContentItem(title="Statistical Analysis Guide", views=534, engagement=56),
            ContentItem(title="Research Methodology", views=489, engagement=82),
            ContentItem(title="Academic Writing Tips", views=445, engagement=59),
            ContentItem(title="Citation Management", views=398, engagement=73),
        ]
        
        return content_items
    
    def _get_performance_metrics(self) -> PerformanceMetrics:
        """Get system performance metrics"""
        import random
        
        return PerformanceMetrics(
            uptime=99.8 + random.uniform(-0.2, 0.2),
            error_rate=random.uniform(0.0, 0.3),
            avg_load_time=random.randint(120, 200)
        )
    
    def _export_to_csv(self, analytics_data: AnalyticsData) -> str:
        """Export analytics data to CSV format"""
        import io
        import csv
        
        output = io.StringIO()
        
        # Write summary data
        writer = csv.writer(output)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Users", analytics_data.total_users])
        writer.writerow(["Active Users", analytics_data.active_users])
        writer.writerow(["Total Messages", analytics_data.total_messages])
        writer.writerow(["Avg Response Time", analytics_data.avg_response_time])
        writer.writerow(["User Growth", f"{analytics_data.user_growth}%"])
        writer.writerow(["Message Growth", f"{analytics_data.message_growth}%"])
        writer.writerow([])
        
        # Write daily activity data
        writer.writerow(["Daily Activity"])
        writer.writerow(["Date", "Users", "Messages"])
        for activity in analytics_data.daily_activity:
            writer.writerow([activity.date, activity.users, activity.messages])
        writer.writerow([])
        
        # Write top content data
        writer.writerow(["Top Content"])
        writer.writerow(["Title", "Views", "Engagement"])
        for content in analytics_data.top_content:
            writer.writerow([content.title, content.views, content.engagement])
        
        return output.getvalue()

# Global analytics service instance
analytics_service = AnalyticsService()