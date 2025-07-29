"""
Research Memory Engine
Maintains persistent research context across sessions and projects,
enabling seamless continuation of research work and intelligent context switching.
"""
import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, or_

from core.database import get_db
from core.advanced_research_models import (
    ResearchProject, ResearchContext, ResearchTimeline,
    ResearchMilestone, QAReport
)
from services.advanced_analytics import AdvancedAnalyticsService

logger = logging.getLogger(__name__)

class ProjectStatus(str, Enum):
    """Research project status types"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class TimelineEventType(str, Enum):
    """Research timeline event types"""
    PROJECT_CREATED = "project_created"
    DOCUMENT_ADDED = "document_added"
    INSIGHT_GENERATED = "insight_generated"
    MILESTONE_REACHED = "milestone_reached"
    CONTEXT_SWITCHED = "context_switched"
    COLLABORATION_STARTED = "collaboration_started"
    ANALYSIS_COMPLETED = "analysis_completed"

@dataclass
class ResearchContextData:
    """Research context data structure"""
    project_id: str
    user_id: str
    session_id: str
    active_documents: List[str]
    current_queries: List[str]
    research_focus: str
    insights_generated: List[Dict[str, Any]]
    context_metadata: Dict[str, Any]
    session_timestamp: datetime
    is_active: bool

@dataclass
class ResearchProjectSummary:
    """Research project summary for quick overview"""
    id: str
    title: str
    description: str
    research_domain: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    document_count: int
    insight_count: int
    milestone_progress: float
    last_activity: datetime

@dataclass
class ResearchTimelineEvent:
    """Research timeline event"""
    id: str
    project_id: str
    event_type: TimelineEventType
    event_description: str
    event_data: Dict[str, Any]
    timestamp: datetime

@dataclass
class ContextSwitchRecommendation:
    """Context switch recommendation"""
    target_project_id: str
    target_project_title: str
    relevance_score: float
    switch_reason: str
    related_insights: List[str]
    estimated_context_load_time: int

class ResearchMemoryEngine:
    """Main research memory engine service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.analytics_service = AdvancedAnalyticsService(db)
        
        # Context cache for active sessions
        self.active_contexts: Dict[str, ResearchContextData] = {}
        
        # Context switching intelligence
        self.context_switch_patterns: Dict[str, List[str]] = {}
        
        # Timeline analysis cache
        self.timeline_cache: Dict[str, List[ResearchTimelineEvent]] = {}

    async def create_research_project(
        self,
        user_id: str,
        title: str,
        description: str = "",
        research_domain: str = "general"
    ) -> ResearchProject:
        """Create a new research project"""
        try:
            project = ResearchProject(
                user_id=user_id,
                title=title,
                description=description,
                research_domain=research_domain,
                status=ProjectStatus.ACTIVE.value
            )
            
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
            
            # Create initial timeline event
            await self._add_timeline_event(
                project_id=str(project.id),
                event_type=TimelineEventType.PROJECT_CREATED,
                event_description=f"Research project '{title}' created",
                event_data={"domain": research_domain}
            )
            
            logger.info(f"Created research project {project.id} for user {user_id}")
            return project
            
        except Exception as e:
            logger.error(f"Error creating research project: {str(e)}")
            self.db.rollback()
            raise

    async def save_research_context(
        self,
        user_id: str,
        project_id: str,
        context_data: Dict[str, Any]
    ) -> bool:
        """Save current research context for future sessions"""
        try:
            session_id = context_data.get("session_id", str(uuid.uuid4()))
            
            # Create context record
            context = ResearchContext(
                project_id=project_id,
                user_id=user_id,
                session_id=session_id,
                active_documents=context_data.get("active_documents", []),
                current_queries=context_data.get("current_queries", []),
                research_focus=context_data.get("research_focus", ""),
                insights_generated=context_data.get("insights_generated", []),
                context_metadata=context_data.get("metadata", {}),
                session_timestamp=datetime.utcnow(),
                is_active=True
            )
            
            # Deactivate previous contexts for this project
            self.db.query(ResearchContext).filter(
                and_(
                    ResearchContext.project_id == project_id,
                    ResearchContext.user_id == user_id,
                    ResearchContext.is_active == True
                )
            ).update({"is_active": False})
            
            self.db.add(context)
            self.db.commit()
            
            # Cache the context
            context_data_obj = ResearchContextData(
                project_id=project_id,
                user_id=user_id,
                session_id=session_id,
                active_documents=context_data.get("active_documents", []),
                current_queries=context_data.get("current_queries", []),
                research_focus=context_data.get("research_focus", ""),
                insights_generated=context_data.get("insights_generated", []),
                context_metadata=context_data.get("metadata", {}),
                session_timestamp=datetime.utcnow(),
                is_active=True
            )
            
            self.active_contexts[f"{user_id}_{project_id}"] = context_data_obj
            
            # Update project timestamp
            self.db.query(ResearchProject).filter(
                ResearchProject.id == project_id
            ).update({"updated_at": datetime.utcnow()})
            
            self.db.commit()
            
            logger.info(f"Saved research context for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving research context: {str(e)}")
            self.db.rollback()
            return False

    async def restore_research_context(
        self,
        user_id: str,
        project_id: str
    ) -> Optional[ResearchContextData]:
        """Restore previous research context"""
        try:
            # Check cache first
            cache_key = f"{user_id}_{project_id}"
            if cache_key in self.active_contexts:
                return self.active_contexts[cache_key]
            
            # Get latest context from database
            context = self.db.query(ResearchContext).filter(
                and_(
                    ResearchContext.project_id == project_id,
                    ResearchContext.user_id == user_id
                )
            ).order_by(desc(ResearchContext.session_timestamp)).first()
            
            if not context:
                return None
            
            # Convert to data structure
            context_data = ResearchContextData(
                project_id=str(context.project_id),
                user_id=str(context.user_id),
                session_id=context.session_id,
                active_documents=context.active_documents or [],
                current_queries=context.current_queries or [],
                research_focus=context.research_focus or "",
                insights_generated=context.insights_generated or [],
                context_metadata=context.context_metadata or {},
                session_timestamp=context.session_timestamp,
                is_active=context.is_active
            )
            
            # Cache the context
            self.active_contexts[cache_key] = context_data
            
            logger.info(f"Restored research context for project {project_id}")
            return context_data
            
        except Exception as e:
            logger.error(f"Error restoring research context: {str(e)}")
            return None

    async def list_research_projects(
        self,
        user_id: str,
        status_filter: Optional[ProjectStatus] = None,
        limit: int = 50
    ) -> List[ResearchProjectSummary]:
        """List user's research projects with summaries"""
        try:
            query = self.db.query(ResearchProject).filter(
                ResearchProject.user_id == user_id
            )
            
            if status_filter:
                query = query.filter(ResearchProject.status == status_filter.value)
            
            projects = query.order_by(desc(ResearchProject.updated_at)).limit(limit).all()
            
            summaries = []
            for project in projects:
                # Get project statistics
                document_count = await self._get_project_document_count(str(project.id))
                insight_count = await self._get_project_insight_count(str(project.id))
                milestone_progress = await self._get_milestone_progress(str(project.id))
                last_activity = await self._get_last_activity_time(str(project.id))
                
                summary = ResearchProjectSummary(
                    id=str(project.id),
                    title=project.title,
                    description=project.description or "",
                    research_domain=project.research_domain or "general",
                    status=ProjectStatus(project.status),
                    created_at=project.created_at,
                    updated_at=project.updated_at,
                    document_count=document_count,
                    insight_count=insight_count,
                    milestone_progress=milestone_progress,
                    last_activity=last_activity
                )
                summaries.append(summary)
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error listing research projects: {str(e)}")
            return []

    async def switch_project_context(
        self,
        user_id: str,
        from_project_id: str,
        to_project_id: str
    ) -> bool:
        """Switch between research project contexts"""
        try:
            # Save current context if active
            if from_project_id:
                current_context = self.active_contexts.get(f"{user_id}_{from_project_id}")
                if current_context:
                    await self.save_research_context(
                        user_id=user_id,
                        project_id=from_project_id,
                        context_data=asdict(current_context)
                    )
            
            # Load new context
            new_context = await self.restore_research_context(user_id, to_project_id)
            
            if new_context:
                # Record context switch event
                await self._add_timeline_event(
                    project_id=to_project_id,
                    event_type=TimelineEventType.CONTEXT_SWITCHED,
                    event_description=f"Switched to project context",
                    event_data={
                        "from_project": from_project_id,
                        "to_project": to_project_id,
                        "switch_time": datetime.utcnow().isoformat()
                    }
                )
                
                # Update context switching patterns for recommendations
                await self._update_context_switch_patterns(
                    user_id, from_project_id, to_project_id
                )
                
                logger.info(f"Switched context from {from_project_id} to {to_project_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error switching project context: {str(e)}")
            return False

    async def generate_research_timeline(
        self,
        user_id: str,
        project_id: str,
        days_back: int = 30
    ) -> List[ResearchTimelineEvent]:
        """Generate comprehensive research timeline"""
        try:
            # Check cache first
            cache_key = f"{project_id}_{days_back}"
            if cache_key in self.timeline_cache:
                cached_timeline = self.timeline_cache[cache_key]
                # Return cached if less than 1 hour old
                if cached_timeline and (datetime.utcnow() - cached_timeline[0].timestamp).seconds < 3600:
                    return cached_timeline
            
            # Get timeline events from database
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            timeline_records = self.db.query(ResearchTimeline).filter(
                and_(
                    ResearchTimeline.project_id == project_id,
                    ResearchTimeline.timestamp >= cutoff_date
                )
            ).order_by(desc(ResearchTimeline.timestamp)).all()
            
            # Convert to timeline events
            timeline_events = []
            for record in timeline_records:
                event = ResearchTimelineEvent(
                    id=str(record.id),
                    project_id=str(record.project_id),
                    event_type=TimelineEventType(record.event_type),
                    event_description=record.event_description,
                    event_data=record.event_data or {},
                    timestamp=record.timestamp
                )
                timeline_events.append(event)
            
            # Enhance timeline with analytics insights
            enhanced_timeline = await self._enhance_timeline_with_insights(
                timeline_events, user_id, project_id
            )
            
            # Cache the timeline
            self.timeline_cache[cache_key] = enhanced_timeline
            
            return enhanced_timeline
            
        except Exception as e:
            logger.error(f"Error generating research timeline: {str(e)}")
            return []

    async def suggest_context_switch(
        self,
        user_id: str,
        current_project_id: str
    ) -> List[ContextSwitchRecommendation]:
        """Suggest relevant context switches based on current work"""
        try:
            # Get current context
            current_context = await self.restore_research_context(user_id, current_project_id)
            if not current_context:
                return []
            
            # Get all user projects
            projects = await self.list_research_projects(user_id)
            
            recommendations = []
            for project in projects:
                if project.id == current_project_id:
                    continue
                
                # Calculate relevance score
                relevance_score = await self._calculate_context_relevance(
                    current_context, project
                )
                
                if relevance_score > 0.3:  # Threshold for recommendations
                    # Get related insights
                    related_insights = await self._find_related_insights(
                        current_context, project.id
                    )
                    
                    # Estimate context load time
                    load_time = await self._estimate_context_load_time(project.id)
                    
                    recommendation = ContextSwitchRecommendation(
                        target_project_id=project.id,
                        target_project_title=project.title,
                        relevance_score=relevance_score,
                        switch_reason=await self._generate_switch_reason(
                            current_context, project
                        ),
                        related_insights=related_insights,
                        estimated_context_load_time=load_time
                    )
                    recommendations.append(recommendation)
            
            # Sort by relevance score
            recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return recommendations[:5]  # Return top 5 recommendations
            
        except Exception as e:
            logger.error(f"Error suggesting context switch: {str(e)}")
            return []

    async def get_project_insights_summary(
        self,
        user_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive insights summary for a project"""
        try:
            # Get project details
            project = self.db.query(ResearchProject).filter(
                and_(
                    ResearchProject.id == project_id,
                    ResearchProject.user_id == user_id
                )
            ).first()
            
            if not project:
                return {}
            
            # Get latest context
            context = await self.restore_research_context(user_id, project_id)
            
            # Get timeline summary
            timeline = await self.generate_research_timeline(user_id, project_id, days_back=7)
            
            # Get analytics insights
            analytics_insights = await self.analytics_service.generate_insights(
                user_id, context="project_summary"
            )
            
            # Compile summary
            summary = {
                "project_id": project_id,
                "project_title": project.title,
                "status": project.status,
                "last_updated": project.updated_at.isoformat(),
                "current_focus": context.research_focus if context else "",
                "active_documents": len(context.active_documents) if context else 0,
                "recent_insights": context.insights_generated[-5:] if context else [],
                "recent_activity": [
                    {
                        "type": event.event_type.value,
                        "description": event.event_description,
                        "timestamp": event.timestamp.isoformat()
                    }
                    for event in timeline[:10]
                ],
                "analytics_insights": analytics_insights[:3],  # Top 3 insights
                "research_domain": project.research_domain,
                "progress_indicators": await self._get_progress_indicators(project_id)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting project insights summary: {str(e)}")
            return {}

    # Helper methods
    async def _add_timeline_event(
        self,
        project_id: str,
        event_type: TimelineEventType,
        event_description: str,
        event_data: Dict[str, Any] = None
    ):
        """Add event to research timeline"""
        try:
            from core.advanced_research_models import ResearchTimeline
            
            timeline_event = ResearchTimeline(
                project_id=project_id,
                event_type=event_type.value,
                event_description=event_description,
                event_data=event_data or {},
                timestamp=datetime.utcnow()
            )
            
            self.db.add(timeline_event)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error adding timeline event: {str(e)}")

    async def _get_project_document_count(self, project_id: str) -> int:
        """Get document count for project"""
        try:
            # This would integrate with the document service
            # For now, return a placeholder
            return 0
        except Exception:
            return 0

    async def _get_project_insight_count(self, project_id: str) -> int:
        """Get insight count for project"""
        try:
            context = self.db.query(ResearchContext).filter(
                ResearchContext.project_id == project_id
            ).order_by(desc(ResearchContext.session_timestamp)).first()
            
            if context and context.insights_generated:
                return len(context.insights_generated)
            return 0
        except Exception:
            return 0

    async def _get_milestone_progress(self, project_id: str) -> float:
        """Get milestone completion progress"""
        try:
            milestones = self.db.query(ResearchMilestone).filter(
                ResearchMilestone.roadmap_id.in_(
                    self.db.query(ResearchMilestone.roadmap_id).join(
                        "roadmap"
                    ).filter(ResearchProject.id == project_id)
                )
            ).all()
            
            if not milestones:
                return 0.0
            
            completed = len([m for m in milestones if m.status == "completed"])
            return (completed / len(milestones)) * 100
            
        except Exception:
            return 0.0

    async def _get_last_activity_time(self, project_id: str) -> datetime:
        """Get last activity time for project"""
        try:
            last_timeline = self.db.query(ResearchTimeline).filter(
                ResearchTimeline.project_id == project_id
            ).order_by(desc(ResearchTimeline.timestamp)).first()
            
            if last_timeline:
                return last_timeline.timestamp
            
            # Fallback to project updated time
            project = self.db.query(ResearchProject).filter(
                ResearchProject.id == project_id
            ).first()
            
            return project.updated_at if project else datetime.utcnow()
            
        except Exception:
            return datetime.utcnow()

    async def _update_context_switch_patterns(
        self,
        user_id: str,
        from_project: str,
        to_project: str
    ):
        """Update context switching patterns for better recommendations"""
        try:
            if user_id not in self.context_switch_patterns:
                self.context_switch_patterns[user_id] = []
            
            switch_pattern = f"{from_project}->{to_project}"
            self.context_switch_patterns[user_id].append(switch_pattern)
            
            # Keep only recent patterns (last 100)
            if len(self.context_switch_patterns[user_id]) > 100:
                self.context_switch_patterns[user_id] = self.context_switch_patterns[user_id][-100:]
                
        except Exception as e:
            logger.error(f"Error updating context switch patterns: {str(e)}")

    async def _enhance_timeline_with_insights(
        self,
        timeline_events: List[ResearchTimelineEvent],
        user_id: str,
        project_id: str
    ) -> List[ResearchTimelineEvent]:
        """Enhance timeline with additional insights"""
        try:
            # Add productivity insights
            for event in timeline_events:
                if event.event_type == TimelineEventType.INSIGHT_GENERATED:
                    # Add insight quality score
                    event.event_data["quality_score"] = await self._calculate_insight_quality(
                        event.event_data
                    )
                elif event.event_type == TimelineEventType.DOCUMENT_ADDED:
                    # Add document relevance score
                    event.event_data["relevance_score"] = await self._calculate_document_relevance(
                        event.event_data, project_id
                    )
            
            return timeline_events
            
        except Exception as e:
            logger.error(f"Error enhancing timeline: {str(e)}")
            return timeline_events

    async def _calculate_context_relevance(
        self,
        current_context: ResearchContextData,
        target_project: ResearchProjectSummary
    ) -> float:
        """Calculate relevance score for context switching"""
        try:
            relevance_score = 0.0
            
            # Domain similarity
            if current_context.context_metadata.get("domain") == target_project.research_domain:
                relevance_score += 0.3
            
            # Recent activity
            days_since_activity = (datetime.utcnow() - target_project.last_activity).days
            if days_since_activity < 7:
                relevance_score += 0.2
            elif days_since_activity < 30:
                relevance_score += 0.1
            
            # Project status
            if target_project.status == ProjectStatus.ACTIVE:
                relevance_score += 0.2
            
            # Milestone progress (projects with pending milestones are more relevant)
            if 0 < target_project.milestone_progress < 100:
                relevance_score += 0.3
            
            return min(1.0, relevance_score)
            
        except Exception as e:
            logger.error(f"Error calculating context relevance: {str(e)}")
            return 0.0

    async def _find_related_insights(
        self,
        current_context: ResearchContextData,
        target_project_id: str
    ) -> List[str]:
        """Find insights related between current and target contexts"""
        try:
            target_context = await self.restore_research_context(
                current_context.user_id, target_project_id
            )
            
            if not target_context:
                return []
            
            # Simple keyword matching for related insights
            current_keywords = set()
            for insight in current_context.insights_generated:
                if isinstance(insight, dict) and "keywords" in insight:
                    current_keywords.update(insight["keywords"])
            
            related_insights = []
            for insight in target_context.insights_generated:
                if isinstance(insight, dict):
                    insight_keywords = set(insight.get("keywords", []))
                    if current_keywords.intersection(insight_keywords):
                        related_insights.append(insight.get("summary", "Related insight found"))
            
            return related_insights[:3]  # Return top 3
            
        except Exception as e:
            logger.error(f"Error finding related insights: {str(e)}")
            return []

    async def _estimate_context_load_time(self, project_id: str) -> int:
        """Estimate time to load project context in seconds"""
        try:
            # Base load time
            load_time = 2
            
            # Add time based on context complexity
            context = self.db.query(ResearchContext).filter(
                ResearchContext.project_id == project_id
            ).order_by(desc(ResearchContext.session_timestamp)).first()
            
            if context:
                # Add time for documents
                load_time += len(context.active_documents or []) * 0.5
                
                # Add time for insights
                load_time += len(context.insights_generated or []) * 0.2
            
            return int(load_time)
            
        except Exception:
            return 5  # Default estimate

    async def _generate_switch_reason(
        self,
        current_context: ResearchContextData,
        target_project: ResearchProjectSummary
    ) -> str:
        """Generate reason for context switch recommendation"""
        try:
            reasons = []
            
            # Domain similarity
            if current_context.context_metadata.get("domain") == target_project.research_domain:
                reasons.append(f"Similar research domain: {target_project.research_domain}")
            
            # Recent activity
            days_since_activity = (datetime.utcnow() - target_project.last_activity).days
            if days_since_activity < 7:
                reasons.append("Recent activity detected")
            
            # Milestone progress
            if 0 < target_project.milestone_progress < 100:
                reasons.append(f"Pending milestones ({target_project.milestone_progress:.0f}% complete)")
            
            if not reasons:
                reasons.append("Potential research synergy identified")
            
            return "; ".join(reasons)
            
        except Exception:
            return "Recommended based on research patterns"

    async def _calculate_insight_quality(self, insight_data: Dict[str, Any]) -> float:
        """Calculate quality score for an insight"""
        try:
            # Simple quality scoring based on available data
            quality_score = 0.5  # Base score
            
            if "confidence" in insight_data:
                quality_score += insight_data["confidence"] * 0.3
            
            if "novelty" in insight_data:
                quality_score += insight_data["novelty"] * 0.2
            
            return min(1.0, quality_score)
            
        except Exception:
            return 0.5

    async def _calculate_document_relevance(
        self,
        document_data: Dict[str, Any],
        project_id: str
    ) -> float:
        """Calculate document relevance to project"""
        try:
            # Placeholder relevance calculation
            return 0.7  # Default relevance score
            
        except Exception:
            return 0.5

    async def _get_progress_indicators(self, project_id: str) -> Dict[str, Any]:
        """Get progress indicators for project"""
        try:
            return {
                "documents_processed": await self._get_project_document_count(project_id),
                "insights_generated": await self._get_project_insight_count(project_id),
                "milestones_completed": await self._get_milestone_progress(project_id),
                "days_active": (datetime.utcnow() - (await self._get_last_activity_time(project_id))).days
            }
        except Exception:
            return {}

    # Public API methods
    async def get_active_context(self, user_id: str, project_id: str) -> Optional[ResearchContextData]:
        """Get currently active research context"""
        return await self.restore_research_context(user_id, project_id)

    async def update_research_focus(
        self,
        user_id: str,
        project_id: str,
        new_focus: str
    ) -> bool:
        """Update research focus for current context"""
        try:
            context = await self.restore_research_context(user_id, project_id)
            if context:
                context.research_focus = new_focus
                context.context_metadata["focus_updated_at"] = datetime.utcnow().isoformat()
                
                await self.save_research_context(
                    user_id=user_id,
                    project_id=project_id,
                    context_data=asdict(context)
                )
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating research focus: {str(e)}")
            return False

    async def add_insight_to_context(
        self,
        user_id: str,
        project_id: str,
        insight: Dict[str, Any]
    ) -> bool:
        """Add new insight to research context"""
        try:
            context = await self.restore_research_context(user_id, project_id)
            if context:
                insight["timestamp"] = datetime.utcnow().isoformat()
                insight["id"] = str(uuid.uuid4())
                
                context.insights_generated.append(insight)
                
                await self.save_research_context(
                    user_id=user_id,
                    project_id=project_id,
                    context_data=asdict(context)
                )
                
                # Add timeline event
                await self._add_timeline_event(
                    project_id=project_id,
                    event_type=TimelineEventType.INSIGHT_GENERATED,
                    event_description=f"New insight: {insight.get('title', 'Untitled')}",
                    event_data={"insight_id": insight["id"], "insight_type": insight.get("type", "general")}
                )
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error adding insight to context: {str(e)}")
            return False

    def cleanup_old_contexts(self, days_old: int = 90):
        """Clean up old inactive contexts"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            self.db.query(ResearchContext).filter(
                and_(
                    ResearchContext.session_timestamp < cutoff_date,
                    ResearchContext.is_active == False
                )
            ).delete()
            
            self.db.commit()
            logger.info(f"Cleaned up contexts older than {days_old} days")
            
        except Exception as e:
            logger.error(f"Error cleaning up old contexts: {str(e)}")

# Export classes
__all__ = [
    'ResearchMemoryEngine',
    'ResearchContextData',
    'ResearchProjectSummary',
    'ResearchTimelineEvent',
    'ContextSwitchRecommendation',
    'ProjectStatus',
    'TimelineEventType'
]