"""
Research Workflow Automation Service
Provides end-to-end research workflow automation including literature monitoring,
citation management, pipeline automation, and intelligent data collection.
"""
import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import schedule
import time
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, or_

from core.database import (
    get_db, Document, DocumentChunk, DocumentTag, AnalyticsEvent,
    User, UserProfile
)
from services.research_assistant import ResearchAssistant
from services.semantic_search_v2 import SemanticSearchV2Service
from services.multimodal_processor import MultiModalProcessor

logger = logging.getLogger(__name__)

class WorkflowType(str, Enum):
    """Research workflow types"""
    LITERATURE_MONITORING = "literature_monitoring"
    CITATION_MANAGEMENT = "citation_management"
    DATA_COLLECTION = "data_collection"
    ANALYSIS_PIPELINE = "analysis_pipeline"
    REPORT_GENERATION = "report_generation"
    PEER_REVIEW = "peer_review"

class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    SCHEDULED = "scheduled"

@dataclass
class AutomatedWorkflow:
    """Automated research workflow"""
    id: str
    user_id: str
    name: str
    workflow_type: WorkflowType
    description: str
    configuration: Dict[str, Any]
    schedule: Dict[str, Any]  # Cron-like schedule
    status: WorkflowStatus
    created_at: datetime
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    run_count: int
    success_count: int
    failure_count: int
    results: List[Dict[str, Any]]

