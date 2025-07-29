"""
Trend Analysis Service for document collection analysis and comparative reporting
"""
import json
import logging
import statistics
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from core.database import (
    Document, DocumentTag, AnalyticsEvent, 
    KnowledgeGraphEntity, KnowledgeGraphRelationship,
    get_db
)
from models.schemas import (
    DocumentTagResponse, AnalyticsEventResponse,
    KnowledgeGraphEntityResponse
)

logger = logging.getLogger(__name__)

class TrendAnalyzer:
    """Service for analyzing trends across document collections and generating comparative reports"""
    
    def __init__(self):
        self.min_documents_for_trend = 3
        self.trend_confidence_threshold = 0.7
        self.comparison_similarity_threshold = 0.6
        
    async def analyze_document_collection_trends(
        self,
        user_id: str,
        db: Session,
        time_range_days: int = 30,
        tag_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze trends across a user's document collection
        
        Args:
            user_id: ID of the user
            db: Database session
            time_range_days: Number of days to analyze
            tag_types: Optional filter for specific tag types
            
        Returns:
            Comprehensive trend analysis results
        """
        try:
            start_date = datetime.now() - timedelta(days=time_range_days)
            
            # Get documents in time range
            documents_query = db.query(Document).filter(
                Document.user_id == user_id,
                Document.created_at >= start_date
            )
            documents = documents_query.all()
            
            if len(documents) < self.min_documents_for_trend:
                return {
                    "status": "insufficient_data",
                    "message": f"Need at least {self.min_documents_for_trend} documents for trend analysis",
                    "document_count": len(documents),
                    "trends": {}
                }
            
            # Analyze different trend dimensions
            tag_trends = await self._analyze_tag_trends(documents, db, tag_types)
            temporal_trends = await self._analyze_temporal_trends(documents, db)
            topic_evolution = await self._analyze_topic_evolution(documents, db)
            complexity_trends = await self._analyze_complexity_trends(documents, db)
            domain_trends = await self._analyze_domain_trends(documents, db)
            
            # Generate insights and recommendations
            insights = await self._generate_trend_insights(
                tag_trends, temporal_trends, topic_evolution, 
                complexity_trends, domain_trends
            )
            
            return {
                "status": "success",
                "analysis_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": datetime.now().isoformat(),
                    "days": time_range_days
                },
                "document_count": len(documents),
                "trends": {
                    "tag_trends": tag_trends,
                    "temporal_trends": temporal_trends,
                    "topic_evolution": topic_evolution,
                    "complexity_trends": complexity_trends,
                    "domain_trends": domain_trends
                },
                "insights": insights,
                "metadata": {
                    "analysis_timestamp": datetime.now().isoformat(),
                    "confidence_threshold": self.trend_confidence_threshold
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing document collection trends: {str(e)}")
            raise
    
    async def _analyze_tag_trends(
        self,
        documents: List[Document],
        db: Session,
        tag_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze trends in document tags over time"""
        try:
            document_ids = [doc.id for doc in documents]
            
            # Get tags for documents
            tags_query = db.query(DocumentTag).filter(
                DocumentTag.document_id.in_(document_ids)
            )
            
            if tag_types:
                tags_query = tags_query.filter(DocumentTag.tag_type.in_(tag_types))
            
            tags = tags_query.all()
            
            # Group tags by type and analyze trends
            tags_by_type = defaultdict(list)
            for tag in tags:
                tags_by_type[tag.tag_type].append(tag)
            
            trend_results = {}
            
            for tag_type, type_tags in tags_by_type.items():
                # Count tag frequency
                tag_counts = Counter(tag.tag_name for tag in type_tags)
                
                # Calculate confidence statistics
                confidence_scores = [tag.confidence_score for tag in type_tags]
                avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0
                
                # Identify trending tags (appearing frequently with high confidence)
                trending_tags = []
                for tag_name, count in tag_counts.most_common(10):
                    tag_confidences = [
                        tag.confidence_score for tag in type_tags 
                        if tag.tag_name == tag_name
                    ]
                    avg_tag_confidence = statistics.mean(tag_confidences)
                    
                    if avg_tag_confidence >= self.trend_confidence_threshold:
                        trending_tags.append({
                            "tag_name": tag_name,
                            "frequency": count,
                            "average_confidence": avg_tag_confidence,
                            "trend_strength": count * avg_tag_confidence
                        })
                
                trend_results[tag_type] = {
                    "total_tags": len(type_tags),
                    "unique_tags": len(tag_counts),
                    "average_confidence": avg_confidence,
                    "trending_tags": trending_tags,
                    "tag_distribution": dict(tag_counts.most_common(20))
                }
            
            return trend_results
            
        except Exception as e:
            logger.error(f"Error analyzing tag trends: {str(e)}")
            return {}
    
    async def _analyze_temporal_trends(
        self,
        documents: List[Document],
        db: Session
    ) -> Dict[str, Any]:
        """Analyze temporal patterns in document creation and processing"""
        try:
            # Group documents by time periods
            daily_counts = defaultdict(int)
            weekly_counts = defaultdict(int)
            monthly_counts = defaultdict(int)
            
            for doc in documents:
                date = doc.created_at.date()
                daily_counts[date.isoformat()] += 1
                
                # Week starting Monday
                week_start = date - timedelta(days=date.weekday())
                weekly_counts[week_start.isoformat()] += 1
                
                # Month
                month_key = f"{date.year}-{date.month:02d}"
                monthly_counts[month_key] += 1
            
            # Calculate trends
            daily_values = list(daily_counts.values())
            avg_daily = statistics.mean(daily_values) if daily_values else 0
            
            # Detect patterns
            patterns = []
            
            # Check for increasing/decreasing trends
            if len(daily_values) >= 7:
                recent_avg = statistics.mean(daily_values[-7:])
                earlier_avg = statistics.mean(daily_values[:-7])
                
                if recent_avg > earlier_avg * 1.2:
                    patterns.append({
                        "type": "increasing_activity",
                        "description": "Document upload activity has increased recently",
                        "confidence": min((recent_avg / earlier_avg - 1), 1.0)
                    })
                elif recent_avg < earlier_avg * 0.8:
                    patterns.append({
                        "type": "decreasing_activity",
                        "description": "Document upload activity has decreased recently",
                        "confidence": min((1 - recent_avg / earlier_avg), 1.0)
                    })
            
            return {
                "daily_distribution": dict(daily_counts),
                "weekly_distribution": dict(weekly_counts),
                "monthly_distribution": dict(monthly_counts),
                "statistics": {
                    "average_daily_uploads": avg_daily,
                    "peak_day": max(daily_counts.items(), key=lambda x: x[1]) if daily_counts else None,
                    "total_days_active": len(daily_counts)
                },
                "patterns": patterns
            }
            
        except Exception as e:
            logger.error(f"Error analyzing temporal trends: {str(e)}")
            return {}
    
    async def _analyze_topic_evolution(
        self,
        documents: List[Document],
        db: Session
    ) -> Dict[str, Any]:
        """Analyze how topics evolve over time in the document collection"""
        try:
            document_ids = [doc.id for doc in documents]
            
            # Get topic tags with timestamps
            topic_tags = db.query(DocumentTag, Document.created_at).join(
                Document, DocumentTag.document_id == Document.id
            ).filter(
                DocumentTag.document_id.in_(document_ids),
                DocumentTag.tag_type == 'topic'
            ).all()
            
            if not topic_tags:
                return {"status": "no_topic_data"}
            
            # Group by time periods
            topic_timeline = defaultdict(lambda: defaultdict(int))
            
            for tag, created_at in topic_tags:
                # Group by week
                week_start = created_at.date() - timedelta(days=created_at.weekday())
                week_key = week_start.isoformat()
                topic_timeline[week_key][tag.tag_name] += 1
            
            # Analyze topic evolution patterns
            all_topics = set()
            for week_topics in topic_timeline.values():
                all_topics.update(week_topics.keys())
            
            topic_evolution = {}
            for topic in all_topics:
                appearances = []
                for week in sorted(topic_timeline.keys()):
                    count = topic_timeline[week].get(topic, 0)
                    appearances.append(count)
                
                # Calculate trend
                if len(appearances) >= 3:
                    recent_avg = statistics.mean(appearances[-3:])
                    earlier_avg = statistics.mean(appearances[:-3]) if len(appearances) > 3 else 0
                    
                    trend_direction = "stable"
                    trend_strength = 0
                    
                    if earlier_avg > 0:
                        ratio = recent_avg / earlier_avg
                        if ratio > 1.5:
                            trend_direction = "increasing"
                            trend_strength = min(ratio - 1, 2.0)
                        elif ratio < 0.5:
                            trend_direction = "decreasing"
                            trend_strength = min(1 - ratio, 1.0)
                    elif recent_avg > 0:
                        trend_direction = "emerging"
                        trend_strength = min(recent_avg, 1.0)
                    
                    topic_evolution[topic] = {
                        "trend_direction": trend_direction,
                        "trend_strength": trend_strength,
                        "total_appearances": sum(appearances),
                        "recent_activity": recent_avg,
                        "timeline": appearances
                    }
            
            # Identify emerging and declining topics
            emerging_topics = [
                topic for topic, data in topic_evolution.items()
                if data["trend_direction"] in ["emerging", "increasing"] and data["trend_strength"] > 0.5
            ]
            
            declining_topics = [
                topic for topic, data in topic_evolution.items()
                if data["trend_direction"] == "decreasing" and data["trend_strength"] > 0.5
            ]
            
            return {
                "topic_evolution": topic_evolution,
                "timeline": dict(topic_timeline),
                "emerging_topics": emerging_topics,
                "declining_topics": declining_topics,
                "total_topics_tracked": len(all_topics)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing topic evolution: {str(e)}")
            return {}
    
    async def _analyze_complexity_trends(
        self,
        documents: List[Document],
        db: Session
    ) -> Dict[str, Any]:
        """Analyze trends in document complexity over time"""
        try:
            document_ids = [doc.id for doc in documents]
            
            # Get complexity tags
            complexity_tags = db.query(DocumentTag, Document.created_at).join(
                Document, DocumentTag.document_id == Document.id
            ).filter(
                DocumentTag.document_id.in_(document_ids),
                DocumentTag.tag_type == 'complexity'
            ).all()
            
            if not complexity_tags:
                return {"status": "no_complexity_data"}
            
            # Map complexity levels to numeric values
            complexity_mapping = {
                "complexity_beginner": 1,
                "complexity_intermediate": 2,
                "complexity_advanced": 3,
                "complexity_expert": 4
            }
            
            # Analyze complexity over time
            complexity_timeline = []
            for tag, created_at in complexity_tags:
                if tag.tag_name in complexity_mapping:
                    complexity_timeline.append({
                        "date": created_at.date(),
                        "complexity_level": complexity_mapping[tag.tag_name],
                        "confidence": tag.confidence_score
                    })
            
            # Sort by date
            complexity_timeline.sort(key=lambda x: x["date"])
            
            # Calculate trends
            if len(complexity_timeline) >= 5:
                recent_complexity = [
                    item["complexity_level"] for item in complexity_timeline[-5:]
                ]
                earlier_complexity = [
                    item["complexity_level"] for item in complexity_timeline[:-5]
                ]
                
                recent_avg = statistics.mean(recent_complexity)
                earlier_avg = statistics.mean(earlier_complexity) if earlier_complexity else recent_avg
                
                trend_analysis = {
                    "recent_average_complexity": recent_avg,
                    "earlier_average_complexity": earlier_avg,
                    "complexity_trend": "increasing" if recent_avg > earlier_avg * 1.1 else 
                                     "decreasing" if recent_avg < earlier_avg * 0.9 else "stable",
                    "trend_strength": abs(recent_avg - earlier_avg) / 4.0  # Normalize to 0-1
                }
            else:
                trend_analysis = {
                    "status": "insufficient_data_for_trend",
                    "data_points": len(complexity_timeline)
                }
            
            # Distribution analysis
            complexity_distribution = Counter(
                item["complexity_level"] for item in complexity_timeline
            )
            
            return {
                "trend_analysis": trend_analysis,
                "complexity_distribution": dict(complexity_distribution),
                "timeline": complexity_timeline,
                "total_documents_analyzed": len(complexity_timeline)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing complexity trends: {str(e)}")
            return {}
    
    async def _analyze_domain_trends(
        self,
        documents: List[Document],
        db: Session
    ) -> Dict[str, Any]:
        """Analyze trends in document domains over time"""
        try:
            document_ids = [doc.id for doc in documents]
            
            # Get domain tags
            domain_tags = db.query(DocumentTag, Document.created_at).join(
                Document, DocumentTag.document_id == Document.id
            ).filter(
                DocumentTag.document_id.in_(document_ids),
                DocumentTag.tag_type == 'domain'
            ).all()
            
            if not domain_tags:
                return {"status": "no_domain_data"}
            
            # Analyze domain distribution and trends
            domain_timeline = defaultdict(lambda: defaultdict(int))
            domain_confidence = defaultdict(list)
            
            for tag, created_at in domain_tags:
                week_start = created_at.date() - timedelta(days=created_at.weekday())
                week_key = week_start.isoformat()
                domain_timeline[week_key][tag.tag_name] += 1
                domain_confidence[tag.tag_name].append(tag.confidence_score)
            
            # Calculate domain statistics
            domain_stats = {}
            for domain, confidences in domain_confidence.items():
                total_appearances = sum(
                    week_data.get(domain, 0) 
                    for week_data in domain_timeline.values()
                )
                
                domain_stats[domain] = {
                    "total_appearances": total_appearances,
                    "average_confidence": statistics.mean(confidences),
                    "confidence_std": statistics.stdev(confidences) if len(confidences) > 1 else 0,
                    "weeks_active": sum(1 for week_data in domain_timeline.values() if domain in week_data)
                }
            
            # Identify dominant and emerging domains
            sorted_domains = sorted(
                domain_stats.items(),
                key=lambda x: x[1]["total_appearances"],
                reverse=True
            )
            
            dominant_domains = [
                domain for domain, stats in sorted_domains[:5]
                if stats["average_confidence"] >= self.trend_confidence_threshold
            ]
            
            # Detect domain shifts
            domain_shifts = []
            if len(domain_timeline) >= 4:
                recent_weeks = list(sorted(domain_timeline.keys()))[-2:]
                earlier_weeks = list(sorted(domain_timeline.keys()))[:-2]
                
                recent_domains = set()
                earlier_domains = set()
                
                for week in recent_weeks:
                    recent_domains.update(domain_timeline[week].keys())
                
                for week in earlier_weeks:
                    earlier_domains.update(domain_timeline[week].keys())
                
                new_domains = recent_domains - earlier_domains
                disappeared_domains = earlier_domains - recent_domains
                
                if new_domains:
                    domain_shifts.append({
                        "type": "new_domains_emerged",
                        "domains": list(new_domains),
                        "description": f"New domains appeared: {', '.join(new_domains)}"
                    })
                
                if disappeared_domains:
                    domain_shifts.append({
                        "type": "domains_disappeared",
                        "domains": list(disappeared_domains),
                        "description": f"Domains no longer active: {', '.join(disappeared_domains)}"
                    })
            
            return {
                "domain_statistics": domain_stats,
                "dominant_domains": dominant_domains,
                "domain_timeline": dict(domain_timeline),
                "domain_shifts": domain_shifts,
                "total_unique_domains": len(domain_stats)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing domain trends: {str(e)}")
            return {}
    
    async def _generate_trend_insights(
        self,
        tag_trends: Dict[str, Any],
        temporal_trends: Dict[str, Any],
        topic_evolution: Dict[str, Any],
        complexity_trends: Dict[str, Any],
        domain_trends: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actionable insights from trend analysis"""
        insights = []
        
        try:
            # Tag trend insights
            if tag_trends:
                for tag_type, data in tag_trends.items():
                    if data.get("trending_tags"):
                        top_tag = data["trending_tags"][0]
                        insights.append({
                            "type": "trending_tag",
                            "category": tag_type,
                            "insight": f"'{top_tag['tag_name']}' is trending in {tag_type} tags",
                            "confidence": top_tag["average_confidence"],
                            "recommendation": f"Consider exploring more content related to {top_tag['tag_name']}"
                        })
            
            # Temporal insights
            if temporal_trends.get("patterns"):
                for pattern in temporal_trends["patterns"]:
                    insights.append({
                        "type": "temporal_pattern",
                        "category": "activity",
                        "insight": pattern["description"],
                        "confidence": pattern["confidence"],
                        "recommendation": "Monitor activity patterns for optimal content planning"
                    })
            
            # Topic evolution insights
            if topic_evolution.get("emerging_topics"):
                insights.append({
                    "type": "emerging_topics",
                    "category": "content",
                    "insight": f"Emerging topics: {', '.join(topic_evolution['emerging_topics'][:3])}",
                    "confidence": 0.8,
                    "recommendation": "Focus on emerging topics for future content"
                })
            
            if topic_evolution.get("declining_topics"):
                insights.append({
                    "type": "declining_topics",
                    "category": "content",
                    "insight": f"Declining topics: {', '.join(topic_evolution['declining_topics'][:3])}",
                    "confidence": 0.8,
                    "recommendation": "Consider refreshing or updating content in declining areas"
                })
            
            # Complexity insights
            if complexity_trends.get("trend_analysis", {}).get("complexity_trend"):
                trend = complexity_trends["trend_analysis"]["complexity_trend"]
                if trend != "stable":
                    insights.append({
                        "type": "complexity_trend",
                        "category": "difficulty",
                        "insight": f"Document complexity is {trend}",
                        "confidence": complexity_trends["trend_analysis"].get("trend_strength", 0.5),
                        "recommendation": f"Consider balancing content complexity based on {trend} trend"
                    })
            
            # Domain insights
            if domain_trends.get("domain_shifts"):
                for shift in domain_trends["domain_shifts"]:
                    insights.append({
                        "type": "domain_shift",
                        "category": "focus",
                        "insight": shift["description"],
                        "confidence": 0.7,
                        "recommendation": "Monitor domain shifts to align with changing interests"
                    })
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating trend insights: {str(e)}")
            return []
    
    async def compare_documents(
        self,
        document_ids: List[str],
        db: Session,
        comparison_aspects: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform comparative analysis between multiple documents
        
        Args:
            document_ids: List of document IDs to compare
            db: Database session
            comparison_aspects: Specific aspects to compare (tags, complexity, etc.)
            
        Returns:
            Comprehensive comparison results
        """
        try:
            if len(document_ids) < 2:
                raise ValueError("Need at least 2 documents for comparison")
            
            # Get documents
            documents = db.query(Document).filter(
                Document.id.in_(document_ids)
            ).all()
            
            if len(documents) != len(document_ids):
                missing = set(document_ids) - {doc.id for doc in documents}
                raise ValueError(f"Documents not found: {missing}")
            
            # Default comparison aspects
            if comparison_aspects is None:
                comparison_aspects = ["tags", "complexity", "domains", "topics", "metadata"]
            
            comparison_results = {
                "documents": [
                    {
                        "id": doc.id,
                        "name": doc.name,
                        "size": doc.size,
                        "created_at": doc.created_at.isoformat()
                    }
                    for doc in documents
                ],
                "comparisons": {}
            }
            
            # Perform different types of comparisons
            if "tags" in comparison_aspects:
                comparison_results["comparisons"]["tag_comparison"] = await self._compare_document_tags(
                    documents, db
                )
            
            if "complexity" in comparison_aspects:
                comparison_results["comparisons"]["complexity_comparison"] = await self._compare_document_complexity(
                    documents, db
                )
            
            if "domains" in comparison_aspects:
                comparison_results["comparisons"]["domain_comparison"] = await self._compare_document_domains(
                    documents, db
                )
            
            if "topics" in comparison_aspects:
                comparison_results["comparisons"]["topic_comparison"] = await self._compare_document_topics(
                    documents, db
                )
            
            if "metadata" in comparison_aspects:
                comparison_results["comparisons"]["metadata_comparison"] = await self._compare_document_metadata(
                    documents
                )
            
            # Generate overall similarity score
            comparison_results["overall_similarity"] = await self._calculate_overall_similarity(
                comparison_results["comparisons"]
            )
            
            # Generate comparison insights
            comparison_results["insights"] = await self._generate_comparison_insights(
                comparison_results["comparisons"], documents
            )
            
            return comparison_results
            
        except Exception as e:
            logger.error(f"Error comparing documents: {str(e)}")
            raise
    
    async def _compare_document_tags(
        self,
        documents: List[Document],
        db: Session
    ) -> Dict[str, Any]:
        """Compare tags across documents"""
        try:
            document_ids = [doc.id for doc in documents]
            
            # Get all tags for documents
            tags = db.query(DocumentTag).filter(
                DocumentTag.document_id.in_(document_ids)
            ).all()
            
            # Group tags by document
            doc_tags = defaultdict(lambda: defaultdict(list))
            for tag in tags:
                doc_tags[tag.document_id][tag.tag_type].append(tag)
            
            # Compare tag overlap
            tag_comparisons = {}
            
            for i, doc1 in enumerate(documents):
                for j, doc2 in enumerate(documents[i+1:], i+1):
                    comparison_key = f"{doc1.name}_vs_{doc2.name}"
                    
                    doc1_tags = doc_tags[doc1.id]
                    doc2_tags = doc_tags[doc2.id]
                    
                    # Calculate overlap for each tag type
                    type_overlaps = {}
                    for tag_type in set(doc1_tags.keys()) | set(doc2_tags.keys()):
                        tags1 = {tag.tag_name for tag in doc1_tags.get(tag_type, [])}
                        tags2 = {tag.tag_name for tag in doc2_tags.get(tag_type, [])}
                        
                        intersection = tags1 & tags2
                        union = tags1 | tags2
                        
                        overlap_score = len(intersection) / len(union) if union else 0
                        
                        type_overlaps[tag_type] = {
                            "overlap_score": overlap_score,
                            "common_tags": list(intersection),
                            "unique_to_doc1": list(tags1 - tags2),
                            "unique_to_doc2": list(tags2 - tags1)
                        }
                    
                    tag_comparisons[comparison_key] = type_overlaps
            
            return tag_comparisons
            
        except Exception as e:
            logger.error(f"Error comparing document tags: {str(e)}")
            return {}
    
    async def _compare_document_complexity(
        self,
        documents: List[Document],
        db: Session
    ) -> Dict[str, Any]:
        """Compare complexity levels across documents"""
        try:
            document_ids = [doc.id for doc in documents]
            
            # Get complexity tags
            complexity_tags = db.query(DocumentTag).filter(
                DocumentTag.document_id.in_(document_ids),
                DocumentTag.tag_type == 'complexity'
            ).all()
            
            # Map complexity to numeric values
            complexity_mapping = {
                "complexity_beginner": 1,
                "complexity_intermediate": 2,
                "complexity_advanced": 3,
                "complexity_expert": 4
            }
            
            # Get complexity for each document
            doc_complexity = {}
            for doc in documents:
                doc_tags = [tag for tag in complexity_tags if tag.document_id == doc.id]
                
                if doc_tags:
                    # Use highest confidence complexity tag
                    best_tag = max(doc_tags, key=lambda x: x.confidence_score)
                    complexity_level = complexity_mapping.get(best_tag.tag_name, 0)
                    
                    doc_complexity[doc.id] = {
                        "level": complexity_level,
                        "level_name": best_tag.tag_name,
                        "confidence": best_tag.confidence_score
                    }
                else:
                    doc_complexity[doc.id] = {
                        "level": 0,
                        "level_name": "unknown",
                        "confidence": 0.0
                    }
            
            # Generate comparison matrix
            complexity_comparison = {}
            for i, doc1 in enumerate(documents):
                for j, doc2 in enumerate(documents[i+1:], i+1):
                    comparison_key = f"{doc1.name}_vs_{doc2.name}"
                    
                    comp1 = doc_complexity[doc1.id]
                    comp2 = doc_complexity[doc2.id]
                    
                    level_diff = abs(comp1["level"] - comp2["level"])
                    similarity = 1 - (level_diff / 4)  # Normalize to 0-1
                    
                    complexity_comparison[comparison_key] = {
                        "doc1_complexity": comp1,
                        "doc2_complexity": comp2,
                        "level_difference": level_diff,
                        "similarity_score": similarity,
                        "comparison": "similar" if level_diff <= 1 else "different"
                    }
            
            return {
                "document_complexities": doc_complexity,
                "pairwise_comparisons": complexity_comparison
            }
            
        except Exception as e:
            logger.error(f"Error comparing document complexity: {str(e)}")
            return {}
    
    async def _compare_document_domains(
        self,
        documents: List[Document],
        db: Session
    ) -> Dict[str, Any]:
        """Compare domains across documents"""
        try:
            document_ids = [doc.id for doc in documents]
            
            # Get domain tags
            domain_tags = db.query(DocumentTag).filter(
                DocumentTag.document_id.in_(document_ids),
                DocumentTag.tag_type == 'domain'
            ).all()
            
            # Group domains by document
            doc_domains = defaultdict(list)
            for tag in domain_tags:
                doc_domains[tag.document_id].append({
                    "name": tag.tag_name,
                    "confidence": tag.confidence_score
                })
            
            # Compare domain overlap
            domain_comparison = {}
            for i, doc1 in enumerate(documents):
                for j, doc2 in enumerate(documents[i+1:], i+1):
                    comparison_key = f"{doc1.name}_vs_{doc2.name}"
                    
                    domains1 = {d["name"] for d in doc_domains[doc1.id]}
                    domains2 = {d["name"] for d in doc_domains[doc2.id]}
                    
                    intersection = domains1 & domains2
                    union = domains1 | domains2
                    
                    overlap_score = len(intersection) / len(union) if union else 0
                    
                    domain_comparison[comparison_key] = {
                        "overlap_score": overlap_score,
                        "common_domains": list(intersection),
                        "doc1_unique_domains": list(domains1 - domains2),
                        "doc2_unique_domains": list(domains2 - domains1),
                        "relationship": "same_domain" if overlap_score > 0.7 else 
                                     "related_domains" if overlap_score > 0.3 else "different_domains"
                    }
            
            return {
                "document_domains": dict(doc_domains),
                "pairwise_comparisons": domain_comparison
            }
            
        except Exception as e:
            logger.error(f"Error comparing document domains: {str(e)}")
            return {}
    
    async def _compare_document_topics(
        self,
        documents: List[Document],
        db: Session
    ) -> Dict[str, Any]:
        """Compare topics across documents"""
        try:
            document_ids = [doc.id for doc in documents]
            
            # Get topic tags
            topic_tags = db.query(DocumentTag).filter(
                DocumentTag.document_id.in_(document_ids),
                DocumentTag.tag_type == 'topic'
            ).all()
            
            # Group topics by document
            doc_topics = defaultdict(list)
            for tag in topic_tags:
                doc_topics[tag.document_id].append({
                    "name": tag.tag_name,
                    "confidence": tag.confidence_score
                })
            
            # Compare topic overlap and relationships
            topic_comparison = {}
            for i, doc1 in enumerate(documents):
                for j, doc2 in enumerate(documents[i+1:], i+1):
                    comparison_key = f"{doc1.name}_vs_{doc2.name}"
                    
                    topics1 = {t["name"] for t in doc_topics[doc1.id]}
                    topics2 = {t["name"] for t in doc_topics[doc2.id]}
                    
                    intersection = topics1 & topics2
                    union = topics1 | topics2
                    
                    overlap_score = len(intersection) / len(union) if union else 0
                    
                    # Calculate weighted similarity based on confidence
                    weighted_similarity = 0
                    if intersection:
                        for topic in intersection:
                            conf1 = next((t["confidence"] for t in doc_topics[doc1.id] if t["name"] == topic), 0)
                            conf2 = next((t["confidence"] for t in doc_topics[doc2.id] if t["name"] == topic), 0)
                            weighted_similarity += (conf1 + conf2) / 2
                        weighted_similarity /= len(intersection)
                    
                    topic_comparison[comparison_key] = {
                        "overlap_score": overlap_score,
                        "weighted_similarity": weighted_similarity,
                        "common_topics": list(intersection),
                        "doc1_unique_topics": list(topics1 - topics2),
                        "doc2_unique_topics": list(topics2 - topics1),
                        "relationship": "highly_related" if overlap_score > 0.6 else 
                                     "somewhat_related" if overlap_score > 0.2 else "unrelated"
                    }
            
            return {
                "document_topics": dict(doc_topics),
                "pairwise_comparisons": topic_comparison
            }
            
        except Exception as e:
            logger.error(f"Error comparing document topics: {str(e)}")
            return {}
    
    async def _compare_document_metadata(
        self,
        documents: List[Document]
    ) -> Dict[str, Any]:
        """Compare basic metadata across documents"""
        try:
            metadata_comparison = {}
            
            for i, doc1 in enumerate(documents):
                for j, doc2 in enumerate(documents[i+1:], i+1):
                    comparison_key = f"{doc1.name}_vs_{doc2.name}"
                    
                    # Size comparison
                    size_ratio = min(doc1.size, doc2.size) / max(doc1.size, doc2.size)
                    
                    # Time comparison
                    time_diff = abs((doc1.created_at - doc2.created_at).days)
                    
                    # Content type comparison
                    same_type = doc1.content_type == doc2.content_type
                    
                    metadata_comparison[comparison_key] = {
                        "size_similarity": size_ratio,
                        "size_difference_bytes": abs(doc1.size - doc2.size),
                        "time_difference_days": time_diff,
                        "same_content_type": same_type,
                        "doc1_metadata": {
                            "size": doc1.size,
                            "content_type": doc1.content_type,
                            "created_at": doc1.created_at.isoformat()
                        },
                        "doc2_metadata": {
                            "size": doc2.size,
                            "content_type": doc2.content_type,
                            "created_at": doc2.created_at.isoformat()
                        }
                    }
            
            return metadata_comparison
            
        except Exception as e:
            logger.error(f"Error comparing document metadata: {str(e)}")
            return {}
    
    async def _calculate_overall_similarity(
        self,
        comparisons: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate overall similarity scores between documents"""
        try:
            overall_similarities = {}
            
            # Get all comparison keys (document pairs)
            comparison_keys = set()
            for comp_type, comp_data in comparisons.items():
                if isinstance(comp_data, dict) and "pairwise_comparisons" in comp_data:
                    comparison_keys.update(comp_data["pairwise_comparisons"].keys())
                elif isinstance(comp_data, dict):
                    comparison_keys.update(comp_data.keys())
            
            # Calculate weighted average similarity for each pair
            for pair_key in comparison_keys:
                similarities = []
                weights = []
                
                # Tag similarity
                if "tag_comparison" in comparisons and pair_key in comparisons["tag_comparison"]:
                    tag_data = comparisons["tag_comparison"][pair_key]
                    avg_overlap = statistics.mean([
                        data["overlap_score"] for data in tag_data.values()
                    ]) if tag_data else 0
                    similarities.append(avg_overlap)
                    weights.append(0.3)
                
                # Complexity similarity
                if ("complexity_comparison" in comparisons and 
                    "pairwise_comparisons" in comparisons["complexity_comparison"] and
                    pair_key in comparisons["complexity_comparison"]["pairwise_comparisons"]):
                    comp_sim = comparisons["complexity_comparison"]["pairwise_comparisons"][pair_key]["similarity_score"]
                    similarities.append(comp_sim)
                    weights.append(0.2)
                
                # Domain similarity
                if ("domain_comparison" in comparisons and 
                    "pairwise_comparisons" in comparisons["domain_comparison"] and
                    pair_key in comparisons["domain_comparison"]["pairwise_comparisons"]):
                    domain_sim = comparisons["domain_comparison"]["pairwise_comparisons"][pair_key]["overlap_score"]
                    similarities.append(domain_sim)
                    weights.append(0.25)
                
                # Topic similarity
                if ("topic_comparison" in comparisons and 
                    "pairwise_comparisons" in comparisons["topic_comparison"] and
                    pair_key in comparisons["topic_comparison"]["pairwise_comparisons"]):
                    topic_sim = comparisons["topic_comparison"]["pairwise_comparisons"][pair_key]["weighted_similarity"]
                    similarities.append(topic_sim)
                    weights.append(0.25)
                
                # Calculate weighted average
                if similarities and weights:
                    weighted_sum = sum(s * w for s, w in zip(similarities, weights))
                    total_weight = sum(weights)
                    overall_similarities[pair_key] = weighted_sum / total_weight
                else:
                    overall_similarities[pair_key] = 0.0
            
            return overall_similarities
            
        except Exception as e:
            logger.error(f"Error calculating overall similarity: {str(e)}")
            return {}
    
    async def _generate_comparison_insights(
        self,
        comparisons: Dict[str, Any],
        documents: List[Document]
    ) -> List[Dict[str, Any]]:
        """Generate insights from document comparisons"""
        insights = []
        
        try:
            # Analyze tag patterns
            if "tag_comparison" in comparisons:
                for pair_key, tag_data in comparisons["tag_comparison"].items():
                    for tag_type, type_data in tag_data.items():
                        if type_data["overlap_score"] > 0.7:
                            insights.append({
                                "type": "high_tag_similarity",
                                "category": tag_type,
                                "insight": f"Documents have high {tag_type} similarity ({type_data['overlap_score']:.2f})",
                                "documents": pair_key,
                                "common_elements": type_data["common_tags"]
                            })
            
            # Analyze complexity patterns
            if ("complexity_comparison" in comparisons and 
                "pairwise_comparisons" in comparisons["complexity_comparison"]):
                for pair_key, comp_data in comparisons["complexity_comparison"]["pairwise_comparisons"].items():
                    if comp_data["comparison"] == "different":
                        insights.append({
                            "type": "complexity_difference",
                            "category": "difficulty",
                            "insight": f"Documents have different complexity levels",
                            "documents": pair_key,
                            "details": {
                                "doc1": comp_data["doc1_complexity"]["level_name"],
                                "doc2": comp_data["doc2_complexity"]["level_name"]
                            }
                        })
            
            # Analyze domain relationships
            if ("domain_comparison" in comparisons and 
                "pairwise_comparisons" in comparisons["domain_comparison"]):
                for pair_key, domain_data in comparisons["domain_comparison"]["pairwise_comparisons"].items():
                    if domain_data["relationship"] == "same_domain":
                        insights.append({
                            "type": "same_domain",
                            "category": "subject_area",
                            "insight": f"Documents belong to the same domain",
                            "documents": pair_key,
                            "common_domains": domain_data["common_domains"]
                        })
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating comparison insights: {str(e)}")
            return []

# Global instance
trend_analyzer = TrendAnalyzer()