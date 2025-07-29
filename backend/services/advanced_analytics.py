"""
Advanced Analytics and Insights Service
Provides comprehensive analytics, visualization, and insights for user interactions,
document relationships, knowledge patterns, and system performance.
"""
import asyncio
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import uuid
from collections import defaultdict, Counter
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA, LatentDirichletAllocation
from sklearn.manifold import TSNE
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, or_, text

from core.database import (
    get_db, Document, DocumentChunk, DocumentTag, AnalyticsEvent,
    User, UserProfile, KGEntity, KGRelationship
)
from services.topic_modeling_service import TopicModelingService
from services.knowledge_graph import KnowledgeGraphService

logger = logging.getLogger(__name__)

class AnalyticsTimeframe(str, Enum):
    """Analytics timeframe options"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    ALL_TIME = "all_time"

class VisualizationType(str, Enum):
    """Visualization type options"""
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    SCATTER_PLOT = "scatter_plot"
    HEATMAP = "heatmap"
    NETWORK_GRAPH = "network_graph"
    TREEMAP = "treemap"
    SANKEY_DIAGRAM = "sankey_diagram"
    WORD_CLOUD = "word_cloud"
    TIMELINE = "timeline"

class MetricType(str, Enum):
    """Metric type categories"""
    USAGE = "usage"
    PERFORMANCE = "performance"
    CONTENT = "content"
    USER_BEHAVIOR = "user_behavior"
    KNOWLEDGE = "knowledge"
    QUALITY = "quality"

@dataclass
class AnalyticsMetric:
    """Analytics metric definition"""
    name: str
    value: Union[int, float, str]
    metric_type: MetricType
    description: str
    unit: Optional[str] = None
    trend: Optional[float] = None  # Percentage change
    benchmark: Optional[float] = None
    timestamp: Optional[datetime] = None

@dataclass
class VisualizationData:
    """Visualization data structure"""
    chart_type: VisualizationType
    title: str
    data: Dict[str, Any]
    config: Dict[str, Any]
    description: str
    insights: List[str]

@dataclass
class InsightReport:
    """Comprehensive insight report"""
    id: str
    title: str
    summary: str
    metrics: List[AnalyticsMetric]
    visualizations: List[VisualizationData]
    recommendations: List[str]
    timeframe: AnalyticsTimeframe
    generated_at: datetime
    confidence_score: float

@dataclass
class DocumentRelationship:
    """Document relationship data"""
    source_doc_id: str
    target_doc_id: str
    relationship_type: str
    strength: float
    shared_concepts: List[str]
    similarity_score: float

@dataclass
class KnowledgePattern:
    """Knowledge pattern identification"""
    pattern_id: str
    pattern_type: str
    entities: List[str]
    relationships: List[str]
    frequency: int
    confidence: float
    examples: List[str]

class AdvancedAnalyticsService:
    """Main advanced analytics service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.topic_service = TopicModelingService(db)
        self.kg_service = KnowledgeGraphService(db)
        
        # Analytics configurations
        self.timeframe_deltas = {
            AnalyticsTimeframe.HOUR: timedelta(hours=1),
            AnalyticsTimeframe.DAY: timedelta(days=1),
            AnalyticsTimeframe.WEEK: timedelta(weeks=1),
            AnalyticsTimeframe.MONTH: timedelta(days=30),
            AnalyticsTimeframe.QUARTER: timedelta(days=90),
            AnalyticsTimeframe.YEAR: timedelta(days=365)
        }

    async def generate_comprehensive_report(
        self,
        user_id: str,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.MONTH,
        include_predictions: bool = True
    ) -> InsightReport:
        """Generate comprehensive analytics report"""
        try:
            logger.info(f"Generating comprehensive report for user {user_id}")
            
            # Collect all metrics
            usage_metrics = await self._get_usage_metrics(user_id, timeframe)
            performance_metrics = await self._get_performance_metrics(user_id, timeframe)
            content_metrics = await self._get_content_metrics(user_id, timeframe)
            behavior_metrics = await self._get_user_behavior_metrics(user_id, timeframe)
            knowledge_metrics = await self._get_knowledge_metrics(user_id, timeframe)
            
            all_metrics = (usage_metrics + performance_metrics + content_metrics + 
                          behavior_metrics + knowledge_metrics)
            
            # Generate visualizations
            visualizations = await self._generate_visualizations(user_id, timeframe, all_metrics)
            
            # Generate insights and recommendations
            insights = await self._generate_insights(all_metrics, visualizations)
            recommendations = await self._generate_recommendations(all_metrics, insights)
            
            # Calculate confidence score
            confidence_score = self._calculate_report_confidence(all_metrics, visualizations)
            
            # Create report
            report = InsightReport(
                id=str(uuid.uuid4()),
                title=f"Analytics Report - {timeframe.value.title()}",
                summary=await self._generate_report_summary(all_metrics, insights),
                metrics=all_metrics,
                visualizations=visualizations,
                recommendations=recommendations,
                timeframe=timeframe,
                generated_at=datetime.utcnow(),
                confidence_score=confidence_score
            )
            
            # Store report
            await self._store_report(user_id, report)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {str(e)}")
            raise

    async def analyze_document_relationships(
        self,
        user_id: str,
        min_similarity: float = 0.3,
        max_relationships: int = 100
    ) -> List[DocumentRelationship]:
        """Analyze relationships between user's documents"""
        try:
            logger.info(f"Analyzing document relationships for user {user_id}")
            
            # Get user's documents
            documents = self.db.query(Document).filter(
                Document.user_id == user_id,
                Document.status == "completed"
            ).all()
            
            if len(documents) < 2:
                return []
            
            # Get document embeddings and content
            doc_data = []
            for doc in documents:
                chunks = self.db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == doc.id
                ).all()
                
                content = " ".join([chunk.content for chunk in chunks])
                doc_data.append({
                    'id': doc.id,
                    'name': doc.name,
                    'content': content,
                    'created_at': doc.created_at
                })
            
            # Calculate document similarities
            relationships = []
            
            # Create TF-IDF vectors
            texts = [doc['content'] for doc in doc_data]
            vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Calculate pairwise similarities
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            for i in range(len(doc_data)):
                for j in range(i + 1, len(doc_data)):
                    similarity = similarity_matrix[i][j]
                    
                    if similarity >= min_similarity:
                        # Find shared concepts
                        shared_concepts = await self._find_shared_concepts(
                            doc_data[i]['content'], doc_data[j]['content']
                        )
                        
                        # Determine relationship type
                        relationship_type = self._classify_relationship_type(
                            doc_data[i], doc_data[j], similarity, shared_concepts
                        )
                        
                        relationship = DocumentRelationship(
                            source_doc_id=doc_data[i]['id'],
                            target_doc_id=doc_data[j]['id'],
                            relationship_type=relationship_type,
                            strength=similarity,
                            shared_concepts=shared_concepts,
                            similarity_score=similarity
                        )
                        
                        relationships.append(relationship)
            
            # Sort by strength and limit results
            relationships.sort(key=lambda x: x.strength, reverse=True)
            return relationships[:max_relationships]
            
        except Exception as e:
            logger.error(f"Error analyzing document relationships: {str(e)}")
            raise

    async def discover_knowledge_patterns(
        self,
        user_id: str,
        min_frequency: int = 3,
        confidence_threshold: float = 0.7
    ) -> List[KnowledgePattern]:
        """Discover patterns in user's knowledge graph"""
        try:
            logger.info(f"Discovering knowledge patterns for user {user_id}")
            
            # Get knowledge graph data
            kg_data = await self.kg_service.get_user_knowledge_graph(user_id)
            
            if not kg_data or not kg_data.get('entities'):
                return []
            
            patterns = []
            
            # Pattern 1: Frequent entity co-occurrences
            cooccurrence_patterns = await self._find_cooccurrence_patterns(
                kg_data, min_frequency, confidence_threshold
            )
            patterns.extend(cooccurrence_patterns)
            
            # Pattern 2: Relationship chains
            chain_patterns = await self._find_relationship_chains(
                kg_data, min_frequency, confidence_threshold
            )
            patterns.extend(chain_patterns)
            
            # Pattern 3: Concept clusters
            cluster_patterns = await self._find_concept_clusters(
                kg_data, min_frequency, confidence_threshold
            )
            patterns.extend(cluster_patterns)
            
            # Pattern 4: Temporal patterns
            temporal_patterns = await self._find_temporal_patterns(
                user_id, kg_data, min_frequency, confidence_threshold
            )
            patterns.extend(temporal_patterns)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error discovering knowledge patterns: {str(e)}")
            raise

    async def generate_usage_insights(
        self,
        user_id: str,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.MONTH
    ) -> Dict[str, Any]:
        """Generate detailed usage insights"""
        try:
            logger.info(f"Generating usage insights for user {user_id}")
            
            # Get time range
            end_date = datetime.utcnow()
            if timeframe != AnalyticsTimeframe.ALL_TIME:
                start_date = end_date - self.timeframe_deltas[timeframe]
            else:
                start_date = datetime.min
            
            # Query usage events
            events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.created_at >= start_date,
                AnalyticsEvent.created_at <= end_date
            ).all()
            
            if not events:
                return {"message": "No usage data available for the specified timeframe"}
            
            # Analyze usage patterns
            insights = {
                "total_events": len(events),
                "event_types": {},
                "daily_activity": {},
                "hourly_patterns": {},
                "feature_usage": {},
                "session_analysis": {},
                "trends": {}
            }
            
            # Event type analysis
            event_types = Counter([event.event_type for event in events])
            insights["event_types"] = dict(event_types)
            
            # Daily activity analysis
            daily_counts = defaultdict(int)
            for event in events:
                date_key = event.created_at.date().isoformat()
                daily_counts[date_key] += 1
            insights["daily_activity"] = dict(daily_counts)
            
            # Hourly pattern analysis
            hourly_counts = defaultdict(int)
            for event in events:
                hour_key = event.created_at.hour
                hourly_counts[hour_key] += 1
            insights["hourly_patterns"] = dict(hourly_counts)
            
            # Feature usage analysis
            feature_usage = defaultdict(int)
            for event in events:
                if event.event_data and isinstance(event.event_data, dict):
                    service = event.event_data.get('service', 'unknown')
                    feature_usage[service] += 1
            insights["feature_usage"] = dict(feature_usage)
            
            # Session analysis
            sessions = await self._analyze_user_sessions(events)
            insights["session_analysis"] = sessions
            
            # Trend analysis
            trends = await self._calculate_usage_trends(events, timeframe)
            insights["trends"] = trends
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating usage insights: {str(e)}")
            raise

    async def create_knowledge_map_visualization(
        self,
        user_id: str,
        layout_algorithm: str = "spring",
        max_nodes: int = 100
    ) -> VisualizationData:
        """Create interactive knowledge map visualization"""
        try:
            logger.info(f"Creating knowledge map for user {user_id}")
            
            # Get knowledge graph data
            kg_data = await self.kg_service.get_user_knowledge_graph(user_id)
            
            if not kg_data or not kg_data.get('entities'):
                return VisualizationData(
                    chart_type=VisualizationType.NETWORK_GRAPH,
                    title="Knowledge Map",
                    data={},
                    config={},
                    description="No knowledge graph data available",
                    insights=["No entities found in knowledge graph"]
                )
            
            # Create NetworkX graph
            G = nx.Graph()
            
            # Add nodes (entities)
            entities = kg_data['entities'][:max_nodes]  # Limit nodes
            for entity in entities:
                G.add_node(
                    entity['id'],
                    label=entity['name'],
                    type=entity.get('type', 'unknown'),
                    frequency=entity.get('frequency', 1)
                )
            
            # Add edges (relationships)
            relationships = kg_data.get('relationships', [])
            for rel in relationships:
                if rel['source'] in G.nodes and rel['target'] in G.nodes:
                    G.add_edge(
                        rel['source'],
                        rel['target'],
                        relationship=rel.get('type', 'related'),
                        strength=rel.get('strength', 1.0)
                    )
            
            # Calculate layout
            if layout_algorithm == "spring":
                pos = nx.spring_layout(G, k=1, iterations=50)
            elif layout_algorithm == "circular":
                pos = nx.circular_layout(G)
            elif layout_algorithm == "kamada_kawai":
                pos = nx.kamada_kawai_layout(G)
            else:
                pos = nx.spring_layout(G)
            
            # Prepare visualization data
            node_trace = []
            edge_trace = []
            
            # Create edges
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_trace.extend([x0, x1, None])
                edge_trace.extend([y0, y1, None])
            
            # Create nodes
            node_x = []
            node_y = []
            node_text = []
            node_size = []
            node_color = []
            
            for node in G.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                
                node_info = G.nodes[node]
                node_text.append(f"{node_info['label']}<br>Type: {node_info['type']}<br>Frequency: {node_info['frequency']}")
                node_size.append(max(10, min(50, node_info['frequency'] * 5)))
                
                # Color by type
                type_colors = {
                    'person': '#FF6B6B',
                    'organization': '#4ECDC4',
                    'location': '#45B7D1',
                    'concept': '#96CEB4',
                    'unknown': '#FFEAA7'
                }
                node_color.append(type_colors.get(node_info['type'], '#FFEAA7'))
            
            # Create Plotly figure
            fig_data = {
                'nodes': {
                    'x': node_x,
                    'y': node_y,
                    'text': node_text,
                    'size': node_size,
                    'color': node_color
                },
                'edges': {
                    'x': edge_trace[::3],  # Every third element (x coordinates)
                    'y': edge_trace[1::3]  # Every third element starting from 1 (y coordinates)
                }
            }
            
            # Generate insights
            insights = [
                f"Knowledge graph contains {len(G.nodes)} entities and {len(G.edges)} relationships",
                f"Most connected entity: {max(G.nodes, key=lambda x: G.degree(x)) if G.nodes else 'None'}",
                f"Graph density: {nx.density(G):.3f}",
                f"Number of connected components: {nx.number_connected_components(G)}"
            ]
            
            # Add centrality insights
            if len(G.nodes) > 0:
                centrality = nx.degree_centrality(G)
                top_central = max(centrality.items(), key=lambda x: x[1])
                insights.append(f"Most central entity: {G.nodes[top_central[0]]['label']}")
            
            return VisualizationData(
                chart_type=VisualizationType.NETWORK_GRAPH,
                title="Knowledge Map",
                data=fig_data,
                config={
                    "layout": layout_algorithm,
                    "max_nodes": max_nodes,
                    "interactive": True
                },
                description="Interactive visualization of your knowledge graph showing entities and their relationships",
                insights=insights
            )
            
        except Exception as e:
            logger.error(f"Error creating knowledge map: {str(e)}")
            raise

    async def generate_content_analytics(
        self,
        user_id: str,
        timeframe: AnalyticsTimeframe = AnalyticsTimeframe.MONTH
    ) -> Dict[str, Any]:
        """Generate comprehensive content analytics"""
        try:
            logger.info(f"Generating content analytics for user {user_id}")
            
            # Get time range
            end_date = datetime.utcnow()
            if timeframe != AnalyticsTimeframe.ALL_TIME:
                start_date = end_date - self.timeframe_deltas[timeframe]
            else:
                start_date = datetime.min
            
            # Get user's documents
            documents = self.db.query(Document).filter(
                Document.user_id == user_id,
                Document.created_at >= start_date,
                Document.created_at <= end_date
            ).all()
            
            if not documents:
                return {"message": "No documents found for the specified timeframe"}
            
            analytics = {
                "document_stats": {},
                "content_analysis": {},
                "topic_distribution": {},
                "quality_metrics": {},
                "growth_trends": {},
                "recommendations": []
            }
            
            # Document statistics
            total_docs = len(documents)
            total_size = sum(doc.size or 0 for doc in documents)
            avg_size = total_size / total_docs if total_docs > 0 else 0
            
            content_types = Counter([doc.content_type for doc in documents])
            
            analytics["document_stats"] = {
                "total_documents": total_docs,
                "total_size_bytes": total_size,
                "average_size_bytes": avg_size,
                "content_type_distribution": dict(content_types)
            }
            
            # Content analysis
            all_content = []
            for doc in documents:
                chunks = self.db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == doc.id
                ).all()
                content = " ".join([chunk.content for chunk in chunks])
                all_content.append(content)
            
            if all_content:
                combined_content = " ".join(all_content)
                
                # Basic text statistics
                word_count = len(combined_content.split())
                char_count = len(combined_content)
                avg_words_per_doc = word_count / total_docs
                
                analytics["content_analysis"] = {
                    "total_words": word_count,
                    "total_characters": char_count,
                    "average_words_per_document": avg_words_per_doc,
                    "vocabulary_size": len(set(combined_content.lower().split()))
                }
                
                # Topic analysis
                try:
                    topic_result = await self.topic_service.analyze_document_topics(
                        user_id=user_id,
                        n_topics=5,
                        update_tags=False
                    )
                    
                    topic_dist = {}
                    for topic in topic_result.topics:
                        topic_dist[f"Topic {topic.id}"] = {
                            "keywords": topic.keywords,
                            "weight": topic.weight
                        }
                    
                    analytics["topic_distribution"] = topic_dist
                    
                except Exception as e:
                    logger.warning(f"Topic analysis failed: {str(e)}")
                    analytics["topic_distribution"] = {}
            
            # Quality metrics
            completed_docs = len([doc for doc in documents if doc.status == "completed"])
            failed_docs = len([doc for doc in documents if doc.status == "failed"])
            success_rate = completed_docs / total_docs if total_docs > 0 else 0
            
            analytics["quality_metrics"] = {
                "processing_success_rate": success_rate,
                "completed_documents": completed_docs,
                "failed_documents": failed_docs
            }
            
            # Growth trends
            if timeframe != AnalyticsTimeframe.ALL_TIME:
                growth_trends = await self._calculate_content_growth_trends(user_id, timeframe)
                analytics["growth_trends"] = growth_trends
            
            # Generate recommendations
            recommendations = []
            
            if success_rate < 0.9:
                recommendations.append("Consider reviewing failed document uploads to improve processing success rate")
            
            if avg_size < 1000:  # Very small documents
                recommendations.append("Documents are quite small on average. Consider combining related content")
            
            if len(content_types) == 1:
                recommendations.append("Consider diversifying content types for richer knowledge base")
            
            analytics["recommendations"] = recommendations
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating content analytics: {str(e)}")
            raise

    # Helper methods
    async def _get_usage_metrics(self, user_id: str, timeframe: AnalyticsTimeframe) -> List[AnalyticsMetric]:
        """Get usage-related metrics"""
        metrics = []
        
        # Get time range
        end_date = datetime.utcnow()
        if timeframe != AnalyticsTimeframe.ALL_TIME:
            start_date = end_date - self.timeframe_deltas[timeframe]
        else:
            start_date = datetime.min
        
        # Query events
        events = self.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.user_id == user_id,
            AnalyticsEvent.created_at >= start_date,
            AnalyticsEvent.created_at <= end_date
        ).all()
        
        # Total events
        metrics.append(AnalyticsMetric(
            name="Total Events",
            value=len(events),
            metric_type=MetricType.USAGE,
            description="Total number of user interactions",
            unit="events"
        ))
        
        # Unique event types
        event_types = set([event.event_type for event in events])
        metrics.append(AnalyticsMetric(
            name="Feature Usage Diversity",
            value=len(event_types),
            metric_type=MetricType.USAGE,
            description="Number of different features used",
            unit="features"
        ))
        
        # Daily average
        if timeframe != AnalyticsTimeframe.ALL_TIME:
            days = self.timeframe_deltas[timeframe].days
            daily_avg = len(events) / max(1, days)
            metrics.append(AnalyticsMetric(
                name="Daily Average Activity",
                value=round(daily_avg, 2),
                metric_type=MetricType.USAGE,
                description="Average events per day",
                unit="events/day"
            ))
        
        return metrics

    async def _get_performance_metrics(self, user_id: str, timeframe: AnalyticsTimeframe) -> List[AnalyticsMetric]:
        """Get performance-related metrics"""
        metrics = []
        
        # Get time range
        end_date = datetime.utcnow()
        if timeframe != AnalyticsTimeframe.ALL_TIME:
            start_date = end_date - self.timeframe_deltas[timeframe]
        else:
            start_date = datetime.min
        
        # Query processing events
        processing_events = self.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.user_id == user_id,
            AnalyticsEvent.event_type.in_(["document_processed", "multimodal_processing", "rag_query"]),
            AnalyticsEvent.created_at >= start_date,
            AnalyticsEvent.created_at <= end_date
        ).all()
        
        if processing_events:
            # Average processing time
            processing_times = []
            for event in processing_events:
                if event.event_data and isinstance(event.event_data, dict):
                    proc_time = event.event_data.get('processing_time', 0)
                    if proc_time > 0:
                        processing_times.append(proc_time)
            
            if processing_times:
                avg_time = sum(processing_times) / len(processing_times)
                metrics.append(AnalyticsMetric(
                    name="Average Processing Time",
                    value=round(avg_time, 3),
                    metric_type=MetricType.PERFORMANCE,
                    description="Average time to process content",
                    unit="seconds"
                ))
        
        # Document processing success rate
        documents = self.db.query(Document).filter(
            Document.user_id == user_id,
            Document.created_at >= start_date,
            Document.created_at <= end_date
        ).all()
        
        if documents:
            completed = len([doc for doc in documents if doc.status == "completed"])
            success_rate = completed / len(documents)
            metrics.append(AnalyticsMetric(
                name="Processing Success Rate",
                value=round(success_rate * 100, 1),
                metric_type=MetricType.PERFORMANCE,
                description="Percentage of successfully processed documents",
                unit="percent"
            ))
        
        return metrics

    async def _get_content_metrics(self, user_id: str, timeframe: AnalyticsTimeframe) -> List[AnalyticsMetric]:
        """Get content-related metrics"""
        metrics = []
        
        # Get time range
        end_date = datetime.utcnow()
        if timeframe != AnalyticsTimeframe.ALL_TIME:
            start_date = end_date - self.timeframe_deltas[timeframe]
        else:
            start_date = datetime.min
        
        # Query documents
        documents = self.db.query(Document).filter(
            Document.user_id == user_id,
            Document.created_at >= start_date,
            Document.created_at <= end_date
        ).all()
        
        # Total documents
        metrics.append(AnalyticsMetric(
            name="Total Documents",
            value=len(documents),
            metric_type=MetricType.CONTENT,
            description="Number of documents in collection",
            unit="documents"
        ))
        
        if documents:
            # Total content size
            total_size = sum(doc.size or 0 for doc in documents)
            metrics.append(AnalyticsMetric(
                name="Total Content Size",
                value=total_size,
                metric_type=MetricType.CONTENT,
                description="Total size of all documents",
                unit="bytes"
            ))
            
            # Content diversity
            content_types = set([doc.content_type for doc in documents])
            metrics.append(AnalyticsMetric(
                name="Content Type Diversity",
                value=len(content_types),
                metric_type=MetricType.CONTENT,
                description="Number of different content types",
                unit="types"
            ))
        
        return metrics

    async def _get_user_behavior_metrics(self, user_id: str, timeframe: AnalyticsTimeframe) -> List[AnalyticsMetric]:
        """Get user behavior metrics"""
        metrics = []
        
        # Get time range
        end_date = datetime.utcnow()
        if timeframe != AnalyticsTimeframe.ALL_TIME:
            start_date = end_date - self.timeframe_deltas[timeframe]
        else:
            start_date = datetime.min
        
        # Query events
        events = self.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.user_id == user_id,
            AnalyticsEvent.created_at >= start_date,
            AnalyticsEvent.created_at <= end_date
        ).all()
        
        if events:
            # Session analysis
            sessions = await self._analyze_user_sessions(events)
            
            metrics.append(AnalyticsMetric(
                name="Average Session Duration",
                value=round(sessions.get('average_duration', 0), 2),
                metric_type=MetricType.USER_BEHAVIOR,
                description="Average time spent per session",
                unit="minutes"
            ))
            
            metrics.append(AnalyticsMetric(
                name="Total Sessions",
                value=sessions.get('total_sessions', 0),
                metric_type=MetricType.USER_BEHAVIOR,
                description="Number of user sessions",
                unit="sessions"
            ))
        
        return metrics

    async def _get_knowledge_metrics(self, user_id: str, timeframe: AnalyticsTimeframe) -> List[AnalyticsMetric]:
        """Get knowledge-related metrics"""
        metrics = []
        
        try:
            # Get knowledge graph data
            kg_data = await self.kg_service.get_user_knowledge_graph(user_id)
            
            if kg_data:
                # Entity count
                entity_count = len(kg_data.get('entities', []))
                metrics.append(AnalyticsMetric(
                    name="Knowledge Entities",
                    value=entity_count,
                    metric_type=MetricType.KNOWLEDGE,
                    description="Number of entities in knowledge graph",
                    unit="entities"
                ))
                
                # Relationship count
                relationship_count = len(kg_data.get('relationships', []))
                metrics.append(AnalyticsMetric(
                    name="Knowledge Relationships",
                    value=relationship_count,
                    metric_type=MetricType.KNOWLEDGE,
                    description="Number of relationships in knowledge graph",
                    unit="relationships"
                ))
                
                # Knowledge density
                if entity_count > 1:
                    max_relationships = entity_count * (entity_count - 1) / 2
                    density = relationship_count / max_relationships if max_relationships > 0 else 0
                    metrics.append(AnalyticsMetric(
                        name="Knowledge Density",
                        value=round(density, 3),
                        metric_type=MetricType.KNOWLEDGE,
                        description="Density of knowledge graph connections",
                        unit="ratio"
                    ))
        
        except Exception as e:
            logger.warning(f"Error getting knowledge metrics: {str(e)}")
        
        return metrics

    async def _generate_visualizations(
        self, user_id: str, timeframe: AnalyticsTimeframe, metrics: List[AnalyticsMetric]
    ) -> List[VisualizationData]:
        """Generate visualizations for metrics"""
        visualizations = []
        
        # Usage metrics visualization
        usage_metrics = [m for m in metrics if m.metric_type == MetricType.USAGE]
        if usage_metrics:
            viz = VisualizationData(
                chart_type=VisualizationType.BAR_CHART,
                title="Usage Metrics",
                data={
                    "labels": [m.name for m in usage_metrics],
                    "values": [m.value for m in usage_metrics]
                },
                config={"orientation": "horizontal"},
                description="Overview of usage patterns and activity levels",
                insights=[f"Total activity: {sum(m.value for m in usage_metrics if isinstance(m.value, (int, float)))}"]
            )
            visualizations.append(viz)
        
        # Performance metrics visualization
        performance_metrics = [m for m in metrics if m.metric_type == MetricType.PERFORMANCE]
        if performance_metrics:
            viz = VisualizationData(
                chart_type=VisualizationType.LINE_CHART,
                title="Performance Metrics",
                data={
                    "labels": [m.name for m in performance_metrics],
                    "values": [m.value for m in performance_metrics]
                },
                config={"show_trend": True},
                description="System performance and processing efficiency",
                insights=["Performance metrics show system efficiency"]
            )
            visualizations.append(viz)
        
        # Content distribution
        content_viz = await self._create_content_distribution_viz(user_id)
        if content_viz:
            visualizations.append(content_viz)
        
        return visualizations

    async def _create_content_distribution_viz(self, user_id: str) -> Optional[VisualizationData]:
        """Create content distribution visualization"""
        try:
            documents = self.db.query(Document).filter(
                Document.user_id == user_id,
                Document.status == "completed"
            ).all()
            
            if not documents:
                return None
            
            content_types = Counter([doc.content_type for doc in documents])
            
            return VisualizationData(
                chart_type=VisualizationType.PIE_CHART,
                title="Content Type Distribution",
                data={
                    "labels": list(content_types.keys()),
                    "values": list(content_types.values())
                },
                config={"show_percentages": True},
                description="Distribution of content types in your document collection",
                insights=[f"Most common type: {max(content_types.items(), key=lambda x: x[1])[0]}"]
            )
            
        except Exception as e:
            logger.warning(f"Error creating content distribution viz: {str(e)}")
            return None

    async def _generate_insights(
        self, metrics: List[AnalyticsMetric], visualizations: List[VisualizationData]
    ) -> List[str]:
        """Generate insights from metrics and visualizations"""
        insights = []
        
        # Usage insights
        usage_metrics = [m for m in metrics if m.metric_type == MetricType.USAGE]
        if usage_metrics:
            total_events = sum(m.value for m in usage_metrics if m.name == "Total Events")
            if total_events > 100:
                insights.append("High user engagement with frequent system interactions")
            elif total_events > 20:
                insights.append("Moderate user engagement with regular system usage")
            else:
                insights.append("Low user engagement - consider exploring more features")
        
        # Performance insights
        performance_metrics = [m for m in metrics if m.metric_type == MetricType.PERFORMANCE]
        for metric in performance_metrics:
            if metric.name == "Processing Success Rate" and isinstance(metric.value, (int, float)):
                if metric.value > 95:
                    insights.append("Excellent processing success rate")
                elif metric.value > 80:
                    insights.append("Good processing success rate with room for improvement")
                else:
                    insights.append("Processing success rate needs attention")
        
        # Content insights
        content_metrics = [m for m in metrics if m.metric_type == MetricType.CONTENT]
        doc_count = next((m.value for m in content_metrics if m.name == "Total Documents"), 0)
        if doc_count > 50:
            insights.append("Large document collection provides rich knowledge base")
        elif doc_count > 10:
            insights.append("Growing document collection with good knowledge diversity")
        else:
            insights.append("Small document collection - consider adding more content")
        
        return insights

    async def _generate_recommendations(
        self, metrics: List[AnalyticsMetric], insights: List[str]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Usage-based recommendations
        usage_metrics = [m for m in metrics if m.metric_type == MetricType.USAGE]
        feature_diversity = next((m.value for m in usage_metrics if m.name == "Feature Usage Diversity"), 0)
        
        if feature_diversity < 3:
            recommendations.append("Explore more features to maximize system value")
        
        # Performance-based recommendations
        performance_metrics = [m for m in metrics if m.metric_type == MetricType.PERFORMANCE]
        for metric in performance_metrics:
            if metric.name == "Average Processing Time" and isinstance(metric.value, (int, float)):
                if metric.value > 10:
                    recommendations.append("Consider optimizing document sizes for faster processing")
        
        # Content-based recommendations
        content_metrics = [m for m in metrics if m.metric_type == MetricType.CONTENT]
        content_diversity = next((m.value for m in content_metrics if m.name == "Content Type Diversity"), 0)
        
        if content_diversity < 3:
            recommendations.append("Diversify content types for richer knowledge representation")
        
        # Knowledge-based recommendations
        knowledge_metrics = [m for m in metrics if m.metric_type == MetricType.KNOWLEDGE]
        entity_count = next((m.value for m in knowledge_metrics if m.name == "Knowledge Entities"), 0)
        
        if entity_count < 10:
            recommendations.append("Add more documents to build a richer knowledge graph")
        
        return recommendations

    def _calculate_report_confidence(
        self, metrics: List[AnalyticsMetric], visualizations: List[VisualizationData]
    ) -> float:
        """Calculate confidence score for the report"""
        confidence_factors = []
        
        # Data availability factor
        data_points = len(metrics)
        if data_points > 20:
            confidence_factors.append(0.9)
        elif data_points > 10:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.5)
        
        # Visualization quality factor
        viz_count = len(visualizations)
        if viz_count > 5:
            confidence_factors.append(0.9)
        elif viz_count > 2:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.6)
        
        # Metric diversity factor
        metric_types = set([m.metric_type for m in metrics])
        diversity_score = len(metric_types) / len(MetricType)
        confidence_factors.append(diversity_score)
        
        return sum(confidence_factors) / len(confidence_factors)

    async def _generate_report_summary(
        self, metrics: List[AnalyticsMetric], insights: List[str]
    ) -> str:
        """Generate executive summary for the report"""
        summary_parts = []
        
        # Overview
        summary_parts.append(f"Analytics report generated with {len(metrics)} metrics across {len(set([m.metric_type for m in metrics]))} categories.")
        
        # Key highlights
        usage_events = next((m.value for m in metrics if m.name == "Total Events"), 0)
        doc_count = next((m.value for m in metrics if m.name == "Total Documents"), 0)
        
        summary_parts.append(f"User activity includes {usage_events} total events across {doc_count} documents.")
        
        # Top insights
        if insights:
            summary_parts.append(f"Key insight: {insights[0]}")
        
        return " ".join(summary_parts)

    async def _store_report(self, user_id: str, report: InsightReport):
        """Store analytics report in database"""
        try:
            # Store as analytics event
            event = AnalyticsEvent(
                user_id=user_id,
                event_type="analytics_report_generated",
                event_data={
                    "report_id": report.id,
                    "title": report.title,
                    "timeframe": report.timeframe.value,
                    "metrics_count": len(report.metrics),
                    "visualizations_count": len(report.visualizations),
                    "confidence_score": report.confidence_score,
                    "generated_at": report.generated_at.isoformat()
                }
            )
            
            self.db.add(event)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error storing report: {str(e)}")

    # Additional helper methods for pattern discovery and analysis
    async def _find_shared_concepts(self, content1: str, content2: str) -> List[str]:
        """Find shared concepts between two pieces of content"""
        try:
            # Simple approach using TF-IDF
            vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform([content1, content2])
            
            feature_names = vectorizer.get_feature_names_out()
            
            # Get top terms for each document
            doc1_scores = tfidf_matrix[0].toarray()[0]
            doc2_scores = tfidf_matrix[1].toarray()[0]
            
            # Find terms that appear in both with significant scores
            shared_concepts = []
            for i, (score1, score2) in enumerate(zip(doc1_scores, doc2_scores)):
                if score1 > 0.1 and score2 > 0.1:  # Both documents have this term
                    shared_concepts.append(feature_names[i])
            
            return shared_concepts[:10]  # Return top 10
            
        except Exception as e:
            logger.warning(f"Error finding shared concepts: {str(e)}")
            return []

    def _classify_relationship_type(
        self, doc1: Dict, doc2: Dict, similarity: float, shared_concepts: List[str]
    ) -> str:
        """Classify the type of relationship between documents"""
        
        # Time-based relationships
        if doc1.get('created_at') and doc2.get('created_at'):
            time_diff = abs((doc1['created_at'] - doc2['created_at']).days)
            if time_diff < 7:
                return "temporal_proximity"
        
        # Content similarity relationships
        if similarity > 0.8:
            return "high_similarity"
        elif similarity > 0.6:
            return "moderate_similarity"
        elif similarity > 0.3:
            return "low_similarity"
        
        # Concept-based relationships
        if len(shared_concepts) > 5:
            return "concept_overlap"
        
        return "related"

    async def _analyze_user_sessions(self, events: List[AnalyticsEvent]) -> Dict[str, Any]:
        """Analyze user sessions from events"""
        if not events:
            return {"total_sessions": 0, "average_duration": 0}
        
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda x: x.created_at)
        
        sessions = []
        current_session = [sorted_events[0]]
        session_timeout = timedelta(minutes=30)  # 30 minutes timeout
        
        for event in sorted_events[1:]:
            time_diff = event.created_at - current_session[-1].created_at
            
            if time_diff <= session_timeout:
                current_session.append(event)
            else:
                sessions.append(current_session)
                current_session = [event]
        
        # Add the last session
        if current_session:
            sessions.append(current_session)
        
        # Calculate session statistics
        session_durations = []
        for session in sessions:
            if len(session) > 1:
                duration = (session[-1].created_at - session[0].created_at).total_seconds() / 60
                session_durations.append(duration)
        
        avg_duration = sum(session_durations) / len(session_durations) if session_durations else 0
        
        return {
            "total_sessions": len(sessions),
            "average_duration": avg_duration,
            "average_events_per_session": sum(len(s) for s in sessions) / len(sessions)
        }

    async def _calculate_usage_trends(
        self, events: List[AnalyticsEvent], timeframe: AnalyticsTimeframe
    ) -> Dict[str, Any]:
        """Calculate usage trends over time"""
        if not events or timeframe == AnalyticsTimeframe.ALL_TIME:
            return {}
        
        # Group events by time periods
        time_groups = defaultdict(int)
        
        for event in events:
            if timeframe == AnalyticsTimeframe.DAY:
                key = event.created_at.strftime("%Y-%m-%d %H:00")
            elif timeframe == AnalyticsTimeframe.WEEK:
                key = event.created_at.strftime("%Y-%m-%d")
            elif timeframe == AnalyticsTimeframe.MONTH:
                key = event.created_at.strftime("%Y-%m-%d")
            else:
                key = event.created_at.strftime("%Y-%m")
            
            time_groups[key] += 1
        
        # Calculate trend
        values = list(time_groups.values())
        if len(values) > 1:
            trend = (values[-1] - values[0]) / values[0] * 100 if values[0] > 0 else 0
        else:
            trend = 0
        
        return {
            "time_series": dict(time_groups),
            "trend_percentage": trend,
            "peak_activity": max(time_groups.items(), key=lambda x: x[1]) if time_groups else None
        }

    async def _calculate_content_growth_trends(
        self, user_id: str, timeframe: AnalyticsTimeframe
    ) -> Dict[str, Any]:
        """Calculate content growth trends"""
        try:
            # Get documents over time
            end_date = datetime.utcnow()
            start_date = end_date - self.timeframe_deltas[timeframe]
            
            documents = self.db.query(Document).filter(
                Document.user_id == user_id,
                Document.created_at >= start_date,
                Document.created_at <= end_date
            ).order_by(Document.created_at).all()
            
            if not documents:
                return {}
            
            # Group by time periods
            time_groups = defaultdict(int)
            size_groups = defaultdict(int)
            
            for doc in documents:
                if timeframe == AnalyticsTimeframe.WEEK:
                    key = doc.created_at.strftime("%Y-%m-%d")
                elif timeframe == AnalyticsTimeframe.MONTH:
                    key = doc.created_at.strftime("%Y-%m-%d")
                else:
                    key = doc.created_at.strftime("%Y-%m")
                
                time_groups[key] += 1
                size_groups[key] += doc.size or 0
            
            # Calculate trends
            doc_counts = list(time_groups.values())
            size_values = list(size_groups.values())
            
            doc_trend = 0
            size_trend = 0
            
            if len(doc_counts) > 1:
                doc_trend = (doc_counts[-1] - doc_counts[0]) / doc_counts[0] * 100 if doc_counts[0] > 0 else 0
            
            if len(size_values) > 1:
                size_trend = (size_values[-1] - size_values[0]) / size_values[0] * 100 if size_values[0] > 0 else 0
            
            return {
                "document_count_trend": doc_trend,
                "content_size_trend": size_trend,
                "time_series_counts": dict(time_groups),
                "time_series_sizes": dict(size_groups)
            }
            
        except Exception as e:
            logger.warning(f"Error calculating content growth trends: {str(e)}")
            return {}

    # Pattern discovery helper methods
    async def _find_cooccurrence_patterns(
        self, kg_data: Dict, min_frequency: int, confidence_threshold: float
    ) -> List[KnowledgePattern]:
        """Find entity co-occurrence patterns"""
        patterns = []
        
        try:
            entities = kg_data.get('entities', [])
            relationships = kg_data.get('relationships', [])
            
            # Build co-occurrence matrix
            entity_pairs = defaultdict(int)
            
            for rel in relationships:
                source = rel.get('source')
                target = rel.get('target')
                if source and target:
                    pair = tuple(sorted([source, target]))
                    entity_pairs[pair] += 1
            
            # Find frequent patterns
            for (entity1, entity2), frequency in entity_pairs.items():
                if frequency >= min_frequency:
                    confidence = frequency / len(relationships) if relationships else 0
                    
                    if confidence >= confidence_threshold:
                        pattern = KnowledgePattern(
                            pattern_id=str(uuid.uuid4()),
                            pattern_type="entity_cooccurrence",
                            entities=[entity1, entity2],
                            relationships=["co_occurs"],
                            frequency=frequency,
                            confidence=confidence,
                            examples=[f"{entity1} and {entity2} appear together {frequency} times"]
                        )
                        patterns.append(pattern)
            
        except Exception as e:
            logger.warning(f"Error finding co-occurrence patterns: {str(e)}")
        
        return patterns

    async def _find_relationship_chains(
        self, kg_data: Dict, min_frequency: int, confidence_threshold: float
    ) -> List[KnowledgePattern]:
        """Find relationship chain patterns"""
        patterns = []
        
        try:
            relationships = kg_data.get('relationships', [])
            
            # Build relationship chains (A -> B -> C)
            chains = defaultdict(int)
            
            # Create adjacency list
            graph = defaultdict(list)
            for rel in relationships:
                source = rel.get('source')
                target = rel.get('target')
                rel_type = rel.get('type', 'related')
                if source and target:
                    graph[source].append((target, rel_type))
            
            # Find 2-hop chains
            for node1 in graph:
                for node2, rel1_type in graph[node1]:
                    for node3, rel2_type in graph.get(node2, []):
                        if node1 != node3:  # Avoid self-loops
                            chain = (node1, rel1_type, node2, rel2_type, node3)
                            chains[chain] += 1
            
            # Find frequent chains
            for chain, frequency in chains.items():
                if frequency >= min_frequency:
                    confidence = frequency / len(relationships) if relationships else 0
                    
                    if confidence >= confidence_threshold:
                        pattern = KnowledgePattern(
                            pattern_id=str(uuid.uuid4()),
                            pattern_type="relationship_chain",
                            entities=[chain[0], chain[2], chain[4]],
                            relationships=[chain[1], chain[3]],
                            frequency=frequency,
                            confidence=confidence,
                            examples=[f"{chain[0]} -> {chain[2]} -> {chain[4]} (frequency: {frequency})"]
                        )
                        patterns.append(pattern)
            
        except Exception as e:
            logger.warning(f"Error finding relationship chains: {str(e)}")
        
        return patterns

    async def _find_concept_clusters(
        self, kg_data: Dict, min_frequency: int, confidence_threshold: float
    ) -> List[KnowledgePattern]:
        """Find concept cluster patterns"""
        patterns = []
        
        try:
            entities = kg_data.get('entities', [])
            relationships = kg_data.get('relationships', [])
            
            if len(entities) < 3:
                return patterns
            
            # Create NetworkX graph
            G = nx.Graph()
            
            for entity in entities:
                G.add_node(entity['id'], **entity)
            
            for rel in relationships:
                source = rel.get('source')
                target = rel.get('target')
                if source and target and source in G.nodes and target in G.nodes:
                    G.add_edge(source, target, **rel)
            
            # Find communities/clusters
            try:
                communities = nx.community.greedy_modularity_communities(G)
                
                for i, community in enumerate(communities):
                    if len(community) >= 3:  # Minimum cluster size
                        # Calculate cluster metrics
                        subgraph = G.subgraph(community)
                        density = nx.density(subgraph)
                        
                        if density >= confidence_threshold:
                            pattern = KnowledgePattern(
                                pattern_id=str(uuid.uuid4()),
                                pattern_type="concept_cluster",
                                entities=list(community),
                                relationships=["clustered_with"],
                                frequency=len(community),
                                confidence=density,
                                examples=[f"Cluster {i+1} with {len(community)} entities (density: {density:.3f})"]
                            )
                            patterns.append(pattern)
                            
            except Exception as e:
                logger.warning(f"Community detection failed: {str(e)}")
            
        except Exception as e:
            logger.warning(f"Error finding concept clusters: {str(e)}")
        
        return patterns

    async def _find_temporal_patterns(
        self, user_id: str, kg_data: Dict, min_frequency: int, confidence_threshold: float
    ) -> List[KnowledgePattern]:
        """Find temporal patterns in knowledge evolution"""
        patterns = []
        
        try:
            # Get documents with timestamps
            documents = self.db.query(Document).filter(
                Document.user_id == user_id,
                Document.status == "completed"
            ).order_by(Document.created_at).all()
            
            if len(documents) < 3:
                return patterns
            
            # Analyze entity emergence over time
            entity_timeline = defaultdict(list)
            
            for doc in documents:
                # Get entities mentioned in this document
                # This is a simplified approach - in practice, you'd extract entities from document content
                doc_entities = []  # Would be populated with actual entity extraction
                
                for entity in doc_entities:
                    entity_timeline[entity].append(doc.created_at)
            
            # Find patterns in entity co-emergence
            for entity, timestamps in entity_timeline.items():
                if len(timestamps) >= min_frequency:
                    # Calculate temporal clustering
                    time_diffs = []
                    for i in range(1, len(timestamps)):
                        diff = (timestamps[i] - timestamps[i-1]).days
                        time_diffs.append(diff)
                    
                    if time_diffs:
                        avg_interval = sum(time_diffs) / len(time_diffs)
                        
                        if avg_interval < 30:  # Entities appearing within 30 days
                            pattern = KnowledgePattern(
                                pattern_id=str(uuid.uuid4()),
                                pattern_type="temporal_clustering",
                                entities=[entity],
                                relationships=["temporal_proximity"],
                                frequency=len(timestamps),
                                confidence=min(1.0, 30 / avg_interval),  # Higher confidence for shorter intervals
                                examples=[f"{entity} appears {len(timestamps)} times with avg interval {avg_interval:.1f} days"]
                            )
                            patterns.append(pattern)
            
        except Exception as e:
            logger.warning(f"Error finding temporal patterns: {str(e)}")
        
        return patterns

# Export classes
__all__ = [
    'AdvancedAnalyticsService',
    'AnalyticsMetric',
    'VisualizationData',
    'InsightReport',
    'DocumentRelationship',
    'KnowledgePattern',
    'AnalyticsTimeframe',
    'VisualizationType',
    'MetricType'
]