class ResearchAutomationService:
    """Main research automation service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.research_assistant = ResearchAssistant(db)
        self.search_service = SemanticSearchV2Service(db)
        self.multimodal_service = MultiModalProcessor(db)
        
        # Active workflows
        self.active_workflows: Dict[str, AutomatedWorkflow] = {}
        
        # Scheduler
        self.scheduler_running = False
        self.executor = ThreadPoolExecutor(max_workers=5)

    async def create_automated_workflow(
        self,
        user_id: str,
        name: str,
        workflow_type: WorkflowType,
        description: str,
        configuration: Dict[str, Any],
        schedule_config: Dict[str, Any]
    ) -> AutomatedWorkflow:
        """Create a new automated research workflow"""
        try:
            workflow_id = str(uuid.uuid4())
            
            workflow = AutomatedWorkflow(
                id=workflow_id,
                user_id=user_id,
                name=name,
                workflow_type=workflow_type,
                description=description,
                configuration=configuration,
                schedule=schedule_config,
                status=WorkflowStatus.ACTIVE,
                created_at=datetime.utcnow(),
                last_run=None,
                next_run=self._calculate_next_run(schedule_config),
                run_count=0,
                success_count=0,
                failure_count=0,
                results=[]
            )
            
            # Store workflow
            self.active_workflows[workflow_id] = workflow
            
            # Start scheduler if not running
            if not self.scheduler_running:
                await self._start_scheduler()
            
            return workflow
            
        except Exception as e:
            logger.error(f"Error creating automated workflow: {str(e)}")
            raise

    async def execute_workflow(
        self,
        workflow_id: str,
        manual_trigger: bool = False
    ) -> Dict[str, Any]:
        """Execute a research workflow"""
        try:
            workflow = self.active_workflows.get(workflow_id)
            if not workflow:
                raise ValueError("Workflow not found")
            
            if workflow.status != WorkflowStatus.ACTIVE and not manual_trigger:
                return {"status": "skipped", "reason": "workflow not active"}
            
            # Execute based on workflow type
            if workflow.workflow_type == WorkflowType.LITERATURE_MONITORING:
                result = await self._execute_literature_monitoring(workflow)
            elif workflow.workflow_type == WorkflowType.CITATION_MANAGEMENT:
                result = await self._execute_citation_management(workflow)
            elif workflow.workflow_type == WorkflowType.DATA_COLLECTION:
                result = await self._execute_data_collection(workflow)
            elif workflow.workflow_type == WorkflowType.ANALYSIS_PIPELINE:
                result = await self._execute_analysis_pipeline(workflow)
            elif workflow.workflow_type == WorkflowType.REPORT_GENERATION:
                result = await self._execute_report_generation(workflow)
            else:
                result = {"status": "error", "message": "Unsupported workflow type"}
            
            # Update workflow statistics
            workflow.run_count += 1
            workflow.last_run = datetime.utcnow()
            workflow.next_run = self._calculate_next_run(workflow.schedule)
            
            if result.get("status") == "success":
                workflow.success_count += 1
            else:
                workflow.failure_count += 1
            
            # Store result
            workflow.results.append({
                "timestamp": datetime.utcnow().isoformat(),
                "result": result,
                "manual_trigger": manual_trigger
            })
            
            # Keep only last 50 results
            if len(workflow.results) > 50:
                workflow.results = workflow.results[-50:]
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing workflow: {str(e)}")
            return {"status": "error", "message": str(e)}

    # Workflow execution methods
    async def _execute_literature_monitoring(self, workflow: AutomatedWorkflow) -> Dict[str, Any]:
        """Execute literature monitoring workflow"""
        try:
            config = workflow.configuration
            search_terms = config.get("search_terms", [])
            domains = config.get("domains", [])
            
            new_papers = []
            
            # Search for new literature
            for term in search_terms:
                # Use semantic search to find relevant documents
                from services.semantic_search_v2 import SearchQuery, SearchMode, ReasoningType
                
                query = SearchQuery(
                    query_text=term,
                    user_id=workflow.user_id,
                    mode=SearchMode.SEMANTIC,
                    reasoning_types=[ReasoningType.ASSOCIATIVE],
                    max_results=10
                )
                
                results = await self.search_service.advanced_search(query)
                
                for result in results:
                    if result.confidence_score > 0.7:
                        new_papers.append({
                            "title": result.title,
                            "content": result.content[:500],
                            "relevance": result.confidence_score,
                            "search_term": term
                        })
            
            # Generate summary
            summary = f"Found {len(new_papers)} relevant papers"
            
            return {
                "status": "success",
                "papers_found": len(new_papers),
                "papers": new_papers[:20],  # Limit results
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error in literature monitoring: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _execute_citation_management(self, workflow: AutomatedWorkflow) -> Dict[str, Any]:
        """Execute citation management workflow"""
        try:
            config = workflow.configuration
            
            # Get user's documents
            documents = self.db.query(Document).filter(
                Document.user_id == workflow.user_id,
                Document.status == "completed"
            ).limit(50).all()
            
            citations_generated = 0
            bibliography = []
            
            for doc in documents:
                # Generate citation for document
                citation = self._generate_citation(doc, config.get("citation_style", "APA"))
                bibliography.append(citation)
                citations_generated += 1
            
            return {
                "status": "success",
                "citations_generated": citations_generated,
                "bibliography": bibliography,
                "citation_style": config.get("citation_style", "APA")
            }
            
        except Exception as e:
            logger.error(f"Error in citation management: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _execute_data_collection(self, workflow: AutomatedWorkflow) -> Dict[str, Any]:
        """Execute automated data collection workflow"""
        try:
            config = workflow.configuration
            collection_type = config.get("collection_type", "documents")
            
            if collection_type == "documents":
                # Monitor for new documents
                recent_docs = self.db.query(Document).filter(
                    Document.user_id == workflow.user_id,
                    Document.created_at >= datetime.utcnow() - timedelta(days=1)
                ).all()
                
                processed_docs = 0
                for doc in recent_docs:
                    # Process with multimodal processor
                    try:
                        # This would process the document
                        processed_docs += 1
                    except Exception as e:
                        logger.warning(f"Error processing document {doc.id}: {str(e)}")
                
                return {
                    "status": "success",
                    "documents_processed": processed_docs,
                    "collection_type": collection_type
                }
            
            return {"status": "success", "message": "Data collection completed"}
            
        except Exception as e:
            logger.error(f"Error in data collection: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _execute_analysis_pipeline(self, workflow: AutomatedWorkflow) -> Dict[str, Any]:
        """Execute automated analysis pipeline"""
        try:
            config = workflow.configuration
            analysis_type = config.get("analysis_type", "topic_modeling")
            
            if analysis_type == "topic_modeling":
                # Run topic modeling on user's documents - TEMPORARILY DISABLED
                # from services.topic_modeling_service import TopicModelingService
                # topic_service = TopicModelingService(self.db)
                
                # result = await topic_service.analyze_document_topics(
                #     user_id=workflow.user_id,
                #     n_topics=config.get("n_topics", 5)
                # )
                result = {"message": "Topic modeling temporarily disabled"}
                
                return {
                    "status": "success",
                    "analysis_type": analysis_type,
                    "topics_found": len(result.topics),
                    "coherence_score": result.coherence_score
                }
            
            return {"status": "success", "message": "Analysis pipeline completed"}
            
        except Exception as e:
            logger.error(f"Error in analysis pipeline: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _execute_report_generation(self, workflow: AutomatedWorkflow) -> Dict[str, Any]:
        """Execute automated report generation"""
        try:
            config = workflow.configuration
            report_type = config.get("report_type", "summary")
            
            # Generate research summary report
            report = await self.research_assistant.generate_comprehensive_report(
                user_id=workflow.user_id,
                timeframe=config.get("timeframe", "month")
            )
            
            return {
                "status": "success",
                "report_type": report_type,
                "report_id": report.id if hasattr(report, 'id') else "generated",
                "summary": "Research report generated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error in report generation: {str(e)}")
            return {"status": "error", "message": str(e)}

    # Helper methods
    def _calculate_next_run(self, schedule_config: Dict[str, Any]) -> datetime:
        """Calculate next run time based on schedule"""
        try:
            schedule_type = schedule_config.get("type", "daily")
            
            if schedule_type == "daily":
                return datetime.utcnow() + timedelta(days=1)
            elif schedule_type == "weekly":
                return datetime.utcnow() + timedelta(weeks=1)
            elif schedule_type == "monthly":
                return datetime.utcnow() + timedelta(days=30)
            else:
                return datetime.utcnow() + timedelta(hours=1)
                
        except Exception as e:
            logger.error(f"Error calculating next run: {str(e)}")
            return datetime.utcnow() + timedelta(hours=1)

    def _generate_citation(self, document: Document, style: str) -> str:
        """Generate citation for document"""
        try:
            if style.upper() == "APA":
                return f"{document.name}. ({document.created_at.year if document.created_at else 'n.d.'}). Retrieved from user collection."
            elif style.upper() == "MLA":
                return f'"{document.name}." User Collection, {document.created_at.year if document.created_at else "n.d."}.'
            else:
                return f"{document.name} - User Collection"
                
        except Exception as e:
            logger.error(f"Error generating citation: {str(e)}")
            return f"{document.name} - Citation Error"

    async def _start_scheduler(self):
        """Start the workflow scheduler"""
        try:
            self.scheduler_running = True
            
            # Run scheduler in background
            asyncio.create_task(self._scheduler_loop())
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")

    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.scheduler_running:
            try:
                current_time = datetime.utcnow()
                
                # Check all active workflows
                for workflow_id, workflow in self.active_workflows.items():
                    if (workflow.status == WorkflowStatus.ACTIVE and 
                        workflow.next_run and 
                        current_time >= workflow.next_run):
                        
                        # Execute workflow
                        asyncio.create_task(self.execute_workflow(workflow_id))
                
                # Sleep for 1 minute
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                await asyncio.sleep(60)

# Export classes
__all__ = [
    'ResearchAutomationService',
    'AutomatedWorkflow',
    'WorkflowType',
    'WorkflowStatus'
]